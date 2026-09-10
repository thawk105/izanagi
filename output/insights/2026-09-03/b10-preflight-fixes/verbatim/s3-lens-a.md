## 所見 1 — binding hash 不変という brief の前提は成立しない

`brief.md:22,71` は binding hash / campaign identity を変えないとしているが、driver 自身の bytes は `analysis_code_sha256` に入り、binding SHA を経て `search_config` と campaign identity に入る。根拠は `orchestrator/campaign/b10_backoff_shape_sweep.py:213-228,1377-1394,1477,1507-1519,2903-2906`。

現行 driver SHA `94d2cb...` と保存対象の SHA `34072f...` の不一致も、`handoff-b10-preflight-fixes.md:85-100` と `output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json:13-15` で確認できる。親の「不一致は現行 main ですでに存在する」という事実は正しいが、それは新しい collector が旧 binding を新規受理することまで正当化しない。

新しい balanced / read-heavy campaign が新しい binding / ID になること自体は受理拡大ではなく、変更後コードを正しく別 identity とする動作である。

成果物影響: 裁定なしに進めると、brief が約束する identity 不変と、実際に発行される campaign ID・binding が食い違う。

深刻度: must-fix

## 所見 2 — `e3de15eb` adapter は提案どおりでは旧 45 件を越えて受理する

現 validator は現行 binding と analysis SHA の exact 一致を要求するため、旧 write-heavy を拒否する。`orchestrator/campaign/b10_backoff_shape_sweep.py:2380-2385`。

一方、段 2 の adapter 条件 `s2-plan-a2.md:455-471` は campaign ID、grid、歴史 binding、spec / patch / formula、自己 hash envelope を検査するだけで、45 record の exact bytes / digest 集合や、各 `build_attempt_id`・`correctness_certified`・`performance_binary_sha256` と歴史 WAL の対応を固定していない。

具体的には、`e3de15eb` の root 内で、正規 grid と歴史 binding・既存 receipt hash を持つ row の `correctness_certified` や `median_tps` を変更し、envelope の自己 SHA を再計算した入力が通りうる。envelope は秘密に束縛された署名ではない (`b10_backoff_shape_sweep.py:2287-2294,2316-2324`)。validator も receipt の bytes hash は見るが、row の correctness / attempt / binary SHA を WAL と再照合しない (`:2411-2426`)。これらの値は `judge()` に直接入る (`:1654-1668,1733-1777`)。

したがって受理集合は明確に広がる。D1509 決定 3 (`verbatim-D1509.md:10-12`) が認めたのは既存 45 セルを残すことであり、「歴史 binding と同じ形の任意 record」を受理することではない。有限な既存 45 record そのものへ限定できる場合だけ、規律 2 と両立する例外と整理できる。

成果物影響: 改変された旧 row が Holm・効果量・等価性を変え、保存対象ではなかった判定値をレポートへ混入できる。

深刻度: must-fix

## 所見 3 — 270 枠 helper が「開示」を report admission gate に変えている

設計文書は 270 / 197 / 73 を「参考値であって受理規則ではない」と明記する (`verbatim-design-s6.md:31-37`)。しかしプランは truncated WAL、unknown tag、反復超過を report 拒否にしている (`s2-plan-a2.md:371-380,406-414,487-490`)。

135 performance record が正しく揃っていても、例えば測定後の WAL に無終端 crash tail が一つ残る、または登録外 tag の追加 verify record があるだけで report が消える。この helper を判定入力へ渡さなくても、`_write_reports()` 前で例外にすれば成果物の受理集合を変える。

純粋な開示 object として追加し、`judge(records, prereg.spec)` へ渡す 135 row を変えなければ、Holm・同値性の数値は変わらない。現行の判定入口は `b10_backoff_shape_sweep.py:2580-2590`。

成果物影響: 正しい 135 セルが存在する系列でも、verify 完全性の付随情報を理由に judgement と台帳が発行されなくなる。

深刻度: must-fix

## 所見 4 — attempt ごとの ordinal reset は完了記録数を誤る

WAL producer は repetition 番号を記録せず、`verify_done` に `build_attempt_id` と tag を記録する (`orchestrator/campaign/pipeline.py:1485-1502`)。反復 loop は `:1521-1529`。設計上の論理 key に attempt ID は含まれない (`verbatim-design-s6.md:26-29`)。

食い違う入力例は次のとおり。

- attempt A が performance 3 件、attempt B が 2 件: reset 後に attempt を投影から外すと ordinal は `{1,2,3}` に潰れ、3 枠になる。件数法なら完了記録は 5 件。
- attempt A が 3 件、attempt B も 3 件: reset 法は 3 枠へ潰れるか重複拒否になる。件数法は 6 件の overrun と判別できる。

