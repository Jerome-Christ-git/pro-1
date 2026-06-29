from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import numpy as np
import time
import os
import urllib.request

app = Flask(__name__)

# ─── Download MediaPipe model ─────────────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
if not os.path.exists(MODEL_PATH):
    print("Downloading hand_landmarker.task (~8 MB)...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
        MODEL_PATH
    )
    print("Model downloaded!")

# ─── MediaPipe Setup ──────────────────────────────────────────────────────────
BaseOptions           = mp.tasks.BaseOptions
HandLandmarker        = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode     = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.5
)
landmarker = HandLandmarker.create_from_options(options)

# ─── Hand connections for drawing ────────────────────────────────────────────
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),(0,17)
]

FINGER_TIPS  = [4, 8, 12, 16, 20]
FINGER_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# ─── Finger counting ──────────────────────────────────────────────────────────
def count_fingers(lm, hand_label):
    fingers = []
    # Thumb
    if hand_label == "Right":
        fingers.append(1 if lm[4].x < lm[3].x else 0)
    else:
        fingers.append(1 if lm[4].x > lm[3].x else 0)
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if lm[tip].y < lm[tip-2].y else 0)
    return fingers

# ─── Digit recognition from fingers ──────────────────────────────────────────
def finger_to_digit(fingers):
    """Map finger pattern to digit 0-10"""
    total = sum(fingers)
    patterns = {
        (0,0,0,0,0): ("0", "Zero"),
        (0,1,0,0,0): ("1", "One"),
        (0,1,1,0,0): ("2", "Two"),
        (0,1,1,1,0): ("3", "Three"),
        (0,1,1,1,1): ("4", "Four"),
        (1,1,1,1,1): ("5", "Five"),
        (1,1,0,0,1): ("6", "Six"),   # thumb+index+pinky
        (0,1,1,1,0): ("3", "Three"),
        (1,0,0,0,0): ("thumb","Thumb Up" if True else "Thumb"),
    }
    key = tuple(fingers)
    if key in patterns:
        return patterns[key]
    # fallback: count total
    return (str(total), f"{total} Fingers")

# ─── Gesture recognition ──────────────────────────────────────────────────────
def recognize_gesture(lm, hand_label):
    f = count_fingers(lm, hand_label)
    total = sum(f)

    # Digit first
    digit_num, digit_name = finger_to_digit(f)

    # Named gesture
    if   f == [0,0,0,0,0]: gesture = ("✊", "Fist",        "#EF4444")
    elif f == [1,1,1,1,1]: gesture = ("🖐", "Open Hand",   "#10B981")
    elif f == [0,1,0,0,0]: gesture = ("☝️", "Pointing",    "#3B82F6")
    elif f == [0,1,1,0,0]: gesture = ("✌️", "Peace / V",   "#8B5CF6")
    elif f == [1,0,0,0,1]: gesture = ("🤙", "Hang Loose",  "#06B6D4")
    elif f == [0,1,0,0,1]: gesture = ("🤘", "Rock On",     "#F97316")
    elif f == [0,0,0,0,1]: gesture = ("🤙", "Pinky Up",    "#EC4899")
    elif f == [1,1,1,1,0]: gesture = ("🖖", "Four Fingers","#6366F1")
    elif f == [1,0,0,0,0]:
        up = lm[4].y < lm[3].y
        gesture = ("👍","Thumbs Up","#22C55E") if up else ("👎","Thumbs Down","#EF4444")
    elif f == [0,1,1,1,0]: gesture = ("🤟", "Three",       "#14B8A6")
    elif total == 2:        gesture = ("✌️", "Two",         "#A855F7")
    else:                   gesture = ("🤚", f"{total} Fingers", "#64748B")

    return {
        "emoji":   gesture[0],
        "gesture": gesture[1],
        "color":   gesture[2],
        "digit":   digit_num,
        "digit_name": digit_name,
        "fingers": f,
        "total":   total
    }

# ─── Draw skeleton ────────────────────────────────────────────────────────────
def draw_hand(frame, lm_list, color=(80,200,120)):
    h, w = frame.shape[:2]
    pts = [(int(l.x*w), int(l.y*h)) for l in lm_list]
    for a,b in HAND_CONNECTIONS:
        cv2.line(frame, pts[a], pts[b], color, 2, cv2.LINE_AA)
    for i,(x,y) in enumerate(pts):
        dot_color = (124,58,237) if i in FINGER_TIPS else (255,255,255)
        cv2.circle(frame, (x,y), 6, dot_color, -1)
        cv2.circle(frame, (x,y), 6, (0,0,0), 1)

