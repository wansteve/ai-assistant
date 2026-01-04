"""
Workflow #1: Verifiability-First Litigation Research Memo
Implements a multi-phase workflow for creating grounded legal research memos.
"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from workflow_engine import WorkflowDefinition, WorkflowStep, WorkflowRun, StepResult, StepStatus, WorkflowStatus
from workflow_verification import VerificationSuite

def create_litigation_workflow() -> WorkflowDefinition:
    """Create the litigation research memo workflow definition"""
    
    steps = [
        WorkflowStep(
            step_id="phase_0_intake",
            name="Human Intake & Framing",
            description="Validate inputs and frame the research question",
            phase_number=0,
            is_verifiable=False,
            requires_human_input=True
        ),
        WorkflowStep(
            step_id="phase_1_authority_grounding",
            name="Authority Grounding",
            description="Retrieve statutes/rules/doctrines from local documents",
            phase_number=1,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_2_case_law_retrieval",
            name="Case Law Retrieval",
            description="Retrieve relevant cases/opinions from local documents",
            phase_number=2,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_3_authority_validation",
            name="Authority Validation",
            description="Check for negative treatment signals in documents",
            phase_number=3,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_4_issue_decomposition",
            name="Issue Decomposition",
            description="Build issue tree with elements and sub-issues",
            phase_number=4,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_5_rule_extraction",
            name="Rule Extraction",
            description="Extract governing tests/elements/standards with quotes",
            phase_number=5,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_6_rule_application",
            name="Rule Application to Facts",
            description="Apply rules to facts with conditional framing",
            phase_number=6,
            is_verifiable=False
        ),
        WorkflowStep(
            step_id="phase_7_memo_drafting",
            name="Memo Drafting",
            description="Draft research memo with all required sections",
            phase_number=7,
            is_verifiable=False
        ),
        WorkflowStep(
            step_id="phase_8_verification",
            name="Verification Suite",
            description="Run HARD GATE verification tests",
            phase_number=8,
            is_verifiable=True
        ),
        WorkflowStep(
            step_id="phase_9_human_review",
            name="Human Review & Judgment",
            description="Mandatory human review before finalization",
            phase_number=9,
            requires_human_input=True
        ),
        WorkflowStep(
            step_id="phase_10_export",
            name="Export & Audit Pack",
            description="Generate final exports and audit bundle",
            phase_number=10
        )
    ]
    
    input_schema = {
        "required": [
            "research_question",
            "jurisdictions",
            "court_level",
            "matter_posture"
        ],
        "optional": [
            "known_facts",
            "adverse_authority_awareness",
            "risk_posture",
            "memo_format_preference"
        ],
        "fields": {
            "research_question": {"type": "text", "label": "Research Question"},
            "jurisdictions": {"type": "multi_select", "label": "Jurisdiction(s)"},
            "court_level": {"type": "select", "label": "Court Level", "options": ["trial", "appellate", "supreme"]},
            "matter_posture": {"type": "select", "label": "Matter Posture", "options": ["MTD", "SJ", "appeal", "discovery", "trial", "other"]},
            "known_facts": {"type": "textarea", "label": "Known Facts (optional)"},
            "adverse_authority_awareness": {"type": "boolean", "label": "Aware of adverse authority?"},
            "risk_posture": {"type": "select", "label": "Risk Posture", "options": ["conservative", "neutral", "aggressive"], "default": "neutral"},
            "memo_format_preference": {"type": "select", "label": "Memo Format", "options": ["IRAC", "CREAC", "narrative"], "default": "IRAC"}
        }
    }
    
    return WorkflowDefinition(
        workflow_id="litigation_research_memo_v1",
        name="Verifiability-First Litigation Research Memo",
        description="Multi-phase workflow for creating grounded legal research memos with citation verification",
        input_schema=input_schema,
        steps=steps,
        version="1.0"
    )

class LitigationWorkflowExecutor:
    """Executes the litigation research memo workflow"""
    
    def __init__(self, doc_processor, anthropic_client, model: str):
        self.doc_processor = doc_processor
        self.client = anthropic_client
        self.model = model
        self.verification_suite = VerificationSuite()
    
    def execute_step(self, run: WorkflowRun, step_index: int, workflow_def: WorkflowDefinition) -> StepResult:
        """Execute a single workflow step"""
        step = workflow_def.steps[step_index]
        step_result = StepResult(
            step_id=step.step_id,
            status=StepStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        try:
            # Route to appropriate phase handler
            if step.step_id == "phase_0_intake":
                self._execute_phase_0(run, step_result)
            elif step.step_id == "phase_1_authority_grounding":
                self._execute_phase_1(run, step_result)
            elif step.step_id == "phase_2_case_law_retrieval":
                self._execute_phase_2(run, step_result)
            elif step.step_id == "phase_3_authority_validation":
                self._execute_phase_3(run, step_result)
            elif step.step_id == "phase_4_issue_decomposition":
                self._execute_phase_4(run, step_result)
            elif step.step_id == "phase_5_rule_extraction":
                self._execute_phase_5(run, step_result)
            elif step.step_id == "phase_6_rule_application":
                self._execute_phase_6(run, step_result)
            elif step.step_id == "phase_7_memo_drafting":
                self._execute_phase_7(run, step_result)
            elif step.step_id == "phase_8_verification":
                self._execute_phase_8(run, step_result)
            elif step.step_id == "phase_9_human_review":
                # This step is handled by UI - just mark as pending human input
                step_result.status = StepStatus.PENDING
                step_result.logs.append("Waiting for human review")
            elif step.step_id == "phase_10_export":
                self._execute_phase_10(run, step_result)
            
            step_result.finished_at = datetime.now().isoformat()
            
        except Exception as e:
            step_result.status = StepStatus.FAILED
            step_result.errors.append(str(e))
            step_result.finished_at = datetime.now().isoformat()
        
        return step_result
    
    def _execute_phase_0(self, run: WorkflowRun, step_result: StepResult):
        """Phase 0: Human Intake & Framing"""
        inputs = run.inputs
        
        # Check required fields
        required_fields = ["research_question", "jurisdictions", "court_level", "matter_posture"]
        missing = [f for f in required_fields if not inputs.get(f)]
        
        if missing:
            step_result.status = StepStatus.FAILED
            step_result.errors.append(f"Missing required fields: {', '.join(missing)}")
            return
        
        # Lock the inputs
        step_result.artifacts['locked_question'] = inputs['research_question']
        step_result.artifacts['locked_jurisdictions'] = inputs['jurisdictions'] if isinstance(inputs['jurisdictions'], list) else [inputs['jurisdictions']]
        step_result.artifacts['court_level'] = inputs['court_level']
        step_result.artifacts['posture'] = inputs['matter_posture']
        
        # Process known facts into assumptions
        known_facts = inputs.get('known_facts', '')
        if known_facts:
            assumptions = [f.strip() for f in known_facts.split('\n') if f.strip()]
        else:
            assumptions = ["Factual record to be developed"]
        step_result.artifacts['assumptions'] = assumptions
        
        # Check if clarification needed
        if not known_facts or len(assumptions) < 2:
            step_result.artifacts['clarifying_questions'] = [
                "What are the key facts of this matter?",
                "Are there any specific precedents you're aware of?",
                "What is the desired outcome or relief sought?"
            ]
            step_result.logs.append("Insufficient facts provided - clarifying questions generated")
        
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append(f"Research question locked: {inputs['research_question']}")
        step_result.logs.append(f"Jurisdictions locked: {', '.join(step_result.artifacts['locked_jurisdictions'])}")
    
    def _execute_phase_1(self, run: WorkflowRun, step_result: StepResult):
        """Phase 1: Authority Grounding"""
        # Get locked question from phase 0
        phase_0_artifacts = run.step_results[0].artifacts if run.step_results else {}
        question = phase_0_artifacts.get('locked_question', run.inputs.get('research_question'))
        jurisdictions = phase_0_artifacts.get('locked_jurisdictions', [run.inputs.get('jurisdictions', '')])
        
        # Search for relevant authorities in documents
        search_query = f"{question} statute rule doctrine law {' '.join(jurisdictions)}"
        results = self.doc_processor.search_documents(search_query, top_k=10)
        
        if not results:
            step_result.status = StepStatus.FAILED
            step_result.errors.append("Not supported by provided documents. No relevant authorities found.")
            step_result.logs.append("Recommendation: Upload statutes, regulations, or legal treatises relevant to this matter")
            return
        
        # Use LLM to extract authority candidates from results
        authority_candidates = []
        sources_used = []
        
        for idx, result in enumerate(results, 1):
            prompt = f"""Based on this legal document excerpt, identify if it contains statutory, regulatory, or doctrinal authority relevant to: "{question}"

