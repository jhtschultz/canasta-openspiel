# North Star Card: Canasta UI

## What We're Building

A visual renderer for canasta-openspiel game states, inspired by Canasta Junction's layout. The UI displays the complete game state as a static visual representation - not interactive at first, but a faithful rendering that could later be made interactive.

## Build Profile

| Attribute | Value |
|-----------|-------|
| **Type** | Feature Extension |
| **Rigor Tier** | Medium (tests required, security scan before commit) |
| **Target User** | Developers working with canasta-openspiel, RL researchers visualizing game states |
| **Success Metric** | Can render any valid CanastaState to a visual format that humans can understand at a glance |

## Priority Order

1. **Correctness** - Every element of game state must be accurately represented
2. **Clarity** - Layout must be immediately comprehensible to someone who knows Canasta
3. **Completeness** - All game state elements visible (hands, melds, piles, scores, phase)
4. **Aesthetics** - Clean, modern look inspired by Canasta Junction

## Constraints

- Must work with existing CanastaState from canasta-openspiel
- No external game assets required (can use Unicode card symbols or simple graphics)
- Python-based (integrate with existing codebase)
- Output format: Start with terminal/text, then HTML/SVG

## Non-Goals (for now)

- Interactive clicking/dragging
- Animation
- Multiplayer networking
- Sound effects
- Mobile-specific layouts

## What "Done" Looks Like

Given any `CanastaState`, the renderer produces a visual showing:
1. All 4 player positions with their hands (current player's hand visible, others hidden/card backs)
2. Both teams' meld areas with canastas clearly marked
3. Central area with stock pile (count) and discard pile (top card visible)
4. Score display for both teams
5. Current phase indicator (draw/meld/discard)
6. Red threes displayed for each team
7. Frozen pile indicator when applicable
