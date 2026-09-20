# [T-2344] enforcement source closure を 63 → 85 path へ 1 段進めた — 現行 63 の直接 import 先 22 本を収載し、exact-63 を歴史閲覧 grammar として収載した

- 日付: 2026-09-20
- wave: dev-wave-t2344-closure-stage (branch `worktree-dev-wave-t2344-closure-stage`)
- 起点: ユーザー直接指示 (2026-09-20、`/dev-wave` 引数)。「収載 tuple を D1075 の推移閉包 (発行器起点を含む候補) へ向けて 1 段進める。
  次の変更単位に含める段は wave が決めてよいが、閉包が閉じるまで『certified 経路が source-bound である』を推移閉包の意味で名乗る文言は
  広げない。tuple 順は epoch の preimage に効くので curated 順を保ち、policy epoch の追随 test を同 commit で更新する。Codex author (D95)、
  収載追加の正例と未収載検出の負例の変異。着手直前の local main から fresh worktree。規律 2 を緩めない。本題だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外」。起票は `docs/archive/worklog-phase3-0905-1279.md` の [T-2344]、裁定は D1884。
- 正本: D1075 (推移閉包へ、段階可、文言は閉じるまで広げない)、D1884 (段階実装の継続、範囲は wave が決める)、D1653 / D1770 (旧 grammar は
  歴史閲覧限定 decoder、収載は実在 corpus が確認できた grammar だけ)、D2081 (scope 文言は日付・commit 付き測定事実)。設計判断は本 wave の
  decisions fragment。一次資料 (先行) は `output/insights/2026-09-09/t2344-closure-reachability/`。
- 基準: local main `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` で着手 (worktree 作成直後に ff-only)。
- 実装 commit: `65e94a3a7` (段 5、Codex author)、`5bfb5fec0` (段 6 fix 1、Codex author)、`95b5d8d3d` (受入赤の fix 2、Codex author)。
- authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾)。

## 1. 何をしたか

