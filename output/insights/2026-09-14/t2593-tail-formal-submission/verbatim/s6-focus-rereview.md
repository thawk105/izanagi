## 6件の対応表

| # | 所見 | 判定 | 根拠（静的読解、file:line）・残る改変 |
|---|---|---|---|
| 1 | `--help` 事前走査による終了コード集合の拡大 | **closed** | `tools/pegasus/submit_b10_backoff_grid.sh:19` の逐次解析へ戻り、`:43` で到達した help だけ rc=0、`:47` の未知引数は rc=2。`orchestrator/tests/test_b10_backoff_grid_submit.py:256` が順序別の rc を固定。新 flag 認識に伴う意図的変更は同`:283` に残り、親裁定`:104` と整合する。 |
| 2 | 到達性テストが実 job の中間区間を素通り | **partial** | `orchestrator/tests/test_b10_backoff_grid_job.py:199` は依然として入力区間と sweep を連結し、実 job の`:287`〜`:596` を実行しない。追加の同`:139` は2変数の文字列出現だけを検査する。**通ってしまう改変：** job の `CURRENT_STAGE=allocation_reservation` 直後に `exit 2` を追加する。対象変数名を含まず、抽出区間にも入らないため、この検査群は検出しないが実 job は driver 到達前に停止する。 |
| 3 | group ID の日時・PID が形式検査のみ | **partial** | `orchestrator/tests/test_b10_backoff_grid_submit.py:67` と`:105` で日時を起動前後の窓に照合し、`:159` で2回の ID 相違を検査する。ただし shell PID の観測・照合はない。**通ってしまう改変：** `tools/pegasus/submit_b10_backoff_grid.sh:148` の末尾 `$$` を `$(( $$ + 1 ))` に置換する。時刻・形式・2回の相違は満たすが、実際の shell PID ではなくなる。 |
| 4 | `realpath` の末尾改行が command substitution で消失 | **closed** | `tools/pegasus/submit_b10_backoff_grid.sh:73`〜`:76` が番兵で改行を保存し、番兵と出力終端を各1個除去してから文字集合を検査する。`orchestrator/tests/test_b10_backoff_grid_submit.py:292` は末尾改行の直接指定と `alias/.` の双方を負例に追加している。 |
| 5 | 集団 report の既存出力先について文書が厳しすぎる | **closed** | `docs/b10-backoff-static-tail-submission.md:74` が「directory 自体は既存可、対象3成果物は既存不可」と区別。`orchestrator/campaign/b10_backoff_static_tail_formal.py:648`〜`:651` の実装と一致する。 |
| 6 | 投入成功と出力 root 作成時点の混同 | **closed** | `docs/b10-backoff-static-tail-submission.md:42`〜`:45` が receipt と job 開始後の root 作成を区別。submit の`:232`・`:250`・`:262` は receipt／qsub、job の`:283` が root 作成であり、元の混同は解消している。 |

## fixによる新しい穴

静的読解では、help 事前走査撤去と番兵処理に新たな実装上の穴は見つからなかった。

- **help：** `--unknown --help` は未知引数で rc=2。`--run-kind --help` は help を値として消費し、種別検査で rc=2。新 flag を正常に読み飛ばして help に到達する rc=0 は、親裁定が許容した変更である。
- **番兵の順序：** 解決先を `P` とすると取得値は `P + LF + x`。`${resolved%x}` が最後の `x` だけを取り、`${resolved%$'\n'}` が `realpath` の終端 LF だけを取る。`P` 自体の末尾 LF は残り、後続検査で拒否される。逆順なら終端が `x` のため LF を除去できず、正常 path まで拒否する。
- **`printf 'x'` 失敗：** `realpath` 成功後に `printf` が非ゼロ終了すると、代入の終了コードも非ゼロになり、`:73` の `|| exit 2` で停止する。番兵なしの値を後続へ渡す経路にはならない。`realpath` 失敗時も同様に停止する。

文書`:42` の「成功した時点で……1本だけ」は少し強い表現で、先に投入した job が既に開始していれば root 等も存在し得る。ただし続く説明は作成主体と時点を区別しており、元所見の再発とは判定しない。

## 追加テストは何を赤にするか

| 検査 | 赤にする改変と限界（静的読解） |
|---|---|
| group ID の時刻窓 | 日時を `20000101T000000Z` に固定する改変を赤にする。期待窓は Python 側の時計から取得しており、恒真ではない。 |
| 2回起動の ID 相違 | group ID 全体を固定する改変を赤にする。ただし出力親は2回で異なり、同一引数の再投入そのものではない。秒をまたぐと日時だけでも相違するため、PID 固定化の確実な検出にはならない。 |
| job の変数出現 | 中間区間への `unset B10_PREREGISTRATION_COMMIT` など、対象名を直書きした行の追加を赤にする。期待行は固定され、追加変異テストも実 source をメモリ上で変更するため恒真ではないが、制御フローの接続保証ではない。 |

## 既存テストとscope

`d895e90b2`→`48450516d` の差分では、`test_backoff_extended_sweep.py` の変更は **2つの `.count()` の期待値を2→3にする変更と、各1行の説明コメント追加**だった。「数以外を変えていない」は文字どおりにはコメント分だけ異なるが、他の検査式の変更・削除による弱体化はない。fix 前後では同ファイルに変更はない。

wave 全体の変更は親裁定`:123`〜`:130` の6ファイルに収まり、fix はそのうち4ファイルだけを変更している。新しい入口・gate・台帳、driver・事前登録・registry への変更はなく、scope 拡大は認めない。ただし到達性と PID 検証は、scope 内の要求が未充足である。

## 総括

**closed 4件 / partial 2件 / regressed 0件。** 全判定は静的読解による。ファイル変更・テスト・変異実行は行っていない。

親が実測で裏取りすべき点は、中間区間への `exit 2` と PID の `$$ + 1` 化が検査をすり抜けること、末尾改行の `alias/.` が副作用前に拒否されること、番兵出力失敗時の rc=2、および help の順序別終了コードである。