---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1999-define-gate-family
seq: 1
title: [T-1999] 測定条件の関門を族として設計し driver 全体へ義務化した (コード + docs、branch worktree-dev-wave-t1999-define-gate-family、変異 matrix = baseline PASSED・KILLED 5・SURVIVED 0・MISMATCH 0・期待 node 完全一致 5/5)
---

## 本文

- D1198 の未実装部分。T-2018 が call-scoped の 2 節と負例を land 済みで、残っていたのは
  patch 供給の define を build へ渡す driver 全体への義務化だった。
- **逐語の読み方が本 wave の分岐点だった。** D1198 が driver 全体へ義務づけているのは
  **効いたことの正例検査**であり、macro ごとの意味 witness を全部実装することではない。
  この読み分けで scope が確定した。段 3 のレンズ B が独立に同じ判断へ達している。
- **正例の形を binary hash 相異から前処理後 bytes の差へ変えた。** hash 案は `BACKOFF_FIXED`
  でしか成立しないと plan 自身が認めていた。前処理差なら未供給・綴り違い・写像欠落・
  条件指令へ未到達のすべてで bytes が同一になり、cache option 経由と compiler flag 経由の
  両方で成立する。無効値 (`-1` や `requested == default`) は向きを反転し、TU 到達を確かめた
  うえで stock との一致を要求する。
- **経路 2 (`-DCMAKE_CXX_FLAGS=-D<NAME>=1`) には fails-closed の保護が 1 つも無いことを実測した。**
  経路 1 の `patches/silo-backoff-fixed.patch:42` は `#error` を持つが、
  `patches/broken-*.patch` は `error` を 0 件しか持たず `#if IZANAGI_BREAK_*` を使う。
  未定義 macro は 0 と評価されるので、綴り違い・未供給・patch 未適用のいずれでも
  壊れているはずの枝が黙って選ばれない。正しさの対照を作る driver 群には
  条件が効いたことを確かめる層が現状ひとつも無かった。
- **段 6 の敵対レビュー 2 本がどちらも NO-GO を出した** (レンズ A = blocker 9、レンズ B = blocker 6)。
  core API (2 節の型・record ID・digest・status・reason の分離) は両者が健全と認め、
  欠陥は配線・昇格境界・閉包検査・record の発行束縛に集中していた。重複を除く 10 件を修正した。
  詳細は {{F:gate-implemented-but-not-firing}}。
- **強化した閉包検査が、誰も閉包に入れていなかった build sink を 3 つ掘り当てた。**
  `screening_driver.py`、`silo_ladder_rung1._build_variant`、`s8b_floor_campaign` の campaign sink。
  plan v2 の 51 sink 独立検出でも、レビュー 2 本でも、親の手検索でも出なかった。
  独立列挙 × 直積という設計の効果である。前 2 者は配線し、3 者目は t2027 所有のため繰延べた。
- **親の裁定を 2 度撤回した。** 1 度目は「単一の絞り口で fail-closed に拒否する」で、
  全閉包が必ず通る絞り口は不在と plan が反証した。2 度目は P-strict ({{D:promotion-requires-effectuation-not-meaning}})。
- **段 5・6 の fix は計 14 巡。** 空転の原因は技術的難易度ではなく、子が毎回「実装済み・未実走」で
  報告し一度も自分の修正を確かめていなかったこと。子は計算ノードへ pytest を投げられないが
  素の python は実行できるので、repo 外の診断スクリプトで直接呼ばせる形に変えたところ
  1 巡で真因に到達した。詳細は {{F:child-reports-unverified-fix}}。
- **親が自分の測定を 3 度訂正した。** patch 供給 define を 11 個と数えた件 (正しくは経路 1 が 9、
  経路 2 が 13)、`CMAKE_CXX_FLAGS` が最適化 flag を壊すという推測 (ccbench 本体は base へ代入せず
  反証)、S1 の赤を選択依存と結論した件 (バッチでも赤で、真因は裁定の反映漏れ)。
- 段 6 レビュー B が親の記述を 2 点訂正した。凍結編集は 7 file 中 5 file でなく **4 file**
  (`axis_trigger_gating.py` は本 wave 非編集で既にずれている)。hold 対象 test は保存済み artifact
  でなく live `build_document()` と人工 tamper を検査するため、hold 解放時の全走の緑は静的には未確認。
- `output/` 配下の pin は多数あるが**いずれも過去の測定に対する historical binding** であり、
  live approval pin ではない。未更新のままが正しい。repin すれば過去測定の実行体参照を改変する。
- 変異は 5 件登録し全件 KILLED、期待 node 完全一致。5 件目は初版が検査関数の改名という誤った
  設計だったため、`_PythonGateFlow.coverage_for_sink` の sink 単位支配計算を file 単位の流用へ
  弱める形へ再照準した (DW-M01/M02 の実効 gate 再照準)。
- 実装 commit `0218acc61` / `ee635c953`、main 取り込み merge `649290c06`。
  main は 130 commit 前進していたが**編集面の重なりはゼロ**で自動 merge が通った。push はしていない。

