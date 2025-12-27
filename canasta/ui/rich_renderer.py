"""Rich terminal renderer for Canasta game states.

Renders game state with colored output using the rich library,
featuring Canasta Junction-inspired color scheme.
"""

from typing import TYPE_CHECKING

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from canasta.cards import card_id_to_rank_suit
from canasta.ui.base import Renderer
from canasta.ui.cards import (
    card_to_str,
    format_hand_summary,
    rank_display_name,
    SUIT_SYMBOLS,
)
from canasta.ui.state_view import StateView, extract_state_view, MeldView

if TYPE_CHECKING:
    from canasta.canasta_game import CanastaState


# Color scheme inspired by Canasta Junction
# Primary teal: #008373
# Hearts/Diamonds: red
# Clubs/Spades: default (white/black for terminal)
# Jokers: magenta/purple
# Natural Canasta: gold/yellow
# Mixed Canasta: silver/bright_black

STYLE_PRIMARY = "bold #008373"  # Teal
STYLE_HEARTS = "red"
STYLE_DIAMONDS = "red"
STYLE_CLUBS = "white"
STYLE_SPADES = "white"
STYLE_JOKER = "magenta"
STYLE_NATURAL_CANASTA = "bold yellow"  # Gold
STYLE_MIXED_CANASTA = "bold bright_black"  # Silver
STYLE_FROZEN = "bold red"
STYLE_CURRENT_PLAYER = "bold cyan"
STYLE_HEADER = "bold #008373"
STYLE_FOOTER = "dim"
STYLE_WILD = "bold magenta"

# Layout constants
MAX_WIDTH = 80
CENTER_WIDTH = 40
MELD_BOX_WIDTH = 36


