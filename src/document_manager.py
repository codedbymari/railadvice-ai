import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import uuid
import threading


class EnhancedFileDocumentManager:
    def __init__(self, docs_dir="./documents"):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

        # Separate directories for organization
        self.content_dir = self.docs_dir / "content"
        self.content_dir.mkdir(exist_ok=True)

        # External folders (projects + regulations)
        self.projects_dir = Path("./projects")
        self.regulations_dir = Path("./regulations")

        self.index_file = self.docs_dir / "document_index.json"
        self.search_index_file = self.docs_dir / "search_index.json"

        # Thread lock for concurrent access
        self._lock = threading.Lock()

        self.load_index()
        self.load_search_index()

    # ---------------------------
    # Index management
    # ---------------------------
    def load_index(self):
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                self.index = json.load(f)
        else:
            self.index = {
                "documents": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "2.0",
                },
            }

    def load_search_index(self):
        if self.search_index_file.exists():
            with open(self.search_index_file, "r", encoding="utf-8") as f:
                self.search_index = json.load(f)
        else:
            self.search_index = {
                "by_type": {},
                "by_category": {},
                "by_tags": {},
                "words": {},
            }

    def save_index(self):
        with self._lock:
            self.index["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)

    def save_search_index(self):
        with self._lock:
            with open(self.search_index_file, "w", encoding="utf-8") as f:
                json.dump(self.search_index, f, indent=2, ensure_ascii=False)

    # ---------------------------
    # Document operations
    # ---------------------------
    def update_search_index(self, doc_id: str, doc_data: Dict, remove: bool = False):
        if remove:
            for type_docs in self.search_index["by_type"].values():
                if isinstance(type_docs, list) and doc_id in type_docs:
                    type_docs.remove(doc_id)

            for cat_docs in self.search_index["by_category"].values():
                if isinstance(cat_docs, list) and doc_id in cat_docs:
                    cat_docs.remove(doc_id)

            for tag_docs in self.search_index["by_tags"].values():
                if isinstance(tag_docs, list) and doc_id in tag_docs:
                    tag_docs.remove(doc_id)
            return

        doc_type = doc_data.get("type", "general")
        category = doc_data.get("category", "general")
        tags = doc_data.get("tags", [])

        if doc_type not in self.search_index["by_type"]:
            self.search_index["by_type"][doc_type] = []
        if doc_id not in self.search_index["by_type"][doc_type]:
            self.search_index["by_type"][doc_type].append(doc_id)

        if category not in self.search_index["by_category"]:
            self.search_index["by_category"][category] = []
        if doc_id not in self.search_index["by_category"][category]:
            self.search_index["by_category"][category].append(doc_id)

        for tag in tags:
            if tag not in self.search_index["by_tags"]:
                self.search_index["by_tags"][tag] = []
            if doc_id not in self.search_index["by_tags"][tag]:
                self.search_index["by_tags"][tag].append(doc_id)

    def add_document(
        self,
        title: str,
        content: str,
        doc_type: str = "general",
        category: str = "general",
        tags: List[str] = None,
        metadata: Dict = None,
    ) -> str:
        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        document_data = {
            "id": doc_id,
            "title": title,
            "type": doc_type,
            "category": category,
            "tags": tags or [],
            "created_at": timestamp,
            "updated_at": timestamp,
            "file_path": f"{doc_id}.json",
            "metadata": metadata or {},
        }

        content_file = self.content_dir / f"{doc_id}.json"
        content_data = {
            "id": doc_id,
            "title": title,
            "content": content,
            "created_at": timestamp,
        }

        with open(content_file, "w", encoding="utf-8") as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)

        self.index["documents"][doc_id] = document_data
        self.update_search_index(doc_id, document_data)

        self.save_index()
        self.save_search_index()

        print(f"✅ Document added: {title} (ID: {doc_id})")
        return doc_id

    def get_document(self, doc_id: str) -> Optional[Dict]:
        if doc_id not in self.index["documents"]:
            return None

        doc_info = self.index["documents"][doc_id]
        content_file = self.content_dir / doc_info["file_path"]

        if not content_file.exists():
            return None

        with open(content_file, "r", encoding="utf-8") as f:
            content_data = json.load(f)

        return {**doc_info, "content": content_data["content"]}

    def list_documents(self, limit: int = 100) -> List[Dict]:
        docs = list(self.index["documents"].values())
        docs.sort(key=lambda x: x["created_at"], reverse=True)
        return docs[:limit]

    def search_documents(
        self,
        query: str = None,
        doc_type: str = None,
        category: str = None,
        tags: List[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        candidate_ids = set(self.index["documents"].keys())

        if doc_type and doc_type in self.search_index["by_type"]:
            candidate_ids &= set(self.search_index["by_type"][doc_type])

        if category and category in self.search_index["by_category"]:
            candidate_ids &= set(self.search_index["by_category"][category])

        if tags:
            tag_ids = set()
            for tag in tags:
                if tag in self.search_index["by_tags"]:
                    tag_ids.update(self.search_index["by_tags"][tag])
            candidate_ids &= tag_ids

        if query:
            query_lower = query.lower()
            filtered_ids = set()

            for doc_id in candidate_ids:
                doc_info = self.index["documents"][doc_id]
                if query_lower in doc_info["title"].lower():
                    filtered_ids.add(doc_id)
                    continue
                if any(query_lower in tag.lower() for tag in doc_info["tags"]):
                    filtered_ids.add(doc_id)
                    continue
                try:
                    doc = self.get_document(doc_id)
                    if doc and query_lower in doc["content"].lower():
                        filtered_ids.add(doc_id)
                except:
                    continue
            candidate_ids = filtered_ids

        results = []
        for doc_id in list(candidate_ids)[:limit]:
            if doc_id in self.index["documents"]:
                doc = self.get_document(doc_id)
                if doc:
                    results.append(doc)

        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    def remove_document(self, doc_id: str) -> bool:
        if doc_id not in self.index["documents"]:
            print(f"❌ Document {doc_id} not found")
            return False

        doc_info = self.index["documents"][doc_id]
        content_file = self.content_dir / doc_info["file_path"]
        if content_file.exists():
            content_file.unlink()

        self.update_search_index(doc_id, doc_info, remove=True)
        removed_doc = self.index["documents"].pop(doc_id)

        self.save_index()
        self.save_search_index()

        print(f"✅ Document removed: {removed_doc['title']}")
        return True

    def update_document(self, doc_id: str, **kwargs) -> bool:
        if doc_id not in self.index["documents"]:
            return False

        doc_info = self.index["documents"][doc_id]

        if "content" in kwargs:
            content_file = self.content_dir / doc_info["file_path"]
            if content_file.exists():
                with open(content_file, "r", encoding="utf-8") as f:
                    content_data = json.load(f)
                content_data["content"] = kwargs["content"]
                content_data["updated_at"] = datetime.now().isoformat()
                with open(content_file, "w", encoding="utf-8") as f:
                    json.dump(content_data, f, indent=2, ensure_ascii=False)

        old_doc_info = doc_info.copy()
        for key, value in kwargs.items():
            if key != "content" and key in doc_info:
                doc_info[key] = value

        doc_info["updated_at"] = datetime.now().isoformat()

        if any(key in kwargs for key in ["type", "category", "tags"]):
            self.update_search_index(doc_id, old_doc_info, remove=True)
            self.update_search_index(doc_id, doc_info)

        self.save_index()
        self.save_search_index()
        return True

    def get_stats(self) -> Dict:
        total = len(self.index["documents"])
        types = {}
        categories = {}
        for doc in self.index["documents"].values():
            doc_type = doc.get("type", "unknown")
            types[doc_type] = types.get(doc_type, 0) + 1
            category = doc.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        return {
            "total_documents": total,
            "document_types": types,
            "categories": categories,
        }

    # ---------------------------
    # Extra loaders (projects + regulations)
    # ---------------------------
    def load_external_documents(self, base_dir="."):
        """Load external JSON documents from projects and regulations folders"""
        base = Path(base_dir)

        # Projects
        if self.projects_dir.exists():
            for file in self.projects_dir.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.add_document(
                        title=file.stem,
                        content=json.dumps(data, indent=2, ensure_ascii=False),
                        doc_type="project",
                        category="projects",
                    )
                    print(f"📂 Loaded project file: {file.name}")
                except Exception as e:
                    print(f"⚠️ Failed to load project file {file}: {e}")

        # Regulations
        if self.regulations_dir.exists():
            for file in self.regulations_dir.glob("*.json"):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.add_document(
                        title=file.stem,
                        content=json.dumps(data, indent=2, ensure_ascii=False),
                        doc_type="regulation",
                        category="regulations",
                    )
                    print(f"📂 Loaded regulation file: {file.name}")
                except Exception as e:
                    print(f"⚠️ Failed to load regulation file {file}: {e}")

    def load_all_documents(self):
        """FIXED: Load all documents WITH content, not just metadata"""
        all_docs = []
        
        for doc_id in self.index["documents"].keys():
            doc = self.get_document(doc_id)  # This loads content from file
            if doc:
                all_docs.append(doc)
            else:
                print(f"⚠️ Warning: Could not load content for document {doc_id}")
        
        return all_docs

    def reload_documents(self):
        self.load_index()
        self.load_search_index()
        print("🔄 Document manager reloaded documents from disk")