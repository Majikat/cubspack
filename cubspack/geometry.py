# -*- coding: utf-8 -*-

from math import sqrt


class Point(object):

    __slots__ = ('x', 'y', 'z')

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y and self.z == other.z)

    def __repr__(self):
        return "P({}, {}, {})".format(self.x, self.y, self.z)

    def distance(self, point):
        """Calculate distance to another point"""
        return sqrt((self.x - point.x)**2 + (self.y - point.y)**2 + (
            self.z - point.z)**2)

    def distance_squared(self, point):
        return (self.x - point.x)**2 + (self.y - point.y)**2 + (
            self.z - point.z)**2


class Segment(object):

    __slots__ = ('start', 'end')

    def __init__(self, start, end):
        """Arguments:

            start (Point): Segment start point
            end (Point): Segment end point
        """
        assert(isinstance(start, Point) and isinstance(end, Point))
        self.start = start
        self.end = end

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            None
        return self.start == other.start and self.end == other.end

    def __repr__(self):
        return "S({}, {})".format(self.start, self.end)

    @property
    def length_squared(self):
        """Faster than length and useful for some comparisons"""
        return self.start.distance_squared(self.end)

    @property
    def length(self):
        return self.start.distance(self.end)

    @property
    def top(self):
        return max(self.start.y, self.end.y)

    @property
    def bottom(self):
        return min(self.start.y, self.end.y)

    @property
    def right(self):
        return max(self.start.x, self.end.x)

    @property
    def left(self):
        return min(self.start.x, self.end.x)

    @property
    def ineye(self):
        return max(self.start.z, self.end.z)

    @property
    def outeye(self):
        return min(self.start.z, self.end.z)


class HSegment(Segment):
    """Horizontal Segment"""

    def __init__(self, start, length):
        """Create an Horizontal segment given its left most end point and its length.

        Arguments:
            - start (Point): Starting Point
            - length (number): segment length
        """
        assert(isinstance(start, Point) and not isinstance(length, Point))
        super(HSegment, self).__init__(
            start, Point(start.x + length, start.y, start.z))

    @property
    def length(self):
        return self.end.x - self.start.x


class VSegment(Segment):
    """Vertical Segment"""

    def __init__(self, start, length):
        """Create a Vertical segment given its bottom most end point and its length.

        Arguments:
            - start (Point): Starting Point
            - length (number): segment length
        """
        assert(isinstance(start, Point) and not isinstance(length, Point))
        super(VSegment, self).__init__(
            start, Point(start.x, start.y + length, start.z))

    @property
    def length(self):
        return self.end.y - self.start.y


class DSegment(Segment):
    """In-Depth Segment"""

    def __init__(self, start, length):
        """Create an In-Depth segment given its bottom most end point and its length.

        Arguments:
            - start (Point): Starting Point
            - length (number): segment length
        """
        assert(isinstance(start, Point) and not isinstance(length, Point))
        super(VSegment, self).__init__(
            start, Point(start.x, start.y, start.z + length))

    @property
    def length(self):
        return self.end.z - self.start.z


