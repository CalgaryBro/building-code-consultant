"""
Geometry Analyzer Module

Analyzes extracted vector geometry from building drawings using Shapely.
Provides room detection, area calculations, spatial queries, and setback analysis.
"""

from shapely.geometry import (
    Polygon, Point, LineString, MultiPolygon, box,
    MultiLineString, GeometryCollection
)
from shapely.ops import unary_union, polygonize, linemerge
from shapely.validation import make_valid
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RoomType(Enum):
    """Types of rooms that can be identified in building drawings."""
    UNKNOWN = "unknown"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    KITCHEN = "kitchen"
    LIVING_ROOM = "living_room"
    DINING_ROOM = "dining_room"
    HALLWAY = "hallway"
    CLOSET = "closet"
    GARAGE = "garage"
    BASEMENT = "basement"
    UTILITY = "utility"
    OFFICE = "office"
    STORAGE = "storage"


@dataclass
class Room:
    """
    Represents a room detected from drawing geometry.

    Attributes:
        name: Room name/label if identified
        room_type: Type of room if identified
        polygon: Shapely polygon representing the room boundary
        area_drawing_units: Area in drawing units (e.g., mm^2)
        area_m2: Area in square meters
        doors: List of door locations (Points)
        windows: List of window locations (Points)
        label_position: Position where room label was found
    """
    name: str
    polygon: Polygon
    area_drawing_units: float
    area_m2: float
    room_type: RoomType = RoomType.UNKNOWN
    doors: List[Point] = field(default_factory=list)
    windows: List[Point] = field(default_factory=list)
    label_position: Optional[Point] = None
    floor_number: int = 0

    @property
    def centroid(self) -> Point:
        """Return the centroid of the room."""
        return self.polygon.centroid

    @property
    def perimeter(self) -> float:
        """Return the perimeter of the room in drawing units."""
        return self.polygon.length

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return bounding box as (minx, miny, maxx, maxy)."""
        return self.polygon.bounds


@dataclass
class Dimension:
    """
    Represents a dimension measurement from a drawing.

    Attributes:
        value: Numeric value
        unit: Unit of measurement
        start_point: Start point of dimension line
        end_point: End point of dimension line
        text_position: Position of dimension text
        orientation: 'horizontal', 'vertical', or 'diagonal'
    """
    value: float
    unit: str
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    text_position: Optional[Tuple[float, float]] = None
    orientation: str = "unknown"

    @property
    def length_drawing_units(self) -> float:
        """Calculate the length of the dimension line in drawing units."""
        dx = self.end_point[0] - self.start_point[0]
        dy = self.end_point[1] - self.start_point[1]
        return (dx**2 + dy**2)**0.5


@dataclass
class WallSegment:
    """Represents a wall segment."""
    line: LineString
    thickness: float = 0.0
    material: str = "unknown"
    is_exterior: bool = False


@dataclass
class SetbackAnalysis:
    """Results of setback analysis."""
    compliant: bool
    violations: List[str] = field(default_factory=list)
    front_distance: Optional[float] = None
    rear_distance: Optional[float] = None
    left_side_distance: Optional[float] = None
    right_side_distance: Optional[float] = None


class GeometryAnalyzer:
    """
    Analyzes building geometry extracted from drawings.

    Uses Shapely for geometric operations including:
    - Room polygon detection from wall lines
    - Area calculations with unit conversion
    - Spatial queries (containment, intersection)
    - Setback analysis using buffer operations
    - Room connectivity analysis

    Example:
        >>> analyzer = GeometryAnalyzer(scale_factor=0.001)  # mm to m
        >>> rooms = analyzer.detect_rooms_from_lines(wall_lines)
        >>> for room in rooms:
        ...     print(f"{room.name}: {room.area_m2:.2f} m^2")
    """

    # NBC minimum room sizes in square meters
    NBC_MIN_ROOM_SIZES = {
        RoomType.BEDROOM: 9.29,      # 100 sq ft
        RoomType.LIVING_ROOM: 13.0,   # ~140 sq ft
        RoomType.KITCHEN: 4.65,       # 50 sq ft
        RoomType.BATHROOM: 2.32,      # 25 sq ft
        RoomType.HALLWAY: 1.0,
    }

    # NBC minimum dimensions in meters
    NBC_MIN_DIMENSIONS = {
        "room_width": 2.44,           # 8 ft minimum for habitable rooms
        "hallway_width": 0.86,        # ~34 inches
        "door_width": 0.81,           # 32 inches clear
        "stair_width": 0.86,          # 34 inches
        "ceiling_height": 2.3,        # ~7.5 ft
    }

    def __init__(self, scale_factor: float = 1.0, unit: str = "mm"):
        """
        Initialize the geometry analyzer.

        Args:
            scale_factor: Factor to convert drawing units to meters.
                         e.g., 0.001 for mm to m, 0.0254 for inches to m
            unit: Unit of the drawing ('mm', 'cm', 'm', 'in', 'ft')
        """
        self.scale_factor = scale_factor
        self.unit = unit
        self.rooms: List[Room] = []
        self.walls: List[WallSegment] = []
        self._tolerance = 1.0  # Tolerance for geometry operations

        # Set scale factor from unit if not explicitly provided
        if scale_factor == 1.0:
            self._set_scale_from_unit(unit)

    def _set_scale_from_unit(self, unit: str) -> None:
        """Set scale factor based on unit."""
        unit_to_meter = {
            "mm": 0.001,
            "cm": 0.01,
            "m": 1.0,
            "in": 0.0254,
            "ft": 0.3048,
        }
        self.scale_factor = unit_to_meter.get(unit.lower(), 1.0)

    def set_tolerance(self, tolerance: float) -> None:
        """Set tolerance for geometry operations."""
        self._tolerance = tolerance

    def create_polygon_from_coords(
        self,
        coords: List[Tuple[float, float]]
    ) -> Optional[Polygon]:
        """
        Create a valid Shapely polygon from coordinates.

        Args:
            coords: List of (x, y) coordinate tuples

        Returns:
            Valid Polygon or None if cannot be created
        """
        if len(coords) < 3:
            return None

        try:
            # Ensure polygon is closed
            if coords[0] != coords[-1]:
                coords = coords + [coords[0]]

            poly = Polygon(coords)

            if not poly.is_valid:
                poly = make_valid(poly)
                if isinstance(poly, (MultiPolygon, GeometryCollection)):
                    # Extract largest polygon from collection
                    poly = max(poly.geoms, key=lambda p: p.area if hasattr(p, 'area') else 0)

            if poly.is_valid and poly.area > 0:
                return poly

        except Exception as e:
            logger.warning(f"Failed to create polygon: {e}")

        return None

    def detect_rooms_from_lines(
        self,
        lines: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        min_area: float = 1000.0
    ) -> List[Room]:
        """
        Detect rooms by finding closed polygons from wall lines.

        Uses Shapely's polygonize to find enclosed areas from lines.

        Args:
            lines: List of line segments as ((x1, y1), (x2, y2))
            min_area: Minimum area in drawing units to be considered a room

        Returns:
            List of detected Room objects
        """
        if not lines:
            return []

        # Convert to LineStrings
        line_strings = []
        for line in lines:
            if len(line) >= 2:
                try:
                    ls = LineString([line[0], line[1]])
                    if ls.is_valid and ls.length > 0:
                        line_strings.append(ls)
                except Exception:
                    continue

        if not line_strings:
            return []

        # Merge connected lines
        try:
            merged = linemerge(line_strings)
            if isinstance(merged, LineString):
                merged = MultiLineString([merged])
        except Exception:
            merged = MultiLineString(line_strings)

        # Find enclosed polygons
        try:
            polygons = list(polygonize(merged))
        except Exception as e:
            logger.warning(f"Polygonize failed: {e}")
            return []

        # Create Room objects from valid polygons
        rooms = []
        for i, poly in enumerate(polygons):
            if not poly.is_valid:
                poly = make_valid(poly)

            if poly.area < min_area:
                continue

            area_m2 = self.calculate_area_m2(poly)

            room = Room(
                name=f"Room_{i+1}",
                polygon=poly,
                area_drawing_units=poly.area,
                area_m2=area_m2
            )
            rooms.append(room)

        self.rooms = rooms
        logger.info(f"Detected {len(rooms)} rooms from {len(lines)} lines")
        return rooms

    def detect_rooms_from_vectors(
        self,
        vectors: List[Any],  # VectorElement from pdf_extractor
        min_area: float = 1000.0
    ) -> List[Room]:
        """
        Detect rooms from VectorElement objects.

        Args:
            vectors: List of VectorElement objects
            min_area: Minimum area in drawing units

        Returns:
            List of detected Room objects
        """
        # Extract line coordinates from vectors
        lines = []
        for vec in vectors:
            if hasattr(vec, 'type') and str(vec.type) in ['VectorType.LINE', 'line']:
                if hasattr(vec, 'coords') and len(vec.coords) >= 2:
                    lines.append((vec.coords[0], vec.coords[1]))
            elif hasattr(vec, 'type') and str(vec.type) in ['VectorType.RECTANGLE', 'rect']:
                # Convert rectangle to 4 lines
                if hasattr(vec, 'coords') and len(vec.coords) >= 4:
                    coords = vec.coords
                    lines.extend([
                        (coords[0], coords[1]),
                        (coords[1], coords[2]),
                        (coords[2], coords[3]),
                        (coords[3], coords[0])
                    ])

        return self.detect_rooms_from_lines(lines, min_area)

    def calculate_area_m2(self, polygon: Polygon) -> float:
        """
        Calculate area in square meters.

        Args:
            polygon: Shapely Polygon

        Returns:
            Area in square meters
        """
        return polygon.area * (self.scale_factor ** 2)

    def calculate_length_m(self, line: LineString) -> float:
        """
        Calculate length in meters.

        Args:
            line: Shapely LineString

        Returns:
            Length in meters
        """
        return line.length * self.scale_factor

    def check_minimum_room_size(
        self,
        room: Room,
        room_type: Optional[RoomType] = None
    ) -> Dict[str, Any]:
        """
        Check if room meets minimum area requirements per NBC.

        Args:
            room: Room object to check
            room_type: Type of room (uses room.room_type if None)

        Returns:
            Dictionary with compliance status and details
        """
        rtype = room_type or room.room_type
        min_area = self.NBC_MIN_ROOM_SIZES.get(rtype, 0)

        return {
            "compliant": room.area_m2 >= min_area,
            "room_name": room.name,
            "room_type": rtype.value,
            "actual_area_m2": room.area_m2,
            "minimum_area_m2": min_area,
            "difference_m2": room.area_m2 - min_area
        }

    def check_all_rooms_minimum_size(self) -> List[Dict[str, Any]]:
        """
        Check all detected rooms for minimum size compliance.

        Returns:
            List of compliance check results
        """
        return [self.check_minimum_room_size(room) for room in self.rooms]

    def analyze_setbacks(
        self,
        building: Polygon,
        lot: Polygon,
        front_setback: float,
        rear_setback: float,
        side_setback: float,
        lot_orientation: str = "north"
    ) -> SetbackAnalysis:
        """
        Analyze if building meets setback requirements.

        Creates buffer zones from lot boundaries and checks if building
        is contained within the buildable area.

        Args:
            building: Building footprint polygon
            lot: Lot boundary polygon
            front_setback: Required front setback in meters
            rear_setback: Required rear setback in meters
            side_setback: Required side setback in meters
            lot_orientation: Direction lot faces ('north', 'south', 'east', 'west')

        Returns:
            SetbackAnalysis with compliance status and violations
        """
        violations = []
        result = SetbackAnalysis(compliant=True)

        # Convert setbacks to drawing units
        front_units = front_setback / self.scale_factor
        rear_units = rear_setback / self.scale_factor
        side_units = side_setback / self.scale_factor

        # Get lot bounds
        minx, miny, maxx, maxy = lot.bounds

        # Create setback zones based on orientation
        # This is simplified - real implementation would need to identify lot sides
        if lot_orientation in ["north", "south"]:
            front_zone = box(minx, miny, maxx, miny + front_units)
            rear_zone = box(minx, maxy - rear_units, maxx, maxy)
            left_zone = box(minx, miny, minx + side_units, maxy)
            right_zone = box(maxx - side_units, miny, maxx, maxy)
        else:
            front_zone = box(minx, miny, minx + front_units, maxy)
            rear_zone = box(maxx - rear_units, miny, maxx, maxy)
            left_zone = box(minx, miny, maxx, miny + side_units)
            right_zone = box(minx, maxy - side_units, maxx, maxy)

        # Check for violations
        if building.intersects(front_zone):
            violations.append("front_setback")
            # Calculate actual distance to front
            result.front_distance = building.distance(
                LineString([(minx, miny), (maxx, miny)])
            ) * self.scale_factor

        if building.intersects(rear_zone):
            violations.append("rear_setback")
            result.rear_distance = building.distance(
                LineString([(minx, maxy), (maxx, maxy)])
            ) * self.scale_factor

        if building.intersects(left_zone):
            violations.append("left_side_setback")
            result.left_side_distance = building.distance(
                LineString([(minx, miny), (minx, maxy)])
            ) * self.scale_factor

        if building.intersects(right_zone):
            violations.append("right_side_setback")
            result.right_side_distance = building.distance(
                LineString([(maxx, miny), (maxx, maxy)])
            ) * self.scale_factor

        result.compliant = len(violations) == 0
        result.violations = violations
        return result

    def find_rooms_containing_point(
        self,
        point: Tuple[float, float]
    ) -> List[Room]:
        """
        Find all rooms that contain a given point.

        Args:
            point: (x, y) coordinate

        Returns:
            List of rooms containing the point
        """
        p = Point(point)
        return [room for room in self.rooms if room.polygon.contains(p)]

    def find_adjacent_rooms(self, room: Room) -> List[Room]:
        """
        Find rooms that share a wall with the given room.

        Args:
            room: Room to find adjacencies for

        Returns:
            List of adjacent rooms
        """
        adjacent = []
        for other in self.rooms:
            if other.name == room.name:
                continue
            if room.polygon.touches(other.polygon) or room.polygon.intersects(other.polygon):
                # Check if they share a wall (not just a point)
                intersection = room.polygon.intersection(other.polygon)
                if intersection.length > self._tolerance:
                    adjacent.append(other)
        return adjacent

    def calculate_building_coverage(
        self,
        building: Polygon,
        lot: Polygon
    ) -> Dict[str, float]:
        """
        Calculate building coverage ratio.

        Args:
            building: Building footprint polygon
            lot: Lot boundary polygon

        Returns:
            Dictionary with coverage statistics
        """
        building_area = self.calculate_area_m2(building)
        lot_area = self.calculate_area_m2(lot)
        coverage_ratio = building_area / lot_area if lot_area > 0 else 0

        return {
            "building_area_m2": building_area,
            "lot_area_m2": lot_area,
            "coverage_ratio": coverage_ratio,
            "coverage_percent": coverage_ratio * 100
        }

    def merge_touching_polygons(
        self,
        polygons: List[Polygon]
    ) -> List[Polygon]:
        """
        Merge polygons that touch or overlap.

        Args:
            polygons: List of polygons to merge

        Returns:
            List of merged polygons
        """
        if not polygons:
            return []

        result = unary_union(polygons)

        if isinstance(result, Polygon):
            return [result]
        elif isinstance(result, MultiPolygon):
            return list(result.geoms)
        else:
            return []

    def simplify_polygon(
        self,
        polygon: Polygon,
        tolerance: float = 1.0
    ) -> Polygon:
        """
        Simplify a polygon by removing small details.

        Useful for cleaning up noisy extraction results.

        Args:
            polygon: Polygon to simplify
            tolerance: Simplification tolerance

        Returns:
            Simplified polygon
        """
        simplified = polygon.simplify(tolerance, preserve_topology=True)
        return simplified if simplified.is_valid else polygon

    def extract_wall_segments(
        self,
        lines: List[Tuple[Tuple[float, float], Tuple[float, float]]],
        thickness_threshold: float = 5.0
    ) -> List[WallSegment]:
        """
        Extract wall segments from lines, attempting to identify wall thickness.

        Args:
            lines: List of line segments
            thickness_threshold: Maximum distance to consider parallel lines as wall edges

        Returns:
            List of WallSegment objects
        """
        walls = []

        line_strings = [LineString([l[0], l[1]]) for l in lines if len(l) >= 2]

        # Group parallel lines
        for i, ls1 in enumerate(line_strings):
            for ls2 in line_strings[i+1:]:
                # Check if parallel and close
                if ls1.distance(ls2) < thickness_threshold:
                    # Check if parallel (similar angles)
                    c1 = list(ls1.coords)
                    c2 = list(ls2.coords)

                    if len(c1) >= 2 and len(c2) >= 2:
                        dx1 = c1[1][0] - c1[0][0]
                        dy1 = c1[1][1] - c1[0][1]
                        dx2 = c2[1][0] - c2[0][0]
                        dy2 = c2[1][1] - c2[0][1]

                        # Check angle similarity (dot product of normalized vectors)
                        len1 = (dx1**2 + dy1**2)**0.5
                        len2 = (dx2**2 + dy2**2)**0.5

                        if len1 > 0 and len2 > 0:
                            dot = abs(dx1*dx2 + dy1*dy2) / (len1 * len2)
                            if dot > 0.95:  # Nearly parallel
                                # Create wall segment at midpoint
                                mid_line = LineString([
                                    ((c1[0][0] + c2[0][0])/2, (c1[0][1] + c2[0][1])/2),
                                    ((c1[1][0] + c2[1][0])/2, (c1[1][1] + c2[1][1])/2)
                                ])
                                walls.append(WallSegment(
                                    line=mid_line,
                                    thickness=ls1.distance(ls2)
                                ))

        self.walls = walls
        return walls

    def detect_openings(
        self,
        room: Room,
        wall_lines: List[LineString],
        opening_min_width: float = 500.0,  # mm
        opening_max_width: float = 2500.0   # mm
    ) -> Dict[str, List[Point]]:
        """
        Detect door and window openings in room walls.

        Looks for gaps in wall lines that could be doors or windows.

        Args:
            room: Room to analyze
            wall_lines: Wall line segments
            opening_min_width: Minimum opening width in drawing units
            opening_max_width: Maximum opening width in drawing units

        Returns:
            Dictionary with 'doors' and 'windows' lists of Points
        """
        openings = {"doors": [], "windows": []}

        # Get room boundary as LineString
        boundary = room.polygon.exterior

        # Find gaps along the boundary
        # This is a simplified implementation
        boundary_coords = list(boundary.coords)

        for i in range(len(boundary_coords) - 1):
            p1 = boundary_coords[i]
            p2 = boundary_coords[i + 1]

            segment_length = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5

            # Check if this segment has any gaps
            segment_line = LineString([p1, p2])

            for wall_line in wall_lines:
                intersection = segment_line.intersection(wall_line)
                if not intersection.is_empty:
                    # Check for gaps in the intersection
                    # Gap detection would require more sophisticated analysis
                    pass

        return openings

    def calculate_room_dimensions(self, room: Room) -> Dict[str, float]:
        """
        Calculate room dimensions (length, width).

        Uses minimum bounding rectangle for regular rooms.

        Args:
            room: Room to measure

        Returns:
            Dictionary with dimension measurements in meters
        """
        minx, miny, maxx, maxy = room.polygon.bounds

        width = (maxx - minx) * self.scale_factor
        length = (maxy - miny) * self.scale_factor

        # Ensure width <= length convention
        if width > length:
            width, length = length, width

        return {
            "length_m": length,
            "width_m": width,
            "aspect_ratio": length / width if width > 0 else 0
        }

    def check_room_dimensions(
        self,
        room: Room,
        min_width: float = 2.44  # 8 ft in meters
    ) -> Dict[str, Any]:
        """
        Check if room meets minimum dimension requirements.

        Args:
            room: Room to check
            min_width: Minimum room width in meters

        Returns:
            Compliance check result
        """
        dims = self.calculate_room_dimensions(room)

        return {
            "compliant": dims["width_m"] >= min_width,
            "room_name": room.name,
            "width_m": dims["width_m"],
            "length_m": dims["length_m"],
            "min_width_required_m": min_width,
            "deficit_m": max(0, min_width - dims["width_m"])
        }

    def export_to_geojson(
        self,
        rooms: Optional[List[Room]] = None
    ) -> Dict[str, Any]:
        """
        Export rooms to GeoJSON format.

        Args:
            rooms: List of rooms to export (uses self.rooms if None)

        Returns:
            GeoJSON FeatureCollection dictionary
        """
        rooms = rooms or self.rooms

        features = []
        for room in rooms:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [list(room.polygon.exterior.coords)]
                },
                "properties": {
                    "name": room.name,
                    "room_type": room.room_type.value,
                    "area_m2": room.area_m2,
                    "area_drawing_units": room.area_drawing_units
                }
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features
        }
