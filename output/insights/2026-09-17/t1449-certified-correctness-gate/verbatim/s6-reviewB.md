## _full_receipt の不変性

以下、`U3`＝`orchestrator/tests/test_t338_submission_gate_unit3.py`、`U5`＝同 `test_t338_submission_gate_unit5.py`、`V`＝`orchestrator/submission_gate/_semantic_validator.py`。変異結果はすべて静的予測であり、pytest・変異試験は実行していません。

**所見**：`_full_receipt` の本文・返却構造と既存 fixture entry の相対順序・内容が変更された懸念は否定できる。
**分類**：refuted
**根拠**：差分の追加行を除いて関数本文を比較すると、既存関数で変化したのは `_make_git_fixture` のみ；U3:268 に11ファイルを追加し、U3:655 の `return value, schema` は不変。
**影響**：既存 fixture の期待値を直接弱める変更はない；ただし追加ファイルによって `head_commit`・`tree_sha` とそれを含む受領証の値は変わる。
**推奨**：コード修正は不要で、「不変」は生成ロジック・返却構造についての表現を維持する。

## 既存 test の期待値

**所見**：既存 test の名前・本文・期待 reason の変更はない。
**分類**：refuted
**根拠**：差分から復元した変更前の既存37 test 関数は全文一致；U3:745 の既存正例、U3:842 の six-pairs、U3:1131 の reason-code、U3:1220 の study test も対象に含む。
**影響**：既存検出力を期待値変更で下げた形跡はない。
**推奨**：既存 test は現状のまま維持する。

## テスト弱体化

**所見**：新負例の広い例外捕捉や正例の例外握りつぶしによる偽陽性は見当たらない。
**分類**：refuted
**根拠**：U3:734 は `pytest.raises(semantic.SemanticValidationError)` と `assert info.value.reason_code == code`；T1（U3:756）は `_validate_receipt_semantics`、T6/T8（U3:812、826）は `_validate_reason_branches` を捕捉なしで呼ぶ。
**影響**：新負例は指定 reason を要求し、正例で例外が出れば失敗する。
**推奨**：修正不要；同じ `correctness` を返す先行層との区別は、予定された M1 の反転確認で確定する。

## 単体 payload

**所見**：T3/T5/T8 は completed 性能分岐を通る形であり、T6 は意図どおり completed 性能分岐を通らない対照である。
**分類**：refuted
**根拠**：U3:708 の helper は marker 非 None、failure None、allocation あり、`cluster_slot: 1` の planned と同じ `run-0`〜`run-35` の actual を生成；V:2019–2030 の条件を満たし、T6 は U3:805 で failure 分岐へ変更して actual を空にする。
**影響**：T3/T5/T8 では `performance_slots` が埋まり、T6 では空になるため、gate 条件の両側を試せる。
**推奨**：修正不要；T6 について「completed 分岐を通らない」を欠陥として扱わない。

## 重複対負例

**所見**：T4 の重複は先行層を壊さず、新 gate の被覆検査へ到達する構成である。
**分類**：refuted
**根拠**：U3:786–788 は entry[0] 全体を deepcopy して ordinal/run_ordinal を6へ補正；V:1510 は ordinal 連番、V:1133 は source の arm 対応、V:1803 は raw 内容を検査し、複製した stock/W1 はこれらを満たす。
**影響**：6件・5対の入力となり、M1/M5 では受理へ反転すると予測できる；検証 attempt を除去しているため既存 verification-completed 規則も先に立たない。
**推奨**：修正不要；M5 の実走ではこの node の単独検出を確認する。

## 変異の帰属

**所見**：新 test への M0〜M9 の帰属は裁定表と整合し、負変異の静的 SURVIVED は見当たらない。
**分類**：refuted
**根拠**：V:2060–2073 と U3:756–826 から、M0＝SURVIVED、M1＝T2全件/T3全件/T4/T5、M2＝同集合＋T6全件、M3＝T8＋既存正例、M4＝M3集合＋T6全件、M5＝T4のみ、M6＝T5のみ、M7＝T2全件/T3全件/T4/T5、M8＝T2[1]/T3[1,5]/T4/T5、M9＝M1集合＋T8＋既存正例が赤になる。
**影響**：特に M5/M6 の検出はそれぞれ T4/T5 に依存し、M8 は非空不足件数の負例でも検出される。
**推奨**：予定された probe でこの帰属を実測し、静的予測と区別して記録する。

