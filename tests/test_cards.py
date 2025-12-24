"""Tests for card representation and utilities."""

import pytest
from canasta.cards import (
    NUM_CARDS,
    RANKS,
    SUITS,
    card_id_to_rank_suit,
    card_point_value,
    is_wild,
    is_joker,
    is_red_three,
    is_black_three,
    is_natural,
    rank_of,
    cards_of_rank,
)


class TestCardEncoding:
    """Test card ID encoding and decoding."""

    def test_num_cards(self):
        """Verify total card count."""
        assert NUM_CARDS == 108

    def test_first_deck_encoding(self):
        """Test first deck (cards 0-51)."""
        # First card: Ace of Clubs
        assert card_id_to_rank_suit(0) == ("A", "clubs")
        # 13th card: King of Clubs
        assert card_id_to_rank_suit(12) == ("K", "clubs")
        # 14th card: Ace of Diamonds
        assert card_id_to_rank_suit(13) == ("A", "diamonds")
        # 27th card: Ace of Hearts
        assert card_id_to_rank_suit(26) == ("A", "hearts")
        # 40th card: Ace of Spades
        assert card_id_to_rank_suit(39) == ("A", "spades")
        # Last card of first deck: King of Spades
        assert card_id_to_rank_suit(51) == ("K", "spades")

    def test_second_deck_encoding(self):
        """Test second deck (cards 52-103)."""
        # First card of second deck: Ace of Clubs
        assert card_id_to_rank_suit(52) == ("A", "clubs")
        # Last card of second deck: King of Spades
        assert card_id_to_rank_suit(103) == ("K", "spades")

    def test_joker_encoding(self):
        """Test joker encoding (cards 104-107)."""
        for joker_id in range(104, 108):
            rank, suit = card_id_to_rank_suit(joker_id)
            assert rank == "JOKER"
            assert suit is None

    def test_all_ranks_present(self):
        """Verify all ranks are represented correctly."""
        for rank_idx, rank in enumerate(RANKS):
            # Check first occurrence in first deck (clubs)
            card_id = rank_idx
            assert card_id_to_rank_suit(card_id)[0] == rank

    def test_all_suits_present(self):
        """Verify all suits are represented correctly."""
        for suit_idx, suit in enumerate(SUITS):
            # Check Ace of each suit in first deck
            card_id = suit_idx * 13
            assert card_id_to_rank_suit(card_id)[1] == suit


class TestCardPointValues:
    """Test card point values per Pagat rules."""

    def test_joker_values(self):
        """Jokers are worth 50 points."""
        for joker_id in range(104, 108):
            assert card_point_value(joker_id) == 50

    def test_two_values(self):
        """2s are worth 20 points."""
        # 2 of clubs (first deck)
        assert card_point_value(1) == 20
        # 2 of diamonds (first deck)
        assert card_point_value(14) == 20
        # 2 of hearts (first deck)
        assert card_point_value(27) == 20
        # 2 of spades (first deck)
        assert card_point_value(40) == 20
        # 2 of clubs (second deck)
        assert card_point_value(53) == 20

    def test_ace_values(self):
        """Aces are worth 20 points."""
        # Ace of clubs (first deck)
        assert card_point_value(0) == 20
        # Ace of diamonds (first deck)
        assert card_point_value(13) == 20
        # Ace of hearts (first deck)
        assert card_point_value(26) == 20
        # Ace of spades (first deck)
        assert card_point_value(39) == 20
        # Ace of clubs (second deck)
        assert card_point_value(52) == 20

    def test_high_card_values(self):
        """8-K are worth 10 points."""
        high_ranks = ["8", "9", "10", "J", "Q", "K"]
        for rank in high_ranks:
            rank_idx = RANKS.index(rank)
            # First card of this rank (clubs, first deck)
            card_id = rank_idx
            assert card_point_value(card_id) == 10

    def test_low_card_values(self):
        """3-7 are worth 5 points."""
        low_ranks = ["3", "4", "5", "6", "7"]
        for rank in low_ranks:
            rank_idx = RANKS.index(rank)
            # First card of this rank (clubs, first deck)
            card_id = rank_idx
            assert card_point_value(card_id) == 5


