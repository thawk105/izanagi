# [T-2344] enforcement source closure を 85 → 96 path へ進めた — 発行器 6 本と発行器起点にだけ居る 10 本 (和 11 本) を収載し、exact-85 を歴史閲覧 grammar として収載した

- 日付: 2026-09-21
- wave: dev-wave-t2344-source-bound-emitters (branch `worktree-dev-wave-t2344-source-bound-emitters`)
- 起点: ユーザー直接指示 (2026-09-21、`/dev-wave` 引数、逐語は `verbatim/origin.md`)。
- 正本: D2194 項 4 (次段 = 発行器先行、記録済み exact-63 成果物の再解析は (c) 現状維持)、D2193 (1 段ずつ + 直前 grammar の歴史収載を同 commit)、
  D1884 / D1075 (推移閉包へ段階実装、閉じるまで名乗りを広げない)、D1653 / D1770 (歴史閲覧限定 decoder、収載は実在 corpus が確認できた grammar だけ)、
  D2081 (scope 文言の形式)。設計判断は本 wave の decisions fragment。一次資料 (先行) は `output/insights/2026-09-20/t2344-closure-stage1/`。
- 基準: local main `5efd69367b641b9bfbd6fb426478f66ae5762783` で着手 (fresh worktree、HEAD == local main)。
  実装前に local main `71e572b3cbb46ab6427512c3edafe91c2a746f37` を ff-only で取り込み (docs のみ、`orchestrator/` と `tools/` の差分 0)。
- 実装 commit: `f605a7ba2` (段 5、Codex author)。段 6 の fix commit は無い (レビューの real 所見は文書側だけ)。
- authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾)。

## 1. 何をしたか

