import re
from typing import Dict, Any, List

class AIRiskEngine:
    @staticmethod
    def analyze_log_content(content: str) -> Dict[str, Any]:
        """Parses logs for anomalies and calculates a DevOps Risk Score (1-100)."""
        anomalies = []
        details = []
        base_score = 10
        
        # Check for Apex compilation or execution failures
        dml_matches = re.findall(r"(System\.DmlException|FIELD_CUSTOM_VALIDATION_EXCEPTION|DmlException)", content, re.IGNORECASE)
        if dml_matches:
            anomalies.append("DML Exception Detected")
            details.append("Salesforce DML validation rules blocked database insertions.")
            base_score += 35
            
        test_fail_matches = re.findall(r"(System\.AssertException|Assertion Failed|System\.Exception.*test)", content, re.IGNORECASE)
        if test_fail_matches:
            anomalies.append("Apex Unit Test Assertion Failure")
            details.append("Critical functional assertions failed during test execution phase.")
            base_score += 40
            
        # Check for code coverage
        coverage_match = re.search(r"Average Code Coverage:\s*(\d+)%", content, re.IGNORECASE)
        if coverage_match:
            coverage = int(coverage_match.group(1))
            if coverage < 75:
                anomalies.append(f"Low Test Coverage ({coverage}%)")
                details.append(f"Deploying with code coverage below target threshold (75%). Current: {coverage}%")
                base_score += 25
            else:
                details.append(f"Code Coverage verified: {coverage}% (above requirement)")
        else:
            # Check if there is a warning about code coverage missing
            if "coverage" in content.lower() and "warning" in content.lower():
                anomalies.append("Test Coverage Missing Warnings")
                details.append("Some components have not been fully evaluated for code coverage.")
                base_score += 15

        # Check for API version issues
        api_matches = re.findall(r"API version\s+(\d+(?:\.\d+)?)\s+is deprecated", content, re.IGNORECASE)
        if api_matches:
            anomalies.append(f"Deprecated API Version v{api_matches[0]} in manifest")
            details.append(f"Manifest utilizes deprecated Salesforce API version {api_matches[0]}. Upgrades recommended.")
            base_score += 10

        # Check for profile permissions conflicts
        profile_mismatch = re.findall(r"(Profile.*missing.*permissions|PermissionSet.*conflict)", content, re.IGNORECASE)
        if profile_mismatch:
            anomalies.append("Security Profile Settings Out-Of-Sync")
            details.append("Profile metadata references system permissions unavailable in target sandbox.")
            base_score += 15

        # Check for git merge conflicts
        merge_conflict = re.findall(r"(Merge Conflict|CONFLICT.*merge)", content, re.IGNORECASE)
        if merge_conflict:
            anomalies.append("Merge Conflict Detected")
            details.append("Git auto-merges failed. Potential code overrides on shared components.")
            base_score += 30

        # Quality scans warning (PMD)
        pmd_violations = re.findall(r"(PMD.*High.*Priority|PMD Violations:\s*[1-9]\d*)", content, re.IGNORECASE)
        if pmd_violations:
            anomalies.append("High Priority PMD Violations")
            details.append("Static analysis discovered high priority styling or logic violations.")
            base_score += 12

        # Final score calculation (clamp between 1 and 100)
        risk_score = min(max(base_score, 1), 100)
        
        # Rollback recommended if risk > 70
        rollback_suggested = risk_score > 70
        
        return {
            "risk_score": risk_score,
            "anomalies": anomalies,
            "rollback_suggested": rollback_suggested,
            "details": details
        }
