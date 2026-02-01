from __future__ import annotations

from enum import Enum


class MapSource(Enum):
    """Enumeration of different map data sources."""
    
    TRAVELLERMAP = "travellermap.com"
    THRIGGLE = "https://thriggle.netlify.app/traveller/subsector#"