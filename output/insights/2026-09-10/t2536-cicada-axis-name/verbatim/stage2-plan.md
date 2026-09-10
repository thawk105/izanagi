## 方針

`Genome` の論理軸名は維持し、protocol と論理軸から CCBench の cache 変数名を引く静的表を `model.py` に置く。正方向と逆方向は同じ表を参照し、cicada の旧汎用名は逆変換時に明示的に拒否する。

変更は `model.py`、`calibrator/cli.py`、`screening_driver.py`、既存テストファイルの 4 ファイルに限定する。`genome.py`、CCBench、認定 shell は編集しない。

## 変更ファイルと行

- [orchestrator/campaign/model.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/model.py:16)
  - typing import を調整する。
  - 現在の `Genome` 定義直前、`model.py:38-39` に静的対応表と変換関数を新設する。
  - `Genome.cmake_defines()` の `model.py:61-63` を共有変換関数経由にする。
  - `Genome.canonical()` の `model.py:56-59` は変更しない。

- [orchestrator/calibrator/cli.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/calibrator/cli.py:42)
  - `model.py` の逆変換関数を import する。
  - `_canonical_genome_from_receipt()` の `cli.py:429-445` で、正規表現から得た cache 変数名を共有逆変換へ通してから `flags` に格納する。
  - `missing_axes` と canonical 化の `cli.py:446-464` は現在の意味を維持する。

- [orchestrator/campaign/screening_driver.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:27)
  - 正方向の共有変換関数を import する。
  - `_require_requests_match_genome_build_arguments()` の `screening_driver.py:142-144` と `_condition_gate_base_configure_args()` の `screening_driver.py:159-168` に残る `-DCCBENCH_{macro}` の局所組み立てを共有関数へ置き換える。
  - 現在の condition macro はすべて恒等写像なので、生成される引数は変わらない。

- [orchestrator/tests/test_pegasus_calibration_workload.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_pegasus_calibration_workload.py:15)
  - 対応表、`Genome`、受領証復元関数を import する。
  - `test_pegasus_calibration_workload.py:18-23` 付近に CCBench root の定数を追加する。
  - 既存 shell 表 parser の前、`test_pegasus_calibration_workload.py:85` 付近に CCBench 実体 parser を追加する。
  - `test_pegasus_calibration_workload.py:198` 付近に正例、負例、producer、receiver の検査を追加する。
  - 既存テストの期待値は編集しない。

## 対応表の正本

`model.py` に次を新設する。

```python
GENOME_AXIS_CMAKE_CACHE_VARIABLES: Dict[tuple[str, str], str]

def cmake_cache_variable_for_axis(protocol: str, axis: str) -> str

def genome_axis_from_cmake_cache_variable(
    protocol: str,
    cache_variable: str,
) -> str
```

表は `SPACES` から実行時生成せず、現在登録されている 17 軸を literal で宣言する。

- silo:
  - `BACK_OFF`
  - `NO_WAIT_LOCKING_IN_VALIDATION`
  - `NO_WAIT_OF_TICTOC`
  - `WAL`
  - すべて `CCBENCH_<軸名>`。

- mocc:
  - `BACK_OFF`
  - `KEY_SORT`
  - `TEMPERATURE_RESET_OPT`
  - すべて `CCBENCH_<軸名>`。

- tictoc:
  - `BACK_OFF`
  - `NO_WAIT_LOCKING_IN_VALIDATION`
  - `NO_WAIT_OF_TICTOC`
  - `PREEMPTIVE_ABORTS`
  - `TIMESTAMP_HISTORY`
  - すべて `CCBENCH_<軸名>`。

- cicada:
  - `INLINE_VERSION_OPT` のみ `CCBENCH_INLINE_VERSION_OPT_CICADA`。
  - `BACK_OFF`、`INLINE_VERSION_PROMOTION`、`REUSE_VERSION`、`WRITE_LATEST_ONLY` は `CCBENCH_<軸名>`。

表にない補助 define は従来互換の恒等写像へ落とす。これにより認定 silo の `TRACE` と `BACKOFF_FIXED`、screening 固有 macro を新しい表へ混ぜず、現在の argv を維持できる。oze は表へ入れない。

## 配置理由と import 循環

