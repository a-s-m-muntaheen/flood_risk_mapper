"""
Singleton model service — loads the trained model once
when Django starts and keeps it in memory.
All scoring goes through this module.
"""
import os
import joblib
import numpy as np
from django.conf import settings


_regressor  = None
_classifier = None
_meta       = None

MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml_models')


def _load_models():
    global _regressor, _classifier, _meta

    reg_path  = os.path.join(MODEL_DIR, 'flood_risk_regressor.pkl')
    clf_path  = os.path.join(MODEL_DIR, 'flood_risk_classifier.pkl')
    meta_path = os.path.join(MODEL_DIR, 'model_meta.pkl')

    if not os.path.exists(reg_path):
        raise FileNotFoundError(
            "Model not found. Run: python scripts/train_model.py"
        )

    _regressor  = joblib.load(reg_path)
    _classifier = joblib.load(clf_path)
    _meta       = joblib.load(meta_path)
    print("Flood risk model loaded into memory.")


def get_models():
    global _regressor, _classifier, _meta
    if _regressor is None:
        _load_models()
    return _regressor, _classifier, _meta


def score_vector(feature_vector: np.ndarray) -> dict:
    """
    Score a single normalized feature vector.

    Returns:
        {
          'risk_score':  float  (0.0 – 1.0),
          'risk_level':  str    ('low' | 'medium' | 'high'),
          'confidence':  float  (0.0 – 1.0),
          'probabilities': {'low': f, 'medium': f, 'high': f}
        }
    """
    regressor, classifier, _ = get_models()

    X = feature_vector.reshape(1, -1)

    risk_score  = float(np.clip(regressor.predict(X)[0], 0, 1))
    risk_level  = classifier.predict(X)[0]
    proba       = classifier.predict_proba(X)[0]
    classes     = classifier.named_steps['rf'].classes_

    proba_dict  = {cls: round(float(p), 4)
                   for cls, p in zip(classes, proba)}
    confidence  = float(max(proba))

    return {
        'risk_score':    round(risk_score, 4),
        'risk_level':    str(risk_level),
        'confidence':    round(confidence, 4),
        'probabilities': proba_dict,
    }


def score_zone(zone) -> dict:
    """Score a FloodZone model instance and save results."""
    from risk_engine.feature_pipeline import zone_to_feature_vector

    raw, normalized, vector = zone_to_feature_vector(zone)
    result = score_vector(vector)

    zone.risk_score = result['risk_score']
    zone.risk_level = result['risk_level']
    zone.save(update_fields=['risk_score', 'risk_level'])

    return {**result, 'features': raw, 'zone_id': zone.id}


def score_all_zones(batch_size=100):
    """
    Score every FloodZone in the database.
    Runs in batches to avoid memory issues.
    """
    from flood_zones.models import FloodZone
    from risk_engine.feature_pipeline import zone_to_feature_vector

    regressor, classifier, _ = get_models()

    zones = FloodZone.objects.exclude(avg_elevation_m=None)
    total = zones.count()
    print(f"Scoring {total} zones...")

    scored = 0
    batch  = []

    for zone in zones.iterator(chunk_size=batch_size):
        _, _, vector = zone_to_feature_vector(zone)
        X = vector.reshape(1, -1)

        zone.risk_score = float(np.clip(regressor.predict(X)[0], 0, 1))
        zone.risk_level = classifier.predict(X)[0]
        batch.append(zone)

        if len(batch) >= batch_size:
            FloodZone.objects.bulk_update(
                batch, ['risk_score', 'risk_level']
            )
            scored += len(batch)
            batch = []
            print(f"  Scored {scored}/{total}...")

    if batch:
        FloodZone.objects.bulk_update(
            batch, ['risk_score', 'risk_level']
        )
        scored += len(batch)

    print(f"Done. {scored} zones scored.")
    return scored