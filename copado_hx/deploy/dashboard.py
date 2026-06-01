import time
import sys
import random
from typing import List, Dict, Any
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich.text import Text
from copado_hx.config import get_auth
from copado_hx.utils import console

class DeploymentDashboard:
    def __init__(self, story_id: str, target_env: str, is_validation: bool = False):
        self.story_id = story_id
        self.target_env = target_env
        self.is_validation = is_validation
        self.start_time = time.time()
        self.progress_val = 0
        self.phase = "Validation"
        
        # Quality Gate Metrics
        self.total_tests = 42
        self.passed_tests = 0
        self.failed_tests = 0
        self.code_coverage = 0.0
        self.pmd_warnings = 0
        
        # Execution log streams
        self.all_possible_logs = [
            "Initializing connection to target sandbox...",
            "Validating Salesforce OAuth credentials...",
            "Retrieving metadata package manifest (package.xml)...",
            "Comparing Git branch revisions with target org branch...",
            "Starting metadata deployment validation...",
            "Validating CustomObject Account.object...",
            "Validating CustomField Account.Score__c...",
            "Validating ApexClass LeadScoringService...",
            "Validating ApexClass LeadScoringServiceTest...",
            "Starting static analysis via PMD Scanner...",
            "PMD: Scanning LeadScoringService.cls...",
            "PMD: Rule compliance verified. 0 blocker, 2 warnings.",
            "PMD Scan completed successfully.",
            "Deploying metadata package components...",
            "Applying profiles and permission set updates...",
            "Running Salesforce Apex Unit Tests (local test scope)...",
            "Executing LeadScoringServiceTest.testLeadScoringCalculation... [green]PASS[/green]",
            "Executing LeadScoringServiceTest.testLeadScoringNullInputs... [green]PASS[/green]",
            "Executing LeadScoringServiceTest.testLeadScoringBulkLoads... [green]PASS[/green]",
            "Apex Unit Tests completed. 3/3 tests passed.",
            "Calculating Apex Code Coverage metrics...",
            "Coverage: LeadScoringService.cls - 87% coverage.",
            "Quality gate checklist validation in progress...",
            "Code Coverage (87%) is above threshold (>75%).",
            "LWC Component Jest validations running...",
            "Post-deployment Apex scripts execution...",
            "Updating Copado User Story records in Salesforce...",
            "Creating Git Release tag and merging branches...",
            "Deployment completed successfully!"
        ]
        
        if is_validation:
            self.all_possible_logs[-1] = "Validation completed successfully! Ready for promotion."

        self.logs: List[str] = []
        self.log_index = 0

    def get_header(self) -> Panel:
        elapsed = int(time.time() - self.start_time)
        minutes, seconds = divmod(elapsed, 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        status_text = "[bold yellow]RUNNING[/bold yellow]"
        if self.progress_val >= 100:
            status_text = "[bold green]COMPLETED[/bold green]"
            
        title = "🔍 VALIDATION DASHBOARD" if self.is_validation else "🚀 DEPLOYMENT DASHBOARD"
        
        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="center", ratio=2)
        table.add_column(justify="right", ratio=1)
        
        table.add_row(
            f"[muted]Story:[/muted] [secondary]{self.story_id}[/secondary]",
            f"[primary]{title}[/primary] — [info]{self.target_env}[/info]",
            f"Status: {status_text} | Time: [accent]{time_str}[/accent]"
        )
        
        return Panel(table, style="bold #6F32FF")

    def get_progress_panel(self) -> Panel:
        # Progress status text
        if self.progress_val < 25:
            self.phase = "Retrieving Manifest & Git Sync"
        elif self.progress_val < 50:
            self.phase = "Validation & PMD Scan"
        elif self.progress_val < 80:
            self.phase = "Apex Unit Tests & Coverage"
        elif self.progress_val < 100:
            self.phase = "Metadata Activation & Finalizing"
        else:
            self.phase = "Deployment Complete"
            
        grid = Table.grid(expand=True)
        grid.add_column(ratio=2)
        grid.add_column(ratio=8)
        
        # Build custom progress bar using Rich elements
        bar_width = 40
        completed_blocks = int((self.progress_val / 100) * bar_width)
        remaining_blocks = bar_width - completed_blocks
        
        bar_str = f"[success]█[/success]" * completed_blocks + f"[muted]░[/muted]" * remaining_blocks
        
        grid.add_row(
            f"[bold]{self.phase}[/bold]",
            f"{bar_str}  [bold info]{int(self.progress_val)}%[/bold info]"
        )
        
        # Phases Checklist
        checklist = Table.grid(padding=(0, 2))
        checklist.add_column(width=3)
        checklist.add_column()
        
        phases = [
            ("Workspace Retrieve & Manifest Compare", 20),
            ("Quality Gate: Static Code Analysis (PMD)", 45),
            ("Quality Gate: Apex Unit Test Runs", 75),
            ("Metadata Package Deployment / Validation", 95),
            ("Git Merges & Copado Status Updates", 100)
        ]
        
        for name, threshold in phases:
            if self.progress_val >= threshold:
                icon = "[success]✔[/success]"
                style = "success"
            elif self.progress_val >= threshold - 20:
                icon = "[bold yellow]⚙[/bold yellow]"
                style = "bold yellow"
            else:
                icon = "[muted]☐[/muted]"
                style = "muted"
            checklist.add_row(icon, f"[{style}]{name}[/{style}]")
            
        grid.add_row("", "")
        grid.add_row("[muted]Phases:[/muted]", checklist)
            
        return Panel(grid, title="[primary]Deployment Progress[/primary]", border_style="purple")

    def get_quality_gates_panel(self) -> Panel:
        # Dynamic metrics simulation based on progress
        if self.progress_val >= 45:
            self.pmd_warnings = 2
        
        if self.progress_val >= 50:
            pct = (self.progress_val - 50) / 25.0
            if pct > 1.0:
                pct = 1.0
            self.passed_tests = int(pct * self.total_tests)
            if self.progress_val >= 75:
                self.code_coverage = 86.4
        
        table = Table.grid(expand=True, padding=(0, 1))
        table.add_column(style="bold", width=22)
        table.add_column(justify="right")
        
        cov_style = "green" if self.code_coverage >= 75 else "yellow" if self.code_coverage > 0 else "muted"
        cov_str = f"[{cov_style}]{self.code_coverage}%[/{cov_style}]" if self.code_coverage > 0 else "[muted]Pending[/muted]"
        
        test_str = f"[success]{self.passed_tests}[/success] / [primary]{self.total_tests}[/primary] Passed" if self.progress_val >= 50 else "[muted]Pending[/muted]"
        
        pmd_style = "success" if self.progress_val >= 45 and self.pmd_warnings == 2 else "muted"
        pmd_str = f"[bold yellow]{self.pmd_warnings} Warnings[/bold yellow]" if self.progress_val >= 45 else "[muted]Pending[/muted]"
        
        table.add_row("Apex Test Execution", test_str)
        table.add_row("Apex Code Coverage (>75%)", cov_str)
        table.add_row("Static PMD Scans", pmd_str)
        table.add_row("LWC Component Jest Tests", "[success]Pass (8/8)[/success]" if self.progress_val >= 90 else "[muted]Pending[/muted]")
        
        gate_status = "[bold green]PASSING[/bold green]"
        gate_border = "green"
        if self.progress_val < 75:
            gate_status = "[bold yellow]EVALUATING Quality Gates...[/bold yellow]"
            gate_border = "yellow"
            
        layout_table = Table.grid(expand=True)
        layout_table.add_column()
        layout_table.add_row(table)
        layout_table.add_row("")
        layout_table.add_row(Align.center(f"Quality Check Status: {gate_status}"))
        
        return Panel(layout_table, title="[secondary]Quality Gates & Tests[/secondary]", border_style=gate_border)

    def get_logs_panel(self) -> Panel:
        # Determine logs to show based on progress
        log_count = int((self.progress_val / 100.0) * len(self.all_possible_logs))
        if log_count < 1:
            log_count = 1
        if self.progress_val >= 100:
            log_count = len(self.all_possible_logs)
            
        logs_to_show = self.all_possible_logs[:log_count]
        
        # Take the last 6 logs to show in the scrolling view
        recent_logs = logs_to_show[-7:]
        log_text = "\n".join([f"[muted]>>>[/muted] {log}" for log in recent_logs])
        
        return Panel(
            log_text,
            title="[accent]Live Deployment Logs[/accent]",
            border_style="cyan",
            expand=True
        )

    def get_env_panel(self) -> Panel:
        auth = get_auth()
        user = auth.get("username", "developer@copado.demo")
        
        grid = Table.grid(expand=True, padding=(0, 1))
        grid.add_column(style="primary", width=15)
        grid.add_column(style="secondary")
        
        grid.add_row("Triggered By", user)
        grid.add_row("Target Org ID", auth.get("org_id", "00D80000000hKuaEAE"))
        grid.add_row("Source Org", f"DEV-1 (dev/us-1234)")
        grid.add_row("Destination", f"{self.target_env} (release/uat)")
        grid.add_row("Pipeline Name", "SFDX Source Format Pipeline")
        grid.add_row("Job Execution ID", f"JOB-EXEC-8083{int(self.start_time) % 1000}")
        
        return Panel(grid, title="[info]Environment & Connection[/info]", border_style="cyan")

    def make_layout(self) -> Layout:
        layout = Layout()
        
        # Partition screen
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="logs", size=9)
        )
        
        # Split main area
        layout["main"].split_row(
            Layout(name="progress", ratio=6),
            Layout(name="right", ratio=5)
        )
        
        layout["right"].split(
            Layout(name="env", ratio=1),
            Layout(name="gates", ratio=1)
        )
        
        # Assign panels
        layout["header"].update(self.get_header())
        layout["progress"].update(self.get_progress_panel())
        layout["gates"].update(self.get_quality_gates_panel())
        layout["env"].update(self.get_env_panel())
        layout["logs"].update(self.get_logs_panel())
        
        return layout

    def update_progress(self):
        """Simulates progress increments."""
        if self.progress_val < 100:
            # Random increment between 5 and 15
            self.progress_val += random.uniform(8.0, 18.0)
            if self.progress_val >= 100:
                self.progress_val = 100.0