現在の依存方向は [genome.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/genome.py:17) の

```python
from .model import Genome
```

すなわち `genome.py → model.py` である。一方、[model.py:14-20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/model.py:14) は `genome.py` を import していない。

対応表を `Genome` と同じ `model.py` に置けば、

- `Genome.cmake_defines()` は同一 module 内で正方向関数を使える。
- `genome.py` の既存 import 方向は変わらない。
- `calibrator/cli.py` は現在も [cli.py:42-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/calibrator/cli.py:42) で `genome.py` と `model.py` の双方を import しており、逆変換関数を追加 import しても新しい逆向き依存は生じない。
- `model.py → genome.py` を追加しないため循環しない。

## producer 側

[Genome.cmake_defines():61-63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/model.py:61) を次の意味へ変更する。

```python
return [
    f"-D{cmake_cache_variable_for_axis(self.protocol, axis)}={self.flags[axis]}"
    for axis in sorted(self.flags)
]
```

ソートキーと値は従来どおり論理軸を使う。そのため次が成立する。

- cicada の `INLINE_VERSION_OPT=1` は
  `-DCCBENCH_INLINE_VERSION_OPT_CICADA=1` になる。
- silo、mocc、tictoc は名前、順序、値、区切りを含め 1 byte も変わらない。
- `canonical()` は論理軸名を使い続け、文字列は変わらない。

これは CCBench 実体の [cicada/CMakeLists.txt:4-6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/external/ccbench/cc/cicada/CMakeLists.txt:4) と [Options.cmake:51-54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/external/ccbench/cmake/Options.cmake:51) に一致する。

## receiver 側と旧汎用名の拒否

`genome_axis_from_cmake_cache_variable()` は次の順序で逆変換する。

1. 同じ protocol の静的表で cache 変数名が完全一致する軸を探す。
2. 一致すればその論理軸名を返す。
3. 一致しなければ `CCBENCH_` を除いた名前を恒等写像候補とする。
4. その候補を正方向関数へ戻し、元の cache 変数名と一致しなければ `ValueError` にする。

拒否分岐の中心は次の形になる。

```python
def genome_axis_from_cmake_cache_variable(
    protocol: str,
    cache_variable: str,
) -> str:
    ...
    candidate = cache_variable.removeprefix("CCBENCH_")
    if cmake_cache_variable_for_axis(protocol, candidate) != cache_variable:
        raise ValueError(...)
```

cicada で旧名 `CCBENCH_INLINE_VERSION_OPT` を受けると、候補軸 `INLINE_VERSION_OPT` の正しい正方向名は `CCBENCH_INLINE_VERSION_OPT_CICADA` になる。元の名前と一致しないので拒否され、`cli.py` が `CertificationError("receipt-genome-invalid", ...)` に包む。旧名を新名へ読み替える alias は作らない。

通る正例は次である。

```text
protocol: cicada
-DCCBENCH_INLINE_VERSION_OPT_CICADA=1
    ↓
flags["INLINE_VERSION_OPT"] == 1
```

全軸を含む受領証なら canonical 結果は例えば次になる。

```text
cicada|BACK_OFF=1,INLINE_VERSION_OPT=1,INLINE_VERSION_PROMOTION=1,REUSE_VERSION=1,WRITE_LATEST_ONLY=0
```

`TRACE` と silo の `BACKOFF_FIXED` は表外の恒等写像として従来どおり復元される。

## CCBench 実体との独立照合

テスト側に次の helper を置く。

```python
def _ccbench_axis_cache_table(
    ccbench_root: Path,
) -> dict[tuple[str, str], str]

def _assert_axis_cache_table_matches_ccbench(
    ccbench_root: Path,
    declared: Mapping[tuple[str, str], str],
) -> None
```

`_ccbench_axis_cache_table()` は Izanagi の対応表を入力にせず、以下を直接読む。

- `external/ccbench/cmake/Options.cmake`
  - `set(CCBENCH_... CACHE ...)` の cache 変数集合。
  - `ccbench_universal_definitions()` 内の `AXIS=${CCBENCH_CACHE}`。
- `external/ccbench/cc/<protocol>/CMakeLists.txt`
  - `OPTIONS` 内の `AXIS=${CCBENCH_CACHE}`。