完全性は「完了した verify record 数」の開示なので、`(workload, variant, tag)` ごとの件数を 1..N の論理枠へ射影し、登録数超過を別に開示する親の件数法が妥当である。これは官製 campaign の 197 / 287 を順序非依存で再現している (`handoff-b10-preflight-fixes.md:66-83`)。

重複 frame と失われた別 repetition が相殺する場合は、どちらの方式でも識別不能であり、attempt reset では解決しない。

成果物影響: retry を含む WAL で completed / incomplete slot 数が過小計上され、270 枠台帳の値が変わる。

深刻度: must-fix

## 所見 5 — cross-cache-root SHA は実在する性質を検査するが、cache split の必要条件ではない

親の「機構はあるが bytes 級の証拠はない」は不完全である。repo 内には、二巡の path 正規化後も別 job の binary が 45,454 bytes 異なり、`verify-perf` を採ったという負の実測がある (`output/insights/2026-08-31_t1905-b10-formal-run/README.md:88-106`)。

現在も未被覆経路がある。

- 主 CMake に渡すのは `CMAKE_CXX_FLAGS` の prefix map (`orchestrator/campaign/buildcache.py:1889-1919`)。
- masstree は staging 配下で `-g` を付けた独自 `make CXXFLAGS=...` により build され、その flags に prefix map がない (`external/ccbench/cmake/ThirdParty.cmake:57-75`)。
- その archive は実 executable へ link される (`external/ccbench/cmake/ProtocolHelpers.cmake:32-39`)。
- 入力差があればリンカの build-id も変わる。過去実測でも `.note.gnu.build-id` 差が確認されている。

ただし SHA 一致条項は、性能用 trace-disabled binary と、その correctness attempt が記録した同じ trace-disabled binary の SHA を比較するもの (`docs/b10-backoff-shape-preregistration.md:646-655`)。`verify-perf` では一つの `cache_root` が correctness campaign と後続 perf build の双方へ渡され (`b10_backoff_shape_sweep.py:2880-2891,2909-2918,2961-2987`)、`verify_performance_binary()` が exact SHA を照合する (`:2463-2483`)。ジョブ間再現性は必要条件ではない。

提案テストは、異なる空 cache root で実 `build_v2` を二度走らせ、双方 `cached is False` と direct `bin_sha256` 一致を要求すれば恒真ではなく、cross-root 再現性を正しく落とす。ただし実 staging path は `BuildResult.configure_argv` からは得られない。返却時の argv は完成 `bdir` から再構成されるためである (`buildcache.py:2088-2121`)。実 configure 呼出しを捕捉せず「staging path 不在」まで主張すると、その部分は偽の保証になりうる。

成果物影響: この強すぎるテストを cache split の先行条件にすると、既知の cross-job 非再現性で修正 (3) が止まる一方、同一ジョブの SHA gate はもともと壊れていない。

深刻度: must-fix

## 所見 6 — v2 additive は受理拡大を避けるが、新規 row の host 欠落も通す

v2 / v3 union は、現行 validator が schema v2 だけを受理するため明確な受理拡大になる (`b10_backoff_shape_sweep.py:2380-2385`)。段 2 が v2 additive に変更した結論は正しい。現行 validator は row の exact key set を検査していないため、host field 自体はすでに unknown additive field として受理される。

しかし `execution_host` を「存在するときだけ」検査する案 (`s2-plan-a2.md:418-451`) では、新 binding の新規 row から host を欠落させても legacy row と区別されず通る。旧 host 欠落を許す必要があるのは固定した歴史 campaign だけである。

host の取得元自体は正しい。job は scheduler の assigned host を export し (`tools/pegasus/b10_backoff_shape_campaign.sh:269-276`)、`reservation.read_binding()` は非空値を要求する (`orchestrator/campaign/reservation.py:120-139,159-175`)。

成果物影響: 新規測定 row でも実行ノードが `not-recorded-legacy-v2` となり、セルから実行ノードへの参照が失われる。

深刻度: must-fix

## 所見 7 — 壁時計案は「単一定数との検査」であり「単一定数からの導出」ではない

PBS directive `tools/pegasus/b10_backoff_shape_campaign.sh:5` は保持され、実 qsub は job script をそのまま投入する (`tools/pegasus/submit_b10_backoff_shape.sh:207-226`)。したがって scheduler request は `policy.json` から導出されず、literal と JSON の二つの真実が残る。

semantic test は drift を land 前に検出できるが、運用上の consumer を単一定数から生成するものではない。壁時計値そのものは変えず、correctness の反復・規模・厳しさにも触れない。

