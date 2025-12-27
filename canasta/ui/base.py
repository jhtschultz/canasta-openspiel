"""Abstract base class for Canasta renderers.

Provides the Renderer ABC that all concrete renderers must implement.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from canasta.canasta_game import CanastaState


class Renderer(ABC):
    """Abstract base class for game state renderers.

    Renderers convert a CanastaState into a visual representation.
    Subclasses implement the render method to produce output in
    their specific format (text, HTML, etc.).

    Attributes:
        perspective: Which player's view to show (0-3)
        show_all_hands: If True, show all hands (debug mode)
    """

    def __init__(self, perspective: int = 0, show_all_hands: bool = False):
        """Initialize the renderer.

        Args:
            perspective: Which player's view to render (0-3).
                         This player's hand is shown, others are hidden.
            show_all_hands: If True, show all players' hands (debug mode).
        """
        if perspective < 0 or perspective > 3:
            raise ValueError(f"perspective must be 0-3, got {perspective}")

        self.perspective = perspective
        self.show_all_hands = show_all_hands

    @abstractmethod
    def render(self, state: "CanastaState") -> str:
        """Render game state to string output.

        Args:
            state: CanastaState object to render

        Returns:
            String representation of the game state
        """
        pass

    def is_visible_hand(self, player: int) -> bool:
        """Check if a player's hand should be visible.

        Args:
            player: Player index (0-3)

        Returns:
            True if the hand should be shown (not hidden)
        """
        if self.show_all_hands:
            return True
        return player == self.perspective
