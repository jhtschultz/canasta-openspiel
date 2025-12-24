"""Observer for Canasta game - provides observation tensors for RL."""
import numpy as np
import pyspiel

from canasta.cards import NUM_CARDS, is_wild, rank_of, is_red_three

# Tensor dimensions
NUM_RANKS = 13
NUM_TEAMS = 2
NUM_PHASES = 4  # draw, meld, discard, going_out_query


class CanastaObserver:
    """Observer providing tensors for Canasta game state."""

    def __init__(self, iig_obs_type, params):
        """Initialize observer with tensor specifications.

        Args:
            iig_obs_type: Type of observation (ignored for now)
            params: Additional parameters (optional)
        """
        if params:
            self.params = dict(params)
        else:
            self.params = {}

        self.iig_obs_type = iig_obs_type

        # Information state tensor structure:
        # - Hand: 108 (one-hot for each card in hand)
        # - Team 0 melds: 13 (count per rank, normalized by 7 for canasta size)
        # - Team 1 melds: 13
        # - Discard top: 109 (108 cards + 1 for empty)
        # - Pile size: 1 (normalized 0-1)
        # - Stock size: 1 (normalized 0-1)
        # - Team scores: 2 (normalized by 10000)
        # - Phase: 4 (one-hot: draw, meld, discard, going_out_query)
        # - Red threes: 8 (4 per team, binary indicators)
        # - Canasta counts: 4 (natural and mixed per team, normalized by 4)
        # - Turn phase indicators: 3 (draw, meld, discard one-hot)
        # - Initial meld made: 2 (per team, binary)
        # - Pile frozen: 1 (binary)
        # - Current player: 4 (one-hot)

        self._info_state_size = (
            108 +      # hand
            13 + 13 +  # team melds
            109 +      # discard top
            1 + 1 +    # pile size, stock size
            2 +        # team scores
            4 +        # phase
            8 +        # red threes
            4 +        # canasta counts
            3 +        # turn phase
            2 +        # initial meld made
            1 +        # pile frozen
            4          # current player
        )  # = 275

        # Observation tensor (same as info state for now, will be filtered later)
        self._obs_size = self._info_state_size

        self.tensor = np.zeros(self._info_state_size, dtype=np.float32)
        self.dict = {"observation": self.tensor}

    def set_from(self, state, player):
        """Set tensor values from game state for given player.

        Args:
            state: CanastaState instance
            player: Player index (0-3)
        """
        self.tensor.fill(0)
        offset = 0

        # Hand encoding (108 dims)
        if 0 <= player < len(state._hands):
            hand = state._hands[player]
            for card_id in hand:
                if 0 <= card_id < NUM_CARDS:
                    self.tensor[offset + card_id] = 1.0
        offset += NUM_CARDS

        # Team melds encoding (13 + 13 dims)
        for team in range(NUM_TEAMS):
            for meld in state._melds[team]:
                rank = meld.rank
                if 0 <= rank < NUM_RANKS:
                    count = len(meld.natural_cards) + len(meld.wild_cards)
                    # Normalize by 7 (canasta size)
                    self.tensor[offset + rank] = min(count / 7.0, 1.0)
            offset += NUM_RANKS

        # Discard top (109 dims - 108 cards + empty)
        if state._discard_pile:
            top_card = state._discard_pile[-1]
            if 0 <= top_card < NUM_CARDS:
                self.tensor[offset + top_card] = 1.0
        else:
            # Empty pile indicator
            self.tensor[offset + NUM_CARDS] = 1.0
        offset += NUM_CARDS + 1

        # Pile size (1 dim, normalized)
        self.tensor[offset] = len(state._discard_pile) / 108.0
        offset += 1

        # Stock size (1 dim, normalized)
        self.tensor[offset] = len(state._stock) / 108.0
        offset += 1

        # Team scores (2 dims, normalized by 10000)
        for team in range(NUM_TEAMS):
            self.tensor[offset + team] = state._team_scores[team] / 10000.0
        offset += NUM_TEAMS

        # Phase encoding (4 dims one-hot)
        # Map game phase to index
        if state._dealing_phase:
            phase_idx = 0
        elif state._go_out_query_pending:
            phase_idx = 3
        elif state._turn_phase == "draw":
            phase_idx = 0
        elif state._turn_phase == "meld":
            phase_idx = 1
        elif state._turn_phase == "discard":
            phase_idx = 2
        else:
            phase_idx = 0

        if 0 <= phase_idx < NUM_PHASES:
            self.tensor[offset + phase_idx] = 1.0
        offset += NUM_PHASES

        # Red threes (8 dims - 4 per team)
        for team in range(NUM_TEAMS):
            red_count = len(state._red_threes[team])
            # Encode count (max 4 per team)
            for i in range(min(red_count, 4)):
                self.tensor[offset + i] = 1.0
            offset += 4

        # Canasta counts (4 dims - natural and mixed per team)
        for team in range(NUM_TEAMS):
            # Count natural and mixed canastas
            natural_count = 0
            mixed_count = 0
            for meld in state._melds[team]:
                if len(meld.natural_cards) + len(meld.wild_cards) >= 7:
                    if len(meld.wild_cards) == 0:
                        natural_count += 1
                    else:
                        mixed_count += 1

            # Normalize by 4 (reasonable max)
            self.tensor[offset] = natural_count / 4.0
            self.tensor[offset + 1] = mixed_count / 4.0
            offset += 2

        # Turn phase indicators (3 dims: draw, meld, discard)
        turn_phase_map = {"draw": 0, "meld": 1, "discard": 2}
        turn_idx = turn_phase_map.get(state._turn_phase, 0)
        if 0 <= turn_idx < 3:
            self.tensor[offset + turn_idx] = 1.0
        offset += 3

        # Initial meld made (2 dims - per team)
        for team in range(NUM_TEAMS):
            self.tensor[offset + team] = 1.0 if state._initial_meld_made[team] else 0.0
        offset += NUM_TEAMS

        # Pile frozen (1 dim)
        # Check if pile is frozen
        if hasattr(state, '_is_pile_frozen'):
            # Save current player and temporarily set to player we're observing
            saved_player = state._current_player
            state._current_player = player
            try:
                frozen = state._is_pile_frozen()
                self.tensor[offset] = 1.0 if frozen else 0.0
            finally:
                state._current_player = saved_player
        else:
            self.tensor[offset] = 1.0 if state._pile_frozen else 0.0
        offset += 1

        # Current player (4 dims one-hot)
        curr = state._current_player
        if 0 <= curr < 4:
            self.tensor[offset + curr] = 1.0
        offset += 4

    def string_from(self, state, player):
        """Return string representation of observation.

        Args:
            state: CanastaState instance
            player: Player index

        Returns:
            String description of observation
        """
        return f"Player {player} observing: Hand={len(state._hands[player])} cards, " \
               f"Stock={len(state._stock)}, Discard={len(state._discard_pile)}, " \
               f"Phase={state._turn_phase}"

    def info_state_size(self):
        """Return size of information state tensor."""
        return self._info_state_size

    def observation_size(self):
        """Return size of observation tensor."""
        return self._obs_size