成果物影響: JSON と PBS literal がずれた commit が実行されると、receipt と実 scheduler 枠が食い違い、job は起動後に拒否されて成果物を作らない。

深刻度: should-fix

## 所見 8 — 新規テストの一部は変異の帰属が一意でない

次の nodeid 候補は、記載されたままでは前後の既存層または既存挙動と重なる。

- `test_report_input_requires_exact_135_registered_cells`: 重複・格子外・136 件は既存 `_validate_prior_block_records()` が先に拒否する (`b10_backoff_shape_sweep.py:2394-2425`)。新 gate へ帰属できるのは構造的な 134 件など。
- `test_present_missing_cell_is_reported_indeterminate_not_structurally_absent`: `judge()` 自身がすでに unusable row を indeterminate にする (`:1752-1777`)。新 completeness 層を無効化しても緑になりうる。
- `test_report_publish_is_create_only_for_one_binding_group`: `_write_reports()` は現時点ですでに create-only (`:2641-2644,2716-2718`)。固定 binding-group path の選択まで検査しなければ新機構の変異を落とさない。
- `test_legacy_v2_block_without_execution_host_remains_reportable`: host を見ない現 validator だけで既に通る (`:2380-2398`)。
- `test_b10_cache_root_is_submission_nonce_scoped_but_source_identity_is_unchanged`: source root は既存 gate `buildcache.py:654-656` と admission preimage `:1314-1325` が守るため、二つの独立原因を一 nodeid に混ぜる。
- `test_new_v2_block_records_reservation_binding_host`: empty host は `reservation.read_binding()` が先に拒否しうる。writer の転記変異と入力 validator の赤を分離できない。
- `test_preserved_write_heavy_campaign_is_exactly_scoped`: 非対象 campaign は通常 validator の現行-binding 不一致でも落ちる。adapter 自身の拒否だと示す必要があり、さらに所見 2 の row 内容改変を検査していない。

`test_report_phase_is_the_only_caller_of_write_reports`、実 binary の direct SHA 比較、270 の固定分母、campaign ID を logical key から外す検査は、直接 helper / AST を検査すれば一意にできる。ordinal-reset と unknown-tag rejection の二件も帰属自体は可能だが、検査する規則が所見 3・4 のとおり不適切である。

成果物影響: 変異赤を新機構の証拠と誤認し、実際には旧 validator だけが働く欠落実装を受け入れうる。

深刻度: should-fix

## 所見 9 — 135 構造欠落と present-but-unusable の区別は支持する

設計文書は report 入力を 135 セルちょうどとする (`verbatim-design-s6.md:20-24`)。一方、事前登録は存在する row の missing、correctness 未認証、unstable、underexposed を family indeterminate とする (`docs/b10-backoff-shape-preregistration.md:460-486,660-668`)。

したがって次の区別は整合する。

- 135 個の論理 record 自体が欠ける、余る、重複する、格子外: report admission を拒否。
- 135 record は存在するが測定不能: `judge()` に渡し、p=1 の indeterminate として開示。

前者は report 受理集合を従来より狭めるが、設計文書の明示要求である。後者では `judge()` の入力と手続きが現行どおりなら Holm・同値性を変更しない。なお report の top-level `official_certification` は現在も false (`b10_backoff_shape_sweep.py:2591-2593`)。

成果物影響: 134 row は report 不発行、135 row 中の測定不能は judgement 内に indeterminate として残る。

深刻度: nit（修正要求なし）

## 所見 10 — enforcement source closure への変更はない

exact 24 path は `orchestrator/campaign/campaign_lock.py:47-74` で確認でき、`b10_backoff_shape_sweep.py` と `buildcache.py` は含まれない。段 2 の変更予定 file (`s2-plan-a2.md:523-531`) に closure 内 file はない。

したがって `authority.contract_loader_blob_sha256s` の既存 24 blob はこの wave では変わらず、完走済み campaign lock の authority 検証へ直接の影響はない。brief P2 の「driver は closure 内」という理由は refuted だが、同 driver に置けば analysis-code SHA に collector が含まれるという別理由は成立する。

成果物影響: 完走済み lock の 24-path authority hash は変化しない。

深刻度: nit（確認事項）

## 所見 11 — 親 brief の実測には二つの過度な一般化がある

確認結果は次のとおり。

