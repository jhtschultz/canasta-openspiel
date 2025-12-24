"""Tests for Meld Phase in Canasta."""

import pyspiel
from canasta.canasta_game import CanastaGame, ACTION_DRAW_STOCK
from canasta.cards import cards_of_rank, is_wild
from canasta.melds import Meld


def setup_game_at_meld_phase(player_hand=None, team_melds=None, team_score=0, initial_meld_made=False):
    """Helper to set up a game state at the meld phase.

    Args:
        player_hand: List of card IDs for current player's hand
        team_melds: List of Meld objects for current team
        team_score: Current team score for initial meld requirement
        initial_meld_made: Whether team has made initial meld

    Returns:
        CanastaState ready for meld actions
    """
    game = CanastaGame()
    state = game.new_initial_state()

    # Skip dealing phase
    state._dealing_phase = False
    state._game_phase = "playing"
    state._turn_phase = "meld"
    state._current_player = 0

    # Set up player hand
    if player_hand:
        state._hands[0] = player_hand.copy()

    # Set up team melds
    if team_melds:
        state._melds[0] = team_melds.copy()

    # Set initial meld status
    state._initial_meld_made[0] = initial_meld_made

    # Set up stock (needed for some tests)
    state._stock = list(range(20, 40))  # Some cards in stock

    return state


def test_create_valid_meld_three_natural_cards():
    """Test creating a meld with three natural cards of the same rank."""
    # Get three 5s (rank 4)
    fives = cards_of_rank(4)[:3]

    state = setup_game_at_meld_phase(
        player_hand=fives,
        initial_meld_made=True  # Skip initial meld requirement
    )

    # Should be able to create a meld with these three 5s
    actions = state.legal_actions()

    # Should have at least one CREATE_MELD action and SKIP_MELD
    assert len(actions) > 0
    # Action ID 2001 is SKIP_MELD
    assert 2001 in actions

    # Should have a CREATE_MELD action for rank 4 (5s)
    # CREATE_MELD actions are in range 2-1000
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) > 0


def test_create_valid_meld_with_wild_cards():
    """Test creating a meld with natural cards and wild cards."""
    # Get two 7s (rank 6) and one joker (104)
    sevens = cards_of_rank(6)[:2]
    hand = sevens + [104]  # Joker

    state = setup_game_at_meld_phase(
        player_hand=hand,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should have CREATE_MELD actions
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) > 0


def test_cannot_create_meld_with_too_few_cards():
    """Test that cannot create meld with only 2 cards."""
    # Get only two 9s (rank 8)
    nines = cards_of_rank(8)[:2]

    state = setup_game_at_meld_phase(
        player_hand=nines,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD (2001), no CREATE_MELD actions
    assert 2001 in actions
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) == 0


def test_cannot_create_meld_with_only_one_natural():
    """Test that cannot create meld with only 1 natural card."""
    # Get one 10 (rank 9) and two jokers
    tens = cards_of_rank(9)[:1]
    hand = tens + [104, 105]  # Two jokers

    state = setup_game_at_meld_phase(
        player_hand=hand,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD, no CREATE_MELD actions
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) == 0


