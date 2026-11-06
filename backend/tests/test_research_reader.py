import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from devnote.app.main import app
from devnote.app.research.url_validator import validate_url_safety
from devnote.app.research.source_detector import detect_source, ReadingStrategy
from devnote.app.research.content_sanitizer import sanitize_html, extract_code_blocks
from devnote.app.research.providers.base_provider import ExtractedContent

client = TestClient(app)


def test_ssrf_and_url_validation():
    # 1. Reject localhost / loopback
    is_safe, msg = validate_url_safety("http://localhost:8000/api")
    assert is_safe is False
    assert "prohibited" in msg.lower() or "loopback" in msg.lower()

    is_safe, msg = validate_url_safety("http://127.0.0.1:3000")
    assert is_safe is False

    # 2. Reject private network IPs (RFC1918)
    is_safe, msg = validate_url_safety("http://192.168.1.100/admin")
    assert is_safe is False
    is_safe, msg = validate_url_safety("http://10.0.0.1/")
    assert is_safe is False
    is_safe, msg = validate_url_safety("http://172.16.0.5/")
    assert is_safe is False

    # 3. Reject cloud metadata IP
    is_safe, msg = validate_url_safety("http://169.254.169.254/latest/meta-data/")
    assert is_safe is False
    assert "metadata" in msg.lower() or "prohibited" in msg.lower()

    # 4. Reject unsupported schemes
    is_safe, msg = validate_url_safety("file:///etc/passwd")
    assert is_safe is False
    is_safe, msg = validate_url_safety("ftp://files.example.com")
    assert is_safe is False

    # 5. Allow safe public web URLs
    is_safe, _ = validate_url_safety("https://github.com/numpy/numpy")
    assert is_safe is True
    is_safe, _ = validate_url_safety("https://docs.python.org/3/")
    assert is_safe is True


def test_source_detection_strategies():
    # GitHub
    gh = detect_source("https://github.com/numpy/numpy")
    assert gh["source_type"] == "github"
    assert gh["strategy"] == ReadingStrategy.OFFICIAL_API
    assert gh["metadata"]["owner"] == "numpy"
    assert gh["metadata"]["repo"] == "numpy"
    assert gh["allows_framing"] is False

    # Python Docs
    py = detect_source("https://docs.python.org/3/library/asyncio.html")
    assert py["source_type"] == "python_docs"
    assert py["strategy"] == ReadingStrategy.DOCUMENTATION_PROVIDER
    assert py["allows_framing"] is False

    # MDN
    mdn = detect_source("https://developer.mozilla.org/en-US/docs/Web/JavaScript")
    assert mdn["source_type"] == "mdn"
    assert mdn["strategy"] == ReadingStrategy.DOCUMENTATION_PROVIDER

    # FastAPI
    fastapi = detect_source("https://fastapi.tiangolo.com/tutorial/")
    assert fastapi["source_type"] == "fastapi"
    assert fastapi["strategy"] == ReadingStrategy.DOCUMENTATION_PROVIDER

    # NumPy
    np = detect_source("https://numpy.org/doc/stable/user/quickstart.html")
    assert np["source_type"] == "numpy"
    assert np["strategy"] == ReadingStrategy.DOCUMENTATION_PROVIDER

    # Stack Overflow
    so = detect_source("https://stackoverflow.com/questions/12345/how-to-do-x")
    assert so["source_type"] == "stackoverflow"
    assert so["allows_framing"] is False


