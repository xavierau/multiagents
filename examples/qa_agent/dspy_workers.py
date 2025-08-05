"""
DSPy-powered Q&A System Workers with Codebase RAG
"""
import os
import ast
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import dspy
from multiagents import worker, dspy_worker


class CodebaseIndexer:
    """Index the MultiAgents codebase for RAG."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.index = {}
        self._build_index()
    
    def _build_index(self):
        """Build an index of all Python files in the project."""
        print("🔍 Indexing codebase...")
        
        # Index Python files
        python_files = list(self.project_root.rglob("*.py"))
        for file_path in python_files:
            # Skip certain directories
            if any(skip in str(file_path) for skip in ['.venv', '__pycache__', '.git', 'htmlcov']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST to extract classes and functions
                try:
                    tree = ast.parse(content)
                    self._extract_ast_info(file_path, tree, content)
                except SyntaxError:
                    # Still index the raw content if AST parsing fails
                    self._index_raw_file(file_path, content)
                    
            except Exception as e:
                print(f"⚠️ Could not index {file_path}: {e}")
        
        # Index markdown documentation
        md_files = list(self.project_root.rglob("*.md"))
        for file_path in md_files:
            if '.git' not in str(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._index_markdown(file_path, content)
                except Exception as e:
                    print(f"⚠️ Could not index {file_path}: {e}")
        
        print(f"✅ Indexed {len(self.index)} code entities")
    
    def _extract_ast_info(self, file_path: Path, tree: ast.AST, content: str):
        """Extract classes, functions, and their docstrings from AST."""
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get the docstring
                docstring = ast.get_docstring(node) or ""
                
                # Get the source code of the function/class
                try:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
                    source = '\n'.join(lines[start_line:end_line])
                except:
                    source = f"# {node.name} definition"
                
                # Determine entity type
                entity_type = "class" if isinstance(node, ast.ClassDef) else "function"
                
                # Create index entry
                key = f"{file_path.relative_to(self.project_root)}::{node.name}"
                self.index[key] = {
                    "type": entity_type,
                    "name": node.name,
                    "file": str(file_path.relative_to(self.project_root)),
                    "docstring": docstring,
                    "source": source,
                    "description": f"{entity_type.title()} {node.name} from {file_path.name}"
                }
    
    def _index_raw_file(self, file_path: Path, content: str):
        """Index raw file content when AST parsing fails."""
        key = str(file_path.relative_to(self.project_root))
        self.index[key] = {
            "type": "file",
            "name": file_path.name,
            "file": str(file_path.relative_to(self.project_root)),
            "content": content[:2000],  # First 2000 chars
            "description": f"File {file_path.name}"
        }
    
    def _index_markdown(self, file_path: Path, content: str):
        """Index markdown documentation."""
        key = str(file_path.relative_to(self.project_root))
        
        # Extract sections from markdown
        sections = []
        current_section = ""
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section.strip())
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        if current_section:
            sections.append(current_section.strip())
        
        self.index[key] = {
            "type": "documentation",
            "name": file_path.name,
            "file": str(file_path.relative_to(self.project_root)),
            "content": content[:3000],  # First 3000 chars
            "sections": sections[:5],  # First 5 sections
            "description": f"Documentation {file_path.name}"
        }
    
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the codebase index for relevant information."""
        query_lower = query.lower()
        results = []
        
        # Search through index
        for key, item in self.index.items():
            score = 0
            
            # Check name match
            if query_lower in item["name"].lower():
                score += 10
            
            # Check docstring match
            if "docstring" in item and query_lower in item["docstring"].lower():
                score += 5
            
            # Check content match  
            if "content" in item and query_lower in item["content"].lower():
                score += 3
            
            # Check file path match
            if query_lower in item["file"].lower():
                score += 2
            
            if score > 0:
                results.append({
                    "key": key,
                    "score": score,
                    "item": item
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]


# Global codebase indexer (initialized once)
CODEBASE_INDEXER = None

def get_codebase_indexer():
    """Get or create the codebase indexer."""
    global CODEBASE_INDEXER
    if CODEBASE_INDEXER is None:
        # Find project root (look for pyproject.toml)
        current_dir = Path(__file__).parent
        while current_dir != current_dir.parent:
            if (current_dir / "pyproject.toml").exists():
                CODEBASE_INDEXER = CodebaseIndexer(str(current_dir))
                break
            current_dir = current_dir.parent
        else:
            # Fallback to current directory
            CODEBASE_INDEXER = CodebaseIndexer(str(Path(__file__).parent.parent.parent))
    
    return CODEBASE_INDEXER


# DSPy Signatures
class QuestionClassifier(dspy.Signature):
    """Classify and clarify user questions about the MultiAgents codebase."""
    
    question = dspy.InputField(desc="User's question about the codebase")
    
    needs_clarification = dspy.OutputField(desc="Boolean: true if question needs clarification")
    topics = dspy.OutputField(desc="List of relevant topics (e.g., ['workers', 'orchestrator', 'events'])")
    clarification_message = dspy.OutputField(desc="Message asking for clarification if needed")
    search_queries = dspy.OutputField(desc="List of search queries for the codebase")


class CodebaseRetriever(dspy.Signature):
    """Retrieve relevant code from the MultiAgents codebase."""
    
    question = dspy.InputField(desc="User's technical question")
    search_queries = dspy.InputField(desc="List of search queries")
    retrieved_code = dspy.InputField(desc="Retrieved code snippets and documentation")
    
    relevant_code = dspy.OutputField(desc="Most relevant code snippets with explanations")
    code_explanation = dspy.OutputField(desc="Detailed explanation of how the code works")
    usage_examples = dspy.OutputField(desc="Practical usage examples if applicable")


class ResponseValidator(dspy.Signature):
    """Validate technical responses about the codebase."""
    
    question = dspy.InputField(desc="Original user question")
    response = dspy.InputField(desc="Generated response")
    code_context = dspy.InputField(desc="Retrieved code context")
    
    is_accurate = dspy.OutputField(desc="Boolean: true if response is technically accurate")
    is_complete = dspy.OutputField(desc="Boolean: true if response fully answers the question")
    improvement_suggestions = dspy.OutputField(desc="Suggestions for improvement if needed")
    final_approved = dspy.OutputField(desc="Boolean: true if response is approved")


@dspy_worker("dspy_coordinator")
async def dspy_coordinator_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """DSPy-powered coordinator that classifies questions and determines search strategy."""
    
    # Configure DSPy with Gemini
    try:
        import google.generativeai as genai
        from dspy import LM
        
        # Try to get API key from environment or context
        api_key = os.getenv("GOOGLE_API_KEY") or context.get("google_api_key")
        if not api_key:
            return {
                "error": "GOOGLE_API_KEY not found in environment variables",
                "needs_clarification": True
            }
        
        # Configure Gemini
        lm = LM(model="gemini/gemini-1.5-pro", api_key=api_key)
        dspy.configure(lm=lm)
        
    except Exception as e:
        return {
            "error": f"Failed to configure DSPy with Gemini: {e}",
            "needs_clarification": True
        }
    
    question = context.get("question", "")
    if not question:
        return {
            "error": "No question provided",
            "needs_clarification": True
        }
    
    try:
        # Use DSPy to classify the question
        classifier = dspy.Predict(QuestionClassifier)
        result = classifier(question=question)
        
        # Parse the results
        import json
        try:
            topics = json.loads(result.topics) if isinstance(result.topics, str) else result.topics
            search_queries = json.loads(result.search_queries) if isinstance(result.search_queries, str) else result.search_queries
        except:
            topics = [result.topics] if result.topics else []
            search_queries = [question]  # Fallback
        
        return {
            "needs_clarification": result.needs_clarification.lower() == "true",
            "topics": topics,
            "clarification_message": result.clarification_message if result.needs_clarification.lower() == "true" else "",
            "search_queries": search_queries,
            "original_question": question
        }
        
    except Exception as e:
        # Fallback to simple classification
        return {
            "needs_clarification": False,
            "topics": ["general"],
            "search_queries": [question],
            "original_question": question,
            "fallback_used": f"DSPy failed: {e}"
        }


@dspy_worker("dspy_rag_agent")
async def dspy_rag_retrieval_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """DSPy-powered RAG agent that retrieves and explains code from the codebase."""
    
    # Skip if clarification needed
    if context.get("needs_clarification", False):
        return {
            "skipped": True,
            "reason": "Clarification still needed"
        }
    
    question = context.get("original_question", context.get("question", ""))
    search_queries = context.get("search_queries", [question])
    
    try:
        # Configure DSPy (should already be configured by coordinator)
        api_key = os.getenv("GOOGLE_API_KEY") or context.get("google_api_key")
        if api_key:
            from dspy import LM
            lm = LM(model="gemini/gemini-1.5-pro", api_key=api_key)
            dspy.configure(lm=lm)
        
        # Get codebase indexer and search
        indexer = get_codebase_indexer()
        
        all_results = []
        for query in search_queries[:3]:  # Limit to 3 queries
            results = indexer.search(query, max_results=3)
            all_results.extend(results)
        
        # Prepare retrieved code context
        retrieved_code = []
        for result in all_results[:5]:  # Top 5 results
            item = result["item"]
            code_snippet = {
                "file": item["file"],
                "name": item["name"],
                "type": item["type"],
                "description": item["description"]
            }
            
            if "source" in item:
                code_snippet["source"] = item["source"]
            if "docstring" in item:
                code_snippet["docstring"] = item["docstring"]
            if "content" in item:
                code_snippet["content"] = item["content"][:1000]  # Limit content
            
            retrieved_code.append(code_snippet)
        
        if not retrieved_code:
            # For general questions, use LLM to answer based on project context
            if any(term in question.lower() for term in ["purpose", "what is", "about", "overview", "goal", "project"]):
                try:
                    # Use DSPy to generate a response about the project
                    from dspy import Predict
                    
                    class ProjectOverview(dspy.Signature):
                        """Provide an overview of the MultiAgents framework project."""
                        question = dspy.InputField(desc="User's question about the project")
                        overview = dspy.OutputField(desc="Comprehensive overview of the MultiAgents framework project")
                    
                    overview_generator = Predict(ProjectOverview)
                    result = overview_generator(question=question)
                    
                    return {
                        "response": f"""**Question**: {question}

**MultiAgents Framework Overview**:
{result.overview}

**Key Features**:
- 🧠 LLM-First Design with DSPy integration
- 🔧 Multi-Agent Orchestration for complex workflows
- 📊 Production-ready monitoring and observability
- 🔄 Event-driven architecture with fault tolerance
- 🛠️ Easy-to-use decorators (@worker, @dspy_worker)

**Use Cases**:
- Conversational AI systems with intelligent routing
- Research assistants with collaborative agents
- LLM-driven workflows with real-time decisions
- Tool-using agents with external integrations
- Data analysis pipelines with LLM insights
""",
                        "retrieved_files": ["Project overview generated by LLM"],
                        "needs_validation": True,
                        "llm_generated": True
                    }
                except Exception as e:
                    # Simple fallback response
                    return {
                        "response": f"""**Question**: {question}

**MultiAgents Framework Purpose**:

The MultiAgents Framework is a hybrid event-driven orchestration framework designed specifically for building intelligent, multi-step, and fault-tolerant applications with LLM integration.

**Core Goals**:
1. **LLM-First Design**: Built specifically for AI developers and LLM-powered applications
2. **Multi-Agent Coordination**: Enable multiple specialized agents to work together seamlessly
3. **Production Ready**: Provide enterprise-grade reliability, monitoring, and fault tolerance
4. **Developer Experience**: Simple APIs with decorators for easy agent creation

**Key Benefits**:
- Combines orchestration (centralized control) with event-driven architecture
- Native DSPy integration for intelligent workers
- Built-in compensation and rollback mechanisms (Saga pattern)
- Comprehensive monitoring and observability
- Scalable async communication via Redis

**Target Applications**:
- Conversational AI systems
- Research assistants
- LLM-driven workflows
- Tool-using agents
- Data analysis pipelines

This framework makes it easy to build sophisticated AI applications where multiple intelligent agents work together reliably in production environments.
""",
                        "retrieved_files": ["Generated overview"],
                        "needs_validation": True,
                        "fallback_used": f"DSPy failed, used fallback: {e}"
                    }
            else:
                return {
                    "error": "No relevant code found in codebase",
                    "question": question,
                    "search_attempted": search_queries
                }
        
        # Use DSPy to generate response
        try:
            retriever = dspy.Predict(CodebaseRetriever)
            result = retriever(
                question=question,
                search_queries=str(search_queries),
                retrieved_code=json.dumps(retrieved_code, indent=2)
            )
            
            return {
                "response": f"""**Question**: {question}

**Code Analysis**:
{result.code_explanation}

**Relevant Code**:
{result.relevant_code}

**Usage Examples**:
{result.usage_examples}
""",
                "retrieved_files": [item["file"] for item in retrieved_code],
                "needs_validation": True,
                "dspy_generated": True
            }
            
        except Exception as e:
            # Fallback to simple response
            simple_response = f"**Question**: {question}\n\n**Found in codebase**:\n\n"
            for item in retrieved_code[:3]:
                simple_response += f"- **{item['name']}** ({item['file']}): {item['description']}\n"
                if 'docstring' in item and item['docstring']:
                    simple_response += f"  - {item['docstring'][:200]}...\n"
                simple_response += "\n"
            
            return {
                "response": simple_response,
                "retrieved_files": [item["file"] for item in retrieved_code],
                "needs_validation": True,
                "fallback_used": f"DSPy failed: {e}"
            }
        
    except Exception as e:
        return {
            "error": f"RAG agent failed: {e}",
            "question": question
        }


@dspy_worker("dspy_validator")
async def dspy_validator_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """DSPy-powered validator that ensures response accuracy."""
    
    # Skip if previous steps were skipped
    if context.get("skipped", False):
        return {
            "skipped": True,
            "reason": "Previous step was skipped"
        }
    
    response = context.get("response", "")
    question = context.get("original_question", context.get("question", ""))
    retrieved_files = context.get("retrieved_files", [])
    
    if not response:
        return {
            "validation_passed": False,
            "error": "No response to validate"
        }
    
    try:
        # Configure DSPy
        api_key = os.getenv("GOOGLE_API_KEY") or context.get("google_api_key")
        if api_key:
            from dspy import LM
            lm = LM(model="gemini/gemini-1.5-pro", api_key=api_key)
            dspy.configure(lm=lm)
        
        # Use DSPy to validate
        try:
            validator = dspy.Predict(ResponseValidator)
            result = validator(
                question=question,
                response=response,
                code_context=f"Retrieved from files: {', '.join(retrieved_files)}"
            )
            
            is_accurate = result.is_accurate.lower() == "true"
            is_complete = result.is_complete.lower() == "true"
            final_approved = result.final_approved.lower() == "true"
            
            if final_approved:
                return {
                    "validation_passed": True,
                    "response": response,
                    "final_response": True,
                    "validation_notes": "DSPy validation passed"
                }
            else:
                return {
                    "validation_passed": False,
                    "validation_errors": [
                        f"Accurate: {is_accurate}",
                        f"Complete: {is_complete}"
                    ],
                    "improvement_suggestions": result.improvement_suggestions,
                    "needs_regeneration": True
                }
                
        except Exception as e:
            # Simple fallback validation
            has_code = "```" in response or "def " in response or "class " in response
            is_relevant = any(word in response.lower() for word in question.lower().split()[:3])
            is_long_enough = len(response) > 100
            
            if has_code and is_relevant and is_long_enough:
                return {
                    "validation_passed": True,
                    "response": response,
                    "final_response": True,
                    "fallback_validation": f"DSPy failed: {e}"
                }
            else:
                return {
                    "validation_passed": False,
                    "validation_errors": [
                        "Response may be incomplete or irrelevant"
                    ],
                    "fallback_validation": f"DSPy failed: {e}"
                }
        
    except Exception as e:
        return {
            "validation_passed": True,  # Accept on error
            "response": response,
            "final_response": True,
            "error": f"Validation failed: {e}"
        }