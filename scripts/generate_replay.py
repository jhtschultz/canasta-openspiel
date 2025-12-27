#!/usr/bin/env python3
"""Generate an interactive HTML replay of a full Canasta game.

Creates a single HTML file with all game states embedded and JavaScript
navigation for stepping forward/backward through the game.

Usage:
    python scripts/generate_replay.py
    python scripts/generate_replay.py --seed 42
    python scripts/generate_replay.py --output replay.html
"""

import argparse
import json
import random
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

import pyspiel
import canasta.canasta_game  # Register the game
from canasta.ui.state_view import extract_state_view
from canasta.ui.cards import rank_display_name
from canasta.cards import card_id_to_rank_suit, is_joker


# Canasta Junction color palette
COLORS = {
    "primary": "#008373",
    "background": "#F5F5F5",
    "card_bg": "#FFFFFF",
    "red": "#E53935",
    "black": "#212121",
    "joker": "#7B1FA2",
    "natural_canasta": "#FFD700",
    "mixed_canasta": "#C0C0C0",
    "border": "#CCCCCC",
    "text": "#333333",
}

SUIT_SYMBOLS = {
    "spades": "\u2660",
    "hearts": "\u2665",
    "diamonds": "\u2666",
    "clubs": "\u2663",
}


def card_to_html(card_id: int) -> str:
    """Convert card ID to HTML span element."""
    rank, suit = card_id_to_rank_suit(card_id)

    if suit is None:
        return '<span class="card joker">JKR</span>'

    suit_symbol = SUIT_SYMBOLS[suit]
    if is_joker(card_id):
        color_class = "joker"
    elif suit in ("hearts", "diamonds"):
        color_class = "red"
    else:
        color_class = "black"

    return f'<span class="card {color_class}">{rank}{suit_symbol}</span>'


def render_state_html(view, move_num: int, action_str: str = "") -> str:
    """Render a single game state to HTML fragment."""

    def render_hand(player: int) -> str:
        hand = view.hands[player]
        if not hand:
            return '<span class="hand-count">(no cards)</span>'
        cards_html = "".join(card_to_html(c) for c in sorted(hand))
        return cards_html

    def render_melds(team: int) -> str:
        team_melds = view.melds[team]
        if not team_melds:
            return '<div class="empty-melds">(no melds)</div>'

        melds_html = ""
        for meld in team_melds:
            rank_name = rank_display_name(meld.rank)

            if meld.is_natural_canasta:
                marker = '<span class="meld-marker">NATURAL</span>'
                meld_class = "meld natural-canasta"
            elif meld.is_mixed_canasta:
                marker = '<span class="meld-marker">MIXED</span>'
                meld_class = "meld mixed-canasta"
            else:
                marker = ""
                meld_class = "meld"

            all_cards = meld.natural_cards + meld.wild_cards
            cards_html = "".join(card_to_html(c) for c in all_cards)

            melds_html += f'''
            <div class="{meld_class}">
                <span class="meld-rank">{rank_name} ({meld.total_cards}):</span>
                {cards_html}
                {marker}
            </div>'''

        return melds_html

    def render_red_threes() -> str:
        parts = []
        for team in range(2):
            rt_cards = view.red_threes[team]
            if rt_cards:
                cards_html = "".join(card_to_html(c) for c in rt_cards)
                parts.append(f"Team {team}: {cards_html}")
        if parts:
            return f'<div class="red-threes">Red Threes: {" | ".join(parts)}</div>'
        return ""

    # Header
    if view.is_terminal:
        if view.winning_team >= 0:
            title = f"Game Over - Team {view.winning_team} Wins!"
        else:
            title = "Game Over"
        subtitle = ""
    else:
        title = "Canasta"
        subtitle = f"Hand {view.hand_number + 1}"

    # Current player marker
    def player_label(p: int) -> str:
        current_class = "current" if view.current_player == p else ""
        current_marker = " *" if view.current_player == p else ""
        return f'<div class="player-label {current_class}">Player {p}{current_marker}</div>'

    # Discard pile
    if view.discard_top is not None:
        discard_html = card_to_html(view.discard_top)
        if len(view.discard_pile) > 1:
            discard_html += f' <span class="hand-count">(+{len(view.discard_pile) - 1})</span>'
    else:
        discard_html = '<span class="hand-count">(empty)</span>'

    frozen_html = '<div class="frozen">*FROZEN*</div>' if view.pile_frozen else ''

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

    # Action display
    action_html = f'<div class="action-display">Move {move_num}: {action_str}</div>' if action_str else f'<div class="action-display">Move {move_num}: Initial State</div>'

    return f'''
    <div class="header">
        <h1>{title}</h1>
        {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
        {action_html}
    </div>

    <div class="player-area">
        {player_label(2)}
        <div class="hand">{render_hand(2)}</div>
    </div>

    <div class="meld-area">
        <h3>Team 1 Melds</h3>
        {render_melds(1)}
    </div>

    <div class="middle-section">
        <div class="side-player">
            <div class="player-area">
                {player_label(1)}
                <div class="hand">{render_hand(1)}</div>
            </div>
        </div>

        <div class="center-area">
            <div class="piles">
                <div class="pile-container">
                    <div class="pile-label">Stock</div>
                    <div class="pile-cards"><span class="hand-count">({view.stock_count})</span></div>
                </div>
                <div class="pile-container">
                    <div class="pile-label">Discard</div>
                    <div class="pile-cards">{discard_html}</div>
                </div>
                {frozen_html}
            </div>
        </div>

        <div class="side-player">
            <div class="player-area">
                {player_label(3)}
                <div class="hand">{render_hand(3)}</div>
            </div>
        </div>
    </div>

    <div class="meld-area">
        <h3>Team 0 Melds</h3>
        {render_melds(0)}
    </div>

    <div class="player-area">
        {player_label(0)}
        <div class="hand">{render_hand(0)}</div>
    </div>

    <div class="footer">
        {render_red_threes()}

        <div class="scores">
            <div class="score-box">
                <div class="team">Team 0</div>
                <div class="value">{view.team_scores[0]}</div>
            </div>
            <div class="score-box">
                <div class="team">Team 1</div>
                <div class="value">{view.team_scores[1]}</div>
            </div>
        </div>

        <div class="game-status">
            <span class="status-item">{status}</span>
        </div>

        <div class="canasta-count">
            <span>Team 0 Canastas: {view.canastas[0]}</span>
            <span>Team 1 Canastas: {view.canastas[1]}</span>
        </div>
    </div>
    '''


