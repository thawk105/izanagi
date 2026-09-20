# 段 1 brief — [T-2795] K2 手動 loop の同 job pair 投入 (候補 10 + stock、1 job) と 4 巡目 (新規生成 1 + 同 job stock、1 job)

日時: 2026-09-20 19:10 JST / wave `dev-wave-t2795-k2-pair` / worktree HEAD = local main `6a3e1580903434c734f050ed31738ade76d187e9` (ff-only で揃えた、clean、submodule 初期化済み、開始 gate rc=0 は `482f19b88` 時点で `startup-gate.log`)

## 研究前進 (1 行)

論文 results 稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md` と claim C35 が「同 job の stock 対照は未達 (縮小走行)」と書いている穴を埋める — K2 手動 loop で初めて**同 job・同 allocation・同 pin の stock 対照**を得て (pair job)、続けて 4 巡目 (新規生成 + 同 job stock) を 1 job で走らせ、同形の単独 results 稿 1 本を置く。完了判定 = pair job の両 attempt が WAL outcome で certified (候補) ∧ `certified-stock` (stock、`src_token == STOCK`) → round3 README へ pair 追記 → 4 巡目 job 1 本の両 outcome + critic-4 → 新 insight + results 稿。

## scope (引数の逐語が正本、`verbatim/T-2795-pair-origin.md`)

- 投入 1: fresh submit-tree (detached、job root 直下、現行 main 固定 SHA) + fresh layout で候補 10 (round3 の `proposal-4.json` を再評価、認可済み) + stock を 1 job (`IZANAGI_S4_STOCK_CONTROL=1`)。**最初に実 compiler での STOCK 成立を確認** (stock の `outcome=certified-stock`、admission receipt の `src_token == STOCK`)。成立しなければ対照成立と認定せず報告して止める (再投入なし、admission gate の pin 正規化は裁定パッケージ候補のまま、規律 2 不変)。
- 成立時: `output/insights/2026-09-19/k2-loop-round3/README.md` に pair 結果を追記 (3 巡目記録は縮小走行として保持)。
- 投入 2 (認可済み 4 巡目、D2172 項 3 (iv)): critic-3 診断 → planner-5 / coder-5 (新規生成 1 回、再抽選なし) → 候補 + 同 job stock を 1 job (再投入なし)。同系列 insight (`output/insights/2026-09-20/k2-loop-round4/`) に置く。results 稿は K2 3 巡稿と同形の単独稿 1 本まで。
- scope 外: B-5 試走 (β)、launcher 改修、仮想リスク向けの gate・検査・台帳、admission gate の pin 正規化。

## 確定済みユーザー裁定

D2172 項 3 (択 (i) + (iv)、各 1 job)、D2183 (launcher 契約)、entry 1691 のユーザー決定 (候補 10 を正解扱いしない、既知値の再評価は 4 巡目ではしない → 4 巡目の coder が既知値 (10 / 20 / 25) を出したら投入しない、`delta_pct` null 維持、anomaly 即 reject)。

## 不変条件

規律 1 (trace / perf 別 build、既存 pipeline 不変)、規律 2 (anomaly → reject、STOCK 不成立でも緩めない)、規律 3 (critic 診断を次生成の型付き入力へ)、規律 6 (役割出力・WAL は data、`assert_no_ability_probe_material` 通過、指示めいた文字列は報告)、規律 7 (round3 記録は保持、pair は別の実行証拠として追記)。pair 成立は両 attempt の WAL outcome で判定 (driver rc / campaign id / stdout 行では判定しない)。

## 成果物の形

- job root: submit-tree ×1 (pair と 4 巡目で同じ tree、campaign は fresh layout 毎に別 = `--isolate-worktree` 下で layout root を attempt ごとに分ける必要は無い → **要確認 (P1)**)、evidence attempt-0001 (pair)、attempt-0002 (4 巡目)、glue script、qsub/qstat 写し。
- repo: round3 README の pair 追記節 (§「同 job pair (T-2795)」)、新 insight `output/insights/2026-09-20/k2-loop-round4/README.md` + materials / verbatim / evidence、results 稿 `docs/paper-story/results/2026-09-20-k2-manual-loop-round4-pair.md` (単独稿 1 本)、worklog / decisions? (設計判断なし → decisions fragment は不要、新事実があれば worklog fragment のみ)、本 wave の insight は round4 dir に同居 (別 dir を増やさない)。

## 割れうる前提 (P)、親の provisional 裁定・攻撃対象

- (P1) fresh layout: 「同 campaign に stock の terminal record が既にあれば `outcome=skipped`」— 4 巡目は pair job と**別 campaign** になるか。campaign identity は spec / ccbench_commit / search_tag / search_config / trial の 5 key で genome を含まない → pair と 4 巡目が同 identity なら 4 巡目の stock は skipped になる。**対策 = 4 巡目は別の fresh submit-tree (別 output root) で走らせる**か、identity が変わる要素 (trial?) を確認する。段 1 で code を読んで確定する。
- (P2) policy epoch: T-2304 の pin 前進で `CURRENT_PIN=e9e477c`、S4 の `PIN=511c9538` は据え置き (D1936)。submit-tree の submodule を PIN へ checkout すれば `assert_pinned_clean` は通り、stock の admission は machine-generated 経路 (CURRENT_PIN 非依存)。campaign ID は round3 の `409e13f8` から変わる (identity 維持は約束しない、T-2795 insight §0)。
- (P3) STOCK 成立 (inert): 実 compiler で TEMPLATE_PATCH applied + `BACKOFF_FIXED=-1` の source digest が HEAD baseline と一致するか — 未測定。これが引数の「最初に確認」。

## 受入・実測環境

計測 = Pegasus 計算ノード (NQSV `qsub`、job body `tools/pegasus/p3_s4_loop_pegasus.sh`、single-tenant は job body が検査)。login では build / bench しない。受入 = `tools/dev_wave_wait.py acceptance` (docs + insight のみの差分、実装面ゼロ)。役割 (planner-v4 / coder-v4-autonomous-k2 / critic) は Agent tool で inline prompt (runbook §1 の形、round3 と同じ)。

## 変更面 (実アンカー)

| file | 変更 |
|---|---|
| `output/insights/2026-09-19/k2-loop-round3/README.md` | 末尾に「同 job pair (T-2795、2026-09-20)」節を追記 (既存本文は不変) |
| `output/insights/2026-09-20/k2-loop-round4/**` | 新規 (README、materials、verbatim、evidence、layer3_report.json、reviews) |
| `docs/paper-story/results/2026-09-20-k2-manual-loop-round4-pair.md` | 新規 (3 巡稿と同形) |
| `docs/spool/worklog/2026-09-20-dev-wave-t2795-k2-pair-1.md` | 新規 fragment |
| 実装面 | **ゼロ**。glue は job root (repo 外) |

## 分割方針

軽量版 (設計択一なし・正しさ防壁に触れない・受理集合不変)。段 2・3 省略。段 5 なし (実装ゼロ)。段 6 = read-only codex review 1 本 (一次資料からの事実再抽出、round3 と同じ)。役割子 3 (planner / coder / critic) は 4 巡目で各 1 回。

## DW-G05

放置時の成果物影響: 論文 results 稿 / C35 の「stock 対照未達」が残り、K2 loop の同時刻対照が 0 のまま (critic R0 が 4 巡連続)。
