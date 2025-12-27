"""Tests for canasta/ui/state_view.py - State extraction."""

import pytest

from canasta.ui.state_view import (
    StateView,
    MeldView,
    extract_state_view,
)
from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
)


class TestMeldView:
    """Tests for MeldView dataclass."""

    def test_total_cards(self):
        """AC-10.1: MeldView.total_cards returns correct count."""
        meld = MeldView(
            rank=0,
            natural_cards=[1, 2, 3],
            wild_cards=[100, 101],
        )
        assert meld.total_cards == 5

    def test_all_cards(self):
        """MeldView.all_cards returns all cards."""
        meld = MeldView(
            rank=0,
            natural_cards=[1, 2, 3],
            wild_cards=[100, 101],
        )
        assert meld.all_cards == [1, 2, 3, 100, 101]

    def test_canasta_flags(self):
        """MeldView canasta flags are stored correctly."""
        meld = MeldView(
            rank=0,
            natural_cards=[1, 2, 3, 4, 5, 6, 7],
            wild_cards=[],
            is_canasta=True,
            is_natural_canasta=True,
            is_mixed_canasta=False,
        )
        assert meld.is_canasta
        assert meld.is_natural_canasta
        assert not meld.is_mixed_canasta


class TestStateView:
    """Tests for StateView dataclass."""

    def test_hand_count(self):
        """AC-10.2: hand_count returns correct value."""
        view = StateView(
            hands=[[1, 2, 3], [4, 5], [6, 7, 8, 9], []]
        )
        assert view.hand_count(0) == 3
        assert view.hand_count(1) == 2
        assert view.hand_count(2) == 4
        assert view.hand_count(3) == 0

    def test_hand_count_invalid_player(self):
        """hand_count returns 0 for invalid player."""
        view = StateView()
        assert view.hand_count(5) == 0
        assert view.hand_count(-1) == 0

    def test_team_of(self):
        """AC-10.3: team_of returns correct team."""
        view = StateView()
        assert view.team_of(0) == 0
        assert view.team_of(1) == 1
        assert view.team_of(2) == 0
        assert view.team_of(3) == 1

    def test_partner_of(self):
        """AC-10.4: partner_of returns correct partner."""
        view = StateView()
        assert view.partner_of(0) == 2
        assert view.partner_of(1) == 3
        assert view.partner_of(2) == 0
        assert view.partner_of(3) == 1


class TestExtractStateView:
    """Tests for extract_state_view function."""

    def test_extract_early_game_hands(self):
        """AC-10.5: Hands are extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        # All players should have 11 cards
        assert view.hand_count(0) == 11
        assert view.hand_count(1) == 11
        assert view.hand_count(2) == 11
        assert view.hand_count(3) == 11

    def test_extract_stock_count(self):
        """AC-10.6: Stock count is extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        # Stock should have cards after dealing
        assert view.stock_count > 0

    def test_extract_discard_pile(self):
        """AC-10.7: Discard pile is extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        # Early game has initial discard
        assert len(view.discard_pile) == 1
        assert view.discard_top is not None
        assert view.discard_top == view.discard_pile[-1]

    def test_extract_melds_empty(self):
        """AC-10.8: Empty melds extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        # Early game has no melds
        assert len(view.melds[0]) == 0
        assert len(view.melds[1]) == 0

    def test_extract_melds_mid_game(self):
        """Melds extracted with correct structure."""
        state = create_mid_game_state()
        view = extract_state_view(state)

        # Mid game has melds for both teams
        assert len(view.melds[0]) > 0
        assert len(view.melds[1]) > 0

        # Check meld structure
        team0_meld = view.melds[0][0]
        assert isinstance(team0_meld, MeldView)
        assert team0_meld.rank == 0  # Aces
        assert len(team0_meld.natural_cards) > 0

    def test_extract_canastas(self):
        """Canasta melds have correct flags."""
        state = create_canasta_state()
        view = extract_state_view(state)

        # Find natural canasta (Team 0)
        team0_melds = view.melds[0]
        assert len(team0_melds) > 0
        natural_canasta = team0_melds[0]
        assert natural_canasta.is_canasta
        assert natural_canasta.is_natural_canasta
        assert not natural_canasta.is_mixed_canasta

        # Find mixed canasta (Team 1)
        team1_melds = view.melds[1]
        assert len(team1_melds) > 0
        mixed_canasta = team1_melds[0]
        assert mixed_canasta.is_canasta
        assert mixed_canasta.is_mixed_canasta
        assert not mixed_canasta.is_natural_canasta

    def test_extract_red_threes(self):
        """AC-10.9: Red threes extracted correctly."""
        state = create_red_threes_state()
        view = extract_state_view(state)

        # Both teams should have red threes
        assert len(view.red_threes[0]) == 2
        assert len(view.red_threes[1]) == 2

    def test_extract_scores(self):
        """Scores extracted correctly."""
        state = create_terminal_state()
        view = extract_state_view(state)

        # Terminal state has final scores
        assert view.team_scores[0] > 0
        assert view.team_scores[1] > 0

    def test_extract_frozen_pile(self):
        """Frozen pile flag extracted correctly."""
        state = create_frozen_pile_state()
        view = extract_state_view(state)

        assert view.pile_frozen is True

    def test_extract_current_player(self):
        """Current player extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        assert view.current_player == 0

    def test_extract_turn_phase(self):
        """Turn phase extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        assert view.turn_phase == "draw"

    def test_extract_game_phase(self):
        """Game phase extracted correctly."""
        state = create_early_game_state()
        view = extract_state_view(state)

        assert view.game_phase == "playing"

    def test_extract_terminal_state(self):
        """Terminal state extracted correctly."""
        state = create_terminal_state()
        view = extract_state_view(state)

        assert view.is_terminal is True
        assert view.winning_team == 0
        assert view.current_player == -1

    def test_extract_initial_meld_made(self):
        """Initial meld flags extracted correctly."""
        state = create_mid_game_state()
        view = extract_state_view(state)

        # Mid game has initial melds for both teams
        assert view.initial_meld_made[0] is True
        assert view.initial_meld_made[1] is True

    def test_extract_canasta_counts(self):
        """Canasta counts extracted correctly."""
        state = create_canasta_state()
        view = extract_state_view(state)

        assert view.canastas[0] == 1
        assert view.canastas[1] == 1
