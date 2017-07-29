
from cubspack.geometry import Cuboid
from cubspack.pack_algo import PackingAlgorithm
import itertools
import operator


class Guillotine(PackingAlgorithm):
    """Implementation of several variants of Guillotine packing algorithm

    For a more detailed explanation of the algorithm used, see:
    Jukka Jylanki - A Thousand Ways to Pack the Bin (February 27, 2010)
    """
    def __init__(self, width, height, depth, rot=True, merge=True,
                 *args, **kwargs):
        """Argument list.

        Arguments:
            width (int, float):
            height (int, float):
            depth (int, float):
            merge (bool): Optional keyword argument
        """
        self._merge = merge
        super(Guillotine, self).__init__(
            width, height, depth, rot, *args, **kwargs)

    def _add_section(self, section):
        """Adds a new section to the free section list.

        But before that and if section merge is enabled, tries to join the
        cuboid with all existing sections, if successful the resulting
        section is again merged with the remaining sections until the operation
        fails. The result is then appended to the list.

        Arguments:
            section (Cuboid): New free section.
        """
        section.rid = 0
        plen = 0

        while self._merge and self._sections and plen != len(self._sections):
            plen = len(self._sections)
            self._sections = [s for s in self._sections if not section.join(s)]
        self._sections.append(section)

    def _split_horizontal(self, section, width, height, depth):
        """We split the section horizontally.

        For an horizontal split the cuboid is placed in the lower
        left corner of the section (section's xyz coordinates), the top
        most side of the cuboid and its horizontal continuation,
        marks the line of division for the split.

        To those we add the cuboid on top of the cuboid we just placed.
        The other two sections created goes all the way to the top of the
        section in which we placed the cuboid.

        +-----------------+
        |                 |
        |                 |
        |                 |
        |                 |
        +-------+---------+
        |#######|         |
        |#######|         |
        |#######|         |
        +-------+---------+

        If the cuboid width is equal to the the section width, only two
        sections are created over the cuboid and on top of it. If the cuboid
        height is equal to the section height, only two sections to the right
        and the top of the cuboid is created. If both width and height are
        equal, only one section is created on top of the cuboid. If both width,
        height and depth are equal, no sections are created.
        """

        # First remove the section we are splitting so it doesn't
        # interfere when later we try to merge the resulting split
        # cuboids, with the rest of free sections.
        # self._sections.remove(section)

        # Creates three new empty sections, and returns the new cuboid.
        if height < section.height:
            self._add_section(Cuboid(
                section.x, section.y + height, section.z,
                section.width, section.height - height, section.depth))

        if width < section.width:
            self._add_section(Cuboid(
                section.x + width, section.y, section.z,
                section.width - width, height, section.depth))

        if depth < section.depth:
            self._add_section(Cuboid(
                section.x, section.y, section.z + depth,
                width, height, section.depth - depth))

    def _split_vertical(self, section, width, height, depth):
        """We split the section vertically.

        For a vertical split the cuboid is placed in the lower
        left corner of the section (section's xyz coordinates), the
        right most side of the cuboid and its vertical continuation,
        marks the line of division for the split.

        To those we add the cuboid on top of the cuboid we just placed.
        The other two sections created goes all the way to the top of the
        section in which we placed the cuboid.

        +-------+---------+
        |       |         |
        |       |         |
        |       |         |
        |       |         |
        +-------+         |
        |#######|         |
        |#######|         |
        |#######|         |
        +-------+---------+

        If the cuboid width is equal to the the section width, only two
        sections are created over the cuboid and on top of it. If the cuboid
        height is equal to the section height, only two sections to the right
        and the top of the cuboid is created. If both width and height are
        equal, only one section is created on top of the cuboid. If both width,
        height and depth are equal, no sections are created.
        """

        # When a section is split, depending on the cuboid size
        # three, two, one, or no new sections will be created.

        if height < section.height:
            self._add_section(Cuboid(
                section.x, section.y + height, section.z,
                width, section.height - height, section.depth))

        if width < section.width:
            self._add_section(Cuboid(
                section.x + width, section.y, section.z,
                section.width - width, section.height, section.depth))

        if depth < section.depth:
            self._add_section(Cuboid(
                section.x, section.y, section.z + depth,
                width, height, section.depth - depth))

    def _split(self, section, width, height, depth):
        """Split it.

        Selects the best split for a section, given a cuboid of dimensions
        width, height and depth, then calls _split_vertical or
        _split_horizontal to do the dirty work.

        Arguments:
            section (Cuboid): Section to split
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float); Cuboid depth
        """
        raise NotImplementedError

    def _section_fitness(self, section, width, height, depth):
        """Guillotine Subclass

        The subclass for each one of the Guillotine selection methods,
        BAF, BLSF.... will override this method, this is here only
        to asure a valid value return if the worst happens.
        """
        raise NotImplementedError

    def _select_fittest_section(self, w, h, d):
        """Select the fittest section

        Calls _section_fitness for each of the sections in free section
        list. Returns the section with the minimal fitness value, all the rest
        is boilerplate to make the fitness comparison, to rotate the cuboids,
        and to take into account when _section_fitness returns None because
        the cuboid couldn't be placed.

        Arguments:
            w (int, float): Cuboid width
            h (int, float): Cuboid height
            d (int, float): Cuboid depth

        Returns:
            (section, was_rotated): Returns the tuple
                section (Cuboid): Section with best fitness
                was_rotated (bool): The cuboid was rotated
        """
        fitn = ((self._section_fitness(s, w, h, d), s, False) for s in
                self._sections if self._section_fitness(
                    s, w, h, d) is not None)
        fitr = ((self._section_fitness(s, h, w, d), s, True) for s in
                self._sections if self._section_fitness(
                    s, h, w, d) is not None)

        if not self.rot:
            fitr = []

        fit = itertools.chain(fitn, fitr)

        try:
            _, sec, rot = min(fit, key=operator.itemgetter(0))
        except ValueError:
            return None, None

        return sec, rot

    def add_cub(self, width, height, depth, rid=None):
        """Add cuboid of widthxheightxdepth dimensions.

        Arguments:
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float): Cuboid depth
            rid: Optional cuboid user id

        Returns:
            Cuboid: Cuboid with placement coordinates
            None: If the cuboid couldn't be placed.
        """
        assert(width > 0 and height > 0 and depth > 0)

        # Obtain the best section to place the cuboid.
        section, rotated = self._select_fittest_section(width, height, depth)
        if not section:
            return None

        if rotated:
            # This should be changed, I'm just supposing that item should be
            # oriented upward all the time.
            # See : pack_algo.py:49
            width, height = height, width

        # Remove section, split and store results
        self._sections.remove(section)
        self._split(section, width, height, depth)

        # Store Cuboid in the selected position
        cub = Cuboid(
            section.x, section.y, section.z, width, height, depth, rid)
        self.cuboids.append(cub)
        return cub

    def fitness(self, width, height, depth):
        """Gets best fitness

        In guillotine algorithm case, returns the min of the fitness of all
        free sections, for the given dimension, both normal and rotated
        (if rotation enabled.)
        """
        assert(width > 0 and height > 0, depth > 0)

        # Get best fitness section.
        section, rotated = self._select_fittest_section(width, height, depth)
        if not section:
            return None

        # Return fitness of returned section, with correct dimmensions if the
        # the cuboid was rotated.
        if rotated:
            return self._section_fitness(section, height, width, depth)
        else:
            return self._section_fitness(section, width, height, depth)

    def reset(self):
        super(Guillotine, self).reset()
        self._sections = []
        self._add_section(Cuboid(0, 0, 0, self.width, self.height, self.depth))


