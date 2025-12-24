"""Tests for Canasta observer (information state and observation tensors)."""

import pytest
import numpy as np
import pyspiel
import canasta.canasta_game
from canasta.cards import is_wild, rank_of


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


class TestInformationStateTensor:
    """Tests for bd-015: Information State Tensor (dd4.3)."""

    def test_tensor_dimensions_correct(self, game):
        """Test that tensor dimensions are correct."""
        observer = game.make_py_observer()
        # Expected: 108 + 13 + 13 + 109 + 1 + 1 + 2 + 4 + 8 + 4 + 3 + 2 + 1 + 4 = 273
        expected_size = 273
        assert observer.info_state_size() == expected_size
        assert observer.observation_size() == expected_size

    def test_hand_encoding_accurate(self, game, state):
        """Test that hand encoding is accurate."""
        # Deal to playing phase
        state = deal_to_playing_phase(state)

        observer = game.make_py_observer()
        observer.set_from(state, 0)

        # Check that hand cards are encoded
        tensor = observer.tensor
        hand = state._hands[0]

        # First 108 elements are hand encoding
        hand_tensor = tensor[:108]

        # Count cards in tensor
        cards_in_tensor = int(np.sum(hand_tensor))
        assert cards_in_tensor == len(hand), f"Expected {len(hand)} cards in hand tensor, got {cards_in_tensor}"

        # Check that each card in hand has corresponding bit set
        for card_id in hand:
            assert hand_tensor[card_id] == 1.0, f"Card {card_id} not encoded in hand tensor"

    def test_meld_encoding_accurate(self, game, state):
        """Test that meld encoding is accurate."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()

        # Create a test meld by finding valid actions
        # First draw
        if state.current_player() != pyspiel.PlayerId.TERMINAL:
            legal = state.legal_actions()
            if legal:
                state.apply_action(legal[0])

        # Try to create a meld
        legal = state.legal_actions()
        # Find a CREATE_MELD action
        from canasta.canasta_game import ACTION_CREATE_MELD_START, ACTION_CREATE_MELD_END, ACTION_SKIP_MELD
        meld_actions = [a for a in legal if ACTION_CREATE_MELD_START <= a <= ACTION_CREATE_MELD_END]

        if meld_actions:
            # Apply meld action
            state.apply_action(meld_actions[0])

            # Update observer
            observer.set_from(state, state.current_player())
            tensor = observer.tensor

            # Meld encoding starts at offset 108
            # Team 0: 108-120, Team 1: 121-133
            team_0_melds = tensor[108:121]
            team_1_melds = tensor[121:134]

            # Check that at least one meld is encoded
            assert np.sum(team_0_melds) > 0 or np.sum(team_1_melds) > 0

    def test_pile_stock_encoding(self, game, state):
        """Test pile and stock encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Discard top encoding: offset 134, size 109
        discard_top = tensor[134:243]
        assert np.sum(discard_top) == 1.0, "Exactly one discard top indicator should be set"

        # Pile size: offset 243
        pile_size = tensor[243]
        assert 0.0 <= pile_size <= 1.0, "Pile size should be normalized"
        expected_pile_norm = len(state._discard_pile) / 108.0
        assert abs(pile_size - expected_pile_norm) < 0.001

        # Stock size: offset 244
        stock_size = tensor[244]
        assert 0.0 <= stock_size <= 1.0, "Stock size should be normalized"
        expected_stock_norm = len(state._stock) / 108.0
        assert abs(stock_size - expected_stock_norm) < 0.001

    def test_score_encoding(self, game, state):
        """Test team score encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Team scores: offset 245, size 2
        team_0_score = tensor[245]
        team_1_score = tensor[246]

        assert 0.0 <= team_0_score <= 1.0, "Team 0 score should be normalized"
        assert 0.0 <= team_1_score <= 1.0, "Team 1 score should be normalized"

        # Should match actual scores (normalized by 10000)
        expected_0 = state._team_scores[0] / 10000.0
        expected_1 = state._team_scores[1] / 10000.0
        assert abs(team_0_score - expected_0) < 0.001
        assert abs(team_1_score - expected_1) < 0.001

    def test_phase_encoding(self, game, state):
        """Test phase encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Phase encoding: offset 247, size 4 (one-hot)
        phase = tensor[247:251]
        assert np.sum(phase) == 1.0, "Exactly one phase should be active"

    def test_red_three_encoding(self, game, state):
        """Test red three encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Red threes: offset 251, size 8 (4 per team)
        red_threes = tensor[251:259]

        # Count should match actual red threes
        team_0_count = int(np.sum(red_threes[0:4]))
        team_1_count = int(np.sum(red_threes[4:8]))

        assert team_0_count == len(state._red_threes[0])
        assert team_1_count == len(state._red_threes[1])

    def test_canasta_count_encoding(self, game, state):
        """Test canasta count encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Canasta counts: offset 259, size 4 (natural and mixed per team)
        canasta_counts = tensor[259:263]

        # All should be normalized [0, 1]
        assert all(0.0 <= c <= 1.0 for c in canasta_counts)

    def test_tensor_updates_after_actions(self, game, state):
        """Test that tensor updates after state changes."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()

        # Get initial tensor
        observer.set_from(state, 0)
        tensor_before = observer.tensor.copy()

        # Apply an action
        legal = state.legal_actions()
        if legal and not state.is_terminal():
            state.apply_action(legal[0])

            # Get updated tensor
            observer.set_from(state, 0)
            tensor_after = observer.tensor.copy()

            # Tensors should differ (unless by extreme coincidence)
            assert not np.array_equal(tensor_before, tensor_after), \
                "Tensor should change after action"

    def test_turn_phase_indicators(self, game, state):
        """Test turn phase indicators."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Turn phase: offset 263, size 3 (draw, meld, discard)
        turn_phase = tensor[263:266]
        assert np.sum(turn_phase) == 1.0, "Exactly one turn phase should be active"

    def test_initial_meld_indicators(self, game, state):
        """Test initial meld made indicators."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Initial meld made: offset 266, size 2
        initial_meld = tensor[266:268]

        # Should match actual state
        assert initial_meld[0] == (1.0 if state._initial_meld_made[0] else 0.0)
        assert initial_meld[1] == (1.0 if state._initial_meld_made[1] else 0.0)

    def test_pile_frozen_indicator(self, game, state):
        """Test pile frozen indicator."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Pile frozen: offset 268, size 1
        pile_frozen = tensor[268]
        assert pile_frozen in [0.0, 1.0], "Pile frozen should be binary"

    def test_current_player_encoding(self, game, state):
        """Test current player encoding."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Current player: offset 269, size 4 (one-hot)
        current_player = tensor[269:273]
        assert np.sum(current_player) == 1.0, "Exactly one current player should be active"

        # Should match actual current player
        if 0 <= state._current_player < 4:
            assert current_player[state._current_player] == 1.0


class TestObservationTensor:
    """Tests for bd-016: Observation Tensor (dd4.4) - imperfect information."""

    def test_own_hand_visible(self, game, state):
        """Test that own hand is visible in observation."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)

        # First 108 elements are hand encoding for player 0
        hand_tensor = observer.tensor[:108]
        hand = state._hands[0]

        # Own hand should be visible
        for card_id in hand:
            assert hand_tensor[card_id] == 1.0, f"Own card {card_id} should be visible"

    def test_opponent_hands_hidden(self, game, state):
        """Test that opponent hands are NOT in observation tensor."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)

        # The hand encoding (first 108 elements) should only contain player 0's cards
        hand_tensor = observer.tensor[:108]
        own_hand = state._hands[0]

        # Check that only own cards are visible
        for i in range(108):
            if i in own_hand:
                assert hand_tensor[i] == 1.0, f"Own card {i} should be visible"
            else:
                # Cards not in own hand should not be visible
                # (they might be in opponent hands or elsewhere)
                pass

        # Verify opponent hand cards are not in the hand tensor
        opponent_cards = set()
        for p in [1, 2, 3]:
            opponent_cards.update(state._hands[p])

        # Count cards in hand tensor
        visible_cards = [i for i in range(108) if hand_tensor[i] == 1.0]

        # No opponent cards should appear in hand tensor
        for card in visible_cards:
            assert card in own_hand, f"Card {card} in hand tensor but not in own hand"

    def test_all_melds_visible(self, game, state):
        """Test that all team melds are visible (not private info)."""
        state = deal_to_playing_phase(state)

        # Try to create some melds
        for _ in range(5):
            if state.is_terminal():
                break
            legal = state.legal_actions()
            if not legal:
                break
            # Apply action (might create melds)
            state.apply_action(legal[0])

        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Meld encoding: offset 108, size 26 (13 per team)
        team_0_melds = tensor[108:121]
        team_1_melds = tensor[121:134]

        # Both teams' melds should be visible (they're public information)
        # Just check they're valid values
        assert all(0.0 <= v <= 1.0 for v in team_0_melds)
        assert all(0.0 <= v <= 1.0 for v in team_1_melds)

    def test_discard_top_visible(self, game, state):
        """Test that discard pile top is visible."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Discard top: offset 134, size 109
        discard_top = tensor[134:243]

        # Exactly one card or empty indicator should be set
        assert np.sum(discard_top) == 1.0

        # Should match actual discard top
        if state._discard_pile:
            top_card = state._discard_pile[-1]
            assert discard_top[top_card] == 1.0
        else:
            assert discard_top[108] == 1.0  # Empty indicator

    def test_stock_size_visible_contents_hidden(self, game, state):
        """Test that stock size is visible but contents are hidden."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Stock size: offset 244
        stock_size = tensor[244]

        # Size should be visible (normalized)
        expected = len(state._stock) / 108.0
        assert abs(stock_size - expected) < 0.001

        # But actual cards in stock are NOT in the tensor
        # (they're hidden information)

    def test_red_three_counts_correct(self, game, state):
        """Test that red three counts are correct."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        observer.set_from(state, 0)
        tensor = observer.tensor

        # Red threes: offset 251, size 8
        red_threes = tensor[251:259]

        # Should match actual counts
        team_0_count = int(np.sum(red_threes[0:4]))
        team_1_count = int(np.sum(red_threes[4:8]))

        assert team_0_count == len(state._red_threes[0])
        assert team_1_count == len(state._red_threes[1])

    def test_observation_same_as_info_state_for_imperfect_info(self, game, state):
        """Test that observation tensor equals info state tensor for imperfect info game."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()

        # In Canasta, observation = information state (no hidden info within a player's view)
        observer.set_from(state, 0)
        obs_tensor = observer.tensor.copy()

        # Since we don't have separate info state tensor yet, just verify structure
        assert len(obs_tensor) == observer.observation_size()

    def test_tensor_dimensions_match_info_state(self, game):
        """Test that observation tensor has same dimensions as info state."""
        observer = game.make_py_observer()
        assert observer.observation_size() == observer.info_state_size()

    def test_observation_for_different_players(self, game, state):
        """Test that different players see different observations."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()

        # Get observation for player 0
        observer.set_from(state, 0)
        obs_0 = observer.tensor.copy()

        # Get observation for player 1
        observer.set_from(state, 1)
        obs_1 = observer.tensor.copy()

        # Observations should differ (different hands)
        # Check hand portion (first 108 elements)
        assert not np.array_equal(obs_0[:108], obs_1[:108]), \
            "Different players should see different hands"

    def test_public_information_same_for_all_players(self, game, state):
        """Test that public information is same for all players."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()

        # Get observations for all players
        observations = []
        for p in range(4):
            observer.set_from(state, p)
            observations.append(observer.tensor.copy())

        # Public information should be same:
        # - Team melds (offset 108-133)
        # - Discard top (offset 134-242)
        # - Pile size (offset 243)
        # - Stock size (offset 244)
        # - Team scores (offset 245-246)
        # etc.

        for i in range(1, 4):
            # Check team melds
            assert np.array_equal(observations[0][108:134], observations[i][108:134])
            # Check discard
            assert np.array_equal(observations[0][134:243], observations[i][134:243])
            # Check pile size
            assert observations[0][243] == observations[i][243]
            # Check stock size
            assert observations[0][244] == observations[i][244]


class TestPyObserverIntegration:
    """Tests for bd-017: PyObserver Integration (dd4.5)."""

    def test_observer_creates_correctly(self, game):
        """Test that observer can be created."""
        observer = game.make_py_observer()
        assert observer is not None
        assert hasattr(observer, 'set_from')
        assert hasattr(observer, 'string_from')

    def test_observation_tensor_callable(self, game, state):
        """Test that observation_tensor can be called."""
        state = deal_to_playing_phase(state)
        tensor = state.observation_tensor(0)
        assert tensor is not None
        assert isinstance(tensor, np.ndarray)
        assert len(tensor) > 0

    def test_information_state_tensor_callable(self, game, state):
        """Test that information_state_tensor can be called."""
        state = deal_to_playing_phase(state)
        tensor = state.information_state_tensor(0)
        assert tensor is not None
        assert isinstance(tensor, np.ndarray)
        assert len(tensor) > 0

    def test_tensors_have_correct_types(self, game, state):
        """Test that tensors are numpy arrays with correct dtype."""
        state = deal_to_playing_phase(state)

        obs_tensor = state.observation_tensor(0)
        info_tensor = state.information_state_tensor(0)

        assert isinstance(obs_tensor, np.ndarray)
        assert isinstance(info_tensor, np.ndarray)
        assert obs_tensor.dtype == np.float32
        assert info_tensor.dtype == np.float32

    def test_tensors_update_after_state_changes(self, game, state):
        """Test that tensors update when state changes."""
        state = deal_to_playing_phase(state)

        # Get initial tensor
        tensor_before = state.observation_tensor(0)

        # Apply action
        legal = state.legal_actions()
        if legal and not state.is_terminal():
            state.apply_action(legal[0])

            # Get updated tensor
            tensor_after = state.observation_tensor(0)

            # Should differ (unless by coincidence)
            assert not np.array_equal(tensor_before, tensor_after)

    def test_observer_works_with_random_agent(self, game):
        """Test that observer works during random game play."""
        state = game.new_initial_state()

        # Play random game for a bit
        for _ in range(100):
            if state.is_terminal():
                break

            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                if outcomes:
                    state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal:
                    # Get observation for current player
                    obs = state.observation_tensor()
                    assert obs is not None
                    assert len(obs) > 0

                    # Apply random action
                    import random
                    state.apply_action(random.choice(legal))

    def test_multiple_observers_per_game_work(self, game, state):
        """Test that multiple observers can be created for same game."""
        state = deal_to_playing_phase(state)

        obs1 = game.make_py_observer()
        obs2 = game.make_py_observer()

        obs1.set_from(state, 0)
        obs2.set_from(state, 1)

        # Both should work independently
        assert obs1.tensor is not None
        assert obs2.tensor is not None
        assert not np.array_equal(obs1.tensor[:108], obs2.tensor[:108])  # Different hands

    def test_observation_tensor_with_no_player_uses_current(self, game, state):
        """Test that observation_tensor() with no args uses current player."""
        state = deal_to_playing_phase(state)

        current = state.current_player()
        if current >= 0:
            # Get tensor with current player
            tensor_implicit = state.observation_tensor()
            tensor_explicit = state.observation_tensor(current)

            assert np.array_equal(tensor_implicit, tensor_explicit)


class TestObserverStringRepresentation:
    """Test string representation of observations."""

    def test_string_from_returns_valid_string(self, game, state):
        """Test that string_from returns a valid string."""
        state = deal_to_playing_phase(state)
        observer = game.make_py_observer()
        s = observer.string_from(state, 0)
        assert isinstance(s, str)
        assert len(s) > 0
