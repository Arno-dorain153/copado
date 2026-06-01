import pytest
from copado_hx.ai.engine import AIRiskEngine

def test_success_log_risk():
    log_content = (
        "[INFO] Initializing validation pipeline\n"
        "[INFO] Static Code Scan via PMD: Clean.\n"
        "[INFO] Executed LeadScoringServiceTest.testLeadScoringCalculation - Success\n"
        "[INFO] Average Code Coverage: 87%\n"
        "[INFO] Validation completed successfully."
    )
    result = AIRiskEngine.analyze_log_content(log_content)
    
    assert result["risk_score"] < 40
    assert len(result["anomalies"]) == 0
    assert not result["rollback_suggested"]

def test_critical_failure_log_risk():
    log_content = (
        "[INFO] Initializing validation pipeline\n"
        "[ERROR] System.AssertException: Assertion Failed: Expected score: 85, Actual: 20\n"
        "[ERROR] System.DmlException: Insert failed.\n"
        "[WARNING] Average Code Coverage: 52%"
    )
    result = AIRiskEngine.analyze_log_content(log_content)
    
    assert result["risk_score"] > 70
    assert "DML Exception Detected" in result["anomalies"]
    assert "Apex Unit Test Assertion Failure" in result["anomalies"]
    assert "Low Test Coverage (52%)" in result["anomalies"]
    assert result["rollback_suggested"] is True

def test_warning_log_risk():
    log_content = (
        "[INFO] Initializing validation pipeline\n"
        "[WARNING] API version 48.0 is deprecated in manifest package.xml\n"
        "[INFO] PMD: 2 minor warnings regarding naming conventions.\n"
        "[INFO] Average Code Coverage: 73%"
    )
    result = AIRiskEngine.analyze_log_content(log_content)
    
    assert 40 <= result["risk_score"] <= 70
    assert "Deprecated API Version v48.0 in manifest" in result["anomalies"]
    assert "Low Test Coverage (73%)" in result["anomalies"]
    assert result["rollback_suggested"] is False
