# 🖐 GestureDigit AI — Hand Gesture + Digit Recognition

Real-time AI that detects **hand gestures** AND **finger count as digits (0–5)**
using your webcam, OpenCV, MediaPipe, and Flask.

---

## 🚀 How to Run

### Step 1 — Create venv on C: drive (avoids disk space issues on D:)
```
python -m venv C:\gesture_venv
C:\gesture_venv\Scripts\activate
```

### Step 2 — Go to project folder
```
cd "D:\Clg Projects\gesture_digit_ai"
```

### Step 3 — Install packages
```
pip install flask opencv-python mediapipe numpy --no-cache-dir
```

### Step 4 — Run
```
python app.py
```

### Step 5 — Open browser
```
http://localhost:5000
```

---

## ✨ What It Does

| Feature | Details |
|---|---|
| 🔢 Digit Recognition | Counts raised fingers → shows digit 0–5 |
| 🤟 Gesture Recognition | Names 10+ gestures (Fist, Peace, Rock On…) |
| 🖐 Finger Indicators | Visual on/off display for each finger |
| 👐 Two Hands | Detects both hands at once |
| 📋 Detection Log | Timestamped history of all detections |
| 📊 Session Stats | Total, gesture, digit counters + FPS |
| 🎨 Modern UI | Dark neon design with color-coded output |

---

## 🖐 Digit → Finger Mapping

| Digit | Fingers Raised |
|---|---|
| 0 | None (Fist) |
| 1 | Index only |
| 2 | Index + Middle |
| 3 | Index + Middle + Ring |
| 4 | All except Thumb |
| 5 | All 5 fingers |

---

## 🛠 Troubleshooting

**Camera not found:** Change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)` in app.py

**Model download fails:** Manually download from:
https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
Place it in the same folder as app.py

**Port in use:** Change `port=5000` to `port=5001` in app.py
