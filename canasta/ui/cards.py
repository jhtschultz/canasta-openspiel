"""Card visual representation for Canasta UI.

Provides functions to convert card IDs to visual string representations
using Unicode suit symbols.
"""

from canasta.cards import card_id_to_rank_suit, NUM_CARDS

# Unicode suit symbols
SUIT_SYMBOLS = {
    "spades": "\u2660",    # Black spade
    "hearts": "\u2665",    # Black heart
    "diamonds": "\u2666",  # Black diamond
    "clubs": "\u2663",     # Black club
}


def card_to_str(card_id: int) -> str:
    """Convert card ID to visual string representation.

    Args:
        card_id: Card ID (0-107)

    Returns:
        Visual card string like "[A\u2660]", "[10\u2665]", "[JKR]"

    Raises:
        ValueError: If card_id is out of range
    """
    if card_id < 0 or card_id >= NUM_CARDS:
        raise ValueError(f"Invalid card_id: {card_id}")

    rank, suit = card_id_to_rank_suit(card_id)

    # Jokers
    if suit is None:
        return "[JKR]"

    # Regular cards with suit symbol
    suit_symbol = SUIT_SYMBOLS[suit]
    return f"[{rank}{suit_symbol}]"


def card_back() -> str:
    """Return visual representation of a card back (hidden card).

    Returns:
        String "[###]" representing a face-down card
    """
    return "[###]"


def rank_display_name(rank_idx: int) -> str:
    """Get display name for a rank index.

    Args:
        rank_idx: Rank index (0-12)

    Returns:
        Display name like "Aces", "Twos", "Kings", etc.
    """
    rank_names = [
        "Aces", "Twos", "Threes", "Fours", "Fives", "Sixes",
        "Sevens", "Eights", "Nines", "Tens", "Jacks", "Queens", "Kings"
    ]
    if 0 <= rank_idx < len(rank_names):
        return rank_names[rank_idx]
    return f"Rank{rank_idx}"


def format_card_list(card_ids: list[int], hidden: bool = False) -> str:
    """Format a list of cards as a string.

    Args:
        card_ids: List of card IDs
        hidden: If True, show all as card backs

    Returns:
        String of cards like "[A\u2660][K\u2665][10\u2666]"
    """
    if hidden:
        return "".join(card_back() for _ in card_ids)
    return "".join(card_to_str(c) for c in card_ids)


def format_hand_summary(card_count: int) -> str:
    """Format a summary for a hidden hand.

    Args:
        card_count: Number of cards in hand

    Returns:
        String like "[11 cards]"
    """
    if card_count == 1:
        return "[1 card]"
    return f"[{card_count} cards]"