class GuillotineBvf(Guillotine):
    """Implements Best Volume Fit (BVF) section selection criteria"""
    def _section_fitness(self, section, width, height, depth):
        if width > section.width or height > section.height or \
                depth > section.depth:
            return None
        return section.volume() - width * height * depth


class GuillotineBlsf(Guillotine):
    """Implements Best Long Side Fit (BLSF) section selection criteria"""
    def _section_fitness(self, section, width, height, depth):
        if width > section.width or height > section.height or \
                depth > section.depth:
            return None
        return max(section.width - width, section.height - height,
                   section.depth - depth)


class GuillotineBssf(Guillotine):
    """Implements Best Short Side Fit (BSSF) section selection criteria"""
    def _section_fitness(self, section, width, height, depth):
        if width > section.width or height > section.height or \
                depth > section.depth:
            return None
        return min(section.width - width, section.height - height,
                   section.depth - depth)


class GuillotineSas(Guillotine):
    """Implements Short Axis Split (SAS) selection rule"""
    def _split(self, section, width, height, depth):
        if section.width < section.height:
            return self._split_horizontal(section, width, height, depth)
        else:
            return self._split_vertical(section, width, height, depth)


class GuillotineLas(Guillotine):
    """Implements Long Axis Split (LAS) selection rule"""
    def _split(self, section, width, height, depth):
        if section.width >= section.height:
            return self._split_horizontal(section, width, height, depth)
        else:
            return self._split_vertical(section, width, height, depth)


