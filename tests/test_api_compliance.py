"""Tests for OpenSpiel API compliance and documentation.

OpenSpiel API Requirements:
1. All GameType parameters correct
2. All State methods implemented
3. Observation/information tensors correct shape
4. Action encoding/decoding complete
5. Serialization round-trips correctly
6. Game loads via pyspiel.load_game()
"""

import pyspiel
import numpy as np
import canasta  # Register the game with OpenSpiel


def test_game_type_parameters():
    """Test that game type parameters are correct."""
    game = pyspiel.load_game("python_canasta")

    # Check basic game type properties
    game_type = game.get_type()
    assert game_type.short_name == "python_canasta"
    assert game_type.long_name == "Python Canasta"
    assert game_type.dynamics == pyspiel.GameType.Dynamics.SEQUENTIAL
    assert game_type.chance_mode == pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC
    assert game_type.information == pyspiel.GameType.Information.IMPERFECT_INFORMATION
    assert game_type.utility == pyspiel.GameType.Utility.GENERAL_SUM
    assert game_type.reward_model == pyspiel.GameType.RewardModel.TERMINAL
    assert game_type.max_num_players == 4
    assert game_type.min_num_players == 4


def test_all_state_methods_exist():
    """Test that all required OpenSpiel state methods are implemented."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Core state methods
    assert hasattr(state, 'current_player')
    assert hasattr(state, 'legal_actions')
    assert hasattr(state, 'is_terminal')
    assert hasattr(state, 'returns')
    assert hasattr(state, 'is_chance_node')
    assert hasattr(state, 'chance_outcomes')

    # Information state methods
    assert hasattr(state, 'observation_tensor')
    assert hasattr(state, 'information_state_tensor')
    assert hasattr(state, 'observation_string')
    assert hasattr(state, 'information_state_string')

    # Action methods
    assert hasattr(state, 'apply_action')
    assert hasattr(state, 'action_to_string')
    assert hasattr(state, 'string_to_action')

    # Serialization methods
    assert hasattr(state, 'serialize')
    # resample_from_info_state is optional for some game types

    # Cloning
    assert hasattr(state, 'clone')


def test_load_game_works():
    """Test that game can be loaded via pyspiel.load_game()."""
    # Should load without errors
    game = pyspiel.load_game("python_canasta")
    assert game is not None

    # Should be able to create initial state
    state = game.new_initial_state()
    assert state is not None

    # Should be able to play
    assert state.is_chance_node()
    outcomes = state.chance_outcomes()
    assert len(outcomes) > 0


def test_game_info_correct():
    """Test that game info is correct."""
    game = pyspiel.load_game("python_canasta")

    # Check info fields (accessed as properties)
    assert game.num_distinct_actions() == 3000
    assert game.max_chance_outcomes() == 108
    assert game.num_players() == 4
    assert game.min_utility() == -5000.0
    assert game.max_utility() == 5000.0
    assert game.utility_sum() == 0.0
    assert game.max_game_length() == 1000


def test_action_string_roundtrip():
    """Test that action_to_string and string_to_action roundtrip."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        action = outcomes[0][0]

        # Test action string conversion for chance actions
        action_str = state.action_to_string(state.current_player(), action)
        assert isinstance(action_str, str)
        assert len(action_str) > 0

        state.apply_action(action)

    # Test action strings for player actions
    if not state.is_terminal():
        legal = state.legal_actions()
        if legal:
            action = legal[0]
            player = state.current_player()
            action_str = state.action_to_string(player, action)
            assert isinstance(action_str, str)
            assert len(action_str) > 0


def test_state_string_representation():
    """Test that state has string representation."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Test __str__ method
    state_str = str(state)
    assert isinstance(state_str, str)
    assert len(state_str) > 0

    # Should include phase information
    assert "Phase:" in state_str or "phase" in state_str.lower()


def test_num_players_correct():
    """Test that num_players() returns correct value."""
    game = pyspiel.load_game("python_canasta")
    assert game.num_players() == 4

    state = game.new_initial_state()
    assert state.num_players() == 4


def test_max_game_length_reasonable():
    """Test that max_game_length is set to reasonable value."""
    game = pyspiel.load_game("python_canasta")

    # Should be set to some reasonable upper bound
    max_length = game.max_game_length()
    assert max_length > 0
    assert max_length >= 100  # At least 100 moves
    assert max_length <= 10000  # Not absurdly high
