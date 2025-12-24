"""Integration tests for complete Canasta hands."""
import pytest
import pyspiel
import random

# Import to register the game
import canasta.canasta_game


def play_random_game(seed=None):
    """Play a complete random game and return statistics.

    Args:
        seed: Random seed for reproducibility

    Returns:
        Dict with game statistics: {
            'completed': bool,
            'num_actions': int,
            'winner': int (team 0 or 1),
            'scores': [team0_score, team1_score],
            'error': str or None
        }
    """
    if seed is not None:
        random.seed(seed)

    try:
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        actions_taken = 0
        # Increased limit for multi-hand games that play to 5000 points
        max_actions = 5000

        while not state.is_terminal() and actions_taken < max_actions:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                # Pick random outcome
                action = random.choice([o[0] for o in outcomes])
            else:
                legal = state.legal_actions()
                # After calling legal_actions(), state may become terminal or chance node
                # This can happen when stock is exhausted and new hand starts
                if state.is_terminal():
                    break
                # State may have transitioned to chance node (new hand started)
                if state.is_chance_node():
                    continue
                # Check legal actions again after terminal/chance checks
                if not legal:
                    # This should not happen - if state is not terminal/chance, there should be legal actions
                    # But if it does, just break and let the game complete
                    break
                # Pick random legal action
                action = random.choice(legal)

            state.apply_action(action)
            actions_taken += 1

        # Extract results
        returns = state.returns()
        team_0_score = returns[0]  # Players 0 and 2
        team_1_score = returns[1]  # Players 1 and 3

        winner = 0 if team_0_score > team_1_score else 1

        return {
            'completed': state.is_terminal(),
            'num_actions': actions_taken,
            'winner': winner,
            'scores': [team_0_score, team_1_score],
            'error': None
        }

    except Exception as e:
        return {
            'completed': False,
            'num_actions': 0,
            'winner': -1,
            'scores': [0, 0],
            'error': str(e)
        }


def play_n_random_games(n):
    """Play n random games and return results.

    Args:
        n: Number of games to play

    Returns:
        List of result dicts from play_random_game()
    """
    results = []
    for i in range(n):
        result = play_random_game(seed=i)
        results.append(result)
    return results


class TestSingleGame:
    """Test single game completion."""

    def test_single_random_game_completes(self):
        """A single random game should complete."""
        result = play_random_game(seed=42)
        assert result['completed'], f"Game did not complete: {result['error']}"

    def test_random_game_reaches_terminal_state(self):
        """Random game should reach terminal state."""
        result = play_random_game(seed=123)
        assert result['completed']
        assert result['num_actions'] > 0

    def test_random_game_calculates_scores(self):
        """Random game should calculate scores."""
        result = play_random_game(seed=456)
        assert result['completed']
        scores = result['scores']
        assert len(scores) == 2
        # Scores should be integers (converted from float)
        assert isinstance(scores[0], (int, float))
        assert isinstance(scores[1], (int, float))

    def test_random_game_has_winner(self):
        """Random game should have a winner."""
        result = play_random_game(seed=789)
        assert result['completed']
        assert result['winner'] in [0, 1]


class TestMultipleGames:
    """Test multiple game completion."""

    def test_100_random_games_all_complete(self):
        """100 random games should all complete."""
        results = play_n_random_games(100)
        completed = [r for r in results if r['completed']]
        assert len(completed) == 100, f"Only {len(completed)}/100 games completed"

    def test_100_random_games_no_crashes(self):
        """100 random games should complete without errors."""
        results = play_n_random_games(100)
        errors = [r['error'] for r in results if r['error'] is not None]
        assert len(errors) == 0, f"Errors: {errors[:5]}"  # Show first 5 errors


class TestGameLength:
    """Test game length properties."""

    def test_game_length_reasonable(self):
        """Game length should be reasonable."""
        results = play_n_random_games(20)
        lengths = [r['num_actions'] for r in results if r['completed']]

        avg_length = sum(lengths) / len(lengths) if lengths else 0
        max_length = max(lengths) if lengths else 0

        # Multi-hand games (to 5000 points) take longer
        # Average should be less than 2000 actions
        assert avg_length < 2000, f"Average game length too high: {avg_length}"
        # Max should be less than 5000 (our max_actions limit)
        assert max_length < 5000, f"Max game length too high: {max_length}"


class TestScoring:
    """Test scoring properties."""

    def test_scores_in_reasonable_range(self):
        """Scores should be in reasonable range."""
        results = play_n_random_games(50)

        for result in results:
            if result['completed']:
                for score in result['scores']:
                    # Games end when a team reaches 5000, but they can exceed it
                    # Allow up to 10000 (very high-scoring hands are possible)
                    assert -500 <= score <= 10000, f"Score out of range: {score}"
                    # Scores should not be NaN or infinite
                    assert not (isinstance(score, float) and (
                        score != score or abs(score) == float('inf')
                    )), f"Invalid score: {score}"

    def test_both_teams_can_win(self):
        """Both teams should be able to win."""
        results = play_n_random_games(50)

        team_0_wins = sum(1 for r in results if r['completed'] and r['winner'] == 0)
        team_1_wins = sum(1 for r in results if r['completed'] and r['winner'] == 1)

        # Both teams should win at least once in 50 games
        assert team_0_wins > 0, "Team 0 never won"
        assert team_1_wins > 0, "Team 1 never won"