class Cuboid(object):
    """Basic cuboid primitive class.

    x, y, z-> Lower right corner coordinates
    width -
    height -
    depth -
    """
    __slots__ = ('width', 'height', 'depth', 'x', 'y', 'z', 'rid')

    def __init__(self, x, y, z, width, height, depth, rid=None):
        """Initiating the Cuboid

        Args:
            x (int, float):
            y (int, float):
            z (int, float):
            width (int, float):
            height (int, float):
            depth (int, float):
            rid (identifier object):
        """
        assert(height >= 0 and width >= 0 and depth >= 0)

        self.width = width
        self.height = height
        self.depth = depth
        self.x = x
        self.y = y
        self.z = z
        self.rid = rid

    @property
    def bottom(self):
        """Cuboid bottom edge y coordinate"""
        return self.y

    @property
    def top(self):
        """Cuboid top edge y coordiante"""
        return self.y + self.height

    @property
    def left(self):
        """Cuboid left edge x coordinate"""
        return self.x

    @property
    def right(self):
        """Cuboid right edge x coordinate"""
        return self.x + self.width

    @property
    def outeye(self):
        """Cuboid farther from eye edge z coordinate"""
        return self.z

    @property
    def ineye(self):
        """Cuboid nearer from eye edge z coordinate"""
        return self.z + self.depth

    @property
    def corner_top_l(self):
        return Point(self.left, self.top, self.outeye)

    @property
    def corner_top_r(self):
        return Point(self.right, self.top, self.outeye)

    @property
    def corner_bot_r(self):
        return Point(self.right, self.bottom, self.outeye)

    @property
    def corner_bot_l(self):
        return Point(self.left, self.bottom, self.outeye)

    @property
    def corner_top_l_out(self):
        return Point(self.left, self.top, self.ineye)

    @property
    def corner_top_r_out(self):
        return Point(self.right, self.top, self.ineye)

    @property
    def corner_bot_r_out(self):
        return Point(self.right, self.bottom, self.ineye)

    @property
    def corner_bot_l_out(self):
        return Point(self.left, self.bottom, self.ineye)

    def __lt__(self, other):
        """Compare cuboids by volume (used for sorting)"""
        return self.volume() < other.volume()

    def __eq__(self, other):
        """Equal cuboids have same properties."""
        if not isinstance(other, self.__class__):
            return False

        return (self.width == other.width and
                self.height == other.height and
                self.depth == other.depth and
                self.x == other.x and
                self.y == other.y and
                self.z == other.z)

    def __hash__(self):
        return hash(
            (self.x, self.y, self.z, self.width, self.height, self.depth))

    def __iter__(self):
        """Iterate through cuboid corners"""
        yield self.corner_top_l
        yield self.corner_top_r
        yield self.corner_bot_r
        yield self.corner_bot_l
        yield self.corner_top_l_out
        yield self.corner_top_r_out
        yield self.corner_bot_r_out
        yield self.corner_bot_l_out

    def __repr__(self):
        return "R({}, {}, {}, {}, {}, {})".format(
            self.x, self.y, self.z, self.width, self.height, self.depth)

    def volume(self):
        """Cuboid volume"""
        return self.width * self.height * self.depth

    def move(self, x, y, z):
        """Move Cuboid to x,y,z coordinates

        Arguments:
            x (int, float): X coordinate
            y (int, float): Y coordinate
            z (int, float): Z coordinate
        """
        self.x = x
        self.y = y
        self.z = z

    def contains(self, cub):
        """Tests if another cuboid is contained by this one

        Arguments:
            cub (Cuboid): The other cuboiud

        Returns:
            bool: True if it is inside this one, False otherwise
        """
        return (cub.y >= self.y and
                cub.x >= self.x and
                cub.z >= self.z and
                cub.y + cub.height <= self.y + self.height and
                cub.x + cub.width <= self.x + self.width and
                cub.z + cub.depth <= self.z + self.depth)

    def intersects(self, cub, edges=False):
        """Detect intersections between this cuboid and cub.

        Args:
            cub (Cuboid): Cuboid to test for intersections.
            edges (bool): Accept edge touching cuboids as intersects or not

        Returns:
            bool: True if the cuboids intersect, False otherwise
        """
        # Not even touching
        if (self.bottom > cub.top or
            self.top < cub.bottom or
            self.left > cub.right or
            self.right < cub.left or
            self.outeye > cub.ineye or
                self.ineye < cub.outeye):
            return False

        # Discard edge intersects
        if not edges:
            if (self.bottom == cub.top or
                self.top == cub.bottom or
                self.left == cub.right or
                self.right == cub.left or
                self.outeye == cub.ineye or
                    self.ineye == cub.outeye):
                return False

        # Discard corner intersects
        if (self.left == cub.right and self.bottom == cub.top and
                self.outeye == cub.ineye or
            self.left == cub.right and cub.bottom == self.top and
                self.outeye == cub.ineye or
            self.left == cub.right and self.bottom == cub.top and
                cub.outeye == self.ineye or
            self.left == cub.right and cub.bottom == self.top and
                cub.outeye == self.ineye or
            cub.left == self.right and self.bottom == cub.top and
                self.outeye == cub.ineye or
            cub.left == self.right and cub.bottom == self.top and
                self.outeye == cub.ineye or
            cub.left == self.right and self.bottom == cub.top and
                cub.outeye == self.ineye or
            cub.left == self.right and cub.bottom == self.top and
                cub.outeye == self.ineye):
            return False

        return True

    def intersection(self, cub, edges=False):
        """Returns the cuboid resulting of the intersection of this and cub

        If the cuboids are only touching by their edges, and the
        argument 'edges' is True the cuboid returned will have a volume of 0.
        Returns None if there is no intersection.

        Arguments:
             cub (Cuboid): The other cuboid.
             edges (bool): If true, touching edges are considered an
             intersection, and a cuboid of 0 height or width or depth will be
             returned

        Returns:
            Cuboid: Intersection.
            None: There was no intersection.
        """
        if not self.intersects(cub, edges=edges):
            return None

        bottom = max(self.bottom, cub.bottom)
        left = max(self.left, cub.left)
        top = min(self.top, cub.top)
        right = min(self.right, cub.right)
        outeye = max(self.outeye, cub.outeye)
        ineye = min(self.ineye, cub.ineye)

        return Cuboid(
            left, bottom, outeye,
            right - left, top - bottom, ineye - outeye)

    def join(self, other):
        """Try to join a cuboid to this one.

        If the result is also a cuboid and the operation is successful then
        this cuboid is modified to the union.

        Arguments:
            other (Cuboid): Cuboid to join

        Returns:
            bool: True when successfully joined, False otherwise
        """
        if self.contains(other):
            return True

        if other.contains(self):
            self.x = other.x
            self.y = other.y
            self.z = other.z
            self.width = other.width
            self.height = other.height
            self.depth = other.depth
            return True

        if not self.intersects(other, edges=True):
            return False

        # Other cuboid is Up/Down from this
        if self.left == other.left and self.width == other.width and \
                self.outeye == other.outeye and self.depth == self.depth:
            y_min = min(self.bottom, other.bottom)
            y_max = max(self.top, other.top)
            self.y = y_min
            self.height = y_max - y_min
            return True

        # Other cuboid is Right/Left from this
        if self.bottom == other.bottom and self.height == other.height and \
                self.outeye == other.outeye and self.depth == self.depth:
            x_min = min(self.left, other.left)
            x_max = max(self.right, other.right)
            self.x = x_min
            self.width = x_max - x_min
            return True

        # Other cuboid is Right/Left from this
        if self.bottom == other.bottom and self.height == other.height and \
                self.left == other.left and self.width == other.width:
            z_min = min(self.outeye, other.outeye)
            z_max = max(self.ineye, other.ineye)
            self.z = z_min
            self.depth = z_max - z_min
            return True

        return False
