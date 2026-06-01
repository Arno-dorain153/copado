import typer
import time
import questionary
from typing import Optional
from rich.panel import Panel
from rich.table import Table
from copado_hx.config import save_auth, get_auth
from copado_hx.utils import console, print_success, print_error, format_json_output

auth_app = typer.Typer(help="🔐 Authenticate with Copado DevOps Platform")

@auth_app.command(name="login", help="Authenticate with the Copado API.")
def login(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="API token for automated environments (CI)."
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u", help="Username for login."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results in machine-readable JSON format."
    )
):
    """Logs into the Copado DevOps platform."""
    if not token:
        # Interactive mode using questionary
        if not json_output:
            console.print("\n[primary]🔑 Interactive Copado Authentication[/primary]\n")
        
        user = username or questionary.text("Enter your Copado Username:").ask()
        if not user:
            print_error("Username is required.")
            raise typer.Exit(code=1)
            
        api_token = questionary.password("Enter your Copado API Personal Access Key:").ask()
        if not api_token:
            print_error("API Personal Access Key is required.")
            raise typer.Exit(code=1)
    else:
        # Token provided directly
        user = username or "ci-agent@copado.com"
        api_token = token

    # Simulation of API handshakes
    if not json_output:
        with console.status("[bold #6F32FF]Connecting to Copado Cloud API...[/bold #6F32FF]", spinner="aesthetic"):
            time.sleep(1.5)
            
    # Success scenario simulation
    org_id = "00D80000000hKuaEAE"
    env_name = "Dev Sandbox 1 (DEV-1)"
    
    save_auth(username=user, token=api_token, org_id=org_id, environment=env_name)
    
    if json_output:
        format_json_output({
            "status": "Authenticated",
            "username": user,
            "orgId": org_id,
            "environment": env_name
        })
    else:
        console.print("\n")
        print_success(f"Successfully authenticated as [secondary]{user}[/secondary]!")
        console.print(Panel(
            f"[bold green]Session Established[/bold green]\n\n"
            f"👤 [bold]User:[/bold] {user}\n"
            f"🏢 [bold]Org ID:[/bold] {org_id}\n"
            f"🌐 [bold]Default Environment:[/bold] {env_name}\n"
            f"🔑 [bold]Token:[/bold] {'*' * 12}{api_token[-4:] if len(api_token) > 4 else ''}",
            title="[primary]Copado Connection Details[/primary]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

@auth_app.command(name="logout", help="Log out and clear active session.")
def logout(
    json_output: bool = typer.Option(
        False, "--json", help="Output results in machine-readable JSON format."
    )
):
    """Clears authentication details from the local configuration."""
    save_auth(None, None, None, None)
    
    if json_output:
        format_json_output({"status": "Logged Out", "message": "Session credentials cleared."})
    else:
        print_success("Successfully logged out. All credentials cleared.")

@auth_app.command(name="status", help="Show current authentication status.")
def status(
    json_output: bool = typer.Option(
        False, "--json", help="Output results in machine-readable JSON format."
    )
):
    """Checks the local config and prints connection status."""
    auth = get_auth()
    
    if not auth or not auth.get("token"):
        if json_output:
            format_json_output({"status": "Unauthenticated"})
        else:
            console.print("\n")
            console.print(Panel(
                "[bold yellow]⚠ Session Inactive[/bold yellow]\n\n"
                "You are currently [bold red]not logged in[/bold red] to Copado.\n"
                "Run [primary]copado-hx auth login[/primary] to establish a connection.",
                title="[warning]Auth Status[/warning]",
                border_style="yellow",
                expand=False
            ))
            console.print("\n")
        raise typer.Exit(code=0)

    if json_output:
        format_json_output({
            "status": "Authenticated",
            "username": auth["username"],
            "orgId": auth["org_id"],
            "environment": auth["environment"]
        })
    else:
        console.print("\n")
        table = Table(title="Copado CLI Authentication", show_header=False, border_style="cyan")
        table.add_column("Property", style="primary")
        table.add_column("Value", style="secondary")
        
        table.add_row("Connection Status", "[bold green]Online / Connected[/bold green]")
        table.add_row("Active User", auth["username"])
        table.add_row("Salesforce Org ID", auth["org_id"])
        table.add_row("Target Pipeline Org", auth["environment"])
        
        console.print(Panel(
            table,
            title="[success]✔ Authentication Status[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")
