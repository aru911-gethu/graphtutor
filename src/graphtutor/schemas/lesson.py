from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LearningTheme(str, Enum):
    CODE = "code"                 # The Builder: Code + line-by-line remarks + terminal output
    SYSTEMS = "systems"           # The Architect: Topology + state journey + CLI + split-brain
    MATH = "math"                 # The Theorist: KaTeX formula + symbol glossary + geometric intuition
    AI_PIPELINE = "ai_pipeline"   # The ML Engineer: Tensor transformations + attention matrix + pipeline
    DECISIONS = "decisions"       # The Decision Maker: Trade-off matrix + decision tree + case study
    DEBUGGING = "debugging"       # The Troubleshooter: Error log + root cause + diff + checklist


class CodeRemark(BaseModel):
    line: int
    note: str


class MathSymbol(BaseModel):
    symbol: str
    name: str
    meaning: str


class JourneyStep(BaseModel):
    step: int
    title: str
    state_description: str


class TradeoffItem(BaseModel):
    dimension: str  # e.g. Latency, Cost, Operational Complexity
    option_a: str
    option_b: str


class DiffBlock(BaseModel):
    before: str
    after: str
    explanation: str


class LessonPayload(BaseModel):
    concept_slug: str
    display_name: str
    theme: LearningTheme
    summary: str
    intuition_anchor: str  # Real-world analogy or problem context

    # Theme 1: Code Fields
    code_snippet: Optional[str] = None
    code_language: Optional[str] = "python"
    code_remarks: List[CodeRemark] = Field(default_factory=list)
    terminal_output: Optional[str] = None

    # Theme 2: Systems & Infra Fields
    topology_mermaid: Optional[str] = None
    data_journey: List[JourneyStep] = Field(default_factory=list)
    cli_commands: Optional[str] = None
    failure_mode_gotcha: Optional[str] = None

    # Theme 3: Math Fields
    formula_latex: Optional[str] = None
    symbol_glossary: List[MathSymbol] = Field(default_factory=list)
    geometric_intuition: Optional[str] = None

    # Theme 4: AI Pipeline Fields
    tensor_pipeline_steps: List[str] = Field(default_factory=list)
    matrix_intuition: Optional[str] = None
    hyperparameters_note: Optional[str] = None

    # Theme 5: Decisions Fields
    tradeoff_matrix: List[TradeoffItem] = Field(default_factory=list)
    decision_tree_mermaid: Optional[str] = None
    case_study: Optional[str] = None

    # Theme 6: Debugging Fields
    error_log: Optional[str] = None
    root_cause: Optional[str] = None
    code_diff: Optional[DiffBlock] = None
    prevention_checklist: List[str] = Field(default_factory=list)
