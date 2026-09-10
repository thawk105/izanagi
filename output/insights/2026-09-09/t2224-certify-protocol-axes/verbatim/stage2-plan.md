## 総括

推奨設計は、protocol→軸集合を `certify_calibration.sh` 内の独立した `case` 表として持ち、受け手の `SPACES` と別系統に保つ案 (a) である。  
静的候補集合は `{silo, mocc, tictoc, cicada}` だが、実ビルド未実施なので生産可能集合とはまだ断定しない。  
最大の危険は、現行 CCBench pin に `BACKOFF_FIXED` の cache 定義・条件分岐が存在せず、現行 `run_condition_gate` が silo を含め静的に成立しない点である。  
また brief の 10 行表だけでは、Cicada の cache 名正規化と acquisition receipt の strict schema 更新が漏れる。

## 決めた 8 項目

### 1. protocol → 軸集合の置き場所

推奨は **(a) `certify_calibration.sh` 内の静的 `case` 表**。

- (a) shell 内の表

  - 利点: producer と受け手の `SPACES` が独立し、片方の軸欠落をもう片方が検出できる。既定 silo の argv 順序も明示的に維持しやすい。
  - 危険: `GenomeSpace` 更新との二重管理。テストで shell 表の4行と `SPACES` の軸集合を照合する。ただし runtime の導出元は共有しない。

- (b) job 実行時に `SPACES` から導出

  - 利点: 重複が無く、登録 protocol の追加に追随する。
  - 危険: `orchestrator/campaign/genome.py:208-220` から producer が軸を生成し、受け手も `orchestrator/calibrator/cli.py:455-460` で同じ `space_for(protocol).axes` を検査するため、`missing_axes` 検査が構造的に恒真になる。
  - 規律2上の問題と判断する。target/basename、TRACE、重複 define、build 側への define 混入は引き続き守られるが、「producer が protocol 軸を落としていない」という独立な歯が失われる。

- (c) 別の静的成果物

  - 利点: shell/Python 双方から読める。
  - 危険: 新しい正本・schema・同期規則が必要になり、この4 protocol だけの変更に対して重い。生成物なら (b) と同じ恒真化、手書きなら (a) と同じ drift を別ファイルへ移すだけ。

したがって、shell の独立表＋静的な交差テストを採る。

### 2. protocol ごとの正確な CCBENCH define

`TRACE=0` は全 protocol、`BACKOFF_FIXED=-1` は条件関門の前提が解決した場合に限り全 protocolへ渡す。その他は各 `GenomeSpace` の軸だけに限定する。

