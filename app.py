import cv2
from ultralytics import YOLO
import time
import numpy as np
import gradio as gr
import threading

# 1. AIモデルを読み込む
model = YOLO("yolov8n.pt")

ITEMS = {
    "すべて同時に探す": "all",
    "携帯電話": "cell phone",
    "リモコン": "remote",
    "ハサミ": "scissors",
    "鍵": "keys",
    "コップ": "cup",
    "ボトル": "bottle",
    "リュック": "backpack",
    "バッグ/ポーチ": "handbag",
    "本/手帳": "book",
    "腕時計": "watch",
    "パソコン": "laptop",
    "傘": "umbrella"
}

current_target = "all"
detection_logs = []
is_running = True

# 2. 外部カメラ（iPhoneのIriunなど）を自動で探して起動
def find_working_camera():
    for index in range(5):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            success, _ = cap.read()
            if success:
                print(f"👉 カメラ番号【 {index} 】が利用可能です。これを使用します。")
                return cap
            cap.release()
    return None

cap = find_working_camera()

# 🔄 裏側でiPhoneのカメラ映像をAI処理し続ける関数
def video_processing_loop():
    global current_target, detection_logs, is_running
    if cap is None:
        return

    while is_running and cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # 画質改善（くっきり化）
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced_frame = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        kernel = np.array([[0, -0.5, 0], [-0.5, 3, -0.5], [0, -0.5, 0]])
        sharpened_frame = cv2.filter2D(enhanced_frame, -1, kernel)

        # AI検出 (RX 9070用に高画質指定)
        results = model(sharpened_frame, imgsz=960, verbose=False)
        
        # resultsがリスト形式で返ってきた場合でも確実に0番目の要素を取り出す
        if isinstance(results, list):
            if len(results) == 0:
                continue
            result = results[0]
        else:
            result = results

        boxes = result.boxes
        found_this_frame = []

        for box in boxes:
            class_id = int(box.cls)
            object_name = model.names[class_id]

            if current_target != "all" and object_name != current_target:
                continue

            jp_name = "オブジェクト"
            is_valid_item = False
            for k, v in ITEMS.items():
                if v == object_name:
                    jp_name = k
                    is_valid_item = True
                    break

            if is_valid_item:
                # 二重リスト構造のエラーも出ないように平坦化して取り出す
                xywh_list = box.xywh.tolist()[0]
                x_center = int(xywh_list[0])
                y_center = int(xywh_list[1])
                
                # ----------------------------------------------------
                # ✨【組み込み箇所】TypeErrorバグを完全に回避する安全な座標計算
                # ----------------------------------------------------
                pos = (x_center, y_center)
                radius = 20  # 例としてターゲットマークや円を描くための半径を指定
                
                # タプルから直接引き算・足し算をせず、展開（アンパック）して計算します
                x, y = pos
                left_up = (x - radius, y - radius)
                right_down = (x + radius, y + radius)
                
                # 計算した安全な座標（left_up, right_down）を使って描画等を行う場合はここに追加できます
                # 例: cv2.rectangle(sharpened_frame, left_up, right_down, (0, 255, 0), 2)
                # ----------------------------------------------------

                current_time = time.strftime("%H:%M:%S", time.localtime())
                log_entry = f"[{current_time}] 🎯 【 {jp_name} 】を発見！ 位置(X:{x_center}, Y:{y_center})"
                found_this_frame.append(log_entry)

        if found_this_frame:
            for log in reversed(found_this_frame):
                if not detection_logs or detection_logs[0] != log:
                    detection_logs.insert(0, log)
            detection_logs = detection_logs[:10]

        # PCの画面上にもリアルタイム映像ウインドウを出しておく
        annotated_frame = result.plot()
        cv2.imshow("AI Monitor Window", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# スレッドをスタート
threading.Thread(target=video_processing_loop, daemon=True).start()

def change_target(selected_jp_name):
    global current_target
    current_target = ITEMS[selected_jp_name]
    return f"🔎 現在の探索ターゲット: 【 {selected_jp_name} 】"

def get_logs():
    global detection_logs
    if not detection_logs:
        return "まだ何も見つかっていません。iPhoneカメラの前にモノを置いてみてください。"
    return "\n".join(detection_logs)

# 🎨 アプリ画面（UI）のデザイン構築
with gr.Blocks(title="部屋のモノ探偵 AI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 部屋のモノ専用探偵 AI アプリ (外部カメラ連動版)")
    gr.Markdown("iPhoneカメラの映像から、無くしたモノをAIが自動検知して操作画面に記録します。")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ コントロールパネル")
            dropdown = gr.Dropdown(choices=list(ITEMS.keys()), value="すべて同時に探す", label="探したいモノを選択")
            status_output = gr.Textbox(value="🔎 現在の探索ターゲット: 【 すべて同時に探す 】", label="ステータス", interactive=False)
            
        with gr.Column(scale=2):
            gr.Markdown("### 📜 リアルタイム発見ログ（履歴）")
            log_output = gr.TextArea(label="最新の10件", interactive=False, lines=10)

    # 1秒ごとに自動で画面のログ履歴を更新する仕組み
    timer = gr.Timer(1.0)
    timer.tick(fn=get_logs, outputs=log_output)
    dropdown.change(fn=change_target, inputs=dropdown, outputs=status_output)

# 🌐 【ノートン対策・完全ローカル起動】
if __name__ == "__main__":
    if cap is None:
        print("カメラを起動できなかったためアプリを開始できません。")
    else:
        # share=False にすることでノートンのブロックを完全に回避して安全にブラウザを開きます
        demo.launch(server_name="127.0.0.1", server_port=7860, share=False, inline=False)



    
