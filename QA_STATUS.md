# TruthLayer QA status

## Verified in this build

- Python code syntax compiled without errors.
- Offline unit and controller tests passed: 13/13.
- A real one-page sample PDF was generated and rendered for layout inspection.
- The Gradio web app was started successfully on localhost and returned HTTP 200.
- The Gradio client discovered both app endpoints and performed an actual upload/API call with the sample PDF.
- The no-key state displayed a clear setup message instead of crashing.
- Controller mock integration produced the complete UI HTML and real PDF/CSV/JSON export files.
- PDF report hyperlinks are valid and read back correctly.

## Not verified / requires deployment account

- No live Gemini Google Search-grounded call has been made: this environment has no API credentials.
- No real public hosting URL or GitHub repository has been created: the owner's accounts/connections are required.
- No 30-second live screen recording has been made: record this after the hosted app passes the live test.
- The Docker image was not built in this execution environment. Render will build it on deployment.

## Acceptance test after deployment

1. Visit the public Render URL, load sample_trap.pdf, and request eight claims.
2. Check that an obviously false claim has a contradiction, concrete corrected fact, and clickable source.
3. Verify source link quality, not merely that a link exists.
4. Upload a different PDF, verify its original quotes and page numbers, and test all download formats.
5. Ensure public users can test without entering an API key (server must have GEMINI_API_KEY configured).
6. Capture the 30-second demo video, and insert its link plus app/repo links into SUBMISSION_TEMPLATE.md.
