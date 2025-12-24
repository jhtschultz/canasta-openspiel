"""Tests for meld validation logic."""
import pytest
from canasta.melds import (
    Meld,
    is_valid_meld,
    meld_point_value,
    is_canasta,
    is_natural_canasta,
    is_mixed_canasta,
    initial_meld_minimum,
    can_form_initial_meld,
    canasta_bonus,
)


class TestMeldValidation:
    """Test basic meld validation rules."""

    def test_valid_meld_three_natural_cards(self):
        """Valid meld: 3 natural cards, no wilds."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2], wild_cards=[])
        assert is_valid_meld(meld) is True

    def test_valid_meld_with_one_wild(self):
        """Valid meld: 2 natural + 1 wild."""
        meld = Meld(rank=7, natural_cards=[0, 1], wild_cards=[2])
        assert is_valid_meld(meld) is True

    def test_valid_meld_with_three_wilds(self):
        """Valid meld: 3 natural + 3 wild (max wilds)."""
        meld = Meld(rank=8, natural_cards=[0, 1, 2], wild_cards=[3, 4, 5])
        assert is_valid_meld(meld) is True

    def test_invalid_meld_too_few_cards(self):
        """Invalid: Only 2 cards total."""
        meld = Meld(rank=4, natural_cards=[0, 1], wild_cards=[])
        assert is_valid_meld(meld) is False

    def test_invalid_meld_only_one_natural(self):
        """Invalid: Only 1 natural card."""
        meld = Meld(rank=6, natural_cards=[0], wild_cards=[1, 2])
        assert is_valid_meld(meld) is False

    def test_invalid_meld_too_many_wilds(self):
        """Invalid: 4 wild cards exceeds limit of 3."""
        meld = Meld(rank=9, natural_cards=[0, 1, 2], wild_cards=[3, 4, 5, 6])
        assert is_valid_meld(meld) is False

    def test_invalid_meld_twos(self):
        """Invalid: Cannot meld 2s (rank 1)."""
        meld = Meld(rank=1, natural_cards=[1, 14, 27], wild_cards=[])
        assert is_valid_meld(meld) is False

    def test_invalid_meld_threes(self):
        """Invalid: Cannot meld 3s (rank 2) normally."""
        meld = Meld(rank=2, natural_cards=[2, 15, 28], wild_cards=[])
        assert is_valid_meld(meld) is False

    def test_valid_black_threes_when_going_out(self):
        """Valid: Black 3s allowed when going out."""
        meld = Meld(rank=2, natural_cards=[2, 15, 28], wild_cards=[])
        assert is_valid_meld(meld, allow_black_threes=True) is True


class TestCanastasValidation:
    """Test canasta detection (7+ cards)."""

    def test_not_canasta_six_cards(self):
        """6 cards is not a canasta."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4], wild_cards=[5])
        assert is_canasta(meld) is False

    def test_canasta_seven_cards(self):
        """7 cards is a canasta."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4, 5, 6], wild_cards=[])
        assert is_canasta(meld) is True

    def test_natural_canasta_seven_natural(self):
        """7 natural cards is a natural canasta."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4, 5, 6], wild_cards=[])
        assert is_natural_canasta(meld) is True
        assert is_mixed_canasta(meld) is False

    def test_mixed_canasta_seven_with_wilds(self):
        """7 cards with wilds is a mixed canasta."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4], wild_cards=[5, 6])
        assert is_mixed_canasta(meld) is True
        assert is_natural_canasta(meld) is False

    def test_not_canasta_types_if_less_than_seven(self):
        """Less than 7 cards is neither natural nor mixed canasta."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2], wild_cards=[])
        assert is_natural_canasta(meld) is False
        assert is_mixed_canasta(meld) is False


class TestCanastaBonus:
    """Test canasta bonus calculation."""

    def test_natural_canasta_bonus(self):
        """Natural canasta = 500 points."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4, 5, 6], wild_cards=[])
        assert canasta_bonus(meld) == 500

    def test_mixed_canasta_bonus(self):
        """Mixed canasta = 300 points."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2, 3, 4], wild_cards=[5, 6])
        assert canasta_bonus(meld) == 300

    def test_non_canasta_no_bonus(self):
        """Non-canasta = 0 bonus."""
        meld = Meld(rank=5, natural_cards=[0, 1, 2], wild_cards=[])
        assert canasta_bonus(meld) == 0


