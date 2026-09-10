## 読んだ資料

全指定 path を読めた。読めなかった path はなし。

- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/s1-brief.md`
- `/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2135-tictoc-cicada-space/d1360-verbatim.md`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/campaign/genome.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/orchestrator/tests/test_campaign.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cmake/Options.cmake`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/tictoc/CMakeLists.txt`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/tictoc/transaction.cc`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/CMakeLists.txt`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/transaction.cc`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/cicada/include/transaction.hh`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/silo/CMakeLists.txt`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/external/ccbench/cc/silo/transaction.cc`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2135-tictoc-cicada-space/output/insights/2026-09-01_t2115-cross-protocol-impl/README.md`

## tictoc の軸と除外

`Options.cmake:3-6,10-11` により cache entry は `-DCCBENCH_FOO=...` から target-private `FOO=...` へ写像される。tictoc の `OPTIONS` に bare define はない。

| flag | 採否 | 理由 | 一次資料 |
|---|---|---|---|
| `BACK_OFF` | 採用 | universal cache option。abort 後の backoff と leader work の両方で live。 | `cmake/Options.cmake:20,60-68`; `cc/tictoc/transaction.cc:486-496,708-710` |
| `NO_WAIT_LOCKING_IN_VALIDATION` | 採用、制約あり | cache option。非 write-only transaction の lock 競合を即 abort にする。 | `cmake/Options.cmake:27`; `cc/tictoc/CMakeLists.txt:5`; `cc/tictoc/transaction.cc:340-347,563-574` |
| `NO_WAIT_OF_TICTOC` | 採用、制約あり | cache option。競合時に既取得 lock を解放し、pre-verify 後に retry する。 | `cmake/Options.cmake:28`; `cc/tictoc/CMakeLists.txt:6`; `cc/tictoc/transaction.cc:574-623` |
| `PREEMPTIVE_ABORTS` | 採用 | cache option。locked version の `rts` と暫定 commit timestamp を比較して abort する独立した read-path 最適化。no-wait flag の内側ではない。 | `cmake/Options.cmake:44`; `cc/tictoc/CMakeLists.txt:9`; `cc/tictoc/transaction.cc:46-61,128-139` |
| `TIMESTAMP_HISTORY` | 採用 | cache option。通常 validation と write phase に非ネストの live site がある。no-wait retry 内にも site はあるが、それだけには依存しない。 | `cmake/Options.cmake:45`; `cc/tictoc/CMakeLists.txt:10`; `cc/tictoc/transaction.cc:379-406,508-511,587-607` |
| `PARTITION_TABLE` | 除外 | cache option ではあるが tictoc の `.cc` / `.hh` に出現 0 の死にフラグ。 | `cc/tictoc/CMakeLists.txt:7`; `s1-brief.md:47`。対象 `transaction.cc:1-730` に出現なし |
| `SLEEP_READ_PHASE` | 除外 | read の途中へ sleep を挿入する計測撹乱ノブ。 | `cmake/Options.cmake:30`; `cc/tictoc/CMakeLists.txt:8`; `cc/tictoc/transaction.cc:68-70`; `s1-brief.md:25-26` |
| bare define | 該当なし | tictoc の全 protocol option は cache variable 経由。 | `cc/tictoc/CMakeLists.txt:5-10`; `cmake/Options.cmake:27-30,44-45` |
| 導出不能 | 該当なし | 指定資料から全候補の live site、除外理由、依存を静的に導出できる。 | 上記各行 |

採用軸は 5 本で、生空間は `2^5 = 32`。

## tictoc の制約

silo と同じ XOR 制約にはしない。tictoc には「両方 1 の冗長だけを除外する」述語が必要である。

| `(NO_WAIT_LOCKING_IN_VALIDATION, NO_WAIT_OF_TICTOC)` | 制御フロー |
|---|---|
| `(0,0)` | `#if` と `#elif` は展開されないが、`#endif` 後の `expected` 再読込が `transaction.cc:626` にある。lock 解放後は `:627-634` の CAS へ進めるため、blocking spin として有効。 |
| `(1,0)` | 非 write-only では `:564-573` で即 abort。write-only では `is_wonly_` guard を通らず `:626` の再読込へ進む。 |
| `(0,1)` | 非 write-only では `:574-623` で unlock、pre-verify、retry。write-only は同じく再読込経路。 |
| `(1,1)` | `#if` が優先され `#elif` は dead code。全制御フローが `(1,0)` と同じなので冗長。 |

述語案は次の意味にする。

```python
def _tictoc_no_wait_not_both(flags: Dict[str, int]) -> bool:
    return not (
        flags.get("NO_WAIT_LOCKING_IN_VALIDATION", 0)
        and flags.get("NO_WAIT_OF_TICTOC", 0)
    )
```

