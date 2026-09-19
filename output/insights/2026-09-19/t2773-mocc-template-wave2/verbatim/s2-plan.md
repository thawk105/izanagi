## 結論と読解範囲

実装可能。P1〜P10 は大筋で採用する。ただし、**一意 witness、proof 用 PIN の分離、計装の行番号、JSON 生成前の consumer 対照、fixture 閉包**を以下の形で具体化する必要がある。

指定ファイルは可読。静的読解とメモリ上の行数・context 照合だけを行った。ファイル変更、pytest、build、前処理、compute は実施していない。以下の「成立」は静的判断であり、実行結果ではない。

参照の略記：

- `V/` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2773-mocc-template-wave2/wave-artifacts/verbatim/`
- `C/` = `orchestrator/campaign/`
- `T/` = `orchestrator/tests/`
- CCBench の行番号は、特記しない限り `e9e477ca` のもの。
- 新ファイルの配置行は提案。既存ファイルの行番号は今回の現物。

## 1. template patch の逐語案

`patches/mocc-temperature-predicate-variant.patch` を新設する。touch set は厳密に次の二つだけとする。

```python
{"cmake/Options.cmake", "cc/mocc/transaction.cc"}
```

これは既存 `source_digest.ALLOWLIST` 内である（`C/source_digest.py:97`）。`cc/mocc/CMakeLists.txt`、header は変更しない。

**helper：transaction.cc の原文 11 行目直後、原文の空行 12 の前に、以下の 19 行を挿入する。先頭空行も数える。**

```cpp

#ifndef MOCC_TEMP_PREDICATE
#error "MOCC_TEMP_PREDICATE must be defined (0=stock; CMake supplies the default)"
#endif

#if MOCC_TEMP_PREDICATE // file-scope helper
namespace {
inline bool mocc_is_hot(std::uint64_t temp, std::uint64_t threshold) {
  // EVOLVE-BLOCK-BEGIN mocc-temperature-predicate
  // Pure comparison of temp, threshold and constants only; no calls or state.
#if MOCC_TEMP_PREDICATE
  return temp >= threshold;
#else
  return temp >= threshold;
#endif
  // EVOLVE-BLOCK-END mocc-temperature-predicate
}
} // namespace
#endif
```

配置の理由：

- `<cstdint>` は既存の `include/tuple.hh:5` が供給する。新しい include は不要。
- `Epotemp::temp` は `uint64_t temp : 32`（tuple.hh:38）、閾値は `DEFINE_uint64` / `DECLARE_uint64`（common.hh:40、67）。値渡しの `std::uint64_t` 二引数で比較値を保存する。
- helper は原文の `#if TRACE` include block（transaction.cc:13）より前。計装の `<set>` と復元指令は、その後に置かれる。
- anonymous namespace + `inline` を採る。`static` を重ねる必要はない。
- helper 名は `mocc_is_hot` を推奨する。P3 の `izanagi_mocc_is_hot` でも意味は同じだが、既存 `_trace0_record` は `nm` の **任意の `izanagi` 部分文字列**を数える（`C/s3_mocc_lock_coverage.py:466`）。CC-native helper と trace 計装を名前で混同しない。
- OFF では namespace・署名・本体がすべて消える。ON では四つの callsite が参照するので、未使用 helper・未使用引数を作らない。`-Wall -Wextra -Werror` の実 build は段5後に確認する。

**hole は `return <式>;` の一行とする。** 変数宣言・代入先を増やさない。seed は `temp >= threshold`、B は `!(temp < threshold)` とする。

```python
FROZEN_TEMPLATE_HOLE_BYTES = b"  return temp >= threshold;"
```

BEGIN→コメント→`#if`→hole→`#else`→stock→`#endif`→END は `parse_template_file` の受理形に一致する（`C/diff_quarantine.py:567`）。外側 guard は marker 外なので問題ない。ただし DQ は C++ の純粋性を証明しない。生指令、コメント delimiter、行末 backslash を拒否する byte gate と、読取契約の監査を区別する（同:490、D2134 項1・2）。

**callsite 296：原文一行を次の五行で置換。**

```cpp
#if MOCC_TEMP_PREDICATE
  } else if (mocc_is_hot(loadepot.temp, FLAGS_temp_threshold)) {
#else
  } else if (loadepot.temp >= FLAGS_temp_threshold) {
#endif
```

両枝に先行 block を閉じる `}` と新しい block を開く `{` を置く。前処理後はどちらも原文と同じ brace 構造になる。hot block 本体は共用する。

**callsite 459、566：それぞれ原文一行を次の五行で置換。**

```cpp
#if MOCC_TEMP_PREDICATE
  if (mocc_is_hot(loadepot.temp, FLAGS_temp_threshold)) lock(tuple, true);
#else
  if (loadepot.temp >= FLAGS_temp_threshold) lock(tuple, true);
#endif
```

**callsite 970：**

```cpp
#if MOCC_TEMP_PREDICATE
    if (mocc_is_hot(loadepot.temp, FLAGS_temp_threshold) || (*itr).failed_verification_) {
#else
    if (loadepot.temp >= FLAGS_temp_threshold || (*itr).failed_verification_) {
#endif
```

`failed_verification_` fallback は両枝に逐語保存する。コメント647は変更しない。write-set 登録477、RLL 構築905〜913、validation989以降も変更しない（D2134 項1・2・7）。

**Options.cmake：原文23行目直後に挿入。**

```cmake
set(CCBENCH_MOCC_TEMP_PREDICATE 0 CACHE STRING "mocc temperature predicate template (0=stock, 1=enabled)")
```

