"""
Spatial feature extraction pipeline.
For each flood zone polygon, extracts:
  - average elevation
  - average slope
  - average monsoon rainfall
  - distance to nearest river
  - land use code

Run with: python scripts/extract_features.py
"""
import os
import sys
import django
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Avg, Count
from flood_zones.models import (
    FloodZone, ElevationPoint, RainfallRecord,
    RiverNetwork, District
)


def extract_elevation_features(zone):
    """
    Find all elevation points inside this zone polygon
    and compute average elevation and slope.
    """
    points = ElevationPoint.objects.filter(
        location__within=zone.geometry
    )
    if not points.exists():
        # fallback — use nearest points within 5km
        points = ElevationPoint.objects.filter(
            location__distance_lte=(zone.geometry.centroid, D(km=5))
        )
    stats = points.aggregate(
        avg_elev=Avg('elevation_m'),
        avg_slope=Avg('slope_degrees'),
    )
    return (
        stats['avg_elev'] or 0.0,
        stats['avg_slope'] or 0.0,
    )


def extract_rainfall_features(zone):
    """
    Find rainfall stations within 50km of zone centroid.
    Return average monsoon rainfall (June-September).
    """
    centroid = zone.geometry.centroid
    monsoon_months = [6, 7, 8, 9]

    records = RainfallRecord.objects.filter(
        location__distance_lte=(centroid, D(km=50)),
        month__in=monsoon_months,
    )
    if not records.exists():
        # fallback — take all stations, nearest year
        records = RainfallRecord.objects.filter(
            month__in=monsoon_months,
        )
    stats = records.aggregate(avg_rain=Avg('rainfall_mm'))
    return stats['avg_rain'] or 0.0


def extract_river_distance(zone):
    """
    Find the distance in metres from the zone centroid
    to the nearest river in RiverNetwork.
    Returns None if no river data loaded yet.
    """
    centroid = zone.geometry.centroid
    if not RiverNetwork.objects.exists():
        return None

    nearest = RiverNetwork.objects.annotate(
        dist=Distance('geometry', centroid)
    ).order_by('dist').first()

    if nearest:
        return nearest.dist.m
    return None


def assign_land_use(zone):
    """
    Simplified land use classification based on elevation.
    In Phase 6 we replace this with real land use raster data.
    0 = water body, 1 = low agriculture, 2 = urban,
    3 = highland agriculture, 4 = forest
    """
    elev = zone.avg_elevation_m or 0
    if elev < 1:
        return 0   # likely water body
    elif elev < 5:
        return 1   # low-lying agriculture — high flood risk
    elif elev < 15:
        return 2   # urban / mixed
    elif elev < 30:
        return 3   # highland agriculture
    else:
        return 4   # forest / hills


def run():
    zones = FloodZone.objects.all()

    if not zones.exists():
        print("No FloodZones found. Run scripts/create_zones.py first.")
        return

    total = zones.count()
    print(f"Extracting features for {total} flood zones...")

    for i, zone in enumerate(zones, 1):
        print(f"  [{i}/{total}] Processing: {zone.name}")

        avg_elev, avg_slope = extract_elevation_features(zone)
        avg_rain = extract_rainfall_features(zone)
        river_dist = extract_river_distance(zone)
        land_use = assign_land_use(zone)

        zone.avg_elevation_m     = round(avg_elev, 2)
        zone.avg_slope_degrees   = round(avg_slope, 4)
        zone.avg_rainfall_mm     = round(avg_rain, 2)
        zone.distance_to_river_m = round(river_dist, 1) if river_dist else None
        zone.land_use_code       = land_use
        zone.save()

    print(f"\nDone. Features extracted for {total} zones.")
    print("\nSample zone:")
    z = FloodZone.objects.first()
    print(f"  Name:        {z.name}")
    print(f"  Elevation:   {z.avg_elevation_m}m")
    print(f"  Slope:       {z.avg_slope_degrees}°")
    print(f"  Rainfall:    {z.avg_rainfall_mm}mm")
    print(f"  Land use:    {z.land_use_code}")


if __name__ == '__main__':
    run()