| 項目 | 変更前 | 変更後 |
|---|---|---|
| `CONTRACT_LOADER_RELATIVE_PATHS` (`orchestrator/campaign/campaign_lock.py`) | exact 63 path | **exact 85 path** = 既存 63 (順序不変) + 現行 63 起点の 1 段目 22 本 (path の sorted 順で末尾へ) |
| 歴史閲覧 grammar (`decode_historical_campaign_lock`) | 現行 / exact-62 / pre-T733 24 | 現行 85 / **exact-63** / exact-62 / 24 の 4 分岐。exact-63 は独立 ordered literal `T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS` + 兄弟 validator (T-2483 と同型) |
| 通常 decoder / encode / resume / certified admission の v2 authority grammar | exact-63 のみ | **exact-85 のみ** (union にしない、D1653) |
| `CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `_EXCLUDED_SCOPE` (`artifact_admission.py`) | curated exact 63 path; 2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63 / 未収載 99 | curated exact 85 path; 2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85 / 未収載 78 (D2081 形式、内訳は書かない) |
| exact-63 の歴史 scope | — | 変更前の現行 2 文言を `T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_*` として byte 同一で凍結 (D2081 訂正後の最終現行 scope) |
| `contract_loader_binding.py` | docstring「exact 63 path」 | 「exact 85 path」 (コードは不変) |
| test | 63 の独立 literal・固定値 | 独立 literal (24 + 39 + 22)、固定 known-answer 4 件、scope 文言、layer3 の歴史 param `[63, 62, 24]`、`CURRENT_E0_EPOCH`、git timeout の派生 literal (10 秒 × 85 = 850) を追随。exact-63 の正例・負例 (codec 4 関数 + admission 5 関数、param 展開 78 件)、新 22 本の drift 拒否 (22 件) を新設。既存テストの期待値は変えていない |

**収載した 22 本と import 元** (着手 commit で probe が数えた、現行 63 の直接 import 先と package 初期化。新規の `__init__.py` は 0 本):
`calibrator/{analyze, benchparse, model, perfparse, tsc}.py`、`campaign/{agent_outputs, backoff_hole_grammar, durable_root, materializer_admission,
p3_b4_admission_record, p3_b4_closed_critic, p3_s4_loop, p3_s4_loop_sort, p3_s4_loop_trigger_gating, paper_story_a1_source, pin, reflux_result_evidence,
s8b_compiler_input, s8b_expected_materialization, silo_ladder_rung1, sort_swo_dependency_material}.py`、`critic/digest.py`
(import 元は `layer1-edges.json`)。T-2344 一次資料が 2026-09-09 に挙げた 1 段目の drift 2 本 (`analyze.py`、`backoff_hole_grammar.py`) と、
認証受理 API で関数本体まで実行された未収載 4 本のうち 2 本 (`materializer_admission.py`、`backoff_hole_grammar.py`) を含む。

**epoch の hash 式は不変** (`campaign-verifier-epoch/v1` + 宣言順の path\0blob)。scope は preimage に入らない。既存 63 の宣言順を動かさないので、
記録済み exact-63 lock の歴史 epoch は変わらない。**固定 known-answer 4 件** (test 実行時に production からも期待列からも再計算しない、D1652):
合成 E1 epoch `E1:bc8a6c8c…423dc7`、順序付き path sha256 `bea36246…6b5a1`、exact-63 の固定 epoch `E1:73f334f6…8ced2` と path sha256 `2247e531…399ec`
(後 2 者は変更前の現行固定値と同一 — 63 path が 85 list の先頭 63 で index 不変のため)。親の独立 oracle (`oracle-fixed-values.json`、現行 63 の対照が
変更前の test 固定値と一致することで正例対照済み)・段 2 plan・段 3 レンズ A・実装子の 4 者で一致。

## 2. 実測 (親、着手 commit f94b61fc8)

T-2344 一次資料の probe 原本 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py` ほか) を書き直さずに実行した。

| 集合 | 09-09 (2143a49c0) | 09-16 (a1b40608c、T-2482) | **09-20 (f94b61fc8)** |
|---|---:|---:|---:|
| 収載 tuple | 63 | 63 | 63 → **85 (本 wave)** |
| tuple 起点の静的 import 発見集合 | 140 | 162 | **163** (85 seed でも同一集合、`closure85-check.json`) |
| 未収載 | 77 | 99 | 100 → **78** |
| 現行 63 起点の 1 段目 | 81 (未収載 18) | — | **85 (未収載 22)** |
| 発行器 6 本起点の発見集合 / 和 | 160 / 165 (未収載 102) | — | **168 / 173 (未収載 110 → 88)** |
| 発行器起点にだけ居る module | 25 | — | **10** |
| 2 段目まで広げたときの追加数 | — | — | 23 (参考) |

引数の「候補 165、未収載 102」は 09-09 の値で、着手時は 173 / 110 だった。

**記録済み campaign.lock の grammar 分布** (root 19 個、lock 92 本、`lock-grammars.json`): authority 無し 32、24-key 29、62-key 6、**63-key 20**、
旧 exploration の 12 / 8-key 5。63-key 20 本は**すべて** wire key 列が `sorted(現行 63)` と exact 一致し (`exact63-locks-verify.json`)、記録 commit 9 件
(`7f17e1c63` 〜 `8737cacb4`) の `CONTRACT_LOADER_RELATIVE_PATHS` 宣言順は現行 63 と同一 (`exact63-declared-order.json`)。D1653 の「実在 corpus が
確認できた grammar だけ」は exact-63 について成立する。所在: B-10 formal `t2500-formal` 6 本、`t2266-formal` 3 本、`t2418-explore` 3 本、
paper-story A-2 `t2489-20260918a` 2 本、A-6 `a6-20260909b` 1 本、B-7 fixed5 `b7f5-20260919a` 3 本、`t2228/attempt-20260917b-official` 1 本、
`t1998-balanced-stock-inline-runs` 1 本。走査 root に K2 手動 loop の durable root は含まない (件数は走査範囲内の値で全影響数ではない)。

