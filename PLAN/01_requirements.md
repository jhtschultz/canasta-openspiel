# Requirements: Canasta UI Renderer

## REQ-1: Card Visual Representation
**Priority:** P0

The system must convert card IDs (0-107) into human-readable visual representations.

### Acceptance Criteria
- **AC-1.1:** Cards 0-103 render as rank + suit (e.g., "A♠", "10♥", "K♦")
- **AC-1.2:** Cards 104-107 render as jokers ("JKR" or "🃏")
- **AC-1.3:** All 4 suits use correct Unicode symbols (♠♥♦♣)
- **AC-1.4:** Ranks display correctly: A, 2-10, J, Q, K
- **AC-1.5:** Card backs render distinctly from face cards

---

## REQ-2: Hand Display
**Priority:** P0

The system must display player hands with appropriate visibility.

### Acceptance Criteria
- **AC-2.1:** Current perspective player's hand shows all cards face-up
- **AC-2.2:** Other players' hands show card backs or card count
- **AC-2.3:** Cards in hand are sorted by rank for readability
- **AC-2.4:** Hand position matches player seat (Bottom/Left/Top/Right)
- **AC-2.5:** Empty hand displays appropriately (e.g., "(empty)")

---

## REQ-3: Meld Display
**Priority:** P0

The system must display team melds with canasta status.

### Acceptance Criteria
- **AC-3.1:** Melds grouped by team (Team 0, Team 1)
- **AC-3.2:** Each meld shows all constituent cards
- **AC-3.3:** Wild cards in melds visually distinguished or labeled
- **AC-3.4:** Natural canastas (7+ cards, no wilds) marked distinctly
- **AC-3.5:** Mixed canastas (7+ cards, with wilds) marked distinctly
- **AC-3.6:** Meld rank is clear (e.g., "Kings:", "Sevens:")
- **AC-3.7:** Card count shown per meld

---

## REQ-4: Stock and Discard Piles
**Priority:** P0

The system must display the central piles.

### Acceptance Criteria
- **AC-4.1:** Stock pile shows remaining card count
- **AC-4.2:** Discard pile shows top card face-up
- **AC-4.3:** Discard pile shows total card count
- **AC-4.4:** Frozen pile status indicated when applicable
- **AC-4.5:** Empty stock renders appropriately
- **AC-4.6:** Empty discard pile renders appropriately

---

## REQ-5: Red Threes Display
**Priority:** P0

The system must display red threes for each team.

### Acceptance Criteria
- **AC-5.1:** Red threes shown separately from melds
- **AC-5.2:** Associated with correct team
- **AC-5.3:** Point value displayed (100 each, 800 for all 4)

---

## REQ-6: Score Display
**Priority:** P0

The system must display current scores.

### Acceptance Criteria
- **AC-6.1:** Cumulative team scores shown
- **AC-6.2:** Current hand scores shown
- **AC-6.3:** Scores associated with correct teams
- **AC-6.4:** Target score (5000) referenced

---

## REQ-7: Game State Indicators
**Priority:** P0

The system must display current game phase and status.

### Acceptance Criteria
- **AC-7.1:** Current player indicated
- **AC-7.2:** Current phase shown (draw/meld/discard)
- **AC-7.3:** Initial meld requirement shown if not yet made
- **AC-7.4:** Hand number shown for multi-hand games
- **AC-7.5:** Terminal state clearly indicated when game over

---

## REQ-8: Layout Structure
**Priority:** P0

The system must use a consistent, comprehensible layout.

### Acceptance Criteria
- **AC-8.1:** 4 player positions around table (Bottom, Left, Top, Right)
- **AC-8.2:** Partners opposite each other (0-2, 1-3)
- **AC-8.3:** Team melds in distinct areas
- **AC-8.4:** Stock/discard in center
- **AC-8.5:** Scores visible without scrolling
- **AC-8.6:** Layout renders correctly in 80-column terminal

---

## REQ-9: Text Renderer
**Priority:** P0

The system must provide a text-based renderer for terminals.

### Acceptance Criteria
- **AC-9.1:** Pure ASCII/Unicode output (no external dependencies)
- **AC-9.2:** Renders complete game state in single output
- **AC-9.3:** Works in standard 80x24 terminal (compact mode)
- **AC-9.4:** Configurable perspective (player 0-3 or omniscient)

---

## REQ-10: State Extraction
**Priority:** P0

The system must correctly extract all data from CanastaState.

### Acceptance Criteria
- **AC-10.1:** Extracts hands for all players
- **AC-10.2:** Extracts melds for both teams
- **AC-10.3:** Extracts stock and discard piles
- **AC-10.4:** Extracts red threes
- **AC-10.5:** Extracts scores (cumulative and hand)
- **AC-10.6:** Extracts phase information
- **AC-10.7:** Extracts frozen pile status
- **AC-10.8:** Extracts initial meld status per team
- **AC-10.9:** Handles all game phases (dealing, playing, terminal)

---

## REQ-11: Rich Terminal Renderer (Phase 2)
**Priority:** P1

The system should provide a colored terminal renderer.

### Acceptance Criteria
- **AC-11.1:** Uses `rich` library for colored output
- **AC-11.2:** Red suits in red, black suits in black
- **AC-11.3:** Canasta Junction color scheme (teal accents)
- **AC-11.4:** Visual hierarchy through color/style

---

## REQ-12: HTML Renderer (Phase 3)
**Priority:** P2

The system should provide an HTML/SVG renderer.

### Acceptance Criteria
- **AC-12.1:** Generates standalone HTML file
- **AC-12.2:** No external dependencies required to view
- **AC-12.3:** SVG or CSS-styled card representations
- **AC-12.4:** Matches Canasta Junction aesthetic

---

## REQ-13: Visual Test Fixtures
**Priority:** P0

The system must provide deterministic game states for visual testing.

### Acceptance Criteria
- **AC-13.1:** Fixtures create reproducible CanastaState objects (not random)
- **AC-13.2:** Fixtures cover key scenarios: early game, mid game, canastas, frozen pile, terminal
- **AC-13.3:** Fixtures can be rendered and viewed without playing a full game
- **AC-13.4:** Each fixture has known expected visual elements (documented)

---

## REQ-14: Render Preview Script
**Priority:** P0

The system must provide a way to render fixtures and view the output.

### Acceptance Criteria
- **AC-14.1:** Script renders all fixtures to chosen format (text/HTML)
- **AC-14.2:** Text output prints to terminal or saves to file
- **AC-14.3:** HTML output can be opened in browser automatically
- **AC-14.4:** Outputs saved to `renders/` directory for review
- **AC-14.5:** Script runnable with single command: `python scripts/preview_render.py`

---

## REQ-15: Human Verification Gate
**Priority:** P0

Visual changes must be verified by human review before completion.

### Acceptance Criteria
- **AC-15.1:** Each render implementation includes a verification step
- **AC-15.2:** Rendered output is saved/displayed for human inspection
- **AC-15.3:** Verification checklist used to confirm correctness
- **AC-15.4:** Issues found during verification are fixed before task closure