これにより `(1,1)` に属する 8 通りだけを除外し、`32 - 8 = 24` 通りとなる。

silo は `cc/silo/transaction.cc:160-168` に同じ `#if/#elif` がある一方、locked 値を更新する後続 load がない。runtime の `else` は `expected.lock == false` の場合だけであり、両 flag が 0 だと stale な locked 値を保持する。対して tictoc は `cc/tictoc/transaction.cc:626` で再読込し、さらに no-wait 分岐自体が `:563` の `is_wonly_ == false` に限定される。このため silo XOR の転用は誤りである。

silo の両 0 livelock は既存 notes が示す実測済みの事実だが、tictoc は未実測である。tictoc notes には「両 0 はコード上の再読込経路を持つという静的導出であり、競合時の進行性は未実測」と明記する。

## cicada の軸と除外

| flag | 採否 | 直交操作・意味・依存 | 一次資料 |
|---|---|---|---|
| `BACK_OFF` | 採用 | universal cache option。abort と leader work で live。 | `cmake/Options.cmake:20`; `cc/cicada/transaction.cc:770-772,964-966` |
| `INLINE_VERSION_OPT` | 採用 | `CCBENCH_INLINE_VERSION_OPT_CICADA` で直交操作可能。inline version の GC、生成、abort cleanup を切り替える内部ストレージ最適化。 | `cmake/Options.cmake:53`; `cc/cicada/CMakeLists.txt:5`; `cc/cicada/include/transaction.hh:178-189,219-244,351-364` |
| `INLINE_VERSION_PROMOTION` | 採用、含意制約あり | cache option。read 時に既存 version を inline version へ promotion する最適化。ただし全 site が `INLINE_VERSION_OPT` の内側で、OPT=0 では完全に inert。 | `cmake/Options.cmake:31`; `cc/cicada/CMakeLists.txt:6`; `cc/cicada/transaction.cc:128-135`; `cc/cicada/include/transaction.hh:199-215` |
| `REUSE_VERSION` | 採用 | cache option。回収 heap version を pool へ戻して再利用する。inline 処理の `#endif` 後に独立した `#if REUSE_VERSION` があり、INLINE flags への含意依存はない。 | `cmake/Options.cmake:32`; `cc/cicada/CMakeLists.txt:7`; `cc/cicada/include/transaction.hh:178-189,219-244,351-364` |
| `SINGLE_EXEC` | 除外 | cache optionだが、timestamp に基づく version-chain search を迂回して常に inline version を読む。update の version 生成・挿入と maintenance も迂回する。真の多版 MVCC から単版実行へ「測るものそのもの」を変えるため、最適化軸にしない。未指定時は cache default 0。 | `cmake/Options.cmake:33`; `cc/cicada/CMakeLists.txt:8`; `cc/cicada/transaction.cc:85-119,235-289,705-707,762-768,952-955` |
| `WRITE_LATEST_ONLY` | 採用 | cache option。blind write について、古い timestamp なら早期 abort して latest だけへ install するか、version chain を辿って timestamp 順の位置へ install するかを切り替える。外部の操作内容ではなく、abort・version-install 方針を変える CC 最適化軸と判定する。update の site は `SINGLE_EXEC=0` 側だが、SINGLE_EXEC は除外し default 0 に固定されるため追加制約は不要。 | `cmake/Options.cmake:34`; `cc/cicada/CMakeLists.txt:9`; `cc/cicada/transaction.cc:235-289,488-529` |
| `WORKER1_INSERT_DELAY_RPHASE` | 除外 | cache optionだが特定 worker の commit 前へ delay を挿入する計測撹乱ノブ。 | `cmake/Options.cmake:49`; `cc/cicada/CMakeLists.txt:10`; `cc/cicada/transaction.cc:919-927`; `s1-brief.md:25-26` |
| `PARTITION_TABLE` | 除外 | cache optionだが print 専用の死にフラグ。 | `cc/cicada/CMakeLists.txt:11`; `s1-brief.md:48` が実アンカー `cc/cicada/util.cc:331` を記録 |
| `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` | 除外 | cache optionだが明示的な計測撹乱ノブ。 | `cmake/Options.cmake:38-39`; `cc/cicada/CMakeLists.txt:12-13`; `s1-brief.md:25-26` |
| bare define | 該当なし | 全 protocol option が cache variable 経由。 | `cc/cicada/CMakeLists.txt:5-13`; `cmake/Options.cmake:29,31-39,49,53` |
| 導出不能 | 該当なし | 指定された 5 flag は全て分類可能。動的な性能・進行性は未測定だが、軸の静的導出を妨げない。 | 上記各行 |

採用軸は `BACK_OFF` を含む 5 本で、生空間は `2^5 = 32`。

