import time
import traceback

from pyclashbot.bot.states import BattleModeState, StateHistory, StateOrder, state_tree
from pyclashbot.emulators.bluestacks import BlueStacksEmulatorController
from pyclashbot.utils.logger import Logger
from pyclashbot.utils.thread import PausableThread, ThreadKilled


class WorkerThread(PausableThread):
    def __init__(self, logger: Logger, args, kwargs=None) -> None:
        super().__init__(args, kwargs)
        self.logger: Logger = logger
        self.in_a_clan = False

    def _setup_emulator(self, jobs):
        """Set up BlueStacks 5 emulator."""
        self.logger.log("Creating BlueStacks 5 emulator")
        try:
            bs_mode = jobs.get("bluestacks_render_mode", "gl")
            render_settings = {"graphics_renderer": bs_mode}
            return BlueStacksEmulatorController(logger=self.logger, render_settings=render_settings)
        except Exception as e:
            self.logger.error(f"Failed to create BlueStacks 5 emulator: {e}")
            self.logger.change_status("Failed to start BlueStacks 5. Verify its installation!")
            return None

    def _run_bot_loop(self, emulator, jobs):
        """Run the main bot state loop."""
        # Initialize card detector with model configuration if provided
        from pyclashbot.bot.card_detection import initialize_card_detector  # noqa: PLC0415
        from pyclashbot.interface.enums import UIField  # noqa: PLC0415

        model_config = {
            'model_enabled': jobs.get(UIField.MODEL_ENABLED_TOGGLE.value, False),
            'model_type': jobs.get(UIField.MODEL_TYPE.value, 'roboflow'),
            'roboflow_api_key': jobs.get(UIField.ROBOFLOW_API_KEY.value),
            'roboflow_model_id': jobs.get(UIField.ROBOFLOW_MODEL_ID.value),
            'roboflow_workflow_id': jobs.get(UIField.ROBOFLOW_WORKFLOW_ID.value),
            'confidence_threshold': jobs.get(UIField.MODEL_CONFIDENCE_THRESHOLD.value, 0.7),
        }

        initialize_card_detector(model_config)
        if model_config.get('model_enabled'):
            model_type = model_config.get('model_type', 'unknown')
            workflow_id = model_config.get('roboflow_workflow_id')
            model_id = model_config.get('roboflow_model_id')

            if workflow_id:
                self.logger.log(f"✓ Roboflow Workflow initialized: {workflow_id}")
                self.logger.log("  Using workflow-based detection pipeline")
            elif model_id:
                self.logger.log(f"✓ Roboflow model initialized: {model_id}")
            else:
                self.logger.log(f"✓ Roboflow connection initialized: Using {model_type}")

            self.logger.log(f"  Confidence threshold: {model_config.get('confidence_threshold', 0.7)}")

            # Check if model is actually available
            from pyclashbot.bot.card_detection import get_card_detector  # noqa: PLC0415
            detector = get_card_detector()
            if detector and detector.model and detector.model.is_available():
                detection_method = "workflow" if workflow_id else "model"
                self.logger.log(f"✓ {model_type.capitalize()} {detection_method} is active and will be used in battles")
            else:
                self.logger.log(f"⚠ {model_type.capitalize()} configuration found but not available")
        else:
            self.logger.log("Model detection disabled - using traditional CV methods only")

        state = "start"
        state_history = StateHistory(self.logger)
        state_order = StateOrder()
        battle_mode_state = BattleModeState()
        consecutive_restarts = 0
        max_consecutive_restarts = 5

        while not self.shutdown_flag.is_set():
            try:
                new_state = state_tree(emulator, self.logger, state, jobs, state_history, state_order, battle_mode_state)

                # Check for restart loops
                if new_state == "restart":
                    consecutive_restarts += 1
                    if consecutive_restarts >= max_consecutive_restarts:
                        self.logger.error(
                            f"Too many consecutive restarts ({consecutive_restarts}) - stopping bot to prevent infinite loop"
                        )
                        break
                    self.logger.log(f"Restart #{consecutive_restarts} - attempting to recover")
                else:
                    consecutive_restarts = 0  # Reset counter on successful state

                # Check for error states that should stop execution
                if new_state in ["fail", None]:
                    self.logger.error(f"Critical error: state_tree returned '{new_state}' - stopping bot")
                    if new_state == "fail":
                        self.logger.add_restart_after_failure()
                    break

                state = new_state

            except Exception as e:
                self.logger.error(f"Exception in state_tree: {e}")
                self.logger.log(f"Current state was: {state}")
                # Try to restart from a known state
                state = "restart"
                # If we keep getting exceptions, break out
                traceback.print_exc()
                consecutive_restarts += 1
                if consecutive_restarts >= max_consecutive_restarts:
                    self.logger.error("Too many consecutive exceptions - stopping bot")
                    break

            while self.pause_flag.is_set():
                time.sleep(0.33)

    def run(self) -> None:
        """Main worker thread execution."""
        self.logger.log("WorkerThread run()...")
        jobs = self.args

        emulator = self._setup_emulator(jobs)
        if emulator is None:
            return

        try:
            self._run_bot_loop(emulator, jobs)
        except ThreadKilled:
            return
        except Exception as err:
            self.logger.error(str(err))
