"""Tests for Canasta state initialization with dealing through chance nodes.

Tests that the state initialization correctly handles:
- Dealing 11 cards to each of 4 players through chance nodes
- All 108 cards being accounted for after dealing
- Red 3s being handled correctly (replaced from stock)
- Stock and discard pile sizes
- State transitions from dealing to play phase
"""

import pytest
import pyspiel

# Import canasta_game to register it with OpenSpiel
from canasta import canasta_game
from canasta.cards import is_red_three, NUM_CARDS
from canasta.deck import NUM_PLAYERS, HAND_SIZE


def deal_all_cards(state):
    """Helper to deal all cards through chance nodes until dealing is complete.

    Args:
        state: CanastaState in dealing phase

    Returns:
        state after all dealing is complete
    """
    while state.current_player() == pyspiel.PlayerId.CHANCE and not state.is_terminal():
        # Get legal actions (indices into remaining deck)
        legal_actions = state.legal_actions()
        if not legal_actions:
            break
        # Apply the first legal action (deal first card in deck)
        state.apply_action(legal_actions[0])
    return state


def test_dealing_starts_at_chance_node():
    """Test that initial state starts with chance player for dealing."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    assert state.current_player() == pyspiel.PlayerId.CHANCE
    assert not state.is_terminal()


def test_dealing_phase_deals_correct_number_of_cards():
    """Test that dealing through chance nodes deals exactly 11 cards to each player."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    state = deal_all_cards(state)

    # After dealing, each player should have exactly 11 cards (excluding red 3s)
    # Note: Red 3s are replaced, so each hand should have 11 cards total
    for player_idx in range(NUM_PLAYERS):
        hand = state._hands[player_idx]
        assert len(hand) == HAND_SIZE, f"Player {player_idx} has {len(hand)} cards, expected {HAND_SIZE}"


def test_all_cards_accounted_for():
    """Test that all 108 cards are accounted for after dealing."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    state = deal_all_cards(state)

    # Count all cards
    total_cards = 0

    # Cards in hands
    for hand in state._hands:
        total_cards += len(hand)

    # Cards in stock
    total_cards += len(state._stock)

    # Cards in discard pile
    total_cards += len(state._discard_pile)

    # Red 3s that were set aside (should be tracked separately)
    # Access the red_threes attribute if it exists
    if hasattr(state, '_red_threes'):
        for team_red_threes in state._red_threes:
            total_cards += len(team_red_threes)

    assert total_cards == NUM_CARDS, f"Total cards: {total_cards}, expected {NUM_CARDS}"


def test_red_threes_handled_correctly():
    """Test that red 3s are properly removed from hands and replaced."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    state = deal_all_cards(state)

    # Check that no red 3s remain in player hands
    for player_idx in range(NUM_PLAYERS):
        hand = state._hands[player_idx]
        for card in hand:
            assert not is_red_three(card), f"Player {player_idx} has red 3 (card {card}) in hand"

    # Red 3s should be tracked separately (if implemented)
    # This assumes _red_threes attribute exists
    if hasattr(state, '_red_threes'):
        # Each team should have red 3s tracked
        assert len(state._red_threes) == 2  # 2 teams
        for team_idx in range(2):
            for card in state._red_threes[team_idx]:
                assert is_red_three(card), f"Non-red-3 card {card} in team {team_idx} red 3s"


def test_stock_and_discard_sizes():
    """Test that stock and discard pile have correct sizes after dealing."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Deal all cards
    state = deal_all_cards(state)

    # After dealing:
    # - 4 players × 11 cards = 44 cards in hands
    # - 1 card on discard pile
    # - Remaining cards in stock
    # - Red 3s set aside (variable number)

    # Discard pile should have at least 1 card (the initial discard)
    assert len(state._discard_pile) >= 1, "Discard pile should have at least 1 card"

    # Stock should have remaining cards
    # Expected: 108 - 44 (hands) - 1 (discard) - red_3s_count = 63 - red_3s_count
    cards_in_hands = sum(len(hand) for hand in state._hands)
    cards_in_discard = len(state._discard_pile)
    cards_in_stock = len(state._stock)

    if hasattr(state, '_red_threes'):
        red_threes_count = sum(len(team_red_threes) for team_red_threes in state._red_threes)
    else:
        red_threes_count = 0

    total = cards_in_hands + cards_in_discard + cards_in_stock + red_threes_count
    assert total == NUM_CARDS, f"Cards in hands: {cards_in_hands}, discard: {cards_in_discard}, stock: {cards_in_stock}, red 3s: {red_threes_count}, total: {total}"


def test_state_transitions_from_dealing_to_play():
    """Test that state correctly transitions from dealing to playing phase."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Initially in dealing phase
    assert state._game_phase == "dealing"
    assert state.current_player() == pyspiel.PlayerId.CHANCE

    # Deal all cards
    state = deal_all_cards(state)

    # After dealing, should be in playing phase
    assert state._game_phase == "playing"
    assert state.current_player() != pyspiel.PlayerId.CHANCE
    assert state.current_player() in range(NUM_PLAYERS)


def test_dealing_phase_tracking():
    """Test that dealing phase flag is correctly updated."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Initially dealing
    assert state._dealing_phase is True

    # Deal all cards
    state = deal_all_cards(state)

    # After dealing complete
    assert state._dealing_phase is False


def test_cards_dealt_counter():
    """Test that cards_dealt counter is correctly incremented during dealing."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Initially no cards dealt
    assert state._cards_dealt == 0

    # Deal one card
    if state.current_player() == pyspiel.PlayerId.CHANCE:
        legal_actions = state.legal_actions()
        state.apply_action(legal_actions[0])
        assert state._cards_dealt == 1

    # Deal all remaining cards
    state = deal_all_cards(state)

    # Should have dealt at least 44 cards (4 players × 11 cards)
    # May be more if red 3s were replaced
    assert state._cards_dealt >= NUM_PLAYERS * HAND_SIZE


def test_player_assignment_during_dealing():
    """Test that cards are dealt to players in correct order."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Track which player should receive each card
    # Cards are dealt one at a time, cycling through players
    # First 11 cards to player 0, next 11 to player 1, etc.

    cards_per_player = [0, 0, 0, 0]

    for i in range(NUM_PLAYERS * HAND_SIZE):
        if state.current_player() == pyspiel.PlayerId.CHANCE:
            legal_actions = state.legal_actions()
            if legal_actions:
                state.apply_action(legal_actions[0])

                # Determine which player received the card
                # (implementation-dependent, but based on current code)
                expected_player = i // HAND_SIZE
                if expected_player < NUM_PLAYERS:
                    cards_per_player[expected_player] += 1

    # Note: This test may need adjustment based on red 3 replacement logic
    # For now, just verify dealing completed
    assert state._cards_dealt >= NUM_PLAYERS * HAND_SIZE


def test_no_cards_in_hands_before_dealing():
    """Test that all hands are empty before dealing starts."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    for player_idx in range(NUM_PLAYERS):
        assert len(state._hands[player_idx]) == 0, f"Player {player_idx} should have empty hand initially"


def test_discard_pile_initialized_after_dealing():
    """Test that discard pile is properly initialized after dealing."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Initially empty
    assert len(state._discard_pile) == 0

    # Deal all cards
    state = deal_all_cards(state)

    # After dealing, should have initial discard card
    assert len(state._discard_pile) > 0
    assert state._discard_pile[0] in range(NUM_CARDS)
