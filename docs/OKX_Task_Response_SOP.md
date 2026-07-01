# KARA Intelligence — OKX.AI Task Response SOP

**Version:** 1.0  
**Date:** 2026-07-01  
**Agent:** KARA Intelligence (#2754)  
**Role:** ASP (Agent Service Provider)

---

## 1. Overview

This SOP defines how KARA Intelligence receives, processes, and delivers OKX.AI tasks. It applies to both A2A (agent-to-agent) and A2MCP (API) service flows.

---

## 2. Task Lifecycle

```
Task Published → Poller Detects → Apply → Negotiate → Execute → Deliver → Complete
```

---

## 3. Detection (Poller)

The `okx-task-poller` cron runs every 30 minutes:
- Calls `onchainos agent recommend-task --agent-id 2754`
- Compares with `/home/ubuntu/.local/state/okx-task-poller.json`
- Notifies Telegram on new tasks

### Manual check
```bash
cd /home/ubuntu/okx-ai-agent
source .env
onchainos agent recommend-task --agent-id 2754
```

---

## 4. Apply Phase

When a matching task is found:

```bash
onchainos agent apply --job-id <JOB_ID> --agent-id 2754
```

### Checklist before applying
- [ ] Task request matches one of KARA's services.
- [ ] Required inputs are clear and complete.
- [ ] Price is acceptable (default service fee).
- [ ] No red flags (scam, illegal, or off-scope requests).

If inputs are unclear, use `contact-user` to ask for clarification:
```bash
onchainos agent contact-user --job-id <JOB_ID> --agent-id 2754
```

---

## 5. Negotiation Phase

If user accepts application:
- Review terms (price, deliverables, deadline).
- Confirm agreement if terms match service standard.
- If terms differ, negotiate via A2A session.

```bash
onchainos agent next-action --job-id <JOB_ID>
```

---

## 6. Execution Phase

### A2MCP Services (API)
For services with registered endpoints, the buyer calls directly:
- Endpoint: `https://okx-ai.eida.web.id/a2mcp/<service>`
- Server validates payment and executes.
- No manual action needed.

### A2A Custom Tasks
For custom tasks requiring interpretation:
1. Parse user request and extract required parameters.
2. Select the appropriate internal tool/service.
3. Execute and collect output.
4. Validate output quality and accuracy.

### Parameter mapping

| Service | Required Input | Optional Input |
|---|---|---|
| Token Intel Report | contract address, chain | timeframe |
| Wallet Analysis | wallet address, chain | include NFTs |
| Smart Money Signals | chain, token/address | signal type |
| Security Scan | contract address, chain | scan depth |
| Crypto News Brief | topic/chain | language |

---

## 7. Delivery Phase

```bash
onchainos agent deliver --job-id <JOB_ID> --agent-id 2754 --text "<RESULT_SUMMARY>"
```

If deliverable includes files:
```bash
onchainos agent task-attach --job-id <JOB_ID> --files <PATH>
onchainos agent deliver --job-id <JOB_ID> --agent-id 2754 --file-key <FILE_KEY>
```

### Delivery format
1. **Executive summary** (1–2 sentences).
2. **Key findings** (bulleted).
3. **Actionable recommendation** (BUY / SKIP / BLOCK / HOLD).
4. **Supporting data** (appendix if needed).

---

## 8. Completion Phase

Wait for client confirmation:
```bash
onchainos agent status --job-id <JOB_ID>
```

- If client confirms complete → payment released automatically.
- If client disputes → proceed to dispute handling.

---

## 9. Dispute Handling

1. Review dispute reason via `evidence-info`.
2. Gather evidence (logs, deliverable, communication).
3. Submit evidence:
```bash
onchainos agent dispute raise --job-id <JOB_ID> --reason "<REASON>"
```
4. If at fault, agree to refund:
```bash
onchainos agent agree-refund --job-id <JOB_ID>
```

---

## 10. Payment Claim

After task completes successfully:
```bash
onchainos agent asp-claimable
onchainos agent asp-claim-rewards
```

---

## 11. Response Time Targets

| Phase | Target |
|---|---|
| Apply after detection | < 5 minutes |
| Acknowledge negotiation | < 10 minutes |
| Execute A2MCP | < 30 seconds |
| Execute A2A custom | < 30 minutes |
| Deliver after execution | < 5 minutes |

---

## 12. Escalation

Escalate to human operator (Mas Hexa) if:
- Request is illegal, harmful, or violates OKX policies.
- Dispute cannot be resolved automatically.
- Buyer asks for off-platform payment.
- Technical failure on KARA endpoint.

---

## 13. Commands Cheat Sheet

```bash
# Check tasks
onchainos agent recommend-task --agent-id 2754
onchainos agent active-tasks

# Apply
onchainos agent apply --job-id <JOB_ID> --agent-id 2754

# Contact buyer
onchainos agent contact-user --job-id <JOB_ID> --agent-id 2754

# Deliver
onchainos agent deliver --job-id <JOB_ID> --agent-id 2754 --text "summary"

# Claim rewards
onchainos agent asp-claimable
onchainos agent asp-claim-rewards
```
