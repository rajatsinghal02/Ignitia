# app/analysis_utils.py
import cv2
import torch
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import asyncio
import scipy.io.wavfile as wav
import tempfile

# --- Conditionally import models to avoid errors during setup ---
try:
    from insightface.app import FaceAnalysis
    from transformers import ViTImageProcessor, ViTForImageClassification
    MODELS_LOADED = True
except ImportError:
    MODELS_LOADED = False

# --- Global Variables ---
device = "cpu"
face_app = None
processor = None
emotion_model = None
EMOTIONS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
AGE_BUCKETS = [(1,5),(6,10),(11,15),(16,20),(21,25),(26,30),
               (31,35),(36,40),(41,45),(46,50),(51,55),(56,60),(61,65),(66,70),(71,75),(76,80),
               (81,85),(86,90),(91,95),(96,100)]

# --- Model Initialization ---
def initialize_models():
    """Initializes and loads all the necessary AI models."""
    global device, face_app, processor, emotion_model
    if not MODELS_LOADED:
        print("[WARN] Analysis libraries not installed. Skipping model loading.")
        return

    if face_app is not None: # Models already loaded
        return

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")

    print("[INFO] Loading InsightFace...")
    face_app = FaceAnalysis(name="buffalo_l")
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    print("[INFO] InsightFace ready.")

    print("[INFO] Loading HuggingFace ViT Emotion Model...")
    processor = ViTImageProcessor.from_pretrained("abhilash88/face-emotion-detection")
    emotion_model = ViTForImageClassification.from_pretrained("abhilash88/face-emotion-detection").to(device)
    emotion_model.eval()
    print("[INFO] Emotion model loaded successfully.")


# --- Analysis Helper Functions ---
def age_to_range(age):
    a = max(0,int(age)-5)
    for s,e in AGE_BUCKETS:
        if s <= a <= e:
            return f"{s}-{e}"
    return "100+"

def get_emotion_vit(face_crop):
    try:
        if not MODELS_LOADED or face_crop.size == 0:
            return "N/A", 0.0
        img_pil = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
        inputs = processor(img_pil, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = emotion_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            idx = torch.argmax(probs, dim=-1).item()
            pred_emotion = EMOTIONS[idx]
        fear_score = (
            probs[0][2].item() + 0.5*probs[0][5].item() + 0.3*probs[0][0].item() + 0.2*probs[0][1].item()
        )
        fear_score = np.clip(fear_score,0,1)
        return pred_emotion, fear_score
    except Exception as e:
        print("[WARN] Emotion prediction failed:", e)
        return "N/A", 0.0

def get_vulnerability_from_age(age):
    if age is None: return 0.2
    if age<=11: return 1.0
    if age<=17: return 0.6
    if age<=64: return 0.2
    return 0.9

def compute_panic_score(age_vuln, fear, gender_score, conf):
    W_AGE = 0.4; W_FACE = 0.4; W_GENDER = 0.2
    raw_score = W_AGE*age_vuln + W_FACE*fear + W_GENDER*gender_score
    panic_score = raw_score*conf*100
    return raw_score, panic_score

def compute_group_panic(face_data_list):
    if not face_data_list:
        return {'PanicScore': 0.0}
    W_E = 0.45; W_V = 0.35; W_GP = 0.20
    mean_emo_fear = np.mean([f['emo_fear'] for f in face_data_list])
    mean_age_vuln = np.mean([f['age_vuln'] for f in face_data_list])
    mean_gender_score = np.mean([f['gender_score'] for f in face_data_list])
    mean_conf = np.mean([f['face_conf'] for f in face_data_list])
    max_individual_raw = max([f['raw_score'] for f in face_data_list])
    G_raw = W_E*mean_emo_fear + W_V*mean_age_vuln + W_GP*mean_gender_score
    size = len(face_data_list)
    GSF = np.clip(1 + (3-size)/6, 0.7,1.5)
    G_score_raw = G_raw*mean_conf*GSF
    alpha, beta = 0.6,0.4
    PanicScore = 100*np.clip(alpha*G_score_raw + beta*max_individual_raw,0,1)
    return {'PanicScore': PanicScore}

def image_to_base64(img_arr):
    """Converts a numpy array (OpenCV image) to a base64 string."""
    _, buffer = cv2.imencode('.jpg', img_arr)
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

# --- Main Analysis Function ---
def analyze_image_from_path(image_path):
    """
    Performs full face, emotion, and panic analysis on an image file.
    Returns a dictionary with group stats and individual face data.
    """
    if not MODELS_LOADED or face_app is None:
        return {"error": "Analysis models are not loaded."}

    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not read the image file."}
    except Exception as e:
        return {"error": f"Error loading image: {e}"}

    faces = face_app.get(img)
    if not faces:
        return {"group_stats": {}, "faces": []}

    face_data_list = []
    person_details = []
    male_count = 0
    female_count = 0

    for idx, f in enumerate(faces):
        x1, y1, x2, y2 = map(int, f.bbox)
        face_crop = img[y1:y2, x1:x2]
        if face_crop.size == 0:
            continue

        gender = "Male" if f.gender == 1 else "Female"
        if gender == "Male": male_count += 1
        else: female_count += 1

        age = int(f.age) if hasattr(f, "age") else 25
        age_vuln = get_vulnerability_from_age(age)
        gender_score = 0.8 if gender == "Male" else 1.0
        face_conf = float(getattr(f, "det_score", 1.0))

        emo_label, emo_fear = get_emotion_vit(face_crop)
        raw_score, panic_score = compute_panic_score(age_vuln, emo_fear, gender_score, face_conf)

        face_data_list.append({
            'emo_fear': emo_fear, 'age_vuln': age_vuln,
            'gender_score': gender_score, 'face_conf': face_conf, 'raw_score': raw_score
        })

        person_details.append({
            "id": idx,
            "crop_base64": image_to_base64(face_crop),
            "gender": gender,
            "age": age,
            "age_range": age_to_range(age),
            "emotion_label": emo_label,
            "confidence": f"{face_conf:.2%}",
            "fear_score": f"{emo_fear:.2%}",
            "vulnerability": f"{age_vuln:.2%}",
            "panic_score": f"{panic_score:.0f}"
        })

    group_scores = compute_group_panic(face_data_list)
    group_stats = {
        "total_faces": len(faces),
        "male_count": male_count,
        "female_count": female_count,
        "panic_score": f"{group_scores.get('PanicScore', 0.0):.0f}"
    }

    return {"group_stats": group_stats, "faces": person_details}