# -*- coding: utf-8 -*-

import collections
from cubspack.geometry import Cuboid
from cubspack.pack_algo import PackingAlgorithm
import itertools
import operator


first_item = operator.itemgetter(0)


class MaxCubs(PackingAlgorithm):

    def __init__(self, width, height, depth, rot=True, *args, **kwargs):
        super(MaxCubs, self).__init__(
            width, height, depth, rot, *args, **kwargs)

    def _cub_fitness(self, max_cub, width, height, depth):
        """Get fitness value

        Arguments:
            max_cub (Cuboid): Destination max_cub
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float): Cuboid depth

        Returns:
            None: Cuboid couldn't be placed into max_cub
            integer, float: fitness value
        """
        if width <= max_cub.width and height <= max_cub.height and \
                depth <= max_cub.depth:
            return 0
        else:
            return None

    def _select_position(self, w, h, d):
        """Find max_cub with best fitness for placing a cuboid(w*h*d)

        Arguments:
            w (int, float): Cuboid width
            h (int, float): Cuboid height
            d (int, float): Cuboid depth

        Returns:
            (cub, max_cub)
            cub (Cuboid): Placed Cuboid or None if was unable.
            max_cub (Cuboid): Maximal cuboid were cub was placed
        """
        if not self._max_cubs:
            return None, None

        # Normal cuboid
        fitn = ((self._cub_fitness(m, w, h, d), w, h, d, m) for m in
                self._max_cubs if self._cub_fitness(m, w, h, d) is not None)

        # Rotated cuboid
        fitr = ((self._cub_fitness(m, h, w, d), h, w, d, m) for m in
                self._max_cubs if self._cub_fitness(m, h, w, d) is not None)

        if not self.rot:
            fitr = []

        fit = itertools.chain(fitn, fitr)

        try:
            _, w, h, d, m = min(fit, key=first_item)
        except ValueError:
            return None, None

        return Cuboid(m.x, m.y, m.z, w, h, d), m

    def _generate_splits(self, m, c):
        """Get new cuboids splits after cuboid is placed

        When a cuboid is placed inside a maximal cuboid, it stops being one
        and up to 5 new maximal cuboids may appear depending on the
        placement.
        _generate_splits calculates them.

        Arguments:
            m (Cuboid): max_cub Cuboid
            r (Cuboid): Cuboid placed

        Returns:
            list : list containing new maximal cuboids or an empty list
        """
        new_cubs = []

        if c.left > m.left:
            new_cubs.append(Cuboid(
                m.left, m.bottom, m.outeye,
                c.left - m.left, m.height, m.depth))
        if c.right < m.right:
            new_cubs.append(Cuboid(
                c.right, m.bottom, m.outeye,
                m.right - c.right, m.height, m.depth))
        if c.top < m.top:
            new_cubs.append(Cuboid(
                m.left, c.top, m.outeye,
                m.width, m.top - c.top, m.depth))
        if c.bottom > m.bottom:
            new_cubs.append(Cuboid(
                m.left, m.bottom, m.outeye,
                m.width, c.bottom - m.bottom, m.depth))
        if c.ineye < m.ineye:
            new_cubs.append(Cuboid(
                c.left, c.bottom, c.ineye,
                c.width, c.height, m.ineye - c.ineye))

        return new_cubs

    def _split(self, cub):
        """Split all max_cubs intersecting the cuboid cub.

        Arguments:
            cub (Cuboid): Cuboid

        Returns:
            split (Cuboid list): List of cuboids resulting from the split
        """
        max_cubs = collections.deque()

        for c in self._max_cubs:
            if c.intersects(cub):
                max_cubs.extend(self._generate_splits(c, cub))
            else:
                max_cubs.append(c)

        # Add newly generated max_cubs
        self._max_cubs = list(max_cubs)

    def _remove_duplicates(self):
        """Remove every maximal cuboid contained by another one."""
        contained = set()
        for m1, m2 in itertools.combinations(self._max_cubs, 2):
            if m1.contains(m2):
                contained.add(m2)
            elif m2.contains(m1):
                contained.add(m1)

        # Remove from max_cubs
        self._max_cubs = [m for m in self._max_cubs if m not in contained]

    def fitness(self, width, height, depth):
        """Is the cuboid well fit ? The anwser here.

        Metric used to rate how much space is wasted if a cuboid is placed.
        Returns a value greater or equal to zero, the smaller the value the
        more 'fit' is the cuboid. If the cuboid can't be placed, returns None.

        Arguments:
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float): Cuboid depth

        Returns:
            int, float: Cuboid fitness
            None: Cuboid can't be placed
        """
        assert(width > 0 and height > 0 and depth > 0)

        cub, max_cub = self._select_position(width, height, depth)
        if cub is None:
            return None

        # Return fitness
        return self._cub_fitness(max_cub, cub.width, cub.height, cub.depth)

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

        # Search best position and orientation
        cub, _ = self._select_position(width, height, depth)
        if not cub:
            return None

        # Subdivide all the max cuboids intersecting with the selected
        # cuboid.
        self._split(cub)

        # Remove any max_cub contained by another
        self._remove_duplicates()

        # Store and return cuboid position.
        cub.rid = rid
        self.cuboids.append(cub)
        return cub

    def reset(self):
        super(MaxCubs, self).reset()
        self._max_cubs = [Cuboid(0, 0, 0, self.width, self.height, self.depth)]


class MaxCubsBl(MaxCubs):

    def _select_position(self, w, h, d):
        """Find lowest position

        Select the position where the y coordinate of the top of the cuboid
        is lower, if there are severtal pick the one with the smallest x
        coordinate
        """
        fitn = ((m.y + h, m.x, m.z, w, h, d, m) for m in self._max_cubs
                if self._cub_fitness(m, w, h, d) is not None)
        fitr = ((m.y + w, m.x, m.z, h, w, d, m) for m in self._max_cubs
                if self._cub_fitness(m, h, w, d) is not None)

        if not self.rot:
            fitr = []

        fit = itertools.chain(fitn, fitr)

        try:
            _, _, _, w, h, d, m = min(fit, key=first_item)
        except ValueError:
            return None, None

        return Cuboid(m.x, m.y, m.z, w, h, d), m


class MaxCubsBssf(MaxCubs):
    """Best Sort Side Fit minimize short leftover side"""
    def _rect_fitness(self, max_cub, width, height, depth):
        if width > max_cub.width or height > max_cub.height or \
                depth > max_cub.depth:
            return None

        return min(max_cub.width - width, max_cub.height -
                   height, max_cub.depth - depth)


class MaxCubsBaf(MaxCubs):
    """Description below

    Best Area Fit pick maximal cuboid with smallest area
    where the cuboid can be placed
    """
    def _rect_fitness(self, max_cub, width, height, depth):
        if width > max_cub.width or height > max_cub.height or \
                depth > max_cub.depth:
            return None

        return (max_cub.width * max_cub.height * max_cub.depth) - \
            (width * height * depth)


class MaxCubsBlsf(MaxCubs):
    """Best Long Side Fit minimize long leftover side"""
    def _rect_fitness(self, max_cub, width, height, depth):
        if width > max_cub.width or height > max_cub.height or \
                depth > max_cub.depth:
            return None

        return max(max_cub.width - width, max_cub.height -
                   height, max_cub.depth - depth)
