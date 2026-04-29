from __future__ import annotations
from ultralytics import YOLO

MODEL_PATH = "models/best.pt"

def main():
    model = YOLO(MODEL_PATH)
    model.export(format="engine", half=True)
    print("Export TensorRT xong. Kiểm tra file .engine trong thư mục export của Ultralytics.")

if __name__ == "__main__":
    main()