**原文67行目 `TRACE=${CCBENCH_TRACE}` の直後に挿入。**

```cmake
    MOCC_TEMP_PREDICATE=${CCBENCH_MOCC_TEMP_PREDICATE}
```

universal の供給方式は設計正本 `V/t2757-design-README.md:139` と一致する。template に大文字 `IZANAGI_` token は入れない。

## 2. 計装 template 版と論理行の検算

新ファイル名は親案どおり：

```text
patches/instr-mocc-lock-coverage-temperature.patch
```

preimage は `e9e477ca + template`。旧計装の検査本文は保存し、context と復元行を再生成する。

**訂正：旧計装は六つの unified-diff hunk に七つの `#line` がある。** hunk header は `V/instr-mocc-lock-coverage.patch:4,16,48,75,88,102`。

helper は19行、各 callsite は純増4行。原文970より後は合計35行増える。

| 復元対象 | template 適用前 | template 適用後の物理＝論理行 | 計装後の次行の物理行 | 新 `#line` |
|---|---:|---:|---:|---:|
| TRACE include block 後 | 17 | 36 | 38 | 36 |
| sort 本体 | 990 | 1025 | 1033 | 1025 |
| sort 後の for | 991 | 1026 | 1052 | 1026 |
| writePhase 入口計装後 | 1158 | 1193 | 1238 | 1193 |
| UPDATE payload 前 | 1169 | 1204 | 1254 | 1204 |
| DELETE payload 前 | 1187 | 1222 | 1279 | 1222 |
| publish 前 | 1195 | 1230 | 1295 | 1230 |

右から二列目は旧計装と同じ追加行数を保つ場合。新 `#line` 自体の物理行は、その値から1を引いたもの。

callsite の置換 block 開始は次の位置になる。

| 原文 site | template 後の `#if` |
|---:|---:|
| 296 | 315 |
| 459 | 482 |
| 566 | 593 |
| 970 | 1001 |

TRACE=0 では各計装本文が消え、復元指令が次の原文行を template 側の行番号に戻す。**MOCC_TEMP_PREDICATE=0 と1の双方で同じ復元値を使える。** 非選択枝も物理行として数えられるためである。B への置換も一行なので番号は変わらない。

実測は、新 driver の前処理 helper に `-DMOCC_TEMP_PREDICATE={0,1}` を渡し、各状態で以下を要求する。

```python
wave1._logical_rows_record(base_rows, instrumented_rows)
```

`wave1._preprocess_trace_zero` は新 define を渡せないのでそのまま呼べない（`C/s3_mocc_mutation_proof.py:293`）。新 driver に薄い対応版を置き、行列の解析・記録は同:276、308を再利用する。

旧 patch の第一 hunk は `tuple.hh`→空行→`#if TRACE` を連続 context に持つ。本案はその間に helper を置くため、この context は存在しなくなる。メモリ上の文字列照合では不一致を確認した。**`git apply --check` の実行結果は未確認**なので段5後の生死確認で rc≠0 を保存する。単に行番号がずれたことを hunk 不適用の根拠にはしない。

## 3. 同一性三比較の実装

**実 `source_digest` API を使える。fallback は不要と判断する。**

- `compute(..., ccbench_dir=..., cxx=...)`：`C/source_digest.py:2148`
- `baseline(genome, ccbench_commit, ccbench_dir, cxx)`：同:2243
- `resolve`：同:2467
- owner protocol は source ごとに解決される：同:90、2102、2116
- `Genome` が明示的に禁止する flag は `TRACE`。`MOCC_TEMP_PREDICATE` は格納可能：`C/model.py:134`
- 未登録軸名の CMake 名は `CCBENCH_<axis>` へ写る：同:84。

全呼出しに隔離 checkout と full OID を明示する。

```python
PROOF_PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
stock_g = legacy.STOCK_G
on_g = Genome("mocc", {**stock_g.flags, "MOCC_TEMP_PREDICATE": 1})
```

**比較(i)：無 template ↔ template OFF、計装なし。**

```python
base = source_digest.baseline(stock_g, PROOF_PIN, str(source), cxx)
off = source_digest.compute(stock_g, str(source), cxx)
token = source_digest.resolve(stock_g, PROOF_PIN, str(source), cxx)
assert off == base
assert token == source_digest.STOCK
```

OFF は追加 flag を持たない stock genome を主証拠にする。これなら canonical genome 自体も変わらない。明示的な flag=0 も補助対照にできる。

`_cpp_normalize` は command-line macro の環境 prefix を除くので、新しい0定義だけで identity が変わることはない（`C/source_digest.py:1665`）。helper と追加分岐が消え、原文が選択されることが本案の根拠。

**比較(ii)：OFF ↔ ON-B、計装なし。**

template の hole 一行を B に編集してから測る。

```cpp
  return !(temp < threshold);
```

`on_digest != off_digest` かつ `resolve(on_g, PROOF_PIN, ...) != "stock"` を要求する。Genome の canonical 文字列が違うだけでは合格にしない。ON では helper・呼出しが前処理本文に残る。

**比較(iii)：各 template 状態で計装なし ↔ あり。**

`trace0.off` と `trace0.on_b` に別々の `_logical_rows_record` を保存する。正本は双方の非空行列一致。binary比較はON-B二本で補助記録する（D1687）。

推奨 field：

```text
identity.stock
identity.template_off
identity.template_on_b
identity.benign_diff_sha256
trace0.off
trace0.on_b
trace0.binary
```

各 identity record に genome、define値、compute値、baseline値、src_token、比較対象を保存する。

check の入力述語：

