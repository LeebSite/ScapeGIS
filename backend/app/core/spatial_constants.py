"""
Spatial Semantic Categories — shared constants.

All valid category/subcategory combinations are defined here.
This prevents typos and gives a single source of truth for
the semantic layer system.
"""
from enum import Enum


class SemanticCategory(str, Enum):
    TRANSPORTATION = "transportation"
    PUBLIC_FACILITY = "public_facility"
    RELIGIOUS = "religious"
    COMMERCIAL = "commercial"
    TRANSPORTATION_INFRA = "transportation_infrastructure"
    ADMINISTRATIVE = "administrative"


class SemanticSubcategory(str, Enum):
    # Transportation
    ARTERIAL_ROAD = "arterial_road"
    COLLECTOR_ROAD = "collector_road"
    LOCAL_ROAD = "local_road"
    OTHER_ROAD = "other_road"

    # Public Facility
    HOSPITAL = "hospital"
    PUSKESMAS = "puskesmas"
    POLICE_STATION = "police_station"
    MILITARY = "military"
    GOVERNMENT_OFFICE = "government_office"
    DISTRICT_OFFICE = "district_office"
    VILLAGE_OFFICE = "village_office"
    CITY_HALL = "city_hall"
    GOVERNOR_OFFICE = "governor_office"

    # Religious
    MOSQUE = "mosque"
    CHURCH = "church"
    VIHARA = "vihara"
    OTHER_WORSHIP = "other_place_of_worship"

    # Commercial
    COMMERCIAL_AREA = "commercial_area"

    # Transportation Infrastructure
    PORT = "port"

    # Administrative
    ADMIN_BOUNDARY = "administrative_boundary"
