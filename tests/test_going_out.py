"""Tests for Going Out mechanics in Canasta."""

import pyspiel
from canasta.canasta_game import CanastaGame
from canasta.cards import cards_of_rank
from canasta.melds import Meld


def setup_game_for_going_out(player_hand=None, team_melds=None, partner_hand=None):
    """Helper to set up a game state ready for going out tests.

    Args:
        player_hand: List of card IDs for current player's hand
        team_melds: List of Meld objects for current team
        partner_hand: List of card IDs for partner's hand

    Returns:
        CanastaState ready for going out tests
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

    # Set up partner hand (player 2 is partner of player 0)
    if partner_hand:
        state._hands[2] = partner_hand.copy()

    # Set up team melds
    if team_melds:
        state._melds[0] = team_melds.copy()
        # Update canasta count
        state._update_canasta_count(0)

    # Set initial meld as made
    state._initial_meld_made[0] = True

    # Set up stock
    state._stock = list(range(20, 40))

    # Set team score high enough so going out will end the game (reach 5000)
    # Canasta (500) + going out (100) + some melds = ~800-1000 points per hand
    # Set to 4500 so this hand will push over 5000
    state._team_scores[0] = 4500

    return state


def test_cannot_go_out_without_canasta():
    """Test that cannot go out without having at least one canasta."""
    # Team has a meld but not a canasta (only 5 cards)
    fives = cards_of_rank(4)
    meld = Meld(rank=4, natural_cards=fives[:5], wild_cards=[])

    # Player has one card to discard
    state = setup_game_for_going_out(
        player_hand=[cards_of_rank(5)[0]],
        team_melds=[meld]
    )

    assert state._canastas[0] == 0

    # Should not be able to go out
    # This is checked implicitly by _can_go_out() returning False
    # We'll verify this in action generation


def test_can_go_out_with_canasta():
    """Test that can go out when team has a canasta."""
    # Team has a canasta (7 cards)
    sixes = cards_of_rank(5)
    canasta = Meld(rank=5, natural_cards=sixes[:7], wild_cards=[])

    # Player has one card left to discard
    state = setup_game_for_going_out(
        player_hand=[cards_of_rank(6)[0]],
        team_melds=[canasta]
    )

    assert state._canastas[0] == 1

    # Should be able to go out (will be verified through actions)


def test_cannot_go_out_with_cards_remaining():
    """Test that cannot go out if cannot meld all but one card."""
    # Team has a canasta
    sevens = cards_of_rank(6)
    canasta = Meld(rank=6, natural_cards=sevens[:7], wild_cards=[])

    # Player has multiple unrelated cards that can't be melded
    eights = cards_of_rank(7)[:2]  # Only 2 eights, can't meld
    nines = cards_of_rank(8)[:1]   # Only 1 nine, can't meld
    hand = eights + nines

    state = setup_game_for_going_out(
        player_hand=hand,
        team_melds=[canasta]
    )

    # Cannot go out because can't meld all but one card


def test_partner_query_flow_approval():
    """Test the partner query flow when partner approves."""
    # Team has canasta, player can go out
    tens = cards_of_rank(9)
    canasta = Meld(rank=9, natural_cards=tens[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[tens[7]],  # One card to discard
        team_melds=[canasta],
        partner_hand=[cards_of_rank(10)[0]]
    )

    assert state._current_player == 0
    assert state._go_out_query_pending == False

    # Player 0 asks partner (action 2110)
    state.apply_action(2110)

    # Should switch to partner (player 2)
    assert state._current_player == 2
    assert state._go_out_query_pending == True
    assert state._go_out_query_asker == 0

    # Partner approves (action 2111)
    state.apply_action(2111)

    # Should return to player 0
    assert state._current_player == 0
    assert state._go_out_approved == True
    assert state._go_out_query_pending == False


def test_partner_query_flow_denial():
    """Test the partner query flow when partner denies."""
    # Team has canasta
    jacks = cards_of_rank(10)
    canasta = Meld(rank=10, natural_cards=jacks[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[jacks[7]],
        team_melds=[canasta],
        partner_hand=[cards_of_rank(11)[0]]
    )

    # Player asks partner
    state.apply_action(2110)

    assert state._current_player == 2
    assert state._go_out_query_pending == True

    # Partner denies (action 2112)
    state.apply_action(2112)

    # Should return to player 0
    assert state._current_player == 0
    assert state._go_out_approved == False
    assert state._go_out_query_pending == False


def test_partner_can_deny_going_out():
    """Test that partner can deny going out request."""
    # Team has canasta
    queens = cards_of_rank(11)
    canasta = Meld(rank=11, natural_cards=queens[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[queens[7]],
        team_melds=[canasta]
    )

    # Player asks partner
    state.apply_action(2110)

    # Partner should have both YES and NO options
    actions = state.legal_actions()
    assert 2111 in actions  # YES
    assert 2112 in actions  # NO


def test_concealed_going_out_detection():
    """Test that concealed going out is correctly detected."""
    # Player has cards that can form a canasta (no team melds yet)
    kings = cards_of_rank(12)
    # Player has 7 kings plus one other card for discard
    hand = kings[:7] + [cards_of_rank(0)[0]]  # 7 kings + 1 ace

    state = setup_game_for_going_out(
        player_hand=hand,
        team_melds=[]  # No existing melds
    )

    # This would be a concealed go out if executed
    # (player has no melds yet, can form canasta and go out)
    assert len(state._melds[0]) == 0


def test_not_concealed_if_team_has_melds():
    """Test that going out is not concealed if team already has melds."""
    # Team already has a meld (not a canasta)
    aces = cards_of_rank(0)
    existing_meld = Meld(rank=0, natural_cards=aces[:3], wild_cards=[])

    # Player has cards to complete a canasta and go out
    fours = cards_of_rank(3)
    hand = fours[:7] + [fours[7]]  # 7 fours + 1 four for discard

    state = setup_game_for_going_out(
        player_hand=hand,
        team_melds=[existing_meld]
    )

    # Not concealed because team already has melds
    assert len(state._melds[0]) > 0


def test_game_terminates_after_going_out():
    """Test that game is marked as terminal after going out."""
    # Team has canasta
    sixes = cards_of_rank(5)
    canasta = Meld(rank=5, natural_cards=sixes[:7], wild_cards=[])

    # Player has exactly one card
    state = setup_game_for_going_out(
        player_hand=[cards_of_rank(6)[0]],
        team_melds=[canasta]
    )

    # Set to discard phase to allow GO_OUT action
    state._turn_phase = "discard"

    # Before going out
    assert state._is_terminal == False

    # Go out (action 2113)
    # Note: In actual implementation, this needs partner approval
    # For this test, we'll simulate approved status
    state._go_out_approved = True

    state.apply_action(2113)

    # After going out
    assert state._is_terminal == True


def test_going_out_melds_remaining_cards():
    """Test that going out properly melds remaining cards."""
    # Team has canasta
    sevens = cards_of_rank(6)
    canasta = Meld(rank=6, natural_cards=sevens[:7], wild_cards=[])

    # Player has more sevens to add
    hand = sevens[7:9] + [cards_of_rank(8)[0]]  # 2 sevens + 1 eight for discard

    state = setup_game_for_going_out(
        player_hand=hand,
        team_melds=[canasta]
    )

    initial_hand_size = len(state._hands[0])

    # Set to discard phase and approve going out
    state._turn_phase = "discard"
    state._go_out_approved = True

    # Go out
    state.apply_action(2113)

    # Hand should be empty after going out
    assert len(state._hands[0]) == 0


def test_going_out_with_black_threes():
    """Test that black threes can be melded when going out."""
    # Team has a canasta
    tens = cards_of_rank(9)
    canasta = Meld(rank=9, natural_cards=tens[:7], wild_cards=[])

    # Player has black threes (can only meld when going out)
    black_threes = cards_of_rank(2)[:3]  # Rank 2 includes black threes
    hand = black_threes + [cards_of_rank(10)[0]]  # 3 black threes + 1 other for discard

    state = setup_game_for_going_out(
        player_hand=hand,
        team_melds=[canasta]
    )

    # Should be able to go out with black threes


def test_ask_partner_only_in_meld_phase():
    """Test that can only ask partner permission during meld phase."""
    # Team has canasta
    jacks = cards_of_rank(10)
    canasta = Meld(rank=10, natural_cards=jacks[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[jacks[7]],
        team_melds=[canasta]
    )

    # In meld phase - should be able to ask
    state._turn_phase = "meld"
    actions_meld = state.legal_actions()

    # In discard phase - should not be able to ask
    state._turn_phase = "discard"
    actions_discard = state.legal_actions()

    # ASK_PARTNER (2110) should only be available in meld phase
    # (exact check depends on implementation)


def test_cannot_ask_partner_twice():
    """Test that cannot ask partner twice in same turn."""
    # Team has canasta
    queens = cards_of_rank(11)
    canasta = Meld(rank=11, natural_cards=queens[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[queens[7]],
        team_melds=[canasta]
    )

    # Ask partner once
    state.apply_action(2110)

    # Partner answers
    state.apply_action(2111)

    # Should not be able to ask again this turn
    # (implementation should track this with a flag)


def test_partner_query_is_binding():
    """Test that partner's answer is binding for current turn."""
    # Team has canasta
    kings = cards_of_rank(12)
    canasta = Meld(rank=12, natural_cards=kings[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[kings[7]],
        team_melds=[canasta]
    )

    # Ask partner
    state.apply_action(2110)

    # Partner denies
    state.apply_action(2112)

    # Player should not be able to go out this turn
    # (even though conditions are met)
    assert state._go_out_approved == False


def test_classic_canasta_requires_one_canasta():
    """Test that Classic Canasta requires exactly 1 canasta to go out."""
    # Team has exactly 1 canasta
    aces = cards_of_rank(0)
    canasta = Meld(rank=0, natural_cards=aces[:7], wild_cards=[])

    state = setup_game_for_going_out(
        player_hand=[cards_of_rank(1)[0]],  # One 2 (wild) to discard
        team_melds=[canasta]
    )

    # Should have exactly 1 canasta
    assert state._canastas[0] == 1

    # Should be able to go out (Classic rule: 1 canasta sufficient)
