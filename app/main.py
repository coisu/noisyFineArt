from flask import Flask, request, jsonify
import os
import sqlite3
import random
from datetime import datetime
import requests
import librosa
import scipy.signal

if not hasattr(scipy.signal, 'hann'):
    from scipy.signal.windows import hann
    scipy.signal.hann = hann

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key is missing. Please set it in the environment variables.")

app = Flask(__name__)

BASE_DIR = "history"
DB_PATH = "db/history.db"

os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["NUMBA_CACHE_DIR"] = "/tmp/numba_cache"

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs("db", exist_ok=True)

# Analyze sound file
def analyze_sound(file_path):
    y, sr = librosa.load(file_path, sr=None, duration=15)

    rms = librosa.feature.rms(y=y).mean()
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y=y).mean()
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=False)
    onset_density = len(onset_frames) / librosa.get_duration(y=y, sr=sr)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()

    features = {
        "loudness": float(rms),
        "tempo": float(tempo),
        "frequency": float(spectral_centroid),
        "zero_crossing_rate": float(zero_crossing_rate),
        "onset_density": float(onset_density),
        "bandwidth": float(bandwidth),
    }

    return features

# Generate keywords based on features
def generate_keywords(features):
    keywords = []

    # Tempo-based keywords considering onset density
    rhythm = [
        "subdued",
        "calm",
        "active",
        "highly dynamic"
    ]

    # 템포와 점수 매핑
    if features["tempo"] < 60:
        index = 0
    elif 60 <= features["tempo"] < 90:
        index = 1
    elif 90 <= features["tempo"] < 150:
        index = 2
    else:
        index = 3

    # 온셋 밀도와 점수 매핑
    if features["onset_density"] < 5:
        if index > 0:
            index -= int(index // 2)  # 정수 변환
    elif 5 <= features["onset_density"] < 10:
        if index > 1:
            index -= int((index - 1) // 2)  # 정수 변환
        else:
            index += 1
    elif 10 <= features["onset_density"] < 15:
        if index > 2:
            index -= int((index - 2) // 2)  # 정수 변환
        elif index < 2:
            index += int((2 - index) // 2)  # 정수 변환
    else:
        if index < 3:
            index += int((3 - index) // 2)  # 정수 변환

    # 최종 키워드 추가
    keywords.append(rhythm[index])


    
    # if features["tempo"] < 60:
    #     if features["onset_density"] < 5:
    #         keywords.append("subdued")  # 매우 차분한
    #     else:
    #         keywords.append("gentle movement")  # 부드럽게 움직이는
    # elif 60 <= features["tempo"] < 90:
    #     if features["onset_density"] < 10:
    #         keywords.append("calm")  # 차분한
    #     else:
    #         keywords.append("flowing")  # 유동적인
    # elif 90 <= features["tempo"] < 150:
    #     if features["onset_density"] < 15:
    #         keywords.append("active")  # 활발한
    #     else:
    #         keywords.append("energetic rhythm")  # 에너지 넘치는 리듬
    # else:
    #     if features["onset_density"] < 20:
    #         keywords.append("highly dynamic")  # 매우 역동적인
    #     else:
    #         keywords.append("intense motion")  # 강렬한 움직임

    # Bandwidth-based keywords
    if features["bandwidth"] > 2000:
        keywords.append("sharp")
    else:
        keywords.append("dull")

    # Touch size keywords: onset density
    if features["onset_density"] > 20:
        keywords.append("fine touch")
    elif 10 < features["onset_density"] <= 20:
        keywords.append("medium touch")
    else:
        keywords.append("broad touch")

    # ZCR-based keywords
    if features["zero_crossing_rate"] > 0.1:
        keywords.append("crisp")
    else:
        keywords.append("smooth")

    # Style keywords
    if features["tempo"] < 60 and features["bandwidth"] < 2000:
        keywords.append("cubism")
    elif 60 <= features["tempo"] < 100 and features["bandwidth"] < 3000:
        keywords.append("de stijl")
    elif 100 <= features["tempo"] < 150 and features["bandwidth"] >= 3000:
        keywords.append("futurism")
    elif features["tempo"] >= 150 and features["onset_density"] > 5:
        keywords.append("neo-impressionism")
    elif features["frequency"] > 5000 and features["zero_crossing_rate"] > 0.15:
        keywords.append("abstract expressionism")
    elif features["loudness"] < 0.02 and features["onset_density"] < 4:
        keywords.append("minimalism")
    elif features["loudness"] > 0.05 and features["bandwidth"] > 5000:
        keywords.append("expressionism")
    elif features["frequency"] < 4000 and features["tempo"] < 60:
        keywords.append("romanticism")
    else:
        keywords.append("experimental")

    return ", ".join(keywords)


# Generate image with prompt
def generate_image(prompt):
    # Access the key
    api_url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "n": 1,
        "size": "512x512"
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data["data"][0]["url"]
    else:
        raise Exception(f"API call failed: {response.status_code}, {response.text}")

# Database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Save files to disk
def save_files_to_disk(job_id, audio_data, image_data, prompt):
    job_dir = os.path.join(BASE_DIR, f"{job_id:06d}")
    os.makedirs(job_dir, exist_ok=True)

    noise_path = os.path.join(job_dir, "noise.wav")
    with open(noise_path, "wb") as f:
        f.write(audio_data)

    image_path = os.path.join(job_dir, "result_image.png")
    with open(image_path, "wb") as f:
        f.write(image_data)

    prompt_path = os.path.join(job_dir, "prompt.txt")
    with open(prompt_path, "w") as f:
        f.write(prompt)

    return noise_path, image_path, prompt_path

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    audio_data = file.read()

    # Analyze and generate keywords
    temp_path = "/tmp/temp.wav"
    with open(temp_path, "wb") as temp_file:
        temp_file.write(audio_data)

    features = analyze_sound(temp_path)
    keywords = generate_keywords(features)
    prompt = f"An abstract art piece inspired by {keywords}"

    # Generate image
    try:
        image_url = generate_image(prompt)
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500

    # Download image
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content
    except Exception as e:
        return jsonify({"error": f"Image download failed: {str(e)}"}), 500

    # Save to database
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO jobs (timestamp, keywords, status) VALUES (?, ?, ?)", (timestamp, keywords, "completed"))
    job_id = cursor.lastrowid

    # Save files
    noise_path, image_path, prompt_path = save_files_to_disk(job_id, audio_data, image_data, prompt)

    # Save metadata
    cursor.execute("INSERT INTO files (job_id, path, type) VALUES (?, ?, ?)", (job_id, noise_path, "audio"))
    cursor.execute("INSERT INTO files (job_id, path, type) VALUES (?, ?, ?)", (job_id, image_path, "image"))
    cursor.execute("INSERT INTO files (job_id, path, type) VALUES (?, ?, ?)", (job_id, prompt_path, "prompt"))
    cursor.execute("INSERT INTO analyzed_features (job_id, features) VALUES (?, ?)", (job_id, str(features)))

    conn.commit()
    conn.close()

    return jsonify({
        "job_id": job_id,
        "keywords": keywords,
        "features": features,
        "image_url": image_url
    })

@app.route("/search", methods=["GET"])
def search_jobs():
    keywords = request.args.getlist("keyword")
    date = request.args.get("date", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if keywords:
        query += " AND (" + " OR ".join(["keywords LIKE ?"] * len(keywords)) + ")"
        params.extend([f"%{keyword}%" for keyword in keywords])

    if date:
        query += " AND timestamp LIKE ?"
        params.append(f"{date}%")

    cursor.execute(query, params)
    jobs = cursor.fetchall()
    conn.close()

    return jsonify([dict(job) for job in jobs])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
