## consumer と pin の取り残し

以下、G＝`orchestrator/campaign/condition_meaning_gate.py`、S2＝`orchestrator/campaign/s2_verify_calibration.py`、TG＝`orchestrator/tests/test_condition_meaning_gate.py`、T5＝`orchestrator/tests/test_s5_permutation_coverage.py`。行番号は適用後。指定 diff と作業ツリーの `git diff` は一致した。

**所見**：検索範囲で、更新漏れの registry pin・未確立期待・S2 JSON golden は見つからない。  
**分類**：refuted  
**根拠**：TG:977 の `tuple(G.CONDITIONAL_BRANCH_WITNESSES) == _COMPILE_TIME_BRANCH_MACROS` は TG:45–46 の追加で追随し、TG:2690–2692 の対応集合も同 tuple から導出する。TG:1572 は未登録例を `IZANAGI_BREAK_TRIGGER_MISATTR` に変更済み。`test_mocc_proof_surface.py:563–570` は MOCC の固定3会員だけを参照する。`orchestrator/`・`tools/`・`docs/` の名前・macro・未確立一覧・JSON 検索で追加 pin は未発見。  
**影響**：nit  
**推奨**：追加修正不要。対応集合15・未対応23と、変更しない supply domain／route 件数を区別して記録する。

**所見**：S2 の caller と直接 consumer は提示された f1／f2 に収まり、追加必須の焦点ファイルは見つからない。  
**分類**：refuted  
**根拠**：S2 内 caller は :134 の `records.append(_require_condition_gate(sub, macro))` と :309 の再検査、直接 test 呼出しは T5:192,199。S2 参照は `test_build_site_gate.py:23`、`test_ccbench_spawn_sites.py:25`、`test_p3_build_authority_cli.py:162` にあり、いずれも提示集合に含まれる。集合外の `test_p3_s4_loop.py:7792–7799` は patch macro の allowlist、`t2187_adaptive_const_probe.py:3840` は `"static-fixture-not-live-broken-build"` の由来記録であり、今回の meaning 会員資格を pin していない。  
**影響**：nit  
**推奨**：焦点集合への追加不要。共有 fixture 等の間接 consumer は裁定どおり受入全走で確認する。f2 の成功は本レビューでは未確認。

## S2 の実機経路

**所見**：configure 回数は増えるが、実機 walltime への影響を「軽微」と断定できる計測資料はない。  
**分類**：plausible  
**根拠**：G:1895,1900 が supply の2回、G:3226–3231 が meaning の2回で、S2:129–134 の2 patch に対して preflight は4→8回。S2:309,399–403 の再検査まで到達すると gate 全体では8→16回になる。一方 G:1893 の `control_build = requested_build if shared_branch_build` により、各呼出しは従来の新規2 root から「supply 新規1 root＋再 configure、meaning 新規1 root＋再 configure」へ変わる。  
**影響**：実機で増分が大きければ S2 完了・成果物生成までの時間が延びるが、その程度は未確認。  
**推奨**：見積りは「preflight で再 configure 約4回分＋meaning 前処理4回分、後段込みではその約2倍」を基本とする。新規依存展開が単純に倍増するとは書かない。S2:354–355 の stock build 2本は cache-hit もあり、:321–324 の broken build 2本は fresh build なので、比較には実機時間が必要。本 wave に実機走や機構変更を追加する必要はない。

**所見**：「supply が通れば meaning も通る」という含意は、configure 引数の一致だけでは成立しない。  
**分類**：refuted  
**根拠**：両経路は G:1703–1716 の `captured.configure_args` を再利用するが、supply は G:1874 の `izanagi_condition_supply_`、meaning は G:3214 の `izanagi_compile_time_branch_` 配下に別 build root を作る。S2:97 は依存供給先を固定していない。S2 PIN `dff0f1e` の `cmake/ThirdParty.cmake:66–78` は masstree `config.h` を `add_custom_command` の生成物としている。  
**影響**：supply 成功を meaning 成功の証明に置き換えると、別依存展開先での前処理失敗・admission 拒否を見落とす。  
**推奨**：保証できるのは同じ source root・要求値組・共通 configure 引数を使うことまで。依存展開先、生成物、compile command の共有は保証しない。config.h 問題と実機 admission は未検証のまま記録する。

**所見**：preflight の例外後に stock build や新しい結果 JSON が生成される経路はない。  
**分類**：refuted  
**根拠**：S2:346 の `_preflight_condition_gates(root, sub)` は例外を捕捉せず、stock build は :354–355、結果辞書は :359、JSON 書込みは :424–425 の `json.dump(results, f, ...)` にある。  
**影響**：nit  
**推奨**：修正不要。「新しい JSON は書かれない」と記録する。既存 JSON があれば残るため、「JSON 自体が存在しない」とは表現しない。

## test の書式・保守性・受入時間

**所見**：S2 の追加配線行は138文字あり、既存の複数行形式に揃える余地がある。  
**分類**：real nit  
**根拠**：S2:109 は `captured, request=request, declaration=... , cxx=...` を1行に置く一方、`s3_lock_coverage.py:99–104` は declaration と compiler 引数を分行している。  
**影響**：nit  
**推奨**：S2 の呼出しを `captured, request=request,`、`declaration=...`、`cxx=...` に分行する。共有 configure 化は行わない。

