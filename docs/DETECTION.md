# Detection and scoring

Detection is deterministic and runs synchronously before an event is committed, so every stored score is explainable.

| Signal | Rule ID | Score |
|---|---|---:|
| Five authentication failures in 60 seconds | `AUTH-BRUTE-001` | 55 |
| `wget`, `curl`, `chmod`, script, or reverse-shell token | `SSH-CMD-*` | 30-60 |
| Credential/secret path or command | `CRED-ACCESS-001` | 40 |
| Sensitive web path (higher after three probes) | `WEB-SCAN-001` | 20/35 |
| SQL injection expression | `WEB-SQLI-001` | 55 |
| Encoded or plain path traversal | `WEB-TRAV-001` | 50 |
| HTTP command-injection metacharacters | `WEB-CMDI-001` | 55 |
| Recognized scanner user agent | `WEB-UA-001` | 25 |
| Thirty HTTP requests in 60 seconds | `WEB-RATE-001` | 45 |

The event score is the strongest matched signal plus 35% of every additional signal (each contribution rounded), capped at 100. This prevents many weak indicators from overwhelming one strong signal while still rewarding corroboration. Severity is LOW 0-29, MEDIUM 30-59, HIGH 60-79, or CRITICAL 80-100.

Events with detections are correlated into an unresolved incident sharing source IP within a rolling 15-minute window. A new incident begins with the event score. Later events retain the maximum existing/event score and add `min(10, 2 * matched_rules)`; the result remains capped at 100. Attack types are a sorted union of observed detections.

Alerts are created for scores of at least 80 or a brute-force incident. An existing unresolved alert is updated rather than duplicated.