def draw_digit_box(frame, lm, digit_info, hand_label, w, h):
    """Draw a styled digit + gesture box near the hand"""
    cx = int(lm[0].x * w)
    cy = int(lm[0].y * h)

    # Parse color
    hex_color = digit_info["color"].lstrip("#")
    r,g,b = tuple(int(hex_color[i:i+2],16) for i in (0,2,4))
    bgr = (b,g,r)

    # Box position
    bw, bh = 200, 80
    bx = max(0, min(cx - bw//2, w - bw))
    by = max(0, min(cy - bh - 20, h - bh))

    # Background
    overlay = frame.copy()
    cv2.rectangle(overlay, (bx,by),(bx+bw,by+bh),(10,10,20),-1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    # Colored top bar
    cv2.rectangle(frame,(bx,by),(bx+bw,by+4),bgr,-1)

    # Big digit
    digit_text = digit_info["digit"]
    (dw,dh),_ = cv2.getTextSize(digit_text, cv2.FONT_HERSHEY_SIMPLEX, 1.8, 3)
    cv2.putText(frame, digit_text, (bx+12, by+dh+10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.8, bgr, 3, cv2.LINE_AA)

    # Gesture name
    gname = f"{digit_info['emoji']} {digit_info['gesture']}"
    cv2.putText(frame, gname[:20], (bx+60, by+32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220,220,220), 1, cv2.LINE_AA)

    # Digit name
    cv2.putText(frame, digit_info["digit_name"], (bx+60, by+52),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160,160,160), 1, cv2.LINE_AA)

    # Hand label
    cv2.putText(frame, hand_label, (bx+60, by+70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100,100,100), 1, cv2.LINE_AA)

    # Finger dots indicator
    for idx, val in enumerate(digit_info["fingers"]):
        dot_x = bx + 8 + idx*10
        dot_y = by + bh - 8
        dot_c = bgr if val else (50,50,50)
        cv2.circle(frame, (dot_x, dot_y), 4, dot_c, -1)

# ─── Global state ─────────────────────────────────────────────────────────────
current_state = {
    "gesture": "No hand", "emoji": "—", "digit": "—",
    "digit_name": "—", "color": "#64748B", "hands": 0, "fps": 0,
    "fingers": [0,0,0,0,0], "total": 0
}
camera = None

def get_camera():
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
    return camera

# ─── Frame generator ──────────────────────────────────────────────────────────
def generate_frames():
    global current_state
    prev_time = time.time()
    cam = get_camera()

    while True:
        ok, frame = cam.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_img)

        detected = []

        if result.hand_landmarks:
            for idx, lm in enumerate(result.hand_landmarks):
                hand_label = result.handedness[idx][0].display_name
                info = recognize_gesture(lm, hand_label)
                detected.append((info, hand_label, lm))

                # Skeleton color based on gesture
                hex_c = info["color"].lstrip("#")
                r,g,b = tuple(int(hex_c[i:i+2],16) for i in (0,2,4))
                draw_hand(frame, lm, color=(b,g,r))
                draw_digit_box(frame, lm, info, hand_label, w, h)

        # FPS overlay
        curr_time = time.time()
        fps = int(1 / max(curr_time - prev_time, 1e-6))
        prev_time = curr_time

        cv2.rectangle(frame,(0,0),(230,40),(8,8,15),-1)
        cv2.putText(frame, f"FPS: {fps}  |  Hands: {len(detected)}", (8,26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80,255,160), 2, cv2.LINE_AA)

        # Mode label
        cv2.rectangle(frame,(w-220,0),(w,40),(8,8,15),-1)
        cv2.putText(frame,"GESTURE + DIGIT AI",(w-215,26),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(180,100,255),1,cv2.LINE_AA)

        # Update state
        if detected:
            info, hand_label, _ = detected[0]
            current_state = {**info, "hands": len(detected), "fps": fps,
                             "all": [{"gesture":d[0]["gesture"],"emoji":d[0]["emoji"],
                                      "digit":d[0]["digit"],"digit_name":d[0]["digit_name"],
                                      "color":d[0]["color"],"hand":d[1]} for d in detected]}
        else:
            current_state = {
                "gesture":"No hand","emoji":"—","digit":"—","digit_name":"—",
                "color":"#64748B","hands":0,"fps":fps,"fingers":[0,0,0,0,0],"total":0
            }

        _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n')

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/state')
def state():
    return jsonify(current_state)

if __name__ == '__main__':
    print("🖐  GestureDigit AI — http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