**所見**：裁定の列挙以外にも赤になる既存 node があり、列挙を完全な kill 集合として扱うと帰属が欠ける。
**分類**：real
**根拠**：U3:865、870、875 の `test_post_failure_accepts_marker_route`／`actual_run_route`／`recomputes_a03_route` は evidence なしで受理するため M2/M4 が殺す；V:2628 の reason 検査は phase 検査より先なので M3/M4/M9 は既存 phase 負例の期待 reason も覆う。
**影響**：nit（s4-ruling.md:105 は probe 後の期待 node 固定を明記しており、現時点の確定 matrix の誤りではない）。
**推奨**：probe の全失敗 node を採録し、既存正例の拒否と既存負例の reason 置換を分けて記録する。

**所見**：M3/M9 は `_full_receipt` を通す unit3・unit5 の複数既存 node を実際に殺す構造になっている。
**分類**：real
**根拠**：U3:575 の検証 attempt は `pre_performance_infra_failure`、evidence は1件；U3:745 と1220、U5:385、397、577、595、675 の経路はこれを単票 validator または writer に渡す。
**影響**：既存正例・study 正例に加え、unit5 の `semantic_positive`、publish authority、既存 destination の試験も過剰な `correctness` 拒否で失敗する。
**推奨**：M3/M9 の matrix にこれらの実測 nodeid を含め、carve-out の証拠を T8 だけへ限定しない。

**所見**：M6/M7 の短い置換文字列はファイル内で一意ではない。
**分類**：real
**根拠**：V:2011 と2068 に `len(evidence) != 6 or` が計2箇所あり、`"correctness",` は14箇所；一方、V:2068 の条件行全体と V:2060 の gate 条件行全体は各1箇所。
**影響**：nit（s4-ruling.md:105 により exact old/new は親がこれから固定する段階）；短い文字列のまま採用すれば既存規則を誤変異させ得る。
**推奨**：M6 は条件行全体、M7 は新 gate 固有の message を含む複数行を old にして一意性を保証する。

## 波及

**所見**：追加した `liveness/` ディレクトリや helper が t139 の複製・unit5 の関数名検査を壊す懸念は否定できる。
**分類**：refuted
**根拠**：`test_t139_submission_path.py:48–54` は各 target に `parent.mkdir(parents=True, exist_ok=True)` を実行して全 entry を commit；U5:350–353 は index が参照する名前への `getattr` と `inspect.isfunction` のみを検査する。
**影響**：11ファイルは複製対象に自然に入り、新 helper の追加は凍結 index の参照集合を変えない。
**推奨**：修正不要。

**所見**：「`_full_receipt` 本文不変だけで46 vector の結果不変が保証される」という裁定の説明は根拠が一段不足しているが、recipe を含めた点検では波及不具合は見当たらない。
**分類**：real
**根拠**：s4-ruling.md:23 は「構造上不変」とする一方、U3:422、424、627 は fixture の commit/tree を埋め込む；46 recipe と U5:104–217 を確認した範囲では `tree_files` 集合・件数・固定 `head_commit` に依存する操作はなく、参照先既存ファイルも保存されている。
**影響**：nit；受領証 bytes は変わるが、動的 identity の整合と既存 recipe の期待結果は維持されると静的に判断できる。
**推奨**：裁定の根拠を「本文不変＋identity の再計算＋recipe 依存点の確認」に補足する。

## 実装子の報告の検算

**所見**：報告の nodeid・件数・未実走の区別は実装と整合するが、実走成功そのものは本レビューでは独立確認していない。
**分類**：refuted
**根拠**：AST による parameter 展開数は U3＝50、U5＝58、t139＝25、合計133；追加は7関数・11ケースで名前と ids は ASCII；s5-author-1.md:75 は「133 passed」、85 は「変異 M0〜M9 の実走は未実施」と明記する。
**影響**：件数・実装範囲の水増しは検出していない；成功・794.95秒・warnings は author の報告値として扱う。
**推奨**：実走結果の確定には親が実行ログを照合し、報告どおり5分超過も残す。

## 裁定パッケージ候補

追加候補はありません。新 gate・台帳・一般化の追加は求めません。裁定 §5 の既存候補は本レビューの must-fix に含めません。

## 総括

静的点検で **must-fix は検出しませんでした**。既存 test の弱体化、単体 payload の空振り、T4 の先行層による偽陽性、fixture 追加による参照破壊は見当たりません。

親の変異試験では、M6/M7 の置換範囲の一意性と、裁定表に未列挙の既存失敗 node を確認してください。M0〜M9 の結果は本回答では静的予測に留めています。