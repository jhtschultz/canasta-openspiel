"""OpenSpiel implementation of Canasta.

This implements a 4-player Canasta game following Pagat Classic rules.
"""

import numpy as np
import pyspiel
from open_spiel.python.observation import IIGObserverForPublicInfoGame

from canasta.cards import NUM_CARDS, is_red_three, is_wild, is_black_three, rank_of, card_point_value
from canasta.deck import NUM_PLAYERS, HAND_SIZE, create_deck, deal_hands
from canasta.melds import (
    Meld,
    is_valid_meld,
    is_canasta,
    initial_meld_minimum,
    can_form_initial_meld,
    meld_point_value,
)
from canasta.scoring import calculate_hand_score
from canasta.observer import CanastaObserver

# Game constants
_NUM_PLAYERS = NUM_PLAYERS
_HAND_SIZE = HAND_SIZE
_NUM_CARDS = NUM_CARDS

# Action encoding
# Draw phase:
#   0: DRAW_STOCK - draw top card from stock pile
#   1: TAKE_PILE - take entire discard pile
# Meld phase:
#   2-1000: CREATE_MELD(rank, cards) - create new meld
#   1001-2000: ADD_TO_MELD(meld_idx, cards) - add to existing meld
#   2001: SKIP_MELD - skip melding, proceed to discard phase
# Discard phase: (to be implemented)
#   2100+: Discard actions
_NUM_DISTINCT_ACTIONS = 3000  # Enough for all action types

# Action constants for draw phase
ACTION_DRAW_STOCK = 0
ACTION_TAKE_PILE = 1

# Action constants for meld phase
ACTION_CREATE_MELD_START = 2
ACTION_CREATE_MELD_END = 1000
ACTION_ADD_TO_MELD_START = 1001
ACTION_ADD_TO_MELD_END = 2000
ACTION_SKIP_MELD = 2001

# Action constants for discard phase
ACTION_DISCARD_START = 2002
ACTION_DISCARD_END = 2109  # 2002 + 107 (max card ID)

# Action constants for going out
ACTION_ASK_PARTNER_GO_OUT = 2110
ACTION_ANSWER_GO_OUT_YES = 2111
ACTION_ANSWER_GO_OUT_NO = 2112
ACTION_GO_OUT = 2113

_GAME_TYPE = pyspiel.GameType(
    short_name="python_canasta",
    long_name="Python Canasta",
    dynamics=pyspiel.GameType.Dynamics.SEQUENTIAL,
    chance_mode=pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC,
    information=pyspiel.GameType.Information.IMPERFECT_INFORMATION,
    utility=pyspiel.GameType.Utility.GENERAL_SUM,
    reward_model=pyspiel.GameType.RewardModel.TERMINAL,
    max_num_players=_NUM_PLAYERS,
    min_num_players=_NUM_PLAYERS,
    provides_information_state_string=True,
    provides_information_state_tensor=True,
    provides_observation_string=True,
    provides_observation_tensor=True,
    parameter_specification={
        "num_players": _NUM_PLAYERS,
    },
)

_GAME_INFO = pyspiel.GameInfo(
    num_distinct_actions=_NUM_DISTINCT_ACTIONS,
    max_chance_outcomes=_NUM_CARDS,  # 108 cards can be dealt
    num_players=_NUM_PLAYERS,
    min_utility=-5000.0,  # Placeholder: large negative score
    max_utility=5000.0,   # Placeholder: large positive score
    utility_sum=0.0,      # Teams are partners, so general sum
    max_game_length=1000, # Placeholder: max rounds
)


class CanastaGame(pyspiel.Game):
    """A Python implementation of Canasta."""

    def __init__(self, params=None):
        super().__init__(_GAME_TYPE, _GAME_INFO, params or dict())

    def new_initial_state(self):
        """Returns a state corresponding to the start of a game."""
        return CanastaState(self)

    def make_py_observer(self, iig_obs_type=None, params=None):
        """Returns an object used for observing game state."""
        return CanastaObserver(
            iig_obs_type or pyspiel.IIGObservationType(perfect_recall=False),
            params,
        )


