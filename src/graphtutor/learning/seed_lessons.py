from typing import Dict
from graphtutor.schemas.lesson import (
    LessonPayload,
    LearningTheme,
    MathSymbol,
)

SEED_LESSONS: Dict[str, LessonPayload] = {
    "transformers": LessonPayload(
        concept_slug="transformers",
        display_name="Transformers",
        theme=LearningTheme.AI_PIPELINE,
        summary="The Transformer architecture replaces sequential recurrent loops with parallelized self-attention across tokens.",
        intuition_anchor="Like an executive briefing room where every advisor listens directly to every other advisor simultaneously, instead of passing notes down a telephone line.",
        tensor_pipeline_steps=[
            "Token IDs [Batch, Seq] -> Embedding + Positional Encoding [Batch, Seq, D_model]",
            "Linear projections generate Q, K, V matrices [Batch, Heads, Seq, D_k]",
            "Scaled Dot-Product Attention: Softmax(Q · K^T / sqrt(D_k)) · V",
            "Multi-head concatenation and projection back to [Batch, Seq, D_model]",
            "Residual connection and LayerNorm: LayerNorm(x + SubLayer(x))",
            "Feed-forward network with non-linear activation (GELU/SwiGLU)",
        ],
        matrix_intuition="The attention matrix is a pairwise affinity grid of shape [Seq, Seq], where cell (i, j) quantifies how strongly token i attends to token j.",
        hyperparameters_note="Key scaling hyperparams: d_model=768..4096, n_heads=12..32, d_k=64, context_length=2048..128k.",
    ),
    "attention-mechanism": LessonPayload(
        concept_slug="attention-mechanism",
        display_name="Attention Mechanism",
        theme=LearningTheme.AI_PIPELINE,
        summary="Soft query-key dictionary retrieval computing continuous context vectors via softmax affinity weights.",
        intuition_anchor="Like looking up an entry in an encyclopedia index: Query is what you seek, Keys are the page headings, and Values are the page contents.",
        tensor_pipeline_steps=[
            "Compute raw scores: Attention_Scores = Q · K^T",
            "Scale by variance: Scaled_Scores = Attention_Scores / sqrt(d_k)",
            "Apply optional causal mask (mask future tokens with -1e9)",
            "Softmax normalization along last dimension: Weights = Softmax(Scaled_Scores)",
            "Output context: Output = Weights · V",
        ],
        matrix_intuition="Softmax transforms arbitrary real-valued dot products into a row-stochastic probability distribution where each row sums to 1.0.",
        hyperparameters_note="Head dimension d_k typically equals d_model / n_heads (commonly 64 or 128).",
    ),
    "linear-algebra": LessonPayload(
        concept_slug="linear-algebra",
        display_name="Linear Algebra",
        theme=LearningTheme.MATH,
        summary="Vector spaces and linear maps providing the geometric and computational bedrock for neural networks.",
        intuition_anchor="Vectors are arrows in space representing data features; matrices are transformation engines that rotate, scale, and project that space.",
        formula_latex="y = W x + b, \\quad W \\in \\mathbb{R}^{m \\times n}, \\; x \\in \\mathbb{R}^n",
        symbol_glossary=[
            MathSymbol(symbol="x", name="Input Vector", meaning="Feature representation vector in n-dimensional Euclidean space."),
            MathSymbol(symbol="W", name="Weight Matrix", meaning="Linear operator projecting vectors from n-space into m-space."),
            MathSymbol(symbol="b", name="Bias Vector", meaning="Affine translation vector shifting the coordinate origin."),
            MathSymbol(symbol="y", name="Output Vector", meaning="Transformed representation vector in m-dimensional target space."),
        ],
        geometric_intuition="Multiplying x by W maps the unit basis sphere into an ellipsoid whose principal axes align with the singular vectors of W.",
    ),
    "docker": LessonPayload(
        concept_slug="docker",
        display_name="Docker & Containers",
        theme=LearningTheme.SYSTEMS,
        summary="Process isolation utilizing Linux kernel cgroups and namespaces to bundle application runtimes consistently.",
        intuition_anchor="Like a standardized shipping container loaded with factory goods: ships and trains do not care what is inside, only how to hoist and transport the standard box.",
        topology_nodes=["Host OS Kernel", "Container Engine (containerd)", "Isolated Container Namespaces (PID, NET, MNT)", "Layered Read-Only Images (OverlayFS)"],
        data_journey_steps=[
            "Developer executes `docker build` creating immutable sha256 layer blobs",
            "Engine pulls base layers from OCI registry and unpacks into OverlayFS lowerdirs",
            "Container startup invokes `clone()` system call with namespace flags",
            "Cgroups limit memory ceiling and CPU quota",
            "Application executes with direct bare-metal kernel performance"
        ]
    )
}
