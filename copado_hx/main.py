import typer
from typing import Optional
from copado_hx.utils import print_banner, console

# Initialize Typer App
app = typer.Typer(
    name="copado-hx",
    help="🚀 Copado Headless CLI — The future of Salesforce DevOps lives in your terminal.",
    no_args_is_help=True,
    add_completion=False
)

# Callback to show a banner on executions unless --json is used
@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Show version and exit.", is_eager=True
    )
):
    if version:
        import copado_hx
        console.print(f"[primary]copado-hx[/primary] version [secondary]{copado_hx.__version__}[/secondary]")
        raise typer.Exit()

# Import command groups (registered after they are implemented)
# We will dynamically register routers in main.py once the files exist to avoid import errors.
def register_routers():
    from copado_hx.auth.commands import auth_app
    from copado_hx.story.commands import story_app
    from copado_hx.test.commands import test_app
    from copado_hx.ai.commands import ai_app
    from copado_hx.deploy.commands import commit_cmd, promote_cmd, deploy_cmd, status_cmd

    app.add_typer(auth_app, name="auth")
    app.add_typer(story_app, name="story")
    app.add_typer(test_app, name="test")
    app.add_typer(ai_app, name="ai")
    
    # Top level shortcuts (extremely convenient for developers!)
    app.command(name="commit", help="Commit metadata changes to the active user story.")(commit_cmd)
    app.command(name="promote", help="Promote a user story to the next environment.")(promote_cmd)
    app.command(name="deploy", help="Deploy changes to an environment.")(deploy_cmd)
    app.command(name="status", help="View deployment pipeline status or watch live dashboard.")(status_cmd)

    # MCP Server Command
    @app.command(name="mcp", help="Start the Model Context Protocol (MCP) server over stdio.")
    def mcp_start():
        from copado_hx.mcp.server import run_mcp_server
        run_mcp_server()

# Register them immediately
register_routers()

if __name__ == "__main__":
    app()