Document: {result['doc_title']}
Excerpt: {result['chunk_text']}

If this contains relevant legal authority:
1. What type is it? (statute/rule/doctrine/case)
2. What is the specific authority name/citation?
3. What is the jurisdiction?
4. Extract the most relevant quote (verbatim, under 100 words)

Respond in this exact format:
TYPE: [statute/rule/doctrine/case/none]
NAME: [name or N/A]
JURISDICTION: [jurisdiction or N/A]
QUOTE: "[exact quote]" or N/A

If not relevant legal authority, respond: TYPE: none"""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse response
            if "TYPE: none" not in response_text and "TYPE:" in response_text:
                lines = response_text.strip().split('\n')
                auth_type = None
                auth_name = None
                jurisdiction = None
                quote = None
                
                for line in lines:
                    if line.startswith("TYPE:"):
                        auth_type = line.replace("TYPE:", "").strip()
                    elif line.startswith("NAME:"):
                        auth_name = line.replace("NAME:", "").strip()
                    elif line.startswith("JURISDICTION:"):
                        jurisdiction = line.replace("JURISDICTION:", "").strip()
                    elif line.startswith("QUOTE:"):
                        quote = line.replace("QUOTE:", "").strip().strip('"')
                
                if auth_type and auth_type != "none" and auth_name and auth_name != "N/A":
                    authority_candidates.append({
                        'authority_id': f"auth_{len(authority_candidates) + 1}",
                        'type': auth_type,
                        'name': auth_name,
                        'jurisdiction_tag': jurisdiction if jurisdiction and jurisdiction != "N/A" else jurisdictions[0],
                        'supporting_quotes': [{
                            'quote': quote if quote and quote != "N/A" else result['chunk_text'][:200],
                            'citation_id': idx
                        }]
                    })
                    
                    sources_used.append({
                        'id': idx,
                        'citation': idx,
                        'document': result['doc_title'],
                        'page': result.get('page'),
                        'chunk_text': result['chunk_text'],
                        'similarity': result['similarity']
                    })
        
        # Verification: each candidate must have >=1 supporting quote
        if not authority_candidates:
            step_result.status = StepStatus.FAILED
            step_result.errors.append("Not supported by provided documents. No statutory/regulatory authorities extracted.")
            return
        
        step_result.artifacts['authority_candidates'] = authority_candidates
        step_result.sources_used = sources_used
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append(f"Found {len(authority_candidates)} authority candidates")
    
    def _execute_phase_2(self, run: WorkflowRun, step_result: StepResult):
        """Phase 2: Case Law Retrieval"""
        phase_0_artifacts = run.step_results[0].artifacts if run.step_results else {}
        question = phase_0_artifacts.get('locked_question', run.inputs.get('research_question'))
        
        # Search for case law
        search_query = f"{question} court opinion case holding"
        results = self.doc_processor.search_documents(search_query, top_k=10)
        
        cases = []
        sources_used = []
        
        for idx, result in enumerate(results, 1):
            # Look for case indicators in the text
            chunk_text = result['chunk_text']
            
            # Simple heuristics for case identification
            has_v = ' v. ' in chunk_text or ' v ' in chunk_text
            has_court_terms = any(term in chunk_text.lower() for term in ['court', 'held', 'opinion', 'judge', 'justice'])
            
            if has_v or has_court_terms:
                # Use LLM to extract case details
                prompt = f"""Analyze this legal document excerpt to determine if it contains a court opinion or case.

