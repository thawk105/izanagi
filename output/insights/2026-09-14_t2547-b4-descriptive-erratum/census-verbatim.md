# 適格な赤 precursor の在庫実測 — 逐語 (2026-09-14)

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は `docs/phase3-b4-reflux-ablation-preregistration.md` §5.1 の追記 (2026-09-14、[T-2547]、
D1936 項 8) が根拠として指す観測の逐語である。

## 適格性述語 (§5.1.1、凍結済み。ここで変えない)

第 1 項は「`whiteboard.result` が `rejected` であり、かつ §3.1 が digest へ載せる 4 クラス
(verify-red / liveness / other / diff-quarantine) の少なくとも 1 件を持つ」。
以下の計数は**この第 1 項だけ**で 0 件が確定する。第 2〜6 項 (校正済み workload 所属 /
固定 bootstrap 集合所属 / 共通 reference の一意性 / 両アーム digest 非汚染) は §5 の該当欄が
未記入のため、そもそも適格性を確認できる状態にない。第 1 項で落ちるので結論は変わらない。

## 合成ループ 3 campaign の whiteboard

```
$ jq -r '.whiteboard[] | {iteration, result}' output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json
{ "iteration": 1, "result": "success" }
{ "iteration": 2, "result": "success" }
{ "iteration": 3, "result": "success" }
{ "iteration": 4, "result": "success" }

$ jq -r '.whiteboard[] | {iteration, result}' output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/loop_state.json
{ "iteration": 2, "result": "success" }

$ jq -r '.whiteboard[] | {iteration, result}' output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json
{ "iteration": 1, "result": "success" }
{ "iteration": 2, "result": "success" }
```

合計 7 行。すべて `success`。`rejected` は 0 行。

## 別 campaign の赤 3 件 (算入しない)

`output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/s4_rejections_digest.txt` に
`[non-serializable]` 1 件、`[indeterminate]` 1 件 (`src_token=fixture`)、
`[liveness:trace-timeout]` 1 件がある。同 campaign ディレクトリの中身は
`campaign.lock`、`runs/wal.jsonl`、`s4_rejections_digest.txt` の 3 つだけで
`loop_state.json` が無い。よって `whiteboard.result` が存在せず、適格性述語の第 1 項を
満たさない。1 件は `src_token=fixture` であり合成ループの産物ですらない。

## 追加探索 (段 3 sol の指摘を親が独立に確認)

campaign 配下には `layer3_report.json` が 7 件あり、これらも `whiteboard` を持つ。

- `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json` — 上記
  trigger loop の成功 2 行の再掲。新しい行ではない。
- 残る 6 件 (すべて `p3-s8a-trigger-sweep-*/reports/layer3_report.json`) — `grep -c rejected`
  がいずれも `0`。

`output/runs/` は存在しない。`output/insights/` の該当物は設計例・fixture・監査資料であり
実測 checkpoint ではない。

## 実走の不在

`grep -rl "b4_reflux_ablation" output/campaigns/` は rc=1 (一致なし)。
`analysis_manifest` / `scheduled_attempt_registry` の固定名成果物も不在。
`docs/phase3-b4-reflux-ablation-admission-record-{base,sort,trigger}.json` はいずれも不在
(`git ls-files docs/` の admission 検索は rc=1)。

## 結論

**適格な赤 precursor = 0 件。要求 n = 201。**

調査範囲はこの checkout に存在する campaign 成果物である。全世界の在庫調査ではない。

## 撤回した論拠 (段 3・段 6 の敵対検査が倒したもの)

- **撤回: ディレクトリの mtime を「前回計数から増えていない」証拠に使うこと。**
  親は当初「`output/campaigns/` の最新 mtime が 2026-08-12 だから 2026-09-10 の前回計数から
  増えていない」と書いたが、(a) ディレクトリの mtime は既存 JSON の内容が変わっていないことを
  証明しない、(b) 段 3 luna が worktree では同じ mtime が再現しない (checkout 時刻になる) と実測した。
  **「今回 0 件」は上の再読取りが支持するが、「前回以降増えていない」の証明にはならない。**
  後者の論拠は撤回する。
- **撤回: 「§5.1.1 の 2 重 sha256 がこの文書の bytes を pin する唯一の経路」。**
  `orchestrator/campaign/p3_b4_admission_record.py` は、宣言 commit の**文書全体**の sha256 と
  HEAD の blob 一致を要求する (`HEAD document differs from declared blob`)。
  したがって「§5.1 は pin されていない」と一般化してはならない。
  ただし admission record は 3 driver 分いずれも不在なので、無効化される既存 admission は 0 件である。
- **撤回: 「§5 固定表の parser は `### 5.1` より後ろを一切読まない」。**
  parser は文書全体の markdown 文脈と見出しを走査する。読まないのは「表の値として評価しない」だけである。
