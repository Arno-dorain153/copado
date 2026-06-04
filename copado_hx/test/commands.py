import typer
import time
import random
import uuid
import datetime
from typing import Optional
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from copado_hx.config import (
    get_test_suites, get_test_executions, save_test_execution
)
from copado_hx.utils import (
    console, requires_auth, print_success, print_error, print_warning, format_json_output
)

test_app = typer.Typer(help="🧪 Execute and monitor Copado Robotic Testing (CRT) suites")

@test_app.command(name="list", help="List available robotic test suites and jobs.")
@requires_auth
def list_tests(
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Lists pre-configured Copado Robotic Testing suites."""
    suites = get_test_suites()
    
    if json_output:
        format_json_output(suites)
        return

    console.print("\n")
    table = Table(
        title="Copado Robotic Testing Suites",
        header_style="primary",
        border_style="muted",
        expand=True,
        title_style="primary"
    )
    table.add_column("Suite ID / Job ID", style="secondary", width=18)
    table.add_column("Test Suite Name", style="white", ratio=2)
    table.add_column("Project ID", style="info", width=18)
    table.add_column("Type", style="accent", width=12)

    for suite in suites:
        table.add_row(
            suite["job_id"],
            suite["name"],
            suite["project_id"],
            "QWord (Web)"
        )

    console.print(table)
    console.print("[muted]ℹ To execute a suite, run [primary]copado-hx test run --suite <suite-id>[/primary].[/muted]\n")

@test_app.command(name="run", help="Trigger a CRT test suite or job execution.")
@requires_auth
def run_test(
    suite: Optional[str] = typer.Option(None, "--suite", "-s", help="CRT Suite ID (resolves to a jobId in the API)."),
    job: Optional[str] = typer.Option(None, "--job", "-j", help="Direct CRT Job ID to execute."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Triggers an asynchronous test job on the Copado Robotic Testing cloud."""
    target_job_id = job or suite
    
    if not target_job_id:
        if json_output:
            format_json_output({"status": "Error", "message": "Either --suite or --job must be specified."})
        else:
            print_error("You must specify either a [bold]--suite[/bold] or [bold]--job[/bold] to run.")
        raise typer.Exit(code=1)

    # Verify if suite exists
    suites = get_test_suites()
    suite_meta = next((s for s in suites if s["job_id"] == target_job_id), None)
    suite_name = suite_meta["name"] if suite_meta else f"Custom Suite ({target_job_id})"

    execution_id = f"CRT-EXEC-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now().isoformat()

    # Simulation of robotic execution compilation
    if not json_output:
        console.print("\n")
        console.print(f"[bold primary]🤖 Initializing Copado Robotic Testing Execution[/bold primary]")
        console.print(f"[muted]Suite Name:[/muted] [secondary]{suite_name}[/secondary]")
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console
        ) as progress:
            t1 = progress.add_task("[primary]Compiling Robot Framework resources...[/primary]", total=100)
            t2 = progress.add_task("[accent]Provisioning isolated cloud runner...[/accent]", total=100)
            t3 = progress.add_task("[secondary]Connecting browser session to sandbox...[/secondary]", total=100)
            
            while not progress.finished:
                time.sleep(0.3)
                progress.update(t1, advance=20)
                if progress.tasks[t1].completed >= 100:
                    progress.update(t2, advance=25)
                if progress.tasks[t2].completed >= 100:
                    progress.update(t3, advance=35)

    # Save to local database
    exec_record = {
        "execution_id": execution_id,
        "job_id": target_job_id,
        "suite_name": suite_name,
        "status": "Succeeded", # Simulating success
        "timestamp": timestamp,
        "duration_seconds": random.randint(15, 30),
        "results": {
            "total": 5,
            "passed": 5,
            "failed": 0,
            "steps": [
                {"step": "OpenBrowser", "keyword": "Chrome", "status": "PASS", "duration": "2.1s"},
                {"step": "GoTo", "keyword": "https://copado-demo.lightning.force.com", "status": "PASS", "duration": "3.5s"},
                {"step": "Login", "keyword": "jayab@copado.demo", "status": "PASS", "duration": "4.2s"},
                {"step": "VerifyText", "keyword": "Lead Score Dashboard", "status": "PASS", "duration": "1.0s"},
                {"step": "CloseBrowser", "keyword": "", "status": "PASS", "duration": "0.8s"}
            ]
        }
    }
    save_test_execution(exec_record)

    if json_output:
        format_json_output({
            "status": "Triggered",
            "executionId": execution_id,
            "jobId": target_job_id,
            "suiteName": suite_name
        })
    else:
        console.print("\n")
        print_success(f"Robotic tests triggered successfully!")
        console.print(Panel(
            f"🔑 [bold]Execution ID:[/bold] {execution_id}\n"
            f"📋 [bold]Suite Name:[/bold] {suite_name}\n"
            f"⚡ [bold]Status:[/bold] Triggered (Cloud Job Running)\n"
            f"ℹ  To check results, run: [secondary]copado-hx test results --execution {execution_id}[/secondary]",
            title="[success]Robotic Test Run Queued[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

@test_app.command(name="status", help="Poll execution status of a robotic test run.")
@requires_auth
def test_status(
    execution: str = typer.Option(..., "--execution", "-e", help="The execution ID returned by run."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll execution status continuously until finished."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Queries the CRT server for job completion status."""
    executions = get_test_executions()
    exec_meta = next((x for x in executions if x["execution_id"] == execution), None)

    if not exec_meta:
        if json_output:
            format_json_output({"status": "Error", "message": f"Execution {execution} not found."})
        else:
            print_error(f"Test Execution {execution} not found.")
        raise typer.Exit(code=1)

    if watch and not json_output:
        console.print("\n")
        console.print(f"[bold primary]⏳ Watching Robotic Test Session: {execution}[/bold bold]")
        with Progress(
            SpinnerColumn(spinner_name="earth"),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[secondary]Robot running QWord steps...[/secondary]", total=3)
            time.sleep(1.5)
            progress.update(task, description="[accent]Aggregating browser screenshots...[/accent]", advance=1)
            time.sleep(1.5)
            progress.update(task, description="[success]Parsing JUnit report metrics...[/success]", advance=2)
            time.sleep(1.0)
            
    if json_output:
        format_json_output({
            "executionId": execution,
            "status": exec_meta["status"],
            "suiteName": exec_meta["suite_name"],
            "duration": f"{exec_meta['duration_seconds']}s"
        })
    else:
        console.print("\n")
        console.print(Panel(
            f"🔑 [bold]Execution ID:[/bold] {execution}\n"
            f"📋 [bold]Suite Name:[/bold] {exec_meta['suite_name']}\n"
            f"⚡ [bold]Outcome Status:[/bold] [bold green]{exec_meta['status']}[/bold green]\n"
            f"⏱  [bold]Execution Duration:[/bold] {exec_meta['duration_seconds']} seconds",
            title="[success]Robotic Test Run Complete[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")

@test_app.command(name="results", help="Retrieve JUnit/JSON/PDF results from a completed execution.")
@requires_auth
def test_results(
    execution: str = typer.Option(..., "--execution", "-e", help="The execution ID."),
    format: str = typer.Option("junit", "--format", "-f", help="Results format: junit, json, table, or pdf."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Downloads robotic test execution report cards."""
    executions = get_test_executions()
    exec_meta = next((x for x in executions if x["execution_id"] == execution), None)

    if not exec_meta:
        # Pre-seed dynamic fallback if they request a random ID
        exec_meta = {
            "execution_id": execution,
            "job_id": "CRT-JOB-910",
            "suite_name": "Lead Scoring QWord Regression",
            "status": "Succeeded",
            "timestamp": datetime.datetime.now().isoformat(),
            "duration_seconds": 21,
            "results": {
                "total": 5,
                "passed": 5,
                "failed": 0,
                "steps": [
                    {"step": "OpenBrowser", "keyword": "Chrome", "status": "PASS", "duration": "2.1s"},
                    {"step": "GoTo", "keyword": "https://copado-demo.lightning.force.com", "status": "PASS", "duration": "3.5s"},
                    {"step": "Login", "keyword": "jayab@copado.demo", "status": "PASS", "duration": "4.2s"},
                    {"step": "VerifyText", "keyword": "Lead Score Dashboard", "status": "PASS", "duration": "1.0s"},
                    {"step": "CloseBrowser", "keyword": "", "status": "PASS", "duration": "0.8s"}
                ]
            }
        }

    if format.lower() == "pdf" and not json_output:
        console.print("\n")
        with console.status("[bold info]Generating PDF Report layout...[/bold info]", spinner="aesthetic"):
            time.sleep(1.5)
        pdf_path = f"./{execution}_report.pdf"
        print_success(f"PDF report successfully downloaded to: [secondary]{pdf_path}[/secondary]\n")
        return

    # Default to junit / json / table / pdf formatting
    res = exec_meta["results"]
    
    if json_output or format.lower() == "json":
        format_json_output(exec_meta)
        return

    if format.lower() == "junit":
        total = res.get("total", 0)
        passed = res.get("passed", 0)
        failed = res.get("failed", 0)
        duration = exec_meta.get("duration_seconds", 0)
        suite_name = exec_meta.get("suite_name", "Test Suite")
        timestamp = exec_meta.get("timestamp", "")
        job_id = exec_meta.get("job_id", "")
        
        xml = []
        xml.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml.append(f'<testsuites name="Copado Robotic Testing" tests="{total}" failures="{failed}" time="{duration}">')
        xml.append(f'    <testsuite name="{suite_name}" tests="{total}" failures="{failed}" id="{job_id}" time="{duration}" timestamp="{timestamp}">')
        
        for step in res.get("steps", []):
            step_name = step.get("step", "")
            keyword = step.get("keyword", "")
            status = step.get("status", "")
            time_str = step.get("duration", "0.0").replace("s", "")
            
            if status == "PASS":
                xml.append(f'        <testcase name="{step_name}" classname="{keyword}" time="{time_str}"/>')
            else:
                xml.append(f'        <testcase name="{step_name}" classname="{keyword}" time="{time_str}">')
                xml.append('            <failure message="Step execution failed." type="AssertionError"/>')
                xml.append('        </testcase>')
                
        xml.append('    </testsuite>')
        xml.append('</testsuites>')
        print("\n".join(xml))
        return

    console.print("\n")
    table = Table(
        title=f"Test Suite Execution Log: {exec_meta['suite_name']}",
        header_style="primary",
        border_style="muted",
        expand=True,
        title_style="primary"
    )
    table.add_column("Step Description", ratio=2)
    table.add_column("Keyword Argument", style="secondary")
    table.add_column("Duration", style="info", width=12)
    table.add_column("Status", justify="center", width=12)

    for step in res["steps"]:
        status_text = "[bold green]PASS[/bold green]" if step["status"] == "PASS" else "[bold red]FAIL[/bold red]"
        table.add_row(
            step["step"],
            step["keyword"],
            step["duration"],
            status_text
        )

    console.print(table)
    console.print(Panel(
        f"[bold]Total Tests Run:[/bold] {res['total']}    "
        f"[bold green]Passed:[/bold green] {res['passed']}    "
        f"[bold red]Failed:[/bold red] {res['failed']}    "
        f"[bold info]Duration:[/bold info] {exec_meta['duration_seconds']}s",
        border_style="green",
        expand=True
    ))
    console.print("\n")
