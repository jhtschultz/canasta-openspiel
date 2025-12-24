# Canasta for OpenSpiel

A complete implementation of 4-player Partnership Canasta as a Python game for [OpenSpiel](https://github.com/google-deepmind/open_spiel).

## Features

- **Full Pagat Classic rules** - Implements the authoritative [Pagat Canasta rules](https://www.pagat.com/rummy/canasta.html)
- **4-player partnership** - Teams of 2 (Players 0+2 vs Players 1+3)
- **Multi-hand games** - Play to 5000 points with proper score accumulation
- **RL-ready** - Observation tensors for use with CFR, MCTS, and other algorithms
- **322 tests** - Comprehensive test coverage of all game mechanics

## Installation

```bash
pip install -e .
```

Requires OpenSpiel:
```bash
pip install open_spiel
```

## Quick Start

```python
import pyspiel
from canasta.canasta_game import CanastaGame

# Create game and initial state
game = CanastaGame()
state = game.new_initial_state()

# Play random actions until terminal
import random
while not state.is_terminal():
    if state.is_chance_node():
        outcomes = state.chance_outcomes()
        action, _ = random.choice(outcomes)
    else:
        action = random.choice(state.legal_actions())
    state.apply_action(action)

# Get final scores
print(f"Returns: {state.returns()}")
```

## Game Rules Summary

### Card Values
- Jokers: 50 points (wild)
- 2s: 20 points (wild)
- Aces: 20 points
- 8-K: 10 points
- 3-7: 5 points

### Melds
- Minimum 3 cards of same rank
- At least 2 natural cards required
- Maximum 3 wild cards per meld
- **Canasta**: 7+ cards (Natural: 500 bonus, Mixed: 300 bonus)

### Initial Meld Requirements
| Team Score | Minimum |
|------------|---------|
| Negative | 15 points |
| 0-1495 | 50 points |
| 1500-2995 | 90 points |
| 3000+ | 120 points |

### Special Cards
- **Red 3s**: Auto-placed, 100 pts each (800 for all 4), penalty without melds
- **Black 3s**: Block pile pickup, can only meld when going out

### Going Out
- Must have at least 1 canasta
- May ask partner for permission
- Concealed going out: 200 bonus (vs 100 regular)

## Project Structure

```
canasta-openspiel/
├── canasta/
│   ├── __init__.py
│   ├── cards.py          # Card representation (108 cards)
│   ├── deck.py           # Deck and dealing
│   ├── melds.py          # Meld validation and scoring
│   ├── scoring.py        # Hand/game scoring
│   ├── canasta_game.py   # CanastaGame, CanastaState
│   └── observer.py       # Observation tensors for RL
├── tests/                # 322 tests
├── examples/
│   └── play_random.py
└── pyproject.toml
```

## Action Space

| Range | Action Type |
|-------|-------------|
| 0 | Draw from stock |
| 1 | Take discard pile |
| 2-1000 | Create new meld |
| 1001-2000 | Add to existing meld |
| 2001 | Skip meld phase |
| 2002-2109 | Discard card |
| 2110-2113 | Going out actions |

## Observation Tensor

273-dimensional tensor including:
- Player hand (108 dims)
- Team melds (26 dims)
- Discard pile top (109 dims)
- Game state (pile size, stock size, scores, phase, etc.)

## Running Tests

```bash
pytest
```

## License

MIT
