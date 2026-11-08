"""Mutation testing for blueprints and automations: break the YAML in small ways and see whether the tests notice.

    python -m ha_blueprint_test_harness.mutate path/to/blueprint.yaml -- python -m pytest -q -x

The file may also hold an automation written directly (as in ``automations.yaml``); for a list use ``--pick``.

Each mutant changes one thing (a comparison, a condition, a ``from:``, a delay, ...). The test command
runs once per mutant; the harness swaps the mutant in for the original blueprint (see
``ha_blueprint_test_harness.env``), so the tests need no changes. A mutant that survives is either a gap in the tests or
an equivalent change; each survivor needs a human look.

Sites are found structurally on the parsed YAML, with a few text operators inside Jinja templates. Not
covered: numbers inside templates, ``choose`` branch bodies beyond dropping items, and anything in the
``blueprint:`` header except input defaults.

How to read this file, top to bottom:
1. YAML round trip: read a blueprint into Python and write it back, keeping Home Assistant's ``!input`` tags.
2. Mutations: walk through the parsed blueprint and list every place that can be broken (``find_mutants``).
3. Runner: for each mutant write a file, run the tests, and judge the outcome (``run_mutation``, ``main``).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import dataclasses
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable, Iterator
from typing import Any

import yaml

from . import _yaml

# --------------------------------------------------------------------------------------- YAML round trip


# Home Assistant writes inputs as ``key: !input name``. Plain YAML does not know "!input", so we keep it as
# a small object (tag + value) that can be read, copied and written back unchanged.
class Tagged:
    """A scalar with a local YAML tag, such as ``!input name``."""

    # tag = the part after the "!", e.g. "input"; value = the text that follows, e.g. "motion_entity".
    def __init__(self, tag: str, value: str) -> None:
        self.tag, self.value = tag, value

    # Two tagged values are equal when tag and value are equal (needed to compare documents in tests).
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Tagged) and (self.tag, self.value) == (other.tag, other.value)

    # Shown the way it is written in the YAML, e.g. "!input motion_entity".
    def __repr__(self) -> str:
        return f"!{self.tag} {self.value}"


# A YAML reader that understands our extra tags (see _construct_tagged).
class _Loader(yaml.SafeLoader):
    pass


# Called by the YAML reader for every ``!something value``: wraps it in a Tagged object.
# Only single values are supported (all that blueprints use); anything else is rejected with a clear error.
def _construct_tagged(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> Tagged:
    if not isinstance(node, yaml.ScalarNode):
        raise yaml.constructor.ConstructorError(None, None, f"only scalar tags are supported: !{suffix}", node.start_mark)
    return Tagged(suffix, loader.construct_scalar(node))


_Loader.add_multi_constructor("!", _construct_tagged)


# A YAML writer that can write Tagged objects back as ``!input name``.
class _Dumper(yaml.SafeDumper):
    # Never write YAML anchors/aliases (&a / *a); every value is written out in full, which is easier to diff.
    def ignore_aliases(self, data: Any) -> bool:
        return True


_Dumper.add_representer(Tagged, lambda dumper, tagged: dumper.represent_scalar(f"!{tagged.tag}", tagged.value))


# The largest file the tool reads. What aliases may expand to is limited too (see ``_yaml.py``).
_MAX_BYTES = 1_000_000


# Reads blueprint text into Python lists, dicts and Tagged objects. Raises ValueError for input that is too large or
# whose aliases expand too far. Shared nodes are made independent (the text is dumped in full and read again), so that a
# mutation changes one place and not every place the same alias points to.
def load(text: str) -> Any:
    if len(text.encode("utf-8")) > _MAX_BYTES:
        raise ValueError(f"the file is too large for the mutation tool (more than {_MAX_BYTES} bytes)")
    _yaml.check_expansion(text)
    document = yaml.load(text, Loader=_Loader)
    if _yaml.has_aliases(text):
        document = yaml.load(dump(document), Loader=_Loader)
    return document


# Writes such a structure back to YAML text, keeping the original key order.
def dump(document: Any) -> str:
    return yaml.dump(document, Dumper=_Dumper, sort_keys=False, width=1000, allow_unicode=True)


# ------------------------------------------------------------------------------------------- mutations


# One planned change to the blueprint. ``apply`` makes the change on a copy of the parsed blueprint.
@dataclasses.dataclass(frozen=True)
class Mutant:
    id: str  # "M001", "M002", ...
    operator: str  # the kind of change, e.g. "drop_key" or "template"
    description: str  # human-readable: where and what, e.g. "triggers.from: remove 'from: off'"
    apply: Callable[[Any], None]

    # Returns a copy of the document with this one change applied. The original stays untouched.
    def mutated(self, document: Any) -> Any:
        mutated = copy.deepcopy(document)
        self.apply(mutated)
        return mutated

    # Returns the blueprint text with this one change applied. The original document stays untouched.
    def build(self, document: Any) -> str:
        return dump(self.mutated(document))


# A position inside the parsed blueprint, as the keys and indexes to follow, e.g. ("actions", 1, "delay").
Path = tuple[Any, ...]

# Lists whose items are steps of the automation; dropping one item at a time shows whether the tests need it.
_ACTION_LISTS = {"triggers", "conditions", "actions", "sequence", "then", "else", "choose"}
# Keys of a trigger or condition that narrow when it applies; removing one makes it fire more often.
_DROPPABLE = ("from", "to", "for", "above", "below", "after", "before", "after_offset", "before_offset")
# Services with a clear opposite; swapping them turns "on" into "off" and the other way round.
_ACTION_SWAPS = {"turn_on": "turn_off", "turn_off": "turn_on", "lock": "unlock", "unlock": "lock"}
# What to replace each automation mode with.
_MODE_SWAP = {"restart": "single", "single": "restart", "queued": "single", "parallel": "single"}
# Comparison operators and their near neighbours (the off-by-one family and the equality pair).
_COMPARISON_SWAP = {"<=": "<", "<": "<=", ">=": ">", ">": ">=", "==": "!=", "!=": "=="}
# Patterns that find these things inside a Jinja template. Comparisons and "and"/"or" must be surrounded by
# spaces so that HTML like "<b>" in a message is not mistaken for a comparison.
_COMPARISON = re.compile(r"(?<=\s)(<=|>=|==|!=|<|>)(?=\s)")
_LOGIC = re.compile(r"(?<=\s)(and|or)(?=\s)")
_NOT = re.compile(r"(?<![\w.])not\s+")
_BOOL_WORD = re.compile(r"\b(true|false)\b")


# Follows a path into the parsed blueprint and returns what is there.
def _get(root: Any, path: Path) -> Any:
    for step in path:
        root = root[step]
    return root


# True for numbers; True/False count as booleans here, not as 1/0.
def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# Turns a path into readable text: ("actions", 1, "delay") becomes "actions[1].delay".
def _label(path: Path) -> str:
    out = ""
    for step in path:
        out += f"[{step}]" if isinstance(step, int) else (f".{step}" if out else str(step))
    return out or "<root>"


# A short one-line version of a value for the description (whitespace squeezed, cut at 60 characters).
def _preview(value: Any) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= 60 else text[:57] + "..."


# Finds every single change that can be made inside one Jinja template string: flip one comparison,
# swap one and/or, remove one "not", flip one true/false. Yields (description, changed text) pairs.
def _template_variants(text: str) -> Iterator[tuple[str, str]]:
    """Yield (description, mutated text) for each single change inside one Jinja string."""
    for match in _COMPARISON.finditer(text):
        swapped = _COMPARISON_SWAP[match.group(1)]
        yield f"'{match.group(1)}' -> '{swapped}'", text[: match.start(1)] + swapped + text[match.end(1):]
    for match in _LOGIC.finditer(text):
        swapped = "or" if match.group(1) == "and" else "and"
        yield f"'{match.group(1)}' -> '{swapped}'", text[: match.start(1)] + swapped + text[match.end(1):]
    for match in _NOT.finditer(text):
        yield "remove 'not'", text[: match.start()] + text[match.end():]
    for match in _BOOL_WORD.finditer(text):
        swapped = "false" if match.group(1) == "true" else "true"
        yield f"'{match.group(1)}' -> '{swapped}'", text[: match.start()] + swapped + text[match.end():]


# Walks through the whole parsed blueprint and yields every place that can be changed, as
# (operator, description, path, apply). The "blueprint:" header is left alone, except for input defaults.
def _walk(node: Any, path: Path = ()) -> Iterator[tuple[str, str, Path, Callable[[Any], None]]]:
    """Yield (operator, description, path, apply) for every mutation site."""
    in_header = bool(path) and path[0] == "blueprint"
    if isinstance(node, dict):
        if not in_header:
            yield from _dict_sites(node, path)
        for key, value in node.items():
            yield from _walk(value, path + (key,))
    elif isinstance(node, list):
        # Drop one item at a time from lists of triggers, conditions and actions. A lone trigger is kept,
        # because an automation without any trigger would fail for a boring reason.
        if not in_header and path and path[-1] in _ACTION_LISTS:
            minimum = 2 if path[-1] == "triggers" else 1
            if len(node) >= minimum:
                for index, item in enumerate(node):
                    yield ("drop_item", f"drop {_preview(item)}", path + (index,), _deleter(path + (index,)))
        for index, value in enumerate(node):
            yield from _walk(value, path + (index,))
    elif in_header:
        # In the header only the default value of an input is changed.
        if path[-1] == "default" and isinstance(node, bool):
            yield ("bool", f"default {node} -> {not node}", path, _setter(path, not node))
        elif path[-1] == "default" and _is_number(node):
            yield from _number_sites(node, path)
    elif isinstance(node, bool):
        yield ("bool", f"{node} -> {not node}", path, _setter(path, not node))
    elif isinstance(node, str) and ("{{" in node or "{%" in node):
        for description, mutated in _template_variants(node):
            yield ("template", description, path, _setter(path, mutated))


# The changes that belong to one YAML mapping (one trigger, condition, action or the top level):
# drop a narrowing key, swap from/to, swap an action for its opposite, drop its target or data,
# change the mode, change a delay.
def _dict_sites(node: dict, path: Path) -> Iterator[tuple[str, str, Path, Callable[[Any], None]]]:
    is_trigger_or_condition = any(key in node for key in ("trigger", "condition", "platform"))
    if is_trigger_or_condition:
        for key in _DROPPABLE:
            if key in node:
                yield ("drop_key", f"remove '{key}: {_preview(node[key])}'", path + (key,), _deleter(path + (key,)))
        if "from" in node and "to" in node:
            swapped = (node["to"], node["from"])
            yield ("swap_from_to", "swap 'from' and 'to'", path, _swap_from_to(path, swapped))
    if "action" in node and isinstance(node["action"], str):
        domain, _, service = node["action"].partition(".")
        if service in _ACTION_SWAPS:
            new = f"{domain}.{_ACTION_SWAPS[service]}"
            yield ("action_swap", f"{node['action']} -> {new}", path + ("action",), _setter(path + ("action",), new))
        for key in ("target", "data"):
            if key in node:
                yield ("drop_key", f"remove '{key}' from {node['action']}", path + (key,), _deleter(path + (key,)))
    if not path and node.get("mode") in _MODE_SWAP:
        new = _MODE_SWAP[node["mode"]]
        yield ("mode", f"mode {node['mode']} -> {new}", ("mode",), _setter(("mode",), new))
    if "delay" in node:
        value = node["delay"]
        if _is_number(value):
            yield from _number_sites(value, path + ("delay",))
        elif isinstance(value, Tagged):
            yield ("number", f"delay {value!r} -> 0", path + ("delay",), _setter(path + ("delay",), 0))


# Two changes for a number: one higher (off-by-one) and to zero (ignored). Zero is skipped for 0 itself.
def _number_sites(value: float, path: Path) -> Iterator[tuple[str, str, Path, Callable[[Any], None]]]:
    yield ("number", f"{value} -> {value + 1}", path, _setter(path, value + 1))
    if value != 0:
        yield ("number", f"{value} -> 0", path, _setter(path, 0))


# Makes a function that, given the blueprint, sets the value at ``path`` to ``value``.
def _setter(path: Path, value: Any) -> Callable[[Any], None]:
    # The function that does the change when the mutant is built.
    def apply(root: Any) -> None:
        _get(root, path[:-1])[path[-1]] = value

    return apply


# Makes a function that, given the blueprint, removes whatever is at ``path`` (a key or a list item).
def _deleter(path: Path) -> Callable[[Any], None]:
    # The function that does the change when the mutant is built.
    def apply(root: Any) -> None:
        del _get(root, path[:-1])[path[-1]]

    return apply


# Makes a function that exchanges the values of "from" and "to" in the trigger at ``path``.
def _swap_from_to(path: Path, swapped: tuple[Any, Any]) -> Callable[[Any], None]:
    # The function that does the change when the mutant is built.
    def apply(root: Any) -> None:
        node = _get(root, path)
        node["from"], node["to"] = swapped[0], swapped[1]

    return apply


# Lists all mutants of a blueprint, numbered M001, M002, ... Changes that would leave the YAML identical
# are left out, because they could never be detected.
def find_mutants(document: Any) -> list[Mutant]:
    original = dump(document)
    mutants: list[Mutant] = []
    for operator, description, path, apply in _walk(document):
        mutant = Mutant("", operator, f"{_label(path)}: {description}", apply)
        if mutant.build(document) != original:
            mutants.append(dataclasses.replace(mutant, id=f"M{len(mutants) + 1:03d}"))
    return mutants


# ------------------------------------------------------------------------------- automations written directly


# A file with automations is either one automation (a dict) or a list as in automations.yaml. Returns the one to
# mutate and its index in the list (None for a dict). A list with several entries needs ``pick``, an id or an alias.
def select_automation(document: Any, pick: str | None) -> tuple[Any, int | None]:
    if not isinstance(document, list):
        return document, None
    if pick is None:
        if len(document) == 1:
            return document[0], 0
        raise SystemExit(f"The file holds {len(document)} automations; say which one to mutate with --pick <id or alias>.")
    matches = [i for i, item in enumerate(document) if isinstance(item, dict) and pick in (item.get("id"), item.get("alias"))]
    if len(matches) != 1:
        raise SystemExit(f"--pick {pick!r} matches {len(matches)} automations; it must match exactly one.")
    return document[matches[0]], matches[0]


# Puts a mutated entry back into the whole file, so that the tests read the same shape as before.
def embed(document: Any, index: int | None, entry: Any) -> Any:
    if index is None:
        return entry
    whole = list(document)
    whole[index] = entry
    return whole


# ----------------------------------------------------------------------------------------------- runner


# Judges one test run of one mutant from its exit code and output:
#   killed   = a test failed or hung, so the tests noticed the change (good)
#   survived = all tests passed although the blueprint was broken (a gap, or a change with no effect)
#   invalid  = the blueprint no longer loads at all; says nothing about the tests, so it is not counted
#   error    = pytest itself broke (bad usage, no tests collected, ...)
# pytest's own lines that name the exception that failed a test ("E   ...BlueprintLoadError: ..." in the traceback, or
# "FAILED test - ...BlueprintLoadError: ..." in the summary). Text that a test prints, or an assertion message that only
# contains the word, does not match, so a test cannot make mutants "invalid" and drop them from the score.
_LOAD_ERROR = re.compile(r"^(?:E\s+|FAILED \S+ - )(?:[\w.]+\.)?BlueprintLoadError\b", re.MULTILINE)


def classify(returncode: int, output: str, timed_out: bool) -> str:
    """killed / survived / invalid (blueprint no longer loads) / error (the test run itself broke)."""
    if timed_out:
        return "killed"
    if returncode == 0:
        return "survived"
    if returncode == 1:
        return "invalid" if _LOAD_ERROR.search(output) else "killed"
    return "error"


# Writes a new file and never writes through a symbolic link or over a file that exists (O_EXCL fails on both). The
# files are private to the user (0600).
def _write_new(path: pathlib.Path, text: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags, 0o600), "w", encoding="utf-8") as handle:
        handle.write(text)


# Files of an earlier run in --workdir (or a link placed there) must not be overwritten or followed.
_OWN_FILES = re.compile(r"control\.yaml|M\d{3,}\.yaml")


# The verdict for one mutant.
@dataclasses.dataclass
class Result:
    mutant: Mutant
    outcome: str


# All verdicts of one run, with counting and the score.
@dataclasses.dataclass
class Report:
    results: list[Result]

    # How many mutants ended with the given outcome ("killed", "survived", ...).
    def count(self, outcome: str) -> int:
        return sum(1 for result in self.results if result.outcome == outcome)

    # Share of killed mutants among those that could be judged (killed + survived), between 0 and 1.
    @property
    def score(self) -> float | None:
        """Share of loadable mutants that the tests caught; ``None`` if there were none."""
        decided = self.count("killed") + self.count("survived")
        return None if decided == 0 else self.count("killed") / decided


# Runs the test command once and returns (exit code, output text, whether it timed out).
# A command that cannot be started at all stops the whole run with a clear message.
def _run(command: list[str], env: dict[str, str], timeout: float) -> tuple[int, str, bool]:
    try:
        done = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout)
        return done.returncode, done.stdout + done.stderr, False
    except FileNotFoundError as error:
        raise SystemExit(f"Cannot run the test command {command!r}: {error}") from error
    except subprocess.TimeoutExpired as expired:
        return -1, str(expired.stdout or ""), True


# Prints one progress line and flushes it. Without the flush, output that goes to a file or through a pipe (`| tee` in CI)
# is held back until a block is full, so a long run showed nothing until it ended.
def _progress(line: str) -> None:
    print(line, flush=True)


# The main routine. Two safety checks first: the tests must pass on the untouched blueprint, and also on an
# unchanged copy that was read and written back by this tool (otherwise the tool itself would be the cause
# of failures). Then each mutant is written to a file, the tests run against it, and the outcome is judged.
def run_mutation(blueprint: pathlib.Path, command: list[str], *, timeout: float = 120, pick: str | None = None, jobs: int = 1,
                 workdir: pathlib.Path | None = None, log: Callable[[str], None] = _progress) -> Report:
    if jobs < 1:
        raise SystemExit(f"--jobs must be at least 1 (got {jobs}).")
    blueprint = blueprint.resolve()
    try:
        document = load(blueprint.read_text(encoding="utf-8"))
    except ValueError as error:
        raise SystemExit(f"{blueprint.name}: {error}") from error
    # A blueprint or one automation is mutated as it is; from a list (automations.yaml) only the picked entry.
    entry, index = select_automation(document, pick)
    mutants = find_mutants(entry)
    # Never inherit mutation settings from an outer run.
    base_env = {key: value for key, value in os.environ.items() if not key.startswith("HA_BLUEPRINT_TEST_HARNESS_")}

    # Check 1: the tests pass on the original blueprint.
    code, output, timed_out = _run(command, base_env, timeout)
    if code != 0 or timed_out:
        raise SystemExit(f"The tests do not pass on the unmodified blueprint (exit {code}); fix that first.\n{output[-2000:]}")

    with tempfile.TemporaryDirectory() as scratch:
        folder = workdir or pathlib.Path(scratch)
        folder.mkdir(parents=True, exist_ok=True)
        leftovers = sorted(item.name for item in folder.iterdir() if _OWN_FILES.fullmatch(item.name))
        if leftovers:
            raise SystemExit(f"The workdir {folder} already holds {', '.join(leftovers[:3])}; use an empty folder, because the tool "
                             "writes control.yaml and M001.yaml, ... there and must not overwrite or follow anything.")
        # HA_BLUEPRINT_TEST_HARNESS_ORIGINAL names the file to replace; HA_BLUEPRINT_TEST_HARNESS_MUTANT (set per run) names its replacement.
        env = {**base_env, "HA_BLUEPRINT_TEST_HARNESS_ORIGINAL": str(blueprint)}

        # Check 2: the tests pass on the round-tripped but otherwise unchanged copy.
        control = folder / "control.yaml"
        _write_new(control, dump(document))
        code, output, timed_out = _run(command, {**env, "HA_BLUEPRINT_TEST_HARNESS_MUTANT": str(control)}, timeout)
        if code != 0 or timed_out:
            raise SystemExit("The tests fail on the unmodified blueprint after a YAML round trip, so mutants "
                             f"cannot be judged (exit {code}).\n{output[-2000:]}")

        log(f"{len(mutants)} mutants of {blueprint.name}" + (f" ({jobs} at a time)" if jobs > 1 else ""))
        log_lock = threading.Lock()

        # Tests one mutant: writes its file, runs the tests against it and judges the outcome. Mutants do not depend on
        # each other (each run is its own process with its own file), so several can run at the same time.
        def judge(mutant: Mutant) -> Result:
            path = folder / f"{mutant.id}.yaml"
            _write_new(path, dump(embed(document, index, mutant.mutated(entry))))
            code, output, timed_out = _run(command, {**env, "HA_BLUEPRINT_TEST_HARNESS_MUTANT": str(path)}, timeout)
            outcome = classify(code, output, timed_out)
            with log_lock:
                log(f"{outcome:9s} {mutant.id}  {mutant.description}")
            return Result(mutant, outcome)

        # map() keeps the order of the mutants, whatever order they finish in.
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            results = list(pool.map(judge, mutants))
    return Report(results)


# Splits the command line at the first "--": everything before is for this tool (options, blueprint path),
# everything after is the test command that is run for each mutant. Needed because the test command has
# options of its own (like --timeout) that must not be mistaken for ours.
def split_command(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split ``[options...] -- command...`` at the first ``--``; options may come before or after the blueprint."""
    if "--" not in argv:
        return argv, []
    index = argv.index("--")
    return argv[:index], argv[index + 1:]


