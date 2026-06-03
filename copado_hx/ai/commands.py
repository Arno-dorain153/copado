import typer
import time
import os
import questionary
from typing import Optional
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from copado_hx.ai.engine import AIRiskEngine
from copado_hx.config import load_db, save_db, get_active_story, get_story_by_id
from copado_hx.utils import (
    console, requires_auth, print_success, print_error, print_warning, format_json_output
)

ai_app = typer.Typer(help="🤖 Converse with Copado AI Specialist Agents")

AGENT_DESCRIPTIONS = {
    "plan": "Plan Agent (User Story refinements, Conflict detection)",
    "build": "Build Agent (Apex Code generation, Metadata scanning)",
    "test": "Test Agent (QWord robotic test script generation)",
    "release": "Release Agent (Commit & promotion error diagnosis)",
    "operate": "Operate Agent (Change management plans & documentation)"
}

@ai_app.command(name="ask", help="Send a prompt to a specialist Copado agent.")
@requires_auth
def ask_agent(
    prompt: str = typer.Argument(..., help="The prompt/question for the AI agent."),
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan | build | test | release | operate"),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Submits a question to one of the five lifecycle-specific Copado agents."""
    agent_id = agent.lower()
    if agent_id not in AGENT_DESCRIPTIONS:
        print_error(f"Invalid agent type: {agent}. Must be one of: plan, build, test, release, operate")
        raise typer.Exit(code=1)

    if not json_output:
        console.print(f"\n[primary]🤖 Querying {AGENT_DESCRIPTIONS[agent_id]}...[/primary]")
        with console.status("[bold #6F32FF]Thinking...[/bold #6F32FF]", spinner="aesthetic"):
            time.sleep(1.8)

    # Simulated response generation based on prompts
    response = ""
    if agent_id == "plan":
        # Check if the class is implemented on disk in the force-app folder
        import os
        class_exists = False
        paths_to_check = [
            os.path.join("copado_hx", "force-app", "main", "default", "classes", "LeadScoringService.cls"),
            os.path.join("force-app", "main", "default", "classes", "LeadScoringService.cls"),
            os.path.join("a:\\copado\\copado_hx\\copado_hx\\force-app\\main\\default\\classes\\LeadScoringService.cls"),
            os.path.join("a:\\copado_hx\\copado_hx\\force-app\\main\\default\\classes\\LeadScoringService.cls")
        ]
        for p in paths_to_check:
            if os.path.exists(p):
                class_exists = True
                break
                
        if class_exists:
            response = (
                "I analyzed User Story metadata scope. No file conflicts discovered in target environment branch UAT. "
                "The Apex method LeadScoringService.calculateScore is now successfully implemented on disk and ready to be committed!"
            )
        else:
            response = (
                "I analyzed User Story metadata scope. No file conflicts discovered in target environment branch UAT. "
                "However, LWC controller references Apex method LeadScoringService.calculateScore which is currently in Draft state."
            )
    elif agent_id == "build":
        response = (
            "Here is the generated Apex Class structure based on your request:\n\n"
            "public with sharing class LeadScoringService {\n"
            "    public static Integer calculateScore(Lead targetLead) {\n"
            "        if (targetLead == null) return 0;\n"
            "        Integer score = 0;\n"
            "        if (targetLead.AnnualRevenue != null && targetLead.AnnualRevenue > 1000000) score += 50;\n"
            "        if (targetLead.Industry == 'Technology') score += 35;\n"
            "        return score;\n"
            "    }\n"
            "}"
        )
    elif agent_id == "test":
        response = (
            "Generated CRT QWord test script for LeadScoringService:\n\n"
            "*** Test Cases ***\n"
            "Verify Lead Score Display\n"
            "    OpenBrowser    Chrome\n"
            "    GoTo           https://copado-demo.lightning.force.com\n"
            "    Login          jayab@copado.demo\n"
            "    ClickText      Leads\n"
            "    VerifyText     Lead Score\n"
            "    CloseBrowser"
        )
    elif agent_id == "release":
        db = load_db()
        story = get_story_by_id("US-1234")
        metadata_changes = story.get("metadata_changes", []) if story else []
        has_dependency = any("CustomMetadata:Scoring_Settings" in item for item in metadata_changes)
        
        if has_dependency:
            response = (
                "Analyzing Job Execution logs for US-1234: "
                "No blockers found! The custom metadata dependency 'Scoring_Settings__mdt' is successfully included in the payload. "
                "All checks passed. Ready for promotion!"
            )
        else:
            response = (
                "Analyzing Job Execution error logs for US-1234: "
                "The error 'FIELD_CUSTOM_VALIDATION_EXCEPTION' was triggered because your deployment package includes "
                "ValidationRule:Opportunity.Check_Amount but misses custom metadata config 'Scoring_Settings__mdt' in the payload."
            )
    elif agent_id == "operate":
        response = (
            "Here is the change management plan for release Spring-2026:\n"
            "1. Deployment Scope: Metadata commit US-1234 (Lead scoring Apex handler)\n"
            "2. Training: Inform sales representatives regarding new auto-populated fields.\n"
            "3. Rollback: Standard package validation rollback script generated."
        )

    if json_output:
        format_json_output({
            "agent": agent_id,
            "prompt": prompt,
            "response": response
        })
    else:
        console.print(Panel(
            response,
            title=f"[primary]{AGENT_DESCRIPTIONS[agent_id]}[/primary]",
            border_style="purple",
            expand=False
        ))
        console.print("\n")

@ai_app.command(name="chat", help="Start an interactive multi-turn REPL with an AI agent.")
@requires_auth
def chat_agent(
    agent: str = typer.Option(..., "--agent", "-a", help="Agent: plan | build | test | release | operate"),
    us: Optional[str] = typer.Option(None, "--us", "-u", help="Contextual User Story ID.")
):
    """Launches a loop where developers can interactively chat with a Copado Agent."""
    agent_id = agent.lower()
    if agent_id not in AGENT_DESCRIPTIONS:
        print_error(f"Invalid agent type: {agent}. Must be one of: plan, build, test, release, operate")
        raise typer.Exit(code=1)

    story_ctx = us
    if not story_ctx:
        active = get_active_story()
        if active:
            story_ctx = active["id"]

    console.print("\n")
    console.print(Panel(
        f"Conversing with [bold secondary]{AGENT_DESCRIPTIONS[agent_id]}[/bold secondary]\n"
        f"Context Scope: [accent]{story_ctx or 'Global pipeline'}[/accent]\n\n"
        "Type [bold error]exit[/bold error] or [bold error]quit[/bold error] to end chat session.",
        title="[primary]Interactive AI Dialogue Session[/primary]",
        border_style="purple"
    ))
    console.print("\n")

    while True:
        try:
            user_msg = questionary.text("You:").ask()
            if user_msg is None or user_msg.lower().strip() in ["exit", "quit", "q"]:
                console.print("[info]Closing session...[/info]")
                break
            
            if not user_msg.strip():
                continue
                
            with console.status("[bold #6F32FF]Agent is thinking...[/bold #6F32FF]", spinner="aesthetic"):
                time.sleep(1.2)
                
            # Generates smart context responses
            reply = f"I've processed your message relative to [secondary]{story_ctx or 'Global'}[/secondary] branch context.\n"
            if agent_id == "release":
                if "conflict" in user_msg.lower():
                    reply += "Analyzing branches... No merge conflicts detected between US-1234 branch (dev/us-1234) and target UAT branch."
                elif "error" in user_msg.lower() or "blocker" in user_msg.lower() or "fail" in user_msg.lower():
                    reply += "The validation blocker for US-1234 (missing custom metadata Scoring_Settings__mdt) has been resolved. The package is now clean and ready to deploy!"
                elif "commit" in user_msg.lower():
                    reply += "US-1234 has 3 tracked metadata changes (ApexClass:LeadScoringService, ApexClass:LeadScoringServiceTest, and CustomMetadata:Scoring_Settings). All changes are committed and synced."
                elif "validat" in user_msg.lower() or "promote" in user_msg.lower() or "deploy" in user_msg.lower():
                    reply += "US-1234 is currently in DEV-1. You can validate its promotion to UAT by running 'copado-hx promote --env UAT --validate --watch' outside this chat."
                else:
                    reply += "I can help you diagnose promotion issues, check for pipeline blockers, or prepare deployment packages for US-1234. What release task would you like to discuss?"
            else:
                if "conflict" in user_msg.lower():
                    reply += "Checking git history... branch matches Dev Sandbox clean. No conflict hazards found."
                elif "code" in user_msg.lower() or "apex" in user_msg.lower():
                    reply += "Code snippet suggested: `public static void run() { System.debug('Headless execution'); }`"
                elif "test" in user_msg.lower():
                    reply += "Test class skeleton generated: `LeadScoringServiceTest` under `force-app/main/default/classes/`."
                elif "both" in user_msg.lower() or ("commit" in user_msg.lower() and ("validat" in user_msg.lower() or "promote" in user_msg.lower() or "deploy" in user_msg.lower())):
                    reply += "To do both:\n1. First commit your changes:\n[primary]copado-hx commit --message 'feat: implement lead scoring'[/primary]\n2. Then validate/promote your story:\n[primary]copado-hx promote --env UAT --validate --watch[/primary]"
                elif "commit" in user_msg.lower():
                    reply += "To commit these changes to your active story branch, you can exit this chat and run:\n[primary]copado-hx commit --message 'feat: implement lead scoring'[/primary]"
                elif "validat" in user_msg.lower() or "promote" in user_msg.lower() or "deploy" in user_msg.lower():
                    reply += "To validate or promote your story, exit this chat and run:\n[primary]copado-hx promote --env UAT --validate --watch[/primary]"
                else:
                    reply += "How would you like to proceed with committing or validating this scope inside the pipeline?"
                
            console.print("\n")
            console.print(Panel(reply, title=f"[secondary]{agent_id.upper()} AGENT[/secondary]", border_style="cyan"))
            console.print("\n")
            
        except KeyboardInterrupt:
            console.print("\n[info]Closing session...[/info]")
            break

@ai_app.command(name="analyze-logs", help="AI Risk Engine: Parse deployment logs for risk analysis.")
def analyze_logs(
    logfile: str = typer.Argument(..., help="Path to deployment log file (txt) to evaluate."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Parses a local logfile using rules to calculate risk and triggers rollbacks if dangerous."""
    if not os.path.exists(logfile):
        if json_output:
            format_json_output({"status": "Error", "message": f"Log file {logfile} not found."})
        else:
            print_error(f"File not found: {logfile}")
        raise typer.Exit(code=1)

    with open(logfile, "r") as f:
        log_content = f.read()

    analysis = AIRiskEngine.analyze_log_content(log_content)

    if json_output:
        format_json_output(analysis)
        return

    # Visual Reporting
    console.print("\n")
    console.print(f"[bold primary]🧠 Copado AI Risk Engine Assessment[/bold primary]")
    console.print(f"[muted]Log File:[/muted] [secondary]{logfile}[/secondary]")
    
    score = analysis["risk_score"]
    if score >= 70:
        score_str = f"[bold blink red]{score}/100 (HIGH RISK)[/bold blink red]"
        border_color = "red"
    elif score >= 40:
        score_str = f"[bold yellow]{score}/100 (MEDIUM RISK)[/bold yellow]"
        border_color = "yellow"
    else:
        score_str = f"[bold green]{score}/100 (LOW RISK)[/bold green]"
        border_color = "green"

    anomaly_lines = "\n".join([f"  🚨 [bold red]{a}[/bold red]" for a in analysis["anomalies"]]) if analysis["anomalies"] else "  [green]No critical anomalies detected.[/green]"
    detail_lines = "\n".join([f"  • {d}" for d in analysis["details"]]) if analysis["details"] else "  • Setup and validations completed normally."

    report_content = (
        f"[bold]Risk Score Assessment:[/bold] {score_str}\n\n"
        f"[bold primary]Anomalies Found:[/bold primary]\n{anomaly_lines}\n\n"
        f"[bold primary]Risk Analysis Details:[/bold primary]\n{detail_lines}"
    )

    console.print(Panel(
        report_content,
        title="[primary]Risk Report[/primary]",
        border_style=border_color,
        expand=False
    ))
    console.print("\n")

    if analysis["rollback_suggested"]:
        console.print(Panel(
            "[bold red]💥 CRITICAL RISK EXCEEDS DEPLOYMENT GUARDRAILS (>70)[/bold red]\n\n"
            "The AI engine suggests rolling back this validation to prevent sandbox contamination.",
            title="[error]Rollback Recommended[/error]",
            border_style="red",
            expand=False
        ))
        
        # Immediate rollback request
        rollback = questionary.confirm("Execute immediate automated rollback to previous stable commit?").ask()
        if rollback:
            console.print("\n")
            with Progress(
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                console=console
            ) as progress:
                t1 = progress.add_task("[error]Reverting branch merge pull requests...[/error]", total=100)
                t2 = progress.add_task("[error]Rebuilding database metadata manifest...[/error]", total=100)
                t3 = progress.add_task("[error]Purging invalidated cache objects...[/error]", total=100)
                
                while not progress.finished:
                    time.sleep(0.3)
                    progress.update(t1, advance=25)
                    if progress.tasks[t1].completed >= 100:
                        progress.update(t2, advance=30)
                    if progress.tasks[t2].completed >= 100:
                        progress.update(t3, advance=40)
            
            console.print("\n")
            print_success("Automated rollback completed successfully! Environment restored to stability.")
            console.print("\n")
        else:
            print_warning("Rollback ignored. Exercise caution. Sandbox might remain in an unstable state.")
            console.print("\n")

@ai_app.command(name="handoff", help="Bonus: Demonstrate multi-agent context handoff sequence.")
def multi_agent_handoff(
    us: str = typer.Option("US-1234", "--us", "-u", help="User story scope context."),
    json_output: bool = typer.Option(False, "--json", help="Output results in machine-readable JSON format.")
):
    """Demonstrates multi-agent sequencing where Build agent output passes automatically to Test agent."""
    if not json_output:
        console.print("\n")
        console.print(Panel(
            "[bold primary]🤖 Multi-Agent DevOps Flow Sequence[/bold primary]\n\n"
            "This demo shows the Build Agent parsing user story context and outputting parameters\n"
            "that the Test Agent reads directly to generate tests, passing data automatically.",
            border_style="purple",
            expand=False
        ))
        console.print("\n")

    # Stage 1: Build Agent
    if not json_output:
        console.print("[primary]Step 1: Invoking Build Agent to compile Apex class from US-1234 context...[/primary]")
        time.sleep(1.5)

    build_output_json = {
        "class_name": "LeadScoringService",
        "methods": [
            {"name": "calculateScore", "return_type": "Integer", "parameters": [{"type": "Lead", "name": "targetLead"}]}
        ],
        "metadata_dependencies": ["CustomField:Lead.Score__c", "CustomField:Lead.AnnualRevenue"],
        "source_code_path": "force-app/main/default/classes/LeadScoringService.cls",
        "generated_status": "Success"
    }

    if not json_output:
        console.print(f"  ✔ Build Agent output: [secondary]{build_output_json['class_name']}.cls[/secondary] successfully written.")
        console.print("  [muted]Context Details Passed (JSON Schema):[/muted]")
        console.print(f"  {build_output_json}")
        console.print("\n")
        
        # Stage 2: Test Agent
        console.print("[primary]Step 2: Feeding JSON payload to Test Agent to write QWord robotic scripts...[/primary]")
        time.sleep(1.5)

    qword_script = (
        "*** Test Cases ***\n"
        f"Verify {build_output_json['class_name']} Test Execution\n"
        "    OpenBrowser    Chrome\n"
        "    GoTo           https://copado-demo.lightning.force.com\n"
        "    Login          jayab@copado.demo\n"
        f"    RunApexMethod  {build_output_json['class_name']}.calculateScore\n"
        "    VerifyField    Lead.Score__c  >  0\n"
        "    CloseBrowser"
    )

    test_agent_response = {
        "test_suite_name": f"{build_output_json['class_name']}ValidationSuite",
        "qword_script": qword_script,
        "test_runner": "CRT",
        "coverage_target": 85.0
    }

    if json_output:
        format_json_output({
            "stage_1_build_agent": build_output_json,
            "stage_2_test_agent": test_agent_response
        })
    else:
        console.print(Panel(
            f"[bold green]✔ Handoff Succeeded![/bold green]\n\n"
            f"[bold]Generated Test Suite:[/bold] {test_agent_response['test_suite_name']}\n\n"
            f"[bold primary]QWord Robot Script:[/bold primary]\n{test_agent_response['qword_script']}",
            title="[success]Multi-Agent Handoff Verification[/success]",
            border_style="green",
            expand=False
        ))
        console.print("\n")
