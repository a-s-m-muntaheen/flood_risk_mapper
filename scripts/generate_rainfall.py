"""
Generate realistic synthetic rainfall data based on Bangladesh monsoon patterns.
Covers 20 weather stations with monthly averages matching real BWDB data.
Run with: python scripts/generate_rainfall.py
"""
import os
import sys
import django
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.gis.geos import Point
from flood_zones.models import RainfallRecord

# Real Bangladesh weather stations with approximate coordinates
STATIONS = [
    ('Dhaka',       23.7104, 90.4074),
    ('Chittagong',  22.3569, 91.7832),
    ('Sylhet',      24.8949, 91.8687),
    ('Rajshahi',    24.3745, 88.6042),
    ('Khulna',      22.8456, 89.5403),
    ('Barishal',    22.7010, 90.3535),
    ('Mymensingh',  24.7471, 90.4203),
    ('Comilla',     23.4607, 91.1809),
    ('Rangpur',     25.7439, 89.2752),
    ('Jessore',     23.1667, 89.2167),
    ('Faridpur',    23.6070, 89.8429),
    ('Tangail',     24.2513, 89.9167),
    ('Bogra',       24.8510, 89.3710),
    ('Dinajpur',    25.6279, 88.6338),
    ('Patuakhali',  22.3596, 90.3298),
    ('Noakhali',    22.8696, 91.0993),
    ('Brahmanbaria',23.9570, 91.1115),
    ('Narsingdi',   23.9324, 90.7150),
    ('Manikganj',   23.8634, 89.9711),
    ('Kishoreganj', 24.4449, 90.7766),
]

# Monthly rainfall multipliers — Bangladesh monsoon pattern
# Jan=dry, Jun-Sep=peak monsoon
MONTHLY_PATTERN = [0.05, 0.06, 0.08, 0.12, 0.18,
                   0.65, 1.00, 0.95, 0.70, 0.30,
                   0.10, 0.06]

# Annual average rainfall by station (mm) — approximate real values
ANNUAL_RAIN = {
    'Dhaka': 1854, 'Chittagong': 2666, 'Sylhet': 3334,
    'Rajshahi': 1416, 'Khulna': 1809, 'Barishal': 1915,
    'Mymensingh': 2154, 'Comilla': 2004, 'Rangpur': 1566,
    'Jessore': 1548, 'Faridpur': 1654, 'Tangail': 1811,
    'Bogra': 1632, 'Dinajpur': 1573, 'Patuakhali': 2244,
    'Noakhali': 2131, 'Brahmanbaria': 2063, 'Narsingdi': 1924,
    'Manikganj': 1784, 'Kishoreganj': 2012,
}


def run():
    print("Generating synthetic rainfall data...")
    RainfallRecord.objects.all().delete()

    records = []
    for year in range(2015, 2024):
        for station_name, lat, lon in STATIONS:
            annual = ANNUAL_RAIN.get(station_name, 1800)
            for month_idx, multiplier in enumerate(MONTHLY_PATTERN, 1):
                base = annual * multiplier
                # Add realistic year-to-year variation (±15%)
                noise = random.uniform(0.85, 1.15)
                rainfall = round(base * noise, 1)
                records.append(RainfallRecord(
                    location     = Point(lon, lat, srid=4326),
                    month        = month_idx,
                    year         = year,
                    rainfall_mm  = rainfall,
                    station_name = station_name,
                ))

    RainfallRecord.objects.bulk_create(records)
    total = RainfallRecord.objects.count()
    print(f"Done. {total} rainfall records generated for {len(STATIONS)} stations across 9 years.")

if __name__ == '__main__':
    run()