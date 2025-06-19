import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

df = pd.read_csv('job_recommendation_dataset.csv')

def skills_overlap(row):
    seeker = set(str(row['seeker_skills']).split('|'))
    job = set(str(row['job_skills']).split('|'))
    return len(seeker & job) / max(1, len(job))

def experience_match(row):
    exp_map = {'ENTRY': 0, 'MID': 2, 'SENIOR': 5}
    return int(row['seeker_experience_years'] >= exp_map.get(row['job_experience_level'], 0))

df['skill_match_score'] = df.apply(skills_overlap, axis=1)
df['salary_match'] = (df['job_salary_min'] >= df['seeker_salary_expectation']).astype(int)
df['location_match'] = (df['job_location'] == df['seeker_location']).astype(int)
df['experience_match'] = df.apply(experience_match, axis=1)

features = ['skill_match_score', 'salary_match', 'location_match', 'experience_match']
X = df[features].values
y = df['applied'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = CatBoostClassifier(
    iterations=300,
    learning_rate=0.04,
    depth=6,
    eval_metric='AUC',
    random_seed=42,
    verbose=50
)

model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)
preds = model.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, preds)
print(f'CatBoost Job Recommendation Validation AUC: {auc:.4f}')
model.save_model('job_catboost_model.cbm')
print('Model saved to job_catboost_model.cbm')