| 項目 | 変更前 | 変更後 |
|---|---|---|
| `CONTRACT_LOADER_RELATIVE_PATHS` (`orchestrator/campaign/campaign_lock.py`) | exact 85 path | **exact 96 path** = 既存 85 (順序不変) + 発行器 6 本 ∪ 発行器起点にだけ居る 10 本 = 11 本 (path の sorted 順で末尾へ) |
| 歴史閲覧 grammar (`decode_historical_campaign_lock`) | 現行 85 / exact-63 / exact-62 / 24 | 現行 96 / **exact-85** / exact-63 / exact-62 / 24 の 5 分岐。exact-85 は独立 ordered literal `T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS` + 兄弟 validator |
| 通常 decoder / encode / resume / certified admission の v2 authority grammar | exact-85 のみ | **exact-96 のみ** (union にしない、D1653) |
| `CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `_EXCLUDED_SCOPE` | curated exact 85 path; 2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85 / 未収載 78 | curated exact 96 path; 2026-09-21 (5efd69367 の source 木、本版の 96 path を起点) の実測では 173 module、うち収載 96 / 未収載 77 |
| exact-85 の歴史 scope | — | 変更前の現行 2 文言を `T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_*` として byte 同一で凍結 |
| `contract_loader_binding.py` | docstring「exact 85 path」 | 「exact 96 path」 (コードは不変) |
| test | 85 の独立 literal・固定値 | 独立 literal (96 と exact-85)、固定 known-answer 4 件、scope 文言、layer3 の歴史 param `[85, 63, 62, 24]`、git timeout の派生 literal (10 秒 × 96 = 960)、`s8b_oracle_report` の unavailable 分岐 scope。exact-85 の正例・負例 (codec 4 群 + admission 6 群)、新 11 本の drift 拒否を新設 |

**収載した 11 本** (着手 commit の実測、`closure-head.json`): `campaign/{autonomous_trial_completeness, b10_backoff_shape_sweep, backoff_extended_sweep,
backoff_extended_sweep_report, backoff_overthrottle, s8b_abort_reason_contract, s8b_oracle_report, s8b_outcome_stage_contract}.py`、
`reports/{__init__, calibration_report, plot}.py`。D2194 項 4 が名指しした発行器 6 本のうち 5 本は「発行器起点にだけ居る 10 本」に含まれ
(`autonomous_trial_completeness` だけは tuple 起点の発見集合に既に居た)、和は 16 ではなく **11** になる。
tuple 起点の 2 段目 23 本との重なりは 0 で、1 本も含めていない。

**epoch の hash 式は不変** (`campaign-verifier-epoch/v1` + 宣言順の path\0blob)。scope は preimage に入らない。既存 85 の宣言順を動かさないので、
exact-85 の固定 epoch は**変更前の**現行 85 固定値と同一である。**固定 known-answer 4 件** (test 実行時に production から再生成しない、D1652):
現行 96 の合成 E1 `E1:244d998f…7da07a` と順序付き path sha256 `5c2c4a6a…683af4`、exact-85 の `E1:bc8a6c8c…423dc7` と `bea36246…6b5a1`。
親の独立 oracle (`oracle-fixed-values.json`、現行 85 で計算した値が変更前の test 固定値と一致することで正例対照済み)・段 2 plan・実装子・段 6 レビュー A の 4 者で一致した。

## 2. 実測 (親、着手 commit 5efd69367)

T-2344 一次資料の probe 原本 (`probe_closure_v2.py` の `Tree` / `expand` / `imports_of` / `package_inits`、`ast.walk` + package 初期化、D1650 と同規則) を
書き直さずに import して実行した (`closure-head.json`)。

| 集合 | 09-20 (f94b61fc8) | **09-21 (5efd69367)** |
|---|---:|---:|
| 収載 tuple | 85 | 85 → **96 (本 wave)** |
| tuple 起点の発見集合 | 163 | **163** → 96 seed で **173** (= 和集合と同一集合) |
| tuple 起点の未収載 | 78 | 78 → **77** |
| tuple 起点の 2 段目 (参考、本 wave では収載しない) | 23 | **23** (新 11 本との重なり 0) |
| 発行器 6 本起点の発見集合 / 和 | 168 / 173 | **168 / 173** (未収載 88 → 77) |
| 発行器起点にだけ居る module | 10 | **10** (顔ぶれも同一) |

**記録済み campaign.lock の走査** (`recent-locks.json`、08:31〜08:45 JST): exact-85 化 commit `65e94a3a7` (09-20 21:55、main への land は
09-21 00:15〜00:21) 以降に mtime を持つ lock は 821 本 (走査 628,967 dir)。内訳は authority 無し (v1 形) 768、63-key v2 53、**85-key v2 は未検出**。
63-key 53 本はすべて T-2797 の submit-tree (記録 commit `11d46a74a`、pre-85) にあり、うち 25 本は mtime が main の land より後 (00:34〜03:53) である
(`stale-tree-locks.json`)。**mtime は発行時刻の証明ではなく、件数分類 (85-key) は exact grammar の照合とも別である。**

**到達可能性 (DW-O13、`exact85-reachable.json`):** clean な着手木で production の `capture_contract_loader_binding()` を 1 回呼ぶと、
binding commit = HEAD、85 key が宣言順で返る (lock へ encode すると canonical JSON の sorted wire 順になる)。campaign も lock も作っていない。

**pin 閉包** (DW-O09、`pin_closure.log`): 変更 3 file の変更前 sha256 で走査。tracked 0 件・`output/` 0 件。新規収載 11 本は bytes を変えない。

## 3. 段 2・3 の所見と段 4 裁定 (逐語は verbatim/)

段 2 plan (codex read-only、`verbatim/s2-plan.md`) は先例 `65e94a3a7` と同型の骨格を file:line で出し、
親 oracle の固定 4 値を独立に再計算して一致させた。段 3 は 2 レンズ (`verbatim/s3-lensA.md` / `s3-lensB.md`、
real 11 / refuted 8)。主な real:

- **(A-1) capture だけの変異では起動 test は赤にならない** — `ident.py:283` の live 検証が後段に残るため。変異の期待 node を admission 側に限った。
- **(A-2 / B-2) 「exact-85 corpus 0 本」は走査条件を越えた断定** — 「指定走査で 85-key v2 未検出、exact 照合済み corpus は未確認」に限定 (must-fix)。
- **(A-3) 収載は記録 blob の整合を検査するが、発行時点・実在 corpus を認証しない** — 合成 exact-85 lock も歴史入口で読める。
- **(A-4) 発行器の収載は全書出し経路に検査を掛けない** — `b10_backoff_shape_sweep` の report 分岐 (歴史 exact-24 限定) は現行 capture を通らない。
- **(B-3) 「発行器 6 本」は certified consumer の全数ではない** — `backoff_sweep_report` / `backoff_requested_us` /
  `b10_backoff_static_tail_formal` / `t1998_stock_inline_pair` / `layer3_report` も certified 経路を持つ。6 本は D2194 項 4 が選んだ seed。
- **(B-6) `s8b_oracle_report` の unavailable 分岐の scope 追随が抜けていた** — 既存 test へ現行 96 scope 2 項の独立 literal assertion を足した。
- **(B-9) 受入増分は exact-85 の 85 件だけでは見積もれない** — 6 群の部分外挿で下限寄り 16 秒 (未追認)。

refuted: certified への exact-85 流入 (入口分離は壊せなかった)、5 grammar の識別衝突、既存の未知 grammar 負例の恒真化、
歴史 85 と現行 96 の固定 epoch の区別、収載数 11 と 173 / 77 の計数規則、scope 案の D2081 適合。

段 4 裁定 (`verbatim/s4-ruling.md`) は (P1) 11 本・(P3) scope 文言・(P4) 固定値・(P5) 識別子名・(P6) 変異 14 件を確定し、
(P2) は §8 のとおり案 A (収載) を採った。

## 4. 段 6 レビューと対応 (DW-O16 の対応表)

レビュー A (正しさ境界) と B (過剰・削除・(P2) の根拠) はいずれも **NO-GO**。ただし **実装面の real 所見は 0 件**で、
must-fix はすべて親の文書 (裁定の根拠の書き方、実測資料の断定、要約の説明) に帰属した。対応表は `verbatim/s6-fix-table.md`。
Codex fix 子は起動せず、親が job dir の資料へ訂正を追記し、本 insight と decisions で閉じた。コード・test は 1 byte も変えていない。

実装面で refuted だった攻撃: certified 経路の受理拡大 (`decode_campaign_lock` / `_validate_authority` / purpose 分離)、
兄弟 validator の禁止条件 (84 / 86 / 同数別集合 / wire 順序違い / 96 / 95 の拒否)、歴史 scope の byte 同一性、
epoch hash 式と固定値、否定側の恒真化 (「96 − 末尾 11 本」は負例に使われていない)、既存テストの緩和 (42 ハンク全確認)、
scope 外実装・局所追随漏れ。

## 5. 受理集合の変化 (開示、DW-G05)

- tuple 前進後の checkout では、**exact-85 で記録された campaign は certified の decode 段で拒否**され、`HISTORICAL_RAW` でだけ読める
  (返却型は歴史型、epoch は `HistoricalCampaignVerifierEpoch`、現行適合 `unknown`、scope は凍結した 85 文言)。
  D1653 / D1770 が裁定済みの帰結で、exact-62 / exact-63 のときと同型。**最新 checkout の certified 再解析は救わない** (HISTORICAL_RAW の維持とは別の話)。
  着手時点で記録済みの exact-85 lock は指定走査では未検出なので、現時点の実害件数は確認できていない (0 と断定しない)。
- **certified 受理時の clean committed 要求が新 11 本へ広がる** (`artifact_admission.py:1186-1206` の
  `capture_contract_loader_binding`、campaign 起動時の capture)。発行器を未 commit の編集のまま certified 受理・campaign 起動に使えない。
  記録時と発行時の bytes 同一は要求しない (D1163 のまま)。広がるのは**中央 capture を通る経路に限る** —
  `b10_backoff_shape_sweep` の report 分岐 (歴史 exact-24 限定) には掛からない。
- `artifact_admission.py` の bytes が変わるので、**新規の admission receipt の `validator.sha256` が変わる**。
  B-4 projection hash の材料にも同 file が入る (D2081 の「保証しない範囲」が既に限界として記す)。記録済み成果物の bytes は変えない。
- 新規 report の `identity_scope` / `excluded_scope` (layer3、s8b oracle report の unavailable 分岐を含む) が 96 / 173 / 77 を名乗る。

## 6. 変異 matrix (DW-M01〜M08)

### 事前登録 (段 4 裁定 §5、実装前)

14 件 (M0 対照 + 正例 4 + 負例 9)。runner は焦点 5 file
(`test_campaign_lock_codec.py` / `test_artifact_admission.py` / `test_t671_source_binding.py` /
`test_s1_9pair_figure_provenance.py` / `test_s8b_oracle_report.py`)。
`test_layer3_report.py` は前段で M0 が 5 node を落とした drift 核なので runner に入れない
(layer3 の追随は焦点走 f1 の緑が担保)。

### probe 走

| 走 | spec sha256 | attempt | 結果 |
|---|---|---|---|
| probe 1 (`mutation-probe.json`) | `cdd0c849…` | 1 | **rc=2 で中止** — 走行中に親が repo へ insight 下書きを作り、harness が untracked file を検出 (`DW-M05` の「変異中は親の編集を止める」違反)。baseline PASSED、M0 SURVIVED まで観測。実害は再投入のみ |
| probe 2 (`mutation-probe2.json`) | `cdd0c849…` | 2 | 完走。baseline PASSED、M0 SURVIVED、他 13 件で観測 node を取得 (09:33〜10:09) |
| probe 3 (`mutation-probe3.json`) | `0ff8298e…` | 3 | M12b だけの追加 probe。baseline PASSED、1 node を観測 (10:11〜10:14) |

### erratum: M12 の不発と M12b への再照準 (DW-M02)

**M12** (`_RecordedCampaignVerifierEpoch` が現行 96 の scope 対と 85 map の組を許す) は probe 2 で **SURVIVED (0 node)**。
原因は他層の mask — 現行 96 の scope 対は `HistoricalCampaignVerifierEpoch.__post_init__` の歴史 scope 白名単に無く、
歴史 epoch としてそもそも構築できない (`artifact_admission.py:270-288`)。したがって変異箇所へ到達する入力が存在しない。
初回結果は消さず本節に残し、実効 gate (歴史 scope 対と map の対応) へ再照準した **M12b**
(exact-85 の scope 対の下で exact-63 の map を許す) を登録した。probe 3 で 1 node
(`test_t2344_exact85_epoch_requires_matching_scope_and_paths`) を観測している。

### 観測 node 数 (probe 2 / 3)

| # | 変異 | 群 | 観測 node |
|---|---|---|---:|
| M0 | comment だけ (対照) | 対照 | 0 (SURVIVED) |
| M1 | 現行 tuple から `s8b_oracle_report.py` を除去 | 収載追加 | 304 |
| M2 | 現行 tuple の末尾 2 path の宣言順を交換 | 収載追加 | 204 |
| M3 | capture の disk-vs-HEAD 比較を新収載 1 本だけ素通り | 収載追加 | 1 |
| M4 | 歴史 decoder の exact-85 分岐を pre-T733 validator へ | 歴史可読性 | 87 |
| M5 | exact-85 の committed blob 検証を省略 | 歴史可読性 | 85 |
| M6 | 兄弟 validator の wire 比較を superset 許容へ | 未知 grammar | 3 |
| M7 | 歴史 authority 白名単を superset 許容へ | 未知 grammar | 3 |
| M8 | 通常 decoder が exact-85 も一貫して受理 | certified 隔離 | 2 |
| M9 | exact-85 歴史 scope の数値を変更 | 歴史 scope 凍結 | 1 |
| M10 | exact-85 epoch が現行 96 の scope 対を運ぶ | 歴史 scope 凍結 | 1 |
| M11 | 歴史 epoch の計算順を sorted に | 歴史 scope 凍結 | 12 |
| M12b | exact-85 scope の下で exact-63 map を許す | certified 隔離 | 1 |
| M13 | 兄弟 validator が wire 順の map を返す | 未知 grammar | 88 |

**帰属の確認 (DW-M03):** M3 は狙った 1 node (`…rejects_each_emitter_stage_source_drift[…s8b_oracle_report.py]`) だけを落とし、
起動 test (`test_loader_drift_rejected_before_campaign_lock_or_wal_bytes`) は落ちていない — 段 6 レビュー A-1 のとおり、
capture の後段にある `ident.py:283` の live 検証が拒否を維持するためで、起動 test は対照として扱う。
M8 は certified 拒否の 2 node、M9 / M10 / M12b は凍結 scope と scope↔path 対応の各 1 node に正確に当たっている。
`KeyError`・import error・fixture 破壊・live drift だけで落ちる赤は登録していない。

### final 走

(記入済み。spec sha256 `4009f3158222beccc39026b7d1ab99442f02bc3523fd2390d8afee418dd19a76`、
repo HEAD `f605a7ba2`、期待は M0 = SURVIVED / 他 13 件 = KILLED で期待 node 完全一致)

### final 走の結果 (10:15〜10:51 JST、`mutation-final.json`)

spec sha256 `4009f3158222beccc39026b7d1ab99442f02bc3523fd2390d8afee418dd19a76`、repo HEAD `f605a7ba2`、
runner-mode = dispatch (計算ノード)、attempt 1、rc=0。baseline PASSED。

**13 / 13 KILLED (期待 node と完全一致)、M0 対照は SURVIVED。**
M1 304 / M2 204 / M3 1 / M4 87 / M5 85 / M6 3 / M7 3 / M8 2 / M9 1 / M10 1 / M11 12 / M12b 1 / M13 88。

M0 が SURVIVED であることは、runner 内に drift 核 (閉包 member への変異が狙った関門より先に
`contract-loader-drift` を発火させる経路、F923 / F741) が無いことの実測である。

## 7. 検査・受入

- **親の独立検算** (`verify-impl.json`、production を import せず AST と git blob で照合): 現行 tuple が 96 本で
  `closure-head.json` の `proposed` と全順序一致 / exact-85 literal が**変更前の**現行 85 と全順序一致し独立 literal /
  exact-63 / 62 / 24 の literal と scope が不変 / 歴史 scope 2 定数が変更前の現行 2 定数と UTF-8 bytes 一致 /
  現行 scope が裁定の確定文字列と完全一致し除外側が 77 で以降の文は不変 / 固定 4 値が test 内 literal に存在 /
  git timeout が 850 → 960。全項一致。
- **焦点走 f1** (`verbatim/focus-f1-summary.md`、job `14685.nqsv`、09:16〜09:22): 31 file =
  変更 test 6 + 変更 production の consumer + 新収載 11 本の自 test + `DW-O26` の inventory 4 群。
  **4441 passed / 9 skipped / 0 failed / 0 error** (313.01 秒)。skip の内訳は環境依存 skip と growth hold
  (`IZANAGI_GROWTH_HOLD_V1`) で、本 wave の変更に帰属しない。焦点走は受入全走ではない。
- **全史 provenance 監査**: 12268 件、新規違反なし (`check_ai_provenance.py`、実装 commit 後)。
- **受入直前の再走査** (裁定 §2 の開示、`recent-locks-preacceptance.json`、11:05 JST、659,712 dir):
  指定条件 (同じ 2 root・除外 dir・mtime ≥ 2026-09-20 21:55) で対象 lock 1141 本 = authority 無し 1088 + 63-key 53、
  **85-key は引き続き未検出**。63-key 53 本の所在と記録 commit (`11d46a74a`) は 08:45 の走査と同じである。
- 受入全走は記録 commit を含む最終 tip に land 前に投入し、受領証は job dir (`acceptance-receipt-*.json`) と
  land の記録が持つ (件数は本文へ書かない)。

## 8. 裁定パッケージ (本 wave の政策判断、ユーザーの裁定を求める)

**exact-85 を corpus 未確認のまま同 commit で収載したこと。** 段 4 裁定 §2・§8 の 4 層 (観測・生成可能性・予測・政策判断) のうち、
最後の層は既裁定から必然的には導けない。

- 観測: 指定走査 (2 root・除外 dir・mtime ≥ 09-20 21:55、08:31〜08:45) で 85-key v2 は未検出。exact 照合済み corpus は未確認。
- 生成可能性: 現行 production の capture は clean な 85 本の木で exact-85 binding を返す (`exact85-reachable.json`)。
- 予測 (不確実): 直前 grammar の lock は tuple 前進後にも固定木から生まれうる (exact-63 で 25 本の実測、ただし同一木の反復で独立証拠ではない)。
- 政策判断: D2194 項 4 / D2193 の同 commit 規則と、取り返しの非対称性を重んじて収載した。**D1653 の corpus 条件は収載時点で未充足。**

択: **(A) 現状維持 (収載を残す)** / (B) corpus 未確認を理由に撤去する / (C) 今後は「直前 grammar に限り corpus 条件を免除する」と明文化する。
撤去の手順は exact-85 の literal・validator・歴史 decoder 分岐・scope 定数・新設 test 群の削除で、exact-63 以前と certified 経路には影響しない。
費用の開示: (a) 記録 commit の 85 blob と整合する**合成 lock** も歴史入口で読める (実在の認証ではない)、(b) 歴史型・validator・scope・test 群の恒久保守、
(c)「production に存在した grammar なら corpus 未確認でも事前収載してよい」という先例。

## 9. 測定の射程 (この結論が言えないこと)

- 「certified 経路が source-bound である」を推移閉包の意味では名乗らない (96 本起点の発見集合 173 のうち未収載 77)。
  「発行器起点も閉じた」とも書かない。言えるのは「指定 seed を足した結果、静的発見集合が従来の和集合と一致した」まで。
- 「発行器 6 本」は D2194 項 4 が名指しした seed であり、certified consumer の全数ではない (§3 の B-3)。
- 収載が発行器に与えるのは「campaign 開始時の記録」と「certified 受理時の clean committed」であって、
  **発行時 bytes と記録 bytes の同一性ではない** (D1163)。`b10_backoff_shape_sweep` の report 分岐には追加の検査が掛からない。
- exact-85 の収載は記録 blob の整合を検査するが、発行時点や実在 corpus を認証しない (合成 lock も読める)。
- 「exact-85 corpus 0 本」は指定走査条件での未検出であり、不在の証明ではない。件数分類 (85-key) は exact grammar の照合とも別である。
- 静的発見集合 173 は import 文だけを辿った上界で、production 実行到達を証明しない。probe の規則 (`ast.walk` + package 初期化、D1650 と同規則) に依存する。
- 変異 matrix は焦点 5 file の runner に対する検出力で、受入全走の検出力ではない。

## 10. 工数

codex 子 6 本 (plan 1、consult 2、author 1、review 2、すべて gpt-6-astra / medium)。fix 子は 0 本
(段 6 の real 所見が実装面に無かったため)。計算ノード job: 焦点走 1 + 変異 probe 3 走 (attempt 1 は親の repo 書き込みで中止、
attempt 2 が本体、attempt 3 は M12b 追加) + 変異 final 1 走 + 受入。段 5 author は 8 分 / 実走 0 (子木では runner が
preflight rc=16 で走らない)。

## 成果物

| ファイル | 内容 |
|---|---|
| `closure-head.json` | 着手 commit の閉包寸法、新 11 本と import 元、提案 96 本の順序、96 seed の発見集合 |
| `oracle-fixed-values.json` | 親の独立 oracle (固定 4 値と現行 85 の正例対照) |
| `verify-impl.json` | 親の検算 (tuple 順序・exact-85 literal・歴史 scope の byte 同一・現行 scope・固定値・timeout) |
| `exact85-reachable.json` | exact-85 が現行 production の capture で生成されることの実測 (DW-O13) |
| `stale-tree-locks.json` | tuple 前進後に旧 grammar の lock が固定木から記録された件数 (exact-63 で 25 本) |
| `pin_closure.log` / `overlap_scan.log` | DW-O09 の pin 閉包、他 worktree との編集面重複走査 |
| `mutation-spec-probe.json` / `mutation-spec-probe-m12b.json` / `mutation-spec-final.json` / `mutation-observed.json` | 変異 spec と probe の観測 node |
| `mutation-probe.json` / `mutation-probe-m12b.json` / `mutation-final.json` | 変異台帳。`stdout` / `collection` を `{omitted, bytes, sha256}` に置換した要約版で、原本は job dir に残し `_summary_of.original_sha256` で束縛 |
| `verbatim/` | brief、measured-facts、plan、lens A/B、裁定、author 報告、review A/B、対応表、焦点走要約、変異台帳の文章、親 probe script 7 本の逐語 |
| `verbatim-normalization.json` | DW-S07 の可逆最小正規化 (codex 出力 4 本の行末 2 空白のみ、原文 sha256 と byte 数を記録) |

### verbatim の可逆最小正規化 (DW-S07)

codex の出力 4 本 (`s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s5-author.md`) は行末に 2 空白を持つ行があり、
`git diff --check` に抵触する。可視文字を変えない範囲で行末空白だけを除去し、原文 sha256・byte 数・対象行番号・
除去した文字列・正規化後 sha256 を `verbatim-normalization.json` に記録した。原文は job dir と codex receipt の
`output_sha256` が持つ。
### 受入 attempt 1 の赤 1 件と是正 (2026-09-21)

受入全走 attempt 1 (門番 11:15 通過、11:47 投入、12:10 終了) は **1 件だけ赤**になった。

- node: `orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- 主張: 所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) が `pytest --collect-only orchestrator/tests` の
  node の **90% 以上**を覆うこと。観測は **89.783890%**。