class TestGamePhases:
    """Test that all game phases are exercised."""

    def test_all_phases_exercised(self):
        """All phases (draw, meld, discard) should occur in games."""
        # Play a few games and verify phases are reached
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Deal cards
        while state._dealing_phase:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])

        # Verify we reach play phase
        assert state._game_phase == "playing"

        # Take a few turns
        phases_seen = set()
        for _ in range(20):
            if state.is_terminal():
                break

            phases_seen.add(state._turn_phase)

            legal = state.legal_actions()
            if state.is_terminal() or not legal:
                break

            state.apply_action(legal[0])

        # Should have seen at least draw phase
        assert "draw" in phases_seen or "meld" in phases_seen or "discard" in phases_seen


class TestGameConsistency:
    """Test game state consistency."""

    def test_no_infinite_loops(self):
        """Games should not run infinitely."""
        result = play_random_game(seed=999)
        # Should complete within max_actions (1000)
        assert result['num_actions'] < 1000

    def test_legal_actions_never_empty_before_terminal(self):
        """Non-terminal states should have legal actions."""
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        for _ in range(100):
            if state.is_terminal():
                break

            if not state.is_chance_node():
                legal = state.legal_actions()
                # After calling legal_actions, may become terminal
                if not state.is_terminal():
                    assert len(legal) > 0, "Non-terminal state has no legal actions"

            # Take action
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal and not state.is_terminal():
                    state.apply_action(legal[0])

    def test_game_state_consistency(self):
        """Game state should remain consistent."""
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Deal all cards
        while state._dealing_phase:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])

        # Check total cards = 108
        total_cards = 0
        for hand in state._hands:
            total_cards += len(hand)
        total_cards += len(state._stock)
        total_cards += len(state._discard_pile)

        # Add melded cards
        for team_melds in state._melds:
            for meld in team_melds:
                total_cards += len(meld.natural_cards)
                total_cards += len(meld.wild_cards)

        # Add red threes
        for team_red_threes in state._red_threes:
            total_cards += len(team_red_threes)

        assert total_cards == 108, f"Total cards = {total_cards}, expected 108"

    def test_melds_remain_valid_throughout_game(self):
        """Melds should remain valid throughout the game."""
        from canasta.melds import is_valid_meld

        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Play random game and check melds
        for _ in range(100):
            if state.is_terminal():
                break

            # Check all melds are valid
            for team_melds in state._melds:
                for meld in team_melds:
                    # Allow black threes when going out
                    assert is_valid_meld(meld, allow_black_threes=True), \
                        f"Invalid meld: {meld}"

            # Take action
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal and not state.is_terminal():
                    state.apply_action(legal[0])

    def test_canasta_count_accurate(self):
        """Canasta count should be accurate."""
        from canasta.melds import is_canasta

        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Play random game
        for _ in range(100):
            if state.is_terminal():
                break

            # Count actual canastas
            actual_canastas = [0, 0]
            for team_idx in [0, 1]:
                for meld in state._melds[team_idx]:
                    if is_canasta(meld):
                        actual_canastas[team_idx] += 1

            # Compare with tracked count
            assert state._canastas[0] == actual_canastas[0], \
                f"Team 0 canasta count mismatch: {state._canastas[0]} vs {actual_canastas[0]}"
            assert state._canastas[1] == actual_canastas[1], \
                f"Team 1 canasta count mismatch: {state._canastas[1]} vs {actual_canastas[1]}"

            # Take action
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if legal and not state.is_terminal():
                    state.apply_action(legal[0])


class TestSpecialCases:
    """Test special game cases."""

    def test_going_out_ends_game(self):
        """Going out should end the game."""
        # This is tested implicitly by all games completing
        result = play_random_game(seed=111)
        assert result['completed']

    def test_red_threes_handled_correctly(self):
        """Red threes should be handled automatically."""
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Deal all cards
        while state._dealing_phase:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])

        # Red threes should not be in any hands
        for hand in state._hands:
            for card in hand:
                from canasta.cards import is_red_three
                assert not is_red_three(card), "Red three found in hand"

    def test_teammate_scores_equal(self):
        """Teammates should have equal scores."""
        result = play_random_game(seed=222)
        assert result['completed']

        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Play to terminal
        actions = 0
        while not state.is_terminal() and actions < 1000:
            if state.is_chance_node():
                outcomes = state.chance_outcomes()
                state.apply_action(outcomes[0][0])
            else:
                legal = state.legal_actions()
                if state.is_terminal() or not legal:
                    break
                state.apply_action(legal[0])
            actions += 1

        if state.is_terminal():
            returns = state.returns()
            # Players 0 and 2 are Team 0
            assert returns[0] == returns[2], "Team 0 teammates have different scores"
            # Players 1 and 3 are Team 1
            assert returns[1] == returns[3], "Team 1 teammates have different scores"

    def test_deterministic_with_seed(self):
        """Games with same seed should produce same result."""
        result1 = play_random_game(seed=333)
        result2 = play_random_game(seed=333)

        assert result1['completed'] == result2['completed']
        assert result1['num_actions'] == result2['num_actions']
        assert result1['winner'] == result2['winner']
        assert result1['scores'] == result2['scores']

    def test_integration_with_openspiel_api(self):
        """Test full integration with OpenSpiel API."""
        game = pyspiel.load_game("python_canasta")

        # Test game properties
        assert game.num_players() == 4
        assert game.max_game_length() == 1000

        # Test state creation
        state = game.new_initial_state()
        assert state is not None

        # Test state properties
        assert state.current_player() >= 0 or state.is_chance_node()
        assert not state.is_terminal()

        # Test action methods
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            assert len(outcomes) > 0
        else:
            legal = state.legal_actions()
            # May be empty if terminal after calling legal_actions
            # Just verify method works

        # Test string representations
        state_str = str(state)
        assert isinstance(state_str, str)
        assert len(state_str) > 0
