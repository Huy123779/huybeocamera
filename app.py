from flask import Flask, Response, render_template
import cv2
import threading

# Thay URL bằng đường dẫn RTSP của camera Ezviz
RTSP_URL = "rtsp://admin:MJALPE@192.168.1.8:554/live"

app = Flask(__name__)

# Biến toàn cục để lưu frame
frame_global = None
lock = threading.Lock()

def capture_frames():
    """Luồng chạy nền để lấy video từ camera RTSP."""
    global frame_global
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2)  # Giảm buffer để giảm độ trễ
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        with lock:
            frame_global = frame

# Chạy luồng lấy video
threading.Thread(target=capture_frames, daemon=True).start()

def generate_frames():
    """Truyền frame đến trình duyệt."""
    global frame_global
    while True:
        with lock:
            if frame_global is None:
                continue
            ret, buffer = cv2.imencode('.jpg', frame_global, [cv2.IMWRITE_JPEG_QUALITY, 95])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)