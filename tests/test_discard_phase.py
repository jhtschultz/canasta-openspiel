"""Tests for Discard Phase in Canasta."""

import pyspiel
from canasta.canasta_game import CanastaGame
from canasta.cards import cards_of_rank, is_wild, is_black_three


def setup_game_at_discard_phase(player_hand=None, discard_pile=None):
    """Helper to set up a game state at the discard phase.

    Args:
        player_hand: List of card IDs for current player's hand
        discard_pile: List of card IDs already in discard pile

    Returns:
        CanastaState ready for discard actions
    """
    game = CanastaGame()
    state = game.new_initial_state()

    # Skip dealing phase
    state._dealing_phase = False
    state._game_phase = "playing"
    state._turn_phase = "discard"
    state._current_player = 0

    # Set up player hand
    if player_hand:
        state._hands[0] = player_hand.copy()

    # Set up discard pile
    if discard_pile:
        state._discard_pile = discard_pile.copy()

    # Set up stock (needed for turn advancement)
    state._stock = list(range(20, 40))

    return state


def test_discard_removes_card_from_hand():
    """Test that discarding a card removes it from the player's hand."""
    # Player has three 5s
    fives = cards_of_rank(4)[:3]

    state = setup_game_at_discard_phase(player_hand=fives)

    assert len(state._hands[0]) == 3
    assert fives[0] in state._hands[0]

    # Discard the first 5
    discard_action = 2002 + fives[0]
    state.apply_action(discard_action)

    # Card should be removed from hand
    assert len(state._hands[0]) == 2
    assert fives[0] not in state._hands[0]


def test_discard_adds_card_to_pile_top():
    """Test that discarding adds the card to the top of the discard pile."""
    # Player has a 6
    sixes = cards_of_rank(5)
    card_to_discard = sixes[0]

    # Start with empty pile
    state = setup_game_at_discard_phase(
        player_hand=[card_to_discard],
        discard_pile=[]
    )

    assert len(state._discard_pile) == 0

    # Discard the 6
    discard_action = 2002 + card_to_discard
    state.apply_action(discard_action)

    # Card should be at top of pile
    assert len(state._discard_pile) == 1
    assert state._discard_pile[-1] == card_to_discard


def test_wild_card_discard_freezes_pile():
    """Test that discarding a wild card (2) freezes the pile."""
    # Player has a 2 (rank 1)
    twos = cards_of_rank(1)
    wild_card = twos[0]

    state = setup_game_at_discard_phase(player_hand=[wild_card])

    assert state._pile_frozen == False

    # Discard the 2
    discard_action = 2002 + wild_card
    state.apply_action(discard_action)

    # Pile should now be frozen
    assert state._pile_frozen == True


def test_joker_discard_freezes_pile():
    """Test that discarding a joker freezes the pile."""
    # Player has a joker (card 104)
    joker = 104

    state = setup_game_at_discard_phase(player_hand=[joker])

    assert state._pile_frozen == False

    # Discard the joker
    discard_action = 2002 + joker
    state.apply_action(discard_action)

    # Pile should now be frozen
    assert state._pile_frozen == True


def test_black_three_discard_sets_blocking_flag():
    """Test that discarding a black 3 sets the blocking flag."""
    # Player has a black 3 (rank 2, clubs or spades)
    black_threes = cards_of_rank(2)
    # Get a black 3 (clubs or spades)
    black_three = black_threes[0]  # Should be clubs
    assert is_black_three(black_three)

    state = setup_game_at_discard_phase(player_hand=[black_three])

    assert state._black_three_blocks_next == False

    # Discard the black 3
    discard_action = 2002 + black_three
    state.apply_action(discard_action)

    # Blocking flag should be set
    assert state._black_three_blocks_next == True


def test_black_three_blocks_next_player_only():
    """Test that black 3 blocking only affects the immediate next player."""
    # Player 0 has a black 3
    black_threes = cards_of_rank(2)
    black_three = black_threes[0]

    state = setup_game_at_discard_phase(player_hand=[black_three])
    state._current_player = 0

    # Discard the black 3
    discard_action = 2002 + black_three
    state.apply_action(discard_action)

    # Should advance to player 1
    assert state._current_player == 1
    assert state._black_three_blocks_next == True

    # When player 1 draws from stock (not takes pile), flag should clear
    # This is tested in draw phase, but we verify the flag is set here


def test_cannot_discard_card_not_in_hand():
    """Test that cannot discard a card not in the player's hand."""
    # Player has 5s
    fives = cards_of_rank(4)[:2]

    # Get a different card (a 6)
    sixes = cards_of_rank(5)
    card_not_in_hand = sixes[0]

    state = setup_game_at_discard_phase(player_hand=fives)

    # Try to discard a card not in hand
    discard_action = 2002 + card_not_in_hand

    # This card should not be in legal actions
    legal_actions = state.legal_actions()
    assert discard_action not in legal_actions


def test_turn_advances_after_discard():
    """Test that the turn advances to the next player after discard."""
    # Player 0 has a card
    sevens = cards_of_rank(6)
    card = sevens[0]

    state = setup_game_at_discard_phase(player_hand=[card])
    state._current_player = 0

    # Discard the card
    discard_action = 2002 + card
    state.apply_action(discard_action)

    # Should advance to player 1
    assert state._current_player == 1


def test_phase_returns_to_draw_after_discard():
    """Test that the phase returns to 'draw' after discard."""
    # Player has a card
    eights = cards_of_rank(7)
    card = eights[0]

    state = setup_game_at_discard_phase(player_hand=[card])

    assert state._turn_phase == "discard"

    # Discard the card
    discard_action = 2002 + card
    state.apply_action(discard_action)

    # Phase should return to draw
    assert state._turn_phase == "draw"


def test_discard_natural_card_does_not_freeze():
    """Test that discarding a natural card does not freeze the pile."""
    # Player has a natural card (9)
    nines = cards_of_rank(8)
    natural_card = nines[0]

    state = setup_game_at_discard_phase(player_hand=[natural_card])

    assert state._pile_frozen == False
    assert not is_wild(natural_card)

    # Discard the natural card
    discard_action = 2002 + natural_card
    state.apply_action(discard_action)

    # Pile should remain unfrozen
    assert state._pile_frozen == False


def test_all_cards_can_be_discarded_in_classic():
    """Test that all cards in hand can be discarded (Classic Canasta rule)."""
    # Player has various cards including wilds
    tens = cards_of_rank(9)[:2]
    twos = cards_of_rank(1)[:1]  # Wild
    joker = [104]  # Wild
    hand = tens + twos + joker

    state = setup_game_at_discard_phase(player_hand=hand)

    legal_actions = state.legal_actions()

    # Should have a discard action for each card
    for card in hand:
        discard_action = 2002 + card
        assert discard_action in legal_actions

    # Should have exactly 4 legal actions (one for each card)
    assert len(legal_actions) == 4


def test_discard_is_mandatory_in_discard_phase():
    """Test that player must discard (has legal actions) in discard phase."""
    # Player has cards
    jacks = cards_of_rank(10)[:3]

    state = setup_game_at_discard_phase(player_hand=jacks)

    assert state._turn_phase == "discard"

    legal_actions = state.legal_actions()

    # Should have discard actions
    assert len(legal_actions) > 0

    # All legal actions should be discard actions (2002-2109)
    for action in legal_actions:
        assert 2002 <= action <= 2109