**pin 閉包** (DW-O09、`pin_closure.log`): 変更 3 file の path・変更前 sha256 で走査。凍結 manifest で pin されるものは 0 件。A-1 receipts と K2 layer3 report の
sha256 は記録 (当時の事実、規律 7) で変えない。B-4 projection hash / admission receipt validator に `artifact_admission.py` の全 bytes が入る (D2081 が既に限界として記す)。

## 3. 段 2・3 の所見と裁定 (逐語は verbatim/)

段 2 plan は T-2429 (末尾 append) + T-2483 (兄弟 validator) の同型を採り、固定値 4 件を独立計算した。段 3 は 2 レンズ (A: 正しさ境界、B: 整合・実効性・過剰) を
親 brief 込みで攻撃させた。real 9 / refuted 8。主なもの:

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 subset 許容の変異は `KeyError` で赤くなり単一理由でない | real | 変異事前登録から外し superset / order で代替 |
| A-2 「63 を現行分岐へ流すと拒否 test が赤」は逆 (落ちるのは歴史正例) | real | (P5) 訂正 |
| A-3 「bytes が変わる commit は受理を変えない」は条件不足 | real | 「記録 E1 と現在 E1 の差は拒否理由にならない (D1163)、current capture と他の受理述語は従来どおり」に限定 |
| A-4〜A-8 certified への抜け道・順序取り違え・恒真化・計数規則 | refuted | 不変条件の裏取り |
| B-1 85 / 163 / 78 を f94b61fc8 の実測と書くのは偽 | real (must-fix) | 親が 85 本を seed に同 commit で再測 (163 / 78) し、文言を「f94b61fc8 の source 木、本版の 85 path を起点」に |
| B-2 22 本は許容、発行器の穴は残る。(P1) の却下理由は不正確 | 段階選択 refuted / 理由 real | 22 本維持、発行器起点の 10 本 + 発行器 6 本は次段の候補 (§8) |
| B-3 「63 key 20 本」≠「exact-63 grammar 20 本」 | real | 20 本の wire 列と記録 commit 9 件の宣言順を exact 照合 (§2) |
| B-5 「記録 commit か HISTORICAL_RAW で足りる」は最新 checkout での certified 再解析運用を救わない | real | §5 で開示、裁定パッケージ候補 (§8) |
| B-6 dirty 拒否は本走・受入とは衝突しない (K2 launcher と受入は tracked dirty を既に拒否)、焦点走は commit 後に | 一般論 refuted / 焦点走 real | 親は焦点走を commit 済みの木で実施 |
| B-8 変異の「未収載検出」の名乗りは広すぎる | real | 収載追加の回帰 / 歴史可読性 / 未知 grammar 拒否 / certified 隔離 の 4 群に分けた |
| B-9 受入増分「約 3 秒」は 63 件分だけ | real | 受入の実測 wall を §7 に記録 |

## 4. 段 6 レビューと fix (DW-O16 の対応表)

レビュー A (正しさ境界・検出力) と B (過剰・削除・名乗り) は独立に同じ唯一の real 所見を出した。

