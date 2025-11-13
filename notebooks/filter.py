import os
import cv2
import numpy as np

def load_pairs(file_path):
    pairs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            pair = line.strip().split(', ')
            pairs.append(tuple(pair))
    return pairs

def resize_to_screen(img, w=1200, h=600):
    img = cv2.resize(img, (int(w), int(h)))
    return img

def filter_pairs(pairs, capture, query_device, map_device, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    keep_path = os.path.join(save_dir, "filtered_keep.txt")
    drop_path = os.path.join(save_dir, "filtered_drop.txt")

    # Load
    reviewed = set()
    for path in [keep_path, drop_path]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                reviewed.update(line.strip() for line in f if line.strip())

    print(f"[INFO] Filtered {len(reviewed)}/{len(pairs)} pair")

    for i, pair in enumerate(pairs):
        key = ', '.join(pair)
        if key in reviewed:
            continue

        q_path = f"{capture}/ARCHE_D2/sessions/{query_device}_query/raw_data/{pair[0]}"
        m_path = f"{capture}/ARCHE_D2/sessions/{map_device}_map/raw_data/{pair[1]}"
        q_img = cv2.imread(q_path)
        m_img = cv2.imread(m_path)
        if q_img is None or m_img is None:
            print(f"[WARN] Reading image error: {pair}")
            continue
        
        ###################
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.5
        thickness = 5
        color = (0, 255, 255)
        
        (text_w, text_h), _ = cv2.getTextSize("Query", font, scale, thickness)
        cv2.putText(q_img, "Query", (q_img.shape[1] - text_w - 20, 50), font, scale, color, thickness)
        (text_w, text_h), _ = cv2.getTextSize("Map", font, scale, thickness)
        cv2.putText(m_img, "Map", (m_img.shape[1] - text_w - 20, 50), font, 1.2, color, thickness)
        ##################

        # Concat
        h = max(q_img.shape[0], m_img.shape[0])
        w = q_img.shape[1] + m_img.shape[1]
        canvas = 255 * np.ones((h, w, 3), dtype=np.uint8)
        canvas[:q_img.shape[0], :q_img.shape[1]] = q_img
        canvas[:m_img.shape[0], q_img.shape[1]:q_img.shape[1]+m_img.shape[1]] = m_img

        err = float(pair[2])
        text = f"[{i+1}/{len(pairs)}] Error: {err:.4f} | q=keep, x=del, esc=quit"
        cv2.putText(canvas, text, (30, 40),
                    font, 1, color, thickness)

        # Resize
        canvas = resize_to_screen(canvas)

        cv2.imshow("Pair Filter", canvas)
        key_pressed = cv2.waitKey(0) & 0xFF

        if key_pressed == 27:  # ESC
            print("[INFO] Escape.")
            break
        elif key_pressed in [ord('x'), ord('d')]:
            print("Delete pair")
            with open(drop_path, 'a') as f:
                f.write(key + '\n')
        elif key_pressed == ord('q'):
            print("Keep pair")
            with open(keep_path, 'a') as f:
                f.write(key + '\n')
        else:
            print(f"[INFO] Pressed key {key_pressed} is invalid, skipping.")
        cv2.destroyAllWindows()

    cv2.destroyAllWindows()
    print("[DONE] Terminated.")


################
capture = "/home/long/Workspace/crocodl-benchmark/capture"
query_device = 'ios'
map_device = 'spot'
group = 'bad'
PAIRS_PATH = f"/home/long/Workspace/crocodl-benchmark/notebooks/estimate_pose/{query_device}_query/{map_device}_map/{group}_pairs.txt"
SAVE_DIR = f"/home/long/Workspace/crocodl-benchmark/notebooks/estimate_pose/{query_device}_query/{map_device}_map/{group}_filtered"

pairs = load_pairs(PAIRS_PATH)
filter_pairs(pairs, capture, query_device, map_device, SAVE_DIR)
