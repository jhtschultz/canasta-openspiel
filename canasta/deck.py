"""Deck creation, shuffling, and dealing for Canasta.

Implements the Pagat Classic 4-player rules:
- Deal 11 cards to each of 4 players
- Red 3s are automatically replaced with new cards from the deck
- One card is placed face-up to start the discard pile
"""

import random
from canasta.cards import NUM_CARDS, is_red_three

# Game constants
NUM_PLAYERS = 4
HAND_SIZE = 11  # Pagat Classic


def create_deck() -> list[int]:
    """Create a standard Canasta deck of 108 cards.

    Returns:
        List of 108 card IDs [0..107] in order.
    """
    return list(range(NUM_CARDS))


def shuffle_deck(deck: list[int], seed: int | None = None) -> list[int]:
    """Shuffle a deck in place.

    Args:
        deck: List of card IDs to shuffle
        seed: Optional random seed for reproducibility

    Returns:
        The shuffled deck (same object, modified in place)
    """
    if seed is not None:
        random.seed(seed)
    random.shuffle(deck)
    return deck


def deal_hands(deck: list[int], return_red_threes: bool = False):
    """Deal 11 cards to each of 4 players with red 3 replacement.

    Algorithm:
    1. Deal 11 cards to each player in turn
    2. For any red 3s dealt, replace them with new cards from deck
    3. Place one card face-up to start discard pile
    4. Remaining cards form the stock

    Args:
        deck: Shuffled deck of 108 cards
        return_red_threes: If True, return red_threes as 4th element

    Returns:
        If return_red_threes=False (default):
            (hands, stock, discard_top)
        If return_red_threes=True:
            (hands, stock, discard_top, red_threes)

        Where:
        - hands: List of 4 hands, each with 11 cards
        - stock: Remaining cards in deck (list)
        - discard_top: Single card at top of discard pile (int)
        - red_threes: List of red 3s removed from hands (only if return_red_threes=True)
    """
    # Make a working copy of the deck
    remaining = deck.copy()
    hands = [[] for _ in range(NUM_PLAYERS)]
    red_threes = []

    # Deal initial hands
    for _ in range(HAND_SIZE):
        for player in range(NUM_PLAYERS):
            card = remaining.pop(0)
            hands[player].append(card)

    # Replace red 3s in hands
    for player in range(NUM_PLAYERS):
        hand = hands[player]
        i = 0
        while i < len(hand):
            card = hand[i]
            if is_red_three(card):
                # Remove red 3 from hand
                hand.pop(i)
                red_threes.append(card)

                # Draw replacement card
                if remaining:
                    replacement = remaining.pop(0)
                    hand.append(replacement)
                    # Don't increment i - check the replacement card
                else:
                    # No cards left in deck
                    break
            else:
                i += 1

    # Deal one card to discard pile
    discard_top = remaining.pop(0)

    # Rest of the deck is the stock
    stock = remaining

    if return_red_threes:
        return hands, stock, discard_top, red_threes
    else:
        return hands, stock, discard_top
