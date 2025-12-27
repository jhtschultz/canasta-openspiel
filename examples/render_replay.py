#!/usr/bin/env python3
"""Example: Render a game replay with random moves.

This script demonstrates how the UI updates as a game progresses:
- Creates a new game
- Plays random moves until terminal or max steps
- Renders each state showing turn-by-turn updates

Usage:
    python examples/render_replay.py
    python examples/render_replay.py --max-steps 20
    python examples/render_replay.py --format rich
    python examples/render_replay.py --delay 0.5
"""

import argparse
import random
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyspiel

from canasta.ui import (
    TextRenderer,
    RichRenderer,
    HTMLRenderer,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Play through a Canasta game with random moves, rendering each state.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Play 10 steps with text rendering
    python examples/render_replay.py --max-steps 10

    # Play with colored output
    python examples/render_replay.py --format rich

    # Add delay between moves for easier viewing
    python examples/render_replay.py --delay 0.5

    # Skip dealing phase for faster start
    python examples/render_replay.py --skip-dealing

Note:
    The game uses random moves, so outcomes will vary each run.
    Dealing phase can take many steps (~45 for initial deal).
""",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=60,
        help="Maximum number of steps to play. Default: 60",
    )
    parser.add_argument(
        "--format",
        choices=["text", "rich"],
        default="text",
        help="Output format (text or rich). Default: text",
    )
    parser.add_argument(
        "--perspective",
        type=int,
        choices=[0, 1, 2, 3],
        default=0,
        help="Player perspective (0-3). Default: 0",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between renders. Default: 0 (no delay)",
    )
    parser.add_argument(
        "--skip-dealing",
        action="store_true",
        help="Skip the dealing phase (start from first player action)",
    )
    parser.add_argument(
        "--show-all-hands",
        action="store_true",
        help="Show all players' hands (debug mode)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    return parser.parse_args()


def get_renderer(fmt: str, perspective: int, show_all_hands: bool):
    """Create a renderer for the specified format.

    Args:
        fmt: Format name ('text' or 'rich')
        perspective: Player perspective (0-3)
        show_all_hands: Whether to show all hands

    Returns:
        Renderer instance
    """
    if fmt == "text":
        return TextRenderer(perspective=perspective, show_all_hands=show_all_hands)
    elif fmt == "rich":
        return RichRenderer(perspective=perspective, show_all_hands=show_all_hands)
    else:
        raise ValueError(f"Unknown format: {fmt}")


def describe_action(state, action: int) -> str:
    """Get a human-readable description of an action.

    Args:
        state: Current game state
        action: Action ID

    Returns:
        Description string
    """
    # Action constants from canasta_game.py
    ACTION_DRAW_STOCK = 0
    ACTION_TAKE_PILE = 1
    ACTION_SKIP_MELD = 2001
    ACTION_DISCARD_START = 2002
    ACTION_DISCARD_END = 2109
    ACTION_ASK_PARTNER_GO_OUT = 2110
    ACTION_ANSWER_GO_OUT_YES = 2111
    ACTION_ANSWER_GO_OUT_NO = 2112
    ACTION_GO_OUT = 2113

    if state.is_chance_node():
        return f"Chance: deal card"
    elif action == ACTION_DRAW_STOCK:
        return "Draw from stock"
    elif action == ACTION_TAKE_PILE:
        return "Take discard pile"
    elif action == ACTION_SKIP_MELD:
        return "Skip melding"
    elif ACTION_DISCARD_START <= action <= ACTION_DISCARD_END:
        card_id = action - ACTION_DISCARD_START
        return f"Discard card {card_id}"
    elif action == ACTION_ASK_PARTNER_GO_OUT:
        return "Ask partner to go out"
    elif action == ACTION_ANSWER_GO_OUT_YES:
        return "Answer: Yes, go out"
    elif action == ACTION_ANSWER_GO_OUT_NO:
        return "Answer: No, don't go out"
    elif action == ACTION_GO_OUT:
        return "Go out!"
    elif 2 <= action <= 1000:
        return f"Create meld (action {action})"
    elif 1001 <= action <= 2000:
        return f"Add to meld (action {action})"
    else:
        return f"Unknown action {action}"


def main():
    """Main entry point."""
    args = parse_args()

    # Set random seed if specified
    if args.seed is not None:
        random.seed(args.seed)

    print("Canasta Game Replay")
    print("=" * 60)
    print(f"Max steps: {args.max_steps}")
    print(f"Format: {args.format}")
    print(f"Perspective: Player {args.perspective}")
    if args.seed is not None:
        print(f"Random seed: {args.seed}")
    print("=" * 60)

    # Load the game and create initial state
    game = pyspiel.load_game("python_canasta")
    state = game.new_initial_state()

    # Create renderer
    renderer = get_renderer(args.format, args.perspective, args.show_all_hands)

    step = 0
    dealing_complete = False

    # Skip dealing if requested
    if args.skip_dealing:
        print("\nSkipping dealing phase...")
        while state.is_chance_node() and not state.is_terminal():
            outcomes = state.chance_outcomes()
            if not outcomes:
                break
            # Pick a random outcome
            actions, probs = zip(*outcomes)
            action = random.choices(actions, weights=probs)[0]
            state.apply_action(action)
        dealing_complete = True
        print("Dealing complete. Starting play phase.\n")

    # Play the game
    while not state.is_terminal() and step < args.max_steps:
        step += 1

        # Check if dealing just completed
        if not dealing_complete and not state.is_chance_node():
            dealing_complete = True
            print("\n" + "=" * 60)
            print("DEALING COMPLETE - GAME BEGINS")
            print("=" * 60 + "\n")

        # Get current player info
        current = state.current_player()
        if current == pyspiel.PlayerId.CHANCE:
            player_str = "Chance"
        elif current == pyspiel.PlayerId.TERMINAL:
            player_str = "Terminal"
        else:
            player_str = f"Player {current}"

        # Get legal actions
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            if not outcomes:
                break
            actions, probs = zip(*outcomes)
            action = random.choices(actions, weights=probs)[0]
        else:
            actions = state.legal_actions()
            if not actions:
                break
            action = random.choice(actions)

        action_desc = describe_action(state, action)

        # Render after dealing is complete (or always if not skipping dealing)
        if dealing_complete or not args.skip_dealing:
            # Only render non-chance nodes for cleaner output
            if not state.is_chance_node():
                print(f"\n{'=' * 60}")
                print(f"Step {step}: {player_str} - {action_desc}")
                print("=" * 60)
                print()
                print(renderer.render(state))

                if args.delay > 0:
                    time.sleep(args.delay)

        # Apply action
        state.apply_action(action)

    # Final state
    print(f"\n{'=' * 60}")
    if state.is_terminal():
        print("GAME OVER - FINAL STATE")
    else:
        print(f"STOPPED AFTER {step} STEPS")
    print("=" * 60)
    print()
    print(renderer.render(state))

    # Print final returns
    if state.is_terminal():
        print("\nFinal Returns:")
        returns = state.returns()
        for i, r in enumerate(returns):
            team = i % 2
            print(f"  Player {i} (Team {team}): {r}")

    print(f"\nReplay complete. {step} steps played.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