class GuillotineSlas(Guillotine):
    """Implements Short Leftover Axis Split (SLAS) selection rule"""
    def _split(self, section, width, height, depth):
        if section.width - width < section.height - height:
            return self._split_horizontal(section, width, height, depth)
        else:
            return self._split_vertical(section, width, height, depth)


class GuillotineLlas(Guillotine):
    """Implements Long Leftover Axis Split (LLAS) selection"""
    def _split(self, section, width, height, depth):
        if section.width - width >= section.height - height:
            return self._split_horizontal(section, width, height, depth)
        else:
            return self._split_vertical(section, width, height, depth)


class GuillotineMaxas(Guillotine):
    """Implements Max Area Axis Split (MAXAS) selection rule

    For Guillotine algorithm. Maximize the larger area == minimize the smaller
    area. Tries to make the cuboids more even-sized.
    """
    def _split(self, section, width, height, depth):
        if width * ((section.height - height) + (section.depth - depth)) <= \
                height * ((section.width - width) + (section.depth - depth)):
            return self._split_horizontal(section, width, height)
        else:
            return self._split_vertical(section, width, height)


class GuillotineMinas(Guillotine):
    """Implements Min Area Axis Split (MINAS) selection rule"""
    def _split(self, section, width, height, depth):
        if width * ((section.height - height) + (section.depth - depth)) >= \
                height * ((section.width - width) + (section.depth - depth)):
            return self._split_horizontal(section, width, height, depth)
        else:
            return self._split_vertical(section, width, height, depth)


# Guillotine algorithms GUILLOTINE-CUB-SPLIT, Selecting one
# Axis split, and one selection criteria.
class GuillotineBssfSas(GuillotineBssf, GuillotineSas):
    pass


class GuillotineBssfLas(GuillotineBssf, GuillotineLas):
    pass


class GuillotineBssfSlas(GuillotineBssf, GuillotineSlas):
    pass


class GuillotineBssfLlas(GuillotineBssf, GuillotineLlas):
    pass


class GuillotineBssfMaxas(GuillotineBssf, GuillotineMaxas):
    pass


class GuillotineBssfMinas(GuillotineBssf, GuillotineMinas):
    pass


class GuillotineBlsfSas(GuillotineBlsf, GuillotineSas):
    pass


class GuillotineBlsfLas(GuillotineBlsf, GuillotineLas):
    pass


class GuillotineBlsfSlas(GuillotineBlsf, GuillotineSlas):
    pass


class GuillotineBlsfLlas(GuillotineBlsf, GuillotineLlas):
    pass


class GuillotineBlsfMaxas(GuillotineBlsf, GuillotineMaxas):
    pass


class GuillotineBlsfMinas(GuillotineBlsf, GuillotineMinas):
    pass


class GuillotineBvfSas(GuillotineBvf, GuillotineSas):
    pass


class GuillotineBvfLas(GuillotineBvf, GuillotineLas):
    pass


class GuillotineBvfSlas(GuillotineBvf, GuillotineSlas):
    pass


class GuillotineBvfLlas(GuillotineBvf, GuillotineLlas):
    pass


class GuillotineBvfMaxas(GuillotineBvf, GuillotineMaxas):
    pass


class GuillotineBvfMinas(GuillotineBvf, GuillotineMinas):
    pass
