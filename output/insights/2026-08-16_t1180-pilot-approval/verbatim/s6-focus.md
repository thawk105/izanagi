GO

### 所見 1 — レビュー A 所見 1 は閉鎖

主張: gate 後の再代入と冒頭 `unset` を新設テストが検出する。

一次証拠 (file:line): `orchestrator/tests/test_pegasus_floor_tools.py:994-1018`。承認変数の全出現を3行に限定し、代入と `unset` を別 assertion でも禁止している。

判定: closed

成果物への影響: 未承認または nonce 不一致の pilot が driver に到達する回帰を防ぐ。

land 阻止級か: 残余なし。

### 所見 2 — レビュー A 所見 2 は閉鎖

主張: 特殊値を承認扱いする shell 解釈上の抜け道はなく、その境界もテストへ追加された。

一次証拠 (file:line): exact 比較は `tools/pegasus/floor_campaign.sh:351-357`。空文字、`*`、`?`、`-n`、改行を含む8ケースは `orchestrator/tests/test_pegasus_floor_tools.py:2068-2123`。

判定: closed

成果物への影響: 特殊値から承認 flag や pilot 測定値が流入しない。

land 阻止級か: いいえ。

### 所見 3 — レビュー B 所見 1 は閉鎖

主張: 実ファイル上の static admission、承認照合、receipt 検査、dependency build、driver 起動の順序が固定された。

一次証拠 (file:line): production 順序は `tools/pegasus/floor_campaign.sh:90-95,351-357,412-415,833-835,977-978`。一意性と source index の昇順検査は `orchestrator/tests/test_pegasus_floor_tools.py:1020-1030`。

判定: closed

成果物への影響: nonce 不一致の job が build や driver を先行実行し、床値出力や誤った台帳 stage を残す回帰を検出する。

land 阻止級か: 残余なし。

### 所見 4 — レビュー B 所見 2 は閉鎖、scheduler 実測は別件

主張: テストの保証名と docstring は submitter が生成する qsub argv に限定された。実 scheduler が ambient env を継承するかは証明していない。

一次証拠 (file:line): `orchestrator/tests/test_pegasus_floor_tools.py:1349-1368`。別起動した driver helper は `:1369-1380` であり、qsub から job への seam ではない。残余は親裁定で T-1180-b として明記済み (`s4-adjudication.md:162-167`)。

判定: closed

成果物への影響: 未実測の scheduler 挙動は nonce 不一致による安全側の拒否となり、誤承認ではなく availability にだけ影響する。

land 阻止級か: いいえ。T-1180-b の初回実投入確認は必要。

### 所見 5 — 新設テストは指定3変異をすべて赤にする

主張: `test_floor_job_confirmation_dataflow_and_admission_order_are_fixed` は恒真ではない。

一次証拠 (file:line):

- N7: `tools/pegasus/floor_campaign.sh:954` 前後へ承認 env の代入を加えると、出現集合 `orchestrator/tests/test_pegasus_floor_tools.py:994-1002` と代入禁止 `:1003` が赤になる。
- N8: `tools/pegasus/floor_campaign.sh:27` の `unset` に承認 env を加えると、出現集合、宣言禁止 `:1005-1008`、対象集合 `:1010-1018` が赤になる。
- 承認照合を build の後ろへ移すと、承認 anchor が `tools/pegasus/floor_campaign.sh:833` より後ろになり、index 昇順 assertion `orchestrator/tests/test_pegasus_floor_tools.py:1020-1030` が赤になる。
- ほかにも照合行 `tools/pegasus/floor_campaign.sh:352`、static admission `:90`、receipt anchor `:412`、driver 起動 `:977` の削除・字句変更・順序変更が当該 node を赤にする。

なお flag append 自体 `tools/pegasus/floor_campaign.sh:974` の削除はこの構造 node ではなく、confirmed driver argv の既存動作テストが検出する。

判定: closed

成果物への影響: N7/N8と承認後置による未承認測定の混入を防ぐ。

land 阻止級か: いいえ。指定変異に生存はない。

### 所見 6 — 新設テストには非阻止級の過剰拘束がある

主張: 行番号や揮発値への依存はないが、正当な refactorでも偽赤になる字句拘束がある。

一次証拠 (file:line): `orchestrator/tests/test_pegasus_floor_tools.py:994-1002` はコメントを含む承認変数の全出現と整形を逐語固定する。`:1017-1018` は承認変数と無関係なものを含め、script 全体の `unset` 対象をちょうど3個に固定する。`:1020-1028` は同値な helper 化や command の整形変更でも赤になる。

判定: partial

成果物への影響: 現在の受理集合や成果物値は変えない。将来、例えば `unset LD_PRELOAD` を追加する正当な hardening が偽赤になる保守性上の問題である。

land 阻止級か: いいえ。後続で `unset` の全体集合固定を「承認変数を含まない」に縮めるのが妥当。

### 所見 7 — 変異復元に残留はない

主張: `git checkout-index` 使用という手順例外はあったが、最終 production bytes は変異前へ復元されている。

一次証拠 (file:line): `git diff HEAD~1 HEAD -- tools/pegasus/` の SHA-256 は fix 報告と同じ `a3f975789c3e647219ae8fb418fa2ba4c46711cc7c9ec3cec4eaf0bb6ce9a31b`。HEAD blob と作業ツリーの SHA-256 も両 production file で一致し、`git diff --quiet HEAD -- tools/pegasus/` は rc=0。N8残留は `tools/pegasus/floor_campaign.sh:27`、N7残留なしは `:351-357,954,973-975` から確認した。

判定: closed

成果物への影響: 変異による承認 bypass、誤った driver argv、意図しない production 差分は残っていない。

land 阻止級か: いいえ。手順例外自体の記録は `s6-fix.md:49-53` に残っている。

### 所見 8 — 統合差分に新たな成果物破壊は認めない

主張: receipt schema、未承認 qsub argv、未承認 driver argv、driver の exact bool gateに回帰はない。

一次証拠 (file:line): 承認 env の nonce export は `tools/pegasus/submit_floor.sh:417-420`、qsub argv は `:429-432`、receipt payloadは変更されず `:483-504`。未承認 driver は基本4引数のまま `tools/pegasus/floor_campaign.sh:968-978`。最終 driver gate は `orchestrator/campaign/s8b_floor_campaign.py:5255-5263`。`orchestrator/campaign/` の commit 差分も空である。

判定: closed

成果物への影響: certified 選択、レポート、台帳の値・受理集合・参照を新たに壊す差分は見つからない。既知の submitter bytes 束縛と scheduler 実測は親裁定どおり scope 外である。

land 阻止級か: いいえ。

## 総括

指定された N7、N8、承認照合の build 後置はいずれも新設テストで赤になる。レビュー A/B の実効上の所見は閉じ、変異の復元漏れや production 残留もないため GO とする。

唯一の残余は、新設した source 構造テストが全 `unset` 集合や逐語的な anchor を必要以上に固定する点である。これは将来の正当な refactorを偽赤にし得るが、現行の成果物値・受理集合・参照を壊さず、land 阻止級ではない。制約どおり pytest、編集、ネットワークアクセスは行っていない。