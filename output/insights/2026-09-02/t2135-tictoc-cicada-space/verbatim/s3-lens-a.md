## 読んだ資料

指定された 10 path はすべて読めた。読めなかった path はなし。

- `s1-brief.md`
- `artifacts/dev-wave-t2135-tictoc-cicada-space/s2-plan.md`
- `d1360-verbatim.md`
- `orchestrator/campaign/genome.py`
- `orchestrator/tests/test_campaign.py`
- `external/ccbench/cc/tictoc/CMakeLists.txt`
- `external/ccbench/cc/tictoc/transaction.cc`
- `external/ccbench/cc/silo/transaction.cc`
- `external/ccbench/cmake/Options.cmake`
- `output/insights/2026-06-22_silo-both-no-wait-zero-livelock.md`

## 正しさ境界の所見

1. **登録が測定経路を開かないという結論は、射影資料だけでは証明できない。確認済みの breach ではなく、証拠不足である。**

   `SPACES` は `space_for()` が返す辞書だが、測定側は registry を通さず、呼び手が直接構築した `Genome` を `pipeline.evaluate()` や `run_campaign()` に渡せる。実例は `orchestrator/tests/test_campaign.py:304-309,3442-3449,8693-8700,9409-9416`、registry 実装は `orchestrator/campaign/genome.py:109-118`。

   したがって、親 brief の「`space_for` production caller 0」という識別子検索だけでは、測定入口の閉包や正しさ admission を証明しない。逆に、射影内には `SPACES` から測定へ自動接続する経路も見えないため、今回の登録が直ちに経路を開くとも断定できない。

   放置時には、別名 import、`SPACES` 直接参照、外部 CLI、将来の consumer が登録済み tictoc を渡した場合に、trace 未整備 protocol がどこで必ず reject されるか不明なままになる。D1360 が禁止する正しさ未検証性能観測の公式利用境界に関わる。`d1360-verbatim.md:8-10`

2. **予定 test は genome 宣言を強く検査するが、正しさ境界は検査しない。**

   予定されている assert は登録 identity、軸、列挙数、制約、notes に限定される。`s2-plan.md:164-174`。`Genome("tictoc", ...)` が評価入口で trace/certification 不備により fail-closed になることは検査しない。

   旧 `test_tictoc_and_cicada_remain_unregistered` は粗いながら「未準備 protocol を registry に出さない」防壁だった。`orchestrator/tests/test_campaign.py:248-251`。新 test は登録後の構造検出力を上げる一方、この安全側の負期待に相当する downstream admission 回帰を置き換えていない。

   放置時には genome test が全て通っても、正しさ未検証経路が別箇所で開いている退行を検出できない。ただし新 gate の実装は今回の scope 外なので、後述の裁定パッケージ候補とする。

## 整合・実効性の所見

1. **最重点の no-wait 判定は段 2 プランが正しく、親 brief の XOR 転用が誤りである。**

   tictoc の `:626` は外側ではなく、`for (;;)` の内側である。外側 `retry: for` は `external/ccbench/cc/tictoc/transaction.cc:556-557`、内側ループは `:561-635`、再読込は `:626`。したがって `(0,0)` で locked を観測しても、各反復で `expected` を更新し、unlock 観測後の次反復で `:627-634` の CAS 側へ入れる。

   silo は初回 load が `external/ccbench/cc/silo/transaction.cc:158`、内側ループが `:159-184` であり、locked 分岐 `:160-168` の後に再読込がない。実測 insight の機構説明とも一致する。`output/insights/2026-06-22_silo-both-no-wait-zero-livelock.md:26-56`

   放置して親の XOR を採用すると、有効な tictoc `(0,0)` を過剰除外し、探索空間を 24 から 16 に誤って縮める。

