# 判定と検査範囲

**GO（段 6 の静的レビューとして）。must-fix は確認しなかった。波及表と変異の帰属には should がある。**

本レビューは**未実走・静的読解**。対象は指定の 3 commit、submodule C、指定資料・親の実測ログである。fetch・変異工程・最終受入の完了を認定するものではない。

以下、`J/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/`、その他は投入先 worktree 相対 path。

# 1. 過剰・削除と完了条件

- **refuted / should 相当：差分の過剰実装は不成立。** driver の識別・配線・記録、5 test、README、候補 patch・JSON は裁定 §2 に対応する。根拠：`orchestrator/campaign/s3_mocc_lock_coverage.py:594`、`orchestrator/tests/test_mocc_xp_pin_candidate.py:68`、`patches/README.md:575`。不要な production gate や試行台帳の受理条件は増えていない。
- **refuted / must-fix 相当：C の証拠が旧 OID に取り残された疑いは不成立。** amend 後の C=`68106660…` を D297・compute・JSON・固定期待値が参照する。根拠：`J/mk-C-amend.log:6`、`J/run-d297.log:2`、`output/env/pegasus/calibration/s3_mocc_xp_pin_candidate.json:5`。別 commit の成功を C の材料へ転記した形ではない。
- **real / should S1：全負例を「X/P 発火により indeterminate」とまとめてはいけない。** `lockskip_high` は `non-serializable`、cycles=3525、`other_integrity_clean=false`。根拠：候補 JSON `:14907`、driver `:553`。放置すると材料レポートが複数原因の拒否を単一理由の拒否として過大評価するが、現行 certified 判定は変わらない。

親の記録で確認できた到達点は次のとおり。

| 完了条件 | 確認結果 |
|---|---|
| C の commit・branch・bundle | 最終 C、目標 blob、自己完結 bundle の verify 成功をログで確認 |
| 主 checkout への fetch | **未実行**。段 9 の残作業 |
| C 上の compute 1 走 | request `15646.nqsv`、rc=0、14 check 全真 |
| D297 GCC 2 版 | 11.4 / 12.3 とも成功、各 16 context |
| clang | 実行済みだが比較未完了。stderr は空入力の環境 prefix 不一致 |
| 負例 D297 | 旧計装で include 行列不一致の rc=1 |
| 波及表 | 主分類の逆転は見つからないが、後述の説明修正を推奨 |

`.text` bytes 一致、hot 経路、I 被覆の追加実装は不要。README の保証範囲の縮小は適切である。

# 2. 可搬性と legacy 保持

- **refuted / must-fix 相当：他 wave に C object が無いと新 test が赤になる経路は不成立。** source は BASE＋候補 patch から作り、routing はその場で別の子 commit を作る。C は識別用文字列・JSON の期待値として使用する。根拠：`test_mocc_xp_pin_candidate.py:51`、`:127`、`:252`、`test_mocc_proof_surface.py:65`。C の配布状況によって test の受理集合が変わる構造ではない。
- **refuted / must-fix 相当：旧成果物の改変は不成立。** 差分は指定の 5 file だけで、旧 test・旧 JSON・旧 patch、`PIN`・`CHECK_KEYS`・既存 helper 本文は不変。根拠：driver `:755`、`:770`。候補引数なしでは旧本体に進み、既存系列の判定条件を保持する。
- **real / nit N1：「Clone only BASE history」は実装より強い。** 通常の local clone であり、BASE だけに取得範囲を限定していない。根拠：`test_mocc_xp_pin_candidate.py:128`、`:140`。受理集合への影響はないが、「C 不在環境を実測した」証拠にはできない。

`tools/dev_waves/git_state.py:645` の初期化は local-only・no-fetch である。したがって「全 wave に C がある」という前提を置かなかった設計は妥当。N1 はコメントを「BASE を checkout して fixture commit を作る」に直せば足り、取得制御や追加 gate は不要。

# 3. 登録簿

