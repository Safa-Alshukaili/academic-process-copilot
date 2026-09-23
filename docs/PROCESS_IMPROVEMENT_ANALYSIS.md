# Process Improvement Analysis

Three typical university administrative processes, reviewed for where AI
and digital tools reduce repetitive work without removing human decisions
from the parts that need them.

## 1. OJT Registration

**Current (manual) pattern**: student is often unsure whether they meet the
credit-hour threshold and asks an advisor directly; advisor manually checks
transcript and repeats the same eligibility explanation to many students
each semester.

**Where AI/digital tools help**: a structured-prompting agent answers the
eligibility question instantly from verified data (this project's Demo 1),
freeing advisor time for the parts that actually need judgment — approving
a specific host organization, reviewing a non-standard case.

**What should stay human**: host-organization approval and supervisor
sign-off — both require judgment about placement quality, not just
information lookup.

## 2. Course Withdrawal

**Current (manual) pattern**: students frequently ask "is it too late to
withdraw?" — a date lookup, not a judgment call — before the actual
advisor-approval step.

**Where AI/digital tools help**: the same agent pattern answers deadline
questions immediately; the workflow could also proactively flag a student
close to a deadline (a scheduled digital-tools improvement, not built here).

**What should stay human**: advisor approval of the withdrawal itself,
since it can affect degree progress.

## 3. Graduation Clearance

**Current (manual) pattern**: students submit a clearance form without
knowing in advance whether they have outstanding fees or missing courses,
causing avoidable back-and-forth with the Registrar.

**Where AI/digital tools help**: a pre-check agent (extending Demo 1's
pattern to combine financial + academic status) could tell a student what's
missing *before* they submit the form, cutting resubmissions.

**What should stay human**: the final clearance decision, and any
fee-waiver or exception request.

## Pattern across all three

The common failure mode is staff time spent answering repetitive,
information-lookup questions that a verified database + structured-prompt
agent can answer directly and consistently — while every step that involves
judgment, exceptions, or approval stays with a named human. That split is
the design principle behind this whole project, not just these three cases.
