"""Deterministic game state fixtures for Canasta UI testing.

These fixtures create reproducible CanastaState objects with known properties
for use in rendering and visual verification.
"""

import pyspiel
from canasta.canasta_game import CanastaGame, CanastaState
from canasta.melds import Meld
from canasta.cards import cards_of_rank, RANKS


def _get_game():
    """Get a CanastaGame instance."""
    return pyspiel.load_game("python_canasta")


def _card_id(rank_idx: int, suit_idx: int, deck: int = 0) -> int:
    """Convert rank, suit, deck to card ID.

    Args:
        rank_idx: Rank index (0=A, 1=2, 2=3, ..., 12=K)
        suit_idx: Suit index (0=clubs, 1=diamonds, 2=hearts, 3=spades)
        deck: Deck number (0 or 1)

    Returns:
        Card ID (0-107)
    """
    return deck * 52 + suit_idx * 13 + rank_idx


def _setup_post_dealing_state(state: CanastaState) -> None:
    """Configure state as if dealing has completed.

    Args:
        state: CanastaState to configure
    """
    state._dealing_phase = False
    state._game_phase = "playing"
    state._turn_phase = "draw"
    state._current_player = 0
    state._deck = []  # Deck is consumed after dealing
    state._cards_dealt = 44  # 4 players * 11 cards


