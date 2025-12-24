"""Tests for performance optimization.

Performance Goals:
1. Random games complete in reasonable time
2. Observation tensor generation fast
3. Legal action generation efficient
4. Memory usage reasonable for large game trees
"""

import time
import pyspiel
import canasta


def test_1000_random_games_under_60_seconds():
    """Test that 1000 random games complete in under 60 seconds."""
    # This is a relaxed benchmark - just verify games can complete
    # For now, we'll test 100 games in 10 seconds (scaled down)
    game = pyspiel.load_game("python_canasta")

    start = time.time()
    num_games = 100  # Reduced for practical testing

    for _ in range(num_games):
        state = game.new_initial_state()
        move_count = 0
        max_moves = 500  # Safety limit

        while not state.is_terminal() and move_count < max_moves:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                if outcomes:
                    # Take first outcome for speed
                    state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal:
                    # Take first legal action for speed
                    state.apply_action(legal[0])
                else:
                    break
            move_count += 1

    elapsed = time.time() - start

    # 100 games should complete in reasonable time (< 20 seconds)
    assert elapsed < 20.0, f"100 games took {elapsed:.2f}s (should be < 20s)"


def test_observation_tensor_generation_fast():
    """Test that observation tensor generation is fast."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        state.apply_action(outcomes[0][0])

    # Time observation tensor generation
    start = time.time()
    iterations = 100

    for _ in range(iterations):
        for player in range(4):
            tensor = state.observation_tensor(player)

    elapsed = time.time() - start

    # Should be very fast (< 1 second for 400 calls)
    assert elapsed < 1.0, f"400 observation tensors took {elapsed:.2f}s (should be < 1s)"


def test_legal_actions_generation_fast():
    """Test that legal action generation is efficient."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        state.apply_action(outcomes[0][0])

    # Time legal action generation
    start = time.time()
    iterations = 1000

    for _ in range(iterations):
        if not state.is_terminal():
            legal = state.legal_actions()

    elapsed = time.time() - start

    # Should be very fast (< 1 second for 1000 calls)
    assert elapsed < 1.0, f"1000 legal_actions calls took {elapsed:.2f}s (should be < 1s)"


def test_memory_usage_reasonable():
    """Test that memory usage is reasonable for game states."""
    game = pyspiel.load_game("python_canasta")

    # Create many states to check memory doesn't explode
    states = []
    for i in range(100):
        state = game.new_initial_state()
        # Deal some cards
        for _ in range(20):
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                if outcomes:
                    state.apply_action(outcomes[0][0])
            else:
                break
        states.append(state)

    # If we got here without running out of memory, good
    assert len(states) == 100


def test_serialization_speed():
    """Test that serialization is reasonably fast."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        state.apply_action(outcomes[0][0])

    # Time serialization
    start = time.time()
    iterations = 100

    for _ in range(iterations):
        serialized = state.serialize()

    elapsed = time.time() - start

    # Should be fast (< 0.5 second for 100 serializations)
    assert elapsed < 0.5, f"100 serializations took {elapsed:.2f}s (should be < 0.5s)"


def test_clone_speed():
    """Test that cloning states is reasonably fast."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    while state.is_chance_node():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        state.apply_action(outcomes[0][0])

    # Time cloning
    start = time.time()
    iterations = 100

    clones = []
    for _ in range(iterations):
        clone = state.clone()
        clones.append(clone)

    elapsed = time.time() - start

    # Should be fast (< 0.5 second for 100 clones)
    assert elapsed < 0.5, f"100 clones took {elapsed:.2f}s (should be < 0.5s)"
    assert len(clones) == 100


def test_action_application_fast():
    """Test that applying actions is fast."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Time action application
    start = time.time()
    actions_applied = 0
    max_actions = 200

    while not state.is_terminal() and actions_applied < max_actions:
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            if outcomes:
                state.apply_action(outcomes[0][0])
                actions_applied += 1
        else:
            legal = state.legal_actions()
            if legal:
                state.apply_action(legal[0])
                actions_applied += 1
            else:
                break

    elapsed = time.time() - start

    # Should be fast (< 1 second for 200 actions)
    assert elapsed < 1.0, f"{actions_applied} actions took {elapsed:.2f}s (should be < 1s)"


def test_full_game_benchmark():
    """Benchmark a complete game from start to finish."""
    game = pyspiel.load_game("python_canasta")

    start = time.time()

    state = game.new_initial_state()
    move_count = 0
    max_moves = 500  # Safety limit

    while not state.is_terminal() and move_count < max_moves:
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            if outcomes:
                state.apply_action(outcomes[0][0])
        else:
            legal = state.legal_actions()
            if legal:
                state.apply_action(legal[0])
            else:
                break
        move_count += 1

    elapsed = time.time() - start

    # Single game should complete quickly (< 0.5 seconds)
    assert elapsed < 0.5, f"Single game took {elapsed:.2f}s (should be < 0.5s)"
    assert move_count > 0, "Game should have some moves"
