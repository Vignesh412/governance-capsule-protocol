const state = {
  scenarios: [],
  selected: null,
  result: null,
  executionId: 0,
};

const $ = (id) => document.getElementById(id);
const list = $("scenarioList");
const runButton = $("runButton");
const TOUR_TIMING = {
  scenarioIntroduction: 5000,
  firstStep: 4300,
  nextStep: 4100,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function loadScenarios() {
  try {
    const response = await fetch("/api/scenarios");
    if (!response.ok) throw new Error("Could not load scenarios");
    state.scenarios = (await response.json()).scenarios;
    $("proofCount").textContent = state.scenarios.length;
    selectScenario(state.scenarios[0].id, true);
  } catch (error) {
    const openedDirectly = window.location.protocol === "file:";
    list.innerHTML = openedDirectly
      ? '<p class="error">Start <code>python3 demo/server.py</code>, then open <code>http://127.0.0.1:8765</code>.</p>'
      : '<p class="error">The Python demo server is not connected.</p>';
    $("scenarioTitle").textContent = openedDirectly ? "Open through the demo server" : "Kernel unavailable";
    $("scenarioDescription").textContent = openedDirectly
      ? "This page was opened as a file, so it cannot call the Python governance kernel."
      : "The browser could not reach the local reference kernel.";
  }
}

function renderScenarios() {
  list.innerHTML = state.scenarios.map((scenario) => `
    <button class="scenario ${state.selected?.id === scenario.id ? "active" : ""}"
            type="button" data-scenario="${escapeHtml(scenario.id)}">
      <span class="indicator"></span>
      <b>${escapeHtml(scenario.name)}</b>
      <small class="${escapeHtml(scenario.tone)}">EXPECTED · ${escapeHtml(scenario.expected)}</small>
    </button>
  `).join("");
  list.querySelectorAll("[data-scenario]").forEach((button) => {
    button.addEventListener("click", () => selectScenario(button.dataset.scenario, true));
  });
}

function selectScenario(id, execute = false) {
  state.selected = state.scenarios.find((item) => item.id === id);
  state.result = null;
  renderScenarios();
  $("scenarioTitle").textContent = state.selected.name;
  $("scenarioDescription").textContent = state.selected.description;
  $("storyUseCase").textContent = state.selected.use_case;
  $("storyTask").textContent = state.selected.task;
  $("storyGovernance").textContent = state.selected.governance;
  $("storyChange").textContent = state.selected.change;
  $("whyItMatters").textContent = state.selected.why_it_matters;
  $("sourceFramework").textContent = state.selected.source_framework || "ORIGINATING AGENT";
  $("sourceAgentName").textContent = state.selected.source_agent || "Procurement intake";
  $("sourceAgentDetail").textContent = state.selected.source_framework ? "Exports signed governance" : "Creates governed task";
  $("destinationFramework").textContent = state.selected.destination_framework || "RECEIVING AGENT";
  $("destinationAgentName").textContent = state.selected.destination_agent || "Supplier operations";
  $("destinationAgentDetail").textContent = state.selected.destination_framework ? "Verifies before tool access" : "Requests protected action";
  $("emptyState").hidden = false;
  $("results").hidden = true;
  runButton.disabled = false;
  if (execute) runScenario();
}

function reasonText(result) {
  const labels = {
    GCP_AUTHORITY_EXPANSION: "The child requested authority that the parent never possessed.",
    GCP_OBLIGATION_REMOVED: "A mandatory parent obligation did not survive the handoff.",
    GCP_BUDGET_OVERALLOCATED: "The child budget exceeded the authority delegated by its parent.",
    GCP_INVALID_DELEGATION_PROOF: "The delegation proof no longer matches its signature or bound artifacts.",
    GCP_REVOKED: "The root authority was revoked and the revocation cascaded to this descendant.",
  };
  if (result.scenario_id === "crash-recovery") {
    return "Restart reconciliation found the prior commit and prevented duplicate execution.";
  }
  if (result.state === "COMMITTED") {
    return "Signatures, lineage, authority, obligations, budget, and revocation checks passed.";
  }
  return labels[result.reason_codes[0]] || result.reason_codes[0] || "The governance kernel rejected this action.";
}

function renderTimeline(items) {
  $("timeline").innerHTML = items.map((item) => `
    <li class="${escapeHtml(item.status)}">
      <i></i>
      <b>${escapeHtml(item.label)}</b>
      <span>${escapeHtml(item.detail)}</span>
    </li>
  `).join("");
}

function renderLineage(result) {
  const holder = $("lineage");
  const recovery = $("recoveryProof");
  if (result.recovery) {
    holder.hidden = true;
    recovery.hidden = false;
    const proof = result.recovery;
    recovery.innerHTML = `
      <div><span>Durable state at crash</span><strong>${escapeHtml(proof.durable_state_at_crash)}</strong></div>
      <div><span>State after recovery</span><strong>${escapeHtml(proof.state_after_recovery)}</strong></div>
      <div><span>Calls before restart</span><strong>${proof.connector_calls_before_restart}</strong></div>
      <div><span>Calls after recovery</span><strong>${proof.connector_calls_after_recovery}</strong></div>
    `;
    return;
  }
  holder.hidden = false;
  recovery.hidden = true;
  holder.innerHTML = result.lineage.map((item, index) => `
    ${index ? '<div class="inherit-arrow"></div>' : ""}
    <div class="lineage-card">
      <div class="lineage-head">
        <div><small>${escapeHtml(item.role)}</small><h4>${escapeHtml(item.subject.split("/").pop())}</h4></div>
        <code>${escapeHtml(item.digest.slice(0, 19))}…</code>
      </div>
      <div class="lineage-values">
        <div><span>Authority</span><b>${escapeHtml(item.authority)}</b></div>
        <div><span>Obligations</span><b>${item.obligations}</b></div>
        <div><span>Budget</span><b>${escapeHtml(item.budget)}</b></div>
      </div>
    </div>
  `).join("");
}

function renderResult(result) {
  const strip = document.querySelector(".decision-strip");
  strip.classList.remove("blocked", "recovered");
  const recovered = result.scenario_id === "crash-recovery";
  const allowed = result.state === "COMMITTED" && !recovered;
  if (recovered) strip.classList.add("recovered");
  else if (!allowed) strip.classList.add("blocked");

  $("decisionSymbol").textContent = allowed ? "✓" : recovered ? "↻" : "×";
  $("decisionTitle").textContent = allowed ? "Action allowed" : recovered ? "Action recovered" : "Action blocked";
  $("decisionReason").textContent = reasonText(result);
  $("connectorCalls").textContent = result.connector_calls;
  $("supplierCount").textContent = result.suppliers_created;
  $("traceStatus").textContent = allowed ? "VERIFIED" : recovered ? "RECOVERED" : "REJECTED";
  renderTimeline(result.timeline);
  renderLineage(result);
  $("receiptContent").textContent = JSON.stringify(result.receipt, null, 2);
  $("emptyState").hidden = true;
  $("results").hidden = false;
  window.requestAnimationFrame(() => {
    $("results").scrollIntoView({behavior: "smooth", block: "start"});
  });
}

function pause(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function guidedDetail(result, step) {
  if (result.scenario_id === "crash-recovery") return step.detail;
  const failed = step.status === "fail";
  const guides = {
    "Capsule received": "Procurement sends the task together with its authority, $10 ceiling, mandatory audit rule, and signed provenance.",
    "Cryptographic proof": failed
      ? "The gateway recalculates the signed content and discovers that the delegation proof was changed after it was signed."
      : "The gateway verifies who issued the capsules and confirms that the parent, child, and receiving agent are cryptographically bound.",
    "Delegation semantics": failed
      ? state.selected.change
      : "The gateway compares parent and child: authority became narrower, the audit rule survived, and the child budget stayed inside the parent limit.",
    "Revocation freshness": failed
      ? "The gateway checks current status and learns that the root authority was cancelled. Every descendant must stop."
      : "Before acting, the gateway checks that neither this capsule nor an upstream capsule has been revoked.",
    "Protected action": result.connector_calls
      ? "Every governance check passed, so the gateway calls the supplier system exactly once."
      : "The gateway stops here. The supplier system is never called, so no business side effect occurs.",
  };
  return guides[step.label] || step.detail;
}

async function playExecution(result, executionId) {
  const visibleSteps = [];
  for (const item of result.timeline) {
    if (item.status === "skip") break;
    visibleSteps.push(item);
    if (item.status === "fail") break;
  }

  $("results").hidden = true;
  $("emptyState").hidden = false;
  $("handoff").classList.add("is-running");
  $("storyCard").scrollIntoView({behavior: "smooth", block: "center"});
  await pause(TOUR_TIMING.scenarioIntroduction);
  if (executionId !== state.executionId) return false;
  $("handoff").scrollIntoView({behavior: "smooth", block: "center"});

  for (let index = 0; index < visibleSteps.length; index += 1) {
    if (executionId !== state.executionId) return false;
    const step = visibleSteps[index];
    $("handoff").dataset.phase = String(Math.min(index, 4));
    const progress = visibleSteps.map((_, dot) =>
      `<i class="${dot < index ? "done" : dot === index ? "active" : ""}"></i>`
    ).join("");
    $("emptyState").innerHTML = `
      <div class="flow-step ${escapeHtml(step.status)}">
        <small>STEP ${index + 1} OF ${visibleSteps.length}</small>
        <strong>${escapeHtml(step.label)}</strong>
        <p>${escapeHtml(guidedDetail(result, step))}</p>
        <div class="flow-dots">${progress}</div>
      </div>
    `;
    await pause(index === 0 ? TOUR_TIMING.firstStep : TOUR_TIMING.nextStep);
  }

  if (executionId !== state.executionId) return false;
  $("handoff").classList.remove("is-running");
  delete $("handoff").dataset.phase;
  return true;
}

async function runScenario() {
  if (!state.selected) return;
  const executionId = ++state.executionId;
  const scenarioId = state.selected.id;
  runButton.disabled = true;
  runButton.classList.add("running");
  runButton.querySelector("span").textContent = "Verifying…";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({scenario_id: scenarioId}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Execution failed");
    if (executionId !== state.executionId) return;
    state.result = result;
    if (await playExecution(result, executionId)) renderResult(result);
  } catch (error) {
    if (executionId !== state.executionId) return;
    $("emptyState").hidden = false;
    $("emptyState").innerHTML = `<span>EXECUTION ERROR</span><p>${escapeHtml(error.message)}</p>`;
  } finally {
    if (executionId !== state.executionId) return;
    runButton.disabled = false;
    runButton.classList.remove("running");
    runButton.querySelector("span").textContent = "Run again";
  }
}

runButton.addEventListener("click", runScenario);
$("evidenceButton").addEventListener("click", () => $("receiptDialog").showModal());
$("closeDialog").addEventListener("click", () => $("receiptDialog").close());
$("receiptDialog").addEventListener("click", (event) => {
  if (event.target === $("receiptDialog")) $("receiptDialog").close();
});

loadScenarios();