class RichRenderer(Renderer):
    """Rich terminal renderer for Canasta game states.

    Renders the game state with colored output using rich library,
    featuring:
    - Red suits (hearts, diamonds) in red
    - Black suits (clubs, spades) in default/white
    - Jokers in magenta/purple
    - Canasta Junction teal (#008373) for headers/accents
    - Gold for natural canastas, silver for mixed
    """

    def __init__(self, perspective: int = 0, show_all_hands: bool = False):
        """Initialize the rich renderer.

        Args:
            perspective: Which player's view to render (0-3).
            show_all_hands: If True, show all players' hands (debug mode).
        """
        super().__init__(perspective, show_all_hands)
        self.console = Console(force_terminal=True, width=MAX_WIDTH)

    def render(self, state: "CanastaState") -> str:
        """Render game state to colored terminal text.

        Args:
            state: CanastaState object to render

        Returns:
            Multi-line string representation with ANSI color codes
        """
        view = extract_state_view(state)

        # Build output using rich Text objects
        output = Text()

        # Header
        self._render_header(view, output)
        output.append("\n\n")

        # Top player
        self._render_top_player(view, output)
        output.append("\n\n")

        # Middle section (side players, piles, melds)
        self._render_middle_section(view, output)
        output.append("\n\n")

        # Bottom player
        self._render_bottom_player(view, output)
        output.append("\n\n")

        # Footer
        self._render_footer(view, output)

        # Convert to string with ANSI codes
        with self.console.capture() as capture:
            self.console.print(output, end="")
        return capture.get()

    def _card_styled(self, card_id: int) -> Text:
        """Create a styled Text object for a card.

        Args:
            card_id: Card ID (0-107)

        Returns:
            Text object with appropriate styling
        """
        rank, suit = card_id_to_rank_suit(card_id)

        # Jokers
        if suit is None:
            return Text("[JKR]", style=STYLE_JOKER)

        # Get suit symbol
        suit_symbol = SUIT_SYMBOLS[suit]
        card_str = f"[{rank}{suit_symbol}]"

        # Apply suit-based styling
        if suit == "hearts":
            return Text(card_str, style=STYLE_HEARTS)
        elif suit == "diamonds":
            return Text(card_str, style=STYLE_DIAMONDS)
        elif suit == "clubs":
            return Text(card_str, style=STYLE_CLUBS)
        else:  # spades
            return Text(card_str, style=STYLE_SPADES)

    def _format_cards_styled(self, card_ids: list[int]) -> Text:
        """Format a list of cards with styling.

        Args:
            card_ids: List of card IDs

        Returns:
            Text object with all cards styled
        """
        result = Text()
        for card_id in sorted(card_ids):
            result.append_text(self._card_styled(card_id))
        return result

    def _center_text(self, text: str | Text, width: int = MAX_WIDTH) -> Text:
        """Center text within the given width.

        Args:
            text: Text to center (string or Text object)
            width: Width to center within

        Returns:
            Centered Text object
        """
        if isinstance(text, str):
            text = Text(text)

        # Calculate padding
        text_len = len(text.plain)
        if text_len >= width:
            return text

        pad_total = width - text_len
        pad_left = pad_total // 2

        result = Text(" " * pad_left)
        result.append_text(text)
        return result

    def _render_header(self, view: StateView, output: Text) -> None:
        """Render the header section.

        Args:
            view: StateView to render
            output: Text object to append to
        """
        # Title
        if view.is_terminal:
            if view.winning_team >= 0:
                title = f"GAME OVER - Team {view.winning_team} Wins!"
            else:
                title = "GAME OVER"
        else:
            title = f"CANASTA - Hand {view.hand_number + 1}"

        separator = Text("=" * 60, style=STYLE_HEADER)
        title_text = Text(title, style=STYLE_HEADER)

        output.append_text(self._center_text(separator))
        output.append("\n")
        output.append_text(self._center_text(title_text))
        output.append("\n")
        output.append_text(self._center_text(separator))

    def _render_top_player(self, view: StateView, output: Text) -> None:
        """Render the top player (Player 2 - partner of perspective player).

        Args:
            view: StateView to render
            output: Text object to append to
        """
        player = 2

        # Player label
        label = self._get_player_label_styled(player, view)
        output.append_text(self._center_text(label))
        output.append("\n")

        # Hand display
        hand_display = self._format_player_hand_styled(player, view)
        output.append_text(self._center_text(hand_display))

    def _render_middle_section(self, view: StateView, output: Text) -> None:
        """Render the middle section with side players, melds, and piles.

        Args:
            view: StateView to render
            output: Text object to append to
        """
        # Team 1 melds box (top center box)
        team1_melds = self._format_melds_box_styled(1, view)
        for meld_line in team1_melds:
            output.append_text(self._center_text(meld_line))
            output.append("\n")

        output.append("\n")

        # Side players
        left_player = 1
        right_player = 3
        left_label = self._get_player_label_styled(left_player, view)
        right_label = self._get_player_label_styled(right_player, view)

        # Side player labels line
        side_line = self._format_side_line(left_label, Text(), right_label)
        output.append_text(side_line)
        output.append("\n")

        # Side player hands line
        left_hand = self._format_player_hand_styled(left_player, view)
        right_hand = self._format_player_hand_styled(right_player, view)
        side_line = self._format_side_line(left_hand, Text(), right_hand)
        output.append_text(side_line)
        output.append("\n\n")

        # Stock and discard piles
        self._render_piles(view, output)

        output.append("\n")

        # Team 0 melds box
        team0_melds = self._format_melds_box_styled(0, view)
        for meld_line in team0_melds:
            output.append_text(self._center_text(meld_line))
            output.append("\n")

    def _format_side_line(
        self, left: Text, center: Text, right: Text, width: int = MAX_WIDTH
    ) -> Text:
        """Format a three-column line with left, center, and right content.

        Args:
            left: Left-aligned content
            center: Centered content
            right: Right-aligned content
            width: Total line width

        Returns:
            Formatted line as Text object
        """
        col_width = width // 3

        # Pad/truncate each section
        left_plain = left.plain[:col_width]
        left_padded = left_plain.ljust(col_width)

        center_plain = center.plain[:col_width]
        center_pad = (col_width - len(center_plain)) // 2
        center_padded = " " * center_pad + center_plain
        center_padded = center_padded[:col_width].ljust(col_width)

        right_plain = right.plain[:col_width]
        right_padded = right_plain.rjust(col_width)

        # Build styled result
        result = Text()

        # Add left with styling
        if left.plain:
            result.append_text(left)
            result.append(" " * (col_width - len(left.plain)))
        else:
            result.append(" " * col_width)

        # Add center with styling
        if center.plain:
            result.append(" " * center_pad)
            result.append_text(center)
            remaining = col_width - center_pad - len(center.plain)
            result.append(" " * max(0, remaining))
        else:
            result.append(" " * col_width)

        # Add right with styling (right-aligned)
        if right.plain:
            result.append(" " * (col_width - len(right.plain)))
            result.append_text(right)
        else:
            result.append(" " * col_width)

        return result

    def _render_piles(self, view: StateView, output: Text) -> None:
        """Render stock and discard piles.

        Args:
            view: StateView to render
            output: Text object to append to
        """
        # Labels
        labels = Text()
        labels.append("STOCK", style=STYLE_PRIMARY)
        labels.append("          ")
        labels.append("DISCARD", style=STYLE_PRIMARY)
        output.append_text(self._center_text(labels))
        output.append("\n")

        # Cards
        stock_display = Text(f"({view.stock_count})")

        if view.discard_top is not None:
            discard_display = self._card_styled(view.discard_top)
            if len(view.discard_pile) > 1:
                discard_display.append(f" (+{len(view.discard_pile) - 1})")
        else:
            discard_display = Text("(empty)")

        pile_line = Text()
        pile_line.append_text(stock_display)
        pile_line.append("          ")
        pile_line.append_text(discard_display)
        output.append_text(self._center_text(pile_line))

        # Frozen indicator
        if view.pile_frozen:
            output.append("\n")
            frozen_text = Text("*FROZEN*", style=STYLE_FROZEN)
            output.append_text(self._center_text(frozen_text))

    def _render_bottom_player(self, view: StateView, output: Text) -> None:
        """Render the bottom player (Player 0 - perspective player).

        Args:
            view: StateView to render
            output: Text object to append to
        """
        player = 0

        # Player label
        label = self._get_player_label_styled(player, view)
        output.append_text(self._center_text(label))
        output.append("\n")

        # Hand display (always visible for perspective player)
        hand_display = self._format_player_hand_styled(player, view)
        output.append_text(self._center_text(hand_display))

    def _render_footer(self, view: StateView, output: Text) -> None:
        """Render footer with scores and status.

        Args:
            view: StateView to render
            output: Text object to append to
        """
        separator = Text("-" * MAX_WIDTH, style=STYLE_FOOTER)
        output.append_text(separator)
        output.append("\n")

        # Red threes
        rt_line = self._format_red_threes_styled(view)
        if rt_line.plain:
            output.append_text(self._center_text(rt_line))
            output.append("\n")

        # Scores
        score_line = Text()
        score_line.append("SCORES: ", style=STYLE_PRIMARY)
        score_line.append(f"Team 0: {view.team_scores[0]} | Team 1: {view.team_scores[1]}")
        output.append_text(self._center_text(score_line))
        output.append("\n")

        # Hand scores if non-zero
        if view.hand_scores[0] != 0 or view.hand_scores[1] != 0:
            hand_score_line = Text(
                f"(Hand: Team 0: {view.hand_scores[0]} | Team 1: {view.hand_scores[1]})",
                style=STYLE_FOOTER,
            )
            output.append_text(self._center_text(hand_score_line))
            output.append("\n")

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

        status_line = Text(" | ".join(status_parts))
        output.append_text(self._center_text(status_line))
        output.append("\n")

        # Canastas
        canasta_line = Text()
        canasta_line.append("Canastas: ", style=STYLE_PRIMARY)
        canasta_line.append(f"Team 0: {view.canastas[0]} | Team 1: {view.canastas[1]}")
        output.append_text(self._center_text(canasta_line))
        output.append("\n")

        output.append_text(separator)

    def _get_player_label_styled(self, player: int, view: StateView) -> Text:
        """Get styled label for a player position.

        Args:
            player: Player index (0-3)
            view: StateView for context

        Returns:
            Styled Text label
        """
        team = view.team_of(player)

        if player == self.perspective:
            role = "(You)"
        elif player == view.partner_of(self.perspective):
            role = "(Partner)"
        else:
            role = f"(Team {team})"

        # Build styled text
        result = Text()

        if view.current_player == player:
            result.append(f"PLAYER {player} {role} *", style=STYLE_CURRENT_PLAYER)
        else:
            result.append(f"PLAYER {player} ", style=STYLE_PRIMARY)
            result.append(role)

        return result

    def _format_player_hand_styled(self, player: int, view: StateView) -> Text:
        """Format a player's hand with styling.

        Args:
            player: Player index (0-3)
            view: StateView containing hands

        Returns:
            Styled Text object for hand display
        """
        hand = view.hands[player]
        card_count = len(hand)

        if card_count == 0:
            return Text("(no cards)", style=STYLE_FOOTER)

        # Show visible hands, hide others
        if self.is_visible_hand(player):
            # Show actual cards with styling
            result = self._format_cards_styled(hand)
            # Check if too long and truncate
            if len(result.plain) > 70:
                result = Text()
                for card_id in sorted(hand)[:10]:
                    result.append_text(self._card_styled(card_id))
                result.append("...", style=STYLE_FOOTER)
            return result
        else:
            # Show count only
            return Text(format_hand_summary(card_count), style=STYLE_FOOTER)

    def _format_melds_box_styled(self, team: int, view: StateView) -> list[Text]:
        """Format a styled meld display box for a team.

        Args:
            team: Team index (0 or 1)
            view: StateView containing melds

        Returns:
            List of Text lines for meld box
        """
        lines = []
        team_melds = view.melds[team]

        # Box top
        box_title = f"[ Team {team} Melds ]"
        dashes = "-" * ((MELD_BOX_WIDTH - len(box_title)) // 2)

        box_top = Text()
        box_top.append(dashes, style=STYLE_PRIMARY)
        box_top.append(box_title, style=STYLE_PRIMARY)
        box_top.append(dashes, style=STYLE_PRIMARY)
        lines.append(box_top)

        if not team_melds:
            lines.append(Text("(no melds)".center(MELD_BOX_WIDTH), style=STYLE_FOOTER))
        else:
            for meld in team_melds:
                meld_line = self._format_meld_styled(meld)
                lines.append(meld_line)

        # Box bottom
        lines.append(Text("-" * MELD_BOX_WIDTH, style=STYLE_PRIMARY))

        return lines

    def _format_meld_styled(self, meld: MeldView) -> Text:
        """Format a single meld with styling.

        Args:
            meld: MeldView to format

        Returns:
            Styled Text object for meld line
        """
        result = Text()
        rank_name = rank_display_name(meld.rank)

        result.append(f"  {rank_name} ({meld.total_cards}): ")

        # Show a few cards as preview with styling
        all_cards = meld.natural_cards + meld.wild_cards
        cards_to_show = all_cards[:4] if len(all_cards) > 4 else all_cards

        for card_id in cards_to_show:
            result.append_text(self._card_styled(card_id))

        if len(all_cards) > 4:
            result.append("...", style=STYLE_FOOTER)

        # Canasta marker with special styling
        if meld.is_natural_canasta:
            result.append(" [NATURAL]", style=STYLE_NATURAL_CANASTA)
        elif meld.is_mixed_canasta:
            result.append(" [MIXED]", style=STYLE_MIXED_CANASTA)

        return result

    def _format_red_threes_styled(self, view: StateView) -> Text:
        """Format red threes display with styling.

        Args:
            view: StateView containing red threes

        Returns:
            Styled Text object for red threes line
        """
        result = Text()
        parts = []

        for team in range(2):
            rt_cards = view.red_threes[team]
            if rt_cards:
                part = Text()
                part.append(f"Team {team}: ")
                for card_id in rt_cards:
                    part.append_text(self._card_styled(card_id))
                parts.append(part)

        if parts:
            result.append("Red Threes: ", style=STYLE_PRIMARY)
            result.append_text(parts[0])
            if len(parts) > 1:
                result.append(" | ")
                result.append_text(parts[1])

        return result
