const demoData = {
  portfolioMetrics: {
    revenueAtRisk: "$184,435",
    openWork: 10,
    recoveryPipeline: "$156,715",
    productivity: "5 documented outcomes",
  },
  mondayMorning: {
    vp: "Morgan Lee, VP Revenue Cycle, opens Citron and sees portfolio health rather than detector screens.",
    brief: [
      "Revenue at risk is concentrated in denials and aging AR across ASC Alpha.",
      "Charge capture and authorization queues are still within service levels.",
      "The operating system recommends denial and AR assignment first because they hold the highest recoverable value.",
    ],
  },
  organizations: [
    {
      id: "org_alpha",
      name: "ASC Alpha",
      summary: "Highest recoverable denial value in the portfolio.",
      roles: [
        {
          role: "VP Revenue Cycle",
          queue: 2,
          task: "Reassign urgent denial and aging AR work",
          recommendation: "Assign denial and AR queues first to preserve near-term recovery.",
          decision: "Morgan Lee assigned the denial deadline task to Jasmine Brooks and the high-dollar AR task to Daniel Ortiz.",
          outcome: "Morning assignments clarified queue ownership and exposed the top workflow bottleneck.",
        },
        {
          role: "Denial Specialist",
          queue: 1,
          task: "Prior authorization denial at deadline",
          recommendation: "Initiate retro authorization remediation with cited denial evidence.",
          decision: "Jasmine Brooks approved the recommendation and moved the workflow into remediation.",
          outcome: "Appeal path documented. Financial result expected: $1,152. Resolution time target: 18 hours.",
        },
        {
          role: "AR Specialist",
          queue: 1,
          task: "High-dollar orthopedic AR follow-up",
          recommendation: "Advance payer follow-up and escalate if unresolved by next touch.",
          decision: "Daniel Ortiz approved follow-up and documented escalation criteria.",
          outcome: "Follow-up completed. Financial result expected: $7,680. Resolution time target: 42 hours.",
        },
        {
          role: "Coding Specialist",
          queue: 0,
          task: "No critical Alpha coding work this morning",
          recommendation: "Monitor the portfolio and absorb overflow if denials resolve early.",
          decision: "Coding queue held in reserve for overflow support.",
          outcome: "No immediate action required.",
        },
        {
          role: "Authorization Specialist",
          queue: 1,
          task: "Validate missing prior authorization support",
          recommendation: "Review retro authorization feasibility before the denial deadline closes.",
          decision: "Elena Park documented the remediation path and attached supporting workflow notes.",
          outcome: "Authorization remediation documented. Financial result expected: $1,152. Resolution time target: 16 hours.",
        },
      ],
    },
    {
      id: "org_bravo",
      name: "ASC Bravo",
      summary: "Coding and charge capture standardization opportunity.",
      roles: [
        {
          role: "Coding Specialist",
          queue: 2,
          task: "Implant charge capture validation",
          recommendation: "Validate the missing implant charge against the implant log and invoice support.",
          decision: "Nina Patel approved charge correction review.",
          outcome: "Charge action recorded. Financial result expected: $422.40. Resolution time target: 18 hours.",
        },
      ],
    },
    {
      id: "org_charlie",
      name: "ASC Charlie",
      summary: "Smaller operator with outsized aging AR exposure.",
      roles: [
        {
          role: "AR Specialist",
          queue: 2,
          task: "120+ day AR follow-up backlog",
          recommendation: "Work the oldest accounts first and escalate claims without payer response.",
          decision: "Maya Foster prioritized the oldest accounts and documented escalation points.",
          outcome: "Backlog stratified by aging and value.",
        },
      ],
    },
  ],
};

const metricsNode = document.getElementById("demoMetrics");
const organizationList = document.getElementById("organizationList");
const mondayPanel = document.getElementById("mondayPanel");
const roleList = document.getElementById("roleList");
const recommendationPanel = document.getElementById("recommendationPanel");
const decisionPanel = document.getElementById("decisionPanel");
const outcomePanel = document.getElementById("outcomePanel");
const loadButton = document.getElementById("loadDemo");
const runSimulator = document.getElementById("runSimulator");
const simulatorPanel = document.getElementById("simulatorPanel");

