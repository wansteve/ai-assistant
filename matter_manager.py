import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional

@dataclass
class MatterHistory:
    timestamp: str
    action_type: str  # research, summary, draft, upload
    description: str
    output: str
    sources_used: List[int] = field(default_factory=list)

@dataclass
class Matter:
    matter_id: str
    matter_name: str
    client_name: str
    description: str
    doc_ids: List[str] = field(default_factory=list)
    history: List[MatterHistory] = field(default_factory=list)
    created_date: str = None
    last_modified: str = None
    
    def to_dict(self):
        return {
            'matter_id': self.matter_id,
            'matter_name': self.matter_name,
            'client_name': self.client_name,
            'description': self.description,
            'doc_ids': self.doc_ids,
            'history': [asdict(h) for h in self.history],
            'created_date': self.created_date,
            'last_modified': self.last_modified
        }
    
    @classmethod
    def from_dict(cls, data):
        history = [MatterHistory(**h) for h in data.get('history', [])]
        return cls(
            matter_id=data['matter_id'],
            matter_name=data['matter_name'],
            client_name=data['client_name'],
            description=data['description'],
            doc_ids=data.get('doc_ids', []),
            history=history,
            created_date=data.get('created_date'),
            last_modified=data.get('last_modified')
        )

class MatterManager:
    def __init__(self, storage_dir="matters"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.matters_file = self.storage_dir / "matters.json"
        self._load_matters()
    
    def _load_matters(self):
        """Load all matters from disk"""
        if self.matters_file.exists():
            with open(self.matters_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.matters = {m['matter_id']: Matter.from_dict(m) for m in data}
        else:
            self.matters = {}
    
    def _save_matters(self):
        """Save all matters to disk"""
        data = [matter.to_dict() for matter in self.matters.values()]
        with open(self.matters_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def create_matter(self, matter_name: str, client_name: str, description: str) -> Matter:
        """Create a new matter"""
        matter_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        matter = Matter(
            matter_id=matter_id,
            matter_name=matter_name,
            client_name=client_name,
            description=description,
            created_date=now,
            last_modified=now
        )
        
        self.matters[matter_id] = matter
        self._save_matters()
        return matter
    
    def get_matter(self, matter_id: str) -> Optional[Matter]:
        """Get a matter by ID"""
        return self.matters.get(matter_id)
    
    def list_matters(self) -> List[Matter]:
        """List all matters"""
        matters = list(self.matters.values())
        # Sort by last modified (newest first)
        matters.sort(key=lambda x: x.last_modified, reverse=True)
        return matters
    
    def add_document_to_matter(self, matter_id: str, doc_id: str):
        """Add a document to a matter"""
        matter = self.matters.get(matter_id)
        if matter and doc_id not in matter.doc_ids:
            matter.doc_ids.append(doc_id)
            matter.last_modified = datetime.now().isoformat()
            self._save_matters()
    
    def remove_document_from_matter(self, matter_id: str, doc_id: str):
        """Remove a document from a matter"""
        matter = self.matters.get(matter_id)
        if matter and doc_id in matter.doc_ids:
            matter.doc_ids.remove(doc_id)
            matter.last_modified = datetime.now().isoformat()
            self._save_matters()
    
    def add_history(self, matter_id: str, action_type: str, description: str, 
                    output: str, sources_used: List[int] = None):
        """Add a history entry to a matter"""
        matter = self.matters.get(matter_id)
        if matter:
            history_entry = MatterHistory(
                timestamp=datetime.now().isoformat(),
                action_type=action_type,
                description=description,
                output=output,
                sources_used=sources_used or []
            )
            matter.history.append(history_entry)
            matter.last_modified = datetime.now().isoformat()
            self._save_matters()
    
    def delete_matter(self, matter_id: str) -> bool:
        """Delete a matter"""
        if matter_id in self.matters:
            del self.matters[matter_id]
            self._save_matters()
            return True
        return False
    
    def update_matter(self, matter_id: str, matter_name: str = None, 
                     client_name: str = None, description: str = None):
        """Update matter details"""
        matter = self.matters.get(matter_id)
        if matter:
            if matter_name:
                matter.matter_name = matter_name
            if client_name:
                matter.client_name = client_name
            if description:
                matter.description = description
            matter.last_modified = datetime.now().isoformat()
            self._save_matters()
            return True
        return False