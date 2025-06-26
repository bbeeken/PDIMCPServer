"""Enhanced product lookup with advanced RapidFuzz scoring and multi-field search.

This tool queries **PDI_Warehouse_1539_01.dbo.product_view** and supports:
• Exact *item_id* match
• Multi-field fuzzy search with weighted composite scoring
• Progressive search fallback for better recall
• Multiple RapidFuzz scoring algorithms for improved accuracy
• Excludes brands marked **UNAUTH** / **DEAUTH**

It returns the *limit* highest-scoring rows with detailed scoring metadata.
"""

from __future__ import annotations

import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from mcp.types import Tool
from ..db.connection import execute_query
from .utils import create_tool_response

try:
    from rapidfuzz import fuzz, process, utils  # type: ignore
    RAPIDFUZZ_AVAILABLE = True
except ImportError:  # pragma: no cover – RapidFuzz optional but strongly recommended
    fuzz = None  # type: ignore
    process = None  # type: ignore
    utils = None  # type: ignore
    RAPIDFUZZ_AVAILABLE = False

# ────────────────────────────────────────────────────────────────
# Configuration and Data Classes
# ────────────────────────────────────────────────────────────────

@dataclass
class SearchConfig:
    """Configuration for fuzzy search behavior."""
    min_score_threshold: float = 60.0  # Minimum score to include in results
    multi_field_weights: Dict[str, float] = None  # Field weights for composite scoring
    use_progressive_search: bool = True  # Enable progressive search fallback
    max_candidates: int = 500  # Maximum candidates to fetch for ranking
    
    def __post_init__(self):
        if self.multi_field_weights is None:
            self.multi_field_weights = {
                'description': 0.6,    # Primary field
                'category': 0.2,       # Secondary relevance
                'department': 0.1,     # Tertiary relevance  
                'brand': 0.1          # Brand relevance
            }

@dataclass
class ScoringResult:
    """Result with detailed scoring information."""
    item: Dict[str, Any]
    composite_score: float
    field_scores: Dict[str, float]
    matching_algorithm: str

# ────────────────────────────────────────────────────────────────
# Text Preprocessing and Normalization
# ────────────────────────────────────────────────────────────────