| 所見 | 判定 | 状態 |
|---|---|---|
| RA-1 / RB-1 焦点走 f1 の赤 3 件 = `test_t671_source_binding.py` の git timeout 期待値 630 (10 秒 × 63) の追随漏れ 5 か所 | real (nit、成果物影響なし) | **closed**: fix 1 (`5bfb5fec0`、Codex author) で 850 = `GIT_TIMEOUT_SECONDS(10) × len(85)` (親が原データから再計算)。焦点走 f2 は 3115 passed / 0 failed |
| RA-2 exact-63 / 62 / 24 の certified 流入 | refuted | closed (不変条件 1・2) |
| RA-3 literal・宣言順・wire 順・固定値 | refuted (独立照合で一致) | closed |
| RA-4 新設 test は機構を通り、否定側は既知集合と衝突しない | refuted | closed |
| RA-5 既存 node の期待値変更は裁定の追随範囲内 | refuted | closed |
| RA-6 実 lock probe は必達を満たすが probe 実装は未監査 | 証拠上の限界 (nit) | closed (probe の source は `verbatim/probe-real-locks.md`) |
| RB-2 他 file に同型の件数依存 literal は無い、古い node 名 (`sixty_two`) は残存 | 他 file refuted / node 名 real (nit) | closed (改名しない — ledger の node 参照を守る) |
| RB-3 scope・tuple 順序の独立照合 | refuted | closed |
| RB-4 裁定外の一般化・互換 union は無い | refuted | closed |
| RB-5 test 構成 (codec 4 + admission 5 + drift 1 = 10 関数 100 ケース) | refuted | closed |
| RB-6 旧 63 の certified 再解析喪失は実装どおり、C の実測は代表 4 件 | 開示 (nit) | closed (§5 に「代表 4 件」と書く) |
| **受入 attempt 1 の赤 1 件** `test_b10_backoff_static_tail_formal.py::test_formal_loader_rejects_real_exploration` = 実在の exploration campaign (`b10-backoff-grid-t2418-explore`、exact-63) を certified 経路に渡し `not formal` を期待していた test が、decode 段 (exact key 集合不正) で拒否されて message 不一致 | real (本 wave 起因 = §5 の受理集合変化そのもの。production は D1653 どおり) | **closed**: fix 2 (`95b5d8d3d`、Codex author) で主張を「実 exact-63 は decode 段拒否」と 「not formal は現行 85 grammar の合成 campaign (run_kind を t2418-explore にした certified lock) で検査」の 2 node に分けて残した (regex の緩和・skip なし)。単独走 f4 緑。逐語は `verbatim/acceptance-red-1.md` / `verbatim/s6-fix2.md` |

fix は 2 巡 (fix 1: test file 1 本・5 literal、fix 2: test file 1 本・2 node)。焦点再レビューの codex 子は投入していない (fix 1 の派生値 850 は親が式から再計算し f2 の緑で閉じ、fix 2 は親が裁定 §6 の開示と junit 本文で帰属を判定し f4 の緑で閉じた)。

**静的レビュー 2 本と焦点走 3 本が受入赤を取り逃した理由 (F474 の再発として failures へ):** 当該 test は `campaign_lock` / `artifact_admission` の symbol を参照せず、`b10_backoff_static_tail_formal` 経由で実 外部 root (`/work/1/SFC/tanab/`) の記録済み campaign (旧 grammar) を読む。記録済み成果物は「変更した値を別の形で持つ consumer」で symbol grep にも literal grep にも掛からない。受理集合を変える wave は実 外部 root を読む test (2026-09-20 時点 14 file) を参照関係に依らず焦点走へ加える (memory へ記録。DW-O26 は予算満杯)。

## 5. 受理集合の変化 (開示、DW-G05) と実 lock での到達点

- tuple 前進後の checkout では、記録済み exact-63 campaign (走査 19 root で 20 本) は `CERTIFIED_ACCEPTANCE` の decode 段で
  「authority.contract_loader_blob_sha256s の exact key 集合が不正」として拒否され、`HISTORICAL_RAW` では新 grammar で読める (返却型は歴史型、
  epoch は `HistoricalCampaignVerifierEpoch`、現行適合 `unknown`、scope は旧 63 文言)。exact-62 のとき (T-2429 → T-2483) と同じ帰結で、D1653 / D1770 が裁定済み。