def test_html_sanitization_and_code_extraction():
    dirty_html = """
    <div>
        <script>alert('xss');</script>
        <iframe src="http://evil.com"></iframe>
        <h2 onclick="malicious()">Clean Heading</h2>
        <p style="color: red;">Valid technical explanation with <a href="/docs/guide" onclick="track()">link</a>.</p>
        <div class="ad-container banner-ad"><span>Buy now</span></div>
        <pre><code class="language-python">import numpy as np\narr = np.array([1, 2, 3])</code></pre>
        <img src="/img/diagram.png" onerror="alert(2)" />
    </div>
    """
    clean_html = sanitize_html(dirty_html, base_url="https://docs.example.com/")

    # Assert scripts, iframes, and dangerous handlers removed
    assert "<script" not in clean_html
    assert "<iframe" not in clean_html
    assert "onclick" not in clean_html
    assert "onerror" not in clean_html
    assert "ad-container" not in clean_html

    # Assert content preserved
    assert "Clean Heading" in clean_html
    assert "Valid technical explanation" in clean_html
    assert "language-python" in clean_html
    assert "href=\"https://docs.example.com/docs/guide\"" in clean_html
    assert "src=\"https://docs.example.com/img/diagram.png\"" in clean_html

    # Assert code blocks extracted
    snippets = extract_code_blocks(clean_html)
    assert len(snippets) == 1
    assert snippets[0]["language"] == "python"
    assert "np.array([1, 2, 3])" in snippets[0]["code"]


def test_api_research_read_ssrf_blocked():
    # Attempt SSRF via reader endpoint
    res = client.get("/api/research/read", params={"url": "http://127.0.0.1:8000/api/health"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "restricted"
    assert data["reading_strategy"] == "external_fallback"
    assert "prohibited" in data["error_message"].lower() or "loopback" in data["error_message"].lower()


def test_api_check_frame_endpoint():
    res_gh = client.get("/api/research/check-frame", params={"url": "https://github.com/numpy/numpy"})
    assert res_gh.status_code == 200
    assert res_gh.json()["allows_framing"] is False


def test_api_research_read_empty_url():
    res = client.get("/api/research/read", params={"url": ""})
    assert res.status_code == 400


def test_api_research_read_github_mocked():
    mock_meta = {
        "full_name": "example/project",
        "description": "An example project",
        "stargazers_count": 420,
        "forks_count": 69,
        "language": "Python",
        "default_branch": "main",
        "html_url": "https://github.com/example/project"
    }
    readme_html = "<h1>Example</h1><p>Welcome to example project</p><pre><code class=\"language-python\">print('hello')</code></pre>"

    with patch("devnote.app.research.providers.github_provider.GitHubReaderProvider._fetch_repo_metadata", new_callable=AsyncMock) as mock_repo_meta, \
         patch("devnote.app.research.providers.github_provider.GitHubReaderProvider._fetch_readme", new_callable=AsyncMock) as mock_fetch_readme:
        mock_repo_meta.return_value = mock_meta
        mock_fetch_readme.return_value = (readme_html, "# Example\nprint('hello')")

        res = client.get("/api/research/read", params={"url": "https://github.com/example/project"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["reading_strategy"] == "official_api"
        assert "example/project" in data["title"]
        assert len(data["code_snippets"]) >= 1
        assert data["code_snippets"][0]["language"] == "python"
        assert "print('hello')" in data["code_snippets"][0]["code"]
        assert data["metadata"]["stars"] == 420


def test_api_research_read_caching():
    mock_meta = {
        "full_name": "example/cached",
        "description": "Cached repo",
        "default_branch": "main"
    }
    with patch("devnote.app.research.providers.github_provider.GitHubReaderProvider._fetch_repo_metadata", new_callable=AsyncMock) as mock_repo_meta, \
         patch("devnote.app.research.providers.github_provider.GitHubReaderProvider._fetch_readme", new_callable=AsyncMock) as mock_fetch_readme:
        mock_repo_meta.return_value = mock_meta
        mock_fetch_readme.return_value = ("<p>Cached content</p>", "Cached content")

        # 1st call
        res1 = client.get("/api/research/read", params={"url": "https://github.com/example/cached"})
        assert res1.status_code == 200
        assert mock_repo_meta.call_count == 1

        # 2nd call (should hit cache)
        res2 = client.get("/api/research/read", params={"url": "https://github.com/example/cached"})
        assert res2.status_code == 200
        assert res2.json()["metadata"].get("cached") is True
        assert mock_repo_meta.call_count == 1
