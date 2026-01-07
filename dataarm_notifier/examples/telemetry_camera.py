#!/usr/bin/env python3
"""Example: Camera Feed Streaming with Rerun SDK.

This script demonstrates streaming camera feeds to the Rerun viewer
with automatic fallback when camera is unavailable.
"""

import time
import argparse
import cv2
import numpy as np

from dataarm_notifier.telemetry.producer import TelemetryProducer


def find_working_camera(max_index: int = 8) -> tuple[cv2.VideoCapture | None, int]:
    """Find a working camera by trying device indices.

    Args:
        max_index: Maximum device index to try

    Returns:
        Tuple of (VideoCapture or None, device index)
    """
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                print(f"  Found working camera at index {idx}: {frame.shape[1]}x{frame.shape[0]}")
                return cap, idx
            cap.release()
    return None, -1


def create_simulated_frame(width: int, height: int, t: float) -> np.ndarray:
    """Create simulated camera frame with animated pattern."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Create moving gradient pattern
    x = np.linspace(0, width, width)
    y = np.linspace(0, height, height)
    xx, yy = np.meshgrid(x, y)

    # Moving circle pattern
    cx = width // 2 + int(100 * np.sin(t * 2))
    cy = height // 2 + int(50 * np.cos(t * 3))
    mask = ((xx - cx) ** 2 + (yy - cy) ** 2) < 1000

    # Color based on time (rainbow effect)
    r = int(127 + 127 * np.sin(t))
    g = int(127 + 127 * np.sin(t + 2))
    b = int(127 + 127 * np.sin(t + 4))

    frame[mask, 0] = b
    frame[mask, 1] = g
    frame[mask, 2] = r

    # Add timestamp text
    cv2.putText(
        frame,
        f"Simulated: {t:.1f}s",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    return frame


def run_camera_example(
    camera_index: int = -1,  # -1 means auto-detect
    width: int = 640,
    height: int = 480,
    fps: int = 30,
    simulate: bool = False,
):
    """Run camera streaming example.

    Args:
        camera_index: Camera device index (-1 for auto-detect)
        width: Frame width
        height: Frame height
        fps: Target FPS
        simulate: Force simulated feed
    """
    print("=" * 60)
    print("Camera Feed Streaming Example")
    print("=" * 60)
    print(f"\nResolution: {width}x{height}")
    print(f"FPS: {fps}")
    print("\nThis example demonstrates:")
    print("  - Camera detection by device index")
    print("  - Camera frame streaming to Rerun viewer")
    print("  - Automatic fallback to simulated feed")
    print("\nPress Ctrl+C to stop\n")

    # Initialize producer
    producer = TelemetryProducer(app_name="Camera_Example")

    # Camera handling
    cap = None
    camera_available = False
    device_info = "unknown"

    if simulate:
        print("Using simulated feed (forced)")
        device_info = "simulated"
    elif camera_index == -1:
        # Auto-detect
        print("Auto-detecting camera...")
        cap, idx = find_working_camera()
        if cap:
            camera_available = True
            device_info = f"index {idx}"
        else:
            print("  No working camera found, using simulated feed")
            device_info = "simulated"
    else:
        # Try specific index
        print(f"Trying camera index {camera_index}...")
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                camera_available = True
                device_info = f"index {camera_index}"
                print(f"  Opened: {frame.shape[1]}x{frame.shape[0]}")
            else:
                print("  Camera opened but no valid frame, using simulated feed")
                cap.release()
                cap = None
                device_info = "simulated"
        else:
            print(f"  Cannot open camera {camera_index}, using simulated feed")
            device_info = "simulated"
            cap = None

    print(f"Source: {device_info}")

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            frame_start = time.time()

            if camera_available:
                # Read from real camera
                ret, frame = cap.read()
                if not ret or frame is None or frame.size == 0:
                    print("Failed to capture frame, switching to simulated feed")
                    camera_available = False
                    if cap:
                        cap.release()
                    continue

                # Convert BGR to RGB for Rerun
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # Create simulated frame (moving pattern)
                t = time.time()
                frame_rgb = create_simulated_frame(width, height, t)

            # Log frame to Rerun
            producer.log_camera(frame_rgb)

            # Progress indicator
            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps_actual = frame_count / elapsed
                status = "Camera" if camera_available else "Simulated"
                print(f"Frames: {frame_count}, FPS: {fps_actual:.1f}, Source: {status}")

            # Maintain loop rate
            loop_time = time.time() - frame_start
            target_frame_time = 1.0 / fps
            sleep_time = max(0, target_frame_time - loop_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        if camera_available and cap:
            cap.release()

        total_time = time.time() - start_time
        print(f"\nStatistics:")
        print(f"  Total frames: {frame_count}")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Average FPS: {frame_count / total_time:.1f}")

        producer.shutdown()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Camera Feed Streaming Example")
    parser.add_argument(
        "--device",
        type=int,
        default=-1,
        help="Camera device index (-1 for auto-detect, 0+ for specific device)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=640,
        help="Frame width (default: 640)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=480,
        help="Frame height (default: 480)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Target FPS (default: 30)",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Force simulated feed even if camera available",
    )

    args = parser.parse_args()

    run_camera_example(
        camera_index=args.device,
        width=args.width,
        height=args.height,
        fps=args.fps,
        simulate=args.simulate,
    )


if __name__ == "__main__":
    main()
