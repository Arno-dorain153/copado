import json
import sys
from functools import wraps
from typing import Any

# Safeguard Windows terminal encoding to support emojis/UTF-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
import typer
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
from copado_hx.config import get_auth

# Modern, harmonious color palette
COPADO_THEME = Theme({
    "info": "cyan",
    "warning": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "primary": "bold #6F32FF",       # Vibrant purple
    "secondary": "bold #00D2FF",     # Cool cyan
    "accent": "bold #FF007F",        # Neon pink
    "muted": "#7A7A7A"
})

console = Console(theme=COPADO_THEME)

def print_banner():
    """Prints a beautiful, modern banner for the CLI."""
    banner_text = """
 [primary]██████╗  ██████╗ ██████╗  █████╗ ██████╗  ██████╗     ██╗  ██╗██╗  ██╗[/primary]
[primary]██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██╔═══██╗    ██║  ██║╚██╗██╔╝[/primary]
[primary]██║      ██║   ██║██████╔╝███████║██║  ██║██║   ██║    ███████║ ╚███╔╝ [/primary]
[primary]██║      ██║   ██║██╔═══╝ ██╔══██║██║  ██║██║   ██║    ██╔══██║ ██╔██╗ [/primary]
[primary]╚██████╗ ╚██████╔╝██║     ██║  ██║██████╔╝╚██████╔╝    ██║  ██║██╔╝ ██╗[/primary]
 [primary]╚══════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═════╝  ╚═════╝     ╚═╝  ╚═╝╚═╝  ╚═╝[/primary]
                    [secondary]» The Headless DevOps Experience «[/secondary]
    """
    console.print(banner_text)

def requires_auth(f):
    """Decorator to ensure commands require an authenticated session."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = get_auth()
        if not auth or not auth.get("token"):
            console.print("\n")
            console.print(Panel(
                "[bold red]❌ Authentication Required[/bold red]\n\n"
                "You must be authenticated to run this command.\n"
                "Please run [primary]copado-hx auth login[/primary] to authenticate.",
                title="[error]Access Denied[/error]",
                border_style="red"
            ))
            console.print("\n")
            raise typer.Exit(code=1)
        return f(*args, **kwargs)
    return wrapper

def format_json_output(data: Any):
    """Outputs the given data as pretty-printed JSON to stdout."""
    print(json.dumps(data, indent=2))

def print_success(message: str):
    """Prints a styled success message."""
    console.print(f"[success]✔[/success] {message}")

def print_error(message: str):
    """Prints a styled error message."""
    console.print(f"[error]✖ Error:[/error] {message}")

def print_warning(message: str):
    """Prints a styled warning message."""
    console.print(f"[warning]⚠ Warning:[/warning] {message}")
