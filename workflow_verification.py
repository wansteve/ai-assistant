"""
Verification suite for workflow validation.
Implements HARD GATE tests that must pass before workflow can proceed.
"""
import re
from typing import Dict, List, Any, Tuple

class VerificationTest:
    """Base class for verification tests"""
    
    def __init__(self, test_id: str, name: str, description: str):
        self.test_id = test_id
        self.name = name
        self.description = description
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        """
        Run the verification test.
        Returns: (passed, details)
        """
        raise NotImplementedError

class CitationIntegrityTest(VerificationTest):
    """Verify all citations reference real sources"""
    
    def __init__(self):
        super().__init__(
            "citation_integrity",
            "Citation Integrity",
            "Every bracket citation [n] must reference a real source"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        memo = artifacts.get('research_memo', '')
        if not memo:
            return True, "No memo to verify"
        
        # Extract all citation numbers from memo
        citation_pattern = r'\[(\d+)\]'
        found_citations = set(int(m) for m in re.findall(citation_pattern, memo))
        
        # Get valid source IDs
        valid_source_ids = set(s.get('id', s.get('citation', -1)) for s in sources)
        
        # Check for invalid citations
        invalid_citations = found_citations - valid_source_ids
        
        if invalid_citations:
            return False, f"Invalid citations found: {sorted(invalid_citations)}. These do not map to any source."
        
        return True, f"All {len(found_citations)} citations are valid"

class QuoteAccuracyTest(VerificationTest):
    """Verify quoted strings appear in source chunks"""
    
    def __init__(self):
        super().__init__(
            "quote_accuracy",
            "Quote Accuracy",
            "All quoted text must appear verbatim in cited source chunks"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        rules = artifacts.get('rules', [])
        if not rules:
            return True, "No rules with quotes to verify"
        
        errors = []
        for rule in rules:
            quoted_text = rule.get('quoted_text', '')
            citation_id = rule.get('citation_id')
            
            if not quoted_text:
                continue
            
            # Find the source
            source = next((s for s in sources if s.get('id') == citation_id or s.get('citation') == citation_id), None)
            
            if not source:
                errors.append(f"Rule {rule.get('rule_id')}: Citation {citation_id} not found in sources")
                continue
            
            # Check if quote appears in source text
            source_text = source.get('chunk_text', source.get('full_text', ''))
            
            # Normalize whitespace for comparison
            normalized_quote = ' '.join(quoted_text.split())
            normalized_source = ' '.join(source_text.split())
            
            if normalized_quote not in normalized_source:
                errors.append(f"Rule {rule.get('rule_id')}: Quote not found verbatim in source {citation_id}")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, f"All {len(rules)} quoted rules verified against sources"

class PrecedentialStatusTest(VerificationTest):
    """Verify no negative-treatment authorities used as controlling"""
    
    def __init__(self):
        super().__init__(
            "precedential_status",
            "Precedential Status",
            "No authority with negative_treatment_found can be cited as controlling"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        validated_authorities = artifacts.get('validated_authorities', [])
        memo = artifacts.get('research_memo', '')
        
        if not validated_authorities:
            return True, "No validated authorities to check"
        
        # Find authorities with negative treatment
        negative_authorities = [
            auth for auth in validated_authorities 
            if auth.get('precedential_status') == 'negative_treatment_found'
        ]
        
        if not negative_authorities:
            return True, "No authorities with negative treatment"
        
        # Check if memo has "Adverse Authority" section
        has_adverse_section = 'adverse authority' in memo.lower() or 'negative treatment' in memo.lower()
        
        # Check if negative authorities appear in main analysis (not in adverse section)
        errors = []
        for auth in negative_authorities:
            auth_name = auth.get('name', '')
            # This is a simplified check - in production, would need more sophisticated parsing
            if auth_name in memo and not has_adverse_section:
                errors.append(f"Authority '{auth_name}' has negative treatment but no Adverse Authority section")
        
        if errors:
            return False, "; ".join(errors)
        
        if negative_authorities and not has_adverse_section:
            return False, f"{len(negative_authorities)} authorities with negative treatment but no Adverse Authority section in memo"
        
        return True, f"All {len(negative_authorities)} negative-treatment authorities properly disclosed"

class JurisdictionConsistencyTest(VerificationTest):
    """Verify authorities match selected jurisdictions"""
    
    def __init__(self):
        super().__init__(
            "jurisdiction_consistency",
            "Jurisdiction Consistency",
            "Memo must not cite out-of-jurisdiction authorities as controlling"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        locked_jurisdictions = artifacts.get('locked_jurisdictions', [])
        authority_candidates = artifacts.get('authority_candidates', [])
        memo = artifacts.get('research_memo', '')
        
        if not locked_jurisdictions or not authority_candidates:
            return True, "No jurisdictions or authorities to verify"
        
        # Find out-of-jurisdiction authorities
        out_of_jurisdiction = [
            auth for auth in authority_candidates
            if auth.get('jurisdiction_tag') not in locked_jurisdictions
        ]
        
        if not out_of_jurisdiction:
            return True, f"All authorities within {', '.join(locked_jurisdictions)}"
        
        # Check if out-of-jurisdiction authorities are labeled as "persuasive"
        errors = []
        for auth in out_of_jurisdiction:
            auth_name = auth.get('name', '')
            if auth_name in memo:
                # Check if marked as persuasive (simplified check)
                if 'persuasive' not in memo.lower():
                    errors.append(f"Authority '{auth_name}' from {auth.get('jurisdiction_tag')} not marked as persuasive")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "Out-of-jurisdiction authorities properly labeled"

class AdverseDisclosureTest(VerificationTest):
    """Verify adverse authority is disclosed in memo"""
    
    def __init__(self):
        super().__init__(
            "adverse_disclosure",
            "Adverse Disclosure",
            "If negative_treatment_found exists, memo must include Adverse Authority section"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        validated_authorities = artifacts.get('validated_authorities', [])
        memo = artifacts.get('research_memo', '')
        
        # Find authorities with negative treatment
        negative_authorities = [
            auth for auth in validated_authorities 
            if auth.get('precedential_status') == 'negative_treatment_found'
        ]
        
        if not negative_authorities:
            return True, "No adverse authorities to disclose"
        
        # Check for adverse authority section
        has_adverse_section = (
            'adverse authority' in memo.lower() or 
            'negative treatment' in memo.lower() or
            'adverse' in memo.lower()
        )
        
        if not has_adverse_section:
            return False, f"{len(negative_authorities)} authorities with negative treatment but no Adverse Authority section in memo"
        
        # Check if the authorities are mentioned
        mentioned_count = sum(1 for auth in negative_authorities if auth.get('name', '') in memo)
        
        return True, f"Adverse Authority section present, {mentioned_count}/{len(negative_authorities)} mentioned"

class ReasoningStructureTest(VerificationTest):
    """Verify conditional language and no outcome predictions"""
    
    def __init__(self):
        super().__init__(
            "reasoning_structure",
            "Reasoning Structure",
            "Application must use conditional markers and avoid outcome predictions"
        )
    
    def run(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Tuple[bool, str]:
        memo = artifacts.get('research_memo', '')
        
        if not memo:
            return True, "No memo to verify"
        
        # Banned outcome language
        banned_phrases = [
            'will win', 'will succeed', 'will prevail',
            'likely to win', 'likely succeed', 'likely prevail',
            'guaranteed', 'slam dunk', 'certain victory',
            'should win', 'definitely win'
        ]
        
        # Check for banned phrases (case-insensitive)
        memo_lower = memo.lower()
        found_banned = [phrase for phrase in banned_phrases if phrase in memo_lower]
        
        if found_banned:
            return False, f"Banned outcome language found: {', '.join(found_banned)}"
        
        # Check for conditional markers (should have at least some)
        conditional_markers = ['if', 'assuming', 'to the extent', 'may', 'could', 'might']
        conditional_count = sum(1 for marker in conditional_markers if marker in memo_lower)
        
        if conditional_count < 3:
            return False, f"Insufficient conditional language (found {conditional_count} markers)"
        
        return True, f"Appropriate conditional language used ({conditional_count} markers found)"

class VerificationSuite:
    """Suite of verification tests for workflow validation"""
    
    def __init__(self):
        self.tests = [
            CitationIntegrityTest(),
            QuoteAccuracyTest(),
            PrecedentialStatusTest(),
            JurisdictionConsistencyTest(),
            AdverseDisclosureTest(),
            ReasoningStructureTest()
        ]
    
    def run_all(self, artifacts: Dict[str, Any], sources: List[Dict]) -> Dict[str, Any]:
        """
        Run all verification tests.
        Returns: {
            'passed': bool,
            'results': [{'test': str, 'pass_fail': bool, 'details': str, 'blocked_step': str}],
            'correction_plan': str (if failed)
        }
        """
        results = []
        all_passed = True
        
        for test in self.tests:
            try:
                passed, details = test.run(artifacts, sources)
                results.append({
                    'test': test.name,
                    'test_id': test.test_id,
                    'pass_fail': passed,
                    'details': details,
                    'blocked_step': '' if passed else 'Phase 8 - Verification Suite'
                })
                
                if not passed:
                    all_passed = False
            except Exception as e:
                results.append({
                    'test': test.name,
                    'test_id': test.test_id,
                    'pass_fail': False,
                    'details': f"Test error: {str(e)}",
                    'blocked_step': 'Phase 8 - Verification Suite'
                })
                all_passed = False
        
        # Generate correction plan if any tests failed
        correction_plan = ""
        if not all_passed:
            failed_tests = [r for r in results if not r['pass_fail']]
            correction_plan = "The following verification tests failed and must be corrected:\n\n"
            
            for failed in failed_tests:
                correction_plan += f"- {failed['test']}: {failed['details']}\n"
            
            correction_plan += "\nRecommended corrections:\n"
            
            for failed in failed_tests:
                if failed['test_id'] == 'citation_integrity':
                    correction_plan += "- Review all citations in memo and ensure they map to valid sources\n"
                elif failed['test_id'] == 'quote_accuracy':
                    correction_plan += "- Verify all quoted text appears verbatim in source documents\n"
                elif failed['test_id'] == 'precedential_status':
                    correction_plan += "- Add 'Adverse Authority' section and move negative-treatment authorities there\n"
                elif failed['test_id'] == 'jurisdiction_consistency':
                    correction_plan += "- Label out-of-jurisdiction authorities as 'persuasive' or remove them\n"
                elif failed['test_id'] == 'adverse_disclosure':
                    correction_plan += "- Add 'Adverse Authority' section to memo disclosing negative treatment\n"
                elif failed['test_id'] == 'reasoning_structure':
                    correction_plan += "- Replace outcome predictions with conditional language (if/assuming/may)\n"
        
        return {
            'passed': all_passed,
            'results': results,
            'correction_plan': correction_plan if not all_passed else None
        }
