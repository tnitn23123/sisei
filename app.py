import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import mediapipe as mp

# --- Streamlitのロゴやメニューを隠す設定 ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("✨ ストリームライン：AIリアルタイム姿勢モニター")
st.write("カメラをオンにすると、AIが自動的に骨格（頭・肩・腰・膝）を検出してリアルタイムにガイド線を引きます。")

# MediaPipe Pose（骨格検出AI）の準備
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

class PostureProcessor(VideoProcessorBase):
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # カメラ映像をNumPy配列（BGR形式）に変換
        img = frame.to_ndarray(format="bgr24")
        
        # AI処理のためにRGBに変換
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)
        
        # 骨格が検出された場合、映像の上に点と線を自動描画
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                img, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=3, circle_radius=4), # 点は緑
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2) # 線は白
            )
            
            # --- 簡易的な自動姿勢判定 ---
            landmarks = results.pose_landmarks.landmark
            # 鼻（頭）、左肩、左腰のランドマークを取得
            nose = landmarks[mp_pose.PoseLandmark.NOSE]
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            
            # 横を向いている時の、腰に対する頭の突き出し度合い（簡易判定）
            diff = abs(nose.x - hip.x)
            if diff > 0.15:
                status_text = "⚠️ POOR POSTURE (NEKOBE)"
                color = (0, 0, 255) # 赤
            else:
                status_text = "GOOD POSTURE"
                color = (0, 255, 0) # 緑
                
            # 映像の左上にリアルタイム判定を表示
            cv2.putText(img, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3, cv2.LINE_AA)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# リアルタイムビデオ配信コンポーネントを画面に設置
webrtc_streamer(
    key="posture-analysis",
    video_processor_factory=PostureProcessor,
    media_stream_constraints={"video": True, "audio": False}, # カメラのみ（音声オフ）
    rtc_configuration={"iceServers": [{"urls": ["stun:://google.com"]}]} # 接続用サーバー設定
)




    