def preprocess_text(text: str) -> str:
    """Advanced text preprocessing for better matching."""
    if not text:
        return ""
    
    # Convert to lowercase and normalize whitespace
    text = re.sub(r'\s+', ' ', text.lower().strip())
    
    # Common retail abbreviations and normalizations
    replacements = {
        r'\b(oz|ounce|ounces)\b': 'oz',
        r'\b(lb|lbs|pound|pounds)\b': 'lb', 
        r'\b(pk|pack|packs)\b': 'pack',
        r'\b(ct|count)\b': 'count',
        r'\b(btl|bottle|bottles)\b': 'bottle',
        r'\b(can|cans)\b': 'can',
        r'\b(reg|regular)\b': 'regular',
        r'\b(lg|lrg|large)\b': 'large',
        r'\b(sm|small)\b': 'small',
        r'\b(med|medium)\b': 'medium',
        r'\b(&|and)\b': 'and',
        r'[^\w\s]': ' ',  # Remove special characters
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    # Remove extra spaces
    return re.sub(r'\s+', ' ', text).strip()

def extract_tokens(text: str) -> List[str]:
    """Extract meaningful tokens from text."""
    preprocessed = preprocess_text(text)
    tokens = [t for t in preprocessed.split() if len(t) > 1]  # Filter very short tokens
    return tokens

# ────────────────────────────────────────────────────────────────
# Multi-Algorithm Scoring
# ────────────────────────────────────────────────────────────────

def calculate_multi_score(query: str, target: str) -> Tuple[float, str]:
    """Calculate composite score using multiple RapidFuzz algorithms."""
    if not RAPIDFUZZ_AVAILABLE or not query or not target:
        return 0.0, "unavailable"
    
    query_norm = preprocess_text(query)
    target_norm = preprocess_text(target)
    
    # Calculate different types of scores
    scores = {
        'token_set_ratio': fuzz.token_set_ratio(query_norm, target_norm),
        'token_sort_ratio': fuzz.token_sort_ratio(query_norm, target_norm),
        'partial_ratio': fuzz.partial_ratio(query_norm, target_norm),
        'ratio': fuzz.ratio(query_norm, target_norm),
        'WRatio': fuzz.WRatio(query_norm, target_norm)  # Weighted ratio (best overall)
    }
    
    # Weighted composite score (WRatio gets highest weight as it's most robust)
    composite = (
        scores['WRatio'] * 0.4 +
        scores['token_set_ratio'] * 0.25 +
        scores['token_sort_ratio'] * 0.15 +
        scores['partial_ratio'] * 0.15 +
        scores['ratio'] * 0.05
    )
    
    # Return best individual algorithm name for metadata
    best_algorithm = max(scores.items(), key=lambda x: x[1])
    
    return composite, f"composite (best: {best_algorithm[0]}={best_algorithm[1]:.1f})"

def score_item_multi_field(query: str, item: Dict[str, Any], config: SearchConfig) -> ScoringResult:
    """Score an item across multiple fields with weighted composite scoring."""
    field_scores = {}
    
    # Score each field
    for field, weight in config.multi_field_weights.items():
        if field in item and item[field]:
            score, algorithm = calculate_multi_score(query, str(item[field]))
            field_scores[field] = score
        else:
            field_scores[field] = 0.0
    
    # Calculate weighted composite score
    composite_score = sum(
        field_scores[field] * weight 
        for field, weight in config.multi_field_weights.items()
    )
    
    # Use the field with highest score for algorithm metadata
    best_field_score = max(field_scores.values()) if field_scores else 0.0
    algorithm = f"multi-field (max: {best_field_score:.1f})"
    
    return ScoringResult(
        item=item,
        composite_score=composite_score,
        field_scores=field_scores,
        matching_algorithm=algorithm
    )

# ────────────────────────────────────────────────────────────────
# Progressive Search Strategy
# ────────────────────────────────────────────────────────────────

def build_progressive_queries(description: str) -> List[Tuple[str, List[str], str]]:
    """Build progressively relaxed SQL queries for better recall."""
    tokens = extract_tokens(description)
    
    if not tokens:
        return []
    
    queries = []
    
    # Strategy 1: All tokens must match (most restrictive)
    if len(tokens) > 1:
        sql_conditions = []
        params = []
        for token in tokens:
            sql_conditions.append("UPPER(Item_Desc) LIKE ?")
            params.append(f"%{token.upper()}%")
        
        queries.append((
            " AND " + " AND ".join(sql_conditions),
            params,
            f"exact_all_tokens ({len(tokens)} tokens)"
        ))
    
    # Strategy 2: Most important tokens (first 2-3 tokens)
    if len(tokens) > 2:
        important_tokens = tokens[:3]
        sql_conditions = []
        params = []
        for token in important_tokens:
            sql_conditions.append("UPPER(Item_Desc) LIKE ?")
            params.append(f"%{token.upper()}%")
        
        queries.append((
            " AND " + " AND ".join(sql_conditions),
            params,
            f"important_tokens ({len(important_tokens)} of {len(tokens)} tokens)"
        ))
    
    # Strategy 3: Any token matches (most permissive)
    sql_conditions = []
    params = []
    for token in tokens:
        sql_conditions.append("UPPER(Item_Desc) LIKE ?")
        params.append(f"%{token.upper()}%")
    
    queries.append((
        " AND (" + " OR ".join(sql_conditions) + ")",
        params,
        f"any_token ({len(tokens)} tokens)"
    ))
    
    # Strategy 4: Partial string match (fallback)
    queries.append((
        " AND UPPER(Item_Desc) LIKE ?",
        [f"%{description.upper()}%"],
        "partial_string"
    ))
    
    return queries

# ────────────────────────────────────────────────────────────────
# Main Implementation
# ────────────────────────────────────────────────────────────────

async def item_lookup_impl(
    item_id: Optional[int] = None,
    description: Optional[str] = None,
    limit: int = 50,
    min_score: Optional[float] = None,
    enable_progressive_search: bool = True,
) -> Dict[str, Any]:
    """Enhanced search of **product_view** with advanced fuzzy matching.

    Parameters
    ----------
    item_id : int | None
        Exact `Item_ID` to match.
    description : str | None
        Free-text search with advanced fuzzy matching across multiple fields.
    limit : int
        Number of rows returned after ranking.
    min_score : float | None
        Minimum fuzzy match score (0-100). Defaults to 60.0.
    enable_progressive_search : bool
        Enable progressive search fallback for better recall.
    """
    
    config = SearchConfig(
        min_score_threshold=min_score or 60.0,
        use_progressive_search=enable_progressive_search
    )
    
    # ── Base SQL --------------------------------------------------------
    base_sql = """
        SELECT TOP (?)
               Item_ID         AS item_id,
               Item_Desc       AS description,
               Category_Desc   AS category,
               Department_Desc AS department,
               UPC,
               Size_Desc       AS size,
               Brand           AS brand
        FROM   PDI_Warehouse_1539_01.dbo.product_view WITH (NOLOCK)
        WHERE  UPPER(Brand) NOT LIKE '%UNAUTH%'
          AND  UPPER(Brand) NOT LIKE '%DEAUTH%'
    """

    # ------------------------------------------------------------------
    # Exact item lookup (unchanged - fast path)
    # ------------------------------------------------------------------
    if item_id is not None:
        sql = base_sql + " AND Item_ID = ? ORDER BY Item_Desc"
        params = [1, item_id]
        try:
            rows = execute_query(sql, params)
            metadata = {
                "search_type": "exact_id",
                "filters": {"item_id": item_id},
                "rapidfuzz_available": RAPIDFUZZ_AVAILABLE
            }
            return create_tool_response(rows, sql, params, metadata)
        except Exception as exc:  # pragma: no cover
            return create_tool_response([], sql, params, error=str(exc))

    # ------------------------------------------------------------------
    # Description search with enhanced fuzzy matching
    # ------------------------------------------------------------------
    if not description:
        return create_tool_response(
            [], base_sql, [], 
            error="Either item_id or description is required"
        )

    if not RAPIDFUZZ_AVAILABLE:
        # Fallback to basic LIKE search
        sql = base_sql + " AND UPPER(Item_Desc) LIKE ? ORDER BY Item_Desc"
        params = [limit, f"%{description.upper()}%"]
        try:
            rows = execute_query(sql, params)
            metadata = {
                "search_type": "basic_fallback",
                "rapidfuzz_available": False,
                "filters": {"description": description}
            }
            return create_tool_response(rows, sql, params, metadata)
        except Exception as exc:  # pragma: no cover
            return create_tool_response([], sql, params, error=str(exc))

    # Progressive search with fuzzy ranking
    all_candidates = []
    search_metadata = {
        "search_type": "enhanced_fuzzy",
        "rapidfuzz_available": True,
        "progressive_search": config.use_progressive_search,
        "min_score_threshold": config.min_score_threshold,
        "field_weights": config.multi_field_weights,
        "strategies_attempted": []
    }
    
    if config.use_progressive_search:
        progressive_queries = build_progressive_queries(description)
    else:
        # Single strategy: all tokens
        tokens = extract_tokens(description)
        sql_conditions = []
        token_params = []
        for token in tokens:
            sql_conditions.append("UPPER(Item_Desc) LIKE ?")
            token_params.append(f"%{token.upper()}%")
        
        progressive_queries = [(
            " AND " + " AND ".join(sql_conditions) if sql_conditions else "",
            token_params,
            "single_strategy"
        )]
    
    for strategy_sql, strategy_params, strategy_name in progressive_queries:
        sql = base_sql + strategy_sql + " ORDER BY Item_Desc"
        params = [config.max_candidates] + strategy_params
        
        try:
            candidates = execute_query(sql, params)
            search_metadata["strategies_attempted"].append({
                "name": strategy_name,
                "candidates_found": len(candidates),
                "sql_fragment": strategy_sql
            })
            
            if candidates:
                all_candidates.extend(candidates)
                if len(all_candidates) >= config.max_candidates:
                    break  # We have enough candidates
                    
        except Exception as exc:  # pragma: no cover
            search_metadata["strategies_attempted"].append({
                "name": strategy_name,
                "error": str(exc)
            })
            continue
    
    # Remove duplicates while preserving order
    seen_ids = set()
    unique_candidates = []
    for candidate in all_candidates:
        if candidate["item_id"] not in seen_ids:
            seen_ids.add(candidate["item_id"])
            unique_candidates.append(candidate)
    
    if not unique_candidates:
        return create_tool_response([], base_sql, [], metadata=search_metadata)
    
    # Enhanced multi-field fuzzy scoring
    scored_results = []
    for candidate in unique_candidates:
        scoring_result = score_item_multi_field(description, candidate, config)
        if scoring_result.composite_score >= config.min_score_threshold:
            scored_results.append(scoring_result)
    
    # Sort by composite score descending
    scored_results.sort(key=lambda x: x.composite_score, reverse=True)
    
    # Format final results
    final_results = []
    for result in scored_results[:limit]:
        item_with_score = result.item.copy()
        item_with_score.update({
            "fuzzy_score": round(result.composite_score, 1),
            "field_scores": {k: round(v, 1) for k, v in result.field_scores.items()},
            "matching_algorithm": result.matching_algorithm
        })
        final_results.append(item_with_score)
    
    # Enhanced metadata
    search_metadata.update({
        "query_processed": preprocess_text(description),
        "tokens_extracted": extract_tokens(description),
        "total_candidates": len(unique_candidates),
        "candidates_above_threshold": len(scored_results),
        "results_returned": len(final_results),
        "score_range": {
            "min": round(min(r.composite_score for r in scored_results), 1) if scored_results else 0,
            "max": round(max(r.composite_score for r in scored_results), 1) if scored_results else 0
        }
    })
    
    return create_tool_response(
        final_results, 
        base_sql + " -- Enhanced fuzzy search with progressive fallback", 
        [], 
        search_metadata
    )


# ────────────────────────────────────────────────────────────────
# Tool Registration
# ────────────────────────────────────────────────────────────────

item_lookup_tool = Tool(
    name="item_lookup",
    description=(
        "Enhanced product lookup in **product_view** with advanced fuzzy search. "
        "Supports exact `item_id` match or intelligent multi-field fuzzy search "
        "with progressive fallback. Uses RapidFuzz for superior matching accuracy. "
        "Example: '20oz coke zero' → matches 'COCA COLA ZERO SUGAR 20 OZ CAN'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "item_id": {
                "type": "integer",
                "description": "Exact item ID for precise lookup"
            },
            "description": {
                "type": "string", 
                "description": "Free-text search with fuzzy matching (word order flexible, typos OK)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 50
            },
            "min_score": {
                "type": "number",
                "description": "Minimum fuzzy match score (0-100, default: 60.0)",
                "minimum": 0,
                "maximum": 100
            },
            "enable_progressive_search": {
                "type": "boolean", 
                "description": "Enable progressive search fallback for better recall",
                "default": True
            }
        },
        "required": [],
        "additionalProperties": False,
    },
)

item_lookup_tool._implementation = item_lookup_impl