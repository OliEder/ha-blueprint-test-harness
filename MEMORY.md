# Memory

An index of facts and decisions that the code and the git history do not record. **Read this index, then open only the entries that match your task.** Each entry is a short file in [`memory/`](memory/) with a one-line description, a type (decision, fact, pitfall, observation, research), the files it applies to and the date it was last checked.

Keep it current. Fix or delete an entry as soon as it is wrong, and check a claim that names a file, command or number before relying on it. A new fact is a new file plus one line here; `tests/test_memory.py` checks that both agree and that the files an entry names still exist. Split an entry that grows past 40 lines. An agent's own memory lives outside the repository; this is the project's record.

## Working on the environment (`env.py`)

- [Why `settle()` and not `async_block_till_done()`](memory/settle-instead-of-block-till-done.md): read before touching waits, timers or any code that makes a test wait.

## Mutation tool and survivors

- [What killed, survived, invalid and error mean](memory/mutation-outcomes-killed-invalid.md): read before changing how a run is judged or when the invalid count surprises you.
- [Equivalent mutants seen so far](memory/equivalent-mutants.md): read when a survivor might not be a test gap; add new ones here.
- [How the reference automations are made and judged](memory/reference-set-rules.md): read before adding a fixture or changing a mutation floor in CI.
- [YAML round-trip quirks](memory/yaml-round-trip-quirks.md): read when the control run fails or the written YAML looks different from the original.

## Writing tests for a blueprint

- [`last_reported` is a weak age signal](memory/last-reported-weak-age-signal.md): read before writing or reviewing an age check or recommending a limit.


## Releases

- [What the first release taught](memory/first-release-lessons.md): read before tagging, before changing the release workflow, or when a release looks wrong.

## Scope, naming and structure

- [Name and package](memory/name-and-package.md): read before renaming, publishing, or when the name is questioned.
- [Scope and why version handling comes early](memory/scope-and-version-compatibility.md): read before adding a new kind of thing to test, a new direct Home Assistant import, or before renaming.
- [Where the longer-term thinking lives](memory/where-longer-term-thinking-lives.md): read before adding an idea or a roadmap item.
- [Making the project known](memory/adoption-and-outreach.md): read before posting anywhere, writing release notes or when asked who this is for.
- [Prior art: no general tool found](memory/prior-art-no-general-tool.md): read only if the claim "nothing like this exists" matters for a decision.