各 `SPACES[protocol].axes` について、protocol 固有 `OPTIONS` または universal definitions のどちらか一方から実体の cache 変数名を得る。参照先が `Options.cmake` の cache 宣言に存在することも確認する。

比較は次の 2 実体の exact equality とする。

- Izanagi 実体: `GENOME_AXIS_CMAKE_CACHE_VARIABLES`。
- CCBench 実体: CMake ファイルを parse して得た表。

`SPACES` は検査対象となる軸集合の確定にだけ使い、CCBench 側の cache 変数名を Izanagi 表から生成しない。これにより D1863 の恒真化を避ける。

[ProtocolHelpers.cmake:29-43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/external/ccbench/cmake/ProtocolHelpers.cmake:29) が universal と protocol OPTIONS の双方を compile definitions へ渡すため、上記 2 系統がコンパイラへ届く実体経路であることも固定できる。

## 検査 nodeid と捕捉対象

| nodeid 候補 | 正負 | 捕捉する崩れ |
|---|---:|---|
| `orchestrator/tests/test_pegasus_calibration_workload.py::test_genome_axis_cache_table_matches_ccbench_sources` | 正例 | 現在の 17 軸と CCBench 実体が一致し、cicada だけが非恒等であること |
| `...::test_genome_axis_cache_table_rejects_ccbench_side_rename` | 負例 | 一時 fixture の `Options.cmake` と cicada `CMakeLists.txt` を整合した別名へ rename しても、Izanagi 宣言が追随していなければ exact 比較が落ちること |
| `...::test_genome_axis_cache_table_rejects_izanagi_side_rename` | 負例 | グローバル定数を変更せず、その copy の cicada 宣言値だけを別名へ変え、実体との比較が落ちること |
| `...::test_cicada_cmake_define_preserves_axis_value[0]` / `[1]` | 正例 | producer が cache 名だけを変換し、0/1 の値を取り違えないこと |
| `...::test_cicada_receipt_accepts_real_cache_name[0]` / `[1]` | 正例 | receiver が実体名を論理軸へ戻し、値を同じ軸へ保持すること |
| `...::test_cicada_receipt_rejects_generic_cache_name` | 負例 | `-DCCBENCH_INLINE_VERSION_OPT=<v>` が alias として受理されないこと |

CCBench 側 rename の負例では `tmp_path` 配下へ必要な CMake 断片を複製し、`_CICADA` を同じ新名へ変更する。repo や submodule は変更しない。宣言側 rename の負例は表の copy を使い、テスト間で正本を変異させない。

値の取り違えは producer と receiver の両方向で 0 と 1 を個別に期待するため、名前だけ合って値が別軸へ付く、固定値になる、または反転する変更を捕捉する。

## screening_driver の扱い

[screening_driver.py:126-168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:126) には、`cmake_defines()` の結果と照合するための局所的な `-DCCBENCH_{macro}` 組み立てが 2 箇所ある。ここも共有正方向関数へ寄せ、別の暗黙写像を残さない。

現在の condition macro 群は [screening_driver.py:51-90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:51) に列挙され、cicada の `INLINE_VERSION_OPT` は含まれない。表外 macro の fallback も恒等写像なので、既存 condition gate の引数は変化しない。

## 呼び出し元と波及

親 brief の静的棚卸しでは `cmake_defines()` の直接呼び出しは次の 4 箇所である。

- `orchestrator/campaign/buildcache.py:1936`
- `orchestrator/campaign/buildcache.py:3189`
- [orchestrator/campaign/screening_driver.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:131)
- [orchestrator/campaign/screening_driver.py:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:166)

波及は次のとおり。

- `buildcache.py` の 2 箇所:
  - cicada Genome の configure 引数だけが `_CICADA` 名へ変わる。
  - silo、mocc、tictoc は表の値が従来文字列そのものなので byte 不変。
- `screening_driver.py`:
  - `evaluate_candidate()` の [screening_driver.py:618-621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/screening_driver.py:618) は通常の `evaluate`、最終的には buildcache 経路へ渡す。
  - 直接照合 2 箇所も共有関数へ統一するが、現在扱う condition macro は恒等写像なので結果不変。
