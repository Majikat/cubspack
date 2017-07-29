# -*- coding: utf-8 -*-

from cubspack.packer import newPacker
from cubspack.packer import PackingBin
from cubspack.packer import PackingMode
from cubspack.packer import SORT_LSIDE
from cubspack.skyline import SkylineBlWm


class Enclose(object):
    def __init__(
        self, cuboids=[], max_width=None, max_height=None,
            max_depth=None, rotation=True):
        """Arguments:

            cuboids (list): Cuboids to be enveloped
                [(width1, height1, depth1), (width2, height2, depth2), ...]
            max_width (number|None): Enveloping cuboid max allowed width.
            max_height (number|None): Enveloping cuboid max allowed height.
            max_depth (number|None): Enveloping cuboid max allowed depth.
            rotation (boolean): Enable/Disable cuboid rotation.
        """
        # Enclosing cuboid max width
        self._max_width = max_width

        # Enclosing cuboid max height
        self._max_height = max_height

        # Enclosing cuboid max depth
        self._max_depth = max_depth

        # Enable or disable cuboid rotation
        self._rotation = rotation

        # Default packing algorithm
        self._pack_algo = SkylineBlWm

        # cuboids to enclose [(width, height), (width, height, ...)]
        self._cuboids = []
        for r in cuboids:
            self.add_cub(*r)

    def _container_candidates(self):
        """Generate container candidate list

        Returns:
            tuple list: [(width1, height1, depth1),
                         (width2, height2, depth2), ...]
        """
        if not self._cuboids:
            return []

        max_depth = sum(c[2] for c in self._cuboids)
        if self._rotation:
            sides = sorted(side for cub in self._cuboids for side in cub)
            max_height = sum(max(c[0], c[1]) for c in self._cuboids)
            min_width = max(min(c[0], c[1]) for c in self._cuboids)
            max_width = max_height
        else:
            sides = sorted(c[0] for c in self._cuboids)
            max_height = sum(c[1] for c in self._cuboids)
            min_width = max(c[0] for c in self._cuboids)
            max_width = sum(sides)

        if self._max_width and self._max_width < max_width:
            max_width = self._max_width

        if self._max_height and self._max_height < max_height:
            max_height = self._max_height

        if self._max_depth and self._max_depth < max_depth:
            max_depth = self._max_depth

        assert(max_width > min_width)

        # Generate initial container widths
        candidates = [max_width, min_width]

        width = 0
        for s in reversed(sides):
            width += s
            candidates.append(width)

        width = 0
        for s in sides:
            width += s
            candidates.append(width)

        candidates.append(max_width)
        candidates.append(min_width)

        # Remove duplicates and widths too big or small
        seen = set()
        seen_add = seen.add
        candidates = [x for x in candidates if not (x in seen or seen_add(x))]
        candidates = [x for x in candidates if not (
            x > max_width or x < min_width)]

        # Remove candidates too small to fit all the cuboids
        min_volume = sum(c[0]*c[1]*c[2] for c in self._cuboids)
        return [(c, max_height, max_depth) for c in candidates if
                c * max_height * max_depth >= min_volume]

    def _refine_candidate(self, width, height, depth):
        """Use bottom-left packing algorithm to find a lower height/depth

        Arguments:
            width
            height
            depth

        Returns:
            tuple (width, height, depth, PackingAlgorithm):
        """
        packer = newPacker(PackingMode.Offline, PackingBin.BFF,
                           pack_algo=self._pack_algo, sort_algo=SORT_LSIDE,
                           rotation=self._rotation)
        packer.add_bin(width, height, depth)

        for c in self._cuboids:
            packer.add_cub(*c)

        packer.pack()

        # Check all cuboids where packed
        if len(packer[0]) != len(self._cuboids):
            return None

        # Find highest cuboid
        new_height = max(packer[0], key=lambda x: x.top).top

        # Find deepest cuboid
        new_depth = max(packer[0], key=lambda x: x.ineye).ineye
        return(width, new_height, new_depth, packer)

    def generate(self):

        # Generate initial containers
        candidates = self._container_candidates()
        if not candidates:
            return None

        # Refine candidates and return the one with the smallest volume
        containers = [self._refine_candidate(*c) for c in candidates]
        containers = [c for c in containers if c]
        if not containers:
            return None

        width, height, depth, packer = min(
            containers, key=lambda x: x[0]*x[1]*x[2])

        packer.width = width
        packer.height = height
        packer.depth = depth
        return packer

    def add_cub(self, width, height, depth):
        """Add another cuboid to be enclosed

        Arguments:
            width (number): Cuboid width
            height (number): Cuboid height
            depth (number): Cuboid depth
        """
        self._cuboids.append((width, height, depth))
