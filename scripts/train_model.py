"""
Train the flood risk Random Forest model.
Reads features from PostGIS, trains, evaluates,
and saves the model to ml_models/flood_risk_model.pkl

Run with: python scripts/train_model.py
"""
import os
import sys
import django
import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    mean_absolute_error, r2_score,
    classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import pandas as pd

from risk_engine.feature_pipeline import (
    build_training_dataframe, FEATURE_COLUMNS
)

MODEL_DIR  = 'ml_models'
REG_PATH   = os.path.join(MODEL_DIR, 'flood_risk_regressor.pkl')
CLF_PATH   = os.path.join(MODEL_DIR, 'flood_risk_classifier.pkl')
META_PATH  = os.path.join(MODEL_DIR, 'model_meta.pkl')


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("=" * 50)
    print("FLOOD RISK MODEL TRAINING")
    print("=" * 50)

    # ── Load data ──────────────────────────────────
    print("\n[1/5] Loading feature data from PostGIS...")
    X, y_reg, y_cls, df = build_training_dataframe()
    print(f"      Samples: {X.shape[0]}  Features: {X.shape[1]}")

    # ── Split ──────────────────────────────────────
    print("\n[2/5] Splitting train/test (80/20)...")
    (X_train, X_test,
     y_reg_train, y_reg_test,
     y_cls_train, y_cls_test) = train_test_split(
        X, y_reg, y_cls,
        test_size=0.2,
        random_state=42
    )
    print(f"      Train: {len(X_train)}  Test: {len(X_test)}")

    # ── Train regressor ────────────────────────────
    print("\n[3/5] Training Random Forest Regressor...")
    regressor = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        ))
    ])
    regressor.fit(X_train, y_reg_train)

    y_pred_reg = regressor.predict(X_test)
    mae = mean_absolute_error(y_reg_test, y_pred_reg)
    r2  = r2_score(y_reg_test, y_pred_reg)

    cv_scores = cross_val_score(
        regressor, X, y_reg, cv=5, scoring='r2'
    )

    print(f"      MAE:  {mae:.4f}")
    print(f"      R²:   {r2:.4f}")
    print(f"      CV R² (5-fold): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Train classifier ───────────────────────────
    print("\n[4/5] Training Random Forest Classifier...")
    classifier = Pipeline([
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=3,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        ))
    ])
    classifier.fit(X_train, y_cls_train)

    y_pred_cls = classifier.predict(X_test)
    print("\n      Classification Report:")
    present_labels = classifier.classes_
    print(classification_report(
        y_cls_test, y_pred_cls,
        labels=present_labels,
        target_names=[str(l) for l in present_labels]
    ))

    # Feature importance
    rf_model = regressor.named_steps['rf']
    importances = rf_model.feature_importances_
    norm_cols = [f'{c}_norm' for c in FEATURE_COLUMNS]
    print("\n      Feature importances:")
    for feat, imp in sorted(
        zip(norm_cols, importances),
        key=lambda x: x[1], reverse=True
    ):
        bar = '█' * int(imp * 40)
        print(f"      {feat:<35} {bar} {imp:.3f}")

    # ── Save models ────────────────────────────────
    print("\n[5/5] Saving models...")
    joblib.dump(regressor,  REG_PATH)
    joblib.dump(classifier, CLF_PATH)

    meta = {
        'feature_columns': FEATURE_COLUMNS,
        'norm_columns':    norm_cols,
        'metrics': {
            'mae':    round(mae, 4),
            'r2':     round(r2, 4),
            'cv_r2':  round(cv_scores.mean(), 4),
        },
        'training_samples': len(X_train),
        'test_samples':     len(X_test),
    }
    joblib.dump(meta, META_PATH)

    print(f"      Regressor  → {REG_PATH}")
    print(f"      Classifier → {CLF_PATH}")
    print(f"      Metadata   → {META_PATH}")
    print("\nTraining complete.")
    return regressor, classifier, meta


if __name__ == '__main__':
    train()