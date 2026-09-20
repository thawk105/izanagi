# 段 4 裁定 — [T-2344] enforcement source closure を 63 → 85 へ 1 段進める

裁定日時: 2026-09-20 21:30 JST。着手 commit `f94b61fc8`。裁定 inbox の再走査: local main は `799d38b97` (T-2766 の conftest / 受入 pairing、
paper-intro 稿) へ進んだが、decisions の新規 D は D2188 (受入 pairing) のみで本件に関わる裁定は無い。実装面の差分は `conftest.py` と
`test_acceptance_schedule_order.py` だけで本 wave の編集面と重ならない。

## 1. 所見の裁定

| 所見 | 判定 | 対応 |
|---|---|---|
| A-1 subset 変異は受理拡大でなく `KeyError` で赤くなる | real (plan の変異設計) | 採用。§5 で変異ごとに「期待する失敗段 (codec 拒否 / blob 拒否 / live 拒否 / 固定値不一致)」を固定し、`KeyError`・fixture 破壊・import error の赤は kill に数えない (DW-M03) |
| A-2 「63 を現行分岐へ流すと拒否 test が赤」は逆 | real (親 brief (P5)) | 採用。落ちるのは歴史読取の正例。§5 で訂正 |
| A-3 「bytes が変わる commit は受理を変えない」は条件不足 | real (親 measured-facts §5) | 採用。「current capture と他の受理述語が成功する限り、記録 epoch と現在 epoch の差だけでは拒否しない」に限定する。A-2 submit-tree 運用の一般化も撤回 (B-5 と併せて §6) |
| A-4 exact-63 → certified の抜け道 | refuted | 採用。不変条件 1・2 の裏取り。「通常 decoder は exact-85 のみ」は **v2 authority grammar に限る** (v1 は decode され certified で E0 拒否) と明記 |
| A-5 wire 順 / 宣言順の二段検査 | refuted (説明の補正) | 採用。production literal 自体の並べ替えは runtime 白名単でなく独立 literal・固定 epoch test が検出する、と記録 |
| A-6 末尾 append で歴史 63 epoch は動かない | refuted | 採用。固定値 4 件は親 oracle・plan・レンズ A の 3 者で一致 |
| A-7 否定側の棚卸しは既知 grammar と衝突しない | refuted | 採用。63 の subset は `env_contract.py` を落とす (末尾 worker を落とすと既知 62)。先例の `paths[:-1]` を複製しない |
| A-8 163 / 85 / 22 の計数規則 | refuted | 採用。レンズ A が probe 原文で独立再計算し一致 |
| B-1 85 / 163 / 78 を f94b61fc8 の実測と書くのは偽 | real (親 brief (P4)・plan §2) | 採用・**must-fix**。親が `f94b61fc8` の source 木で **85 本を起点に**全展開し 163 (未収載 78) を実測した (`closure85-check.json`)。文言は §2 の確定文字列。内訳 (63 + 22) は書かない |
| B-2 22 本は許容、発行器の穴は残る。(P1) の却下理由は不正確 | 段階選択 refuted / 理由づけ real | 採用。(P1) は維持。理由を「再現可能な BFS 深さ 1 で、drift 2 本と production 到達 2 本を含む」に限定し、発行器起点の 10 本 + 発行器 6 本は D1884 の目標内で**次段の候補**と記す。順序の優先は裁定パッケージ候補 (§7) |
| B-3 「63 key 20 本」≠「exact-63 grammar 20 本」 | real (親 measured-facts §3) | 採用。親が 20 本すべての wire key 列を `sorted(現行 63)` と exact 照合し **20/20 一致**、記録 commit 9 件の宣言順も現行 63 順と同一 (`exact63-locks-verify.json`、`exact63-declared-order.json`)。「19 root の走査で 20 本」と「全影響数」は分ける |
| B-4 exact-63 の歴史 scope を現行 2 定数から凍結 | refuted | 採用。「exact-63 の最終現行 scope (D2081 訂正後) を凍結」と記す |
| B-5 「記録 commit か HISTORICAL_RAW で足りる」は最新 checkout での certified 再解析運用を救わない | real (親 brief / measured-facts §5) | 採用。本 wave は decoder / purpose を緩めない (D1653 必須条件・規律 2)。失われるものを §6 に明示し、裁定パッケージ候補 (§7) へ |
| B-6 dirty 拒否は増えるが K2 本走・受入とは衝突しない。焦点走は commit 後に | 一般論 refuted / 焦点走 real | 採用。親は実 certified consumer を含む焦点走を commit 済みの木で行う。capture の mock 互換層は作らない |
| B-7 過剰なし・必要な局所追随は含まれる | refuted | 採用 |
| B-8 変異の「未収載検出」という名乗りは広すぎる | real (親 brief (P5)) | 採用。§5 で主張を 4 群に分ける |
| B-9 「約 3 秒」は 63 件分だけ | real (親 measured-facts §5) | 採用。ledger 静的集計: exact-63 の 63 件 ≈ 2.82 worker 秒、T671 の 4 系列 63 → 85 ≈ +21.55 worker 秒、ほか未集計分あり。受入実走で wall と実増分を記録する |

