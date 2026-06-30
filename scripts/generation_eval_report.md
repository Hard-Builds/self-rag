# Generation Evaluation Report

**Date:** 2026-06-30  
**User:** `019eee25-3f42-73ec-9374-a54c54d168ad`  
**LLM (generator + judge):** `gemini-3.1-flash-lite`  
**Embedding model:** `models/gemini-embedding-001`  
**Test set:** 20 queries  
**Retrieval Top-K:** 5  

---

## Summary

| Metric | Score |
|---|---|
| **Faithfulness** | 1.0000 |
| **Answer Relevance** | 0.9850 |
| Fully faithful (≥0.9) | 20 / 20 |
| Fully relevant (≥0.9) | 19 / 20 |

> **Faithfulness** measures whether each claim in the generated answer is grounded in the retrieved context (0 = hallucinated, 1 = fully grounded).  
> **Answer Relevance** measures whether the generated answer actually addresses the question (0 = off-topic, 1 = fully responsive).

---

## Results by Category

### Company Overview  (4 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 1.0000 |

### HR Policy  (4 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 0.9250 |

### Leadership  (2 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 1.0000 |

### Pricing  (5 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 1.0000 |

### Product  (4 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 1.0000 |

### Workplace Conduct  (1 queries)

| Metric | Score |
|---|---|
| Avg Faithfulness | 1.0000 |
| Avg Answer Relevance | 1.0000 |

---

## Per-Query Results

| # | Question | Faithfulness | Answer Relevance | Relevance Assessment |
|---|---|---|---|---|
| 1 | How many annual leave days are employees entitled to at NexaAI? | 1.00 | 1.00 | The answer directly and clearly provides the specific number of annual leave day |
| 2 | What is the maximum number of unused annual leave days that can be carried  | 1.00 | 0.70 | The answer provides a specific numerical limit for carrying forward annual leave |
| 3 | How many sick leave days per year does NexaAI provide to its employees? | 1.00 | 1.00 | The answer directly and concisely provides the specific number of sick leave day |
| 4 | What disciplinary actions can NexaAI take for policy violations? | 1.00 | 1.00 | The answer directly and concisely lists the disciplinary actions NexaAI can take |
| 5 | How often does NexaAI conduct performance reviews? | 1.00 | 1.00 | The answer directly and concisely addresses the frequency of NexaAI's performanc |
| 6 | When was NexaAI Solutions founded and where is it headquartered? | 1.00 | 1.00 | The answer directly and accurately provides the founding year and headquarters l |
| 7 | Which industries does NexaAI primarily serve? | 1.00 | 1.00 | The answer directly identifies the primary industries served by NexaAI as reques |
| 8 | Who founded NexaAI and what is their background? | 1.00 | 1.00 | The answer directly identifies the founder and provides a concise summary of his |
| 9 | Who is the CTO of NexaAI and what is their area of expertise? | 1.00 | 1.00 | The answer directly identifies the CTO and their area of expertise as requested. |
| 10 | In which regions does NexaAI currently operate? | 1.00 | 1.00 | The answer directly identifies the specific regions where NexaAI operates as req |
| 11 | What is NexaChat and what problem does it solve? | 1.00 | 1.00 | The answer clearly defines what NexaChat is and explicitly identifies the proble |
| 12 | What file types does NexaChat support for document querying? | 1.00 | 1.00 | The answer directly lists the supported file types, providing a clear and concis |
| 13 | What is the monthly price per user for the Starter Plan? | 1.00 | 1.00 | The answer directly and accurately provides the specific monthly price per user  |
| 14 | What products are included in the Growth Plan? | 1.00 | 1.00 | The answer directly and completely lists the products included in the Growth Pla |
| 15 | What discount does NexaAI offer for annual billing? | 1.00 | 1.00 | The answer directly and accurately addresses the question regarding the specific |
| 16 | What query limit does the Starter Plan enforce per month? | 1.00 | 1.00 | The answer directly and accurately addresses the specific query limit for the St |
| 17 | What is NexaSupport and what channels does it support? | 1.00 | 1.00 | The answer accurately defines NexaSupport and lists the specific communication c |
| 18 | What makes NexaSecure useful for regulated industries? | 1.00 | 1.00 | The answer directly addresses the question by identifying the specific features  |
| 19 | What support level is included in the Enterprise Plan? | 1.00 | 1.00 | The answer directly and accurately addresses the question regarding the support  |
| 20 | What are the core values of NexaAI Solutions? | 1.00 | 1.00 | The answer directly and completely lists the core values of the specified compan |

