"""Brain Dump CLI — Ingest communications and query the knowledge graph."""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_pipeline():
    """Initialize the full pipeline with configured services."""
    from core.nlp_processor import Extractor
    from core.graph_engine import GraphStore
    from core.vector_engine import VectorStore
    from core.orchestrator import Pipeline

    extractor = Extractor(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        model=os.getenv("LLM_MODEL", "qwen2.5-coder:30b"),
    )
    graph = GraphStore(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password_here"),
    )
    vector = VectorStore(
        host=os.getenv("CHROMA_HOST", "localhost"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    return Pipeline(extractor, graph, vector)


def cmd_ingest(args):
    """Ingest a local text file into the knowledge graph and vector store."""
    pipeline = get_pipeline()
    print(f"Ingesting: {args.file}")

    extraction = pipeline.process_file(args.file)

    print(f"\n--- Extraction Result ---")
    print(f"Summary: {extraction.summary}")
    print(f"People:  {[p.name for p in extraction.people]}")
    print(f"Projects: {[p.name for p in extraction.projects]}")
    print(f"Tasks:   {len(extraction.tasks)} extracted")
    for i, task in enumerate(extraction.tasks, 1):
        status = f"[{task.priority}]"
        assignee = f" -> {task.assignee}" if task.assignee else ""
        waiting = f" (waiting on {task.waiting_on})" if task.waiting_on else ""
        due = f" due {task.due_date}" if task.due_date else ""
        print(f"  {i}. {status} {task.description}{assignee}{waiting}{due}")

    pipeline.graph.close()
    print("\nDone.")


def cmd_query(args):
    """Query the knowledge graph for insights."""
    pipeline = get_pipeline()
    question = args.question.lower()

    if "waiting" in question or "blocked" in question or "hanging" in question:
        print("--- Blocked / Hanging Tasks ---")
        results = pipeline.graph.query_hanging_tasks()
        if not results:
            print("  No blocked tasks found.")
        for r in results:
            due = f" (due {r['due_date']})" if r.get("due_date") else ""
            print(f"  - {r['task']} -> waiting on {r['waiting_on']}{due}")

        # Enrich with RAG context
        if results:
            print("\n--- Context from Communications ---")
            query_text = "; ".join(r["task"] for r in results)
            context = pipeline.vector.search_context(query_text, n_results=3)
            if context and context.get("documents"):
                for doc in context["documents"][0]:
                    snippet = doc[:200].replace("\n", " ")
                    print(f"  > {snippet}...")

    elif "project" in question or "overview" in question:
        print("--- Project Overview ---")
        results = pipeline.graph.query_project_overview()
        if not results:
            print("  No projects found.")
        current_project = None
        for r in results:
            if r["project"] != current_project:
                current_project = r["project"]
                print(f"\n  [{current_project}]")
            blocked = f" (blocked by {r['blocked_by']})" if r.get("blocked_by") else ""
            assignee = f" [{r['assignee']}]" if r.get("assignee") else ""
            print(f"    - [{r['status']}] {r['task']}{assignee}{blocked}")
    else:
        print(f"Searching for: {args.question}")
        context = pipeline.vector.search_context(args.question, n_results=5)
        if context and context.get("documents"):
            for i, doc in enumerate(context["documents"][0], 1):
                snippet = doc[:300].replace("\n", " ")
                print(f"\n  Result {i}: {snippet}...")
        else:
            print("  No results found.")

    pipeline.graph.close()


def main():
    parser = argparse.ArgumentParser(
        description="Brain Dump — Second Brain Ingestion Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a text file")
    ingest_parser.add_argument("--file", "-f", required=True, help="Path to text file")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge graph")
    query_parser.add_argument(
        "--question", "-q", required=True, help="Natural language question"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "query":
        cmd_query(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