class TestWildCards:
    """Test wild card detection."""

    def test_jokers_are_wild(self):
        """Jokers are wild cards."""
        for joker_id in range(104, 108):
            assert is_wild(joker_id)
            assert is_joker(joker_id)

    def test_twos_are_wild(self):
        """2s are wild cards."""
        # All 2s in both decks (8 total)
        two_ids = [1, 14, 27, 40, 53, 66, 79, 92]
        for card_id in two_ids:
            assert is_wild(card_id)
            assert not is_joker(card_id)

    def test_non_wild_cards(self):
        """Non-wild cards are correctly identified."""
        # Test various non-wild cards
        non_wild_ids = [0, 2, 3, 12, 13, 26, 39, 50, 52, 65]
        for card_id in non_wild_ids:
            assert not is_wild(card_id)


class TestThreeDetection:
    """Test red and black three detection."""

    def test_red_threes(self):
        """Red threes (diamonds and hearts) are correctly identified."""
        # 3 of diamonds (first deck)
        assert is_red_three(15)
        # 3 of hearts (first deck)
        assert is_red_three(28)
        # 3 of diamonds (second deck)
        assert is_red_three(67)
        # 3 of hearts (second deck)
        assert is_red_three(80)

        # Count all red threes
        red_three_count = sum(1 for i in range(NUM_CARDS) if is_red_three(i))
        assert red_three_count == 4

    def test_black_threes(self):
        """Black threes (clubs and spades) are correctly identified."""
        # 3 of clubs (first deck)
        assert is_black_three(2)
        # 3 of spades (first deck)
        assert is_black_three(41)
        # 3 of clubs (second deck)
        assert is_black_three(54)
        # 3 of spades (second deck)
        assert is_black_three(93)

        # Count all black threes
        black_three_count = sum(1 for i in range(NUM_CARDS) if is_black_three(i))
        assert black_three_count == 4

    def test_non_threes(self):
        """Non-three cards are not identified as threes."""
        non_three_ids = [0, 1, 3, 4, 12, 13, 104, 105]
        for card_id in non_three_ids:
            assert not is_red_three(card_id)
            assert not is_black_three(card_id)


class TestNaturalCards:
    """Test natural card detection."""

    def test_natural_cards(self):
        """Natural cards (non-wild) are correctly identified."""
        # Aces, 3s, and high cards are natural
        natural_ids = [0, 2, 3, 12, 13, 15, 26, 28, 39, 50]
        for card_id in natural_ids:
            assert is_natural(card_id)

    def test_wild_not_natural(self):
        """Wild cards are not natural."""
        # Jokers
        for joker_id in range(104, 108):
            assert not is_natural(joker_id)

        # 2s
        two_ids = [1, 14, 27, 40, 53, 66, 79, 92]
        for card_id in two_ids:
            assert not is_natural(card_id)


class TestRankQueries:
    """Test rank query functions."""

    def test_rank_of_normal_cards(self):
        """Test rank index for normal cards."""
        for rank_idx in range(len(RANKS)):
            # Check first card of each rank (clubs, first deck)
            card_id = rank_idx
            assert rank_of(card_id) == rank_idx

    def test_rank_of_jokers(self):
        """Jokers return -1 for rank."""
        for joker_id in range(104, 108):
            assert rank_of(joker_id) == -1

    def test_cards_of_rank(self):
        """Test getting all cards of a specific rank."""
        for rank_idx in range(len(RANKS)):
            cards = cards_of_rank(rank_idx)
            # Should be 8 cards (4 suits × 2 decks)
            assert len(cards) == 8
            # All should have the same rank
            for card_id in cards:
                assert rank_of(card_id) == rank_idx

    def test_cards_of_rank_ace(self):
        """Test all Aces."""
        aces = cards_of_rank(0)
        assert len(aces) == 8
        expected_aces = [0, 13, 26, 39, 52, 65, 78, 91]
        assert sorted(aces) == expected_aces

    def test_cards_of_rank_two(self):
        """Test all 2s."""
        twos = cards_of_rank(1)
        assert len(twos) == 8
        # All should be wild
        for card_id in twos:
            assert is_wild(card_id)
