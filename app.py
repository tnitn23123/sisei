import streamlit as st
import streamlit.components.v1 as components

# --- Streamlitのロゴやメニューを完全に隠す設定 ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    stDeployButton {display:none;}
    div[data-testid="stToolbar"] {display: none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("✨ ストリームライン：AIリアルタイム姿勢モニター")
st.write("カメラがオンになると、AI（MoveNet）が自動的に頭、肩、腰、膝を検出し、姿勢が良いか悪いかを判定します。")

# 🆕 JavaScriptベースの超軽量・超高速リアルタイムAI骨格検出システム
html_code = """
<!DOCTYPE html>
<html>
<head>
    <!-- TensorFlow.js と MoveNet AIモデルの読み込み -->
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #fff; margin: 0; padding: 0; }
        #video-container { position: relative; width: 640px; height: 480px; background: #222; border-radius: 8px; overflow: hidden; }
        video { transform: scaleX(-1); width: 640px; height: 480px; position: absolute; top:0; left:0; }
        canvas { transform: scaleX(-1); position: absolute; top:0; left:0; z-index: 10; }
        #status-box { width: 620px; margin-top: 15px; padding: 15px; border-radius: 8px; font-size: 20px; font-weight: bold; text-align: center; background: #f0f2f6; }
        .good { background: #d4edda !important; color: #155724; }
        .poor { background: #f8d7da !important; color: #721c24; }
    </style>
</head>
<body>

    <div id="video-container">
        <video id="webcam" autoplay playsinline muted></video>
        <canvas id="output"></canvas>
    </div>
    <div id="status-box">🔄 AIモデルを読み込んでいます。カメラを許可してください...</div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('output');
        const ctx = canvas.getContext('2d');
        const statusBox = document.getElementById('status-box');
        let detector;

        async function setupCamera() {
            const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 }, audio: false });
            video.srcObject = stream;
            return new Promise((resolve) => { video.onloadedmetadata = () => { resolve(video); }; });
        }

        async function init() {
            // 軽量かつ高速な骨格検出AI「MoveNet」を初期化
            detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet, {
                modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING
            });
            await setupCamera();
            video.play();
            canvas.width = 640;
            canvas.height = 480;
            detectPose();
        }

        async function detectPose() {
            const poses = await detector.estimatePoses(video);
            ctx.clearRect(0, 0, 640, 480);

            if (poses.length > 0) {
                const keypoints = poses[0].keypoints;
                
                // 主要な部位のポイントを取得 (MoveNetのインデックス: 0=鼻, 5=左肩, 6=右肩, 11=左腰, 12=右腰, 13=左膝, 14=右膝)
                const nose = keypoints[0];
                const leftShoulder = keypoints[5];
                const rightShoulder = keypoints[6];
                const leftHip = keypoints[11];
                const rightHip = keypoints[12];
                const leftKnee = keypoints[13];
                const rightKnee = keypoints[14];

                // 骨格を描画する関数
                function drawLine(p1, p2) {
                    if (p1.score > 0.3 && p2.score > 0.3) {
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = '#bcbcbc';
                        ctx.lineWidth = 3;
                        ctx.stroke();
                    }
                }

                function drawKeypoint(kp, color) {
                    if (kp.score > 0.3) {
                        ctx.beginPath();
                        ctx.arc(kp.x, kp.y, 8, 0, 2 * Math.PI);
                        ctx.fillStyle = color;
                        ctx.fill();
                    }
                }

                // 線をつなぐ
                drawLine(leftShoulder, rightShoulder);
                drawLine(leftShoulder, leftHip);
                drawLine(rightShoulder, rightHip);
                drawLine(leftHip, leftKnee);
                drawLine(rightHip, rightKnee);

                // 単色ドットを打つ (上から順に 赤、緑、青、黄)
                drawKeypoint(nose, '#ff0000');           // 頭(鼻): 赤
                drawKeypoint(leftShoulder, '#00ff00');   // 背中(肩): 緑
                drawKeypoint(leftHip, '#0078ff');        // 手元(腰): 青
                drawKeypoint(leftKnee, '#ffd700');       // 膝: 黄
                drawKeypoint(rightShoulder, '#00ff00');
                drawKeypoint(rightHip, '#0078ff');
                drawKeypoint(rightKnee, '#ffd700');

                // 📐 姿勢の良し悪しをリアルタイム自動判定
                if (nose.score > 0.3 && leftHip.score > 0.3) {
                    // 横向き・斜め向き時の頭の前方突き出しを計算
                    const diffX = Math.abs(nose.x - leftHip.x);
                    if (diffX > 75) { 
                        status_text = "🔴 姿勢が崩れています！背中が丸まっているか、頭が前に出ています。";
                        statusBox.className = "poor";
                    } else {
                        status_text = "🟢 素晴らしい姿勢です！そのままキープしましょう。";
                        statusBox.className = "good";
                    }
                    statusBox.innerText = status_text;
                }
            }
            requestAnimationFrame(detectPose);
        }

        window.onload = init;
    </script>
</body>
</html>
"""

# HTMLコンポーネントを画面に埋め込み
components.html(html_code, height=600)



    
