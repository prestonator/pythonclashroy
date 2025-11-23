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
                from inference_sdk import InferenceConfiguration, InferenceHTTPClient  # noqa: PLC0415

                # Create configuration with confidence threshold
                config = InferenceConfiguration(
                    confidence_threshold=self.confidence
                )

                self.inference_client = InferenceHTTPClient(
                    api_url="https://detect.roboflow.com",
                    api_key=self.api_key,
                )

                # Configure the client with the confidence threshold
                self.inference_client.configure(config)

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
            **kwargs: Additional inference parameters (not used - configuration is set during initialization)

        Returns:
            list[dict]: List of detection results with format:
                {
                    "class": str,          # Card/object name
                    "confidence": float,   # Detection confidence (0-1)
                    "bbox": [x, y, w, h], # Bounding box [x, y, width, height]
                    "center": (x, y),     # Center coordinates
                }
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

            # Run inference (confidence is already configured in the client)
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
                            # Store raw prediction for advanced use cases
                            "raw": pred,
                        }
                    )

            return predictions

        except Exception as e:
            print(f"Warning: Roboflow inference failed: {e}")
            return []
    
    def detect_battlefield_objects(self, image: Any, region: tuple[int, int, int, int] | None = None) -> list[dict[str, Any]]:
        """Detect objects on the battlefield (towers, troops, etc.).
        
        This is useful for detecting enemy units, tower health, and battlefield state
        to make better strategic decisions.
        
        Args:
            image: Full battlefield screenshot as numpy array
            region: Optional (x1, y1, x2, y2) region to analyze, None for full image
            
        Returns:
            list[dict]: List of detected objects with their positions and classifications
        """
        if not self.is_available():
            return []
        
        # Extract region if specified
        if region and isinstance(image, np.ndarray):
            x1, y1, x2, y2 = region
            image = image[y1:y2, x1:x2]
            offset = (x1, y1)
        else:
            offset = (0, 0)
        
        # Run detection
        predictions = self.predict(image)
        
        # Adjust bounding boxes if we analyzed a sub-region
        if offset != (0, 0):
            for pred in predictions:
                if "bbox" in pred:
                    pred["bbox"][0] += offset[0]
                    pred["bbox"][1] += offset[1]
                if "center" in pred:
                    pred["center"] = (
                        pred["center"][0] + offset[0],
                        pred["center"][1] + offset[1]
                    )
        
        return predictions

    def is_available(self) -> bool:
        """Check if Roboflow model is available.

        Returns:
            bool: True if model is configured and ready
        """
        return self._available and self.inference_client is not None
