import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

# --- Streamlitのロゴやメニューを完全に隠す設定 ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    stDeployButton {display:none;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 💡 サイトタイトル
st.title("✨ ストリームライン：多角分析姿勢モニター")

# 📸 STEP 1: 撮影アングルの選択
st.subheader("📸 STEP 1: 撮影した向きを選んでください")
angle_choice = st.radio(
    "写真の向きによって、採点するポイントが変わります：",
    ["① 真横から撮影（背中・頭の突き出しメイン）", 
     "② 斜め前から撮影（デスクワークの姿勢・膝や手元メイン）", 
     "③ 真正面から撮影（肩の左右の高さ・中心のズレ）"]
)

st.write("---")
uploaded_file = st.file_uploader("写真をアップロードしてください（jpg, png）", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    h, w, _ = image_np.shape
    
    col1, col2 = st.columns(2)
    annotated_image = image_np.copy()
    
    # モード別のパーツ名と初期配置（重ならないように高さを分散）
    pts = {}
    colors = {
        "P1": (0, 0, 255),    # 赤
        "P2": (0, 255, 0),  # 緑
        "P3": (255, 120, 0),  # 青
        "P4": (0, 255, 255)   # 黄
    }
    
    with col2:
        st.subheader("⚙️ マーカー位置調整 & 部分採点")
        st.write("スライダーを動かして、点（マーカー）をピッタリ合わせてください。")
        
        if "真横から" in angle_choice:
            st.markdown("### 🟢 真横モードの調整")
            head_x = st.slider("💀 頭（耳の穴）の左右位置", 0, 100, 45)
            back_x = st.slider("🦴 背中の中心の左右位置", 0, 100, 50)
            hand_x = st.slider("👋 手（手首）の左右位置", 0, 100, 42)
            knee_x = st.slider("🦵 膝の皿の左右位置", 0, 100, 38)
            
            # 各パーツに名前をつけて配置
            pts = {
                "HEAD": (int(w * (head_x / 100)), int(h * 0.25)),
                "BACK": (int(w * (back_x / 100)), int(h * 0.45)),
                "HAND": (int(w * (hand_x / 100)), int(h * 0.60)),
                "KNEE": (int(w * (knee_x / 100)), int(h * 0.75))
            }
            colors = {"HEAD": (0, 0, 255), "BACK": (0, 255, 0), "HAND": (255, 120, 0), "KNEE": (0, 255, 255)}
            
            # 採点ロジック
            head_error = abs(back_x - head_x)
            score_back = max(0, 100 - head_error * 4)
            total_score = int(score_back)
            
            status_text = "🟢 頭と背中のラインが綺麗に揃っています！" if total_score >= 85 else (
                "🟡 頭が少し前に出て猫背・スマホ首の傾向があります。" if total_score >= 60 else
                "🔴 強い猫背、または顎が前に突き出た姿勢です。骨盤を立てましょう。"
            )

        elif "斜め前から" in angle_choice:
            st.markdown("### 🔵 斜め前モードの調整")
            head_y = st.slider("💀 頭の高さ (上下)", 0, 100, 25)
            back_x = st.slider("🦴 背中の丸み (左右)", 0, 100, 45)
            hand_y = st.slider("👋 手（机）の高さ (上下)", 0, 100, 55)
            knee_y = st.slider("🦵 膝の高さ (上下)", 0, 100, 75)
            
            pts = {
                "HEAD": (int(w * 0.5), int(h * (head_y / 100))),
                "BACK": (int(w * (back_x / 100)), int(h * 0.45)),
                "HAND": (int(w * 0.45), int(h * (hand_y / 100))),
                "KNEE": (int(w * 0.4), int(h * (knee_y / 100)))
            }
            colors = {"HEAD": (0, 0, 255), "BACK": (0, 255, 0), "HAND": (255, 120, 0), "KNEE": (0, 255, 255)}
            
            score_back = max(0, 100 - abs(back_x - 50) * 5)
            total_score = int(score_back)
            status_text = "🟢 背すじが程よく伸びた良い姿勢バランスです！" if total_score >= 85 else "🔴 背中が丸まりすぎています。椅子に深く座りましょう。"

        else:
            # 🆕 正面モードのバグを完全に修正！
            st.markdown("### 🟡 真正面モードの調整")
            head_x = st.slider("💀 頭（鼻すじ）の左右ブレ", 0, 100, 50)
            shoulder_y = st.slider("📏 両肩の上下基準位置", 0, 100, 35)
            shoulder_tilt = st.slider("⚖️ 肩の左右の傾き（バランス）", -20.0, 20.0, 0.0, step=0.5)
            
            cx, cy = int(w * (head_x / 100)), int(h * (shoulder_y / 100))
            rad = np.radians(shoulder_tilt)
            arm_len = int(w * 0.18) # 肩幅の長さ
            
            # 正面モード専用の点（頭、首の付け根、左肩、右肩）
            pts = {
                "HEAD": (cx, int(h * 0.20)),
                "NECK": (cx, cy),
                "L-SHOULDER": (int(cx - arm_len * np.cos(rad)), int(cy - arm_len * np.sin(rad))),
                "R-SHOULDER": (int(cx + arm_len * np.cos(rad)), int(cy + arm_len * np.sin(rad)))
            }
            colors = {"HEAD": (0, 0, 255), "NECK": (0, 255, 0), "L-SHOULDER": (255, 120, 0), "R-SHOULDER": (255, 0, 255)}
            
            tilt_error = abs(shoulder_tilt)
            center_error = abs(head_x - 50)
            total_score = max(0, int(100 - (tilt_error * 4.5) - (center_error * 1.5)))
            
            status_text = "🟢 左右対称で非常にバランスが良い真っ直ぐな姿勢です！" if total_score >= 85 else (
                "🟡 片方の肩が下がるなど、左右の重心が少し偏っています。" if total_score >= 60 else
                "🔴 体の軸が左右に大きく傾いています。足を組む癖などを見直しましょう。"
            )

        # 🏆 スコア表示
        st.write("---")
        st.metric(label="🏆 総合姿勢スコア", value=f"{total_score} / 100 点")
        if total_score >= 85: st.success(status_text)
        elif total_score >= 60: st.warning(status_text)
        else: st.error(status_text)

    # --- 🎨 画像描画処理（バグ修正版） ---
    pt_list = list(pts.values())
    
    # 骨格線の描画（正面モードとそれ以外で繋ぎ方を変える）
    if "真正面から" in angle_choice and len(pt_list) == 4:
        # 頭から首、首から左右の肩へ綺麗に線を引く
        cv2.line(annotated_image, pt_list[0], pt_list[1], (200, 200, 200), 2, cv2.LINE_AA)
        cv2.line(annotated_image, pt_list[1], pt_list[2], (200, 200, 200), 2, cv2.LINE_AA)
        cv2.line(annotated_image, pt_list[1], pt_list[3], (200, 200, 200), 2, cv2.LINE_AA)
    else:
        for i in range(len(pt_list) - 1):
            cv2.line(annotated_image, pt_list[i], pt_list[i+1], (200, 200, 200), 2, cv2.LINE_AA)

    # 各パーツに円と文字を打つ
    for name, pos in pts.items():
        color = colors.get(name, (255, 255, 255))
        cv2.circle(annotated_image, pos, 8, color, -1)
        cv2.circle(annotated_image, pos, 10, (255, 255, 255), 1)
        # 文字の背景に黒い影を入れて、白い服の上でも読めるようにする
        cv2.putText(annotated_image, name, (pos[0] + 12, pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(annotated_image, name, (pos[0] + 12, pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    # 上部の黒い文字盤ボックスを確実に描画
    score_display = f"MODE: FRONT/SIDE | SCORE: {total_score}"
    cv2.rectangle(annotated_image, (0, 0), (w, 60), (0, 0, 0), -1)
    cv2.putText(annotated_image, score_display, (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    # 💾 ダウンロードデータ化
    result_img = Image.fromarray(annotated_image)
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    with col1:
        st.subheader("📊 姿勢モニター（骨格ガイド）")
        st.image(annotated_image, caption="スライダーでお好みの位置に調整してください", use_container_width=True)
        st.download_button(
            label="💾 この測定結果を保存する",
            data=byte_im,
            file_name="posture_analysis.png",
            mime="image/png"
        )






    
