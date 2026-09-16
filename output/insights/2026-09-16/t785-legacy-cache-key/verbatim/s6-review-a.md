## 所見

**RA-1・SHOULD — 新規テストは片側だけを比較する誤修正を見逃す。**

根拠: `orchestrator/tests/test_campaign.py:3217` は cc/cxx を常に同時変更する。このため `buildcache.py:641` の条件を `cxx == "g++-13"` だけにしても、新規テスト・既存 compiler 名分離テスト・golden のすべてが通る構造である。`cc == "gcc-13"` だけの場合、新規テストは見逃すが、既存の compiler 名分離テスト (`test_campaign.py:3197`) が検出する。

同じ新規テスト内に、歴史的組から **cc だけ変更する入力と cxx だけ変更する入力**を追加すると、この穴を閉じられる。literal の取り違えも新規テスト単独では必ずしも検出しない。例えば比較先を `("gcc-14", "g++-14")` にすると歴史キー H 自体が suffix 付きで計算され、相対比較は成立する。ただし、この場合は既存 golden (`test_campaign.py:11220`) が検出する。

放置時の成果物影響: 現在の実装に誤りはないが、将来の片側比較への退行を受理するテスト集合が残る。cc だけ替えた要求が旧 binary を参照し、compiler 記録と異なる条件の検査結果・性能値をレポートや台帳へ取り込む経路を見逃し得る。今回、そのような成果物の発生を実測したわけではない。

MUST 所見はない。

## 親の実測の検算

以下、job 内のパスは `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key/` を基準とする。

**修正の到達範囲。** `buildcache.py:3451` は実際の build 要求の cc/cxx を明示して `cache_key()` へ渡す。したがって、既定変更後に新しく import したプロセスでは、次の経路すべてに固定した省略条件が効く。

| 呼出経路 | compiler の取得方法・根拠 |
|---|---|
| s1 | 定義時既定。`s1_verify_extime_calibration.py:390` |
| s2 | 定義時既定。`s2_verify_calibration.py:350`、`:354` |
| s3 | 定義時既定。`s3_lock_coverage.py:258` |
| s5 | 定義時既定。`s5_permutation_coverage.py:293` |
| pipeline の legacy 分岐 | 定義時既定。`pipeline.py:1991`、`:2002`。compiler 入りの `common` は build_v2 用 |
| backoff_profile | site 解決した runtime の cc/cxx。`backoff_profile.py:273`、`:307`、`:857` |
| between_run_floor | Pegasus 分岐は site 解決、それ以外は定義時既定。`between_run_floor.py:316`、`:324` |
| pegasus_floor_scoping | site 解決した cc/cxx。`pegasus_floor_scoping.py:214`、`:218` |

`compilers_for_current_site()` は Pegasus compute では固定の `gcc/g++`、それ以外では module global を返す (`buildcache.py:1863`)。compute では DEFAULT の編集だけでは要求 compiler 自体が変わらない。変更された要求が歴史的組と異なる場合は suffix が付き、今回の省略条件による衝突を防ぐ。

s1/s2/s3/s5・非 Pegasus between_run_floor の evidence 側に別の既定が残る点は、裁定 `s4-ruling.md:22` に既知の限界として記載済み。今回の変更がこれを解消したとは言えない。同名 compiler の実体・版変更も同様に対象外であり、追加対応は **scope 外候補**となる。

**現行 key。** 現行 DEFAULT は `("gcc-13", "g++-13")` (`buildcache.py:622`)。変更前後の条件はこの状態では同値であり、残りの pre-image・hash 計算は変更されていない。したがって現行通常状態の全入力で key は不変である。

golden は `test_campaign.py:11067`、照合は `:11217`。直接 consumer の `tools/pegasus/probes/t2187_adaptive_const_probe.py:3925` と `:4346` も、対応する build と同じ cc/cxx・admission を渡している。今回の差分による consumer と build の key 不一致は見つからない。

**変異の完全集合。** 登録された4 node 内では、静的に次の集合と一致する。

