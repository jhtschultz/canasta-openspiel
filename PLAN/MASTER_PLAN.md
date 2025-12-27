# Master Plan: Canasta UI Renderer

## Overview

Build a visual renderer for CanastaState that produces clear, human-readable output showing the complete game state. Inspired by Canasta Junction's teal/turquoise aesthetic and 4-player table layout.

---

## 1. Layout Design

### Table Layout (Top-Down View)

```
                    ┌─────────────────────────────────────┐
                    │         PLAYER 2 (Top)              │
                    │  [Card backs or "11 cards"]         │
                    │                                     │
                    │    ┌──────────────────────┐        │
                    │    │   Team 1 Melds       │        │
                    │    │   (Players 1 & 3)    │        │
                    │    └──────────────────────┘        │
    ┌───────────┐   │                                    │   ┌───────────┐
    │ PLAYER 1  │   │   ┌────────┐    ┌────────┐        │   │ PLAYER 3  │
    │  (Left)   │   │   │ STOCK  │    │DISCARD │        │   │  (Right)  │
    │ [backs]   │   │   │  (45)  │    │  [K♠]  │        │   │ [backs]   │
    └───────────┘   │   └────────┘    └────────┘        │   └───────────┘
                    │                                     │
                    │    ┌──────────────────────┐        │
                    │    │   Team 0 Melds       │        │
                    │    │   (Players 0 & 2)    │        │
                    │    └──────────────────────┘        │
                    │                                     │
                    │         PLAYER 0 (Bottom/You)      │
                    │  [A♠] [A♥] [5♦] [5♣] [5♠] [7♥]... │
                    └─────────────────────────────────────┘

    SCORES: Team 0: 1250  |  Team 1: 980
    PHASE: Player 0's turn - MELD phase
    PILE: Unfrozen | Initial meld: Required (50 pts)
```

### Player Positions

| Position | Player | Team | Visual Location |
|----------|--------|------|-----------------|
| Bottom | Player 0 | Team 0 | South (your hand, visible) |
| Left | Player 1 | Team 1 | West |
| Top | Player 2 | Team 0 | North (your partner) |
| Right | Player 3 | Team 1 | East |

Partners sit opposite each other (standard Canasta seating).

---

## 2. Visual Elements

### 2.1 Cards

**Card Representation (Unicode approach):**
```
┌─────┐
│ A   │
│  ♠  │
│   A │
└─────┘
```

**Compact representation:** `[A♠]` or `[10♥]` or `[JKR]`

**Card Backs:** `[###]` or `[???]`

**Unicode Suits:**
- ♠ (spades) - U+2660
- ♥ (hearts) - U+2665
- ♦ (diamonds) - U+2666
- ♣ (clubs) - U+2663

**Rank Display:**
| Rank Index | Display |
|------------|---------|
| 0 | A |
| 1 | 2 |
| 2 | 3 |
| 3 | 4 |
| 4 | 5 |
| 5 | 6 |
| 6 | 7 |
| 7 | 8 |
| 8 | 9 |
| 9 | 10 |
| 10 | J |
| 11 | Q |
| 12 | K |
| -1 (joker) | JKR |