Document: {result['doc_title']}
Excerpt: {chunk_text}

If this is a court case/opinion, extract:
CASE_NAME: [Caption, e.g., "Smith v. Jones"]
COURT: [Court name]
YEAR: [Year decided, or "unknown"]
KEY_QUOTE: "[Most relevant quote, verbatim, under 100 words]"

If NOT a case, respond: NOT_A_CASE"""
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=400,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                response_text = message.content[0].text
                
                if "NOT_A_CASE" not in response_text and "CASE_NAME:" in response_text:
                    lines = response_text.strip().split('\n')
                    case_name = None
                    court = None
                    year = None
                    key_quote = None
                    
                    for line in lines:
                        if line.startswith("CASE_NAME:"):
                            case_name = line.replace("CASE_NAME:", "").strip()
                        elif line.startswith("COURT:"):
                            court = line.replace("COURT:", "").strip()
                        elif line.startswith("YEAR:"):
                            year = line.replace("YEAR:", "").strip()
                        elif line.startswith("KEY_QUOTE:"):
                            key_quote = line.replace("KEY_QUOTE:", "").strip().strip('"')
                    
                    if case_name:
                        case_id = f"case_{len(cases) + 1}"
                        cases.append({
                            'case_id': case_id,
                            'caption': case_name,
                            'court': court if court else "Unknown",
                            'year': year if year and year != "unknown" else None,
                            'jurisdiction_tag': phase_0_artifacts.get('locked_jurisdictions', ['Unknown'])[0],
                            'chunk_citations': [idx],
                            'key_quotes': [key_quote] if key_quote else []
                        })
                        
                        sources_used.append({
                            'id': idx,
                            'citation': idx,
                            'document': result['doc_title'],
                            'page': result.get('page'),
                            'chunk_text': result['chunk_text'],
                            'similarity': result['similarity']
                        })
        
        if cases:
            step_result.artifacts['cases'] = cases
            step_result.sources_used = sources_used
            step_result.status = StepStatus.COMPLETED
            step_result.logs.append(f"Retrieved {len(cases)} cases from documents")
        else:
            step_result.status = StepStatus.COMPLETED
            step_result.artifacts['cases'] = []
            step_result.logs.append("No case law found in provided documents - proceeding with statutory/doctrinal analysis only")
    
    def _execute_phase_3(self, run: WorkflowRun, step_result: StepResult):
        """Phase 3: Authority Validation - Check for negative treatment"""
        cases = run.step_results[2].artifacts.get('cases', []) if len(run.step_results) > 2 else []
        authority_candidates = run.step_results[1].artifacts.get('authority_candidates', []) if len(run.step_results) > 1 else []
        
        all_authorities = cases + authority_candidates
        validated_authorities = []
        
        for authority in all_authorities:
            auth_name = authority.get('caption', authority.get('name', ''))
            
            # Search for negative treatment signals
            negative_signals = ['overruled', 'abrogated', 'superseded', 'distinguished', 'limited', 'vacated', 'reversed']
            search_query = f"{auth_name} {' OR '.join(negative_signals)}"
            
            results = self.doc_processor.search_documents(search_query, top_k=5)
            
            precedential_status = "unknown"
            evidence_citations = []
            
            for result in results:
                text_lower = result['chunk_text'].lower()
                
                # Check for negative signals
                found_negative = [sig for sig in negative_signals if sig in text_lower and auth_name.lower() in text_lower]
                
                if found_negative:
                    precedential_status = "negative_treatment_found"
                    evidence_citations.append({
                        'signal': found_negative[0],
                        'citation_id': result.get('citation', len(evidence_citations) + 1),
                        'excerpt': result['chunk_text'][:200]
                    })
                    break
                
                # Check for positive treatment
                positive_signals = ['followed', 'affirmed', 'adopted', 'applied', 'good law']
                found_positive = [sig for sig in positive_signals if sig in text_lower and auth_name.lower() in text_lower]
                
                if found_positive and precedential_status == "unknown":
                    precedential_status = "treated_as_good_law_in_docs"
            
            validated_authorities.append({
                **authority,
                'precedential_status': precedential_status,
                'evidence_citations': evidence_citations
            })
        
        step_result.artifacts['validated_authorities'] = validated_authorities
        step_result.status = StepStatus.COMPLETED
        
        negative_count = sum(1 for a in validated_authorities if a.get('precedential_status') == 'negative_treatment_found')
        step_result.logs.append(f"Validated {len(validated_authorities)} authorities - {negative_count} with negative treatment")
    
    def _execute_phase_4(self, run: WorkflowRun, step_result: StepResult):
        """Phase 4: Issue Decomposition"""
        phase_0_artifacts = run.step_results[0].artifacts
        question = phase_0_artifacts.get('locked_question')
        validated_authorities = run.step_results[3].artifacts.get('validated_authorities', [])
        
        # Use LLM to build issue tree
        authorities_text = "\n".join([
            f"- {a.get('name', a.get('caption', 'Unknown'))} ({a.get('type', 'case')})"
            for a in validated_authorities[:10]  # Limit to top 10
        ])
        
        prompt = f"""Given this legal research question and available authorities, decompose it into a structured issue tree.

