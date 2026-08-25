---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1176-t1230-role-diagnosability
seq: 1
---

## 新規

### {{F:codex-event-split-by-line-separator}}. codex 子の完成した成果物が U+2028 / U+2029 で全損する [恒真ゲート] [手順漏れ]

- 事象: 段 2 の plan 子が 6 回連続で `evidence_status=invalid` により不採用になった。
  `codex_exit_code=0`、内容検査 `validator_rc=0`、成果物 17〜24KB が完成していたのに破棄された。
  完成済み成果物 6 本と約 2 時間を失った。F217 の再発だが、今回は根本原因を特定した。
- 根本原因: `tools/codex_worker_launch.py` は子の stdout を
  `orchestrator/codex_roles/events.py` の `parse_jsonl` へ渡す。同関数は bytes を str へ
  decode したのち **`str.splitlines()`** で分割する。これは改行に加えて U+2028
  (LINE SEPARATOR) と U+2029 (PARAGRAPH SEPARATOR) でも分割する。この 2 文字は
  **JSON 文字列内では escape 不要の正当な文字**なので codex は raw のまま出力する。
  正常な 1 event が途中で切られ `Unterminated string` となり `stdout_invalid` が立つ。
  この 2 文字は子が repo のソースを読むと `item.completed` event に載る。
  リテラルで含む tracked file は repo 全体で 2 つあり、**どちらも本 wave の主編集面**
  だった (`orchestrator/campaign/p3_autonomous_workload_trial.py` の制御文字除去正規表現と、
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` のその負例)。
  この 2 file を読む必要のある wave は構造的に全 attempt を失う。
  全 wave の invalid 率が 1142 attempt 中 25 件 (2%) なのに本 wave が 6/6 で失敗した理由である。
  失敗した attempt の rollout と stdout を実物で検査すると最終状態はすべて正常であり
  (改行終端あり、`session_meta` 1 件、`turn_context` 1 件、壊れた行 0 件、byte 数一致)、
  成果物の欠陥ではないことを確認した。
- 恒久対応: 未実施。`{{T:launcher-splitlines-line-separator}}` として裁定パッケージへ送った。
  `parse_jsonl` の `text.splitlines()` を `text.split("\n")` へ変えれば構造的に断てる。
  本 wave で実測した回避策は、該当行を無害化した写しを job dir へ置き、
  子には repo を読ませず写しを読ませることである (行番号を保てば file:line 引用はそのまま使える)。
  7 回目の投入で rc=0 になった。
- 再発検知: 同 T が要求する `text.split("\n")` への変更と、U+2028 / U+2029 を含む
  event 行を受理することの負例テスト。それまでは本エントリを検索して回避策を適用する。

### {{F:mutation-shared-tree-source-repo}}. 変異走行に自分の作業ツリーを渡すと rc=125 で中止する [手順漏れ]

- 事象: `tools/mutation_worktree.py --source-repo` に wave 自身の worktree を渡したところ、
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で中止した (rc=125)。
  投入直後に失敗していたが親が完了通知を待っており、約 4 時間の空転を招いた。
- 根本原因: 作業ツリーは wave 自身の他の処理も触るため、走行前後で観測 bytes が一致しない。
  `DW-M05` は独自 harness の要件を定めるが `--source-repo` に何を渡すかを書いていない。
- 恒久対応: 未実施。`{{T:mutation-source-repo-doc}}` として裁定パッケージへ送った。
  実測で有効な運用は、固定 commit の独立 clone を作って `--source-repo` に渡すことである。
- 再発検知: 同 T が要求する `DW-M05` への 1 行追記。それまでは本エントリを検索する。

## 再発

### F217

- **再発: 2026-08-26** — 段 2 の plan 子が 6 回連続で不採用になった。
  根本原因は {{F:codex-event-split-by-line-separator}} で特定した。以降の調査はそちらを先に読む。
