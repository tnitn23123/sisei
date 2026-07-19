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

# 🆕 撮影アングルの選択
st.subheader("📸 STEP 1: 撮影した向きを選んでください")
angle_choice = st.radio(
    "写真の向きによって、採点するポイント（頭・背中・手・膝）が変わります：",
    ["① 真横から撮影（背中・頭の突き出しメイン）", 
     "② 斜め前から撮影（デスクワークの姿勢・膝や手元メイン）", 
     "③ 真正面から撮影（肩の左右の高さ・中心のズレ）"]
)

st.write("---")
uploaded_file = st.file_uploader("写真をアップロードしてください（jpg, png）", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 画像の読み込み
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    h, w, _ = image_np.shape
    
    # 画面を2分割
    col1, col2 = st.columns(2)
    annotated_image = image_np.copy()
    
    with col2:
        st.subheader("⚙️ マーカー位置調整 & 部分採点")
        st.write("スライダーを動かして、写真の中のそれぞれの場所に「点（マーカー）」をピッタリ合わせてください。")
        
        # --- モード別のスライダーと採点ロジック ---
        if "真横から" in angle_choice:
            # ① 真横モード
            st.markdown("### 🟢 各パーツの座標調整")
            head_x = st.slider("💀 頭の位置 (左右)", 0, 100, 45)
            back_x = st.slider("🦴 背中の位置 (左右)", 0, 100, 50)
            hand_x = st.slider("👋 手の位置 (左右)", 0, 100, 40)
            knee_x = st.slider("🦵 膝の位置 (左右)", 0, 100, 35)
            
            # 共通の高さ（標準的な人間のバランスで配置）
            pts = {
                "頭": (int(w * (head_x / 100)), int(h * 0.2)),
                "背中": (int(w * (back_x / 100)), int(h * 0.45)),
                "手": (int(w * (hand_x / 100)), int(h * 0.6)),
                "膝": (int(w * (knee_x / 100)), int(h * 0.8))
            }
            
            # 横から見た採点ロジック（背中を基準にした頭・手のズレ）
            head_error = abs(back_x - head_x) # 背中と頭のズレ（猫背・ストレートネック）
            hand_error = abs(back_x - hand_x - 10) # 巻き込み肩のズレ
            
            score_back = max(0, 100 - head_error * 4)
            score_upper = max(0, 100 - hand_error * 3)
            total_score = int((score_back + score_upper) / 2)
            
            status_text = "🟢 頭と背中のラインが綺麗に揃っています！" if total_score >= 85 else (
                "🟡 頭が少し前に出て猫背・スマホ首の傾向があります。" if total_score >= 60 else
                "🔴 強い猫背、または顎が前に突き出た座り方になっています。骨盤を立てましょう。"
            )

        elif "斜め前から" in angle_choice:
            # ② 斜め前モード（デスクワーク姿勢）
            st.markdown("### 🔵 各パーツの座標調整")
            head_y = st.slider("💀 頭の高さ (上下)", 0, 100, 25)
            back_x = st.slider("🦴 背中の丸み (左右)", 0, 100, 45)
            hand_y = st.slider("👋 手（机）の高さ (上下)", 0, 100, 55)
            knee_y = st.slider("🦵 膝の曲がり (上下)", 0, 100, 75)
            
            pts = {
                "頭": (int(w * 0.5), int(h * (head_y / 100))),
                "背中": (int(w * (back_x / 100)), int(h * 0.45)),
                "手": (int(w * 0.45), int(h * (hand_y / 100))),
                "膝": (int(w * 0.4), int(h * (knee_y / 100)))
            }
            
            # 斜め前採点：手と膝の高さバランス、椅子の沈み込み
            height_diff = abs((knee_y - hand_y) - 20)
            score_lower = max(0, 100 - height_diff * 4)
            score_back = max(0, 100 - abs(back_x - 50) * 5)
            total_score = int((score_lower + score_back) / 2)
            
            status_text = "🟢 肘と膝の角度がデスクワークに理想的なバランスです！" if total_score >= 85 else (
                "🟡 机が高すぎるか、椅子が低くて肩に力が入りやすい状態です。" if total_score >= 60 else
                "🔴 膝が浮いているか、極端に背中が丸まっています。足裏をしっかり床につけましょう。"
            )

        else:
            # ③ 真正面モード
            st.markdown("### 🟡 各パーツの座標調整")
            head_x = st.slider("💀 頭の左右ブレ", 0, 100, 50)
            back_y = st.slider("🦴 背中（胸椎）の高さ", 0, 100, 40)
            shoulder_tilt = st.slider("⚖️ 肩の左右の傾き（手元のズレ）", -20.0, 20.0, 0.0, step=0.5)
            knee_x = st.slider("🦵 膝の左右の開き", 0, 100, 50)
            
            # 肩の左右に点をうつための計算
            cx, cy = int(w * 0.5), int(h * (back_y / 100))
            rad = np.radians(shoulder_tilt)
            arm = int(w * 0.2)
            
            pts = {
                "頭": (int(w * (head_x / 100)), int(h * 0.2)),
                "背中": (cx, cy),
                "手(左肩)": (int(cx - arm * np.cos(rad)), int(cy - arm * np.sin(rad))),
                "膝(右肩)": (int(cx + arm * np.cos(rad)), int(cy + arm * np.sin(rad)))
            }
            
            # 正面採点：頭のズレ、肩の傾き
            tilt_error = abs(shoulder_tilt)
            center_error = abs(head_x - 50)
            
            score_tilt = max(0, 100 - tilt_error * 5)
            score_center = max(0, 100 - center_error * 4)
            total_score = int((score_tilt + score_center) / 2)
            
            status_text = "🟢 左右対称で非常にバランスが良い真っ直ぐな姿勢です！" if total_score >= 85 else (
                "🟡 片方の肩が下がるなど、左右の重心が少し偏っています。" if total_score >= 60 else
                "🔴 体の軸が左右に大きく傾いています。カバンの持ち方や足を組む癖を見直しましょう。"
            )

        # 🏆 総合得点表示
        st.write("---")
        st.metric(label="🏆 総合姿勢スコア", value=f"{total_score} / 100 点")
        
        if total_score >= 85:
            st.success(status_text)
        elif total_score >= 60:
            st.warning(status_text)
        else:
            st.error(status_text)

    # --- 🎨 画像上に点と線、パーツ名を描画する処理 ---
    colors = {
        "頭": (0, 0, 255),    # 赤
        "背中": (0, 255, 0),  # 緑
        "手": (255, 120, 0),  # 青
        "膝": (0, 255, 255),  # 黄
        "手(左肩)": (255, 0, 255),
        "膝(右肩)": (255, 0, 255)
    }
    
    # 点同士を繋ぐ骨格ガイドラインの描画
    pt_list = list(pts.values())
    for i in range(len(pt_list) - 1):
        cv2.line(annotated_image, pt_list[i], pt_list[i+1], (200, 200, 200), 2, cv2.LINE_AA)

    # 各パーツに円と文字を打つ
    for name, pos in pts.items():
        color = colors.get(name, (255, 255, 255))
        cv2.circle(annotated_image, pos, 10, color, -1)
        cv2.circle(annotated_image, pos, 12, (255, 255, 255), 2)
        # 日本語を画像に描画するために簡易英名に変換して表示
        eng_name = "HEAD" if "頭" in name else ("BACK" if "背中" in name else ("HAND" if "手" in name else "KNEE"))
        cv2.putText(annotated_image, eng_name, (pos[0] + 15, pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(annotated_image, eng_name, (pos[0] + 15, pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1, cv2.LINE_AA)

    # デジタルスコアボードの描画
    score_display = f"ANGLE MODE: {angle_choice[:3]} | SCORE: {total_score}"
    cv2.rectangle(annotated_image, (20, 20), (w - 20, 70), (0, 0, 0), -1)
    cv2.putText(annotated_image, score_display, (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    # 💾 ダウンロードデータ化
    result_img = Image.fromarray(annotated_image)
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    with col1:
        st.subheader("📊 姿勢モニター（骨格ガイド）")
        st.image(annotated_image, caption="各色の点を写真の体の位置に合わせてください", use_container_width=True)
        st.download_button(
            label="💾 この測定結果を保存する",
            data=byte_im,
            file_name="posture_analysis.png",
            mime="image/png"
        )






    