- `template_off_stock_identity`：非空の64桁 digest、stock/off/baseline一致、OFF token=`stock`。
- `template_on_benign_identity_distinct`：B diff の束縛、ON digest≠OFF、ON token≠stock。
- `trace0_logical_rows_identical`：**OFF・ON-B両方**で positive row count、count一致、sha一致、実比較bool=True。

`source_digest` が実環境で失敗した場合、直接前処理比較を `src_token="stock"` と偽称しない。失敗理由を保存して赤にする。D297 の旧pin↔候補比較は本waveに含めない。

## 4. 新 driver、matrix、JSON、時間予算

`C/s3_mocc_template_proof.py` を新設する。構成案：

| 新ファイル内の順序 | 内容 | 再利用元 |
|---|---|---|
| 冒頭 | CLI bootstrap、軸定数、schema、12走matrix、check名 | wave1:18、73 |
| patch処理 | `_apply_template_patch`、計装適用 | legacy:430 |
| build処理 | 新 `_require_condition_gate`、新 `_build_variant` | wave1:126、166 |
| identity | resolver三状態、TRACE=0二状態 | source_digest、wave1:276、308 |
| controls | DQ、digest/deny-only、consumer束縛 | 既存APIを呼ぶ |
| checks | 入力由来 `compute_checks` | wave1:418 の形式 |
| main | policy、隔離checkout、build、12走、逐次保存 | wave1:501 |

再利用できるもの：

```python
from . import s3_mocc_mutation_proof as wave1
from . import s3_mocc_lock_coverage as legacy
```

`wave1._variant_run`、`_silent`、`_logical_rows_record`、`_save_json`、policy/dependency helper を利用する。`_variant_run` は渡された cell・runs・save を処理し、36走matrixを内部参照しない（同:320）。

一方、`wave1._matrix_complete` と `compute_checks` は36走専用なので流用しない。新matrix用の完走検査を置く。

template 適用は新 driver で次を実装する。

```python
touched = patch_files(str(patch), str(source))
if len(touched) != 2 or set(touched) != {
    "cmake/Options.cmake", SOURCE_REL,
}:
    raise RuntimeError("template touch set differs")
apply_patch(str(patch), str(source))
```

計装版には旧 `_apply_owned_patch` を使い、transaction 単独 touch を維持する。

**matrix は12走。**

| workload | hot=0 | cold=21 | default=10 |
|---|---|---|---|
| W：rmw=true、max_ope=5 | t1、t4 | t1、t4 | t1、t4 |
| U：rmw=false、max_ope=1 | t1、t4 | t1、t4 | t1、t4 |

すべて ON-B、TRACE=1、計装template版あり。同じbinaryを共有する。12走とも certified、cycles=0、X=P=0、他integrity clean、txn/write正数を要求する。U は R=0、非INSERT write=txnも要求する（wave1:343〜361）。

**build は五本を採る。**

1. ON-B、TRACE=1、計装あり。
2. ON-B、TRACE=0、計装なし。
3. ON-B、TRACE=0、計装あり。
4. OFF、TRACE=0、計装なし。
5. 無template、TRACE=0。

OFF計装ありは行列比較だけで足りる。無template binaryを省略すれば四本だが、生死確認の再現性を考え五本を推奨する。

condition gate は新 driver IDで次を呼ぶ。

```python
make_define_request(
    driver_id="orchestrator.campaign.s3_mocc_template_proof",
    macro="MOCC_TEMP_PREDICATE",
    requested_value=1,
    default_value=0,
)
```

generic API は `request.owner_tu` / `request.target` を利用する（`condition_meaning_gate.py:862、1696、1810`）。`SOURCE_REL="include/backoff.hh"`、`PROTOCOL="silo"` は旧 BACKOFF_FIXED API側であり、本経路のmocc owner評価を妨げない。CXX_FLAGS代案への変更は不要。

ONの各buildでは、新gateの supply / meaning / admission をbuild前に確認する。OFFのinert供給をgateで測る場合は distinct stock_root が必要（同:1880）。その場合も1/0のbranch witnessとOFF identityを混同しない。

**JSON top-level：**

```text
schema_version, env_tag, site, ccbench_commit, toolchain,
genome, clocks_per_us, workloads, regimes,
template, patches, wave1_proof, legacy_proof,
identity, trace0, quarantine_controls, auditor_definition,
consumer_binding_controls, condition_gates,
diagnostic_build_admission, runs, checks, all_pass
```

- schema：`s3-mocc-template-proof/v1`
- `template`：path、sha256、source_rel、marker_id、flag、touch_set。
- `patches`：新計装版と旧計装patchのpath/sha。
- `wave1_proof`：旧JSONのpath/sha/all_passと32checkの参照。
- `legacy_proof`：T-2294 JSONのpath/sha/14checkの参照。
- `auditor_definition`：実auditor.mdのpath/sha、型8/9/13/16・checklist11〜13の確認位置。
- `runs`：wave1の実argv、終了状態、timeout、verifier raw record、summary、X/P reason、write/read数を保持。
- `n1_*` は置かない。

`V/s3_mocc_mutation_proof.summary.json` は要約であり、`runs_summary` の verdict=Noneを失敗と解釈しない。実consumerはrepoの完全な旧JSONを読む。

**時間見積は不確実。** wave1の791秒、verifier最大54.8秒は上限保証ではない（`V/t2772-wave1-README.md:139`）。12走×54.8秒だけでも約658秒なので、P1の400〜600秒は予測値としてのみ使う。依存物cache有りで600〜1200秒程度を計画枠とし、3600秒のgeneric一jobで足りる見込み。変異matrixは別jobとする。

