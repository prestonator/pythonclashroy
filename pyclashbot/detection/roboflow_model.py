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
    enhanced detection capabilities. Supports both direct model inference
    and Roboflow Workflows for more complex detection pipelines.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_id: str | None = None,
        workflow_id: str | None = None,
        confidence: float = 0.5,
        **kwargs,
    ):
        """Initialize Roboflow model or workflow.

        Args:
            api_key: Roboflow API key (can also be set via ROBOFLOW_API_KEY env var)
            model_id: Roboflow model ID (e.g., 'clash-royale-cards/1') - for direct model inference
            workflow_id: Roboflow workflow ID (e.g., 'my-workspace/my-workflow') - for workflow-based inference
            confidence: Minimum confidence threshold for predictions (0.0-1.0)
            **kwargs: Additional inference parameters
            
        Note: Provide either model_id OR workflow_id, not both. Workflows take precedence if both provided.
        """
        self.api_key = api_key or os.environ.get("ROBOFLOW_API_KEY")
        self.model_id = model_id
        self.workflow_id = workflow_id
        self.confidence = confidence
        self.inference_client = None
        self._available = False
        self._use_workflow = bool(workflow_id)

        # Initialize the inference client if credentials are provided
        if self.api_key and (self.model_id or self.workflow_id):
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
        """Run inference using Roboflow model or workflow.

        Args:
            image: Input image as numpy array (RGB format)
            **kwargs: Additional inference parameters for workflows

        Returns:
            list[dict]: List of detection results with format:
                {
                    "class": str,          # Card/object name
                    "confidence": float,   # Detection confidence (0-1)
                    "bbox": [x, y, w, h], # Bounding box [x, y, width, height]
                    "center": (x, y),     # Center coordinates
                    "raw": dict,          # Raw prediction from Roboflow API (optional)
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

            # Choose between workflow and direct model inference
            if self._use_workflow and self.workflow_id:
                return self._predict_with_workflow(image_data, **kwargs)
            else:
                return self._predict_with_model(image_data)

        except Exception as e:
            print(f"Warning: Roboflow inference failed: {e}")
            return []
    
    def _predict_with_model(self, image_data: Any) -> list[dict[str, Any]]:
        """Run direct model inference.
        
        Args:
            image_data: Image data as numpy array
            
        Returns:
            list[dict]: Standardized prediction results
        """
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
    
    def _predict_with_workflow(self, image_data: Any, **kwargs) -> list[dict[str, Any]]:
        """Run workflow-based inference.
        
        Workflows allow chaining multiple models and logic together for
        more sophisticated detection pipelines.
        
        Args:
            image_data: Image data as numpy array
            **kwargs: Additional workflow parameters
            
        Returns:
            list[dict]: Standardized prediction results
        """
        # Run workflow inference
        result = self.inference_client.run_workflow(
            workspace_name=self.workflow_id.split('/')[0] if '/' in self.workflow_id else None,
            workflow_id=self.workflow_id.split('/')[-1] if '/' in self.workflow_id else self.workflow_id,
            images={"image": image_data},
            parameters=kwargs,
        )

        # Parse workflow results
        # Workflows can return complex nested results, try to extract predictions
        predictions = []
        
        if result and isinstance(result, dict):
            # Try to find predictions in common workflow output formats
            # Format 1: Direct predictions array
            if "predictions" in result:
                for pred in result["predictions"]:
                    predictions.append(self._standardize_prediction(pred))
            
            # Format 2: Nested in output
            elif "output" in result and isinstance(result["output"], dict):
                if "predictions" in result["output"]:
                    for pred in result["output"]["predictions"]:
                        predictions.append(self._standardize_prediction(pred))
            
            # Format 3: Results array with predictions
            elif "results" in result:
                for res in result["results"]:
                    if isinstance(res, dict) and "predictions" in res:
                        for pred in res["predictions"]:
                            predictions.append(self._standardize_prediction(pred))

        return predictions
    
    def _standardize_prediction(self, pred: dict) -> dict[str, Any]:
        """Standardize a prediction to our common format.
        
        Args:
            pred: Raw prediction dict from Roboflow
            
        Returns:
            dict: Standardized prediction
        """
        return {
            "class": pred.get("class", pred.get("class_name", "unknown")),
            "confidence": pred.get("confidence", 0.0),
            "bbox": [
                pred.get("x", 0) - pred.get("width", 0) / 2,
                pred.get("y", 0) - pred.get("height", 0) / 2,
                pred.get("width", 0),
                pred.get("height", 0),
            ],
            "center": (pred.get("x", 0), pred.get("y", 0)),
            "raw": pred,
        }
    
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