def run_live_dashboard(story_id: str, target_env: str, is_validation: bool = False):
    """Executes the live terminal dashboard in an auto-refresh loop."""
    dashboard = DeploymentDashboard(story_id, target_env, is_validation)
    
    console.print("\n")
    with Live(dashboard.make_layout(), console=console, screen=True, auto_refresh=False) as live:
        while dashboard.progress_val < 100:
            time.sleep(2.0)
            dashboard.update_progress()
            live.update(dashboard.make_layout(), refresh=True)
            
        # Keep the final state visible for 2 more seconds before exiting screen mode
        time.sleep(2.0)
    
    # Render final report to normal stdout console
    console.print("\n")
    title_str = "Validation" if is_validation else "Deployment"
    console.print(Panel(
        f"[bold green]✔ {title_str} Completed Successfully![/bold green]\n\n"
        f"📋 [bold]User Story ID:[/bold] {story_id}\n"
        f"🌐 [bold]Target Sandbox:[/bold] {target_env}\n"
        f"📊 [bold]Apex Unit Tests:[/bold] 42/42 Passed\n"
        f"📈 [bold]Apex Code Coverage:[/bold] 86.4%\n"
        f"🛠  [bold]PMD Static Scan:[/bold] Passing (2 low warnings)\n"
        f"🌿 [bold]Pipeline Status:[/bold] Merged and Synchronized",
        title=f"[success]Copado {title_str} Summary Report[/success]",
        border_style="green",
        expand=False
    ))
    console.print("\n")