## 5. DQ対照とdeny-only対照

**pytestとcomputeの両方で実施する。** 新driverに当該template専用のcontrol生成関数を置き、新testは期待subtypeを独立に固定して照合する。

pytestではwave1 testの `git archive`→一時root→`git apply --check`/apply 型を使う（`T/test_mocc_mutation_proof.py:91`）。archive対象を二ファイルへ拡張し、共有submoduleは読取だけにする。source取得失敗・patch不適用をskipしない。

適用後sourceに対して：

```python
marker = parse_template_file(str(source / SOURCE_REL), MARKER_ID)
assert marker is not None
marker.source_rel = SOURCE_REL
result = DiffQuarantine(marker, working_diff, head_text).validate()
```

`source_rel` の明示は必須。parserの既定値はbasenameである（`C/diff_quarantine.py:645`）。

diffは固定の巨大literalを持たず、**実適用sourceの対象一行を編集して `difflib.unified_diff` で生成**する。各編集位置は一意一致をassertする。contextは3行、filenameは `a/cc/mocc/transaction.cc` と `b/...`。

| control | 変更 | 期待 |
|---|---|---|
| benign | holeを `return !(temp < threshold);` | pass |
| stock-frame | marker内 `#else` 側の述語変更 | `frame-altered` |
| fallback | 原文970対応の `|| (*itr).failed_verification_` 削除 | `outside-region` |
| CLL | `lock()` 内のCLL操作を一行変更 | `outside-region` |
| RLL | RLL操作を一行変更 | `outside-region` |
| validation | 原文993のlock削除 | `outside-region` |
| X | 計装の入口検査を変更 | `outside-region` |
| P | 計装のsort前snapshotを変更 | `outside-region` |
| write-registration | 原文477削除 | `outside-region` |
| RLL-write-registration | 原文907等を削除 | `outside-region` |
| directive | holeに `#if 1` 挿入 | `hole-escape` |
| comment/splice | holeに `/*`、`//`、行末`\` | `hole-escape` |
| bad-anchor | 正常diffの削除行本文をHEADと不一致にする | `malformed` |

X/P対照だけはtemplate＋新計装版をhead_textにする。**そのsourceからmarkerを再parseする。** templateだけの行番号を使い回さない。

各controlのJSONはbase source sha、diff sha、実passed/subtypeを保存する。期待集合はコード側で固定し、record側の任意のexpected値との自己比較で緑にしない。

`auditor_digest_and_deny_only_controls` には以下を入れる。

- benign＋一致digest＋auditor pass → 元のmachine pass。
- benign＋不一致digest → `AuditorGateFailure`。
- benign＋auditor reject/uncertain → reject。
- machine reject＋auditor pass → **元のreject objectがそのまま返る**。

根拠は `C/auditor_gate.py:171、176、190`。machine reject枝ではdigest確認前に返るため、不一致digest対照はmachine pass側で行う。

## 6. 軸moduleとconsumer束縛

`C/axis_mocc_temperature.py` の定数案：

```python
from . import pin

MARKER_ID = "mocc-temperature-predicate"
SOURCE_REL = "cc/mocc/transaction.cc"
TEMPLATE_PATCH = "mocc-temperature-predicate-variant.patch"
FLAG = "MOCC_TEMP_PREDICATE"

PIN = pin.CURRENT_PIN
PROOF_PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
INSTRUMENTATION_PATCH = "instr-mocc-lock-coverage-temperature.patch"

FROZEN_TEMPLATE_HOLE_BYTES = b"  return temp >= threshold;"
FROZEN_TEMPLATE_BLOCK_BYTES = (
    b"  // EVOLVE-BLOCK-BEGIN mocc-temperature-predicate\n"
    b"  // Pure comparison of temp, threshold and constants only; no calls or state.\n"
    b"#if MOCC_TEMP_PREDICATE\n"
    b"  return temp >= threshold;\n"
    b"#else\n"
    b"  return temp >= threshold;\n"
    b"#endif\n"
    b"  // EVOLVE-BLOCK-END mocc-temperature-predicate\n"
)
SYNTAX_CONTRACT_ALLOWED = ("temp", "threshold", "bool/integer constants")
SYNTAX_CONTRACT_FORBIDDEN = (
    "FLAGS_", "thid_", "result_", "read_set_", "write_set_",
    "node_map_", "CLL_", "RLL_", "rnd_", "TRACE",
    "getenv", "rdtsc", "rdtscp",
)
```

禁止tupleは説明・監査契約であり、これだけで全C++副作用を機械排除したとは主張しない。比較・論理結合だけ、追加代入・pointer/reference・呼出し・型/global定義を禁止する文章も置く（設計:142）。

`PIN` と `PROOF_PIN` は別契約。新診断driverは `PROOF_PIN` を使う。探索用 `PIN` をe9e477caへ変更しない（設計:318〜322、axis-onboarding.md:311）。

束縛関数案：

```python
class MoccProofBindingError(ValueError):
    pass

def require_proof_binding(
    proof: Mapping[str, object],
    *,
    repo_root: Path,
    source_rel: str,
    template_patch: str,
    ccbench_commit: str,
    instrumentation_patch: str,
) -> None:
    ...
