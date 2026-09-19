## 総括

**GO（実装着手）。must-fix はなし。** 指定資料と対象コードの静的検査では、親brief・planを覆す具体的な破綻は確認できませんでした。実装後の受入判定ではありません。編集・実測・pytest・commit・子起動は行っていません。

**must**
- なし。承認済み(a-1)+(a-3)を変更する理由、新gateを追加する理由はありません。

**should**
- **Pの脱落も変異候補に含める。** [plan-result.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/plan-result.md:56)はQ/W/G/A/Cの脱落だけを列挙しています。再現例：既定値・spec=3600でPを落とすと、実効値が5130秒から4950秒になります。前段余裕の欠落を検査が取り逃すため、最小処置はP脱落の1変異と、独立した期待値を検査する専用nodeの追加です。
- **内側期限後のhold有無を分けて回帰確認する。** [mutation_harness.py:365](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:365)。再現例：外側は未発火でも、内側rc=16・`job_may_remain=true`ならhold・変異残置が必要です。これを「in-bandだから復元・resume可能」と扱うと、生存jobが読む変異sourceを復元してしまいます。最小処置は、planの回帰対象にこのケースを明記し、残存なしのrc=16と区別することです。

**nit**
- [plan-result.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2484-timeout-contract/plan-result.md:34)のPは前段だけでなくpoll・終端処理の余裕も含みます。実装コメントにもその意味を残すと、後から「前段実測15.9秒」だけを根拠に削られる誤解を防げます。

**refuted — 攻撃したが成立しなかった点**
- **max補正でcollection拒否が消える：不成立。** gateへ元のspec値を渡す計画なら、Q/G=1800/600で2399拒否・2400通過を維持します。根拠：[mutation_harness.py:1451](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/mutation_harness.py:1451)。
- **dispatch callerの漏れ：確認なし。** `_run_tests`の本番callerはcollection・baseline・mutationの3か所で、計画は全部を対象にしています。resume時も実行callerで補正できます。
- **walltime overrideとの不整合：計画上はなし。** 実行側は延長overrideも転送し、collectionはW既定値です。計画はこの差を扱っています。根拠：[run_tests.py:1343](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2484-timeout-contract/tools/run_tests.py:1343)。
- **local hang短期停止・復元の喪失：計画上はなし。** localは従来値を維持し、既存復元テストも回帰対象です。
- **変異の複数理由失敗をKILLEDとして受理：計画上はなし。** 専用fixture・選択node・期待node完全一致を維持する方針です。実装時には、予算計算の誤りを診断文言assertでも同時検出する構成を避けてください。
- **有限Pでhold消滅を保証できる：不成立。** 計画自身が保証を否定しており、内側期限・回収・holdを保持しています。P=180秒の実効性は親の実測事項です。