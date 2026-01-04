import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Any
from enum import Enum

class WorkflowStatus(Enum):
    """Status of a workflow run"""
    PENDING = "pending"
    RUNNING = "running"
    NEEDS_INPUT = "needs_input"
    COMPLETED = "completed"
    FAILED = "failed"

class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StepResult:
    """Result of a workflow step execution"""
    step_id: str
    status: StepStatus
    artifacts: Dict[str, Any] = field(default_factory=dict)
    sources_used: List[Dict] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: str = None
    finished_at: str = None
    
    def to_dict(self):
        return {
            'step_id': self.step_id,
            'status': self.status.value,
            'artifacts': self.artifacts,
            'sources_used': self.sources_used,
            'logs': self.logs,
            'errors': self.errors,
            'started_at': self.started_at,
            'finished_at': self.finished_at
        }
    
    @classmethod
    def from_dict(cls, data):
        data['status'] = StepStatus(data['status'])
        return cls(**data)

@dataclass
class WorkflowStep:
    """Definition of a workflow step"""
    step_id: str
    name: str
    description: str
    phase_number: int
    is_verifiable: bool = True
    requires_human_input: bool = False
    
    def to_dict(self):
        return asdict(self)

@dataclass
class WorkflowDefinition:
    """Definition of a workflow"""
    workflow_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    steps: List[WorkflowStep]
    version: str = "1.0"
    
    def to_dict(self):
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'steps': [step.to_dict() for step in self.steps],
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data):
        steps = [WorkflowStep(**step) for step in data['steps']]
        data['steps'] = steps
        return cls(**data)

@dataclass
class WorkflowRun:
    """A running or completed workflow instance"""
    run_id: str
    matter_id: str
    workflow_id: str
    status: WorkflowStatus
    current_step: int = 0
    inputs: Dict[str, Any] = field(default_factory=dict)
    step_results: List[StepResult] = field(default_factory=list)
    started_at: str = None
    finished_at: str = None
    error_message: str = None
    correction_plan: str = None
    
    def to_dict(self):
        return {
            'run_id': self.run_id,
            'matter_id': self.matter_id,
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'current_step': self.current_step,
            'inputs': self.inputs,
            'step_results': [sr.to_dict() for sr in self.step_results],
            'started_at': self.started_at,
            'finished_at': self.finished_at,
            'error_message': self.error_message,
            'correction_plan': self.correction_plan
        }
    
    @classmethod
    def from_dict(cls, data):
        data['status'] = WorkflowStatus(data['status'])
        data['step_results'] = [StepResult.from_dict(sr) for sr in data.get('step_results', [])]
        return cls(**data)

class WorkflowEngine:
    """Minimal orchestration engine for workflows"""
    
    def __init__(self, storage_dir="workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_file = self.storage_dir / "workflow_definitions.json"
        self.runs_dir = self.storage_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load workflow definitions
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self._load_workflows()
    
    def _load_workflows(self):
        """Load workflow definitions from disk"""
        if self.workflows_file.exists():
            with open(self.workflows_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workflows = {w['workflow_id']: WorkflowDefinition.from_dict(w) for w in data}
    
    def _save_workflows(self):
        """Save workflow definitions to disk"""
        data = [wf.to_dict() for wf in self.workflows.values()]
        with open(self.workflows_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def register_workflow(self, workflow: WorkflowDefinition):
        """Register a new workflow definition"""
        self.workflows[workflow.workflow_id] = workflow
        self._save_workflows()
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """List all available workflows"""
        return list(self.workflows.values())
    
    def create_run(self, matter_id: str, workflow_id: str, inputs: Dict[str, Any]) -> WorkflowRun:
        """Create a new workflow run"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        run_id = str(uuid.uuid4())
        run = WorkflowRun(
            run_id=run_id,
            matter_id=matter_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            inputs=inputs,
            started_at=datetime.now().isoformat()
        )
        
        # Initialize step results
        for step in workflow.steps:
            step_result = StepResult(
                step_id=step.step_id,
                status=StepStatus.PENDING
            )
            run.step_results.append(step_result)
        
        self._save_run(run)
        return run
    
    def get_run(self, run_id: str) -> Optional[WorkflowRun]:
        """Get a workflow run by ID"""
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.exists():
            return None
        
        with open(run_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return WorkflowRun.from_dict(data)
    
    def list_runs(self, matter_id: Optional[str] = None) -> List[WorkflowRun]:
        """List all workflow runs, optionally filtered by matter"""
        runs = []
        for run_file in self.runs_dir.glob("*.json"):
            with open(run_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                run = WorkflowRun.from_dict(data)
                if matter_id is None or run.matter_id == matter_id:
                    runs.append(run)
        
        # Sort by started_at (newest first)
        runs.sort(key=lambda x: x.started_at, reverse=True)
        return runs
    
    def _save_run(self, run: WorkflowRun):
        """Save a workflow run to disk"""
        run_file = self.runs_dir / f"{run.run_id}.json"
        with open(run_file, 'w', encoding='utf-8') as f:
            json.dump(run.to_dict(), f, indent=2)
    
    def update_run_status(self, run_id: str, status: WorkflowStatus, 
                         error_message: str = None, correction_plan: str = None):
        """Update the status of a workflow run"""
        run = self.get_run(run_id)
        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            if correction_plan:
                run.correction_plan = correction_plan
            if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                run.finished_at = datetime.now().isoformat()
            self._save_run(run)
    
    def update_step_result(self, run_id: str, step_index: int, step_result: StepResult):
        """Update the result of a specific step"""
        run = self.get_run(run_id)
        if run and 0 <= step_index < len(run.step_results):
            run.step_results[step_index] = step_result
            run.current_step = step_index
            self._save_run(run)
    
    def get_run_artifacts_dir(self, run_id: str) -> Path:
        """Get the directory for storing run artifacts"""
        artifacts_dir = self.runs_dir / f"{run_id}_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        return artifacts_dir
    
    def save_artifact(self, run_id: str, artifact_name: str, content: Any):
        """Save an artifact to the run's artifacts directory"""
        artifacts_dir = self.get_run_artifacts_dir(run_id)
        
        # Determine file extension based on content type
        if isinstance(content, (dict, list)):
            file_path = artifacts_dir / f"{artifact_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2)
        else:
            file_path = artifacts_dir / f"{artifact_name}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(content))
        
        return str(file_path)
    
    def load_artifact(self, run_id: str, artifact_name: str) -> Optional[Any]:
        """Load an artifact from the run's artifacts directory"""
        artifacts_dir = self.get_run_artifacts_dir(run_id)
        
        # Try JSON first
        json_path = artifacts_dir / f"{artifact_name}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Try text
        txt_path = artifacts_dir / f"{artifact_name}.txt"
        if txt_path.exists():
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a workflow run and its artifacts"""
        run_file = self.runs_dir / f"{run_id}.json"
        artifacts_dir = self.get_run_artifacts_dir(run_id)
        
        try:
            # Delete run file
            if run_file.exists():
                run_file.unlink()
            
            # Delete artifacts directory
            if artifacts_dir.exists():
                import shutil
                shutil.rmtree(artifacts_dir)
            
            return True
        except Exception as e:
            print(f"Error deleting run {run_id}: {str(e)}")
            return False