Question: {question}

Available Authorities:
{authorities_text}

Create an issue tree with:
1. Main legal issue
2. Sub-issues or elements that must be proven
3. For each element, identify which authority governs it
4. Note any uncertainties or gaps

Respond in this format:
ISSUE 1: [Main issue description]
  ELEMENT 1.1: [Element description]
    AUTHORITY: [Authority name from list above]
    UNCERTAINTY: [Any gaps or uncertainties, or "None"]
  ELEMENT 1.2: [Element description]
    AUTHORITY: [Authority name]
    UNCERTAINTY: [Any gaps]

Continue for all issues and elements."""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        
        # Parse issue tree (simplified parsing)
        issue_tree = []
        current_issue = None
        issue_counter = 0
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('ISSUE'):
                issue_counter += 1
                if current_issue:
                    issue_tree.append(current_issue)
                current_issue = {
                    'issue_id': f"issue_{issue_counter}",
                    'element': line.split(':', 1)[1].strip() if ':' in line else line,
                    'authority_ids': [],
                    'supporting_citations': [],
                    'uncertainty_flag': False,
                    'notes': ''
                }
            elif line.startswith('ELEMENT') and current_issue:
                # This is a sub-element, could enhance parsing here
                current_issue['notes'] += line + '\n'
            elif line.startswith('AUTHORITY:') and current_issue:
                auth_name = line.replace('AUTHORITY:', '').strip()
                # Find matching authority
                matching_auth = next((a for a in validated_authorities if auth_name in a.get('name', a.get('caption', ''))), None)
                if matching_auth:
                    auth_id = matching_auth.get('authority_id', matching_auth.get('case_id'))
                    if auth_id and auth_id not in current_issue['authority_ids']:
                        current_issue['authority_ids'].append(auth_id)
            elif line.startswith('UNCERTAINTY:') and current_issue:
                uncertainty_text = line.replace('UNCERTAINTY:', '').strip()
                if uncertainty_text and uncertainty_text != "None":
                    current_issue['uncertainty_flag'] = True
                    current_issue['notes'] += f"Uncertainty: {uncertainty_text}\n"
        
        if current_issue:
            issue_tree.append(current_issue)
        
        step_result.artifacts['issue_tree'] = issue_tree
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append(f"Created issue tree with {len(issue_tree)} main issues")
    
    def _execute_phase_5(self, run: WorkflowRun, step_result: StepResult):
        """Phase 5: Rule Extraction"""
        issue_tree = run.step_results[4].artifacts.get('issue_tree', [])
        validated_authorities = run.step_results[3].artifacts.get('validated_authorities', [])
        all_sources = run.step_results[1].sources_used + run.step_results[2].sources_used
        
        rules = []
        
        for issue in issue_tree:
            for auth_id in issue['authority_ids']:
                # Find the authority
                authority = next((a for a in validated_authorities if a.get('authority_id') == auth_id or a.get('case_id') == auth_id), None)
                
                if not authority:
                    continue
                
                # Get quotes from authority
                quotes = authority.get('supporting_quotes', authority.get('key_quotes', []))
                
                for quote_data in quotes:
                    if isinstance(quote_data, dict):
                        quote_text = quote_data.get('quote', '')
                        citation_id = quote_data.get('citation_id')
                    else:
                        quote_text = quote_data
                        citation_id = None
                    
                    if quote_text:
                        rules.append({
                            'rule_id': f"rule_{len(rules) + 1}",
                            'quoted_text': quote_text,
                            'court': authority.get('court', 'N/A'),
                            'citation_id': citation_id,
                            'precedential_status': authority.get('precedential_status', 'unknown'),
                            'issue_id': issue['issue_id']
                        })
        
        step_result.artifacts['rules'] = rules
        step_result.sources_used = all_sources
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append(f"Extracted {len(rules)} rules with quoted text")
    
    def _execute_phase_6(self, run: WorkflowRun, step_result: StepResult):
        """Phase 6: Rule Application to Facts"""
        issue_tree = run.step_results[4].artifacts.get('issue_tree', [])
        rules = run.step_results[5].artifacts.get('rules', [])
        assumptions = run.step_results[0].artifacts.get('assumptions', [])
        
        applications = []
        
        for issue in issue_tree:
            # Get rules for this issue
            issue_rules = [r for r in rules if r.get('issue_id') == issue['issue_id']]
            
            if not issue_rules:
                continue
            
            # Use LLM to apply rules to facts
            rules_text = "\n".join([f"- {r['quoted_text']}" for r in issue_rules[:3]])
            facts_text = "\n".join([f"- {a}" for a in assumptions])
            
            prompt = f"""Apply these legal rules to the following facts using conditional language.