- **最新 checkout の certified consumer (`b10_backoff_static_tail_formal.load_formal_campaign`、`paper_story_a2_certification` の collect、
  `t1998_stock_inline_pair` 等) でこれらを再解析する運用は失われる。** T-1998 の再検証記録 (`output/insights/2026-09-15/t1998-landed-main-recheck/`) は
  測定 commit の consumer 欠陥を後日の main で直して同じ成果物を accepted にした実例で、「記録 commit へ戻す」では修正を失う。回避は
  修正済み exact-63 checkout の保存か新 grammar での再測定で、本 wave は decoder / purpose を緩めない (§8 の裁定パッケージ候補 2)。
- 新 22 本は capture の clean committed 要求の対象になる。K2 launcher (`tools/pegasus/p3_s4_loop_pegasus.sh`) と受入の clean preflight は既に tracked dirty を
  拒否するので本走は変わらない。開発中に loop / critic を編集した checkout で実 certified admission を通す test は新たに赤になる (commit 後に走らせる)。
- **実 lock probe** (`real-locks-probe.json`、親が repo 外から commit 済み wave 木の code で実行、source は `verbatim/probe-real-locks.md`):
  必達 A (20 本すべて `decode_historical_campaign_lock_bytes` 成功、記録 tuple = exact-63 literal) **20 / 20**、
  必達 B (代表 4 本 — t2500-formal balanced 09-19、A-2 t2489 rr5 / rr50、t1998 — で `require_campaign_verifier_epoch(HISTORICAL_RAW)` が
  `HistoricalCampaignVerifierEpoch` E1・旧 63 scope・`unknown`) **4 / 4**、必達 C (同 4 本で通常 decoder が `CampaignLockCodecError`、
  CERTIFIED_ACCEPTANCE の epoch API が拒否、理由はいずれも exact key 集合) **4 / 4**、対象 lock の sha256 は前後で不変。
  C は代表 4 件の実測であり、20 件すべてへの拒否は grammar 検査からの静的結論である。

## 6. 変異 matrix (DW-M01〜M08)

事前登録は `verbatim/s4-ruling.md` §5 (4 群: 収載追加の回帰 / 歴史可読性 / 未知 grammar 拒否 / certified 隔離)。subset 許容の単独変異は
`KeyError` で赤くなり単一理由にならない (レンズ A 所見 1) ので登録せず、superset / order で代替した。harness は `tools/mutation_harness.py`
(dispatch、spec は repo 外、HEAD blob 束縛)。runner は `tools/run_tests.py <焦点 file> -q -rf --force-dispatch`。

**probe 走** (`mutation-spec-probe.json` sha256 `423c8659…`、12 変異 全件 SURVIVED 期待で観測 node を集める、runner 5 file = codec / admission / t671 / layer3 / s1_9pair、
`mutation-probe.json`): baseline 緑。**対照 M0 (campaign_lock.py の comment 1 行だけ) が `test_layer3_report.py` の 5 node
(`test_accepted_report_rejects_no_commit_campaign` / `test_certified_report_omits_current_verifier_conformance` / `test_accepted_report_requires_e1_and_records_epoch` /
`test_render_accepted_persists_certifying_report` / `test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`) を落とした** = この 5 node は
実 repo の live binding を capture する drift 核で、収載 file の bytes が HEAD と違えば変異の意味に関係なく赤になる (F358 の型)。他 11 変異の観測 node は
すべてこの 5 を含み、5 を除いた非 drift の赤は事前登録の対象 test と一致した (`mutation-final-derivation.json`)。

**final 走** (`mutation-spec-final.json` sha256 `642b0474…`、runner から `test_layer3_report.py` を外し drift 核を除く。layer3 の追随 (歴史 param 63・現行 85 ラベル) は
焦点走 f2 の緑が担保。期待 node = probe の観測 node − drift 核 − layer3 node、`mutation-final.json`): **baseline 緑、M0 SURVIVED、他 11 変異すべて KILLED で期待 node と完全一致 (matching 12 / 12、rc=0)。** 木は各変異後に HEAD へ復元 (harness の fail-closed 検査)。

