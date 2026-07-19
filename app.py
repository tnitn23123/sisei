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
st.title("デジタル姿勢分析モニター")
st.write("写真をアップロードし、右側のスライダーで「線の位置」と「角度」を合わせてください。")

uploaded_file = st.file_uploader("写真をアップロードしてください（jpg, png）", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 画像の読み込み
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    h, w, _ = image_np.shape
    
    # 画面を2分割
    col1, col2 = st.columns(2)
    
    with col2:
        st.subheader("⚙️ 測定コントロール")
        
        # 1. 線の根元（腰）の位置を調整するスライダー
        st.write("**① 測定の基準点（腰の位置）を合わせる**")
        base_x_percent = st.slider("左右の位置調整", 0, 100, 50, step=1)
        base_y_percent = st.slider("上下の位置調整", 0, 100, 70, step=1)
        
        # ％から実際のピクセル座標に変換
        base_x = int(w * (base_x_percent / 100))
        base_y = int(h * (base_y_percent / 100))
        
        st.write("---")
        
        # 2. 角度を調整するスライダー（⚠️上限を70度まで拡大しました！）
        st.write("**② 背中の前後傾き（度数）を合わせる**")
        back_angle = st.slider("角度調整", -70.0, 70.0, 0.0, step=0.5)
        
        # 理想は0〜15度前後（真っ直ぐな姿勢）
        if 0.0 <= back_angle <= 15.0:
            score = 100
            status_text = "🟢 理想的なまっすぐな背筋です！その調子です。"
            box_type = "success"
            text_color = (0, 255, 0) # 緑色
        elif back_angle > 15.0:
            # 70度まで滑らかに減点されるように計算式を調整
            score = max(0, int(100 - (back_angle - 15.0) * 1.8))
            if back_angle <= 25.0:
                status_text = "🟡 軽度の前傾（猫背側）の傾向があります。"
                box_type = "warning"
                text_color = (0, 255, 255) # 黄色
            else:
                status_text = "🔴 大きく前傾しています。背もたれの使い方や座り方、姿勢を見直しましょう。"
                box_type = "error"
                text_color = (0, 0, 255) # 赤色
        else:
            # 70度まで滑らかに減点されるように計算式を調整
            score = max(0, int(100 - abs(back_angle) * 1.8))
            if back_angle >= -15.0:
                status_text = "🟡 わずかに後ろに傾いています。"
                box_type = "warning"
                text_color = (0, 255, 255) # 黄色
            else:
                status_text = "🔴 大きく後ろに反っています（仙骨座り・ずっこけ座りの状態です）。お尻を椅子の奥まで引きましょう。"
                box_type = "error"
                text_color = (0, 0, 255) # 赤色
        
        st.metric(label="🏆 姿勢スコア", value=f"{score} / 100 点")
        
        # 傾き方向のテキスト表示
        if back_angle > 0:
            st.write(f"**現在の状態:** 前傾 {back_angle:.1f} 度")
        elif back_angle < 0:
            st.write(f"**現在の状態:** 後傾 {abs(back_angle):.1f} 度")
        else:
            st.write("**現在の状態:** 垂直 0.0 度")
        
        # アドバイスの表示
        if box_type == "success":
            st.success(status_text)
        elif box_type == "warning":
            st.warning(status_text)
        else:
            st.error(status_text)

    # --- 画像加工（背中に沿った青い線とデジタル数字の表示） ---
    annotated_image = image_np.copy()
    
    # ① 理想的な「垂直の基準線」を黄色の点線で引く
    cv2.line(annotated_image, (base_x, 0), (base_x, h), (0, 255, 255), 1, cv2.LINE_AA)
    
    # ② スライダーの値に合わせて動く「背中の測定線（青）」を引く
    rad = np.radians(-90 + back_angle)
    
    # 💡 70度倒しても頭までしっかり線が届くように、線の長さを1.5倍（h * 0.65）に延長
    line_len = int(h * 0.65) 
    end_x = int(base_x + line_len * np.cos(rad))
    end_y = int(base_y + line_len * np.sin(rad))
    
    # 青い傾き線を引く（鮮やかな水色・太め）
    cv2.line(annotated_image, (base_x, base_y), (end_x, end_y), (255, 120, 0), 4, cv2.LINE_AA)
    cv2.circle(annotated_image, (base_x, base_y), 8, (255, 120, 0), -1) # 基準点
    
    # ③ 画像の上に「角度」と「スコア」を大きく表示
    if back_angle >= 0:
        text = f"Front: {back_angle:.1f} deg | Score: {score}"
    else:
        text = f"Back: {abs(back_angle):.1f} deg | Score: {score}"
        
    (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
    bx, by = int(w * 0.05), int(h * 0.12)
    
    # 真っ黒な四角マスク
    cv2.rectangle(annotated_image, (bx - 15, by - text_h - 15), (bx + text_w + 15, by + 15), (0, 0, 0), -1)
    # 文字の縁取りと重ねて描画
    cv2.putText(annotated_image, text, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(annotated_image, text, (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 1.0, text_color, 2, cv2.LINE_AA)

    # 💾 --- 画像ダウンロード用データの作成 ---
    result_img = Image.fromarray(annotated_image)
    buf = io.BytesIO()
    result_img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    with col1:
        st.subheader("📊 姿勢モニター")
        st.image(annotated_image, caption="位置調整スライダーで青い点を腰に合わせ、角度を調整してください", use_container_width=True)
        
        st.download_button(
            label="💾 測定結果の画像を保存する",
            data=byte_im,
            file_name="streamline_result.png",
            mime="image/png"
        )






    