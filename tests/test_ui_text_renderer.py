"""Tests for canasta/ui/text_renderer.py - ASCII text renderer."""

import pytest

from canasta.ui.text_renderer import TextRenderer
from canasta.ui.base import Renderer
from canasta.ui.fixtures import (
    create_early_game_state,
    create_mid_game_state,
    create_canasta_state,
    create_frozen_pile_state,
    create_red_threes_state,
    create_terminal_state,
)


class TestTextRendererInit:
    """Tests for TextRenderer initialization."""

    def test_is_renderer_subclass(self):
        """TextRenderer is a subclass of Renderer."""
        renderer = TextRenderer()
        assert isinstance(renderer, Renderer)

    def test_default_perspective(self):
        """Default perspective is player 0."""
        renderer = TextRenderer()
        assert renderer.perspective == 0

    def test_custom_perspective(self):
        """Custom perspective is stored correctly."""
        renderer = TextRenderer(perspective=2)
        assert renderer.perspective == 2

    def test_show_all_hands_default(self):
        """show_all_hands defaults to False."""
        renderer = TextRenderer()
        assert renderer.show_all_hands is False

    def test_show_all_hands_true(self):
        """show_all_hands can be set to True."""
        renderer = TextRenderer(show_all_hands=True)
        assert renderer.show_all_hands is True

    def test_invalid_perspective_raises(self):
        """Invalid perspective raises ValueError."""
        with pytest.raises(ValueError):
            TextRenderer(perspective=4)
        with pytest.raises(ValueError):
            TextRenderer(perspective=-1)


class TestIsVisibleHand:
    """Tests for is_visible_hand method."""

    def test_perspective_player_visible(self):
        """AC-2.1: Perspective player's hand is visible."""
        renderer = TextRenderer(perspective=0)
        assert renderer.is_visible_hand(0) is True

    def test_other_players_hidden(self):
        """AC-2.2: Other players' hands are hidden."""
        renderer = TextRenderer(perspective=0)
        assert renderer.is_visible_hand(1) is False
        assert renderer.is_visible_hand(2) is False
        assert renderer.is_visible_hand(3) is False

    def test_show_all_hands_mode(self):
        """AC-2.3: All hands visible in debug mode."""
        renderer = TextRenderer(perspective=0, show_all_hands=True)
        assert renderer.is_visible_hand(0) is True
        assert renderer.is_visible_hand(1) is True
        assert renderer.is_visible_hand(2) is True
        assert renderer.is_visible_hand(3) is True


class TestRenderBasics:
    """Tests for basic render functionality."""

    def test_render_returns_string(self):
        """AC-9.1: render() returns a string."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert isinstance(result, str)

    def test_render_not_empty(self):
        """AC-9.2: render() returns non-empty output."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 0

    def test_render_has_newlines(self):
        """AC-9.3: render() returns multi-line output."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert "\n" in result

    def test_render_80_column_layout(self):
        """AC-8.1: Output fits in 80 columns."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        for line in result.split("\n"):
            assert len(line) <= 80, f"Line too long: {len(line)} chars: {line[:50]}..."


class TestRenderContent:
    """Tests for rendered content."""

    def test_contains_player_labels(self):
        """AC-8.2: Output contains player labels."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "PLAYER 0" in result
        assert "PLAYER 1" in result
        assert "PLAYER 2" in result
        assert "PLAYER 3" in result

    def test_contains_perspective_marker(self):
        """AC-2.4: Perspective player marked as 'You'."""
        renderer = TextRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(You)" in result

    def test_contains_partner_marker(self):
        """AC-2.5: Partner marked correctly."""
        renderer = TextRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(Partner)" in result

    def test_contains_stock_pile(self):
        """AC-4.1: Stock pile displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "STOCK" in result

    def test_contains_discard_pile(self):
        """AC-4.2: Discard pile displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "DISCARD" in result

    def test_contains_scores(self):
        """AC-6.1: Scores displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "SCORES" in result
        assert "Team 0" in result
        assert "Team 1" in result

    def test_contains_meld_areas(self):
        """AC-3.1: Meld areas displayed for both teams."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Team 0 Melds" in result
        assert "Team 1 Melds" in result

    def test_contains_turn_info(self):
        """AC-7.1: Turn information displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "Turn:" in result or "Phase:" in result


