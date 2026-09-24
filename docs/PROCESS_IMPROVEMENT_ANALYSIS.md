# Process Improvement Analysis

Three real UTAS academic processes (Academic Regulation, Decision
612/2022), reviewed for where AI and digital tools reduce repetitive work
without removing human decisions from the parts that need them.

## 1. Academic Probation (Articles 46-49)

**Current (manual) pattern**: a student whose GPA drops below 2.00 often
doesn't know exactly how many credit hours they're now allowed to
register (Article 46 caps this at 9-12, or 6-12 part-time), or how many
semesters they have left to recover (a maximum of 3 consecutive semesters
per Article 47) — this is frequently the same lookup, repeated by an
advisor for every student who lands on probation each semester.

**Where AI/digital tools help**: a structured-prompting agent answers the
credit-cap and recovery-deadline questions instantly and consistently from
the regulation text (this project's `/ask` endpoint, tested against this
exact question — see the main README). That frees advisor time for the
part that actually needs judgment: building the individual remedial course
plan Article 46 requires.

**What should stay human**: the remedial plan itself, and the final
withdrawal decision if the student doesn't recover in time — both require
judgment about a specific student's situation, not just a rule lookup.

## 2. Course Withdrawal (Article 38)

**Current (manual) pattern**: students frequently ask "is it too late to
withdraw?" (the Article 38 deadline is the end of week 8) and "how many
withdrawals do I have left?" (a running count against the Article 38.1-38.2
limits) — both are lookups against a rule and the student's own history,
not judgment calls, but they still route through an advisor today.

**Where AI/digital tools help**: the same agent pattern answers the
deadline question immediately and consistently; a fuller version would
also check the student's withdrawal count against their transcript
automatically (this project checks the rule, not yet the student's
individual count — see "What a real deployment would add" in the
automation README).

**What should stay human**: instructor and advisor approval of the
withdrawal itself (both required by Article 38), since it can affect
degree progress.

## 3. Study Deferral (Articles 39-40)

**Current (manual) pattern**: students often submit deferral requests
without knowing the hard deadline (week 10, per Article 40) or that
subsistence allowances stop during deferral (Article 39) — both facts a
student would want *before* deciding to defer, not after.

**Where AI/digital tools help**: an agent surfaces these facts immediately
when asked, and the required advising session (Article 40) becomes a more
informed conversation instead of the point where the student first learns
the deadline and stipend rules.

**What should stay human**: the advising session itself, and any decision
on the exceptional 3rd deferral semester Article 39 allows — both require
judgment about the student's specific circumstances.

## Pattern across all three

The common failure mode is staff time spent answering repetitive,
regulation-lookup questions that a verified, article-cited database and a
structured-prompt agent can answer directly and consistently — while every
step that involves judgment, exceptions, or approval stays with a named
human. That split is the design principle behind this whole project, not
just these three cases.