| 変異 | 期待 KILLED 集合 |
|---|---|
| M1 | 新規テスト |
| M2 | golden テスト |
| M3 | compiler 名分離テスト、新規テスト |

trace/genome/commit 分離テストは、どの変異でも比較する軸の差が残る。

ただし、**4 node 外では M2 に追加の赤が出る経路がある**。`orchestrator/tests/test_p3_s4_loop_sort.py:1708` の `test_sort_contract_none_preserves_preexisting_identities` は、`:1745` で compiler suffix のない pre-image を独立に組み立て、`:1752` で `cache_key()` と比較している。常に suffix を付ける M2 はこの assertion も破る。裁定の erratum (`s4-ruling.md:81`) は対象を4 node に限定しているため登録との矛盾はないが、その完全集合を全 suite の集合として記録してはいけない。以上は実走結果ではなく静的判定である。

**probe の差し替え範囲。** `t785_legacy_cache_probe.py:234` で実 evidence、`:240` で実 context/admission を導出し、`:257` で差し替える production 関数は `_run` だけ。`:258` の `build()` 呼出は cc/cxx を省略し、`:264` で復元している。定義時既定との一致も `:224` で検査している。

差し替えは CMake を実行せず、configure 相で要求 cxx に極小 C++ をコンパイルさせる (`:116`、`:123`)。したがって「production の cache/admission/evidence 経路を通じて異なる compiler の ELF を返した」という主張は支えるが、**実 CCBench binary のビルド・動作・性能の検証ではない**。この制限は probe 冒頭 `:5` と brief `s1-brief.md:17` に明示されている。

**4 JSON の整合。**

| 相 | key | cached | ELF `.comment` |
|---|---|---:|---|
| 修正前 seed | `silo_fed9a86c14_t0` | false | GCC 12.3.0 |
| 修正前 gcc 要求 | `silo_fed9a86c14_t0` | true | GCC 12.3.0 |
| 修正後 seed | `silo_6c154d405d_t0` | false | GCC 12.3.0 |
| 修正後 gcc 要求 | `silo_f368efad6c_t0` | false | GCC 11.4.0 |

各 JSON の `:12`、`:14` が key/cached。`.comment` は `before-hit-gcc.json:40`、他の3本は `:65` にある。

修正前 hit は seed と binary SHA256 が一致し、`run_calls=[]`、要求 cxx は実体・版とも異なる。`before-hit-gcc.json:82` の比較結果は `reproduced_false_hit=true` を支える。修正後は新しい要求でのコンパイル記録と返却 binary の SHA256 が一致し、`after-hit-gcc.json:144` は `fix_demonstrated=true` を支える。4本とも source evidence と admission receipt は一致している。

判定式 (`t785_legacy_cache_probe.py:174`–`:186`) も裁定仕様と一致する。`.comment` 単独で compiler 全体の由来を保証するものではないが、今回は実コンパイル argv・成功記録・binary SHA256・版の一致を併用しており、極小 ELF に関する結論は妥当である。

**規律2と一般化。** commit 差分は省略条件・docstring・新規テストだけ。admission 検査 (`buildcache.py:3436`)、hit 時の sidecar 検査 (`:3484`)、evidence 再照合 (`:3493`)、trace 検査、および build_v2 に検査の緩和はない。既存テストの期待値変更もない。

brief 初版の「pipeline は site 解決」「between_run_floor は全分岐で site 解決」「s1 は stock control」は現物と一致しないが、追記と段4裁定で訂正済み。修正後の主張を反証する観測は見つからない。ただし、4 JSON から8 caller 全部の実走成功や性能・certified 選択の改善までは言えない。それらへの到達範囲は上記コード経路の静的確認による。

## 総括

実装は今回の既定 toolchain 変更による省略衝突を閉じ、現行 key と既存検査を維持している。親の再現・修正確認は、極小 ELF を用いた production cache 経路の実証として成立する。

SHOULD 1件は片側変更のテスト被覆。M2 は4 node 外の sort identity テストも破るため、変異結果の完全集合は対象4 node に限定して記録すること。

本レビューは読み取りと静的検算のみ。pytest・変異 matrix・受入全走は実行していない。