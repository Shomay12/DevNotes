import re
from typing import Dict, Any, List, Optional

class QueryClassification:
    def __init__(
        self,
        query: str,
        intent: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        recommended_providers: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ):
        self.query = query
        self.intent = intent  # 'concept', 'error', 'code', 'api', 'research'
        self.language = language
        self.framework = framework
        self.recommended_providers = recommended_providers or []
        self.keywords = keywords or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent,
            "language": self.language,
            "framework": self.framework,
            "recommended_providers": self.recommended_providers,
            "keywords": self.keywords
        }

class QueryClassifier:
    """
    Lightweight, deterministic query classifier and routing engine.
    Analyzes developer queries for intent, language, framework, and
    recommends the most suitable search providers.
    """

    ERROR_PATTERNS = [
        r"\b(?:error|exception|traceback|failed|fatal|cannot|invalid|not found|undefined|nullpointer|overflow|syntaxerror|typeerror|attributeerror|keyerror|indexerror|modulenotfounderror|valueerror|zerodivisionerror|recursionerror|filenotfounderror)\b",
        r"\b(?:errno \d+|404 not found|500 internal server error|corrupted|abort|crashed|segmentation fault|panic:)\b",
        r"cannot read propert(?:y|ies)",
        r"is not defined",
        r"is not a function",
        r"not subscriptable"
    ]

    CODE_PATTERNS = [
        r"\b(?:example|sample|how to|implement|implementation|template|snippet|algorithm|function|code for|pattern|boiler-?plate|use-?case)\b",
        r"\b(?:quick-?sort|merge-?sort|binary-?search|debounce|throttle|regex email|breadth-?first|depth-?first)\b"
    ]

    API_PATTERNS = [
        r"\b(?:api|method|function|class|interface|parameters?|args?|kwargs?|endpoint|signature|syntax|module|decorator|property|attribute|returns?)\b",
        r"\.[a-zA-Z0-9_]+\([^\)]*\)",  # e.g. .reshape() or .fit()
        r"\b(?:docs?|reference|manual|spec|specification)\b"
    ]

    RESEARCH_PATTERNS = [
        r"\b(?:best|vs|versus|compare|comparison|alternative|benchmark|state of the art|trade-?off|architecture|evaluation)\b",
        r"\b(?:for rag|for ai|for production|scalability)\b"
    ]

    LANGUAGES = {
        "python": [r"\bpython\b", r"\bpy\b", r"\bpip\b", r"\bdef\b", r"\bself\b", r"\bdecorator\b", r"\basyncio\b", r"\bpydantic\b"],
        "javascript": [r"\bjavascript\b", r"\bjs\b", r"\bnode(?:\.js)?\b", r"\bnpm\b", r"\bconst\b", r"\bconsole\.log\b", r"\bes6\b", r"\btypescript\b", r"\bts\b"],
        "rust": [r"\brust\b", r"\bcargo\b", r"\bimpl\b", r"\btrait\b", r"\blifetime\b", r"\bmut\b", r"\bunwrap\(\)\b"],
        "go": [r"\bgolang\b", r"\bgo\b", r"\bgoroutine\b", r"\bchannel\b", r"\bstruct\b", r"\bfunc\b"],
        "java": [r"\bjava\b", r"\bmaven\b", r"\bgradle\b", r"\bpublic static void\b", r"\bspring\b", r"\bjvm\b"],
        "c++": [r"\bc\+\+\b", r"\bcpp\b", r"\bstd::\b", r"\bvector\b", r"\bpointer\b", r"\btemplate<"],
        "c": [r"\bc programming\b", r"\bgcc\b", r"\bclang\b", r"\bmalloc\b", r"\bprintf\b"],
        "sql": [r"\bsql\b", r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\bsqlite\b", r"\bselect\b", r"\bjoin\b", r"\bgroup by\b"],
        "dart": [r"\bdart\b", r"\bflutter\b", r"\bwidget\b", r"\bpubspec\b", r"\bstateful\b"],
        "php": [r"\bphp\b", r"\bcomposer\b", r"\blaravel\b", r"\$\w+"],
    }

    FRAMEWORKS = {
        "fastapi": [r"\bfastapi\b", r"\buvicorn\b", r"\bapirouter\b"],
        "django": [r"\bdjango\b", r"\bmanage\.py\b", r"\bqueryset\b"],
        "flask": [r"\bflask\b", r"\bwerkzeug\b", r"\bapp\.route\b"],
        "react": [r"\breact(?:\.js)?\b", r"\busestate\b", r"\buseeffect\b", r"\bjx\b", r"\bnext(?:\.js)?\b"],
        "node.js": [r"\bnode(?:\.js)?\b", r"\bexpress(?:\.js)?\b"],
        "flutter": [r"\bflutter\b", r"\bstatelesswidget\b"],
        "docker": [r"\bdocker\b", r"\bdockerfile\b", r"\bdocker-compose\b", r"\bcontainer\b"],
        "git": [r"\bgit\b", r"\brebase\b", r"\bcommit\b", r"\bcherry-pick\b"],
        "pytorch": [r"\bpytorch\b", r"\btorch\b", r"\bnn\.module\b", r"\btensor\b"],
        "tensorflow": [r"\btensorflow\b", r"\btf\b", r"\bkeras\b"]
    }

    @classmethod
    def classify(cls, query: str) -> QueryClassification:
        q = query.strip()
        q_lower = q.lower()

        # 1. Detect Language
        detected_language = None
        for lang, patterns in cls.LANGUAGES.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                detected_language = lang
                break

        # 2. Detect Framework
        detected_framework = None
        for fw, patterns in cls.FRAMEWORKS.items():
            if any(re.search(pat, q_lower) for pat in patterns):
                detected_framework = fw
                break

        # If framework implies language, auto-fill language
        if detected_framework in ("fastapi", "django", "flask", "pytorch", "tensorflow") and not detected_language:
            detected_language = "python"
        elif detected_framework in ("react", "node.js") and not detected_language:
            detected_language = "javascript"
        elif detected_framework == "flutter" and not detected_language:
            detected_language = "dart"

        # 3. Detect Intent
        intent = "concept"  # default
        recommended_providers = []

        if any(re.search(pat, q_lower) for pat in cls.ERROR_PATTERNS):
            intent = "error"
            recommended_providers = ["stackoverflow", "github", "devdocs", "local_docs"]
        elif any(re.search(pat, q_lower) for pat in cls.CODE_PATTERNS):
            intent = "code"
            recommended_providers = ["github", "devdocs", "stackoverflow", "local_docs"]
        elif any(re.search(pat, q_lower) for pat in cls.API_PATTERNS):
            intent = "api"
            recommended_providers = ["devdocs", "local_docs", "google", "github"]
        elif any(re.search(pat, q_lower) for pat in cls.RESEARCH_PATTERNS):
            intent = "research"
            recommended_providers = ["google", "github", "devdocs"]
        else:
            intent = "concept"
            recommended_providers = ["devdocs", "local_docs", "google", "stackoverflow"]

        # Tokenize meaningful keywords
        clean_words = re.findall(r"[a-zA-Z0-9_\-\.\:]{2,}", q)
        stop_words = {"the", "a", "an", "is", "in", "for", "to", "and", "or", "of", "with", "on", "at", "by", "from"}
        keywords = [w for w in clean_words if w.lower() not in stop_words]

        return QueryClassification(
            query=q,
            intent=intent,
            language=detected_language,
            framework=detected_framework,
            recommended_providers=recommended_providers,
            keywords=keywords
        )
