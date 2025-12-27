"""HTML renderer for Canasta game states.

Generates standalone HTML files with CSS-styled cards using
Canasta Junction aesthetic colors:
- Primary: Teal (#008373)
- Background: Light gray (#F5F5F5)
- Cards: White with colored text/borders
- Hearts/Diamonds: Red (#E53935)
- Clubs/Spades: Black (#212121)
- Jokers: Purple (#7B1FA2)
"""

from typing import TYPE_CHECKING

from canasta.ui.base import Renderer
from canasta.ui.cards import rank_display_name
from canasta.ui.state_view import StateView, extract_state_view, MeldView
from canasta.cards import card_id_to_rank_suit, is_joker

if TYPE_CHECKING:
    from canasta.canasta_game import CanastaState


# Canasta Junction color palette
COLORS = {
    "primary": "#008373",       # Teal
    "background": "#F5F5F5",    # Light gray
    "card_bg": "#FFFFFF",       # White
    "red": "#E53935",           # Hearts/Diamonds
    "black": "#212121",         # Clubs/Spades
    "joker": "#7B1FA2",         # Purple
    "natural_canasta": "#FFD700",  # Gold
    "mixed_canasta": "#C0C0C0",    # Silver
    "border": "#CCCCCC",
    "text": "#333333",
}

# Unicode suit symbols
SUIT_SYMBOLS = {
    "spades": "\u2660",
    "hearts": "\u2665",
    "diamonds": "\u2666",
    "clubs": "\u2663",
}


def _card_color_class(card_id: int) -> str:
    """Get CSS class for a card's color.

    Args:
        card_id: Card ID (0-107)

    Returns:
        CSS class name: 'red', 'black', or 'joker'
    """
    if is_joker(card_id):
        return "joker"

    _, suit = card_id_to_rank_suit(card_id)
    if suit in ("hearts", "diamonds"):
        return "red"
    return "black"


def _card_to_html(card_id: int) -> str:
    """Convert card ID to HTML span element.

    Args:
        card_id: Card ID (0-107)

    Returns:
        HTML span element like '<span class="card red">A&hearts;</span>'
    """
    rank, suit = card_id_to_rank_suit(card_id)

    if suit is None:
        # Joker
        return '<span class="card joker">JKR</span>'

    suit_symbol = SUIT_SYMBOLS[suit]
    color_class = _card_color_class(card_id)

    return f'<span class="card {color_class}">{rank}{suit_symbol}</span>'


def _card_back_html() -> str:
    """Return HTML for a hidden card back.

    Returns:
        HTML span element representing face-down card
    """
    return '<span class="card back">###</span>'


class HTMLRenderer(Renderer):
    """HTML renderer for Canasta game states.

    Generates standalone HTML files with CSS-styled cards that match
    the Canasta Junction aesthetic. No external dependencies are
    required to view the output.
    """

    def render(self, state: "CanastaState") -> str:
        """Render game state to standalone HTML.

        Args:
            state: CanastaState object to render

        Returns:
            Complete HTML document as a string
        """
        view = extract_state_view(state)
        return self._generate_html(view)

    def _generate_html(self, view: StateView) -> str:
        """Generate complete HTML document.

        Args:
            view: StateView to render

        Returns:
            Complete HTML document string
        """
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Canasta Game State</title>
    <style>
{self._css()}
    </style>
</head>
<body>
    <div class="game-table">
        {self._render_header(view)}
        {self._render_top_player(view)}
        {self._render_middle_section(view)}
        {self._render_bottom_player(view)}
        {self._render_footer(view)}
    </div>