| protocol | configure に渡す `CCBENCH_*` |
|---|---|
| silo | `TRACE=0`, `BACK_OFF=0`, `BACKOFF_FIXED=-1`, `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `WAL=0` |
| mocc | `TRACE=0`, `BACK_OFF=1`, `BACKOFF_FIXED=-1`, `TEMPERATURE_RESET_OPT=1`, `KEY_SORT=0` |
| tictoc | `TRACE=0`, `BACK_OFF=1`, `BACKOFF_FIXED=-1`, `NO_WAIT_LOCKING_IN_VALIDATION=1`, `NO_WAIT_OF_TICTOC=0`, `PREEMPTIVE_ABORTS=1`, `TIMESTAMP_HISTORY=1` |
| cicada | `TRACE=0`, `BACK_OFF=1`, `BACKOFF_FIXED=-1`, `INLINE_VERSION_OPT_CICADA=0`, `INLINE_VERSION_PROMOTION=1`, `REUSE_VERSION=1`, `WRITE_LATEST_ONLY=0` |

根拠は `genome.py:106-205` と `Options.cmake:13-54`。silo の `BACK_OFF=0` は Options 既定の `1` ではなく、既存 argv の byte 互換を優先する。

軸外 define は混ぜない。したがって mocc/tictoc/cicada に `WAL` や silo の no-wait 軸を渡さない。`BACKOFF_FIXED` だけは探索軸ではなく、D1198 の既存条件関門が要求する補助 define として明示的に例外扱いする。

Cicada は論理軸名と cache 名が異なる。`external/ccbench/cc/cicada/CMakeLists.txt:5` は `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_CICADA}` なので、実 configure では `_CICADA` 名を使う。受け手 `cli.py:429-464` に、protocol が cicada の場合だけ `INLINE_VERSION_OPT_CICADA` を論理名 `INLINE_VERSION_OPT` へ正規化する処理が必要である。両名が同時に現れた場合は既存の重複 define 拒否へ落とす。

### 3. build target と binary path

次で正しい。

- target: `ycsb_<protocol>.exe`
- binary: `$BUILD_DIR/cc/<protocol>/ycsb_<protocol>.exe`

`ProtocolHelpers.cmake:32-35` が target を `${wl}_${name}.exe` として生成する。トップレベル `external/ccbench/CMakeLists.txt:81-83` が `add_subdirectory(cc/${_proto})` を使うため、CMake の binary directory は `cc/<protocol>/` になる。

各4 protocol はそれぞれの `CMakeLists.txt:3` に `WORKLOADS ycsb ...` を持つ。YCSB を持つ全7 protocol と `SPACES` の積集合は静的には `{silo,mocc,tictoc,cicada}`。

### 4. `run_condition_gate` の protocol 非依存性

判定は二段階になる。

- 設計上は、準備済み source に `silo-backoff-fixed.patch` 相当が materialize されていれば共通条件として使える。

  - patch は `BACKOFF_FIXED` を `ccbench_universal_definitions()` に入れ、共有 `include/backoff.hh` の分岐を変える。
  - silo は `transaction.cc:42-52,717-721`、mocc は `transaction.cc:981-990,1085-1089`、tictoc は `transaction.cc:486-495,706-710`、cicada は `include/transaction.hh:161-170` と `transaction.cc:962-966` で共有 Backoff を使用する。
  - したがって共通 cache-to-header の意味検査としては protocol ごとの別 gate を新設しない。

- ただし現物では成立していない。

  - `Options.cmake:13-24,60-68` に `CCBENCH_BACKOFF_FIXED` が無い。
  - `include/backoff.hh:94-107` は無条件に `Backoff_` を読むだけで、`BACKOFF_FIXED` 分岐が無い。
  - 条件関門 registry は `condition_meaning_gate.py:70-78` で owner=`cc/silo/transaction.cc`、target=`ycsb_silo.exe` に固定される。
  - `certify_calibration.sh:526-545` は clean detached worktreeを作るだけで、patchを materialize していない。

従って、現状のまま `BACKOFF_FIXED=-1` を全 protocol に渡す前提は不可。gate の削除・skip・green 扱いは規律2違反なので提案しない。親は実装前に「既存 patch を prepared build source へ適用する既存の正規経路があるか」を確定する必要がある。無ければ、本 wave の禁止条件「CCBench 改変なし」と衝突し、単位Aは停止対象になる。

なお `git apply --check` による静的確認では、現 pin に `patches/silo-backoff-fixed.patch` 自体は適用可能だった。実適用は行っていない。

### 5. `submit_certify.sh` の引数・env・receipt

受理集合は次に固定する。

- `--protocol`: `{silo,mocc,tictoc,cicada}` の whitelist。既定 `silo`。
- `--rratio`: 現行どおり `{20,50,80}`。既定 `50`。
- `--skew`: `0` または `0.<digits>` の canonical decimal、範囲 `[0,1)`。固定 whitelist にはしない。既定 `0.9`。
- `--rmw`: `{0,1}`。既定 `0`。

`--skew` は符号、指数表記、空白、カンマ、`.9`、`1` 以上を拒否する。これで qsub `-v` の区切り文字混入も防ぐ。

既定値省略時の qsub argv を byte 単位で維持するため、`PROTOCOL_EXPLICIT`、`SKEW_EXPLICIT`、`RMW_EXPLICIT` を持つ。

- 3引数を省略した場合、`export_spec` は現行どおり  
  `IZANAGI_SUBMISSION_NONCE=...,IZANAGI_CALIBRATION_RRATIO=50`
- 明示された値だけを、protocol→skew→rmw の固定順で後置する。
- job 側は env が無ければ silo/0.9/0 を採る。

`pre-submit.json`、`submit-receipt.json` は常に実効値を次の同型で記録する。

```json
{
  "calibration": {
    "protocol": "silo",
    "workload": {
      "ycsb_zipf_skew": "0.9",
      "ycsb_rratio": "50",
      "ycsb_rmw": "0"
    }
  }
}
```

job 側 `certify_calibration.sh:188-219` は現行の `calibration_rratio` に加えて4項目すべてを exact string で再照合する。省略時も submit receipt と job default が一致しなければ停止する。

### 6. job-result.json / acquisition receipt

`job-result.json` は `certify_calibration.sh:820-836` を次の形へ拡張する。

```json
"calibration": {
  "protocol": "mocc",
  "workload": {
    "ycsb_zipf_skew": "0.9",
    "ycsb_rratio": "50",
    "ycsb_rmw": "0"
  }
}
```

acquisition receipt も同じ `calibration` object を持たせる。現行の strict writer は `make_acquisition_receipt.py:30-48` で top-level key を閉じ、schema は `schema_v2.py:445-469,560-563,613-629` で完全一致を要求するため、launcher だけの変更では実現できない。

必要な schema 方針は以下。

- 新しく genome を持つ certification record では `acquisition_receipt.calibration` を必須にする。
- brief が示す既存2 recordは genome 自体が無いため、歴史的 no-genome recordだけは従来 acquisition shapeを受理する。
- 新規 genome 付き recordが calibration binding を省略する経路は作らない。
- calibrator は receipt protocol と `_canonical_genome_from_receipt` が導出した protocol、receipt workload と CLI `--workload` の3キー完全一致を bench 前に確認する。

これは検査緩和ではなく、新規 record の束縛追加である。ただし brief の「変更 script 2本＋テスト」では不足しており、schema/writer/consumer/test の追加面が必須になる。

### 7. テスト更新方針と literal pin 一覧

assert は削除しない。固定値をパラメータ化後の等価な検査へ置換し、負例を追加する。

| 現行 pin | 処置 |
|---|---|
| `test_pegasus_calibration_workload.py:33` usage の `--rratio` | protocol/skew/rmw を含む usage へ更新 |
| 同 `:34-40` RRATIO既定、3値 whitelist、env、pre/submit receipt literal | 維持しつつ4軸形へ更新 |
| 同 `:47-51` job の rratio受理・workload argv・job-result・`rratio=50` 非直書き | 4項目の変数・構造へ更新 |
| 同 `:52-58` gate順序、BACKOFF_FIXED、stock/meaning/use-class、CXX_FLAGS不使用 | 全て維持 |
| 同 `:61-70` `bash -n` | 維持 |
| 同 `:142-159` 不正rratioを副作用前に拒否 | 維持し、protocol/skew/rmw負例を追加 |
| 同 `:188-228` 省略時dry-run qsub argv | byte互換の中心テストへ強化 |
| 同 `:231-274` scheduler出力path | 維持 |
| 同 `:276-281` README の rr80/rr20 手順 | 維持し、非silo例を追加 |
| `test_pegasus_tools.py:124-184` shell/PBS/policy literal | 維持 |
| 同 `:200-215` 凍結CLI・reservation・walltime | 維持 |
| 同 `:331-359` calibrate timeout/perf順序 | 維持 |
| 同 `:425-537` gflags/glog・CMake配列数・`configure_argv[@]:5` | 維持。protocol define配列は別配列として検査 |
| 同 `:692-713` module/toolchain/acquisition fragment抽出 | 維持 |
| 同 `:716-831` acquisition candidate fixture | calibration objectを必須化して更新 |
| 同 `:1140-1294` binary symbol検査 | 維持 |
| 同 `:1382-1414` calibrate failure時のargv/job-result | protocol/skew/rmw変数と記録assertを追加 |
| 同 `:1473-1509` request ID binding fixture | 4軸を含むreceipt/envへ等価更新 |
| 同 `:1512-1561` rratio mismatch exact stderr | 4軸を各1件ずつ壊すparameterized負例へ強化 |
| 同 `:1564-1619` default dry-run | qsub default env byte互換と4軸receiptを追加 |

新規追加する検査:

- shell の4 protocol表が期待する論理軸集合と完全一致する。
- mocc/tictoc/cicada に `WAL` が無く、他 protocol の軸も混入しない。
- `TRACE=0` と `BACKOFF_FIXED=-1` が各1回だけ。
- Cicada の raw cache名が `INLINE_VERSION_OPT_CICADA`、canonical genome が `INLINE_VERSION_OPT`。
- target/binary path が4 protocolすべてで一致。
- 引数省略時の configure/build/calibrate/qsub argv が現行期待値と完全一致。
- acquisition/job-result/submit receipt の4項目完全一致。
- protocol/skew/rmw の不正値が staging 作成前に拒否される。

さらに、brief に無いが必要な既存テスト面:

- `test_calibrator_certify.py:431-452` の「非軸 define を保持する」既存検査は反転・削除せず維持する。Cicada alias の正例とalias重複負例を追加する。
- `test_schema_v2.py:34-114,136-178,274-315` に新 acquisition binding と欠落・未知・型不正負例を追加する。
- `test_pegasus_tools.py:1068-1086` の writer round-trip で calibration field drop を新たに拒否する。

### 8. 生産可能 protocol の実測方法

静的候補集合は次の積で4件。

- YCSB targetあり: cicada, ermia, mocc, oze, si, silo, tictoc
- `SPACES` 登録: silo, mocc, tictoc, cicada
- 積集合: `{silo,mocc,tictoc,cicada}`

最終的な生産可能集合は、各 protocol について以下の全段が green のものだけとする。

1. fresh configure
2. 既存 condition gate の3 recordが受理
3. target build成功
4. binary存在・実行可能
5. symbol table非空・`izanagi_trace` 不在
6. acquisition receipt writer成功
7. `_canonical_genome_from_receipt` 受理
8. canonical protocol/軸が期待値と一致

較正計測本体は実行しない。

## 編集手順 (file:line 粒度)

以下はすべて現行行番号。編集後の行番号ではない。

### 単位 A — `certify_calibration.sh` と直接必要な受け手

1. `tools/pegasus/certify_calibration.sh:150-165`

   - 現状: submission nonce と必須 `IZANAGI_CALIBRATION_RRATIO` だけを検査。
   - 変更: protocol/skew/rmw の env default、whitelist/range検査、`CALIBRATION_*` 変数を追加。
   - 理由: job単体でも不正な qsub env を受け入れず、省略時は従来値へ戻す。

2. `tools/pegasus/certify_calibration.sh:188-219`

   - 現状: submit receipt の `ycsb_rratio` だけを再照合。
   - 変更: Python argv に protocol/skew/rmw を渡し、receipt の4項目を独立した check keyで照合。
   - 理由: qsub env差替えやsubmit/job default driftを停止する。

3. `tools/pegasus/certify_calibration.sh:380-395`

   - 現状: `BACKOFF_FIXED=-1` の silo owner/target関門を一律実行。
   - 変更: gate自体、stock comparison、meaning case、実行順は維持。全 protocol 配列に `BACKOFF_FIXED=-1` が1回あることを前提化する。
   - 理由:検査を弱めない。prepared source 問題が解決しない限りこのハンクには進まない。

4. `tools/pegasus/certify_calibration.sh:526-550`

   - 現状: silo define、`ycsb_silo.exe`、`cc/silo/...` を直書き。
   - 変更: protocol `case` で exact define配列を構築し、`TARGET="ycsb_${CALIBRATION_PROTOCOL}.exe"`、`BINARY="$BUILD_DIR/cc/$CALIBRATION_PROTOCOL/$TARGET"` とする。
   - silo 分岐の配列順は現行 `538-540` と同じにし、省略時の configure argvを完全一致させる。
   - 理由:軸外 defineのcanonical混入を防ぎながら4 protocolへ展開する。

5. `orchestrator/calibrator/cli.py:429-464`

   - 現状: `CCBENCH_` suffixをそのままGenome flag名にし、Cicadaの `_CICADA` aliasを扱えない。
   - 変更: protocol=cicada の `INLINE_VERSION_OPT_CICADA` だけを `INLINE_VERSION_OPT` に正規化してから重複・missing axes検査へ渡す。
   - 理由:実CMake cache名と論理Genome軸の両方を正直に記録するため。

6. `tools/pegasus/certify_calibration.sh:598-682`

   - 現状: acquisition candidate に qsub/allocation/toolchain/ccbench等だけを入れる。
   - 変更: Python argvへ4項目を渡し、candidateに厳密な `calibration` objectを追加。
   - 理由: acquisition時点でprotocol/workload/binaryを同一receiptへ束縛する。

7. `tools/pegasus/make_acquisition_receipt.py:30-48`、
   `orchestrator/calibrator/schema_v2.py:445-469,560-563,613-629,770-813`

   - 現状: acquisition top-level key集合が閉じており、calibration bindingを受けられない。
   - 変更:新規genome付きreceiptでは `calibration` を必須化し、protocolとworkloadのexact key/typeを検証。歴史的no-genome recordのみ旧shapeを許す。
   - 理由: launcherだけでfieldを足すとwriter/schemaで必ず拒否されるため。

8. `tools/pegasus/certify_calibration.sh:788-808`

   - 現状: workload は `skew=0.9,rratio=<var>,rmw=0`、binaryはsilo固定由来。
   - 変更: workloadを `"$CALIBRATION_WORKLOAD"` に置換。文字列のkey順は現行順を維持。
   - 理由:省略時calibrate argvのbyte互換と明示軸の伝播を両立する。

9. `tools/pegasus/certify_calibration.sh:820-836`

   - 現状: job-resultはrratioだけ。
   - 変更: protocol＋3 workload軸を記録。
   - 理由:失敗時を含め、どのbuild/workloadがcalibratorへ渡ったかを残す。

### 単位 B — `submit_certify.sh` + テスト

1. `tools/pegasus/submit_certify.sh:5-18`

   - 現状: usage/defaultはrratioのみ。
   - 変更: `--protocol`、`--skew`、`--rmw`、各default、各explicit markerを追加。
   - 理由:省略時envと明示時envを区別する。

2. `tools/pegasus/submit_certify.sh:24-40`

   - 現状: `--rratio` のみparse/whitelist。
   - 変更:3引数をparseし、protocol exact whitelist、skew canonical decimal、rmw 0/1をstaging作成前に検査。
   - 理由:副作用前fail-closedとqsub env安全性。

3. `tools/pegasus/submit_certify.sh:133-171`

   - 現状: pre-submit requestは`calibration_rratio`だけ。
   - 変更:protocolと全workload軸を渡し、構造化calibration bindingを記録。
   - 理由:submit前snapshotで選択値を固定する。

4. `tools/pegasus/submit_certify.sh:178-184`

   - 現状: nonceとrratioのenv 2本。
   - 変更:省略時はこの文字列を一切変えず、明示されたenvだけ固定順でappend。
   - 理由:qsub argvの1-byte互換。

5. `tools/pegasus/submit_certify.sh:218-247`

   - 現状: submit receiptはrratioだけ。
   - 変更:pre-submitの4項目を同型のcalibration objectへ写す。
   - 理由:job側のexact再照合元にする。

6. `orchestrator/tests/test_pegasus_calibration_workload.py:30-70,142-281`、
   `orchestrator/tests/test_pegasus_tools.py:497-537,705-831,1382-1619`

   - 現状:前節のliteral pin一覧どおり。
   - 変更:削除せず、4軸・default argv・負例・receipt整合へ拡張。
   - 理由:検査の意味を維持または強化する。

7. `tools/pegasus/README.md:113-160`

   - 現状:rr20/50/80とsilo相当の固定workloadのみ記載。
   - 変更:4引数の受理集合、省略時既定、非silo例、receipt記録、4 protocol実測表への参照を追加。
   - 理由:実際のsubmit契約と運用文書を一致させる。

briefとの行番号差は #4 のみ明確で、briefの `151-158` に対し現物のrratio検査本体は `154-159`、代入まで含めると `154-161`。その他の数値アンカー `538-540`, `546`, `549`, `796`, `830`, submit `8-40`, `178` は現物と一致した。  
ただし変更面そのものは、上記の `cli.py`、schema/writer、追加テスト、READMEがbriefの10行表から漏れている。

## 実測手順

実装後、親が書込み可能なlogin nodeで行う。新しい `tools/pegasus/` 実行体は作らず、作業用directoryはrepo外の一時領域に置く。

```bash
python3 -m orchestrator.campaign.queue_state
hostname
T2224_PROBE_ROOT=$(mktemp -d /scr/t2224-certify.XXXXXX)
git -C external/ccbench worktree add --detach \
  "$T2224_PROBE_ROOT/ccbench-source" \
  "$(git -C external/ccbench rev-parse HEAD)"
