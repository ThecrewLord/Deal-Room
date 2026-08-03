# Week 1 Project Charter

## Project Information

**Project Name:** Collaborating Opportunities (Deal Room)  
**Company:** Dataeko.AI

---

# Why This Project

The **Deal Room** project tests core engineering disciplines, including data modeling, business-rule enforcement, and usability under real-world constraints rather than open-ended exploration.

Its primary failure mode is **Proof of Concept (POC) engagements drifting without written exit criteria**, resulting in projects continuing indefinitely without a defined measure of success, failure, or closure.

This project addresses that issue by designing a structured system that enforces clear business processes while also demonstrating sound engineering decisions. The three-person team structure naturally aligns with implementation, data management, and project delivery responsibilities.

---

# Team & Roles

| Role | Team Member |
|------|-------------|
| **Team Lead** | ya Narayan Gour |
| **Build Owner** | Rajdeep Singh Sidhu |
| **Data & Quality Owner** | Deekshitha Karri |
| **Mentor(s)** | Phanee / Shwetha |

---

# Problem Statement

Dataeko's commercial team currently manages OEM partnerships and sales opportunities using informal processes without a centralized system of record.

The most significant issue is that **POCs begin without documented exit criteria**, causing them to remain active indefinitely because there is no agreed definition of success, failure, or completion.

The Deal Room application provides a unified platform to manage:

- Customer Accounts
- Sales Opportunities
- Pipeline Progress
- Stakeholders
- OEM Partnerships
- Proof of Concept (POC) Tracking

A mandatory POC exit-criteria workflow ensures every POC has measurable objectives before it begins, preventing project drift by design instead of relying on manual discipline.

---

# Project Scope

## In Scope

- Account Management
- Opportunity Management
- Sales Pipeline Management
- Forecast Tracking
- Stage Ageing
- Stalled Deal Detection
- Stakeholder Mapping
- Activity Logging
- POC Tracker with Mandatory Exit Criteria
- OEM Partner Registry
- Pipeline Dashboard

## Out of Scope

- Email Integration
- Calendar Synchronization
- Quote Generation
- Proposal Generation
- Contract & E-signature Workflows
- Marketing Automation
- Website Activity Lead Scoring

---

# Success Metrics

The project will be considered successful when the following objectives are achieved:

- Dashboard forecast and conversion metrics exactly reconcile with a dataset containing **150+ opportunity records**.
- **100%** of newly created POCs include:
  - Written exit criteria
  - Measurable success metrics
  - System-enforced validation
- Successfully load and document:
  - **80+ Accounts**
  - **150+ Opportunities**
  - **3–6 Stakeholders per Opportunity**
  - **30+ POC Records**
- Verify stalled-deal detection against **10+ manually validated cases**.
- Demonstrate optimistic concurrency handling during live usage.
- Allow commercial users to complete the full **Opportunity + POC creation workflow in under 3 minutes**.

---

# Key Risks & Mitigation Strategies

| Risk | Mitigation |
|------|------------|
| Pipeline calculations become inconsistent | Document every calculation formula and validate results against manually calculated samples before Week 8. |
| Stalled-deal detection is subjective | Make stage-ageing thresholds configurable while providing documented default values. |
| Mandatory exit criteria reduce usability | Keep the POC form concise, structured, and validate usability before finalizing enforcement. |
| Concurrent updates cause data conflicts | Implement a documented **Last-Write-Wins** strategy with visible **Last Updated By** and **Last Updated At** information for users. |

---

# Expected Outcome

The Deal Room will provide a centralized collaboration platform that improves visibility into the commercial pipeline, standardizes opportunity management, enforces structured POC governance, and enables accurate forecasting while reducing manual coordination and process ambiguity.
