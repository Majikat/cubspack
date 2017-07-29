# -*- coding: utf-8 -*-

from cubspack.geometry import Cuboid


class PackingAlgorithm(object):
    """PackingAlgorithm base class"""

    def __init__(self, width, height, depth, rot=True, *args, **kwargs):
        """Initialize packing algorithm

        Arguments:
            width (int, float): Packing volume width
            height (int, float): Packing volume height
            depth (int, float): Packing volume depth
            rot (bool): Cuboid rotation enabled or disabled
        """
        self.width = width
        self.height = height
        self.depth = depth
        self.rot = rot
        self.cuboids = []
        self._surface = Cuboid(0, 0, 0, width, height, depth)
        self.reset()

    def __len__(self):
        return len(self.cuboids)

    def __iter__(self):
        return iter(self.cuboids)

    def _fits_volume(self, width, height, depth):
        """Test volume is big enough to place a cuboid

        Arguments:
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float): Cuboid depth

        Returns:
            boolean: True if it could be placed, False otherwise
        """
        assert(width > 0 and height > 0 and depth > 0)
        w, h, d = width, height, depth

        if self.rot and w > self.width or h > self.height:
            w, h = h, w

        # The rest here is for future development where it is possible
        # To put the package in position that is not upward.
        # For now, the cuboid have a direction in which it should be.

        # o_width, o_height, o_depth = width, height, depth
        # if self.rot:
        #     if w > self.width or h > self.height or d > self.depth:
        #         w, h, d = o_width, o_depth, o_height
        #     if w > self.width or h > self.height or d > self.depth:
        #         w, h, d = o_height, o_width, o_depth
        #     if w > self.width or h > self.height or d > self.depth:
        #         w, h, d = o_height, o_depth, o_width
        #     if w > self.width or h > self.height or d > self.depth:
        #         w, h, d = o_depth, o_height, o_width
        #     if w > self.width or h > self.height or d > self.depth:
        #         w, h, d = o_depth, o_width, o_height

        if w > self.width or h > self.height or d > self.depth:
            return False
        else:
            return True

    def __getitem__(self, key):
        """Return cuboid in selected position."""
        return self.cuboids[key]

    def used_volume(self):
        """Total volume of cuboids placed

        Returns:
            int, float: Volume
        """
        return sum(c.volume() for c in self)

    def fitness(self, width, height, depth, rot=False):
        """Metric used to rate how much space is wasted.

        Metric used to rate how much space is wasted if a cuboid is placed.
        Returns a value greater or equal to zero, the smaller the value the
        more 'fit' is the cuboid. If the cuboid can't be placed, returns
        None.

        Arguments:
            width (int, float): Cuboid width
            height (int, float): Cuboid height
            depth (int, float): Cuboid depth
            rot (bool): Enable cuboid rotation

        Returns:
            int, float: Cuboid fitness
            None: Cuboid can't be placed
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def cubs_list(self):
        """Returns a list with all cuboids placed into the volume.

        Returns:
            List: Format [(rid, x, y, z, width, height, depth), ...]
        """
        cuboid_list = []
        for c in self:
            cuboid_list.append(
                (c.x, c.y, c.z, c.width, c.height, c.depth, c.rid))

        return cuboid_list

    def validate_packing(self):
        """Check for collisions between cuboids.

        Also check all are placed inside surface.
        """
        volume = Cuboid(0, 0, 0, self.width, self.height, self.width)

        for c in self:
            if not volume.contains(c):
                raise Exception("Cuboid placed outside volume.")

        cuboids = [c for c in self]
        if len(cuboids) <= 1:
            return

        for c1 in range(0, len(cuboids)-2):
            for c2 in range(c1+1, len(cuboids)-1):
                if cuboids[c1].intersects(cuboids[c2]):
                    raise Exception("Cuboid collision detected")

    def is_empty(self):
        # Returns true if there is no cuboids placed.
        return not bool(len(self))

    def reset(self):
        self.cuboids = []
