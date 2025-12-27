#!/usr/bin/env python3
"""Preview render script for Canasta UI fixtures.

This script creates all fixture states and renders them using the TextRenderer,
RichRenderer, or HTMLRenderer, saving the results to the renders/ directory
for visual verification.

Usage:
    python scripts/preview_render.py
    python scripts/preview_render.py --format text
    python scripts/preview_render.py --format rich
    python scripts/preview_render.py --format html
    python scripts/preview_render.py --format html --open
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from canasta.ui.fixtures import get_all_fixtures
from canasta.ui.text_renderer import TextRenderer
from canasta.cards import card_id_to_rank_suit, is_wild, is_red_three
from canasta.melds import is_canasta, is_natural_canasta, is_mixed_canasta


def format_card(card_id: int) -> str:
    """Format a card ID as a human-readable string.

    Args:
        card_id: Card ID (0-107)

    Returns:
        Formatted card string like "A of clubs" or "JOKER"
    """
    rank, suit = card_id_to_rank_suit(card_id)
    if suit:
        return f"{rank} of {suit}"
    return rank


def format_hand(hand: list[int]) -> list[str]:
    """Format a hand of cards as human-readable strings.

    Args:
        hand: List of card IDs

    Returns:
        List of formatted card strings
    """
    return [format_card(c) for c in hand]


def format_meld(meld) -> dict:
    """Format a meld as a dictionary for display.

    Args:
        meld: Meld object

    Returns:
        Dictionary with meld information
    """
    from canasta.cards import RANKS
    return {
        "rank": RANKS[meld.rank],
        "natural_cards": format_hand(meld.natural_cards),
        "wild_cards": format_hand(meld.wild_cards),
        "total_cards": len(meld.natural_cards) + len(meld.wild_cards),
        "is_canasta": is_canasta(meld),
        "is_natural_canasta": is_natural_canasta(meld),
        "is_mixed_canasta": is_mixed_canasta(meld),
    }


def describe_state(name: str, state) -> dict:
    """Create a description dictionary for a game state.

    Args:
        name: Name of the fixture
        state: CanastaState object

    Returns:
        Dictionary with state description
    """
    description = {
        "fixture_name": name,
        "game_phase": state._game_phase,
        "turn_phase": state._turn_phase if hasattr(state, '_turn_phase') else "N/A",
        "current_player": state.current_player() if not state.is_terminal() else "TERMINAL",
        "is_terminal": state.is_terminal(),
        "pile_frozen": getattr(state, '_pile_frozen', False),
        "hands": {},
        "melds": {},
        "red_threes": {},
        "discard_pile": {
            "count": len(state._discard_pile),
            "top_card": format_card(state._discard_pile[-1]) if state._discard_pile else None,
            "cards": format_hand(state._discard_pile),
        },
        "stock_count": len(state._stock),
        "canastas": {
            "team_0": state._canastas[0],
            "team_1": state._canastas[1],
        },
        "initial_meld_made": {
            "team_0": state._initial_meld_made[0],
            "team_1": state._initial_meld_made[1],
        },
        "team_scores": {
            "team_0": state._team_scores[0],
            "team_1": state._team_scores[1],
        },
    }

    # Format hands
    for player_idx in range(4):
        hand = state._hands[player_idx]
        team = player_idx % 2
        description["hands"][f"player_{player_idx}"] = {
            "team": team,
            "card_count": len(hand),
            "cards": format_hand(hand),
            "wild_count": sum(1 for c in hand if is_wild(c)),
        }

    # Format melds
    for team_idx in range(2):
        team_melds = state._melds[team_idx]
        description["melds"][f"team_{team_idx}"] = [
            format_meld(meld) for meld in team_melds
        ]

    # Format red threes
    for team_idx in range(2):
        team_red_threes = state._red_threes[team_idx]
        description["red_threes"][f"team_{team_idx}"] = {
            "count": len(team_red_threes),
            "cards": format_hand(team_red_threes),
        }

    return description


def print_state_summary(name: str, description: dict) -> None:
    """Print a summary of a game state to console.

    Args:
        name: Name of the fixture
        description: State description dictionary
    """
    print(f"\n{'='*60}")
    print(f"FIXTURE: {name}")
    print(f"{'='*60}")

    print(f"\nPhase: {description['game_phase']} / {description['turn_phase']}")
    print(f"Current Player: {description['current_player']}")
    print(f"Terminal: {description['is_terminal']}")
    print(f"Pile Frozen: {description['pile_frozen']}")

    print(f"\nStock: {description['stock_count']} cards")
    print(f"Discard Pile: {description['discard_pile']['count']} cards")
    if description['discard_pile']['top_card']:
        print(f"  Top card: {description['discard_pile']['top_card']}")

    print("\nHands:")
    for player_key, hand_info in description['hands'].items():
        print(f"  {player_key} (Team {hand_info['team']}): {hand_info['card_count']} cards, {hand_info['wild_count']} wild")

    print("\nMelds:")
    for team_key, melds in description['melds'].items():
        print(f"  {team_key}:")
        if not melds:
            print("    (no melds)")
        for meld in melds:
            canasta_type = ""
            if meld['is_natural_canasta']:
                canasta_type = " [NATURAL CANASTA]"
            elif meld['is_mixed_canasta']:
                canasta_type = " [MIXED CANASTA]"
            print(f"    {meld['rank']}s: {meld['total_cards']} cards{canasta_type}")

    print("\nRed Threes:")
    for team_key, rt_info in description['red_threes'].items():
        print(f"  {team_key}: {rt_info['count']} red threes")

    print("\nScores:")
    print(f"  Team 0: {description['team_scores']['team_0']}")
    print(f"  Team 1: {description['team_scores']['team_1']}")

    print("\nCanastas:")
    print(f"  Team 0: {description['canastas']['team_0']}")
    print(f"  Team 1: {description['canastas']['team_1']}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Preview render Canasta UI fixtures."
    )
    parser.add_argument(
        "--format",
        choices=["text", "rich", "html"],
        default="text",
        help="Output format: text (ASCII), rich (colored terminal), or html. Default: text",
    )
    parser.add_argument(
        "--perspective",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="Player perspective (0-3). Default: 0",
    )
    parser.add_argument(
        "--hide-hands",
        action="store_true",
        help="Hide other players' hands (default shows all hands)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open rendered HTML files in browser (only with --format html)",
    )
    return parser.parse_args()


def main():
    """Main entry point for preview render script."""
    args = parse_args()

    print("Canasta UI Fixture Preview")
    print("=" * 60)
    print(f"Generated: {datetime.now().isoformat()}")
    print(f"Format: {args.format}")

    # Get renders directory
    renders_dir = project_root / "renders"
    renders_dir.mkdir(exist_ok=True)

    # Get all fixtures
    fixtures = get_all_fixtures()

    # Create renderer based on format choice
    show_all_hands = not args.hide_hands
    if args.format == "rich":
        from canasta.ui.rich_renderer import RichRenderer
        renderer = RichRenderer(perspective=args.perspective, show_all_hands=show_all_hands)
    elif args.format == "html":
        from canasta.ui.html_renderer import HTMLRenderer
        renderer = HTMLRenderer(perspective=args.perspective, show_all_hands=show_all_hands)
    else:
        renderer = TextRenderer(perspective=args.perspective, show_all_hands=show_all_hands)

    all_descriptions = {}
    all_renders = []
    html_files = []

    for name, state in fixtures.items():
        description = describe_state(name, state)
        all_descriptions[name] = description

        # Render using selected renderer
        rendered = renderer.render(state)
        all_renders.append((name, rendered))

        # Print rendered output to console (skip for HTML - too verbose)
        if args.format != "html":
            print(f"\n{'='*60}")
            print(f"  {name}")
            print(f"{'='*60}")
            print(rendered)

        # Save individual render
        if args.format == "html":
            html_file = renders_dir / f"{name}.html"
            with open(html_file, 'w') as f:
                f.write(rendered)
            html_files.append(html_file)
            print(f"  Saved: {html_file}")
        else:
            text_file = renders_dir / f"{name}.txt"
            with open(text_file, 'w') as f:
                f.write(f"Fixture: {name}\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(rendered)
            print(f"\n  Saved: {text_file}")

        # Save individual fixture description (JSON)
        fixture_file = renders_dir / f"{name}.json"
        with open(fixture_file, 'w') as f:
            json.dump(description, f, indent=2)

    # Save combined renders (text/rich only)
    if args.format != "html":
        combined_text_file = renders_dir / "all_renders.txt"
        with open(combined_text_file, 'w') as f:
            f.write("Canasta UI Text Renders\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n")
            for name, rendered in all_renders:
                f.write(f"\n{'='*60}\n")
                f.write(f"  {name}\n")
                f.write(f"{'='*60}\n")
                f.write(rendered)
                f.write("\n")

    # Save combined fixtures file (JSON)
    combined_file = renders_dir / "all_fixtures.json"
    with open(combined_file, 'w') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "fixtures": all_descriptions,
        }, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Preview complete. {len(fixtures)} fixtures rendered.")
    print(f"Output saved to: {renders_dir}")
    if args.format != "html":
        print(f"Text renders: {renders_dir / 'all_renders.txt'}")
    else:
        print(f"HTML files: {len(html_files)} files in {renders_dir}")
    print(f"JSON data: {combined_file}")

    # Open HTML files in browser if requested
    if args.format == "html" and args.open_browser and html_files:
        import webbrowser
        # Open the first HTML file
        first_file = html_files[0]
        file_url = f"file://{first_file.resolve()}"
        print(f"\nOpening in browser: {file_url}")
        webbrowser.open(file_url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