**帰属 (親の実測):** 台帳に未登録の実行 node は全体で約 2757 件あり (分母 ≈ 26,988)、そのうち**本 wave が触れた 4 test file に
属するものが 433 件**である (`test_artifact_admission` 195 / `test_t671_source_binding` 132 / `test_layer3_report` 57 /
`test_campaign_lock_codec` 49)。本 wave の新設 test (exact-85 の正例・負例 10 関数 = 111 node) と、同 file の既存
parametrize の未登録分 (322 node、前段 wave の 22 本 drift parametrize を含む) がこれに当たる。
残り約 2300 件は他 wave 由来で、別 wave が全面 refresh で扱うため本 wave は触らない。

**是正 (Codex author、commit `b820bbaa7`):** 433 件を、本 wave の受入 JUnit を
`tools/update_acceptance_duration_ledger.py --add-only` に通した canonical な実測値のまま追加した。
既存 24,379 件の key と値は byte exact に保ち、`nodeid_count` を 24,812 へ追随させた。
親の検算: key 集合 == 変更前 ∪ 433 / 既存値不変 / 追加値が入力と一致 / 余分な key なし。
**閾値 (90%) は下げていない。** 追加後の被覆率は約 91.4% (分母 ≈ 26,988 の実測ベース見積り、実値は再走で確認)。

台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) は path 上「実装面」なので、親は直接編集せず
Codex `role=author` の fix 子が書いた (D95)。

### 受入 final2 と land (2026-09-21)

- 是正 commit `b820bbaa7` の後、焦点走 f2 (job `15021.nqsv`、被覆率 test・台帳 consumer・変更 test file・docs 検査 test の 10 file) が
  **2461 passed / 4 skipped / 赤 0** (31.35 秒)。
- 受入全走 final2 (門番 12:21 通過、12:23 投入、12:32 終了): **verdict = child-green、child_rc 0、赤 0・flake 0**
  (tested main `6496ab2dc` / tested tip `6fa7a2b75`、受領証は job dir の `acceptance-receipt-final2-1.json`)。
- land: tested tip を local main へ ff-only 取り込み、同じ lock 内で spool を fold。worklog entry **1794**、
  decisions **D2203** (直前 grammar を corpus 未確認で同 commit 収載する政策判断) と **D2204** (発行器先行の次段)、
  failures は F106 の再発追記。fold 後の main は `eaeaeb388`。
