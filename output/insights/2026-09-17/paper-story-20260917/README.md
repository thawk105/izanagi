# 論文ストーリー 2026-09-17 版の全項目再導出 — wave 記録

`docs/paper-story/2026-09-17.md` を、2026-09-17 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版 7 本・`results/` 7 稿・`figures/`・`claim-evidence/`・
`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-paper-story-20260917`、branch `worktree-dev-wave-paper-story-20260917`
- 起点: wave 開始時 local main `bf4f91f51` (2026-09-17 00:33 JST)。段 4 直前に `1042a1bc9` へ ff-only で取り込んだ
  ([T-2630] の記録の fold 1 commit = worklog entry 1580・F1016・F1017・[T-2731])
- 成果物: `docs/paper-story/2026-09-17.md` (新規、段 6 の fix 後で 2,765 行 / 約 302 KB) と
  `docs/paper-story/README.md` の 3 節の更新 (版の履歴表へ 1 行、訂正一覧を 09-17 版の 3 件へ、stale 注記を 0 件へ)
- 依頼: 「論文ストーリー本体の新版を、その日付の local main の正典全体から全面再導出して作る。2026-09-14 版以後に
  確定した事実を本文へ取り込む。§8 の A/B 群の状態欄を現物で埋める。T-2647 (1) の 09-15 cohort の論文図は、置き場所を
  本版が定め FIGURE_CONVENTIONS §10 を満たせるときだけ同梱し、無理なら『未作成』と書く — 図を完了条件にしない。
  凍結物は 1 byte も変えない。本題の版だけ」

## 1. 依頼が挙げた前提の実測

依頼が挙げた 12 項目は、いずれも一次資料と一致した (段 1、`brief.md` の表)。

| 項目 | 一次資料 | 実測値 |
|---|---|---|
| B-10 右 tail 本走 | `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md`、`output/insights/2026-09-16/t2647-b10-tail-downstream.md` | group `b10-backoff-grid-20260915T061814Z-545445`、verdict `not-observed-in-any-workload`、18 区間 `declining`、`performance_certified: false`。前版の 5 箇所 (当時は真) を現在地として更新 |
| official 床値 | `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md` | request `1818.nqsv`、96 attempt 完走、rr20 = 35,817.945 / rr80 = 46,065.78、両 holdout とも配線下限 0.03 × scale_ref (u_noise 15,859〜28,966 / 20,843〜27,543 が下限未満)、`eligible_for_refreeze: true` は自己申告、未発効 |
| B-7 三走行材料 | `docs/paper-story/results/2026-09-16-b7-three-run-materials.md`、D2044 項3 | 3 走行・4 対比較・8 arm・限定 20 件。要件充足へは昇格しない |
| rr5 accepted 較正 | `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json` (jq 実測) | records 2,000,000、`miss_rate_at` 0.01567、`noise_floor.cv` 0.009707、`quality.status` accepted |
| 非 silo 較正 4 対 | `docs/phase3.md` 8b 節、D2083 | tictoc rr50 / rr95、mocc rr50 / rr95。registered は 8 record |
| B-4 binary record・配置 | `output/insights/2026-09-16/t2636-b4-binary-record/README.md`、D2069 | binary 701,760 bytes、record `records/rr20--stock_common.json`、配置 `output/env/<env_tag>/binaries/<sha256>` (ignored) |
| D1640 追補 | D2049 | H1 = rr80 / H2 = rr20、凍結側不変 |
| fig7 | `docs/paper-story/figures/README.md` fig7 節、D2053 | 旧 attempt と同値・条件記述訂正、fig5 bytes 不変 |
| D2044 | `docs/decisions.md` | 全 39 項を読了 |
| README の stale 注記 3 件 | `docs/paper-story/README.md` | B-2 追補・層3・B-10 — 3 件とも本文へ吸収 |
| 8c §5 | `docs/phase3-8c-preregistration.md` | 9 欄中 8 欄未記入、検定 4 点は `no_hypothesis_test` で記入済み |
| 完了証明層 | `orchestrator/campaign/s8c_preregistration_evidence.py` | `SATISFIABLE_CONDITION_IDS = frozenset({"C10"})` (評価器は再走していない) |

## 2. 前版を訂正した 3 件 (いずれも執筆時点で偽)

1. **層3 screening の 6 箇所** — 対応は 2026-08-25 [T-1291] (schema の 2 段の変更)。4 版続けて運ばれた (F1 再発)。
2. **official 初投入日** — 前版の「2026-09-11」は誤り。`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md` §2 は
   request `988501.nqsv` の投入を 2026-09-09 22:09 JST、RUN 観測 22:10:31 JST と記録する。
