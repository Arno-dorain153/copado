import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_DIR = Path.home() / ".copado_hx"
DB_FILE = DB_DIR / "db.json"

DEFAULT_DB = {
    "auth": {
        "username": None,
        "token": None,
        "org_id": None,
        "environment": None
    },
    "active_story_id": None,
    "environments": [
        {"id": "DEV-1", "name": "Dev Sandbox 1", "branch": "dev/us-1234", "status": "Connected", "type": "ScratchOrg"},
        {"id": "DEV-2", "name": "Dev Sandbox 2", "branch": "dev/us-1235", "status": "Connected", "type": "ScratchOrg"},
        {"id": "UAT", "name": "UAT Integration", "branch": "release/uat", "status": "Connected", "type": "Sandbox"},
        {"id": "PROD", "name": "Production Org", "branch": "main", "status": "Connected", "type": "Production"}
    ],
    "pipelines": [
        {"id": "PL-101", "name": "Salesforce Source Format Pipeline", "stages": ["DEV-1", "DEV-2", "UAT", "PROD"]}
    ],
    "stories": [
        {
            "id": "US-1234",
            "title": "Add lead scoring logic",
            "pipeline": "PL-101",
            "status": "In Progress",
            "environment": "DEV-1",
            "developer": "jayab@copado.demo",
            "metadata_changes": ["ApexClass:LeadScoringService", "ApexClass:LeadScoringServiceTest"],
            "commits": []
        },
        {
            "id": "US-1235",
            "title": "Update contact mailing layout",
            "pipeline": "PL-101",
            "status": "Draft",
            "environment": "DEV-2",
            "developer": "jayab@copado.demo",
            "metadata_changes": [],
            "commits": []
        },
        {
            "id": "US-1236",
            "title": "Fix validation rule for opportunities",
            "pipeline": "PL-101",
            "status": "Promoted",
            "environment": "UAT",
            "developer": "jayab@copado.demo",
            "metadata_changes": ["ValidationRule:Opportunity.Check_Amount"],
            "commits": [{"id": "C-9921", "message": "fix: Opportunity check amount validation", "files": ["ValidationRule:Opportunity.Check_Amount"], "timestamp": "2026-05-30T10:14:00"}]
        }
    ],
    "test_suites": [
        {"id": "CRT-SUITE-10", "name": "Lead Scoring QWord Regression", "job_id": "CRT-JOB-910", "project_id": "CRT-PROJ-88"},
        {"id": "CRT-SUITE-11", "name": "Contact Layout Validation", "job_id": "CRT-JOB-911", "project_id": "CRT-PROJ-88"}
    ],
    "test_executions": [],
    "deployments": [],
    "dialogues": {}
}

def init_db():
    """Initializes the database directory and file if they do not exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        with open(DB_FILE, "w") as f:
            json.dump(DEFAULT_DB, f, indent=4)

def load_db() -> Dict[str, Any]:
    """Loads and returns the database contents."""
    init_db()
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_DB

def save_db(data: Dict[str, Any]):
    """Saves the given data dictionary to the database file."""
    init_db()
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_auth() -> Dict[str, Any]:
    """Returns authentication details."""
    db = load_db()
    return db.get("auth", DEFAULT_DB["auth"])

def save_auth(username: Optional[str], token: Optional[str], org_id: Optional[str] = None, environment: Optional[str] = None):
    """Saves authentication details."""
    db = load_db()
    db["auth"] = {
        "username": username,
        "token": token,
        "org_id": org_id or "00D80000000hKuaEAE",
        "environment": environment or "Production"
    }
    save_db(db)

def get_active_story() -> Optional[Dict[str, Any]]:
    """Returns the currently active user story details if set."""
    db = load_db()
    active_id = db.get("active_story_id")
    if not active_id:
        return None
    for story in db.get("stories", []):
        if story["id"] == active_id:
            return story
    return None

def set_active_story_id(story_id: Optional[str]) -> bool:
    """Sets the active story ID. Returns True if successfully found, False otherwise."""
    db = load_db()
    if story_id is None:
        db["active_story_id"] = None
        save_db(db)
        return True
    
    # Verify story exists
    exists = any(story["id"] == story_id for story in db.get("stories", []))
    if exists:
        db["active_story_id"] = story_id
        save_db(db)
        return True
    return False

def get_stories() -> List[Dict[str, Any]]:
    """Returns all stories."""
    return load_db().get("stories", [])

def get_story_by_id(story_id: str) -> Optional[Dict[str, Any]]:
    """Returns a story by its ID."""
    for story in get_stories():
        if story["id"] == story_id:
            return story
    return None

def save_story(story_data: Dict[str, Any]):
    """Saves or updates a user story."""
    db = load_db()
    stories = db.get("stories", [])
    for idx, story in enumerate(stories):
        if story["id"] == story_data["id"]:
            stories[idx] = story_data
            break
    else:
        stories.append(story_data)
    db["stories"] = stories
    save_db(db)

def get_environments() -> List[Dict[str, Any]]:
    """Returns pipeline environments."""
    return load_db().get("environments", [])

def get_test_suites() -> List[Dict[str, Any]]:
    """Returns CRT test suites."""
    return load_db().get("test_suites", [])

def get_test_executions() -> List[Dict[str, Any]]:
    """Returns CRT test executions."""
    return load_db().get("test_executions", [])

def save_test_execution(exec_data: Dict[str, Any]):
    """Saves a test execution."""
    db = load_db()
    db["test_executions"].append(exec_data)
    save_db(db)

def get_deployments() -> List[Dict[str, Any]]:
    """Returns deployments."""
    return load_db().get("deployments", [])

def save_deployment(deploy_data: Dict[str, Any]):
    """Saves a deployment execution."""
    db = load_db()
    db["deployments"].append(deploy_data)
    save_db(db)
