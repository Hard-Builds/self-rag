"""
Retrieval evaluation script — Precision@K and MRR.

Measures how well the retriever surfaces the right chunks for each question
in the test dataset. Two metrics are computed per query and averaged:

  Precision@K  — fraction of the top-K retrieved chunks that are relevant.
                 A chunk is "relevant" if any keyword from the test case
                 appears (case-insensitive) in its content, or if its UUID
                 matches a `relevant_ids` entry.

  MRR          — Mean Reciprocal Rank: 1/rank of the first relevant chunk.
                 0.0 if no relevant chunk appears in the top-K window.

Usage:
    # Evaluate against the bundled test set (requires --user-id):
    python scripts/eval_retrieval.py --user-id <uuid>

    # Point at a custom JSONL test set:
    python scripts/eval_retrieval.py --user-id <uuid> --test-file path/to/set.jsonl

    # Single ad-hoc query:
    python scripts/eval_retrieval.py --user-id <uuid> \\
        --query "What is the Starter Plan price?" --relevant "2,499"

    # Tune K or switch to dense-only:
    python scripts/eval_retrieval.py --user-id <uuid> --top-k 3 --no-hybrid

    # Verbose mode shows per-chunk hit/miss for every query:
    python scripts/eval_retrieval.py --user-id <uuid> -v

Test-set JSONL format (one JSON object per line):
    {"query": "...", "relevant": ["keyword1", "keyword2"]}
    {"query": "...", "relevant_ids": ["chunk-uuid-1"]}
    {"query": "...", "relevant": ["kw"], "relevant_ids": ["uuid"]}

Environment: reads .env (same as the app). Requires GEMINI_API_KEY and
GEMINI_EMBEDDING_MODEL to be set.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import settings  # noqa: E402
from app.db.client import DBClient  # noqa: E402

# Load Retriever directly to avoid pulling in the full LangGraph pipeline
# via app/rag/__init__.py (which imports RAGGraph and all bot nodes).
import importlib.util as _ilu, types as _types  # noqa: E401,E402
_rspec = _ilu.spec_from_file_location("app.rag.retriever", ROOT / "app" / "rag" / "retriever.py")
_rmod = _types.ModuleType("app.rag.retriever")
sys.modules.setdefault("app.rag", _types.ModuleType("app.rag"))
sys.modules["app.rag.retriever"] = _rmod
_rspec.loader.exec_module(_rmod)  # type: ignore[union-attr]
Retriever = _rmod.Retriever

_DEFAULT_TEST_FILE = ROOT / "scripts" / "eval_testset.jsonl"


# ── relevance helpers ─────────────────────────────────────────────────────────

def _is_relevant(content: str, chunk_id: str,
                 keywords: list[str], ids: list[str]) -> bool:
    if ids and chunk_id in ids:
        return True
    return any(kw.lower() in content.lower() for kw in keywords)


# ── metric functions ──────────────────────────────────────────────────────────

def precision_at_k(hits: list[bool]) -> float:
    """Fraction of retrieved chunks that are relevant."""
    return sum(hits) / len(hits) if hits else 0.0


def reciprocal_rank(hits: list[bool]) -> float:
    """1 / rank of the first relevant chunk; 0 if none found."""
    for rank, hit in enumerate(hits, start=1):
        if hit:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(hits: list[bool]) -> float:
    """Normalised Discounted Cumulative Gain (binary relevance)."""
    dcg = sum(int(h) / math.log2(i + 2) for i, h in enumerate(hits))
    ideal = sorted(hits, reverse=True)
    idcg = sum(int(h) / math.log2(i + 2) for i, h in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


# ── core evaluation ───────────────────────────────────────────────────────────

async def evaluate_query(
    db,
    user_id: UUID,
    query: str,
    keywords: list[str],
    ids: list[str],
    top_k: int,
    use_hybrid: bool,
    use_reranker: bool,
) -> dict:
    docs = await Retriever.get(
        db,
        user_id=user_id,
        query=query,
        top_k=top_k,
        use_hybrid=use_hybrid,
        use_reranker=use_reranker,
    )

    hits = [
        _is_relevant(
            d.page_content,
            str(d.metadata.get("chunk_id", "")),
            keywords,
            ids,
        )
        for d in docs
    ]

    return {
        "query": query,
        "hits": hits,
        "precision": precision_at_k(hits),
        "mrr": reciprocal_rank(hits),
        "ndcg": ndcg_at_k(hits),
        "snippets": [d.page_content[:120] for d in docs],
    }


async def run_eval(
    user_id: UUID,
    test_cases: list[dict],
    top_k: int,
    use_hybrid: bool,
    use_reranker: bool,
    verbose: bool,
) -> list[dict]:
    Retriever.init()
    if use_reranker:
        Retriever.init_reranker()

    results: list[dict] = []

    # DBClient.get_session() returns a plain AsyncSession, not a context manager
    db = DBClient.get_session()
    try:
        for i, tc in enumerate(test_cases, start=1):
            query = tc["query"]
            keywords = tc.get("relevant", [])
            ids = tc.get("relevant_ids", [])

            print(f"[{i:>2}/{len(test_cases)}] {query[:75]}", flush=True)

            r = await evaluate_query(
                db, user_id, query, keywords, ids,
                top_k, use_hybrid, use_reranker,
            )
            results.append(r)

            if verbose:
                print(f"         P@{top_k}={r['precision']:.2f}  "
                      f"MRR={r['mrr']:.2f}  NDCG@{top_k}={r['ndcg']:.2f}")
                for rank, (hit, snip) in enumerate(
                        zip(r["hits"], r["snippets"]), start=1):
                    mark = "✓" if hit else "✗"
                    print(f"         {mark} [{rank}] {snip!r}")
    finally:
        await db.close()

    return results


# ── summary output ────────────────────────────────────────────────────────────

def print_summary(results: list[dict], top_k: int) -> None:
    n = len(results)
    if n == 0:
        print("No results to summarise.")
        return

    avg_p   = sum(r["precision"] for r in results) / n
    avg_mrr = sum(r["mrr"]       for r in results) / n
    avg_ndcg= sum(r["ndcg"]      for r in results) / n
    zero_hit = sum(1 for r in results if not any(r["hits"]))

    bar = "─" * 52
    print(f"\n{bar}")
    print(f"  Queries evaluated  : {n}")
    print(f"  Top-K              : {top_k}")
    print(f"  Precision@{top_k:<6}   : {avg_p:.4f}")
    print(f"  MRR                : {avg_mrr:.4f}")
    print(f"  NDCG@{top_k:<10}   : {avg_ndcg:.4f}")
    print(f"  Zero-hit queries   : {zero_hit} / {n}")
    print(bar)

    if zero_hit:
        print("\nQueries with no relevant chunk retrieved:")
        for r in results:
            if not any(r["hits"]):
                print(f"  ✗  {r['query']}")


# ── test-set loader ───────────────────────────────────────────────────────────

def load_testset(path: Path) -> list[dict]:
    cases: list[dict] = []
    with path.open() as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                sys.exit(f"Bad JSON on line {lineno} of {path}: {exc}")
            if "query" not in obj:
                sys.exit(f"Line {lineno}: missing 'query' field")
            if "relevant" not in obj and "relevant_ids" not in obj:
                sys.exit(f"Line {lineno}: need 'relevant' (keywords) or 'relevant_ids' (UUIDs)")
            cases.append(obj)
    return cases


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Measure retrieval Precision@K and MRR on a test set",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--user-id", required=True,
        help="UUID of the user whose ingested documents to query",
    )
    p.add_argument(
        "--test-file", type=Path, default=_DEFAULT_TEST_FILE,
        help=f"JSONL test set (default: {_DEFAULT_TEST_FILE.name})",
    )
    p.add_argument(
        "--query",
        help="Single ad-hoc query (skips --test-file)",
    )
    p.add_argument(
        "--relevant", nargs="*", default=[],
        help="Keyword substrings marking a chunk as relevant (single-query mode)",
    )
    p.add_argument(
        "--relevant-ids", nargs="*", default=[],
        help="Exact chunk UUIDs that are relevant (single-query mode)",
    )
    p.add_argument(
        "--top-k", type=int, default=5,
        help="Number of chunks to retrieve per query (default: 5)",
    )
    p.add_argument(
        "--no-hybrid", action="store_true",
        help="Use dense-only (cosine) retrieval instead of hybrid BM25+dense",
    )
    p.add_argument(
        "--rerank", action="store_true",
        help="Enable cross-encoder reranking (requires sentence-transformers)",
    )
    p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print per-query hit/miss breakdown for every retrieved chunk",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.query and args.test_file != _DEFAULT_TEST_FILE:
        sys.exit("Pass either --query or --test-file, not both.")

    if args.query:
        if not args.relevant and not args.relevant_ids:
            sys.exit("Single-query mode requires --relevant or --relevant-ids.")
        test_cases = [{"query": args.query, "relevant": args.relevant,
                       "relevant_ids": args.relevant_ids}]
    else:
        test_file = args.test_file
        if not test_file.exists():
            sys.exit(f"Test file not found: {test_file}")
        test_cases = load_testset(test_file)

    try:
        user_id = UUID(args.user_id)
    except ValueError:
        sys.exit(f"Invalid UUID: {args.user_id!r}")

    results = asyncio.run(run_eval(
        user_id=user_id,
        test_cases=test_cases,
        top_k=args.top_k,
        use_hybrid=not args.no_hybrid,
        use_reranker=args.rerank,
        verbose=args.verbose,
    ))

    print_summary(results, args.top_k)


if __name__ == "__main__":
    main()