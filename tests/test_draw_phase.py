"""Tests for the draw phase of Canasta gameplay."""

import pytest
import pyspiel

from canasta.cards import is_red_three, is_wild, is_black_three, rank_of
from canasta.deck import HAND_SIZE


@pytest.fixture
def game():
    """Create a Canasta game instance."""
    return pyspiel.load_game("python_canasta")


@pytest.fixture
def state_after_deal(game):
    """Create a game state after dealing is complete."""
    state = game.new_initial_state()

    # Simulate dealing by applying chance actions until dealing phase is done
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            # Choose first action (deterministic for testing)
            state.apply_action(actions[0])
        else:
            break

    return state


def test_draw_from_stock_reduces_stock_size(state_after_deal):
    """Drawing from stock should reduce stock size by 1."""
    initial_stock_size = len(state_after_deal._stock)

    # Should be in draw phase at start of turn
    assert state_after_deal._turn_phase == "draw"

    # Draw from stock (action 0)
    state_after_deal.apply_action(0)

    assert len(state_after_deal._stock) == initial_stock_size - 1


def test_draw_from_stock_adds_card_to_hand(state_after_deal):
    """Drawing from stock should add card to current player's hand."""
    player = state_after_deal.current_player()
    initial_hand_size = len(state_after_deal._hands[player])

    # Draw from stock (action 0)
    state_after_deal.apply_action(0)

    # If card was not a red 3, hand size increases by 1
    # Red 3s are auto-replaced, so hand size might stay same or increase
    # At minimum, hand should not decrease
    assert len(state_after_deal._hands[player]) >= initial_hand_size


def test_cannot_draw_from_empty_stock(game):
    """Cannot draw from stock when it's empty."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    # Empty the stock
    state._stock = []
    state._turn_phase = "draw"

    # Action 0 (draw stock) should not be legal
    legal = state.legal_actions()
    assert 0 not in legal


def test_take_pile_with_matching_cards(game):
    """Can take pile when holding matching cards and pile not frozen."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    # Set up scenario: player has two cards matching top of pile
    player = state.current_player()

    # Create a simple scenario: discard pile has a 4, player has two 4s
    # Find cards of rank 4 (rank index 3)
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)

    # Set up discard pile with one 4
    state._discard_pile = [rank_4_cards[0]]

    # Give player two other 4s
    state._hands[player] = [rank_4_cards[1], rank_4_cards[2]]

    # Ensure pile is not frozen
    state._pile_frozen = False
    state._initial_meld_made[player % 2] = True
    state._turn_phase = "draw"

    # Action 1 (take pile) should be legal
    legal = state.legal_actions()
    assert 1 in legal


def test_cannot_take_pile_without_matching_cards(game):
    """Cannot take pile without matching cards."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()

    # Set up discard pile with a 4
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)
    state._discard_pile = [rank_4_cards[0]]

    # Give player cards that don't match (two 5s)
    rank_5_cards = cards_of_rank(4)
    state._hands[player] = [rank_5_cards[0], rank_5_cards[1]]

    # Ensure pile is not frozen
    state._pile_frozen = False
    state._initial_meld_made[player % 2] = True
    state._turn_phase = "draw"

    # Action 1 (take pile) should NOT be legal
    legal = state.legal_actions()
    assert 1 not in legal


def test_frozen_pile_requires_two_natural_cards(game):
    """Frozen pile requires two natural matching cards in hand."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()

    # Set up discard pile with a 4
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)
    state._discard_pile = [rank_4_cards[0]]

    # Give player one natural 4 and one wild card
    # Wild card: 2 (rank index 1)
    rank_2_cards = cards_of_rank(1)
    state._hands[player] = [rank_4_cards[1], rank_2_cards[0]]

    # Freeze the pile
    state._pile_frozen = True
    state._turn_phase = "draw"

    # Cannot take pile with only one natural matching card
    legal = state.legal_actions()
    assert 1 not in legal


def test_frozen_pile_allows_take_with_two_naturals(game):
    """Frozen pile can be taken with two natural matching cards."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()

    # Set up discard pile with a 4
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)
    state._discard_pile = [rank_4_cards[0]]

    # Give player two natural 4s
    state._hands[player] = [rank_4_cards[1], rank_4_cards[2]]

    # Freeze the pile
    state._pile_frozen = True
    state._turn_phase = "draw"

    # Can take pile with two naturals
    legal = state.legal_actions()
    assert 1 in legal


def test_wild_card_in_pile_freezes_it(game):
    """Discarding a wild card freezes the pile."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    # Add a wild card to discard pile
    from canasta.cards import cards_of_rank
    rank_2_cards = cards_of_rank(1)  # 2s are wild
    state._discard_pile = [rank_2_cards[0]]

    # Pile should be frozen
    assert state._is_pile_frozen()