RULES:
{rules_text}

FACTS:
{facts_text}

For issue: {issue['element']}

Provide:
1. FACT MAPPING: How do the facts map to rule elements? (Use "If X is established, then...")
2. GAPS: What facts are missing?
3. UNCERTAINTIES: What is unclear?
4. ADVERSE READINGS: How might opposing counsel interpret these facts?

Use conditional language: "if", "assuming", "to the extent", "may", "could"
Do NOT predict outcomes like "will win" or "likely to succeed"."""
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse response
            fact_mapping = ""
            gaps = []
            uncertainties = []
            adverse_readings = []
            
            current_section = None
            for line in response_text.split('\n'):
                line = line.strip()
                if 'FACT MAPPING' in line:
                    current_section = 'mapping'
                elif 'GAPS' in line:
                    current_section = 'gaps'
                elif 'UNCERTAINTIES' in line:
                    current_section = 'uncertainties'
                elif 'ADVERSE' in line:
                    current_section = 'adverse'
                elif line:
                    if current_section == 'mapping':
                        fact_mapping += line + " "
                    elif current_section == 'gaps' and line.startswith('-'):
                        gaps.append(line[1:].strip())
                    elif current_section == 'uncertainties' and line.startswith('-'):
                        uncertainties.append(line[1:].strip())
                    elif current_section == 'adverse' and line.startswith('-'):
                        adverse_readings.append(line[1:].strip())
            
            applications.append({
                'issue_id': issue['issue_id'],
                'fact_mapping': fact_mapping.strip(),
                'gaps': gaps,
                'uncertainties': uncertainties,
                'adverse_readings': adverse_readings
            })
        
        step_result.artifacts['applications'] = applications
        step_result.status = StepStatus.COMPLETED
        
        # Check if too many gaps
        total_gaps = sum(len(app['gaps']) + len(app['uncertainties']) for app in applications)
        if total_gaps > 5:
            step_result.logs.append(f"WARNING: {total_gaps} gaps/uncertainties identified - may need more facts before drafting")
        else:
            step_result.logs.append(f"Applied rules to facts - {total_gaps} gaps identified")
    
    def _execute_phase_7(self, run: WorkflowRun, step_result: StepResult):
        """Phase 7: Memo Drafting"""
        # Gather all artifacts
        phase_0 = run.step_results[0].artifacts
        issue_tree = run.step_results[4].artifacts.get('issue_tree', [])
        rules = run.step_results[5].artifacts.get('rules', [])
        applications = run.step_results[6].artifacts.get('applications', [])
        validated_authorities = run.step_results[3].artifacts.get('validated_authorities', [])
        all_sources = run.step_results[1].sources_used + run.step_results[2].sources_used
        
        # Check for adverse authorities
        adverse_authorities = [a for a in validated_authorities if a.get('precedential_status') == 'negative_treatment_found']
        
        # Build comprehensive prompt
        question = phase_0['locked_question']
        jurisdictions = ', '.join(phase_0['locked_jurisdictions'])
        memo_format = run.inputs.get('memo_format_preference', 'IRAC')
        
        # Format sources for citation
        sources_text = "\n".join([
            f"[{s['citation']}] {s['document']}" + (f" - Page {s['page']}" if s.get('page') else "")
            for s in all_sources
        ])
        
        # Format rules
        rules_text = "\n".join([
            f"- {r['quoted_text']} [{r.get('citation_id', '?')}]"
            for r in rules[:10]
        ])
        
        # Format applications
        applications_text = "\n\n".join([
            f"Issue: {next((i['element'] for i in issue_tree if i['issue_id'] == app['issue_id']), 'Unknown')}\n" +
            f"Analysis: {app['fact_mapping']}\n" +
            f"Gaps: {', '.join(app['gaps']) if app['gaps'] else 'None identified'}"
            for app in applications
        ])
        
        prompt = f"""Draft a legal research memorandum using {memo_format} format.

