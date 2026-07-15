const typedText = document.getElementById("typed-text");
const contextText = document.getElementById("context-text");
const suggestBtn = document.getElementById("suggest-btn");
const clearBtn = document.getElementById("clear-btn");
const suggestionsList = document.getElementById("suggestions-list");
const suggestionStatus = document.getElementById("suggestion-status");
const serviceStatus = document.getElementById("service-status");
const serviceStatusValue = document.getElementById("service-status-value");
const modelNameValue = document.getElementById("model-name-value");
const gpuLayersValue = document.getElementById("gpu-layers-value");
const errorBanner = document.getElementById("error-banner");
const charCount = document.getElementById("char-count");
const choicesInput = document.getElementById("choices");
const candidateTokensInput = document.getElementById("candidate-tokens");
const candidateWordsInput = document.getElementById("candidate-words");
const tokenRecommendation = document.getElementById("token-recommendation");
const temperatureInput = document.getElementById("temperature");
const topPInput = document.getElementById("top-p");
const logprobPoolInput = document.getElementById("logprob-pool");
const suggestOnSpacebarInput = document.getElementById("suggest-on-spacebar");
const infrastructureMetrics = document.getElementById("infrastructure-metrics");
const refreshInfrastructureBtn = document.getElementById("refresh-infrastructure-btn");
let requestId = 0;
let lastSuggestionRequestText = "";

function updateCount() {
  const count = typedText.value.length;
  charCount.textContent = `${count} ${count === 1 ? "character" : "characters"}`;
}

function updateTokenRecommendation() {
  const words = Math.max(1, Math.round(numberValue(candidateWordsInput, 1)));
  const tokens = Math.max(1, Math.round(numberValue(candidateTokensInput, 1)));
  const recommended = Math.max(2, Math.ceil(words * 1.5));
  const high = recommended + 2;
  let message = `For ${words} ${words === 1 ? "word" : "words"}, about ${recommended} tokens is usually enough.`;
  let isWarning = false;

  if (tokens < recommended) {
    message += ` Current ${tokens} may truncate suggestions.`;
    isWarning = true;
  } else if (tokens > high) {
    message += ` Current ${tokens} may add latency.`;
    isWarning = true;
  } else {
    message += ` Current ${tokens} looks balanced.`;
  }

  tokenRecommendation.textContent = message;
  tokenRecommendation.classList.toggle("is-warning", isWarning);
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
    const statusText = titleCase(data.status || "unknown");
    const modelName = data.model ? basename(data.model) : data.backend || "Unknown";
    const gpuLayerText = formatGpuLayers(data);
    serviceStatusValue.textContent = statusText;
    serviceStatusValue.classList.toggle("is-ok", data.status === "ok");
    serviceStatusValue.classList.toggle("is-error", data.status !== "ok");
    modelNameValue.textContent = modelName;
    gpuLayersValue.textContent = gpuLayerText;
    serviceStatus.title = [
      `Service status: ${statusText}`,
      data.backend ? `Backend: ${data.backend}` : "",
      data.model ? `Model: ${data.model}` : "",
      `GPU layers: ${gpuLayerText}`,
      typeof data.model_layers === "number" ? `Model layers: ${data.model_layers}` : "",
      typeof data.gpu_offload_supported === "boolean"
        ? `GPU offload supported: ${data.gpu_offload_supported ? "yes" : "no"}`
        : "",
    ]
      .filter(Boolean)
      .join(" / ");
    renderInfrastructure(data.infrastructure);
  } catch {
    serviceStatusValue.textContent = "Unavailable";
    serviceStatusValue.classList.remove("is-ok");
    serviceStatusValue.classList.add("is-error");
    modelNameValue.textContent = "Unknown";
    gpuLayersValue.textContent = "Unknown";
    serviceStatus.title = "Service status: Unavailable";
    renderInfrastructure(null);
  }
}

