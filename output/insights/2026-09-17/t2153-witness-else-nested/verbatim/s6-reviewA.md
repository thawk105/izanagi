## 差分と仕様の一致

以下、G＝`orchestrator/campaign/condition_meaning_gate.py`、TG＝`orchestrator/tests/test_condition_meaning_gate.py`、S2＝`orchestrator/campaign/s2_verify_calibration.py`、T5＝`orchestrator/tests/test_s5_permutation_coverage.py`。行番号は差分適用後。変異の結果はすべて静的予測であり、本レビューでは pytest・compiler・変異を実行していない。

**所見**：拒否時の reason code 検査を除き、差分は裁定 §4 の追加・変更範囲と一致する。  
**分類**：refuted  
**根拠**：G:282,285 に NOREAD→HIGHKEY の指定逐語、TG:45,46 に同順、TG:1572 に `"IZANAGI_BREAK_TRIGGER_MISATTR"`、S2:109 に実 factory 呼出し、T5:89 に `{s2, s3, coverage}` がある；現物の差分は指定4 file、+173/−3。  
**影響**：registry の位置・順序・所有 TU、未登録例、S2 配線について仕様逸脱は確認できない；`DEFINE_SPECS`、factory 条件、一意性・非識別・完了 marker、対応集合の導出式、旧 CLI は未変更。  
**推奨**：この部分の修正は不要。

**所見**：S2 consumer の拒否分岐は、裁定が要求する例外内の reason code を検査していない。  
**分類**：real nit  
**根拠**：`s4-ruling.md:74` は「`RuntimeError` (reason code 文字列を含む) を assert」だが、T5:198 は `pytest.raises(RuntimeError, match=macro)` のみ；S2:117,118 の現実装には両 reason code が含まれる。  
**影響**：nit；現在の受理判定は変わらないが、例外から reason code を削除する退行をこの test は検出しない。  
**推奨**：例外を取得し、macro に加えて `supply_stub.reason_code` と `meaning_stub.reason_code` が文面に含まれることを assert する。

## 新正例の実効性

**所見**：新正例の supply green と未確立一覧の空判定は、本文差と実 evaluator・実 family に裏付けられている。  
**分類**：refuted  
**根拠**：TG:1354,1357,1360 は要求側 `izanagi_selected_body` と既定側 `izanagi_default_body` を分け、HIGHKEY も TG:1369–1380 で異なる本文を持つ；TG:1394–1403 は実 supply・meaning・family を呼び、G:4109–4114 は実 status から一覧を作る。  
**影響**：要求1／既定0の前処理 bytes は本文自体で異なり、marker だけの差や family stub による偽緑ではない；新正例には evaluator を置き換える monkeypatch がない。  
**推奨**：修正不要；動的実行・枝本文の意味の検証とは区別して記録する。

**所見**：registry 逐語違い、factory の `None`、対応集合欠落のいずれも新正例を失敗させるが、失敗箇所は異なる。  
**分類**：refuted  
**根拠**：TG:1391 は宣言の exact type、TG:1393 は `start_directive == f"#if {macro}"` を検査する；G:1080 の record 発行時検証から G:3845 の `record.macro not in MEANING_SUPPORTED_MACROS` に到達する。  
**影響**：M1/M2 は新正例では前処理前の逐語 assert、factory `None` は型 assert、M4 は meaning の green record 発行時の `admission-contract-invalid` で失敗する；M4 は family 呼出しに到達する前に失敗する。  
**推奨**：変異記録では各失敗位置を残し、新正例の M1/M2 検出を compiler による検出とは記載しない。

**所見**：`ADD_ANALYSIS` 未定義という comment と、実 patch の前処理構造を模した toy という説明は fixture に一致する。  
**分類**：refuted  
**根拠**：TG:1349 は「ADD_ANALYSIS 未定義の正例」、TG:1351–1386 は関数・通常の `if`・`#else`・入れ子 `#if ADD_ANALYSIS` を配置する；`condition_gate_test_support.py:17–38` の fixture 定義に `ADD_ANALYSIS` はなく、owner 本文にも定義や include はない。  
**影響**：未定義時には analysis 本文が消えるが、両枝の異なる本文は残る；ADD_ANALYSIS=1 や実 CCBench TU の成功を示す test ではない。  
**推奨**：現 comment を維持する。

## S2 consumer test の実効性

**所見**：consumer test は実 factory の戻り値と request の同一性、family の実呼出し形、返却 JSON と拒否の転送を検査している。  
**分類**：refuted  
**根拠**：T5:159–162 は `real(request)` を保存し、T5:173–175 は request と declaration の `is` を検査する；T5:179 の `args == ([supply_stub], [meaning_stub])` は S2:112 と一致し、T5:198 の macro は S2:116 の `"condition gate rejected {macro}: "` に含まれる。  
**影響**：macro は正規表現の特殊文字を含まず `match=macro` は成立する；capture の TRACE、同じ captured、宣言の型・macro・所有 TU・逐語、要求1／既定0も検査され、実 compiler へ進む呼出しは stub 化されている。  
**推奨**：reason code の追加検査以外は不要；実 family の正しさは新 toy 正例の証拠として扱う。

**所見**：M3 の現 consumer における最初の失敗は declaration の assert ではなく、空の spy 記録を読む `IndexError` になる。  
**分類**：real nit  
**根拠**：S2:109 を `declaration=None` にすると `declare` が呼ばれず、T5:173 の `calls[0][0]` で失敗する；T5:175 の declaration 比較と T5:201 の `assert len(calls) == 1` は未到達。  
**影響**：nit；4 consumer node はいずれも同じ factory 未呼出しを原因として赤になるが、「declaration 同一性 assert が M3 を殺した」という帰属は成立しない。  
**推奨**：T5:173 より前に `assert len(calls) == 1` を置いて失敗理由を明示する；現状で実測するなら `IndexError` をそのまま記録する。

## 受理集合の向き

**所見**：供給結果を固定すれば、新2 macro の meaning 追加から旧拒否入力を admit へ変える経路は確認できない。  
**分類**：refuted  
**根拠**：G:973 は要求 `"1"`／既定 `"0"` と owner 所属を要求し、G:3347 以降は宣言なしを `"unestablished"` とする；G:4104–4109 は `supply_green and meaning_not_red`。  
**影響**：有効な1／0要求では旧 unestablished が green または red になり、前者は従来 admit の維持、後者は拒否への縮小；その他の有効な要求対は factory `None` のまま、不正 request は検証エラーとなる。  
**推奨**：この説明を meaning arm に限定する；既存12 witness と BACKOFF_FIXED の登録・条件・判定経路は差分で変わっていない。

**所見**：family 全体の受理集合が全入力で縮小するという証明は、今回の静的点検と焦点走だけでは閉じない。  
**分類**：plausible  
**根拠**：G:1885–1894 の `shared_branch_build` は registry 所属で切り替わり、G:2505 の同一 build root 許容も新2 macro に及ぶ；author 報告:66 は「供給内部は既存の共有 build root 分岐へ移ります」と明記する。  
**影響**：共有 root の cache・生成物に依存する入力では supply 観測が変わり得るため、旧 supply red→green→admit の可能性を全入力について排除できない；具体的反例は本レビューでは未確認。  
**推奨**：段3 A6/A7 の裁定どおり、共有 root への移行と回帰で確認した範囲を記録する；既存12 witness の分岐選択は変わらない。

## 変異事前登録の帰属

ここでの KILLED／SURVIVED は静的予測。並列実行時の「最初の失敗 node」は未確定であり、以下の記載順を実測順とは扱わない。

**所見**：M0 は等価変異として SURVIVED が予測されるが、指定された「registry 直前の comment」は現物に存在しない。  
**分類**：real nit  
**根拠**：G:243–245 は `DEFINE_SPECS`、`SUPPLY_DOMAIN_MACROS`、`_CONDITIONAL_BRANCH_WITNESSES = {` と続き、直前 comment はない；最後の逐語は file 内1箇所。  
**影響**：nit；存在しない comment を old にすると変異が適用されず、等価変異を実行した記録にならない。  
**推奨**：old を `_CONDITIONAL_BRANCH_WITNESSES = {` とし、new をその直前に通常の Python comment 1行を足した文字列にする；対象 test の値・構造・観測に変化はなく、SURVIVED 予測。

**所見**：M1/M2 は指定した3種類の node で KILLED が予測され、置換対象も一意にできる。  
**分類**：refuted  
**根拠**：G:283,286 の `"cc/silo/transaction.cc", "#if IZANAGI_BREAK_…_VALIDATION",` は各1箇所；TG:990 の patch 束縛、TG:1215 の green 期待、TG:1393 の逐語期待がそれぞれ独立に不一致を検出する。  
**影響**：各 macro の `accepts_each_registry_macro` は開始指令0件による red、`accepts_else_with_nested_analysis` は逐語 assert、`registry_and_fixtures_are_bound_to_real_patches` は registry と patch の不一致で失敗する；新 S2 consumer の対応 macro も T5:206 で失敗する。  
**推奨**：既登録の3種類を維持し、compiler による検出と宣言束縛 assert による検出を区別する；逐次 file 順では TG:974 の束縛 test が先に位置する。

**所見**：M3 は新 consumer 4 node と既存静的検査で KILLED が予測される。  
**分類**：refuted  
**根拠**：S2 内の `declaration=condition_meaning_gate.declare_define_runtime_meaning(request)` は1箇所；T5:91 は factory 呼出し文字列を要求し、T5:173 は前述の空 `calls` 参照になる。  
**影響**：SURVIVED にはならない予測だが、consumer の失敗は `IndexError`、静的検査の失敗は文字列 assert であり別の検出経路；逐次 T5 file 順では静的検査が先に位置する。  
**推奨**：主 killer は consumer のままとし、traceback に即した帰属を残す；factory 呼出しを残して戻り値だけ捨てる退行なら T5:175 が検出する。

