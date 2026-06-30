"""
Generation evaluation script — Faithfulness and Answer Relevance.

  Faithfulness   — does every claim in the generated answer have explicit
                   support in the retrieved context chunks?
                   Scored 0.0–1.0 (fraction of claims that are grounded).

  Answer Relevance — does the generated answer actually address the question?
                     Scored 0.0–1.0 (how fully the question is addressed).

Both metrics are judged by the Gemini LLM using structured prompts.  The
script calls the live retriever to fetch chunks, then calls the live RAG
pipeline (generate_from_context / generate_direct) to get the generated
answer, then asks the judge LLM to score it.

Usage:
    # Full test-set evaluation (requires --user-id):
    python scripts/eval_generation.py --user-id <uuid>

    # Single ad-hoc query:
    python scripts/eval_generation.py --user-id <uuid> \\
        --query "How many sick leave days does NexaAI provide?"

    # Point at a custom JSON test set:
    python scripts/eval_generation.py --user-id <uuid> \\
        --test-file path/to/testset.json

    # Skip retrieval — pass context manually (useful for offline testing):
    python scripts/eval_generation.py --user-id <uuid> \\
        --query "How many sick leave days?" \\
        --context "NexaAI provides 10 working days of sick leave per year."

    # Verbose: show per-claim breakdown for each query:
    python scripts/eval_generation.py --user-id <uuid> -v

    # Save report to a file:
    python scripts/eval_generation.py --user-id <uuid> \\
        --report scripts/generation_eval_report.md

Test-set JSON format (same schema as test_dataset.json):
    [{"question": "...", "answer": "...", "source": "...", "category": "..."}, ...]

Environment: reads .env (same as the app). Requires GEMINI_API_KEY and
GEMINI_MODEL / GEMINI_EMBEDDING_MODEL to be set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import textwrap
import time
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load .env before importing settings so all env vars are present
from dotenv import load_dotenv  # noqa: E402
load_dotenv(ROOT / ".env")

from app.core.config import settings  # noqa: E402
from app.db.client import DBClient  # noqa: E402

# ---------------------------------------------------------------------------
# Lazy-load Retriever without pulling the full LangGraph pipeline
# ---------------------------------------------------------------------------
import importlib.util as _ilu, types as _types  # noqa: E401,E402
_rspec = _ilu.spec_from_file_location(
    "app.rag.retriever", ROOT / "app" / "rag" / "retriever.py"
)
_rmod = _types.ModuleType("app.rag.retriever")
sys.modules.setdefault("app.rag", _types.ModuleType("app.rag"))
sys.modules["app.rag.retriever"] = _rmod
_rspec.loader.exec_module(_rmod)  # type: ignore[union-attr]
Retriever = _rmod.Retriever

from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: E402
from langchain_core.output_parsers import StrOutputParser  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate  # noqa: E402

_DEFAULT_TEST_FILE = ROOT / "test_dataset.json"
_DEFAULT_TOP_K = 5

# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

def _build_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )


# ── Faithfulness ─────────────────────────────────────────────────────────────

_FAITHFULNESS_SYSTEM = textwrap.dedent("""\
    You are a strict factual auditor.

    You will be given:
    - CONTEXT: a set of retrieved text chunks (the only allowed source of facts)
    - ANSWER: a generated answer to evaluate

    Your task:
    1. Break the ANSWER into atomic claims (one fact / assertion per item).
    2. For each claim, decide: SUPPORTED (the claim can be directly verified
       from CONTEXT) or UNSUPPORTED (the claim cannot be verified or
       contradicts CONTEXT).
    3. Return ONLY valid JSON in this exact format:
       {{ "claims": [ {{"claim": "<claim text>", "supported": true}}, ... ], "faithfulness_score": <float 0.0-1.0> }}
    faithfulness_score = supported_count / total_claims (0.0 if no claims).
    Do not include any explanation outside the JSON.
""")

_FAITHFULNESS_HUMAN = textwrap.dedent("""\
    CONTEXT:
    {context}

    ANSWER:
    {answer}
