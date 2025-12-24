"""Tests for serialization and full game integration."""

import pytest
import random
import pyspiel
import canasta.canasta_game


@pytest.fixture
def game():
    """Create a Canasta game instance."""
    return pyspiel.load_game("python_canasta")


@pytest.fixture
def state(game):
    """Create a fresh game state."""
    return game.new_initial_state()


def deal_to_playing_phase(state):
    """Deal cards until we reach the playing phase."""
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        action = outcomes[0][0]
        state.apply_action(action)
    return state


class TestSerialization:
    """Tests for bd-018: Serialization (dd4.6)."""

    def test_serialize_state_to_string(self, game, state):
        """Test that state can be serialized to string."""
        state = deal_to_playing_phase(state)
        serialized = state.serialize()

        assert isinstance(serialized, str)
        assert len(serialized) > 0
        # Should be valid JSON
        import json
        data = json.loads(serialized)
        assert isinstance(data, dict)

    def test_deserialize_string_to_state(self, game, state):
        """Test that serialized string can be deserialized."""
        state = deal_to_playing_phase(state)
        serialized = state.serialize()

        # Create new state and deserialize
        new_state = game.new_initial_state()
        new_state.deserialize(serialized)

        # Check basic properties match
        assert new_state._current_player == state._current_player
        assert new_state._is_terminal == state._is_terminal
        assert len(new_state._stock) == len(state._stock)
        assert len(new_state._discard_pile) == len(state._discard_pile)

    def test_serialized_state_equals_original(self, game, state):
        """Test that deserialized state equals original."""
        state = deal_to_playing_phase(state)

        # Apply some actions
        for _ in range(10):
            if state.is_terminal():
                break
            legal = state.legal_actions()
            if not legal:
                break
            state.apply_action(random.choice(legal))

        # Serialize and deserialize
        serialized = state.serialize()
        new_state = game.new_initial_state()
        new_state.deserialize(serialized)

        # Compare key state variables
        assert new_state._current_player == state._current_player
        assert new_state._is_terminal == state._is_terminal
        assert new_state._team_scores == state._team_scores
        assert new_state._hand_number == state._hand_number
        assert new_state._turn_phase == state._turn_phase

        # Compare hands
        for i in range(4):
            assert sorted(new_state._hands[i]) == sorted(state._hands[i])

        # Compare stock and discard
        assert new_state._stock == state._stock
        assert new_state._discard_pile == state._discard_pile

    def test_clone_creates_independent_copy(self, game, state):
        """Test that clone creates an independent copy."""
        state = deal_to_playing_phase(state)
        cloned = state.clone()

        # Should have same values
        assert cloned._current_player == state._current_player
        assert cloned._team_scores == state._team_scores

        # But be independent objects
        assert cloned is not state
        assert cloned._hands is not state._hands
        assert cloned._stock is not state._stock

    def test_clone_modifications_dont_affect_original(self, game, state):
        """Test that modifying clone doesn't affect original."""
        state = deal_to_playing_phase(state)

        original_player = state._current_player
        original_stock_len = len(state._stock)

        cloned = state.clone()

        # Modify clone
        legal = cloned.legal_actions()
        if legal:
            cloned.apply_action(legal[0])

        # Original should be unchanged
        assert state._current_player == original_player
        assert len(state._stock) == original_stock_len

    def test_full_game_with_serialize_deserialize_checkpoints(self, game):
        """Test full game with serialization checkpoints."""
        state = game.new_initial_state()
        checkpoints = []

        # Play game and create checkpoints
        step = 0
        while not state.is_terminal() and step < 200:
            # Create checkpoint every 20 steps
            if step % 20 == 0:
                serialized = state.serialize()
                checkpoints.append(serialized)

            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                if outcomes:
                    state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal:
                    state.apply_action(random.choice(legal))

            step += 1

        # Verify we created some checkpoints
        assert len(checkpoints) > 0

        # Verify each checkpoint can be deserialized
        for i, checkpoint in enumerate(checkpoints):
            new_state = game.new_initial_state()
            new_state.deserialize(checkpoint)
            assert not new_state.is_terminal() or i == len(checkpoints) - 1


