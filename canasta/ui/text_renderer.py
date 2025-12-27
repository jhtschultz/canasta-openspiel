"""ASCII text renderer for Canasta game states.

Renders game state as text output suitable for terminal display,
using an 80-column layout with Unicode box-drawing characters.
"""

from typing import TYPE_CHECKING

from canasta.ui.base import Renderer
from canasta.ui.cards import (
    card_to_str,
    format_hand_summary,
    rank_display_name,
)
from canasta.ui.state_view import StateView, extract_state_view, MeldView

if TYPE_CHECKING:
    from canasta.canasta_game import CanastaState


# Layout constants
MAX_WIDTH = 80
CENTER_WIDTH = 40
MELD_BOX_WIDTH = 36


class TextRenderer(Renderer):
    """ASCII text renderer for Canasta game states.

    Renders the game state as text output with:
    - Player positions around a virtual table
    - Meld areas for each team
    - Stock and discard piles in center
    - Score and status information
    """

    def render(self, state: "CanastaState") -> str:
        """Render game state to ASCII text.

        Args:
            state: CanastaState object to render

        Returns:
            Multi-line string representation of the game state
        """
        view = extract_state_view(state)
        lines = []

        # Build the display
        lines.extend(self._render_header(view))
        lines.append("")
        lines.extend(self._render_top_player(view))
        lines.append("")
        lines.extend(self._render_middle_section(view))
        lines.append("")
        lines.extend(self._render_bottom_player(view))
        lines.append("")
        lines.extend(self._render_footer(view))

        return "\n".join(lines)

    def _center_text(self, text: str, width: int = MAX_WIDTH) -> str:
        """Center text within the given width.

        Args:
            text: Text to center
            width: Width to center within

        Returns:
            Centered text with padding
        """
        return text.center(width)

    def _render_header(self, view: StateView) -> list[str]:
        """Render the header section.

        Args:
            view: StateView to render

        Returns:
            List of header lines
        """
        lines = []

        # Title
        if view.is_terminal:
            if view.winning_team >= 0:
                title = f"GAME OVER - Team {view.winning_team} Wins!"
            else:
                title = "GAME OVER"
        else:
            title = f"CANASTA - Hand {view.hand_number + 1}"

        lines.append(self._center_text("=" * 60))
        lines.append(self._center_text(title))
        lines.append(self._center_text("=" * 60))

        return lines

    def _render_top_player(self, view: StateView) -> list[str]:
        """Render the top player (Player 2 - partner of perspective player).

        Args:
            view: StateView to render

        Returns:
            List of lines for top player area
        """
        lines = []
        player = 2

        # Player label
        label = self._get_player_label(player, view)
        lines.append(self._center_text(label))

        # Hand display
        hand_display = self._format_player_hand(player, view)
        lines.append(self._center_text(hand_display))

        return lines

    def _render_middle_section(self, view: StateView) -> list[str]:
        """Render the middle section with side players, melds, and piles.

        Args:
            view: StateView to render

        Returns:
            List of lines for middle section
        """
        lines = []

        # Team 1 melds box (top center box)
        team1_melds = self._format_melds_box(1, view)

        # Side players
        left_player = 1
        right_player = 3
        left_label = self._get_player_label(left_player, view)
        right_label = self._get_player_label(right_player, view)
        left_hand = self._format_player_hand(left_player, view)
        right_hand = self._format_player_hand(right_player, view)

        # Build the section line by line
        # First, render Team 1 meld box
        for meld_line in team1_melds:
            lines.append(self._center_text(meld_line))

        lines.append("")

        # Side players with their hands
        side_format = "{:<20}{:^40}{:>20}"
        lines.append(side_format.format(left_label, "", right_label))
        lines.append(side_format.format(left_hand, "", right_hand))

        lines.append("")

        # Stock and discard piles
        lines.extend(self._render_piles(view))

        lines.append("")

        # Team 0 melds box
        team0_melds = self._format_melds_box(0, view)
        for meld_line in team0_melds:
            lines.append(self._center_text(meld_line))

        return lines

    def _render_piles(self, view: StateView) -> list[str]:
        """Render stock and discard piles.

        Args:
            view: StateView to render

        Returns:
            List of lines for pile display
        """
        lines = []

        # Labels
        lines.append(self._center_text("STOCK          DISCARD"))

        # Cards
        stock_display = f"({view.stock_count})"
        if view.discard_top is not None:
            discard_display = card_to_str(view.discard_top)
            if len(view.discard_pile) > 1:
                discard_display += f" (+{len(view.discard_pile) - 1})"
        else:
            discard_display = "(empty)"

        pile_line = f"{stock_display:^15}{discard_display:^15}"
        lines.append(self._center_text(pile_line))

        # Frozen indicator
        if view.pile_frozen:
            lines.append(self._center_text("*FROZEN*"))

        return lines

    def _render_bottom_player(self, view: StateView) -> list[str]:
        """Render the bottom player (Player 0 - perspective player).

        Args:
            view: StateView to render

        Returns:
            List of lines for bottom player area
        """
        lines = []
        player = 0

        # Player label
        label = self._get_player_label(player, view)
        lines.append(self._center_text(label))

        # Hand display (always visible for perspective player)
        hand_display = self._format_player_hand(player, view)
        lines.append(self._center_text(hand_display))

        return lines

    def _render_footer(self, view: StateView) -> list[str]:
        """Render footer with scores and status.

        Args:
            view: StateView to render

        Returns:
            List of footer lines
        """
        lines = []
        lines.append("-" * MAX_WIDTH)

        # Red threes
        rt_line = self._format_red_threes(view)
        if rt_line:
            lines.append(rt_line)

        # Scores
        score_line = f"SCORES: Team 0: {view.team_scores[0]} | Team 1: {view.team_scores[1]}"
        lines.append(self._center_text(score_line))

        # Hand scores if non-zero
        if view.hand_scores[0] != 0 or view.hand_scores[1] != 0:
            hand_score_line = f"(Hand: Team 0: {view.hand_scores[0]} | Team 1: {view.hand_scores[1]})"
            lines.append(self._center_text(hand_score_line))

        # Game status
        status_parts = []

        if view.is_terminal:
            status_parts.append("Game: TERMINAL")
        else:
            if view.current_player >= 0:
                status_parts.append(f"Turn: Player {view.current_player}")
            status_parts.append(f"Phase: {view.turn_phase.upper()}")

        if view.pile_frozen:
            status_parts.append("Pile: FROZEN")

        status_line = " | ".join(status_parts)
        lines.append(self._center_text(status_line))

        # Canastas
        canasta_line = f"Canastas: Team 0: {view.canastas[0]} | Team 1: {view.canastas[1]}"
        lines.append(self._center_text(canasta_line))

        lines.append("-" * MAX_WIDTH)

        return lines

    def _get_player_label(self, player: int, view: StateView) -> str:
        """Get label for a player position.

        Args:
            player: Player index (0-3)
            view: StateView for context

        Returns:
            Label string like "PLAYER 0 (You)" or "PLAYER 2 (Partner)"
        """
        team = view.team_of(player)

        if player == self.perspective:
            role = "(You)"
        elif player == view.partner_of(self.perspective):
            role = "(Partner)"
        else:
            role = f"(Team {team})"

        # Current player indicator
        current_marker = ""
        if view.current_player == player:
            current_marker = " *"

        return f"PLAYER {player} {role}{current_marker}"

    def _format_player_hand(self, player: int, view: StateView) -> str:
        """Format a player's hand for display.

        Args:
            player: Player index (0-3)
            view: StateView containing hands

        Returns:
            Formatted hand string
        """
        hand = view.hands[player]
        card_count = len(hand)

        if card_count == 0:
            return "(no cards)"

        # Show visible hands, hide others
        if self.is_visible_hand(player):
            # Show actual cards
            cards = "".join(card_to_str(c) for c in sorted(hand))
            # Truncate if too long
            if len(cards) > 70:
                cards = cards[:67] + "..."
            return cards
        else:
            # Show count only
            return format_hand_summary(card_count)

    def _format_melds_box(self, team: int, view: StateView) -> list[str]:
        """Format a meld display box for a team.

        Args:
            team: Team index (0 or 1)
            view: StateView containing melds

        Returns:
            List of lines for meld box
        """
        lines = []
        team_melds = view.melds[team]

        # Box top
        box_top = f"[ Team {team} Melds ]"
        lines.append(box_top.center(MELD_BOX_WIDTH, "-"))

        if not team_melds:
            lines.append("(no melds)".center(MELD_BOX_WIDTH))
        else:
            for meld in team_melds:
                meld_line = self._format_meld(meld)
                lines.append(meld_line)

        # Box bottom
        lines.append("-" * MELD_BOX_WIDTH)

        return lines

    def _format_meld(self, meld: MeldView) -> str:
        """Format a single meld for display.

        Args:
            meld: MeldView to format

        Returns:
            Formatted meld string
        """
        rank_name = rank_display_name(meld.rank)

        # Canasta marker
        if meld.is_natural_canasta:
            marker = " [NATURAL]"
        elif meld.is_mixed_canasta:
            marker = " [MIXED]"
        else:
            marker = ""

        # Card count
        count = meld.total_cards

        # Show a few cards as preview
        all_cards = meld.natural_cards + meld.wild_cards
        if len(all_cards) <= 4:
            cards_preview = "".join(card_to_str(c) for c in all_cards)
        else:
            cards_preview = "".join(card_to_str(c) for c in all_cards[:3]) + "..."

        return f"  {rank_name} ({count}): {cards_preview}{marker}"

    def _format_red_threes(self, view: StateView) -> str:
        """Format red threes display.

        Args:
            view: StateView containing red threes

        Returns:
            Formatted red threes line, or empty string if none
        """
        parts = []

        for team in range(2):
            rt_cards = view.red_threes[team]
            if rt_cards:
                cards = "".join(card_to_str(c) for c in rt_cards)
                parts.append(f"Team {team}: {cards}")

        if parts:
            return "Red Threes: " + " | ".join(parts)
        return ""
