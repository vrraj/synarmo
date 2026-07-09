const typedText = document.getElementById("typed-text");
const contextText = document.getElementById("context-text");
const suggestBtn = document.getElementById("suggest-btn");
const clearBtn = document.getElementById("clear-btn");
const suggestionsList = document.getElementById("suggestions-list");
const suggestionStatus = document.getElementById("suggestion-status");
const serviceStatus = document.getElementById("service-status");
const errorBanner = document.getElementById("error-banner");
const charCount = document.getElementById("char-count");
const choicesInput = document.getElementById("choices");
const candidateTokensInput = document.getElementById("candidate-tokens");
const candidateWordsInput = document.getElementById("candidate-words");
const temperatureInput = document.getElementById("temperature");
const topPInput = document.getElementById("top-p");
const logprobPoolInput = document.getElementById("logprob-pool");
const suggestOnSpacebarInput = document.getElementById("suggest-on-spacebar");
let requestId = 0;
let lastSuggestionRequestText = "";

function updateCount() {
  const count = typedText.value.length;
  charCount.textContent = `${count} ${count === 1 ? "character" : "characters"}`;
}

function setError(message) {
  errorBanner.textContent = message || "";
  errorBanner.style.display = message ? "block" : "none";
}

function setLoading(isLoading) {
  suggestBtn.disabled = isLoading;
  suggestionsList.classList.toggle("loading", isLoading);
  suggestionStatus.textContent = isLoading ? "Predicting..." : "Ready";
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    serviceStatus.textContent = `${data.status} / ${data.backend}${data.model ? ` / ${data.model}` : ""}`;
    serviceStatus.title = serviceStatus.textContent;
  } catch {
    serviceStatus.textContent = "service unavailable";
  }
}

async function fetchSuggestions(textOverride) {
  const text = textOverride ?? typedText.value;
  const requestText = text.trimEnd();
  if (!requestText.trim()) {
    suggestionsList.innerHTML = '<div class="muted">Enter typed text to get suggestions.</div>';
    return;
  }

  const currentRequest = ++requestId;
  lastSuggestionRequestText = requestText;
  setError("");
  setLoading(true);
  try {
    const response = await fetch("/evaluate/autocomplete", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        text: requestText,
        contexts: [contextText.value.trim() || ""],
        choices: numberValue(choicesInput, 3),
        candidate_tokens: numberValue(candidateTokensInput, 10),
        candidate_words: numberValue(candidateWordsInput, 1),
        temperature: numberValue(temperatureInput, 0.5),
        top_p: numberValue(topPInput, 0.95),
        logprob_pool: numberValue(logprobPoolInput, 12),
      }),
    });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    const data = await response.json();
    if (currentRequest !== requestId) {
      return;
    }
    const firstResult = (data.results || [])[0] || {};
    const candidates = firstResult.candidates || [];
    renderSuggestions(
      candidates.map((candidate) => candidate.text),
      candidates.map((candidate) => candidate.logprob)
    );
  } catch (error) {
    if (currentRequest === requestId) {
      suggestionsList.innerHTML = '<div class="muted">No suggestions available.</div>';
      setError(error.message || "Unable to fetch suggestions.");
    }
  } finally {
    if (currentRequest === requestId) {
      setLoading(false);
    }
  }
}

function renderSuggestions(suggestions, scores) {
  if (!suggestions.length) {
    suggestionsList.innerHTML = '<div class="muted">No suggestions returned.</div>';
    return;
  }

  suggestionsList.innerHTML = "";
  suggestions.forEach((suggestion, index) => {
    const button = document.createElement("button");
    button.className = "suggestion-button";
    button.type = "button";
    button.innerHTML = `
      <span class="suggestion-text">${escapeHtml(suggestion)}</span>
      <span class="suggestion-score">${formatProbability(scores[index])}</span>
    `;
    button.addEventListener("click", () => applySuggestion(suggestion));
    suggestionsList.appendChild(button);
  });
}

function applySuggestion(suggestion) {
  const nextText = appendCandidate(typedText.value, suggestion);
  if (nextText === typedText.value) {
    return;
  }
  typedText.value = nextText;
  updateCount();
  typedText.focus();
  fetchSuggestions();
}

function appendCandidate(typedTextValue, candidate) {
  if (!candidate) {
    return typedTextValue;
  }
  if (!typedTextValue || /[\s]$/.test(typedTextValue)) {
    return typedTextValue + candidate;
  }
  if (/^['",.;:!?]/.test(candidate)) {
    return typedTextValue + candidate;
  }
  return `${typedTextValue} ${candidate}`;
}

function maybeSuggestAfterSpace(event) {
  updateCount();
  if (!suggestOnSpacebarInput.checked || event.inputType !== "insertText" || event.data !== " ") {
    return;
  }

  const textBeforeSpace = typedText.value.trimEnd();
  if (!textBeforeSpace || textBeforeSpace === lastSuggestionRequestText) {
    return;
  }
  if (!/\S$/.test(textBeforeSpace) || !/\S+\s*$/.test(textBeforeSpace)) {
    return;
  }

  fetchSuggestions(textBeforeSpace);
}

function formatProbability(score) {
  if (typeof score !== "number") {
    return "";
  }
  const probability = Math.exp(score) * 100;
  if (!Number.isFinite(probability)) {
    return "";
  }
  return `${probability.toFixed(probability >= 10 ? 0 : 1)}%`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function numberValue(input, fallback) {
  const value = Number(input.value);
  return Number.isFinite(value) ? value : fallback;
}

suggestBtn.addEventListener("click", () => fetchSuggestions());
clearBtn.addEventListener("click", () => {
  typedText.value = "";
  suggestionsList.innerHTML = '<div class="muted">Type something to begin</div>';
  lastSuggestionRequestText = "";
  updateCount();
  setError("");
  typedText.focus();
});
typedText.addEventListener("input", maybeSuggestAfterSpace);

updateCount();
checkHealth();