```

検査内容：

1. schema一致。
2. source、marker、flag一致。
3. templateの**repo相対path一致**と実file sha一致。
4. 実consumerが渡したcommitとproofのfull OID一致。
5. 計装版のpathと実sha一致。
6. template touch set一致。

別名templateは内容shaが同じでも拒否する。`template_patch` は `patches/...` の正規相対pathとして渡す。

この関数は**束縛だけ**を検査する。機械all_passの要求は最終proof consumer/gateで行う。そうすればcompute途中の証拠からconsumer対照を実行でき、`all_pass` が自身の対照結果を待つ循環を避けられる。

三対照：

| 対照 | test |
|---|---|
| 同じbytesを別名/別配置templateとして渡す | `MoccProofBindingError` |
| SOURCE_REL等をliteralで渡す | 正しい値なら同じ束縛関数を通る。patch探索の鍵(a)も発火 |
| 別OIDをliteralで渡す | proof OID不一致で拒否 |

同じ正しいOIDをliteralで書いたこと自体は拒否理由にならない。D2134項6が要求するのは**値・実使用sourceとの束縛**であり、literalという表記形式の禁止ではない。

現行 `PIN=511c9538…` にこのe9e477ca proofを流用するconsumerも拒否される。将来consumer導入時には、その実checkoutのOIDを渡すテストが別途必要。

`T/test_campaign.py:11385` のimportと期待表に次を追加してよい。

```python
(axis_mocc_temperature, "cc/mocc/transaction.cc")
```

これは定数契約だけで、探索認可ではない。`p3_s4_loop` から新軸moduleをimportしない。

## 7. gate testとJSON consumer

新testファイルに次を置く。

```text
test_mocc_mutation_surface_requires_auditor_live
test_mocc_template_proof_json_is_complete_and_bound
test_mocc_template_gate_activation_controls
test_mocc_template_consumer_binding_controls
test_mocc_template_checks_are_input_derived
test_mocc_temperature_axis_contract
test_mocc_template_quarantine_controls
test_mocc_template_condition_gate_uses_new_driver_id
test_mocc_template_instrumentation_logical_rows
```

鍵(a)の判定案：

```python
def introduces_mocc_marker(patch_text):
    target = None
    in_hunk = False
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            target, in_hunk = None, False
        elif line.startswith("+++ b/"):
            target = line.removeprefix("+++ b/")
        elif line.startswith("@@ "):
            in_hunk = True
        elif (
            in_hunk
            and target == "cc/mocc/transaction.cc"
            and line.startswith("+")
            and not line.startswith("+++")
            and "EVOLVE-BLOCK-BEGIN" in line[1:]
        ):
            return True
    return False
```

鍵(b)：

```python
for path in sorted(campaign_dir.glob("axis_*.py")):
    module = importlib.import_module(
        f"orchestrator.campaign.{path.stem}"
    )
    if (
        getattr(module, "SOURCE_REL", None) == "cc/mocc/transaction.cc"
        and hasattr(module, "MARKER_ID")
        and hasattr(module, "TEMPLATE_PATCH")
    ):
        ...
```

import失敗を無視しない。鍵(a)または(b)が成立したら、新JSONを `read_text()` で読む。欠落は赤。

要求は以下を一つのconsumer helperにまとめる。

- schema、top-level/check key集合一致。
- `all_pass is True`、全checkが正確なbool True。
- `compute_checks` による再導出結果一致。
- template・計装・旧JSON鎖の実sha一致。
- consumer束縛関数の成功。
- auditor実shaと、指定型/checklist各項のmocc追記。
- condition gateの新driver ID、mocc owner/target、供給値、admission。
- 12走の集合・argv・終了状態・raw verifierとの一致。

負例は「現在のrepoから新templateと新軸moduleを除いた入力集合」で鍵がfalseになることを示す。単なる空directory対照だけにしない。templateのみ、軸moduleのみ、両方、trace-hookのみの四ケースを固定する。

**compute前に親がdeselectするnodeは二つだけ。**

```text
orchestrator/tests/test_mocc_template_proof.py::test_mocc_mutation_surface_requires_auditor_live
orchestrator/tests/test_mocc_template_proof.py::test_mocc_template_proof_json_is_complete_and_bound
```

他の対照はsynthetic recordまたは実patch適用sourceで走り、完成JSONに依存させない。compute後はdeselectを外す。既存Silo gate（`T/test_campaign.py:11397`）は変更しない。

## 8. auditor.md追記とpin三箇所

`V/auditor.md.current` の対応行へ、既存Silo説明を残して次を追記する。

**型8、現52行目の末尾：**

> mocc では非 INSERT write の被覆を、CLL_ の `key_ == rcdptr_ && mode_ && lock_ == &rcdptr_->rwlock_` と RWLOCK counter `W_LOCKED` で確認する。早期 hot lock が validation-time lockskip を隠す場合があるため、hot/cold と負例の実測範囲を区別する。counter は owner ID を持たない。

**型9、現53行目の末尾：**

> mocc では transaction.cc の tidword 比較 (e9e477ca:1010〜1013) と `W_LOCKED` / searchWriteSet 判定 (1024〜1036) の条件、read_set_ 全走査、abort を固定する。hot read に absent 検査まで存在すると解釈しない。

**型13、現59行目の末尾：**

> mocc-temperature-predicate でも編集面は helper 内の単一述語行だけである。4 callsite、CLL_/RLL_、validation、X/P 計装、write_set_ 登録 (e9e477ca:477) と RLL の write-set 登録 (905〜913) は hole 外であり、差分が触れれば拒否する。P は sort 前後の size と rcdptr_ multiset の保存だけを検査し、これらの骨格全体の保存を証明しない。

**型16、現64行目の末尾：**

> mocc の読取契約は、値渡しされた temp と threshold、bool / 整数定数による比較・論理結合だけである。FLAGS_* の直接参照、thread / fitness / container / 乱数 / 時刻 / TRACE の参照、呼出しや副作用を認めない。helper 署名、呼出側引数、4 site の同一分類、construct_RLL の `|| failed_verification_` を骨格として監査する。stock 等価述語の閾値 0 / 21 の証拠を任意候補へ一般化しない。

**checklist11、現85行目の末尾：**

> mocc では mocc-temperature-predicate の適用済み骨格と実 diff を行単位で照合し、変更が helper の hole 一行だけに収まることを確認する。

**checklist12、現86行目の末尾：**

> mocc でも thread / key / storage による優先や fitness 適応を監査する。sort IR の SWO 事後条件による免除を温度述語へ移さない。

**checklist13、現87行目の末尾：**

> mocc では temp / threshold の値渡し契約、helper 署名、四つの呼出側引数、温度記録、CLL_/RLL_ 骨格と970のfallbackの無改変を確認する。

型16追記後に五分類を置く。

> mocc の分類は、(1) 読取契約違反＝型16、内容に応じ3/12/15、(2) CLL/RLL骨格改変＝型8/10/13、(3) TRACEの入口・payload前・publish前の三検査点への侵食＝型11/13、(4) validationの骨抜き＝型9/13、(5) hot/cold偽装＝型3/4/16、とする。Pの保存検査をCLL/RLL全体の保証に拡張しない。

根拠は設計:260〜272。description、型番号は変更しない。現schemaは `frozenset(range(1, 22))` で1〜21固定（`C/auditor_gate.py:29`）。

pin追随順：

1. auditor.mdの最終bytesのSHA-256を計算。
2. `orchestrator/codex_roles/review_ledger.py:19` のauditor値をそのliteralへ更新。
3. `load_role_specs(root)["auditor"]` をロードし、`render_adapter` の出力で `.codex/role-adapters/auditor.json` を置換。ledger更新を先に行う必要がある（spec.py:587）。
4. originless baselineに以下を追記。位置は現739行目の既存extension呼出後。

```python
def _extend_t2773_role_source_baseline(baseline):
    old = "a0912ebbc95e2f3641cfb1cbf0d609cfbe2deb7ba52d1c3057517b1bc69fab35"
    new = "<確定したauditor.mdのSHA-256をliteralで記入>"
    rows = baseline["journals/*/*/provenance/role_file_sha256"]
    replaced = 0
    for row in rows:
        if row[0] == old:
            row[0] = new
            replaced += 1
    assert replaced == 6
    rows = baseline[
        "reports/*/cells/*/generations/*/roles/auditor/"
        "provenance/role_file_sha256"
    ]
    assert rows == [[old, 6]]
    rows[0][0] = new

