import typer
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns
from rich.text import Text
from copado_hx.config import (
    get_stories, get_story_by_id, set_active_story_id, get_active_story, save_story, get_environments
)
from copado_hx.utils import console, requires_auth, print_success, print_error, print_warning, format_json_output

story_app = typer.Typer(help="📋 Manage Copado user stories and working context")

@story_app.command(name="list", help="List user stories assigned to me.")
@requires_auth
def list_stories(
    pipeline: Optional[str] = typer.Option(None, "--pipeline", "-p", help="Filter stories by Pipeline ID."),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter stories by Status."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Lists all user stories with optional filters."""
    stories = get_stories()
    active_story = get_active_story()
    active_id = active_story["id"] if active_story else None
    
    # Apply filters
    filtered_stories = []
    for s in stories:
        if pipeline and s["pipeline"] != pipeline:
            continue
        if status and s["status"].lower() != status.lower():
            continue
        filtered_stories.append(s)

    if json_output:
        format_json_output(filtered_stories)
        return

    console.print("\n")
    if not filtered_stories:
        console.print(Panel("[warning]No user stories found matching the filters.[/warning]", border_style="yellow"))
        console.print("\n")
        return

    # Render a premium Rich Table
    table = Table(
        title="Copado User Stories", 
        header_style="primary", 
        border_style="muted", 
        expand=True,
        title_style="primary"
    )
    table.add_column("Active", width=8, justify="center")
    table.add_column("ID", style="secondary", width=10)
    table.add_column("Title", style="white", ratio=3)
    table.add_column("Environment", style="info", width=15)
    table.add_column("Status", width=15)
    table.add_column("Commits", justify="right", width=8)
    table.add_column("Metadata Items", justify="right", width=15)

    for s in filtered_stories:
        is_active = "[success]●[/success]" if s["id"] == active_id else ""
        
        # Color code statuses
        status_str = s["status"]
        if status_str == "Promoted":
            status_style = "[bold green]Promoted[/bold green]"
        elif status_str == "In Progress":
            status_style = "[bold cyan]In Progress[/bold cyan]"
        elif status_str == "Draft":
            status_style = "[bold white]Draft[/bold white]"
        else:
            status_style = f"[white]{status_str}[/white]"

        table.add_row(
            is_active,
            s["id"],
            s["title"],
            s["environment"],
            status_style,
            str(len(s.get("commits", []))),
            str(len(s.get("metadata_changes", [])))
        )

    console.print(table)
    if active_id:
        console.print(f"[muted]ℹ Working context is currently locked to User Story [secondary]{active_id}[/secondary].[/muted]\n")
    else:
        console.print("[muted]ℹ No active story context set. Run [primary]copado-hx story set --id <story-id>[/primary] to set one.[/muted]\n")

@story_app.command(name="set", help="Set the current active user story context.")
@requires_auth
def set_story(
    id: str = typer.Option(..., "--id", "-i", help="The User Story ID (e.g. US-1234) to set as context."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Sets the working story context (similar to git checkout)."""
    success = set_active_story_id(id)
    story = get_story_by_id(id)
    
    if not success or not story:
        if json_output:
            format_json_output({"status": "Failed", "error": f"User Story {id} not found."})
        else:
            print_error(f"User Story [bold]{id}[/bold] not found.")
        raise typer.Exit(code=1)

    branch_name = f"dev/{id.lower()}"
    
    if json_output:
        format_json_output({
            "status": "Success",
            "activeStoryId": id,
            "branch": branch_name
        })
    else:
        console.print("\n")
        print_success(f"Working context set to User Story [secondary]{id}[/secondary].")
        console.print(Panel(
            f"📋 [bold]Title:[/bold] {story['title']}\n"
            f"🌿 [bold]Git Branch:[/bold] {branch_name}\n"
            f"🌐 [bold]Environment:[/bold] {story['environment']}\n"
            f"⚡ [bold]Status:[/bold] {story['status']}",
            title="[primary]Story Context Locked[/primary]",
            border_style="cyan",
            expand=False
        ))
        console.print("\n")

@story_app.command(name="show", help="Show current user story details and metadata scope.")
@requires_auth
def show_story(
    story_id: Optional[str] = typer.Argument(None, help="The User Story ID (e.g. US-1234). If omitted, shows active story."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Shows comprehensive details of a user story, including its committed metadata tree and pipeline positioning."""
    target_id = story_id
    if not target_id:
        active = get_active_story()
        if not active:
            if json_output:
                format_json_output({"status": "Error", "message": "No active story context set and no story ID provided."})
            else:
                console.print("\n")
                print_warning("No active story context set. Please provide a story ID or run [primary]copado-hx story set --id <id>[/primary].")
                console.print("\n")
            raise typer.Exit(code=0)
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        if json_output:
            format_json_output({"status": "Error", "message": f"User Story {target_id} not found."})
        else:
            print_error(f"User story {target_id} not found.")
        raise typer.Exit(code=1)

    if json_output:
        format_json_output(story)
        return

    # Visual Presentation using Rich Tree and Panel
    console.print("\n")
    
    # Left column: metadata tree
    tree = Tree(f"[primary]📂 Metadata Scope ({len(story.get('metadata_changes', []))} items)[/primary]")
    
    components = {}
    for item in story.get("metadata_changes", []):
        parts = item.split(":")
        comp_type = parts[0] if len(parts) > 1 else "Unknown"
        comp_name = parts[1] if len(parts) > 1 else parts[0]
        
        if comp_type not in components:
            components[comp_type] = []
        components[comp_type].append(comp_name)

    for comp_type, names in components.items():
        type_node = tree.add(f"[accent]{comp_type}[/accent]")
        for name in names:
            type_node.add(f"[white]{name}[/white]")

    # Right column: pipeline visualization
    pipeline_repr = []
    pipeline_envs = ["DEV-1", "DEV-2", "UAT", "PROD"]
    
    for idx, env in enumerate(pipeline_envs):
        if story["environment"] == env:
            pipeline_repr.append(f"[bold reverse #00D2FF] {env} [/bold reverse #00D2FF]")
        else:
            pipeline_repr.append(f"[muted] {env} [/muted]")
        
        if idx < len(pipeline_envs) - 1:
            pipeline_repr.append("[accent]➔[/accent]")
            
    pipeline_str = " ".join(pipeline_repr)

    info_panel = Panel(
        f"👤 [bold]Developer:[/bold] {story.get('developer', 'N/A')}\n"
        f"🌿 [bold]Feature Branch:[/bold] dev/{story['id'].lower()}\n"
        f"⚡ [bold]Status:[/bold] {story['status']}\n"
        f"🛠  [bold]Pipeline Path:[/bold] {pipeline_str}\n\n"
        f"📝 [bold]Commits Count:[/bold] {len(story.get('commits', []))}",
        title=f"[primary]{story['id']}: {story['title']}[/primary]",
        border_style="purple",
        expand=True
    )
    
    # Output layout
    console.print(Columns([info_panel, tree], equal=True))
    console.print("\n")

@story_app.command(name="create", help="Create a new user story.")
@requires_auth
def create_story(
    title: str = typer.Option(..., "--title", "-t", help="The title of the user story."),
    pipeline: str = typer.Option("PL-101", "--pipeline", "-p", help="The pipeline ID."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Creates a new user story in the local database."""
    stories = get_stories()
    
    # Generate new story ID
    max_id = 1200
    for s in stories:
        try:
            val = int(s["id"].split("-")[1])
            if val > max_id:
                max_id = val
        except Exception:
            pass
    new_id = f"US-{max_id + 1}"
    
    new_story = {
        "id": new_id,
        "title": title,
        "pipeline": pipeline,
        "status": "Draft",
        "environment": "DEV-1",
        "developer": "jayab@copado.demo",
        "metadata_changes": [],
        "commits": []
    }
    
    save_story(new_story)
    
    if json_output:
        format_json_output(new_story)
    else:
        console.print("\n")
        print_success(f"User story [secondary]{new_id}[/secondary] created successfully.")
        console.print(Panel(
            f"📋 [bold]Title:[/bold] {title}\n"
            f"⚡ [bold]Status:[/bold] Draft\n"
            f"🌐 [bold]Environment:[/bold] DEV-1\n"
            f"🛠  [bold]Pipeline ID:[/bold] {pipeline}",
            title="[primary]New Story Created[/primary]",
            border_style="green",
            expand=False
        ))
        console.print("\n")
