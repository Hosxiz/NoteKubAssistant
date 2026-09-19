"""
Entry module moved into `src/` so project can be organized.
This file mirrors previous `app.py` but uses absolute paths for templates/static/data.
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

#ส่วนของการตั้งค่าและโหลดตัวแปรสภาพแวดล้อมให้โปรแกรมสามารถเข้าถึง API Key และโหมดจำลองได้
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.environ.get("DEEPSEEK_API_KEY")
MOCK_MODE = os.environ.get("MOCK_MODE", "").lower() in ("1", "true", "yes")
API_URL = "https://api.deepseek.com/chat/completions"
DATA_FILE = os.path.join(BASE_DIR, "data", "notes.json")

#สร้างโฟลเดอร์สำหรับเก็บข้อมูลหากยังไม่มี
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

#เริ่มต้น Flask app และกำหนดโฟลเดอร์สำหรับ static และ templates
static_folder = os.path.join(BASE_DIR, "static")
template_folder = os.path.join(BASE_DIR, "templates")
app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)

MODE_PROMPTS = {
    "short": "สรุปเนื้อหาต่อไปนี้ให้สั้น กระชับ ไม่เกิน 5 บรรทัด:\n\n{text}",
    "bullet": "สรุปเนื้อหาต่อไปนี้เป็น bullet point:\n\n{text}",
    "simple": "อธิบายเนื้อหาต่อไปนี้แบบง่ายที่สุด เหมือนอธิบายให้เด็กมัธยมฟัง:\n\n{text}",
}

#ส่วนของฟังก์ชันที่เรียกใช้งาน DeepSeek API และจัดการประวัติการสรุป
def call_deepseek(text, mode):
    if MOCK_MODE:
        if mode == "short":
            first_line = text.strip().split('\n')[0]
            short = first_line[:200] if first_line else text.strip()[:200]
            return f"(MOCK) สรุปสั้น: {short}"
        if mode == "bullet":
            sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
            bullets = sentences[:3] or [text.strip()[:80]]
            return '\n'.join(f"- {b}" for b in bullets)
        if mode == "simple":
            return f"(MOCK) อธิบายง่าย: {text.strip()[:250]}"

    if not API_KEY:
        raise RuntimeError("ไม่พบ DEEPSEEK_API_KEY กรุณาตั้งค่าในไฟล์ .env")
    if mode not in MODE_PROMPTS:
        raise ValueError("โหมดไม่ถูกต้อง")

    prompt = MODE_PROMPTS[mode].format(text=text)
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "stream": False}

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def load_history():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_record(original, summary, mode):
    history = load_history()
    record = {
        "id": len(history) + 1,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "mode": mode,
        "original": original,
        "summary": summary,
    }
    history.append(record)
    save_history(history)
    return record

# ส่วนของ route และ API endpoint ของ Flask app
def get_summary(text, mode):
    try:
        return call_deepseek(text, mode), None
    except RuntimeError as e:
        return None, (str(e), 400)
    except ValueError as e:
        return None, (str(e), 400)
    except requests.exceptions.Timeout:
        return None, ("การเชื่อมต่อหมดเวลา ลองใหม่อีกครั้ง", 504)
    except requests.exceptions.HTTPError as e:
        return None, (f"API ตอบกลับผิดพลาด: {e}", 502)
    except requests.exceptions.RequestException:
        return None, ("เชื่อมต่ออินเทอร์เน็ตไม่ได้", 502)
    except (KeyError, IndexError):
        return None, ("รูปแบบผลลัพธ์จาก API ผิดปกติ", 502)

#ส่วนของ route และ API endpoint ของ Flask app
@app.route("/")
def index():
    return render_template("index.html", history=list(reversed(load_history())))


@app.route("/api/summarize", methods=["POST"])
def summarize():
    body = request.get_json(silent=True) or {}
    note_text = (body.get("text") or "").strip()
    mode = body.get("mode", "short")

    if not note_text:
        return jsonify({"ok": False, "error": "ยังไม่ได้กรอกเนื้อหา"}), 400

    summary, error = get_summary(note_text, mode)
    if error:
        message, status = error
        return jsonify({"ok": False, "error": message}), status

    record = add_record(note_text, summary, mode)
    return jsonify({"ok": True, "summary": summary, "record": record})


@app.route("/api/history")
def history():
    return jsonify(list(reversed(load_history())))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)