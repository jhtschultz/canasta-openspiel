"""Tests for Canasta scoring module."""
import pytest
from canasta.scoring import (
    calculate_card_points,
    calculate_meld_bonuses,
    calculate_red_three_bonus,
    calculate_going_out_bonus,
    calculate_hand_score,
)
from canasta.melds import Meld


class TestCardPoints:
    """Test card point value calculations."""

    def test_card_point_value_joker(self):
        """Joker is worth 50 points."""
        assert calculate_card_points([104]) == 50
        assert calculate_card_points([105, 106]) == 100

    def test_card_point_value_ace(self):
        """Ace is worth 20 points."""
        # Ace of clubs (first deck)
        assert calculate_card_points([0]) == 20
        # Ace of spades (second deck)
        assert calculate_card_points([52]) == 20

    def test_card_point_value_two(self):
        """2 is worth 20 points."""
        # 2 of clubs (first deck)
        assert calculate_card_points([1]) == 20
        # 2 of diamonds (second deck)
        assert calculate_card_points([53]) == 20

    def test_card_point_value_high_card(self):
        """8-K are worth 10 points."""
        # 8 of clubs
        assert calculate_card_points([7]) == 10
        # King of spades
        assert calculate_card_points([12]) == 10

    def test_card_point_value_low_card(self):
        """3-7 are worth 5 points."""
        # 3 of clubs
        assert calculate_card_points([2]) == 5
        # 7 of hearts
        assert calculate_card_points([6]) == 5

    def test_calculate_card_points_multiple_cards(self):
        """Sum multiple card point values."""
        # Joker (50) + Ace (20) + King (10) + 5 (5) = 85
        assert calculate_card_points([104, 0, 12, 4]) == 85


class TestMeldBonuses:
    """Test canasta bonus calculations."""

    def test_natural_canasta_bonus_500(self):
        """Natural canasta (7+ naturals) earns 500 bonus."""
        meld = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26, 78, 39], wild_cards=[])
        assert calculate_meld_bonuses([meld]) == 500

    def test_mixed_canasta_bonus_300(self):
        """Mixed canasta (7+ cards with wilds) earns 300 bonus."""
        meld = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26], wild_cards=[1, 104])
        assert calculate_meld_bonuses([meld]) == 300

    def test_non_canasta_bonus_zero(self):
        """Non-canasta melds earn no bonus."""
        meld = Meld(rank=0, natural_cards=[0, 52, 13], wild_cards=[])
        assert calculate_meld_bonuses([meld]) == 0

    def test_multiple_canastas(self):
        """Multiple canastas add bonuses together."""
        natural = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26, 78, 39], wild_cards=[])
        mixed = Meld(rank=3, natural_cards=[3, 55, 16, 68, 29], wild_cards=[1, 104])
        assert calculate_meld_bonuses([natural, mixed]) == 800


class TestRedThreeBonus:
    """Test red three bonus/penalty calculations."""

    def test_red_three_bonus_one_red_three(self):
        """One red three with melds earns 100 bonus."""
        assert calculate_red_three_bonus(1, has_melds=True) == 100

    def test_red_three_bonus_two_red_threes(self):
        """Two red threes with melds earn 200 bonus."""
        assert calculate_red_three_bonus(2, has_melds=True) == 200

    def test_red_three_bonus_three_red_threes(self):
        """Three red threes with melds earn 300 bonus."""
        assert calculate_red_three_bonus(3, has_melds=True) == 300

    def test_red_three_bonus_all_four(self):
        """All four red threes with melds earn 800 bonus."""
        assert calculate_red_three_bonus(4, has_melds=True) == 800

    def test_red_three_penalty_no_melds(self):
        """Red threes without melds are -100 each."""
        assert calculate_red_three_bonus(2, has_melds=False) == -200

    def test_red_three_penalty_all_four_no_melds(self):
        """All four red threes without melds are -400 (not -800)."""
        assert calculate_red_three_bonus(4, has_melds=False) == -400


