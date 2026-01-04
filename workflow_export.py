from datetime import datetime
import json


def export_memo_to_markdown(memo_text: str, run_metadata: dict, audit_pack: dict) -> str:
    """Export research memo to Markdown format"""
    
    md = f"# Legal Research Memorandum\n\n"
    md += f"**Matter:** {run_metadata.get('matter_name', 'N/A')}\n\n"
    md += f"**Research Question:** {run_metadata['inputs'].get('research_question', 'N/A')}\n\n"
    md += f"**Jurisdiction(s):** {', '.join(run_metadata['inputs'].get('jurisdictions', []))}\n\n"
    md += f"**Court Level:** {run_metadata['inputs'].get('court_level', 'N/A')}\n\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    md += f"**Workflow Run ID:** {run_metadata.get('run_id', 'N/A')}\n\n"
    md += "---\n\n"
    
    # Add memo content
    md += memo_text + "\n\n"
    
    # Add verification status
    verification = audit_pack.get('verification_report', [])
    if verification:
        md += "---\n\n"
        md += "## Verification Report\n\n"
        
        passed_tests = [v for v in verification if v.get('passed')]
        failed_tests = [v for v in verification if not v.get('passed')]
        
        md += f"**Status:** {'✅ ALL TESTS PASSED' if not failed_tests else '❌ VERIFICATION FAILED'}\n\n"
        md += f"**Passed:** {len(passed_tests)}/{len(verification)} tests\n\n"
        
        if failed_tests:
            md += "### Failed Tests\n\n"
            for test in failed_tests:
                md += f"- **{test['test_name']}**: {test['details']}\n"
                if test.get('blocked_step'):
                    md += f"  - *Requires re-running: {test['blocked_step']}*\n"
            md += "\n"
        
        md += "### All Tests\n\n"
        for test in verification:
            status = "✅" if test.get('passed') else "❌"
            md += f"{status} **{test['test_name']}**: {test['details']}\n\n"
    
    return md


def export_authority_table_to_markdown(audit_pack: dict) -> str:
    """Export authority table to Markdown"""
    
    md = "# Authority Table\n\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    md += "---\n\n"
    
    # Statutes/Rules
    authorities = audit_pack.get('authority_table', {}).get('authorities', [])
    if authorities:
        md += "## Statutes, Rules & Regulations\n\n"
        md += "| Authority | Type | Jurisdiction | Status |\n"
        md += "|-----------|------|--------------|--------|\n"
        
        for auth in authorities:
            name = auth.get('name', 'Unknown')
            auth_type = auth.get('type', 'N/A')
            jurisdiction = auth.get('jurisdiction_tag', 'N/A')
            status = auth.get('precedential_status', 'Unknown')
            md += f"| {name} | {auth_type} | {jurisdiction} | {status} |\n"
        
        md += "\n"
    
    # Cases
    cases = audit_pack.get('authority_table', {}).get('cases', [])
    if cases:
        md += "## Case Law\n\n"
        md += "| Case | Court | Year | Jurisdiction | Status |\n"
        md += "|------|-------|------|--------------|--------|\n"
        
        for case in cases:
            caption = case.get('caption', 'Unknown')
            court = case.get('court', 'N/A')
            year = case.get('year', 'N/A')
            jurisdiction = case.get('jurisdiction_tag', 'N/A')
            status = case.get('precedential_status', 'Unknown')
            md += f"| {caption} | {court} | {year} | {jurisdiction} | {status} |\n"
        
        md += "\n"
    
    return md


def export_issue_tree_to_markdown(audit_pack: dict) -> str:
    """Export issue tree to Markdown"""
    
    md = "# Issue Tree\n\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    md += "---\n\n"
    
    issue_tree = audit_pack.get('issue_tree', [])
    
    if not issue_tree:
        md += "*No issues identified*\n"
        return md
    
    for issue in issue_tree:
        issue_id = issue.get('issue_id', 'Unknown')
        element = issue.get('element', 'N/A')
        authority_ids = issue.get('authority_ids', [])
        uncertainty = "⚠️" if issue.get('uncertainty_flag') else ""
        
        md += f"## {issue_id} {uncertainty}\n\n"
        md += f"**Element:** {element}\n\n"
        md += f"**Governing Authorities:** {', '.join(authority_ids)}\n\n"
        md += f"**Supporting Citations:** {issue.get('supporting_citations', 'N/A')}\n\n"
        
        if issue.get('notes'):
            md += f"**Notes:** {issue['notes']}\n\n"
        
        md += "---\n\n"
    
    return md


def export_audit_pack_to_json(audit_pack: dict) -> str:
    """Export complete audit pack as JSON"""
    return json.dumps(audit_pack, indent=2)