""")

_FAITHFULNESS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _FAITHFULNESS_SYSTEM),
    ("human", _FAITHFULNESS_HUMAN),
])


# ── Answer Relevance ─────────────────────────────────────────────────────────

_RELEVANCE_SYSTEM = textwrap.dedent("""\
    You are an answer quality evaluator.

    You will be given:
    - QUESTION: the user's original question
    - ANSWER: the generated response to evaluate

    Your task:
    1. Rate how completely and directly the ANSWER addresses the QUESTION.
    2. Consider: Does it answer what was asked? Are key aspects of the
       question addressed? Is there unnecessary or off-topic content?
    3. Return ONLY valid JSON in this exact format:
       {{ "assessment": "<one-sentence explanation>", "relevance_score": <float 0.0-1.0> }}
    Scoring guide:
      1.0 — fully addresses the question, nothing missing
      0.7 — mostly addresses the question, minor gaps
      0.5 — partially addresses, significant aspect missed
      0.3 — tangentially related, barely answers
      0.0 — completely off-topic or refuses to answer
    Do not include any explanation outside the JSON.
""")

_RELEVANCE_HUMAN = textwrap.dedent("""\
    QUESTION:
    {question}

    ANSWER:
    {answer}
""")

_RELEVANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _RELEVANCE_SYSTEM),
    ("human", _RELEVANCE_HUMAN),
])


# ---------------------------------------------------------------------------
# Generation — call the LLM directly with retrieved context
# ---------------------------------------------------------------------------

_GENERATION_SYSTEM = textwrap.dedent("""\
    You are a helpful assistant for NexaAI Solutions.
    Answer the user's question using ONLY the information in the provided context.
    If the context does not contain the answer, say "I don't have enough information
    to answer this question based on the available documents."
    Be concise and factual.
""")

_GENERATION_HUMAN = textwrap.dedent("""\
    CONTEXT:
    {context}

    QUESTION:
    {question}
