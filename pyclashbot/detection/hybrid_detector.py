"""
Enhanced detection module that combines traditional CV with ML models.

This module provides a unified interface that can use both traditional
computer vision techniques and optional ML models for improved
detection accuracy.
"""

import numpy as np

from pyclashbot.detection.image_rec import find_image
from pyclashbot.detection.model_interface import DetectionModel, ModelFactory


class HybridDetector:
    """Hybrid detector combining traditional CV and ML models.

    This class provides a fallback mechanism:
    1. Try ML model detection first (if available)
    2. Fall back to traditional CV methods if ML fails
    """

    def __init__(
        self,
        model: DetectionModel | None = None,
        use_model_first: bool = True,
        model_confidence_threshold: float = 0.7,
    ):
        """Initialize hybrid detector.

        Args:
            model: ML model to use for detection (optional)
            use_model_first: Whether to try model detection before CV
            model_confidence_threshold: Minimum confidence to trust model results
        """
        self.model = model
        self.use_model_first = use_model_first
        self.model_confidence_threshold = model_confidence_threshold

    def detect_card(
        self,
        image: np.ndarray,
        traditional_method: callable,
        *args,
        **kwargs,
    ) -> tuple[str | None, dict]:
        """Detect card using hybrid approach.

        Args:
            image: Input image
            traditional_method: Traditional CV detection function
            *args: Arguments for traditional method
            **kwargs: Keyword arguments for traditional method

        Returns:
            tuple: (detected_card_name, metadata_dict)
        """
        metadata = {"method": "none", "confidence": 0.0}

        # Try ML model first if configured
        if self.use_model_first and self.model and self.model.is_available():
            predictions = self.model.predict(image)
            if predictions:
                # Get highest confidence prediction
                best_pred = max(predictions, key=lambda x: x["confidence"])
                if best_pred["confidence"] >= self.model_confidence_threshold:
                    metadata = {
                        "method": "model",
                        "confidence": best_pred["confidence"],
                        "bbox": best_pred.get("bbox"),
                    }
                    return best_pred["class"], metadata

        # Fall back to traditional CV method
        try:
            result = traditional_method(*args, **kwargs)
            metadata = {"method": "traditional_cv", "confidence": 1.0}
            return result, metadata
        except Exception as e:
            print(f"Warning: Traditional detection failed: {e}")
            return None, metadata

    def detect_with_template(
        self,
        image: np.ndarray,
        folder: str,
        tolerance: float = 0.88,
        **kwargs,
    ) -> tuple[tuple[int, int] | None, dict]:
        """Detect using template matching with optional model assistance.

        Args:
            image: Input image
            folder: Folder containing reference images
            tolerance: Template matching tolerance
            **kwargs: Additional parameters

        Returns:
            tuple: (coordinates, metadata)
        """
        metadata = {"method": "template_matching", "confidence": 0.0}

        # Try model first if available
        if self.use_model_first and self.model and self.model.is_available():
            predictions = self.model.predict(image)
            if predictions:
                best_pred = max(predictions, key=lambda x: x["confidence"])
                if best_pred["confidence"] >= self.model_confidence_threshold:
                    metadata = {
                        "method": "model",
                        "confidence": best_pred["confidence"],
                    }
                    return best_pred["center"], metadata

        # Fall back to traditional template matching
        result = find_image(image, folder, tolerance, **kwargs)
        if result:
            metadata["confidence"] = 1.0
        return result, metadata


def create_detector_from_config(config: dict) -> HybridDetector:
    """Create a hybrid detector from configuration.

    Args:
        config: Configuration dictionary with keys:
            - model_type: 'custom', 'dummy', or None (for future model integration)
            - model_config: Model-specific configuration
            - use_model_first: Whether to prioritize model detection
            - confidence_threshold: Minimum confidence for model results

    Returns:
        HybridDetector: Configured detector instance
    """
    model = None
    model_type = config.get("model_type")

    if model_type and model_type != "dummy":
        model_config = config.get("model_config", {})
        try:
            model = ModelFactory.create_model(model_type, **model_config)
        except Exception as e:
            print(f"Warning: Failed to create model: {e}")

    return HybridDetector(
        model=model,
        use_model_first=config.get("use_model_first", True),
        model_confidence_threshold=config.get("confidence_threshold", 0.7),
    )
