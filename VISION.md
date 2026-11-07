# Vision

This document is for thinking that is not ready to become work. [`ROADMAP.md`](ROADMAP.md) lists what is planned and in which order; this file collects the larger picture, the open questions and ideas, including ideas from people who use the project. Nothing here is a promise. An idea becomes work when it is accepted into the roadmap with a milestone.

Status: first draft, 2026-11-07. Everything under "Candidate building blocks" is a candidate, not a decision.

## The picture

Home Assistant is extended by many people in many ways: blueprints, automations, scripts, helpers, integrations. Most of that is written without a repeatable way to check it, and more and more of it is written with the help of AI agents. An agent that edits a blueprint can look correct and be wrong, and it can be confident about both.

The long-term aim is to make that safe and boring:

1. **A complete testing harness** for what people build for Home Assistant (the direction in the roadmap): deterministic, no real device, results a machine can read, and tests that are themselves measured (mutation testing), so that "green" means something.
2. **An agent harness on top of it:** the environment in which an AI agent works on Home Assistant code, with the specifics of Home Assistant built in. Where a standard coding harness knows files and shells, this one would also know blueprints, versions, services, the ways a Home Assistant change goes wrong, and when to stop.

The first is under construction. The second is only defined here, and only as far as the evidence goes.

## Principles

- **A person is accountable.** An agent proposes; a person decides what is published, merged or written to a real instance.
- **Claims come with proof.** Report what ran, say what did not run. A claim that can be checked by a tool is checked by the tool, not by reading.
- **Safe by default.** Read-only toward real instances, isolated execution of code from others, writes only with approval and a way back.
- **Agent-agnostic.** Plain files and a command line. It has to work with any coding agent, and without one.
- **Small context.** An agent should be told where to look, not given everything. A project map beats a long document.
- **Moves with Home Assistant.** Home Assistant changes monthly. Anything that encodes its behaviour carries the version it was checked on.

## What went wrong when this project was built with an agent

These are real, from the session that built the first version (2026-11-07). They are the evidence base: a building block belongs in the harness if it would have prevented one of these.

| What happened | Why it matters | Which building block would have helped |
| --- | --- | --- |
| A test command hung because `async_block_till_done()` never returns while a script waits for a trigger. | An unbounded command stalls an agent for minutes and gives no signal. | Time limits on every run by default; a hint that names the cause of a known hang |
| A history query written as `10m` was read as ten months and hit a safety limit. | Time units differ between tools; the agent guessed. | Tool descriptions with examples; a check that turns a surprising argument into a question |
| A count in a summary was wrong (6 of 8 instead of 5 of 8). | An agent states numbers from memory of what it ran. | A machine-readable report that the summary is built from |
| The mutation tool swallowed `--timeout` into the test command; the first big run never started. | The tool reported a clean exit while nothing had run. | A run that checks it did what it was asked to; a test for the command line |
| A first test set killed 16 of 18 mutants; the two survivors showed a gap no one had seen while reading the tests. | Reading tests does not find missing tests. | Mutation score as a gate before "done" |
| `AGENTS.md` pointed at a file outside the repository, which could be read as a loop. | Instructions that cannot be opened by everyone mislead. | A check that links in agent instructions resolve inside the repository |
| An external test suite could not be run at first because the environment treats unknown code as unsafe. | The right default; but the next step needed a clear, safe path. | A documented way to run untrusted tests in isolation |
| Shell commands behaved differently locally than in CI (BSD and GNU tools, different shells). | Local and CI environments differ. | Commands run the way CI runs them |

## Candidate building blocks

Each is a question, not an answer. Where something similar already exists it is named.

- **Knowledge of Home Assistant that is version-aware.** Best practices for blueprints, automations and templates, tied to the version they were checked on. Prior art: the best-practices skill that `ha-mcp` tells agents to read before changing configuration.
- **Verification gates.** What "done" means for a change: tests pass, mutation score at or above a threshold, no new survivors left unexplained, no invalid mutants, the same on the supported versions.
- **Safe execution.** A sandbox for code from others; a read-only default for real instances; an approval step and a rollback for writes (a configuration hash or a backup).
- **Task recipes.** Short, tested procedures: write tests for a blueprint, triage mutation survivors, move to a new Home Assistant version, review a blueprint from someone else, report a finding in another project's repository.
- **Tools an agent can call.** Run a scenario, list survivors with their mutants, render a template against a read-only instance, compare behaviour between two Home Assistant versions. Whether these are an MCP server, a command line, or both is open.
- **Memory and project map conventions.** A status file with a map by task, a record of decisions, a log of progress; the conventions already used in this repository.
- **Contribution hygiene for other people's repositories.** One topic per change, follow the existing structure, tests stay in your own fork unless the maintainer asks, say plainly where AI was used, post nothing without a person's go-ahead.

## Open questions

- **Where does it live?** In this repository, in a repository of its own that calls this one, or as part of a larger project? Until decided, only this document lives here and no code depends on it.
- **Which agents?** Written for any, tested with at least two? Or tuned to one?
- **How much is enforced by tools and how much by text?** Rules in a file are followed when the agent reads them; a check in a tool is followed always. Which rules deserve a tool?
- **How is the harness itself tested?** Agents are not deterministic. What would count as evidence that a building block works?
- **What is out of scope?** Front-end work (custom cards, dashboards) needs a browser. Device firmware is out of reach.
- **How does it stay current** when Home Assistant ships a new version every month?

## Ideas from the community

The project is not public yet, so there is no public place to send ideas. When it is, this section will name one (a GitHub Discussions category "Ideas" is the likely choice) and link it here. Until then ideas are added to the log below by the maintainer.

A good idea says:

1. **The problem.** What went wrong or was hard, for whom, how often.
2. **What would help.** The smallest thing that would change it.
3. **How we would know.** A check that tells us it worked.
4. **The risk.** What it could break or whom it could mislead.

Please leave real entity names, hostnames, tokens and other details of your own installation out.

### Ideas log

| # | Idea | Source | Status |
| --- | --- | --- | --- |
| 1 | Machine-readable report (JSON) from the test and mutation runs, so summaries are built from data | session 2026-11-07 | candidate, see M9 in the roadmap |
| 2 | Default time limit on every run, with a named hint for known hangs | session 2026-11-07 | candidate |
| 3 | Version-aware best-practice notes for blueprints | session 2026-11-07 | candidate |
| 4 | Check that links in agent instructions resolve inside the repository | session 2026-11-07 | candidate |
| 5 | A documented, isolated way to run tests and blueprints from other people | session 2026-11-07 | candidate |

Status values: candidate (written down, not discussed), discussed, accepted (now in the roadmap), parked (good, not now), declined (with the reason).

## How this document is kept

Add to it when an agent or a person hits a problem the harness could prevent. Say what happened, not what you assume. When an idea is accepted, move it to the roadmap and leave a one-line note in the ideas log. Date what you add, and keep the table of observations honest: remove an entry that turns out to be wrong.
