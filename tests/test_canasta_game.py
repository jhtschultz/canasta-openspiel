"""Tests for OpenSpiel Canasta game skeleton."""

import pytest
import pyspiel

# Import canasta_game to register it with OpenSpiel
from canasta import canasta_game


def test_load_game():
    """Test that pyspiel.load_game('python_canasta') works."""
    game = pyspiel.load_game("python_canasta")
    assert game is not None
    assert game.get_type().short_name == "python_canasta"


def test_game_type_attributes():
    """Test game type attributes match Canasta specifications."""
    game = pyspiel.load_game("python_canasta")
    game_type = game.get_type()

    assert game_type.long_name == "Python Canasta"
    assert game_type.dynamics == pyspiel.GameType.Dynamics.SEQUENTIAL
    assert game_type.chance_mode == pyspiel.GameType.ChanceMode.EXPLICIT_STOCHASTIC
    assert game_type.information == pyspiel.GameType.Information.IMPERFECT_INFORMATION
    assert game_type.utility == pyspiel.GameType.Utility.GENERAL_SUM
    assert game_type.reward_model == pyspiel.GameType.RewardModel.TERMINAL
    assert game_type.max_num_players == 4
    assert game_type.min_num_players == 4
    assert game_type.provides_information_state_tensor
    assert game_type.provides_observation_tensor


def test_game_info():
    """Test game info attributes."""
    game = pyspiel.load_game("python_canasta")

    assert game.num_players() == 4
    assert game.num_distinct_actions() > 0
    assert game.max_chance_outcomes() == 108  # 108 cards in deck


def test_game_parameters():
    """Test game parameters."""
    game = pyspiel.load_game("python_canasta")
    params = game.get_parameters()

    # Default parameters
    assert "num_players" in params
    assert params["num_players"] == 4


def test_new_initial_state():
    """Test that game can create a new initial state."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    assert state is not None
    assert not state.is_terminal()


def test_initial_state_is_chance():
    """Test that initial state starts with chance player (dealing)."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Initially should be chance player (dealing cards)
    assert state.current_player() == pyspiel.PlayerId.CHANCE


def test_state_clone():
    """Test that state can be cloned."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    cloned_state = state.clone()
    assert cloned_state is not None
    assert cloned_state.current_player() == state.current_player()


def test_state_string_representation():
    """Test that state has string representation."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    state_str = str(state)
    assert state_str is not None
    assert len(state_str) > 0


def test_legal_actions_at_chance():
    """Test that chance node has legal actions (cards to deal)."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # At chance node, legal actions should be cards in deck
    if state.current_player() == pyspiel.PlayerId.CHANCE:
        legal_actions = state.legal_actions()
        assert len(legal_actions) > 0
        assert all(0 <= action < 108 for action in legal_actions)


def test_chance_outcomes():
    """Test chance outcomes at chance node."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    if state.current_player() == pyspiel.PlayerId.CHANCE:
        outcomes = state.chance_outcomes()
        assert len(outcomes) > 0
        # Should sum to 1.0 (probability distribution)
        total_prob = sum(prob for _, prob in outcomes)
        assert abs(total_prob - 1.0) < 1e-6


def test_observation_tensor_shape():
    """Test that observation tensor has correct shape."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()
    observer = game.make_py_observer()

    # Observation should have some structure
    obs = observer.dict["observation"]
    assert obs is not None
    assert len(obs) > 0

    # Can get observation for player 0
    observer.set_from(state, 0)
    assert observer.dict["observation"] is not None


def test_make_py_observer():
    """Test that game can create a Python observer."""
    game = pyspiel.load_game("python_canasta")
    observer = game.make_py_observer()

    assert observer is not None