## 2. プラン v2 (確定)

段 2 plan を次の補正つきで採用する。

1. `orchestrator/campaign/campaign_lock.py`
   - `:47` comment を `exact 85 path` に。`CONTRACT_LOADER_RELATIVE_PATHS` は既存 63 の順序不変 + 22 本を path の sorted 順で末尾へ (plan §1 の 85 行をそのまま)。
   - `T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS` を `T733_EXACT62_...` の直後に**独立 ordered literal** (現行 63 と同一内容・同一順) として新設。slice / 連結にしない。
   - `HistoricalCampaignLockAuthority.__post_init__` の白名単に追加。兄弟 `_validate_t2429_exact63_historical_authority` (62 版の複製、tuple 参照 3 か所だけ変更)。
   - `decode_historical_campaign_lock` を 現行 85 / exact-63 / exact-62 / pre-T733 24 の 4 分岐に。docstring 更新。既存 24 / 62 の検証順・例外文面・返却値は 1 文字も変えない。
2. `orchestrator/campaign/artifact_admission.py`
   - **確定文字列 (B-1 must-fix):**
     ```
     CAMPAIGN_VERIFIER_EPOCH_SCOPE = (
         "enforcement source closure (curated exact 85 path; source-import 推移閉包ではない; "
         "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
         "2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85)"
     )
     CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE = (
         "同実測の発見集合の未収載 78 module、同発見集合に入らない module、"
         "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
         "package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、"
         "外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり "
         "(収載 path の source bytes は委譲先であっても本 map の内)、完全性を主張しない"
     )
     ```
     (excluded は先頭の数値 99 → 78 だけが変更。identity の括弧内は測定の対象木と起点を書くもので、収載の内訳ではない。)
   - `T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE` / `_EXCLUDED_SCOPE` を、変更前 `:76-86` の 2 文字列と **1 byte も違わない**独立文字列として `:98` の exact-62 定数群の後に新設。
   - `HistoricalCampaignVerifierEpoch.__post_init__`、`_RecordedCampaignVerifierEpoch.__post_init__`、`_verify_committed_loader_binding`、`_recorded_campaign_verifier_epoch` の 4 か所に exact-63 分岐 (plan §2 の骨格どおり)。epoch hash 式は不変。scope を preimage へ足さない。`:1082` / `:1185` の説明に exact-63 を追記。
3. `orchestrator/campaign/contract_loader_binding.py`: docstring `:2,58,61` の 63 → 85 だけ。
4. テスト (plan §4 の表どおり)。追加の確定事項:
   - `test_artifact_admission.py` の固定値: `_FIXED_SYNTHETIC_E1_EPOCH = "E1:bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7"`、
     `_FIXED_ORDERED_CLOSURE_PATHS_SHA256 = "bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1"`、
     `_FIXED_T2429_EXACT63_EPOCH = "E1:73f334f62ec13c394aae3d4787b80117562187984b6e0e372f2c0f7058b8ced2"`、
     `_FIXED_T2429_EXACT63_PATH_SHA256 = "2247e5312a327caca9d0d4be081457eaf196513764010f64ccad1561409399ec"`
     (親 oracle `oracle-fixed-values.json`・plan・レンズ A の 3 者一致。実装子は自分でも算出して報告に手順を書く。D1652: test 実行時に production から再生成しない)。
   - `:1447` と `test_s1_9pair_figure_provenance.py:74-90` `CURRENT_E0_EPOCH` は上の確定文字列を**独立 literal** で置く。`FROZEN_E0_EPOCH` は不変。
   - exact-63 の新設 node は plan §4 の 9 本 (codec 4 + admission 5)。負例の変形は plan §5 の具体案 (subset = `env_contract.py` 落とし / superset = `unknown_t2344.py` / 同数別集合 / wire 順序違い) と、現行 85 から 1 本落とした 84 の歴史 decoder 拒否。
   - plan §7 の `test_t2344_certified_acceptance_rejects_each_new_source_drift` (新 22 本 parametrize) を採る。
   - 既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。
