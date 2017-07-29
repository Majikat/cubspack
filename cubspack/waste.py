# -*- coding: utf-8 -*-

from cubspack.geometry import Cuboid
from cubspack.guillotine import GuillotineBafMinas


class WasteManager(GuillotineBafMinas):

    def __init__(self, rot=True, merge=True, *args, **kwargs):
        super(WasteManager, self).__init__(
            1, 1, 1, rot=rot, merge=merge, *args, **kwargs)

    def add_waste(self, x, y, z, width, height, depth):
        """Add new waste section"""
        self._add_section(Cuboid(x, y, z, width, height, depth))

    def _fits_volume(self, width, height, depth):
        raise NotImplementedError

    def validate_packing(self):
        raise NotImplementedError

    def reset(self):
        super(WasteManager, self).reset()
        self._sections = []