- N1 は支持: signal handler は二文に分離済み (`b10_backoff_shape_campaign.sh:107-110`) で、挙動テストもある (`test_b10_backoff_shape_sweep.py:1851-1882`)。
- N5 は支持: `external/ccbench/.gitignore:11-12` の `build*/` が新 cache path を覆う。
- N6 の「出現順で数えるほかない」は反対: repetition ID はないが、完了記録数は順序非依存の件数法で数えられる。
- 親実測 A は支持: driver は exact 24 closure 外。
- 親実測 B の「bytes 証拠がない」は、過去の負の bytes 実測と未被覆経路を落としており不十分。
- 親実測 C は支持: 件数法を採る。
- 親実測 D の SHA 不一致という事実は支持するが、「以前からあるから adapter は受理拡大でない」という含意には反対する。
- N4 の「文字列出現は driver と test だけ」は literal な repo 全検索としては false で、既存 provenance に schema 文字列がある。ただし executable consumer / pin がその二箇所だけ、という限定なら実害はない。
- N3 の他 worktree 全走査は、今回の「worktree 外 repo を読まない」境界のため独立再実測していない。

成果物影響: N6・B・D の一般化を採ると、270 台帳、cache split の可否、歴史 record の受理範囲を誤って決める。

深刻度: should-fix

## 規律 2 の接触面

- 正しさ receipt の発行、verifier、anomaly 即 reject、反復 loopは変更予定外。現行の即 reject は `pipeline.py:1505-1515`、反復数は `:1521-1529`、事前登録値の exact gate は `b10_backoff_shape_sweep.py:945-959`。
- SHA 一致比較 `verify_performance_binary()` は変更予定外 (`:2463-2483`)。cache path は入力 bytes に間接接触するが、比較を緩めない。
- 壁時計は submission receipt の発行・二重消費を変更するが、correctness receipt ではなく scheduler admission。
- 135 gate は report admission を狭める。
- 270 helper は開示だけなら非接触だが、提案された例外発生は report admission を変える。
- 歴史 adapter は row の `correctness_certified` を `judge()` が消費できる範囲を増やすため、規律 2 へ直接接触する。
- v2 additive host は、通常 validator の受理集合を広げない。ただし新 row の host 必須性を閉じていない。

成果物影響: correctness gate 本体の反復数・規模・厳しさは維持されるが、歴史 row と completeness helper の二箇所で report 側の受理集合が変わる。

深刻度: must-fix

## 総括

must-fix は以下の 6 件。

- brief の binding / campaign identity 不変条件を撤回または明示裁定する。
- `e3de15eb` 例外を歴史 binding の形ではなく、保存対象の有限な 45 record そのものへ限定する。
- 270 枠の完全性 helper を report rejection に使わない。
- repetition は attempt-reset ordinal でなく、`(workload, variant, tag)` ごとの件数法にする。
- cross-cache-root SHA 一致を cache split の必須条件にしない。同一 `verify-perf` job 内の SHA gate と分ける。
- 新 binding の v2 row では host を必須にし、host 欠落例外を歴史 campaign だけへ限定する。

未決 3 件への結論:

1. driver bytes / binding / campaign ID: 新しい campaign が新 ID になることは承認してよい。旧 `e3de15eb` adapter は受理拡大であり、D1509 の有限な既存 45 record へ exact に限定できる場合だけ承認可能。「不一致が既存」という親実測だけでは正当化されない。
2. repetition 番号: attempt ごとの ordinal reset には反対。順序非依存の件数法を採る。重複と別 repetition の識別不能は両方式に残る既知限界として開示する。
3. 135 record: 構造欠落は report 拒否、row が存在して測定不能なら indeterminate 開示、を支持する。Holm・同値性の手続きは変えない。

親 brief の provisional 裁定:

- P1: 反対。literal と JSON の同値検査であり、単一契約からの導出ではない。
- P2: 結論は支持、理由は反対。driver は closure 外だが、同 driver に置けば collector が analysis-code SHA に入る。
- P3: 反対。v2 / v3 union は受理拡大。v2 additive を使い、旧 campaign だけ host 欠落を許す。
- P4: 支持。135 performance cell と 270 verify slot は別母集団・別 object とする。
- P5: 支持。`IZANAGI_RESERVATION_HOST` を `reservation.read_binding()` 経由で使う。

親裁定へ返すべき設計択一:

- 歴史 write-heavy は「campaign ID + 歴史 binding の形」を受理するか、「既存 45 record の exact 有限集合」だけを受理するか。後者を推奨。
- 270 完了数は attempt-reset ordinal か件数法か。件数法を推奨。
- 270 helper の異常を report rejection にするか、完全性上の異常として開示するか。開示のみを推奨。
- cache split を cross-job bytes 再現性に条件づけるか、裁定済み `verify-perf` の同一ジョブ SHA 照合を境界にするか。後者を推奨。
- host 欠落を全 v2 で optional にするか、歴史 `e3de15eb` だけに限定するか。歴史限定を推奨。