**Color Coding (for HTML/SVG):**
- Hearts/Diamonds: Red (#E53935)
- Clubs/Spades: Black (#212121)
- Jokers: Purple (#7B1FA2)
- Wild 2s: Blue highlight (#1976D2)

### 2.2 Melds

Display melds as horizontal card groups with canasta status:

```
Team 0 Melds:
  Kings (5): [K♠][K♥][K♦][K♣][K♠]
  Sevens (7) ★CANASTA★: [7♠][7♥][7♦][7♣][7♠][7♥][7♦]
  Fives (4+1w): [5♠][5♥][5♦][5♣][2♠]  ← wild card shown
```

**Canasta Indicators:**
- Natural canasta (7+ cards, no wilds): `★NATURAL★` (gold/yellow)
- Mixed canasta (7+ cards, with wilds): `★MIXED★` (silver/gray)
- Not yet canasta: just show count

### 2.3 Stock & Discard Piles

**Stock Pile:**
```
┌─────┐
│#####│
│ 45  │  ← card count
│#####│
└─────┘
```

**Discard Pile:**
```
┌─────┐
│ K   │
│  ♠  │  ← top card visible
│   K │
└─────┘
(12 cards)  ← pile depth

[FROZEN] indicator when applicable
```

### 2.4 Red Threes

Display red threes prominently for each team:
```
Team 0 Red 3s: [3♥] [3♦]  (200 pts)
Team 1 Red 3s: [3♥]       (100 pts)
```

### 2.5 Scores

```
╔═══════════════════════════════════════╗
║  SCORES                               ║
║  Team 0 (You + Partner): 1,250        ║
║  Team 1 (Opponents):       980        ║
║                                       ║
║  This Hand: Team 0: +450  Team 1: +0  ║
╚═══════════════════════════════════════╝
```

### 2.6 Game State Indicators

```
Turn: Player 0 (You)
Phase: MELD (Draw → [MELD] → Discard)
Pile: FROZEN (team hasn't made initial meld)
Initial Meld Required: 50 points (team score: 0-1495)
Hand: 2 of 5000 point target
```

---

## 3. Output Formats

### Phase 1: Text/Terminal (ASCII Art)

Pure text output that works in any terminal. Uses box-drawing characters and Unicode suits.

**Pros:** Simple, works everywhere, easy to test
**Cons:** Limited layout flexibility, no colors in basic terminals

### Phase 2: Rich Terminal (with colors)

Use `rich` library for colored, formatted terminal output.

**Dependencies:** `rich` (pip install rich)

### Phase 3: HTML/SVG

Generate static HTML/SVG that can be:
- Viewed in browser
- Saved as image
- Embedded in notebooks

**Structure:**
```
canasta/
  ui/
    __init__.py
    renderer.py      # Abstract base, format-agnostic game state → visual
    text_renderer.py # Terminal ASCII output
    rich_renderer.py # Rich library colored terminal
    html_renderer.py # HTML/SVG output
    cards.py         # Card visual representations
    layout.py        # Position calculations
```

---

## 4. API Design

### Core Interface

```python
from canasta.ui import render_state, TextRenderer, HTMLRenderer

# Get a CanastaState from gameplay
state = game.new_initial_state()
# ... play some actions ...

# Render to terminal
print(render_state(state))

# Or with specific renderer
renderer = TextRenderer(
    perspective=0,        # Which player's view (0-3), or None for omniscient
    show_all_hands=False, # Debug mode: show all hands
    compact=False,        # Compact vs expanded layout
)
print(renderer.render(state))

# HTML output
html_renderer = HTMLRenderer(perspective=0)
html = html_renderer.render(state)
with open("game_state.html", "w") as f:
    f.write(html)
```

### Perspective Modes

| Mode | Description |
|------|-------------|
| `perspective=0` | Player 0's view - own hand visible, others show backs |
| `perspective=1` | Player 1's view |
| `perspective=2` | Player 2's view |
| `perspective=3` | Player 3's view |
| `perspective=None` | Omniscient - all hands visible (debug/replay mode) |

### State Extraction

The renderer needs to extract from CanastaState:
- `state._hands[player]` - list of card IDs
- `state._melds[team]` - list of Meld objects
- `state._discard_pile` - list of card IDs (show top)
- `state._stock` - list of card IDs (show count only)
- `state._red_threes[team]` - list of card IDs
- `state._team_scores[team]` - cumulative scores
- `state._hand_scores[team]` - current hand scores
- `state._current_player` - whose turn
- `state._turn_phase` - "draw", "meld", "discard"
- `state._pile_frozen` - bool
- `state._initial_meld_made[team]` - bool per team
- `state._canastas[team]` - canasta count per team
- `state._hand_number` - which hand we're on
- `state._target_score` - typically 5000

---

## 5. Visual Verification Loop

**Critical:** Every render change must be visually verified by a human or screenshot comparison.

### Verification Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    RENDER → VIEW → ITERATE                   │
│                                                              │
│  1. Generate sample states (fixtures)                        │
│  2. Render to output (text/HTML)                            │
│  3. View output (terminal / browser)                         │
│  4. Human verifies correctness                               │
│  5. If wrong → fix → re-render → re-view                    │
└─────────────────────────────────────────────────────────────┘
```

### Sample Game States (Fixtures)

Create deterministic game states for visual testing:

```python
# canasta/ui/fixtures.py

def create_early_game_state():
    """State after dealing - full hands, no melds, empty discard."""
    ...

def create_mid_game_state():
    """State with melds on both teams, partial hands, discard pile."""
    ...

def create_canasta_state():
    """State where Team 0 has a natural canasta, Team 1 has mixed."""
    ...

def create_going_out_state():
    """State where current player can go out."""
    ...

def create_terminal_state():
    """Game over state with final scores."""
    ...

def create_frozen_pile_state():
    """State with frozen discard pile (wild card discarded)."""
    ...

def create_red_threes_state():
    """State with red threes on both teams."""
    ...
```

### Render Preview Script

```python
# scripts/preview_render.py
"""
Render sample states and open for viewing.

Usage:
    python scripts/preview_render.py --format text
    python scripts/preview_render.py --format html --open
    python scripts/preview_render.py --format html --save renders/
"""

from canasta.ui import TextRenderer, HTMLRenderer
from canasta.ui.fixtures import *

def main():
    states = {
        "early_game": create_early_game_state(),
        "mid_game": create_mid_game_state(),
        "canasta": create_canasta_state(),
        "frozen_pile": create_frozen_pile_state(),
        "terminal": create_terminal_state(),
    }

    for name, state in states.items():
        # Render
        output = renderer.render(state)

        # Save to file
        save_path = f"renders/{name}.{ext}"

        # For HTML: optionally open in browser
        if args.open and format == "html":
            webbrowser.open(f"file://{save_path}")

        print(f"Rendered: {save_path}")
```

### Viewing Methods

| Format | How to View | Automation |
|--------|-------------|------------|
| Text | Print to terminal | `python -c "..."` |
| Text | Save to file, `cat` | Save to `renders/*.txt` |
| HTML | Open in browser | `webbrowser.open()` |
| HTML | Screenshot | Playwright/Selenium headless |

### Screenshot Comparison (Optional, for CI)

For automated visual regression:

```python
# scripts/screenshot_compare.py
"""
Capture screenshots of HTML renders and compare to golden images.
Uses Playwright for headless browser screenshots.
"""

from playwright.sync_api import sync_playwright

def capture_screenshot(html_path, output_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{html_path}")
        page.screenshot(path=output_path)
        browser.close()

def compare_to_golden(current, golden, threshold=0.01):
    """Return True if images match within threshold."""
    ...
```

### Manual Verification Checklist

When reviewing rendered output, check:

- [ ] All 4 player positions visible and correctly placed
- [ ] Current player's hand shows face-up cards
- [ ] Other players show card backs or counts
- [ ] Melds grouped by team correctly
- [ ] Canastas marked (natural vs mixed)
- [ ] Wild cards visible in melds
- [ ] Stock pile shows count
- [ ] Discard pile shows top card
- [ ] Frozen pile indicator when applicable
- [ ] Red threes displayed per team
- [ ] Scores correct for both teams
- [ ] Current phase indicator correct
- [ ] Layout fits in viewport/terminal

---

## 6. Testing Strategy

### Unit Tests

1. **Card Rendering**
   - Each rank/suit renders correctly
   - Jokers render correctly
   - Card backs render correctly

2. **Meld Rendering**
   - Melds show all cards
   - Canasta status displayed correctly
   - Wild cards distinguished

3. **Layout**
   - All 4 player positions correct
   - Team melds in correct areas
   - Center area (stock/discard) positioned

4. **State Extraction**
   - All state fields correctly read
   - Perspective filtering works (hide other hands)

5. **Edge Cases**
   - Empty hand
   - Empty melds
   - Empty discard pile
   - All 4 red threes on one team
   - Maximum hand size
   - Game terminal state

### Integration Tests

1. **Full Game Render**
   - Render state at various points in a game
   - Verify no crashes on random game states

2. **Round-Trip** (for debug mode)
   - Render state → human can understand what actions are legal

---

## 7. Phase Breakdown

### Phase 1: Fixtures & Preview Infrastructure
- Create deterministic game state fixtures
- Build preview script (`scripts/preview_render.py`)
- Establish render → view → verify workflow
- **Output:** Can generate and view sample game states
- **Verification:** Run preview script, visually confirm fixtures look reasonable

### Phase 2: Core Text Renderer
- Card representation utilities (`canasta/ui/cards.py`)
- State extraction (`canasta/ui/state_view.py`)
- Basic ASCII layout (`canasta/ui/text_renderer.py`)
- Unit tests for all components
- **Output:** Working `TextRenderer` that prints game state to terminal
- **Verification:**
  1. Run `python scripts/preview_render.py --format text`
  2. View each rendered fixture in terminal
  3. Check against verification checklist
  4. Fix any issues, re-render, re-verify

### Phase 3: Rich Terminal Renderer
- Color support via `rich` library
- Better visual hierarchy
- Canasta Junction color scheme (teal primary)
- **Output:** `RichRenderer` with colored output
- **Verification:**
  1. Run `python scripts/preview_render.py --format rich`
  2. View colored output in terminal
  3. Verify colors match design (red suits red, etc.)
  4. Fix any issues, re-render, re-verify

### Phase 4: HTML/SVG Renderer
- SVG card graphics (simple vector cards)
- CSS styling matching Canasta Junction aesthetic
- Responsive layout
- **Output:** `HTMLRenderer` producing standalone HTML files
- **Verification:**
  1. Run `python scripts/preview_render.py --format html --open`
  2. Browser opens with rendered game state
  3. Check layout, colors, card rendering
  4. Test at different viewport sizes
  5. Fix any issues, re-render, re-verify

### Phase 5: Integration & Polish
- Example scripts showing usage
- Documentation
- Golden image snapshots (optional)
- **Output:** Complete, documented UI module
- **Verification:** Full visual review of all fixtures in all formats

---

## 8. File Structure

```
canasta-openspiel/
├── canasta/
│   ├── ui/
│   │   ├── __init__.py          # Exports: render_state, TextRenderer, etc.
│   │   ├── base.py              # Abstract Renderer base class
│   │   ├── cards.py             # Card → visual representation
│   │   ├── state_view.py        # Extract renderable data from CanastaState
│   │   ├── fixtures.py          # Deterministic game states for testing
│   │   ├── text_renderer.py     # ASCII art renderer
│   │   ├── rich_renderer.py     # Rich library renderer
│   │   └── html_renderer.py     # HTML/SVG renderer
│   ├── cards.py                 # (existing)
│   ├── canasta_game.py          # (existing)
│   └── ...
├── scripts/
│   ├── preview_render.py        # Render fixtures and view output
│   └── screenshot_compare.py    # (optional) Visual regression testing
├── renders/                     # Output directory for rendered previews
│   ├── early_game.txt
│   ├── mid_game.txt
│   ├── early_game.html
│   └── ...
├── tests/
│   ├── test_ui_cards.py
│   ├── test_ui_text_renderer.py
│   ├── test_ui_state_view.py
│   ├── test_ui_fixtures.py
│   └── ...
├── examples/
│   ├── render_game.py           # Example: render a game in progress
│   └── render_replay.py         # Example: render each state in a game
└── PLAN/
    ├── NORTH_STAR.md
    ├── MASTER_PLAN.md
    └── 01_requirements.md
```

---

## 9. Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| (none) | Phase 1 text renderer | Yes (stdlib only) |
| `rich` | Phase 2 colored terminal | Optional |
| (stdlib) | Phase 3 HTML generation | Yes (no external deps) |

---

## 10. Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Card representation | Unicode suits (♠♥♦♣) | Universal, no assets needed |
| Layout orientation | Top-down table view | Matches Canasta Junction, intuitive |
| Partner position | Opposite (N/S, E/W) | Standard Canasta seating |
| Default perspective | Player 0 | Most common use case |
| Phase 1 output | ASCII text | Simple, testable, no deps |
| Meld display | Horizontal card rows | Clear, space-efficient |

---

## 11. Open Questions (Resolved)

1. **Q: Which player is "you"?**
   A: Configurable via `perspective` parameter, default Player 0

2. **Q: Show hidden hands as backs or just count?**
   A: Compact mode shows count, expanded shows card back symbols

3. **Q: How to show wild cards in melds?**
   A: Show the actual card (e.g., `[2♠]` or `[JKR]`) - wilds are visible in melds

4. **Q: Frozen pile indicator?**
   A: Text label `[FROZEN]` below discard pile, red color in rich/HTML
