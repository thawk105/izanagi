# [T-2647] B-10 静的 backoff 右 tail 本走 (09-15 cohort) の results 稿を results 系列へ置いた

`authority: none` / `default_effect: no-state-change`

**種別:** 記録 (論文材料の凍結稿の起草)。**実装面 (D95 決定 2) の差分はゼロ。新規測定もゼロ。**

- 日付: 2026-09-16 (JST)
- wave: `dev-wave-t2647-b10-tail-results`、branch `worktree-dev-wave-t2647-b10-tail-results`
- 起点 local main: `8f17db5981a689789916fcc56ccf373b10347e1a`
- 依頼: 「B-10 静的 backoff 右 tail 本走 (2026-09-15 完走、group `b10-backoff-grid-20260915T061814Z-545445`、
  集団判定 `not-observed-in-any-workload`) の results 稿を `docs/paper-story/results/` へ起草する。A-2 / B-7 の
  既存稿と同型の日付付き凍結物として置く。言い方は事前登録 §4.5 の固定表現に限る。性能値は未認証のままで
  採用根拠にしない。論文図は作らない。2 本目 cohort の地位には触れない。docs のみ。本題の results 稿だけ。
  gate・検査・台帳・一般化の追加は scope 外」

## 0. この wave が主張すること・しないこと

**主張する。**

1. **results 系列に 09-15 cohort の結果節材料を置いた。** `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`
   (限定 15 件、生標本 24 cell) と、`docs/paper-story/README.md` の results 表への 1 行登録。§1。
2. **数値は原成果物の直読と再計算から作り、レビュー子が独立に全件一致を確かめた。** §2。
3. **主張範囲のレビューが real 所見 4 件を出し、すべて採用した。焦点再レビューが親の誤った不在断定を 1 件
   捕まえ、実測へ書き直した。** §3。

**主張しない。**

- **飽和が存在しないとは言わない。** 稿の言い方は事前登録 §4.5 の固定表現に限る。
- **性能を認証していない。** `performance_certified: false` のままである。
- **図を作っていない。** 09-15 cohort を描いた図は存在しない (`t2647-b10-tail-downstream.md` §4 の 3 条件は未充足のまま)。
- **[T-2647] を閉じない。B-10 も閉じない。** 残るのは論文図と版への取り込みである (§5)。
- **2 本目 cohort の地位に触れない。** 稿からもその言及を除いた (§3 の F1)。

## 1. 置いたもの

| file | 内容 |
|---|---|
| `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` (新規) | 冒頭の但し書き、§0 位置づけ、§1 条件 (事前登録への束縛・格子・実行 identity・正しさの記録)、§2 結果 (集団 verdict・18 区間の推定・過抑制の費用・生標本)、§3 限定 15 件、§4 一次資料 (権威 bytes の SHA-256・値の出所・repo 内資料) |
| `docs/paper-story/README.md` (results 表に 1 行) | 対象・protocol status・言い方の固定・未認証・図なし |
| `docs/spool/worklog/2026-09-16-dev-wave-t2647-b10-tail-results-1.md` | worklog fragment ([T-2647] を `更新`) |
| 本 insight | 記録と逐語 |

README の項目 3 (2026-09-16 追記)、両論文系列の版・claim-evidence・figures、phase doc、decisions は触っていない。

## 2. 数値の出所と検算

親が読んだのは `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/` の 3 成果物である
(SHA-256 は `5f426ecb…` / `758b3121…` / `7192d1da…`、`b10-tail-formal-submit/README.md` §4 の再導出記録と一致)。
18 区間の推定値は JSON の `workloads[].intervals[]` から、24 cell の 5 反復平均・変動係数・生標本は `.dat` の
120 行から再計算した。`L = 1 − 2^qU` の再計算、`.dat` の `abort_rate` 列と整数カウンタの再計算値の一致
(120 行)、`points[].tps` と `points[].reps[].throughput_tps` の一致も確かめた。

レビュー A (逐語と数値の検算、`verbatim/review-a-out.md`) は、原成果物から独立に 18 × 6 = 108 の推定値、
24 cell × 2 の平均 48 値と変動係数 48 値、生標本 120 + 120、集団 verdict・状態・分類・フラグ、格子・raw 値・
genome・動作点・測定順・seed・時間枠・job id・JST 開始時刻・所要、正しさ記録 120 件、`perf_bin_sha256` の相異数、
7 file の SHA-256 (repo 外 3 + repo 内 4)、spec の JSON 本文の SHA-256 を検算し、**不一致 0** と報告した。
nit 1 件 (§2.2 の引用が `U ≤ 0.05` で非逐語) は原文 `U_i <= 0.05` へ戻した。