5. 変更しない: `layer3_report.py` (test の label 追随のみ)、`b10_backoff_shape_sweep.py`、`b10_backoff_static_tail_formal.py`、`paper_story_a2_certification.py`、docs 群 (日付付き既述は真のまま)。

### 新 validator の禁止 (署名で書く)

`_validate_t2429_exact63_historical_authority(value) -> HistoricalCampaignLockAuthority` は、`value` が次のいずれかなら `CampaignLockCodecError` を送出しなければならない:
`authority` の key 集合が `AUTHORITY_KEYS` と厳密一致しない / `contract_loader_blob_sha256s` の key 列が `tuple(sorted(T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS))` と厳密一致しない
(subset 62 (worker あり) / superset 64 / 同数別集合 63 / 順序違い 63 をすべて含む) / 63 path のいずれかの digest が 64 桁 hex でない / `activation_serial` が正の exact int でない。
**通る正例:** 実在する `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260919T131526Z-2235286-balanced/campaigns/t2500-backoff-static-tail-formal-silo-balanced-sweep-d7cbfe58/campaign.lock`
の `authority` object (wire 列 = sorted(63)、記録 commit `8737cacb4`)。受理され、宣言順で再構成した blob map を持つ `HistoricalCampaignLockAuthority` を返す。

## 3. 受入到達点 (実 lock での確認、親が repo 外で実行し逐語を insight へ)

- **必達 A:** 20 本すべてで `decode_historical_campaign_lock_bytes` が成功し `recorded_contract_loader_relative_paths` が exact-63 tuple。
- **必達 B:** 代表 3 本 (t2500-formal balanced 09-19 / A-2 t2489 rr5 / t1998) で `require_campaign_verifier_epoch(..., HISTORICAL_RAW)` が `HistoricalCampaignVerifierEpoch` (`E1`、旧 63 scope) を返す。
- **必達 C (規律 2):** 同 3 本で `decode_campaign_lock_bytes` が `CampaignLockCodecError`、`require_campaign_verifier_epoch(..., CERTIFIED_ACCEPTANCE)` が拒否。
- **bytes 不変:** 実行の前後で対象 lock の sha256 が変わらない (`exact63-locks-verify.json` の `lock_sha256` と照合)。

## 4. 親の実測の射程訂正

- measured-facts §5 の「閉包の bytes が変わる commit は既存 campaign の certified 受理を変えない」→ 「記録 E1 と現在 E1 の差は拒否理由にならない (D1163)。current capture と他の受理述語は従来どおり要求される」。
- 「A-2 系の collect は記録 commit の submit-tree で呼ぶ」→ 確認済みの A-1 sized attempt の運用 (memory) に限り、全 consumer への一般化はしない。
- measured-facts §3 の「20 本」→ 20 本の wire key 列と記録 commit 9 件の宣言順を exact 照合済み (§1 B-3)。走査 root 19 個の範囲での件数であり全影響数ではない。

## 5. 変異事前登録 (DW-M01、主張を 4 群に分ける。単一理由性は実装後に anchor で確認)