- **継続セッション (段 4 再開: 閉包検査の是正と land)。** 以下はこのセッションで測った事実である。

- **裁定 file が消えていた。** 引数が指す `ruling-stage4.md` は前 job の tmp ごと消失していた。
  commit `ecba5a059` の message 逐語と branch 上の spool fragment から裁定内容を復元し、
  ユーザー引数と一致することを確認して進めた。
- **裁定が名指した s8b 以外に 2 件、裁定時に見えていなかった破れがあった。** 着手前の実測で判明した。
  - `s1_direct_comparison.py` にも同じ helper が同時に入っており、同じ理由で 18 セルが赤だった。
    詳細は {{F:same-defect-injected-into-two-files-but-only-one-measured}}。
  - local main を 63 commit 取り込んだところ、繰延べ台帳が pin する行番号 3 件が
    無関係な main の前進でずれ、赤が 62 セルから 106 セルへ増えた。
    `_deferred_member()` は (path, kind, scope, lineno) の 4 つ全一致を要求する。
- **緑になった理由を分解したら、22 セルが誤った理由で緑だった。** 段 6 のレンズ A が
  「0 は本当に被覆か」を軸に据えて 40 / 22 / 44 の内訳を出し、親が反実仮想で裏を取った。
  実装子が第 1 位置引数を `prepared_for_eval.genome` から `prepared.genome` へ書き換えたことが、
  s8b 既定枝の 22 セルを `proven-unreachable` へ倒していた。**値は完全に同一である**
  (`PreparedCell(genome=prepared.genome, ...)`)。正しい式へ戻すと 22 セルが赤へ戻ることを実測した。
  裁定は {{D:do-not-choose-the-analyzed-expression-to-pass-the-gate}}。
  経緯は {{F:green-accepted-without-asking-why-it-turned-green}}。
- **除外を沈黙から名前へ移した。** 誤った `proven-unreachable` の陰に隠すのをやめ、
  s8b 既定枝の campaign sink を繰延べ台帳へ所有者・理由付きで 1 件登録した。
  裁定は {{D:record-gate-exclusions-by-name-not-by-silence}}。
- **レンズ B が受入を赤にする欠陥を 1 件見つけた。** 展開の初版は `authorization_contract` を
  他の keyword と一緒に dict へ入れていたが、`test_campaign.py:5262` が resolved な
  certified-writer 呼び出しの `call.keywords` に、同 `:5340` が `evaluate_fn(...)` に、
  それぞれ明記を要求している。`screening_driver.evaluate_candidate` と同じ形へ揃えた。
  レンズ B は 24 項目の引数照合表を全項目出し、不一致 1 件 (上記の genome) を独立に検出した。
- **閉包検査は本 wave の新設であり、main には存在しない。** main の
  `test_ccbench_spawn_sites.py` に `_production_build_sources` は無い。したがって
  本 wave が main より受理集合を広げることはありえない。誤った `proven-unreachable` は
  回帰ではなく、新設した検査の射程の限界である。
- **変異は 4 件。M2 の初版が SURVIVED した。** s1 で閉包検査が捕まえていたのは既定枝ではなく
  注入枝だったため、実効 gate へ再照準した (DW-M01 / DW-M02)。初回結果は消さず erratum に残す。
  詳細は {{F:mutation-aimed-at-the-arm-the-gate-does-not-watch}}。
  変異 runner の射程は `orchestrator/tests/test_ccbench_spawn_sites.py` に絞った
  (関門を宿す file。実測 baseline 18 件緑・42.9 秒)。M1 は `test_campaign.py` の
  認可引数明記検査も同時に赤にするが、これは射程外の冗長 gate として単独変異の証拠から外す。
- **閉包検査の最終内訳 (親の実測):** 失敗セル 106 → 0。真に被覆 40 / 誤って到達不能 44
  (s1 既定枝 22 + s8b 以外の既存 sink) / 明示繰延べ 66 (t1905・t1819・t2027・protocol-r33 の 44 +
  本 wave の 22)。注入枝は s8b・s1 とも 22/22 で真に被覆されている。
- 親作成の main 取り込み merge `9bb9024aa` は実装面 3 path を含むため
  `missing-codex-author` を 1 件出す。先例 `311d463f` に倣い `tools/known_violations/` へ登録した
  (新規登録に事前承認を課さないのは D662 の裁定)。全史監査は 7393 件・新規違反なし。
- 実装 commit `785d4f533`、main 取り込み merge `9bb9024aa`。push はしていない。

- **受入全走で 8 件の赤が出た (19442 緑)。全件この branch 由来だった。** 焦点再走で 8 件とも
  決定的に再現し、main の tip (`f137427d4`) を別 worktree に置いて同じ node を走らせたところ
  8 件とも緑だった。非帰属ではない。4 系統に分かれ、いずれも**実体が正当に変わったのに、
  それを写している一覧・literal が追随していない**型だった。
  - 公式 perf 面の一覧 (1 件): `pipeline.evaluate` の呼び出し位置が helper 内から
    `run_role` / `run_block` へ移り、`_REVIEWED_PREDICATES` に `evaluate` が無かった。
  - provenance の件数 literal (4 件): known-violation を 1 件足したので post-baseline が 1 から 2 へ。
  - 承認済み reviewed spec の fixture (2 件): 下記 {{F:pin-keyed-by-role-name-missed-by-path-search}}。
  - 受入所要時間台帳の被覆 (1 件): 本 wave が test を増やして 89.908914% となり 90% を割った。
    今回の受入の実測 JUnit XML から `--add-only` で未登録 nodeid だけを足した。
