"""Unit tests for auth middleware and keyboard builders."""

from __future__ import annotations

import unittest

from teleserver_bot.auth import is_authorized
from teleserver_bot.config import _parse_ids
from teleserver_bot.keyboards import (
    container_actions,
    containers_menu,
    main_menu,
    restart_confirmation,
)


class AuthTests(unittest.TestCase):
    def test_allowed_user(self) -> None:
        self.assertTrue(is_authorized(42, frozenset({1, 42})))

    def test_blocked_user(self) -> None:
        self.assertFalse(is_authorized(7, frozenset({1, 42})))

    def test_none_user(self) -> None:
        self.assertFalse(is_authorized(None, frozenset({1})))

    def test_parse_ids_supports_commas_and_semicolons(self) -> None:
        self.assertEqual(_parse_ids("1, 2;3"), frozenset({1, 2, 3}))

    def test_parse_ids_rejects_garbage(self) -> None:
        with self.assertRaises(ValueError):
            _parse_ids("1,not-a-number")


class KeyboardTests(unittest.TestCase):
    def test_main_menu_has_expected_callbacks(self) -> None:
        markup = main_menu()
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        self.assertIn("menu:status", callbacks)
        self.assertIn("menu:containers", callbacks)
        self.assertIn("menu:refresh", callbacks)

    def test_containers_menu_lists_each_container(self) -> None:
        containers = [
            {"name": "nginx", "state": "running"},
            {"name": "postgres", "state": "exited"},
        ]
        markup = containers_menu(containers)
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        self.assertIn("container:info:nginx", callbacks)
        self.assertIn("container:info:postgres", callbacks)

    def test_empty_containers_menu(self) -> None:
        markup = containers_menu([])
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        self.assertIn("noop", callbacks)

    def test_container_actions(self) -> None:
        markup = container_actions({"name": "redis", "state": "running"})
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        self.assertIn("container:restart:redis", callbacks)

    def test_restart_confirmation(self) -> None:
        markup = restart_confirmation("redis")
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        self.assertIn("container:confirm:redis", callbacks)


if __name__ == "__main__":
    unittest.main()
