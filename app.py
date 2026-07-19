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
    iframe { width: 100% !important; height: 550px !important; border: none; }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("✨ ストリームライン：AIリアルタイム姿勢モニター")
st.write("カメラをオンにすると、AIがあなたの頭・肩・腰・膝を自動検出して姿勢を採点します。")

# 🆕 スマホのカメラ制限（ブロックバグ）を完全に回避した特別版JavaScriptコード
html_code = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- TensorFlow.js と AIモデル（MoveNet）を高速読み込み -->
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #fff; margin: 0; padding: 10px; box-sizing: border-box; }
        #video-container { position: relative; width: 100%; max-width: 480px; aspect-ratio: 4/3; background: #222; border-radius: 12px; overflow: hidden; }
        video { transform: scaleX(-1); width: 100%; height: 100%; object-fit: cover; position: absolute; top:0; left:0; }
        canvas { transform: scaleX(-1); width: 100%; height: 100%; position: absolute; top:0; left:0; z-index: 10; pointer-events: none; }
        #status-box { width: 100%; max-width: 480px; margin-top: 12px; padding: 12px; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; background: #f0f2f6; box-sizing: border-box; }
        .good { background: #d4edda !important; color: #155724; border: 1px solid #c3e6cb; }
        .poor { background: #f8d7da !important; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>

    <div id="video-container">
        <!-- スマホのインカメラを強制起動する設定を付与 -->
        <video id="webcam" autoplay playsinline muted></video>
        <canvas id="output"></canvas>
    </div>
    <div id="status-box">🔄 AIの準備中... カメラの許可ポップアップが出たら「許可」を押してください</div>

    <script>
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('output');
        const ctx = canvas.getContext('2d');
        const statusBox = document.getElementById('status-box');
        let detector;

        async function init() {
            try {
                // AIモデルを起動
                detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet, {
                    modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING
                });
                
                // スマホ・PC共通でカメラを確実に呼び出す特別設定
                const constraints = {
                    video: {
                        facingMode: "user", // 自撮り用インカメラを指定
                        width: { ideal: 640 },
                        height: { ideal: 480 }
                    },
                    audio: false
                };
                
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    video.play();
                    detectPose();
                };
            } catch (err) {
                statusBox.className = "poor";
                statusBox.innerText = "❌ カメラの起動に失敗しました。ブラウザの設定でカメラを許可するか、Safari/Chromeアプリで開き直してください。";
            }
        }

        async function detectPose() {
            if (!detector) return;
            const poses = await detector.estimatePoses(video);
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (poses.length > 0) {
                const keypoints = poses[0].keypoints;
                
                const nose = keypoints[0];
                const leftShoulder = keypoints[5];
                const rightShoulder = keypoints[6];
                const leftHip = keypoints[11];
                const rightHip = keypoints[12];
                const leftKnee = keypoints[13];
                const rightKnee = keypoints[14];

                function drawLine(p1, p2) {
                    if (p1 && p2 && p1.score > 0.3 && p2.score > 0.3) {
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = '#bcbcbc';
                        ctx.lineWidth = 3;
                        ctx.stroke();
                    }
                }

                function drawKeypoint(kp, color) {
                    if (kp && kp.score > 0.3) {
                        ctx.beginPath();
                        ctx.arc(kp.x, kp.y, 8, 0, 2 * Math.PI);
                        ctx.fillStyle = color;
                        ctx.fill();
                    }
                }

                // 体の骨格ガイドラインを描画
                drawLine(leftShoulder, rightShoulder);
                drawLine(leftShoulder, leftHip);
                drawLine(rightShoulder, rightHip);
                drawLine(leftHip, leftKnee);
                drawLine(rightHip, rightKnee);

                // 単色ドットを打つ (赤、緑、青、黄)
                drawKeypoint(nose, '#ff0000');           // 頭: 赤
                drawKeypoint(leftShoulder, '#00ff00');   // 肩: 緑
                drawKeypoint(rightShoulder, '#00ff00');
                drawKeypoint(leftHip, '#0078ff');        // 腰: 青
                drawKeypoint(rightHip, '#0078ff');
                drawKeypoint(leftKnee, '#ffd700');       // 膝: 黄
                drawKeypoint(rightKnee, '#ffd700');

                // 姿勢自動採点の判定ロジック
                if (nose.score > 0.3 && leftHip.score > 0.3) {
                    const diffX = Math.abs(nose.x - leftHip.x);
                    // 画面サイズに合わせてズレの判定幅を自動調整
                    const threshold = canvas.width * 0.12; 
                    if (diffX > threshold) {
                        statusBox.className = "poor";
                        statusBox.innerText = "🔴 姿勢が崩れています！頭が前に突き出ているか、猫背の可能性があります。";
                    } else {
                        statusBox.className = "good";
                        statusBox.innerText = "🟢 素晴らしい姿勢です！そのままキープしましょう。";
                    }
                }
            }
            requestAnimationFrame(detectPose);
        }

        // 起動処理
        init();
    </script>
</body>
</html>
"""

# スマホでも枠崩れしないよう設定を最適化して画面にセット
components.html(html_code, height=550)




    
