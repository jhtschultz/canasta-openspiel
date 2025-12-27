"""Tests for Canasta UI fixtures.

These tests verify that the fixture states are:
1. Deterministic (same output every time)
2. Valid CanastaState objects
3. Have the expected properties for each scenario
"""

import pytest
import pyspiel

# Import fixtures
from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
    get_all_fixtures,
)
from canasta.cards import is_wild, is_red_three, NUM_CARDS
from canasta.melds import is_canasta, is_natural_canasta, is_mixed_canasta


class TestFixtureDeterminism:
    """Test that fixtures produce deterministic results."""

    def test_early_game_state_deterministic(self):
        """Early game state should be identical on repeated calls."""
        state1 = create_early_game_state()
        state2 = create_early_game_state()

        for player_idx in range(4):
            assert state1._hands[player_idx] == state2._hands[player_idx]

        assert state1._discard_pile == state2._discard_pile
        assert state1._stock == state2._stock

    def test_mid_game_state_deterministic(self):
        """Mid game state should be identical on repeated calls."""
        state1 = create_mid_game_state()
        state2 = create_mid_game_state()

        for player_idx in range(4):
            assert state1._hands[player_idx] == state2._hands[player_idx]

        for team_idx in range(2):
            assert len(state1._melds[team_idx]) == len(state2._melds[team_idx])
            for i, meld in enumerate(state1._melds[team_idx]):
                assert meld.rank == state2._melds[team_idx][i].rank
                assert meld.natural_cards == state2._melds[team_idx][i].natural_cards
                assert meld.wild_cards == state2._melds[team_idx][i].wild_cards

    def test_canasta_state_deterministic(self):
        """Canasta state should be identical on repeated calls."""
        state1 = create_canasta_state()
        state2 = create_canasta_state()

        assert state1._canastas == state2._canastas

    def test_frozen_pile_state_deterministic(self):
        """Frozen pile state should be identical on repeated calls."""
        state1 = create_frozen_pile_state()
        state2 = create_frozen_pile_state()

        assert state1._discard_pile == state2._discard_pile
        assert state1._pile_frozen == state2._pile_frozen

    def test_red_threes_state_deterministic(self):
        """Red threes state should be identical on repeated calls."""
        state1 = create_red_threes_state()
        state2 = create_red_threes_state()

        assert state1._red_threes == state2._red_threes

    def test_terminal_state_deterministic(self):
        """Terminal state should be identical on repeated calls."""
        state1 = create_terminal_state()
        state2 = create_terminal_state()

        assert state1._team_scores == state2._team_scores
        assert state1._returns == state2._returns
        assert state1._winning_team == state2._winning_team


class TestEarlyGameState:
    """Tests for create_early_game_state fixture."""

    def test_phase_is_playing(self):
        """Early game should be in playing phase."""
        state = create_early_game_state()
        assert state._game_phase == "playing"
        assert state._dealing_phase is False

    def test_all_hands_have_11_cards(self):
        """Each player should have 11 cards."""
        state = create_early_game_state()
        for player_idx in range(4):
            assert len(state._hands[player_idx]) == 11, f"Player {player_idx} should have 11 cards"

    def test_no_melds(self):
        """No melds should exist in early game."""
        state = create_early_game_state()
        assert state._melds[0] == []
        assert state._melds[1] == []
        assert state._canastas == [0, 0]

    def test_empty_discard_except_initial(self):
        """Discard pile should have only initial card."""
        state = create_early_game_state()
        assert len(state._discard_pile) == 1

    def test_no_red_threes(self):
        """No red threes in early game fixture."""
        state = create_early_game_state()
        assert state._red_threes[0] == []
        assert state._red_threes[1] == []

    def test_initial_meld_not_made(self):
        """Neither team has made initial meld."""
        state = create_early_game_state()
        assert state._initial_meld_made == [False, False]

    def test_current_player_is_zero(self):
        """Current player should be 0."""
        state = create_early_game_state()
        assert state.current_player() == 0

    def test_all_cards_accounted_for(self):
        """All 108 cards should be accounted for."""
        state = create_early_game_state()
        total = 0
        for hand in state._hands:
            total += len(hand)
        total += len(state._discard_pile)
        total += len(state._stock)
        for rt in state._red_threes:
            total += len(rt)

        assert total == NUM_CARDS


class TestMidGameState:
    """Tests for create_mid_game_state fixture."""

    def test_both_teams_have_melds(self):
        """Both teams should have made melds."""
        state = create_mid_game_state()
        assert len(state._melds[0]) > 0
        assert len(state._melds[1]) > 0

    def test_initial_melds_made(self):
        """Both teams should have made initial melds."""
        state = create_mid_game_state()
        assert state._initial_meld_made == [True, True]

    def test_hands_smaller_than_11(self):
        """Hands should have fewer cards than initial deal."""
        state = create_mid_game_state()
        for player_idx in range(4):
            assert len(state._hands[player_idx]) < 11

    def test_discard_pile_has_multiple_cards(self):
        """Discard pile should have multiple cards."""
        state = create_mid_game_state()
        assert len(state._discard_pile) > 1


