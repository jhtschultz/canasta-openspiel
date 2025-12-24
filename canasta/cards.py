"""Card representation and utilities for Canasta.

Encoding:
- 108 cards total: 2 standard decks (52×2=104) + 4 jokers
- Card IDs 0-51: First deck (A-K of clubs, diamonds, hearts, spades)
- Card IDs 52-103: Second deck (same)
- Card IDs 104-107: Jokers
"""

NUM_CARDS = 108
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["clubs", "diamonds", "hearts", "spades"]


def card_id_to_rank_suit(card_id: int) -> tuple[str, str | None]:
    """Decode card ID to (rank, suit).

    Args:
        card_id: Card ID (0-107)

    Returns:
        Tuple of (rank, suit). Jokers return ("JOKER", None).
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers (104-107)
    if card_id >= 104:
        return ("JOKER", None)

    # Standard cards (0-103)
    # Each deck has 52 cards, organized as 4 suits of 13 ranks
    deck_offset = card_id % 52
    suit_idx = deck_offset // 13
    rank_idx = deck_offset % 13

    return (RANKS[rank_idx], SUITS[suit_idx])


def card_point_value(card_id: int) -> int:
    """Get point value for a card per Pagat rules.

    Point values:
    - Jokers: 50
    - 2s: 20
    - Aces: 20
    - 8-K: 10
    - 3-7: 5

    Args:
        card_id: Card ID (0-107)

    Returns:
        Point value of the card.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers
    if card_id >= 104:
        return 50

    rank_idx = rank_of(card_id)

    # 2s (rank index 1)
    if rank_idx == 1:
        return 20

    # Aces (rank index 0)
    if rank_idx == 0:
        return 20

    # 8-K (rank indices 7-12)
    if rank_idx >= 7:
        return 10

    # 3-7 (rank indices 2-6)
    return 5


def is_wild(card_id: int) -> bool:
    """Check if card is wild.

    Wild cards are jokers and 2s.

    Args:
        card_id: Card ID (0-107)

    Returns:
        True if card is wild.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers
    if card_id >= 104:
        return True

    # 2s (rank index 1)
    return rank_of(card_id) == 1


def is_joker(card_id: int) -> bool:
    """Check if card is a joker.

    Args:
        card_id: Card ID (0-107)

    Returns:
        True if card is a joker.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    return card_id >= 104


def is_red_three(card_id: int) -> bool:
    """Check if card is a red three (diamonds or hearts).

    Args:
        card_id: Card ID (0-107)

    Returns:
        True if card is a red three.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers are not red threes
    if card_id >= 104:
        return False

    rank, suit = card_id_to_rank_suit(card_id)
    return rank == "3" and suit in ["diamonds", "hearts"]


def is_black_three(card_id: int) -> bool:
    """Check if card is a black three (clubs or spades).

    Args:
        card_id: Card ID (0-107)

    Returns:
        True if card is a black three.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers are not black threes
    if card_id >= 104:
        return False

    rank, suit = card_id_to_rank_suit(card_id)
    return rank == "3" and suit in ["clubs", "spades"]


def is_natural(card_id: int) -> bool:
    """Check if card is natural (not wild).

    Args:
        card_id: Card ID (0-107)

    Returns:
        True if card is natural.
    """
    return not is_wild(card_id)


def rank_of(card_id: int) -> int:
    """Get rank index of a card.

    Args:
        card_id: Card ID (0-107)

    Returns:
        Rank index (0-12), or -1 for jokers.
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    # Jokers
    if card_id >= 104:
        return -1

    # Standard cards
    deck_offset = card_id % 52
    return deck_offset % 13


def cards_of_rank(rank_idx: int) -> list[int]:
    """Get all card IDs of a given rank.

    Args:
        rank_idx: Rank index (0-12)

    Returns:
        List of 8 card IDs (4 suits × 2 decks) with the given rank.
    """
    if rank_idx < 0 or rank_idx >= len(RANKS):
        raise ValueError(f"Invalid rank_idx: {rank_idx}")

    cards = []

    # First deck
    for suit_idx in range(len(SUITS)):
        card_id = suit_idx * 13 + rank_idx
        cards.append(card_id)

    # Second deck
    for suit_idx in range(len(SUITS)):
        card_id = 52 + suit_idx * 13 + rank_idx
        cards.append(card_id)

    return cards
