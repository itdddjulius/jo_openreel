# OPENREELpy - TESTS

Version 1.1.0 adds a deployment regression test that starts a fresh Python process from the project root and imports `app`, matching the critical Vercel cold-start step. A second test verifies the HTML, CSS, JavaScript and documentation assets needed after import. Together, these tests catch the two common causes of `FUNCTION_INVOCATION_FAILED`: an import exception and an incomplete deployment bundle.

Before deployment run `python -m unittest discover -s tests -v`. Then start `uvicorn app:app --port 8080` and request `/api/health`. The response must report status `ok`, version `1.1.0`, runtime `FastAPI` and Python `3.12`. On Vercel, repeat the health request against the deployment URL and inspect Function Logs if it is not HTTP 200.

## Page 1 - Startup and Static Resources

Run `uvicorn app:app --port 8080`. Verify `/`, `/static/app.css`, `/static/app.js`, `/api/health`, `/api/docs` and all Markdown/PDF routes. Confirm no Python import, ASGI or browser-console error. Verify fixed header/footer and independently scrolling main content.

Confirm startup without an account or API key. Validate root `app.py` auto-detection, the Python 3.12 pin, minimal `vercel.json`, requirements installation, Docker behaviour and ZIP integrity. After Vercel import, confirm FastAPI detection rather than `FUNCTION_INVOCATION_FAILED`.

<!-- PAGE BREAK -->

## Page 2 - Search Compiler Tests

Search “silent comedy films”. Confirm the dork contains `site:archive.org/details`, quoted terms, video file types and open-rights wording. Edit the dork and verify OPEN GOOGLE follows the latest value. Test COPY and SAVE SEARCH.

Test empty input, 301 characters and piracy indicators such as torrent, DRM bypass and leaked copy. Each must display a notice without calling the media index. Test angle brackets and quotes; generated output must remain safe and balanced.

<!-- PAGE BREAK -->

## Page 3 - Results and Playback Tests

With a live network, verify an Archive search returns result cards. Open DETAILS and confirm the correct identifier. Select PLAY and verify metadata is requested, private files are excluded and a supported file is selected.

Exercise native video controls plus Play/Pause, seek backward, seek forward, speed and Fullscreen. Close during playback and confirm pause. Force a bad media URL and confirm a visible error with an intact source link.

Simulate API failure. The results modal must retain the editable dork and external Google option. Simulate metadata with no video and confirm VIDEO UNAVAILABLE.

<!-- PAGE BREAK -->

## Page 4 - Persistence and Modal Tests

Save a result, reopen WATCHLIST and play it. Remove and re-add items through controls. Perform searches and playback, then inspect newest-first HISTORY. Reload and confirm persistence. Corrupt stored JSON and verify safe recovery.

Open all four manuals from header and footer. Confirm scrolling, Escape, X and backdrop closure. Open CONTACT and verify the exact required URL, sandbox and fallback. Confirm every video opens inside the modal rather than replacing the application page.

Test CLEAR, cancel once, then confirm. OPENREELpy keys should disappear while an unrelated localStorage test key remains.

<!-- PAGE BREAK -->

## Page 5 - Accessibility, Responsive and Security Tests

Navigate using keyboard only. Verify visible focus, form labels, named icon buttons, dialog titles and accessible native video controls. Test at approximately 390, 768, 1024 and 1440 pixels and at 200% zoom.

Inject HTML-like search text and metadata values; they must display as text. Verify encoded external URLs, `noopener`, `noreferrer`, CONTACT sandbox and absence of credentials. Confirm blocked piracy wording does not initiate external requests.

Release passes when JavaScript syntax, deterministic dork output, safety cases, local startup, five-page documentation, PDF rendering and ZIP integrity succeed.