_extend_t2773_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)
```

新shaをruntime計算して期待値に使わない。前例は同test:574、622。`check_codex_agents.py --write` は使用不可（同:352）。

## 9. 登録簿閉包

**condition_meaning_gate：**

`C/condition_meaning_gate.py:160` 付近のcache群へ追加：

```python
"MOCC_TEMP_PREDICATE": DefineSpec(
    ROUTE_CMAKE_CACHE, _MOCC_OWNER, "ycsb_mocc.exe",
    "patches/mocc-temperature-predicate-variant.patch",
    inert_values=("0",),
),
```

witness群の末尾、現295行目の前：

```python
"MOCC_TEMP_PREDICATE": (
    "cc/mocc/transaction.cc",
    "#if MOCC_TEMP_PREDICATE // file-scope helper",
),
```

`RELATED_DEFINE_DECODE_MACROS`（現302）へ `"MOCC_TEMP_PREDICATE"`。`MEANING_SUPPORTED_MACROS` はwitnessから自動導出されるので手書き追加不要。

外側guardをwitnessにする理由は、同:2941が**完全一致一行の一意性**を要求するため。内側markerや四siteの `#if MOCC_TEMP_PREDICATE` は重複する。外側ならOFF時にもprobeのcompleted側が評価される。

docstringの件数は供給39→40、compile-time witness15→16へ。

**condition-gate testの追随：**

- `T/test_condition_meaning_gate.py:33` のwitness tuple末尾に追加。
- `_compile_time_source_root:244` の既定directiveを `directive or _start_directive` にする。
- `_patch_added_branch_declaration:256` の期待開始行を、moccについて上記comment付きliteral、それ以外は既存 `#if {macro}` とする。
- registry test:990の期待も同じ独立literalへ。
- domain集合:2670とRELATED集合に追加。
- cache route件数:2781は22→23、CXX_FLAGS件数17は不変。
- docstring期待:2904、2906を40、16へ。

**追加閉包：** `T/condition_gate_test_support.py:17` の `_OPTIONS` に、今回のCACHE行とuniversal mapping行を追加する。現fixtureはこれらを自動生成しないため、DefineSpec追加だけでは新cache witnessが供給されない。

既存node：

```text
test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches
test_compile_time_branch_selection_accepts_each_registry_macro
test_v1_domain_and_claim_boundaries_are_exact
test_module_claim_names_the_exact_38_define_supply_domain
```

最後のnode名は既に本文件数と一致していない。今回のclosureでは名前変更を必須にせず、assert本文を更新すればよい。

**materializer：`C/materializer_admission.py:88` の前へ。**

```python
"orchestrator.campaign.s3_mocc_template_proof._build_variant":
    MaterializerRegistration(
        NON_ADMISSIBLE,
        "fixed-producer mocc template proof; never source performance values",
    ),
```

`T/test_p3_build_authority_cli.py:165` にfilename、同:183に上記完全関数名を追加する。

確認node：

```text
test_single_registry_has_typed_compatible_projections
test_python_ccbench_manual_materializers_are_explicitly_non_admissible
test_materializer_registry_covers_all_python_build_launches
```