def test_no_initial_meld_freezes_pile_for_team(game):
    """Pile is frozen for team that hasn't made initial meld."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2

    # Team hasn't made initial meld
    state._initial_meld_made[team] = False

    # Add non-wild card to pile
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)
    state._discard_pile = [rank_4_cards[0]]

    # Pile should be frozen for this team
    assert state._is_pile_frozen()


def test_initial_meld_made_unfreezes_pile_for_team(game):
    """Pile is not frozen for team that has made initial meld (unless wild in pile)."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2

    # Team has made initial meld
    state._initial_meld_made[team] = True

    # Add non-wild card to pile
    from canasta.cards import cards_of_rank
    rank_4_cards = cards_of_rank(3)
    state._discard_pile = [rank_4_cards[0]]

    # Pile should NOT be frozen for this team
    assert not state._is_pile_frozen()


def test_can_take_pile_by_adding_to_existing_meld(game):
    """Can take pile if top card can be added to existing team meld."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2

    # Create existing meld of 4s for the team
    from canasta.cards import cards_of_rank
    from canasta.melds import Meld
    rank_4_cards = cards_of_rank(3)
    state._melds[team] = [Meld(rank=3, natural_cards=[rank_4_cards[0], rank_4_cards[1], rank_4_cards[2]], wild_cards=[])]

    # Top of pile is a 4
    state._discard_pile = [rank_4_cards[3]]

    # Player has a natural 4 to add
    state._hands[player] = [rank_4_cards[4]]

    # Pile not frozen
    state._pile_frozen = False
    state._initial_meld_made[team] = True
    state._turn_phase = "draw"

    # Should be able to take pile
    legal = state.legal_actions()
    assert 1 in legal


def test_cannot_take_frozen_pile_by_adding_to_meld(game):
    """Cannot take frozen pile by adding to existing meld - need two naturals."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2

    # Create existing meld of 4s for the team
    from canasta.cards import cards_of_rank
    from canasta.melds import Meld
    rank_4_cards = cards_of_rank(3)
    state._melds[team] = [Meld(rank=3, natural_cards=[rank_4_cards[0], rank_4_cards[1], rank_4_cards[2]], wild_cards=[])]

    # Top of pile is a 4
    state._discard_pile = [rank_4_cards[3]]

    # Player has only one natural 4
    state._hands[player] = [rank_4_cards[4]]

    # Pile IS frozen
    state._pile_frozen = True
    state._turn_phase = "draw"

    # Should NOT be able to take pile (need two naturals)
    legal = state.legal_actions()
    assert 1 not in legal


def test_draw_red_three_auto_replaces(game):
    """Drawing a red 3 from stock auto-replaces it."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2
    initial_hand_size = len(state._hands[player])

    # Put a red 3 on top of stock
    from canasta.cards import cards_of_rank
    rank_3_cards = cards_of_rank(2)
    red_three = None
    for card in rank_3_cards:
        if is_red_three(card):
            red_three = card
            break

    assert red_three is not None

    # Set up stock with red 3 first, then replacement card
    # (Drawing from stock uses pop(0), so first item is drawn first)
    rank_4_cards = cards_of_rank(3)
    state._stock = [red_three, rank_4_cards[0]]

    state._turn_phase = "draw"

    # Draw from stock
    state.apply_action(0)

    # Red 3 should be in team's red threes, not in hand
    assert red_three in state._red_threes[team]
    assert red_three not in state._hands[player]

    # Hand should have the replacement card
    assert len(state._hands[player]) == initial_hand_size + 1


def test_take_pile_with_red_threes(game):
    """Taking pile with red 3s processes them correctly."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    player = state.current_player()
    team = player % 2

    # Set up pile with a red 3 and a 4
    from canasta.cards import cards_of_rank
    rank_3_cards = cards_of_rank(2)
    rank_4_cards = cards_of_rank(3)

    red_three = None
    for card in rank_3_cards:
        if is_red_three(card):
            red_three = card
            break

    # Pile has a 4 on top, red 3 underneath
    state._discard_pile = [red_three, rank_4_cards[0]]

    # Player has two natural 4s
    state._hands[player] = [rank_4_cards[1], rank_4_cards[2]]

    state._pile_frozen = False
    state._initial_meld_made[team] = True
    state._turn_phase = "draw"

    # Take pile
    state.apply_action(1)

    # Red 3 should be in team's red threes
    assert red_three in state._red_threes[team]
    assert red_three not in state._hands[player]


def test_black_three_blocks_next_player_from_pile(game):
    """Black 3 on top of pile blocks next player from taking pile."""
    state = game.new_initial_state()

    # Deal all cards
    while state.current_player() == pyspiel.PlayerId.CHANCE:
        actions = state.legal_actions()
        if actions:
            state.apply_action(actions[0])
        else:
            break

    # Set up pile with black 3 on top
    from canasta.cards import cards_of_rank
    rank_3_cards = cards_of_rank(2)

    black_three = None
    for card in rank_3_cards:
        if is_black_three(card):
            black_three = card
            break

    state._discard_pile = [black_three]

    # Player has matching black 3s (doesn't matter, can't take)
    state._hands[state.current_player()] = [rank_3_cards[0], rank_3_cards[1]]

    state._pile_frozen = False
    state._initial_meld_made[state.current_player() % 2] = True
    state._turn_phase = "draw"

    # Should be blocked by black 3
    state._black_three_blocks_next = True

    # Cannot take pile
    legal = state.legal_actions()
    assert 1 not in legal