def generate_replay_html(states: list, seed: int) -> str:
    """Generate complete HTML document with all states and navigation."""

    # Escape states for JavaScript embedding
    states_json = json.dumps(states)

    css = f'''
    * {{ box-sizing: border-box; }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background: {COLORS["background"]};
        margin: 0;
        padding: 20px;
        color: {COLORS["text"]};
    }}
    .replay-container {{
        max-width: 900px;
        margin: 0 auto;
    }}
    .controls {{
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        padding: 20px;
        background: white;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        position: sticky;
        top: 10px;
        z-index: 100;
    }}
    .controls button {{
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        background: {COLORS["primary"]};
        color: white;
        transition: background 0.2s;
    }}
    .controls button:hover {{
        background: #006b5f;
    }}
    .controls button:disabled {{
        background: #ccc;
        cursor: not-allowed;
    }}
    .controls .position {{
        font-size: 18px;
        font-weight: bold;
        min-width: 120px;
        text-align: center;
    }}
    .controls input[type="range"] {{
        width: 200px;
        cursor: pointer;
    }}
    .game-table {{
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .header {{
        text-align: center;
        padding: 20px;
        background: {COLORS["primary"]};
        color: white;
        border-radius: 8px;
        margin-bottom: 20px;
    }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .header .subtitle {{ margin-top: 8px; opacity: 0.9; }}
    .action-display {{
        margin-top: 10px;
        padding: 8px 16px;
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
        font-size: 14px;
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
    .card.red {{ color: {COLORS["red"]}; }}
    .card.black {{ color: {COLORS["black"]}; }}
    .card.joker {{ color: {COLORS["joker"]}; }}
    .player-area {{
        text-align: center;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background: {COLORS["background"]};
    }}
    .player-label {{
        font-weight: bold;
        margin-bottom: 8px;
        color: {COLORS["primary"]};
    }}
    .player-label.current {{ color: {COLORS["red"]}; }}
    .hand {{ min-height: 30px; }}
    .hand-count {{ color: #666; font-style: italic; }}
    .middle-section {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 15px 0;
    }}
    .side-player {{ flex: 1; min-width: 150px; }}
    .center-area {{ flex: 2; min-width: 200px; }}
    .piles {{
        text-align: center;
        padding: 20px;
        background: {COLORS["background"]};
        border-radius: 8px;
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
    .frozen {{ color: {COLORS["red"]}; font-weight: bold; margin-top: 8px; }}
    .meld-area {{
        border: 2px solid {COLORS["primary"]};
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        background: {COLORS["background"]};
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
        background: white;
    }}
    .meld.natural-canasta {{ background: {COLORS["natural_canasta"]}; }}
    .meld.mixed-canasta {{ background: {COLORS["mixed_canasta"]}; }}
    .meld-rank {{ font-weight: bold; margin-right: 10px; }}
    .meld-marker {{
        font-size: 12px;
        padding: 2px 6px;
        border-radius: 3px;
        background: rgba(0,0,0,0.1);
        margin-left: 8px;
    }}
    .empty-melds {{ color: #999; font-style: italic; }}
    .footer {{
        background: {COLORS["background"]};
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
    }}
    .scores {{
        display: flex;
        justify-content: space-around;
        margin-bottom: 15px;
    }}
    .score-box {{
        text-align: center;
        padding: 10px 20px;
        background: white;
        border-radius: 8px;
    }}
    .score-box .team {{ font-weight: bold; color: {COLORS["primary"]}; }}
    .score-box .value {{ font-size: 24px; font-weight: bold; }}
    .game-status {{ text-align: center; padding: 10px; color: #666; }}
    .red-threes {{ text-align: center; padding: 10px; color: {COLORS["red"]}; }}
    .canasta-count {{ text-align: center; padding: 10px; font-size: 14px; }}
    .canasta-count span {{ margin: 0 15px; }}
    .keyboard-hint {{
        text-align: center;
        padding: 10px;
        color: #999;
        font-size: 12px;
    }}
    '''

    javascript = '''
    const states = ''' + states_json + ''';
    let currentIndex = 0;

    function updateDisplay() {
        document.getElementById('game-state').innerHTML = states[currentIndex];
        document.getElementById('position').textContent = `${currentIndex + 1} / ${states.length}`;
        document.getElementById('slider').value = currentIndex;
        document.getElementById('prev').disabled = currentIndex === 0;
        document.getElementById('next').disabled = currentIndex === states.length - 1;
    }

    function prev() {
        if (currentIndex > 0) {
            currentIndex--;
            updateDisplay();
        }
    }

    function next() {
        if (currentIndex < states.length - 1) {
            currentIndex++;
            updateDisplay();
        }
    }

    function first() {
        currentIndex = 0;
        updateDisplay();
    }

    function last() {
        currentIndex = states.length - 1;
        updateDisplay();
    }

    function onSlider(value) {
        currentIndex = parseInt(value);
        updateDisplay();
    }

    // Keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft' || e.key === 'a') prev();
        else if (e.key === 'ArrowRight' || e.key === 'd') next();
        else if (e.key === 'Home') first();
        else if (e.key === 'End') last();
    });

    // Initialize
    updateDisplay();
    '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Canasta Game Replay (Seed: {seed})</title>
    <style>{css}</style>
</head>
<body>
    <div class="replay-container">
        <div class="controls">
            <button id="first" onclick="first()">|&lt;</button>
            <button id="prev" onclick="prev()">&lt; Prev</button>
            <span class="position" id="position">1 / {len(states)}</span>
            <button id="next" onclick="next()">Next &gt;</button>
            <button id="last" onclick="last()">&gt;|</button>
        </div>
        <div class="controls">
            <input type="range" id="slider" min="0" max="{len(states) - 1}" value="0"
                   oninput="onSlider(this.value)" style="width: 100%;">
        </div>
        <div class="keyboard-hint">
            Keyboard: Arrow keys or A/D to navigate | Home/End for first/last
        </div>
        <div class="game-table" id="game-state"></div>
    </div>
    <script>{javascript}</script>
</body>
</html>'''


