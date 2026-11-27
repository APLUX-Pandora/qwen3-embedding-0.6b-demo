"use strict";

const tabs = Array.from(document.querySelectorAll('[role="tab"]'));

function selectTab(index, focus = false) {
  tabs.forEach((tab, position) => {
    const active = position === index;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
    document.getElementById(tab.getAttribute("aria-controls")).hidden = !active;
  });
  updateEncoding();
  if (focus) tabs[index].focus();
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(index));
  tab.addEventListener("keydown", (event) => {
    let next;
    switch (event.key) {
      case "ArrowLeft": next = (index + tabs.length - 1) % tabs.length; break;
      case "ArrowRight": next = (index + 1) % tabs.length; break;
      case "Home": next = 0; break;
      case "End": next = tabs.length - 1; break;
      default: return;
    }
    event.preventDefault();
    selectTab(next, true);
  });
});

const byId = (id) => document.getElementById(id);

const sentenceExamples = [
  ["Paraphrase", "The meeting has been moved to Friday.", "The meeting was rescheduled for Friday."],
  ["Opposite meanings", "I support extending the opening hours.", "I oppose extending the opening hours."],
  ["Cross-language pair", "The train will arrive in ten minutes.", "火车将在十分钟后到站。"],
  ["Unrelated pair", "I need to buy a train ticket to Boston.", "Octopuses have three hearts."],
];

function registerExamples(container, examples, onSelect) {
  for (const [label, ...values] of examples) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "example";
    button.textContent = label;
    button.disabled = true;
    button.addEventListener("click", () => onSelect(...values));
    container.append(button);
  }
}

const similarityForm = byId("similarity-form");
registerExamples(byId("similarity-examples"), sentenceExamples, (first, second) => {
  byId("first-sentence").value = first;
  byId("second-sentence").value = second;
  byId("similarity-error").hidden = true;
  byId("similarity-result").hidden = true;
  showEncoding("similarity", null);
});

similarityForm.addEventListener("submit", (event) => {
  event.preventDefault();
  byId("similarity-result").hidden = true;
  runOperation(similarityForm, byId("similarity-error"), "/api/similarity", {
    first: byId("first-sentence").value,
    second: byId("second-sentence").value,
  }, ({ score, encoding }) => {
    byId("similarity-score").textContent = score.toFixed(3);
    byId("similarity-bar").value = score;
    byId("similarity-result").hidden = false;
    showEncoding("similarity", encoding);
  });
});

const queryExamples = [
  ["Chinese query, English result", "怎样让正在运行的推理马上停下来？"],
  ["Paraphrased query", "已经开始计算了，怎么中途终止？"],
  ["Renew a library book", "这本书还没看完，怎么晚几天再还？"],
];

function libraryEntry({ title, text }) {
  const item = document.createElement("details");
  const heading = document.createElement("summary");
  const body = document.createElement("p");
  heading.textContent = title;
  body.textContent = text;
  item.append(heading, body);
  return item;
}

function renderResults(results) {
  const rows = results.map(({ title, snippet, score }, index) => {
    const item = document.createElement("li");
    item.className = "match";
    const heading = document.createElement("div");
    heading.className = "score-heading";
    const titleNode = document.createElement("h3");
    titleNode.textContent = index === 0 ? "Top match · " + title : title;
    const value = document.createElement("output");
    value.textContent = score.toFixed(3);
    heading.append(titleNode, value);
    const original = document.createElement("p");
    original.textContent = snippet;
    const meter = document.createElement("meter");
    meter.min = -1;
    meter.max = 1;
    meter.value = score;
    meter.setAttribute("aria-label", "Cosine similarity");
    item.append(heading, original, meter);
    return item;
  });
  byId("results").replaceChildren(...rows);
  const status = byId("results-status");
  status.textContent = `${results.length} results ranked by relevance.`;
  status.hidden = false;
}