| 群 | 変異 | 期待 node 数 (final) | 代表 node |
|---|---|---:|---|
| 対照 | M0 comment だけ (positive、SURVIVED 期待) | 0 | — (probe では drift 核 5 だけ) |
| 収載追加の回帰 | M1 85 tuple から `calibrator/analyze.py` を削除 | 271 | `test_t671::test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths`、admission の固定 epoch |
| 収載追加の回帰 | M2 追加 22 本の隣接 2 本を production だけで交換 | 182 | 同上 (独立 literal・固定 epoch・順序 sha) |
| 収載追加の回帰 | M3 live 照合で `p3_s4_loop.py` を skip | 2 | `test_t671::test_live_verification_rejects_each_dirty_enforcement_source[p3_s4_loop.py]` |
| 歴史可読性 | M5 exact-63 分岐を pre-T733 validator へ流す | 65 | codec / admission の exact-63 正例、blob mismatch 63 件 (codec 拒否で到達不能) |
| 歴史可読性 | M7 63 literal の worker path を置換 | 67 | 同上 + 独立 literal 不一致 |
| 歴史可読性 | M8 63 literal の末尾 2 要素を入替 (宣言順) | 4 | admission 正例の固定 E1 (D1652)、codec の宣言順 test |
| 歴史可読性 | M9 exact-63 の committed blob 照合を省略 | 63 | `test_t2429_exact63_rejects_each_recorded_commit_blob_mismatch[*]` 63 件 |
| 歴史可読性 | M10 (both-layers) exact-63 分岐に 62 scope を与え、62 scope → 63 tuple の対応も変える | 4 | 63 と 62 の歴史正例・scope/map 対応 test |
| 未知 grammar 拒否 | M11 authority 白名単を superset 可へ | 2 | `test_t2429_exact63_authority_requires_exact_declared_order` (+ 62 の同型) |
| 未知 grammar 拒否 | M12 63 validator の wire 比較を集合比較へ | 1 | `test_t2429_exact63_rejects_unknown_grammars[order]` (validator 直接呼出し) |
| certified 隔離 | M13 通常 decoder を exact-63 との union へ | 2 | `test_t2429_exact63_remains_rejected_by_normal_decoder`、`..._is_rejected_for_certified_use` |

kill は受理集合か fail-closed 挙動が期待方向へ変わった赤だけを数え (DW-M03)、drift 核の 5 node は kill に数えない。M10 は両層変異で、単層では
`_RecordedCampaignVerifierEpoch` の exact 検査が fail-closed (TypeError) で受け止める (冗長 gate の実在、DW-M02)。

## 7. 検査・受入

- 焦点走 (DW-O26、23 file = 変更 test 5 + symbol consumer 15 + 実 certified admission を通す loop / critic 3、計算ノード dispatch):
  f1 (`65e94a3a7`、job 13633.nqsv、Elapse 39 s) 3112 passed / 3 failed (§4)、f2 (`5bfb5fec0`、job 13649.nqsv、Elapse 40 s) **3115 passed / 0 failed**。
- 全史 provenance 監査 (`check_ai_provenance.py`): 12061 件、新規違反なし (実装 commit 後)。
- 焦点走 f3 (merge 後の tip、DW-O26 改訂版 (T-2813) の inventory 4 群 `test_campaign.py` / `test_official_perf_closure.py` / `test_p3_exploration_namespace.py` / `test_p3_b4_wiring_probe.py` + 変更 test 5 file): job 13858.nqsv、Elapse 44 s、**1721 passed / 3 skipped / 0 failed**。
- 焦点走 f4 (fix 2 後、`test_b10_backoff_static_tail_formal.py` 単独走): job 13908.nqsv、Elapse 14 s、**69 passed / 0 failed**。
- 受入全走 attempt 1 (tip `43c32588b` = 記録 commit + main `6305f2d05` の merge、3 shard): 赤 1 件 (上の受入赤、F945 型でないので script が停止)。fix 2 後に同系列の最終 tip へ再投入する。受領証は job dir (`acceptance-receipt-*.json`) と land の記録が持つ。件数は本文へ書かない (書けば tip が変わり取り直しになる)。

