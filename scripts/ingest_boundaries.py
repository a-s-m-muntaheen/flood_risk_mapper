"""
Load Bangladesh upazila boundaries from HUMDATA shapefile into PostGIS.
Run with: python manage.py shell < scripts/ingest_boundaries.py
"""
import os
import sys
import django

# Bootstrap Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry
from flood_zones.models import District
import json

SHP_PATH = 'data/raw/bgd_admin_boundaries.shp'

def run():
    if not os.path.exists(SHP_PATH):
        print(f"Shapefile not found at {SHP_PATH}")
        print("Download from: https://data.humdata.org/dataset/cod-ab-bgd")
        return

    print("Reading shapefile...")
    gdf = gpd.read_file(SHP_PATH)
    gdf = gdf.to_crs(epsg=4326)

    print(f"Found {len(gdf)} upazilas. Loading into PostGIS...")
    District.objects.all().delete()

    created = 0
    for _, row in gdf.iterrows():
        geom_json = json.dumps(row.geometry.__geo_interface__)
        geos_geom = GEOSGeometry(geom_json, srid=4326)

        District.objects.create(
            name     = row.get('ADM2_EN', 'Unknown'),
            district = row.get('ADM2_EN', 'Unknown'),
            division = row.get('ADM1_EN', 'Unknown'),
            geometry = geos_geom,
        )
        created += 1

    print(f"Done. {created} districts loaded into PostGIS.")

if __name__ == '__main__':
    run()