QUESTION PRESENTED
{question}

JURISDICTION
{jurisdictions}

GOVERNING RULES (with citations)
{rules_text}

ANALYSIS
{applications_text}

AVAILABLE SOURCES (for citation)
{sources_text}

REQUIREMENTS:
1. Include these sections:
   - Question Presented
   - Short Answer (qualified, conditional - no predictions)
   - Background Law (with citations to sources)
   - Analysis (issue-by-issue, with citations)
   - {"Adverse Authority / Negative Treatment" if adverse_authorities else ""}
   - Open Questions

2. Citation rules:
   - Every legal claim MUST cite a source using [citation number]
   - Use ONLY the citations provided above
   - Multiple citations for same point: [1][3][5]

3. Language rules:
   - Use conditional language: "if", "assuming", "to the extent", "may", "could"
   - NO outcome predictions: Never say "will win", "likely to succeed", "should prevail"
   - NO strategic advice: Focus on legal analysis only

4. Short Answer must be qualified, e.g.:
   "If the facts establish X, then under [authority], the element of Y may be satisfied, subject to..."

{"5. MANDATORY: Include 'Adverse Authority' section discussing these authorities with negative treatment: " + ', '.join([a.get('name', a.get('caption')) for a in adverse_authorities]) if adverse_authorities else ""}

