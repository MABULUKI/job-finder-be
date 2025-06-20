"""
Train a CatBoost model for job recommendation using the generated CSV.
- Evaluates and saves the model for backend integration.
- Prints ROC-AUC and feature importances.
"""
import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
import joblib

DATA_PATH = "data/job_recommendation_training.csv"
MODEL_PATH = "models/job_recommendation_model.cbm"

# 1. Load data
df = pd.read_csv(DATA_PATH)

# 2. Features/labels
FEATURES = [
    "skills_jaccard",
    "skills_overlap",
    "education_match",
    "experience_years",
    "job_experience_required",
    "experience_gap",
    "preferred_job_type_match",
    "location_match",
    "salary_within_range",
    "seeker_rating",
    "is_available",
]
X = df[FEATURES]
y = df["label"]

# 3. Split train/val
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# 4. Train CatBoost
model = CatBoostClassifier(
    iterations=300,
    learning_rate=0.08,
    depth=6,
    loss_function="Logloss",
    eval_metric="AUC",
    verbose=50,
    random_seed=42,
)
model.fit(X_train, y_train, eval_set=(X_val, y_val), use_best_model=True)

# 5. Evaluate
val_pred = model.predict_proba(X_val)[:, 1]
roc_auc = roc_auc_score(y_val, val_pred)
print(f"Validation ROC-AUC: {roc_auc:.4f}")
print(classification_report(y_val, (val_pred > 0.5).astype(int)))

# 6. Feature importances
print("Feature importances:")
for feat, imp in zip(FEATURES, model.feature_importances_):
    print(f"  {feat}: {imp:.2f}")

# 7. Save model
model.save_model(MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
