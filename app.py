from flask import Flask, Response, render_template_string
import cv2
import threading
import os

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
def home():
    html_content = """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fire Suppression Systems</title>
        <link rel="icon" href="favicon.ico" type="image/x-icon">
        <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js"></script>
        <script src="https://www.gstatic.com/firebasejs/8.10.1/firebase-database.js"></script>
        <style>
            body {
                text-align: center;
                font-family: Arial, sans-serif;
                background: linear-gradient(to bottom, #87CEEB, #4682B4);
                color: white;
            }
            h2 {
                font-size: 36px;
                color: #FFD700;
                text-shadow: 4px 4px 6px rgba(0, 0, 0, 0.6);
                padding: 20px;
            }
            .mode-switch {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
            }
            .mode-switch button {
                padding: 10px 20px;
                font-size: 18px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                background-color: #ff5733;
                color: white;
                box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.5);
            }
            .mode-switch button:hover {
                background-color: #c70039;
            }
            .control-buttons {
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-top: 20px;
            }
            .row {
                display: flex;
                justify-content: center;
            }
            .control-buttons button {
                width: 80px;
                height: 80px;
                margin: 10px;
                font-size: 18px;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                background-color: #007bff;
                color: white;
                box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.6);
            }
            .control-buttons button:hover {
                background-color: #0056b3;
            }
            .active {
                background-color: #28a745 !important;
                box-shadow: 0px 0px 15px rgba(0, 255, 0, 0.8);
            }
            .video-container {
                margin-top: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h2>Fire Suppression Systems</h2>

        <!-- Hiển thị video từ camera -->
        <div class="video-container">
            <h3>Camera Giám Sát</h3>
            <img src="{{ url_for('video_feed') }}" width="320" height="240">
        </div>

        <!-- Chế độ điều khiển -->
        <div class="mode-switch">
            <button onclick="setMode('manual')">Bằng Tay</button>
            <button id="mayBom" onclick="toggleControl('mayBom')">💧</button>
            <button onclick="setMode('auto')">Tự Động</button>
        </div>

        <div class="control-buttons">
            <div class="row">
                <button id="toi" onclick="toggleControl('toi')">▲</button>
            </div>
            <div class="row">
                <button id="trai" onclick="toggleControl('trai')">◀</button>
                <button id="dung" onclick="stopAll()">■</button>
                <button id="phai" onclick="toggleControl('phai')">▶</button>
            </div>
            <div class="row">
                <button id="lui" onclick="toggleControl('lui')">▼</button>
            </div>
        </div>

        <script>
            var firebaseConfig = {
                apiKey: "AIzaSyAIOOTrB8GF1UdjHvMEQcMpIU5hActSMhI",
                authDomain: "esp32-control-ec470.firebaseapp.com",
                databaseURL: "https://esp32-control-ec470-default-rtdb.firebaseio.com",
                projectId: "esp32-control-ec470",
                storageBucket: "esp32-control-ec470.firebasestorage.app",
                messagingSenderId: "548864181367",
                appId: "1:548864181367:web:801037ada43188d023b272"
            };
            firebase.initializeApp(firebaseConfig);
            var database = firebase.database();

            function setMode(mode) {
                database.ref("/Dieu_Khien_Thiet_Bi/mode").set(mode);
            }
            
            function toggleControl(command) {
                var button = document.getElementById(command);
                var isActive = button.classList.contains("active");
                stopAll();
                if (!isActive) {
                    database.ref("/Dieu_Khien_Thiet_Bi/" + command).set("ON");
                    button.classList.add("active");
                }
            }

            function stopAll() {
                let commands = ["toi", "trai", "phai", "lui", "mayBom"];
                commands.forEach(cmd => {
                    database.ref("/Dieu_Khien_Thiet_Bi/" + cmd).set("OFF");
                    document.getElementById(cmd).classList.remove("active");
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    # Đảm bảo Flask lắng nghe tất cả kết nối và sử dụng cổng đúng
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 3000)))


