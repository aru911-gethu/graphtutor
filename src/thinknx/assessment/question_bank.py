from typing import List, Optional
from thinknx.assessment.models import Question, BloomsLevel

QUESTION_BANK: List[Question] = [
    Question(
        id="q_trans_1",
        concept_slug="transformers",
        blooms_level=BloomsLevel.UNDERSTAND,
        difficulty=0.4,
        prompt="What is the core architectural innovation of the Transformer over RNNs?",
        options=[
            "It computes pairwise token self-attention in parallel, eliminating sequential bottleneck.",
            "It uses continuous Fourier transformations instead of matrix multiplications.",
            "It eliminates all matrix multiplications using discrete lookup trees.",
            "It requires strictly single-precision integer CPU arithmetic."
        ],
        correct_index=0,
        explanation="Self-attention allows O(1) sequential operations across sequence lengths, enabling GPU parallelism.",
        prerequisite_probes=["attention-mechanism", "neural-networks"]
    ),
    Question(
        id="q_trans_2",
        concept_slug="transformers",
        blooms_level=BloomsLevel.ANALYZE,
        difficulty=0.7,
        prompt="Why does standard full self-attention have O(N^2) memory complexity with respect to sequence length N?",
        options=[
            "Because an N x N affinity score matrix must be computed and stored for each attention head.",
            "Because the vocabulary size grows quadratically with context length.",
            "Because feed-forward layers duplicate weights for each input token.",
            "Because positional encodings require O(N^2) parameter storage."
        ],
        correct_index=0,
        explanation="Every token attends to every other token, producing an N x N attention matrix per head.",
        prerequisite_probes=["linear-algebra", "attention-mechanism"]
    ),
    Question(
        id="q_attn_1",
        concept_slug="attention-mechanism",
        blooms_level=BloomsLevel.APPLY,
        difficulty=0.5,
        prompt="In scaled dot-product attention, what operation produces the unnormalized attention weights?",
        options=[
            "Matrix multiplication of Query matrix Q by transposed Key matrix K^T.",
            "Element-wise addition of Query matrix Q and Value matrix V.",
            "Convolution of Key matrix K over Value matrix V.",
            "Discrete cosine transform of Value vectors."
        ],
        correct_index=0,
        explanation="Q · K^T computes all pairwise dot products between query tokens and key tokens.",
        prerequisite_probes=["linear-algebra"]
    ),
    Question(
        id="q_la_1",
        concept_slug="linear-algebra",
        blooms_level=BloomsLevel.UNDERSTAND,
        difficulty=0.3,
        prompt="What geometric operation does a matrix multiplication W · x perform on vector x?",
        options=[
            "A linear transformation that rotates, scales, or shears the vector space.",
            "A non-linear clustering of points into discrete Voronoi cells.",
            "An irreversible reduction of all vector components to scalar zero.",
            "A random permutation of vector elements."
        ],
        correct_index=0,
        explanation="Matrices represent linear coordinate transformations that preserve vector addition and scalar multiplication.",
        prerequisite_probes=[]
    ),
    Question(
        id="q_docker_1",
        concept_slug="docker",
        blooms_level=BloomsLevel.UNDERSTAND,
        difficulty=0.4,
        prompt="Which Linux kernel feature is primarily responsible for isolating process IDs, networks, and mounts in containers?",
        options=[
            "Namespaces (pid, net, mnt, ipc, uts)",
            "Control Groups (cgroups)",
            "Kernel Ring Buffer (dmesg)",
            "Virtual memory swap partition"
        ],
        correct_index=0,
        explanation="Namespaces provide process-level view isolation; cgroups enforce resource consumption limits.",
        prerequisite_probes=[]
    ),
]


def get_questions_for_concept(concept_slug: str) -> List[Question]:
    slug = concept_slug.lower().strip()
    return [q for q in QUESTION_BANK if q.concept_slug == slug]


def get_question_by_id(question_id: str) -> Optional[Question]:
    return next((q for q in QUESTION_BANK if q.id == question_id), None)
