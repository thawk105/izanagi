# ~/.codex/sessions の掃除と izanagi の依存 (2026-09-30)

- authority: none (測定時点の記録。可変状態の正本は worklog)
- wave: dev-wave-codex-sessions-gc (repo 基準 main 4f412c67b)

## 問い

ユーザーは肥大した `~/.codex/sessions` (20G、12,520 rollout) をほぼ全部消したいが、izanagi が
そこに依存していて消すと壊れるのではと懸念した。依存を調べ、あれば解消し、掃除する。

## 依存の棚卸し (git grep と読解、HEAD 4f412c67b)

rollout を読む経路は 4 つで、いずれも `CODEX_HOME` があればそちらを優先し、無ければ
`~/.codex/sessions` を使う (`tools/codex_worker_launch.py:4980-4984`、
`tools/codex_worker_ledger.py:154-157`、`tools/codex_reasoning_ab.py:12246-12252`)。

| 経路 | 用途 | 古い rollout を消した影響 |
|---|---|---|
| `tools/codex_worker_launch.py` `_discover_rollouts` (:1451) | dev-wave の全 codex 子が**走行中・終了直後の自 session** の rollout を探し、計量と evidence 判定に使う | 無し。ただし走行中の子の rollout を消すと計量欠測・不受理になる。launcher は読むたびに開閉するので「開いている file を残す」では守れない |
| 同 `check-receipt` (:4898、`_check_receipt_paths` :4799) | 受領証に封印された rollout の元の絶対 path を再読し sha256 照合 | repo 内に呼び出し元 0 件 (land・受入・provenance 監査・usage 集計・hooks は rollout を読まない)。手動再検証は退避 tar から元 path へ 1 本戻せば可能 |
| `tools/codex_worker_ledger.py` | 手動の usage 台帳 CLI | 消した期間は 0 として rc=0 で集計される。過去分の再集計を測定値として扱わない |
| `tools/codex_reasoning_ab.py:196-209` | 2026/07/29 の 5 rollout を pin した過去実験の再現 | pin 先は 2026-09-01 の剪定で既に不在 (F773/F776/D1367)。今回の削除は事実を変えない |

テストで実 home を読むのは `orchestrator/tests/test_codex_reasoning_ab.py` の
`test_real_rollout_collector_golden_is_source_bound` (:9283) だけで、固定 path が無ければ sha 照合を飛ばす。
他の codex 系テストは tmp の `CODEX_HOME` を使う。

**挙動での確認:** `CODEX_HOME` を空 dir に向けて codex 系 5 test file
(`test_codex_reasoning_ab.py`、`test_codex_worker_launch.py`、`test_codex_worker_ledger.py`、
`test_codex_jsonl_line_split.py`、`test_codex_worker_launch_budget.py`) を Pegasus 計算ノードで走らせ、
**1003 passed, 2 skipped** (request 37539.nqsv、105 秒)。skip 2 件は tmp を使う guard 自身のテスト側で、実 home とは無関係。

結論: izanagi の自動経路で古い rollout に依存するものは無く、コード変更は要らない。守るべきは走行中の子の rollout だけ。

## 相談 (Codex 2 レンズ、read-only)

- 決定役 (sol): 古い rollout に依存する自動経路なし。直近 3 日を残し、削除対象だけを検証付きで退避してから消す。
- 攻撃役 (luna) で成立した攻撃: (1) 開いている file の保護では走行中の子を守れない、(2) tar の sha だけでは
  受領証が封印した rollout の退避を示せない、(3) ledger は空でも rc=0 で 0 を出す。
  不成立: B-5・K2 の原本が rollout にしかない (両者とも逐語を repo 内に保存)、reasoning A/B の pin を新たに壊す。
- 採否: (1) は「削除対象に直近 2 日以内の更新が 0 件」と「日付 dir を 9/28 以降残す」で担保 (launcher は子を既定 3,600 秒で打ち切る)。
  (2) は受領証参照を封印 sha と照合。(3) は退避物の README に明記。

## 実施

- 残した: `2026/09/28`〜`2026/09/30` (619 file、686M)。
- 退避: `/work/1/SFC/tanab/archive/codex-sessions-2026-09-30/` (repo 外、所有者のみ読取)。
  `2026/08/01`〜`2026/09/27` の 54 dir・11,918 file・19,816,174,380 bytes を zstd tar 1 本 (2,876,453,187 bytes、
  sha256 `454e1cd69b0d901c091b0d37946010043b97f631e508c645dba8816015e2abd5`) にし、file 別 sha256 を記録。
  tar を展開して全件照合し一致 (request 37665.nqsv)。
- 受領証参照の照合: repo の `output/` が参照する rollout 52 件 = 封印 sha と一致 33、封印値なし 5 (退避済み)、
  不一致 0、既欠損 14 (全て 2026/07)。
- 削除: 直前に対象 dir の現物が退避一覧と完全一致し直近 2 日の更新 0 件であることを確かめてから削除。
  `/home` の使用量は 36G → 18G。復元手順は退避先の README。
- codex 本体の `state_5.sqlite` / `session_index.jsonl` は消した rollout を指したまま残る。codex の resume で古い thread は
  開けない可能性がある (未実測、izanagi は使わない)。