class TestGoingOutBonus:
    """Test going out bonus calculations."""

    def test_going_out_bonus_regular(self):
        """Regular going out earns 100 bonus."""
        assert calculate_going_out_bonus(went_out=True, concealed=False) == 100

    def test_going_out_bonus_concealed(self):
        """Concealed going out earns 200 bonus."""
        assert calculate_going_out_bonus(went_out=True, concealed=True) == 200

    def test_no_going_out_bonus(self):
        """No bonus if didn't go out."""
        assert calculate_going_out_bonus(went_out=False, concealed=False) == 0
        assert calculate_going_out_bonus(went_out=False, concealed=True) == 0


class TestHandScore:
    """Test complete hand score calculation."""

    def test_calculate_hand_score_basic(self):
        """Calculate score with melds but no canastas."""
        # Meld: 3 Aces (20 each) = 60
        meld = Meld(rank=0, natural_cards=[0, 52, 13], wild_cards=[])
        score = calculate_hand_score(
            melded_cards=[0, 52, 13],
            melds=[meld],
            red_three_count=0,
            hand_cards=[],
            went_out=False,
            concealed=False,
        )
        assert score == 60

    def test_calculate_hand_score_with_canasta(self):
        """Calculate score with natural canasta."""
        # Natural canasta: 7 Aces = 140 + 500 bonus = 640
        meld = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26, 78, 39], wild_cards=[])
        score = calculate_hand_score(
            melded_cards=[0, 52, 13, 65, 26, 78, 39],
            melds=[meld],
            red_three_count=0,
            hand_cards=[],
            went_out=False,
            concealed=False,
        )
        assert score == 640

    def test_calculate_hand_score_complete_game(self):
        """Calculate score with all components."""
        # Natural canasta: 7 Aces = 140 + 500 = 640
        # Red threes: 2 × 100 = 200
        # Going out: 100
        # Total = 940
        meld = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26, 78, 39], wild_cards=[])
        score = calculate_hand_score(
            melded_cards=[0, 52, 13, 65, 26, 78, 39],
            melds=[meld],
            red_three_count=2,
            hand_cards=[],
            went_out=True,
            concealed=False,
        )
        assert score == 940

    def test_cards_in_hand_subtract_from_score(self):
        """Cards left in hand subtract from score."""
        # Meld: 3 Aces = 60
        # Hand: King (10) + 5 (5) = -15
        # Total = 45
        meld = Meld(rank=0, natural_cards=[0, 52, 13], wild_cards=[])
        score = calculate_hand_score(
            melded_cards=[0, 52, 13],
            melds=[meld],
            red_three_count=0,
            hand_cards=[12, 4],
            went_out=False,
            concealed=False,
        )
        assert score == 45

    def test_concealed_going_out_bonus(self):
        """Concealed going out earns 200 bonus."""
        # Natural canasta: 7 Aces = 140 + 500 = 640
        # Concealed going out: 200
        # Total = 840
        meld = Meld(rank=0, natural_cards=[0, 52, 13, 65, 26, 78, 39], wild_cards=[])
        score = calculate_hand_score(
            melded_cards=[0, 52, 13, 65, 26, 78, 39],
            melds=[meld],
            red_three_count=0,
            hand_cards=[],
            went_out=True,
            concealed=True,
        )
        assert score == 840

    def test_red_three_penalty_without_melds(self):
        """Red threes are penalized when team has no melds."""
        # No melds = 0
        # Red threes penalty: 2 × -100 = -200
        # Total = -200
        score = calculate_hand_score(
            melded_cards=[],
            melds=[],
            red_three_count=2,
            hand_cards=[12, 4],  # King + 5 in hand
            went_out=False,
            concealed=False,
        )
        # Hand cards also subtract: -10 -5 = -15
        # Total: -200 - 15 = -215
        assert score == -215

    def test_scoring_integration_in_game_state(self):
        """Test that scoring is integrated into game state."""
        import pyspiel

        # Create a game and verify scoring attributes exist
        game = pyspiel.load_game("python_canasta")
        state = game.new_initial_state()

        # Verify state has scoring attributes
        assert hasattr(state, '_team_scores')
        assert hasattr(state, '_hand_scores')
        assert state._team_scores == [0, 0]
        assert state._hand_scores == [0, 0]
