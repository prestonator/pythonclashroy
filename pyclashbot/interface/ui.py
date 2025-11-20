from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox
from typing import TYPE_CHECKING

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, READONLY, YES, X
from ttkbootstrap.tooltip import ToolTip

from pyclashbot.interface.config import (
    JOBS,
    ComboConfig,
)
from pyclashbot.interface.enums import (
    BotStatField,
    DerivedStatField,
    StatField,
    UIField,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def no_jobs_popup() -> None:
    messagebox.showerror("Critical Error!", "You must select at least one job!")


class PyClashBotUI(ttk.Window):
    DEFAULT_THEME = "darkly"

    def __init__(self) -> None:
        super().__init__(themename=self.DEFAULT_THEME)
        self.title("py-clash-bot")
        self.geometry("490x650")
        self.minsize(490, 500)
        self.resizable(True, True)

        self._style = ttk.Style()
        current_theme = self._style.theme_use()
        if not current_theme:
            current_theme = self.DEFAULT_THEME
        self.theme_var = ttk.StringVar(value=current_theme)
        self._config_callback: Callable[[dict[str, object]], None] | None = None
        self._open_recordings_callback: Callable[[], None] | None = None
        self._open_logs_callback: Callable[[], None] | None = None
        self._config_widgets: dict[str, tk.Widget] = {}
        self._theme_labels: list[tk.Widget] = []
        self._traces: list[tuple[tk.Variable, str]] = []
        self._suspend_traces = 0

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_tabs()
        self._build_bottom_row()
        self._refresh_theme_colours()

    def register_config_callback(self, callback: Callable[[dict[str, object]], None]) -> None:
        self._config_callback = callback

    def register_open_recordings_callback(self, callback: Callable[[], None]) -> None:
        self._open_recordings_callback = callback

    def register_open_logs_callback(self, callback: Callable[[], None]) -> None:
        self._open_logs_callback = callback

    def get_all_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for field, var in self.jobs_vars.items():
            values[field.value] = bool(var.get())

        values[UIField.DECK_NUMBER_SELECTION.value] = self._safe_int(self.deck_var.get(), fallback=2)
        values[UIField.CYCLE_DECKS_USER_TOGGLE.value] = bool(self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE].get())
        values[UIField.MAX_DECK_SELECTION.value] = self._safe_int(self.max_deck_var.get(), fallback=2)
        values[UIField.RECORD_FIGHTS_TOGGLE.value] = bool(self.record_var.get())

        # Only BlueStacks is supported
        values[UIField.BLUESTACKS_EMULATOR_TOGGLE.value] = True

        bs_render = self.bs_render_var.get()
        values[UIField.BS_RENDERER_DX.value] = bs_render == "DirectX"
        values[UIField.BS_RENDERER_GL.value] = bs_render == "OpenGL"
        values[UIField.BS_RENDERER_VK.value] = bs_render == "Vulkan"

        values[UIField.THEME_NAME.value] = self.theme_var.get() or self.DEFAULT_THEME

        # AI/ML Model settings
        values[UIField.MODEL_ENABLED_TOGGLE.value] = bool(self.model_enabled_var.get())
        values[UIField.MODEL_TYPE.value] = self.model_type_var.get()
        values[UIField.ROBOFLOW_API_KEY.value] = self.roboflow_api_key_var.get()
        values[UIField.ROBOFLOW_MODEL_ID.value] = self.roboflow_model_id_var.get()
        values[UIField.MODEL_CONFIDENCE_THRESHOLD.value] = self._safe_float(
            self.model_confidence_var.get(), fallback=0.7
        )

        return values

    def set_all_values(self, values: dict[str, object]) -> None:
        theme_value: str | None = None
        self._suspend_traces += 1
        try:
            for field, var in self.jobs_vars.items():
                if field.value in values:
                    var.set(bool(values[field.value]))

            if UIField.DECK_NUMBER_SELECTION.value in values:
                self.deck_var.set(str(values[UIField.DECK_NUMBER_SELECTION.value]))
            if UIField.MAX_DECK_SELECTION.value in values:
                self.max_deck_var.set(str(values[UIField.MAX_DECK_SELECTION.value]))
            if UIField.RECORD_FIGHTS_TOGGLE.value in values:
                self.record_var.set(bool(values[UIField.RECORD_FIGHTS_TOGGLE.value]))

            if UIField.THEME_NAME.value in values:
                theme_value = str(values[UIField.THEME_NAME.value])

            # BlueStacks is the only emulator
            if values.get(UIField.BS_RENDERER_VK.value):
                self.bs_render_var.set("Vulkan")
            elif values.get(UIField.BS_RENDERER_DX.value):
                self.bs_render_var.set("DirectX")
            elif values.get(UIField.BS_RENDERER_GL.value):
                self.bs_render_var.set("OpenGL")

            # AI/ML Model settings
            if UIField.MODEL_ENABLED_TOGGLE.value in values:
                self.model_enabled_var.set(bool(values[UIField.MODEL_ENABLED_TOGGLE.value]))
            if UIField.MODEL_TYPE.value in values:
                self.model_type_var.set(str(values[UIField.MODEL_TYPE.value]))
            if UIField.ROBOFLOW_API_KEY.value in values:
                self.roboflow_api_key_var.set(str(values[UIField.ROBOFLOW_API_KEY.value]))
            if UIField.ROBOFLOW_MODEL_ID.value in values:
                self.roboflow_model_id_var.set(str(values[UIField.ROBOFLOW_MODEL_ID.value]))
            if UIField.MODEL_CONFIDENCE_THRESHOLD.value in values:
                self.model_confidence_var.set(str(values[UIField.MODEL_CONFIDENCE_THRESHOLD.value]))

        finally:
            self._suspend_traces -= 1

        if theme_value is not None:
            self._apply_theme(theme_value)

    def set_running_state(self, running: bool) -> None:
        start_state = tk.DISABLED if running else tk.NORMAL
        stop_state = tk.NORMAL if running else tk.DISABLED
        self.start_btn.configure(state=start_state)
        self.stop_btn.configure(state=stop_state)

        for key, widget in self._config_widgets.items():
            if widget in {self.stop_btn, self.start_btn}:
                continue
            try:
                if isinstance(widget, ttk.Combobox):
                    if key == "emulator_combobox":
                        widget.configure(state=tk.DISABLED if running else READONLY)
                    elif widget is self.adb_serial_combo:
                        widget.configure(state=tk.DISABLED if running else tk.NORMAL)
                    else:
                        widget.configure(state=tk.DISABLED if running else READONLY)
                elif isinstance(widget, ttk.Spinbox):
                    widget.configure(state=tk.DISABLED if running else READONLY)
                elif isinstance(widget, ttk.Radiobutton) and key in [
                    UIField.DIRECTX_TOGGLE.value,
                    UIField.OPENGL_TOGGLE.value,
                    UIField.BS_RENDERER_DX.value,
                    UIField.BS_RENDERER_GL.value,
                    UIField.BS_RENDERER_VK.value,
                ]:
                    widget.configure(state=tk.DISABLED if running else tk.NORMAL)
                elif widget in [
                    self.adb_connect_btn,
                    self.adb_refresh_btn,
                    self.adb_restart_btn,
                    self.adb_set_size_btn,
                    self.adb_reset_size_btn,
                ]:
                    widget.configure(state=tk.DISABLED if running else tk.NORMAL)
                elif isinstance(widget, ttk.Checkbutton):
                    widget.configure(state=tk.DISABLED if running else tk.NORMAL)
                elif isinstance(widget, ttk.Button):
                    widget.configure(state=tk.DISABLED if running else tk.NORMAL)

            except tk.TclError:
                continue
        if running:
            self._hide_action_button()

    def show_action_button(self, text: str, callback: Callable[[], None]) -> None:
        self._action_callback = callback
        self.action_btn.configure(text=text)
        self.stop_btn.grid_remove()
        self.action_btn.grid()

    def hide_action_button(self) -> None:
        self._hide_action_button()

    def append_log(self, message: str) -> None:
        self.event_log.configure(state="normal")
        self.event_log.delete("1.0", "end")
        self.event_log.insert("end", message)
        self.event_log.configure(state="disabled")
        self.event_log.see("end")

    def set_status(self, text: str) -> None:
        self._status_text = text

    def set_model_connection_status(self, connected: bool, model_type: str = "", in_use: bool = False) -> None:
        """Update the model connection status display in the GUI.

        Args:
            connected: Whether the model is connected and available
            model_type: Type of model (e.g., 'roboflow')
            in_use: Whether the model is actively being used
        """
        if not hasattr(self, 'model_connection_status_label'):
            return

        if connected and in_use:
            status_text = f"🟢 {model_type.capitalize()} model connected and active"
            self.model_connection_status_label.configure(text=status_text, foreground="green")
        elif connected:
            status_text = f"🟡 {model_type.capitalize()} model connected (not in use)"
            self.model_connection_status_label.configure(text=status_text, foreground="orange")
        else:
            self.model_connection_status_label.configure(text="", foreground="")

    def update_stats(self, stats: dict[str, object] | None) -> None:
        if not stats:
            return

        def as_string(field: StatField, default: str = "0") -> str:
            value = stats.get(field.value, default)
            return str(value)

        def as_int(field: StatField) -> int:
            value = stats.get(field.value)
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        for field, var in self.stat_labels.items():
            var.set(as_string(field))

        runtime = stats.get(BotStatField.TIME_SINCE_START.value)
        if runtime is not None:
            self.bot_labels[BotStatField.TIME_SINCE_START].set(str(runtime))
        failures = stats.get(BotStatField.RESTARTS_AFTER_FAILURE.value)
        if failures is not None:
            self.bot_labels[BotStatField.RESTARTS_AFTER_FAILURE].set(str(failures))

        winrate_raw = stats.get(DerivedStatField.WINRATE.value)
        wins = as_int(StatField.WINS)
        losses = as_int(StatField.LOSSES)
        parsed_winrate = self._parse_winrate_value(winrate_raw)
        winrate = parsed_winrate if parsed_winrate is not None else self._calculate_winrate_percentage(wins, losses)
        gauge_fg = getattr(self._style.colors, "success", "#2ecc71") if hasattr(self._style, "colors") else "#2ecc71"
        self.win_gauge.animate_to(winrate, fg_colour=gauge_fg, text_colour=self._label_foreground())

        # Update win streak stats
        current_streak = stats.get(DerivedStatField.CURRENT_WIN_STREAK.value, 0)
        best_streak = stats.get(DerivedStatField.BEST_WIN_STREAK.value, 0)
        if hasattr(self, "current_streak_var"):
            self.current_streak_var.set(str(current_streak))
        if hasattr(self, "best_streak_var"):
            self.best_streak_var.set(str(best_streak))

    def _build_tabs(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))

        self.jobs_tab = ttk.Frame(self.notebook)
        self.emulator_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.misc_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.jobs_tab, text="Jobs")
        self.notebook.add(self.emulator_tab, text="Emulator")
        self.notebook.add(self.stats_tab, text="Stats")
        self.notebook.add(self.misc_tab, text="Misc")
        self.notebook.add(self.help_tab, text="Help")

        self._create_jobs_tab()
        self._create_emulator_tab()
        self._create_stats_tab()
        self._create_misc_tab()
        self._create_help_tab()

    def _build_bottom_row(self) -> None:
        bottom = ttk.Frame(self)
        bottom.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom.columnconfigure(0, weight=1)

        log_container = ttk.Frame(bottom)
        log_container.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        log_container.columnconfigure(0, weight=1)
        self.event_log = tk.Text(log_container, height=1, wrap="none")
        self.event_log.grid(row=0, column=0, sticky="ew")
        self.event_log.configure(state="disabled")
        self._status_text = "Idle"

        self.start_btn = tk.Button(bottom, text="Start", bg="green", fg="white", width=10)
        self.start_btn.grid(row=0, column=1, sticky="e", padx=(0, 6))
        self._register_config_widget("Start", self.start_btn)

        self.stop_btn = tk.Button(bottom, text="Stop", bg="red", fg="white", width=10, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, sticky="e")
        self._register_config_widget("Stop", self.stop_btn)

        self.action_btn = ttk.Button(bottom, text="Retry")
        self.action_btn.grid(row=0, column=2, sticky="e")
        self.action_btn.grid_remove()
        self._action_callback: Callable[[], None] | None = None
        self.action_btn.configure(command=self._on_action_pressed)

    def _create_jobs_tab(self) -> None:
        frame = ttk.Labelframe(self.jobs_tab, text="Jobs", padding=10)
        frame.pack(padx=10, pady=10, anchor="n", fill="x")

        frame.columnconfigure(1, weight=1)

        job_defaults = {job.key: job.default for job in JOBS}
        jobs_by_key = {job.key: job for job in JOBS}
        self.jobs_vars: dict[UIField, ttk.BooleanVar] = {}

        checkbox_width = 25

        def add_job_checkbox(
            field: UIField,
            text: str,
            row_index: int,
            bootstyle: str,
        ) -> None:
            var = ttk.BooleanVar(value=job_defaults.get(field, False))
            checkbox = ttk.Checkbutton(
                frame,
                text=text,
                variable=var,
                bootstyle=bootstyle,
                command=self._notify_config_change,
                width=checkbox_width,
            )
            checkbox.grid(row=row_index, column=0, sticky="w", pady=2)
            self.jobs_vars[field] = var
            self._trace_variable(var)
            self._register_config_widget(field.value, checkbox)

        primary_bootstyle = "warning-outline-toolbutton"
        secondary_bootstyle = "info-outline-toolbutton"

        add_job_checkbox(
            UIField.CLASSIC_1V1_USER_TOGGLE,
            "⚔️ Classic 1v1 battles",
            0,
            primary_bootstyle,
        )
        add_job_checkbox(
            UIField.CLASSIC_2V2_USER_TOGGLE,
            "👥 Classic 2v2 battles",
            1,
            primary_bootstyle,
        )
        add_job_checkbox(
            UIField.TROPHY_ROAD_USER_TOGGLE,
            "🏆 Trophy Road battles",
            2,
            primary_bootstyle,
        )

        random_job = jobs_by_key[UIField.RANDOM_DECKS_USER_TOGGLE]
        deck_config: ComboConfig = random_job.extras[UIField.DECK_NUMBER_SELECTION]
        self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE] = ttk.BooleanVar(value=random_job.default)
        random_checkbox = ttk.Checkbutton(
            frame,
            text="🎲 Randomize Deck",
            variable=self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE],
            bootstyle=secondary_bootstyle,
            command=self._notify_config_change,
            width=checkbox_width,
        )
        random_checkbox.grid(row=3, column=0, sticky="w", pady=2)
        self._trace_variable(self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE])
        self._register_config_widget(UIField.RANDOM_DECKS_USER_TOGGLE.value, random_checkbox)

        deck_info = ttk.Label(frame, text="ⓘ", bootstyle="info")
        deck_info.grid(row=3, column=2, sticky="e", padx=(0, 2))
        ToolTip(deck_info, "Deck Number to use for Randomization")
        self.deck_var = ttk.StringVar(value=str(deck_config.default))
        self.deck_spin = ttk.Spinbox(
            frame,
            from_=min(deck_config.values),
            to=max(deck_config.values),
            width=6,
            textvariable=self.deck_var,
            command=self._notify_config_change,
            state=READONLY,
        )
        self.deck_spin.grid(row=3, column=3, sticky="e")
        self._trace_variable(self.deck_var)
        self._register_config_widget(UIField.DECK_NUMBER_SELECTION.value, self.deck_spin)

        cycle_job = jobs_by_key[UIField.CYCLE_DECKS_USER_TOGGLE]
        max_config: ComboConfig = cycle_job.extras[UIField.MAX_DECK_SELECTION]
        self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE] = ttk.BooleanVar(value=cycle_job.default)
        cycle_checkbox = ttk.Checkbutton(
            frame,
            text="♻️ Cycle decks",
            variable=self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE],
            bootstyle=secondary_bootstyle,
            command=self._notify_config_change,
            width=checkbox_width,
        )
        cycle_checkbox.grid(row=4, column=0, sticky="w", pady=2)
        self._trace_variable(self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE])
        self._register_config_widget(UIField.CYCLE_DECKS_USER_TOGGLE.value, cycle_checkbox)

        max_deck_info = ttk.Label(frame, text="ⓘ", bootstyle="info")
        max_deck_info.grid(row=4, column=2, sticky="e", padx=(0, 2))
        ToolTip(max_deck_info, "Number of decks to cycle through")
        self.max_deck_var = ttk.StringVar(value=str(max_config.default))
        self.max_deck_spin = ttk.Spinbox(
            frame,
            from_=min(max_config.values),
            to=max(max_config.values),
            width=6,
            textvariable=self.max_deck_var,
            command=self._notify_config_change,
            state=READONLY,
        )
        self.max_deck_spin.grid(row=4, column=3, sticky="e")
        self._trace_variable(self.max_deck_var)
        self._register_config_widget(UIField.MAX_DECK_SELECTION.value, self.max_deck_spin)

        add_job_checkbox(UIField.RANDOM_PLAYS_USER_TOGGLE, "❔ Random plays", 5, secondary_bootstyle)
        add_job_checkbox(UIField.DISABLE_WIN_TRACK_TOGGLE, "⏭️ Skip win/loss check", 6, secondary_bootstyle)
        add_job_checkbox(UIField.CARD_MASTERY_USER_TOGGLE, "🎯 Card Masteries", 7, secondary_bootstyle)
        add_job_checkbox(UIField.CARD_UPGRADE_USER_TOGGLE, "⬆️ Upgrade Cards", 8, secondary_bootstyle)

    def _create_emulator_tab(self) -> None:
        # Main container frame for the tab
        container = ttk.Frame(self.emulator_tab, padding=10)
        container.pack(fill=BOTH, expand=YES)

        # BlueStacks info label
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(info_frame, text="Emulator: BlueStacks 5 (Only supported emulator)").pack(side=LEFT, padx=(0, 5))

        # Frame to hold BlueStacks settings
        self.settings_container = ttk.Frame(container)
        self.settings_container.pack(fill=BOTH, expand=YES)

        # Create BlueStacks settings frame
        self.bluestacks_frame = ttk.Frame(self.settings_container)
        self.bluestacks_frame.pack(fill=BOTH, expand=YES)

        # Populate the BlueStacks settings
        self._create_bluestacks_settings(self.bluestacks_frame)

