from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox
from typing import TYPE_CHECKING

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, READONLY, YES, X
from ttkbootstrap.tooltip import ToolTip

from pyclashbot.interface.config import (
    BLUESTACKS_SETTINGS,
    CLAN_BATTLE_MODES,
    JOBS,
    STRATEGY_SETTINGS,
    ComboConfig,
)
from pyclashbot.interface.enums import (
    BATTLE_STAT_FIELDS,
    BATTLE_STAT_LABELS,
    BOT_STAT_FIELDS,
    BOT_STAT_LABELS,
    COLLECTION_STAT_FIELDS,
    COLLECTION_STAT_LABELS,
    BotStatField,
    DerivedStatField,
    StatField,
    UIField,
)
from pyclashbot.interface.widgets import DualRingGauge

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

        emulator_choice = self.emulator_var.get()
        values[UIField.BLUESTACKS_EMULATOR_TOGGLE.value] = emulator_choice == "BlueStacks 5"
        values[UIField.ADB_TOGGLE.value] = emulator_choice == "ADB Device"

        bs_render = self.bs_render_var.get()
        values[UIField.BS_RENDERER_DX.value] = bs_render == "DirectX"
        values[UIField.BS_RENDERER_GL.value] = bs_render == "OpenGL"
        values[UIField.BS_RENDERER_VK.value] = bs_render == "Vulkan"

        values[UIField.ADB_SERIAL.value] = self.adb_serial_var.get()

        values[UIField.THEME_NAME.value] = self.theme_var.get() or self.DEFAULT_THEME

        # AI/ML Model settings
        values[UIField.MODEL_ENABLED_TOGGLE.value] = bool(self.model_enabled_var.get())
        values[UIField.MODEL_TYPE.value] = self.model_type_var.get()
        values[UIField.ROBOFLOW_API_KEY.value] = self.roboflow_api_key_var.get()
        values[UIField.ROBOFLOW_MODEL_ID.value] = self.roboflow_model_id_var.get()
        values[UIField.ROBOFLOW_WORKFLOW_ID.value] = self.roboflow_workflow_id_var.get()
        values[UIField.MODEL_CONFIDENCE_THRESHOLD.value] = self._safe_float(
            self.model_confidence_var.get(), fallback=0.7
        )

        # Battle Strategy settings
        values[UIField.STRATEGY_ELIXIR_MODE.value] = self.strategy_elixir_var.get()
        values[UIField.STRATEGY_PUSH_MODE.value] = self.strategy_push_var.get()
        values[UIField.STRATEGY_AGGRESSION_LEVEL.value] = self.strategy_aggression_var.get()
        values[UIField.STRATEGY_TOWER_HEALTH_AWARE.value] = bool(self.strategy_tower_health_var.get())
        values[UIField.STRATEGY_PLACEMENT_MODE.value] = self.strategy_placement_var.get()

        # Clan Battle settings
        values[UIField.CLAN_BATTLE_USER_TOGGLE.value] = bool(self.clan_battle_enabled_var.get())
        values[UIField.CLAN_BATTLE_MODE.value] = self.clan_battle_mode_var.get()
        values[UIField.CLAN_BATTLE_MANUAL_START.value] = bool(self.clan_battle_manual_var.get())

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

            if values.get(UIField.BLUESTACKS_EMULATOR_TOGGLE.value):
                self.emulator_var.set("BlueStacks 5")
            elif values.get(UIField.ADB_TOGGLE.value):
                self.emulator_var.set("ADB Device")
            else:
                self.emulator_var.set("BlueStacks 5")

            if values.get(UIField.BS_RENDERER_VK.value):
                self.bs_render_var.set("Vulkan")
            elif values.get(UIField.BS_RENDERER_DX.value):
                self.bs_render_var.set("DirectX")
            elif values.get(UIField.BS_RENDERER_GL.value):
                self.bs_render_var.set("OpenGL")

            if UIField.ADB_SERIAL.value in values:
                self.adb_serial_var.set(str(values[UIField.ADB_SERIAL.value]))

            # AI/ML Model settings
            if UIField.MODEL_ENABLED_TOGGLE.value in values:
                self.model_enabled_var.set(bool(values[UIField.MODEL_ENABLED_TOGGLE.value]))
            if UIField.MODEL_TYPE.value in values:
                self.model_type_var.set(str(values[UIField.MODEL_TYPE.value]))
            if UIField.ROBOFLOW_API_KEY.value in values:
                self.roboflow_api_key_var.set(str(values[UIField.ROBOFLOW_API_KEY.value]))
            if UIField.ROBOFLOW_MODEL_ID.value in values:
                self.roboflow_model_id_var.set(str(values[UIField.ROBOFLOW_MODEL_ID.value]))
            if UIField.ROBOFLOW_WORKFLOW_ID.value in values:
                self.roboflow_workflow_id_var.set(str(values[UIField.ROBOFLOW_WORKFLOW_ID.value]))
            if UIField.MODEL_CONFIDENCE_THRESHOLD.value in values:
                self.model_confidence_var.set(str(values[UIField.MODEL_CONFIDENCE_THRESHOLD.value]))

            # Battle Strategy settings
            if UIField.STRATEGY_ELIXIR_MODE.value in values:
                self.strategy_elixir_var.set(str(values[UIField.STRATEGY_ELIXIR_MODE.value]))
            if UIField.STRATEGY_PUSH_MODE.value in values:
                self.strategy_push_var.set(str(values[UIField.STRATEGY_PUSH_MODE.value]))
            if UIField.STRATEGY_AGGRESSION_LEVEL.value in values:
                self.strategy_aggression_var.set(str(values[UIField.STRATEGY_AGGRESSION_LEVEL.value]))
            if UIField.STRATEGY_TOWER_HEALTH_AWARE.value in values:
                self.strategy_tower_health_var.set(bool(values[UIField.STRATEGY_TOWER_HEALTH_AWARE.value]))
            if UIField.STRATEGY_PLACEMENT_MODE.value in values:
                self.strategy_placement_var.set(str(values[UIField.STRATEGY_PLACEMENT_MODE.value]))

            # Clan Battle settings
            if UIField.CLAN_BATTLE_USER_TOGGLE.value in values:
                self.clan_battle_enabled_var.set(bool(values[UIField.CLAN_BATTLE_USER_TOGGLE.value]))
            if UIField.CLAN_BATTLE_MODE.value in values:
                self.clan_battle_mode_var.set(str(values[UIField.CLAN_BATTLE_MODE.value]))
            if UIField.CLAN_BATTLE_MANUAL_START.value in values:
                self.clan_battle_manual_var.set(bool(values[UIField.CLAN_BATTLE_MANUAL_START.value]))

        finally:
            self._suspend_traces -= 1

        if theme_value is not None:
            self._apply_theme(theme_value)

        self._show_current_emulator_settings()

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
        self.strategy_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)
        self.misc_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.jobs_tab, text="Jobs")
        self.notebook.add(self.emulator_tab, text="Emulator")
        self.notebook.add(self.strategy_tab, text="Strategy")
        self.notebook.add(self.stats_tab, text="Stats")
        self.notebook.add(self.misc_tab, text="Misc")
        self.notebook.add(self.help_tab, text="Help")

        self._create_jobs_tab()
        self._create_emulator_tab()
        self._create_strategy_tab()
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

        # Clan Battle Settings Frame
        clan_frame = ttk.Labelframe(self.jobs_tab, text="Clan Battles", padding=10)
        clan_frame.pack(padx=10, pady=(0, 10), anchor="n", fill="x")
        clan_frame.columnconfigure(1, weight=1)

        # Clan battle enabled toggle
        self.clan_battle_enabled_var = ttk.BooleanVar(value=False)
        clan_battle_checkbox = ttk.Checkbutton(
            clan_frame,
            text="🏰 Enable Clan Battles",
            variable=self.clan_battle_enabled_var,
            bootstyle=primary_bootstyle,
            command=self._on_clan_battle_toggle_changed,
            width=checkbox_width,
        )
        clan_battle_checkbox.grid(row=0, column=0, sticky="w", pady=2)
        self._trace_variable(self.clan_battle_enabled_var)
        self._register_config_widget(UIField.CLAN_BATTLE_USER_TOGGLE.value, clan_battle_checkbox)

        # Clan battle mode dropdown
        ttk.Label(clan_frame, text="Mode:").grid(row=1, column=0, sticky="w", padx=(20, 5), pady=2)
        self.clan_battle_mode_var = ttk.StringVar(value="Battle")
        self.clan_battle_mode_combo = ttk.Combobox(
            clan_frame,
            textvariable=self.clan_battle_mode_var,
            values=CLAN_BATTLE_MODES,
            state=READONLY,
            width=18,
        )
        self.clan_battle_mode_combo.grid(row=1, column=1, sticky="w", pady=2)
        self._trace_variable(self.clan_battle_mode_var)
        self._register_config_widget(UIField.CLAN_BATTLE_MODE.value, self.clan_battle_mode_combo)
        ToolTip(self.clan_battle_mode_combo, "Select the clan battle mode to use")

        # Manual start toggle
        self.clan_battle_manual_var = ttk.BooleanVar(value=False)
        clan_manual_checkbox = ttk.Checkbutton(
            clan_frame,
            text="⏳ Manual Start (wait for battle)",
            variable=self.clan_battle_manual_var,
            bootstyle=secondary_bootstyle,
            command=self._notify_config_change,
            width=checkbox_width,
        )
        clan_manual_checkbox.grid(row=2, column=0, columnspan=2, sticky="w", padx=(20, 0), pady=2)
        self._trace_variable(self.clan_battle_manual_var)
        self._register_config_widget(UIField.CLAN_BATTLE_MANUAL_START.value, clan_manual_checkbox)
        ToolTip(clan_manual_checkbox, "When enabled, the bot will wait for you to start the battle manually")

        # Upload custom icon button
        self.upload_icon_btn = ttk.Button(
            clan_frame,
            text="📁 Upload Mode Icon",
            command=self._on_upload_clan_icon,
            bootstyle="info-outline",
        )
        self.upload_icon_btn.grid(row=3, column=0, columnspan=2, sticky="w", padx=(20, 0), pady=(8, 2))
        self._register_config_widget("upload_clan_icon_btn", self.upload_icon_btn)
        ToolTip(self.upload_icon_btn, "Upload a custom icon for the selected clan battle mode")

        # Icon status label
        self.clan_icon_status_label = ttk.Label(
            clan_frame,
            text="",
            font=("TkDefaultFont", 8),
        )
        self.clan_icon_status_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=(20, 0), pady=(0, 2))

        # Initialize clan battle widgets state
        self._on_clan_battle_toggle_changed()

    def _create_emulator_tab(self) -> None:
        # Main container frame for the tab
        container = ttk.Frame(self.emulator_tab, padding=10)
        container.pack(fill=BOTH, expand=YES)

        # Emulator Selection Dropdown
        selection_frame = ttk.Frame(container)
        selection_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(selection_frame, text="Select Emulator:").pack(side=LEFT, padx=(0, 5))

        self.emulator_var = ttk.StringVar(value="BlueStacks 5")  # Default value
        emulator_choices = ["BlueStacks 5", "ADB Device"]
        self.emulator_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.emulator_var,
            values=emulator_choices,
            state=READONLY,
            width=20,
        )
        self.emulator_combo.pack(side=LEFT, fill=X, expand=True)
        self.emulator_combo.bind("<<ComboboxSelected>>", self._on_emulator_changed)
        # Register the combobox itself for state management
        self._register_config_widget("emulator_combobox", self.emulator_combo)

        # Frame to hold the currently selected emulator's settings
        self.settings_container = ttk.Frame(container)
        self.settings_container.pack(fill=BOTH, expand=YES)

        # Create the individual settings frames but don't pack them yet
        self.bluestacks_frame = ttk.Frame(self.settings_container)
        self.adb_frame = ttk.Frame(self.settings_container)

        # Store frames in a dictionary for easy access
        self.emulator_settings_frames = {
            "BlueStacks 5": self.bluestacks_frame,
            "ADB Device": self.adb_frame,
        }

        # Populate the settings frames
        self._create_bluestacks_settings(self.bluestacks_frame)
        self._create_adb_tab(self.adb_frame)

        # Show the initial settings based on the default value
        self._show_current_emulator_settings()

    def _create_bluestacks_settings(self, parent_frame: ttk.Frame) -> None:
        frame = ttk.Labelframe(parent_frame, text="Render Mode", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        self.bs_render_var = ttk.StringVar(value="DirectX")
        for config in BLUESTACKS_SETTINGS:
            if config.key == UIField.BS_RENDERER_DX:
                value = "DirectX"
            elif config.key == UIField.BS_RENDERER_VK:
                value = "Vulkan"
            else:
                value = "OpenGL"
            rb = ttk.Radiobutton(
                frame,
                text=value,
                variable=self.bs_render_var,
                value=value,
                command=self._notify_config_change,
            )
            rb.pack(anchor="w")
            self._register_config_widget(config.key.value, rb)

    def _create_adb_tab(self, parent_frame: ttk.Frame) -> None:
        """Create the widgets for the ADB Device settings tab."""
        frame = ttk.Labelframe(parent_frame, text="Device Settings", padding=10)
        frame.pack(fill="x", padx=5, pady=5)

        # --- Row 1: Serial Input ---
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=(0, 5))
        row1.columnconfigure(1, weight=1)

        ttk.Label(row1, text="Device Serial:").grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.adb_serial_var = ttk.StringVar(value="")
        self.adb_serial_combo = ttk.Combobox(
            row1,
            textvariable=self.adb_serial_var,
            state=tk.NORMAL,
        )
        self.adb_serial_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self._register_config_widget(UIField.ADB_SERIAL.value, self.adb_serial_combo)
        self._trace_variable(self.adb_serial_var)

        # --- Row 2: Connect/Refresh Buttons ---
        row_buttons_connect = ttk.Frame(frame)
        row_buttons_connect.pack(fill="x", pady=(0, 8))
        row_buttons_connect.columnconfigure(0, weight=1)
        row_buttons_connect.columnconfigure(1, weight=1)

        self.adb_connect_btn = ttk.Button(row_buttons_connect, text="Connect", style="success.TButton")
        self.adb_connect_btn.grid(row=0, column=0, padx=(0, 3), sticky="ew")
        self._register_config_widget("adb_connect_btn", self.adb_connect_btn)

        self.adb_refresh_btn = ttk.Button(row_buttons_connect, text="Refresh")
        self.adb_refresh_btn.grid(row=0, column=1, padx=(3, 0), sticky="ew")
        self._register_config_widget("adb_refresh_btn", self.adb_refresh_btn)

        # --- Row 3: Action Buttons (Stacked Vertically) ---
        row_buttons_action = ttk.Frame(frame)
        row_buttons_action.pack(fill="x")

        self.adb_restart_btn = ttk.Button(row_buttons_action, text="Restart ADB")
        self.adb_restart_btn.pack(fill=X, pady=(0, 3))
        self._register_config_widget("adb_restart_btn", self.adb_restart_btn)

        self.adb_set_size_btn = ttk.Button(row_buttons_action, text="Set Size & Density")
        self.adb_set_size_btn.pack(fill=X, pady=3)
        self._register_config_widget("adb_set_size_btn", self.adb_set_size_btn)

        self.adb_reset_size_btn = ttk.Button(row_buttons_action, text="Reset Size & Density")
        self.adb_reset_size_btn.pack(fill=X, pady=(3, 0))
        self._register_config_widget("adb_reset_size_btn", self.adb_reset_size_btn)

        ToolTip(self.adb_set_size_btn, "Sets screen to 419x633 and density to 160")
        ToolTip(self.adb_reset_size_btn, "Resets screen size and density to device defaults")

    def _create_strategy_tab(self) -> None:
        """Create the Strategy tab with battle strategy configuration."""
        container = ttk.Frame(self.strategy_tab, padding=10)
        container.pack(fill=BOTH, expand=YES)

        # Elixir Management Frame
        elixir_frame = ttk.Labelframe(container, text="⚡ Elixir Management", padding=10)
        elixir_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(elixir_frame, text="Strategy:").pack(anchor="w", pady=(0, 4))

        elixir_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_ELIXIR_MODE)
        self.strategy_elixir_var = ttk.StringVar(value=str(elixir_config.default))
        self.strategy_elixir_combo = ttk.Combobox(
            elixir_frame,
            textvariable=self.strategy_elixir_var,
            values=elixir_config.values,
            state=READONLY,
            width=25,
        )
        self.strategy_elixir_combo.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.strategy_elixir_var)
        self._register_config_widget(UIField.STRATEGY_ELIXIR_MODE.value, self.strategy_elixir_combo)

        elixir_desc = ttk.Label(
            elixir_frame,
            text="• Conservative: Save elixir, wait for bigger pushes\n"
                 "• Balanced: Mix of patience and aggression\n"
                 "• Aggressive: Spend elixir quickly, constant pressure\n"
                 "• Adaptive: Dynamically adjust based on battle phase",
            justify=LEFT,
            font=("TkDefaultFont", 9),
        )
        elixir_desc.pack(anchor="w", pady=(0, 4))

        # Push Strategy Frame
        push_frame = ttk.Labelframe(container, text="🎯 Push Strategy", padding=10)
        push_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(push_frame, text="Strategy:").pack(anchor="w", pady=(0, 4))

        push_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_PUSH_MODE)
        self.strategy_push_var = ttk.StringVar(value=str(push_config.default))
        self.strategy_push_combo = ttk.Combobox(
            push_frame,
            textvariable=self.strategy_push_var,
            values=push_config.values,
            state=READONLY,
            width=25,
        )
        self.strategy_push_combo.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.strategy_push_var)
        self._register_config_widget(UIField.STRATEGY_PUSH_MODE.value, self.strategy_push_combo)

        push_desc = ttk.Label(
            push_frame,
            text="• Single Lane: Focus attacks on one lane\n"
                 "• Dual Lane: Alternate between both lanes\n"
                 "• Counter Push: Push in lane after successful defense\n"
                 "• Adaptive: Smart lane selection based on tower health",
            justify=LEFT,
            font=("TkDefaultFont", 9),
        )
        push_desc.pack(anchor="w", pady=(0, 4))

        # Aggression Level Frame
        aggression_frame = ttk.Labelframe(container, text="🔥 Aggression Level", padding=10)
        aggression_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(aggression_frame, text="Level:").pack(anchor="w", pady=(0, 4))

        aggression_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_AGGRESSION_LEVEL)
        self.strategy_aggression_var = ttk.StringVar(value=str(aggression_config.default))
        self.strategy_aggression_combo = ttk.Combobox(
            aggression_frame,
            textvariable=self.strategy_aggression_var,
            values=aggression_config.values,
            state=READONLY,
            width=25,
        )
        self.strategy_aggression_combo.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.strategy_aggression_var)
        self._register_config_widget(UIField.STRATEGY_AGGRESSION_LEVEL.value, self.strategy_aggression_combo)

        aggression_desc = ttk.Label(
            aggression_frame,
            text="• Defensive: Wait longer, patient play style\n"
                 "• Moderate: Balanced timing between plays\n"
                 "• Aggressive: Faster plays, more pressure\n"
                 "• Very Aggressive: Minimal waiting, maximum pressure",
            justify=LEFT,
            font=("TkDefaultFont", 9),
        )
        aggression_desc.pack(anchor="w", pady=(0, 4))

        # Advanced Strategy Settings Frame
        advanced_frame = ttk.Labelframe(container, text="🏰 Advanced Settings", padding=10)
        advanced_frame.pack(fill=X, pady=(0, 10))

        # Tower Health Awareness Toggle
        self.strategy_tower_health_var = ttk.BooleanVar(value=True)
        tower_health_checkbox = ttk.Checkbutton(
            advanced_frame,
            text="Enable Tower Health Awareness",
            variable=self.strategy_tower_health_var,
            bootstyle="round-toggle",
            command=self._notify_config_change,
        )
        tower_health_checkbox.pack(anchor="w", pady=(0, 4))
        self._trace_variable(self.strategy_tower_health_var)
        self._register_config_widget(UIField.STRATEGY_TOWER_HEALTH_AWARE.value, tower_health_checkbox)

        tower_health_desc = ttk.Label(
            advanced_frame,
            text="Adjusts strategy based on tower health differences.\n"
                 "When enabled, bot plays more defensively when behind\n"
                 "and more aggressively when ahead.",
            justify=LEFT,
            font=("TkDefaultFont", 9),
        )
        tower_health_desc.pack(anchor="w", padx=(20, 0), pady=(0, 8))

        # Placement Mode
        ttk.Label(advanced_frame, text="Card Placement Mode:").pack(anchor="w", pady=(4, 4))

        placement_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_PLACEMENT_MODE)
        self.strategy_placement_var = ttk.StringVar(value=str(placement_config.default))
        self.strategy_placement_combo = ttk.Combobox(
            advanced_frame,
            textvariable=self.strategy_placement_var,
            values=placement_config.values,
            state=READONLY,
            width=25,
        )
        self.strategy_placement_combo.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.strategy_placement_var)
        self._register_config_widget(UIField.STRATEGY_PLACEMENT_MODE.value, self.strategy_placement_combo)

        placement_desc = ttk.Label(
            advanced_frame,
            text="• Auto: Adjusts based on game state (recommended)\n"
                 "• Offensive: Place troops at bridge for pressure\n"
                 "• Defensive: Place troops near towers for protection\n"
                 "• Balanced: Standard placement based on threat detection",
            justify=LEFT,
            font=("TkDefaultFont", 9),
        )
        placement_desc.pack(anchor="w", pady=(0, 4))

        # Info box
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=X, pady=(10, 0))

        info_label = ttk.Label(
            info_frame,
            text="Info: These strategies control how the bot manages elixir, chooses lanes, "
                 "and positions cards during battle. Settings are applied at the start of each battle.",
            wraplength=450,
            justify=LEFT,
            font=("TkDefaultFont", 9),
            bootstyle="info",
        )
        info_label.pack(anchor="w")


    def _create_stats_tab(self) -> None:
        container = ttk.Frame(self.stats_tab, padding=10)
        container.pack(fill=BOTH, expand=YES)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)
        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        gauge_frame = ttk.Labelframe(left, text="Win Rate", padding=10)
        gauge_frame.pack(fill=X)
        self.win_gauge = DualRingGauge(gauge_frame, diameter=120, thickness=12, text_color="#00aaff")
        self.win_gauge.pack(anchor="center")

        battle_frame = ttk.Labelframe(left, text="Battle Stats", padding=10)
        battle_frame.pack(fill=BOTH, expand=YES, pady=(8, 0))
        self.stat_labels: dict[StatField, ttk.StringVar] = {}
        for row, field in enumerate(BATTLE_STAT_FIELDS):
            title = BATTLE_STAT_LABELS[field]
            label = ttk.Label(battle_frame, text=title)
            label.grid(row=row, column=0, sticky="w")
            self._theme_labels.append(label)
            var = ttk.StringVar(value="0")
            ttk.Label(battle_frame, textvariable=var, foreground="#00aaff").grid(row=row, column=1, sticky="e")
            self.stat_labels[field] = var

        # Add win streak stats
        ttk.Separator(battle_frame, orient="horizontal").grid(
            row=len(BATTLE_STAT_FIELDS), column=0, columnspan=2, sticky="ew", pady=(8, 4)
        )
        streak_row = len(BATTLE_STAT_FIELDS) + 1
        ttk.Label(battle_frame, text="Current Streak:").grid(row=streak_row, column=0, sticky="w")
        self.current_streak_var = ttk.StringVar(value="0")
        ttk.Label(battle_frame, textvariable=self.current_streak_var, foreground="#00aaff").grid(
            row=streak_row, column=1, sticky="e"
        )
        ttk.Label(battle_frame, text="Best Streak:").grid(row=streak_row + 1, column=0, sticky="w")
        self.best_streak_var = ttk.StringVar(value="0")
        ttk.Label(battle_frame, textvariable=self.best_streak_var, foreground="#00aaff").grid(
            row=streak_row + 1, column=1, sticky="e"
        )

        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        collection_frame = ttk.Labelframe(right, text="Collection Stats", padding=10)
        collection_frame.pack(fill=X)
        for row, field in enumerate(COLLECTION_STAT_FIELDS):
            title = COLLECTION_STAT_LABELS[field]
            label = ttk.Label(collection_frame, text=title)
            label.grid(row=row, column=0, sticky="w")
            self._theme_labels.append(label)
            var = ttk.StringVar(value="0")
            ttk.Label(collection_frame, textvariable=var, foreground="#00aaff").grid(row=row, column=1, sticky="e")
            self.stat_labels[field] = var

        bot_frame = ttk.Labelframe(right, text="Bot Stats", padding=10)
        bot_frame.pack(fill=BOTH, expand=YES, pady=(8, 0))
        self.bot_labels = {
            BotStatField.RESTARTS_AFTER_FAILURE: ttk.StringVar(value="0"),
            BotStatField.TIME_SINCE_START: ttk.StringVar(value="00:00:00"),
        }
        for row, field in enumerate(BOT_STAT_FIELDS):
            title = BOT_STAT_LABELS[field]
            label = ttk.Label(bot_frame, text=title)
            label.grid(row=row, column=0, sticky="w")
            self._theme_labels.append(label)
            ttk.Label(
                bot_frame,
                textvariable=self.bot_labels[field],
                foreground="#00aaff",
            ).grid(row=row, column=1, sticky="e")

    def _create_misc_tab(self) -> None:
        appearance = ttk.Labelframe(self.misc_tab, text="Appearance", padding=10)
        appearance.pack(padx=10, pady=10, anchor="n", fill="x")

        ttk.Label(appearance, text="Select Theme:").pack(anchor="w", pady=(0, 4))
        self.theme_combo = ttk.Combobox(
            appearance,
            values=self._style.theme_names(),
            width=25,
            state=READONLY,
            textvariable=self.theme_var,
        )
        self.theme_combo.pack(anchor="w")
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        self._trace_variable(self.theme_var)
        self._register_config_widget(UIField.THEME_NAME.value, self.theme_combo)

        ttk.Separator(self.misc_tab, orient="horizontal").pack(fill="x", padx=10, pady=(6, 0))
        data_frame = ttk.Labelframe(self.misc_tab, text="Data Settings", padding=10)
        data_frame.pack(fill="x", padx=10, pady=10)

        self.record_var = ttk.BooleanVar()
        record_checkbox = ttk.Checkbutton(
            data_frame,
            text="Record fights",
            variable=self.record_var,
            bootstyle="round-toggle",
            command=self._notify_config_change,
        )
        record_checkbox.pack(anchor="w")
        self._trace_variable(self.record_var)
        self._register_config_widget(UIField.RECORD_FIGHTS_TOGGLE.value, record_checkbox)

        self.open_recordings_btn = ttk.Button(
            data_frame,
            text="Open Recordings Folder",
            command=self._on_open_recordings_clicked,
        )
        self.open_recordings_btn.pack(fill="x", pady=(6, 0))

        self.open_logs_btn = ttk.Button(
            data_frame,
            text="Open Logs Folder",
            command=self._on_open_logs_clicked,
        )
        self.open_logs_btn.pack(fill="x", pady=(6, 0))

        # AI/ML Model Settings
        ttk.Separator(self.misc_tab, orient="horizontal").pack(fill="x", padx=10, pady=(6, 0))
        model_frame = ttk.Labelframe(self.misc_tab, text="AI/ML Model Settings (Optional)", padding=10)
        model_frame.pack(fill="x", padx=10, pady=10)

        # Model enabled toggle
        self.model_enabled_var = ttk.BooleanVar(value=False)
        model_enabled_checkbox = ttk.Checkbutton(
            model_frame,
            text="Enable ML Model Detection",
            variable=self.model_enabled_var,
            bootstyle="round-toggle",
            command=self._on_model_enabled_changed,
        )
        model_enabled_checkbox.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.model_enabled_var)
        self._register_config_widget(UIField.MODEL_ENABLED_TOGGLE.value, model_enabled_checkbox)

        # Model type selection
        model_type_frame = ttk.Frame(model_frame)
        model_type_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(model_type_frame, text="Model Type:").pack(side=LEFT, padx=(0, 8))
        self.model_type_var = ttk.StringVar(value="roboflow")
        model_type_combo = ttk.Combobox(
            model_type_frame,
            values=["roboflow"],
            width=15,
            state=READONLY,
            textvariable=self.model_type_var,
        )
        model_type_combo.pack(side=LEFT)
        self._trace_variable(self.model_type_var)
        self._register_config_widget(UIField.MODEL_TYPE.value, model_type_combo)
        ToolTip(model_type_combo, "Select the ML model provider")

        # Roboflow API Key
        api_key_frame = ttk.Frame(model_frame)
        api_key_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(api_key_frame, text="Roboflow API Key:").pack(anchor="w")
        self.roboflow_api_key_var = ttk.StringVar(value="")
        api_key_entry = ttk.Entry(
            api_key_frame,
            textvariable=self.roboflow_api_key_var,
            width=40,
            show="*",
        )
        api_key_entry.pack(fill="x", pady=(4, 0))
        self._trace_variable(self.roboflow_api_key_var)
        self._register_config_widget(UIField.ROBOFLOW_API_KEY.value, api_key_entry)
        ToolTip(api_key_entry, "Your Roboflow API key (can also use ROBOFLOW_API_KEY env var)")

        # Roboflow Model ID
        model_id_frame = ttk.Frame(model_frame)
        model_id_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(model_id_frame, text="Roboflow Model ID:").pack(anchor="w")
        self.roboflow_model_id_var = ttk.StringVar(value="")
        model_id_entry = ttk.Entry(
            model_id_frame,
            textvariable=self.roboflow_model_id_var,
            width=40,
        )
        model_id_entry.pack(fill="x", pady=(4, 0))
        self._trace_variable(self.roboflow_model_id_var)
        self._register_config_widget(UIField.ROBOFLOW_MODEL_ID.value, model_id_entry)
        ToolTip(model_id_entry, "Format: project-name/version (e.g., clash-royale-cards/1)")

        # OR label
        or_label = ttk.Label(
            model_frame,
            text="— OR —",
            font=("TkDefaultFont", 8),
            bootstyle="secondary",
        )
        or_label.pack(pady=(4, 4))

        # Roboflow Workflow ID (alternative to Model ID)
        workflow_id_frame = ttk.Frame(model_frame)
        workflow_id_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(workflow_id_frame, text="Roboflow Workflow ID (Advanced):").pack(anchor="w")
        self.roboflow_workflow_id_var = ttk.StringVar(value="")
        workflow_id_entry = ttk.Entry(
            workflow_id_frame,
            textvariable=self.roboflow_workflow_id_var,
            width=40,
        )
        workflow_id_entry.pack(fill="x", pady=(4, 0))
        self._trace_variable(self.roboflow_workflow_id_var)
        self._register_config_widget(UIField.ROBOFLOW_WORKFLOW_ID.value, workflow_id_entry)
        ToolTip(
            workflow_id_entry,
            "Format: workspace/workflow-id. Use workflows for multi-model pipelines. Leave blank to use Model ID above. See QUICKSTART_MODELS.md for recommendations."
        )

        # Confidence threshold
        confidence_frame = ttk.Frame(model_frame)
        confidence_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(confidence_frame, text="Confidence Threshold:").pack(side=LEFT, padx=(0, 8))
        self.model_confidence_var = ttk.StringVar(value="0.7")
        confidence_spin = ttk.Spinbox(
            confidence_frame,
            from_=0.0,
            to=1.0,
            increment=0.05,
            width=8,
            textvariable=self.model_confidence_var,
        )
        confidence_spin.pack(side=LEFT)
        self._trace_variable(self.model_confidence_var)
        self._register_config_widget(UIField.MODEL_CONFIDENCE_THRESHOLD.value, confidence_spin)
        ToolTip(confidence_spin, "Minimum confidence (0.0-1.0) to use model predictions")

        # Test Connection button and status
        test_frame = ttk.Frame(model_frame)
        test_frame.pack(fill="x", pady=(8, 0))
        self.test_model_btn = ttk.Button(
            test_frame,
            text="Test Connection",
            command=self._on_test_model_connection,
            bootstyle="info-outline",
        )
        self.test_model_btn.pack(side=LEFT, padx=(0, 8))
        self._register_config_widget("test_model_button", self.test_model_btn)

        self.model_status_label = ttk.Label(
            test_frame,
            text="",
            font=("TkDefaultFont", 9),
        )
        self.model_status_label.pack(side=LEFT)

        # Info label
        info_label = ttk.Label(
            model_frame,
            text="Info: Install inference-sdk with: pip install inference-sdk\n"
            "See pyclashbot/detection/README_MODELS.md for setup guide",
            bootstyle="info",
            font=("TkDefaultFont", 8),
        )
        info_label.pack(anchor="w", pady=(8, 0))

        # Model connection status (displayed when model is active)
        self.model_connection_status_label = ttk.Label(
            model_frame,
            text="",
            font=("TkDefaultFont", 9, "bold"),
        )
        self.model_connection_status_label.pack(anchor="w", pady=(8, 0))

        # Initialize model settings as disabled
        self._on_model_enabled_changed()

        ttk.Separator(self.misc_tab, orient="horizontal").pack(fill="x", padx=10, pady=(6, 0))
        display_frame = ttk.Labelframe(self.misc_tab, text="Display Settings", padding=10)
        display_frame.pack(fill="x", padx=10, pady=10)

    def _create_help_tab(self) -> None:
        """Create the Help tab with information about model types and usage."""
        container = ttk.Frame(self.help_tab, padding=10)
        container.pack(fill=BOTH, expand=YES)

        # Title
        title_label = ttk.Label(
            container,
            text="AI/ML Model Help",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack(anchor="w", pady=(0, 10))

        # Introduction
        intro_frame = ttk.Labelframe(container, text="Overview", padding=10)
        intro_frame.pack(fill="x", pady=(0, 10))
        intro_text = (
            "This application supports AI/ML models to enhance card detection accuracy. "
            "Currently, Roboflow integration is supported with more providers coming soon."
        )
        intro_label = ttk.Label(intro_frame, text=intro_text, wraplength=450, justify=LEFT)
        intro_label.pack(anchor="w")

        # Model Types
        types_frame = ttk.Labelframe(container, text="Recommended Model Types", padding=10)
        types_frame.pack(fill="x", pady=(0, 10))

        # Object Detection
        od_title = ttk.Label(types_frame, text="✓ Object Detection (Recommended)", font=("TkDefaultFont", 10, "bold"))
        od_title.pack(anchor="w", pady=(0, 2))
        od_text = (
            "Best for detecting cards in hand and on the battlefield. "
            "Returns bounding boxes and class labels for each detected card."
        )
        od_label = ttk.Label(types_frame, text=od_text, wraplength=450, justify=LEFT)
        od_label.pack(anchor="w", padx=(10, 0), pady=(0, 8))

        # Instance Segmentation
        is_title = ttk.Label(types_frame, text="✓ Instance Segmentation (Advanced)", font=("TkDefaultFont", 10, "bold"))
        is_title.pack(anchor="w", pady=(0, 2))
        is_text = (
            "Similar to object detection but provides pixel-level masks. "
            "Useful for precise card boundaries but may be slower."
        )
        is_label = ttk.Label(types_frame, text=is_text, wraplength=450, justify=LEFT)
        is_label.pack(anchor="w", padx=(10, 0), pady=(0, 8))

        # Classification
        class_title = ttk.Label(types_frame, text="✗ Classification (Not Recommended)", font=("TkDefaultFont", 10, "bold"))
        class_title.pack(anchor="w", pady=(0, 2))
        class_text = (
            "Only provides a class label for the entire image without location information. "
            "Not suitable for this application as we need to detect multiple cards with positions."
        )
        class_label = ttk.Label(types_frame, text=class_text, wraplength=450, justify=LEFT)
        class_label.pack(anchor="w", padx=(10, 0), pady=(0, 8))

        # Setup Guide
        setup_frame = ttk.Labelframe(container, text="Quick Setup Guide", padding=10)
        setup_frame.pack(fill="x", pady=(0, 10))

        setup_steps = [
            "1. Install inference-sdk: pip install inference-sdk",
            "2. Sign up at roboflow.com and get your API key",
            "3. Train or find an object detection model for Clash Royale cards",
            "4. Enter your API key and model ID in the Misc tab",
            "5. Click 'Test Connection' to verify your setup",
            "6. Enable 'ML Model Detection' toggle to start using the model",
        ]

        for step in setup_steps:
            step_label = ttk.Label(setup_frame, text=step, wraplength=450, justify=LEFT)
            step_label.pack(anchor="w", pady=1)

        # Documentation Links
        docs_frame = ttk.Labelframe(container, text="Documentation", padding=10)
        docs_frame.pack(fill="x", pady=(0, 10))

        docs_text = (
            "• Full documentation: pyclashbot/detection/README_MODELS.md\n"
            "• Quick start guide: QUICKSTART_MODELS.md\n"
            "• Roboflow Universe: universe.roboflow.com\n"
            "• Training guide: docs.roboflow.com/quick-start"
        )
        docs_label = ttk.Label(docs_frame, text=docs_text, justify=LEFT)
        docs_label.pack(anchor="w")

    def _register_config_widget(self, key: str, widget: tk.Widget) -> None:
        self._config_widgets[key] = widget

    def _notify_config_change(self, *_: object) -> None:
        if self._suspend_traces > 0 or self._config_callback is None:
            return
        self.after_idle(lambda: self._config_callback(self.get_all_values()))

    def _trace_variable(self, var: tk.Variable) -> None:
        trace_id = var.trace_add("write", self._notify_config_change)
        self._traces.append((var, trace_id))

    def _notify_config_change_event(self, _event: object) -> None:
        self._notify_config_change()

    def _apply_theme(self, theme_name: str, skip_variable_update: bool = False) -> None:
        available = tuple(self._style.theme_names())
        selected = theme_name if theme_name in available else self.DEFAULT_THEME
        if selected not in available and available:
            selected = available[0]
        if not skip_variable_update or self.theme_var.get() != selected:
            self._suspend_traces += 1
            try:
                self.theme_var.set(selected)
            finally:
                self._suspend_traces -= 1
        self._style.theme_use(selected)
        self._refresh_theme_colours()

    def _label_foreground(self) -> str:
        try:
            colour = self._style.lookup("TLabel", "foreground")
            return colour or "#202020"
        except tk.TclError:
            return "#202020"

    def _refresh_theme_colours(self) -> None:
        foreground = self._label_foreground()
        for label in self._theme_labels:
            try:
                label.configure(foreground=foreground)
            except tk.TclError:
                continue
        gauge_fg = getattr(self._style.colors, "success", "#2ecc71")
        gauge_bg = getattr(self._style.colors, "danger", "#e74c3c")
        self.win_gauge.set_colours(gauge_fg, gauge_bg, foreground)

    def _on_theme_change(self, _event: object | None = None) -> None:
        self._apply_theme(self.theme_var.get(), skip_variable_update=True)
        self._notify_config_change()

    def _on_emulator_changed(self, _event: object = None) -> None:
        self._show_current_emulator_settings()
        self._notify_config_change()

    def _show_current_emulator_settings(self) -> None:
        """Hides all emulator settings frames and shows the one selected in the combobox."""
        selected_emulator = self.emulator_var.get()

        # Hide all frames first
        for frame in self.emulator_settings_frames.values():
            frame.pack_forget()

        # Show the selected frame
        frame_to_show = self.emulator_settings_frames.get(selected_emulator)
        if frame_to_show:
            frame_to_show.pack(fill=BOTH, expand=YES)

    def _hide_action_button(self) -> None:
        self.action_btn.grid_remove()
        self.stop_btn.grid()

    def _on_action_pressed(self) -> None:
        if self._action_callback:
            self._action_callback()
        self._hide_action_button()

    def _on_open_recordings_clicked(self) -> None:
        if self._open_recordings_callback:
            self._open_recordings_callback()

    def _on_open_logs_clicked(self) -> None:
        if self._open_logs_callback:
            self._open_logs_callback()

    def _on_model_enabled_changed(self) -> None:
        """Handle model enabled toggle change."""
        enabled = self.model_enabled_var.get()
        state = tk.NORMAL if enabled else tk.DISABLED

        # Enable/disable model configuration widgets
        for key in [
            UIField.MODEL_TYPE.value,
            UIField.ROBOFLOW_API_KEY.value,
            UIField.ROBOFLOW_MODEL_ID.value,
            UIField.MODEL_CONFIDENCE_THRESHOLD.value,
            "test_model_button",
        ]:
            widget = self._config_widgets.get(key)
            if widget:
                try:
                    if isinstance(widget, ttk.Combobox):
                        widget.configure(state=READONLY if enabled else tk.DISABLED)
                    elif isinstance(widget, ttk.Spinbox):
                        widget.configure(state=READONLY if enabled else tk.DISABLED)
                    else:
                        widget.configure(state=state)
                except tk.TclError:
                    continue

        # Clear status label when disabled
        if not enabled and hasattr(self, "model_status_label"):
            self.model_status_label.configure(text="")

        self._notify_config_change()

    def _on_clan_battle_toggle_changed(self) -> None:
        """Handle clan battle enabled toggle change."""
        enabled = self.clan_battle_enabled_var.get()
        state = tk.NORMAL if enabled else tk.DISABLED

        # Enable/disable clan battle configuration widgets
        for key in [
            UIField.CLAN_BATTLE_MODE.value,
            UIField.CLAN_BATTLE_MANUAL_START.value,
            "upload_clan_icon_btn",
        ]:
            widget = self._config_widgets.get(key)
            if widget:
                try:
                    if isinstance(widget, ttk.Combobox):
                        widget.configure(state=READONLY if enabled else tk.DISABLED)
                    elif isinstance(widget, ttk.Checkbutton):
                        widget.configure(state=state)
                    else:
                        widget.configure(state=state)
                except tk.TclError:
                    continue

        # Clear status label when disabled
        if not enabled and hasattr(self, "clan_icon_status_label"):
            self.clan_icon_status_label.configure(text="")

        self._notify_config_change()

    def _on_upload_clan_icon(self) -> None:
        """Handle uploading a custom icon for the selected clan battle mode."""
        import shutil  # noqa: PLC0415
        from pathlib import Path  # noqa: PLC0415
        from tkinter import filedialog  # noqa: PLC0415

        # Get the currently selected clan battle mode
        selected_mode = self.clan_battle_mode_var.get()

        # Map mode to folder name
        mode_to_folder = {
            "Sudden Death Battle": "clan_sudden_death",
            "Battle": "clan_battle",
            "Colosseum Duel": "clan_colosseum_duel",
        }

        folder_name = mode_to_folder.get(selected_mode)
        if not folder_name:
            self.clan_icon_status_label.configure(text="❌ Unknown mode", foreground="red")
            return

        # Open file dialog
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("All files", "*.*"),
        ]

        filepath = filedialog.askopenfilename(
            title=f"Select icon for {selected_mode}",
            filetypes=filetypes,
        )

        if not filepath:
            return  # User cancelled

        try:
            # Get the reference_images folder path
            detection_path = Path(__file__).parent.parent / "detection" / "reference_images" / folder_name

            # Ensure directory exists
            detection_path.mkdir(parents=True, exist_ok=True)

            # Count existing files to determine new filename
            existing_files = list(detection_path.glob("*.png")) + list(detection_path.glob("*.jpg"))
            new_index = len(existing_files) + 1
            ext = Path(filepath).suffix
            new_filename = f"{new_index}{ext}"
            dest_path = detection_path / new_filename

            # Copy the file
            shutil.copy2(filepath, dest_path)

            self.clan_icon_status_label.configure(
                text=f"✓ Saved: {new_filename} for {selected_mode}",
                foreground="green",
            )

        except Exception as e:
            self.clan_icon_status_label.configure(
                text=f"❌ Error: {str(e)[:40]}",
                foreground="red",
            )
        """Test connection to Roboflow model."""
        api_key = self.roboflow_api_key_var.get()
        model_id = self.roboflow_model_id_var.get()

        if not api_key or not model_id:
            self.model_status_label.configure(text="❌ Please enter API key and Model ID", foreground="red")
            self.set_model_connection_status(False)
            return

        self.model_status_label.configure(text="⏳ Testing connection...", foreground="gray")
        self.test_model_btn.configure(state=tk.DISABLED)
        self.update_idletasks()

        try:
            from pyclashbot.detection.roboflow_model import RoboflowModel  # noqa: PLC0415

            # Create a test model instance
            test_model = RoboflowModel(api_key=api_key, model_id=model_id)

            if not test_model.is_available():
                self.model_status_label.configure(
                    text="❌ Connection failed - check API key/model ID", foreground="red"
                )
                self.set_model_connection_status(False)
                return

            # Try a simple test inference with a dummy image
            import numpy as np  # noqa: PLC0415

            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_model.predict(test_image)

            # Connection successful (even if no predictions, it means API works)
            self.model_status_label.configure(text="✓ Connection successful!", foreground="green")
            # Update persistent status
            model_enabled = self.model_enabled_var.get()
            self.set_model_connection_status(True, "roboflow", model_enabled)

        except ImportError:
            self.model_status_label.configure(
                text="❌ inference-sdk not installed. Run: pip install inference-sdk", foreground="red"
            )
            self.set_model_connection_status(False)
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 50:
                error_msg = error_msg[:50] + "..."
            self.model_status_label.configure(text=f"❌ Error: {error_msg}", foreground="red")
            self.set_model_connection_status(False)
        finally:
            self.test_model_btn.configure(state=tk.NORMAL)

    @staticmethod
    def _safe_int(value: object, fallback: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _safe_float(value: object, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _parse_winrate_value(raw: object) -> float | None:
        if isinstance(raw, str):
            stripped = raw.strip()
            if stripped.endswith("%"):
                stripped = stripped[:-1]
            try:
                return float(stripped)
            except ValueError:
                return None
        if isinstance(raw, int | float):
            return float(raw)
        return None

    @staticmethod
    def _calculate_winrate_percentage(wins: int, losses: int) -> float:
        total = wins + losses
        if total <= 0:
            return 0.0
        return wins / total * 100
