"""D1 bounded newc transformation. Initial API only for the red test."""
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping


class ArchiveError(ValueError):
    """Input or containment gate failed."""


@dataclass(frozen=True)
class Member:
    name: str
    raw_name: bytes
    fields: tuple[int, ...]
    payload: bytes
    raw: bytes


@dataclass(frozen=True)
class Archive:
    raw: bytes
    members: tuple[Member, ...]
    tail: bytes


def parse_newc(raw: bytes) -> Archive:
    raise NotImplementedError("D1 red-test boundary")


def replace_members(original: Archive, replacements: Mapping[str, bytes],
                    additions: tuple[tuple[str, bytes], ...]) -> bytes:
    raise NotImplementedError("D1 red-test boundary")


def read_regular(path: Path, expected_sha256: str | None = None) -> bytes:
    raise NotImplementedError("D1 red-test boundary")


def write_new(path: Path, payload: bytes) -> None:
    raise NotImplementedError("D1 red-test boundary")
