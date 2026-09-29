const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  let token = "";
  if (typeof window !== "undefined") {
    token = localStorage.getItem("graphtutor_token") || "";
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText}`);
  }

  return res.json();
}

export async function createGuestDemoSession() {
  const data = await fetchApi("/api/v1/demo/session", { method: "POST" });
  if (typeof window !== "undefined" && data.access_token) {
    localStorage.setItem("graphtutor_token", data.access_token);
    localStorage.setItem("graphtutor_user", JSON.stringify(data.user));
  }
  return data;
}

export async function getUserProfile() {
  return fetchApi("/api/v1/me");
}

export async function getGraphData() {
  return fetchApi("/api/v1/graph");
}

export async function getDueReviews() {
  return fetchApi("/api/v1/reviews/due");
}

export async function submitReview(concept: string, rating: number, targetDepth?: string) {
  return fetchApi(`/api/v1/reviews/${concept}`, {
    method: "POST",
    body: JSON.stringify({ rating, target_depth: targetDepth }),
  });
}

export async function getLearningPath(goal: string) {
  return fetchApi(`/api/v1/path?goal=${encodeURIComponent(goal)}`);
}

export async function ingestContent(sourceType: string, content: string) {
  return fetchApi("/api/v1/ingest", {
    method: "POST",
    body: JSON.stringify({ source_type: sourceType, content }),
  });
}

export async function getAssessmentQuestions(conceptSlug: string) {
  return fetchApi(`/api/v1/assessment/questions/${conceptSlug}`);
}

export async function submitAssessmentAnswer(payload: {
  question_id: string;
  concept_slug: string;
  selected_index: number;
  response_time_ms: number;
  current_theta: number;
}) {
  return fetchApi("/api/v1/assessment/submit", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSkillReport() {
  return fetchApi("/api/v1/assessment/report");
}

export async function createChallenge(conceptSlug: string, score: number, questionIds: string[]) {
  return fetchApi("/api/v1/assessment/challenge", {
    method: "POST",
    body: JSON.stringify({
      concept_slug: conceptSlug,
      score,
      question_ids: questionIds,
    }),
  });
}