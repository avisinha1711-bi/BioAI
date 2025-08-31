from flask import Flask, request, jsonify
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_curve

# ---------- Setup ----------
REGION_NAMES = [
    "C=O (~1720)",
    "CH3 (~1300)",
    "C-OH (~1100)",
    "O-H (~3500)"
]

NORMAL_MEANS = [1.2, 1.8, 2.8, 2.2]
NORMAL_STDS  = [0.4, 0.6, 0.7, 0.9]

# ---------- Synthetic Data ----------
def generate_synthetic_data(n_samples=2000, cancer_ratio=0.35, noise=0.15):
    rng = np.random.RandomState(42)
    n_cancer = int(n_samples * cancer_ratio)
    n_normal = n_samples - n_cancer
    base_normal_means = np.array(NORMAL_MEANS)
    base_cancer_shift = np.array([0.8, 0.9, 0.5, 1.9])
    stds = np.array(NORMAL_STDS)

    normal_data = rng.normal(loc=base_normal_means, scale=stds, size=(n_normal, 4))
    cancer_data = rng.normal(loc=base_normal_means + base_cancer_shift, scale=stds, size=(n_cancer, 4))

    X = np.vstack([normal_data, cancer_data])
    y = np.hstack([np.zeros(n_normal, dtype=int), np.ones(n_cancer, dtype=int)])
    perm = rng.permutation(len(y))
    X, y = X[perm], y[perm]

    X += rng.normal(scale=noise, size=X.shape)
    X = np.clip(X, a_min=0.01, a_max=None)
    return X, y

# ---------- Train Model ----------
def train_models():
    X, y = generate_synthetic_data()
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    Xtr_scaled = scaler.transform(X_train)
    Xval_scaled = scaler.transform(X_val)

    logreg = LogisticRegression(solver='liblinear', class_weight='balanced', random_state=42)
    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1)

    stack = StackingClassifier(
        estimators=[('logreg', logreg), ('rf', rf)],
        final_estimator=LogisticRegression(max_iter=500),
        cv=5, stack_method='predict_proba', n_jobs=-1
    )

    calibrated = CalibratedClassifierCV(stack, method="isotonic", cv=3)
    calibrated.fit(Xtr_scaled, y_train)

    val_probs = calibrated.predict_proba(Xval_scaled)[:, 1]
    fpr, tpr, thr = roc_curve(y_val, val_probs)
    best_thr = float(thr[(tpr - fpr).argmax()])

    return {"scaler": scaler, "stack": calibrated, "threshold": best_thr}

# Train once when server starts
models = train_models()

# ---------- Flask API ----------
app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    try:
        vals = [float(data.get("C=O")), float(data.get("CH3")), float(data.get("C-OH")), float(data.get("O-H"))]
        scaler, stack, thr = models['scaler'], models['stack'], models['threshold']
        arr_scaled = scaler.transform([vals])
        prob = float(stack.predict_proba(arr_scaled)[0, 1])
        result = "High Risk of Cancer" if prob >= thr else "Low Risk of Cancer"
        return jsonify({"probability": prob, "threshold": thr, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)


