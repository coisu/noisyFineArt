from flask import Flask, request, jsonify
import os
import sqlite3
import librosa
import random
from datetime import datetime

app = Flask(__name__)

BASE_DIR = "history"
DB_PATH = "db/history.db"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs("db", exist_ok=True)

# 소음 분석 함수
def analyze_sound(file_path):
    y, sr = librosa.load(file_path, sr=None, duration=15)
    rms = librosa.feature.rms(y=y).mean()
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()

    return {"loudness": rms, "tempo": tempo, "frequency": spectral_centroid}

# 키워드 생성 함수
def generate_keywords(features):
    keywords = []

    if features["loudness"] > 0.05:
        keywords.append("강렬한")
    else:
        keywords.append("고요한")

    if features["frequency"] > 3000:
        keywords.append("밝은")
    else:
        keywords.append("어두운")

    if features["tempo"] > 120:
        keywords.append("활기찬")
    else:
        keywords.append("느린")

    style_keywords = ["추상 표현주의", "점묘화", "미래파"]
    material_keywords = ["유화로 만든", "수채화로 만든", "금속으로 만든"]

    keywords.append(random.choice(style_keywords))
    keywords.append(random.choice(material_keywords))

    return ", ".join(keywords)

# DB 연결 함수
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 파일 저장 함수
def save_files_to_disk(job_id, audio_data, image_data):
    job_dir = os.path.join(BASE_DIR, f"{job_id:06d}")
    os.makedirs(job_dir, exist_ok=True)

    noise_path = os.path.join(job_dir, "noise.wav")
    with open(noise_path, "wb") as f:
        f.write(audio_data)

    image_path = os.path.join(job_dir, "result_image.png")
    with open(image_path, "wb") as f:
        f.write(image_data)

    return noise_path, image_path

# 작업 생성 엔드포인트
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    audio_data = file.read()

    # 소음 데이터 분석 및 키워드 생성
    temp_path = "temp.wav"
    with open(temp_path, "wb") as temp_file:
        temp_file.write(audio_data)

    features = analyze_sound(temp_path)
    keywords = generate_keywords(features)

    # Stable Diffusion 이미지 생성 (dummy 이미지 생성)
    dummy_image_data = b"dummy image data"  # 실제 Stable Diffusion API로 교체

    # DB에 작업 생성
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO jobs (timestamp, keywords, status) VALUES (?, ?, ?)", (timestamp, keywords, "completed"))
    job_id = cursor.lastrowid

    # 파일 저장 및 경로 기록
    noise_path, image_path = save_files_to_disk(job_id, audio_data, dummy_image_data)
    cursor.execute("INSERT INTO files (job_id, path, type) VALUES (?, ?, ?)", (job_id, noise_path, "audio"))
    cursor.execute("INSERT INTO files (job_id, path, type) VALUES (?, ?, ?)", (job_id, image_path, "image"))

    conn.commit()
    conn.close()

    return jsonify({"job_id": job_id, "keywords": keywords})

# 작업 검색 엔드포인트
@app.route("/search", methods=["GET"])
def search_jobs():
    keyword = request.args.get("keyword", "")
    date = request.args.get("date", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if keyword:
        query += " AND keywords LIKE ?"
        params.append(f"%{keyword}%")

    if date:
        query += " AND timestamp LIKE ?"
        params.append(f"{date}%")

    cursor.execute(query, params)
    jobs = cursor.fetchall()
    conn.close()

    return jsonify([dict(job) for job in jobs])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