- **refuted / should 相当：spawn・materializer・build authority の登録漏れは不成立。** 新 driver 関数は既存 `_run_checked`・`_build_variant` を呼び、直接 subprocess site や `"--build"` を持つ関数を追加していない。根拠：driver `:633`、`:695`、`test_ccbench_spawn_sites.py:423`、`test_s8b_floor_campaign.py:8071`、`test_p3_build_authority_cli.py:1224`。登録済み build の受理範囲は変わらない。
- **refuted / should 相当：新 macro・自走 harness の欠落は不成立。** patch の追加条件は既存 TRACE、負例は既存 3 macro、新 test は `_run()` で 5 node を収集する。根拠：候補 patch `:15`、新 test `:309`、`test_plain_runner_coverage.py:36`。未登録 macro や 0 件実行による偽緑は見つからない。

以上は静的結論であり、spawn inventory・materializer exact 閉包等の実走成功は本レビューでは主張しない。

# 4. scope 境界と実測の解釈

- **refuted / must-fix 相当：pin 前進・探索開始・検査器変更への越境は不成立。** gitlink、承認定数、verifier、D297 は差分外。README は候補の再現資料・NON_ADMISSIBLE・I 被覆なしを明記する。根拠：`patches/README.md:577`、`:592`、driver `:729`。正式 campaign の受理集合や試行台帳は拡張されない。
- **refuted / should 相当：clang を合格扱いした証拠はない。** rc=1 と prefix 不一致が記録されている。根拠：`J/run-d297.log:20`、`J/evidence/d297-clang14.stderr.txt:1`。材料では「GCC 2 版成功、clang 比較未完了」と保持すべきで、「3 本合格」にはできない。

正例 2 走は JSON 上 certified。単一スレッドの負例 3 種は、直交する X/P 違反が 0、cycles=0、`other_integrity_clean=true`、verdict=`indeterminate` である。この範囲と S1 の high 負例を分ければ、親の実測を過大に一般化せず記述できる。

# 5. 保全手順

- **refuted / must-fix 相当：提示された最終 bundle・fetch 手順の保全穴は不成立。** bundle は complete history、fetch script は異なる既存 OID で停止し、force・checkout・gitlink 更新を行わない。根拠：`J/mk-C-amend.log:41`、`J/fetch-C-to-main.sh:19`、`:23`、`:26`。指定どおり実施すれば、wave 撤去後も C を主 submodule store に保持できる。

実行順序は script 冒頭の「land 後・wave 撤去前」でよい。ただし**script が存在することは fetch 完了の証拠ではない**。段 9 で実行し、最終 ref=最終 C と HEAD 不変のログを残す必要がある。現時点の未実行は予定された残作業であり、設計欠陥には数えない。

# 6. 波及表

45 件の **追随 15・据置 29・衝突 1** という主分類を覆す根拠は見つからなかった。とくに `axis_mocc_temperature.py` の `PIN` と `PROOF_PIN` の分離、歴史 JSON の据置、policy epoch の集合外 consumer の併記は妥当。

ただし次を修正したい。

- **real / should S2：floor resolver の説明が実装と不一致。** 下書きは head exact を必須とするが、実装は現行環境契約の候補が 1 件ならそのまま返し、複数候補のとき head exact を選ぶ。根拠：`J/ripple-table-draft.md:42`、`orchestrator/campaign/s8b_floor_campaign.py:1061`。放置すると材料 3 が resolver の拒否集合を過大に記述し、successor 作成の必要条件を誤る。
- **real / should S3：template 系の preimage と二重計装を一括している。** 温度述語 template 単体は X/P を追加せず、計装 template 版の preimage は BASE＋template。根拠：`J/ripple-table-draft.md:43`、`patches/mocc-temperature-predicate-variant.patch:24`、`patches/instr-mocc-lock-coverage-temperature.patch:4`。放置すると材料 3 が移植対象と必要変更を過大に見積もる。
- **real / should S4：本 wave の追加成果物の将来扱いが未記載。** baseline 45 件の表としては正しいが、最終材料には新 test・候補 JSON・候補 patch と候補 mode の扱いを補うべき。根拠：`J/ripple-table-draft.md:3`、`:22`、`test_mocc_xp_pin_candidate.py:24`。放置すると後続 pin 更新で候補取得事実の固定値まで追随対象と誤認しうる。

S2 は「head exact 優先・一意候補 fallback」と記述し、C 系列の新 protocol が必要なことと resolver の選択規則を分ける。S3 は「旧計装の再適用」「template 単体の移植」「BASE＋template 用計装の移植」に分ける。