if (loadButton) {
  loadButton.addEventListener("click", () => {
    renderMetrics();
    renderMondayMorning();
    renderOrganizations();
    renderOrganization(demoData.organizations[0]);
  });
}

if (runSimulator) {
  runSimulator.addEventListener("click", () => {
    const specialty = document.getElementById("specialtySelect").value;
    const headcount = Number(document.getElementById("headcountInput").value);
    const maturity = document.getElementById("maturitySelect").value;
    renderSimulator(specialty, headcount, maturity);
  });
}

function renderMetrics() {
  metricsNode.innerHTML = `
    <div><strong>${demoData.portfolioMetrics.revenueAtRisk}</strong><br/>Revenue at risk</div>
    <div><strong>${demoData.portfolioMetrics.openWork}</strong><br/>Open work</div>
    <div><strong>${demoData.portfolioMetrics.recoveryPipeline}</strong><br/>Recovery pipeline</div>
    <div><strong>${demoData.portfolioMetrics.productivity}</strong><br/>Productivity</div>
  `;
}

function renderMondayMorning() {
  mondayPanel.innerHTML = `
    <strong>${demoData.mondayMorning.vp}</strong>
    <ul>${demoData.mondayMorning.brief.map((line) => `<li>${line}</li>`).join("")}</ul>
  `;
}

function renderOrganizations() {
  organizationList.innerHTML = "";
  demoData.organizations.forEach((organization, index) => {
    const item = document.createElement("button");
    item.className = `queue-item${index === 0 ? " is-active" : ""}`;
    item.innerHTML = `<strong>${organization.name}</strong><p>${organization.summary}</p>`;
    item.addEventListener("click", () => {
      document.querySelectorAll("#organizationList .queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderOrganization(organization);
    });
    organizationList.appendChild(item);
  });
}

function renderOrganization(organization) {
  roleList.innerHTML = "";
  organization.roles.forEach((roleEntry, index) => {
    const item = document.createElement("button");
    item.className = `queue-item${index === 0 ? " is-active" : ""}`;
    item.innerHTML = `<strong>${roleEntry.role}</strong><p>${roleEntry.queue} queued item(s)</p>`;
    item.addEventListener("click", () => {
      document.querySelectorAll("#roleList .queue-item").forEach((node) => node.classList.remove("is-active"));
      item.classList.add("is-active");
      renderRole(roleEntry, organization.name);
    });
    roleList.appendChild(item);
  });
  renderRole(organization.roles[0], organization.name);
}

function renderRole(roleEntry, organizationName) {
  recommendationPanel.innerHTML = `
    <strong>${organizationName} · ${roleEntry.role}</strong>
    <p><strong>Task:</strong> ${roleEntry.task}</p>
    <p><strong>Recommendation:</strong> ${roleEntry.recommendation}</p>
  `;
  decisionPanel.innerHTML = `
    <strong>Decision Memory</strong>
    <p>${roleEntry.decision}</p>
  `;
  outcomePanel.innerHTML = `
    <strong>Outcome</strong>
    <p>${roleEntry.outcome}</p>
  `;
}

function renderSimulator(specialty, headcount, maturity) {
  const urgency = maturity === "fragmented" ? "high" : maturity === "scaled" ? "low" : "medium";
  simulatorPanel.innerHTML = `
    <strong>${specialty} acquisition plan</strong>
    <p><strong>Headcount:</strong> ${headcount}</p>
    <p><strong>Workflow maturity:</strong> ${maturity}</p>
    <p><strong>Operational gaps:</strong> ${specialty} work is likely running across disconnected systems with ${urgency} standardization urgency.</p>
    <p><strong>Standardization opportunities:</strong> Stand up workflow definitions, assign queue ownership, and track decision memory across the acquired operator.</p>
    <p><strong>Deployment plan:</strong> Map the workflow, import tasks, assign users, and begin measuring financial result plus resolution time.</p>
  `;
}
