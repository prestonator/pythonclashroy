"""
Model Interface for external AI/ML model integration.

This module provides an abstraction layer for integrating external computer vision models
(e.g., YOLOv8, custom models, etc.) to enhance card and object detection in Clash Royale.
"""

from abc import ABC, abstractmethod
from typing import Any


class DetectionModel(ABC):
    """Abstract base class for external detection models."""

    @abstractmethod
    def predict(self, image: Any, **kwargs) -> list[dict[str, Any]]:
        """Run inference on an image.

        Args:
            image: Input image (numpy array or PIL Image)
            **kwargs: Additional model-specific parameters

        Returns:
            list[dict]: List of detection results with format:
                [
                    {
                        'class': 'card_name',
                        'confidence': 0.95,
                        'bbox': [x, y, width, height],
                        'center': (x, y)
                    },
                    ...
                ]
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and ready for inference.

        Returns:
            bool: True if model is available, False otherwise
        """


class DummyModel(DetectionModel):
    """Dummy model that always returns empty results.

    Used as a fallback when no model is configured.
    """

    def predict(self, image: Any, **kwargs) -> list[dict[str, Any]]:
        """Return empty predictions."""
        return []

    def is_available(self) -> bool:
        """Dummy model is always unavailable."""
        return False


class ModelFactory:
    """Factory for creating detection model instances."""

    @staticmethod
    def create_model(model_type: str, **config) -> DetectionModel:
        """Create a detection model instance.

        Args:
            model_type: Type of model to create ('yolo', 'custom', 'dummy', etc.)
            **config: Model-specific configuration parameters

        Returns:
            DetectionModel: An instance of the requested model

        Raises:
            ValueError: If model_type is not supported
        """
        # Future model types can be added here (e.g., YOLO, custom models)
        if model_type == "dummy" or model_type is None:
            return DummyModel()
        msg = f"Unsupported model type: {model_type}. Add custom model implementations here."
        raise ValueError(msg)
