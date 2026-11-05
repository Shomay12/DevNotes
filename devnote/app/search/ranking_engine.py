import re
from typing import List, Optional
from devnote.app.schemas.search import SearchResultItem
from devnote.app.search.query_classifier import QueryClassification

class RankingEngine:
    """
    Ranks search results multi-dimensionally:
    - Textual relevance (exact phrase, keyword overlap in title, snippet, code)
    - Query intent alignment (e.g. error queries boost Stack Overflow; concept queries boost Official Docs)
    - Language and framework compatibility
    - Official documentation trust tier
    - Community freshness & validation indicators
    """

    @classmethod
    def rank(
        cls,
        results: List[SearchResultItem],
        classification: QueryClassification,
        user_category: Optional[str] = "all",
        user_language: Optional[str] = None,
        user_framework: Optional[str] = None
    ) -> List[SearchResultItem]:
        q_raw = classification.query.strip().lower()
        q_tokens = [t.lower() for t in classification.keywords if len(t) > 1]

        scored_results = []
        for item in results:
            score = 50.0  # base score
            t_lower = item.title.lower()
            s_lower = item.snippet.lower()
            c_lower = (item.code or "").lower()

            # 1. Exact Phrase Match
            if q_raw and q_raw in t_lower:
                score += 80.0
            elif q_raw and q_raw in s_lower:
                score += 35.0

            # 2. Token overlap in title (weight: 15 per token)
            for tok in q_tokens:
                if tok in t_lower:
                    score += 20.0
                elif tok in s_lower:
                    score += 8.0
                elif tok in c_lower:
                    score += 5.0

            # 3. Intent alignment boost
            intent = classification.intent
            cat = item.category.lower()

            if intent == "error":
                if cat in ("stackoverflow", "error"):
                    score += 45.0
                elif "github" in cat:
                    score += 20.0
            elif intent in ("concept", "api"):
                if cat in ("doc", "concept", "offline"):
                    score += 45.0
            elif intent == "code":
                if item.code:
                    score += 40.0
                if cat in ("github", "code", "snippet"):
                    score += 30.0

            # 4. Language compatibility boost
            target_lang = user_language or classification.language
            if target_lang and item.language:
                if target_lang.lower() == item.language.lower():
                    score += 35.0
                else:
                    score -= 15.0

            # 5. Framework compatibility boost
            target_fw = user_framework or classification.framework
            if target_fw:
                fw_clean = target_fw.lower()
                if fw_clean in t_lower or fw_clean in s_lower or (item.framework and item.framework.lower() == fw_clean):
                    score += 30.0

            # 6. Official documentation / Trust status boost
            source_lower = (item.source or "").lower()
            if any(trusted in source_lower for trusted in ["documentation", "docs", "python", "mdn", "official", "devdocs"]):
                score += 25.0

            # 7. Code presence bonus
            if item.code and len(item.code.strip()) > 10:
                score += 15.0

            # 8. Community score (capped to prevent vote domination)
            if item.stars:
                score += min(15.0, item.stars / 1000.0)
            if item.score:
                score += min(15.0, max(0, item.score) / 10.0)
            if item.is_answered:
                score += 10.0

            # Set computed score on item
            item.relevance_score = round(score, 1)
            scored_results.append((score, item))

        # Sort descending by score
        scored_results.sort(key=lambda pair: pair[0], reverse=True)
        return [pair[1] for pair in scored_results]