function renderInfrastructure(infrastructure) {
  infrastructureMetrics.innerHTML = "";
  if (!infrastructure) {
    appendInfrastructureMetric("Status", "Unavailable");
    return;
  }
  appendInfrastructureMetric("Model file", formatBytes(infrastructure.model_file_bytes));
  appendInfrastructureMetric("Model weights resident in RAM", formatBytes(infrastructure.model_mapped_resident_ram_bytes));
  appendInfrastructureMetric("Synarmo process RAM", formatBytes(infrastructure.process_resident_ram_bytes));
  appendInfrastructureMetric("KV tokens (last evaluation)", formatTokenUsage(infrastructure));
  const architecture = infrastructure.model_architecture || {};
  appendInfrastructureMetric("Model architecture", formatValue(architecture.architecture));
  appendInfrastructureMetric("Sequence length (n_ctx)", formatValue(architecture.sequence_length));
  appendInfrastructureMetric("Trained sequence length", formatValue(architecture.trained_sequence_length));
  appendInfrastructureMetric("Vocabulary size", formatValue(architecture.vocabulary_size));
  appendInfrastructureMetric("Hidden dimension", formatValue(architecture.hidden_dimension));
  appendInfrastructureMetric("Attention heads", formatValue(architecture.attention_heads));
  appendInfrastructureMetric("Key/value attention heads", formatValue(architecture.key_value_attention_heads));
  appendInfrastructureMetric("Transformer layers", formatValue(architecture.layers));
  const gpu = infrastructure.gpu || {};
  if (gpu.available) {
    appendInfrastructureMetric("Synarmo GPU VRAM", formatBytes(gpu.process_memory_bytes));
    appendInfrastructureMetric("GPU device VRAM", `${formatBytes(gpu.device_memory_used_bytes)} / ${formatBytes(gpu.device_memory_total_bytes)}`);
    appendInfrastructureMetric("GPU device utilization", formatPercent(gpu.device_utilization_pct));
  } else {
    appendInfrastructureMetric("NVIDIA GPU telemetry", gpu.reason || "Unavailable");
  }
}

function appendInfrastructureMetric(label, value) {
  const item = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value;
  item.append(term, description);
  infrastructureMetrics.appendChild(item);
}

function formatBytes(value) {
  if (typeof value !== "number" || value < 0) return "Unavailable";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  let amount = value;
  let unit = 0;
  while (amount >= 1024 && unit < units.length - 1) { amount /= 1024; unit += 1; }
  return `${amount.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function formatTokenUsage(infrastructure) {
  const { kv_cache_tokens_current: current, kv_cache_tokens_max: maximum } = infrastructure;
  if (typeof current !== "number" || typeof maximum !== "number") return "Unavailable";
  const utilization = infrastructure.kv_cache_utilization_pct;
  const suffix = typeof utilization === "number" ? ` (${utilization.toFixed(1)}%)` : "";
  return `${current} / ${maximum}${suffix}`;
}

function formatPercent(value) {
  return typeof value === "number" ? `${value}%` : "Unavailable";
}

function formatValue(value) {
  return value === null || value === undefined || value === "" ? "Unavailable" : String(value);
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
        candidate_tokens: numberValue(candidateTokensInput, 5),
        candidate_words: numberValue(candidateWordsInput, 1),
        temperature: numberValue(temperatureInput, 0.5),
        top_p: numberValue(topPInput, 0.95),
        logprob_pool: numberValue(logprobPoolInput, 24),
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

function basename(path) {
  return String(path).split(/[\\/]/).filter(Boolean).pop() || String(path);
}

function formatGpuLayers(data) {
  if (data.requested_gpu_layers === "all") {
    return typeof data.model_layers === "number" ? `All (${data.model_layers})` : "All";
  }
  if (data.n_gpu_layers === 0) {
    return "CPU";
  }
  if (typeof data.requested_gpu_layers === "number") {
    return String(data.requested_gpu_layers);
  }
  if (typeof data.n_gpu_layers === "number") {
    return String(data.n_gpu_layers);
  }
  return "Unknown";
}

function titleCase(value) {
  const text = String(value);
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
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
candidateWordsInput.addEventListener("input", updateTokenRecommendation);
candidateTokensInput.addEventListener("input", updateTokenRecommendation);
refreshInfrastructureBtn.addEventListener("click", checkHealth);

updateCount();
updateTokenRecommendation();
checkHealth();
