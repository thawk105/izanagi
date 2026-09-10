## 総括

静的レビューでは、現行実装の protocol whitelist・submit binding・silo argv 互換・trace 分離に直接の正しさ回帰は見つからなかった。  
最も重い所見は、**非 silo の define 値を壊しても新設テストが全緑になり、`SPACES` の制約外 genome を認定できること**である。  
また、既知の build-sink 赤を literal 3 分岐で直すだけでは、条件付き gate を全 sink の支配 gate と誤認して偽緑になる。  
DW-M01 は M1 と M8 が現状の事前登録理由では成立しない。テストは実行していない。

## 所見

### 1. must-fix — protocol 軸の「名前」しか検査せず、値と制約を守っていない

成果物影響: `SPACES` に存在しない tictoc genome を calibration record として認定し得る。

根拠:

- `orchestrator/tests/test_pegasus_calibration_workload.py:192-215` は `TRACE=0` と define 名集合しか比較しない。
- `tools/pegasus/certify_calibration.sh:565-573` が非 silo の値を所有する。
- `orchestrator/campaign/genome.py:74-88,147-156` は tictoc の no-wait 両方 1 を空間から除外する。
- `orchestrator/calibrator/cli.py:455-464` は軸欠落だけを検査し、値域・`constraints` を検証せず `Genome.canonical()` へ進む。

反例:

`tools/pegasus/certify_calibration.sh:570` を
`-DCCBENCH_NO_WAIT_OF_TICTOC=1`
へ変える。`NO_WAIT_LOCKING_IN_VALIDATION=1` と合わせて制約外の `(1,1)` になるが、define 名集合・TRACE・target・BACKOFF_FIXED・silo byte 互換の全新設テストは緑のままである。calibrator も全軸が存在するため拒否しない。

protocol ごとの exact 値表を `Options.cmake` の既定値または独立した期待表と比較する必要がある。

### 2. must-fix — build-sink の literal 3 分岐修正は条件付き gate を偽の支配関係として数える

成果物影響: 非 silo build が実際には condition gate を通らなくても、全 build sink が gated という偽の緑を出す。

根拠:

- `orchestrator/tests/test_ccbench_spawn_sites.py:809-832` は literal target が同一行にある sink を検出する。
- 同 `:2139-2185` は module scope の gate 呼出しが sink より前にあるだけで gated とし、`if` の条件を見ない。
- `tools/pegasus/certify_calibration.sh:586-590` では gate 呼出しは silo 条件内で、build はその後にある。
- `orchestrator/tests/test_ccbench_spawn_sites.py:2626-2639` がこの分類を合格根拠にする。

反例:

親方針どおり mocc/tictoc/silo の literal build 行を `run_condition_gate` の条件分岐より後に置く。実行時 `CALIBRATION_PROTOCOL=mocc` は `run_condition_gate` を呼ばないが、解析は「前に gate 行がある」として mocc sink にも全 macro coverage を付ける。

また literal `ycsb_silo.exe` を置く修正は、現状の `orchestrator/tests/test_pegasus_calibration_workload.py:228-230` と衝突するため、単に build 行だけを直しても全走は緑にならない。

### 3. must-fix — 非 silo の最終 `calibrate_argv` 伝播がテストされていない

成果物影響: mocc/tictoc を正しく build しても、calibrator に別 binary を渡して認定不能または誤対象化できる。

根拠:

- `orchestrator/tests/test_pegasus_calibration_workload.py:113-166,218-230` は初回の `BINARY` 導出までしか観測しない。
- 同 `:169-189,245-272` の calibrate argv 検査は silo 固定である。
- 実際の consumer は `tools/pegasus/certify_calibration.sh:834-843`。
- `orchestrator/tests/test_pegasus_tools.py:1382-1418` も `CALIBRATION_PROTOCOL=silo` のみ。

反例:

acquisition candidate 作成後、`calibrate_argv` 構築前に mocc のときだけ `BINARY` を silo path へ再代入する。build/初期 BINARY/全 silo テストは緑のままだが、明示 mocc は誤った binary を calibrator に渡す。

最終 `calibrate_argv` の `--binary` を 3 protocol すべてで観測し、build 時に観測した `BINARY` と一致させる必要がある。