3. **「[T-1851] の実装単位群は D1341 により未 land」** — `git merge-base --is-ancestor ce2769c32 af3762d62` は rc=0
   (D2 統合 commit は前版起点の祖先)。entry 1450 (2026-09-11) が一括 land を記録。D1341 の裁定自体は有効。

**2 と 3 は段 2 の plan が見つけ、段 3 の 2 レンズが独立に支持し、親が一次資料で検算した。** 親の段 1 brief は
「訂正は層3 の 1 件」と起案しており (P3)、撤回した。

## 3. 親の暫定裁定の結末

| # | 結末 |
|---|---|
| (P1) 図は未作成、置き場所だけ定める | 採用。`fig8_…` と生成器名は「未作成の予定仕様」と明記、2 本目の論文との共用図にしない |
| (P2) §9 の第 4 文は不変 | 採用。「前進がない」とは書かず、記述的な測定 2 件・材料・訂正の増加を別段落で述べる |
| (P3) 訂正は層3 の 1 件 | **撤回 → 3 件** |
| (P4) T-2630 を exact claim の限定 (v) に | 採用、文面を段 3 レンズ A の案へ差し替え。「D1993 の 4 限定 + この版が明示する 1 つ」と数える。修正方式は [T-2731] の裁定待ちで本版は選ばない |
| (P5) stale 注記を 0 件へ | 採用。基準 HEAD と 3 件の移管先を残す。「0 件」を「誤りが無い保証」としない |

**親の brief 自身の誤り 1 件** — `results/` を 6 稿と書いたが現物は 7 稿 (段 3 レンズ A)。

## 4. 子の工数と所見

| 段 | 子 | 結果 |
|---|---|---|
| 2 | plan 1 本 (`plan-1`) | 再導出地図 (§0〜§10 全項目) + (P3) 不同意 + 落ちやすい前進 13 件 + 射程超過 10 件 |
| 3 | consult 2 本 (`consult-a-1` = sol、`consult-b-1` = luna) | 両者 NO-GO → 文面修正後 GO。所見 13 件 + 11 件、refuted 1 (前版 §7 の 58 項は正しい) |
| 6 | review 2 本 (`review-a-1` = 一次資料照合・母集合・件数、`review-b-1` = 主張の強さ・分類・内部整合・前版差分) | 両者 NO-GO。報告 10 件、相異なる所見 8 件 (must-fix 5 / should-fix 2 / nit 1)。親が 8 件を一次資料で検算し 7 件を real として反映、1 件はレンズ B 自身が refuted と判定 (変更不要)。「前版から消えた項目」7 件のうち 3 件を復元 |

**`--lane` の 2 値は現在同じモデルに解決される (D1987)。「別系統モデル 2 本」とは数えない。**
子は 5 本とも `tools/check_codex_output.py` rc=0 を通した。逐語は `verbatim/` に全文を収める。

**段 6 で最も重い所見は 3 つある。** (1) K2 の「新しい値」は既評価値 `20` の再提案だった (レンズ A。
`output/insights/2026-09-16/t2588-k2-loop-roundtrip/README.md` が「未評価値生成の成功には数えない」と明記)。
(2) official 床値の 108 file バックアップを D2077 の namespace 退避の完了と同一視していた (レンズ A。取得記録は
「wave worktree 側の原本は撤去まで残す」と書く)。(3) B-10 の固定表現が 6 箇所で短縮形に崩れ、§8 は事前登録 §0 の
開示を「『表現域内で飽和しない』を正当な結末に含める」と書いていた (レンズ B。観測の不在から性質の否定へ変わる)。
両レンズが独立に、冒頭と §10 の「本文レビューを通した」という完了形が §10 の記録に対応していないことも指摘した
(本文修正後に §10 段 6 節を追記して真にした)。所見と裁定の全文は新版 §10 と `verbatim/review-*-out.md`。

**親の手順は前回 (entry 1485) の違反を繰り返していない** — レビュー子 2 本が worktree を読んでいる間、親は
worktree の docs に触れず、修正は job dir の下書きへ当ててから子の完了後に連結し直した。
**修正後の焦点再レビューは起動していない** — 8 件はいずれも親が一次資料で検算して閉じており、新しい所見を生む
変更面 (受理集合・判定・機構) が無いためである。

## 5. 図を作らなかった理由

