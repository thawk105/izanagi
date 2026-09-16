## 配線先の妥当性

以下、`G`＝`orchestrator/campaign/condition_meaning_gate.py`、`S2`＝`orchestrator/campaign/s2_verify_calibration.py`、`TG`＝`orchestrator/tests/test_condition_meaning_gate.py`、`T5`＝`orchestrator/tests/test_s5_permutation_coverage.py`。`brief`・`plan` は指定された段 1・段 2 資料を指す。行番号は変更前。

**所見**：親の「両 macro を要求する production 経路は S2 だけ」は、汎用 CLI と screening の request 生成を落としている。  
**分類**：real  
**根拠**：G:4163 は `choices=sorted(SUPPLY_DOMAIN_MACROS)`、G:4181 は CLI 入力から request を生成し、G:4196 は `else declare_define_runtime_meaning(request)`。`screening_driver.py:116` も両 macro の request を生成できる。直接呼出しの全生産側は、campaign 配下の `backoff_sweep:175`、`p3_kickoff:75`、`p3_s4_loop:426`、`p3_s4_red:90`、`p3_s4_loop_sort:122`、`p3_s4_loop_trigger_gating:121`、`s1_direct_comparison:210`、`s1_verify_extime_calibration:92`、`s2_verify_calibration:99`、`s3_lock_coverage:86`、`s3_mocc_lock_coverage:282`、`s5_permutation_coverage:83`、`s6_sort_sweep:222`、`s8a_trigger_coverage:109`、`s8a_trigger_sweep:318`、`silo_ladder_rung1:2213`、`t152_write_intent_coverage:183`、`paper_story_a1_paired:6891`、`paper_story_a2_certification:728`、G:4181、および tools 配下の `pegasus/run_ss2pl_lock_study.py:2014`、`pegasus/probes/t1683_rr5_cost_probe.py:157`、`t316_sandbox_backend_probe.py:1947`。family の再検証のみの呼出しは `t316_sandbox_backend_probe.py:369`、`t2228_driver_gate_liveness_probe.py:449`。`.claude/`・`hooks/` に該当呼出しは見つからない。  
**影響**：registry 追加だけで CLI の両 macro の出力も unestablished から green/red へ変わりうるため、「S2 だけが変わる」は誤り。  
**推奨**：brief:20,35、plan:117 を「追加配線が必要な専用 driver は S2。CLI は既配線、screening は route 拒否」に訂正する。他の列挙先は固定 macro・既定値集合・呼出し側の選択集合が両 macro を含まない。

**所見**：screening の admission 前拒否は現行でも成立するが、既定値 0 が拒否理由ではない。  
**分類**：real  
**根拠**：`screening_driver.py:81–82` は既定値表。`:116` の request は G:874 の `route=spec.route` により CXX_FLAGS route となる。一方 `model.py:92,146` は `CCBENCH_<axis>` の cache 引数を生成し、`screening_driver.py:147–159` は裸の `-D<macro>=<value>` 不在を `screening-build-route-mismatch` で拒否する。  
**影響**：要求値 1 でも 0 でも同じ route 不一致で admission に届かず、factory を追加配線しても成果物は改善しない。  
**推奨**：brief の「既定 0 で admission 前拒否」を「既定値表には存在するが、実 build 引数との route 不一致で拒否」に直す。

**所見**：未確立一覧の縮小を観測する場所は JSON に限定され、後段の機械 consumer は確認できない。  
**分類**：real  
**根拠**：S2:124 の `"admission"` が S2:363 の `"condition_gates"` に入り、S2:423–425 で保存される。観測箇所は **`output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json → condition_gates[0/1].admission.unestablished_meaning_macros`**。S2:435 以降の Markdown 生成はこの field を読まず、`pipeline.py:157` の成果物名はコメント参照である。  
**影響**：成功した新規実走で各単要素配列が `[]` になるが、既存 JSON・Markdown・後段の認証値が自動更新されるわけではない。  
**推奨**：plan v2 に上記観測箇所と「機械 consumer は検索範囲で未発見」を明記する。`_broken_build_and_verify` の再検査結果は S2:309 で返却値を捨てるため、保存対象は preflight の結果であることも区別する。

## S2 配線の実効性