def play_game(seed: int, max_steps: int = 500) -> list:
    """Play a full game and capture all states."""
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    rng = random.Random(seed)
    states = []
    move_num = 0
    step = 0
    dealing_complete = False

    # Skip through dealing phase first
    print("  Dealing cards...")
    while state.is_chance_node() and not state.is_terminal():
        outcomes = state.chance_outcomes()
        if not outcomes:
            break
        actions, probs = zip(*outcomes)
        action = rng.choices(actions, weights=probs)[0]
        state.apply_action(action)

    # Capture state after dealing
    view = extract_state_view(state)
    states.append(render_state_html(view, move_num, "Initial deal"))
    print("  Playing game...")

    while not state.is_terminal() and step < max_steps:
        step += 1

        # Handle chance nodes (shouldn't happen after dealing, but just in case)
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            if not outcomes:
                break
            actions, probs = zip(*outcomes)
            action = rng.choices(actions, weights=probs)[0]
            state.apply_action(action)
            continue

        # Get legal actions for the current player
        legal_actions = state.legal_actions()
        if not legal_actions:
            break

        action = rng.choice(legal_actions)
        player = state.current_player()
        action_str = f"P{player}: {state.action_to_string(action)}"

        state.apply_action(action)
        move_num += 1

        # Handle any resulting chance nodes (like drawing cards)
        while state.is_chance_node() and not state.is_terminal():
            outcomes = state.chance_outcomes()
            if not outcomes:
                break
            actions, probs = zip(*outcomes)
            chance_action = rng.choices(actions, weights=probs)[0]
            state.apply_action(chance_action)

        # Capture state after action and any resulting chance events
        if not state.is_terminal():
            view = extract_state_view(state)
            states.append(render_state_html(view, move_num, action_str))

    # Capture terminal state
    if state.is_terminal():
        view = extract_state_view(state)
        states.append(render_state_html(view, move_num + 1, "Game Over"))

    return states


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Canasta game replay HTML")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for game")
    parser.add_argument("--output", type=str, default="replay.html", help="Output filename")
    return parser.parse_args()


def main():
    args = parse_args()

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    print(f"Generating game replay with seed: {seed}")

    states = play_game(seed)
    print(f"Game completed: {len(states)} states captured")

    html = generate_replay_html(states, seed)

    output_path = project_root / "renders" / args.output
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Replay saved to: {output_path}")
    print(f"File size: {len(html) / 1024:.1f} KB")

    return output_path


if __name__ == "__main__":
    main()
