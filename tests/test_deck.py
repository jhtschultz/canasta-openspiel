"""Tests for deck.py."""

import pytest
from canasta.cards import NUM_CARDS, is_red_three
from canasta.deck import create_deck, shuffle_deck, deal_hands


class TestCreateDeck:
    """Tests for create_deck()."""

    def test_returns_108_cards(self):
        """Deck should have exactly 108 cards."""
        deck = create_deck()
        assert len(deck) == NUM_CARDS

    def test_all_cards_unique(self):
        """All card IDs should be unique."""
        deck = create_deck()
        assert len(set(deck)) == NUM_CARDS

    def test_cards_in_valid_range(self):
        """All card IDs should be in range [0, 107]."""
        deck = create_deck()
        for card_id in deck:
            assert 0 <= card_id < NUM_CARDS


class TestShuffleDeck:
    """Tests for shuffle_deck()."""

    def test_preserves_all_cards(self):
        """Shuffling should not add or remove cards."""
        deck = create_deck()
        original_set = set(deck)
        shuffled = shuffle_deck(deck.copy())
        assert set(shuffled) == original_set

    def test_seed_produces_reproducible_shuffle(self):
        """Same seed should produce same shuffle."""
        deck1 = create_deck()
        deck2 = create_deck()

        shuffled1 = shuffle_deck(deck1.copy(), seed=42)
        shuffled2 = shuffle_deck(deck2.copy(), seed=42)

        assert shuffled1 == shuffled2

    def test_different_seeds_produce_different_shuffles(self):
        """Different seeds should (very likely) produce different shuffles."""
        deck1 = create_deck()
        deck2 = create_deck()

        shuffled1 = shuffle_deck(deck1.copy(), seed=42)
        shuffled2 = shuffle_deck(deck2.copy(), seed=123)

        assert shuffled1 != shuffled2

    def test_shuffle_modifies_in_place(self):
        """shuffle_deck should modify the deck in place."""
        deck = create_deck()
        deck_id = id(deck)
        result = shuffle_deck(deck)
        assert id(result) == deck_id


class TestDealHands:
    """Tests for deal_hands()."""

    def test_deals_11_cards_per_player(self):
        """Each of 4 players should get 11 cards."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top = deal_hands(deck)

        assert len(hands) == 4
        for hand in hands:
            assert len(hand) == 11

    def test_no_red_threes_in_hands(self):
        """Red threes should be removed from hands."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top = deal_hands(deck)

        for hand in hands:
            for card in hand:
                assert not is_red_three(card)

    def test_all_cards_accounted_for(self):
        """All 108 cards should be in hands + stock + discard + red_threes."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top, red_threes = deal_hands(deck, return_red_threes=True)

        all_cards = []
        for hand in hands:
            all_cards.extend(hand)
        all_cards.extend(stock)
        all_cards.append(discard_top)
        all_cards.extend(red_threes)

        assert len(all_cards) == NUM_CARDS
        assert set(all_cards) == set(range(NUM_CARDS))

    def test_discard_pile_has_one_card(self):
        """Discard pile should start with exactly one card."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top = deal_hands(deck)

        assert isinstance(discard_top, int)
        assert 0 <= discard_top < NUM_CARDS

    def test_red_threes_tracked_separately(self):
        """Red threes should be tracked when return_red_threes=True."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top, red_threes = deal_hands(deck, return_red_threes=True)

        # All returned red threes should actually be red threes
        for card in red_threes:
            assert is_red_three(card)

    def test_red_threes_not_returned_by_default(self):
        """By default, deal_hands should return 3-tuple without red_threes."""
        deck = shuffle_deck(create_deck(), seed=42)
        result = deal_hands(deck)

        assert len(result) == 3
        hands, stock, discard_top = result

    def test_players_get_replacement_cards_for_red_threes(self):
        """Players should get replacement cards when they draw red threes."""
        # Use a specific seed known to produce red threes in initial deal
        deck = shuffle_deck(create_deck(), seed=1)
        hands, stock, discard_top, red_threes = deal_hands(deck, return_red_threes=True)

        # If red threes were dealt, verify players still have 11 cards each
        if red_threes:
            for hand in hands:
                assert len(hand) == 11

    def test_stock_size_correct(self):
        """Stock should have correct number of cards after dealing."""
        deck = shuffle_deck(create_deck(), seed=42)
        hands, stock, discard_top, red_threes = deal_hands(deck, return_red_threes=True)

        # 108 cards - (4 hands × 11 cards) - 1 discard - red_threes
        expected_stock_size = NUM_CARDS - (4 * 11) - 1 - len(red_threes)
        assert len(stock) == expected_stock_size


class TestDealHandsEdgeCases:
    """Edge case tests for deal_hands()."""

    def test_handle_deck_with_all_red_threes_in_initial_deal(self):
        """Should handle case where many red threes are in initial hands."""
        # Create a deck with red threes at the top
        deck = create_deck()
        # Move all red threes to the top
        red_three_cards = [c for c in deck if is_red_three(c)]
        non_red_three_cards = [c for c in deck if not is_red_three(c)]

        # Put enough red threes at top to hit initial hands
        stacked_deck = red_three_cards[:20] + non_red_three_cards

        hands, stock, discard_top, red_threes = deal_hands(stacked_deck, return_red_threes=True)

        # Should still deal 11 cards to each player
        for hand in hands:
            assert len(hand) == 11
            # No red threes in hands
            for card in hand:
                assert not is_red_three(card)

    def test_consistent_dealing_with_same_seed(self):
        """Same shuffled deck should produce same deal."""
        deck1 = shuffle_deck(create_deck(), seed=999)
        deck2 = shuffle_deck(create_deck(), seed=999)

        result1 = deal_hands(deck1, return_red_threes=True)
        result2 = deal_hands(deck2, return_red_threes=True)

        hands1, stock1, discard1, red_threes1 = result1
        hands2, stock2, discard2, red_threes2 = result2

        assert hands1 == hands2
        assert stock1 == stock2
        assert discard1 == discard2
        assert red_threes1 == red_threes2
