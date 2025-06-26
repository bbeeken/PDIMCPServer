"""Enhanced product lookup with advanced RapidFuzz scoring and size-specific business logic.

This tool queries **PDI_Warehouse_1539_01.dbo.product_view** and supports:
• Exact *item_id* match
• Multi-field fuzzy search with weighted composite scoring
• Size-specific matching with product separation
• Business logic prioritization (regular > flavored variants)
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
    high_confidence_threshold: float = 85.0  # Threshold for accepting single result
    multi_field_weights: Dict[str, float] = None  # Field weights for composite scoring
    use_progressive_search: bool = True  # Enable progressive search fallback
    max_candidates: int = 500  # Maximum candidates to fetch for ranking
    prioritize_regular_variants: bool = True  # Prefer regular over flavored variants
    
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
    business_score: float  # Score after applying business logic
    field_scores: Dict[str, float]
    matching_algorithm: str
    size_match: bool = False
    variant_type: str = "unknown"  # regular, flavored, diet, etc.

@dataclass
class QueryComponents:
    """Parsed components of user query."""
    original_query: str
    product_name: str
    size: Optional[str] = None
    size_variants: List[str] = None  # Different ways to write the size
    
    def __post_init__(self):
        if self.size_variants is None:
            self.size_variants = []

# ────────────────────────────────────────────────────────────────
# Size and Product Extraction
# ────────────────────────────────────────────────────────────────

def extract_size_and_product(query: str) -> QueryComponents:
    """Extract size and product components from query with size normalization."""
    original = query.strip()
    query_lower = query.lower().strip()
    
    # Common size patterns
    size_patterns = [
        (r'(\d+(?:\.\d+)?)\s*oz\b', lambda m: f"{m.group(1)}oz"),
        (r'(\d+(?:\.\d+)?)\s*ounce(?:s)?\b', lambda m: f"{m.group(1)}oz"),
        (r'(\d+(?:\.\d+)?)\s*ml\b', lambda m: f"{m.group(1)}ml"),
        (r'(\d+(?:\.\d+)?)\s*liter?(?:s)?\b', lambda m: f"{m.group(1)}l"),
        (r'(\d+(?:\.\d+)?)\s*lb(?:s)?\b', lambda m: f"{m.group(1)}lb"),
        (r'(\d+(?:\.\d+)?)\s*pound(?:s)?\b', lambda m: f"{m.group(1)}lb"),
        (r'(\d+)\s*pack?\b', lambda m: f"{m.group(1)}pk"),
        (r'(\d+)\s*ct\b', lambda m: f"{m.group(1)}ct"),
        (r'(\d+)\s*count\b', lambda m: f"{m.group(1)}ct"),
    ]
    
    size = None
    size_variants = []
    product_name = query_lower
    
    for pattern, normalizer in size_patterns:
        match = re.search(pattern, query_lower)
        if match:
            size = normalizer(match)
            
            # Generate size variants for better matching
            if 'oz' in size:
                base_num = match.group(1)
                size_variants = [
                    f"{base_num}oz", f"{base_num} oz", f"{base_num}OZ", f"{base_num} OZ",
                    f"{base_num}ounce", f"{base_num} ounce", f"{base_num} ounces"
                ]
            elif 'ml' in size:
                base_num = match.group(1)
                size_variants = [f"{base_num}ml", f"{base_num} ml", f"{base_num}ML", f"{base_num} ML"]
            # Add more variant patterns as needed
            
            # Remove size from product name
            product_name = re.sub(pattern, '', query_lower).strip()
            break
    
    return QueryComponents(
        original_query=original,
        product_name=product_name,
        size=size,
        size_variants=size_variants
    )

def detect_variant_type(description: str) -> str:
    """Detect if item is regular, diet, flavored, etc."""
    desc_upper = description.upper()
    
    # Diet/Zero variants
    if any(term in desc_upper for term in ['DIET', 'ZERO', 'LIGHT', 'LITE']):
        return "diet"
    
    # Flavored variants
    flavor_terms = ['CHERRY', 'VANILLA', 'LEMON', 'LIME', 'ORANGE', 'GRAPE', 'STRAWBERRY', 
                   'PEACH', 'MANGO', 'BERRY', 'MINT', 'CHOCOLATE']
    if any(term in desc_upper for term in flavor_terms):
        return "flavored"
    
    # Energy/functional
    if any(term in desc_upper for term in ['ENERGY', 'CAFFEINE', 'PLUS', 'MAX']):
        return "functional"
    
    # Regular variant (most basic form)
    return "regular"

def has_size_match(description: str, query_components: QueryComponents) -> bool:
    """Check if description contains the size from query."""
    if not query_components.size or not query_components.size_variants:
        return False
    
    desc_upper = description.upper()
    
    # Check all size variants
    for variant in query_components.size_variants:
        if variant.upper() in desc_upper:
            return True
    
    return False

# ────────────────────────────────────────────────────────────────
# Size and Product Extraction
# ────────────────────────────────────────────────────────────────

def extract_size_and_product(query: str) -> QueryComponents:
    """Extract size and product components from query with size normalization."""
    original = query.strip()
    query_lower = query.lower().strip()
    
    # Common size patterns
    size_patterns = [
        (r'(\d+(?:\.\d+)?)\s*oz\b', lambda m: f"{m.group(1)}oz"),
        (r'(\d+(?:\.\d+)?)\s*ounce(?:s)?\b', lambda m: f"{m.group(1)}oz"),
        (r'(\d+(?:\.\d+)?)\s*ml\b', lambda m: f"{m.group(1)}ml"),
        (r'(\d+(?:\.\d+)?)\s*liter?(?:s)?\b', lambda m: f"{m.group(1)}l"),
        (r'(\d+(?:\.\d+)?)\s*lb(?:s)?\b', lambda m: f"{m.group(1)}lb"),
        (r'(\d+(?:\.\d+)?)\s*pound(?:s)?\b', lambda m: f"{m.group(1)}lb"),
        (r'(\d+)\s*pack?\b', lambda m: f"{m.group(1)}pk"),
        (r'(\d+)\s*ct\b', lambda m: f"{m.group(1)}ct"),
        (r'(\d+)\s*count\b', lambda m: f"{m.group(1)}ct"),
    ]
    
    size = None
    size_variants = []
    product_name = query_lower
    
    for pattern, normalizer in size_patterns:
        match = re.search(pattern, query_lower)
        if match:
            size = normalizer(match)
            
            # Generate size variants for better matching
            if 'oz' in size:
                base_num = match.group(1)
                size_variants = [
                    f"{base_num}oz", f"{base_num} oz", f"{base_num}OZ", f"{base_num} OZ",
                    f"{base_num}ounce", f"{base_num} ounce", f"{base_num} ounces"
                ]
            elif 'ml' in size:
                base_num = match.group(1)
                size_variants = [f"{base_num}ml", f"{base_num} ml", f"{base_num}ML", f"{base_num} ML"]
            # Add more variant patterns as needed
            
            # Remove size from product name
            product_name = re.sub(pattern, '', query_lower).strip()
            break
    
    return QueryComponents(
        original_query=original,
        product_name=product_name,
        size=size,
        size_variants=size_variants
    )

def detect_variant_type(description: str) -> str:
    """Detect if item is regular, diet, flavored, etc."""
    desc_upper = description.upper()
    
    # Diet/Zero variants
    if any(term in desc_upper for term in ['DIET', 'ZERO', 'LIGHT', 'LITE']):
        return "diet"
    
    # Flavored variants
    flavor_terms = ['CHERRY', 'VANILLA', 'LEMON', 'LIME', 'ORANGE', 'GRAPE', 'STRAWBERRY', 
                   'PEACH', 'MANGO', 'BERRY', 'MINT', 'CHOCOLATE']
    if any(term in desc_upper for term in flavor_terms):
        return "flavored"
    
    # Energy/functional
    if any(term in desc_upper for term in ['ENERGY', 'CAFFEINE', 'PLUS', 'MAX']):
        return "functional"
    
    # Regular variant (most basic form)
    return "regular"

def has_size_match(description: str, query_components: QueryComponents) -> bool:
    """Check if description contains the size from query."""
    if not query_components.size or not query_components.size_variants:
        return False
    
    desc_upper = description.upper()
    
    # Check all size variants
    for variant in query_components.size_variants:
        if variant.upper() in desc_upper:
            return True
    
    return False

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

def score_item_multi_field(query: str, item: Dict[str, Any], config: SearchConfig, 
                          query_components: QueryComponents) -> ScoringResult:
    """Score an item across multiple fields with weighted composite scoring and business logic."""
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
    
    # Business logic scoring
    business_score = composite_score
    variant_type = detect_variant_type(item.get('description', ''))
    size_match = has_size_match(item.get('description', ''), query_components)
    
    # Size match bonus (huge boost for exact size matches)
    if size_match:
        business_score *= 1.5
    
    # Variant type preferences when size is specified
    if query_components.size and config.prioritize_regular_variants:
        if variant_type == "regular":
            business_score *= 1.3  # Strong preference for regular variants
        elif variant_type == "diet":
            business_score *= 1.1  # Slight preference for diet over flavored
        elif variant_type == "flavored":
            business_score *= 0.9  # Slight penalty for flavored variants
    
    # Use the field with highest score for algorithm metadata
    best_field_score = max(field_scores.values()) if field_scores else 0.0
    algorithm = f"multi-field (max: {best_field_score:.1f})"
    
    return ScoringResult(
        item=item,
        composite_score=composite_score,
        business_score=business_score,
        field_scores=field_scores,
        matching_algorithm=algorithm,
        size_match=size_match,
        variant_type=variant_type
    )

# ────────────────────────────────────────────────────────────────
# Smart Result Selection
# ────────────────────────────────────────────────────────────────

def select_best_match(scored_results: List[ScoringResult], query_components: QueryComponents, 
                     config: SearchConfig) -> List[ScoringResult]:
    """Apply intelligent result selection based on query context."""
    if not scored_results:
        return []
    
    # Sort by business score (not just fuzzy score)
    scored_results.sort(key=lambda x: x.business_score, reverse=True)
    
    # If we have a high-confidence match with size match, return just that one
    if (query_components.size and 
        scored_results[0].business_score >= config.high_confidence_threshold and
        scored_results[0].size_match):
        
        # Return the single best match for sized queries
        return [scored_results[0]]
    
    # For non-sized queries or lower confidence, return multiple results
    return scored_results

# ────────────────────────────────────────────────────────────────
# Smart Result Selection
# ────────────────────────────────────────────────────────────────

def select_best_match(scored_results: List[ScoringResult], query_components: QueryComponents, 
                     config: SearchConfig) -> List[ScoringResult]:
    """Apply intelligent result selection based on query context."""
    if not scored_results:
        return []
    
    # Sort by business score (not just fuzzy score)
    scored_results.sort(key=lambda x: x.business_score, reverse=True)
    
    # If we have a high-confidence match with size match, return just that one
    if (query_components.size and 
        scored_results[0].business_score >= config.high_confidence_threshold and
        scored_results[0].size_match):
        
        # Return the single best match for sized queries
        return [scored_results[0]]
    
    # For non-sized queries or lower confidence, return multiple results
    return scored_results

# ────────────────────────────────────────────────────────────────
# Progressive Search Strategy
# ────────────────────────────────────────────────────────────────

def build_progressive_queries(description: str, query_components: QueryComponents) -> List[Tuple[str, List[str], str]]:
    """Build progressively relaxed SQL queries with size-aware strategies."""
    queries = []
    
    # Strategy 1: Exact query as provided (highest priority for sized items)
    queries.append((
        " AND UPPER(Item_Desc) LIKE ?",
        [f"%{description.upper()}%"],
        "exact_query"
    ))
    
    # Strategy 2: Size + product name (if size was detected)
    if query_components.size and query_components.product_name:
        # Try all size variants with product name
        for size_variant in query_components.size_variants[:3]:  # Limit to top 3 variants
            sql_conditions = [
                "UPPER(Item_Desc) LIKE ?",
                "UPPER(Item_Desc) LIKE ?"
            ]
            params = [f"%{query_components.product_name.upper()}%", f"%{size_variant.upper()}%"]
            
            queries.append((
                " AND " + " AND ".join(sql_conditions),
                params,
                f"size_product_match ({size_variant})"
            ))
    
    # Strategy 3: Product tokens only (for fallback)
    tokens = extract_tokens(query_components.product_name)
    if tokens:
        if len(tokens) > 1:
            sql_conditions = []
            params = []
            for token in tokens:
                sql_conditions.append("UPPER(Item_Desc) LIKE ?")
                params.append(f"%{token.upper()}%")
            
            queries.append((
                " AND " + " AND ".join(sql_conditions),
                params,
                f"product_tokens ({len(tokens)} tokens)"
            ))
    
        # Strategy 4: Any token matches (most permissive)
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
    prioritize_single_match: bool = True,
) -> Dict[str, Any]:
    """Enhanced search of **product_view** with size-specific business logic.

    Parameters
    ----------
    item_id : int | None
        Exact `Item_ID` to match.
    description : str | None
        Free-text search with advanced fuzzy matching and size extraction.
    limit : int
        Number of rows returned after ranking.
    min_score : float | None
        Minimum fuzzy match score (0-100). Defaults to 60.0.
    enable_progressive_search : bool
        Enable progressive search fallback for better recall.
    prioritize_single_match : bool
        For sized items, prefer returning single best match over multiple variants.
    """
    
    config = SearchConfig(
        min_score_threshold=min_score or 60.0,
        use_progressive_search=enable_progressive_search,
        prioritize_regular_variants=True
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
    # Description search with size-aware business logic
    # ------------------------------------------------------------------
    if not description:
        return create_tool_response(
            [], base_sql, [], 
            error="Either item_id or description is required"
        )

    # Parse query components
    query_components = extract_size_and_product(description)
    
    if not RAPIDFUZZ_AVAILABLE:
        # Fallback to basic LIKE search
        sql = base_sql + " AND UPPER(Item_Desc) LIKE ? ORDER BY Item_Desc"
        params = [limit, f"%{description.upper()}%"]
        try:
            rows = execute_query(sql, params)
            metadata = {
                "search_type": "basic_fallback",
                "rapidfuzz_available": False,
                "filters": {"description": description},
                "query_components": {
                    "original": query_components.original_query,
                    "product": query_components.product_name,
                    "size": query_components.size
                }
            }
            return create_tool_response(rows, sql, params, metadata)
        except Exception as exc:  # pragma: no cover
            return create_tool_response([], sql, params, error=str(exc))

    # Enhanced search with size-aware progressive queries
    all_candidates = []
    search_metadata = {
        "search_type": "size_aware_fuzzy",
        "rapidfuzz_available": True,
        "progressive_search": config.use_progressive_search,
        "min_score_threshold": config.min_score_threshold,
        "field_weights": config.multi_field_weights,
        "strategies_attempted": [],
        "query_components": {
            "original": query_components.original_query,
            "product": query_components.product_name,
            "size": query_components.size,
            "size_variants": query_components.size_variants
        }
    }
    
    # Build search strategies
    if config.use_progressive_search:
        progressive_queries = build_progressive_queries(description, query_components)
    else:
        # Single strategy: exact query
        progressive_queries = [(
            " AND UPPER(Item_Desc) LIKE ?",
            [f"%{description.upper()}%"],
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
                # For sized queries, if we found good candidates, don't keep searching
                if query_components.size and len(candidates) >= 5:
                    break
                if len(all_candidates) >= config.max_candidates:
                    break
                    
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
    
    # Enhanced multi-field fuzzy scoring with business logic
    scored_results = []
    for candidate in unique_candidates:
        scoring_result = score_item_multi_field(description, candidate, config, query_components)
        if scoring_result.composite_score >= config.min_score_threshold:
            scored_results.append(scoring_result)
    
    # Smart result selection (size-aware)
    if prioritize_single_match:
        final_scored_results = select_best_match(scored_results, query_components, config)
    else:
        final_scored_results = scored_results
        final_scored_results.sort(key=lambda x: x.business_score, reverse=True)
    
    # Limit results
    final_scored_results = final_scored_results[:limit]
    
    # Format final results
    final_results = []
    for result in final_scored_results:
        item_with_score = result.item.copy()
        item_with_score.update({
            "fuzzy_score": round(result.composite_score, 1),
            "business_score": round(result.business_score, 1),
            "field_scores": {k: round(v, 1) for k, v in result.field_scores.items()},
            "matching_algorithm": result.matching_algorithm,
            "size_match": result.size_match,
            "variant_type": result.variant_type
        })
        final_results.append(item_with_score)
    
    # Enhanced metadata
    search_metadata.update({
        "total_candidates": len(unique_candidates),
        "candidates_above_threshold": len(scored_results),
        "results_returned": len(final_results),
        "single_match_returned": len(final_results) == 1 and query_components.size is not None,
        "score_range": {
            "fuzzy_min": round(min(r.composite_score for r in scored_results), 1) if scored_results else 0,
            "fuzzy_max": round(max(r.composite_score for r in scored_results), 1) if scored_results else 0,
            "business_min": round(min(r.business_score for r in scored_results), 1) if scored_results else 0,
            "business_max": round(max(r.business_score for r in scored_results), 1) if scored_results else 0
        }
    })
    
    return create_tool_response(
        final_results, 
        base_sql + " -- Size-aware fuzzy search with business logic", 
        [], 
        search_metadata
    )


# ────────────────────────────────────────────────────────────────
# Tool Registration
# ────────────────────────────────────────────────────────────────

item_lookup_tool = Tool(
    name="item_lookup",
    description=(
        "Enhanced product lookup in **product_view** with size-specific business logic. "
        "Intelligently handles sized queries like '20oz coke' → returns 'COKE 20OZ' (single best match) "
        "rather than aggregating all Coke variants. Uses RapidFuzz + business rules for smart matching. "
        "Prioritizes regular variants over flavored when size is specified."
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
                "description": "Free-text search with size extraction (e.g., '20oz coke', '2 liter pepsi')"
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
            },
            "prioritize_single_match": {
                "type": "boolean",
                "description": "For sized items, return single best match instead of multiple variants",
                "default": True
            }
        },
        "required": [],
        "additionalProperties": False,
    },
)

item_lookup_tool._implementation = item_lookup_impl