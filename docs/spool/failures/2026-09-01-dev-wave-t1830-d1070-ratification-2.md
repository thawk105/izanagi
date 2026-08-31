---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t1830-d1070-ratification
seq: 2
---

## 再発

### F43

- **再発: 2026-09-01** — 段 3 敵対相談の親 prompt が、出力形式節で必須見出しを
  `### 総括` (level 3) と指定した。子は指定どおり level 3 で書いて完走したが
  (`codex_exit_code=0`、`output_bytes=7755`、model call 58、wall 1072 秒)、
  `check_codex_output.py` は `^## 総括` を要求するため `f43_fragment` で不受理になった。
  子の欠陥ではなく親の指定ミスであり、`DW-O01` の `## 総括` を**見出し level の要求**として
  読まなかったことが原因である。過去の再発は「fence の内側へ置いた」「太字表記で代替した」で、
  いずれも fence 位置と表記の問題だったが、本件は**親が level を明示的に誤指定した**点が新しい。
  出力形式節に `### 総括` と書けば、子が忠実に従うほど確実に全損する。
  親側の是正は、出力形式へ `見出し level 2 (##) で書く` と `fence の外に置く` を併記すること。
  再投入は prompt を直して別 job-id で行い、初回の出力は非採用として artifact dir へ保全した
  (2 本目は `check_codex_output.py` rc=0 で採用)。
