---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1219-carry-same-id
seq: 2
---

## 新規

### {{F:mutation-nodeid-nonascii}}. parametrize の表示 ID に非 ASCII があると変異登録が構造的に不可能になる [手順漏れ] [道具の射程誤認]

- 事象: 段 6 の変異事前登録で
  `mutation harness aborted: 期待 node が pytest collection に実在しない` が出た。
  対象は `test_backlog_guard_carry_candidate_parse_break_is_positive_control[[T-999] 変わらず ( (73) 参照)]`
  と `test_backlog_guard_carry_target_index_states_are_distinct[missing-missing-索引 key 不在-...]` の 2 件。
  nodeid は実在し、pytest collection にも出ている。
- 根本原因: `tools/run_tests.py` は子プロセスの出力を中継するとき非 ASCII を `\uXXXX` へ
  エスケープする。`tools/mutation_harness.py` の `_collected_nodes()` はその中継出力から
  collected node を読むため、harness が見る nodeid はエスケープ済み文字列になる。
  実文字で登録すれば一致せず、エスケープ形で登録すれば中継実装の表現を凍結 artifact へ
  焼き込むことになる。**parametrize id に日本語を使うと、その test は変異の証拠に使えない。**
- 恒久対応: 変異で殺す対象にする parametrized test には
  `pytest.param(..., id="ascii-only-id")` で ASCII 英小文字・数字・ハイフンだけの明示 id を付ける。
  値・assertion・case 数は変えず表示 id だけを変える。実体は本 wave の
  `orchestrator/tests/test_check_docs.py` の 3 つの parametrized test
  (`carry_candidate_parse_break_is_positive_control` / `carry_target_index_states_are_distinct` /
  `carry_index_failures_count_every_occurrence`) に入れた ASCII id と、
  memory `mutation-expected-nodes-must-be-ascii`。
- 再発検知: 段 4 の変異事前登録で `expected_nodes` を確定した直後に
  `all(n.isascii() for n in expected_nodes)` を確認する。本 wave はこの検査を spec 生成時に置き、
  非 ASCII 0 件を機械確認してから投入した。

### {{F:codex-max-attempts-sandbox-coupling}}. workspace-write の codex 子に --max-attempts を付けると起動前に即死する [手順漏れ]

- 事象: 段 5 の実装子が 1 度も起動せず rc=2 で終わった。
  `dev_wave_codex.py: error: --max-attempts > 1 は --sandbox read-only のときだけ許可される`。
  `.done` には 2 が入り、待ち手は `stage=producer-files rc=70` を返した。
- 根本原因: 書き込みを伴う子を再試行すると同じ編集を二度なぞることになるため、
  launcher が argv 段階で拒否する。この制約は `DW-O01` の argv 記述にも起動例にも無く、
  read-only 段で F217 の flake を launcher に吸わせる目的で `--max-attempts 2` を
  付ける運用が、そのまま author / fix 段へ持ち込まれた。
- 恒久対応: read-only の段 (plan / consult / review) にだけ `--max-attempts` を付ける。
  author / fix は失敗したら新しい job-id と新しい `.done` で親が投げ直す。
  実体は memory `dev-wave-max-attempts-is-read-only-only` と、
  本 wave の起動 script の注記行。
- 再発検知: 起動 script に `--max-attempts` を書く時点で `--sandbox` の値を見る。
  `workspace-write` なら書かない。

## 再発

### F217

- **再発: 2026-08-26** — 段 2 のプラン子が `codex_exit_code=0` / `validator_rc=0` /
  出力 16,458 bytes / 51 model call / 893 秒 / 入力 7.69M token で完走したのに
  `evidence_status=invalid` / `accepted=false` になった。
  **既知 2 原因を両方とも反証した** — `web_search` イベントは 0 件 (prompt で明示禁止済み)、
  出力は `is_NFC=True` で結合文字 0 件。親が独立に検証した証跡もすべて正常だった
  (session_meta 1 / turn_context 1 / model・effort・cwd 一致 / rollout 391 行・events 131 行とも
  不正 JSON 0・非 UTF-8 0・最長行 153,811 と 55,427 で上限 4MiB 未満・末尾改行あり /
  token_count 51 件すべて info 正常・非単調 0)。
  2026-08-25 の再発項が言う「invalid は最終 artifact の性質ではなく tailing 中に立った
  sticky flag であり、第 3 の原因が存在する」の**独立 2 例目**である。
  本 wave では同じ prompt のまま `--max-attempts 2` で再投入し、1 回目の attempt で受理された
  (16 model call / 624 秒 / 入力 1.33M token)。**縮約を要さずに通ったので、
  2026-08-25 の「回避できた手段は prompt の縮約だけ」も因果ではない可能性が上がった。**
  read-only 段では launcher 自身の再試行が有効な回避策になる。
