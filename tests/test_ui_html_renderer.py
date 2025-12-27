"""Tests for canasta/ui/html_renderer.py - HTML renderer."""

import pytest
import re

from canasta.ui.html_renderer import (
    HTMLRenderer,
    COLORS,
    _card_color_class,
    _card_to_html,
    _card_back_html,
)
from canasta.ui.base import Renderer
from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
)


class TestHTMLRendererInit:
    """Tests for HTMLRenderer initialization."""

    def test_is_renderer_subclass(self):
        """HTMLRenderer is a subclass of Renderer."""
        renderer = HTMLRenderer()
        assert isinstance(renderer, Renderer)

    def test_default_perspective(self):
        """Default perspective is player 0."""
        renderer = HTMLRenderer()
        assert renderer.perspective == 0

    def test_custom_perspective(self):
        """Custom perspective is stored correctly."""
        renderer = HTMLRenderer(perspective=2)
        assert renderer.perspective == 2

    def test_show_all_hands_default(self):
        """show_all_hands defaults to False."""
        renderer = HTMLRenderer()
        assert renderer.show_all_hands is False

    def test_show_all_hands_true(self):
        """show_all_hands can be set to True."""
        renderer = HTMLRenderer(show_all_hands=True)
        assert renderer.show_all_hands is True

    def test_invalid_perspective_raises(self):
        """Invalid perspective raises ValueError."""
        with pytest.raises(ValueError):
            HTMLRenderer(perspective=4)
        with pytest.raises(ValueError):
            HTMLRenderer(perspective=-1)


class TestCardColorClass:
    """Tests for _card_color_class helper."""

    def test_hearts_are_red(self):
        """Hearts cards have 'red' class."""
        # Card 26-38 are hearts in first deck (13-25 offset + 13 for diamonds)
        # Actually: suit_idx = deck_offset // 13, rank_idx = deck_offset % 13
        # hearts is index 2, so cards 26-38 are hearts
        assert _card_color_class(26) == "red"  # Ace of hearts

    def test_diamonds_are_red(self):
        """Diamonds cards have 'red' class."""
        # Diamonds is suit index 1, cards 13-25
        assert _card_color_class(13) == "red"  # Ace of diamonds

    def test_clubs_are_black(self):
        """Clubs cards have 'black' class."""
        # Clubs is suit index 0, cards 0-12
        assert _card_color_class(0) == "black"  # Ace of clubs

    def test_spades_are_black(self):
        """Spades cards have 'black' class."""
        # Spades is suit index 3, cards 39-51
        assert _card_color_class(39) == "black"  # Ace of spades

    def test_jokers_are_purple(self):
        """Jokers have 'joker' class."""
        assert _card_color_class(104) == "joker"
        assert _card_color_class(107) == "joker"


class TestCardToHtml:
    """Tests for _card_to_html helper."""

    def test_joker_html(self):
        """Jokers render correctly."""
        html = _card_to_html(104)
        assert "JKR" in html
        assert 'class="card joker"' in html

    def test_red_card_html(self):
        """Red cards have red class."""
        html = _card_to_html(26)  # Ace of hearts
        assert 'class="card red"' in html

    def test_black_card_html(self):
        """Black cards have black class."""
        html = _card_to_html(0)  # Ace of clubs
        assert 'class="card black"' in html

    def test_card_is_span(self):
        """Cards are rendered as span elements."""
        html = _card_to_html(0)
        assert html.startswith('<span')
        assert html.endswith('</span>')


class TestCardBackHtml:
    """Tests for _card_back_html helper."""

    def test_card_back_html(self):
        """Card back renders correctly."""
        html = _card_back_html()
        assert "###" in html
        assert 'class="card back"' in html


class TestHTMLRenderBasics:
    """Tests for basic render functionality."""

    def test_render_returns_string(self):
        """AC-12.1: render() returns a string."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert isinstance(result, str)

    def test_render_not_empty(self):
        """render() returns non-empty output."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 0

    def test_render_is_html(self):
        """AC-12.1: render() returns valid HTML structure."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "</head>" in result
        assert "<body>" in result
        assert "</body>" in result

    def test_render_has_meta_charset(self):
        """AC-12.2: HTML has charset declaration."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert 'charset="utf-8"' in result

    def test_render_has_embedded_css(self):
        """AC-12.2: HTML has embedded CSS (no external deps)."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "<style>" in result
        assert "</style>" in result
        # Should not have external stylesheets
        assert 'rel="stylesheet"' not in result
        assert '<link' not in result or 'href=' not in result


class TestHTMLRenderContent:
    """Tests for rendered content."""

    def test_contains_player_labels(self):
        """Output contains player labels."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Player 0" in result
        assert "Player 1" in result
        assert "Player 2" in result
        assert "Player 3" in result

    def test_contains_perspective_marker(self):
        """Perspective player marked as 'You'."""
        renderer = HTMLRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(You)" in result

    def test_contains_partner_marker(self):
        """Partner marked correctly."""
        renderer = HTMLRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(Partner)" in result

    def test_contains_stock_pile(self):
        """Stock pile displayed."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Stock" in result

    def test_contains_discard_pile(self):
        """Discard pile displayed."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Discard" in result

    def test_contains_scores(self):
        """Scores displayed."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Team 0" in result
        assert "Team 1" in result

    def test_contains_meld_areas(self):
        """Meld areas displayed for both teams."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Team 0 Melds" in result
        assert "Team 1 Melds" in result


