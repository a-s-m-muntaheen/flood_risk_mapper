"""
Sample elevation points from SRTM DEM raster and load into PostGIS.
Run with: python scripts/ingest_elevation.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import numpy as np
from osgeo import gdal
from django.contrib.gis.geos import Point
from flood_zones.models import ElevationPoint

DEM_PATH = 'data/raw/bangladesh_dem.tif'
SAMPLE_STEP = 20   # sample every 20th pixel — adjust for density vs speed


def compute_slope(elevation_array, geotransform):
    """Simple slope calculation from elevation grid."""
    dx = geotransform[1]  # pixel width in degrees
    dy = abs(geotransform[5])  # pixel height in degrees
    # Convert degrees to approximate metres at Bangladesh latitude
    dx_m = dx * 111320 * np.cos(np.radians(23.8))
    dy_m = dy * 111320
    gy, gx = np.gradient(elevation_array, dy_m, dx_m)
    slope = np.degrees(np.arctan(np.sqrt(gx**2 + gy**2)))
    return slope


def run():
    if not os.path.exists(DEM_PATH):
        print(f"DEM not found at {DEM_PATH}")
        print("Download SRTM data from OpenTopography")
        return

    print("Opening DEM raster...")
    ds = gdal.Open(DEM_PATH)
    band = ds.GetRasterBand(1)
    gt = ds.GetGeoTransform()

    elevation = band.ReadAsArray().astype(float)
    nodata = band.GetNoDataValue()
    if nodata:
        elevation[elevation == nodata] = np.nan

    slope = compute_slope(elevation, gt)

    print(f"Raster size: {elevation.shape}. Sampling every {SAMPLE_STEP}th pixel...")
    ElevationPoint.objects.all().delete()

    points = []
    rows, cols = elevation.shape
    for row in range(0, rows, SAMPLE_STEP):
        for col in range(0, cols, SAMPLE_STEP):
            elev_val = elevation[row, col]
            if np.isnan(elev_val):
                continue
            lon = gt[0] + col * gt[1]
            lat = gt[3] + row * gt[5]
            points.append(ElevationPoint(
                location    = Point(lon, lat, srid=4326),
                elevation_m = float(elev_val),
                slope_degrees = float(slope[row, col]),
            ))
            if len(points) >= 1000:
                ElevationPoint.objects.bulk_create(points)
                points = []

    if points:
        ElevationPoint.objects.bulk_create(points)

    total = ElevationPoint.objects.count()
    print(f"Done. {total} elevation points loaded into PostGIS.")

if __name__ == '__main__':
    run()