**所見**：現行 S2 の supply green を示す実機証拠は確認できず、「既に同じ前処理を通っている」から config.h 問題を否定することはできない。  
**分類**：real  
**根拠**：`docs/archive/worklog-phase3-0702-0713.md:614` と `docs/archive/phase3-kickoff-stages1-5.md:79` は 2026-07-06 の S2 完走を記録する。対応 JSON は `:205` に `"all_pass": true` を持つが、`condition_gates` は持たない。同 JSON の最終変更も `9606c668c`、2026-07-06。`output/env/pegasus/calibration/` には S2 成果物・該当走行記録を検索で確認できなかった。  
**影響**：historical all_pass を現行 condition gate の成功証拠として扱うと、実機で JSON が生成されない可能性を見落とす。  
**推奨**：brief:26,40 の「通っている状態」を「供給が green なら未確立を許容するコード上の状態」に訂正し、確認できた最後の実測と現行 gate の証拠不在を記載する。

**所見**：masstree config.h 欠落は meaning 固有の仮想問題ではなく、現行 S2 の supply から残る実行上の懸念である。  
**分類**：plausible  
**根拠**：S2:95–98 は依存供給先を指定せず、G:1703–1720 は configure と compile database 読取りだけを行う。S2 PIN `dff0f1e` の `cmake/ThirdParty.cmake:66–78` も `config.h` を build 時の `add_custom_command` で生成する。S2:346 の preflight は stock build より先である。対照的に `screening_driver.py:203` は `prepare_masstree_fetchcontent` を呼ぶ。  
**影響**：fresh な依存展開先に config.h が無ければ supply は `preprocess-failed`、meaning は `compile-time-branch-preprocess-failed` となり、未確立一覧が空の新 JSON は得られない。  
**推奨**：plan の未確定点を維持しつつ、S2 の旧 PIN でも同じ生成方式であることを追記する。toy の成功を実機 admission の成功へ読み替えない。

**所見**：P1-d の「共有 configure 化は効率化」という説明は強すぎるが、今回それを must-fix とする具体的な drift は未確認である。  
**分類**：plausible  
**根拠**：追加後は G:1888–1897 の supply 2 configure と G:3220–3227 の meaning 2 configure が別 temporary root で走る。G:3267 の `comparables[0] != comparables[1]` は meaning 内の要求／対照比較で、G:4089–4097 の family 突合せは `request_digest` による。供給／意味間の compile command 同一性そのものは要求していない。  
**影響**：別 configure で外部依存や生成物が変われば、異なる build 文脈の二節を同じ request として組み合わせうるが、今回の入力で起きる証拠はない。  
**推奨**：P1-d を「既存の独立 configure 経路を維持し、共有 command の保証は主張しない」に訂正する。未確認リスクだけを理由に S3 形への変更を必須化しない。

**所見**：「供給側も完全不変」と読める説明は registry 追加の効果を落としている。  
**分類**：real  
**根拠**：G:1879–1888 は `request.macro in CONDITIONAL_BRANCH_WITNESSES` のとき `control_build = requested_build` とする。G:2499–2504 の共有 root 許容も会員資格で変わる。一方、meaning は G:3222 から同じ `captured` を渡し、G:1697–1707 が TRACE=1 を含む configure 引数を再利用する。  
**影響**：S2 の supply 呼出しを編集しなくても、一時 root 配置と evidence 内の command が変わる。  
**推奨**：plan が既に指摘した補足を brief の I4 に反映し、「呼出し・configure 引数は不変、内部 root 配置は変わる」とする。ADD_ANALYSIS/TRACE は対象指令を包む条件ではなく、marker 選択への影響は現物から認められない。

## test 設計の実効性

**所見**：consumer test 案は declaration の型・内容だけでなく、factory 戻り値との同一性を明記する必要がある。  
**分類**：real  
**根拠**：plan:166 は request の同一性、:167 は declaration の型・内容を指定するが、戻り値との `is` は明記していない。手本の T5:115–117 は `kwargs["request"] is request` と `kwargs["declaration"] is declaration` の両方を検査する。T5:91 の文字列検査だけなら、未使用の factory 呼出しを残した `declaration=None` を排除できない。  
**影響**：factory の結果を捨てて別宣言を渡す実装が、型・内容検査だけでは通りうる。  
**推奨**：実 factory を包む spy が request と返却 object を保存し、evaluator stub で両方の `is` を検査すると明記する。capture stub は `configure_args` を受け取り、S2:98 の TRACE=1 と両 evaluator への captured 同一性も確認する。

