"""Scoring calculations for Canasta.

Implements Pagat Classic Canasta scoring rules including:
- Card point values
- Canasta bonuses (natural/mixed)
- Red three bonuses/penalties
- Going out bonuses (regular/concealed)
- Complete hand score calculation
"""
from typing import List
from canasta.cards import card_point_value
from canasta.melds import Meld, canasta_bonus


def calculate_card_points(card_ids: List[int]) -> int:
    """Calculate total point value of cards.

    Uses card_point_value() from cards module:
    - Jokers: 50 points
    - 2s: 20 points
    - Aces: 20 points
    - 8-K: 10 points
    - 3-7: 5 points

    Args:
        card_ids: List of card IDs to score

    Returns:
        Total point value of all cards
    """
    return sum(card_point_value(card_id) for card_id in card_ids)


def calculate_meld_bonuses(melds: List[Meld]) -> int:
    """Calculate total canasta bonuses from melds.

    Uses canasta_bonus() from melds module:
    - Natural canasta (7+ cards, no wilds): 500 points
    - Mixed canasta (7+ cards with wilds): 300 points
    - Non-canasta melds: 0 points

    Args:
        melds: List of melds to score

    Returns:
        Total bonus points from all canastas
    """
    return sum(canasta_bonus(meld) for meld in melds)


def calculate_red_three_bonus(red_three_count: int, has_melds: bool) -> int:
    """Calculate red three bonus or penalty.

    Pagat Classic rules:
    - With melds: 100 points each (800 for all 4)
    - Without melds: -100 points each (no special -800 for all 4)

    Args:
        red_three_count: Number of red threes (0-4)
        has_melds: Whether team has any melds

    Returns:
        Bonus (positive) or penalty (negative) from red threes
    """
    if red_three_count == 0:
        return 0

    if has_melds:
        # Bonus with melds: 100 each, 800 for all 4
        if red_three_count == 4:
            return 800
        else:
            return red_three_count * 100
    else:
        # Penalty without melds: -100 each (no special case for all 4)
        return red_three_count * -100


def calculate_going_out_bonus(went_out: bool, concealed: bool) -> int:
    """Calculate going out bonus.

    Bonuses:
    - Regular going out: 100 points
    - Concealed going out: 200 points
    - Did not go out: 0 points

    Args:
        went_out: Whether this team went out
        concealed: Whether going out was concealed (no prior melds)

    Returns:
        Going out bonus (0, 100, or 200)
    """
    if not went_out:
        return 0

    if concealed:
        return 200
    else:
        return 100


def calculate_hand_score(
    melded_cards: List[int],
    melds: List[Meld],
    red_three_count: int,
    hand_cards: List[int],
    went_out: bool,
    concealed: bool,
) -> int:
    """Calculate complete hand score for a team.

    Score components:
    1. Add points for melded cards
    2. Add canasta bonuses
    3. Add red three bonus/penalty
    4. Add going out bonus
    5. Subtract points for cards left in hand

    Args:
        melded_cards: All cards in this team's melds
        melds: All melds for this team
        red_three_count: Number of red threes for this team
        hand_cards: Cards remaining in hand (if didn't go out)
        went_out: Whether this team went out
        concealed: Whether going out was concealed

    Returns:
        Total hand score (can be negative)
    """
    score = 0

    # 1. Add points for melded cards
    score += calculate_card_points(melded_cards)

    # 2. Add canasta bonuses
    score += calculate_meld_bonuses(melds)

    # 3. Add red three bonus/penalty
    has_melds = len(melds) > 0
    score += calculate_red_three_bonus(red_three_count, has_melds)

    # 4. Add going out bonus
    score += calculate_going_out_bonus(went_out, concealed)

    # 5. Subtract points for cards left in hand
    score -= calculate_card_points(hand_cards)

    return score
