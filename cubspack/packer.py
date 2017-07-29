# -*- coding: utf-8 -*-

from cubspack.maxcubs import MaxCubsBssf

import collections
import decimal
import itertools
import operator


# Float to Decimal helper
def float2dec(ft, decimal_digits):
    """Convert float (or int) to Decimal (rounding up)

    With the requested number of decimal digits.

    Arguments:
        ft (float, int): Number to convert
        decimal (int): Number of digits after decimal point

    Return:
        Decimal: Number converted to decimal
    """
    with decimal.localcontext() as ctx:
        ctx.rounding = decimal.ROUND_UP
        places = decimal.Decimal(10)**(-decimal_digits)
        return decimal.Decimal.from_float(float(ft)).quantize(places)


# Sorting algos for cuboid lists
# Sort by volume
SORT_VOLUME = lambda cublist: sorted(
    cublist, reverse=True, key=lambda c: c[0]*c[1]*c[2])

# Sort by area
SORT_AREA = lambda cublist: sorted(
    cublist, reverse=True, key=lambda c: 2*(
        c[0]*c[1]) + 2*(c[0]*c[2]) + 2*(c[1]*c[2]))

# Sort by Diff
SORT_DIFF = lambda cublist: sorted(
    cublist, reverse=True, key=lambda c: (
        abs(c[0]-c[1]), abs(c[0]-c[2]), abs(c[1]-c[2])))

# Sort by short side
SORT_SSIDE = lambda cublist: sorted(
    cublist, reverse=True,  key=lambda c: (
        min(c[0], c[1], c[2]), max(c[0], c[1], c[2])))

# Sort by long side
SORT_LSIDE = lambda cublist: sorted(
    cublist, reverse=True,  key=lambda c: (
        max(c[0], c[1], c[2]), min(c[0], c[1], c[2])))

# Sort by side ratio
SORT_RATIO = lambda cublist: sorted(
    cublist, reverse=True, key=lambda c: (c[0]/c[1], c[0]/c[2], c[1]/c[2]))

# Unsorted
SORT_NONE = lambda cublist: list(cublist)


class BinFactory(object):

    def __init__(
            self, width, height, depth, count, pack_algo, *args, **kwargs):
        self._width = width
        self._height = height
        self._depth = depth
        self._count = count

        self._pack_algo = pack_algo
        self._algo_kwargs = kwargs
        self._algo_args = args
        # Reference bin used to calculate fitness
        self._ref_bin = None

    def _create_bin(self):
        return self._pack_algo(
            self._width, self._height, self._depth,
            *self._algo_args, **self._algo_kwargs)

    def is_empty(self):
        return self._count < 1

    def fitness(self, width, height, depth):
        if not self._ref_bin:
            self._ref_bin = self._create_bin()

        return self._ref_bin.fitness(width, height, depth)

    def fits_inside(self, width, height, depth):
        # Determine if cuboid widthxheightxdepth will fit into empty bin
        if not self._ref_bin:
            self._ref_bin = self._create_bin()

        return self._ref_bin._fits_volume(width, height, depth)

    def new_bin(self):
        if self._count > 0:
            self._count -= 1
            return self._create_bin()
        else:
            return None

    def __eq__(self, other):
        return self._width * self._height * self._depth == \
            other._width * other._height * other._depth

    def __lt__(self, other):
        return self._width * self._height * self._depth < \
            other._width * other._height * other._depth

    def __str__(self):
        return "Bin: {} {} {} {}".format(
            self._width, self._height, self._depth, self._count)


class PackerBNFMixin(object):
    """BNF (Bin Next Fit)

    Only one open bin at a time.  If the cuboid
    doesn't fit, close the current bin and go to the next.
    """

    def add_cub(self, width, height, depth, rid=None):
        while True:
            # if there are no open bins, try to open a new one
            if len(self._open_bins) == 0:
                # can we find an unopened bin that will hold this cub?
                new_bin = self._new_open_bin(width, height, depth, rid=rid)
                if new_bin is None:
                    return None

            # we have at least one open bin, so check if it can hold this cub
            cub = self._open_bins[0].add_cub(width, height, depth, rid=rid)
            if cub is not None:
                return cub

            # since the cub doesn't fit, close this bin and try again
            closed_bin = self._open_bins.popleft()
            self._closed_bins.append(closed_bin)


