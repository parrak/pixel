const demoData = {
  organization: "Citron ASC West",
  metrics: {
    revenueAtRisk: "$286,420",
    openWork: 28,
    bottleneck: "ASC Denials",
  },
  tasks: [
    {
      id: "TASK-AUTH-01",
      workflow: "ASC Authorization",
      priority: "urgent",
      title: "Prior authorization denial at deadline",
      owner: "Auth Specialist",
      amountAtRisk: "$3,600",
      recommendation: {
        title: "Request retro authorization review",
        summary: "Synthetic denial evidence suggests retro review may prevent avoidable write-off.",
        action: "Assemble supporting records and escalate to authorization remediation.",
      },
    },
    {
      id: "TASK-CHARGE-02",
      workflow: "ASC Charge Capture",
      priority: "high",
      title: "Implant charge capture validation",
      owner: "Coder",
      amountAtRisk: "$1,320",
      recommendation: {
        title: "Validate missing implant charge",
        summary: "Implant log references a separately reimbursable device not present on the charge export.",
        action: "Confirm invoice support and add facility charge if validated.",
      },
    },
    {
      id: "TASK-AR-03",
      workflow: "ASC AR Follow-Up",
      priority: "normal",
      title: "120+ day orthopedic AR follow-up",
      owner: "Biller",
      amountAtRisk: "$24,000",
      recommendation: {
        title: "Advance payer follow-up",
        summary: "High-value claim is aging beyond 120 days without resolution.",
        action: "Validate status, prior touches, and move to escalation if unresolved.",
      },
    },
  ],
};

const loadButton = document.getElementById("loadDemo");
const queueList = document.getElementById("queueList");
const recommendationPanel = document.getElementById("recommendationPanel");
const decisionPanel = document.getElementById("decisionPanel");
const outcomePanel = document.getElementById("outcomePanel");
const demoMetrics = document.getElementById("demoMetrics");

if (loadButton) {
  loadButton.addEventListener("click", () => {
    renderMetrics();
    renderQueue();
    renderTask(demoData.tasks[0]);
  });
}

function renderMetrics() {
  demoMetrics.innerHTML = `
    <div><strong>${demoData.metrics.revenueAtRisk}</strong><br/>Revenue at risk</div>
    <div><strong>${demoData.metrics.openWork}</strong><br/>Open work</div>
    <div><strong>${demoData.metrics.bottleneck}</strong><br/>Workflow bottleneck</div>
  `;
}

function renderQueue() {
  queueList.innerHTML = "";
  demoData.tasks.forEach((task, index) => {
    const item = document.createElement("button");
    item.className = `queue-item${index === 0 ? " is-active" : ""}`;
    item.innerHTML = `
      <span class="pill pill-${task.priority}">${task.priority}</span>
      <strong>${task.title}</strong>
      <p>${task.workflow} · ${task.owner} · ${task.amountAtRisk}</p>
    `;
    item.addEventListener("click", () => {
      document.querySelectorAll(".queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderTask(task);
    });
    queueList.appendChild(item);
  });
}

function renderTask(task) {
  recommendationPanel.innerHTML = `
    <strong>${task.recommendation.title}</strong>
    <p>${task.recommendation.summary}</p>
    <p><strong>Suggested action:</strong> ${task.recommendation.action}</p>
  `;

  decisionPanel.innerHTML = `
    <strong>Record a synthetic decision</strong>
    <div class="decision-buttons">
      <button data-decision="approve">Approve</button>
      <button data-decision="escalate">Escalate</button>
      <button data-decision="reroute">Reroute</button>
    </div>
  `;

  decisionPanel.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => renderOutcome(task, button.dataset.decision));
  });

  outcomePanel.innerHTML = "<p>Outcome pending.</p>";
}

function renderOutcome(task, decision) {
  const outcomes = {
    approve: {
      status: "Recovery pipeline advanced",
      summary: `${task.workflow} moved forward with an approved recommendation.`,
    },
    escalate: {
      status: "Escalated to manager review",
      summary: "Human judgment preserved the task and routed it into operational oversight.",
    },
    reroute: {
      status: "Rerouted",
      summary: "Recommendation rejected and the task returned to workflow routing.",
    },
  };
  const outcome = outcomes[decision];
  outcomePanel.innerHTML = `
    <strong>${outcome.status}</strong>
    <p>${outcome.summary}</p>
    <p><strong>Task:</strong> ${task.id}</p>
  `;
}