const searchForm = byId("search-form");
registerExamples(byId("query-examples"), queryExamples, (query) => {
  byId("query").value = query;
  searchForm.requestSubmit();
});
searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  byId("results-status").hidden = true;
  byId("results").replaceChildren();
  runOperation(searchForm, byId("search-error"), "/api/search", { query: byId("query").value },
    ({ results, encoding, index }) => {
      renderResults(results);
      showEncoding("retrieval", encoding);
      showIndex(index);
    });
});

const documentForm = byId("document-form");
documentForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runOperation(documentForm, byId("document-error"), "/api/documents", async () => {
    const pasted = byId("document-body").value;
    const file = byId("document-file").files[0];
    let title = byId("document-title").value.trim();
    if (!file) return { title, text: pasted };
    if (pasted.trim()) throw new Error("Paste text or upload a file.");
    if (!/\.txt$/i.test(file.name)) throw new Error("Choose a .txt file.");
    if (file.size > 128 * 1024) throw new Error("The file must be 128 KiB or smaller.");
    let text;
    try {
      text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
    } catch {
      throw new Error("Could not read the file. Upload a UTF-8 .txt file.");
    }
    title = title || Array.from(file.name.slice(0, -4)).slice(0, 80).join("");
    return { title, text };
  }, ({ document: added, encoding, index }) => {
    byId("library").prepend(libraryEntry(added));
    byId("library").scrollTop = 0;
    documentForm.reset();
    showIndex(index);
    showEncoding("retrieval", encoding);
  });
});

const encodingByTab = {};
let busy = true;

function showEncoding(tab, encoding) {
  encodingByTab[tab] = encoding;
  updateEncoding();
}

function updateEncoding() {
  const tab = tabs.find((tab) => tab.getAttribute("aria-selected") === "true");
  const encoding = encodingByTab[tab.getAttribute("aria-controls")];
  byId("encode-time").textContent = encoding ? encoding.encode_ms.toFixed(2) + " ms" : "—";
  byId("input-tokens").textContent = encoding ? String(encoding.input_tokens) : "—";
}

function showIndex(index) {
  byId("index-status").textContent =
    `${index.count} documents indexed in ${index.total_s.toFixed(2)} s`;
  byId("index-total").textContent = index.total_s.toFixed(2) + " s";
  byId("index-average").textContent = index.average_ms.toFixed(2) + " ms";
  byId("document-form").querySelector("button").disabled = busy || index.count >= index.limit;
  byId("document-form").dataset.full = String(index.count >= index.limit);
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll(".example, .primary").forEach((button) => { button.disabled = value; });
  if (byId("document-form").dataset.full === "true") {
    byId("document-form").querySelector("button").disabled = true;
  }
}

async function readJson(path, options) {
  let response, result;
  try {
    response = await fetch(path, options);
    result = await response.json();
  } catch {
    throw new Error("Request failed. Try again.");
  }
  if (!response.ok) throw new Error(result.error || "Request failed. Try again.");
  return result;
}

async function runOperation(form, error, path, payload, onSuccess) {
  if (busy) return;
  setBusy(true);
  form.setAttribute("aria-busy", "true");
  error.hidden = true;
  try {
    const value = typeof payload === "function" ? await payload() : payload;
    const result = await readJson(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(value),
    });
    onSuccess(result);
  } catch (problem) {
    error.textContent = problem.message;
    error.hidden = false;
  } finally {
    form.removeAttribute("aria-busy");
    setBusy(false);
  }
}

async function start() {
  try {
    const data = await readJson("/api/library");
    byId("chip").textContent = data.chip;
    byId("indicator").classList.add("ready");
    byId("model-status").textContent = "Model loaded";
    byId("load-time").textContent = data.load_s.toFixed(2) + " s";
    byId("first-encode").textContent = data.first_encode_ms.toFixed(2) + " ms";
    byId("embedding-dim").textContent = String(data.embedding_dim);
    byId("max-input").textContent = data.max_input_tokens + " tokens";
    byId("library").replaceChildren(...data.documents.map(libraryEntry));
    showIndex(data.index);
    setBusy(false);
  } catch {
    byId("model-status").textContent = "Could not load model status. Refresh the page.";
  }
}

start();