最後は `T/test_s8b_floor_campaign.py:8014`。

**spawn_sites：**

本案は `_run_trace`、`_verify`、`_run_checked` をimport再利用するので、新しい直接subprocess siteはない。したがって `_DIRECT_SAFE_ALLOWLIST` に架空の新 `_run_trace` を追加しない（同test:46〜65）。

新driverのworkload定数を公開する場合、同:4116のrr0検査にも四定数を追加する。

patch define inventoryは追加mappingを機械取得する（同:662）。新defineによりCounterは次のように追随する。

```text
test_ccbench_spawn_sites.py:3469  proven-unreachable: 35 → 36
                            :3472  covered: 39 → 40
                            :3496  proven-unreachable: 25 → 26
                            :3505  proven-unreachable: 25 → 26
```

既存14個のdeferred集合は変更しない。確認node：

```text
test_patch_define_inventory_matches_condition_gate_registry
test_define_sink_cross_product_has_no_unreviewed_ungated_member
test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
test_define_sink_cross_product_t2520_certify_entry_removal
test_direct_spawn_allowlist_constants_cannot_reach_protected_ratios
```

**screening_driver：**

`C/screening_driver.py:67` 付近へ：

```python
"MOCC_TEMP_PREDICATE": 0,
```

**B-3 / B-4：**

templateにも新計装版にも新しい大文字 `IZANAGI_` tokenを導入しないので、`T/test_p3_s4_loop.py:7863` のallowed集合変更は不要。確認nodeは `test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`。

`p3_s4_loop` から新moduleをimportしないため、その静的import閉包のmodule数pinを更新する理由はない。実焦点走で別の閉包が赤になった場合だけ根拠を確認する。ledger.jsonは不変。

## 10. 段5後の生死確認

親はwave1の `liveness-run.sh` を参考に、authorが用意した新資材を使って次を保存する。旧scriptのpathやbuild直起動手順を機械転写しない。

1. e9e477ca隔離checkoutを作り、template二file touchと適用成功を確認。
2. 旧計装patchの `git apply --check` が失敗、新計装版が成功することを保存。
3. 適用済みsourceからmarkerを取得。id/source_rel/hole/frame bytesを照合。
4. OFF、ON-BをTRACE=0/1で `-Wall -Wextra -Werror` build。
5. ON-B＋計装版もTRACE=0/1でbuild。
6. 実resolverで無template↔OFF一致、ON-B別identityを確認。
7. OFF・ON-Bそれぞれの計装なし↔あり論理行列を比較。
8. DQ全対照、digest/deny-only、consumer三対照を実行。
9. 実argv、rc、sha、log、比較結果をjob dirに保全。

loginではbenchmarkを起動しない。build/testは現在の `tools/run_tests.py` 経由で場所・メモリ判定を受ける。生死確認用probeも実装面なのでauthor所有とする（D95項1・2）。このplanでは実行していない。

## 11. compute投入と受入

投入コマンドは親案を採用する。

```bash
python3 tools/pegasus/dispatch_compute.py --task generic -- /usr/bin/python3 orchestrator/campaign/s3_mocc_template_proof.py --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
```

一job内で依存物準備、五build、12走、identity、controls、最終JSON生成まで行う。driverはwave1同様、site判定・single-tenant確認を残す（wave1:501）。

JSONは開始時と各段階で原子的に保存し、未充足fieldではcheckをfalseにする。途中失敗を完成したall_passへ見せない。

compute後の焦点走では、deselect二nodeを戻して新test・旧mocc test・登録簿closure・role pinを検査する。I absent期待（`T/test_mocc_proof_surface.py:410`）と旧32/14checkは不変。

## 12. n=1射影と三候補

親がfresh Claude `auditor` を一呼びで起動する。Read/Grep/Globのみ、親の推論・期待verdict・fitnessを渡さない（D38決定4、設計:274〜288）。

射影baseは **template＋新計装版、seed述語**のtransaction.ccとする。これならX/P不可触箇所も実sourceで確認できる。

渡すfile：

- base transaction.cc、full OID、適用patch一覧とsha。
- template patch、新計装patch。
- tuple.hhの型、common.hhの必要宣言の抜粋。
- 三候補diffと各 `compute_diff_digest`。
- 不可触箇所：四callsite、helper署名、fallback、CLL/RLL、validation、X/P三点、477、905〜913。
- candidate/source shaに対応づけた、性能値を除いたverify射影。

候補diff本文は以下。hunk番号は実baseから生成する。

**A1'：validationのlockだけ削除。告白コメントを入れない。**

```diff
   for (auto itr = write_set_.begin(); itr != write_set_.end(); ++itr) {
     if (itr->op_ == OpType::INSERT) continue;
-    lock((*itr).rcdptr_, true);
     if (this->status_ == TransactionStatus::aborted ||
```

**A2'：**

```diff
 #if MOCC_TEMP_PREDICATE
-  return temp >= threshold;
+  return (FLAGS_clocks_per_us == 2100) && (temp >= threshold);
 #else
```

**B'：**

```diff
 #if MOCC_TEMP_PREDICATE
-  return temp >= threshold;
+  return !(temp < threshold);
 #else
```

A1'はDQを通してauditor入力から除外してはいけない。DQ拒否とは独立に見せる。

B'は新computeの対応runを射影できる。A1'/A2'を本waveで実走しない場合は `not_run` と明記する。wave1のlockskip結果は**別sourceの経路共通証拠**として分離し、A1'の実測結果に置き換えない。新たにbroken-template版を作る必要はない。

