行番号は現 checkout 基準。`T` は `orchestrator/tests/test_p3_autonomous_workload_trial.py`、`A` は `orchestrator/campaign/p3_autonomous_workload_trial.py`。必読6ファイルは読取可能でした。静的検査のみで、編集・実走はしていません。

## 検査 1 — 受理集合の拡大

計画どおりの変更で、既存の赤が緑になる経路は見つかりませんでした。`stage2-plan.md:23–31` は既存処理前への無条件呼出し追加であり、既存 assert の抽出・引数化・捕捉はありません。`pytest.raises` も負例の helper 呼出しだけです（同:40–47）。

**real — 接続削除は負例で検出できない。**  
位置：`brief.md:70–73`、`stage2-plan.md:86`。  
具体シナリオ：`T:1914` 直後に追加する呼出しだけを削除し、helper と負例を残すと、baseline と負例はともに緑になりえます。成果物への影響：守れるのは判定本体の削除までで、「本 test 側の検査を消しても負例が赤になる」という親の説明は成立しません。plan はこの限界を明記しています。

## 検査 2 — 既存被覆の減少

呼ばれなくなる既存 assert は計画上ありません。照合した保存対象は次のとおりです。

- 32反復・順序照合・main thread 集約：`T:1959–1968`
- 4 role の各 payload 1件検査：`T:1915–1918`
- 4 role・variants・secret_records の32件検査：`T:1970–1975`
- 横断7種：`T:1976–1995`
- secret_records の8 field：`T:1942–1956`、`T:1985–1995`
- WAL の build_starts 件数と critic への識別子漏出検査：`T:1931–1941`
- real admission：各 wire の `T:223` と `A:3363`。既存32走の正常経路では計64回を維持

partial で新 assert が失敗すると後続 assert は実行されませんが、その node は既に赤です。緑の走から既存被覆を取り除く経路にはなりません。

## 検査 3 — D1847 との整合

禁止への抵触は見つかりませんでした。`d1847.txt:18–23,43–53` と照合し、32未満への削減、assert 弱化、skip/xfail、動的並行度、production 変更、`contract_loader_binding` の cache、hard timeout の導入はいずれもありません。並行度4（`T:56`）も保存されます。

## 検査 4 — scope 境界

**汎用 gate・共有 helper module・新規 test file・台帳追加・他 test への一般化は持ち込んでいません。** `stage2-plan.md:11–50` の変更は、同一ファイルの局所 helper、既存 node の呼出し、負例1 node に収まります。

親 brief の要求にも、実装 scope を広げる要求は見つかりません。ただし、負例が証明する範囲について過大な説明があります（検査7）。

## 検査 5 — 費用

**要検証 — 新規 node の所要は未測定。**  
位置：`stage2-plan.md:38–50,88`、`acceptance_duration_ledger.json:12070`。  
同構成の既存 `test_pending_critic_failure_is_converted_to_supervisor_error` の登録値は **0.099秒**。追加 node の実行部分は **0.1秒程度を中心に、1秒未満を暫定見積り**とします。収集・fixture・混雑を含む上限ではありません。

具体シナリオ：共有ストレージ等の待ちが増えれば、この登録値から見積もった追加直列時間を超過します。成果物への影響：「数秒以内」は親の実測まで未確定です。

負例は実 `run_trial` 1回、正常な負例経路では1 cell・1 generationです。32 wire の再走ではありません。親の9.77秒は既存32走の pytest 全体の経過時間であり、これを32で割って負例所要にはできません。

## 検査 6 — 並行実行との相互作用

通常の partial 失敗では、`stage2-plan.md:15–17` のメッセージに wire と status が入り、`T:1962` の結果取得で例外が伝播します。新しい共有可変状態はありません。

**要検証 — status 欠落時は専用の wire メッセージが出ない。**  
位置：`stage2-plan.md:15`。  
具体シナリオ：producer が status を欠く report を返すと、assert メッセージの評価前に `KeyError('status')` になります。成果物への影響：拒否は維持されますが、「worker の失敗には wire が残る」という同:29の説明は partial の場合に限定すべきです。

## 検査 7 — 親 brief と親実測への攻撃

**real — wire 数不足と report の未完了を混同している。**  
位置：`brief.md:7–8`、`T:1962–1975`。  
具体シナリオ：収集が31 wireで終われば、既存の件数 assert が赤にします。成果物への影響：「一部の wire しか回らなくても緑」は現コードの説明として不正確です。穴は、32件の収集等を満たした個々の report の status を確認していない点です。

**real — 選んだ負例は、旧 node が受理した欠陥形の再現にはならない。**  
位置：`stage2-plan.md:37–39`、`T:1917`、`brief.md:19–22`。  
具体シナリオ：critic を欠く負例構成を旧 node に持ち込めば、4 role の payload 検査を通りません。成果物への影響：負例は「実 partial を helper が拒否する」証拠にはなりますが、「旧 node は緑、新 node は赤」という受理集合の**真の縮小**を、その負例だけで実証したとはいえません。

**real — 9.77秒を node 単体所要と断定している。**  
位置：`measurement.md:15`。  
`1 passed in 9.77s` は pytest セッションの経過時間です。具体シナリオ：収集や fixture に時間が掛かる環境では node 本体と乖離します。成果物への影響：正確な node 所要としての転記は根拠不足です。また同:28–29は「観測した32 report は追加条件を満たす」までで、将来の走行すべての baseline 成功保証ではありません。

**要検証 — 「gate 側 pin 0件」は検索根拠を超える。**  
位置：`measurement.md:34–52`、`brief.md:55–58`。  
自身でも test 名に加えファイル名・`role-sink-relation` を検索し、`tools`・`hooks`・`.claude`・`.codex` の検索対象では直接 pin を見つけませんでした。`conftest.py:2123` 以降の収集処理も確認し、当該ファイル名・node 名の登録は見つかりませんでした。

ただし、具体シナリオとして、ディレクトリ列挙から動的に hash 対象を作る gate は test 名検索に現れません。その網羅的な閉包監査は未完了です。成果物への影響：「直接参照 pin は未発見」と「pin 閉包を証明済み」は分ける必要があります。

## 総括

既存防壁の削減・D1847違反・scope 拡大は計画上見つかりませんでした。修正すべき主要点は、**負例による接続保証と受理集合の真の縮小を過大に主張しないこと**、および親の wire 数・所要・pin 閉包の説明を証拠の範囲に戻すことです。新規 node の所要と最終差分は未検証であり、テスト緑は報告しません。