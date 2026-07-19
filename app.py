import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
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
    # 画像の読み込み (PILオブジェクトとして扱う)
    image = Image.open(uploaded_file).convert("RGB")
    w, h = image.size
    
    col1, col2 = st.columns(2)
    
    # 描画用のオブジェクトを作成
    annotated_image = image.copy()
    draw = ImageDraw.Draw(annotated_image)
    
    pts = {}
    # PIL用の確実なRGBカラー指定
    colors = {
        "P1": (255, 0, 0),    # 赤
        "P2": (0, 255, 0),    # 緑
        "P3": (0, 120, 255),  # 青
        "P4": (255, 215, 0)   # 黄
    }
    
    with col2:
        st.subheader("⚙️ マーカー位置調整 & 部分採点")
        st.write("右側のスライダーを動かして、4つの点を写真の各パーツ（上から頭・背中・手・膝）にピッタリ合わせてください。")
        
        if "真横から" in angle_choice:
            st.markdown("### 🟢 真横モードの調整")
            p1_x = st.slider("🔴 1番目の点（頭）の左右位置", 0, 100, 45)
            p2_x = st.slider("🟢 2番目の点（背中）の左右位置", 0, 100, 50)
            p3_x = st.slider("🔵 3番目の点（手）の左右位置", 0, 100, 42)
            p4_x = st.slider("🟡 4番目の点（膝）の左右位置", 0, 100, 38)
            
            pts = {
                "P1": (int(w * (p1_x / 100)), int(h * 0.25)),
                "P2": (int(w * (p2_x / 100)), int(h * 0.45)),
                "P3": (int(w * (p3_x / 100)), int(h * 0.60)),
                "P4": (int(w * (p4_x / 100)), int(h * 0.75))
            }
            
            head_error = abs(p2_x - p1_x)
            total_score = max(0, 100 - head_error * 4)
            status_text = "🟢 頭と背中のラインが綺麗に揃っています！" if total_score >= 85 else (
                "🟡 頭が少し前に出て猫背・スマホ首の傾向があります。" if total_score >= 60 else
                "🔴 強い猫背、または顎が前に突き出た姿勢です。骨盤を立てましょう。"
            )

        elif "斜め前から" in angle_choice:
            st.markdown("### 🔵 斜め前モードの調整")
            p1_y = st.slider("🔴 1番目の点（頭）の高さ", 0, 100, 25)
            p2_x = st.slider("🟢 2番目の点（背中）の丸み", 0, 100, 45)
            p3_y = st.slider("🔵 3番目の点（手）の高さ", 0, 100, 55)
            p4_y = st.slider("🟡 4番目の点（膝）の高さ", 0, 100, 75)
            
            pts = {
                "P1": (int(w * 0.5), int(h * (p1_y / 100))),
                "P2": (int(w * (p2_x / 100)), int(h * 0.45)),
                "P3": (int(w * 0.45), int(h * (p3_y / 100))),
                "P4": (int(w * 0.4), int(h * (p4_y / 100)))
            }
            
            total_score = max(0, 100 - abs(p2_x - 50) * 5)
            status_text = "🟢 背すじが程よく伸びた良い姿勢バランスです！" if total_score >= 85 else "🔴 背中が丸まりすぎています。椅子に深く座りましょう。"

        else:
            st.markdown("### 🟡 真正面モードの調整")
            p1_x = st.slider("🔴 1番目の点（頭）の左右ブレ", 0, 100, 50)
            p2_y = st.slider("🟢 2番目の点（首・中心）の高さ", 0, 100, 35)
            shoulder_tilt = st.slider("⚖️ 肩の左右の傾き調整", -20.0, 20.0, 0.0, step=0.5)
            
            cx, cy = int(w * (p1_x / 100)), int(h * (p2_y / 100))
            rad = np.radians(shoulder_tilt)
            arm_len = int(w * 0.18)
            
            pts = {
                "P1": (cx, int(h * 0.20)),
                "P2": (cx, cy),
                "P3": (int(cx - arm_len * np.cos(rad)), int(cy - arm_len * np.sin(rad))),
                "P4": (int(cx + arm_len * np.cos(rad)), int(cy + arm_len * np.sin(rad)))
            }
            
            tilt_error = abs(shoulder_tilt)
            center_error = abs(p1_x - 50)
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

    # --- 🎨 画像描画処理（PILで確実に上書き） ---
    pt_list = list(pts.values())
    
    # 1. 骨格線の描画（グレーの細い線）
    for i in range(len(pt_list) - 1):
        draw.line([pt_list[i], pt_list[i+1]], fill=(180, 180, 180), width=3)

    # 2. 🆕 各パーツに「単色のドット」を描画（白丸のバグを完全回避）
    radius = max(8, int(w * 0.015)) # 写真のサイズに合わせた適切な丸の大きさ
    for name, pos in pts.items():
        color = colors.get(name, (255, 255, 255))
        left_up = (pos[0] - radius, pos[1] - radius)
        right_down = (pos[0] + radius, pos[1] + radius)
        # 完全に塗りつぶされた綺麗な色の丸を描きます
        draw.ellipse([left_up, right_down], fill=color)

    # 3. 🆕 上部のスコア表示ボックスを確実に真っ黒で描画
    box_height = max(40, int(h * 0.08))
    draw.rectangle([(0, 0), (w, box_height)], fill=(20, 20, 20))
    
    # スコアテキストを白文字で描画
    score_display = f"POSTURE SCORE: {total_score}"
    # フォントサイズを自動調整
    try:
        font = ImageFont.load_default()
    except:
        font = None
    draw.text((20, int(box_height * 0.25)), score_display, fill=(255, 255, 255), font=font)

    # 💾 ダウンロードデータ化
    buf = io.BytesIO()
    annotated_image.save(buf, format="PNG")
    byte_im = buf.getvalue()

    with col1:
        st.subheader("📊 姿勢モニター（骨格ガイド）")
        st.image(annotated_image, caption="スライダーを動かして隙間に点を合わせてください", use_container_width=True)
        st.download_button(
            label="💾 この測定結果を保存する",
            data=byte_im,
            file_name="posture_analysis.png",
            mime="image/png"
        )






    
