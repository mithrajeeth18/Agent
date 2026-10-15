"""Document-skill discovery and single-prompt instruction injection."""

from __future__ import annotations

from pathlib import Path

from schemas import SkillNeeded


class SkillRouter:
    """Resolve document skill requests relative to the project root."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def instruction_for(self, skill: SkillNeeded) -> str:
        """Return the selected SKILL.md content, or an empty string for no skill."""
        if skill.type == "none":
            return ""
        path = self.project_root / "Document skills" / skill.type / "SKILL.md"
        if not path.is_file():
            raise FileNotFoundError(f"Document skill is missing: {path}")
        return f"\n\nACTIVE DOCUMENT SKILL ({skill.type}; action: {skill.action}):\n{path.read_text(encoding='utf-8')}\n"

    @staticmethod
    def infer_from_request(request: str) -> SkillNeeded:
        """Choose the output document skill before the first model decision when obvious."""
        normalized = request.lower()
        if any(word in normalized for word in ("powerpoint", "power point", "pptx", "slide", "presentation")):
            return SkillNeeded(type="pptx", action="create or edit a presentation")
        if any(word in normalized for word in ("pdf", ".pdf")):
            return SkillNeeded(type="pdf", action="create, inspect, or edit a PDF")
        if any(word in normalized for word in ("docx", "word document")):
            return SkillNeeded(type="docx", action="create, inspect, or edit a Word document")
        if any(word in normalized for word in ("xlsx", "spreadsheet", "excel", "csv")):
            return SkillNeeded(type="xlsx", action="create, inspect, or edit a spreadsheet")
        return SkillNeeded()