---

## Detailed Results

### 1. How many annual leave days are employees entitled to at NexaAI?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> Employees are entitled to 18 working days of annual leave per year.

**Reference answer:**
> Employees at NexaAI are entitled to 18 working days of annual leave per year.

**Claim breakdown:**

- ✓ Employees are entitled to 18 working days of annual leave per year.

**Relevance assessment:** The answer directly and clearly provides the specific number of annual leave days for NexaAI employees.

---

### 2. What is the maximum number of unused annual leave days that can be carried forward?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 0.70

**Generated answer:**
> Unused annual leave may be carried forward up to 30 days.

**Reference answer:**
> Unused annual leave may be carried forward up to 30 days.

**Claim breakdown:**

- ✓ Unused annual leave may be carried forward up to 30 days.

**Relevance assessment:** The answer provides a specific numerical limit for carrying forward annual leave, though it lacks context regarding the specific jurisdiction or policy to which this rule applies.

---

### 3. How many sick leave days per year does NexaAI provide to its employees?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI provides 10 working days of sick leave per year.

**Reference answer:**
> NexaAI provides 10 working days of sick leave per year.

**Claim breakdown:**

- ✓ NexaAI provides 10 working days of sick leave per year.

**Relevance assessment:** The answer directly and concisely provides the specific number of sick leave days offered by NexaAI.

---

### 4. What disciplinary actions can NexaAI take for policy violations?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI can take the following disciplinary actions for policy violations:  \n> * Written warning  \n> * Suspension  \n> * Termination of employment in severe cases

**Reference answer:**
> NexaAI may issue a written warning, impose a suspension, or terminate employment in severe cases.

**Claim breakdown:**

- ✓ NexaAI can take the following disciplinary actions for policy violations: Written warning
- ✓ NexaAI can take the following disciplinary actions for policy violations: Suspension
- ✓ NexaAI can take the following disciplinary actions for policy violations: Termination of employment in severe cases

**Relevance assessment:** The answer directly and concisely lists the disciplinary actions NexaAI can take for policy violations as requested.

---

### 5. How often does NexaAI conduct performance reviews?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI conducts performance reviews on a bi-annual basis.

**Reference answer:**
> NexaAI conducts bi-annual (twice a year) performance reviews.

**Claim breakdown:**

- ✓ NexaAI conducts performance reviews on a bi-annual basis.

**Relevance assessment:** The answer directly and concisely addresses the frequency of NexaAI's performance reviews.

---

### 6. When was NexaAI Solutions founded and where is it headquartered?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI Solutions was founded in 2021 and is headquartered in Bengaluru, India.

**Reference answer:**
> NexaAI Solutions was founded in 2021 and is headquartered in Bengaluru, India.

**Claim breakdown:**

- ✓ NexaAI Solutions was founded in 2021.
- ✓ NexaAI Solutions is headquartered in Bengaluru, India.

**Relevance assessment:** The answer directly and accurately provides the founding year and headquarters location for NexaAI Solutions.

---

### 7. Which industries does NexaAI primarily serve?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI primarily serves mid-sized and large organizations across the technology, finance, healthcare, and education sectors.

**Reference answer:**
> NexaAI primarily serves mid-sized and large organizations in the technology, finance, healthcare, and education sectors.

**Claim breakdown:**

- ✓ NexaAI primarily serves mid-sized and large organizations across the technology, finance, healthcare, and education sectors.

**Relevance assessment:** The answer directly identifies the primary industries served by NexaAI as requested.

---

### 8. Who founded NexaAI and what is their background?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> Aarav Mehta founded NexaAI. He has over 10 years of experience in enterprise data platforms and cloud infrastructure, and he previously worked with global consulting firms where he led multiple large-scale digital transformation projects.

**Reference answer:**
> NexaAI was founded by Aarav Mehta, who has over 10 years of experience in enterprise data platforms and cloud infrastructure. He previously worked with global consulting firms leading large-scale digital transformation projects.

**Claim breakdown:**

