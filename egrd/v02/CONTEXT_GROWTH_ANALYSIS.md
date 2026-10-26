# Forty real requests, three prevented generations

Source: original private Notebook 140785918/v 1 archive
`90226b7c…b811d3`, CRC/SHA verified. `REQUEST_TIMELINE.json` contains all 40 actual
requests and three separate rejection records with exact wire/journal line
references. Three 14297 sessions remain NOT_RUN/null; they are not failures.

| Arm | Sent | Initial input | Last sent input | Rejected next input | Growth initial→rejection |
|---|---:|---:|---:|---:|---:|
| A EGR | 20 | 2199 | 13802 | 15607 | 13408 |
| B MEER | 12 | 2999 | 14702 | 15684 | 12685 |
| C advisory | 8 | 2999 | 11535 | 15989 | 12990 |

All 40 counters equal actual prompt usage. There are 303244 prompt+11090 completion
=314334 received tokens. All 40 responses finish tool_calls; maximum completion
2920. No response has a length finish. Per-response thinking usage is not
separately available. This is one completed task, not 40 independent repair trials.

## Identifiable growth, without fabricated token decomposition

Every admitted transition adds exactly an assistant/tool message pair. The
aggregate token delta is observed. It can be linked to the preceding tool
interaction, but cannot be split into source-output versus assistant reasoning,
call arguments, tool framing or template contributions without exact replay.

| Arm | Read-file-associated whole-turn growth | Other whole-turn growth | Qualification |
|---|---:|---:|---|
| A | 4098 /13408(30.56%) | 9310 | Includes scratch read as well as implementation reads |
| B | 8839 /12685(69.68%) | 3846 | Includes assistant generation and framing, not 8839 isolated source tokens |
| C | 11726 /12990(90.27%) | 1264 | Same combined-turn limitation; terminal read pair contributes 4454 |

Canonical serialized message characters in the **last sent** requests:

| Arm | System | Normal task user | Assistant history | Tool history | Tool-schema chars |
|---|---:|---:|---:|---:|---:|
| A | 5260 | 2300 | 27626 | 25951 | 3336 |
| B | 6613 | 2300 | 14256 | 37123 | 5325 |
| C | 6613 | 2300 | 9495 | 27739 | 5325 |

These are exact canonical JSON **character counts**, not model tokens or
semantic information. Tool payloads are the largest serialized message-role
category in B/C; token dominance is not separately proven. Reasoning can have
multiple provider representations, some possibly ignored by the template.

The fixed Skill package adds 800 initial counted tokens: identical B/C first
messages and tool schemas, identical normal task input across arms, A 2199 versus
B/C 2999. This is 5.21% of the 15360 input allowance. It identifies combined
instruction/schema overhead; it does not divide that 800 between descriptions
and schemas or explain all later differences.

## Negative findings that constrain the intervention

- No compaction, summary-generation or Issue-restoration event; no message
  insertion duplication. Ordinary ever-longer replay is observed.
- Thirteen read windows return 1833 lines: C750 with 0 same-path overlap, B750 with
  1 overlap line, A333 with 0 overlap (33 are scratch). A generic repeated-read cache
  is therefore not supported as the principal remedy for this cohort.
- At the first post-implementation-read measured input, B/C both use 5906 tokens.
  Subsequent growth to rejection is 9778/10083 tokens. This baseline is the next
  observed request after the read, not a fabricated count at the read timestamp.
- A spends its first 120.959 seconds in scratch investigation; first implementation
  excerpt appears at 124.921 seconds and first read_file window at 133.008 seconds.
  Its diagnosis cost is qualitatively different from B/C's source-reading cost.

Which evidence could be omitted safely is not established by size alone.
Exact duplicate elision would recover little observed read content. Shrinking
windows, pruning old evidence or summarizing would require preserving the Issue,
source-version provenance and adverse observations, and then testing repair
outcomes; none is implemented or claimed successful here.
