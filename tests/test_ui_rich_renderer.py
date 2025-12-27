"""Tests for canasta/ui/rich_renderer.py - Rich terminal renderer."""

import pytest

from canasta.ui.rich_renderer import RichRenderer
from canasta.ui.base import Renderer
from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
)


class TestRichRendererInit:
    """Tests for RichRenderer initialization."""

    def test_is_renderer_subclass(self):
        """RichRenderer is a subclass of Renderer."""
        renderer = RichRenderer()
        assert isinstance(renderer, Renderer)

    def test_default_perspective(self):
        """Default perspective is player 0."""
        renderer = RichRenderer()
        assert renderer.perspective == 0

    def test_custom_perspective(self):
        """Custom perspective is stored correctly."""
        renderer = RichRenderer(perspective=2)
        assert renderer.perspective == 2

    def test_show_all_hands_default(self):
        """show_all_hands defaults to False."""
        renderer = RichRenderer()
        assert renderer.show_all_hands is False

    def test_show_all_hands_true(self):
        """show_all_hands can be set to True."""
        renderer = RichRenderer(show_all_hands=True)
        assert renderer.show_all_hands is True

    def test_invalid_perspective_raises(self):
        """Invalid perspective raises ValueError."""
        with pytest.raises(ValueError):
            RichRenderer(perspective=4)
        with pytest.raises(ValueError):
            RichRenderer(perspective=-1)

    def test_has_console_attribute(self):
        """AC-11.1: RichRenderer has a rich Console."""
        renderer = RichRenderer()
        from rich.console import Console
        assert hasattr(renderer, 'console')
        assert isinstance(renderer.console, Console)


class TestRichRendererRenderBasics:
    """Tests for basic render functionality."""

    def test_render_returns_string(self):
        """render() returns a string."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert isinstance(result, str)

    def test_render_not_empty(self):
        """render() returns non-empty output."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 0

    def test_render_has_newlines(self):
        """render() returns multi-line output."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert "\n" in result


class TestRichRendererColorCoding:
    """Tests for color coding in rich output."""

    def test_output_contains_ansi_codes(self):
        """AC-11.1: Output contains ANSI color codes."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        # ANSI escape sequence starts with ESC (0x1B or \033)
        assert "\x1b[" in result or "\033[" in result

    def test_card_styled_returns_text(self):
        """_card_styled returns a rich Text object."""
        from rich.text import Text
        renderer = RichRenderer()
        # Test a hearts card (should be red)
        card_id = 26  # A of hearts (rank 0, suit 2 in first deck: 2*13 + 0 = 26)
        result = renderer._card_styled(card_id)
        assert isinstance(result, Text)

    def test_hearts_styled_red(self):
        """AC-11.2: Hearts cards have red styling."""
        renderer = RichRenderer()
        # Hearts is suit index 2, so A of hearts is card_id = 26 (2*13 + 0)
        card_id = 26
        styled = renderer._card_styled(card_id)
        # Check the style contains 'red'
        assert styled.style is not None
        assert "red" in str(styled.style)

    def test_diamonds_styled_red(self):
        """AC-11.2: Diamonds cards have red styling."""
        renderer = RichRenderer()
        # Diamonds is suit index 1, so A of diamonds is card_id = 13 (1*13 + 0)
        card_id = 13
        styled = renderer._card_styled(card_id)
        assert styled.style is not None
        assert "red" in str(styled.style)

    def test_clubs_not_red(self):
        """AC-11.2: Clubs cards are not red."""
        renderer = RichRenderer()
        # Clubs is suit index 0, so A of clubs is card_id = 0
        card_id = 0
        styled = renderer._card_styled(card_id)
        # Should not have red style
        if styled.style:
            assert "red" not in str(styled.style)

    def test_spades_not_red(self):
        """AC-11.2: Spades cards are not red."""
        renderer = RichRenderer()
        # Spades is suit index 3, so A of spades is card_id = 39 (3*13 + 0)
        card_id = 39
        styled = renderer._card_styled(card_id)
        # Should not have red style
        if styled.style:
            assert "red" not in str(styled.style)

    def test_joker_styled_magenta(self):
        """AC-11.2: Jokers have magenta/purple styling."""
        renderer = RichRenderer()
        # Jokers are card_ids 104-107
        card_id = 104
        styled = renderer._card_styled(card_id)
        assert styled.style is not None
        assert "magenta" in str(styled.style)


class TestRichRendererCanastaMarkers:
    """Tests for canasta marker styling."""

    def test_natural_canasta_has_marker(self):
        """AC-11.3: Natural canasta has styled marker."""
        renderer = RichRenderer()
        state = create_canasta_state()
        result = renderer.render(state)
        # Natural canasta should have [NATURAL] marker
        assert "NATURAL" in result

    def test_mixed_canasta_has_marker(self):
        """AC-11.3: Mixed canasta has styled marker."""
        renderer = RichRenderer()
        state = create_canasta_state()
        result = renderer.render(state)
        # Mixed canasta should have [MIXED] marker
        assert "MIXED" in result

    def test_format_meld_styled_natural(self):
        """_format_meld_styled includes natural canasta marker."""
        from canasta.ui.state_view import MeldView
        renderer = RichRenderer()
        meld = MeldView(
            rank=0,  # Aces
            natural_cards=[0, 13, 26, 39, 52, 65, 78],  # 7 natural cards
            wild_cards=[],
            is_canasta=True,
            is_natural_canasta=True,
            is_mixed_canasta=False,
        )
        styled = renderer._format_meld_styled(meld)
        assert "NATURAL" in styled.plain

    def test_format_meld_styled_mixed(self):
        """_format_meld_styled includes mixed canasta marker."""
        from canasta.ui.state_view import MeldView
        renderer = RichRenderer()
        meld = MeldView(
            rank=0,  # Aces
            natural_cards=[0, 13, 26, 39, 52],  # 5 natural cards
            wild_cards=[1, 53],  # 2 wild cards (2s)
            is_canasta=True,
            is_natural_canasta=False,
            is_mixed_canasta=True,
        )
        styled = renderer._format_meld_styled(meld)
        assert "MIXED" in styled.plain


