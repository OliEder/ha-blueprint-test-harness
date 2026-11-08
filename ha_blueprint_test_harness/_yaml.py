"""Helpers for YAML files that use aliases (``&anchor`` and ``*name``). Shared by the test environment (``env.py``) and the
mutation tool (``mutate.py``), so that a file is treated the same way in both.

An alias is cheap to read but expensive to use: Home Assistant (and the mutation tool, which writes every mutant out in
full) walks an aliased part once for every place it is used, so a few nested aliases make the work grow without limit. A
260-byte file kept the mutation tool busy for minutes before its first test. Ordinary aliases (a list of options that is
used in three places) are fine; what is limited is what a file expands to.
"""

from __future__ import annotations

from typing import Any

import yaml

# The most values a file may expand to through aliases. The real blueprint that showed the need has 1 040.
MAX_VALUES = 20_000


# A loader that reads any file that is YAML at all, with any tag (such as !input), only to measure it. It builds plain
# lists, dicts and text and never runs anything.
class _MeasuringLoader(yaml.SafeLoader):
    pass


# What a tagged value becomes in the measuring loader: its plain content.
def _plain(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_mapping(node, deep=True)


_MeasuringLoader.add_multi_constructor("!", _plain)


# Counts the values of a document, a shared one every time it is reached, and stops counting above ``limit`` (so that an
# alias bomb does not take long to refuse).
def expanded_size(document: Any, limit: int) -> int:
    count, stack = 0, [document]
    while stack and count <= limit:
        node = stack.pop()
        count += 1
        if isinstance(node, dict):
            stack.extend(node.keys())
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return count


# True when the text uses at least one alias.
def has_aliases(text: str) -> bool:
    return any(isinstance(event, yaml.AliasEvent) for event in yaml.parse(text, Loader=_MeasuringLoader))


# Raises ValueError when the aliases of the text expand to more than ``MAX_VALUES`` values. Text without aliases, and text
# that is not valid YAML (its reader reports that itself), pass.
def check_expansion(text: str) -> None:
    try:
        if not has_aliases(text):
            return
        document = yaml.load(text, Loader=_MeasuringLoader)
    except yaml.YAMLError:
        return
    if expanded_size(document, MAX_VALUES) > MAX_VALUES:
        raise ValueError(f"the file expands to more than {MAX_VALUES} values through YAML aliases (*name); write some of them out")


# Writes every value out in full, never as an alias: a shared part dumped this way becomes independent copies when it is read.
class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True


# The same document with every shared part made independent, so that a change to one place never changes another place that
# was an alias of it. Only for plain data (what ``yaml.safe_load`` returns).
def unshare(document: Any) -> Any:
    return yaml.safe_load(yaml.dump(document, Dumper=_NoAliasDumper, sort_keys=False, width=10**6, allow_unicode=True))