```

最初に `certify_calibration.sh:397-524` と同じ gflags/glog configure→build→install を一度だけ行い、4 build directoryで共有する。source HEADは `policy.json:15-18` と照合する。

各 protocol に対し、単位Aの表から `DEFINE_ARGS` を作る。条件関門は `BACKOFF_FIXED` 自身を `--configure-arg` に重複投入せず、他の実 configure引数を渡す。

```bash
python3 -m orchestrator.campaign.condition_meaning_gate \
  --source-root "$T2224_PROBE_ROOT/ccbench-source" \
  --stock-root "$PWD/external/ccbench" \
  --driver-id tools.pegasus.certify_calibration \
  --macro BACKOFF_FIXED \
  --requested-value=-1 \
  --stock-comparison \
  --meaning-case=-1:branch:stock-adaptive-backoff \
  --cxx "$(realpath "$(command -v g++)")" \
  --cmake "$(realpath "$(command -v cmake)")" \
  --use-class certified-selection \
  --configure-arg=-DCMAKE_BUILD_TYPE=Release \
  --configure-arg=-DENABLE_SANITIZER=OFF \
  --configure-arg=-DCCBENCH_TRACE=0
```

ここへ各 protocol の `BACKOFF_FIXED` 以外の define、prefix/compiler引数を追加する。期待観測は `condition_meaning_gate.py:4175-4178` の3 JSONL recordがすべてgreen/admitted、rc=0。現在のunprepared CCBench sourceではここがredになる見込みであり、その場合はbuildへ進めない。

次に fresh configure/build。

```bash
cmake -S "$T2224_PROBE_ROOT/ccbench-source" \
  -B "$T2224_PROBE_ROOT/build-<protocol>" \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_SANITIZER=OFF \
  <protocolごとのDEFINE_ARGS> \
  "-DCMAKE_PREFIX_PATH=<gflags-install>;<glog-install>" \
  "-DCMAKE_C_COMPILER=$(realpath "$(command -v gcc)")" \
  "-DCMAKE_CXX_COMPILER=$(realpath "$(command -v g++)")"

