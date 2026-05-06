# geoagent/geo/rules.py
"""GEO rules definitions based on yao-geo-skills rubric."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GEODimension:
    name: str
    description: str
    optimization_action: str


@dataclass
class GEORules:
    dimensions: dict[str, GEODimension]
    min_score: int = 4

    @classmethod
    def from_rubric_file(cls, path: str) -> "GEORules":
        content = Path(path).read_text()
        dimensions = {}

        dimension_map = {
            "source_quality": "Add authoritative citations and official sources",
            "freshness": "Add dates, mention recent developments and updates",
            "directness": "Lead with conclusion, front-load key points, answer directly",
            "fairness": "Avoid promotion, present balanced view, evidence-based comparisons",
            "traceability": "Add citation anchors, reference list, link claims to evidence",
            "anti_hallucination": "Avoid absolute claims, note uncertainty, verify facts"
        }

        for name, action in dimension_map.items():
            dimensions[name] = GEODimension(
                name=name,
                description=f"GEO dimension: {name}",
                optimization_action=action
            )

        return cls(dimensions=dimensions)

    def get_optimization_prompt(self) -> str:
        parts = ["Apply the following GEO optimizations to the document:\n"]
        for name, dim in self.dimensions.items():
            parts.append(f"- **{dim.name}**: {dim.optimization_action}")
        return "\n".join(parts)