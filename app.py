import streamlit as st
import numpy as np
from PIL import Image, ImageDraw
import io  # 🆕 漏れていたパーツを確実に追加しました！

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

st.title("✨ ストリームライン：多角分析姿勢モニター")
st.write("下のカメラで撮影するか、写真をアップロードしたあと、スライダーで体の隙間に点を合わせてください。")

# 📸 スマホカメラと画像アップロードの両方に対応
img_file = st.camera_input("📸 ここを押して写真を撮影してください")
uploaded_file = st.file_uploader("または、スマホ内の写真を選ぶ（jpg, png）", type=["jpg", "png", "jpeg"])

# どちらかに入力があれば処理を開始
target_file = img_file if img_file is not None else uploaded_file

if target_file is not None:
    image = Image.open(target_file).convert("RGB")
    w, h = image.size
    
    # 画面を2分割（スマホでは自動で縦並びになります）
    col1, col2 = st.columns(2)
    
    with col2:
        st.subheader("⚙️ マーカー位置調整 & 採点")
        st.write("スライダーを動かして、4つの点（上から頭・背中・手・膝）を写真の体の位置にピッタリ合わせてください。")
        
        # 指でも操作しやすいスライダー（初期位置を人間の体型に合わせました）
        p1_x = st.slider("🔴 1番目の点（頭）の左右位置", 0, 100, 50)
        p2_x = st.slider("🟢 2番目の点（背中）の左右位置", 0, 100, 50)
        p3_x = st.slider("🔵 3番目の点（手）の左右位置", 0, 100, 48)
        p4_x = st.slider("🟡 4番目の点（膝）の左右位置", 0, 100, 45)
        
        # 採点ロジック（背中に対する頭のズレで計算）
        head_error = abs(p2_x - p1_x)
        total_score = max(0, 100 - head_error * 4)
        
        # 姿勢アドバイス
        if total_score >= 85:
            status_text = "🟢 頭と背中のラインが綺麗に揃っています！素晴らしい姿勢です。"
            st.success(status_text)
        elif total_score >= 60:
            status_text = "🟡 頭が少し前に出て猫背・スマホ首の傾向があります。"
            st.warning(status_text)
        else:
            status_text = "🔴 強い猫背、または顎が前に突き出た姿勢です。骨盤を立てましょう。"
            st.error(status_text)
            
        st.metric(label="🏆 総合姿勢スコア", value=f"{total_score} / 100 点")

    # --- 🎨 写真の上への描画処理 ---
    annotated_image = image.copy()
    draw = ImageDraw.Draw(annotated_image)
    
    # スライダーの値に合わせて点の座標を計算
    pts = {
        "P1": (int(w * (p1_x / 100)), int(h * 0.25)), # 頭
        "P2": (int(w * (p2_x / 100)), int(h * 0.45)), # 背中
        "P3": (int(w * (p3_x / 100)), int(h * 0.60)), # 手
        "P4": (int(w * (p4_x / 100)), int(h * 0.75))  # 膝
    }
    
    colors = {
        "P1": (255, 0, 0),    # 赤
        "P2": (0, 255, 0),    # 緑
        "P3": (0, 120, 255),  # 青
        "P4": (255, 215, 0)   # 黄
    }
    
    # 1. 骨格ガイドラインを結ぶ（細いグレーの線）
    pt_list = list(pts.values())
    for i in range(len(pt_list) - 1):
        draw.line([pt_list[i], pt_list[i+1]], fill=(180, 180, 180), width=3)
        
    # 2. 単色ドットを打つ（中心に白い穴がないきれいな丸）
    radius = max(8, int(w * 0.015))
    for name, pos in pts.items():
        color = colors[name]
        left_up = (pos - radius, pos - radius)
        right_down = (pos + radius, pos + radius)
        draw.ellipse([left_up, right_down], fill=color)
        
    # 3. 上部の文字盤（確実に真っ黒な帯に白文字）
    box_height = max(40, int(h * 0.08))
    draw.rectangle([(0, 0), (w, box_height)], fill=(20, 20, 20))
    score_display = f"POSTURE SCORE: {total_score}"
    draw.text((20, int(box_height * 0.25)), score_display, fill=(255, 255, 255))

    with col1:
        st.subheader("📊 姿勢モニター（骨格ガイド）")
        st.image(annotated_image, caption="スライダーを動かして隙間に点を合わせてください", use_container_width=True)
        
        # 💾 保存用データの作成
        buf = io.BytesIO()
        annotated_image.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="💾 この測定結果を保存する",
            data=byte_im,
            file_name="posture_analysis.png",
            mime="image/png"
        )


    