cmake --build "$T2224_PROBE_ROOT/build-<protocol>" \
  --target "ycsb_<protocol>.exe" -j 48
```

期待するbinary:

```text
$T2224_PROBE_ROOT/build-silo/cc/silo/ycsb_silo.exe
$T2224_PROBE_ROOT/build-mocc/cc/mocc/ycsb_mocc.exe
$T2224_PROBE_ROOT/build-tictoc/cc/tictoc/ycsb_tictoc.exe
$T2224_PROBE_ROOT/build-cicada/cc/cicada/ycsb_cicada.exe
```

symbol検査:

```bash
/usr/bin/nm -C "$BINARY" >"$T2224_PROBE_ROOT/<protocol>.symbols"
test -s "$T2224_PROBE_ROOT/<protocol>.symbols"
! grep -qi izanagi_trace "$T2224_PROBE_ROOT/<protocol>.symbols"
sha256sum "$BINARY"
```

その後、`certify_calibration.sh:598-679` と同じfieldからprotocol別の `acquisition-candidate.json` を一時領域へ組み立て、既存writerを通す。

```bash
python3 tools/pegasus/make_acquisition_receipt.py \
  --input "$T2224_PROBE_ROOT/<protocol>-acquisition-candidate.json" \
  --output "$T2224_PROBE_ROOT/<protocol>-acquisition-receipt.json"