2. **`PREEMPTIVE_ABORTS` と `TIMESTAMP_HISTORY` を独立軸にする段 2 の結論は妥当である。**

   `PREEMPTIVE_ABORTS` の call site は no-wait 分岐外の read path にある。`external/ccbench/cc/tictoc/transaction.cc:128-139`。`TIMESTAMP_HISTORY` は no-wait retry 内の `:587-606` だけでなく、通常 validation の `:379-406` と write phase の `:508-511` に独立 site がある。

   よって `NO_WAIT_OF_TICTOC=0` では retry 内 site が無効になるが、`TIMESTAMP_HISTORY` 全体は無効にならない。no-wait 対への含意制約は不要である。放置時の成果物変更はなし。段 2 の 5 軸判断を維持できる。

3. **tictoc `PARTITION_TABLE` の「完全な死にフラグ」は、提示された一次資料では確定できない。**

   親 brief は「tictoc の `.cc`/`.hh` に出現 0」とする。`s1-brief.md:47`。しかし build 対象には `transaction.cc` だけでなく `util.cc` と四つの workload がある。`external/ccbench/cc/tictoc/CMakeLists.txt:1-3`。`transaction.cc` 自身も protocol header と共通 header を複数 include する。`external/ccbench/cc/tictoc/transaction.cc:7-14`

   段 2 は `transaction.cc` に無いことと親の記録だけで死にフラグを確定している。`s2-plan.md:30,105-107`。workload 側や共通 header を含む transitive な探索範囲が示されていない。

   放置時には、実際には YCSB 等で live な軸を除外し、notes に事実でない「死にフラグ」を固定する可能性がある。これは current scope 内の軸導出なので、実装前に親側で検索範囲を補完すべきである。

4. **`CACHE STRING` と「独立に設定可能」は区別すべきである。**

   CMake 上は各 tictoc option が別々の cache variable から一対一で展開されている。`external/ccbench/cmake/Options.cmake:27-30,44-45`、`external/ccbench/cc/tictoc/CMakeLists.txt:5-10`。提示範囲には、ある値が別 option の CMake 展開値を変更する式はない。

   一方、実行時の意味は直交していない。`#if/#elif` により `NO_WAIT_LOCKING_IN_VALIDATION=1` は `NO_WAIT_OF_TICTOC` の branch を消す。`external/ccbench/cc/tictoc/transaction.cc:564-624`。`TIMESTAMP_HISTORY` にも `NO_WAIT_OF_TICTOC` 内だけの site がある。`:574-607`

   したがって「CLI から個別指定できる」という意味なら妥当だが、「全組合せが異なる挙動を持つ」という意味では誤りである。段 2 は no-wait 冗長制約と timestamp の外部 site 確認で、この差を実質的には処理できている。

5. **予定される制約 test は恒真ではなく、制約取り外し変異を検出できる。notes test は事実を検証しない。**

   `GenomeSpace.enumerate()` は全 Cartesian product を作ってから制約で filter する。`orchestrator/campaign/genome.py:35-41`。予定軸が全て `[0,1]` なら `(1,1)` は raw 集合に必ず存在し、`{(0,0),(0,1),(1,0)}` との厳密一致は制約削除、XOR 誤用、別組除外のいずれも検出する。`s2-plan.md:167-169,174`

   axes の完全一致、値域、列挙数 24、canonical 一意性も併用するため、性質だけを見る弱い assert ではない。旧未登録 test の差し替えも、registry 構造については検出力低下ではない。`s2-plan.md:166-174`

   ただし notes の語句存在 assert は、`PARTITION_TABLE` が本当に死んでいることや `:626` が残っていることを検査しない。C++ 側の根拠が変わっても文字列だけで通る。放置時には宣言と一次資料の drift を検出できない。

## 親 brief の実測値への指摘

- **`PARTITION_TABLE` の一般化が過大。** `.cc/.hh` の検索 root、共通 header、workload source の包含が記録されていないため、「出現 0」から「完全な死にフラグ」へ進めない。`s1-brief.md:43,47`、`external/ccbench/cc/tictoc/CMakeLists.txt:1-3`