## 3. レビュー B (主張範囲) の所見と裁定、焦点再レビュー

レビュー B (`verbatim/review-b-out.md`) は must-fix 1、should-fix 3 を出した。**4 件とも real として採用した。**

| # | 所見 | 裁定と対応 |
|---|---|---|
| F1 (must-fix) | §0.3 と限定 9 の「D2050 が持つ」は、依頼の「触れない」に反する | real。D2050 と「再現・置換・併記」の語を除き、「本稿は 09-15 の 1 本の cohort だけを扱う」だけを残した |
| F2 (should-fix) | 事前登録 §0 の更新契約違反 (追補の §0 未記載、`b10-tail-formal-submit` §3.2) が稿に引き継がれていない | real。§1.1 に、違反が残ること、ただし §7 の失敗条件 12 や `invalid` へ読み替えないことの両面を追記した |
| F3 (should-fix) | 事前登録 §3 の「物理量の意味の witness を主張しない」が限定に無い | real。限定 15 を新設 |
| F4 (should-fix) | 限定 12 の探索後選択の開示が 2 値だけで、格子の位置・刻み幅と域内非飽和を結末に含める選択が抜けている | real。事前登録 §0 のとおり 4 事項を列挙した |

焦点再レビュー (`verbatim/focus-out.md`) は closed 4・**partial 1 (F3)**。親が限定 15 に書いた
「集団報告と campaign lock に意味 witness の状態を記録する field は無い」のうち、campaign lock 側が
子の射影では裏付けられないという指摘だった。

**親が数え直すと、親の不在断定は誤りだった。** campaign lock の `identity_preimage` は JSON を文字列として抱えて
おり、親の最初の検索 (`meaning_witness[a-z_]*\"` で終端を固定) はエスケープされた引用符で外れて 0 件と読んで
いた。`grep -c meaning_witness` は 3 lock とも 1 を返し、生文字列は
`meaning_witness_status = unestablished_for_positive_backoff_fixed_as_in_existing_sweep`、
`meaning_witness_gate_required = false` である (3 campaign で同値)。限定 15 をこの実測へ書き直した。
事前登録 §3 の「既存 sweep 全体と同じく未確立」と一致する記録であり、稿の境界は変わらない。

**焦点再レビューは fix 後の版に対して 1 本だけ走らせ、この書き直しの後には再投入していない。** 書き直しは
限定 15 の 1 文を「無い」から「lock はこう記録している」へ変えただけで、新しい主張を足していない。
その 1 文の検算は親の `grep -c` と生文字列の抜き出し (上記) が担う。

## 4. 実施した検査

- `python3 tools/check_docs.py` rc=0 (起草後、fix 後の 2 回)。
- `git diff --check` rc=0。
- `python3 -m orchestrator.campaign.s8b_holdout_freeze search` rc=0 (holdout の conjunction hit 0)。
- `python3 tools/spool_fold.py --dry-run` rc=0 (fragment 1、`planned`)。
- **変異 matrix は免除**: 実装面の差分ゼロ (DW-S04)。
- **受入全走**: 記録 commit を含む tip に対して land 前に 1 回投入する。結果は worklog に書く。
- results 系列を読む test は無い (`docs/paper-story` を参照する test は figures の provenance だけを見る)。
  両 README は `LIVING_DOCS` の対象外であり、文面の正しさを機械は保証しない。意味は段 6 の 3 本と親の裁定が担う。

## 5. 本 wave が閉じないもの

- **[T-2647]。** 残るのは (1) 09-15 cohort を描く論文図 — `t2647-b10-tail-downstream.md` §4 の 3 条件を先に解く
  別 wave が要る、(2) 版への取り込み — 次の版の契約が決める。
- **B-10。** 機序、901〜998 マイクロ秒の帯、schema v2 入力時の判定は未了のまま。
- **性能の認証。当時の実行の独立監査。** いずれも動いていない。

## 6. 逐語

`verbatim/` に親の段 1 brief、prompt 3 本 (review-a / review-b / focus)、出力 3 本を置いた。
子は 3 本とも Codex `gpt-6-astra` / `medium`、receipt `accepted` (model call 7 / 8 / 4)。
生の log と受領証は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-results/` にある。