## 8. 裁定パッケージ候補 (本 wave では実装しない)

1. **次段の順序** (レンズ B 所見 2): 発行器 6 本 (`s8b_oracle_report` / `autonomous_trial_completeness` / `b10_backoff_shape_sweep` / `backoff_extended_sweep` /
   `backoff_extended_sweep_report` / `backoff_overthrottle`) と発行器起点にだけ居る 10 本を先に収載するか、tuple 起点の 2 段目 (23 本) を先にするか。
   D1884 の目標内で wave が決めてよいが、発行器を先にする方が D1884 が名指しした穴 (発行器自身が束縛されていない) に直接効く。
2. **記録済み exact-63 成果物の「最新 consumer での certified 再解析」を続けるか** (レンズ B 所見 5): (a) 修正済み exact-63 解析 checkout の保存、
   (b) 新 grammar で再測定、(c) 現状維持 (HISTORICAL_RAW と記録 commit)。D1653 / D1770 だけでは (a)(b) の選択は決まらない。

## 9. 測定の射程 (この結論が言えないこと)

- 「certified 経路が source-bound である」を推移閉包の意味では名乗らない (未収載 78、発行器起点の和で 88 が残る)。本 wave は 1 段目の束縛を足しただけである。
- 静的発見集合 163 は import 文だけを辿った上界で、production 実行到達を証明しない (一次資料と同じ限定)。
- 記録済み exact-63 lock の件数 20 は走査 19 root の値。K2 手動 loop の durable root は走査していない。
- 変異 matrix は焦点 5 file の runner に対する検出力で、受入全走の検出力ではない。

## 10. 工数

codex 子 9 本 (plan 1、consult 2、author 2 (v1 は編集許可の不一致で即停止・変更 0)、review 2、fix 2、全て gpt-6-astra / medium)。
計算ノード job: 焦点走 4 (f1 / f2 / f3 / f4) + 変異 probe 13 run + final 13 run + 受入 2 回 (attempt 1 赤 1 件、最終 tip で再投入)。段 5 author v2 は 851 s / 26 call。

## 成果物

| ファイル | 内容 |
|---|---|
| `closure-head.json` / `producer-universe.json` / `layer1-edges.json` / `closure85-check.json` | 着手 commit の閉包寸法、発行器起点、22 本と import 元、85 seed の閉包 |
| `lock-grammars.json` / `exact63-locks-verify.json` / `exact63-declared-order.json` | 記録済み lock の grammar 分布、20 本の wire 列 exact 照合、記録 commit 9 件の宣言順 |
| `oracle-fixed-values.json` | 親の独立 oracle (固定値 4 件と現行 63 の対照) |
| `real-locks-probe.json` | 実 lock 20 本での到達点 A/B/C |
| `pin_closure.log` / `overlap_scan.log` | DW-O09 の pin 閉包、他 worktree との編集面重複走査 |
| `mutation-spec-*.json` / `mutation-probe.json` / `mutation-final.json` / `mutation-final-derivation.json` | 変異 spec と台帳 (probe / final)。台帳 2 本は `artifact.stdout` と `procedure.collection` を `{omitted, bytes, sha256}` に置換した要約版で、原本 (2.95 MB / 2.01 MB) は job dir に残し `_summary_of.original_sha256` で束縛 |
| `focus-runs.md` | 焦点走 3 本 (fix 前 / fix 後 / merge 後 + inventory 4 群) の job ID・所要・合否・赤 node と raw log の sha256 (raw log は末尾空白のため job dir に残す) |
| `verbatim/` | brief、measured-facts、plan、lens A/B、ruling、author v1/v2、review A/B、fix 1、受入赤 1 件の裁定、fix 2、probe script の逐語 |