- ✓ Aarav Mehta founded NexaAI.
- ✓ He has over 10 years of experience in enterprise data platforms and cloud infrastructure.
- ✓ He previously worked with global consulting firms where he led multiple large-scale digital transformation projects.

**Relevance assessment:** The answer directly identifies the founder and provides a concise summary of his professional background as requested.

---

### 9. Who is the CTO of NexaAI and what is their area of expertise?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The CTO of NexaAI is Riya Kapoor, and her area of expertise is distributed systems and AI platforms.

**Reference answer:**
> Riya Kapoor is the CTO of NexaAI, with expertise in distributed systems and AI platforms.

**Claim breakdown:**

- ✓ The CTO of NexaAI is Riya Kapoor.
- ✓ Riya Kapoor's area of expertise is distributed systems and AI platforms.

**Relevance assessment:** The answer directly identifies the CTO and their area of expertise as requested.

---

### 10. In which regions does NexaAI currently operate?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI operates in India, Southeast Asia, and Europe.

**Reference answer:**
> NexaAI operates in India, Southeast Asia, and Europe.

**Claim breakdown:**

- ✓ NexaAI operates in India, Southeast Asia, and Europe.

**Relevance assessment:** The answer directly identifies the specific regions where NexaAI operates as requested.

---

### 11. What is NexaChat and what problem does it solve?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaChat is an AI-powered internal assistant that allows employees to query company documents, policies, reports, and knowledge bases using natural language. It is designed to reduce the time spent searching for information and ensure consistent, citation-backed answers across the organization.

**Reference answer:**
> NexaChat is an AI-powered internal knowledge assistant that allows employees to query company documents, policies, reports, and knowledge bases using natural language. It reduces time spent searching for information and ensures consistent, citation-backed answers across the organization.

**Claim breakdown:**

- ✓ NexaChat is an AI-powered internal assistant that allows employees to query company documents, policies, reports, and knowledge bases using natural language.
- ✓ It is designed to reduce the time spent searching for information and ensure consistent, citation-backed answers across the organization.

**Relevance assessment:** The answer clearly defines what NexaChat is and explicitly identifies the problems it solves, such as information retrieval time and consistency.

---

### 12. What file types does NexaChat support for document querying?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaChat supports PDFs, Word documents, presentations, and web pages.

**Reference answer:**
> NexaChat supports PDFs, Word documents, presentations, and web pages.

**Claim breakdown:**

- ✓ NexaChat supports PDFs, Word documents, presentations, and web pages.

**Relevance assessment:** The answer directly lists the supported file types, providing a clear and concise response to the question.

---

### 13. What is the monthly price per user for the Starter Plan?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The monthly price for the Starter Plan is ■2,499 per user.

**Reference answer:**
> The Starter Plan is priced at 2,499 per user per month.

**Claim breakdown:**

- ✓ The monthly price for the Starter Plan is ■2,499 per user.

**Relevance assessment:** The answer directly and accurately provides the specific monthly price per user for the Starter Plan as requested.

---

### 14. What products are included in the Growth Plan?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The Growth Plan includes access to NexaChat, NexaInsight, and NexaSupport.

**Reference answer:**
> The Growth Plan includes access to NexaChat, NexaInsight, and NexaSupport, along with advanced analytics, third-party integrations, and priority support.

**Claim breakdown:**

- ✓ The Growth Plan includes access to NexaChat, NexaInsight, and NexaSupport.

**Relevance assessment:** The answer directly and completely lists the products included in the Growth Plan as requested.

---

### 15. What discount does NexaAI offer for annual billing?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaAI offers a 15% discount for annual billing.

**Reference answer:**
> NexaAI offers a 15% discount for annual billing.

**Claim breakdown:**

- ✓ NexaAI offers a 15% discount for annual billing.

**Relevance assessment:** The answer directly and accurately addresses the question regarding the specific discount percentage offered by NexaAI for annual billing.

---

### 16. What query limit does the Starter Plan enforce per month?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The Starter Plan enforces a limit of up to 5,000 queries per month.

**Reference answer:**
> The Starter Plan allows up to 5,000 queries per month.

**Claim breakdown:**

- ✓ The Starter Plan enforces a limit of up to 5,000 queries per month.

**Relevance assessment:** The answer directly and accurately addresses the specific query limit for the Starter Plan.

---

