"""
Creates a grid of flood zone polygons covering Bangladesh.
Each cell becomes one zone the AI model will score.
Run with: python scripts/create_zones.py
"""
import os
import sys
import django
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.gis.geos import Polygon, MultiPolygon
from flood_zones.models import FloodZone, District

# Bangladesh approximate bounding box
BBOX = {
    'min_lon': 88.0,
    'max_lon': 92.7,
    'min_lat': 20.5,
    'max_lat': 26.7,
}

# Grid cell size in degrees
# 0.1° ≈ 11km — gives ~2900 zones covering Bangladesh
CELL_SIZE = 0.1


def make_cell_polygon(min_lon, min_lat, size):
    return Polygon((
        (min_lon,        min_lat),
        (min_lon + size, min_lat),
        (min_lon + size, min_lat + size),
        (min_lon,        min_lat + size),
        (min_lon,        min_lat),
    ), srid=4326)


def get_district_name(centroid):
    """Find which district this centroid falls in."""
    district = District.objects.filter(
        geometry__contains=centroid
    ).first()
    return district.name if district else 'Bangladesh'


def run():
    print("Creating flood zone grid over Bangladesh...")
    FloodZone.objects.all().delete()

    lons = np.arange(BBOX['min_lon'], BBOX['max_lon'], CELL_SIZE)
    lats = np.arange(BBOX['min_lat'], BBOX['max_lat'], CELL_SIZE)

    zones = []
    count = 0

    for lon in lons:
        for lat in lats:
            cell = make_cell_polygon(lon, lat, CELL_SIZE)

            # Only keep cells that intersect Bangladesh
            # (rough filter — if District data loaded, use it)
            if District.objects.exists():
                if not District.objects.filter(
                    geometry__intersects=cell
                ).exists():
                    continue

            count += 1
            # Name the zone by its centroid coordinates
            name = f"Zone {lat:.1f}N {lon:.1f}E"

            zones.append(FloodZone(
                name     = name,
                geometry = cell,
            ))

            # Bulk create every 500 zones
            if len(zones) >= 500:
                FloodZone.objects.bulk_create(zones)
                zones = []
                print(f"  Created {count} zones so far...")

    if zones:
        FloodZone.objects.bulk_create(zones)

    total = FloodZone.objects.count()
    print(f"\nDone. {total} flood zones created.")
    print(f"Grid: {len(lons)} columns × {len(lats)} rows")
    print(f"Cell size: {CELL_SIZE}° ≈ {CELL_SIZE * 111:.0f}km per side")


if __name__ == '__main__':
    run()