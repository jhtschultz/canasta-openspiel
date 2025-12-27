#!/usr/bin/env python3
"""Example: Render a Canasta game in progress.

This script demonstrates how to use the Canasta UI renderers to visualize
game states. It shows:
- Creating a game state using fixtures
- Rendering in all 3 formats (text, rich, HTML)
- Switching player perspectives

Usage:
    python examples/render_game.py
    python examples/render_game.py --fixture mid_game
    python examples/render_game.py --perspective 2
    python examples/render_game.py --format html --open
"""

import argparse
import sys
import webbrowser
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from canasta.ui import (
    # Renderers
    TextRenderer,
    RichRenderer,
    HTMLRenderer,
    # Fixtures
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
    get_all_fixtures,
)


FIXTURE_CREATORS = {
    "early_game": create_early_game_state,
    "mid_game": create_mid_game_state,
    "canasta": create_canasta_state,
    "frozen_pile": create_frozen_pile_state,
    "red_threes": create_red_threes_state,
    "terminal": create_terminal_state,
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Render a Canasta game state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Render mid-game state in text format
    python examples/render_game.py --fixture mid_game

    # Render from Player 2's perspective
    python examples/render_game.py --perspective 2

    # Render in HTML and open in browser
    python examples/render_game.py --format html --open

    # Show all hands (debug mode)
    python examples/render_game.py --show-all-hands

Available fixtures:
    early_game   - Right after dealing, no melds
    mid_game     - Game in progress with melds
    canasta      - Both teams have canastas
    frozen_pile  - Discard pile is frozen
    red_threes   - Red threes placed for both teams
    terminal     - Game over with final scores
""",
    )
    parser.add_argument(
        "--fixture",
        choices=list(FIXTURE_CREATORS.keys()),
        default="mid_game",
        help="Which fixture to render. Default: mid_game",
    )
    parser.add_argument(
        "--format",
        choices=["text", "rich", "html", "all"],
        default="text",
        help="Output format. 'all' shows all 3 formats. Default: text",
    )
    parser.add_argument(
        "--perspective",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="Player perspective (0-3). Default: 0",
    )
    parser.add_argument(
        "--show-all-hands",
        action="store_true",
        help="Show all players' hands (debug mode)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open HTML output in browser (only with --format html)",
    )
    return parser.parse_args()


def render_with_format(state, fmt: str, perspective: int, show_all_hands: bool) -> str:
    """Render state with the specified format.

    Args:
        state: CanastaState to render
        fmt: Format name ('text', 'rich', or 'html')
        perspective: Player perspective (0-3)
        show_all_hands: Whether to show all hands

    Returns:
        Rendered string
    """
    if fmt == "text":
        renderer = TextRenderer(perspective=perspective, show_all_hands=show_all_hands)
    elif fmt == "rich":
        renderer = RichRenderer(perspective=perspective, show_all_hands=show_all_hands)
    elif fmt == "html":
        renderer = HTMLRenderer(perspective=perspective, show_all_hands=show_all_hands)
    else:
        raise ValueError(f"Unknown format: {fmt}")

    return renderer.render(state)


def demonstrate_perspective_switching(state, fmt: str, show_all_hands: bool):
    """Demonstrate rendering from different player perspectives.

    Args:
        state: CanastaState to render
        fmt: Format name
        show_all_hands: Whether to show all hands
    """
    print("\n" + "=" * 60)
    print("PERSPECTIVE SWITCHING DEMONSTRATION")
    print("=" * 60)

    for perspective in range(4):
        print(f"\n--- Player {perspective}'s Perspective ---\n")
        output = render_with_format(state, fmt, perspective, show_all_hands)
        print(output)
        print()


def main():
    """Main entry point."""
    args = parse_args()

    # Create the game state
    create_func = FIXTURE_CREATORS[args.fixture]
    state = create_func()

    print(f"Canasta UI Renderer Example")
    print(f"=" * 60)
    print(f"Fixture: {args.fixture}")
    print(f"Perspective: Player {args.perspective}")
    print(f"Format: {args.format}")
    print(f"Show all hands: {args.show_all_hands}")
    print(f"=" * 60)

    if args.format == "all":
        # Show all 3 formats
        for fmt in ["text", "rich", "html"]:
            print(f"\n{'=' * 60}")
            print(f"  {fmt.upper()} FORMAT")
            print(f"{'=' * 60}\n")
            output = render_with_format(
                state, fmt, args.perspective, args.show_all_hands
            )
            if fmt == "html":
                # Truncate HTML for console display
                print(output[:2000] + "..." if len(output) > 2000 else output)
            else:
                print(output)
    else:
        # Single format
        output = render_with_format(
            state, args.format, args.perspective, args.show_all_hands
        )
        print()
        print(output)

        # Open in browser if requested (HTML only)
        if args.format == "html" and args.open_browser:
            with NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            ) as f:
                f.write(output)
                temp_path = f.name

            file_url = f"file://{temp_path}"
            print(f"\nOpening in browser: {file_url}")
            webbrowser.open(file_url)

    # Show perspective switching demo if text format
    if args.format == "text" and not args.show_all_hands:
        print("\n" + "=" * 60)
        print("TIP: Try --perspective 1 or --perspective 2 to see different views")
        print("     Use --show-all-hands to reveal all cards (debug mode)")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
