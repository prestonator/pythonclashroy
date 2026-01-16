"""Modern ttkbootstrap UI for py-clash-bot (BlueStacks only)."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox
from typing import TYPE_CHECKING

import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, LEFT, READONLY, YES, X
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.scrolled import ScrolledFrame

from pyclashbot.interface.config import (
    BLUESTACKS_SETTINGS,
    JOBS,
    PERFORMANCE_SETTINGS,
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
    messagebox.showerror("Error", "Please select at least one job to run!")


class PyClashBotUI(ttk.Window):
    """Modern UI for py-clash-bot with BlueStacks support."""

    DEFAULT_THEME = "superhero"  # Modern dark theme

    def __init__(self) -> None:
        super().__init__(themename=self.DEFAULT_THEME)
        self.title("🏰 py-clash-bot")
        self.geometry("520x680")
        self.minsize(480, 580)
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

        # Configure custom styles
        self._configure_styles()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_ui()
        self._refresh_theme_colours()

    def _configure_styles(self) -> None:
        """Configure custom styles for a modern look."""
        self._style.configure("Card.TFrame", padding=12)
        self._style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))
        self._style.configure("Stat.TLabel", font=("Segoe UI", 10))
        self._style.configure("StatValue.TLabel", font=("Segoe UI", 12, "bold"))

    def register_config_callback(self, callback: Callable[[dict[str, object]], None]) -> None:
        self._config_callback = callback

    def register_open_recordings_callback(self, callback: Callable[[], None]) -> None:
        self._open_recordings_callback = callback

    def register_open_logs_callback(self, callback: Callable[[], None]) -> None:
        self._open_logs_callback = callback

    def get_all_values(self) -> dict[str, object]:
        """Get all current UI values."""
        values: dict[str, object] = {}

        # Job toggles
        for field, var in self.jobs_vars.items():
            values[field.value] = bool(var.get())

        values[UIField.DECK_NUMBER_SELECTION.value] = self._safe_int(self.deck_var.get(), fallback=2)
        values[UIField.CYCLE_DECKS_USER_TOGGLE.value] = bool(self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE].get())
        values[UIField.MAX_DECK_SELECTION.value] = self._safe_int(self.max_deck_var.get(), fallback=2)
        values[UIField.RECORD_FIGHTS_TOGGLE.value] = bool(self.record_var.get())

        # BlueStacks render mode
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

        # Performance settings
        values[UIField.NAV_SPEED_MODE.value] = self.nav_speed_var.get()
        values[UIField.WIN_CHECK_BATCH_SIZE.value] = self._safe_int(self.win_batch_var.get(), fallback=3)

        return values

    def set_all_values(self, values: dict[str, object]) -> None:
        """Set all UI values from a dictionary."""
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

            # BlueStacks render mode
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

            # Performance settings
            if UIField.NAV_SPEED_MODE.value in values:
                self.nav_speed_var.set(str(values[UIField.NAV_SPEED_MODE.value]))
            if UIField.WIN_CHECK_BATCH_SIZE.value in values:
                self.win_batch_var.set(str(values[UIField.WIN_CHECK_BATCH_SIZE.value]))

        finally:
            self._suspend_traces -= 1

        if theme_value is not None:
            self._apply_theme(theme_value)

    def set_running_state(self, running: bool) -> None:
        """Enable/disable controls based on running state."""
        start_state = tk.DISABLED if running else tk.NORMAL
        stop_state = tk.NORMAL if running else tk.DISABLED
        self.start_btn.configure(state=start_state)
        self.stop_btn.configure(state=stop_state)

        for key, widget in self._config_widgets.items():
            if widget in {self.stop_btn, self.start_btn}:
                continue
            try:
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state=tk.DISABLED if running else READONLY)
                elif isinstance(widget, ttk.Spinbox):
                    widget.configure(state=tk.DISABLED if running else READONLY)
                elif isinstance(widget, ttk.Radiobutton) and key in [
                    UIField.BS_RENDERER_DX.value,
                    UIField.BS_RENDERER_GL.value,
                    UIField.BS_RENDERER_VK.value,
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
        self.stop_btn.pack_forget()
        self.action_btn.pack(side=LEFT)

    def hide_action_button(self) -> None:
        self._hide_action_button()

    def append_log(self, message: str) -> None:
        """Update status log text."""
        self.status_label.configure(text=message)

    def set_status(self, text: str) -> None:
        self._status_text = text

    def set_model_connection_status(self, connected: bool, model_type: str = "", in_use: bool = False) -> None:
        """Update the model connection status display."""
        if not hasattr(self, "model_connection_status_label"):
            return

        if connected and in_use:
            status_text = f"🟢 {model_type.capitalize()} model active"
            self.model_connection_status_label.configure(text=status_text, bootstyle="success")
        elif connected:
            status_text = f"🟡 {model_type.capitalize()} connected"
            self.model_connection_status_label.configure(text=status_text, bootstyle="warning")
        else:
            self.model_connection_status_label.configure(text="")

    def update_stats(self, stats: dict[str, object] | None) -> None:
        """Update statistics display."""
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

        current_streak = stats.get(DerivedStatField.CURRENT_WIN_STREAK.value, 0)
        best_streak = stats.get(DerivedStatField.BEST_WIN_STREAK.value, 0)
        if hasattr(self, "current_streak_var"):
            self.current_streak_var.set(str(current_streak))
        if hasattr(self, "best_streak_var"):
            self.best_streak_var.set(str(best_streak))

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame, bootstyle="primary")
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Create tabs
        self.jobs_tab = ttk.Frame(self.notebook, padding=8)
        self.bluestacks_tab = ttk.Frame(self.notebook, padding=8)
        self.strategy_tab = ttk.Frame(self.notebook, padding=8)
        self.stats_tab = ttk.Frame(self.notebook, padding=8)
        self.settings_tab = ttk.Frame(self.notebook, padding=8)

        self.notebook.add(self.jobs_tab, text="  ⚔️ Jobs  ")
        self.notebook.add(self.bluestacks_tab, text="  📱 BlueStacks  ")
        self.notebook.add(self.strategy_tab, text="  🎯 Strategy  ")
        self.notebook.add(self.stats_tab, text="  📊 Stats  ")
        self.notebook.add(self.settings_tab, text="  ⚙️ Settings  ")

        # Build each tab
        self._create_jobs_tab()
        self._create_bluestacks_tab()
        self._create_strategy_tab()
        self._create_stats_tab()
        self._create_settings_tab()

        # Bottom control bar
        self._build_control_bar(main_frame)

    def _build_control_bar(self, parent: ttk.Frame) -> None:
        """Build the bottom control bar with status and buttons."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        control_frame.columnconfigure(0, weight=1)

        # Status label
        self.status_label = ttk.Label(
            control_frame,
            text="Ready to start",
            bootstyle="secondary",
            font=("Segoe UI", 9),
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=(4, 8))
        self._status_text = "Ready"

        # Button frame
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=0, column=1, sticky="e")

        self.start_btn = ttk.Button(btn_frame, text="▶ Start", bootstyle="success", width=10)
        self.start_btn.pack(side=LEFT, padx=(0, 4))
        self._register_config_widget("Start", self.start_btn)

        self.stop_btn = ttk.Button(btn_frame, text="⬛ Stop", bootstyle="danger", width=10, state=tk.DISABLED)
        self.stop_btn.pack(side=LEFT)
        self._register_config_widget("Stop", self.stop_btn)

        # Hidden action button
        self.action_btn = ttk.Button(btn_frame, text="Retry", bootstyle="warning")
        self._action_callback: Callable[[], None] | None = None
        self.action_btn.configure(command=self._on_action_pressed)

    def _create_jobs_tab(self) -> None:
        """Create the Jobs tab with battle mode toggles."""
        # Battle Modes Section
        battle_frame = ttk.Labelframe(self.jobs_tab, text="🎮 Battle Modes", padding=12, bootstyle="primary")
        battle_frame.pack(fill=X, pady=(0, 8))

        job_defaults = {job.key: job.default for job in JOBS}
        jobs_by_key = {job.key: job for job in JOBS}
        self.jobs_vars: dict[UIField, ttk.BooleanVar] = {}

        def add_toggle(parent: ttk.Frame, field: UIField, text: str, style: str = "primary") -> None:
            var = ttk.BooleanVar(value=job_defaults.get(field, False))
            cb = ttk.Checkbutton(
                parent,
                text=text,
                variable=var,
                bootstyle=f"{style}-round-toggle",
                command=self._notify_config_change,
            )
            cb.pack(anchor="w", pady=3)
            self.jobs_vars[field] = var
            self._trace_variable(var)
            self._register_config_widget(field.value, cb)

        add_toggle(battle_frame, UIField.TROPHY_ROAD_USER_TOGGLE, "🏆 Trophy Road 1v1", "warning")
        add_toggle(battle_frame, UIField.CLASSIC_1V1_USER_TOGGLE, "⚔️ Classic 1v1", "info")
        add_toggle(battle_frame, UIField.CLASSIC_2V2_USER_TOGGLE, "👥 Classic 2v2", "info")

        # Deck Management Section
        deck_frame = ttk.Labelframe(self.jobs_tab, text="🃏 Deck Management", padding=12, bootstyle="info")
        deck_frame.pack(fill=X, pady=(0, 8))

        # Random Decks
        random_job = jobs_by_key[UIField.RANDOM_DECKS_USER_TOGGLE]
        deck_config: ComboConfig = random_job.extras[UIField.DECK_NUMBER_SELECTION]

        random_row = ttk.Frame(deck_frame)
        random_row.pack(fill=X, pady=3)
        random_row.columnconfigure(1, weight=1)

        self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE] = ttk.BooleanVar(value=random_job.default)
        random_cb = ttk.Checkbutton(
            random_row,
            text="🎲 Randomize Deck",
            variable=self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE],
            bootstyle="secondary-round-toggle",
            command=self._notify_config_change,
        )
        random_cb.grid(row=0, column=0, sticky="w")
        self._trace_variable(self.jobs_vars[UIField.RANDOM_DECKS_USER_TOGGLE])
        self._register_config_widget(UIField.RANDOM_DECKS_USER_TOGGLE.value, random_cb)

        deck_select = ttk.Frame(random_row)
        deck_select.grid(row=0, column=2, sticky="e")
        ttk.Label(deck_select, text="Deck #:").pack(side=LEFT, padx=(0, 4))
        self.deck_var = ttk.StringVar(value=str(deck_config.default))
        self.deck_spin = ttk.Spinbox(
            deck_select,
            from_=min(deck_config.values),
            to=max(deck_config.values),
            width=4,
            textvariable=self.deck_var,
            command=self._notify_config_change,
            state=READONLY,
        )
        self.deck_spin.pack(side=LEFT)
        self._trace_variable(self.deck_var)
        self._register_config_widget(UIField.DECK_NUMBER_SELECTION.value, self.deck_spin)

        # Cycle Decks
        cycle_job = jobs_by_key[UIField.CYCLE_DECKS_USER_TOGGLE]
        max_config: ComboConfig = cycle_job.extras[UIField.MAX_DECK_SELECTION]

        cycle_row = ttk.Frame(deck_frame)
        cycle_row.pack(fill=X, pady=3)
        cycle_row.columnconfigure(1, weight=1)

        self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE] = ttk.BooleanVar(value=cycle_job.default)
        cycle_cb = ttk.Checkbutton(
            cycle_row,
            text="♻️ Cycle Decks",
            variable=self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE],
            bootstyle="secondary-round-toggle",
            command=self._notify_config_change,
        )
        cycle_cb.grid(row=0, column=0, sticky="w")
        self._trace_variable(self.jobs_vars[UIField.CYCLE_DECKS_USER_TOGGLE])
        self._register_config_widget(UIField.CYCLE_DECKS_USER_TOGGLE.value, cycle_cb)

        cycle_select = ttk.Frame(cycle_row)
        cycle_select.grid(row=0, column=2, sticky="e")
        ttk.Label(cycle_select, text="# Decks:").pack(side=LEFT, padx=(0, 4))
        self.max_deck_var = ttk.StringVar(value=str(max_config.default))
        self.max_deck_spin = ttk.Spinbox(
            cycle_select,
            from_=min(max_config.values),
            to=max(max_config.values),
            width=4,
            textvariable=self.max_deck_var,
            command=self._notify_config_change,
            state=READONLY,
        )
        self.max_deck_spin.pack(side=LEFT)
        self._trace_variable(self.max_deck_var)
        self._register_config_widget(UIField.MAX_DECK_SELECTION.value, self.max_deck_spin)

        # Other Options Section
        other_frame = ttk.Labelframe(self.jobs_tab, text="📦 Other Options", padding=12, bootstyle="secondary")
        other_frame.pack(fill=X, pady=(0, 8))

        add_toggle(other_frame, UIField.RANDOM_PLAYS_USER_TOGGLE, "🎲 Random Card Plays", "secondary")
        add_toggle(other_frame, UIField.DISABLE_WIN_TRACK_TOGGLE, "⏭️ Skip Win/Loss Check", "secondary")
        add_toggle(other_frame, UIField.CARD_MASTERY_USER_TOGGLE, "🎯 Collect Card Masteries", "secondary")
        add_toggle(other_frame, UIField.CARD_UPGRADE_USER_TOGGLE, "⬆️ Auto Upgrade Cards", "secondary")

    def _create_bluestacks_tab(self) -> None:
        """Create the BlueStacks settings tab."""
        # Emulator info
        info_frame = ttk.Frame(self.bluestacks_tab)
        info_frame.pack(fill=X, pady=(0, 12))

        ttk.Label(
            info_frame, text="📱 BlueStacks 5 Emulator", font=("Segoe UI", 12, "bold"), bootstyle="primary"
        ).pack(anchor="w")

        ttk.Label(
            info_frame,
            text="The bot will automatically create and manage a 'pyclashbot-96' instance.",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        ).pack(anchor="w", pady=(4, 0))

        # Render Mode Section
        render_frame = ttk.Labelframe(self.bluestacks_tab, text="🎨 Render Mode", padding=12, bootstyle="primary")
        render_frame.pack(fill=X, pady=(0, 12))

        self.bs_render_var = ttk.StringVar(value="DirectX")

        render_options = [
            ("DirectX", UIField.BS_RENDERER_DX, "Recommended for most systems"),
            ("OpenGL", UIField.BS_RENDERER_GL, "Better compatibility"),
            ("Vulkan", UIField.BS_RENDERER_VK, "Best performance on newer GPUs"),
        ]

        for text, field, tooltip in render_options:
            rb = ttk.Radiobutton(
                render_frame,
                text=text,
                variable=self.bs_render_var,
                value=text,
                command=self._notify_config_change,
                bootstyle="primary-toolbutton",
            )
            rb.pack(anchor="w", pady=2)
            ToolTip(rb, tooltip)
            self._register_config_widget(field.value, rb)

        # Tips Section
        tips_frame = ttk.Labelframe(self.bluestacks_tab, text="💡 Tips", padding=12, bootstyle="info")
        tips_frame.pack(fill=X)

        tips = [
            "• Make sure BlueStacks 5 is installed (not BlueStacks X/10)",
            "• Complete the Clash Royale tutorial before starting",
            "• Set Clash Royale language to English",
            "• Close BlueStacks before starting the bot",
            "• Switch render mode if you experience black screens",
        ]

        for tip in tips:
            ttk.Label(tips_frame, text=tip, font=("Segoe UI", 9)).pack(anchor="w", pady=1)

    def _create_strategy_tab(self) -> None:
        """Create the Strategy tab with battle strategy configuration."""
        scroll = ScrolledFrame(self.strategy_tab, autohide=True)
        scroll.pack(fill=BOTH, expand=YES)
        container = scroll

        # Elixir Management
        elixir_frame = ttk.Labelframe(container, text="⚡ Elixir Management", padding=12, bootstyle="warning")
        elixir_frame.pack(fill=X, pady=(0, 8), padx=2)

        elixir_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_ELIXIR_MODE)
        self.strategy_elixir_var = ttk.StringVar(value=str(elixir_config.default))

        elixir_combo = ttk.Combobox(
            elixir_frame,
            textvariable=self.strategy_elixir_var,
            values=elixir_config.values,
            state=READONLY,
            bootstyle="warning",
        )
        elixir_combo.pack(fill=X, pady=(0, 8))
        self._trace_variable(self.strategy_elixir_var)
        self._register_config_widget(UIField.STRATEGY_ELIXIR_MODE.value, elixir_combo)

        ttk.Label(
            elixir_frame,
            text="Conservative: Save elixir | Aggressive: Constant pressure | Adaptive: Smart adjustment",
            font=("Segoe UI", 8),
            bootstyle="secondary",
            wraplength=400,
        ).pack(anchor="w")

        # Push Strategy
        push_frame = ttk.Labelframe(container, text="🎯 Push Strategy", padding=12, bootstyle="success")
        push_frame.pack(fill=X, pady=(0, 8), padx=2)

        push_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_PUSH_MODE)
        self.strategy_push_var = ttk.StringVar(value=str(push_config.default))

        push_combo = ttk.Combobox(
            push_frame,
            textvariable=self.strategy_push_var,
            values=push_config.values,
            state=READONLY,
            bootstyle="success",
        )
        push_combo.pack(fill=X, pady=(0, 8))
        self._trace_variable(self.strategy_push_var)
        self._register_config_widget(UIField.STRATEGY_PUSH_MODE.value, push_combo)

        ttk.Label(
            push_frame,
            text="Single Lane: Focus one lane | Dual Lane: Split push | Counter Push: After defense",
            font=("Segoe UI", 8),
            bootstyle="secondary",
            wraplength=400,
        ).pack(anchor="w")

        # Aggression Level
        aggression_frame = ttk.Labelframe(container, text="🔥 Aggression Level", padding=12, bootstyle="danger")
        aggression_frame.pack(fill=X, pady=(0, 8), padx=2)

        aggression_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_AGGRESSION_LEVEL)
        self.strategy_aggression_var = ttk.StringVar(value=str(aggression_config.default))

        aggression_combo = ttk.Combobox(
            aggression_frame,
            textvariable=self.strategy_aggression_var,
            values=aggression_config.values,
            state=READONLY,
            bootstyle="danger",
        )
        aggression_combo.pack(fill=X, pady=(0, 8))
        self._trace_variable(self.strategy_aggression_var)
        self._register_config_widget(UIField.STRATEGY_AGGRESSION_LEVEL.value, aggression_combo)

        # Advanced Settings
        advanced_frame = ttk.Labelframe(container, text="🏰 Advanced", padding=12, bootstyle="secondary")
        advanced_frame.pack(fill=X, pady=(0, 8), padx=2)

        self.strategy_tower_health_var = ttk.BooleanVar(value=True)
        tower_cb = ttk.Checkbutton(
            advanced_frame,
            text="Tower Health Awareness",
            variable=self.strategy_tower_health_var,
            bootstyle="secondary-round-toggle",
            command=self._notify_config_change,
        )
        tower_cb.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.strategy_tower_health_var)
        self._register_config_widget(UIField.STRATEGY_TOWER_HEALTH_AWARE.value, tower_cb)

        ttk.Label(advanced_frame, text="Card Placement:").pack(anchor="w")
        placement_config = next(s for s in STRATEGY_SETTINGS if s.key == UIField.STRATEGY_PLACEMENT_MODE)
        self.strategy_placement_var = ttk.StringVar(value=str(placement_config.default))

        placement_combo = ttk.Combobox(
            advanced_frame,
            textvariable=self.strategy_placement_var,
            values=placement_config.values,
            state=READONLY,
        )
        placement_combo.pack(fill=X, pady=(4, 0))
        self._trace_variable(self.strategy_placement_var)
        self._register_config_widget(UIField.STRATEGY_PLACEMENT_MODE.value, placement_combo)

    def _create_stats_tab(self) -> None:
        """Create the Stats tab with statistics display."""
        container = ttk.Frame(self.stats_tab)
        container.pack(fill=BOTH, expand=YES)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        # Left column
        left = ttk.Frame(container)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        # Win Rate Gauge
        gauge_frame = ttk.Labelframe(left, text="📈 Win Rate", padding=12, bootstyle="success")
        gauge_frame.pack(fill=X, pady=(0, 8))
        self.win_gauge = DualRingGauge(gauge_frame, diameter=100, thickness=10, text_color="#00aaff")
        self.win_gauge.pack(anchor="center", pady=8)

        # Battle Stats
        battle_frame = ttk.Labelframe(left, text="⚔️ Battle Stats", padding=12, bootstyle="primary")
        battle_frame.pack(fill=BOTH, expand=YES)

        self.stat_labels: dict[StatField, ttk.StringVar] = {}
        for row, field in enumerate(BATTLE_STAT_FIELDS):
            title = BATTLE_STAT_LABELS[field]
            ttk.Label(battle_frame, text=title).grid(row=row, column=0, sticky="w", pady=2)
            var = ttk.StringVar(value="0")
            ttk.Label(battle_frame, textvariable=var, bootstyle="info").grid(row=row, column=1, sticky="e", pady=2)
            self.stat_labels[field] = var

        # Win streaks
        ttk.Separator(battle_frame).grid(row=len(BATTLE_STAT_FIELDS), column=0, columnspan=2, sticky="ew", pady=8)
        streak_row = len(BATTLE_STAT_FIELDS) + 1

        ttk.Label(battle_frame, text="🔥 Current Streak:").grid(row=streak_row, column=0, sticky="w")
        self.current_streak_var = ttk.StringVar(value="0")
        ttk.Label(battle_frame, textvariable=self.current_streak_var, bootstyle="warning").grid(
            row=streak_row, column=1, sticky="e"
        )

        ttk.Label(battle_frame, text="🏆 Best Streak:").grid(row=streak_row + 1, column=0, sticky="w")
        self.best_streak_var = ttk.StringVar(value="0")
        ttk.Label(battle_frame, textvariable=self.best_streak_var, bootstyle="success").grid(
            row=streak_row + 1, column=1, sticky="e"
        )

        # Right column
        right = ttk.Frame(container)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        # Collection Stats
        collection_frame = ttk.Labelframe(right, text="🎁 Collection", padding=12, bootstyle="info")
        collection_frame.pack(fill=X, pady=(0, 8))

        for row, field in enumerate(COLLECTION_STAT_FIELDS):
            title = COLLECTION_STAT_LABELS[field]
            ttk.Label(collection_frame, text=title).grid(row=row, column=0, sticky="w", pady=2)
            var = ttk.StringVar(value="0")
            ttk.Label(collection_frame, textvariable=var, bootstyle="info").grid(row=row, column=1, sticky="e", pady=2)
            self.stat_labels[field] = var

        # Bot Stats
        bot_frame = ttk.Labelframe(right, text="🤖 Bot Status", padding=12, bootstyle="secondary")
        bot_frame.pack(fill=BOTH, expand=YES)

        self.bot_labels = {
            BotStatField.RESTARTS_AFTER_FAILURE: ttk.StringVar(value="0"),
            BotStatField.TIME_SINCE_START: ttk.StringVar(value="00:00:00"),
        }

        for row, field in enumerate(BOT_STAT_FIELDS):
            title = BOT_STAT_LABELS[field]
            ttk.Label(bot_frame, text=title).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(bot_frame, textvariable=self.bot_labels[field], bootstyle="info").grid(
                row=row, column=1, sticky="e", pady=2
            )

    def _create_settings_tab(self) -> None:
        """Create the Settings tab with appearance and data options."""
        scroll = ScrolledFrame(self.settings_tab, autohide=True)
        scroll.pack(fill=BOTH, expand=YES)
        container = scroll

        # Appearance
        appearance_frame = ttk.Labelframe(container, text="🎨 Appearance", padding=12, bootstyle="primary")
        appearance_frame.pack(fill=X, pady=(0, 8), padx=2)

        ttk.Label(appearance_frame, text="Theme:").pack(anchor="w")
        self.theme_combo = ttk.Combobox(
            appearance_frame,
            values=self._style.theme_names(),
            state=READONLY,
            textvariable=self.theme_var,
        )
        self.theme_combo.pack(fill=X, pady=(4, 0))
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)
        self._trace_variable(self.theme_var)
        self._register_config_widget(UIField.THEME_NAME.value, self.theme_combo)

        # Data Settings
        data_frame = ttk.Labelframe(container, text="💾 Data", padding=12, bootstyle="info")
        data_frame.pack(fill=X, pady=(0, 8), padx=2)

        self.record_var = ttk.BooleanVar()
        record_cb = ttk.Checkbutton(
            data_frame,
            text="📹 Record Fights",
            variable=self.record_var,
            bootstyle="info-round-toggle",
            command=self._notify_config_change,
        )
        record_cb.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.record_var)
        self._register_config_widget(UIField.RECORD_FIGHTS_TOGGLE.value, record_cb)

        btn_frame = ttk.Frame(data_frame)
        btn_frame.pack(fill=X)

        self.open_recordings_btn = ttk.Button(
            btn_frame,
            text="📂 Recordings",
            command=self._on_open_recordings_clicked,
            bootstyle="outline",
        )
        self.open_recordings_btn.pack(side=LEFT, expand=YES, fill=X, padx=(0, 4))

        self.open_logs_btn = ttk.Button(
            btn_frame,
            text="📋 Logs",
            command=self._on_open_logs_clicked,
            bootstyle="outline",
        )
        self.open_logs_btn.pack(side=LEFT, expand=YES, fill=X)

        # AI/ML Model Settings
        model_frame = ttk.Labelframe(container, text="🤖 AI Model (Optional)", padding=12, bootstyle="warning")
        model_frame.pack(fill=X, pady=(0, 8), padx=2)

        self.model_enabled_var = ttk.BooleanVar(value=False)
        model_cb = ttk.Checkbutton(
            model_frame,
            text="Enable ML Detection",
            variable=self.model_enabled_var,
            bootstyle="warning-round-toggle",
            command=self._on_model_enabled_changed,
        )
        model_cb.pack(anchor="w", pady=(0, 8))
        self._trace_variable(self.model_enabled_var)
        self._register_config_widget(UIField.MODEL_ENABLED_TOGGLE.value, model_cb)

        # Model type
        type_frame = ttk.Frame(model_frame)
        type_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(type_frame, text="Model:").pack(side=LEFT, padx=(0, 8))
        self.model_type_var = ttk.StringVar(value="roboflow")
        model_type_combo = ttk.Combobox(
            type_frame,
            values=["roboflow"],
            width=15,
            state=READONLY,
            textvariable=self.model_type_var,
        )
        model_type_combo.pack(side=LEFT, fill=X, expand=YES)
        self._trace_variable(self.model_type_var)
        self._register_config_widget(UIField.MODEL_TYPE.value, model_type_combo)

        # API Key
        ttk.Label(model_frame, text="API Key:").pack(anchor="w")
        self.roboflow_api_key_var = ttk.StringVar(value="")
        api_entry = ttk.Entry(model_frame, textvariable=self.roboflow_api_key_var, show="•")
        api_entry.pack(fill=X, pady=(4, 8))
        self._trace_variable(self.roboflow_api_key_var)
        self._register_config_widget(UIField.ROBOFLOW_API_KEY.value, api_entry)

        # Model ID
        ttk.Label(model_frame, text="Model ID:").pack(anchor="w")
        self.roboflow_model_id_var = ttk.StringVar(value="")
        model_entry = ttk.Entry(model_frame, textvariable=self.roboflow_model_id_var)
        model_entry.pack(fill=X, pady=(4, 8))
        self._trace_variable(self.roboflow_model_id_var)
        self._register_config_widget(UIField.ROBOFLOW_MODEL_ID.value, model_entry)
        ToolTip(model_entry, "Format: project-name/version")

        # Workflow ID (optional)
        ttk.Label(model_frame, text="Workflow ID (optional):").pack(anchor="w")
        self.roboflow_workflow_id_var = ttk.StringVar(value="")
        workflow_entry = ttk.Entry(model_frame, textvariable=self.roboflow_workflow_id_var)
        workflow_entry.pack(fill=X, pady=(4, 8))
        self._trace_variable(self.roboflow_workflow_id_var)
        self._register_config_widget(UIField.ROBOFLOW_WORKFLOW_ID.value, workflow_entry)

        # Confidence threshold
        conf_frame = ttk.Frame(model_frame)
        conf_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(conf_frame, text="Confidence:").pack(side=LEFT, padx=(0, 8))
        self.model_confidence_var = ttk.StringVar(value="0.7")
        conf_spin = ttk.Spinbox(
            conf_frame,
            from_=0.0,
            to=1.0,
            increment=0.05,
            width=8,
            textvariable=self.model_confidence_var,
        )
        conf_spin.pack(side=LEFT)
        self._trace_variable(self.model_confidence_var)
        self._register_config_widget(UIField.MODEL_CONFIDENCE_THRESHOLD.value, conf_spin)

        # Test button and status
        test_frame = ttk.Frame(model_frame)
        test_frame.pack(fill=X)

        self.test_model_btn = ttk.Button(
            test_frame,
            text="Test Connection",
            command=self._on_test_model_connection,
            bootstyle="warning-outline",
        )
        self.test_model_btn.pack(side=LEFT, padx=(0, 8))
        self._register_config_widget("test_model_button", self.test_model_btn)

        self.model_status_label = ttk.Label(test_frame, text="")
        self.model_status_label.pack(side=LEFT)

        self.model_connection_status_label = ttk.Label(model_frame, text="")
        self.model_connection_status_label.pack(anchor="w", pady=(8, 0))

        self._on_model_enabled_changed()

        # Performance/Navigation Settings
        perf_frame = ttk.Labelframe(container, text="⚡ Performance", padding=12, bootstyle="success")
        perf_frame.pack(fill=X, pady=(0, 8), padx=2)

        # Navigation Speed
        nav_config = next(s for s in PERFORMANCE_SETTINGS if s.key == UIField.NAV_SPEED_MODE)
        ttk.Label(perf_frame, text="Navigation Speed:").pack(anchor="w")
        self.nav_speed_var = ttk.StringVar(value=str(nav_config.default))
        nav_combo = ttk.Combobox(
            perf_frame,
            textvariable=self.nav_speed_var,
            values=nav_config.values,
            state=READONLY,
            bootstyle="success",
        )
        nav_combo.pack(fill=X, pady=(4, 8))
        self._trace_variable(self.nav_speed_var)
        self._register_config_widget(UIField.NAV_SPEED_MODE.value, nav_combo)
        ToolTip(nav_combo, "Safe: Longer delays for slow systems\nNormal: Balanced timing\nFast: Reduced delays\nAggressive: Minimum delays")

        # Win Check Batch Size
        batch_config = next(s for s in PERFORMANCE_SETTINGS if s.key == UIField.WIN_CHECK_BATCH_SIZE)
        batch_frame = ttk.Frame(perf_frame)
        batch_frame.pack(fill=X, pady=(0, 8))
        ttk.Label(batch_frame, text="Win Check Every N Battles:").pack(side=LEFT, padx=(0, 8))
        self.win_batch_var = ttk.StringVar(value=str(batch_config.default))
        batch_spin = ttk.Spinbox(
            batch_frame,
            from_=min(batch_config.values),
            to=max(batch_config.values),
            width=4,
            textvariable=self.win_batch_var,
            command=self._notify_config_change,
            state=READONLY,
        )
        batch_spin.pack(side=LEFT)
        self._trace_variable(self.win_batch_var)
        self._register_config_widget(UIField.WIN_CHECK_BATCH_SIZE.value, batch_spin)
        ToolTip(batch_spin, "Check win/loss after this many battles (saves 10-20s per battle)")

        ttk.Label(
            perf_frame,
            text="💡 Tip: Higher batch size = faster battles but less accurate stats per deck",
            font=("Segoe UI", 8),
            bootstyle="secondary",
            wraplength=400,
        ).pack(anchor="w")

    def _register_config_widget(self, key: str, widget: tk.Widget) -> None:
        self._config_widgets[key] = widget

    def _notify_config_change(self, *_: object) -> None:
        if self._suspend_traces > 0 or self._config_callback is None:
            return
        self.after_idle(lambda: self._config_callback(self.get_all_values()))

    def _trace_variable(self, var: tk.Variable) -> None:
        trace_id = var.trace_add("write", self._notify_config_change)
        self._traces.append((var, trace_id))

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

    def _hide_action_button(self) -> None:
        self.action_btn.pack_forget()
        if not self.stop_btn.winfo_ismapped():
            self.stop_btn.pack(side=LEFT)

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
        enabled = self.model_enabled_var.get()
        state = tk.NORMAL if enabled else tk.DISABLED

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

        if not enabled and hasattr(self, "model_status_label"):
            self.model_status_label.configure(text="")

        self._notify_config_change()

    def _on_test_model_connection(self) -> None:
        api_key = self.roboflow_api_key_var.get()
        model_id = self.roboflow_model_id_var.get()

        if not api_key or not model_id:
            self.model_status_label.configure(text="❌ Enter API key and Model ID", bootstyle="danger")
            self.set_model_connection_status(False)
            return

        self.model_status_label.configure(text="⏳ Testing...", bootstyle="secondary")
        self.test_model_btn.configure(state=tk.DISABLED)
        self.update_idletasks()

        try:
            from pyclashbot.detection.roboflow_model import RoboflowModel  # noqa: PLC0415

            test_model = RoboflowModel(api_key=api_key, model_id=model_id)

            if not test_model.is_available():
                self.model_status_label.configure(text="❌ Connection failed", bootstyle="danger")
                self.set_model_connection_status(False)
                return

            import numpy as np  # noqa: PLC0415

            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            test_model.predict(test_image)

            self.model_status_label.configure(text="✓ Connected!", bootstyle="success")
            self.set_model_connection_status(True, "roboflow", self.model_enabled_var.get())

        except ImportError:
            self.model_status_label.configure(text="❌ Install inference-sdk", bootstyle="danger")
            self.set_model_connection_status(False)
        except Exception as e:
            error_msg = str(e)[:40] + "..." if len(str(e)) > 40 else str(e)
            self.model_status_label.configure(text=f"❌ {error_msg}", bootstyle="danger")
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
