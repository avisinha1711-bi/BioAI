import numpy as np
import pandas as pd
import os, shutil
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_curve
from colorama import Fore, Style, init

# ---------- Setup ----------
init(autoreset=True)
RNG = np.random.RandomState(42)

REGION_NAMES = [
    "C=O (~1720 cm^-1)",
    "CH3 (~1300 cm^-1)",
    "C-OH (~1100 cm^-1)",
    "O-H (~3500 cm^-1)"
]

# Normal ranges (means & stds) for interactive feedback
NORMAL_MEANS = [1.2, 1.8, 2.8, 2.2]
NORMAL_STDS  = [0.4, 0.6, 0.7, 0.9]

# ---------- UI ----------
def show_bioai_header(width: int):
    os.system('cls' if os.name == 'nt' else 'clear')
    title = "BIOAI – AI-powered Cancer Photoacoustic Diagnosis"
    author = "Developed by: Avi Sinha"
    border = "═" * width
    print(Fore.CYAN + Style.BRIGHT + border)
    print(Fore.YELLOW + Style.BRIGHT + title.center(width))
    print(Fore.WHITE + author.center(width))
    print(Fore.CYAN + border + Style.RESET_ALL + "\n")

def print_section(msg: str, color=Fore.CYAN):
    width = shutil.get_terminal_size().columns
    print(color + "─" * width)
    print(color + Style.BRIGHT + msg.center(width))
    print(color + "─" * width + Style.RESET_ALL)

# ---------- Data ----------
def generate_synthetic_data(n_samples=2000, cancer_ratio=0.35, noise=0.15):
    n_cancer = int(n_samples * cancer_ratio)
    n_normal = n_samples - n_cancer
    base_normal_means = np.array(NORMAL_MEANS)
    base_cancer_shift = np.array([0.8, 0.9, 0.5, 1.9])
    stds = np.array(NORMAL_STDS)

    normal_data = RNG.normal(loc=base_normal_means, scale=stds, size=(n_normal, 4))
    cancer_data = RNG.normal(loc=base_normal_means + base_cancer_shift, scale=stds, size=(n_cancer, 4))

    X = np.vstack([normal_data, cancer_data])
    y = np.hstack([np.zeros(n_normal, dtype=int), np.ones(n_cancer, dtype=int)])
    perm = RNG.permutation(len(y))
    X, y = X[perm], y[perm]

    X += RNG.normal(scale=noise, size=X.shape)
    X = np.clip(X, a_min=0.01, a_max=None)
    df = pd.DataFrame(X, columns=REGION_NAMES)
    df['label'] = y
    return df

# ---------- Model ----------
def train_models(df):
    X = df[REGION_NAMES].values
    y = df['label'].values
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    Xtr_scaled = scaler.transform(X_train)
    Xval_scaled = scaler.transform(X_val)

    # Base models
    logreg = LogisticRegression(solver='liblinear', class_weight='balanced', random_state=42)
    rf = RandomForestClassifier(
        n_estimators=100, random_state=42, class_weight='balanced', n_jobs=-1
    )

    stack = StackingClassifier(
        estimators=[('logreg', logreg), ('rf', rf)],
        final_estimator=LogisticRegression(max_iter=500),
        cv=5, stack_method='predict_proba', n_jobs=-1
    )

    calibrated = CalibratedClassifierCV(stack, method="isotonic", cv=3)
    calibrated.fit(Xtr_scaled, y_train)

    # Tune threshold with Youden’s J
    val_probs = calibrated.predict_proba(Xval_scaled)[:, 1]
    fpr, tpr, thr = roc_curve(y_val, val_probs)
    best_thr = float(thr[(tpr - fpr).argmax()])

    return {"scaler": scaler, "stack": calibrated, "threshold": best_thr}

def load_or_train():
    df = generate_synthetic_data()
    return train_models(df)

# ---------- Inference ----------
def diagnose_patient(vals, models, width: int, patient_num: int):
    scaler, stack, thr = models['scaler'], models['stack'], models['threshold']
    arr_scaled = scaler.transform([vals])
    prob = float(stack.predict_proba(arr_scaled)[0, 1])

    print(Fore.CYAN + "═" * width)
    print(Fore.MAGENTA + f"🧾 Patient {patient_num} – Diagnosis".center(width))
    print(Fore.MAGENTA + f"📈 Probability: {prob:.3f}  (Threshold={thr:.2f})".center(width))
    if prob >= thr:
        print(Fore.RED + "⚠️ HIGH RISK OF CANCER DETECTION — MAY REQUIRE FURTHER DIAGNOSIS".center(width))
    else:
        print(Fore.GREEN + "✅ LESS CHANCE OF CANCER DETECTION".center(width))
    print(Fore.CYAN + "═" * width + Style.RESET_ALL)

# ---------- Interactive ----------
def interactive_predict(models, width: int):
    patient_num = 1
    print_section(f"Patient {patient_num}: Provide IR frequency readings (MHz). Type 'exit' anytime to quit.")

    while True:
        vals = []
        for i, name in enumerate(REGION_NAMES):
            while True:  # keep asking until valid
                s = input(Fore.CYAN + f"  ➤ {name}: " + Style.RESET_ALL).strip()
                if s.lower() in ("exit", "q"):
                    print(Fore.CYAN + "Goodbye!".center(width) + Style.RESET_ALL)
                    return
                try:
                    value = float(s)
                    vals.append(value)
                    mean, std = NORMAL_MEANS[i], NORMAL_STDS[i]
                    if abs(value - mean) <= std:
                        print(Fore.GREEN + "   ✅ At normal level")
                    elif value > mean:
                        print(Fore.RED + "   ⚠️ Higher than normal level")
                    else:
                        print(Fore.LIGHTGREEN_EX + "   ⚠️ Lower than normal level")
                    break
                except ValueError:
                    print(Fore.RED + "❌ Invalid input. Please enter a number." + Style.RESET_ALL)

        # After collecting all 4 values
        diagnose_patient(vals, models, width, patient_num)

        # Ask to continue
        cont = input(Fore.CYAN + "\nPress Enter for next patient or type 'exit' to quit: " + Style.RESET_ALL).strip().lower()
        if cont in ("exit", "q"):
            print(Fore.CYAN + "Goodbye!".center(width) + Style.RESET_ALL)
            return
        else:
            patient_num += 1
            print_section(f"Patient {patient_num}: Provide IR frequency readings (MHz)")

# ---------- Main ----------
def main():
    width = shutil.get_terminal_size().columns
    show_bioai_header(width)
    models = load_or_train()
    interactive_predict(models, width)

if __name__ == "__main__":
    main()