class TestCanastaState:
    """Tests for create_canasta_state fixture."""

    def test_team_0_has_natural_canasta(self):
        """Team 0 should have a natural canasta."""
        state = create_canasta_state()
        assert state._canastas[0] >= 1

        # Find a natural canasta in Team 0's melds
        has_natural = False
        for meld in state._melds[0]:
            if is_natural_canasta(meld):
                has_natural = True
                break
        assert has_natural, "Team 0 should have a natural canasta"

    def test_team_1_has_mixed_canasta(self):
        """Team 1 should have a mixed canasta."""
        state = create_canasta_state()
        assert state._canastas[1] >= 1

        # Find a mixed canasta in Team 1's melds
        has_mixed = False
        for meld in state._melds[1]:
            if is_mixed_canasta(meld):
                has_mixed = True
                break
        assert has_mixed, "Team 1 should have a mixed canasta"

    def test_natural_canasta_has_no_wilds(self):
        """Natural canasta should have no wild cards."""
        state = create_canasta_state()
        for meld in state._melds[0]:
            if is_natural_canasta(meld):
                assert len(meld.wild_cards) == 0

    def test_mixed_canasta_has_wilds(self):
        """Mixed canasta should have wild cards."""
        state = create_canasta_state()
        for meld in state._melds[1]:
            if is_mixed_canasta(meld):
                assert len(meld.wild_cards) > 0


class TestFrozenPileState:
    """Tests for create_frozen_pile_state fixture."""

    def test_pile_is_frozen(self):
        """Pile should be frozen."""
        state = create_frozen_pile_state()
        assert state._pile_frozen is True

    def test_discard_pile_contains_wild(self):
        """Discard pile should contain a wild card."""
        state = create_frozen_pile_state()
        has_wild = any(is_wild(c) for c in state._discard_pile)
        assert has_wild, "Discard pile should contain a wild card"

    def test_initial_melds_not_made(self):
        """Neither team has made initial meld (double frozen)."""
        state = create_frozen_pile_state()
        assert state._initial_meld_made == [False, False]


class TestRedThreesState:
    """Tests for create_red_threes_state fixture."""

    def test_both_teams_have_red_threes(self):
        """Both teams should have red threes."""
        state = create_red_threes_state()
        assert len(state._red_threes[0]) > 0
        assert len(state._red_threes[1]) > 0

    def test_red_threes_are_valid(self):
        """All red threes should be valid red three cards."""
        state = create_red_threes_state()
        for team_idx in range(2):
            for card in state._red_threes[team_idx]:
                assert is_red_three(card), f"Card {card} should be a red three"

    def test_no_red_threes_in_hands(self):
        """No red threes should be in player hands."""
        state = create_red_threes_state()
        for player_idx in range(4):
            for card in state._hands[player_idx]:
                assert not is_red_three(card), f"Red three found in player {player_idx}'s hand"


class TestTerminalState:
    """Tests for create_terminal_state fixture."""

    def test_state_is_terminal(self):
        """State should be terminal."""
        state = create_terminal_state()
        assert state.is_terminal() is True
        assert state._is_terminal is True
        assert state._game_over is True

    def test_phase_is_terminal(self):
        """Game phase should be terminal."""
        state = create_terminal_state()
        assert state._game_phase == "terminal"

    def test_has_winning_team(self):
        """Should have a winning team."""
        state = create_terminal_state()
        assert state._winning_team in [0, 1]

    def test_scores_are_set(self):
        """Team scores should be set."""
        state = create_terminal_state()
        assert state._team_scores[0] > 0 or state._team_scores[1] > 0

    def test_returns_are_set(self):
        """Player returns should be set."""
        state = create_terminal_state()
        assert state._returns[0] == state._returns[2]  # Team 0 players
        assert state._returns[1] == state._returns[3]  # Team 1 players

    def test_going_out_team_has_empty_hands(self):
        """The team that went out should have empty hands."""
        state = create_terminal_state()
        winning_team = state._winning_team

        # Players on winning team should have empty hands
        player1 = winning_team  # Player 0 or 1
        player2 = winning_team + 2  # Player 2 or 3

        assert len(state._hands[player1]) == 0, f"Player {player1} (winning team) should have empty hand"
        assert len(state._hands[player2]) == 0, f"Player {player2} (winning team) should have empty hand"


class TestGetAllFixtures:
    """Tests for get_all_fixtures function."""

    def test_returns_all_fixtures(self):
        """Should return all 6 fixtures."""
        fixtures = get_all_fixtures()
        assert len(fixtures) == 6

    def test_fixture_names(self):
        """Should have expected fixture names."""
        fixtures = get_all_fixtures()
        expected_names = {
            "early_game",
            "mid_game",
            "canasta",
            "frozen_pile",
            "red_threes",
            "terminal",
        }
        assert set(fixtures.keys()) == expected_names

    def test_all_fixtures_are_states(self):
        """All fixtures should be CanastaState objects."""
        fixtures = get_all_fixtures()
        for name, state in fixtures.items():
            assert hasattr(state, '_hands'), f"{name} should have _hands attribute"
            assert hasattr(state, '_melds'), f"{name} should have _melds attribute"
            assert hasattr(state, '_discard_pile'), f"{name} should have _discard_pile attribute"

    def test_fixtures_can_be_serialized(self):
        """All fixtures should be serializable."""
        fixtures = get_all_fixtures()
        for name, state in fixtures.items():
            # Just check that serialize doesn't raise
            serialized = state.serialize()
            assert isinstance(serialized, str), f"{name} serialize should return string"
            assert len(serialized) > 0, f"{name} serialized state should not be empty"
