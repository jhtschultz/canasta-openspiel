"""Tests for canasta/ui/cards.py - Card visual representation."""

import pytest

from canasta.ui.cards import (
    card_to_str,
    card_back,
    rank_display_name,
    format_card_list,
    format_hand_summary,
    SUIT_SYMBOLS,
)


class TestCardToStr:
    """Tests for card_to_str function."""

    def test_ace_of_spades(self):
        """AC-1.1: Ace of spades renders correctly."""
        # Ace (rank 0) of spades (suit 3) in deck 1
        # card_id = suit * 13 + rank = 3 * 13 + 0 = 39
        result = card_to_str(39)
        assert result == "[A\u2660]"
        assert "\u2660" in result  # spades symbol

    def test_ten_of_hearts(self):
        """AC-1.2: 10 of hearts renders correctly."""
        # 10 (rank 9) of hearts (suit 2) in deck 1
        # card_id = suit * 13 + rank = 2 * 13 + 9 = 35
        result = card_to_str(35)
        assert result == "[10\u2665]"
        assert "\u2665" in result  # hearts symbol

    def test_king_of_diamonds(self):
        """AC-1.3: King of diamonds renders correctly."""
        # King (rank 12) of diamonds (suit 1) in deck 1
        # card_id = suit * 13 + rank = 1 * 13 + 12 = 25
        result = card_to_str(25)
        assert result == "[K\u2666]"
        assert "\u2666" in result  # diamonds symbol

    def test_queen_of_clubs(self):
        """Test Queen of clubs renders correctly."""
        # Queen (rank 11) of clubs (suit 0) in deck 1
        # card_id = suit * 13 + rank = 0 * 13 + 11 = 11
        result = card_to_str(11)
        assert result == "[Q\u2663]"
        assert "\u2663" in result  # clubs symbol

    def test_joker(self):
        """AC-1.4: Joker renders correctly."""
        # Jokers are card IDs 104-107
        result = card_to_str(104)
        assert result == "[JKR]"

        result = card_to_str(107)
        assert result == "[JKR]"

    def test_second_deck_card(self):
        """Test second deck cards render the same as first deck."""
        # Ace of spades in deck 2: 52 + 39 = 91
        result = card_to_str(91)
        assert result == "[A\u2660]"

    def test_invalid_card_id_negative(self):
        """Test invalid negative card ID raises error."""
        with pytest.raises(ValueError):
            card_to_str(-1)

    def test_invalid_card_id_too_high(self):
        """Test invalid high card ID raises error."""
        with pytest.raises(ValueError):
            card_to_str(108)


class TestCardBack:
    """Tests for card_back function."""

    def test_card_back_format(self):
        """AC-1.5: Card back renders correctly."""
        result = card_back()
        assert result == "[###]"

    def test_card_back_length(self):
        """Card back has consistent length."""
        result = card_back()
        assert len(result) == 5


class TestRankDisplayName:
    """Tests for rank_display_name function."""

    def test_aces(self):
        """Aces display name is correct."""
        assert rank_display_name(0) == "Aces"

    def test_twos(self):
        """Twos display name is correct."""
        assert rank_display_name(1) == "Twos"

    def test_kings(self):
        """Kings display name is correct."""
        assert rank_display_name(12) == "Kings"

    def test_all_ranks(self):
        """All ranks have display names."""
        expected = [
            "Aces", "Twos", "Threes", "Fours", "Fives", "Sixes",
            "Sevens", "Eights", "Nines", "Tens", "Jacks", "Queens", "Kings"
        ]
        for i, name in enumerate(expected):
            assert rank_display_name(i) == name


class TestFormatCardList:
    """Tests for format_card_list function."""

    def test_empty_list(self):
        """Empty list returns empty string."""
        assert format_card_list([]) == ""

    def test_single_card(self):
        """Single card formats correctly."""
        result = format_card_list([39])  # Ace of spades
        assert result == "[A\u2660]"

    def test_multiple_cards(self):
        """Multiple cards concatenate correctly."""
        result = format_card_list([39, 35, 25])  # A spades, 10 hearts, K diamonds
        assert "[A\u2660]" in result
        assert "[10\u2665]" in result
        assert "[K\u2666]" in result

    def test_hidden_cards(self):
        """Hidden cards show as backs."""
        result = format_card_list([39, 35, 25], hidden=True)
        assert result == "[###][###][###]"
        assert "[A" not in result


class TestFormatHandSummary:
    """Tests for format_hand_summary function."""

    def test_zero_cards(self):
        """Zero cards formats correctly."""
        assert format_hand_summary(0) == "[0 cards]"

    def test_one_card(self):
        """One card uses singular form."""
        assert format_hand_summary(1) == "[1 card]"

    def test_multiple_cards(self):
        """Multiple cards uses plural form."""
        assert format_hand_summary(11) == "[11 cards]"
        assert format_hand_summary(5) == "[5 cards]"


class TestSuitSymbols:
    """Tests for suit symbols."""

    def test_spades_symbol(self):
        """Spades uses correct Unicode symbol."""
        assert SUIT_SYMBOLS["spades"] == "\u2660"

    def test_hearts_symbol(self):
        """Hearts uses correct Unicode symbol."""
        assert SUIT_SYMBOLS["hearts"] == "\u2665"

    def test_diamonds_symbol(self):
        """Diamonds uses correct Unicode symbol."""
        assert SUIT_SYMBOLS["diamonds"] == "\u2666"

    def test_clubs_symbol(self):
        """Clubs uses correct Unicode symbol."""
        assert SUIT_SYMBOLS["clubs"] == "\u2663"
