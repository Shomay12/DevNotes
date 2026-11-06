"""
DevNote Research Reader — Content Sanitizer.
Sanitizes untrusted HTML retrieved from the web, eliminating scripts, dangerous attributes,
unrelated navigation/ads, and normalizing links and code blocks for technical reading.
"""

import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment, Tag

# Tags that must be stripped completely along with their content
DISALLOWED_TAGS = {
    "script", "style", "iframe", "object", "embed", "applet",
    "meta", "link", "form", "button", "input", "textarea", "select",
    "noscript", "canvas", "svg", "frame", "frameset"
}

# Whitelist of allowed HTML tags for reader view
ALLOWED_TAGS = {
    "article", "section", "header", "div", "main",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "span", "blockquote", "pre", "code", "kbd", "samp", "var",
    "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    "a", "img", "figure", "figcaption",
    "b", "strong", "i", "em", "mark", "small", "del", "ins", "sub", "sup", "u",
    "hr", "br", "details", "summary"
}

# Allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "code": {"class", "data-lang", "data-language"},
    "pre": {"class", "data-lang", "data-language"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan"},
    "details": {"open"},
}

# Class / ID patterns indicating ads, trackers, sidebars, cookie banners, popups
CLUTTER_PATTERNS = re.compile(
    r"(advert|banner-ad|google-ad|ad-container|cookie|consent|gdpr|newsletter|"
    r"social-share|share-buttons|sidebar-right|modal-backdrop|newsletter-signup|"
    r"disqus|comment-section|adzerk|outbrain|taboola)",
    re.I
)


def sanitize_html(raw_html: str, base_url: str = "") -> str:
    """
    Sanitizes raw HTML string for safe in-application rendering.
    - Strips all executable scripts and hazardous tags
    - Resolves relative URLs to absolute based on base_url
    - Strips ads, modals, and cookie banners
    - Normalizes code blocks and typography
    """
    if not raw_html or not raw_html.strip():
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove comments
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    # 2. Remove explicitly disallowed tags (including scripts & styles)
    for tag in soup.find_all(DISALLOWED_TAGS):
        tag.decompose()

    # 3. Remove clutter / ad elements
    for el in list(soup.find_all(True)):
        if not isinstance(el, Tag) or el.attrs is None:
            continue

        classes = " ".join(el.get("class", [])) if isinstance(el.get("class"), list) else str(el.get("class", ""))
        el_id = str(el.get("id", ""))
        role = str(el.get("role", "")).lower()

        if role in ("banner", "complementary", "alert") and not el.find(["h1", "h2", "pre"]):
            el.decompose()
            continue

        if CLUTTER_PATTERNS.search(classes) or CLUTTER_PATTERNS.search(el_id):
            if not el.find(["pre", "code", "table"]):
                el.decompose()

    # 4. Clean attributes and validate URLs
    for tag in list(soup.find_all(True)):
        if not isinstance(tag, Tag):
            continue

        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue

        if tag.attrs is None:
            tag.attrs = {}

        allowed_attrs = ALLOWED_ATTRIBUTES.get(tag.name, set())

        # Strip unapproved or dangerous attributes
        attrs_to_remove = []
        for attr, val in list(tag.attrs.items()):
            attr_lower = attr.lower()

            if attr_lower.startswith("on") or attr_lower == "style":
                attrs_to_remove.append(attr)
                continue

            if attr_lower not in allowed_attrs and attr_lower != "class":
                attrs_to_remove.append(attr)

        for attr in attrs_to_remove:
            del tag[attr]

        # Process Links
        if tag.name == "a":
            href = tag.get("href", "").strip()
            if not href or href.lower().startswith(("javascript:", "data:", "vbscript:")):
                tag["href"] = "#"
            elif base_url:
                tag["href"] = urljoin(base_url, href)
            tag["target"] = "_blank"
            tag["rel"] = "noopener noreferrer"

        # Process Images
        if tag.name == "img":
            src = tag.get("src", "").strip()
            if not src or src.lower().startswith(("javascript:", "vbscript:")):
                tag.decompose()
                continue
            elif base_url and not src.startswith("data:image/"):
                tag["src"] = urljoin(base_url, src)
            tag["loading"] = "lazy"

        # Preserve / Normalize Code Block classes
        if tag.name in ("code", "pre"):
            classes = tag.get("class", [])
            if isinstance(classes, str):
                classes = classes.split()
            valid_classes = [c for c in classes if re.match(r"^(language-|lang-|highlight-)", c, re.I)]
            if valid_classes:
                tag["class"] = valid_classes
            elif "class" in tag.attrs:
                del tag["class"]

    return str(soup)


def extract_code_blocks(html_content: str) -> list[dict]:
    """Extracts all code snippets from sanitized HTML for quick copy/insertion."""
    soup = BeautifulSoup(html_content, "html.parser")
    snippets = []

    for pre in soup.find_all("pre"):
        code_tag = pre.find("code")
        raw_code = code_tag.get_text() if code_tag else pre.get_text()
        raw_code = raw_code.strip()
        if not raw_code:
            continue

        language = "code"
        if code_tag and code_tag.get("class"):
            for cls in code_tag["class"]:
                if cls.startswith("language-") or cls.startswith("lang-"):
                    language = cls.split("-", 1)[1].lower()
                    break

        snippets.append({
            "language": language,
            "code": raw_code
        })

    return snippets