## cicada の制約

必要な制約は `INLINE_VERSION_PROMOTION => INLINE_VERSION_OPT` の 1 件だけである。

```python
def _cicada_promotion_requires_inline_opt(flags: Dict[str, int]) -> bool:
    return (
        not flags.get("INLINE_VERSION_PROMOTION", 0)
        or bool(flags.get("INLINE_VERSION_OPT", 0))
    )
```

`transaction.cc:128-135` と `include/transaction.hh:199-215` の promotion site は、いずれも `#if INLINE_VERSION_OPT` の内側にある。したがって `(OPT, PROMOTION) = (0,1)` は `(0,0)` と同一 binary behavior になる冗長 genome である。

有効な組は `(0,0)`, `(1,0)`, `(1,1)`。残り 3 軸の各 8 通りと組み合わせて `3 x 8 = 24` 通りとなる。

`REUSE_VERSION` は inline block の外側に独立 site があるため制約不要。`WRITE_LATEST_ONLY` は `SINGLE_EXEC=0` の多版経路で live となり、SINGLE_EXEC 自体を軸から外すため制約不要である。

## notes 案

tictoc:

```python
notes="tictoc の現行 CMake から直交操作できる YCSB 向け空間。"
      "PARTITION_TABLE は .cc/.hh 出現 0 の死にフラグ、SLEEP_READ_PHASE は"
      "計測撹乱ノブとして除外する (絶対規律4)。"
      "生 2^5=32、no-wait は #if/#elif により両 1 が (1,0) と冗長なので"
      "8 通りを除外し 24 有効。両 0 は lock word を再読込して待つため"
      "silo の XOR とは異なる。24 通りは YCSB workload での静的導出であり、"
      "tictoc の競合時進行性は未実測。OPTIONS に bare define はなく、"
      "導出不能として残す候補もない。",
```

cicada:

```python
notes="cicada の現行 CMake から直交操作できる YCSB 向け多版 MVCC"
      "最適化空間。SINGLE_EXEC は timestamp による version chain 選択と"
      "多版 maintenance を迂回して単版実行へ変え、測るものそのものを"
      "変えるため軸にしない。PARTITION_TABLE は print 専用の死にフラグ、"
      "WORKER1_INSERT_DELAY_RPHASE / INSERT_*_DELAY_MS は計測撹乱ノブとして"
      "除外する (絶対規律4)。WRITE_LATEST_ONLY は blind write の early-abort /"
      "version-install 方針を変える最適化軸として含める。生 2^5=32、"
      "INLINE_VERSION_PROMOTION => INLINE_VERSION_OPT 制約で 8 冗長を除外し"
      "24 有効。24 通りは YCSB workload での静的導出であり、実測値ではない。"
      "OPTIONS に bare define はなく、導出不能として残す候補もない。",
```

## 実装プラン

1. `orchestrator/campaign/genome.py:63-71` の既存 `_no_wait_xor` は silo 専用として変更しない。その直後へ `_tictoc_no_wait_not_both` と `_cicada_promotion_requires_inline_opt` を追加する。

2. `orchestrator/campaign/genome.py:87-105` の `MOCC_SPACE` 後、現行 `SPACES` 定義の前へ `TICTOC_SPACE` を追加する。axes は次の 5 本を全て `[0, 1]` とする。

   - `BACK_OFF`
   - `NO_WAIT_LOCKING_IN_VALIDATION`
   - `NO_WAIT_OF_TICTOC`
   - `PREEMPTIVE_ABORTS`
   - `TIMESTAMP_HISTORY`

   `constraints=[_tictoc_no_wait_not_both]` とし、上記 notes を設定する。

3. 同じ位置へ `CICADA_SPACE` を追加する。axes は次の 5 本を全て `[0, 1]` とする。

   - `BACK_OFF`
   - `INLINE_VERSION_OPT`
   - `INLINE_VERSION_PROMOTION`
   - `REUSE_VERSION`
   - `WRITE_LATEST_ONLY`

   `constraints=[_cicada_promotion_requires_inline_opt]` とし、上記 notes を設定する。`SINGLE_EXEC` は追加しないため cache default 0 のままとなる。

4. `orchestrator/campaign/genome.py:108-112` の古い「初手 mocc まで」のコメントを 4 protocol 登録済みの説明へ更新し、`SPACES` に `"tictoc": TICTOC_SPACE` と `"cicada": CICADA_SPACE` を追加する。

5. `orchestrator/tests/test_campaign.py:228-251` の genome test 群を拡張する。mocc の既存 2 test は保持し、その直後へ tictoc/cicada の軸、除外、制約 test を追加する。