**所見**：M4 は指定2 macro のみを除外する一意な置換が可能で、指定 node の KILLED 予測も成立する。  
**分類**：refuted  
**根拠**：G:292–294 の導出文全体は1箇所；G:3845 は対応集合外の green を拒否し、TG:2690 は `{"BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS}` との等値を要求する。  
**影響**：新正例2 node と `accepts_each_registry_macro` の対応2 node は green record 発行時の `admission-contract-invalid`、domain test は集合 assert で失敗する；registry 束縛 test と stub S2 consumer はこの変異を検出しない。  
**推奨**：old を現導出文全体、new を `MEANING_SUPPORTED_MACROS = frozenset({"BACKOFF_FIXED", *CONDITIONAL_BRANCH_WITNESSES} - {"IZANAGI_BREAK_NOREAD_VALIDATION", "IZANAGI_BREAK_HIGHKEY_VALIDATION"})` とする；対象名を明示でき、順序にも依存しない。

**所見**：M5 は既存の重複開始指令 node によって KILLED が予測される。  
**分類**：refuted  
**根拠**：G:2940 の `if len(starts) != 1:` は1箇所；TG:1448 は `duplicate=True`、TG:1458 は `"compile-time-branch-start-not-unique"` を要求する。  
**影響**：`< 1` にすると重複の最初の1箇所だけを計装し、この fixture では要求／既定の marker 数が成立するため green となり、既存負例の red 期待が失敗する。  
**推奨**：登録 node を維持し、既存被覆として数える；新2 macro の固有検出力とはしない。

**所見**：M6 は既存 factory 負例 `[0-0]` によって KILLED が予測される。  
**分類**：refuted  
**根拠**：G:973 の `elif requested != "1" or default != "0" \` は1箇所；TG:1591 は `(0, 0)` を含み、TG:1602 は factory が `None` であることを要求する。  
**影響**：`requested not in {"0", "1"}` に変えると要求0／既定0で宣言を返し、その assert が失敗する；1／0の新正例自体はこの変異の killer ではない。  
**推奨**：指定 node と既存被覆の帰属を維持する。

**所見**：M7 は reason 契約の検出として KILLED が予測され、非識別入力の誤受理を実証する変異ではない。  
**分類**：refuted  
**根拠**：G:3294–3300 の非識別検査 block は1箇所；TG:1316 は `"compile-time-branch-selection-not-discriminating"` を要求し、除去後も G:3301 の期待値不一致検査が残る。  
**影響**：観測 `(1,1)/(1,1)` は引き続き red だが reason が `compile-time-branch-selection-mismatch` に変わって失敗する；TG:1516 の非指令本文2 node も `(0,0)/(0,0)` の reason 違いで失敗する予測。  
**推奨**：block 全体を old として削除し、既存被覆・reason 契約という裁定済みの記録を維持する。

## 主張の境界と記録

**所見**：author 報告と新 test の comment は、toy・配線・実機未検証の境界を守っている。  
**分類**：refuted  
**根拠**：author 報告:70 は変異 matrix を「未実走」、:72 は実 CCBench TU・masstree `config.h`・実機 S2 JSON を「未検証」とする；TG:1349–1350 は toy と明示し、報告:59,62 は対応集合13→15／未対応25→23と CLI 自動追随を記載する。  
**影響**：枝選択の確立を動的到達性・positive control 発火・実機 JSON 縮小へ読み替えた主張は確認できない；段3で裁定された主要な記録上の懸念は反映されている。  
**推奨**：最終記録にも前処理成功時という条件と、1195 の現在未対応12→10、実機未確認の carry を残す。

**所見**：提供された焦点走ログは136 passedを裏付けるが、変異 matrix や受入全走の完了証拠ではない。  
**分類**：refuted  
**根拠**：`focus-f1.log:17` は `"136 passed in 5.27s"`、:1 は「受入形でない走行」；`s4-ruling.md:46` は別途 M0 SURVIVED と負例 KILLED を完了条件にする。  
**影響**：baseline の焦点走成功は報告できるが、現資料だけで wave 全体の完了や変異の実測結果は確定できない。  
**推奨**：親の焦点走136件と author の焦点44件を区別し、後続変異では node・例外・失敗行を採取する。

## 裁定パッケージ候補

新しい gate・台帳・一般化機構の提案はない。共有 root と実機依存供給の未確認点は既裁定の留保を維持し、(b)〜(f) 型への拡張は本差分の修正条件にしない。

## 総括

**real must-fix は確認できなかった。** 実装は裁定の主要仕様を満たし、新正例は実 supply・meaning・family に結び付いている。

real nit は3点：拒否文面の reason code 未検査、M3 の `IndexError` による失敗帰属、M0 の存在しない comment アンカー。M0 は SURVIVED、M1〜M7 は指定 node で KILLED を静的に予測する。実測判定は親の後続変異走で確定する必要がある。