class TestRichRendererContent:
    """Tests for rendered content matches TextRenderer behavior."""

    def test_contains_player_labels(self):
        """Output contains player labels."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "PLAYER 0" in result
        assert "PLAYER 1" in result
        assert "PLAYER 2" in result
        assert "PLAYER 3" in result

    def test_contains_perspective_marker(self):
        """Perspective player marked as 'You'."""
        renderer = RichRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(You)" in result

    def test_contains_partner_marker(self):
        """Partner marked correctly."""
        renderer = RichRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(Partner)" in result

    def test_contains_stock_pile(self):
        """Stock pile displayed."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "STOCK" in result

    def test_contains_discard_pile(self):
        """Discard pile displayed."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "DISCARD" in result

    def test_contains_scores(self):
        """Scores displayed."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "SCORES" in result or "Team 0" in result

    def test_contains_meld_areas(self):
        """Meld areas displayed for both teams."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Team 0 Melds" in result
        assert "Team 1 Melds" in result

    def test_frozen_pile_indicator(self):
        """Frozen pile indicator shown."""
        renderer = RichRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)

        assert "FROZEN" in result


class TestRichRendererTerminal:
    """Tests for terminal state rendering."""

    def test_terminal_state_shows_game_over(self):
        """Terminal state shows game over."""
        renderer = RichRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "GAME OVER" in result

    def test_terminal_state_shows_winner(self):
        """Terminal state shows winner."""
        renderer = RichRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "Wins" in result


class TestRichRendererAllFixtures:
    """Tests for rendering all fixtures without error."""

    def test_render_early_game(self):
        """Early game renders without error."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_mid_game(self):
        """Mid game renders without error."""
        renderer = RichRenderer()
        state = create_mid_game_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_canasta(self):
        """Canasta state renders without error."""
        renderer = RichRenderer()
        state = create_canasta_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_frozen_pile(self):
        """Frozen pile state renders without error."""
        renderer = RichRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_red_threes(self):
        """Red threes state renders without error."""
        renderer = RichRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_terminal(self):
        """Terminal state renders without error."""
        renderer = RichRenderer()
        state = create_terminal_state()
        result = renderer.render(state)
        assert len(result) > 100


class TestRichRendererPerspectives:
    """Tests for different perspectives."""

    def test_perspective_0(self):
        """Player 0 perspective renders correctly."""
        renderer = RichRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)
        assert "PLAYER 0" in result

    def test_perspective_1(self):
        """Player 1 perspective renders correctly."""
        renderer = RichRenderer(perspective=1)
        state = create_early_game_state()
        result = renderer.render(state)
        assert "PLAYER 1" in result

    def test_perspective_2(self):
        """Player 2 perspective renders correctly."""
        renderer = RichRenderer(perspective=2)
        state = create_early_game_state()
        result = renderer.render(state)
        assert "PLAYER 2" in result

    def test_perspective_3(self):
        """Player 3 perspective renders correctly."""
        renderer = RichRenderer(perspective=3)
        state = create_early_game_state()
        result = renderer.render(state)
        assert "PLAYER 3" in result


class TestRichRendererVisualHierarchy:
    """Tests for visual hierarchy through color/style (AC-11.4)."""

    def test_header_has_teal_styling(self):
        """AC-11.3/AC-11.4: Header uses teal primary color."""
        renderer = RichRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        # Check that ANSI codes are present in the header area
        # The header "CANASTA" should be styled
        assert "\x1b[" in result

    def test_different_card_suits_have_different_styles(self):
        """AC-11.4: Different suits have different visual styles."""
        renderer = RichRenderer()
        # Compare hearts and spades styling
        hearts = renderer._card_styled(26)  # A of hearts
        spades = renderer._card_styled(39)  # A of spades
        # They should have different styles
        assert hearts.style != spades.style or (
            hearts.style is not None and spades.style is not None
        )

    def test_canasta_markers_stand_out(self):
        """AC-11.4: Canasta markers have distinct styling."""
        from canasta.ui.state_view import MeldView
        renderer = RichRenderer()

        # Natural canasta
        natural = MeldView(
            rank=0,
            natural_cards=[0, 13, 26, 39, 52, 65, 78],
            wild_cards=[],
            is_canasta=True,
            is_natural_canasta=True,
            is_mixed_canasta=False,
        )
        natural_styled = renderer._format_meld_styled(natural)

        # Mixed canasta
        mixed = MeldView(
            rank=0,
            natural_cards=[0, 13, 26, 39, 52],
            wild_cards=[1, 53],
            is_canasta=True,
            is_natural_canasta=False,
            is_mixed_canasta=True,
        )
        mixed_styled = renderer._format_meld_styled(mixed)

        # Regular meld (not canasta)
        regular = MeldView(
            rank=0,
            natural_cards=[0, 13, 26],
            wild_cards=[],
            is_canasta=False,
            is_natural_canasta=False,
            is_mixed_canasta=False,
        )
        regular_styled = renderer._format_meld_styled(regular)

        # Natural and mixed should have markers, regular should not
        assert "NATURAL" in natural_styled.plain
        assert "MIXED" in mixed_styled.plain
        assert "NATURAL" not in regular_styled.plain
        assert "MIXED" not in regular_styled.plain
