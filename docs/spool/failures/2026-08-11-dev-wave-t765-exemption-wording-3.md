---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t765-exemption-wording
seq: 3
---

## 新規

### {{F:non-nfc-line-invalidates-codex-run}}. repo 内のたった 2 行の非 NFC 文字が、それを読んだ Codex 子の成果物を丸ごと捨てさせる [恒真ゲート] [手順漏れ]

- 事象: 段 3 の敵対レンズ 1 本が `codex_exit_code=0`、`validator_rc=0`、rollout 健全
  (`session_meta=1` / `turn_context=1` / model・effort・cwd 一致)、成果物 10,488 bytes 完全
  (`check_codex_output.py` rc=0) でありながら、receipt が `evidence_status=invalid` /
  `accepted=false` / `launcher_rc=1` になり `-o` の成果物が書かれなかった。784 秒・入力 237 万 token。
- 根本原因: `tools/codex_worker_launch.py` の stdout 解析は **JSONL が Unicode NFC であることを要求**する。
  子が `grep` で読んだ行に分解済みの「プ」(U+30D5 + U+309A) が含まれており、
  `item.completed` (command_execution) の event 行が非 NFC になって `stdout_invalid` が立った。
  出典は **repo の tracked file 全体でわずか 2 行** —
  `orchestrator/tests/test_check_docs.py:4442` と `:4465` の `プレースホルダ`。
  この 2 行を出力に含めた子は、内容や品質と無関係に必ず不採用になる。
  症状は F217 と同じだが原因は別で、F217 の再発検知手順 (web 検索イベントの重複キー) では検出できない。
- 恒久対応: 当該 2 行を NFC へ正規化する ({{T:normalize-non-nfc-test-literals}}、実装面のため Codex author が必要)。
  併せて非 NFC 行を拒否する repo 全体の機械検査を `tools/check_docs.py` へ入れるかを同タスクで裁定する
  (入れれば混入時点で赤になり、子を走らせてから捨てる無駄が構造的に消える)。
- 再発検知: `evidence_status=invalid` を見たら、`attempt-*.events.jsonl` の各行へ
  `unicodedata.normalize("NFC", line) != line` を当てて非 NFC 行を特定する。
  該当があれば本 F、`web_search` の重複キーなら F217。
  repo 側は `git ls-files` の全 tracked file に同じ判定を当てれば 2 秒で棚卸しできる。

## supersede 追記

- F217 **supersede: 2026-08-11** — `evidence_status=invalid` の原因は web 検索の重複キーだけではない。同症状で原因が非 NFC 行の例を {{F:non-nfc-line-invalidates-codex-run}} に記録した。invalid を見たら両方を判定する。
