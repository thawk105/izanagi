# [T-179] 段 4 裁定 + 変異事前登録

段 2 / 段 3 を省いたため外部所見はない。親 brief の provisional 裁定 (P1)〜(P8) を確定裁定へ昇格する。
昇格の根拠は紙の議論ではなく、10 個の実 rollout に対する直接実測 (全数値が完全一致で再現) である。

## 確定裁定

| # | 裁定 | 根拠 |
|---|---|---|
| P1 | データ源 = `$CODEX_HOME/sessions/**/rollout-*.jsonl`。root は CLI 引数 + 環境変数。docs にマシン固有パスを書かない | 実測で 626 file を走査、全 field 実在確認 |
| P2 | session key = 完全 `session_id`。短縮禁止 | 先頭 8 hex が実データで 2 組衝突 |
| P3 | token 正本 = 最終 `total_token_usage` の `input - cached + output`。per-turn 和は補助列 | 2,757,982 が完全一致。per-turn 和は 2,765,553 (7,571 差) |
| P4 | stage = 規則表 + override map、未分類は `unclassified` を必ず表出 | 実 prompt に段番号と role が逐語で存在 |
| P5 | 終了分類 = `completed` / `incomplete` / `aborted_turn`。exit code は `unknown` と明示 | rollout に `.done` も exit code も無い |
| P6 | validator = `tools/check_codex_output.py` の述語を再利用 | 既存実装で十分、二重実装は drift 源 |
| P7 | retry = 同一 wave 内の正規化 prompt hash 一致で group 化 | F43 の B/B2 が同一 prompt 再投 |
| P8 | worklog 突合 = `エージェント工数: Codex N job (...)` 行を解析し非 0 rc | (59) の実文字列で確認済み |

`DW-M08` の「新旧両走」は**不適用** — 本 wave は既存テストの強化ではなく新規ツールの新設で、
変更前 HEAD に対応する旧版が存在しない。この判断を worklog に明記する。

## 変異事前登録 (`DW-M01`、実装前)

各変異は「その位置より前に同じ入力を拒否する検査が無いこと」と「赤理由が一つに絞れること」を
実装完了後の最終 commit で anchor 再検証する (`DW-M07`)。以下は**意味論としての事前登録**であり、
逐語 anchor は実装後に確定する。

| ID | 攻撃する不変条件 | 変異内容 | 期待 kill (受理集合 / fail-closed の変化) |
|---|---|---|---|
| M1 | token 正本 (P3) | 最終 `total_token_usage` の代わりに per-turn `last_token_usage` の和を使う | compaction を含む fixture で blended 合計が変わる。単一 node が赤 |
| M2 | session 同一性 (P2) | `session_id` を先頭 8 文字へ短縮して key にする | 衝突 fixture で session 数が減り、台帳行が融合する |
| M3 | 未分類の表出 (P4) | `unclassified` session を集計から黙って除外する | 未分類 fixture で合計が減り `--strict` が緑になる (fail-closed → fail-open) |
| M4 | validator (P6) | 成果物述語を常に合格として扱う | fragment fixture (F43 型) が `completed` に化ける |
| M5 | 終了分類 (P5) | `task_complete` 欠落を `completed` として扱う | incomplete fixture (F45 型) の分類が変わる |
| M6 | 突合 gate (P8) | 不一致でも rc=0 を返す | 9-vs-10 fixture で非 0 が 0 になる (gate の無効化) |
| M7 | retry 検出 (P7) | prompt 正規化を外し常に別 group とする | 同一 prompt 再投 fixture の retry group 数が変わる |
| M8 | **過剰拒否の正例** | 健全な wave にも `--strict` で非 0 を返すようにする | 完全に健全な正例 fixture が rc=0 のはずが非 0 になる |

M8 は `DW-M01` の「受理集合を縮小する wave では承認外の過剰拒否を検出する正例も登録する」に対応する。
負例だけでは「拒否しすぎる実装」が生き残るため、正例 fixture を必ず持つ。

`DW-M03` に従い、kill は「赤くなったこと」ではなく**受理集合または fail-closed 挙動が期待方向へ
変わったこと**でのみ数える。診断文字列だけの赤は kill にしない。
`DW-M08` に従い harness は赤 node を毎回記録し、`-rf` + ANSI 除去で node を正規化する。

## 実装単位と所有

単一単位。Codex `role=author` が排他所有するパス:

- `tools/codex_worker_ledger.py`
- `orchestrator/tests/test_codex_worker_ledger.py`
- `orchestrator/tests/fixtures/codex_ledger/**`

docs (`docs/worklog.md`、`docs/phase3.md`、`output/insights/**`) と commit は親のみ。
