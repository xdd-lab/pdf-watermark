from __future__ import annotations

from typing import Optional

import cv2
import numpy as np
from PIL import Image


class ImageProcessor:
    """Utility class for loading and preprocessing images."""

    def __init__(self, rectify: bool = True):
        self.rectify = rectify

    def load(self, path: str) -> Image.Image:
        image = Image.open(path)
        return image.convert("RGB")

    def preprocess_for_embedding(self, image: Image.Image) -> Image.Image:
        return image.convert("RGB")

    def preprocess_for_extraction(self, image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        if not self.rectify:
            return image

        rectified = self._rectify(np.array(image))
        if rectified is None:
            return image
        return Image.fromarray(rectified)

    def _rectify(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Attempt to detect document boundaries and apply perspective correction."""
        try:
            bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)

            contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for contour in contours[:5]:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
                if len(approx) == 4:
                    pts = approx.reshape(4, 2)
                    warped = self._four_point_transform(bgr, pts)
                    if warped is not None:
                        return cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
        except Exception:
            return None
        return None

    def _four_point_transform(self, image: np.ndarray, pts: np.ndarray) -> Optional[np.ndarray]:
        rect = self._order_points(pts)
        (tl, tr, br, bl) = rect

        width_top = np.linalg.norm(tr - tl)
        width_bottom = np.linalg.norm(br - bl)
        max_width = int(max(width_top, width_bottom))

        height_left = np.linalg.norm(bl - tl)
        height_right = np.linalg.norm(br - tr)
        max_height = int(max(height_left, height_right))

        if max_width <= 0 or max_height <= 0:
            return None

        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype="float32",
        )

        rect = rect.astype("float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (max_width, max_height), flags=cv2.INTER_LINEAR)
        return warped

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect
