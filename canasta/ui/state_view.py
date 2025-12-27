"""State view extraction for Canasta UI.

Provides a StateView dataclass that contains all data needed for rendering,
extracted from a CanastaState object.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from canasta.canasta_game import CanastaState
    from canasta.melds import Meld


@dataclass
class MeldView:
    """Extracted view of a meld for rendering.

    Attributes:
        rank: Rank index (0-12) of the meld
        natural_cards: List of natural card IDs
        wild_cards: List of wild card IDs
        is_canasta: Whether this meld is a canasta (7+ cards)
        is_natural_canasta: Whether this is a natural canasta (no wilds)
        is_mixed_canasta: Whether this is a mixed canasta (has wilds)
    """

    rank: int
    natural_cards: list[int] = field(default_factory=list)
    wild_cards: list[int] = field(default_factory=list)
    is_canasta: bool = False
    is_natural_canasta: bool = False
    is_mixed_canasta: bool = False

    @property
    def total_cards(self) -> int:
        """Total number of cards in the meld."""
        return len(self.natural_cards) + len(self.wild_cards)

    @property
    def all_cards(self) -> list[int]:
        """All cards in the meld (natural + wild)."""
        return self.natural_cards + self.wild_cards


@dataclass
class StateView:
    """Extracted view of game state for rendering.

    Contains all data needed to render the game state without
    requiring access to the CanastaState object directly.

    Attributes:
        hands: List of card IDs per player (4 lists)
        melds: List of MeldView per team (2 lists)
        stock_count: Number of cards in stock pile
        discard_pile: List of card IDs in discard pile (top is last)
        discard_top: Top card of discard pile, or None if empty
        red_threes: List of red three card IDs per team (2 lists)
        team_scores: Cumulative score per team [team0, team1]
        hand_scores: Current hand score per team [team0, team1]
        current_player: Current player index (0-3), or -1 if terminal
        turn_phase: Current turn phase ("draw", "meld", "discard")
        game_phase: Current game phase ("dealing", "playing", "terminal")
        pile_frozen: Whether discard pile is frozen
        initial_meld_made: Whether each team has made initial meld [team0, team1]
        canastas: Number of canastas per team [team0, team1]
        is_terminal: Whether game is over
        winning_team: Winning team index (0 or 1), or -1 if not determined
        hand_number: Current hand number
    """

    # Player hands
    hands: list[list[int]] = field(default_factory=lambda: [[], [], [], []])

    # Team melds
    melds: list[list[MeldView]] = field(default_factory=lambda: [[], []])

    # Pile information
    stock_count: int = 0
    discard_pile: list[int] = field(default_factory=list)
    discard_top: int | None = None

    # Red threes per team
    red_threes: list[list[int]] = field(default_factory=lambda: [[], []])

    # Scores
    team_scores: list[int] = field(default_factory=lambda: [0, 0])
    hand_scores: list[int] = field(default_factory=lambda: [0, 0])

    # Game state
    current_player: int = 0
    turn_phase: str = "draw"
    game_phase: str = "playing"
    pile_frozen: bool = False
    initial_meld_made: list[bool] = field(default_factory=lambda: [False, False])
    canastas: list[int] = field(default_factory=lambda: [0, 0])
    is_terminal: bool = False
    winning_team: int = -1
    hand_number: int = 0

    def hand_count(self, player: int) -> int:
        """Get number of cards in a player's hand.

        Args:
            player: Player index (0-3)

        Returns:
            Number of cards in hand
        """
        if 0 <= player < len(self.hands):
            return len(self.hands[player])
        return 0

    def team_of(self, player: int) -> int:
        """Get team index for a player.

        Args:
            player: Player index (0-3)

        Returns:
            Team index (0 or 1)
        """
        return player % 2

    def partner_of(self, player: int) -> int:
        """Get partner index for a player.

        Args:
            player: Player index (0-3)

        Returns:
            Partner player index
        """
        return (player + 2) % 4


def _extract_meld_view(meld: "Meld") -> MeldView:
    """Extract MeldView from a Meld object.

    Args:
        meld: Meld object from game state

    Returns:
        MeldView with extracted data
    """
    from canasta.melds import is_canasta, is_natural_canasta, is_mixed_canasta

    return MeldView(
        rank=meld.rank,
        natural_cards=list(meld.natural_cards),
        wild_cards=list(meld.wild_cards),
        is_canasta=is_canasta(meld),
        is_natural_canasta=is_natural_canasta(meld),
        is_mixed_canasta=is_mixed_canasta(meld),
    )


def extract_state_view(state: "CanastaState") -> StateView:
    """Extract a StateView from a CanastaState.

    Creates a StateView containing all data needed for rendering,
    extracted from the game state object.

    Args:
        state: CanastaState object

    Returns:
        StateView with all rendering data
    """
    # Extract melds for each team
    melds = [[], []]
    for team_idx in range(2):
        for meld in state._melds[team_idx]:
            melds[team_idx].append(_extract_meld_view(meld))

    # Get current player (handle terminal state)
    current = state.current_player()
    if current < 0:  # TERMINAL or CHANCE
        current_player = -1
    else:
        current_player = current

    # Get discard top
    discard_top = None
    if state._discard_pile:
        discard_top = state._discard_pile[-1]

    return StateView(
        hands=[list(hand) for hand in state._hands],
        melds=melds,
        stock_count=len(state._stock),
        discard_pile=list(state._discard_pile),
        discard_top=discard_top,
        red_threes=[list(rt) for rt in state._red_threes],
        team_scores=list(state._team_scores),
        hand_scores=list(state._hand_scores),
        current_player=current_player,
        turn_phase=getattr(state, "_turn_phase", "draw"),
        game_phase=getattr(state, "_game_phase", "playing"),
        pile_frozen=getattr(state, "_pile_frozen", False),
        initial_meld_made=list(state._initial_meld_made),
        canastas=list(state._canastas),
        is_terminal=state.is_terminal(),
        winning_team=getattr(state, "_winning_team", -1),
        hand_number=getattr(state, "_hand_number", 0),
    )
