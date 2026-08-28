import os
import re
import math
from typing import List, Dict, Any, Optional
from app.knowledge.knowledge_seed import KNOWLEDGE_DOCUMENTS


class RoadSafeKnowledgeStore:
    """
    Manages vector embeddings and semantic search for RoadSafe knowledge base.
    Uses ChromaDB persistent collection if available; falls back to an embedded cosine-vector store.
    """

    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.docs = {d["id"]: d for d in KNOWLEDGE_DOCUMENTS}
        self._init_store()

    def _init_store(self):
        try:
            import chromadb
            # Initialize persistent or ephemeral ChromaDB client
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
            os.makedirs(db_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=db_dir)
            self.collection = self.chroma_client.get_or_create_collection(
                name="roadsafe_knowledge",
                metadata={"description": "RoadSafe GPS emergency and services knowledge base"}
            )
            # Seed documents into ChromaDB
            ids = [d["id"] for d in KNOWLEDGE_DOCUMENTS]
            documents = [d["content"] for d in KNOWLEDGE_DOCUMENTS]
            metadatas = [{"title": d["title"], "category": d["category"]} for d in KNOWLEDGE_DOCUMENTS]

            # Upsert into ChromaDB
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        except Exception:
            # Fallback to internal TF-IDF Cosine Vector Search if chromadb has environmental constraints
            self.chroma_client = None
            self.collection = None

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text)]

    def _compute_tf_idf(self, query: str, doc_text: str, tags: List[str]) -> float:
        q_tokens = set(self._tokenize(query))
        if not q_tokens:
            return 0.0
        doc_tokens = self._tokenize(doc_text) + [t.lower() for t in tags] * 3
        if not doc_tokens:
            return 0.0

        score = 0.0
        for token in q_tokens:
            count = doc_tokens.count(token)
            if count > 0:
                score += (1.0 + math.log(count)) * (1.5 if token in [t.lower() for t in tags] else 1.0)
        return score / (math.sqrt(len(doc_tokens)) + 1.0)

    def query(self, question: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top relevant knowledge chunks using ChromaDB or cosine similarity.
        """
        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[question],
                    n_results=min(n_results, len(KNOWLEDGE_DOCUMENTS))
                )
                retrieved = []
                if results and results.get("ids") and results["ids"][0]:
                    for idx, doc_id in enumerate(results["ids"][0]):
                        distance = results["distances"][0][idx] if "distances" in results and results["distances"] else 0.5
                        content = results["documents"][0][idx]
                        metadata = results["metadatas"][0][idx]
                        # In Chroma, cosine distance < 1.0 indicates relevant content
                        if distance < 1.3:
                            retrieved.append({
                                "id": doc_id,
                                "title": metadata.get("title", ""),
                                "category": metadata.get("category", ""),
                                "content": content,
                                "score": 1.0 - (distance / 2.0)
                            })
                if retrieved:
                    return retrieved
            except Exception:
                pass

        # Fallback ranking
        scored = []
        for doc in KNOWLEDGE_DOCUMENTS:
            score = self._compute_tf_idf(question, doc["content"], doc.get("tags", []))
            if score > 0.05:
                scored.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "category": doc["category"],
                    "content": doc["content"],
                    "score": score
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:n_results]


knowledge_store = RoadSafeKnowledgeStore()


class AIKnowledgeService:
    @staticmethod
    async def ask_assistant(question: str, role: str = "CUSTOMER") -> Dict[str, Any]:
        """
        Executes grounded RAG pipeline:
        1. Semantic retrieval from ChromaDB collection
        2. Strict relevance threshold evaluation
        3. Grounded answer generation
        """
        trimmed_q = question.strip()
        if not trimmed_q:
            return {
                "answer": "Please ask a question about roadside assistance, vehicle emergencies, safety, or RoadSafe services.",
                "sources": [],
                "grounded": True
            }

        # 1. Retrieve relevant knowledge chunks
        retrieved_docs = knowledge_store.query(trimmed_q, n_results=3)

        # 2. Check for grounding relevance
        if not retrieved_docs:
            return {
                "answer": (
                    "I am sorry, but I do not have relevant information in the RoadSafe knowledge base regarding that topic. "
                    "For emergencies, vehicle breakdowns, or service pricing, please submit an assistance request or contact RoadSafe 24/7 dispatch."
                ),
                "sources": [],
                "grounded": False
            }

        # 3. Grounded Synthesis
        primary_doc = retrieved_docs[0]
        sources = [{"title": d["title"], "category": d["category"]} for d in retrieved_docs]

        # Extract synthesis
        answer_parts = [
            f"Here is the verified information from RoadSafe's knowledge base regarding **{primary_doc['title']}**:\n",
            primary_doc["content"]
        ]

        if len(retrieved_docs) > 1 and retrieved_docs[1]["score"] > 0.15:
            sec_doc = retrieved_docs[1]
            if sec_doc["id"] != primary_doc["id"]:
                answer_parts.append(f"\n\n**Additional Relevant Context ({sec_doc['title']}):**\n" + sec_doc["content"])

        answer_parts.append("\n\n*Tip: You can request immediate roadside assistance directly from the Assist tab in your app.*")

        return {
            "answer": "\n".join(answer_parts),
            "sources": sources,
            "grounded": True
        }