class TestInitialMeldMinimum:
    """Test initial meld minimum thresholds."""

    def test_negative_score_minimum(self):
        """Negative score = 15 points minimum."""
        assert initial_meld_minimum(-100) == 15
        assert initial_meld_minimum(-1) == 15

    def test_zero_to_1495_minimum(self):
        """0-1495 = 50 points minimum."""
        assert initial_meld_minimum(0) == 50
        assert initial_meld_minimum(1000) == 50
        assert initial_meld_minimum(1495) == 50

    def test_1500_to_2995_minimum(self):
        """1500-2995 = 90 points minimum."""
        assert initial_meld_minimum(1500) == 90
        assert initial_meld_minimum(2000) == 90
        assert initial_meld_minimum(2995) == 90

    def test_3000_plus_minimum(self):
        """3000+ = 120 points minimum."""
        assert initial_meld_minimum(3000) == 120
        assert initial_meld_minimum(5000) == 120


class TestMeldPointValue:
    """Test meld point value calculation."""

    def test_point_value_aces(self):
        """Aces = 20 points each."""
        # Rank 0 = Aces, 3 aces = 60 points
        meld = Meld(rank=0, natural_cards=[0, 13, 26], wild_cards=[])
        assert meld_point_value(meld) == 60

    def test_point_value_eights_to_kings(self):
        """8-K = 10 points each."""
        # Rank 7 = 8s, 3 eights = 30 points
        meld = Meld(rank=7, natural_cards=[7, 20, 33], wild_cards=[])
        assert meld_point_value(meld) == 30

    def test_point_value_fours_to_sevens(self):
        """4-7 = 5 points each."""
        # Rank 3 = 4s, 3 fours = 15 points
        meld = Meld(rank=3, natural_cards=[3, 16, 29], wild_cards=[])
        assert meld_point_value(meld) == 15

    def test_point_value_with_wilds(self):
        """Wilds (2s and jokers) = 20 and 50 points."""
        # 3 natural 10s (10 pts each) + 1 two (20 pts) + 1 joker (50 pts) = 100 points
        meld = Meld(rank=8, natural_cards=[8, 21, 34], wild_cards=[1, 104])
        assert meld_point_value(meld) == 100


class TestInitialMeldValidation:
    """Test can_form_initial_meld function."""

    def test_meets_minimum_exact(self):
        """Melds exactly meet minimum."""
        # Team score 0 = 50 point minimum
        # One meld of 10s: 5 cards @ 10 pts = 50 points
        melds = [Meld(rank=8, natural_cards=[0, 1, 2, 3, 4], wild_cards=[])]
        assert can_form_initial_meld(melds, team_score=0) is True

    def test_meets_minimum_exceeds(self):
        """Melds exceed minimum."""
        # Team score 0 = 50 point minimum
        # Two melds totaling 80 points
        melds = [
            Meld(rank=8, natural_cards=[0, 1, 2, 3], wild_cards=[]),  # 40 pts
            Meld(rank=6, natural_cards=[5, 6, 7, 8], wild_cards=[]),  # 40 pts
        ]
        assert can_form_initial_meld(melds, team_score=0) is True

    def test_fails_minimum(self):
        """Melds don't meet minimum."""
        # Team score 0 = 50 point minimum
        # One meld: 3 fours @ 5 pts = 15 points
        melds = [Meld(rank=2, natural_cards=[0, 1, 2], wild_cards=[])]
        assert can_form_initial_meld(melds, team_score=0) is False

    def test_high_score_threshold(self):
        """High team score requires 120 points."""
        # Team score 3000 = 120 point minimum
        # Meld of aces: 6 aces @ 20 pts = 120 points
        melds = [Meld(rank=0, natural_cards=[0, 13, 26, 39, 52, 65], wild_cards=[])]
        assert can_form_initial_meld(melds, team_score=3000) is True

    def test_empty_melds(self):
        """No melds cannot meet any minimum."""
        assert can_form_initial_meld([], team_score=0) is False
