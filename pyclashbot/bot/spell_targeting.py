"""
Intelligent spell targeting system for dynamic spell placement.

This module provides smart spell usage including:
- Targeting enemy troop clusters for splash spells
- Finishing off low-health towers with damage spells
- Freezing enemy pushes at optimal moments
- Using arrows/zap on swarms efficiently
- Resetting inferno towers/dragons with zap

The system uses a combination of:
1. Battlefield detection (via hybrid_detector if available)
2. Tower health estimation via pixel sampling
3. Threat level analysis from bridge activity
4. Strategic spell value calculation
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

# Import card data constants - these are defined in card_data.py
from pyclashbot.bot.card_data import (
    ALL_SPELL_CARDS,
    ANTI_SWARM_SPELLS,
    BRIDGE_ZONE_Y_MAX,
    BRIDGE_ZONE_Y_MIN,
    ENEMY_KING_TOWER_POS,
    ENEMY_LEFT_TOWER_POS,
    ENEMY_RIGHT_TOWER_POS,
    ENEMY_TERRITORY_Y_MAX,
    ENEMY_TERRITORY_Y_MIN,
    HEAVY_SPELLS,
    LEFT_LANE_X_MAX,
    LEFT_LANE_X_MIN,
    OUR_TERRITORY_Y_MAX,
    OUR_TERRITORY_Y_MIN,
    PLAY_COORDS,
    RESET_SPELLS,
    RIGHT_LANE_X_MAX,
    RIGHT_LANE_X_MIN,
    SPELL_PROPERTIES,
    TOWER_FINISHING_SPELLS,
)

if TYPE_CHECKING:
    from pyclashbot.utils.logger import Logger


class SpellUseCase(Enum):
    """Enumeration of spell use cases for decision making."""

    TOWER_FINISH = "tower_finish"
    CLUSTER_DAMAGE = "cluster_damage"
    ANTI_SWARM = "anti_swarm"
    DEFENSIVE = "defensive"
    INFERNO_RESET = "inferno_reset"
    PUSH_SUPPORT = "push_support"
    KING_ACTIVATION = "king_activation"
    DEFAULT = "default"


@dataclass
class TroopCluster:
    """Represents a detected cluster of enemy troops."""

    center_x: int
    center_y: int
    estimated_elixir: float
    troop_count: int
    is_air: bool = False
    has_swarm: bool = False
    lane: str = "center"  # "left", "right", or "center"


@dataclass
class TowerState:
    """Represents the estimated state of a tower."""

    position: tuple[int, int]
    health_percent: float  # 0.0 to 1.0
    is_destroyed: bool = False
    lane: str = "center"  # "left", "right", or "king"


@dataclass
class SpellDecision:
    """Result of spell targeting decision."""

    should_play: bool
    target_coords: tuple[int, int] | None
    use_case: SpellUseCase
    expected_value: float  # Estimated elixir value of the play
    reason: str


@dataclass
class BattlefieldState:
    """Current state of the battlefield for spell decisions."""

    troop_clusters: list[TroopCluster] = field(default_factory=list)
    enemy_towers: dict[str, TowerState] = field(default_factory=dict)
    our_towers: dict[str, TowerState] = field(default_factory=dict)
    left_threat_level: float = 0.0
    right_threat_level: float = 0.0
    elapsed_time: float = 0.0
    our_elixir: int = 5


class SpellAnalyzer:
    """Analyzes spell cards and their properties."""

    @staticmethod
    def is_spell(card_id: str) -> bool:
        """Check if a card is a spell."""
        return card_id in ALL_SPELL_CARDS

    @staticmethod
    def get_spell_properties(card_id: str) -> dict | None:
        """Get properties of a spell card."""
        return SPELL_PROPERTIES.get(card_id)

    @staticmethod
    def can_target_troops(card_id: str) -> bool:
        """Check if spell can effectively target troops."""
        props = SPELL_PROPERTIES.get(card_id, {})
        # Spells that spawn troops or buff don't target enemy troops
        return props.get("is_spell", False) and not props.get("spawns_troop", False) and not props.get("buffs_troops", False)

    @staticmethod
    def is_anti_swarm_spell(card_id: str) -> bool:
        """Check if spell is effective against swarms."""
        return card_id in ANTI_SWARM_SPELLS

    @staticmethod
    def can_finish_tower(card_id: str) -> bool:
        """Check if spell can be used to finish towers."""
        return card_id in TOWER_FINISHING_SPELLS

    @staticmethod
    def is_heavy_spell(card_id: str) -> bool:
        """Check if spell is a heavy damage spell."""
        return card_id in HEAVY_SPELLS

    @staticmethod
    def can_reset_charge(card_id: str) -> bool:
        """Check if spell can reset charge-based attacks (inferno/sparky)."""
        return card_id in RESET_SPELLS

    @staticmethod
    def get_spell_damage(card_id: str) -> int:
        """Get the crown tower damage of a spell."""
        props = SPELL_PROPERTIES.get(card_id, {})
        return props.get("damage", 0)

    @staticmethod
    def get_spell_radius(card_id: str) -> float:
        """Get the radius of a spell."""
        props = SPELL_PROPERTIES.get(card_id, {})
        return props.get("radius", 0.0)

    @staticmethod
    def get_spell_elixir(card_id: str) -> int:
        """Get the elixir cost of a spell."""
        props = SPELL_PROPERTIES.get(card_id, {})
        return props.get("elixir", 0)


class TowerHealthDetector:
    """Detects tower health via pixel sampling."""

    # Tower HP bar color ranges (approximate)
    # Healthy tower: more blue/cyan
    # Damaged tower: more red/orange
    HP_BAR_HEALTHY_COLOR = np.array([50, 200, 50])  # Green-ish
    HP_BAR_DAMAGED_COLOR = np.array([200, 50, 50])  # Red-ish

    # HP bar positions relative to tower centers (Y offset above tower)
    HP_BAR_Y_OFFSET = -20

    # HP bar sampling dimensions
    HP_BAR_WIDTH = 40
    HP_BAR_SAMPLE_POINTS = 10

    # Enemy tower HP bar coordinates (screen positions)
    ENEMY_LEFT_HP_BAR = (116, 140)
    ENEMY_RIGHT_HP_BAR = (302, 140)
    ENEMY_KING_HP_BAR = (207, 80)

    # Threshold below which we consider a tower "finishable"
    FINISH_THRESHOLD = 0.15  # 15% HP

    @classmethod
    def estimate_tower_health(
        cls,
        screenshot: np.ndarray,
        tower_type: str,
        is_enemy: bool = True,
    ) -> TowerState:
        """Estimate tower health from screenshot.

        Args:
            screenshot: Current game screenshot
            tower_type: "left", "right", or "king"
            is_enemy: Whether this is an enemy tower

        Returns:
            TowerState with estimated health
        """
        # Get HP bar position based on tower type
        if is_enemy:
            if tower_type == "left":
                hp_bar_pos = cls.ENEMY_LEFT_HP_BAR
                tower_pos = ENEMY_LEFT_TOWER_POS
            elif tower_type == "right":
                hp_bar_pos = cls.ENEMY_RIGHT_HP_BAR
                tower_pos = ENEMY_RIGHT_TOWER_POS
            else:  # king
                hp_bar_pos = cls.ENEMY_KING_HP_BAR
                tower_pos = ENEMY_KING_TOWER_POS
        else:
            # Our towers - for now just return high health
            # Could be extended to track our tower health too
            return TowerState(
                position=(207, 460),
                health_percent=1.0,
                is_destroyed=False,
                lane=tower_type,
            )

        try:
            # Sample pixels along the HP bar
            hp_bar_x = hp_bar_pos[0]
            hp_bar_y = hp_bar_pos[1]

            # Check if tower exists (not destroyed) by sampling tower area
            tower_area = screenshot[
                max(0, tower_pos[1] - 10) : tower_pos[1] + 10,
                max(0, tower_pos[0] - 10) : tower_pos[0] + 10,
            ]

            # If tower area is mostly dark/empty, tower might be destroyed
            if np.mean(tower_area) < 30:
                return TowerState(
                    position=tower_pos,
                    health_percent=0.0,
                    is_destroyed=True,
                    lane=tower_type,
                )

            # Sample HP bar pixels
            health_samples = []
            for i in range(cls.HP_BAR_SAMPLE_POINTS):
                x = hp_bar_x - cls.HP_BAR_WIDTH // 2 + (i * cls.HP_BAR_WIDTH // cls.HP_BAR_SAMPLE_POINTS)
                x = max(0, min(x, screenshot.shape[1] - 1))
                y = max(0, min(hp_bar_y, screenshot.shape[0] - 1))

                pixel = screenshot[y, x]

                # Check if pixel is part of HP bar (greenish = health remaining)
                # Simple heuristic: green channel dominance indicates health
                if pixel[1] > pixel[0] and pixel[1] > pixel[2]:  # Green dominant
                    health_samples.append(1)
                elif pixel[0] > 150:  # Red indicates damage/no health
                    health_samples.append(0)
                else:
                    health_samples.append(0.5)  # Unknown

            # Calculate health percentage from samples
            if health_samples:
                # Count from left - first non-healthy pixel indicates end of HP bar
                health_percent = sum(health_samples) / len(health_samples)
            else:
                health_percent = 1.0  # Default to full if can't detect

            return TowerState(
                position=tower_pos,
                health_percent=health_percent,
                is_destroyed=False,
                lane=tower_type,
            )

        except (IndexError, ValueError):
            # If any error in sampling, return unknown state
            return TowerState(
                position=tower_pos,
                health_percent=0.5,  # Unknown
                is_destroyed=False,
                lane=tower_type,
            )

    @classmethod
    def can_finish_tower(
        cls,
        tower_state: TowerState,
        spell_damage: int,
        tower_max_hp: int = 2534,  # Princess tower HP at tournament standard
    ) -> bool:
        """Check if a spell can finish off a tower.

        Args:
            tower_state: Current tower state
            spell_damage: Damage spell deals to crown towers
            tower_max_hp: Maximum HP of the tower type

        Returns:
            True if spell damage exceeds remaining tower HP
        """
        if tower_state.is_destroyed:
            return False

        remaining_hp = tower_state.health_percent * tower_max_hp
        return spell_damage >= remaining_hp


class ClusterDetector:
    """Detects clusters of enemy troops for splash spell targeting."""

    # Minimum cluster size to be worth a spell
    MIN_CLUSTER_VALUE = 3.0  # Elixir value

    # Cluster detection grid size
    GRID_SIZE = 40

    @classmethod
    def detect_clusters_from_threat(
        cls,
        left_threat: float,
        right_threat: float,
        threshold: float = 5000,
    ) -> list[TroopCluster]:
        """Estimate troop clusters from threat levels.

        This is a fallback when no ML detection is available.
        Uses bridge activity to infer troop presence.

        Args:
            left_threat: Left lane threat level
            right_threat: Right lane threat level
            threshold: Minimum threat to consider a cluster

        Returns:
            List of estimated troop clusters
        """
        clusters = []

        if left_threat > threshold:
            # Estimate cluster near left bridge
            estimated_elixir = min(left_threat / 2000, 10.0)  # Rough estimate
            clusters.append(
                TroopCluster(
                    center_x=(LEFT_LANE_X_MIN + LEFT_LANE_X_MAX) // 2,
                    center_y=(BRIDGE_ZONE_Y_MIN + BRIDGE_ZONE_Y_MAX) // 2,
                    estimated_elixir=estimated_elixir,
                    troop_count=int(estimated_elixir / 1.5),
                    lane="left",
                    has_swarm=left_threat > threshold * 1.5,
                )
            )

        if right_threat > threshold:
            estimated_elixir = min(right_threat / 2000, 10.0)
            clusters.append(
                TroopCluster(
                    center_x=(RIGHT_LANE_X_MIN + RIGHT_LANE_X_MAX) // 2,
                    center_y=(BRIDGE_ZONE_Y_MIN + BRIDGE_ZONE_Y_MAX) // 2,
                    estimated_elixir=estimated_elixir,
                    troop_count=int(estimated_elixir / 1.5),
                    lane="right",
                    has_swarm=right_threat > threshold * 1.5,
                )
            )

        return clusters

    @classmethod
    def detect_clusters_from_detections(
        cls,
        detections: list[dict],
        min_cluster_distance: int = 60,
    ) -> list[TroopCluster]:
        """Group detected troops into clusters for splash targeting.

        Args:
            detections: List of detection results from ML model
            min_cluster_distance: Maximum distance to group into same cluster

        Returns:
            List of troop clusters
        """
        if not detections:
            return []

        # Simple clustering: group nearby detections
        clusters = []
        used = set()

        for i, det in enumerate(detections):
            if i in used:
                continue

            # Start a new cluster with this detection
            cluster_detections = [det]
            used.add(i)

            center = det.get("center", (0, 0))

            # Find nearby detections
            for j, other in enumerate(detections):
                if j in used:
                    continue

                other_center = other.get("center", (0, 0))
                distance = (
                    (center[0] - other_center[0]) ** 2 + (center[1] - other_center[1]) ** 2
                ) ** 0.5

                if distance < min_cluster_distance:
                    cluster_detections.append(other)
                    used.add(j)

            # Calculate cluster properties
            if cluster_detections:
                avg_x = sum(d.get("center", (0, 0))[0] for d in cluster_detections) // len(
                    cluster_detections
                )
                avg_y = sum(d.get("center", (0, 0))[1] for d in cluster_detections) // len(
                    cluster_detections
                )

                # Estimate elixir value (rough heuristic)
                estimated_elixir = len(cluster_detections) * 2.0

                # Determine lane
                if avg_x < LEFT_LANE_X_MAX:
                    lane = "left"
                elif avg_x > RIGHT_LANE_X_MIN:
                    lane = "right"
                else:
                    lane = "center"

                # Check for swarm (many small units)
                has_swarm = len(cluster_detections) >= 4

                clusters.append(
                    TroopCluster(
                        center_x=avg_x,
                        center_y=avg_y,
                        estimated_elixir=estimated_elixir,
                        troop_count=len(cluster_detections),
                        lane=lane,
                        has_swarm=has_swarm,
                    )
                )

        return clusters


class SpellDecisionEngine:
    """Main engine for making spell targeting decisions."""

    # Minimum value threshold for playing spells
    MIN_SPELL_VALUE = 1.5  # Must get at least 1.5x elixir value

    # Threat threshold for defensive spells
    DEFENSIVE_THREAT_THRESHOLD = 8000

    # Tower finish thresholds
    TOWER_FINISH_HP_THRESHOLD = 0.20  # Below 20% HP, consider finishing

    def __init__(self, logger: "Logger | None" = None):
        """Initialize the spell decision engine.

        Args:
            logger: Optional logger for debugging
        """
        self.logger = logger
        self.tower_detector = TowerHealthDetector()
        self.cluster_detector = ClusterDetector()
        self.spell_analyzer = SpellAnalyzer()

    def _log(self, message: str):
        """Log a message if logger is available."""
        if self.logger:
            self.logger.log(f"[SpellTarget] {message}")

    def get_spell_target(
        self,
        card_id: str,
        screenshot: np.ndarray | None,
        left_threat: float,
        right_threat: float,
        preferred_lane: str = "left",
        elapsed_time: float = 0.0,
        detections: list[dict] | None = None,
    ) -> SpellDecision:
        """Determine the optimal target for a spell.

        Args:
            card_id: The spell card ID
            screenshot: Current game screenshot (for tower health detection)
            left_threat: Left lane threat level
            right_threat: Right lane threat level
            preferred_lane: Preferred lane to target if no clear choice
            elapsed_time: Seconds elapsed in battle
            detections: Optional ML detections of battlefield objects

        Returns:
            SpellDecision with targeting information
        """
        # Verify this is a spell we can handle
        if not self.spell_analyzer.is_spell(card_id):
            return SpellDecision(
                should_play=False,
                target_coords=None,
                use_case=SpellUseCase.DEFAULT,
                expected_value=0.0,
                reason="Not a spell card",
            )

        props = self.spell_analyzer.get_spell_properties(card_id)
        if not props:
            return self._get_fallback_coords(card_id, preferred_lane)

        # Special handling for spells that spawn troops or buff
        if props.get("spawns_troop") or props.get("buffs_troops"):
            return self._get_fallback_coords(card_id, preferred_lane)

        # Build battlefield state
        battlefield = self._build_battlefield_state(
            screenshot, left_threat, right_threat, elapsed_time, detections
        )

        # Check use cases in priority order
        decisions = []

        # 1. Tower finish opportunity (highest priority for finisher spells)
        if self.spell_analyzer.can_finish_tower(card_id):
            tower_decision = self._evaluate_tower_finish(card_id, battlefield)
            if tower_decision.should_play:
                decisions.append(tower_decision)

        # 2. Defensive spell against heavy threat
        if left_threat > self.DEFENSIVE_THREAT_THRESHOLD or right_threat > self.DEFENSIVE_THREAT_THRESHOLD:
            defensive_decision = self._evaluate_defensive_spell(card_id, battlefield)
            if defensive_decision.should_play:
                decisions.append(defensive_decision)

        # 3. Cluster damage (for splash spells)
        if props.get("radius", 0) > 0:
            cluster_decision = self._evaluate_cluster_target(card_id, battlefield)
            if cluster_decision.should_play:
                decisions.append(cluster_decision)

        # 4. Anti-swarm (for cheap spells against swarms)
        if self.spell_analyzer.is_anti_swarm_spell(card_id):
            swarm_decision = self._evaluate_swarm_target(card_id, battlefield)
            if swarm_decision.should_play:
                decisions.append(swarm_decision)

        # 5. Inferno/Sparky reset
        if self.spell_analyzer.can_reset_charge(card_id):
            reset_decision = self._evaluate_reset_target(card_id, battlefield)
            if reset_decision.should_play:
                decisions.append(reset_decision)

        # Choose the best decision based on expected value
        if decisions:
            best_decision = max(decisions, key=lambda d: d.expected_value)
            self._log(f"Spell {card_id}: {best_decision.reason} (value: {best_decision.expected_value:.1f})")
            return best_decision

        # If late game (double/triple elixir), be more willing to use spells on tower
        if elapsed_time > 120 and self.spell_analyzer.can_finish_tower(card_id):
            return self._get_tower_chip_coords(card_id, preferred_lane, battlefield)

        # Fallback to default coords
        return self._get_fallback_coords(card_id, preferred_lane)

    def _build_battlefield_state(
        self,
        screenshot: np.ndarray | None,
        left_threat: float,
        right_threat: float,
        elapsed_time: float,
        detections: list[dict] | None,
    ) -> BattlefieldState:
        """Build current battlefield state from available information."""
        state = BattlefieldState(
            left_threat_level=left_threat,
            right_threat_level=right_threat,
            elapsed_time=elapsed_time,
        )

        # Detect troop clusters
        if detections:
            state.troop_clusters = self.cluster_detector.detect_clusters_from_detections(detections)
        else:
            # Fall back to threat-based estimation
            state.troop_clusters = self.cluster_detector.detect_clusters_from_threat(
                left_threat, right_threat
            )

        # Detect tower health if screenshot available
        if screenshot is not None:
            for tower_type in ["left", "right", "king"]:
                tower_state = self.tower_detector.estimate_tower_health(
                    screenshot, tower_type, is_enemy=True
                )
                state.enemy_towers[tower_type] = tower_state

        return state

    def _evaluate_tower_finish(
        self, card_id: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Evaluate if spell should be used to finish a tower."""
        spell_damage = self.spell_analyzer.get_spell_damage(card_id)
        spell_elixir = self.spell_analyzer.get_spell_elixir(card_id)

        best_target = None
        best_value = 0.0

        for tower_type, tower_state in battlefield.enemy_towers.items():
            if tower_state.is_destroyed:
                continue

            # Check if we can finish this tower
            if self.tower_detector.can_finish_tower(tower_state, spell_damage):
                # Finishing a tower is extremely high value
                value = 10.0  # Tower finish is always worth it
                if value > best_value:
                    best_value = value
                    best_target = tower_state

            # Even if we can't finish, check if tower is low enough to chip
            elif tower_state.health_percent < self.TOWER_FINISH_HP_THRESHOLD:
                # Good value to chip a low tower
                value = 3.0 / spell_elixir if spell_elixir > 0 else 0
                if value > best_value:
                    best_value = value
                    best_target = tower_state

        if best_target and best_value > 0:
            return SpellDecision(
                should_play=True,
                target_coords=best_target.position,
                use_case=SpellUseCase.TOWER_FINISH,
                expected_value=best_value,
                reason=f"Tower finish on {best_target.lane} tower ({best_target.health_percent:.0%} HP)",
            )

        return SpellDecision(
            should_play=False,
            target_coords=None,
            use_case=SpellUseCase.TOWER_FINISH,
            expected_value=0.0,
            reason="No tower finish opportunity",
        )

    def _evaluate_defensive_spell(
        self, card_id: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Evaluate if spell should be used defensively against a push."""
        props = self.spell_analyzer.get_spell_properties(card_id)
        if not props:
            return SpellDecision(
                should_play=False,
                target_coords=None,
                use_case=SpellUseCase.DEFENSIVE,
                expected_value=0.0,
                reason="Unknown spell",
            )

        # Find the highest threat lane
        if battlefield.left_threat_level > battlefield.right_threat_level:
            threat_lane = "left"
            threat_level = battlefield.left_threat_level
        else:
            threat_lane = "right"
            threat_level = battlefield.right_threat_level

        # Find clusters in our territory on the threatened lane
        defensive_clusters = [
            c
            for c in battlefield.troop_clusters
            if c.lane == threat_lane and c.center_y > OUR_TERRITORY_Y_MIN
        ]

        if not defensive_clusters:
            # No clusters detected, but high threat - target bridge area
            if threat_level > self.DEFENSIVE_THREAT_THRESHOLD:
                # Target defensive zone
                if threat_lane == "left":
                    target_x = random.randint(LEFT_LANE_X_MIN + 20, LEFT_LANE_X_MAX - 20)
                else:
                    target_x = random.randint(RIGHT_LANE_X_MIN + 20, RIGHT_LANE_X_MAX - 20)

                target_y = random.randint(OUR_TERRITORY_Y_MIN, OUR_TERRITORY_Y_MIN + 80)

                # Estimate value based on threat level
                estimated_value = threat_level / 3000

                return SpellDecision(
                    should_play=estimated_value > self.MIN_SPELL_VALUE,
                    target_coords=(target_x, target_y),
                    use_case=SpellUseCase.DEFENSIVE,
                    expected_value=estimated_value,
                    reason=f"Defensive spell on {threat_lane} lane (threat: {threat_level:.0f})",
                )

        else:
            # Target the highest value cluster
            best_cluster = max(defensive_clusters, key=lambda c: c.estimated_elixir)
            spell_elixir = props.get("elixir", 3)
            value = best_cluster.estimated_elixir / spell_elixir

            return SpellDecision(
                should_play=value > self.MIN_SPELL_VALUE,
                target_coords=(best_cluster.center_x, best_cluster.center_y),
                use_case=SpellUseCase.DEFENSIVE,
                expected_value=value,
                reason=f"Defensive spell on cluster ({best_cluster.troop_count} troops)",
            )

        return SpellDecision(
            should_play=False,
            target_coords=None,
            use_case=SpellUseCase.DEFENSIVE,
            expected_value=0.0,
            reason="No defensive opportunity",
        )

    def _evaluate_cluster_target(
        self, card_id: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Evaluate cluster damage opportunity for splash spells."""
        props = self.spell_analyzer.get_spell_properties(card_id)
        if not props:
            return SpellDecision(
                should_play=False,
                target_coords=None,
                use_case=SpellUseCase.CLUSTER_DAMAGE,
                expected_value=0.0,
                reason="Unknown spell",
            )

        spell_elixir = props.get("elixir", 3)
        min_value = props.get("min_value_elixir", spell_elixir)

        # Find best cluster to target
        best_cluster = None
        best_value = 0.0

        for cluster in battlefield.troop_clusters:
            # Prefer clusters in enemy territory or at bridge
            position_bonus = 1.0
            if cluster.center_y < ENEMY_TERRITORY_Y_MAX:
                position_bonus = 1.2  # Bonus for hitting near their tower
            elif cluster.center_y < BRIDGE_ZONE_Y_MAX:
                position_bonus = 1.1  # Bonus for bridge area

            value = (cluster.estimated_elixir / spell_elixir) * position_bonus

            if value > best_value and cluster.estimated_elixir >= min_value:
                best_value = value
                best_cluster = cluster

        if best_cluster and best_value > self.MIN_SPELL_VALUE:
            return SpellDecision(
                should_play=True,
                target_coords=(best_cluster.center_x, best_cluster.center_y),
                use_case=SpellUseCase.CLUSTER_DAMAGE,
                expected_value=best_value,
                reason=f"Cluster damage ({best_cluster.estimated_elixir:.1f} elixir value)",
            )

        return SpellDecision(
            should_play=False,
            target_coords=None,
            use_case=SpellUseCase.CLUSTER_DAMAGE,
            expected_value=0.0,
            reason="No valuable cluster found",
        )

    def _evaluate_swarm_target(
        self, card_id: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Evaluate anti-swarm opportunity for cheap spells."""
        # Find clusters that look like swarms
        swarm_clusters = [c for c in battlefield.troop_clusters if c.has_swarm]

        if not swarm_clusters:
            return SpellDecision(
                should_play=False,
                target_coords=None,
                use_case=SpellUseCase.ANTI_SWARM,
                expected_value=0.0,
                reason="No swarm detected",
            )

        spell_elixir = self.spell_analyzer.get_spell_elixir(card_id)

        # Target the swarm with most troops
        best_swarm = max(swarm_clusters, key=lambda c: c.troop_count)
        value = best_swarm.estimated_elixir / spell_elixir

        return SpellDecision(
            should_play=value > self.MIN_SPELL_VALUE,
            target_coords=(best_swarm.center_x, best_swarm.center_y),
            use_case=SpellUseCase.ANTI_SWARM,
            expected_value=value,
            reason=f"Anti-swarm ({best_swarm.troop_count} troops)",
        )

    def _evaluate_reset_target(
        self, card_id: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Evaluate inferno/sparky reset opportunity.

        Note: This requires ML detection to identify specific unit types.
        For now, returns no play - could be enhanced with detection.
        """
        # Would need ML detection to identify inferno tower/dragon/sparky
        # For now, just return no play
        return SpellDecision(
            should_play=False,
            target_coords=None,
            use_case=SpellUseCase.INFERNO_RESET,
            expected_value=0.0,
            reason="Reset target detection not yet implemented",
        )

    def _get_tower_chip_coords(
        self, card_id: str, preferred_lane: str, battlefield: BattlefieldState
    ) -> SpellDecision:
        """Get coordinates to chip a tower with spell damage."""
        # Determine which tower to target
        if preferred_lane == "left":
            target_tower = battlefield.enemy_towers.get("left")
            if not target_tower or target_tower.is_destroyed:
                target_tower = battlefield.enemy_towers.get("right")
        else:
            target_tower = battlefield.enemy_towers.get("right")
            if not target_tower or target_tower.is_destroyed:
                target_tower = battlefield.enemy_towers.get("left")

        if target_tower and not target_tower.is_destroyed:
            return SpellDecision(
                should_play=True,
                target_coords=target_tower.position,
                use_case=SpellUseCase.DEFAULT,
                expected_value=1.0,
                reason=f"Tower chip on {target_tower.lane} tower",
            )

        # Fall back to default
        return self._get_fallback_coords(card_id, preferred_lane)

    def _get_fallback_coords(
        self, card_id: str, preferred_lane: str
    ) -> SpellDecision:
        """Get fallback coordinates using the existing PLAY_COORDS system."""
        # Get card group for this spell
        from pyclashbot.bot.card_data import CARD_TO_GROUP

        group = CARD_TO_GROUP.get(card_id, card_id)

        # Look up coords from PLAY_COORDS
        if group in PLAY_COORDS:
            group_coords = PLAY_COORDS[group]
            if preferred_lane in group_coords:
                coords = random.choice(group_coords[preferred_lane])
                return SpellDecision(
                    should_play=True,
                    target_coords=coords,
                    use_case=SpellUseCase.DEFAULT,
                    expected_value=1.0,
                    reason=f"Default {group} placement on {preferred_lane}",
                )

        # Ultimate fallback - generic spell coords
        if "spell" in PLAY_COORDS:
            spell_coords = PLAY_COORDS["spell"]
            if preferred_lane in spell_coords:
                coords = random.choice(spell_coords[preferred_lane])
                return SpellDecision(
                    should_play=True,
                    target_coords=coords,
                    use_case=SpellUseCase.DEFAULT,
                    expected_value=1.0,
                    reason="Default spell placement",
                )

        # Absolute fallback
        if preferred_lane == "left":
            coords = (116, 170)
        else:
            coords = (302, 170)

        return SpellDecision(
            should_play=True,
            target_coords=coords,
            use_case=SpellUseCase.DEFAULT,
            expected_value=0.5,
            reason="Fallback spell placement",
        )


# Convenience functions for easy integration

def get_smart_spell_coords(
    card_id: str,
    screenshot: np.ndarray | None,
    left_threat: float,
    right_threat: float,
    preferred_lane: str = "left",
    elapsed_time: float = 0.0,
    detections: list[dict] | None = None,
    logger: "Logger | None" = None,
) -> tuple[int, int]:
    """Get smart spell targeting coordinates.

    This is the main entry point for spell targeting integration.

    Args:
        card_id: The spell card ID
        screenshot: Current game screenshot
        left_threat: Left lane threat level
        right_threat: Right lane threat level
        preferred_lane: Preferred lane if no clear choice
        elapsed_time: Seconds elapsed in battle
        detections: Optional ML detections
        logger: Optional logger

    Returns:
        Tuple of (x, y) coordinates for spell placement
    """
    engine = SpellDecisionEngine(logger)
    decision = engine.get_spell_target(
        card_id=card_id,
        screenshot=screenshot,
        left_threat=left_threat,
        right_threat=right_threat,
        preferred_lane=preferred_lane,
        elapsed_time=elapsed_time,
        detections=detections,
    )

    if decision.target_coords:
        return decision.target_coords

    # Ultimate fallback
    if preferred_lane == "left":
        return (116, 170)
    return (302, 170)


def is_spell_card(card_id: str) -> bool:
    """Check if a card ID is a spell card."""
    return SpellAnalyzer.is_spell(card_id)