### verbatim の可逆最小正規化 (DW-S07)

codex 子の出力 9 本は行末に Markdown の hard break (半角空白 2 つ) を持ち `git diff --check` に抵触するため、**行末の空白だけ**を除去した (可視文字不変)。復元は下表の行の行末に半角空白 2 つを付ける。原文は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/`) の元 file と codex launcher の receipt (`output_sha256`) に残る。記録は `verbatim-normalization.json`。

| file | 行 | 原文 sha256 (bytes) | 正規化後 sha256 (bytes) |
|---|---|---|---|
| `verbatim/s2-plan.md` | 489, 490, 491, 492 | `dc9a4e154524998af4564998c90f4dc6317abbe686554036e07115f32e15ae7b` (34384) | `b14aed23b929689a29d78d59e61b56a1079d8ad13f344370ce48de7a9df8d8a6` (34376) |
| `verbatim/s3-lensA.md` | 110, 111, 112 | `9f2870abc5cbc34f2d7d029127b3e562815959a2226b5330f8c5f40da35ed877` (11940) | `c7235a84296bc19144c771353a55c037fa34fa4c0279152c789f68a2fad67ae9` (11934) |
| `verbatim/s3-lensB.md` | 15, 32, 65, 74, 141, 142, 143 | `457579d67f2e5578492e9697e20fae745d23a8acc3b412499e6744e4ac7c8924` (13681) | `7ea5437c46abeaa2a815daaa1a85b35e22166c8268afbe4c3eaace41e5a7e829` (13667) |
| `verbatim/s5-author-v1-stopped.md` | 39, 40, 41 | `1db8e1403fd43da9f54375a2752cc68ebc5d4f0fe16be5c01259d02db98f5104` (3060) | `df023b0876cd0938bbbf62fd5f120e095ff371def73867f84ebcf22e113bc0a4` (3054) |
| `verbatim/s5-author-v2.md` | 325, 326, 327 | `1e3cde5fa2e215ceffe7949c2b9172807ed6c70763483269e1fa14e53f440fda` (34020) | `ac91c789ce965151be085f60a8dd1b7c5f3639f84efb9abdea665a057268f3b7` (34014) |
| `verbatim/s6-fix1.md` | 21, 22 | `4a7f61fbbc4dab9b09bade550ae9cd9e55d4d4d21c3c9fbc515d2ece9c44b243` (1458) | `aaf22bce8e0e9ebc3f4bd32f4b7b7b79ca5cf71f6cf87d1cf6b1cb86aba064e2` (1454) |
| `verbatim/s6-reviewA.md` | 7, 8, 19, 20, 33, 34, 47, 48, 57, 58, 67, 68, 73, 74, 75 | `c6145a797a3e450372d62ddc88def35d3999ff0eaa3baf38702d08c4a5a9f91e` (8151) | `5360d783cfae9543beb8a62c2ce0469443b003a87f144becf0f3a260803fc62b` (8121) |
| `verbatim/s6-reviewB.md` | 75, 76, 77 | `9ff5d55c8a47ce7393ce0375f4ae409009f032f3d1913c5f2174b001e66b7506` (7301) | `f2b25dfc4cc01de2afa3d5a5c9a5b17b25664ddbfaa3d7b5f97102b15c3ddf81` (7295) |
| `verbatim/s6-fix2.md` | 27 | `c50cdbe2981ba590b796e5ac54644976ecab516cc4a60095ad9f2b2d9a0359ca` (1420) | `42be28cb4ac8ea351383e23acb3a1839b7a81880e8a37af87ef3f0049532d448` (1418) |
