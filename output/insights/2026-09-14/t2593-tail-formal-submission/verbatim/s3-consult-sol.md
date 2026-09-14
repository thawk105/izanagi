## 読解範囲

必読6ファイルはすべて読めました。以下は**静的読解による所見**です。ファイル変更・テスト実行・投入はしていません。

参照の略号を次のように用います。

- `B`：親 `brief.md`
- `P`：段2の `plan.md`
- `S`：`tools/pegasus/submit_b10_backoff_grid.sh`
- `J`：`tools/pegasus/b10_backoff_grid.sh`
- `F`：`orchestrator/campaign/b10_backoff_static_tail_formal.py`
- `R`：`docs/b10-backoff-static-tail-preregistration.md`

## 1. 「1 bit 不変」と argv 正規化の契約が両立するよう定義されていない

- **所見：** 親の不変条件は文字どおりには達成できず、plan の「可変ID等」の正規化範囲も未定義なので、必須の変更と回帰を区別できません。
- **根拠〔読解〕：** `B:49–50` は環境変数まで完全不変としますが、`S:95–96,184` は編集対象の job script の SHA を計算して渡します。今回の編集だけで旧3系列の argv 内の SHA も変わります。`P:111` の比較で旧 SHA を固定すれば必ず赤になり、SHA を無検査で置換すれば、例えば `S:96` の直後に誤った64桁 SHA を代入する編集を見逃します。その場合、実 job は `J:376–378` の SHA 束縛で拒否されます。日時・PID・nonce（`S:93–94`）も、値の置換前に形式と参照関係の検証が必要です。
- **成果物への影響：** 誤った script 参照を持つ投入 receipt が生成され、旧系列が実行前に拒否されても「argv 不変」が緑になり得ます。
- **深刻度：must-fix。** 比較対象は旧系列の構造・意味・束縛関係と明記し、SHA は当該版の実 bytes との一致を検証してください。group ID は固定部分と workload suffix、nonce は3 job と manifest 間の一致を残して正規化すべきです。

## 2. qsub argv の完全一致だけでは旧系列の成果物不変を守れない

- **所見：** plan の互換性テストには、投入 receipt 自体の回帰を検出する観測が抜けています。
- **根拠〔読解〕：** 具体的な変異は `S:121` の manifest schema を `b10-backoff-grid-submit-event/v2` に変える編集です。全旧系列の成果物が変わりますが、`P:111` の qsub argv 比較、`P:118` の job 呼出し比較、`P:121` の finalizer 検査では赤になりません。既存 `orchestrator/tests/test_backoff_extended_sweep.py:1750–1755` も run_kind のソース文字列と出現数を検査するだけです。
- **成果物への影響：** 旧系列の投入台帳の schema が変わり、既存 consumer からの参照・受理が変わります。
- **深刻度：must-fix。** 既に実行する submit テストで生成された receipt の schema・event・run_kind・argvとの対応も確認してください。新しい台帳の追加は不要です。

## 3. 8 commit＋execution 実在は成功の十分条件ではなく、非ゼロ終了から finalizer への非到達が未検証

- **所見：** P1-b は既存の失敗停止経路と組み合わせれば成立しますが、plan の負例はその組合せを検証していません。
- **根拠〔読解〕：** `F:639–642` は execution を直接 create して書くため、8 commit 後の `F:773` で書込み・close が失敗すると、通常ファイルの execution が残ったまま異常終了し得ます。外側 timeout が execution 作成後、プロセス終了前に発火する場合も同様です。現行は `J:595` の非ゼロ終了を `J:153–160` が停止させるため finalizer に到達しません。しかし `P:123–125` は finalizer の入力負例であり、「成果物条件は満たすが sweep が失敗」という経路を含みません。
  
  `report_sweep_timeout()` 自体は `F:668–675` から **`<output-root>/reports/<workload>/` に `.json`・`.dat`・`-complete.json`** を書きます。新規走の内部 deadline は execution 作成より前（`F:750–773`）なので、この経路では8 commit があっても execution は生成されません。既存 execution の削除もしません。既存 timeout テストは先に execution を作る fixture を使用しています（`orchestrator/tests/test_b10_backoff_static_tail_formal.py:315,448–464`）。
  
  一方、`run` が rc=0 で終了しながら execution 作成を飛ばす正常経路は、読解上ありません（`F:773–799`）。正常な `report` は execution を書きませんが、job が呼ぶ subcommand は `run` です。
