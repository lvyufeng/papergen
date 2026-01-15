"""Main REPL loop for PaperGen interactive CLI."""

from typing import Optional, List, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live

from .session import Session
from .tools.base import BaseTool, ToolSafety, ToolResult
from .input_handler import InputHandler


class PaperGenREPL:
    """Interactive REPL for paper writing assistance."""

    def __init__(self):
        """Initialize REPL."""
        self.console = Console()
        self.session = Session()
        self.input_handler = InputHandler()
        self.tools: Dict[str, BaseTool] = {}
        self.running = False
        self.provider = "anthropic"

    def register_tool(self, tool: BaseTool):
        """Register a tool."""
        self.tools[tool.name] = tool

    def _load_default_tools(self):
        """Load default tools."""
        from .tools.file_tools import ReadFileTool, WriteFileTool, SearchFilesTool
        from .tools.paper_tools import AnalyzePDFTool, SearchPapersTool

        for tool in [ReadFileTool(), WriteFileTool(), SearchFilesTool(),
                     AnalyzePDFTool(), SearchPapersTool()]:
            self.register_tool(tool)

    def _get_tool_schemas(self) -> List[Dict]:
        """Get schemas for all tools."""
        return [t.get_schema() for t in self.tools.values()]

    def _execute_tool(self, name: str, args: Dict) -> ToolResult:
        """Execute a tool with confirmation if needed."""
        if name not in self.tools:
            return ToolResult(False, "", f"Unknown tool: {name}")

        tool = self.tools[name]

        # Check safety level for hybrid mode
        if tool.safety == ToolSafety.MODERATE:
            if not self._confirm_tool(name, args):
                return ToolResult(False, "User cancelled")

        return tool.execute(**args)

    def _confirm_tool(self, name: str, args: Dict) -> bool:
        """Ask user to confirm tool execution."""
        self.console.print(f"[yellow]Tool: {name}[/yellow]")
        self.console.print(f"[dim]Args: {args}[/dim]")
        response = input("Execute? [y/N]: ").strip().lower()
        return response == 'y'

    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI."""
        return """You are PaperGen, an AI research assistant for academic paper writing.
You help with: literature review, paper analysis, writing, LaTeX editing.
Use tools to read files, search papers, and analyze PDFs.
Be concise and helpful. Focus on research tasks."""

    def _chat(self, user_input: str):
        """Send message and handle streaming response."""
        self.session.add_message("user", user_input)

        try:
            from ..ai.claude_client import ClaudeClient
            client = ClaudeClient()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return

        # Stream response
        self.console.print()
        response_text = ""
        for chunk in client.stream_generate(
            prompt=user_input,
            system=self._get_system_prompt(),
            max_tokens=4096
        ):
            self.console.print(chunk, end="")
            response_text += chunk

        self.console.print("\n")
        self.session.add_message("assistant", response_text)

    def _handle_command(self, cmd: str) -> bool:
        """Handle slash commands. Returns True if handled."""
        if cmd == "/help":
            self._show_help()
            return True
        elif cmd == "/clear":
            self.session.clear()
            self.console.print("[green]Session cleared[/green]")
            return True
        elif cmd == "/exit" or cmd == "/quit":
            self.running = False
            return True
        return False

    def _show_help(self):
        """Show help message."""
        help_text = """
[bold]PaperGen Interactive CLI[/bold]

[cyan]Commands:[/cyan]
  /help   - Show this help
  /clear  - Clear conversation
  /exit   - Exit the CLI

[cyan]Tools:[/cyan]
  - read_file, write_file, search_files
  - analyze_pdf, search_papers
"""
        self.console.print(help_text)

    def run(self):
        """Run the interactive REPL."""
        self._load_default_tools()
        self.input_handler.initialize()
        self.running = True

        self.console.print(Panel(
            "[bold cyan]PaperGen[/bold cyan] - AI Research Assistant",
            subtitle="Type /help for commands | Tab for completion | Up/Down for history"
        ))

        while self.running:
            try:
                user_input = self.input_handler.prompt("\nYou > ").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        continue

                self._chat(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /exit to quit[/dim]")
            except EOFError:
                break

        self.console.print("[dim]Goodbye![/dim]")