""")

_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _GENERATION_SYSTEM),
    ("human", _GENERATION_HUMAN),
])


def _parse_json_response(raw: str) -> dict:
    """Extract the first JSON object from an LLM response string."""
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            ln for ln in lines
            if not ln.startswith("```")
        )
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response: {raw!r}")
    return json.loads(raw[start:end])


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

async def evaluate_single(
    db,
    llm: ChatGoogleGenerativeAI,
    user_id: UUID,
    question: str,
    reference_answer: str | None,
    top_k: int,
    prebuilt_context: str | None = None,
) -> dict:
    """Run faithfulness + relevance evaluation for one question."""

    # 1. Retrieve context (or use prebuilt)
    if prebuilt_context:
        context_text = prebuilt_context
        chunks = []
    else:
        chunks = await Retriever.get(
            db,
            user_id=user_id,
            query=question,
            top_k=top_k,
            use_hybrid=not settings.RETRIEVER_HYBRID,
        )
        context_text = "\n\n---\n\n".join(c.page_content for c in chunks)

    # 2. Generate an answer from context
    gen_chain = _GENERATION_PROMPT | llm | StrOutputParser()
    generated_answer = await gen_chain.ainvoke({
        "context": context_text or "(no context retrieved)",
        "question": question,
    })

    # 3. Faithfulness: judge if each claim in generated_answer is grounded
    faith_chain = _FAITHFULNESS_PROMPT | llm | StrOutputParser()
    faith_raw = await faith_chain.ainvoke({
        "context": context_text or "(no context retrieved)",
        "answer": generated_answer,
    })
    try:
        faith_data = _parse_json_response(faith_raw)
        faith_score = float(faith_data.get("faithfulness_score", 0.0))
        claims = faith_data.get("claims", [])
    except (ValueError, KeyError, TypeError) as exc:
        faith_score = 0.0
        claims = []
        print(f"  [WARN] Could not parse faithfulness JSON: {exc}", file=sys.stderr)

    # 4. Answer Relevance: judge if generated_answer addresses the question
    rel_chain = _RELEVANCE_PROMPT | llm | StrOutputParser()
    rel_raw = await rel_chain.ainvoke({
        "question": question,
        "answer": generated_answer,
    })
    try:
        rel_data = _parse_json_response(rel_raw)
        rel_score = float(rel_data.get("relevance_score", 0.0))
        rel_assessment = rel_data.get("assessment", "")
    except (ValueError, KeyError, TypeError) as exc:
        rel_score = 0.0
        rel_assessment = ""
        print(f"  [WARN] Could not parse relevance JSON: {exc}", file=sys.stderr)

    return {
        "question": question,
        "reference_answer": reference_answer,
        "generated_answer": generated_answer,
        "context_chunks": len(chunks),
        "context_preview": context_text[:200] if context_text else "",
        "faithfulness": faith_score,
        "claims": claims,
        "answer_relevance": rel_score,
        "relevance_assessment": rel_assessment,
    }


async def run_eval(
    user_id: UUID,
    test_cases: list[dict],
    top_k: int,
    verbose: bool,
    prebuilt_context: str | None = None,
) -> list[dict]:
    Retriever.init()
    llm =  ()

    results: list[dict] = []
    db = DBClient.get_session()
    try:
        for i, tc in enumerate(test_cases, start=1):
            question = tc.get("question") or tc.get("query", "")
            reference = tc.get("answer")

            print(f"[{i:>2}/{len(test_cases)}] {question[:75]}", flush=True)

            r = await evaluate_single(
                db, llm, user_id, question, reference, top_k,
                prebuilt_context=prebuilt_context,
            )
            results.append(r)

            print(
                f"         Faithfulness={r['faithfulness']:.2f}  "
                f"Relevance={r['answer_relevance']:.2f}",
                flush=True,
            )

            if verbose:
                print(f"         Generated: {r['generated_answer'][:120]!r}")
                if r["claims"]:
                    for c in r["claims"]:
                        mark = "✓" if c.get("supported") else "✗"
                        print(f"         {mark} {c.get('claim', '')[:100]}")
                print(f"         Relevance assessment: {r['relevance_assessment']}")

            # Rate-limit: Gemini free tier allows ~15 RPM; 3 LLM calls per query
            await asyncio.sleep(1.5)

    finally:
        await db.close()

    return results


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


def print_summary(results: list[dict], top_k: int) -> None:
    n = len(results)
    if n == 0:
        print("No results to summarise.")
        return

    avg_faith = sum(r["faithfulness"] for r in results) / n
    avg_rel = sum(r["answer_relevance"] for r in results) / n
    fully_faithful = sum(1 for r in results if r["faithfulness"] >= 0.9)
    fully_relevant = sum(1 for r in results if r["answer_relevance"] >= 0.9)
    low_faith = [r for r in results if r["faithfulness"] < 0.5]
    low_rel = [r for r in results if r["answer_relevance"] < 0.5]

    bar = "─" * 56
    print(f"\n{bar}")
    print(f"  Generation Evaluation Summary")
    print(f"  Queries evaluated   : {n}")
    print(f"  Retrieval Top-K     : {top_k}")
    print(bar)
    print(f"  Faithfulness        : {avg_faith:.4f}  {_bar(avg_faith)}")
    print(f"  Answer Relevance    : {avg_rel:.4f}  {_bar(avg_rel)}")
    print(bar)
    print(f"  Fully faithful (≥0.9) : {fully_faithful} / {n}")
    print(f"  Fully relevant (≥0.9) : {fully_relevant} / {n}")
    print(bar)

    if low_faith:
        print("\nLow faithfulness queries (<0.5):")
        for r in low_faith:
            print(f"  ✗ [{r['faithfulness']:.2f}] {r['question'][:75]}")

    if low_rel:
        print("\nLow relevance queries (<0.5):")
        for r in low_rel:
            print(f"  ✗ [{r['answer_relevance']:.2f}] {r['question'][:75]}")


def build_markdown_report(
    results: list[dict],
    top_k: int,
    user_id: str,
) -> str:
    n = len(results)
    if n == 0:
        return "No results.\n"

    avg_faith = sum(r["faithfulness"] for r in results) / n
    avg_rel = sum(r["answer_relevance"] for r in results) / n
    fully_faithful = sum(1 for r in results if r["faithfulness"] >= 0.9)
    fully_relevant = sum(1 for r in results if r["answer_relevance"] >= 0.9)

    # Group by category if available
    categories: dict[str, list[dict]] = {}
    for r in results:
        cat = r.get("category", "Uncategorised")
        categories.setdefault(cat, []).append(r)

    lines = [
        "# Generation Evaluation Report",
        "",
        f"**Date:** {_today()}  ",
        f"**User:** `{user_id}`  ",
        f"**LLM (generator + judge):** `{settings.GEMINI_MODEL}`  ",
        f"**Embedding model:** `{settings.GEMINI_EMBEDDING_MODEL}`  ",
        f"**Test set:** {n} queries  ",
        f"**Retrieval Top-K:** {top_k}  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Score |",
        "|---|---|",
        f"| **Faithfulness** | {avg_faith:.4f} |",
        f"| **Answer Relevance** | {avg_rel:.4f} |",
        f"| Fully faithful (≥0.9) | {fully_faithful} / {n} |",
        f"| Fully relevant (≥0.9) | {fully_relevant} / {n} |",
        "",
        "> **Faithfulness** measures whether each claim in the generated answer "
        "is grounded in the retrieved context (0 = hallucinated, 1 = fully grounded).  ",
        "> **Answer Relevance** measures whether the generated answer actually addresses "
        "the question (0 = off-topic, 1 = fully responsive).",
        "",
        "---",
        "",
        "## Results by Category",
        "",
    ]

    for cat, items in sorted(categories.items()):
        cat_faith = sum(r["faithfulness"] for r in items) / len(items)
        cat_rel = sum(r["answer_relevance"] for r in items) / len(items)
        lines.append(f"### {cat}  ({len(items)} queries)")
        lines.append("")
        lines.append(f"| Metric | Score |")
        lines.append(f"|---|---|")
        lines.append(f"| Avg Faithfulness | {cat_faith:.4f} |")
        lines.append(f"| Avg Answer Relevance | {cat_rel:.4f} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Per-Query Results",
        "",
        "| # | Question | Faithfulness | Answer Relevance | Relevance Assessment |",
        "|---|---|---|---|---|",
    ]

    for i, r in enumerate(results, start=1):
        faith_str = f"{r['faithfulness']:.2f}"
        rel_str = f"{r['answer_relevance']:.2f}"
        assessment = r.get("relevance_assessment", "").replace("|", "/")[:80]
        q = r["question"].replace("|", "/")[:75]
        lines.append(f"| {i} | {q} | {faith_str} | {rel_str} | {assessment} |")

    lines += [
        "",
        "---",
        "",
        "## Detailed Results",
        "",
    ]

    for i, r in enumerate(results, start=1):
        lines.append(f"### {i}. {r['question']}")
        lines.append("")
        lines.append(f"**Faithfulness:** {r['faithfulness']:.2f} &nbsp; "
                     f"**Answer Relevance:** {r['answer_relevance']:.2f}")
        lines.append("")
        lines.append("**Generated answer:**")
        lines.append(f"> {r['generated_answer'].replace(chr(10), '  \\n> ')}")
        lines.append("")
        if r.get("reference_answer"):
            lines.append("**Reference answer:**")
            lines.append(f"> {r['reference_answer']}")
            lines.append("")
        if r.get("claims"):
            lines.append("**Claim breakdown:**")
            lines.append("")
            for c in r["claims"]:
                mark = "✓" if c.get("supported") else "✗"
                lines.append(f"- {mark} {c.get('claim', '')}")
            lines.append("")
        if r.get("relevance_assessment"):
            lines.append(f"**Relevance assessment:** {r['relevance_assessment']}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Analysis section
    low_faith = [r for r in results if r["faithfulness"] < 0.5]
    low_rel = [r for r in results if r["answer_relevance"] < 0.5]
    partial_faith = [r for r in results if 0.5 <= r["faithfulness"] < 0.9]

    lines += [
        "## Analysis",
        "",
        "### Faithfulness",
        "",
        f"Average faithfulness of **{avg_faith:.2f}** means roughly "
        f"{avg_faith*100:.0f}% of all generated claims are grounded in the retrieved context.  ",
        f"**{fully_faithful}/{n}** queries produced fully faithful answers (score ≥ 0.9).  ",
    ]

    if low_faith:
        lines.append(f"**{len(low_faith)}** queries had low faithfulness (<0.5), "
                     "indicating hallucination or context mismatch:")
        for r in low_faith:
            lines.append(f"- `{r['question'][:80]}` → {r['faithfulness']:.2f}")
        lines.append("")

    if partial_faith:
        lines.append(f"**{len(partial_faith)}** queries had partial faithfulness (0.5–0.9), "
                     "meaning some claims were unsupported:")
        for r in partial_faith:
            lines.append(f"- `{r['question'][:80]}` → {r['faithfulness']:.2f}")
        lines.append("")

    lines += [
        "### Answer Relevance",
        "",
        f"Average relevance of **{avg_rel:.2f}** indicates the model "
        f"{'consistently addresses the question' if avg_rel >= 0.8 else 'sometimes misses key aspects of the question'}.  ",
        f"**{fully_relevant}/{n}** queries received fully relevant answers (score ≥ 0.9).  ",
    ]

    if low_rel:
        lines.append(f"**{len(low_rel)}** queries had low relevance (<0.5):")
        for r in low_rel:
            lines.append(f"- `{r['question'][:80]}` → {r['answer_relevance']:.2f}")
        lines.append("")

    lines += [
        "### Recommendations",
        "",
        "| Priority | Issue | Recommendation |",
        "|---|---|---|",
    ]

    if avg_faith < 0.8:
        lines.append(
            "| **High** | Faithfulness below 0.8 — model generating unsupported claims | "
            "Tighten the generation system prompt to explicitly forbid claims outside context; "
            "consider reducing top-K to return higher-quality context |"
        )
    if low_faith:
        lines.append(
            f"| **High** | {len(low_faith)} queries with <0.5 faithfulness | "
            "Review chunk boundaries for these queries — context may be incomplete or split "
            "across chunk boundaries causing the model to fill gaps from training data |"
        )
    if avg_rel < 0.8:
        lines.append(
            "| **Medium** | Relevance below 0.8 — answers missing key question aspects | "
            "Check if retrieved context covers the queried topics; poor relevance often "
            "traces back to retrieval misses rather than generation failures |"
        )
    if avg_faith >= 0.9 and avg_rel >= 0.9:
        lines.append(
            "| **Low** | Both metrics strong (≥0.9) | "
            "Consider expanding the test set with adversarial questions to stress-test edge cases |"
        )

    lines.append("")

    return "\n".join(lines)


def _today() -> str:
    import datetime
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Test-set loader
# ---------------------------------------------------------------------------

def load_testset(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    with path.open() as fh:
        if suffix == ".json":
            data = json.load(fh)
            if not isinstance(data, list):
                sys.exit(f"Expected a JSON array in {path}")
            for obj in data:
                if "question" not in obj and "query" not in obj:
                    sys.exit(f"Each object needs 'question' or 'query': {obj}")
            return data
        else:
            # JSONL
            cases = []
            for lineno, raw in enumerate(fh, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    sys.exit(f"Bad JSON on line {lineno} of {path}: {exc}")
                if "question" not in obj and "query" not in obj:
                    sys.exit(f"Line {lineno}: need 'question' or 'query'")
                cases.append(obj)
            return cases


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Measure generation Faithfulness and Answer Relevance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--user-id", required=True,
        help="UUID of the user whose ingested documents to query",
    )
    p.add_argument(
        "--test-file", type=Path, default=_DEFAULT_TEST_FILE,
        help=f"JSON or JSONL test set (default: {_DEFAULT_TEST_FILE.name})",
    )
    p.add_argument(
        "--query",
        help="Single ad-hoc question (skips --test-file)",
    )
    p.add_argument(
        "--context",
        help="Pre-built context string for single-query mode (skips retrieval)",
    )
    p.add_argument(
        "--top-k", type=int, default=_DEFAULT_TOP_K,
        help=f"Number of chunks to retrieve per query (default: {_DEFAULT_TOP_K})",
    )
    p.add_argument(
        "--report", type=Path,
        help="Write a Markdown report to this path",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print per-claim breakdown and generated answers",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not settings.GEMINI_MODEL:
        sys.exit("GEMINI_MODEL is not set in the environment.")
    if not settings.GEMINI_API_KEY:
        sys.exit("GEMINI_API_KEY is not set in the environment.")
    if not settings.GEMINI_EMBEDDING_MODEL:
        sys.exit("GEMINI_EMBEDDING_MODEL is not set in the environment.")

    if args.query:
        test_cases = [{"question": args.query}]
    else:
        test_file = args.test_file
        if not test_file.exists():
            sys.exit(f"Test file not found: {test_file}")
        test_cases = load_testset(test_file)

    try:
        user_id = UUID(args.user_id)
    except ValueError:
        sys.exit(f"Invalid UUID: {args.user_id!r}")

    t0 = time.monotonic()
    results = asyncio.run(run_eval(
        user_id=user_id,
        test_cases=test_cases,
        top_k=args.top_k,
        verbose=args.verbose,
        prebuilt_context=args.context,
    ))
    elapsed = time.monotonic() - t0

    # Carry over category metadata from test_cases into results
    for r, tc in zip(results, test_cases):
        r.setdefault("category", tc.get("category", "Uncategorised"))

    print_summary(results, args.top_k)
    print(f"\n  Total time: {elapsed:.1f}s")

    if args.report:
        report_md = build_markdown_report(results, args.top_k, str(user_id))
        args.report.write_text(report_md, encoding="utf-8")
        print(f"\n  Report written to: {args.report}")


if __name__ == "__main__":
    main()