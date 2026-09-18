## 所見対応表 (A1 / A2 / B4: closed / partial / regressed、根拠と実測)

**A1・A2・B4 は closed。** 判定は現物・差分の静的確認と、指定された完了報告・親検査の実測に基づきます。本レビュー独自の `decide()` 直呼びは実行前に拒否されたため、以下の実測を自身の実行結果とは扱っていません。

| 所見 | 判定 | 根拠・既実測 |
|---|---|---|
| A1：深い入れ子による例外 | **closed** | 層剥きは反復処理。各層への呼び出しは `peel_executors=False` で、executor による追加呼出し深さは一定。fix A2 報告では1,100層の後続 pytest／内側 pytest が例外なく DENY、軽量形は ALLOW。 |
| A2：script 形の期待値 | **closed** | v2 が契約を直接形との一致に確定。既存 residual は変更されず、追加された一致テストは7組の実際の `decide()` 結果を比較する。fix A2 報告の7組も全件一致。拒否を緩める変更はない。 |
| B4：M8 の識別入力 | **closed** | 新規 `precedes_sanctioned_allow` は指定の2入力を検査。外側の先行 gate は通過し、合成した内側の residual が拒否する。層剥きを sanctioned 許可後へ移すと外側で許可されるため、位置変更を識別できる。現物の2入力の DENY は fix A2 報告済み。 |

A1 の呼出し関係は [guard_bash.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2498-executor-recurse/hooks/guard_bash.py:1249) で確認しました。`peel_executors` は keyword-only、既定値は `True`。`_heavy_command_violation` と shell 内側からの入口はこの既定値を使い、反復中の各層だけが `False` を明示します。合成した head は Python interpreter のままなので、各層から shell 再帰が再発する経路もありません。

各層は provenance、`_executor_output_violation`、admission、residual、sanctioned、pytest 等の既存 gate を受けます。内側の検査が許可を返しても、外側の反復は次層へ進むため、sanctioned 許可で以後の層を省略しません。

停止性の説明も実装と整合します。次層は program と残余引数から合成され、executor 部分を消費します。密着 option の分離や `--` 補完により**生 token 数**は増え得ますが、正規形の尺度は減少します。

既実測の具体例は、site=`PEGASUS_LOGIN`、command=`"python3 " + "-m cProfile " * N + tail` です。

| N | tail | fix A2 報告の結果 |
|---:|---|---|
| 1100 | `-m json.tool ; pytest -q` | DENY：後続 pytest |
| 1100 | `-m pytest -q` | DENY：baseline 重量対象 pytest |
| 1100 | `-m json.tool /tmp/a.json` | ALLOW |
| 300 | `-m json.tool ; pytest -q` | DENY：後続 pytest |

B4 の識別入力は次の2本です。外側 residual が最初に見る module は `cProfile`／`profile` なので、後方の pytest を理由に先行拒否しません。内側へ合成して初めて residual が pytest を検出します。

```text
python3 -m cProfile tools/run_tests.py -m pytest -q
python3 -m profile -o /tmp/p tools/run_tests.py -m pytest -q
```

## 新規所見

新規の実装上の **real / must-fix は認めません**。

段5からの差分は層剥きの反復化と3テスト追加です。通常終了する入力について受理集合を変える経路は見当たりません。`_script_executor_targets` は fix で変更されておらず、main 比でも表選択を共通 helper に移した後の走査処理は不変です。

[親検査報告](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2498-executor-recurse/review/parent-checks-2.md) では、383 command × 4 site で deny→allow 0・例外0、焦点走は806 passed／1 skipped／0 failed。v1 §2 の全行が期待どおりであることは fix A2 報告にあります。これらは親・実装担当の検査結果です。

変異 anchor と赤理由の静的確認は以下のとおりです。**fix 後の変異を本レビューで実行した結果ではありません。**

| 変異 | anchor の一意性 | 赤理由・扱い |
|---|---|---|
| M0 | docstring の指定行は一意 | 挙動不変の対照 |
| M1 | `if peel_executors:` は一意 | 層剥き欠落。複数関数が検出し得る |
| M2 | module 名検証条件は一意 | module 抽出欠落 |
| M3 | **関数内に限定すれば一意** | coverage 経路欠落 |
| M4 | module 合成行は一意 | 非実行引数消失による過剰拒否と、二重 wrapper 素通しの**二理由** |
| M5 | program の返却行は一意 | script 抽出欠落 |
| M6 | module 名検証条件は一意 | 不正 module 名を実行対象扱い。既存テストと冗長 |
| M7 | multi-target 除外条件は一意 | 非実行対象を実行対象扱い。既存テストの検出力 |
| M8 | block の開始・終了・移動先は一意 | sanctioned 許可による層剥き省略 |
| M9 | 次層への更新行は一意 | 二層目以降の検査欠落 |

M3 の報告中の2行 anchor はファイル全体では807行と854行の2か所にあります。指定どおり `_script_executor_program` に範囲を限定するか、後続の `return None` まで含めれば一意です。指定位置自体の曖昧さという疑いは **refuted / nit** と判断します。

**DW-G05 成果物影響：M3 は対象関数を限定して適用すれば、targets 側を誤変異させず coverage 抽出の検出力を評価できます。**

M4 は裁定どおり単一理由の証拠に数えず、M6・M7 は新規検出力に数えない扱いが必要です。fix 後の「赤になる node の完全集合」は本レビューでは未確定です。

## 判定 (GO / NO-GO と理由)

**GO — 指定された fix の焦点再レビューとして。**

A1 の反復化、A2 の契約と一致テスト、B4 の識別入力は裁定 v2 に適合しています。各層の gate 脱落、既存拒否の緩和、v1 の ALLOW 行を壊す変更は静的確認で認めません。

この判定は、未実施の独立直呼びや fix 後の変異 matrix を合格扱いするものではありません。

## 総括

A1・A2・B4 は closed。ファイル変更・pytest 実行は行っていません。M3 は関数範囲を限定し、M4 の二理由と M6・M7 の既存検出力を区別してください。

実行前の自動審査 `PreToolUse/guard_bash` が、メモリ内比較用コマンドを「防護パスと不透明構文の同居」、通常 import による直呼びも「program の中身を追えない」として拒否しました。そのため、本レビュー独自の `decide()` 実測・変異実行結果はありません。