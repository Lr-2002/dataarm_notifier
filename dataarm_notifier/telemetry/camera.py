"""Camera capture module with OpenCV for V4L2 devices.

This module provides camera capture using OpenCV with V4L2 backend,
optimized for real-time performance.
"""

import time
import numpy as np
import cv2
from typing import Optional, Generator


class CameraCapture:
    """Camera capture using OpenCV with V4L2 backend."""

    def __init__(
        self,
        device: str = "/dev/video1",
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ):
        """Initialize camera capture.

        Args:
            device: V4L2 device path (e.g., "/dev/video1")
            width: Frame width
            height: Frame height
            fps: Frame rate
        """
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False

    def open(self) -> bool:
        """Open the camera.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use CAP_V4L2 backend explicitly with device path
            self._cap = cv2.VideoCapture(self.device, cv2.CAP_V4L2)

            if not self._cap.isOpened():
                # Try without backend hint
                self._cap = cv2.VideoCapture(self.device)

            if not self._cap.isOpened():
                return False

            # Set MJPG for better performance (reduces latency)
            self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

            # Set resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            # Set FPS
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Reduce buffer size for lower latency
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Read one frame to verify
            ret, frame = self._cap.read()
            if ret and frame is not None:
                self._running = True
                print(f"  Camera opened: {frame.shape[1]}x{frame.shape[0]} @ {self.fps}fps")
                return True
            else:
                self._cap.release()
                self._cap = None
                return False

        except Exception as e:
            print(f"Failed to open camera: {e}")
            return False

    def isOpened(self) -> bool:
        """Check if camera is open and running."""
        return self._cap is not None and self._cap.isOpened() and self._running

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Read next frame.

        Returns:
            Tuple of (success, frame)
        """
        if not self.isOpened():
            return False, None

        try:
            ret, frame = self._cap.read()
            return ret, frame if ret else None
        except Exception:
            return False, None

    def release(self) -> None:
        """Release the camera."""
        self._running = False
        if self._cap:
            self._cap.release()
            self._cap = None

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


class FFmpegCamera:
    """Camera capture using FFmpeg pipeline (fallback for problematic devices)."""

    def __init__(
        self,
        device: str = "/dev/video1",
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ):
        """Initialize FFmpeg camera capture.

        Args:
            device: V4L2 device path (e.g., "/dev/video1")
            width: Frame width
            height: Frame height
            fps: Frame rate
        """
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self._cap: Optional[CameraCapture] = None

    def open(self) -> bool:
        """Open the camera using FFmpeg backend."""
        # Try OpenCV with GStreamer backend first
        try:
            self._cap = cv2.VideoCapture(self.device, cv2.CAP_GSTREAMER)
            if self._cap.isOpened():
                self._setup_camera()
                return True
        except Exception:
            pass

        # Fall back to regular OpenCV
        self._cap = CameraCapture(self.device, self.width, self.height, self.fps)
        return self._cap.open()

    def _setup_camera(self):
        """Setup camera properties."""
        if self._cap:
            self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.fps)

    def isOpened(self) -> bool:
        """Check if camera is open."""
        return self._cap is not None and self._cap.isOpened()

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Read next frame."""
        if not self.isOpened():
            return False, None
        return self._cap.read()

    def release(self) -> None:
        """Release the camera."""
        if self._cap:
            self._cap.release()
            self._cap = None


def auto_detect_camera() -> tuple[Optional[CameraCapture], str]:
    """Auto-detect available camera.

    Returns:
        Tuple of (CameraCapture or None, device info string)
    """
    from pathlib import Path

    # Check /dev/video* devices
    video_devices = sorted(Path("/dev").glob("video*"), reverse=True)
    for dev_path in video_devices:
        try:
            print(f"  Trying {dev_path}...")
            cap = CameraCapture(str(dev_path), width=640, height=480, fps=30)
            if cap.open():
                return cap, str(dev_path)
        except Exception as e:
            print(f"  Error: {e}")

    return None, "none"


def capture_frames(device: str = "/dev/video1", width: int = 640, height: int = 480) -> Generator[np.ndarray, None, None]:
    """Generator that yields camera frames."""
    cap = CameraCapture(device, width, height)
    if cap.open():
        while cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                yield frame
            else:
                break
        cap.release()


if __name__ == "__main__":
    print("Testing camera capture...")
    cap = CameraCapture("/dev/video1", width=640, height=480, fps=30)

    if cap.open():
        print("Camera opened successfully!")

        for i in range(10):
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"Frame {i+1}: {frame.shape}")
            else:
                print(f"Failed to read frame {i+1}")
                break

        cap.release()
    else:
        print("Failed to open camera")