- **`CACHE STRING` の一般化が過大。** 個別指定可能性は確認できるが、意味上の直交性とは同値でない。no-wait の `#if/#elif` が具体的反例である。`s1-brief.md:45`、`external/ccbench/cc/tictoc/transaction.cc:564-624`

- **`space_for` caller 0 の一般化が過大。** `space_for` は唯一の測定入口ではなく、直接構築した `Genome` を評価できる。`orchestrator/tests/test_campaign.py:3442-3449,8693-8700`。caller 0 自体は射影範囲内では反証されないが、それだけから「測定経路を開かない」は導けない。`s1-brief.md:54`

## tictoc no-wait 制約の判定

置くべき制約は XOR ではなく、段 2 案の「両方 1 だけを禁止」である。

```python
return not (
    flags.get("NO_WAIT_LOCKING_IN_VALIDATION", 0)
    and flags.get("NO_WAIT_OF_TICTOC", 0)
)
```

制御構造は次の通り。

- `retry` は外側 write-set loop の label。`transaction.cc:556-557`
- 各 tuple の初回 load は `:559-560`。
- 内側 spin loop は `:561-635`。
- locked かつ非 write-only では compile-time no-wait branch を処理する。`:562-624`
- `(0,0)` ではその branch 本体が空でも、`expected` を `:626` で再読込して内側 loop の先頭へ戻る。
- write-only は `is_wonly_` guard を通らないが、同じ `:626` へ進む。従って write-only の根拠だけで非 write-only を説明しているわけではなく、両方に再読込がある。
- `(1,1)` は `#if` が選ばれ `#elif` が消える。validation 後の status check も `(1,0)` と同じ。`transaction.cc:340-347,564-624`

この述語は `[0,1]` の raw 候補に含まれる `(1,1)` で偽になるため恒真ではない。5 軸が確定するなら有効数は `3 × 2^3 = 24`。

notes は「blocking spin として有効」と広く断定せず、次の限界まで書くのが正確である。

> `(0,0)` は inner spin loop 内で lock word を再読込するため、silo で実測された stale-expected livelock と同じ機構ではない。競合下の完走性、公平性、starvation は tictoc では未実測である。

## 裁定パッケージ候補

- **正しさ境界の repo-wide 閉包確認。** `between_run_floor.py` の exact predicate、`SPACES`/`space_for` の直接・別名・動的参照、CLI と campaign entrypoint、tictoc/cicada が未検証のまま certified にならないことを別 wave で確認する。新 gate や恒久 inventory test の追加は今回の scope 外。

- **tictoc `(0,0)` の競合実測。** 今回の静的登録を妨げるものではないが、将来 measurable/certified campaign に入れる前に、複数 thread の完走性を確認する。今回の wave では測定しない。

## 見落としの自己申告

- 必読 10 path は全て読めた。
- 単独段 dispatch の射影外である `between_run_floor.py`、`ProtocolHelpers.cmake`、tictoc の `util.cc`、protocol/common include、各 workload source、repo-wide caller は読んでいない。このため正しさ境界と `PARTITION_TABLE` の完全な閉包は判定不能。
- build、pytest、benchmark は実行していない。緑は主張しない。
- tictoc の公平性や starvation は静的には判定していない。

## 総括

親 brief の tictoc XOR は誤りで、段 2 の「両 1 のみ除外、24 有効」が正しい。
`:626` は inner loop 内であり、write-only と非 write-only の双方が再読込へ到達する。
`PREEMPTIVE_ABORTS` と `TIMESTAMP_HISTORY` は独立軸として維持できる。
一方、`PARTITION_TABLE` の死にフラグ判定は検索範囲不足で、実装前の補完が必要。
予定 test は軸と制約には有効だが、正しさ未検証測定経路の閉包は保証しない。