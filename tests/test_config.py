import pytest
import os
from copado_hx.config import (
    init_db, load_db, save_auth, get_auth, set_active_story_id, get_active_story
)

def test_auth_persistence():
    # Save auth config and verify retrieval
    save_auth(username="test@copado.com", token="my-token-123", org_id="00D80000000hKuaEAE", environment="Production")
    auth = get_auth()
    assert auth["username"] == "test@copado.com"
    assert auth["token"] == "my-token-123"
    assert auth["org_id"] == "00D80000000hKuaEAE"
    assert auth["environment"] == "Production"

def test_active_story_switching():
    # Lock context to US-1234
    success = set_active_story_id("US-1234")
    assert success is True
    
    active = get_active_story()
    assert active is not None
    assert active["id"] == "US-1234"
    
    # Try invalid story
    success_invalid = set_active_story_id("US-9999")
    assert success_invalid is False
