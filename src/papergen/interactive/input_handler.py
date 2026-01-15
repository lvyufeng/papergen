"""Input handling with prompt_toolkit for PaperGen CLI."""

from typing import List, Optional
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style


# Custom style for the prompt
PROMPT_STYLE = Style.from_dict({
    'prompt': '#00aa00 bold',
    'input': '#ffffff',
})


from prompt_toolkit.completion import Completer, Completion


class CommandCompleter(Completer):
    """Auto-completer for slash commands."""

    COMMANDS = [
        '/help', '/clear', '/exit', '/quit',
        '/save', '/load', '/history', '/tools'
    ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/'):
            for cmd in self.COMMANDS:
                if cmd.startswith(text):
                    yield Completion(cmd, -len(text))


class InputHandler:
    """Handles user input with prompt_toolkit features."""

    def __init__(self, history_file: Optional[Path] = None):
        """Initialize input handler."""
        self.history_file = history_file or self._get_default_history()
        self.session: Optional[PromptSession] = None

    def _get_default_history(self) -> Path:
        """Get default history file path."""
        home = Path.home()
        history_dir = home / ".papergen"
        history_dir.mkdir(exist_ok=True)
        return history_dir / "chat_history"

    def initialize(self):
        """Initialize the prompt session."""
        self.session = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=CommandCompleter(),
            style=PROMPT_STYLE,
            multiline=False,
        )

    def prompt(self, message: str = "You > ") -> str:
        """Get user input with prompt_toolkit features."""
        if not self.session:
            self.initialize()
        return self.session.prompt(message)

    def prompt_multiline(self, message: str = "You > ") -> str:
        """Get multiline input (Esc+Enter to submit)."""
        if not self.session:
            self.initialize()
        return self.session.prompt(message, multiline=True)