### 17. What is NexaSupport and what channels does it support?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaSupport is an AI-driven customer support solution that automates responses to common customer queries while escalating complex issues to human agents. It supports multi-channel support, including chat, email, and web.

**Reference answer:**
> NexaSupport is an AI-driven customer support solution that automates responses to common queries and escalates complex issues to human agents. It supports multi-channel interactions including chat, email, and web.

**Claim breakdown:**

- ✓ NexaSupport is an AI-driven customer support solution that automates responses to common customer queries while escalating complex issues to human agents.
- ✓ It supports multi-channel support, including chat, email, and web.

**Relevance assessment:** The answer accurately defines NexaSupport and lists the specific communication channels it supports as requested.

---

### 18. What makes NexaSecure useful for regulated industries?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> NexaSecure is useful for regulated industries because it provides an AI governance layer that ensures secure, compliant, and auditable usage of AI systems across the organization. It includes features such as role-based access, document permissions, query logging, audit trails, data residency and compliance controls, and policy-based response filtering.

**Reference answer:**
> NexaSecure provides role-based access and document permissions, query logging and audit trails, data residency and compliance controls, policy-based response filtering, and integration with enterprise IAM systems — making it well-suited for compliance-heavy regulated industries.

**Claim breakdown:**

- ✓ NexaSecure is useful for regulated industries.
- ✓ NexaSecure provides an AI governance layer that ensures secure, compliant, and auditable usage of AI systems across the organization.
- ✓ NexaSecure includes role-based access.
- ✓ NexaSecure includes document permissions.
- ✓ NexaSecure includes query logging.
- ✓ NexaSecure includes audit trails.
- ✓ NexaSecure includes data residency and compliance controls.
- ✓ NexaSecure includes policy-based response filtering.

**Relevance assessment:** The answer directly addresses the question by identifying the specific features and governance capabilities that make NexaSecure suitable for regulated environments.

---

### 19. What support level is included in the Enterprise Plan?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The Enterprise Plan includes 24x7 support with SLA.

**Reference answer:**
> The Enterprise Plan includes 24x7 support with SLA, a dedicated customer success manager, and quarterly security and compliance reviews.

**Claim breakdown:**

- ✓ The Enterprise Plan includes 24x7 support with SLA.

**Relevance assessment:** The answer directly and accurately addresses the question regarding the support level included in the Enterprise Plan.

---

### 20. What are the core values of NexaAI Solutions?

**Faithfulness:** 1.00 &nbsp; **Answer Relevance:** 1.00

**Generated answer:**
> The core values of NexaAI Solutions are:  \n>   \n> *   **Customer Obsession** – Every solution starts with a real business pain point.  \n> *   **Transparency** – Clear communication with customers and within teams.  \n> *   **Accountability** – Ownership of outcomes, not just tasks.  \n> *   **Security First** – Data protection is non-negotiable.  \n> *   **Continuous Improvement** – Iterate, learn, and improve relentlessly.

**Reference answer:**
> NexaAI's core values are: Customer Obsession (solutions start with real business pain points), Transparency (clear communication internally and externally), Accountability (ownership of outcomes), Security First (data protection is non-negotiable), and Continuous Improvement (iterate, learn, and improve relentlessly).

**Claim breakdown:**

- ✓ The core values of NexaAI Solutions are Customer Obsession, Transparency, Accountability, Security First, and Continuous Improvement.
- ✓ Customer Obsession means every solution starts with a real business pain point.
- ✓ Transparency means clear communication with customers and within teams.
- ✓ Accountability means ownership of outcomes, not just tasks.
- ✓ Security First means data protection is non-negotiable.
- ✓ Continuous Improvement means iterate, learn, and improve relentlessly.

**Relevance assessment:** The answer directly and completely lists the core values of the specified company as requested.

---

## Analysis

### Faithfulness

Average faithfulness of **1.00** means roughly 100% of all generated claims are grounded in the retrieved context.  
**20/20** queries produced fully faithful answers (score ≥ 0.9).  
### Answer Relevance

Average relevance of **0.98** indicates the model consistently addresses the question.  
**19/20** queries received fully relevant answers (score ≥ 0.9).  
### Recommendations

| Priority | Issue | Recommendation |
|---|---|---|
| **Low** | Both metrics strong (≥0.9) | Consider expanding the test set with adversarial questions to stress-test edge cases |