- **成果物への影響：** 失敗終了の握り潰しが入ると、不完全な execution を持つ job に `completion.json` が発行され得ます。
- **深刻度：must-fix。** 新しい正しさ gate ではなく、予定の shell テストに「8 commit＋executionあり、driver rc≠0／timeout→completion不在」を加えてください。

## 4. 新 literal は一致しているが、fixture の期待値を生産コードから取ると二重定義を検査できない

- **所見：** 現在の plan に literal の食い違いはありませんが、shell に複製する run_kind・stem の検査元を固定する必要があります。
- **根拠〔読解〕：** 事前登録の現物 `R:1063–1065` は逐語で次を定めています。

  > `run_kind` は `t2500-tail-formal`、report schema は  
  > `t2500-backoff-static-tail-formal-report/v1`、成果物 stem は  
  > `t2500-backoff-static-tail-formal`

  `P:13,18,65` は run_kind と stem を shell 側にも持ちます。report schema は新設せず、既存 driver が spec から生成します（`F:636,649–660`）。spec の literal だけを変更すれば `F:144–147` が拒否します。shell の stem だけを誤変更した場合は、登録済みの正しい名前を持つ fixture を使う `P:123` が赤になる設計です。ただし fixture 名を検査対象 shell から抽出すると追随して緑になります。
- **成果物への影響：** 誤った stem を要求する finalizer が正常走を拒否し、登録成果物への参照が切れます。
- **深刻度：nit。** 既存の完全一致テスト計画に、期待 literal は事前登録由来で固定し、shell から逆算しないと明記してください。

## 5. explore は判定に効く外部データだが、正しさゲートの緩和経路は確認されない

- **所見：** `--explore-campaign` は correctness mode の比較基準を供給しますが、検査命令・反復数・閾値を供給する経路ではありません。
- **根拠〔読解〕：** `F:351–358` は `HISTORICAL_RAW` admission、run_kind、非空で一意な `verify_done.payload.workload.tag` を検査します。これは探索 campaign の現行 certified 認証を意味しません。実行では取得 mode を `F:285` が `legacy` に限定し、`F:761` は spec の正しさ反復数で `CorrectnessWorkload` を作ります。report では外部 mode が `F:418` の比較に効きますが、同時に `F:343–348` が本走の5本・certified・anomalyを要求し、本走 admission も `F:393` で別に行います。探索の数値や report verdict はこの経路から渡りません。
- **成果物への影響：** 別 mode の探索入力は本走の起動または report の受理を拒否する方向に効き、同じ mode の別探索 campaign は比較基準として区別されません。
- **深刻度：scope 外。** 特定探索 campaign の identity を追加固定する gate は別 scope です。この wave の must-fix とする根拠はありません。

## 6. P1-c は通常の受理集合を狭めないが、help の順序には取りこぼしがある

- **所見：** 「旧種別＋新 flag を rc=2」は現状維持ですが、新 flag の認識追加と即時 help 終了を組み合わせると rc=0 の集合が広がり得ます。
- **根拠〔読解〕：** 現在、新 flag は `S:29–31` の未知引数で rc=2 となるため、P1-c 自体は旧系列の受理集合を狭めません。ただし `--run-kind extended --explore-campaign /x --help` は現在 rc=2 なのに、`P:14–15` の「新 flag を読んで loop 後に拒否」と `S:25–27` の即時 help 終了をそのまま組み合わせると rc=0 になります。逆順の `--help --explore-campaign /x` は現在から rc=0 です。`P:114` の負例にはこの順序差がありません。
- **成果物への影響：** qsub や成果物生成には到達しませんが、CLI の成功終了集合が変わり、親の厳密な不変条件から外れます。
- **深刻度：nit。** help を含む引数順序の扱いを明記し、通常の P1-c を「互換性を狭める」と誤って撤回しないでください。

## 総括

最も重い3件は、**SHAを含む正規化契約の未定義、投入 receipt の観測漏れ、driver 非ゼロ終了から finalizer への非到達の未検証**です。いずれも既存の比較・テスト計画の具体化で対処でき、新しい gate や台帳は不要です。

親が実測で裏取りすべきなのは、誤SHA・manifest schema変更で互換性テストが赤になること、および8 commit＋executionが残っても driver失敗／timeoutでは completionが発行されないことです。

内部 timeout が生成する記述用3成果物と、正常 `run` の execution を区別して確認してください。本段では、実行成功・テストの赤緑・性能測定可能性を実測確認していません。