def create_early_game_state() -> CanastaState:
    """Create an early game state: after dealing, full hands, no melds, empty discard.

    This represents the game state right after dealing is complete:
    - Each player has 11 cards
    - No melds have been made
    - Discard pile has only the initial card
    - Stock has remaining cards

    Returns:
        CanastaState with early game configuration
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure post-dealing state
    _setup_post_dealing_state(state)

    # Deal deterministic hands (11 cards each)
    # Player 0 (Team 0): Mix of high cards
    state._hands[0] = [
        _card_id(0, 0),   # A clubs
        _card_id(0, 1),   # A diamonds
        _card_id(12, 0),  # K clubs
        _card_id(12, 1),  # K diamonds
        _card_id(11, 0),  # Q clubs
        _card_id(11, 1),  # Q diamonds
        _card_id(10, 0),  # J clubs
        _card_id(10, 1),  # J diamonds
        _card_id(9, 0),   # 10 clubs
        _card_id(9, 1),   # 10 diamonds
        _card_id(8, 0),   # 9 clubs
    ]

    # Player 1 (Team 1): Mix of mid-range cards
    state._hands[1] = [
        _card_id(7, 0),   # 8 clubs
        _card_id(7, 1),   # 8 diamonds
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
        _card_id(5, 1),   # 6 diamonds
        _card_id(4, 0),   # 5 clubs
        _card_id(4, 1),   # 5 diamonds
        _card_id(3, 0),   # 4 clubs
        _card_id(3, 1),   # 4 diamonds
        _card_id(0, 2),   # A hearts
    ]

    # Player 2 (Team 0): Partner of player 0
    state._hands[2] = [
        _card_id(0, 3),   # A spades
        _card_id(12, 2),  # K hearts
        _card_id(12, 3),  # K spades
        _card_id(11, 2),  # Q hearts
        _card_id(11, 3),  # Q spades
        _card_id(10, 2),  # J hearts
        _card_id(10, 3),  # J spades
        _card_id(9, 2),   # 10 hearts
        _card_id(9, 3),   # 10 spades
        _card_id(8, 1),   # 9 diamonds
        _card_id(8, 2),   # 9 hearts
    ]

    # Player 3 (Team 1): Partner of player 1
    state._hands[3] = [
        _card_id(7, 2),   # 8 hearts
        _card_id(7, 3),   # 8 spades
        _card_id(6, 2),   # 7 hearts
        _card_id(6, 3),   # 7 spades
        _card_id(5, 2),   # 6 hearts
        _card_id(5, 3),   # 6 spades
        _card_id(4, 2),   # 5 hearts
        _card_id(4, 3),   # 5 spades
        _card_id(3, 2),   # 4 hearts
        _card_id(3, 3),   # 4 spades
        _card_id(0, 0, 1),  # A clubs (2nd deck)
    ]

    # Initial discard pile (one card)
    state._discard_pile = [_card_id(8, 3)]  # 9 spades

    # Stock: remaining cards (not in hands or discard)
    used_cards = set()
    for hand in state._hands:
        used_cards.update(hand)
    used_cards.update(state._discard_pile)

    state._stock = [c for c in range(108) if c not in used_cards]

    # No melds yet
    state._melds = [[], []]
    state._canastas = [0, 0]
    state._red_threes = [[], []]
    state._initial_meld_made = [False, False]

    return state


def create_mid_game_state() -> CanastaState:
    """Create a mid-game state: melds on both teams, partial hands, cards in discard.

    This represents a game in progress:
    - Both teams have made initial melds
    - Players have fewer cards in hand
    - Discard pile has multiple cards
    - Some cards have been melded

    Returns:
        CanastaState with mid-game configuration
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure post-dealing state
    _setup_post_dealing_state(state)

    # Smaller hands (6-7 cards each)
    state._hands[0] = [
        _card_id(0, 0),   # A clubs
        _card_id(12, 0),  # K clubs
        _card_id(12, 1),  # K diamonds
        _card_id(11, 0),  # Q clubs
        _card_id(10, 0),  # J clubs
        _card_id(1, 0),   # 2 clubs (wild)
    ]

    state._hands[1] = [
        _card_id(7, 0),   # 8 clubs
        _card_id(7, 1),   # 8 diamonds
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
        _card_id(5, 1),   # 6 diamonds
        _card_id(1, 1),   # 2 diamonds (wild)
    ]

    state._hands[2] = [
        _card_id(0, 3),   # A spades
        _card_id(11, 2),  # Q hearts
        _card_id(11, 3),  # Q spades
        _card_id(10, 2),  # J hearts
        _card_id(9, 2),   # 10 hearts
        104,              # Joker
    ]

    state._hands[3] = [
        _card_id(4, 2),   # 5 hearts
        _card_id(4, 3),   # 5 spades
        _card_id(3, 2),   # 4 hearts
        _card_id(3, 3),   # 4 spades
        _card_id(6, 2),   # 7 hearts
        _card_id(6, 3),   # 7 spades
    ]

    # Team 0 melds: Aces (3 naturals + 1 wild = 4 cards)
    team0_meld = Meld(
        rank=0,  # Aces
        natural_cards=[_card_id(0, 1), _card_id(0, 2), _card_id(0, 0, 1)],  # A diamonds, A hearts, A clubs deck2
        wild_cards=[_card_id(1, 2)],  # 2 hearts
    )
    state._melds[0] = [team0_meld]

    # Team 1 melds: 8s (3 naturals)
    team1_meld = Meld(
        rank=7,  # 8s
        natural_cards=[_card_id(7, 2), _card_id(7, 3), _card_id(7, 0, 1)],  # 8 hearts, 8 spades, 8 clubs deck2
        wild_cards=[],
    )
    state._melds[1] = [team1_meld]

    state._initial_meld_made = [True, True]
    state._canastas = [0, 0]

    # Discard pile with several cards
    state._discard_pile = [
        _card_id(9, 0),   # 10 clubs
        _card_id(9, 1),   # 10 diamonds
        _card_id(8, 0),   # 9 clubs
        _card_id(8, 1),   # 9 diamonds
        _card_id(8, 3),   # 9 spades
    ]

    # Build stock from remaining cards
    used_cards = set()
    for hand in state._hands:
        used_cards.update(hand)
    used_cards.update(state._discard_pile)
    for team_melds in state._melds:
        for meld in team_melds:
            used_cards.update(meld.natural_cards)
            used_cards.update(meld.wild_cards)

    state._stock = [c for c in range(108) if c not in used_cards]
    state._red_threes = [[], []]

    return state


def create_canasta_state() -> CanastaState:
    """Create a state with canastas: Team 0 has natural, Team 1 has mixed.

    This represents a game where:
    - Team 0 has a natural canasta (7+ cards, no wilds)
    - Team 1 has a mixed canasta (7+ cards with wilds)

    Returns:
        CanastaState with canasta configuration
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure post-dealing state
    _setup_post_dealing_state(state)

    # Smaller hands
    state._hands[0] = [
        _card_id(12, 0),  # K clubs
        _card_id(12, 1),  # K diamonds
        _card_id(11, 0),  # Q clubs
        _card_id(1, 0),   # 2 clubs (wild)
    ]

    state._hands[1] = [
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
        _card_id(5, 1),   # 6 diamonds
    ]

    state._hands[2] = [
        _card_id(11, 2),  # Q hearts
        _card_id(11, 3),  # Q spades
        _card_id(10, 2),  # J hearts
        105,              # Joker
    ]

    state._hands[3] = [
        _card_id(4, 2),   # 5 hearts
        _card_id(4, 3),   # 5 spades
        _card_id(3, 2),   # 4 hearts
        _card_id(3, 3),   # 4 spades
    ]

    # Team 0: Natural canasta of Aces (7 naturals, no wilds)
    team0_canasta = Meld(
        rank=0,  # Aces
        natural_cards=[
            _card_id(0, 0),      # A clubs deck1
            _card_id(0, 1),      # A diamonds deck1
            _card_id(0, 2),      # A hearts deck1
            _card_id(0, 3),      # A spades deck1
            _card_id(0, 0, 1),   # A clubs deck2
            _card_id(0, 1, 1),   # A diamonds deck2
            _card_id(0, 2, 1),   # A hearts deck2
        ],
        wild_cards=[],
    )
    state._melds[0] = [team0_canasta]
    state._canastas[0] = 1

    # Team 1: Mixed canasta of 8s (5 naturals + 2 wilds)
    team1_canasta = Meld(
        rank=7,  # 8s
        natural_cards=[
            _card_id(7, 0),      # 8 clubs deck1
            _card_id(7, 1),      # 8 diamonds deck1
            _card_id(7, 2),      # 8 hearts deck1
            _card_id(7, 3),      # 8 spades deck1
            _card_id(7, 0, 1),   # 8 clubs deck2
        ],
        wild_cards=[
            _card_id(1, 1),   # 2 diamonds
            _card_id(1, 2),   # 2 hearts
        ],
    )
    state._melds[1] = [team1_canasta]
    state._canastas[1] = 1

    state._initial_meld_made = [True, True]

    # Discard pile
    state._discard_pile = [
        _card_id(9, 0),   # 10 clubs
        _card_id(8, 0),   # 9 clubs
    ]

    # Build stock from remaining cards
    used_cards = set()
    for hand in state._hands:
        used_cards.update(hand)
    used_cards.update(state._discard_pile)
    for team_melds in state._melds:
        for meld in team_melds:
            used_cards.update(meld.natural_cards)
            used_cards.update(meld.wild_cards)

    state._stock = [c for c in range(108) if c not in used_cards]
    state._red_threes = [[], []]

    return state


def create_frozen_pile_state() -> CanastaState:
    """Create a state with frozen pile: wild card in discard pile.

    The pile is frozen when:
    - A wild card has been discarded
    - Team hasn't made initial meld (always frozen for them)

    This state has a wild card in the discard pile, making it frozen.

    Returns:
        CanastaState with frozen pile configuration
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure post-dealing state
    _setup_post_dealing_state(state)

    # Standard hands
    state._hands[0] = [
        _card_id(0, 0),   # A clubs
        _card_id(0, 1),   # A diamonds
        _card_id(12, 0),  # K clubs
        _card_id(12, 1),  # K diamonds
        _card_id(11, 0),  # Q clubs
        _card_id(11, 1),  # Q diamonds
        _card_id(10, 0),  # J clubs
    ]

    state._hands[1] = [
        _card_id(7, 0),   # 8 clubs
        _card_id(7, 1),   # 8 diamonds
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
        _card_id(5, 1),   # 6 diamonds
        _card_id(4, 0),   # 5 clubs
    ]

    state._hands[2] = [
        _card_id(0, 3),   # A spades
        _card_id(12, 2),  # K hearts
        _card_id(12, 3),  # K spades
        _card_id(11, 2),  # Q hearts
        _card_id(11, 3),  # Q spades
        _card_id(10, 2),  # J hearts
        _card_id(10, 3),  # J spades
    ]

    state._hands[3] = [
        _card_id(7, 2),   # 8 hearts
        _card_id(7, 3),   # 8 spades
        _card_id(6, 2),   # 7 hearts
        _card_id(6, 3),   # 7 spades
        _card_id(5, 2),   # 6 hearts
        _card_id(5, 3),   # 6 spades
        _card_id(4, 2),   # 5 hearts
    ]

    # Discard pile with wild card (freezes the pile)
    state._discard_pile = [
        _card_id(9, 0),   # 10 clubs
        _card_id(9, 1),   # 10 diamonds
        _card_id(1, 3),   # 2 spades (WILD - freezes pile)
        _card_id(8, 0),   # 9 clubs
    ]
    state._pile_frozen = True

    # No melds yet
    state._melds = [[], []]
    state._canastas = [0, 0]
    state._initial_meld_made = [False, False]

    # Build stock from remaining cards
    used_cards = set()
    for hand in state._hands:
        used_cards.update(hand)
    used_cards.update(state._discard_pile)

    state._stock = [c for c in range(108) if c not in used_cards]
    state._red_threes = [[], []]

    return state


def create_red_threes_state() -> CanastaState:
    """Create a state with red threes placed for both teams.

    Red threes (3 of diamonds and 3 of hearts) are automatically set aside
    when dealt or drawn. Each team's red threes are tracked separately.

    Returns:
        CanastaState with red threes for both teams
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure post-dealing state
    _setup_post_dealing_state(state)

    # Red threes card IDs:
    # 3 of diamonds: rank=2, suit=1 -> 1*13 + 2 = 15 (deck 1), 52+15 = 67 (deck 2)
    # 3 of hearts: rank=2, suit=2 -> 2*13 + 2 = 28 (deck 1), 52+28 = 80 (deck 2)

    # Team 0 has 2 red threes (both 3 of hearts)
    state._red_threes[0] = [
        _card_id(2, 2),      # 3 hearts deck1
        _card_id(2, 2, 1),   # 3 hearts deck2
    ]

    # Team 1 has 2 red threes (both 3 of diamonds)
    state._red_threes[1] = [
        _card_id(2, 1),      # 3 diamonds deck1
        _card_id(2, 1, 1),   # 3 diamonds deck2
    ]

    # Standard hands (11 cards each, no red threes)
    state._hands[0] = [
        _card_id(0, 0),   # A clubs
        _card_id(0, 1),   # A diamonds
        _card_id(12, 0),  # K clubs
        _card_id(12, 1),  # K diamonds
        _card_id(11, 0),  # Q clubs
        _card_id(11, 1),  # Q diamonds
        _card_id(10, 0),  # J clubs
        _card_id(10, 1),  # J diamonds
        _card_id(9, 0),   # 10 clubs
        _card_id(9, 1),   # 10 diamonds
        _card_id(8, 0),   # 9 clubs
    ]

    state._hands[1] = [
        _card_id(7, 0),   # 8 clubs
        _card_id(7, 1),   # 8 diamonds
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
        _card_id(5, 1),   # 6 diamonds
        _card_id(4, 0),   # 5 clubs
        _card_id(4, 1),   # 5 diamonds
        _card_id(3, 0),   # 4 clubs
        _card_id(3, 1),   # 4 diamonds
        _card_id(0, 2),   # A hearts
    ]

    state._hands[2] = [
        _card_id(0, 3),   # A spades
        _card_id(12, 2),  # K hearts
        _card_id(12, 3),  # K spades
        _card_id(11, 2),  # Q hearts
        _card_id(11, 3),  # Q spades
        _card_id(10, 2),  # J hearts
        _card_id(10, 3),  # J spades
        _card_id(9, 2),   # 10 hearts
        _card_id(9, 3),   # 10 spades
        _card_id(8, 1),   # 9 diamonds
        _card_id(8, 2),   # 9 hearts
    ]

    state._hands[3] = [
        _card_id(7, 2),   # 8 hearts
        _card_id(7, 3),   # 8 spades
        _card_id(6, 2),   # 7 hearts
        _card_id(6, 3),   # 7 spades
        _card_id(5, 2),   # 6 hearts
        _card_id(5, 3),   # 6 spades
        _card_id(4, 2),   # 5 hearts
        _card_id(4, 3),   # 5 spades
        _card_id(3, 2),   # 4 hearts
        _card_id(3, 3),   # 4 spades
        _card_id(0, 0, 1),  # A clubs deck2
    ]

    # Discard pile
    state._discard_pile = [_card_id(8, 3)]  # 9 spades

    # Build stock from remaining cards
    used_cards = set()
    for hand in state._hands:
        used_cards.update(hand)
    used_cards.update(state._discard_pile)
    for team_red_threes in state._red_threes:
        used_cards.update(team_red_threes)

    state._stock = [c for c in range(108) if c not in used_cards]

    # No melds yet
    state._melds = [[], []]
    state._canastas = [0, 0]
    state._initial_meld_made = [False, False]

    return state


def create_terminal_state() -> CanastaState:
    """Create a terminal state: game over with final scores.

    This represents a completed game where:
    - One team has gone out
    - Final scores have been calculated
    - The game is in terminal state

    Returns:
        CanastaState in terminal configuration
    """
    game = _get_game()
    state = game.new_initial_state()

    # Configure terminal state
    state._dealing_phase = False
    state._game_phase = "terminal"
    state._is_terminal = True
    state._game_over = True
    state._deck = []
    state._cards_dealt = 44

    # Empty hands (Team 0 went out)
    state._hands[0] = []
    state._hands[2] = []

    # Team 1 still has cards (penalty)
    state._hands[1] = [
        _card_id(6, 0),   # 7 clubs
        _card_id(6, 1),   # 7 diamonds
        _card_id(5, 0),   # 6 clubs
    ]
    state._hands[3] = [
        _card_id(4, 2),   # 5 hearts
        _card_id(4, 3),   # 5 spades
    ]

    # Team 0: Natural canasta of Aces + Queens meld
    team0_canasta = Meld(
        rank=0,  # Aces
        natural_cards=[
            _card_id(0, 0),
            _card_id(0, 1),
            _card_id(0, 2),
            _card_id(0, 3),
            _card_id(0, 0, 1),
            _card_id(0, 1, 1),
            _card_id(0, 2, 1),
        ],
        wild_cards=[],
    )
    team0_queens = Meld(
        rank=11,  # Queens
        natural_cards=[
            _card_id(11, 0),
            _card_id(11, 1),
            _card_id(11, 2),
        ],
        wild_cards=[_card_id(1, 0)],  # 2 clubs
    )
    state._melds[0] = [team0_canasta, team0_queens]
    state._canastas[0] = 1

    # Team 1: Mixed canasta of 8s
    team1_canasta = Meld(
        rank=7,  # 8s
        natural_cards=[
            _card_id(7, 0),
            _card_id(7, 1),
            _card_id(7, 2),
            _card_id(7, 3),
            _card_id(7, 0, 1),
        ],
        wild_cards=[
            _card_id(1, 1),
            _card_id(1, 2),
        ],
    )
    state._melds[1] = [team1_canasta]
    state._canastas[1] = 1

    state._initial_meld_made = [True, True]

    # Red threes
    state._red_threes[0] = [_card_id(2, 2)]  # 3 hearts
    state._red_threes[1] = [_card_id(2, 1)]  # 3 diamonds

    # Final scores
    # Team 0: Natural canasta (500) + card points + going out bonus (100)
    # Team 1: Mixed canasta (300) + card points - cards in hand
    state._team_scores = [1250, 680]
    state._hand_scores = [1250, 680]
    state._winning_team = 0

    # Set returns (players 0,2 are Team 0, players 1,3 are Team 1)
    state._returns = [1250.0, 680.0, 1250.0, 680.0]

    # Empty discard and stock
    state._discard_pile = [_card_id(9, 0)]  # Last discarded card
    state._stock = []

    return state


def get_all_fixtures() -> dict[str, CanastaState]:
    """Get all fixture states as a dictionary.

    Returns:
        Dictionary mapping fixture names to CanastaState objects
    """
    return {
        "early_game": create_early_game_state(),
        "mid_game": create_mid_game_state(),
        "canasta": create_canasta_state(),
        "frozen_pile": create_frozen_pile_state(),
        "red_threes": create_red_threes_state(),
        "terminal": create_terminal_state(),
    }
