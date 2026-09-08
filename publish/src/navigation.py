"""Read-only navigation of the shared OctoPlant server archive."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable


_PLC_PATTERN = re.compile(r"\bPLC\s*0*(\d+)(?![A-Za-z0-9])", re.IGNORECASE)
_PLC_INPUT_PATTERN = re.compile(r"^\s*0*(\d+)\s*$")
_NUMBER_PATTERN = re.compile(r"\d+")
_SERVER_ARCHIVE_RWZI_PATH = Path(
    r"\\pOctoplan1\poctoplan1_D\vdServerArchive\RWZI's"
)


class ProjectNavigationError(RuntimeError):
    """Raised when the shared server archive cannot resolve a project."""


@dataclass(frozen=True)
class ProjectLocation:
    """A project location resolved from the shared server archive."""

    root_folder: str
    installation_folder: str
    archive_folder: str
    project_folder: str
    component_path: str
    archive_relative_path: str
    last_version_timestamp: float

    def as_dict(self) -> dict[str, str]:
        """Return MCP-safe project metadata."""
        return {
            "root_folder": self.root_folder,
            "installation_folder": self.installation_folder,
            "archive_folder": self.archive_folder,
            "project_folder": self.project_folder,
            "component_path": self.component_path,
            "archive_relative_path": self.archive_relative_path,
        }


def _normalise(value: str) -> str:
    """Normalize text for case-, separator-, and accent-insensitive matching."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(
        character.casefold()
        for character in decomposed
        if not unicodedata.combining(character) and character.isalnum()
    )


def _plc_number(value: str) -> int | None:
    """Extract a PLC number from a project name."""
    match = _PLC_PATTERN.search(value)
    if match:
        return int(match.group(1))

    input_match = _PLC_INPUT_PATTERN.fullmatch(value)
    return int(input_match.group(1)) if input_match else None


def _canonical_cost_center(value: str) -> str:
    """Return the six-digit archive cost-center code."""
    digits = "".join(_NUMBER_PATTERN.findall(value))
    if not digits:
        raise ProjectNavigationError("De kostenplaats bevat geen cijfers.")
    if len(digits) == 6 and digits.startswith("100"):
        return digits
    return f"{100_000 + int(digits):06d}"


class ServerArchiveNavigator:
    """Resolve installations and PLC projects from the fixed read-only archive."""

    def __init__(self) -> None:
        self._archive_root = _SERVER_ARCHIVE_RWZI_PATH

    def resolve(
        self,
        installation_name: str | None = None,
        cost_center: str | None = None,
        plc_name: str | None = None,
    ) -> ProjectLocation:
        """Scan the archive and return the best matching PLC project.

        The scan deliberately has no cache: an MCP session sees the current
        spelling and contents of the shared server archive on every lookup.
        """
        if not (installation_name or cost_center):
            raise ProjectNavigationError(
                "Geef minstens een installatienaam of kostenplaats op."
            )

        installation = self._find_installation(
            self._archive_root,
            installation_name=installation_name,
            cost_center=cost_center,
        )
        archive = self._find_archive_folder(installation)
        project, timestamp = self._find_project(
            archive, plc_name=plc_name or "PLC01"
        )
        archive_relative_path = "\\" + "\\".join(
            (self._archive_root.name, *project.relative_to(self._archive_root).parts)
        )
        component_path = "\\" + "\\".join(
            (self._archive_root.name, installation.name, project.name)
        )

        return ProjectLocation(
            root_folder=self._archive_root.name,
            installation_folder=installation.name,
            archive_folder=archive.name,
            project_folder=project.name,
            component_path=component_path,
            archive_relative_path=archive_relative_path,
            last_version_timestamp=timestamp,
        )

    def _directories(self, folder: Path) -> list[Path]:
        """List a folder's direct child directories without leaking OS errors."""
        try:
            return [entry for entry in folder.iterdir() if entry.is_dir()]
        except OSError as error:
            raise ProjectNavigationError(
                "De gedeelde OctoPlant-serverarchive kan niet worden gelezen."
            ) from error

    def _find_installation(
        self,
        root: Path,
        installation_name: str | None,
        cost_center: str | None,
    ) -> Path:
        candidates = self._directories(root)
        name_query = _normalise(installation_name or "")
        cost_query = _canonical_cost_center(cost_center) if cost_center else ""

        scored: list[tuple[int, Path]] = []
        for candidate in candidates:
            normalized = _normalise(candidate.name)
            score = 0
            if cost_query:
                number_groups = _NUMBER_PATTERN.findall(candidate.name)
                if cost_query not in number_groups:
                    continue
                score += 1_000
            if name_query:
                if name_query not in normalized:
                    continue
                score += 500 if normalized.endswith(name_query) else 400
            scored.append((score, candidate))

        if not scored:
            raise ProjectNavigationError(
                "Geen installatiemap gevonden voor de opgegeven naam of kostenplaats."
            )
        return max(scored, key=lambda entry: (entry[0], entry[1].name.casefold()))[1]

    def _find_archive_folder(self, installation: Path) -> Path:
        archives = [
            folder
            for folder in self._directories(installation)
            if _normalise(folder.name) == "archive"
        ]
        if not archives:
            raise ProjectNavigationError(
                "De installatiemap bevat geen ARCHIVE-submap."
            )
        return archives[0]

    def _find_project(self, archive: Path, plc_name: str) -> tuple[Path, float]:
        requested_number = _plc_number(plc_name)
        query = _normalise(plc_name)
        candidates = self._directories(archive)
        if not candidates:
            raise ProjectNavigationError("De ARCHIVE-submap bevat geen PLC-projecten.")

        scored = [
            (self._project_score(candidate.name, requested_number, query), candidate)
            for candidate in candidates
        ]
        best_score = max(score for score, _ in scored)
        best = [candidate for score, candidate in scored if score == best_score]
        if best_score <= 0:
            raise ProjectNavigationError(
                "Geen PLC-project gevonden dat overeenkomt met de opgegeven PLC-naam."
            )

        dated = [
            (self._latest_version_timestamp(candidate), candidate)
            for candidate in best
        ]
        timestamp, project = max(dated, key=lambda entry: (entry[0], entry[1].name.casefold()))
        return project, timestamp

    @staticmethod
    def _project_score(
        candidate_name: str, requested_number: int | None, query: str
    ) -> int:
        normalized = _normalise(candidate_name)
        candidate_number = _plc_number(candidate_name)
        if requested_number is not None and candidate_number != requested_number:
            return 0

        score = 1_000 if candidate_number is not None else 0
        if normalized.endswith("ce"):
            score += 100
        score += int(SequenceMatcher(None, normalized, query).ratio() * 100)
        return score

    @staticmethod
    def _latest_version_timestamp(project: Path) -> float:
        """Find the newest nested version timestamp only for tied candidates."""
        paths: Iterable[Path] = project.rglob("*")
        timestamps: list[float] = []
        for path in paths:
            try:
                timestamps.append(path.stat().st_mtime)
            except OSError:
                continue
        if timestamps:
            return max(timestamps)
        try:
            return project.stat().st_mtime
        except OSError:
            return 0.0