**所見**：S5 形の stub test は S2 に移植できるが、それだけでは実 admission の未確立一覧減少を実証しない。  
**分類**：real  
**根拠**：S2:94 は同じ `(source_root, macro)` signature で、S2 には共有 configure context がない。plan:164 は meaning と family を stub 化し、:169 は canonical JSON の転送を検査する設計である。  
**影響**：配線・拒否伝播・serialization の故障は検出できる一方、stub が返した空配列は実 meaning/family の成功証拠にはならない。  
**推奨**：test の主張を「factory 戻り値の伝達と admission 結果の転送」に限定する。brief の完了報告では、実 evaluator の toy 正例と stub consumer の証明範囲を分ける。

**所見**：関数内外の位置差や HIGHKEY の `ADD_ANALYSIS` 行が、今回の正例・patch 束縛を無効にするという懸念は反証できる。  
**分類**：refuted  
**根拠**：G:3100–3108 はコンパイルではなく前処理を行い、G:2949–2955 の marker は元の枝本文より前で閉じる。TG:261–264 は `line[1:] == f"#if {macro}"` の完全一致なので、`broken-silo-highkey-validation.patch:22` の `+#if ADD_ANALYSIS` は対象にならず、`:8` の対象指令だけが一致する。  
**影響**：nit。ただし前処理に成功する toy は、実 TU の include 依存や C++ コンパイル成功までは証明しない。  
**推奨**：この理由による追加 test は不要。親の生死実験と plan の正例は ADD_ANALYSIS 未定義の fixture であり、ADD_ANALYSIS=1 や S2 実 TU の実測とは記録しない。

## pin 閉包と件数

**所見**：brief の pin 一覧には NOREAD を未登録扱いする既存 test が欠けている。  
**分類**：real  
**根拠**：TG:1488–1489 は `_compile_time_request("IZANAGI_BREAK_NOREAD_VALIDATION")` に対して factory が `None` であると要求する。plan:129–131 は既に MISATTR への差替えを挙げている。TG:975 は集合ではなく `tuple(G.CONDITIONAL_BRANCH_WITNESSES) == _COMPILE_TIME_BRANCH_MACROS`。  
**影響**：未登録 test を残すと追加後に失敗し、tuple の追加順序を変えても registry 束縛 test が失敗する。  
**推奨**：plan の差替えを brief の変更表にも反映し、registry と test tuple の追加順序を一致させる。

**所見**：13→15／12→14 の literal 更新を要する追加 pin は検索範囲で見つからず、歴史件数を書き換える必要はない。  
**分類**：refuted  
**根拠**：TG:2606 は `{"BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS}`、TG:2691 以降の route 件数は 22/16。`patches/README.md:50,88` は positive control の挙動説明であり witness 件数 pin ではない。旧 insight:10 の「1 件から 9 件」、`:35` の「動かせなかった 13 件」は 1195 時点の記録である。`acceptance_duration_ledger.json` に両新 macro の既存 node 記載は見つからない。  
**影響**：nit。歴史記録を現行件数に上書きすると、過去 wave の成果の参照を壊す。  
**推奨**：TG の tuple を更新し、domain 式・route 件数は維持する。新しい insight に現行件数を記録し、旧 insight・過去 receipt は変更しない。

## 親 brief 自身の点検

**所見**：集合件数は合っているが、「意味確立 13」は登録能力の件数であり、全 driver の実測 green 件数ではない。  
**分類**：real  
**根拠**：G:74–240 の DefineSpec は再計数で 38、route は 22/16。G:245–282 の枝 registry は 12、G:286–288 が BACKOFF_FIXED を加えるため 13、差は 25。旧 insight の残り 13 件には BACKOFF_NOINLINE が含まれ、G:246 に現在は登録済みなので、その歴史集合の残りは 12 件である。  
**影響**：「13 件確立」を実走実績として読むと、未走行・条件不一致の request まで green と誤認する。  
**推奨**：brief:9 を「意味 witness 対応集合 13、未対応 25」に改め、「1195 の残り 13 件のうち現在未対応は 12 件、本 wave 後は 10 件」を併記する。

**所見**：brief の CLI 境界と marker 期待値には適用範囲の省略がある。  
**分類**：real  
**根拠**：brief:29 は「CLI は BACKOFF_FIXED 固定」とするが、G:4189 は `if cases and request.macro != MACRO`、G:4196 は cases 無しなら factory を使う。brief:13 は要求 `(1,1)`／対照 `(0,1)` に一般化するが、G:3282–3283 は `(int(requested),1)`／`(int(comparison),1)` で、BACKOFF_NOINLINE の要求 0 では逆になる。  
**影響**：CLI を誤って閉じたり、既存 NOINLINE の正しい受理を壊す修正を誘導しうる。  
**推奨**：I2 を「旧宣言型と CLI の `--meaning-case` 経路は BACKOFF_FIXED 固定」、期待組を「今回の要求 1／既定 0 に限る」に訂正する。

**所見**：(c) の完全一致件数は 2・2・12 で、末尾コメントや空白による一意な逃げ道は確認できない。  
**分類**：refuted  
**根拠**：`silo-backoff-requested-us.patch:60,178`、`silo_ladder_rung1.patch:9,31`、`silo-backoff-trigger-gating-variant.patch:41,79,101,107,119,133,143,153,163,173,183,193` はそれぞれ行末まで完全一致する追加指令。REQUESTED_US の header 側 `:29,41` は別 file。G:2932 は改行だけを除く一致、G:2934 は `len(starts) != 1` を拒否する。  
**影響**：同じ開始指令を registry に追加するだけでは、3 件とも一意性検査で red になる。  
**推奨**：既存機構で代表箇所を選べるという反証は採用しない。旧 insight の「3〜12 箇所」は現在の所有 TU の完全一致件数と区別する。

**所見**：主要アンカーの行番号は一致し、実質的な不足は行ずれより変更対象の漏れである。  
**分類**：refuted  
**根拠**：G:245,279,283、S2:94,109、TG:217,253,972,1320,2585、T5:86,89、support:145 は brief の指定と一致する。TG の parametrize は :1195、関数定義が :1196 である。  
**影響**：nit。TG:1488 の未登録 test 漏れは前述のとおり実際の回帰になる。  
**推奨**：parametrize／関数の表記だけ分け、未登録 test と supply 内部分岐をアンカー表に追加する。

## 依頼文の読み替え

**所見**：(a) の 2 件への絞込みを否定する現物上の根拠は見つからないが、理由を「複数箇所は過大主張」だけに置くべきではない。  
**分類**：refuted  
**根拠**：G:2934 の一意性条件と G:967–969 の所有 TU 条件が (c) の実指令を拒否する。RUNG1 の一意な複合条件は `silo_ladder_rung1.patch:56` の別 TU にある。(b) は `broken-silo-trigger-misattr.patch:9` の `#ifdef` なので要求 1／対照 0 が識別できず、親の `liveness_a_type.out:10–11` も両観測同一の red を記録する。  
**影響**：一意性や所有 TU 条件を保ったまま、代表 1 箇所だけを登録して green にする候補は得られない。  
**推奨**：plan v2 は機構上の拒否を主根拠にする。ユーザーの「既存機構で届くものから取る」を、全型から最低 1 件ずつ採る指示へ読み替えない。

## 裁定パッケージ候補

**所見**：裁定に返すなら、(c) の追加ではなく「本 wave の完了主張を実機成果物の縮小まで含めるか」が未解決点である。  
**分類**：real  
**根拠**：brief:26 は「S2 の admission の未確立一覧が 2 件縮む」を完了判定とし、brief:32,38 は S2 実機再走を除外する。確認済み履歴 JSON には condition gate 証拠がなく、plan:164 の consumer test は meaning/family を stub 化する。  
**影響**：そのままでは、配線と toy witness の検証をもって実機成果物が更新されたと報告しうる。  
**推奨**：親に「今回の完了を registry・配線・toy 生死確認までとし、実機 JSON 縮小は未検証と明記する」か「実機確認を別途含める」かの裁定候補として返す。新 gate・台帳・機構変更は提案しない。

## 総括

**所見**：必須の修正点は CLI を含む consumer 説明、実機成功の未証明、consumer test の declaration 同一性、brief の境界表現である。  
**分類**：real  
**根拠**：G:4196 の既配線 CLI、現存 S2 JSON の condition gate 証拠不在、plan:166–167 の検査指定、G:1879 の supply 分岐、TG:1488 の未登録期待が根拠となる。  
**影響**：修正しなければ、変更の到達範囲と完了実績を過大に報告する一方、実機の依存不足を見落とす。  
**推奨**：上記を plan v2／brief に反映する。(b)(c) への拡張や新機構は不要。本レビューは静的検査のみで、ファイル変更・pytest・compiler 実行は行っていない。