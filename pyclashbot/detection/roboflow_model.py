"""
Roboflow model integration for enhanced card detection.

This module provides integration with Roboflow's inference API for
improved card and object detection in Clash Royale.
"""

import os
from typing import Any

import numpy as np

from pyclashbot.detection.model_interface import DetectionModel


class RoboflowModel(DetectionModel):
    """Roboflow model implementation for card detection.

    This class integrates with Roboflow's inference SDK to provide
    enhanced detection capabilities. It's designed to be lightweight
    and easily configurable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_id: str | None = None,
        confidence: float = 0.5,
        **kwargs,
    ):
        """Initialize Roboflow model.

        Args:
            api_key: Roboflow API key (can also be set via ROBOFLOW_API_KEY env var)
            model_id: Roboflow model ID (e.g., 'clash-royale-cards/1')
            confidence: Minimum confidence threshold for predictions (0.0-1.0)
            **kwargs: Additional inference parameters
        """
        self.api_key = api_key or os.environ.get("ROBOFLOW_API_KEY")
        self.model_id = model_id
        self.confidence = confidence
        self.inference_client = None
        self._available = False

        # Initialize the inference client if credentials are provided
        if self.api_key and self.model_id:
            try:
                from inference_sdk import (  # noqa: PLC0415
                    InferenceHTTPClient,
                )

                self.inference_client = InferenceHTTPClient(
                    api_url="https://detect.roboflow.com",
                    api_key=self.api_key,
                )
                self._available = True
            except ImportError:
                print(
                    "Warning: inference-sdk not installed. "
                    "Install with: pip install inference-sdk"
                )
            except Exception as e:
                print(f"Warning: Failed to initialize Roboflow client: {e}")

    def predict(self, image: Any, **kwargs) -> list[dict[str, Any]]:
        """Run inference using Roboflow model.

        Args:
            image: Input image as numpy array (RGB format)
            **kwargs: Additional inference parameters (not used directly,
                     confidence is set via InferenceConfiguration)

        Returns:
            list[dict]: List of detection results
        """
        if not self.is_available():
            return []

        try:
            # Convert numpy array to format expected by Roboflow
            if isinstance(image, np.ndarray):
                # Roboflow expects RGB format
                image_data = image
            else:
                return []

            # Use InferenceConfiguration to set confidence threshold
            from inference_sdk import InferenceConfiguration  # noqa: PLC0415

            # Get confidence threshold from kwargs or use default
            confidence_threshold = kwargs.get("confidence", self.confidence)
            
            config = InferenceConfiguration(
                confidence_threshold=confidence_threshold,
            )

            # Run inference with configuration context manager
            with self.inference_client.use_configuration(config):
                result = self.inference_client.infer(
                    image_data,
                    model_id=self.model_id,
                )

            # Convert Roboflow result format to our standard format
            predictions = []
            if result and "predictions" in result:
                for pred in result["predictions"]:
                    predictions.append(
                        {
                            "class": pred.get("class", "unknown"),
                            "confidence": pred.get("confidence", 0.0),
                            "bbox": [
                                pred.get("x", 0) - pred.get("width", 0) / 2,
                                pred.get("y", 0) - pred.get("height", 0) / 2,
                                pred.get("width", 0),
                                pred.get("height", 0),
                            ],
                            "center": (pred.get("x", 0), pred.get("y", 0)),
                        }
                    )

            return predictions

        except Exception as e:
            print(f"Warning: Roboflow inference failed: {e}")
            return []

    def is_available(self) -> bool:
        """Check if Roboflow model is available.

        Returns:
            bool: True if model is configured and ready
        """
        return self._available and self.inference_client is not None
