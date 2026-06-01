import typer
import time
import uuid
import datetime
import questionary
from typing import List, Optional
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from copado_hx.config import (
    get_active_story, get_story_by_id, save_story, save_deployment, get_deployments
)
from copado_hx.utils import (
    console, requires_auth, print_success, print_error, print_warning, format_json_output
)
from copado_hx.deploy.dashboard import run_live_dashboard

deploy_app = typer.Typer(help="🚀 Manage Copado CI/CD Pipeline and Deployments")

def commit_cmd(
    files: Optional[List[str]] = typer.Argument(None, help="Metadata components to commit (e.g. ApexClass:MyService)."),
    message: Optional[str] = typer.Option(None, "--message", "-m", help="The commit message."),
    us: Optional[str] = typer.Option(None, "--us", "-u", help="User Story ID context. If omitted, uses active story."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Commits metadata changes from the current user story to Git and updates Copado."""
    # Ensure authenticated (manual check because decorators behave differently on top-level commands)
    from copado_hx.config import get_auth
    auth = get_auth()
    if not auth or not auth.get("token"):
        console.print(Panel("[bold red]❌ Access Denied[/bold red]\n\nPlease login first: [primary]copado-hx auth login[/primary]", border_style="red"))
        raise typer.Exit(code=1)

    target_id = us
    if not target_id:
        active = get_active_story()
        if not active:
            if json_output:
                format_json_output({"status": "Error", "message": "No active story context set and no story ID provided."})
            else:
                print_error("No active story context set. Run [primary]copado-hx story set --id <id>[/primary] or pass [primary]--us <id>[/primary].")
            raise typer.Exit(code=1)
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        if json_output:
            format_json_output({"status": "Error", "message": f"User Story {target_id} not found."})
        else:
            print_error(f"User Story {target_id} not found.")
        raise typer.Exit(code=1)

    commit_msg = message or f"update: metadata commit for {target_id}"
    commit_id = f"C-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now().isoformat()

    # Determine what components to commit
    components_to_commit = files or story.get("metadata_changes", [])
    if not components_to_commit:
        if json_output:
            format_json_output({"status": "Warning", "message": "No metadata changes found to commit."})
            return
        else:
            print_warning("No metadata components specified. Generating sample changes...")
            components_to_commit = ["ApexClass:LeadScoringService", "ApexClass:LeadScoringServiceTest"]
            story["metadata_changes"] = components_to_commit

    # Simulate Git commit and Copado mapping
    if not json_output:
        console.print("\n")
        console.print(f"[bold primary]📦 Initiating Copado Metadata Commit ({target_id})[/bold primary]")
        console.print(f"[muted]Message:[/muted] [secondary]\"{commit_msg}\"[/secondary]")
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console
        ) as progress:
            t1 = progress.add_task("[primary]Staging Salesforce metadata...[/primary]", total=100)
            t2 = progress.add_task("[accent]Running local Git diff...[/accent]", total=100)
            t3 = progress.add_task("[secondary]Pushing feature branch to Git...[/secondary]", total=100)
            t4 = progress.add_task("[info]Syncing story metadata scope...[/info]", total=100)
            
            while not progress.finished:
                time.sleep(0.3)
                progress.update(t1, advance=25)
                if progress.tasks[t1].completed >= 100:
                    progress.update(t2, advance=30)
                if progress.tasks[t2].completed >= 100:
                    progress.update(t3, advance=35)
                if progress.tasks[t3].completed >= 100:
                    progress.update(t4, advance=40)

    # Save to JSON DB
    commit_record = {
        "id": commit_id,
        "message": commit_msg,
        "files": components_to_commit,
        "timestamp": timestamp
    }
    story["commits"].append(commit_record)
    story["status"] = "In Progress"
    save_story(story)

    if json_output:
        format_json_output({
            "status": "Completed Successfully",
            "commitId": commit_id,
            "userStory": target_id,
            "message": commit_msg,
            "filesCommitted": components_to_commit
        })
    else:
        console.print("\n")
        print_success(f"Commit [secondary]{commit_id}[/secondary] successfully registered!")
        console.print(Panel(
            f"🌿 [bold]Git Branch:[/bold] dev/{target_id.lower()}\n"
            f"📦 [bold]Committed Items:[/bold] {', '.join(components_to_commit)}\n"
            f"⚡ [bold]User Story Status:[/bold] In Progress",
            title="[success]Commit Tracked in Copado[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

def promote_cmd(
    env: str = typer.Option(..., "--env", "-e", help="The target environment to promote to (e.g. UAT)."),
    us: Optional[str] = typer.Option(None, "--us", "-u", help="The User Story ID. If omitted, uses active story."),
    validate: bool = typer.Option(False, "--validate", help="Trigger a validation-only deployment (no release)."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch live progress in the deployment dashboard."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Promotes a user story to the next pipeline environment."""
    from copado_hx.config import get_auth
    auth = get_auth()
    if not auth or not auth.get("token"):
        console.print(Panel("[bold red]❌ Access Denied[/bold red]\n\nPlease login first: [primary]copado-hx auth login[/primary]", border_style="red"))
        raise typer.Exit(code=1)

    target_id = us
    if not target_id:
        active = get_active_story()
        if not active:
            if json_output:
                format_json_output({"status": "Error", "message": "No active story context set."})
            else:
                print_error("No active story context set. Run [primary]copado-hx story set --id <id>[/primary].")
            raise typer.Exit(code=1)
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        if json_output:
            format_json_output({"status": "Error", "message": f"User Story {target_id} not found."})
        else:
            print_error(f"User Story {target_id} not found.")
        raise typer.Exit(code=1)

    # Error handling for source vs metadata pipeline
    # The Release Agent's commit, promote, and deploy capabilities are only available for Source Format Pipelines.
    # The CLI should handle this gracefully and surface a clear error for Metadata Pipeline users.
    if story["pipeline"] == "PL-METADATA":
        if json_output:
            format_json_output({
                "status": "Failed",
                "error_code": "PIPELINE_NOT_SUPPORTED",
                "error": "The promote capability is only available for Source Format Pipelines. Metadata Pipeline users must promote via the UI."
            })
        else:
            console.print("\n")
            print_error("The promote capability is only available for Source Format Pipelines.")
            console.print(Panel(
                "[bold yellow]Metadata Pipeline Limitation[/bold yellow]\n\n"
                "The promotion requested for user story [secondary]US-1234[/secondary] belongs to a Salesforce Metadata Pipeline.\n"
                "To promote this story, please log into Copado's web app or transition to a [bold green]Source Format Pipeline[/bold green].",
                title="[error]Feature Unavailable[/error]",
                border_style="red",
                expand=False
            ))
            console.print("\n")
        raise typer.Exit(code=1)

    promotion_id = f"PR-{uuid.uuid4().hex[:6].upper()}"
    job_exec_id = f"JOB-EXEC-8083{int(time.time()) % 1000}"

    # Log deployment execution details
    deploy_record = {
        "id": promotion_id,
        "user_story": target_id,
        "environment": env,
        "type": "Validation" if validate else "Promotion",
        "status": "Completed Successfully",
        "job_execution_id": job_exec_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    save_deployment(deploy_record)

    if watch and not json_output:
        # Launch beautiful live-updating fullscreen dashboard
        run_live_dashboard(target_id, env, is_validation=validate)
        return

    # Non-watch mode (simulates short CLI API response)
    if not json_output:
        console.print("\n")
        action = "Validation" if validate else "Promotion"
        with console.status(f"[bold primary]Triggering {action} to {env}...[/bold primary]", spinner="aesthetic"):
            time.sleep(2.0)

    # Set story status to Promoted if it was a real promotion to UAT or PROD
    if not validate:
        story["environment"] = env
        if env == "PROD":
            story["status"] = "Promoted"
        else:
            story["status"] = "Ready for Test"
        save_story(story)

    if json_output:
        format_json_output({
            "status": "Completed Successfully",
            "promotionId": promotion_id,
            "jobExecutionId": job_exec_id,
            "targetEnvironment": env,
            "type": "Validation" if validate else "Promotion"
        })
    else:
        console.print("\n")
        print_success(f"Promotion trigger complete!")
        console.print(Panel(
            f"🔑 [bold]Promotion ID:[/bold] {promotion_id}\n"
            f"🌐 [bold]Target Environment:[/bold] {env}\n"
            f"⚡ [bold]Job Execution ID:[/bold] {job_exec_id}\n"
            f"📝 [bold]Type:[/bold] {'Validation-Only' if validate else 'Full Promotion'}\n"
            f"ℹ  To monitor live logs, run: [secondary]copado-hx status --watch[/secondary]",
            title="[success]Copado Job Created[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

def deploy_cmd(
    env: str = typer.Option(..., "--env", "-e", help="The destination environment (e.g. PROD)."),
    us: Optional[str] = typer.Option(None, "--us", "-u", help="The User Story ID. If omitted, uses active story."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Watch live progress in the deployment dashboard."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Executes a deployment. Requires manual confirmation for Production orgs."""
    from copado_hx.config import get_auth
    auth = get_auth()
    if not auth or not auth.get("token"):
        console.print(Panel("[bold red]❌ Access Denied[/bold red]\n\nPlease login first: [primary]copado-hx auth login[/primary]", border_style="red"))
        raise typer.Exit(code=1)

    target_id = us
    if not target_id:
        active = get_active_story()
        if not active:
            if json_output:
                format_json_output({"status": "Error", "message": "No active story context set."})
            else:
                print_error("No active story context set.")
            raise typer.Exit(code=1)
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        if json_output:
            format_json_output({"status": "Error", "message": f"User story {target_id} not found."})
        else:
            print_error(f"User Story {target_id} not found.")
        raise typer.Exit(code=1)

    # Production gate approval guardrail
    if env.upper() in ["PROD", "PRODUCTION"]:
        if not json_output:
            console.print("\n")
            console.print(Panel(
                "[bold accent]🚫 PROD Deployment Safety Gate[/bold accent]\n\n"
                "You are attempting to deploy changes directly to the [bold red]Production Org[/bold red].\n"
                "This action bypassing automated sandbox staging requires manual validation.",
                title="[accent]Approval Gate Blocked[/accent]",
                border_style="yellow",
                expand=False
            ))
            
            # Interactive prompt for approval
            confirm = questionary.confirm("Are you sure you want to deploy this changes to Production?").ask()
            if not confirm:
                print_error("Deployment aborted by user.")
                raise typer.Exit(code=0)
        else:
            # Under JSON mode, if it's PROD, error out if approval is not provided (or assume require interactive)
            format_json_output({
                "status": "Failed",
                "error": "Deployments to Production environments require human confirmation. Run interactively to confirm."
            })
            raise typer.Exit(code=1)

    promotion_id = f"DP-{uuid.uuid4().hex[:6].upper()}"
    job_exec_id = f"JOB-EXEC-8083{int(time.time()) % 1000}"

    deploy_record = {
        "id": promotion_id,
        "user_story": target_id,
        "environment": env,
        "type": "Deployment",
        "status": "Completed Successfully",
        "job_execution_id": job_exec_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    save_deployment(deploy_record)

    if watch and not json_output:
        run_live_dashboard(target_id, env, is_validation=False)
        return

    if not json_output:
        console.print("\n")
        with console.status(f"[bold accent]Deploying to {env} Sandbox...[/bold accent]", spinner="aesthetic"):
            time.sleep(2.0)

    # Update story
    story["environment"] = env
    story["status"] = "Promoted"
    save_story(story)

    if json_output:
        format_json_output({
            "status": "Completed Successfully",
            "deploymentId": promotion_id,
            "jobExecutionId": job_exec_id,
            "targetEnvironment": env
        })
    else:
        console.print("\n")
        print_success(f"Deployment to {env} was successful!")
        console.print("\n")

def status_cmd(
    watch: bool = typer.Option(False, "--watch", "-w", help="Open the live-updating deployment dashboard."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Displays pipeline deployment status or watches live progress."""
    from copado_hx.config import get_auth
    auth = get_auth()
    if not auth or not auth.get("token"):
        console.print(Panel("[bold red]❌ Access Denied[/bold red]\n\nPlease login first: [primary]copado-hx auth login[/primary]", border_style="red"))
        raise typer.Exit(code=1)

    if watch and not json_output:
        active = get_active_story()
        story_id = active["id"] if active else "US-1234"
        run_live_dashboard(story_id, "UAT", is_validation=False)
        return

    deployments = get_deployments()

    # Pre-seed some history if empty
    if not deployments:
        deployments = [
            {
                "id": "DP-AA928B",
                "user_story": "US-1236",
                "environment": "UAT",
                "type": "Promotion",
                "status": "Completed Successfully",
                "job_execution_id": "JOB-EXEC-80811",
                "timestamp": "2026-05-30T10:15:22"
            },
            {
                "id": "DP-B1102A",
                "user_story": "US-1234",
                "environment": "UAT",
                "type": "Validation",
                "status": "Completed Successfully",
                "job_execution_id": "JOB-EXEC-80829",
                "timestamp": "2026-05-31T14:22:10"
            }
        ]

    if json_output:
        format_json_output(deployments)
        return

    console.print("\n")
    table = Table(
        title="Copado Recent Deployments & Job Executions",
        header_style="primary",
        border_style="muted",
        expand=True,
        title_style="primary"
    )
    table.add_column("Date/Time", style="muted", width=22)
    table.add_column("Job Exec ID", style="secondary", width=18)
    table.add_column("User Story", style="info", width=12)
    table.add_column("Target Env", style="white", width=12)
    table.add_column("Type", style="accent", width=12)
    table.add_column("Status", width=25)

    for dep in deployments:
        # Style status
        status_str = dep["status"]
        if "Success" in status_str:
            status_style = "[bold green]Completed Successfully[/bold green]"
        elif "Failed" in status_str:
            status_style = "[bold red]Failed[/bold red]"
        else:
            status_style = f"[bold yellow]{status_str}[/bold yellow]"

        table.add_row(
            dep["timestamp"][:19].replace("T", " "),
            dep["job_execution_id"],
            dep["user_story"],
            dep["environment"],
            dep["type"],
            status_style
        )

    console.print(table)
    console.print("[muted]ℹ To view real-time pipeline telemetry, run [primary]copado-hx status --watch[/primary].[/muted]\n")