class PackerBFFMixin(object):
    """BFF (Bin First Fit)

    Pack cuboid in first bin it fits
    """

    def add_cub(self, width, height, depth, rid=None):
        # see if this cub will fit in any of the open bins
        for b in self._open_bins:
            cub = b.add_cub(width, height, depth, rid=rid)
            if cub is not None:
                return cub

        while True:
            # can we find an unopened bin that will hold this cub?
            new_bin = self._new_open_bin(width, height, depth, rid=rid)
            if new_bin is None:
                return None

            # _new_open_bin may return a bin that's too small,
            # so we have to double-check
            cub = new_bin.add_cub(width, height, depth, rid=rid)
            if cub is not None:
                return cub


class PackerBBFMixin(object):
    """BBF (Bin Best Fit)

    Pack Cuboid in bin that gives best fitness
    """

    # only create this getter once
    first_item = operator.itemgetter(0)

    def add_cub(self, width, height, depth, rid=None):

        # Try packing into open bins
        fit = ((b.fitness(width, height, depth),  b) for b in self._open_bins)
        fit = (b for b in fit if b[0] is not None)
        try:
            _, best_bin = min(fit, key=self.first_item)
            best_bin.add_cub(width, height, depth, rid)
            return True
        except ValueError:
            pass

        # Try packing into one of the empty bins
        while True:
            # can we find an unopened bin that will hold this cub?
            new_bin = self._new_open_bin(width, height, depth, rid=rid)
            if new_bin is None:
                return False

            # _new_open_bin may return a bin that's too small,
            # so we have to double-check
            if new_bin.add_cub(width, height, depth, rid):
                return True


class PackerOnline(object):
    """Cuboids are packed as soon are they are added"""

    def __init__(self, pack_algo=MaxCubsBssf, rotation=True):
        """Arguments:

            pack_algo (PackingAlgorithm): What packing algo to use
            rotation (bool): Enable/Disable cuboid rotation
        """
        self._rotation = rotation
        self._pack_algo = pack_algo
        self.reset()

    def __iter__(self):
        return itertools.chain(self._closed_bins, self._open_bins)

    def __len__(self):
        return len(self._closed_bins) + len(self._open_bins)

    def __getitem__(self, key):
        """Return bin in selected position. (excluding empty bins)"""
        if not isinstance(key, int):
            raise TypeError("Indices must be integers")

        size = len(self)  # avoid recalulations

        if key < 0:
            key += size

        if not 0 <= key < size:
            raise IndexError("Index out of range")

        if key < len(self._closed_bins):
            return self._closed_bins[key]
        else:
            return self._open_bins[key-len(self._closed_bins)]

    def _new_open_bin(self, width=None, height=None, depth=None, rid=None):
        """Extract the next empty bin and append it to open bins

        Returns:
            PackingAlgorithm: Initialized empty packing bin.
            None: No bin big enough for the cuboid was found
        """
        factories_to_delete = set()
        new_bin = None

        for key, binfac in self._empty_bins.items():

            # Only return the new bin if the cub fits.
            # If width, height or depth is None, caller doesn't know the size.
            if not binfac.fits_inside(width, height, depth):
                continue

            # Create bin and add to open_bins
            new_bin = binfac.new_bin()
            if new_bin is None:
                continue
            self._open_bins.append(new_bin)

            # If the factory was depleted mark for deletion
            if binfac.is_empty():
                factories_to_delete.add(key)

            break

        # Delete marked factories
        for f in factories_to_delete:
            del self._empty_bins[f]

        return new_bin

    def add_bin(self, width, height, depth, count=1, **kwargs):
        # accept the same parameters as PackingAlgorithm objects
        kwargs['rot'] = self._rotation
        bin_factory = BinFactory(width, height, depth, count,
                                 self._pack_algo, **kwargs)
        self._empty_bins[next(self._bin_count)] = bin_factory

    def cub_list(self):
        cuboids = []
        bin_count = 0

        for abin in self:
            for cub in abin:
                cuboids.append((bin_count, cub.x, cub.y, cub.z, cub.width,
                                cub.height, cub.depth, cub.rid))
            bin_count += 1

        return cuboids

    def bin_list(self):
        """Return a list of the dimmensions of the bins in use.

        Either they are closed or open but containing at least one cuboid
        """
        return [(b.width, b.height, b.depth) for b in self]

    def validate_packing(self):
        for b in self:
            b.validate_packing()

    def reset(self):
        # Bins fully packed and closed.
        self._closed_bins = collections.deque()

        # Bins ready to pack cuboids
        self._open_bins = collections.deque()

        # User provided bins not in current use
        # O(1) deletion of arbitrary elem
        self._empty_bins = collections.OrderedDict()
        self._bin_count = itertools.count()