### 4. must-fix — M1 の負例は mutation 自身による dirty-tree 拒否にマスクされる

成果物影響: whitelist を緩めても、qsub/staging 防止を検証せず診断文字列の差だけで KILLED と誤記録できる。

根拠:

- `orchestrator/tests/test_pegasus_calibration_workload.py:376-391` は変更中の実 repository を直接実行する。
- `tools/pegasus/submit_certify.sh:88-100` は staging 前に dirty tree を拒否する。
- protocol gate は同 `:44-49`。

再現手順:

whitelist に `ermia` を加える mutation を適用すると、その mutation 自身で repository が dirty になる。`ermia` は protocol gate を抜けても dirty check で rc=2、staging なしとなる。テストが赤になるのは期待する protocol 診断が出ないためだけで、DW-M03 の semantic kill ではない。

clean fixture に mutated script を commit したうえで、`ermia` が staging/qsub へ到達することを負例として観測する必要がある。

### 5. must-fix — M8 は位置が曖昧で、登録した「byte 互換」理由では赤にならない

成果物影響: mutation matrix が qsub byte 互換を検証したと誤記録する。

根拠:

- submit 側既定は `tools/pegasus/submit_certify.sh:19`。
- job 側既定は `tools/pegasus/certify_calibration.sh:162`。したがって「既定 protocol」は一意な位置でない。
- submit の既定を mocc にしても `PROTOCOL_EXPLICIT=0` は維持され、`tools/pegasus/submit_certify.sh:189-192` の qsub export は変化しない。
- `orchestrator/tests/test_pegasus_calibration_workload.py:493-518` は receipt の `"silo"` で先に赤になり、qsub argv の exact assertionまで到達しない。
- job は `tools/pegasus/certify_calibration.sh:224` で mocc receipt と silo fallback の不一致を拒否する。

反例:

`PROTOCOL=silo` だけを `PROTOCOL=mocc` へ変える。qsub argv は byte 同一だが、pre-submit/receipt の既定値 assertion と後段 submit binding が赤になる。

qsub byte 互換を狙うなら、mutation を `PROTOCOL_EXPLICIT=0` → `1` に再照準すべきである。

## 検査した 6 項目への回答

### 1. 既存の受理・拒否集合

既存検査の削除・緩和はない。

- nonce と rratio の拒否は `tools/pegasus/certify_calibration.sh:150-161` にそのまま残る。
- legacy env は job 側 `:170-173`、submit 側 `tools/pegasus/submit_certify.sh:22-25` で引き続き拒否する。
- submit binding の旧 `checks` は `tools/pegasus/certify_calibration.sh:208-223` に全件残り、`:224` の protocol 一致が追加された。
- 変更前に通った protocol 無指定入力は silo として通る。ただし旧形式の protocol 欠落 receipt は、新 job では protocol 一致で拒否される。
- submitter の新規受理は明示 `silo/mocc/tictoc`。それ以外は `tools/pegasus/submit_certify.sh:44-49` で拒否される。
- submitter の protocol 検査は scheduler output 作成 `:98-100`、submission staging `:109-117` より前にある。
- job 側の protocol/receipt 検査は qstat・build・calibration より前だが、既存設計どおり `/scr` と job-staging 自体は先に作る。

予期しない受理集合の拡大は見つからなかった。

### 2. 新設テストの実効性

`test_certify_shell_protocol_axes_match_independent_genome_spaces` は恒真ではない。`orchestrator/tests/test_pegasus_calibration_workload.py:85-110` が shell の `case` を直接 parseし、`:192-199` が別 module の `SPACES` と比較している。mocc の `KEY_SORT` を落とせば赤になる。

個別評価:

- shell axes test: 軸名には load-bearing。値・制約には無効。
- non-silo outsider test: define 名と configure 展開には load-bearing。値には無効。
- target/binary test: build 時の導出には load-bearing。最終 calibrate 伝播は未検査。
- BACKOFF_FIXED test: silo 所有と gate 呼出回数には load-bearing。
- default silo byte test: hardcoded の旧 argv と比較しており load-bearing。
- unregistered protocol test: baseline では正しいが、mutation 下では dirty-tree にマスクされる。
- explicit protocol dry-run test: clean fixture で export/receipt を検査しており load-bearing。
- omitted protocol test: receipt の silo と qsub argv を独立に固定しており load-bearing。
- submit-binding mismatch test: mismatch と match の両方を通し、load-bearing。
- job-result assertion: protocol 記録には load-bearingだが silo のみ。
- README assertion: 文書 pin であり、実装の正しさ根拠にはならない。

