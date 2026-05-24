"""
Feature pipeline for the flood risk AI model.
Converts raw PostGIS data into a numpy array
ready for scikit-learn.
"""
import numpy as np
import pandas as pd
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Avg
from flood_zones.models import (
    FloodZone, ElevationPoint, RainfallRecord
)

FEATURE_COLUMNS = [
    'avg_elevation_m',
    'avg_slope_degrees',
    'avg_rainfall_mm',
    'distance_to_river_m',
    'land_use_code',
]

# Bangladesh-specific normalization bounds
# Based on real geographic ranges
FEATURE_BOUNDS = {
    'avg_elevation_m':      (0,   200),
    'avg_slope_degrees':    (0,   45),
    'avg_rainfall_mm':      (0,   600),
    'distance_to_river_m':  (0,   50000),
    'land_use_code':        (0,   4),
}


def normalize(value, feature_name):
    """Min-max normalize a single feature value (safe for None/NaN)."""
    if value is None or pd.isna(value):
        return 0.0
    lo, hi = FEATURE_BOUNDS[feature_name]
    if hi == lo:
        return 0.0
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


def zone_to_feature_vector(zone):
    """
    Convert a FloodZone instance into a normalized
    feature vector for the ML model.
    """
    raw = {
        'avg_elevation_m':     zone.avg_elevation_m or 0.0,
        'avg_slope_degrees':   zone.avg_slope_degrees or 0.0,
        'avg_rainfall_mm':     zone.avg_rainfall_mm or 0.0,
        'distance_to_river_m': zone.distance_to_river_m or 25000.0,
        'land_use_code':       zone.land_use_code or 2,
    }
    normalized = {k: normalize(v, k) for k, v in raw.items()}
    vector = np.array([normalized[c] for c in FEATURE_COLUMNS])
    return raw, normalized, vector


def build_training_dataframe():
    """
    Build a labelled DataFrame for training.
    Labels are derived from domain rules.
    """
    zones = FloodZone.objects.exclude(
        avg_elevation_m=None
    ).values(*FEATURE_COLUMNS)

    df = pd.DataFrame(list(zones))

    if df.empty:
        raise ValueError(
            "No zones with extracted features found. "
            "Run scripts/create_zones.py then "
            "scripts/extract_features.py first."
        )

    # ✅ FIX: Vectorized normalization with safe type coercion
    for col in FEATURE_COLUMNS:
        lo, hi = FEATURE_BOUNDS[col]
        
        # 1. Coerce to numeric (turns None/invalid strings into NaN)
        numeric_series = pd.to_numeric(df[col], errors='coerce')
        
        # 2. Fill NaN with a neutral midpoint (prevents skewing the model)
        numeric_series = numeric_series.fillna((lo + hi) / 2)
        
        # 3. Vectorized min-max normalization (fast & type-safe)
        df[f'{col}_norm'] = np.clip((numeric_series - lo) / (hi - lo), 0.0, 1.0)

    # ✅ Vectorized risk score calculation
    land_use_term = np.where(df['land_use_code_norm'] < 0.3, 0.2, 0.0) * 0.05
    df['risk_score'] = (
        (1 - df['avg_elevation_m_norm']) * 0.40 +
        df['avg_rainfall_mm_norm'] * 0.25 +
        (1 - df['avg_slope_degrees_norm']) * 0.15 +
        (1 - df['distance_to_river_m_norm']) * 0.15 +
        land_use_term
    )

    # Clip to [0, 1] range
    df['risk_score'] = df['risk_score'].clip(0.0, 1.0)

    # Convert to 3-class label
    df['risk_level'] = pd.cut(
        df['risk_score'],
        bins=[0, 0.35, 0.65, 1.0],
        labels=['low', 'medium', 'high'],
        include_lowest=True,
    )

    norm_cols = [f'{c}_norm' for c in FEATURE_COLUMNS]
    X = df[norm_cols].values
    y = df['risk_score'].values
    y_class = df['risk_level'].values

    print(f"✅ Training data built: {len(df)} zones")
    print("📊 Risk distribution:")
    print(df['risk_level'].value_counts().to_string())

    return X, y, y_class, df


def geometry_to_features(geojson_geometry):
    """
    Given a GeoJSON polygon from the React frontend,
    extract features on the fly for real-time scoring.
    """
    from django.contrib.gis.geos import GEOSGeometry
    import json

    geom = GEOSGeometry(json.dumps(geojson_geometry), srid=4326)
    centroid = geom.centroid

    # Elevation
    elev_qs = ElevationPoint.objects.filter(location__within=geom)
    if not elev_qs.exists():
        elev_qs = ElevationPoint.objects.filter(
            location__distance_lte=(centroid, D(km=10))
        )
    elev_stats = elev_qs.aggregate(
        e=Avg('elevation_m'), s=Avg('slope_degrees')
    )

    # Rainfall
    rain_stats = RainfallRecord.objects.filter(
        location__distance_lte=(centroid, D(km=50)),
        month__in=[6, 7, 8, 9],
    ).aggregate(r=Avg('rainfall_mm'))

    raw = {
        'avg_elevation_m':     elev_stats['e'] or 5.0,
        'avg_slope_degrees':   elev_stats['s'] or 1.0,
        'avg_rainfall_mm':     rain_stats['r'] or 300.0,
        'distance_to_river_m': 5000.0,
        'land_use_code':       2,
    }

    normalized = {k: normalize(v, k) for k, v in raw.items()}
    vector = np.array([normalized[c] for c in FEATURE_COLUMNS])
    return raw, normalized, vector