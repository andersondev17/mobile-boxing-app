import cv2

def save_video(frames, out_path, fps=30):
    if not frames:
        return

    h, w, _ = frames[0].shape
    writer = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h)
    )

    for f in frames:
        writer.write(f)

    writer.release()