- **DW-O09 の着手前検索で pin を 1 件取りこぼしていた。** 承認済み reviewed spec が
  `materializer` という key で `s1_direct_comparison.py` の bytes を pin していた。
  親は `output/` 配下を path で検索して「両 driver とも bytes 束縛なし」と結論していたが、
  この束縛は key 側にあり path 検索では出ない。DW-O09 が名指しで警告している型そのものである。
  詳細は {{F:pin-keyed-by-role-name-missed-by-path-search}}。
- 是正後の焦点走 (`test_acceptance_schedule_order.py` / `test_check_ai_provenance.py` /
  `test_official_perf_closure.py` / `test_s8b_oracle_manifest.py` /
  `test_update_acceptance_duration_ledger.py` / `test_ccbench_spawn_sites.py`) は **596 passed**。
  拒否側の負例を含めて緑で、閾値・assert を 1 つも緩めていない。
- 変異 spec が触る 3 file は本走時点 (`785d4f533`) と最終 tip で blob 同一のため、
  DW-M07 の anchor 再検証は blob 一致で足り、変異の再走はしていない。
- 実装 commit `785d4f533`、受入赤の是正 commit `2e62753a7`。

## 次の一手差分

### 完了

- [T-1999] patch 供給の define を build へ渡す driver 全体へ、効いたことの正例検査を義務化した。
  供給・実効化の節と実行側の意味の節を、独立した必須節と負例として持たせた。
  remaining: none
  base: f2e462befffdee1e09d84ae2abda5648512bdb00980f7883d3a0b127a1a162c6

### 新規

- {{T:meaning-witness-backlog}} **P2・新規**: 意味 witness を持つ macro は `BACKOFF_FIXED` の 1 件だけで、
  残り 21 macro は昇格時に `unestablished` として成果物へ持ち越される。この一覧が縮むことが後続の仕事。
  macro ごとに実行側の意味を観測する witness を実装する。
- {{T:deferred-gate-members}} **P2・新規**: 稼働 wave 所有と事前登録束縛のため本 wave で配線しなかった
  4 member を配線する (台帳には本 wave が別種の繰延べを 1 件足したので全 5 entry。本項の対象は他 wave 所有・事前登録束縛の 4 件だけである)。`b10_backoff_shape_sweep.py` (t1905)、`paper_story_a1_paired.py` (t1819)、
  `s8b_floor_campaign.py` の `build_fn` seam と campaign sink (t2027)、
  `s8b_oracle_n_pilot.py` (事前登録 `protocol-r33.json` の `driver_sha256` 束縛)。
  最後の 1 件は事前登録の後継発行か凍結解除のユーザー裁定が要る。
- {{T:closure-check-cannot-see-through-with-bindings}} **P1・新規・ユーザー裁定要**: 閉包検査が
  **本当に守りたい 2 経路を静的に証明できていない。** `s8b_oracle_driver.run_block` と
  `s1_direct_comparison.run_role` の既定枝 (production 経路) は、実行時には
  `require_returned_condition_evidence(prepared, ...)` が無条件に支配しているが、検査は
  (a) `with ... as (..., prepared)` の束縛を追えず (`_expression_depends_on_scope_parameter` が
  `Assign` / `AnnAssign` / `For` しか見ない)、(b) `campaign` kind の sink に対して支配的な
  返却物検査を被覆として数える仕組みを持たない (注入枝には既にある)。結果、s8b は本 wave の
  繰延べ entry で、s1 は誤った `proven-unreachable` で、それぞれ除外されている。
  **この 2 つを直せば両方が真に被覆された状態になる。** ただし検査の受理集合を変える設計判断
  であり、本 wave の裁定 (helper の展開) の射程外のためユーザー裁定へ返す。
  実測: (a) を直すと s1 既定枝の 22 セルが `proven-unreachable` から `unresolved` へ移り、
  (b) が無ければ赤になる。
- {{T:deferred-ledger-key-is-fail-open}} **P2・新規**: 繰延べ台帳の pin が
  (path, kind, scope, lineno) の 4 field だけで、安定した繰延べ ID を持たない。元 sink が
  移動・削除され別 sink が同じ 4 つ組へ来ると、その別 sink を黙って繰延べる fail-open がありうる。
  本 wave が実際に踏んだのは fail-closed 側 (main の前進で pin がずれて赤が増えた) だが、
  逆向きは塞がっていない。sink 直近へ安定 ID を置き、台帳をその ID と AST call へ一対一で束縛する。
  元 sink を消して同じ 4 つ組へ別 call を置く変異が拒否される負例も足す。