class CanastaState(pyspiel.State):
    """A Python implementation of the Canasta state."""

    def __init__(self, game):
        """Constructor; should only be called by Game.new_initial_state."""
        super().__init__(game)
        self._game = game
        self._num_players = game.num_players()

        # Game state
        self._deck = create_deck()
        self._hands = [[] for _ in range(self._num_players)]
        self._stock = []
        self._discard_pile = []
        self._melds = [[] for _ in range(2)]  # 2 teams (list of Meld objects)
        self._canastas = [0, 0]  # Count of canastas for Team 0, Team 1
        self._red_threes = [[] for _ in range(2)]  # Red 3s for each team

        # Tracking dealing phase
        self._cards_dealt = 0
        self._total_cards_to_deal = _NUM_PLAYERS * _HAND_SIZE
        self._red_three_replacements_needed = []  # Queue of (player_idx, red_three_card) needing replacement

        # Player tracking
        self._current_player = 0
        self._is_terminal = False
        self._returns = [0.0 for _ in range(self._num_players)]

        # Scoring tracking
        self._team_scores = [0, 0]  # Cumulative scores across hands
        self._hand_scores = [0, 0]  # Current hand scores

        # Multi-hand tracking
        self._hand_number = 0  # Current hand number (starts at 0)
        self._target_score = 5000  # Target score to win the game

        # Phase tracking
        self._dealing_phase = True
        self._game_phase = "dealing"  # "dealing", "playing", "terminal"
        self._turn_phase = "draw"  # "draw", "meld", "discard"

        # Draw phase tracking
        self._pile_frozen = False  # True if wild card discarded
        self._initial_meld_made = [False, False]  # Team 0, Team 1
        self._black_three_blocks_next = False  # True when black 3 discarded

        # Going out tracking
        self._go_out_query_pending = False  # True when waiting for partner answer
        self._go_out_query_asker = -1  # Player who asked permission
        self._go_out_approved = False  # Partner's answer
        self._partner_asked_this_turn = False  # Prevents asking twice
        self._game_over = False
        self._winning_team = -1  # 0 or 1

    def _start_new_hand(self):
        """Start a new hand, resetting cards but preserving team scores."""
        # Increment hand number
        self._hand_number += 1

        # Reset deck and dealing
        self._deck = create_deck()
        self._hands = [[] for _ in range(self._num_players)]
        self._stock = []
        self._discard_pile = []
        self._melds = [[] for _ in range(2)]
        self._canastas = [0, 0]
        self._red_threes = [[] for _ in range(2)]

        # Reset dealing phase
        self._cards_dealt = 0
        self._red_three_replacements_needed = []
        self._dealing_phase = True
        self._game_phase = "dealing"

        # Reset player state
        self._current_player = 0
        self._turn_phase = "draw"

        # Reset hand-specific state
        self._pile_frozen = False
        self._initial_meld_made = [False, False]
        self._black_three_blocks_next = False
        self._go_out_query_pending = False
        self._go_out_query_asker = -1
        self._go_out_approved = False
        self._partner_asked_this_turn = False
        self._hand_scores = [0, 0]

        # Preserve: _team_scores (cumulative), _target_score, _hand_number
        # Game is not terminal
        self._is_terminal = False
        self._game_over = False
        self._winning_team = -1

    def current_player(self):
        """Returns id of the next player to move, or TERMINAL if game is over."""
        if self._is_terminal:
            return pyspiel.PlayerId.TERMINAL

        # During dealing phase, chance player deals cards
        if self._dealing_phase:
            return pyspiel.PlayerId.CHANCE

        return self._current_player

    def _can_draw_stock(self):
        """Check if current player can draw from stock."""
        return len(self._stock) > 0

    def _can_take_pile(self):
        """Check if current player can take the discard pile."""
        if not self._discard_pile:
            return False

        # Black 3 blocks next player from taking pile
        if self._black_three_blocks_next:
            return False

        player = self._current_player
        team = player % 2
        top_card = self._discard_pile[-1]
        top_rank = rank_of(top_card)

        # Cannot take pile with black 3 on top
        if is_black_three(top_card):
            return False

        # Find matching natural cards in hand
        hand = self._hands[player]
        matching_naturals = []
        for card in hand:
            if not is_wild(card) and rank_of(card) == top_rank:
                matching_naturals.append(card)

        # Check if pile is frozen
        if self._is_pile_frozen():
            # Frozen pile requires two natural matching cards
            if len(matching_naturals) >= 2:
                return True
            return False
        else:
            # Unfrozen pile requires either:
            # 1. Two natural matching cards to form new meld
            # 2. One natural matching card if can add to existing team meld
            if len(matching_naturals) >= 2:
                return True

            # Check if we have existing meld for this rank
            if len(matching_naturals) >= 1:
                for meld in self._melds[team]:
                    if meld and meld.rank == top_rank:
                        return True

            return False

    def _is_pile_frozen(self):
        """Check if the discard pile is frozen."""
        player = self._current_player
        team = player % 2

        # Pile is frozen if team hasn't made initial meld
        if not self._initial_meld_made[team]:
            return True

        # Pile is frozen if it contains a wild card
        if self._pile_frozen:
            return True

        # Check if any card in pile is wild
        for card in self._discard_pile:
            if is_wild(card):
                return True

        return False

    def _can_create_meld(self, rank, card_ids):
        """Check if can create a new meld with given cards.

        Args:
            rank: Rank index (0-12) of the meld
            card_ids: List of card IDs to use in the meld

        Returns:
            True if meld can be created
        """
        player = self._current_player
        team = player % 2

        # Separate natural and wild cards
        natural_cards = []
        wild_cards = []
        for card_id in card_ids:
            if is_wild(card_id):
                wild_cards.append(card_id)
            else:
                # Check that natural cards match the rank
                if rank_of(card_id) != rank:
                    return False
                natural_cards.append(card_id)

        # Create proposed meld
        meld = Meld(rank=rank, natural_cards=natural_cards, wild_cards=wild_cards)

        # Check basic meld validity
        if not is_valid_meld(meld):
            return False

        # Check that team doesn't already have a meld of this rank
        for existing_meld in self._melds[team]:
            if existing_meld.rank == rank:
                return False

        # Check initial meld requirement if not yet made
        if not self._initial_meld_made[team]:
            # Use cumulative team score to determine threshold
            team_score = self._team_scores[team]

            # Check if this meld meets the requirement
            if not can_form_initial_meld([meld], team_score):
                return False

        return True

    def _can_add_to_meld(self, meld_idx, card_ids):
        """Check if can add cards to an existing meld.

        Args:
            meld_idx: Index of the meld in team's meld list
            card_ids: List of card IDs to add

        Returns:
            True if cards can be added
        """
        player = self._current_player
        team = player % 2

        # Check meld index is valid
        if meld_idx < 0 or meld_idx >= len(self._melds[team]):
            return False

        existing_meld = self._melds[team][meld_idx]

        # Separate natural and wild cards
        natural_cards = []
        wild_cards = []
        for card_id in card_ids:
            if is_wild(card_id):
                wild_cards.append(card_id)
            else:
                # Check that natural cards match the meld's rank
                if rank_of(card_id) != existing_meld.rank:
                    return False
                natural_cards.append(card_id)

        # Create updated meld
        updated_meld = Meld(
            rank=existing_meld.rank,
            natural_cards=existing_meld.natural_cards + natural_cards,
            wild_cards=existing_meld.wild_cards + wild_cards,
        )

        # Check that updated meld is still valid (enforces wild card limit)
        if not is_valid_meld(updated_meld):
            return False

        return True

    def _meets_initial_meld_requirement(self, proposed_melds):
        """Check if proposed melds meet initial meld requirement.

        Args:
            proposed_melds: List of Meld objects being created

        Returns:
            True if melds meet requirement
        """
        player = self._current_player
        team = player % 2

        # Use cumulative team score to determine threshold
        team_score = self._team_scores[team]

        return can_form_initial_meld(proposed_melds, team_score)

    def _update_canasta_count(self, team_idx):
        """Update canasta count for a team.

        Args:
            team_idx: Team index (0 or 1)
        """
        count = 0
        for meld in self._melds[team_idx]:
            if is_canasta(meld):
                count += 1
        self._canastas[team_idx] = count

    def _apply_create_meld(self, rank, card_ids):
        """Apply create meld action.

        Args:
            rank: Rank index of the meld
            card_ids: List of card IDs to use
        """
        player = self._current_player
        team = player % 2

        # Separate natural and wild cards
        natural_cards = []
        wild_cards = []
        for card_id in card_ids:
            if is_wild(card_id):
                wild_cards.append(card_id)
            else:
                natural_cards.append(card_id)

        # Create meld
        meld = Meld(rank=rank, natural_cards=natural_cards, wild_cards=wild_cards)

        # Add to team melds
        self._melds[team].append(meld)

        # Remove cards from hand
        for card_id in card_ids:
            if card_id in self._hands[player]:
                self._hands[player].remove(card_id)

        # Mark initial meld as made
        self._initial_meld_made[team] = True

        # Update canasta count
        self._update_canasta_count(team)

    def _apply_add_to_meld(self, meld_idx, card_ids):
        """Apply add to meld action.

        Args:
            meld_idx: Index of the meld to add to
            card_ids: List of card IDs to add
        """
        player = self._current_player
        team = player % 2

        # Get existing meld
        existing_meld = self._melds[team][meld_idx]

        # Separate natural and wild cards
        natural_cards = []
        wild_cards = []
        for card_id in card_ids:
            if is_wild(card_id):
                wild_cards.append(card_id)
            else:
                natural_cards.append(card_id)

        # Update meld
        existing_meld.natural_cards.extend(natural_cards)
        existing_meld.wild_cards.extend(wild_cards)

        # Remove cards from hand
        for card_id in card_ids:
            if card_id in self._hands[player]:
                self._hands[player].remove(card_id)

        # Update canasta count
        self._update_canasta_count(team)

    def _apply_skip_meld(self):
        """Apply skip meld action - advance to discard phase."""
        self._turn_phase = "discard"

    def _generate_meld_actions(self):
        """Generate all valid meld actions.

        Returns:
            List of action IDs for valid meld actions
        """
        player = self._current_player
        team = player % 2
        hand = self._hands[player]

        actions = []

        # Always can skip melding
        actions.append(ACTION_SKIP_MELD)

        # Generate CREATE_MELD actions
        # For each rank (0-12), try to form melds with combinations of cards
        for rank_idx in range(13):
            # Skip rank 1 (2s are wild) and rank 2 (3s cannot be melded normally)
            if rank_idx == 1 or rank_idx == 2:
                continue

            # Find cards of this rank in hand
            natural_cards = [c for c in hand if not is_wild(c) and rank_of(c) == rank_idx]
            wild_cards = [c for c in hand if is_wild(c)]

            # Try different combinations of natural and wild cards
            # Need at least 2 naturals, at most 3 wilds, at least 3 total
            for num_naturals in range(2, len(natural_cards) + 1):
                for num_wilds in range(0, min(len(wild_cards), 3) + 1):
                    if num_naturals + num_wilds < 3:
                        continue

                    # Create card combination
                    card_ids = natural_cards[:num_naturals] + wild_cards[:num_wilds]

                    # Check if this meld can be created
                    if self._can_create_meld(rank_idx, card_ids):
                        # Encode action: rank * 50 + combination index
                        action_id = ACTION_CREATE_MELD_START + rank_idx * 50 + num_naturals * 4 + num_wilds
                        if action_id <= ACTION_CREATE_MELD_END:
                            actions.append(action_id)

        # Generate ADD_TO_MELD actions
        for meld_idx, meld in enumerate(self._melds[team]):
            # Find cards that can be added to this meld
            natural_cards = [c for c in hand if not is_wild(c) and rank_of(c) == meld.rank]
            wild_cards = [c for c in hand if is_wild(c)]

            # Try adding individual cards or combinations
            # Add natural cards
            for num_naturals in range(1, len(natural_cards) + 1):
                card_ids = natural_cards[:num_naturals]
                if self._can_add_to_meld(meld_idx, card_ids):
                    action_id = ACTION_ADD_TO_MELD_START + meld_idx * 50 + num_naturals
                    if action_id <= ACTION_ADD_TO_MELD_END:
                        actions.append(action_id)

            # Add wild cards
            for num_wilds in range(1, min(len(wild_cards), 3 - len(meld.wild_cards)) + 1):
                card_ids = wild_cards[:num_wilds]
                if self._can_add_to_meld(meld_idx, card_ids):
                    action_id = ACTION_ADD_TO_MELD_START + meld_idx * 50 + 10 + num_wilds
                    if action_id <= ACTION_ADD_TO_MELD_END:
                        actions.append(action_id)

            # Add combinations of naturals and wilds
            for num_naturals in range(1, len(natural_cards) + 1):
                for num_wilds in range(1, min(len(wild_cards), 3 - len(meld.wild_cards)) + 1):
                    card_ids = natural_cards[:num_naturals] + wild_cards[:num_wilds]
                    if self._can_add_to_meld(meld_idx, card_ids):
                        action_id = ACTION_ADD_TO_MELD_START + meld_idx * 50 + 20 + num_naturals * 4 + num_wilds
                        if action_id <= ACTION_ADD_TO_MELD_END:
                            actions.append(action_id)

        return actions

    def _decode_create_meld_action(self, action_id):
        """Decode CREATE_MELD action to rank and card selection.

        Args:
            action_id: Action ID in range [ACTION_CREATE_MELD_START, ACTION_CREATE_MELD_END]

        Returns:
            Tuple of (rank, card_ids)
        """
        player = self._current_player
        hand = self._hands[player]

        offset = action_id - ACTION_CREATE_MELD_START
        rank = offset // 50
        combo_idx = offset % 50

        num_naturals = combo_idx // 4
        num_wilds = combo_idx % 4

        # Get cards from hand
        natural_cards = [c for c in hand if not is_wild(c) and rank_of(c) == rank]
        wild_cards = [c for c in hand if is_wild(c)]

        card_ids = natural_cards[:num_naturals] + wild_cards[:num_wilds]

        return rank, card_ids

    def _decode_add_to_meld_action(self, action_id):
        """Decode ADD_TO_MELD action to meld index and card selection.

        Args:
            action_id: Action ID in range [ACTION_ADD_TO_MELD_START, ACTION_ADD_TO_MELD_END]

        Returns:
            Tuple of (meld_idx, card_ids)
        """
        player = self._current_player
        team = player % 2
        hand = self._hands[player]

        offset = action_id - ACTION_ADD_TO_MELD_START
        meld_idx = offset // 50
        combo_idx = offset % 50

        if meld_idx >= len(self._melds[team]):
            return meld_idx, []

        meld = self._melds[team][meld_idx]

        # Decode combination
        natural_cards = [c for c in hand if not is_wild(c) and rank_of(c) == meld.rank]
        wild_cards = [c for c in hand if is_wild(c)]

        if combo_idx < 10:
            # Just naturals
            num_naturals = combo_idx
            card_ids = natural_cards[:num_naturals]
        elif combo_idx < 20:
            # Just wilds
            num_wilds = combo_idx - 10
            card_ids = wild_cards[:num_wilds]
        else:
            # Combination
            adjusted = combo_idx - 20
            num_naturals = adjusted // 4
            num_wilds = adjusted % 4
            card_ids = natural_cards[:num_naturals] + wild_cards[:num_wilds]

        return meld_idx, card_ids

    def _can_discard(self, card_id):
        """Check if can discard a specific card.

        Args:
            card_id: Card ID to discard

        Returns:
            True if card is in current player's hand
        """
        player = self._current_player
        return card_id in self._hands[player]

    def _is_valid_discard(self, card_id):
        """Check if a discard is valid (Classic Canasta rule).

        In Classic Canasta, all cards can be freely discarded.

        Args:
            card_id: Card ID to discard

        Returns:
            True if discard is valid
        """
        return self._can_discard(card_id)

    def _apply_discard(self, card_id):
        """Apply discard action.

        Args:
            card_id: Card ID to discard
        """
        player = self._current_player

        # Remove card from hand
        if card_id in self._hands[player]:
            self._hands[player].remove(card_id)

        # Add card to top of discard pile
        self._discard_pile.append(card_id)

        # Check if wild card (freezes pile)
        if is_wild(card_id):
            self._pile_frozen = True

        # Check if black 3 (blocks next player)
        if is_black_three(card_id):
            self._black_three_blocks_next = True

        # Advance turn phase to draw
        self._turn_phase = "draw"

        # Advance to next player
        self._current_player = (self._current_player + 1) % self._num_players

        # Reset going out flags for new turn
        self._go_out_approved = False
        self._partner_asked_this_turn = False

    def _generate_discard_actions(self):
        """Generate all valid discard actions.

        Returns:
            List of action IDs for valid discard actions
        """
        player = self._current_player
        hand = self._hands[player]

        actions = []

        # Generate discard action for each card in hand
        for card_id in hand:
            if self._is_valid_discard(card_id):
                action_id = ACTION_DISCARD_START + card_id
                actions.append(action_id)

        return actions

    def _can_ask_partner_go_out(self):
        """Check if can ask partner for permission to go out.

        Returns:
            True if in meld phase and hasn't asked this turn
        """
        if self._turn_phase != "meld":
            return False

        if self._partner_asked_this_turn:
            return False

        if self._go_out_query_pending:
            return False

        player = self._current_player
        team = player % 2

        # Must have at least one canasta
        if self._canastas[team] < 1:
            return False

        # Must be able to meld all but one card
        if not self._can_meld_all_but_one():
            return False

        return True

    def _can_go_out(self):
        """Check if can go out.

        Returns:
            True if conditions are met and partner approved (or concealed)
        """
        player = self._current_player
        team = player % 2

        # Must have at least one canasta (Classic Canasta rule)
        if self._canastas[team] < 1:
            return False

        # Must be able to meld all but one card
        if not self._can_meld_all_but_one():
            return False

        # If concealed, no partner permission needed
        if self._is_concealed_go_out():
            return True

        # Otherwise, must have partner approval
        return self._go_out_approved

    def _can_meld_all_but_one(self):
        """Check if can meld all cards except one for discard.

        Returns:
            True if all but one card can be melded
        """
        player = self._current_player
        team = player % 2
        hand = self._hands[player].copy()

        # Try each card as the potential discard
        for discard_candidate in hand:
            remaining_cards = [c for c in hand if c != discard_candidate]

            # Check if can meld all remaining cards
            if self._can_meld_all_cards(remaining_cards, team):
                return True

        return False

    def _can_meld_all_cards(self, cards, team):
        """Check if all given cards can be melded.

        Args:
            cards: List of card IDs to try melding
            team: Team index

        Returns:
            True if all cards can be melded
        """
        # Group cards by rank
        cards_by_rank = {}
        wild_cards = []

        for card in cards:
            if is_wild(card):
                wild_cards.append(card)
            else:
                r = rank_of(card)
                if r not in cards_by_rank:
                    cards_by_rank[r] = []
                cards_by_rank[r].append(card)

        # Try to meld all natural cards
        for rank_idx, rank_cards in cards_by_rank.items():
            # Check if team already has a meld for this rank
            existing_meld = None
            for meld in self._melds[team]:
                if meld.rank == rank_idx:
                    existing_meld = meld
                    break

            if existing_meld:
                # Can add to existing meld
                continue
            else:
                # Need to form new meld - requires at least 2 naturals
                if len(rank_cards) < 2:
                    # Try to use wilds, but need at least 2 naturals
                    return False

        # All cards can be melded
        return True

    def _is_concealed_go_out(self):
        """Check if going out would be concealed.

        Returns:
            True if team has no prior melds
        """
        player = self._current_player
        team = player % 2

        # Concealed means team has no melds yet
        return len(self._melds[team]) == 0

    def _apply_ask_partner(self):
        """Apply ask partner permission action."""
        player = self._current_player

        # Set query state
        self._go_out_query_pending = True
        self._go_out_query_asker = player
        self._partner_asked_this_turn = True

        # Switch to partner (partner is player + 2 mod 4)
        self._current_player = (player + 2) % self._num_players

    def _apply_answer_yes(self):
        """Apply partner answers yes action."""
        # Approve going out
        self._go_out_approved = True
        self._go_out_query_pending = False

        # Return control to asker
        self._current_player = self._go_out_query_asker

    def _apply_answer_no(self):
        """Apply partner answers no action."""
        # Deny going out
        self._go_out_approved = False
        self._go_out_query_pending = False

        # Return control to asker
        self._current_player = self._go_out_query_asker

    def _finalize_game(self, winning_team=-1, went_out_concealed=False):
        """Calculate final scores and set game to terminal state.

        Args:
            winning_team: Team that went out (0 or 1), or -1 if stock exhausted
            went_out_concealed: Whether going out was concealed
        """
        for t in [0, 1]:
            # Collect all melded cards for this team
            melded_cards = []
            for meld in self._melds[t]:
                melded_cards.extend(meld.natural_cards)
                melded_cards.extend(meld.wild_cards)

            # Collect cards in hands for this team (players t and t+2)
            hand_cards = []
            hand_cards.extend(self._hands[t])
            hand_cards.extend(self._hands[t + 2])

            # Count red threes
            red_three_count = len(self._red_threes[t])

            # Check if this team went out
            went_out = (winning_team >= 0 and t == winning_team)

            # Calculate hand score
            score = calculate_hand_score(
                melded_cards=melded_cards,
                melds=self._melds[t],
                red_three_count=red_three_count,
                hand_cards=hand_cards,
                went_out=went_out,
                concealed=went_out_concealed if went_out else False,
            )

            self._hand_scores[t] = score
            self._team_scores[t] += score

        # Set returns (teammates share team scores)
        # Players 0 and 2 are Team 0, players 1 and 3 are Team 1
        self._returns[0] = float(self._team_scores[0])
        self._returns[2] = float(self._team_scores[0])
        self._returns[1] = float(self._team_scores[1])
        self._returns[3] = float(self._team_scores[1])

        # Check if either team has reached the target score
        if self._team_scores[0] >= self._target_score or self._team_scores[1] >= self._target_score:
            # Game ends - determine winning team
            if self._team_scores[0] > self._team_scores[1]:
                self._winning_team = 0
            elif self._team_scores[1] > self._team_scores[0]:
                self._winning_team = 1
            else:
                # Tie - team that went out wins (if any)
                if winning_team >= 0:
                    self._winning_team = winning_team
                else:
                    # Stock exhausted tie - use team 0 as default
                    self._winning_team = 0

            # Set game over
            self._game_over = True
            self._is_terminal = True
        else:
            # Neither team has reached target score - start new hand
            self._start_new_hand()

    def _apply_go_out(self):
        """Apply go out action - end the game."""
        player = self._current_player
        team = player % 2

        # Meld all remaining cards (except one for discard)
        hand = self._hands[player].copy()

        # Find which card to discard
        discard_card = None
        for card in hand:
            remaining = [c for c in hand if c != card]
            if self._can_meld_all_cards(remaining, team):
                discard_card = card
                break

        if discard_card is None:
            # Shouldn't happen if validation correct, but handle gracefully
            discard_card = hand[0] if hand else None

        # Meld all cards except discard
        for card in hand:
            if card == discard_card:
                continue

            # Try to add to existing meld or create new one
            if is_wild(card):
                # Add wild to any compatible meld
                added = False
                for meld in self._melds[team]:
                    if len(meld.wild_cards) < 3:
                        meld.wild_cards.append(card)
                        added = True
                        break
            else:
                r = rank_of(card)
                # Find or create meld for this rank
                found = False
                for meld in self._melds[team]:
                    if meld.rank == r:
                        meld.natural_cards.append(card)
                        found = True
                        break

                if not found:
                    # Create new meld (need to find other cards of same rank)
                    # This is simplified - actual implementation would group cards first
                    pass

        # Clear hand
        self._hands[player] = []

        # Discard last card if exists
        if discard_card is not None:
            self._discard_pile.append(discard_card)

        # Update canasta count
        self._update_canasta_count(team)

        # Calculate scores and finalize game
        concealed = self._is_concealed_go_out()
        self._finalize_game(winning_team=team, went_out_concealed=concealed)

    def _legal_actions(self, player):
        """Returns a list of legal actions for the given player."""
        if player == pyspiel.PlayerId.CHANCE:
            # During dealing, any card remaining in deck is a legal action
            return list(range(len(self._deck)))

        # During play phase
        actions = []

        if self._turn_phase == "draw":
            # Draw from stock
            if self._can_draw_stock():
                actions.append(ACTION_DRAW_STOCK)

            # Take pile
            if self._can_take_pile():
                actions.append(ACTION_TAKE_PILE)

            # If no legal draw actions, game ends (stock exhausted)
            if not actions:
                # End game with current scores - no team went out
                self._finalize_game(winning_team=-1, went_out_concealed=False)
                return []

            return actions

        # Handle partner query
        if self._go_out_query_pending:
            # Partner must answer yes or no
            return [ACTION_ANSWER_GO_OUT_YES, ACTION_ANSWER_GO_OUT_NO]

        if self._turn_phase == "meld":
            # Generate meld actions
            actions = self._generate_meld_actions()

            # Add ask partner action if eligible
            if self._can_ask_partner_go_out():
                actions.append(ACTION_ASK_PARTNER_GO_OUT)

            return actions

        if self._turn_phase == "discard":
            # Check if hand is empty (shouldn't happen, but handle gracefully)
            player = self._current_player
            if not self._hands[player]:
                # Hand is empty - game should end
                # This can happen if all cards were melded
                team = player % 2
                self._finalize_game(winning_team=team, went_out_concealed=False)
                return []

            # Generate discard actions
            actions = self._generate_discard_actions()

            # Add go out action if eligible
            if self._can_go_out():
                actions.append(ACTION_GO_OUT)

            return actions

        # Placeholder for other phases
        # This will be expanded in future beads
        if not actions:
            actions = [0]  # Placeholder

        return actions

    def chance_outcomes(self):
        """Returns the possible chance outcomes and their probabilities."""
        assert self.is_chance_node()

        # During dealing, each remaining card has equal probability
        num_cards = len(self._deck)
        if num_cards == 0:
            return []

        prob = 1.0 / num_cards
        return [(card_idx, prob) for card_idx in range(num_cards)]

    def _apply_draw_stock(self):
        """Draw top card from stock pile."""
        if not self._stock:
            return

        player = self._current_player
        team = player % 2

        # Draw card from stock (from the front of the list, index 0)
        card = self._stock.pop(0)
        self._hands[player].append(card)

        # Auto-replace red 3s
        while card in self._hands[player] and is_red_three(card):
            self._hands[player].remove(card)
            self._red_threes[team].append(card)

            # Draw replacement if stock not empty
            if self._stock:
                card = self._stock.pop(0)
                self._hands[player].append(card)
            else:
                break

        # Clear black 3 blocking (only blocks immediate next player)
        self._black_three_blocks_next = False

        # Advance to meld phase
        self._turn_phase = "meld"

    def _apply_take_pile(self):
        """Take entire discard pile."""
        player = self._current_player
        team = player % 2

        # Add all cards from pile to hand
        for card in self._discard_pile:
            self._hands[player].append(card)

        # Process red 3s
        red_threes = [card for card in self._hands[player] if is_red_three(card)]
        for red_three in red_threes:
            self._hands[player].remove(red_three)
            self._red_threes[team].append(red_three)

            # No replacement for red 3s from pile (only from stock)

        # Clear discard pile
        self._discard_pile = []

        # Clear black 3 blocking
        self._black_three_blocks_next = False

        # Advance to meld phase
        self._turn_phase = "meld"

    def _apply_action(self, action):
        """Applies the specified action to the state."""
        if self.is_chance_node():
            # Dealing phase: action is an index into the remaining deck
            card = self._deck.pop(action)

            # Determine which player gets the card
            player_idx = self._cards_dealt // _HAND_SIZE
            if player_idx < self._num_players:
                self._hands[player_idx].append(card)

                # Check if this is a red 3
                if is_red_three(card):
                    # Remove from hand and set aside for the player's team
                    self._hands[player_idx].remove(card)
                    team_idx = player_idx % 2  # Teams are 0,2 vs 1,3
                    self._red_threes[team_idx].append(card)

                    # Mark that this player needs a replacement card
                    self._red_three_replacements_needed.append((player_idx, card))

            self._cards_dealt += 1

            # Check if initial dealing is complete (44 cards dealt)
            if self._cards_dealt >= self._total_cards_to_deal:
                # Now handle red 3 replacements
                while self._red_three_replacements_needed and self._deck:
                    player_idx, _ = self._red_three_replacements_needed.pop(0)

                    # Draw replacement card from deck
                    replacement = self._deck.pop(0)
                    self._hands[player_idx].append(replacement)

                    # Check if replacement is also a red 3
                    if is_red_three(replacement):
                        self._hands[player_idx].remove(replacement)
                        team_idx = player_idx % 2
                        self._red_threes[team_idx].append(replacement)
                        # Need another replacement
                        self._red_three_replacements_needed.append((player_idx, replacement))

                # All replacements done, transition to play phase
                if not self._red_three_replacements_needed:
                    self._dealing_phase = False
                    self._game_phase = "playing"

                    # Place one card on discard pile
                    if self._deck:
                        self._discard_pile.append(self._deck.pop(0))

                    # Remaining cards form the stock
                    self._stock = self._deck
                    self._deck = []

                    # Start with player 0
                    self._current_player = 0
        else:
            # Handle play actions
            if action == ACTION_DRAW_STOCK:
                self._apply_draw_stock()
            elif action == ACTION_TAKE_PILE:
                self._apply_take_pile()
            elif action == ACTION_SKIP_MELD:
                self._apply_skip_meld()
            elif ACTION_CREATE_MELD_START <= action <= ACTION_CREATE_MELD_END:
                rank, card_ids = self._decode_create_meld_action(action)
                self._apply_create_meld(rank, card_ids)
            elif ACTION_ADD_TO_MELD_START <= action <= ACTION_ADD_TO_MELD_END:
                meld_idx, card_ids = self._decode_add_to_meld_action(action)
                self._apply_add_to_meld(meld_idx, card_ids)
            elif ACTION_DISCARD_START <= action <= ACTION_DISCARD_END:
                card_id = action - ACTION_DISCARD_START
                self._apply_discard(card_id)
            elif action == ACTION_ASK_PARTNER_GO_OUT:
                self._apply_ask_partner()
            elif action == ACTION_ANSWER_GO_OUT_YES:
                self._apply_answer_yes()
            elif action == ACTION_ANSWER_GO_OUT_NO:
                self._apply_answer_no()
            elif action == ACTION_GO_OUT:
                self._apply_go_out()
            else:
                # Placeholder for other actions
                pass

    def _action_to_string(self, player, action):
        """Action -> string representation."""
        if player == pyspiel.PlayerId.CHANCE:
            return f"Deal card {action}"

        if action == ACTION_DRAW_STOCK:
            return "Draw from stock"
        elif action == ACTION_TAKE_PILE:
            return "Take discard pile"
        elif action == ACTION_SKIP_MELD:
            return "Skip meld"
        elif ACTION_CREATE_MELD_START <= action <= ACTION_CREATE_MELD_END:
            rank, card_ids = self._decode_create_meld_action(action)
            from canasta.cards import RANKS
            return f"Create meld of {RANKS[rank]}s with {len(card_ids)} cards"
        elif ACTION_ADD_TO_MELD_START <= action <= ACTION_ADD_TO_MELD_END:
            meld_idx, card_ids = self._decode_add_to_meld_action(action)
            return f"Add {len(card_ids)} cards to meld {meld_idx}"
        elif ACTION_DISCARD_START <= action <= ACTION_DISCARD_END:
            card_id = action - ACTION_DISCARD_START
            from canasta.cards import card_id_to_rank_suit
            rank, suit = card_id_to_rank_suit(card_id)
            if suit:
                return f"Discard {rank} of {suit}"
            else:
                return f"Discard {rank}"
        elif action == ACTION_ASK_PARTNER_GO_OUT:
            return "Ask partner: May I go out?"
        elif action == ACTION_ANSWER_GO_OUT_YES:
            return "Partner answers: Yes, go out"
        elif action == ACTION_ANSWER_GO_OUT_NO:
            return "Partner answers: No, don't go out"
        elif action == ACTION_GO_OUT:
            return "Go out"

        return f"Action {action}"

    def is_terminal(self):
        """Returns True if the game is over."""
        return self._is_terminal

    def returns(self):
        """Total reward for each player over the course of the game so far."""
        return self._returns

    def observation_tensor(self, player=None):
        """Return observation tensor for the specified player.

        Args:
            player: Player index (0-3). If None, uses current player.

        Returns:
            numpy array containing the observation tensor
        """
        if player is None:
            player = self.current_player()
            if player < 0:  # CHANCE or TERMINAL
                player = 0

        observer = self._game.make_py_observer()
        observer.set_from(self, player)
        return observer.tensor.copy()

    def information_state_tensor(self, player=None):
        """Return information state tensor for the specified player.

        Args:
            player: Player index (0-3). If None, uses current player.

        Returns:
            numpy array containing the information state tensor
        """
        if player is None:
            player = self.current_player()
            if player < 0:  # CHANCE or TERMINAL
                player = 0

        observer = self._game.make_py_observer()
        observer.set_from(self, player)
        return observer.tensor.copy()

    def serialize(self):
        """Serialize the state to a string.

        Returns:
            JSON string containing the complete game state
        """
        import json

        # Serialize melds
        melds_data = []
        for team_melds in self._melds:
            team_data = []
            for meld in team_melds:
                team_data.append({
                    'rank': meld.rank,
                    'natural_cards': meld.natural_cards.copy(),
                    'wild_cards': meld.wild_cards.copy()
                })
            melds_data.append(team_data)

        state_dict = {
            'hands': [hand.copy() for hand in self._hands],
            'stock': self._stock.copy(),
            'discard_pile': self._discard_pile.copy(),
            'melds': melds_data,
            'canastas': self._canastas.copy(),
            'red_threes': [rt.copy() for rt in self._red_threes],
            'cards_dealt': self._cards_dealt,
            'red_three_replacements_needed': self._red_three_replacements_needed.copy(),
            'current_player': self._current_player,
            'is_terminal': self._is_terminal,
            'returns': self._returns.copy(),
            'team_scores': self._team_scores.copy(),
            'hand_scores': self._hand_scores.copy(),
            'hand_number': self._hand_number,
            'target_score': self._target_score,
            'dealing_phase': self._dealing_phase,
            'game_phase': self._game_phase,
            'turn_phase': self._turn_phase,
            'pile_frozen': self._pile_frozen,
            'initial_meld_made': self._initial_meld_made.copy(),
            'black_three_blocks_next': self._black_three_blocks_next,
            'go_out_query_pending': self._go_out_query_pending,
            'go_out_query_asker': self._go_out_query_asker,
            'go_out_approved': self._go_out_approved,
            'partner_asked_this_turn': self._partner_asked_this_turn,
            'game_over': self._game_over,
            'winning_team': self._winning_team,
        }

        return json.dumps(state_dict)

    def deserialize(self, data):
        """Deserialize state from a string.

        Args:
            data: JSON string containing the game state
        """
        import json
        state_dict = json.loads(data)

        # Restore basic state
        self._hands = [list(hand) for hand in state_dict['hands']]
        self._stock = list(state_dict['stock'])
        self._discard_pile = list(state_dict['discard_pile'])
        self._canastas = list(state_dict['canastas'])
        self._red_threes = [list(rt) for rt in state_dict['red_threes']]
        self._cards_dealt = state_dict['cards_dealt']
        self._red_three_replacements_needed = list(state_dict['red_three_replacements_needed'])
        self._current_player = state_dict['current_player']
        self._is_terminal = state_dict['is_terminal']
        self._returns = list(state_dict['returns'])
        self._team_scores = list(state_dict['team_scores'])
        self._hand_scores = list(state_dict['hand_scores'])
        self._hand_number = state_dict['hand_number']
        self._target_score = state_dict['target_score']
        self._dealing_phase = state_dict['dealing_phase']
        self._game_phase = state_dict['game_phase']
        self._turn_phase = state_dict['turn_phase']
        self._pile_frozen = state_dict['pile_frozen']
        self._initial_meld_made = list(state_dict['initial_meld_made'])
        self._black_three_blocks_next = state_dict['black_three_blocks_next']
        self._go_out_query_pending = state_dict['go_out_query_pending']
        self._go_out_query_asker = state_dict['go_out_query_asker']
        self._go_out_approved = state_dict['go_out_approved']
        self._partner_asked_this_turn = state_dict['partner_asked_this_turn']
        self._game_over = state_dict['game_over']
        self._winning_team = state_dict['winning_team']

        # Restore melds
        self._melds = [[], []]
        for team_idx, team_data in enumerate(state_dict['melds']):
            for meld_data in team_data:
                meld = Meld(
                    rank=meld_data['rank'],
                    natural_cards=list(meld_data['natural_cards']),
                    wild_cards=list(meld_data['wild_cards'])
                )
                self._melds[team_idx].append(meld)

    def clone(self):
        """Create a deep copy of this state.

        Returns:
            A new CanastaState instance with copied data
        """
        cloned = CanastaState(self._game)

        # Copy all state variables
        cloned._hands = [hand.copy() for hand in self._hands]
        cloned._stock = self._stock.copy()
        cloned._discard_pile = self._discard_pile.copy()
        cloned._canastas = self._canastas.copy()
        cloned._red_threes = [rt.copy() for rt in self._red_threes]
        cloned._cards_dealt = self._cards_dealt
        cloned._total_cards_to_deal = self._total_cards_to_deal
        cloned._red_three_replacements_needed = self._red_three_replacements_needed.copy()
        cloned._current_player = self._current_player
        cloned._is_terminal = self._is_terminal
        cloned._returns = self._returns.copy()
        cloned._team_scores = self._team_scores.copy()
        cloned._hand_scores = self._hand_scores.copy()
        cloned._hand_number = self._hand_number
        cloned._target_score = self._target_score
        cloned._dealing_phase = self._dealing_phase
        cloned._game_phase = self._game_phase
        cloned._turn_phase = self._turn_phase
        cloned._pile_frozen = self._pile_frozen
        cloned._initial_meld_made = self._initial_meld_made.copy()
        cloned._black_three_blocks_next = self._black_three_blocks_next
        cloned._go_out_query_pending = self._go_out_query_pending
        cloned._go_out_query_asker = self._go_out_query_asker
        cloned._go_out_approved = self._go_out_approved
        cloned._partner_asked_this_turn = self._partner_asked_this_turn
        cloned._game_over = self._game_over
        cloned._winning_team = self._winning_team

        # Deep copy melds
        cloned._melds = [[], []]
        for team_idx, team_melds in enumerate(self._melds):
            for meld in team_melds:
                cloned_meld = Meld(
                    rank=meld.rank,
                    natural_cards=meld.natural_cards.copy(),
                    wild_cards=meld.wild_cards.copy()
                )
                cloned._melds[team_idx].append(cloned_meld)

        # Copy deck (might be empty after dealing)
        cloned._deck = self._deck.copy() if hasattr(self, '_deck') else []

        return cloned

    def __str__(self):
        """String representation of the current game state."""
        s = []
        s.append(f"Phase: {self._game_phase}")
        s.append(f"Current player: {self.current_player()}")

        if self._game_phase == "dealing":
            s.append(f"Cards dealt: {self._cards_dealt}/{self._total_cards_to_deal}")
        else:
            s.append(f"Stock: {len(self._stock)} cards")
            s.append(f"Discard: {len(self._discard_pile)} cards")
            for i, hand in enumerate(self._hands):
                s.append(f"Player {i}: {len(hand)} cards")

        return "\n".join(s)




# Register the game with OpenSpiel
pyspiel.register_game(_GAME_TYPE, CanastaGame)