**所見**：f1 は十分短いが、新正例2件・consumer 4件の個別所要や受入全走の5分以内は、このログだけでは確定できない。  
**分類**：plausible  
**根拠**：`focus-f1.log:17` は `136 passed in 5.27s`、:47 は job の `Elapse: 13S` で、node 別 duration はない。:1,23 は「受入形でない走行」と明記する。T5:185–189 は evaluator と family を stub 化している。  
**影響**：焦点走の時間を受入全走の余裕や個別増分に読み替えると、5分上限の判定を誤る。  
**推奨**：記録は「追加6件を含む f1 全体が5.27秒」に留める。追加6件の個別秒数は推定値としても実測扱いせず、受入時間は予定された全走で判断する。

**所見**：新 nodeid の ASCII 要件と parameter 順序に問題はなく、既存期待値の変更も裁定範囲内である。  
**分類**：refuted  
**根拠**：TG:1341–1345 の関数名・macro 値、T5:131–133 の関数名・値は ASCII。T5 は上段が `macro`、関数に近い下段が `admitted` で、生成直積は admitted 外側・macro 内側、ID は `[True-IZANAGI_BREAK_NOREAD_VALIDATION]` 形になる。差分の既存箇所変更は TG tuple 追加、TG:1572 の macro 差し替え、T5:89 の S2 適用追加のみ。  
**影響**：nit  
**推奨**：変更不要。変異 harness にはこの ID 形を使う。本レビューでは pytest collection は実行していない。

## 裁定 §1 の反映

**所見**：レンズ B が求めた declaration/request/captured の同一性、TRACE 検査、未登録例差し替えは閉じている。  
**分類**：refuted  
**根拠**：T5:159–162 は実 factory の戻り値を保存し、:173–175 は request と declaration を `is` で照合する。:165,172 は `args[0] is captured`、:156 は `"-DCCBENCH_TRACE=1" in configure_args`。TG:1572–1585 は MISATTR に対して従来の `None`／`meaning-witness-undeclared` を維持する。TG:1393–1420 は実 supply・meaning・family で空の未確立一覧を要求する。  
**影響**：nit  
**推奨**：追加修正不要。consumer stub の配線検証と toy 上の実 family 検証を引き続き分けて報告する。

**所見**：consumer の拒否分岐は RuntimeError と macro を検査するが、裁定で指定された reason code の検査が抜けている。  
**分類**：real nit  
**根拠**：`s4-ruling.md` §4-2 は「RuntimeError（reason code 文字列を含む）」を要求するが、T5:198 は `pytest.raises(RuntimeError, match=macro)` のみ。S2:117–118 は現実には supply／meaning の reason code を出力している。  
**影響**：nit  
**推奨**：既存の拒否分岐で例外を取得し、stub の reason code が例外文字列に含まれることを assert する。現行 production の受理集合・成果物値に不具合は確認されないため must-fix にはしない。

## 報告の過大主張

**所見**：author 報告と新 test comment は、toy・実機未検証・CLI・screening・件数の裁定境界を概ね守っている。  
**分類**：refuted  
**根拠**：`s5-author.md:60` は「13→15、25→23」、:63 は CLI 自動追随と screening の route 不一致、:66 は供給内部の共有 root 化、:72 は実機 JSON 縮小未検証を明記する。TG:1349–1350 も「toy TU」「実 patch 適用後の TU の実測ではない」と限定する。G:4203 は factory 自動呼出し、`screening_driver.py:147–158` は裸 define 不在による `screening-build-route-mismatch` を裏付ける。  
**影響**：nit  
**推奨**：修正不要。author:26 の「supply 維持」は呼出しの維持として読み、内部 root 配置まで不変とは要約しない。

**所見**：「136 passed、skip 0」は親ログと整合し、author の44件報告とは実行範囲が異なる。  
**分類**：refuted  
**根拠**：`focus-f1.log:17` は `136 passed` で skipped の記載なし。`s5-author.md:36–37` は TG `32 passed、92 deselected` と T5 `12 passed`、:53 は TG 残り92件を未実走とする。TG 124＋T5 12＝136 と整合するが、親ログ自身にはファイル別内訳や node 一覧はない。  
**影響**：nit  
**推奨**：親の f1 結果と author 時点の44件を区別する。136件成功を変異 matrix・f2・受入全走・実機 S2 の成功へ拡張しない。

## 依頼文との整合

**所見**：差分に新 gate・防壁・一般化・台帳の追加はなく、S2 consumer test は指定配線の検証に留まる。  
**分類**：refuted  
**根拠**：差分は指定4 file の `+173/−3` と一致し、production 変更は G:282–287 の registry 2 entry と S2:109 の factory 配線のみ。T5:185–199 は既存 family の戻り値を stub 化し、受理時の転送と拒否時の停止を検査する。  
**影響**：nit  
**推奨**：scope の追加変更は不要。指摘した nit を直す場合も既存呼出し・既存 test 内に限定する。

## 裁定パッケージ候補

新 gate・台帳・一般化の候補は提出しない。実機再走と依存供給の未確認事項は、裁定済みの持ち越し範囲を維持する。

## 総括

**must-fix は0件、nit は2件**：S2:109 の分行と、T5:198 の例外 reason code 検査。採用済みの同一性・TRACE・未登録例差し替えは閉じており、追加必須の consumer／pin 更新や焦点ファイルは見つからなかった。

親ログの136件成功は確認した。個別所要、受入5分上限、実機 S2 の成功・walltime は未確認。本レビューではファイル変更・Git 状態変更・pytest 実行を行っていない。