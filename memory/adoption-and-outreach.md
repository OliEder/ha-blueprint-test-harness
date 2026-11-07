---
name: adoption-and-outreach
description: What was found on 2026-11-07 about making the project known, the two Home Assistant feature requests it answers, and the rules for posting.
metadata:
  type: research
  applies_to: [README.md, RELEASING.md, status/open.md, VISION.md]
  checked: 2026-11-07
---

**State when checked.** The repository had 0 stars, 0 forks, 0 issues and 0 page views in the 14 days before (GitHub traffic API), no release, no tag and no PyPI package (the name returned HTTP 404). Nobody can install it with `pip` yet, so spreading the word comes after the first release.

**Two open feature requests on the Home Assistant community forum ask for this.**
- [Test Suite for Blueprints](https://community.home-assistant.io/t/test-suite-for-blueprints/683482), category Feature Requests, opened 2024-02-02, last reply 2026-01-16, 3 replies and 4 votes. It asks for a command-line tool that feeds simulated inputs into a blueprint, or a `tests` section in the blueprint. A reply points to Home Assistant's own `test_blueprint.py` and to another test suite for blueprints (`getaivi/ha-blueprints`, not examined).
- [Automations: Testing Framework](https://community.home-assistant.io/t/automations-testing-framework/688889), category Feature Requests, opened 2024-02-12, last reply 2025-11-10, 2 votes and 3 replies. It asks for YAML tests with mocked actions.

Other work seen: `ChuckBuilds/ha-blueprints` (headless Home Assistant per project), a pull request adding a test per blueprint to a blueprint collection (`AboveColin/HA-Jev` #53), `ha-testcontainer` (whole instance in a container). None examined in detail; see [[prior-art-no-general-tool]].

**Rules.**
- Post nothing, open nothing and ask nobody for anything without the maintainer's go-ahead. Answering a feature request is on topic, but only once the package can be installed, and with a short, factual reply: what it does, what it does not do, how to try it.
- The forum's rules on self-promotion and the conditions of the `awesome-home-assistant` list were **not found**. Read them before posting or proposing.
- No mass posts, no star exchanges, nothing off topic.

**Open.** How many blueprint authors want automated tests is unknown; the audience may be small. The usage steps were missing from the README until 0.1.0 was prepared: a stranger failed the first test. Always try a release by installing it into a fresh environment (recipe in `status/practical.md`).

**Why:** the plan to become known started in a chat and would otherwise be lost.

**How to apply:** read before posting, before writing release notes, or when asked "who is this for". Re-check the threads and the numbers before relying on them.
