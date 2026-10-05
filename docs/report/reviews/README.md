# Review record

The files in this folder record internal review passes of the Experiment 7
closeout documents and the technical report.

**None of these passes was external human peer review.** Each one was carried
out by an AI system (Anthropic's Claude), working as subagents of the same
AI-assisted session that drafted the documents, at the request of the human
author, Ian Gregory. None of these reviewers is independent of the author's
project or tooling.

Some file names and headings use journal vocabulary such as "referee report",
"handling editor's adjudication" and "independent referee". Those words
describe the role each AI pass was asked to play. They do not mean an
unaffiliated human reviewed the work.

The historical files are kept unchanged. Downstream documents describe these
passes as AI-assisted adversarial manuscript reviews or internal audits.

| pass | files | performed by | independent of the human author? | generative AI? | read-only or edited? | commit reviewed | disposition |
|---|---|---|---|---|---|---|---|
| Round 0, review 1 | `ROUND0_DOC_REVIEW_PROPOSALS.md` | AI subagent (Claude), adversarial documentation audit | No (commissioned by the author; same AI system that drafted) | Yes | Read-only | `5dc3f408` | 37 proposals and errata E7–E13 |
| Round 0, review 2 | `ROUND0_DOC_REVIEW_ADJUDICATION.md` | AI subagent (Claude), adjudication of review 1 | No | Yes | Read-only | `5dc3f408` | 9 accepted, 28 accepted with modification. Implemented by a third AI subagent that edited files, in `4cf3dc30` and `9527f540` |
| Round 1 | `ROUND1_REFEREE_REPORT.md`, `ROUND1_ADJUDICATION.md` | AI subagents (Claude): an adversarial manuscript review pass, then an AI adjudication pass | No | Yes | Review and adjudication read-only; an AI implementation pass edited files | `189dfa64` | Major revision requested. Implemented in `1c866d54`, `6366b000`, `cc3bb236` and `f0db4729` |
| Round 2 | `ROUND2_REFEREE_REPORT.md`, `ROUND2_ADJUDICATION.md` | AI subagent (Claude) review pass. The adjudication and edits were made by the main AI-assisted session | No | Yes | Review read-only; adjudication and implementation edited files | `f0db4729` | Minor revision requested: 6 important and 17 minor comments. All accepted except figures, which were deferred and later produced in `cd03af9c`. Implemented in `c9e28600` |
| Round 3 check | appended to `ROUND2_ADJUDICATION.md` | AI subagent (Claude), read-only internal audit of the round-2 edits | No | Yes | Read-only | uncommitted working tree on `f0db4729`, committed as `c9e28600` | 3 important and 3 minor issues, all fixed in `c9e28600` |

The human author directed each pass and is responsible for the content that
resulted. No external human review has taken place as of `c90d8b18`.