Draft the complete memorandum now."""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        memo_text = message.content[0].text
        
        step_result.artifacts['research_memo'] = memo_text
        step_result.sources_used = all_sources
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append(f"Drafted memorandum ({len(memo_text)} characters)")
    
    def _execute_phase_8(self, run: WorkflowRun, step_result: StepResult):
        """Phase 8: Verification Suite - HARD GATE"""
        # Collect all artifacts for verification
        all_artifacts = {}
        all_sources = []
        
        for prev_result in run.step_results[:8]:  # All results up to this point
            all_artifacts.update(prev_result.artifacts)
            all_sources.extend(prev_result.sources_used)
        
        # Run verification suite
        verification_results = self.verification_suite.run_all(all_artifacts, all_sources)
        
        step_result.artifacts['verification_report'] = verification_results['results']
        step_result.artifacts['verification_passed'] = verification_results['passed']
        
        if verification_results['passed']:
            step_result.status = StepStatus.COMPLETED
            step_result.logs.append("All verification tests passed")
        else:
            step_result.status = StepStatus.FAILED
            step_result.errors.append("Verification failed - see correction plan")
            step_result.artifacts['correction_plan'] = verification_results['correction_plan']
            step_result.logs.append(f"Failed {sum(1 for r in verification_results['results'] if not r['pass_fail'])} verification tests")
    
    def _execute_phase_10(self, run: WorkflowRun, step_result: StepResult):
        """Phase 10: Export & Audit Pack"""
        # Collect all final artifacts
        memo = run.step_results[7].artifacts.get('research_memo', '')
        authority_table = run.step_results[3].artifacts.get('validated_authorities', [])
        issue_tree = run.step_results[4].artifacts.get('issue_tree', [])
        verification_report = run.step_results[8].artifacts.get('verification_report', [])
        all_sources = []
        
        for result in run.step_results:
            all_sources.extend(result.sources_used)
        
        # Create provenance bundle
        provenance_bundle = {
            'memo': memo,
            'sources': all_sources,
            'citations_mapping': self._build_citations_mapping(memo, all_sources)
        }
        
        step_result.artifacts['final_memo'] = memo
        step_result.artifacts['authority_table'] = authority_table
        step_result.artifacts['issue_tree'] = issue_tree
        step_result.artifacts['verification_report'] = verification_report
        step_result.artifacts['provenance_bundle'] = provenance_bundle
        step_result.artifacts['run_metadata'] = {
            'run_id': run.run_id,
            'matter_id': run.matter_id,
            'workflow_id': run.workflow_id,
            'started_at': run.started_at,
            'completed_at': datetime.now().isoformat(),
            'research_question': run.inputs.get('research_question'),
            'jurisdictions': run.inputs.get('jurisdictions')
        }
        
        step_result.status = StepStatus.COMPLETED
        step_result.logs.append("Export artifacts prepared")
    
    def _build_citations_mapping(self, memo: str, sources: List[Dict]) -> Dict:
        """Build mapping of citations to source chunks"""
        citation_pattern = r'\[(\d+)\]'
        found_citations = set(int(m) for m in re.findall(citation_pattern, memo))
        
        mapping = {}
        for citation_num in found_citations:
            source = next((s for s in sources if s.get('id') == citation_num or s.get('citation') == citation_num), None)
            if source:
                mapping[citation_num] = {
                    'document': source['document'],
                    'page': source.get('page'),
                    'excerpt': source.get('chunk_text', '')[:300]
                }
        
        return mapping