# The command-line entry point: read the options, run all mutants, print the summary and the survivors.
# Exit code: 0 = fine, 1 = score below --fail-under, 2 = a test run broke.
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ha_blueprint_test_harness.mutate", description=__doc__.split("\n\n")[0])
    parser.add_argument("blueprint", type=pathlib.Path, help="a blueprint file, or a file with an automation written directly")
    parser.add_argument("--pick", help="for a file with several automations: the id or alias of the one to mutate")
    parser.add_argument("--timeout", type=float, default=120, help="seconds per test run (default 120)")
    parser.add_argument("--jobs", type=int, default=1, help="run this many mutants at the same time (default 1); the tests must not share files")
    parser.add_argument("--workdir", type=pathlib.Path, help="keep the mutant files here")
    parser.add_argument("--fail-under", type=float, default=0.0, help="exit 1 if the score is lower (0 to 100)")
    own, command = split_command(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(own)
    command = command or [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"]

    report = run_mutation(args.blueprint, command, timeout=args.timeout, pick=args.pick, jobs=args.jobs, workdir=args.workdir)
    survivors = [result for result in report.results if result.outcome == "survived"]
    print()
    print(f"killed {report.count('killed')}, survived {report.count('survived')}, "
          f"invalid {report.count('invalid')} (blueprint no longer loads, not counted), error {report.count('error')}")
    if report.score is not None:
        print(f"score {report.score * 100:.0f}% of the {report.count('killed') + report.count('survived')} loadable mutants")
    if survivors:
        print("survivors (a test gap or an equivalent change; judge each one):")
        for result in survivors:
            print(f"  {result.mutant.id}  {result.mutant.description}")
    if report.count("error"):
        return 2
    return 1 if report.score is not None and report.score * 100 < args.fail_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