class Packer(PackerOnline):
    """Cuboids aren't packed untils pack() is called"""

    def __init__(self, pack_algo=MaxCubsBssf, sort_algo=SORT_NONE,
                 rotation=True):
        super(Packer, self).__init__(pack_algo=pack_algo, rotation=rotation)

        self._sort_algo = sort_algo

        # User provided bins and Cuboids
        self._avail_bins = collections.deque()
        self._avail_cub = collections.deque()

        # Aux vars used during packing
        self._sorted_cub = []

    def add_bin(self, width, height, depth, count=1, **kwargs):
        self._avail_bins.append((width, height, depth, count, kwargs))

    def add_cub(self, width, height, depth, rid=None):
        self._avail_cub.append((width, height, depth, rid))

    def _is_everything_ready(self):
        return self._avail_cub and self._avail_bins

    def pack(self):

        self.reset()

        if not self._is_everything_ready():
            # maybe we should throw an error here?
            return

        # Add available bins to packer
        for b in self._avail_bins:
            width, height, depth, count, extra_kwargs = b
            super(Packer, self).add_bin(width, height, depth, count,
                                        **extra_kwargs)

        # If enabled sort cuboids
        self._sorted_cub = self._sort_algo(self._avail_cub)

        # Start packing
        for r in self._sorted_cub:
            super(Packer, self).add_cub(*r)


class PackerBNF(Packer, PackerBNFMixin):
    """BNF (Bin Next Fit)

    Only one open bin, if cuboid doesn't fit
    go to next bin and close current one.
    """
    pass


class PackerBFF(Packer, PackerBFFMixin):
    """BFF (Bin First Fit)

    Pack cuboid in first bin it fits
    """
    pass


class PackerBBF(Packer, PackerBBFMixin):
    """BBF (Bin Best Fit)

    Pack cuboid in bin that gives best fitness
    """
    pass


class PackerOnlineBNF(PackerOnline, PackerBNFMixin):
    """BNF Bin Next Fit Online variant"""
    pass


class PackerOnlineBFF(PackerOnline, PackerBFFMixin):
    """BFF Bin First Fit Online variant"""
    pass


class PackerOnlineBBF(PackerOnline, PackerBBFMixin):
    """BBF Bin Best Fit Online variant"""
    pass