def export_complete_report_to_markdown(workflow_run, audit_pack: dict, matter_name: str) -> str:
    """Export complete workflow report with all components"""
    
    md = f"# Complete Workflow Report\n\n"
    md += f"**Matter:** {matter_name}\n\n"
    md += f"**Workflow:** {workflow_run.workflow_id}\n\n"
    md += f"**Run ID:** {workflow_run.run_id}\n\n"
    md += f"**Status:** {workflow_run.status}\n\n"
    md += f"**Started:** {workflow_run.started_at}\n\n"
    if workflow_run.finished_at:
        md += f"**Finished:** {workflow_run.finished_at}\n\n"
    md += "---\n\n"
    
    # Table of Contents
    md += "## Table of Contents\n\n"
    md += "1. [Research Question & Inputs](#research-question--inputs)\n"
    md += "2. [Research Memorandum](#research-memorandum)\n"
    md += "3. [Authority Table](#authority-table)\n"
    md += "4. [Issue Tree](#issue-tree)\n"
    md += "5. [Verification Report](#verification-report)\n"
    md += "6. [Workflow Steps](#workflow-steps)\n"
    md += "\n---\n\n"
    
    # Research Question & Inputs
    md += "## Research Question & Inputs\n\n"
    inputs = workflow_run.inputs
    md += f"**Research Question:** {inputs.get('research_question', 'N/A')}\n\n"
    md += f"**Jurisdiction(s):** {', '.join(inputs.get('jurisdictions', []))}\n\n"
    md += f"**Court Level:** {inputs.get('court_level', 'N/A')}\n\n"
    md += f"**Matter Posture:** {inputs.get('matter_posture', 'N/A')}\n\n"
    
    if inputs.get('known_facts'):
        md += f"**Known Facts:**\n\n{inputs['known_facts']}\n\n"
    
    md += f"**Risk Posture:** {inputs.get('risk_posture', 'N/A')}\n\n"
    md += f"**Memo Format:** {inputs.get('memo_format', 'N/A')}\n\n"
    md += "---\n\n"
    
    # Research Memorandum
    md += "## Research Memorandum\n\n"
    memo_text = audit_pack.get('memo', '')
    if memo_text:
        md += memo_text + "\n\n"
    else:
        md += "*Memo not generated*\n\n"
    md += "---\n\n"
    
    # Authority Table
    md += "## Authority Table\n\n"
    authorities = audit_pack.get('authority_table', {}).get('authorities', [])
    cases = audit_pack.get('authority_table', {}).get('cases', [])
    
    if authorities:
        md += "### Statutes, Rules & Regulations\n\n"
        for auth in authorities:
            md += f"- **{auth.get('name', 'Unknown')}** ({auth.get('type', 'N/A')})\n"
            md += f"  - Jurisdiction: {auth.get('jurisdiction_tag', 'N/A')}\n"
            md += f"  - Status: {auth.get('precedential_status', 'Unknown')}\n\n"
    
    if cases:
        md += "### Case Law\n\n"
        for case in cases:
            md += f"- **{case.get('caption', 'Unknown')}**\n"
            md += f"  - Court: {case.get('court', 'N/A')}\n"
            md += f"  - Year: {case.get('year', 'N/A')}\n"
            md += f"  - Jurisdiction: {case.get('jurisdiction_tag', 'N/A')}\n"
            md += f"  - Status: {case.get('precedential_status', 'Unknown')}\n\n"
    
    md += "---\n\n"
    
    # Issue Tree
    md += "## Issue Tree\n\n"
    issue_tree = audit_pack.get('issue_tree', [])
    if issue_tree:
        for issue in issue_tree:
            md += f"### {issue.get('issue_id', 'Unknown')}\n\n"
            md += f"**Element:** {issue.get('element', 'N/A')}\n\n"
            md += f"**Authorities:** {', '.join(issue.get('authority_ids', []))}\n\n"
            if issue.get('uncertainty_flag'):
                md += "⚠️ **Uncertainty Flag Set**\n\n"
    else:
        md += "*No issues identified*\n\n"
    md += "---\n\n"
    
    # Verification Report
    md += "## Verification Report\n\n"
    verification = audit_pack.get('verification_report', [])
    if verification:
        passed_tests = [v for v in verification if v.get('passed')]
        failed_tests = [v for v in verification if not v.get('passed')]
        
        md += f"**Overall Status:** {'✅ PASSED' if not failed_tests else '❌ FAILED'}\n\n"
        md += f"**Tests Passed:** {len(passed_tests)}/{len(verification)}\n\n"
        
        for test in verification:
            status = "✅ PASSED" if test.get('passed') else "❌ FAILED"
            md += f"### {test['test_name']} - {status}\n\n"
            md += f"{test['details']}\n\n"
    else:
        md += "*Verification not completed*\n\n"
    md += "---\n\n"
    
    # Workflow Steps
    md += "## Workflow Steps\n\n"
    for step_result in workflow_run.step_results:
        md += f"### {step_result.step_id}\n\n"
        md += f"**Status:** {step_result.status}\n\n"
        md += f"**Started:** {step_result.started_at}\n\n"
        if step_result.finished_at:
            md += f"**Finished:** {step_result.finished_at}\n\n"
        
        if step_result.logs:
            md += "**Logs:**\n"
            for log in step_result.logs:
                md += f"- {log}\n"
            md += "\n"
        
        if step_result.errors:
            md += "**Errors:**\n"
            for error in step_result.errors:
                md += f"- ❌ {error}\n"
            md += "\n"
        
        md += "---\n\n"
    
    return md
