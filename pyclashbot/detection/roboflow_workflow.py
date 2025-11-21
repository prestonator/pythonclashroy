"""
Roboflow workflow integration for strategy and analysis.

This module provides integration with Roboflow's workflow API for
enhanced strategy decisions and game analysis in Clash Royale.
"""

import os
from typing import Any

import numpy as np


class RoboflowWorkflowClient:
    """Roboflow workflow implementation for strategy and analysis.

    This class integrates with Roboflow's workflow API to provide
    enhanced decision-making capabilities. Workflows can perform
    object detection, classification, and other analysis tasks.
    """

    def __init__(
        self,
        api_key: str | None = None,
        workspace_name: str | None = None,
        workflow_id: str | None = None,
        workflow_type: str = "detection",
        **kwargs,
    ):
        """Initialize Roboflow workflow client.

        Args:
            api_key: Roboflow API key (can also be set via ROBOFLOW_API_KEY env var)
            workspace_name: Roboflow workspace name (e.g., 'my-workspace')
            workflow_id: Workflow ID to execute (e.g., 'card-counter')
            workflow_type: Type of workflow ('detection' or 'classification')
            **kwargs: Additional workflow parameters
        """
        self.api_key = api_key or os.environ.get("ROBOFLOW_API_KEY")
        self.workspace_name = workspace_name
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.inference_client = None
        self._available = False

        # Initialize the inference client if credentials are provided
        if self.api_key and self.workspace_name and self.workflow_id:
            try:
                from inference_sdk import InferenceHTTPClient  # noqa: PLC0415

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
                print(f"Warning: Failed to initialize Roboflow workflow client: {e}")

    def run_workflow(
        self, image: Any, parameters: dict[str, Any] | None = None, **kwargs
    ) -> dict[str, Any]:
        """Run workflow on an image.

        Args:
            image: Input image as numpy array (RGB format)
            parameters: Additional workflow parameters
            **kwargs: Additional keyword arguments for the workflow

        Returns:
            dict: Workflow execution results. Structure depends on workflow type:
                For detection workflows:
                    {
                        'count_objects': int,
                        'output_image': image data,
                        'predictions': [{'class': str, 'confidence': float, ...}, ...]
                    }
                For classification workflows:
                    {
                        'predictions': [{'class': str, 'confidence': float}, ...]
                    }
        """
        if not self.is_available():
            return {}

        try:
            # Convert numpy array to format expected by Roboflow
            if isinstance(image, np.ndarray):
                # Roboflow expects RGB format
                image_data = image
            else:
                return {}

            # Prepare workflow parameters
            workflow_params = parameters or {}

            # Run workflow
            result = self.inference_client.run_workflow(
                workspace_name=self.workspace_name,
                workflow_id=self.workflow_id,
                images={"image": image_data},
                parameters=workflow_params,
            )

            # Process workflow results based on type
            if not result or len(result) == 0:
                return {}

            # Get the first result (workflows return list of results per image)
            workflow_output = result[0] if isinstance(result, list) else result

            # Parse and normalize the output
            return self._parse_workflow_output(workflow_output)

        except Exception as e:
            print(f"Warning: Roboflow workflow execution failed: {e}")
            return {}

    def _parse_workflow_output(self, output: dict[str, Any]) -> dict[str, Any]:
        """Parse and normalize workflow output.

        Args:
            output: Raw workflow output

        Returns:
            dict: Normalized output with consistent structure
        """
        parsed = {}

        # Handle detection workflow outputs
        if self.workflow_type == "detection":
            # Count objects if available
            if "count_objects" in output:
                parsed["count_objects"] = output["count_objects"]

            # Extract output image if available
            if "output_image" in output:
                parsed["output_image"] = output["output_image"]

            # Extract predictions
            if "predictions" in output:
                parsed["predictions"] = output["predictions"]

        # Handle classification workflow outputs
        elif self.workflow_type == "classification":
            # Extract predictions
            if "predictions" in output:
                parsed["predictions"] = output["predictions"]

        # Include any other keys that might be present
        for key, value in output.items():
            if key not in parsed:
                parsed[key] = value

        return parsed

    def is_available(self) -> bool:
        """Check if workflow client is available.

        Returns:
            bool: True if client is configured and ready
        """
        return (
            self._available
            and self.inference_client is not None
            and self.workspace_name is not None
            and self.workflow_id is not None
        )

    def get_workflow_info(self) -> dict[str, Any]:
        """Get information about the configured workflow.

        Returns:
            dict: Workflow configuration information
        """
        return {
            "workspace_name": self.workspace_name,
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "available": self.is_available(),
        }