6. `orchestrator/tests/test_campaign.py:248-251` の `test_tictoc_and_cicada_remain_unregistered` は削除し、登録 identity を確認する `test_tictoc_and_cicada_are_registered` へ差し替える。

7. build、benchmark、測定、freeze bytes、`docs/phase3.md`、新 gate、台帳、汎用化には触れない。実装子は diff の静的確認までとし、pytest 実走と緑判定は親へ委ねる。

## test 計画

| 関数名 | assert 内容 |
|---|---|
| `test_tictoc_and_cicada_are_registered` | `space_for("tictoc") is TICTOC_SPACE`、`space_for("cicada") is CICADA_SPACE`。旧 KeyError 期待を完全に反転する。 |
| `test_tictoc_space_has_twenty_four_operable_ycsb_boolean_genomes` | `raw_size() == 32`、axes の集合が指定 5 本と完全一致、`len(enumerate()) == 24`、canonical が 24 個全て一意、全 genome の protocol が `tictoc`。 |
| `test_tictoc_space_excludes_redundant_double_no_wait_but_keeps_wait_pair` | 列挙結果の no-wait pair 集合が厳密に `{(0,0), (0,1), (1,0)}`。制約が無ければ `(1,1)` が混入して落ち、silo XOR を誤用すれば `(0,0)` が欠けて落ちる。 |
| `test_tictoc_space_excludes_dead_and_measurement_axes_and_names_ycsb_scope` | `PARTITION_TABLE`, `SLEEP_READ_PHASE`, `TRACE` が axes にない。notes に `PARTITION_TABLE` と `死にフラグ`、`SLEEP_READ_PHASE` と `計測撹乱ノブ`、`YCSB workload`、`24`、`未実測`、`silo` と `XOR` がある。 |
| `test_cicada_space_has_twenty_four_operable_ycsb_boolean_genomes` | `raw_size() == 32`、axes が指定 5 本と完全一致、列挙数 24、canonical 24 個が一意、全 protocol が `cicada`。これにより `WRITE_LATEST_ONLY` の採用も固定する。 |
| `test_cicada_space_requires_inline_opt_for_promotion` | `(INLINE_VERSION_OPT, INLINE_VERSION_PROMOTION)` の集合が厳密に `{(0,0), (1,0), (1,1)}`。制約が無ければ `(0,1)` が混入するため落ちる非恒真 test になる。 |
| `test_cicada_space_excludes_semantic_dead_and_measurement_axes_and_names_ycsb_scope` | `SINGLE_EXEC`, `PARTITION_TABLE`, `WORKER1_INSERT_DELAY_RPHASE`, `INSERT_READ_DELAY_MS`, `INSERT_BATCH_DELAY_MS`, `TRACE` が axes にない。notes に `SINGLE_EXEC`、`単版`、`測るものそのもの`、`PARTITION_TABLE`、`print 専用`、`計測撹乱ノブ`、`WRITE_LATEST_ONLY`、`YCSB workload`、`24` がある。 |

値域の取り違えも防ぐため、2 件の size test では `all(values == [0, 1] for values in gs.axes.values())` も assert する。

## 裁定パッケージ候補

なし。

P1 は「silo XOR を転用せず、tictoc は両 1 のみ除外」、P2 は含意制約、P3 は `SINGLE_EXEC` 除外・`WRITE_LATEST_ONLY` 採用、P4 は両 flag 採用として、現行 scope 内で静的に解ける。trace-hook 移植、certified admission、calibration、between-run floor の再実測は既裁定の別 wave 残余であり、本実装計画には含めない。

## 残る不確かさ

- tictoc `(0,0)` は stale 値による silo 型 livelockではないとコードから導けるが、継続的競合下の公平性や starvation は未実測。
- `WRITE_LATEST_ONLY` は提示コード上、workload を変えず blind write の abort・install 方針を変える軸と判定した。性能効果と verifier 上の正しさは未実測。
- cicada `PARTITION_TABLE` の print 専用判定は、射影対象の `s1-brief.md:48` に記録された親の `util.cc:331` 実測アンカーへ依拠する。`util.cc` 自体は今回の必読射影に含まれていない。
- 24 通りはいずれも YCSB 向けの静的 genome 数であり、build 成功、実行可能性、性能、certification を主張しない。

## 総括

tictoc は 5 軸・生 32 通りから、冗長な no-wait 両 1 のみを除外して 24 通りとする。
silo と違い、tictoc の両 0 には lock word 再読込があるため XOR 制約は使わない。
cicada は `SINGLE_EXEC` を多版 MVCC の意味を変えるノブとして除外し、残る 5 軸を採る。
promotion の含意制約で cicada も生 32 通りから 24 通りとなる。
変更範囲は `genome.py` の登録・導出と `test_campaign.py` の期待差し替えに限定する。