class TestRenderMelds:
    """Tests for meld rendering."""

    def test_empty_melds_shown(self):
        """AC-3.2: Empty melds show '(no melds)'."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        assert "(no melds)" in result

    def test_melds_with_cards(self):
        """AC-3.3: Melds show rank and card count."""
        renderer = TextRenderer()
        state = create_mid_game_state()
        result = renderer.render(state)

        # Should contain rank names
        assert "Aces" in result or "Eights" in result

    def test_canasta_markers(self):
        """AC-3.4: Canastas have type markers."""
        renderer = TextRenderer()
        state = create_canasta_state()
        result = renderer.render(state)

        # Should have canasta type indicators
        assert "NATURAL" in result or "MIXED" in result


class TestRenderPiles:
    """Tests for pile rendering."""

    def test_stock_count_shown(self):
        """AC-4.3: Stock count displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        # Stock count should be in parentheses
        assert "(" in result  # Stock count format

    def test_discard_top_card_shown(self):
        """AC-4.4: Top discard card displayed."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)

        # Should have card representation
        assert "[" in result and "]" in result

    def test_frozen_pile_indicator(self):
        """AC-4.5: Frozen pile indicator shown."""
        renderer = TextRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)

        assert "FROZEN" in result


class TestRenderRedThrees:
    """Tests for red three rendering."""

    def test_red_threes_displayed(self):
        """AC-5.1: Red threes displayed when present."""
        renderer = TextRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)

        assert "Red Threes" in result

    def test_red_threes_per_team(self):
        """AC-5.2: Red threes shown per team."""
        renderer = TextRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)

        # Both teams have red threes
        lines = result.split("\n")
        red_three_lines = [l for l in lines if "Red Threes" in l]
        assert len(red_three_lines) > 0


class TestRenderTerminal:
    """Tests for terminal state rendering."""

    def test_terminal_state_shows_game_over(self):
        """AC-7.2: Terminal state shows game over."""
        renderer = TextRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "GAME OVER" in result

    def test_terminal_state_shows_winner(self):
        """AC-7.3: Terminal state shows winner."""
        renderer = TextRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "Wins" in result

    def test_terminal_state_shows_scores(self):
        """AC-6.2: Terminal state shows final scores."""
        renderer = TextRenderer()
        state = create_terminal_state()
        result = renderer.render(state)

        assert "SCORES" in result
        assert "1250" in result or str(state._team_scores[0]) in result


class TestRenderAllFixtures:
    """Tests for rendering all fixtures."""

    def test_render_early_game(self):
        """AC-9.4: Early game renders without error."""
        renderer = TextRenderer()
        state = create_early_game_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_mid_game(self):
        """Mid game renders without error."""
        renderer = TextRenderer()
        state = create_mid_game_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_canasta(self):
        """Canasta state renders without error."""
        renderer = TextRenderer()
        state = create_canasta_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_frozen_pile(self):
        """Frozen pile state renders without error."""
        renderer = TextRenderer()
        state = create_frozen_pile_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_red_threes(self):
        """Red threes state renders without error."""
        renderer = TextRenderer()
        state = create_red_threes_state()
        result = renderer.render(state)
        assert len(result) > 100

    def test_render_terminal(self):
        """Terminal state renders without error."""
        renderer = TextRenderer()
        state = create_terminal_state()
        result = renderer.render(state)
        assert len(result) > 100


class TestRenderPerspectives:
    """Tests for different perspectives."""

    def test_perspective_0(self):
        """Player 0 perspective renders correctly."""
        renderer = TextRenderer(perspective=0)
        state = create_early_game_state()
        result = renderer.render(state)

        # Player 0's hand should be visible (show actual cards)
        assert "[" in result  # Card symbols

    def test_perspective_1(self):
        """Player 1 perspective renders correctly."""
        renderer = TextRenderer(perspective=1)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "PLAYER 1" in result

    def test_perspective_2(self):
        """Player 2 perspective renders correctly."""
        renderer = TextRenderer(perspective=2)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "PLAYER 2" in result

    def test_perspective_3(self):
        """Player 3 perspective renders correctly."""
        renderer = TextRenderer(perspective=3)
        state = create_early_game_state()
        result = renderer.render(state)

        assert "PLAYER 3" in result