class TestHTMLRenderColors:
    """Tests for Canasta Junction color scheme (AC-12.4)."""

    def test_primary_teal_color(self):
        """AC-12.4: Uses teal primary color."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert COLORS["primary"] in result  # #008373

    def test_background_color(self):
        """AC-12.4: Uses light gray background."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert COLORS["background"] in result  # #F5F5F5

    def test_red_card_color(self):
        """AC-12.4: Uses red for hearts/diamonds."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert COLORS["red"] in result  # #E53935

    def test_black_card_color(self):
        """AC-12.4: Uses black for clubs/spades."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert COLORS["black"] in result  # #212121

    def test_joker_color(self):
        """AC-12.4: Uses purple for jokers."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert COLORS["joker"] in result  # #7B1FA2


class TestHTMLRenderCards:
    """Tests for CSS-styled card representations (AC-12.3)."""

    def test_cards_have_css_classes(self):
        """AC-12.3: Cards use CSS classes."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert 'class="card' in result

    def test_card_styling_defined(self):
        """AC-12.3: Card CSS styling is defined."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert ".card" in result
        assert "border" in result
        assert "border-radius" in result


class TestHTMLRenderMelds:
    """Tests for meld rendering."""

    def test_empty_melds_shown(self):
        """Empty melds show '(no melds)'."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(no melds)" in result

    def test_melds_with_cards(self):
        """Melds show rank and card count."""
        renderer = HTMLRenderer()
        state = create_mid_game_state()
        result = renderer.render(state)

        # Should contain rank names
        assert "Aces" in result or "Eights" in result

    def test_canasta_markers(self):
        """Canastas have type markers."""
        renderer = HTMLRenderer()
        state = create_canasta_state()
        result = renderer.render(state)

        # Should have canasta type indicators
        assert "NATURAL" in result or "MIXED" in result

    def test_natural_canasta_styling(self):
        """Natural canastas have gold background."""
        renderer = HTMLRenderer()
        state = create_canasta_state()
        result = renderer.render(state)

        # CSS should define gold background
        assert COLORS["natural_canasta"] in result  # #FFD700

    def test_mixed_canasta_styling(self):
        """Mixed canastas have silver background."""
        renderer = HTMLRenderer()
        state = create_canasta_state()
        result = renderer.render(state)

        # CSS should define silver background
        assert COLORS["mixed_canasta"] in result  # #C0C0C0


class TestHTMLRenderPiles:
    """Tests for pile rendering."""

    def test_stock_count_shown(self):
        """Stock count displayed."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        # Stock count should be in parentheses
        assert re.search(r'\(\d+\)', result)

    def test_frozen_pile_indicator(self):
        """Frozen pile indicator shown."""
        renderer = HTMLRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)

        assert "FROZEN" in result


class TestHTMLRenderRedThrees:
    """Tests for red three rendering."""

    def test_red_threes_displayed(self):
        """Red threes displayed when present."""
        renderer = HTMLRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)

        assert "Red Threes" in result


class TestHTMLRenderTerminal:
    """Tests for terminal state rendering."""

    def test_terminal_state_shows_game_over(self):
        """Terminal state shows game over."""
        renderer = HTMLRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "Game Over" in result

    def test_terminal_state_shows_winner(self):
        """Terminal state shows winner."""
        renderer = HTMLRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "Wins" in result


class TestHTMLRenderAllFixtures:
    """Tests for rendering all fixtures."""

    def test_render_early_game(self):
        """Early game renders without error."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 500

    def test_render_mid_game(self):
        """Mid game renders without error."""
        renderer = HTMLRenderer()
        state = create_mid_game_state()
        result = renderer.render(state)
        assert len(result) > 500

    def test_render_canasta(self):
        """Canasta state renders without error."""
        renderer = HTMLRenderer()
        state = create_canasta_state()
        result = renderer.render(state)
        assert len(result) > 500

    def test_render_frozen_pile(self):
        """Frozen pile state renders without error."""
        renderer = HTMLRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)
        assert len(result) > 500

    def test_render_red_threes(self):
        """Red threes state renders without error."""
        renderer = HTMLRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)
        assert len(result) > 500

    def test_render_terminal(self):
        """Terminal state renders without error."""
        renderer = HTMLRenderer()
        state = create_terminal_state()
        result = renderer.render(state)
        assert len(result) > 500


class TestHTMLRenderPerspectives:
    """Tests for different perspectives."""

    def test_perspective_0(self):
        """Player 0 perspective renders correctly."""
        renderer = HTMLRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        # Should have card elements
        assert 'class="card' in result

    def test_perspective_1(self):
        """Player 1 perspective renders correctly."""
        renderer = HTMLRenderer(perspective=1)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Player 1" in result

    def test_perspective_2(self):
        """Player 2 perspective renders correctly."""
        renderer = HTMLRenderer(perspective=2)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Player 2" in result

    def test_perspective_3(self):
        """Player 3 perspective renders correctly."""
        renderer = HTMLRenderer(perspective=3)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Player 3" in result


class TestHTMLStandalone:
    """Tests for standalone HTML requirements (AC-12.1, AC-12.2)."""

    def test_no_external_js(self):
        """AC-12.2: No external JavaScript dependencies."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        # Should not have external script references
        assert '<script src=' not in result

    def test_no_external_css(self):
        """AC-12.2: No external CSS dependencies."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        # Should not have external stylesheet links
        assert 'rel="stylesheet"' not in result

    def test_has_title(self):
        """HTML has a title element."""
        renderer = HTMLRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "<title>" in result
        assert "</title>" in result
        assert "Canasta" in result
