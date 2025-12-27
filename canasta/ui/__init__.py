"""Canasta UI package for rendering and visualizing game states."""

from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
    get_all_fixtures,
)
from canasta.ui.base import Renderer
from canasta.ui.cards import card_to_str, card_back, format_card_list
from canasta.ui.state_view import StateView, MeldView, extract_state_view
from canasta.ui.text_renderer import TextRenderer
from canasta.ui.rich_renderer import RichRenderer
from canasta.ui.html_renderer import HTMLRenderer

__all__ = [
    # Fixtures
    "create_early_game_state",
    "create_mid_game_state",
    "create_canasta_state",
    "create_frozen_pile_state",
    "create_red_threes_state",
    "create_terminal_state",
    "get_all_fixtures",
    # Base
    "Renderer",
    # Cards
    "card_to_str",
    "card_back",
    "format_card_list",
    # State view
    "StateView",
    "MeldView",
    "extract_state_view",
    # Renderers
    "TextRenderer",
    "RichRenderer",
    "HTMLRenderer",
]