```

最後に既存受け手を直接呼び、rc=0とcanonical文字列を確認する。

```bash
python3 -c '
import json
import sys
from orchestrator.calibrator.cli import _canonical_genome_from_receipt
receipt = json.load(open(sys.argv[1], encoding="utf-8"))
print(_canonical_genome_from_receipt(receipt, sys.argv[2]))
' "$T2224_PROBE_ROOT/<protocol>-acquisition-receipt.json" "$BINARY"
```

期待値:

```text
silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
mocc|BACKOFF_FIXED=-1,BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1
tictoc|BACKOFF_FIXED=-1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1
cicada|BACKOFF_FIXED=-1,BACK_OFF=1,INLINE_VERSION_OPT=0,INLINE_VERSION_PROMOTION=1,REUSE_VERSION=1,WRITE_LATEST_ONLY=0
```

所要時間見積り:

- gflags/glog準備: 3〜8分
- 初回FetchContent/configure: 5〜15分
- condition gate＋target build: 1 protocolあたり4〜10分
- symbol/receipt/canonical検査: 1 protocolあたり1分未満
- 合計: warm cacheで約25〜45分、cold fetch/buildで最大60〜90分程度
- 2時間の較正本体は実行しない

## 残る不確実性

- 段2のため実CMake build、条件関門、binary検査は未実施。生産可能集合はまだ確定していない。
- 現行 CCBench pinには `BACKOFF_FIXED` 実装が無く、現行 launcherのcondition gateは静的に自己矛盾している。prepared sourceの正規経路が別に存在するかは指定資料から確認できなかった。
- 既存patchを一時build sourceへ適用することを「CCBench改変禁止」の範囲外とみなしてよいかは判断権限が無い。ここが否なら本waveは実装前に停止する。
- acquisition receipt拡張はstrict schemaへ波及するため、briefの「script 2本＋テスト」だけでは完結しない。
- FetchContentのcold network可否と実所要時間は実測していない。
- 誤って `tools/run_tests.py --help` を呼んだが、tmp不在によりpytest collection前に失敗した。テスト・buildは一件も実行されていない。ファイル編集、commit、pushは行っていない。