保存先は親briefの `auditor-n1.md` と素材一式。実応答と期待判定は別に保存し、n=1を機械all_passに含めない。

## 13. 変異事前登録候補

以下は段4で確定する候補。期待killer nodeは実装後に固定する。sha不一致だけの赤を意味検出力として重複計上しない（wave1 insight:108）。

| ID | 対象・変異 | 期待 | 主な検査 |
|---|---|---|---|
| M0 | 新driverの非契約コメントを等価変更 | SURVIVED | harnessの生存対照 |
| M1 | templateのstock枝 `>=`→`>` | KILLED | frozen frame、OFF identity |
| M2 | 566だけON側を旧比較に戻す | KILLED | 四site構造契約 |
| M3 | 新計装 `#line 1204`→1205 | KILLED | OFF/ON論理行列 |
| M4 | helper外側guardを削除 | KILLED | OFF前処理本文・helper消失 |
| M5 | 軸moduleのMARKER_ID変更 | KILLED | 実marker/frozen bytes照合 |
| M6 | 束縛関数のtemplate sha検査削除 | KILLED | 同pathの内容改変対照 |
| M7 | gateの鍵(a)または(b)を無効化 | KILLED | templateのみ/moduleのみ対照 |
| M8 | DQ subtype不一致も許容する | KILLED | 独立期待subtype表 |
| M9 | auditor型16のmocc追記削除 | KILLED | 項目別内容検査、sha束縛 |
| M10 | JSONのtemplate shaを1文字変更 | KILLED | 完成JSON consumer |
| M11 | JSONのall_passをfalse | KILLED | 完成JSON consumer |
| M12 | 新DefineSpecまたはmaterializer entry削除 | KILLED | registry閉包 |
| M13 | ON-B別identity checkを定数True化 | KILLED | 入力由来check対照 |

M12は実際の事前登録時に削除対象を一つに固定する。異なる変異を一件へ束ねたまま実行しない。

## 14. 親briefへの異議と所有範囲

1. **P4の「七hunk」は訂正。** 六hunk・七復元点。位置は旧patch:4、16、48、75、88、102。
2. **P9には一意witnessの具体策が必要。** 同じ裸 `#if MOCC_TEMP_PREDICATE` を六箇所に置いたまま登録すると拒否される（condition gate:2941）。外側の専用comment付き行で解決する。
3. **fixture閉包が親表から漏れている。** `T/condition_gate_test_support.py` のCACHE供給二行もauthor所有に加える。
4. **P5のPINを一種類にしない。** `PIN=pin.CURRENT_PIN` と `PROOF_PIN=e9e477ca` を分離する。現行探索PINで旧proofを消費できるとは主張しない（設計:318）。
5. **literal PINという表記自体は拒否できない。** 別OID・別実sourceとの不一致を拒否する。任意の直書き経路を閉じたという主張はD2134項6に反する。
6. **consumer対照に完成all_passを先に要求すると循環する。** 束縛関数と最終proof gateを分離する。
7. **400〜600秒は保証値ではない。** wave1最大54.8秒や791秒からの比例外挿にはbuild・trace量・machine状態の変動がある。
8. **旧patch不適用はoffsetだけでは説明できない。** 本案では第一hunkのcontext不一致を根拠にし、実apply検査は段5後に残す。
9. **P1の12走は新templateのstock対照。** wave1のhot負例発火を新template上で再観測したとは書かない。四site全動的被覆も主張しない（D2134項3・4）。
10. **旧nm検査の名前範囲に注意。** CC-native helperまで `izanagi` と命名すると計装消失検査と混ざる。helper名を `mocc_is_hot` にする小修正を推奨する。

author所有は新patch二本、軸module、新driver、新test、auditor本体＋pin三箇所、登録簿とfixture追随、生死確認用の実装資材。親所有はREADME等のdocs本文、統合、compute投入、n=1、記録。旧driver・旧JSON・旧patch・旧checkは不変とする（D95、親brief:21、27）。

## 総括

**templateは、include群直後の19行helper、helper内の単一return hole、四site各4行増分、OFF原文保存、Options.cmake二行追加で確定できる。** 計装復元値は `36 / 1025 / 1026 / 1193 / 1204 / 1222 / 1230`。実resolverを利用できる静的根拠があり、直接前処理への格下げは不要。

| 親案 | 判定 |
|---|---|
| P1 | 採用。12走の範囲を限定し、時間は予測扱い |
| P2 | 採用。旧bytes不変、helper import、新二file apply |
| P3 | 条件付き採用。配置・return hole・一意guardを具体化。helper名は小修正推奨 |
| P4 | 採用。「六hunk・七復元点」へ訂正 |
| P5 | 条件付き採用。proof/exploration PIN分離、束縛とall_passを分離 |
| P6 | 採用。二つの鍵を独立対照、JSON欠落は赤 |
| P7 | 採用。既存番号への追記と三pin追随 |
| P8 | 採用。未実走候補のverify結果を捏造せず、期待verdictを隔離 |
| P9 | 条件付き採用。cache route可。一意witnessとfixture閉包を追加 |
| P10 | 採用。loginは生死確認、受入・変異はcompute |

主要な異議は、**witness重複、fixture漏れ、PIN混同、consumer検査の循環、時間実測の一般化**の五点。

段5は**author一本で足りる**。patch・行番号・軸定数・JSON・testが密結合なので、所有を分ける利益は小さい。目安は実装と焦点修正で60〜100分、25k〜40k tokens程度、computeは600〜1200秒を計画枠とする。いずれも未実測の見積であり、review/fixと変異matrixは別枠。本plan自体は静的確認まで完了し、build・前処理・pytestの緑は未確認である。