"""Release mode build command helpers."""

import os
from pathlib import Path
from typing import List, Optional, Sequence, Union

from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

from buildkit.clean import (
    CleanCommand,
    DEFAULT_SUFFIX_PATTERNS,
    iter_matched_files,
    normalize_patterns,
    remove_files,
)
from buildkit.summary import filter_files


def _env_flag(name: str) -> bool:
    """Return True if the environment variable represents a truthy value."""

    value = os.environ.get(name)
    if value is None:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _parse_patterns(value: Optional[Union[Sequence[str], str]]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    else:
        items = [str(part).strip() for part in value]
    return [item for item in items if item]


class ReleaseBuildCommand(_bdist_wheel):
    """Build wheels with optional release cleanup for source and intermediate files."""

    description = "Build wheel with optional release cleanup"
    user_options = _bdist_wheel.user_options + [
        ("release", None, "Enable release mode post-processing."),
        ("del-py", None, "Remove Python source files (requires --release)."),
        ("del-c", None, "Remove generated C files."),
        ("del-so", None, "Remove compiled extension files (.so/.pyd)."),
        ("del-all", None, "Remove Python, C, and compiled extension files."),
        (
            "keep-patterns=",
            None,
            "Comma separated glob patterns to keep even when release cleanup is enabled.",
        ),
    ]
    boolean_options = _bdist_wheel.boolean_options + [
        "release",
        "del-py",
        "del-c",
        "del-so",
        "del-all",
    ]

    def initialize_options(self):
        super().initialize_options()
        self.release = False
        self.del_py = False
        self.del_c = False
        self.del_so = False
        self.del_all = False
        self.keep_patterns = None
        self._parsed_keep_patterns: List[str] = []

    def finalize_options(self):
        super().finalize_options()

        env_release = _env_flag("BUILD_RELEASE")
        env_del_all = _env_flag("BUILD_RELEASE_DEL_ALL")
        env_del_py = _env_flag("BUILD_RELEASE_DEL_PY")
        env_del_c = _env_flag("BUILD_RELEASE_DEL_C")
        env_del_so = _env_flag("BUILD_RELEASE_DEL_SO")

        keep_env = os.environ.get("BUILD_RELEASE_KEEP")

        if keep_env and not self.keep_patterns:
            self.keep_patterns = keep_env

        self.release = bool(self.release or env_release)
        self.del_all = bool(self.del_all or env_del_all)
        self.del_py = bool(self.del_py or env_del_py)
        self.del_c = bool(self.del_c or env_del_c)
        self.del_so = bool(self.del_so or env_del_so)

        if self.del_all:
            self.del_py = True
            self.del_c = True
            self.del_so = True

        if self.release and not any([self.del_py, self.del_c, self.del_so]):
            self.del_py = True
            self.del_c = True
            self.del_so = True

        self._parsed_keep_patterns = _parse_patterns(self.keep_patterns)

    # -- Helpers -----------------------------------------------------------------
    def _collect_suffix_patterns(self) -> List[str]:
        patterns: List[str] = []
        if self.del_py:
            patterns.append("*.py")
        if self.del_c:
            patterns.append("*.c")
        if self.del_so:
            patterns.extend(DEFAULT_SUFFIX_PATTERNS)
        return normalize_patterns(patterns)

    def _resolve_files_to_remove(self, patterns: Sequence[str]) -> List[Path]:
        matched = iter_matched_files(patterns, Path("."))
        if not self._parsed_keep_patterns:
            return matched
        return list(filter_files(matched, self._parsed_keep_patterns))

    def _get_clean_command(self) -> CleanCommand:
        try:
            existing_cmd = self.get_finalized_command("clean")
        except (AttributeError, KeyError):
            existing_cmd = None

        if isinstance(existing_cmd, CleanCommand):
            return existing_cmd

        cmd = CleanCommand(self.distribution)
        cmd.ensure_finalized()
        return cmd

    # -- Main command ------------------------------------------------------------
    def run(self):
        super().run()

        if not (self.release or self.del_py or self.del_c or self.del_so):
            return

        patterns = self._collect_suffix_patterns()
        if not patterns:
            return

        files_to_remove = self._resolve_files_to_remove(patterns)

        clean_cmd = self._get_clean_command()
        if not self._parsed_keep_patterns:
            clean_cmd.set_suffixes(patterns)
            clean_cmd.run()
            return

        if files_to_remove:
            remove_files(files_to_remove)

        clean_cmd.set_suffixes([])
        clean_cmd.run()