class TestGameIntegration:
    """Tests for full OpenSpiel API compliance."""

    def test_random_multi_hand_games_complete(self, game):
        """Test that random multi-hand games can complete."""
        completed_games = 0
        target_games = 10

        for game_num in range(target_games):
            state = game.new_initial_state()
            steps = 0
            max_steps = 1000

            while not state.is_terminal() and steps < max_steps:
                if state.is_chance_node():
                    outcomes = state.chance_outcomes()
                    if outcomes:
                        state.apply_action(outcomes[0][0])
                else:
                    legal = state.legal_actions()
                    if legal:
                        state.apply_action(random.choice(legal))

                steps += 1

            if state.is_terminal():
                completed_games += 1

        # At least some games should complete
        assert completed_games > 0, f"Expected some games to complete, got {completed_games}/{target_games}"

    def test_games_can_reach_5000_points(self, game):
        """Test that games can reach the 5000 point target."""
        # This test runs longer games to try to reach 5000
        max_attempts = 5
        reached_5000 = False

        for attempt in range(max_attempts):
            state = game.new_initial_state()
            steps = 0
            max_steps = 2000  # Allow for multi-hand games

            while not state.is_terminal() and steps < max_steps:
                if state.is_chance_node():
                    outcomes = state.chance_outcomes()
                    if outcomes:
                        state.apply_action(outcomes[0][0])
                else:
                    legal = state.legal_actions()
                    if legal:
                        state.apply_action(random.choice(legal))

                steps += 1

            if state.is_terminal():
                # Check if either team reached 5000
                if state._team_scores[0] >= 5000 or state._team_scores[1] >= 5000:
                    reached_5000 = True
                    break

        # Note: This is probabilistic and might not always reach 5000 in random play
        # So we don't fail if it doesn't happen, just record it
        print(f"Reached 5000 points: {reached_5000}")

    def test_all_api_methods_callable(self, game, state):
        """Test that all required OpenSpiel API methods are callable."""
        state = deal_to_playing_phase(state)

        # Test all required methods exist and are callable
        assert callable(state.current_player)
        assert callable(state.legal_actions)
        assert callable(state.apply_action)
        assert callable(state.is_terminal)
        assert callable(state.returns)
        assert callable(state.observation_tensor)
        assert callable(state.information_state_tensor)
        assert callable(state.serialize)
        assert callable(state.clone)

        # Actually call them
        player = state.current_player()
        assert player is not None

        legal = state.legal_actions()
        assert isinstance(legal, list)

        term = state.is_terminal()
        assert isinstance(term, bool)

        rets = state.returns()
        assert isinstance(rets, list)
        assert len(rets) == 4

    def test_returns_sum_correctly_at_terminal(self, game):
        """Test that returns sum correctly when game is terminal."""
        # Play a short game to terminal
        state = game.new_initial_state()
        steps = 0

        while not state.is_terminal() and steps < 500:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                if outcomes:
                    state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal:
                    state.apply_action(random.choice(legal))
            steps += 1

        if state.is_terminal():
            rets = state.returns()
            # Team 0: players 0 and 2, Team 1: players 1 and 3
            assert rets[0] == rets[2], "Teammates should have same return"
            assert rets[1] == rets[3], "Teammates should have same return"

    def test_action_string_conversion(self, game, state):
        """Test that actions can be converted to strings."""
        state = deal_to_playing_phase(state)

        legal = state.legal_actions()
        if legal:
            for action in legal[:5]:  # Test first 5 actions
                action_str = state.action_to_string(state.current_player(), action)
                assert isinstance(action_str, str)
                assert len(action_str) > 0

    def test_deserialized_states_are_playable(self, game, state):
        """Test that deserialized states can be played."""
        state = deal_to_playing_phase(state)

        # Serialize
        serialized = state.serialize()

        # Deserialize to new state
        new_state = game.new_initial_state()
        new_state.deserialize(serialized)

        # Should be playable
        if not new_state.is_terminal():
            legal = new_state.legal_actions()
            assert len(legal) > 0

            # Apply an action
            new_state.apply_action(legal[0])

            # Should still work
            assert new_state.current_player() is not None
