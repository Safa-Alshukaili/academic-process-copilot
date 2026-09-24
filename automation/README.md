# No-Code Automation Layer (n8n)

Two real, importable **n8n** workflows — not descriptions of one. Both
orchestrate the Academic Process Copilot API (`src/api.py`) with zero
application code: every step is a configured node.

**Why this exists separately from the Python agent**: the job requirement
this addresses — *"AI agents, workflow automation, or no-code/low-code
platforms"* — is a distinct skill from writing the agent itself. These
files are the evidence for the no-code half specifically.

## The two workflows, and why there are two

| File | Trigger | Purpose |
|---|---|---|
| `apc-student-inquiry.n8n.json` | Webhook (one call per student question) | Answers the question, or escalates instead of guessing |
| `apc-daily-digest.n8n.json` | Schedule (once a day) | Batches unanswered questions into one summary instead of one alert per failure |

**The trade-off that led to two files instead of one:** wiring a real
email/Slack send directly into the first workflow's "Notify Staff" node
means one notification per failed question — noisy if the same gap gets
asked several times in a day, and easy to start ignoring. The second
workflow calls `GET /admin/unanswered` (already grouped by question, most-
asked first) once a day and only sends anything if there's something new
to report. That's the recommended path; the first workflow's "Notify
Staff" node is left as a No-Op on purpose, with a note explaining why,
rather than wired to send per-question by default.

## Workflow 1: student inquiry

```
Webhook (receives a question)
   → HTTP Request (calls POST /ask on the Academic Process Copilot API)
   → IF: did the answer pass QA?
        ├─ Yes → Respond to the caller with the answer
        └─ No  → Notify Staff (No-Op, see trade-off above) → Respond "escalated"
```

If the agent can't ground an answer in verified data, this workflow does
**not** silently return a bad answer — it escalates instead.

## Workflow 2: scheduled gap digest

```
Schedule (default: every 2 days at 8am — adjustable)
   → HTTP Request (calls GET /admin/unanswered)
   → IF: count > 0?
        ├─ Yes → Send Digest (placeholder — one email/Slack message listing all gaps)
        └─ No  → Nothing To Report (silent — no "zero gaps" email every check)
```

**Changing the interval**: the Schedule Trigger node ("Every Day at 8am")
defaults to every 2 days. To change it in n8n's UI: open that node →
under the interval row, set "Days Between Triggers" to 1 (daily) or
whatever cadence you want, and set the hour/minute. No JSON editing
needed once it's imported.

**This only fires while n8n is actually running.** A Schedule Trigger
node does nothing unless the workflow is toggled **Active** (top-right
switch in the n8n editor, not the "Execute Workflow" button used for
one-off tests) *and* the n8n process itself is running at the scheduled
time. Running `npx n8n` in a terminal only counts while that terminal
and your laptop are on — for a check that actually happens unattended
every 2 days regardless of whether your laptop is open, n8n needs to run
somewhere persistent: n8n Cloud (hosted, has a free tier), or a small
always-on server/Docker container. This is a real gap between "the
workflow is correctly designed" and "it is actually running for you
right now" — worth being upfront about in an interview if asked.

## Honest status

Both JSON files were built by hand to match n8n's workflow schema.
`apc-student-inquiry.n8n.json` **has been imported and executed in a real
n8n instance** and confirmed working end to end (both the answered and
escalated paths). `apc-daily-digest.n8n.json` has **not** been executed
live yet — it follows the same node patterns that already worked in the
first file, but import and test it yourself before treating it as proven,
the same way the first one was tested here.

## How to run workflow 1 yourself

1. Install n8n: `npx n8n` (or `npm install -g n8n`, or Docker — see
   [n8n's docs](https://docs.n8n.io/hosting/)). It opens at
   `http://localhost:5678`.
2. In n8n: **Workflows → Import from File** → select
   `apc-student-inquiry.n8n.json`.
3. In a separate terminal, start the API this workflow calls:
   `python -m uvicorn src.api:app --reload` (from the project root).
   If the HTTP Request node can't connect even though the API is clearly
   running, change its URL from `http://localhost:8000/...` to
   `http://127.0.0.1:8000/...` — Node.js sometimes resolves `localhost` to
   `::1` (IPv6) instead of the address the API is actually listening on.
4. Click **Execute Workflow** — this activates a one-time *test* webhook
   at `/webhook-test/student-inquiry`, different from the permanent
   `/webhook/student-inquiry` path a **Published/Active** workflow uses.
   Click Execute Workflow again before each test call; it only listens
   for one request at a time.
5. Send a test request (PowerShell — `curl` on Windows is aliased to a
   different command and will error on `-H`):
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5678/webhook-test/student-inquiry" -Method POST -ContentType "application/json" -Body '{"question": "What GPA puts me on academic probation?"}'
   ```
   (macOS/Linux: `curl -X POST http://localhost:5678/webhook-test/student-inquiry -H "Content-Type: application/json" -d '{"question": "What GPA puts me on academic probation?"}'`)

   Expected: `status: answered` with the answer.
6. Click Execute Workflow again, then try a question the database can't
   answer (e.g. `"what is the weather today"`) — expect `status: escalated`.
7. Screenshot the n8n canvas mid-execution (green checkmarks on each node,
   both the answered and escalated runs) — that screenshot is stronger
   portfolio evidence than the JSON file itself.

## How to run workflow 2 yourself

Same install as above. Import `apc-daily-digest.n8n.json`, make sure the
API is running, click **Execute Workflow** to run it once immediately
(rather than waiting for 8am) and confirm it reaches `Send Digest` when
there are unanswered questions logged, and `Nothing To Report` when there
aren't.

## Wiring up real notifications

For either workflow: in n8n, delete the No-Op placeholder node and drag in
a **Gmail** node (or Outlook, or Slack) in its place, connected the same
way. Add your own credentials (n8n → Credentials → New — stored locally,
nothing shared with this repo). For the digest workflow specifically, the
message body should list `$json.questions` (each has `question`,
`times_asked`, `last_asked`) rather than a single question. Save, then
re-run the test above to confirm you actually receive it.

## Closing the loop

Once you know what's missing (from a digest email or `GET
/admin/unanswered` directly), run `src/add_faq.py` to publish the verified
answer — **not** `data/seed.py`, which wipes the whole database including
audit history. See "Closing the loop" in `docs/QA_PROCESS.md`.

## What a real deployment would add

- Replace both placeholder notification nodes with real Gmail/Outlook/Slack
  nodes using real credentials.
- Point the HTTP Request nodes at a deployed API URL instead of `localhost`.
- A lightweight admin UI over `add_faq.py` so non-technical staff can
  close gaps without touching the command line.