完全な恒真テストはないが、所見 1・3 の実装破壊は全新設テストを緑のまま通せる。

### 3. silo byte 互換

引数省略時の実 argv は変更前と同一である。

- `configure_argv`: `tools/pegasus/certify_calibration.sh:576-581` は旧並びを同じ順序で展開する。
- `build_argv`: 現行の変数展開後は旧 `ycsb_silo.exe` と同一。親の literal 3 分岐修正でも silo branch が同じ token 列なら同一。
- `BINARY` と `calibrate_argv`: silo では旧 path と同じで、`tools/pegasus/certify_calibration.sh:834-844` の token 列も同一。
- qsub argv: protocol 省略時は `PROTOCOL_EXPLICIT=0` なので `tools/pegasus/submit_certify.sh:189-195` の export と argv は変更前と同一。
- `run_condition_gate` の slice は `tools/pegasus/certify_calibration.sh:398` の `:5` のまま。configure の先頭 5 tokenも変化していないため起点はずれていない。

変わるのは裁定どおり pre-submit/submit/job-result JSON bytes であり、argv の byte 互換主張とは区別されている。

### 4. 観測者効果の分離

成立している。

- `-DCCBENCH_TRACE=0` は silo/mocc/tictoc 全 branch にある: `tools/pegasus/certify_calibration.sh:548-573`。
- protocol 別に導出された `BINARY` に対し、共通の `nm -C`、非空 symbol table、`izanagi_trace` 不在検査が `:593-605` で実行される。
- trace 検査は protocol 条件分岐の外なので全 protocol に効く。

### 5. `BACKOFF_FIXED` の silo 限定分岐

実行時の正しさは緩めていない。

- `run_condition_gate` が検査するのは `BACKOFF_FIXED=-1` だけである: `tools/pegasus/certify_calibration.sh:389-404`。
- mocc/tictoc はその define 自体を持たない: `:557-574`。
- したがって非 silo で gate を呼ばないのは「供給した条件を未検査で build」ではなく、「対象条件を供給していない」ためである。
- trace symbol、binary existence/hash、acquisition receipt、calibrator の検査は分岐外に残る。

ただし所見 2 のとおり、既存 build-sink 静的検査はこの非対称を正しくモデル化できない。

### 6. DW-M01

M2〜M7 は、現行コード上では各々「軸集合不一致」「binary path」「target」「非 silo outsider」「receipt protocol binding」という単一の契約違反へ帰属できる。複数 node が落ち得る M2/M3/M6/M7 は、同じ契約違反の重複観測なので、初回 probe で完全集合を取得する必要がある。

M1 は dirty-tree mask、M8 は位置と期待理由の不一致により、現登録のままでは単一理由性が成立しない。

## 変異事前登録への所見

- M1「submit whitelist に ermia 追加」: 不成立。mutation 自身による dirty-tree 拒否で公開負例が protocol gate を越えない。  
  再照準先: mutated script を commit した clean fixture の submit 公開経路。staging/qsub 未到達を判定する。

- M8「既定 protocol を mocc」: 不成立。「既定」は submit/job の2箇所で曖昧で、submit 側だけ変えても qsub argv は同一のまま。赤理由は receipt/fallback 不一致であり、登録した byte 互換ではない。  
  再照準先: `tools/pegasus/submit_certify.sh:20` の `PROTOCOL_EXPLICIT=0` → `1`。省略時 qsub export に protocol が増えることを exact argv test が単一理由で検出する。

- M2〜M7: 静的には登録継続可能。ただし期待 node は裁定どおり初回 probe の完全集合で再登録する。特に M6 は所見 2 の build-sink cross-product test を KILL 根拠に数えず、protocol table/非 silo outsider/BACKOFF_FIXED 専用 testだけへ帰属させる。