S4 は 45 件を組み替えず、次の補足表で足りる。

| 本 wave の成果物 | 将来 pin 前進時の扱い |
|---|---|
| 候補 patch | BASE→C の固定再現資料として据置。C に再適用しない |
| 新 test | BASE/C・blob・tree の固定期待値を据置 |
| 候補 JSON | C で取得した診断記録として bytes を保持 |
| driver 候補 mode | BASE の単一子を検査する診断契約として据置 |
| README | 承認・採用状態だけを実際の進捗に合わせて追記 |

# 7. 15 変異の帰属

以下は**未実走・静的読解による失敗見込み**。実際の失敗 node 集合・最初の assertion は変異工程で記録する必要がある。

| 変異 | 主な失敗見込み | 併発・帰属上の注意 |
|---|---|---|
| MP1 | source_contract | routing の固定 blob、JSON consumer も赤になる見込み |
| MP2 | trace0_logical_rows | source_contract、routing、JSON consumer も赤になる見込み |
| MP3 | source_contract | 現状は構造 helper より先に bytes 一致で停止 |
| MP4 | source_contract | 同上 |
| MD1 | identity_checks | 複数親の拒否対照 |
| MD2 | identity_checks | 追加 path の拒否対照。具体的置換後の確認が必要 |
| MD3 | identity_checks | old/new mode の拒否対照 |
| MD4 | identity_checks、source_routing | blob 不一致の単体対照と実 Git 対照 |
| MD5 | source_routing | 二重適用の失敗又は source 不一致 |
| MD6 | source_routing | macro ごとの期待 source 不一致 |
| MD7 | source_routing | TRACE=0 BASE 側 HEAD/blob 不一致 |
| MD8 | source_routing | verifier argv の root 不一致 |
| MD9 | source_routing | 旧 JSON path の拒否対照 |
| MJ1 | json_is_bound | 固定 C との不一致 |
| MJ2 | json_is_bound | 固定・再構成 blob との不一致 |

- **real / should S5：MP3/MP4 の「構造 helper が kill」は現状の順序では成立しない。** 全体 bytes 一致が helper 呼出しより先にある。根拠：`test_mocc_xp_pin_candidate.py:74`、`:86`、`J/s4-ruling.md:65`。放置すると変異台帳で source 束縛による拒否を意味構造検査の実証として誤帰属する。

失敗 node が `source_contract` だけでも、意味検査が発火したとは限らない。最小対応は実際の assertion に基づいて「bytes 契約による kill」と記録すること。構造 helper 自体の kill を必要とするなら、既存 helper 呼出しを全体一致より前へ移すだけでよく、新 gate・新 test 群は不要。

## 総括

**GO。静的レビューで実装上の must-fix はなし。fetch・変異・最終受入は未完了であり、wave 完了認定ではない。**

- **must-fix：なし。** 最小修正案・正例の提示対象なし。
- **should S1：負例全体を indeterminate／単一理由と一般化しない。** 根拠：候補 JSON `:14907`。
- **should S2：floor resolver を「head exact 優先・一意候補 fallback」と訂正。** 根拠：`J/ripple-table-draft.md:42`、`s8b_floor_campaign.py:1061`。
- **should S3：温度述語 template と X/P 計装の preimage・二重適用を分ける。** 根拠：`J/ripple-table-draft.md:43`。
- **should S4：本 wave の追加成果物を据置の補足表へ収載。** 根拠：`J/ripple-table-draft.md:3`、`test_mocc_xp_pin_candidate.py:24`。
- **should S5：MP3/MP4 の bytes 一致による拒否を構造 helper の kill と数えない。** 根拠：`test_mocc_xp_pin_candidate.py:74`。
- **nit N1：「Clone only BASE history」のコメントを取得実装に合わせる。** 根拠：`test_mocc_xp_pin_candidate.py:128`。

削除・縮小は、追加 gate ではなく上記の説明修正を優先する。候補 JSON が揃った現在は、新 test `:279` の「JSON 不在時用」独立 fixture を実 JSON のコピーによる改変対照へ縮小する余地があるが、必須ではない。