</body>
</html>'''

    def _css(self) -> str:
        """Generate CSS styles.

        Returns:
            CSS stylesheet as string
        """
        return f'''
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: {COLORS["background"]};
            margin: 0;
            padding: 20px;
            color: {COLORS["text"]};
        }}
        .game-table {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            background: {COLORS["primary"]};
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header .subtitle {{
            margin-top: 8px;
            opacity: 0.9;
        }}
        .card {{
            display: inline-block;
            padding: 4px 8px;
            margin: 2px;
            border: 1px solid {COLORS["border"]};
            border-radius: 4px;
            background: {COLORS["card_bg"]};
            font-weight: bold;
            font-size: 14px;
        }}
        .card.red {{
            color: {COLORS["red"]};
        }}
        .card.black {{
            color: {COLORS["black"]};
        }}
        .card.joker {{
            color: {COLORS["joker"]};
        }}
        .card.back {{
            color: {COLORS["border"]};
            background: #EEE;
        }}
        .player-area {{
            text-align: center;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .player-label {{
            font-weight: bold;
            margin-bottom: 8px;
            color: {COLORS["primary"]};
        }}
        .player-label.current {{
            color: {COLORS["red"]};
        }}
        .player-label .tag {{
            font-weight: normal;
            opacity: 0.8;
        }}
        .hand {{
            min-height: 30px;
        }}
        .hand-count {{
            color: #666;
            font-style: italic;
        }}
        .middle-section {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
        }}
        .side-player {{
            flex: 1;
            min-width: 150px;
        }}
        .center-area {{
            flex: 2;
            min-width: 200px;
        }}
        .piles {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .pile-container {{
            display: inline-block;
            margin: 0 20px;
            text-align: center;
        }}
        .pile-label {{
            font-weight: bold;
            margin-bottom: 8px;
            color: {COLORS["primary"]};
        }}
        .pile-cards {{
            min-height: 30px;
        }}
        .frozen {{
            color: {COLORS["red"]};
            font-weight: bold;
            margin-top: 8px;
        }}
        .meld-area {{
            border: 2px solid {COLORS["primary"]};
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            background: white;
        }}
        .meld-area h3 {{
            margin: 0 0 10px 0;
            color: {COLORS["primary"]};
            font-size: 16px;
        }}
        .meld {{
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
            background: {COLORS["background"]};
        }}
        .meld.natural-canasta {{
            background: {COLORS["natural_canasta"]};
        }}
        .meld.mixed-canasta {{
            background: {COLORS["mixed_canasta"]};
        }}
        .meld-rank {{
            font-weight: bold;
            margin-right: 10px;
        }}
        .meld-marker {{
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 3px;
            background: rgba(0,0,0,0.1);
            margin-left: 8px;
        }}
        .empty-melds {{
            color: #999;
            font-style: italic;
        }}
        .footer {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .scores {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 15px;
        }}
        .score-box {{
            text-align: center;
            padding: 10px 20px;
            background: {COLORS["background"]};
            border-radius: 8px;
        }}
        .score-box .team {{
            font-weight: bold;
            color: {COLORS["primary"]};
        }}
        .score-box .value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .score-box .hand-score {{
            font-size: 12px;
            color: #666;
        }}
        .game-status {{
            text-align: center;
            padding: 10px;
            color: #666;
        }}
        .game-status .status-item {{
            display: inline-block;
            margin: 0 10px;
        }}
        .red-threes {{
            text-align: center;
            padding: 10px;
            color: {COLORS["red"]};
        }}
        .canasta-count {{
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }}
        .canasta-count span {{
            margin: 0 15px;
        }}
        '''

    def _render_header(self, view: StateView) -> str:
        """Render header section.

        Args:
            view: StateView to render

        Returns:
            HTML for header
        """
        if view.is_terminal:
            if view.winning_team >= 0:
                title = f"Game Over - Team {view.winning_team} Wins!"
            else:
                title = "Game Over"
            subtitle = ""
        else:
            title = "Canasta"
            subtitle = f"Hand {view.hand_number + 1}"

        return f'''
        <div class="header">
            <h1>{title}</h1>
            {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
        </div>'''

    def _render_player_label(self, player: int, view: StateView) -> str:
        """Render a player label.

        Args:
            player: Player index (0-3)
            view: StateView for context

        Returns:
            HTML for player label
        """
        team = view.team_of(player)

        if player == self.perspective:
            tag = "(You)"
        elif player == view.partner_of(self.perspective):
            tag = "(Partner)"
        else:
            tag = f"(Team {team})"

        current_class = "current" if view.current_player == player else ""
        current_marker = " *" if view.current_player == player else ""

        return f'<div class="player-label {current_class}">Player {player} <span class="tag">{tag}</span>{current_marker}</div>'

    def _render_hand(self, player: int, view: StateView) -> str:
        """Render a player's hand.

        Args:
            player: Player index (0-3)
            view: StateView containing hands

        Returns:
            HTML for hand display
        """
        hand = view.hands[player]
        card_count = len(hand)

        if card_count == 0:
            return '<div class="hand"><span class="hand-count">(no cards)</span></div>'

        if self.is_visible_hand(player):
            # Show actual cards
            cards_html = "".join(_card_to_html(c) for c in sorted(hand))
            return f'<div class="hand">{cards_html}</div>'
        else:
            # Show count only
            card_word = "card" if card_count == 1 else "cards"
            return f'<div class="hand"><span class="hand-count">[{card_count} {card_word}]</span></div>'

    def _render_top_player(self, view: StateView) -> str:
        """Render top player area (Player 2 - partner).

        Args:
            view: StateView to render

        Returns:
            HTML for top player area
        """
        player = 2
        return f'''
        <div class="player-area">
            {self._render_player_label(player, view)}
            {self._render_hand(player, view)}
        </div>'''

    def _render_bottom_player(self, view: StateView) -> str:
        """Render bottom player area (Player 0 - perspective).

        Args:
            view: StateView to render

        Returns:
            HTML for bottom player area
        """
        player = 0
        return f'''
        <div class="player-area">
            {self._render_player_label(player, view)}
            {self._render_hand(player, view)}
        </div>'''

    def _render_middle_section(self, view: StateView) -> str:
        """Render middle section with side players, piles, and melds.

        Args:
            view: StateView to render

        Returns:
            HTML for middle section
        """
        return f'''
        <div class="meld-area">
            <h3>Team 1 Melds</h3>
            {self._render_melds(1, view)}
        </div>

        <div class="middle-section">
            <div class="side-player">
                <div class="player-area">
                    {self._render_player_label(1, view)}
                    {self._render_hand(1, view)}
                </div>
            </div>

            <div class="center-area">
                {self._render_piles(view)}
            </div>

            <div class="side-player">
                <div class="player-area">
                    {self._render_player_label(3, view)}
                    {self._render_hand(3, view)}
                </div>
            </div>
        </div>

        <div class="meld-area">
            <h3>Team 0 Melds</h3>
            {self._render_melds(0, view)}
        </div>'''

    def _render_piles(self, view: StateView) -> str:
        """Render stock and discard piles.

        Args:
            view: StateView to render

        Returns:
            HTML for piles
        """
        # Stock
        stock_html = f'<span class="hand-count">({view.stock_count})</span>'

        # Discard
        if view.discard_top is not None:
            discard_html = _card_to_html(view.discard_top)
            if len(view.discard_pile) > 1:
                discard_html += f' <span class="hand-count">(+{len(view.discard_pile) - 1})</span>'
        else:
            discard_html = '<span class="hand-count">(empty)</span>'

        frozen_html = '<div class="frozen">*FROZEN*</div>' if view.pile_frozen else ''

        return f'''
        <div class="piles">
            <div class="pile-container">
                <div class="pile-label">Stock</div>
                <div class="pile-cards">{stock_html}</div>
            </div>
            <div class="pile-container">
                <div class="pile-label">Discard</div>
                <div class="pile-cards">{discard_html}</div>
            </div>
            {frozen_html}
        </div>'''

    def _render_melds(self, team: int, view: StateView) -> str:
        """Render melds for a team.

        Args:
            team: Team index (0 or 1)
            view: StateView containing melds

        Returns:
            HTML for melds
        """
        team_melds = view.melds[team]

        if not team_melds:
            return '<div class="empty-melds">(no melds)</div>'

        melds_html = ""
        for meld in team_melds:
            melds_html += self._render_meld(meld)

        return melds_html

    def _render_meld(self, meld: MeldView) -> str:
        """Render a single meld.

        Args:
            meld: MeldView to render

        Returns:
            HTML for meld
        """
        rank_name = rank_display_name(meld.rank)

        # Canasta marker and class
        if meld.is_natural_canasta:
            marker = '<span class="meld-marker">NATURAL</span>'
            meld_class = "meld natural-canasta"
        elif meld.is_mixed_canasta:
            marker = '<span class="meld-marker">MIXED</span>'
            meld_class = "meld mixed-canasta"
        else:
            marker = ""
            meld_class = "meld"

        # Cards
        all_cards = meld.natural_cards + meld.wild_cards
        cards_html = "".join(_card_to_html(c) for c in all_cards)

        return f'''
        <div class="{meld_class}">
            <span class="meld-rank">{rank_name} ({meld.total_cards}):</span>
            {cards_html}
            {marker}
        </div>'''

    def _render_footer(self, view: StateView) -> str:
        """Render footer with scores and status.

        Args:
            view: StateView to render

        Returns:
            HTML for footer
        """
        # Red threes
        red_threes_html = self._render_red_threes(view)

        # Scores
        hand_score_0 = f'<div class="hand-score">Hand: {view.hand_scores[0]}</div>' if view.hand_scores[0] != 0 else ''
        hand_score_1 = f'<div class="hand-score">Hand: {view.hand_scores[1]}</div>' if view.hand_scores[1] != 0 else ''

        # Status
        if view.is_terminal:
            status = "Game: TERMINAL"
        else:
            status_parts = []
            if view.current_player >= 0:
                status_parts.append(f"Turn: Player {view.current_player}")
            status_parts.append(f"Phase: {view.turn_phase.upper()}")
            if view.pile_frozen:
                status_parts.append("Pile: FROZEN")
            status = " | ".join(status_parts)

        return f'''
        <div class="footer">
            {red_threes_html}

            <div class="scores">
                <div class="score-box">
                    <div class="team">Team 0</div>
                    <div class="value">{view.team_scores[0]}</div>
                    {hand_score_0}
                </div>
                <div class="score-box">
                    <div class="team">Team 1</div>
                    <div class="value">{view.team_scores[1]}</div>
                    {hand_score_1}
                </div>
            </div>

            <div class="game-status">
                <span class="status-item">{status}</span>
            </div>

            <div class="canasta-count">
                <span>Team 0 Canastas: {view.canastas[0]}</span>
                <span>Team 1 Canastas: {view.canastas[1]}</span>
            </div>
        </div>'''

    def _render_red_threes(self, view: StateView) -> str:
        """Render red threes section.

        Args:
            view: StateView containing red threes

        Returns:
            HTML for red threes, or empty string if none
        """
        parts = []

        for team in range(2):
            rt_cards = view.red_threes[team]
            if rt_cards:
                cards_html = "".join(_card_to_html(c) for c in rt_cards)
                parts.append(f"Team {team}: {cards_html}")

        if parts:
            return f'<div class="red-threes">Red Threes: {" | ".join(parts)}</div>'
        return ""
