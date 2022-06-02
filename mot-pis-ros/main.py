#!/usr/bin/env python3
import cv2
import time
import argparse
import numpy as np
from yolo.cv_yolo import YOLO
from deep_sort.tracker import DeepSORT


def parse_args():
    parser = argparse.ArgumentParser(description="Open Video Deep SORT")
    parser.add_argument(
        "--video", type=str, required=True, help="Fonte de vídeo.")
    parser.add_argument(
        "--model", type=str, default="../datasets/YOLO/yolov5/yolov5s.onnx",
        help="Modelo treinado.")
    parser.add_argument(
        "--classes", type=str, default="../datasets/YOLO/yolov5/classes.txt",
        help="Lista de classes.")
    parser.add_argument(
        "--gpu", action="store_true", default=False, help="Usa GPU como backend.")
    return parser.parse_args()


def main(source, detector, tracker):
    # Abre captura de vídeo
    cap = cv2.VideoCapture(source)

    # Variáveis para fps
    fps = 0
    count_frames = 0
    max_count = 20

    # Resize
    factor = 0.5
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    dsize = np.int32([width*factor, height*factor])

    while cap.isOpened():
        if count_frames == 0:
            start = time.time()

        ret, frame = cap.read()

        if not ret or frame is None:
            break

        frame = cv2.resize(frame, dsize)

        # Faz detecções com yolo
        start_detector = time.time()
        detector.detect(frame)
        time_detector = time.time() - start_detector

        # Atualiza rastreio
        if tracker is not None:
            start_tracker = time.time()
            tracker.update(frame, detector.detections)
            time_tracker = time.time() - start_tracker

        # Calcula fps
        if count_frames >= max_count:
            fps = count_frames/(time.time() - start)
            count_frames = 0
        else:
            count_frames += 1

        # Desenha detecções
        detector.draw(frame)
        if tracker is not None:
            tracker.draw(frame)

        # Desenha fps na imagem
        fps_label = "FPS: %.2f" % fps
        cv2.putText(
            frame, fps_label, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Results
        cv2.imshow("Result", frame)
        print(f"timing: detection {time_detector}, tracking {time_tracker}")

        # Key
        key = cv2.waitKey(10)
        if key == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Argumentos de entrada
    args = parse_args()

    # Objeto de detecção
    detector = YOLO(
        model=args.model,
        classes=args.classes,
        gpu=args.gpu)

    # Objeto de rastreio
    tracker = DeepSORT(
        max_iou_distance=0.7,
        max_age=30,
        n_init=3,
        matching_threshold=0.2)

    # Framework de detecção e rastreio
    main(source=args.video, detector=detector, tracker=tracker)