"""
Export utilities for workflow artifacts
"""
import json
from datetime import datetime
from typing import Dict, List, Any

def export_memo_to_markdown(memo: str, matter_name: str, run_metadata: Dict, 
                            authority_table: List[Dict], sources: List[Dict]) -> str:
    """Export research memo to Markdown format"""
    md = f"# Legal Research Memorandum\n\n"
    md += f"**Matter:** {matter_name}\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    md += f"**Workflow Run ID:** {run_metadata.get('run_id', 'N/A')}\n"
    md += f"**Research Question:** {run_metadata.get('research_question', 'N/A')}\n"
    md += f"**Jurisdiction(s):** {', '.join(run_metadata.get('jurisdictions', [])) if isinstance(run_metadata.get('jurisdictions'), list) else run_metadata.get('jurisdictions', 'N/A')}\n\n"
    md += "---\n\n"
    
    # Add memo content
    md += memo + "\n\n"
    
    # Add authority table
    md += "---\n\n"
    md += "## Authority Table\n\n"
    md += "| Authority | Type | Status | Jurisdiction |\n"
    md += "|-----------|------|--------|-------------|\n"
    
    for auth in authority_table:
        name = auth.get('name', auth.get('caption', 'N/A'))
        auth_type = auth.get('type', 'case')
        status = auth.get('precedential_status', 'unknown')
        jurisdiction = auth.get('jurisdiction_tag', 'N/A')
        md += f"| {name} | {auth_type} | {status} | {jurisdiction} |\n"
    
    md += "\n---\n\n"
    
    # Add sources
    md += "## Source Documents\n\n"
    for source in sources:
        md += f"### [{source.get('citation', source.get('id'))}] {source['document']}\n\n"
        if source.get('page'):
            md += f"**Page:** {source['page']}\n\n"
        md += f"**Relevance:** {source.get('similarity', 0):.2%}\n\n"
        md += f"**Excerpt:**\n\n"
        md += f"> {source.get('chunk_text', '')[:500]}...\n\n"
        md += "---\n\n"
    
    return md

def export_audit_pack_to_json(run_metadata: Dict, memo: str, authority_table: List[Dict],
                               issue_tree: List[Dict], verification_report: List[Dict],
                               provenance_bundle: Dict) -> str:
    """Export complete audit pack as JSON"""
    audit_pack = {
        'metadata': run_metadata,
        'memo': memo,
        'authority_table': authority_table,
        'issue_tree': issue_tree,
        'verification_report': verification_report,
        'provenance_bundle': provenance_bundle,
        'export_timestamp': datetime.now().isoformat()
    }
    
    return json.dumps(audit_pack, indent=2)

def export_verification_report_to_markdown(verification_report: List[Dict]) -> str:
    """Export verification report to Markdown"""
    md = "# Verification Report\n\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    
    passed_count = sum(1 for r in verification_report if r.get('pass_fail'))
    total_count = len(verification_report)
    
    md += f"**Overall Result:** {'✅ PASSED' if passed_count == total_count else '❌ FAILED'}\n"
    md += f"**Tests Passed:** {passed_count}/{total_count}\n\n"
    md += "---\n\n"
    
    for test in verification_report:
        status_icon = "✅" if test.get('pass_fail') else "❌"
        md += f"## {status_icon} {test['test']}\n\n"
        md += f"**Status:** {'PASSED' if test.get('pass_fail') else 'FAILED'}\n\n"
        md += f"**Details:** {test.get('details', 'N/A')}\n\n"
        if test.get('blocked_step'):
            md += f"**Blocked Step:** {test['blocked_step']}\n\n"
        md += "---\n\n"
    
    return md

def export_issue_tree_to_markdown(issue_tree: List[Dict]) -> str:
    """Export issue tree to Markdown"""
    md = "# Issue Tree Analysis\n\n"
    md += f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    md += "---\n\n"
    
    for idx, issue in enumerate(issue_tree, 1):
        md += f"## Issue {idx}: {issue.get('element', 'N/A')}\n\n"
        
        if issue.get('authority_ids'):
            md += f"**Governing Authorities:** {', '.join(issue['authority_ids'])}\n\n"
        
        if issue.get('uncertainty_flag'):
            md += f"**⚠️ Uncertainty Noted**\n\n"
        
        if issue.get('notes'):
            md += f"**Notes:**\n\n{issue['notes']}\n\n"
        
        md += "---\n\n"
    
    return md