- その他の campaign driver:
  - `cmake_defines()` を直接再実装せず、中央の buildcache 経路を通るため個別編集は不要。
  - silo、mocc、tictoc の driver は configure argv 不変。
  - 親 brief `:22` のとおり cicada の live build driver は現存しない。将来の cicada driver が中央経路を使った時点で正しい名前を得る。
- `calibrator/cli.py`:
  - silo、mocc、tictoc の cache 名は恒等逆写像となり、現在の受領証は不変。
  - cicada の実体名は新たに正しく復元され、旧汎用名だけが拒否される。

## 既存テストへの影響

次の既存 nodeid は期待値を変更しない。

- `test_submitter_exposes_only_the_calibration_whitelist`
- `test_job_rechecks_the_submission_workload_and_records_it`
- `test_certify_shell_protocol_axes_match_independent_genome_spaces`
- `test_certify_shell_protocol_defines_match_exact_values`
- `test_certify_shell_protocol_axis_values_satisfy_genome_spaces`
- `test_certify_non_silo_defines_contain_no_axis_outsider`
- `test_default_silo_build_and_calibrate_argv_are_byte_compatible`
- `test_submitter_rejects_unregistered_protocol_before_side_effects[cicada]`

理由は、これらが検査する認定 shell の受理集合と silo / mocc / tictoc の静的 configure argv を一切編集しないためである。特に [test_pegasus_calibration_workload.py:449-464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/tests/test_pegasus_calibration_workload.py:449) の cicada 拒否はそのまま残し、認定受理集合を広げない。

既存 suite で挙動が変わりうるのは、cicada の `Genome.cmake_defines()` が旧汎用名を返すこと、または cicada 受領証が旧汎用名で復元できることを直接期待している検査だけである。射影された既存テストファイルにはその期待はないため、既存 assertion の書換えではなく新規 nodeid を追加する。

## 変更しないもの

- [orchestrator/campaign/genome.py:178-214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2536-cicada-axis-name/orchestrator/campaign/genome.py:178): 軸名、値域、制約、`SPACES` を変更しない。
- `Genome.canonical()`: 変更しない。
- `external/ccbench/**`: 実体として読むだけで編集しない。
- `tools/pegasus/certify_calibration.sh` と `submit_certify.sh`: cicada を追加せず、silo / mocc / tictoc のみを維持する。
- 既存テストの期待値、台帳、gate、oze 対応、runtime CMake parser は追加しない。

## 却下する設計案

- 対応表を `genome.py` に置く案:
  `Genome.cmake_defines()` のある `model.py` から `genome.py` を import すると、既存の `genome.py → model.py` と循環する。関数内遅延 import も循環を隠すだけなので採らない。

- producer と receiver に別々の辞書を置く案:
  正方向と逆方向が独立に drift し、今回の欠陥を別の場所へ移すだけになる。逆表は静的宣言せず、正方向表から完全一致で逆引きする。

- cicada の genome 軸自体を `INLINE_VERSION_OPT_CICADA` に変える案:
  C++ マクロ名ではなく cache 名が論理軸へ漏れ、`Genome.canonical()` と variant identity を変更するため不変条件に反する。

- 旧汎用名と実体名の両方を receiver で受理する案:
  コンパイラへ届かなかった旧 configure argvを正しい genome として認定できてしまう。D1864 が却下した alias 正規化そのものなので採らない。

- 実行時に CCBench の CMake を parse して変換する案:
  build と受領証復元が submodule の可用性へ依存するうえ、検査対象と期待値が同じ実体から生成されて D1863 の 2 実体照合を失う。CMake parser はテスト内だけに置く。

## 検証方針

この段では read-only のため実装、patch、pytest 実走は行わない。段 5 で上記 4 ファイルを同一変更単位にし、親が追加 nodeid、関連既存 nodeid、所定 checker を実走する。現時点では静的確認のみで、テストを緑とは報告しない。

## 総括

正本は `model.py` の protocol・論理軸から cache 変数名への 1 個の静的表とし、producer、receiver、screening の全変換を共有関数へ集約する。  
CCBench の CMake 実体を独立 parse する正負検査で両側 rename と値取り違えを捕捉し、cicada の旧汎用名は拒否する。  
canonical、既存 3 protocol の argv、認定 protocol 受理集合は変更しない。