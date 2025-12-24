"""Tests for multi-hand game loop in Canasta.

Tests that games can play multiple hands to reach 5000 points.
"""

import pyspiel
import pytest

# Import to register the game
from canasta import canasta_game


def test_hand_number_initialization():
    """Test that hand number starts at 0."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()
    assert hasattr(state, '_hand_number')
    assert state._hand_number == 0


def test_target_score_initialization():
    """Test that target score is 5000."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()
    assert hasattr(state, '_target_score')
    assert state._target_score == 5000


def test_hand_number_increments_on_new_hand():
    """Test that hand number increments when starting a new hand."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Manually trigger new hand to test
    initial_hand_number = state._hand_number
    state._start_new_hand()
    assert state._hand_number == initial_hand_number + 1


def test_start_new_hand_clears_hands():
    """Test that starting a new hand clears player hands."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Add cards to hands
    state._hands[0] = [0, 1, 2]
    state._hands[1] = [3, 4, 5]

    state._start_new_hand()

    # All hands should be empty
    for hand in state._hands:
        assert len(hand) == 0


def test_start_new_hand_clears_melds():
    """Test that starting a new hand clears team melds."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    from canasta.melds import Meld

    # Add melds
    state._melds[0] = [Meld(rank=5, natural_cards=[20, 21, 22], wild_cards=[])]
    state._melds[1] = [Meld(rank=6, natural_cards=[24, 25, 26], wild_cards=[])]

    state._start_new_hand()

    # All melds should be cleared
    assert len(state._melds[0]) == 0
    assert len(state._melds[1]) == 0


def test_start_new_hand_clears_discard_pile():
    """Test that starting a new hand clears discard pile."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Add cards to discard pile
    state._discard_pile = [10, 11, 12, 13]

    state._start_new_hand()

    assert len(state._discard_pile) == 0


def test_start_new_hand_clears_red_threes():
    """Test that starting a new hand clears red threes."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Add red threes
    state._red_threes[0] = [104, 105]
    state._red_threes[1] = [106, 107]

    state._start_new_hand()

    # Red threes should be cleared
    assert len(state._red_threes[0]) == 0
    assert len(state._red_threes[1]) == 0


def test_start_new_hand_preserves_team_scores():
    """Test that starting a new hand preserves cumulative team scores."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Set team scores
    state._team_scores[0] = 1200
    state._team_scores[1] = 800

    state._start_new_hand()

    # Team scores should be preserved
    assert state._team_scores[0] == 1200
    assert state._team_scores[1] == 800


def test_start_new_hand_resets_dealing_phase():
    """Test that starting a new hand resets to dealing phase."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Set to playing phase
    state._dealing_phase = False
    state._game_phase = "playing"

    state._start_new_hand()

    # Should reset to dealing
    assert state._dealing_phase == True
    assert state._game_phase == "dealing"


def test_finalize_game_ends_at_5000():
    """Test that game ends when a team reaches 5000 points."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Set team scores to simulate reaching 5000
    state._team_scores[0] = 5100
    state._team_scores[1] = 3000

    state._finalize_game(winning_team=0, went_out_concealed=False)

    # Game should be terminal
    assert state.is_terminal()
    assert state._winning_team == 0


def test_finalize_game_starts_new_hand_below_5000():
    """Test that finalize checks for 5000 and starts new hand if below."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Set team scores below 5000
    state._team_scores[0] = 2000
    state._team_scores[1] = 1500
    state._hand_scores[0] = 500
    state._hand_scores[1] = 300

    # Call finalize - should start new hand instead of ending game
    initial_hand_number = state._hand_number

    # Manually set up to trigger the logic
    # We'll test this by modifying _finalize_game to check scores first
    # For now, this test will verify the behavior exists
    state._finalize_game(winning_team=0, went_out_concealed=False)

    # After finalize, check if new hand started (scores below 5000)
    # The game should either be terminal (if >= 5000) or start new hand
    if state._team_scores[0] >= 5000 or state._team_scores[1] >= 5000:
        assert state.is_terminal()
    else:
        # Should have started new hand
        assert state._hand_number == initial_hand_number + 1


def test_initial_meld_threshold_updates_with_score():
    """Test that initial meld threshold increases with team score."""
    from canasta.melds import initial_meld_minimum

    # Test different score thresholds
    assert initial_meld_minimum(0) == 50
    assert initial_meld_minimum(1500) == 90
    assert initial_meld_minimum(3000) == 120


def test_winner_determination_higher_score():
    """Test that team with higher score wins."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    state._team_scores[0] = 5200
    state._team_scores[1] = 4800

    state._finalize_game(winning_team=0, went_out_concealed=False)

    assert state._winning_team == 0


def test_winner_determination_tie_goes_to_out_team():
    """Test that in a tie, team that went out wins."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    state._team_scores[0] = 5000
    state._team_scores[1] = 5000

    state._finalize_game(winning_team=1, went_out_concealed=False)

    # Team 1 went out, so they should win the tie
    assert state._winning_team == 1
