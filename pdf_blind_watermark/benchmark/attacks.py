from __future__ import annotations

import io
from enum import Enum
from typing import Callable, Dict

import cv2
import numpy as np
from PIL import Image, ImageFilter


class AttackType(Enum):
    """Types of attacks for robustness testing."""

    JPEG_COMPRESSION = "jpeg_compression"
    SCALE_DOWN = "scale_down"
    SCALE_UP = "scale_up"
    ROTATION = "rotation"
    CROP = "crop"
    GAUSSIAN_NOISE = "gaussian_noise"
    SALT_PEPPER_NOISE = "salt_pepper_noise"
    GAUSSIAN_BLUR = "gaussian_blur"
    MEDIAN_FILTER = "median_filter"
    SCREENSHOT_SIMULATION = "screenshot_simulation"
    BRIGHTNESS_CHANGE = "brightness_change"
    CONTRAST_CHANGE = "contrast_change"


class AttackSimulator:
    """Simulate various attacks on watermarked images."""

    @staticmethod
    def jpeg_compression(image: Image.Image, quality: int = 50) -> Image.Image:
        """Apply JPEG compression.

        Args:
            image: Input PIL Image
            quality: JPEG quality (1-100)

        Returns:
            Compressed image
        """
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")

    @staticmethod
    def scale_down(image: Image.Image, scale_factor: float = 0.5) -> Image.Image:
        """Scale image down.

        Args:
            image: Input PIL Image
            scale_factor: Scale factor (0 < scale_factor < 1)

        Returns:
            Scaled down image
        """
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        return image.resize(new_size, Image.LANCZOS)

    @staticmethod
    def scale_up(image: Image.Image, scale_factor: float = 1.5) -> Image.Image:
        """Scale image up.

        Args:
            image: Input PIL Image
            scale_factor: Scale factor (scale_factor > 1)

        Returns:
            Scaled up image
        """
        new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
        return image.resize(new_size, Image.LANCZOS)

    @staticmethod
    def rotation(image: Image.Image, angle: float = 5.0) -> Image.Image:
        """Rotate image.

        Args:
            image: Input PIL Image
            angle: Rotation angle in degrees

        Returns:
            Rotated image
        """
        return image.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

    @staticmethod
    def crop(image: Image.Image, crop_ratio: float = 0.1) -> Image.Image:
        """Crop image borders.

        Args:
            image: Input PIL Image
            crop_ratio: Ratio of image to crop from each side (0-0.5)

        Returns:
            Cropped image
        """
        crop_x = int(image.width * crop_ratio)
        crop_y = int(image.height * crop_ratio)
        return image.crop((crop_x, crop_y, image.width - crop_x, image.height - crop_y))

    @staticmethod
    def gaussian_noise(image: Image.Image, sigma: float = 10.0) -> Image.Image:
        """Add Gaussian noise.

        Args:
            image: Input PIL Image
            sigma: Standard deviation of Gaussian noise

        Returns:
            Noisy image
        """
        img_array = np.array(image, dtype=np.float32)
        noise = np.random.normal(0, sigma, img_array.shape)
        noisy = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy, mode="RGB")

    @staticmethod
    def salt_pepper_noise(image: Image.Image, probability: float = 0.01) -> Image.Image:
        """Add salt and pepper noise.

        Args:
            image: Input PIL Image
            probability: Probability of noise per pixel

        Returns:
            Noisy image
        """
        img_array = np.array(image)
        mask = np.random.random(img_array.shape[:2])

        noisy = img_array.copy()
        noisy[mask < probability / 2] = 0
        noisy[mask > 1 - probability / 2] = 255

        return Image.fromarray(noisy, mode="RGB")

    @staticmethod
    def gaussian_blur(image: Image.Image, radius: float = 2.0) -> Image.Image:
        """Apply Gaussian blur.

        Args:
            image: Input PIL Image
            radius: Blur radius

        Returns:
            Blurred image
        """
        return image.filter(ImageFilter.GaussianBlur(radius=radius))

    @staticmethod
    def median_filter(image: Image.Image, size: int = 3) -> Image.Image:
        """Apply median filter.

        Args:
            image: Input PIL Image
            size: Filter size

        Returns:
            Filtered image
        """
        return image.filter(ImageFilter.MedianFilter(size=size))

    @staticmethod
    def screenshot_simulation(image: Image.Image) -> Image.Image:
        """Simulate screenshot capture (color space conversion + slight blur).

        Args:
            image: Input PIL Image

        Returns:
            Screenshot-like image
        """
        img_array = np.array(image)

        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

        blurred = cv2.GaussianBlur(img_array, (3, 3), 0.5)

        return Image.fromarray(blurred, mode="RGB")

    @staticmethod
    def brightness_change(image: Image.Image, factor: float = 1.2) -> Image.Image:
        """Change image brightness.

        Args:
            image: Input PIL Image
            factor: Brightness factor (>1 brighter, <1 darker)

        Returns:
            Adjusted image
        """
        img_array = np.array(image, dtype=np.float32)
        adjusted = np.clip(img_array * factor, 0, 255).astype(np.uint8)
        return Image.fromarray(adjusted, mode="RGB")

    @staticmethod
    def contrast_change(image: Image.Image, factor: float = 1.2) -> Image.Image:
        """Change image contrast.

        Args:
            image: Input PIL Image
            factor: Contrast factor (>1 more contrast, <1 less contrast)

        Returns:
            Adjusted image
        """
        img_array = np.array(image, dtype=np.float32)
        mean = img_array.mean()
        adjusted = mean + (img_array - mean) * factor
        adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
        return Image.fromarray(adjusted, mode="RGB")

    @classmethod
    def get_attack_configs(cls) -> Dict[str, list]:
        """Get predefined attack configurations for benchmarking.

        Returns:
            Dictionary mapping attack type to list of (attack_func, params, description) tuples
        """
        return {
            AttackType.JPEG_COMPRESSION: [
                (cls.jpeg_compression, {"quality": 90}, "JPEG Q90"),
                (cls.jpeg_compression, {"quality": 75}, "JPEG Q75"),
                (cls.jpeg_compression, {"quality": 50}, "JPEG Q50"),
                (cls.jpeg_compression, {"quality": 30}, "JPEG Q30"),
            ],
            AttackType.SCALE_DOWN: [
                (cls.scale_down, {"scale_factor": 0.75}, "Scale 75%"),
                (cls.scale_down, {"scale_factor": 0.5}, "Scale 50%"),
                (cls.scale_down, {"scale_factor": 0.25}, "Scale 25%"),
            ],
            AttackType.SCALE_UP: [
                (cls.scale_up, {"scale_factor": 1.25}, "Scale 125%"),
                (cls.scale_up, {"scale_factor": 1.5}, "Scale 150%"),
                (cls.scale_up, {"scale_factor": 2.0}, "Scale 200%"),
            ],
            AttackType.ROTATION: [
                (cls.rotation, {"angle": 2.0}, "Rotate 2°"),
                (cls.rotation, {"angle": 5.0}, "Rotate 5°"),
                (cls.rotation, {"angle": 10.0}, "Rotate 10°"),
                (cls.rotation, {"angle": -5.0}, "Rotate -5°"),
            ],
            AttackType.CROP: [
                (cls.crop, {"crop_ratio": 0.05}, "Crop 5%"),
                (cls.crop, {"crop_ratio": 0.10}, "Crop 10%"),
                (cls.crop, {"crop_ratio": 0.15}, "Crop 15%"),
            ],
            AttackType.GAUSSIAN_NOISE: [
                (cls.gaussian_noise, {"sigma": 5.0}, "Gaussian σ=5"),
                (cls.gaussian_noise, {"sigma": 10.0}, "Gaussian σ=10"),
                (cls.gaussian_noise, {"sigma": 15.0}, "Gaussian σ=15"),
            ],
            AttackType.SALT_PEPPER_NOISE: [
                (cls.salt_pepper_noise, {"probability": 0.005}, "S&P p=0.005"),
                (cls.salt_pepper_noise, {"probability": 0.01}, "S&P p=0.01"),
                (cls.salt_pepper_noise, {"probability": 0.02}, "S&P p=0.02"),
            ],
            AttackType.GAUSSIAN_BLUR: [
                (cls.gaussian_blur, {"radius": 1.0}, "Blur r=1"),
                (cls.gaussian_blur, {"radius": 2.0}, "Blur r=2"),
                (cls.gaussian_blur, {"radius": 3.0}, "Blur r=3"),
            ],
            AttackType.MEDIAN_FILTER: [
                (cls.median_filter, {"size": 3}, "Median 3x3"),
                (cls.median_filter, {"size": 5}, "Median 5x5"),
            ],
            AttackType.SCREENSHOT_SIMULATION: [
                (cls.screenshot_simulation, {}, "Screenshot Sim"),
            ],
            AttackType.BRIGHTNESS_CHANGE: [
                (cls.brightness_change, {"factor": 0.8}, "Brightness 80%"),
                (cls.brightness_change, {"factor": 1.2}, "Brightness 120%"),
            ],
            AttackType.CONTRAST_CHANGE: [
                (cls.contrast_change, {"factor": 0.8}, "Contrast 80%"),
                (cls.contrast_change, {"factor": 1.2}, "Contrast 120%"),
            ],
        }
