"""Meld validation and scoring for Canasta.

A meld is a set of 3 or more cards of the same rank (with possible wild cards).
"""
from dataclasses import dataclass
from typing import List
from canasta.cards import card_point_value, rank_of


@dataclass
class Meld:
    """Represents a meld of cards.

    Attributes:
        rank: Rank index (0-12) of the natural cards in the meld
        natural_cards: List of card IDs for natural cards
        wild_cards: List of card IDs for wild cards (2s and jokers)
    """

    rank: int
    natural_cards: List[int]
    wild_cards: List[int]


def is_valid_meld(meld: Meld, allow_black_threes: bool = False) -> bool:
    """Validate meld per Pagat rules.

    Rules:
    - At least 3 cards total
    - At least 2 natural cards
    - At most 3 wild cards
    - Cannot meld 2s (rank 1) or 3s (rank 2) except black 3s when going out

    Args:
        meld: The meld to validate
        allow_black_threes: If True, allows melding black 3s (rank 2)

    Returns:
        True if meld is valid
    """
    total_cards = len(meld.natural_cards) + len(meld.wild_cards)

    # Rule 1: At least 3 cards
    if total_cards < 3:
        return False

    # Rule 2: At least 2 natural cards
    if len(meld.natural_cards) < 2:
        return False

    # Rule 3: At most 3 wild cards
    if len(meld.wild_cards) > 3:
        return False

    # Rule 4: Cannot meld 2s (rank 1)
    if meld.rank == 1:
        return False

    # Rule 5: Cannot meld 3s (rank 2) unless black 3s when going out
    if meld.rank == 2 and not allow_black_threes:
        return False

    return True


def meld_point_value(meld: Meld) -> int:
    """Calculate total point value of cards in meld.

    Sums the point values of all natural and wild cards.

    Args:
        meld: The meld to score

    Returns:
        Total point value
    """
    total = 0

    # Add natural card values
    for card_id in meld.natural_cards:
        total += card_point_value(card_id)

    # Add wild card values
    for card_id in meld.wild_cards:
        total += card_point_value(card_id)

    return total


def is_canasta(meld: Meld) -> bool:
    """Check if meld is a canasta (7+ cards).

    Args:
        meld: The meld to check

    Returns:
        True if meld has 7 or more cards
    """
    total_cards = len(meld.natural_cards) + len(meld.wild_cards)
    return total_cards >= 7


def is_natural_canasta(meld: Meld) -> bool:
    """Check if meld is a natural canasta (7+ cards, no wilds).

    Args:
        meld: The meld to check

    Returns:
        True if meld has 7+ cards and no wild cards
    """
    return is_canasta(meld) and len(meld.wild_cards) == 0


def is_mixed_canasta(meld: Meld) -> bool:
    """Check if meld is a mixed canasta (7+ cards with wilds).

    Args:
        meld: The meld to check

    Returns:
        True if meld has 7+ cards and at least one wild card
    """
    return is_canasta(meld) and len(meld.wild_cards) > 0


def canasta_bonus(meld: Meld) -> int:
    """Calculate canasta bonus for a meld.

    Bonuses:
    - Natural canasta: 500 points
    - Mixed canasta: 300 points
    - Not a canasta: 0 points

    Args:
        meld: The meld to score

    Returns:
        Bonus points (500, 300, or 0)
    """
    if is_natural_canasta(meld):
        return 500
    elif is_mixed_canasta(meld):
        return 300
    else:
        return 0


def initial_meld_minimum(team_score: int) -> int:
    """Get initial meld minimum based on team score.

    Per Pagat rules:
    - Negative score: 15 points
    - 0-1495: 50 points
    - 1500-2995: 90 points
    - 3000+: 120 points

    Args:
        team_score: Current team score

    Returns:
        Minimum points required for initial meld
    """
    if team_score < 0:
        return 15
    elif team_score < 1500:
        return 50
    elif team_score < 3000:
        return 90
    else:
        return 120


def can_form_initial_meld(melds: list[Meld], team_score: int) -> bool:
    """Check if melds meet initial meld requirement.

    Sums the point values of all melds and checks if they meet
    the minimum required for the team's current score.

    Args:
        melds: List of melds being played
        team_score: Current team score

    Returns:
        True if total meld points meet or exceed minimum
    """
    if not melds:
        return False

    total_points = sum(meld_point_value(meld) for meld in melds)
    minimum = initial_meld_minimum(team_score)

    return total_points >= minimum