| 群 | 変異 | 落ちるべき node (期待する失敗段) |
|---|---|---|
| 収載追加の回帰 | production 85 tuple から `orchestrator/calibrator/analyze.py` を削除 | `test_t671_source_binding.py::test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths` (独立 literal 不一致) |
| 収載追加の回帰 | 追加 22 本のうち隣接 2 本を production だけで交換 | 同上 + `test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture` (固定 epoch 不一致) |
| 収載追加の回帰 | live 比較で `p3_s4_loop.py` を skip | `test_t671_source_binding.py::test_live_verification_rejects_each_dirty_enforcement_source[...p3_s4_loop.py]` (live 拒否が出ない) |
| 収載追加の回帰 | capture で `p3_b4_closed_critic.py` の disk 照合を skip | 新 `test_t2344_certified_acceptance_rejects_each_new_source_drift[...p3_b4_closed_critic.py]` |
| 歴史可読性 | exact-63 decoder 分岐を削除 (63 が pre-T733 validator へ落ちる) | 新 codec 正例 + admission 歴史正例 (codec 拒否で正例が赤) |
| 歴史可読性 | 白名単から exact-63 tuple を削除 | authority 直接構築の正例 |
| 歴史可読性 | 63 literal の 1 path を置換 / 宣言順を 2 要素入れ替え | codec 正例の固定期待 tuple + admission 正例の固定 E1 (D1652) |
| 歴史可読性 | exact-63 の committed blob 照合を省略 | 新 `test_t2429_exact63_rejects_each_recorded_commit_blob_mismatch[...]` (blob 拒否が出ない) |
| 歴史可読性 | exact-63 epoch を通常 `CampaignVerifierEpoch` で返す / 85 scope を割り当てる | admission 歴史型正例 (型・scope 不一致) |
| 未知 grammar 拒否 | 白名単を「63 を含む superset 可」へ緩める | 新 `test_t2429_exact63_authority_requires_exact_declared_order` の superset 直接構築 |
| 未知 grammar 拒否 | 63 兄弟 validator の wire 比較を集合比較へ | 新 `test_t2429_exact63_rejects_unknown_grammars[order]` の validator 直接呼出し |
| certified 隔離 | 通常 `_validate_authority` の受理集合へ exact-63 を union | 新 `..._remains_rejected_by_normal_decoder` + `..._is_rejected_for_certified_use` |
| 対照 | comment だけを変える等価変異 (M0、SURVIVED 期待、別 spec) | なし (harness の SURVIVED 検出の正例、DW-M02) |

登録しない: 「subset 許容へ緩める単独変異」(A-1: `KeyError` で赤くなり単一理由でない。superset / order の変異で代替)。

## 6. 受理集合の変化 (開示、DW-G05)

- tuple 前進後の checkout では、記録済み exact-63 campaign (走査 19 root で 20 本、`exact63-locks-verify.json`) は `CERTIFIED_ACCEPTANCE` の decode 段で拒否され、
  `HISTORICAL_RAW` では新 grammar で読める。**最新 checkout の certified consumer (`b10_backoff_static_tail_formal.load_formal_campaign`、
  `paper_story_a2_certification` の collect、`t1998_stock_inline_pair` 等) でこれらを再解析する運用は失われる。** T-1998 の再検証記録
  (`output/insights/2026-09-15/t1998-landed-main-recheck/`) は、測定 commit の consumer 欠陥を後日の main で直して同じ成果物を accepted にした実例で、
  「記録 commit へ戻す」では修正を失う。回避は「修正済み exact-63 checkout の保存」または新 grammar での再測定。本 wave は decoder / purpose を緩めない。
- 新 22 本は capture の clean committed 要求の対象になる。K2 launcher (`tools/pegasus/p3_s4_loop_pegasus.sh`) と受入の clean preflight は既に tracked dirty を拒否するので本走は変わらない。
  開発中に loop / critic を編集した checkout で実 certified admission を通す test は新たに赤になる (commit 後に走らせる)。

## 7. 裁定パッケージ候補 (本 wave では実装しない、insight に記録)

1. 次段の順序: 発行器 6 本 (+ 発行器起点にだけ居る 10 本) を先に収載するか、tuple 起点の 2 段目 (23 本) を先にするか (B-2)。D1884 の目標内で wave が決めてよいが、
   発行器を先にする方が D1884 が名指しした穴に直接効く。
2. 記録済み exact-63 成果物の「最新 consumer での certified 再解析」を続けるか (B-5)。選択肢: (a) 修正済み exact-63 解析 checkout の保存、(b) 新 grammar で再測定、
   (c) 現状維持 (HISTORICAL_RAW と記録 commit)。D1653 / D1770 だけでは (a)(b) の選択は決まらない。