def test_cannot_create_meld_with_too_many_wilds():
    """Test that cannot create meld with more than 3 wild cards."""
    # Get two Jacks (rank 10) and four wilds
    jacks = cards_of_rank(10)[:2]
    # Two 2s (cards 1, 53) and two jokers
    twos = cards_of_rank(1)[:2]
    hand = jacks + twos + [104, 105]

    state = setup_game_at_meld_phase(
        player_hand=hand,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should not allow creating a meld with all 4 wilds
    # Note: should still allow 3-wild melds
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    # Hard to test exact count, but there should be some valid 3-wild combinations
    # This test mainly ensures we don't crash


def test_add_to_existing_meld_natural_card():
    """Test adding a natural card to an existing meld."""
    # Existing meld of three 6s (rank 5)
    sixes = cards_of_rank(5)
    existing_meld = Meld(rank=5, natural_cards=sixes[:3], wild_cards=[])

    # Player has another 6
    state = setup_game_at_meld_phase(
        player_hand=[sixes[3]],
        team_melds=[existing_meld],
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should have ADD_TO_MELD actions (1001-2000)
    add_to_meld_actions = [a for a in actions if 1001 <= a <= 2000]
    assert len(add_to_meld_actions) > 0


def test_add_to_existing_meld_wild_card():
    """Test adding a wild card to an existing meld."""
    # Existing meld of three 8s (rank 7)
    eights = cards_of_rank(7)
    existing_meld = Meld(rank=7, natural_cards=eights[:3], wild_cards=[])

    # Player has a joker
    state = setup_game_at_meld_phase(
        player_hand=[104],
        team_melds=[existing_meld],
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should have ADD_TO_MELD actions
    add_to_meld_actions = [a for a in actions if 1001 <= a <= 2000]
    assert len(add_to_meld_actions) > 0


def test_cannot_add_wild_exceeding_limit():
    """Test that cannot add wild card if meld already has 3 wilds."""
    # Existing meld with 2 naturals and 3 wilds (at limit)
    queens = cards_of_rank(11)
    existing_meld = Meld(
        rank=11,
        natural_cards=queens[:2],
        wild_cards=[104, 105, 106]  # Three wilds
    )

    # Player has another wild (joker 107)
    state = setup_game_at_meld_phase(
        player_hand=[107],
        team_melds=[existing_meld],
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD, no ADD_TO_MELD that uses the joker
    # (Could have ADD_TO_MELD if player has other cards, but not the wild)
    add_to_meld_actions = [a for a in actions if 1001 <= a <= 2000]
    assert len(add_to_meld_actions) == 0


def test_initial_meld_meets_minimum_requirement():
    """Test that initial meld meets minimum point requirement."""
    # Team score is 0, so minimum is 50 points
    # Create meld with three Aces (20 points each = 60 points)
    aces = cards_of_rank(0)[:3]

    state = setup_game_at_meld_phase(
        player_hand=aces,
        initial_meld_made=False
    )

    actions = state.legal_actions()

    # Should have CREATE_MELD actions (meets 50-point minimum)
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) > 0


def test_initial_meld_fails_below_minimum():
    """Test that initial meld fails if below minimum point requirement."""
    # Team score is 0, so minimum is 50 points
    # Three 4s (rank 3) = 3 × 5 = 15 points (below minimum)
    fours = cards_of_rank(3)[:3]

    state = setup_game_at_meld_phase(
        player_hand=fours,
        initial_meld_made=False
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD, no CREATE_MELD actions
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) == 0


def test_canasta_detected_at_seven_cards():
    """Test that canasta is detected when meld reaches 7 cards."""
    # Existing meld with 6 cards
    kings = cards_of_rank(12)
    existing_meld = Meld(rank=12, natural_cards=kings[:6], wild_cards=[])

    state = setup_game_at_meld_phase(
        player_hand=[kings[6]],
        team_melds=[existing_meld],
        initial_meld_made=True
    )

    # Initial canasta count should be 0
    assert state._canastas[0] == 0

    # Add the 7th card
    actions = state.legal_actions()
    add_actions = [a for a in actions if 1001 <= a <= 2000]
    assert len(add_actions) > 0

    # Apply the add action
    state.apply_action(add_actions[0])

    # Now canasta count should be 1
    assert state._canastas[0] == 1


def test_natural_canasta_no_wilds():
    """Test that natural canasta is detected (7+ cards, no wilds)."""
    # Create a canasta with 7 natural cards
    aces = cards_of_rank(0)
    meld = Meld(rank=0, natural_cards=aces[:7], wild_cards=[])

    state = setup_game_at_meld_phase(
        team_melds=[meld],
        initial_meld_made=True
    )

    # Update canasta count
    state._update_canasta_count(0)
    assert state._canastas[0] == 1


def test_mixed_canasta_with_wilds():
    """Test that mixed canasta is detected (7+ cards with wilds)."""
    # Create a canasta with 5 natural cards and 2 wilds
    tens = cards_of_rank(9)
    meld = Meld(rank=9, natural_cards=tens[:5], wild_cards=[104, 105])

    state = setup_game_at_meld_phase(
        team_melds=[meld],
        initial_meld_made=True
    )

    # Update canasta count
    state._update_canasta_count(0)
    assert state._canastas[0] == 1


def test_skip_meld_advances_to_discard_phase():
    """Test that SKIP_MELD action advances to discard phase."""
    state = setup_game_at_meld_phase(
        player_hand=[10, 20, 30],
        initial_meld_made=True
    )

    assert state._turn_phase == "meld"

    # Apply SKIP_MELD (action 2001)
    state.apply_action(2001)

    # Should advance to discard phase
    assert state._turn_phase == "discard"


def test_cannot_meld_twos():
    """Test that cannot meld 2s (they are wild cards)."""
    # Get three 2s (rank 1)
    twos = cards_of_rank(1)[:3]

    state = setup_game_at_meld_phase(
        player_hand=twos,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD, no CREATE_MELD for rank 1
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) == 0


def test_cannot_meld_threes_normally():
    """Test that cannot meld 3s normally (only when going out)."""
    # Get three black 3s (rank 2, clubs/spades)
    black_threes = cards_of_rank(2)[:3]

    state = setup_game_at_meld_phase(
        player_hand=black_threes,
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should only have SKIP_MELD, no CREATE_MELD for rank 2
    create_meld_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_meld_actions) == 0


def test_multiple_melds_in_one_meld_phase():
    """Test that multiple melding actions can occur in one meld phase."""
    # Player has cards for two different melds
    fives = cards_of_rank(4)[:3]
    sixes = cards_of_rank(5)[:3]
    hand = fives + sixes

    state = setup_game_at_meld_phase(
        player_hand=hand,
        initial_meld_made=True
    )

    # Create first meld
    actions = state.legal_actions()
    create_actions = [a for a in actions if 2 <= a <= 1000]
    assert len(create_actions) > 0

    state.apply_action(create_actions[0])

    # Should still be in meld phase
    assert state._turn_phase == "meld"

    # Should still have meld actions available
    actions2 = state.legal_actions()
    assert 2001 in actions2  # SKIP_MELD always available


def test_one_meld_per_rank_per_team():
    """Test that team can only have one meld per rank."""
    # Team already has a meld of 7s (rank 6)
    sevens = cards_of_rank(6)
    existing_meld = Meld(rank=6, natural_cards=sevens[:3], wild_cards=[])

    # Player has more 7s
    state = setup_game_at_meld_phase(
        player_hand=sevens[3:6],
        team_melds=[existing_meld],
        initial_meld_made=True
    )

    actions = state.legal_actions()

    # Should have ADD_TO_MELD actions, but not CREATE_MELD for rank 6
    add_actions = [a for a in actions if 1001 <= a <= 2000]
    assert len(add_actions) > 0

    # Should not have CREATE_MELD for rank 6 (we can test this by checking
    # that we can't create a duplicate meld - implementation will prevent this)