FIGURE_CONVENTIONS §10 は実寸 fixture (3 workload × 8 点 × 5 反復 + 境界参照)・本物の Figure の検査・実データ全モード
実走と 3 成果物の確認を要求し、`figures/README.md` の caption・proof chain と provenance の pin test も要る。これは
実装面 (D95) であり Codex author の別 wave になる (fig7 wave は Codex 子 6 本 + 変異 matrix を要した)。依頼が
「図を完了条件にしない」と定めたので、版は置き場所だけを予定仕様として定めた (§4 の表の末尾)。

## 6. 検査

- `python3 tools/check_docs.py`: rc=0 (`check_docs: 違反なし`)
- `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc=0 (holdout conjunction hit 0、陽性対照 182 件)
- `git diff --check`: rc=0。新版の末尾空白 0・tab 0
- 本文が引く `output/` 56 path と `docs/` 18 path の実在確認 (fix 後に再走。不在は fig8 の予定仕様、図 stem、`<env_tag>` 等の template 記法のみ)。行番号形式の参照は 0 件
- 件数検算: §7 前半 58 / 後半 9、§0 の動いた事実 14 点、§2 (g) の 11 点、冒頭の訂正 3 件、§9 の 7 種
- 変更面: `git diff --stat` は `docs/paper-story/README.md` (更新) と `docs/paper-story/2026-09-17.md` (新規) の 2 file だけ
- 実装面 (D95 決定 2 = 非 Markdown) の差分はゼロ。**変異 matrix は DW-S04 により免除。受入全走は免除していない。**

## 7. 逐語の可逆最小正規化 (DW-S07)

子の出力 5 file は Markdown の改行記法として行末に 2 空白を持ち、`git diff --check` に抵触した。
**可視文字を変えずに、行末がちょうど 2 空白で終わる行の 2 空白だけを除去した** (`sed 's/  $//'`)。
1 空白・tab の行末は元から 0 件。原文 (正規化前の bytes) は job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260917/codex/` にそのまま残る。
復元法: 下の行番号の各行末へ 2 空白 (`U+0020` × 2) を付加する。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去した行 (行番号) |
|---|---|---:|---|---:|---|
| `verbatim/plan-out.md` | `6a3d50fb41ef1c88032c1c14ab642cd4251482665d5660617b83a08488fe4c7d` | 38,379 | `aea07875262189d91ca2c7aadc5727541067c8536a41fab868278d6279999927` | 38,359 | 369 372 373 376 377 378 381 455 456 457 |
| `verbatim/consult-a-out.md` | `0229b268ca5f3a9cf4baeddcb10af0981cd934a274043d8b0da72aa6a75372d9` | 11,707 | `e0c87e2873735311dc3d8225269be60f3c72828968cb819c7d9827c129b1b5ea` | 11,615 | 3 4 13 14 15 18 19 20 23 24 25 28 29 30 33 34 37 38 39 44 45 46 49 50 51 54 55 56 59 60 61 64 65 66 69 70 71 74 75 76 104 105 106 107 108 109 |
| `verbatim/consult-b-out.md` | `ba06b14259cd3a4530137fc20825c4831a2b3ed706cd206de4d93b46e7aaa465` | 9,828 | `8e9aafff814fab85e44ca223201de7083855fc5ffd6a1b802db163fc7c5bc305` | 9,754 | 3 4 7 8 9 12 13 14 17 18 19 22 23 28 29 30 33 34 35 36 37 40 41 42 45 46 49 50 51 54 55 56 82 83 84 85 86 |
| `verbatim/review-a-out.md` | `e8f1bbdb80bd480315c181873ea31c53c84922f48a7da3a98922989a1f05830e` | 8,926 | `2b772ead231c17b290b5931a95f4d86448cadf05e03135c8d91c100dbe9995ec` | 8,868 | 3 4 5 6 7 8 11 12 13 14 15 16 19 20 21 22 23 24 27 28 29 30 31 32 61 62 63 64 65 |
| `verbatim/review-b-out.md` | `5342ce4d2ed28452b7e5a1a8f6538d1045ac851401e3ec48232da2f9ffd24f20` | 8,603 | `9115250ba916b20a9092337ca872034616e846bdeb3770703979fc5f1bd353ff` | 8,543 | 3 4 5 6 9 10 11 12 15 16 17 18 21 22 23 24 27 28 29 30 33 34 35 36 71 72 73 74 75 76 |

byte 差はいずれも除去行数 × 2 と一致する (92 / 74 / 20 / 58 / 60)。prompt 5 本・brief・裁定 file は抵触なし。