class PackerGlobal(Packer, PackerBNFMixin):
    """GLOBAL: For each bin pack the cuboid with the best fitness."""
    first_item = operator.itemgetter(0)

    def __init__(self, pack_algo=MaxCubsBssf, rotation=True):
        super(PackerGlobal, self).__init__(
            pack_algo=pack_algo, sort_algo=SORT_NONE, rotation=rotation)

    def _find_best_fit(self, pbin):
        """Return best fitness cub from cubs packing _sorted_cub list

        Arguments:
            pbin (PackingAlgorithm): Packing bin

        Returns:
            key of the cuboid with best fitness
        """
        fit = ((pbin.fitness(c[0], c[1], c[2]), k) for k, c in
               self._sorted_cub.items())
        fit = (f for f in fit if f[0] is not None)
        try:
            _, cub = min(fit, key=self.first_item)
            return cub
        except ValueError:
            return None

    def _new_open_bin(self, remaining_cub):
        """Extract the next bin where at least one of the cuboids in rem

        Arguments:
            remaining_cub (dict): cuboids not placed yet

        Returns:
            PackingAlgorithm: Initialized empty packing bin.
            None: No bin big enough for the cuboid was found
        """
        factories_to_delete = set()
        new_bin = None

        for key, binfac in self._empty_bins.items():

            # Only return the new bin if at least one of the remaining
            # cuboids fit inside.
            a_cuboid_fits = False
            for _, cub in remaining_cub.items():
                if binfac.fits_inside(cub[0], cub[1], cub[2]):
                    a_cuboid_fits = True
                    break

            if not a_cuboid_fits:
                factories_to_delete.add(key)
                continue

            # Create bin and add to open_bins
            new_bin = binfac.new_bin()
            if new_bin is None:
                continue
            self._open_bins.append(new_bin)

            # If the factory was depleted mark for deletion
            if binfac.is_empty():
                factories_to_delete.add(key)

            break

        # Delete marked factories
        for f in factories_to_delete:
            del self._empty_bins[f]

        return new_bin

    def pack(self):

        self.reset()

        if not self._is_everything_ready():
            return

        # Add available bins to packer
        for b in self._avail_bins:
            width, height, depth, count, extra_kwargs = b
            super(Packer, self).add_bin(width, height, depth, count,
                                        **extra_kwargs)

        # Store cuboids into dict for fast deletion
        self._sorted_cub = collections.OrderedDict(
            enumerate(self._sort_algo(self._avail_cub)))

        # For each bin, pack the cuboids with lowest fitness until it is filled
        # or the cuboids exhausted, then open the next bin where at least one
        # cuboid will fit and repeat the process until there aren't more
        # cuboids or bins available.
        while len(self._sorted_cub) > 0:

            # Find one bin where at least one of the remaining cuboids fit
            pbin = self._new_open_bin(self._sorted_cub)
            if pbin is None:
                break

            # Pack as many cuboids as possible into the open bin
            while True:

                # Find 'fittest' cuboid
                best_cub_key = self._find_best_fit(pbin)
                if best_cub_key is None:
                    closed_bin = self._open_bins.popleft()
                    self._closed_bins.append(closed_bin)
                    # None of the remaining cuboids can be packed in this bin
                    break

                best_cub = self._sorted_cub[best_cub_key]
                del self._sorted_cub[best_cub_key]

                PackerBNFMixin.add_cub(self, *best_cub)


# Packer factory
class Enum(tuple):
    __getattr__ = tuple.index

PackingMode = Enum(["Online", "Offline"])
PackingBin = Enum(["BNF", "BFF", "BBF", "Global"])


def newPacker(mode=PackingMode.Offline,
              bin_algo=PackingBin.BBF,
              pack_algo=MaxCubsBssf,
              sort_algo=SORT_VOLUME,
              rotation=True):
    """Packer factory helper function

    Arguments:
        mode (PackingMode): Packing mode
            Online: Cuboids are packed as soon are they are added
            Offline: Cuboids aren't packed until pack() is called
        bin_algo (PackingBin): Bin selection heuristic
        pack_algo (PackingAlgorithm): Algorithm used
        rotation (boolean): Enable or disable cuboid rotation.

    Returns:
        Packer: Initialized packer instance.
    """
    packer_class = None

    # Online Mode
    if mode == PackingMode.Online:
        sort_algo = None
        if bin_algo == PackingBin.BNF:
            packer_class = PackerOnlineBNF
        elif bin_algo == PackingBin.BFF:
            packer_class = PackerOnlineBFF
        elif bin_algo == PackingBin.BBF:
            packer_class = PackerOnlineBBF
        else:
            raise AttributeError("Unsupported bin selection heuristic")

    # Offline Mode
    elif mode == PackingMode.Offline:
        if bin_algo == PackingBin.BNF:
            packer_class = PackerBNF
        elif bin_algo == PackingBin.BFF:
            packer_class = PackerBFF
        elif bin_algo == PackingBin.BBF:
            packer_class = PackerBBF
        elif bin_algo == PackingBin.Global:
            packer_class = PackerGlobal
            sort_algo = None
        else:
            raise AttributeError("Unsupported bin selection heuristic")

    else:
        raise AttributeError("Unknown packing mode.")

    if sort_algo:
        return packer_class(pack_algo=pack_algo, sort_algo=sort_algo,
                            rotation=rotation)
    else:
        return packer_class(pack_algo=pack_algo, rotation=rotation)
