from __future__ import annotations

import io
from typing import List, Tuple

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class SampleGenerator:
    """Generate controlled sample PDFs and images for testing."""

    @staticmethod
    def generate_gradient_image(
        width: int = 1024, height: int = 768, orientation: str = "horizontal"
    ) -> Image.Image:
        """Generate a gradient image.

        Args:
            width: Image width
            height: Image height
            orientation: 'horizontal', 'vertical', or 'radial'

        Returns:
            PIL Image with gradient pattern
        """
        if orientation == "horizontal":
            x = np.linspace(0, 255, width, dtype=np.uint8)
            gradient = np.tile(x, (height, 1))
        elif orientation == "vertical":
            y = np.linspace(0, 255, height, dtype=np.uint8)
            gradient = np.tile(y.reshape(-1, 1), (1, width))
        elif orientation == "radial":
            y_coords, x_coords = np.ogrid[:height, :width]
            center_x, center_y = width // 2, height // 2
            distance = np.sqrt((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2)
            max_distance = np.sqrt(center_x**2 + center_y**2)
            gradient = (255 * distance / max_distance).astype(np.uint8)
        else:
            raise ValueError(f"Unknown orientation: {orientation}")

        image = np.stack([gradient, gradient, gradient], axis=2)
        return Image.fromarray(image, mode="RGB")

    @staticmethod
    def generate_text_document(
        width: int = 1240,
        height: int = 1754,
        num_lines: int = 30,
        background_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """Generate a document-like image with text.

        Args:
            width: Image width
            height: Image height
            num_lines: Number of text lines
            background_color: Background color RGB tuple

        Returns:
            PIL Image with text content
        """
        image = Image.new("RGB", (width, height), color=background_color)
        draw = ImageDraw.Draw(image)

        title = "Sample Document for Watermark Testing"
        draw.text((width // 2 - 200, 100), title, fill=(0, 0, 0))

        y_pos = 200
        line_spacing = (height - 300) // num_lines
        for i in range(num_lines):
            line = f"Line {i + 1:02d}: This is sample text content for watermark robustness testing."
            draw.text((100, y_pos), line, fill=(50, 50, 50))
            y_pos += line_spacing

        for i in range(5):
            x1 = 100 + i * 200
            y1 = height - 250
            x2 = x1 + 150
            y2 = y1 + 100
            draw.rectangle([x1, y1, x2, y2], outline=(100, 100, 200), width=2)

        return image

    @staticmethod
    def generate_mixed_content(
        width: int = 1240, height: int = 1754, complexity: str = "medium"
    ) -> Image.Image:
        """Generate an image with mixed content (text, shapes, gradients).

        Args:
            width: Image width
            height: Image height
            complexity: 'low', 'medium', or 'high'

        Returns:
            PIL Image with mixed content
        """
        image = Image.new("RGB", (width, height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)

        if complexity in ["medium", "high"]:
            for i in range(10):
                x1 = np.random.randint(0, width - 200)
                y1 = np.random.randint(0, height - 200)
                x2 = x1 + np.random.randint(50, 200)
                y2 = y1 + np.random.randint(50, 200)
                color = tuple(np.random.randint(0, 256, 3).tolist())
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(0, 0, 0))

        if complexity == "high":
            for i in range(20):
                x1 = np.random.randint(0, width - 100)
                y1 = np.random.randint(0, height - 100)
                x2 = x1 + np.random.randint(50, 100)
                y2 = y1 + np.random.randint(50, 100)
                color = tuple(np.random.randint(0, 256, 3).tolist())
                draw.ellipse([x1, y1, x2, y2], fill=color, outline=(0, 0, 0))

        y_pos = 50
        for i in range(15):
            text = f"Content line {i + 1} with various patterns and data"
            draw.text((50, y_pos), text, fill=(0, 0, 0))
            y_pos += 40

        return image

    @staticmethod
    def generate_noise_pattern(
        width: int = 1024, height: int = 768, noise_type: str = "uniform"
    ) -> Image.Image:
        """Generate an image with noise pattern.

        Args:
            width: Image width
            height: Image height
            noise_type: 'uniform', 'gaussian', or 'salt_pepper'

        Returns:
            PIL Image with noise pattern
        """
        if noise_type == "uniform":
            data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        elif noise_type == "gaussian":
            base = np.ones((height, width, 3), dtype=np.float32) * 128
            noise = np.random.normal(0, 50, (height, width, 3))
            data = np.clip(base + noise, 0, 255).astype(np.uint8)
        elif noise_type == "salt_pepper":
            base = np.ones((height, width, 3), dtype=np.uint8) * 128
            mask = np.random.random((height, width, 3))
            base[mask < 0.05] = 0
            base[mask > 0.95] = 255
            data = base
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")

        return Image.fromarray(data, mode="RGB")

    @staticmethod
    def generate_sample_pdf(
        output_path: str, images: List[Image.Image], quality: int = 90
    ) -> None:
        """Generate a PDF from a list of images.

        Args:
            output_path: Output PDF file path
            images: List of PIL Images
            quality: JPEG compression quality (1-100)
        """
        doc = fitz.open()

        for img in images:
            page = doc.new_page(width=img.width, height=img.height)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            buf.seek(0)

            img_rect = fitz.Rect(0, 0, img.width, img.height)
            page.insert_image(img_rect, stream=buf.getvalue())

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

    @classmethod
    def generate_test_suite(
        cls, output_dir: str = ".", num_samples: int = 3
    ) -> List[str]:
        """Generate a suite of test images and PDFs.

        Args:
            output_dir: Output directory
            num_samples: Number of samples per type

        Returns:
            List of generated file paths
        """
        import os

        os.makedirs(output_dir, exist_ok=True)
        generated_files = []

        image_types = [
            ("gradient_horizontal", lambda: cls.generate_gradient_image(orientation="horizontal")),
            ("gradient_vertical", lambda: cls.generate_gradient_image(orientation="vertical")),
            ("text_document", lambda: cls.generate_text_document()),
            ("mixed_content_medium", lambda: cls.generate_mixed_content(complexity="medium")),
            ("mixed_content_high", lambda: cls.generate_mixed_content(complexity="high")),
        ]

        for type_name, generator in image_types:
            for i in range(num_samples):
                image = generator()
                filename = os.path.join(output_dir, f"{type_name}_{i + 1}.png")
                image.save(filename)
                generated_files.append(filename)

        pdf_filename = os.path.join(output_dir, "sample_document.pdf")
        pdf_images = [
            cls.generate_text_document(),
            cls.generate_mixed_content(complexity="medium"),
            cls.generate_gradient_image(),
        ]
        cls.generate_sample_pdf(pdf_filename, pdf_images)
        generated_files.append(pdf_filename)

        return generated_files
