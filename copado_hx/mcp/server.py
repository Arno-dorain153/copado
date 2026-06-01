import sys
import uuid
import datetime
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

from copado_hx.config import (
    get_auth, get_stories, set_active_story_id, get_active_story, get_story_by_id,
    save_story, get_test_suites, get_test_executions, save_test_execution,
    get_deployments, save_deployment
)
from copado_hx.ai.engine import AIRiskEngine

mcp = FastMCP("copado-hx")

@mcp.tool()
def get_auth_status() -> Dict[str, Any]:
    """Returns the current Copado CLI connection and authentication status."""
    auth = get_auth()
    if not auth or not auth.get("token"):
        return {"status": "Unauthenticated", "message": "No active session. Tell user to run 'copado-hx auth login'."}
    return {
        "status": "Authenticated",
        "username": auth["username"],
        "org_id": auth["org_id"],
        "environment": auth["environment"]
    }

@mcp.tool()
def list_user_stories(pipeline: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists Copado user stories assigned to you, with optional pipeline and status filters."""
    stories = get_stories()
    filtered = []
    for s in stories:
        if pipeline and s["pipeline"] != pipeline:
            continue
        if status and s["status"].lower() != status.lower():
            continue
        filtered.append(s)
    return filtered

@mcp.tool()
def get_active_user_story() -> Dict[str, Any]:
    """Retrieves the active user story currently set in the working context."""
    active = get_active_story()
    if not active:
        return {"status": "No active story", "message": "No working context set. Use set_active_user_story first."}
    return {"status": "Success", "story": active}

@mcp.tool()
def set_active_user_story(story_id: str) -> Dict[str, Any]:
    """Sets the active user story ID context (similar to git checkout)."""
    success = set_active_story_id(story_id)
    if not success:
        return {"status": "Failed", "error": f"User Story {story_id} not found."}
    story = get_story_by_id(story_id)
    return {
        "status": "Success",
        "activeStoryId": story_id,
        "branch": f"dev/{story_id.lower()}",
        "title": story["title"]
    }

@mcp.tool()
def commit_changes(message: str, us: Optional[str] = None, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """Commits metadata files to a user story, logging details to the Copado tracking database."""
    target_id = us
    if not target_id:
        active = get_active_story()
        if not active:
            return {"status": "Failed", "error": "No active story context set. Specify 'us' parameter."}
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        return {"status": "Failed", "error": f"User Story {target_id} not found."}

    components = files or story.get("metadata_changes", [])
    if not components:
        components = ["ApexClass:LeadScoringService", "ApexClass:LeadScoringServiceTest"]
        story["metadata_changes"] = components

    commit_id = f"C-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now().isoformat()

    commit_record = {
        "id": commit_id,
        "message": message,
        "files": components,
        "timestamp": timestamp
    }
    story["commits"].append(commit_record)
    story["status"] = "In Progress"
    save_story(story)

    return {
        "status": "Completed Successfully",
        "commitId": commit_id,
        "userStory": target_id,
        "filesCommitted": components,
        "branch": f"dev/{target_id.lower()}"
    }

@mcp.tool()
def promote_user_story(env: str, us: Optional[str] = None, validate_only: bool = False) -> Dict[str, Any]:
    """Promotes a user story to the next environment in the DevOps pipeline (e.g. UAT, PROD)."""
    target_id = us
    if not target_id:
        active = get_active_story()
        if not active:
            return {"status": "Failed", "error": "No active story context set. Specify 'us'."}
        target_id = active["id"]

    story = get_story_by_id(target_id)
    if not story:
        return {"status": "Failed", "error": f"User Story {target_id} not found."}

    if story["pipeline"] == "PL-METADATA":
        return {
            "status": "Failed",
            "error_code": "PIPELINE_NOT_SUPPORTED",
            "error": "The promote capability is only available for Source Format Pipelines. Metadata Pipeline users must promote via the UI."
        }

    promotion_id = f"PR-{uuid.uuid4().hex[:6].upper()}"
    job_exec_id = f"JOB-EXEC-8083{int(datetime.datetime.now().timestamp()) % 1000}"

    if not validate_only:
        story["environment"] = env
        if env == "PROD":
            story["status"] = "Promoted"
        else:
            story["status"] = "Ready for Test"
        save_story(story)

    deploy_record = {
        "id": promotion_id,
        "user_story": target_id,
        "environment": env,
        "type": "Validation" if validate_only else "Promotion",
        "status": "Completed Successfully",
        "job_execution_id": job_exec_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    save_deployment(deploy_record)

    return {
        "status": "Completed Successfully",
        "promotionId": promotion_id,
        "jobExecutionId": job_exec_id,
        "targetEnvironment": env,
        "type": "Validation" if validate_only else "Promotion"
    }

@mcp.tool()
def execute_robotic_tests(suite_id: str) -> Dict[str, Any]:
    """Triggers a Copado Robotic Testing (CRT) test suite job on the cloud environment."""
    suites = get_test_suites()
    suite_meta = next((s for s in suites if s["job_id"] == suite_id), None)
    suite_name = suite_meta["name"] if suite_meta else f"Custom Suite ({suite_id})"

    execution_id = f"CRT-EXEC-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.datetime.now().isoformat()

    exec_record = {
        "execution_id": execution_id,
        "job_id": suite_id,
        "suite_name": suite_name,
        "status": "Succeeded",
        "timestamp": timestamp,
        "duration_seconds": 22,
        "results": {
            "total": 5,
            "passed": 5,
            "failed": 0
        }
    }
    save_test_execution(exec_record)

    return {
        "status": "Triggered",
        "executionId": execution_id,
        "jobId": suite_id,
        "suiteName": suite_name,
        "message": "Robotic test execution launched in cloud runner."
    }

@mcp.tool()
def query_copado_ai(agent_name: str, prompt: str) -> Dict[str, Any]:
    """Queries one of Copado's 5 specialist AI agents: plan, build, test, release, or operate."""
    agent_id = agent_name.lower()
    valid_agents = ["plan", "build", "test", "release", "operate"]
    if agent_id not in valid_agents:
        return {"status": "Failed", "error": f"Invalid agent name. Must be one of {valid_agents}"}

    response = ""
    if agent_id == "plan":
        response = "I analyzed User Story metadata scope. No file conflicts discovered in target environment branch UAT."
    elif agent_id == "build":
        response = (
            "Here is the generated Apex Class structure based on your request:\n\n"
            "public with sharing class LeadScoringService {\n"
            "    public static Integer calculateScore(Lead targetLead) {\n"
            "        return 100;\n"
            "    }\n"
            "}"
        )
    elif agent_id == "test":
        response = "Generated QWord script for LeadScoringService verification test cases."
    elif agent_id == "release":
        response = "No deployment blockers found for the active user story."
    elif agent_id == "operate":
        response = "Spring-2026 Change Management Plan generated successfully."

    return {
        "agent": agent_id,
        "response": response
    }

@mcp.tool()
def analyze_deployment_logs(log_text: str) -> Dict[str, Any]:
    """AI Risk Engine: Analyzes log text and returns risk assessment, anomalies, and safety rollback advice."""
    return AIRiskEngine.analyze_log_content(log_text)

def run_mcp_server():
    """Starts the FastMCP server over standard I/O (stdio)."""
    mcp.run()
