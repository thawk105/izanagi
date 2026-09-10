## プラン

### checker

新規 `tools/check_silo_validation_isolation.py` を作る。

- `tools/check_silo_validation_isolation.py:1-45`
  - schema 名、終了コード、`AnalysisError`、`Hunk`、`EditSpan`、`FunctionRegion`、`CallEdge` を定義する。
  - repo root は `Path(__file__).resolve().parents[1]`、入力 source は固定で `external/ccbench/` とする。
  - `.git`、`cc/silo/transaction.cc`、`cc/silo/include/transaction.hh` が存在しない場合は未初期化として停止する。

- `tools/check_silo_validation_isolation.py:46-165`
  - UTF-8 の git unified diff を解析する。
  - 通常の既存 file 編集だけを受理し、binary diff、rename/copy、new/delete file、path traversal、重複 file section は `ERROR` にする。
  - hunk の old-side contextと削除行を submodule 現物へ完全一致で探索する。行番号は探索開始位置のヒントに使うが、現物とのずれを許すため一致箇所は file 全体から求め、0 件または複数件なら停止する。
  - patch は tree に適用せず、全 file の post-image をメモリ上で組み立てる。
  - `+` 行には post-image 行番号、`-` 行には前後の残存行間の zero-width deletion anchor を記録する。削除 anchor の region が一意でなければ停止する。

- `tools/check_silo_validation_isolation.py:166-305`
  - `cc/silo/transaction.cc` を root TU とし、raw post-image の quoted include を再帰的に解決する。
  - file 集合は root TU と、そこから到達する `external/ccbench/cc/silo/include/` および `external/ccbench/include/` 配下の first-party header とする。angle include と `gflags/`、`glog/` は外部 leaf とする。
  - コメント、文字列、文字 literal、raw string を同じ改行数の空白へ置換する。preprocessor directive 行は構文境界解析時だけ空白化し、各条件枝の本文はすべて残す。
  - brace/parenthesis の balanced scan で class、namespace、out-of-class definition、inline definition、template method を抽出する。symbol は `owner::name/arity` で一意化する。
  - 変更行の region は signature、連続する属性・decorator、関数 body を含む最小 region とする。コメント以外の変更がどの regionにも属さず、後述の macro 編集にも分類できない場合は停止する。

- `tools/check_silo_validation_isolation.py:306-430`
  - `TxExecutor::validationPhase/0` を一意な root として breadth-first search する。
  - direct call は、同一 class、明示 namespace、名前と arity が一意な first-party definitionの順で解決する。曖昧な overload、未知の first-party call、関数 pointer、virtual dispatch は停止する。
  - `sort(write_set_.begin(), write_set_.end())` は、`transaction.hh:35-36` の `std::vector<WriteElement<Tuple>>` から element type を導き、`silo_op_element.hh:67-71` の `WriteElement::operator</1` へ implicit edge を張る。
  - `std::max(max_rset_, check)` と `std::max(max_wset_, expected)` は field/local 宣言から `Tidword` を導き、`tuple.hh:30` の `Tidword::operator</1` へ implicit edge を張る。型が導けなければ停止する。
  - 各 region に最短 depth と caller、callsite、`direct` または `implicit-comparator` を記録する。
  - 実体上の主要 anchor は `transaction.cc:383-493`、`lockWriteSet` の `transaction.cc:145-193`、両 `unlockWriteSet` の `transaction.cc:352-381`、`searchWriteSet` の `transaction.cc:342-350`。`atomic_tool.hh:21-29`、`atomic_wrapper.hh:33-35`、`trace.hh:41-62,105-119` も実際の呼び先として解析する。

- `tools/check_silo_validation_isolation.py:431-495`
  - `cmake/Options.cmake` の pre/post image から cache `set(CCBENCH_X ...)` と `ccbench_universal_definitions` 内の `X=${CCBENCH_X}` を balanced scan する。
  - defaultまたは供給 mapping が変わった TU macro を抽出する。説明できない非コメント CMake 差分は停止する。
  - preprocess は使わず、validation closure の各 raw regionをコメント・literal除去後の identifier token 単位で検索する。
  - function外で変更された C++ conditional macroも同じ検査へ加える。token paste、computed include、編集された `#define/#undef/#include` は扱わず停止する。
  - 正例では `BACKOFF_FIXED` と `BACKOFF_NOINLINE` が抽出されるが、closure regionには現れないことを evidence に残す。参考にする既存手法は `source_digest.py:1646-1678` だけで、同 fileは変更も import もしない。

- `tools/check_silo_validation_isolation.py:496-565`
  - region intersection と macro reference intersection を統合し、決定的な JSON 1 行を stdout へ出す。
  - CLI は次の一形だけとする。

```text
python3 tools/check_silo_validation_isolation.py PATCH
```

  - rc `0`: `verdict="PASS"`、交差なし。
  - rc `1`: `verdict="FAIL"`、交差あり。
  - rc `2`: `verdict="ERROR"`、判定不能または入力不正。これを PASS と同一視しない。
  - stdout は `schema`、`verdict`、`patch`、`validation_root`、`closure`、`cmake_macros`、`intersections` を持つ canonical JSON とする。`ERROR` は同 schema で `error.code` と `error.message` を返す。

### test

新規 `orchestrator/tests/test_silo_validation_isolation.py` を作る。

- `orchestrator/tests/test_silo_validation_isolation.py:1-45`
  - repo、checker、submodule現物、3 patch の絶対 pathを定義する。
  - `_invoke(patch)` は常に `[sys.executable, CHECKER, patch]` の同じ argv で subprocess 実行し、stdout JSON を検証する。checkerやsource dependencyは stub しない。

- `orchestrator/tests/test_silo_validation_isolation.py:46-105`
  - 正例 1 本と負例 2 本の CLI verdict、rc、intersection evidence を固定する。
  - 正例では CMake macro evidence が `BACKOFF_FIXED`、`BACKOFF_NOINLINE` の2件で、closure参照が空であることも確認する。

- `orchestrator/tests/test_silo_validation_isolation.py:106-150`
  - submodule現物から closure を直接導出し、root、深さ1 helper、implicit comparator、深さ2 overloadを名指しで検査する。
  - caller、post-validation、abort/backoff側が closure に混入しないことを別 nodeで検査する。

- `orchestrator/tests/test_silo_validation_isolation.py:151-205`
  - 存在しない patch、適用不能 hunk、存在しない ccbench root がすべて `ERROR` になることを固定する。
  - temporary patch は `tempfile.TemporaryDirectory` 内で作り、各 test は引数なしにして自走可能にする。

- `orchestrator/tests/test_silo_validation_isolation.py:206-245`
  - 固定した test 関数 tuple を実行する `_run()` と `if __name__ == "__main__": sys.exit(_run())` を置く。0件実行の偽緑を許さない。

既存の入力 patch、source、checker は変更しない。特に `patches/*.patch`、`condition_meaning_gate.py`、`source_digest.py` は不可触とする。

## 判定式

post-image source treeを `T' = apply_in_memory(T, P)` とする。validation経路は、preprocessor条件を評価しない raw-config union call graph上の最小不動点とする。

```text
V0 = { TxExecutor::validationPhase/0 }
Vn+1 = Vn ∪ { resolve(call) | call は Vn の region内に出現 }
V = Vn+1 = Vn となるまで反復
```

`resolve` には direct callに加え、`std::sort` と `std::max` の implicit `operator<` edgeを含める。`commit()` は callerなので含めず、`writePhase()` は validation成功後なので含めない。`abort()` と `Backoff::backoff()` も call edgeがないため含めない。

編集面を次で定義する。

```text
Eregion = post-imageの追加行または削除anchorが属する関数region
M = Options.cmakeの変更で影響するTU macro
    ∪ function外C++ conditional編集のmacro
R(m) = macro mをidentifier tokenとして含むV内のraw region
```

交差集合は次である。

```text
Iregion = Eregion ∩ V
Imacro  = { (m, r) | m ∈ M かつ r ∈ R(m) }
I       = Iregion ∪ Imacro
```

`I` が空なら PASS、非空なら FAIL。`T'`、region、call edge、implicit comparator、macro effectのいずれかを一意に導出できなければ ERROR とする。

`broken-silo-norw-validation.patch:5-26` は `validationPhase` 自体へ写るため depth 0、`broken-silo-lockskip-validation.patch:5-20` は `lockWriteSet` へ写るため depth 1で FAIL になる。正例の `silo-backoff-fixed.patch:32-77` は `Backoff::backoff` と function外 guard、同 patch `:5-27` は未参照 macroの CMake供給だけなので PASS になる。

## 適用限界

次は「交差なし」ではなく rc 2の ERROR にする。

- submodule未初期化、source/patchが読めない、UTF-8不正。
- binary、rename、copy、new/delete file、path escapeを含む diff。
- hunk contextが現物に0件または複数件一致する、または削除anchorのpost-image regionが一意でない。
- root、callee、overload、型、implicit comparatorを一意に導出できない。
- macroが関数定義やcallを生成する、token paste、computed include、関数 pointer、virtual dispatch、lambda経由のcall。
- validationから別 translation unitのextern定義へ新しいcallが追加される。この限定parserでは追跡せず ERROR とする。
- 条件枝を同時に残したraw sourceでbrace構造を解析できない。
- `Options.cmake` 以外のbuild-system変更、または cache/default/compile-definition mappingとして説明できない CMake変更。
- token-bearing C++ file-scope編集が、対応するfunction regionまたは限定したmacro検査へ分類できない。

恒真化は避けられる。関数regionの所有判定、call抽出、macro参照走査のいずれも preprocess 後出力を使わず、すべての `#if` branchを残す。したがって未定義の `IZANAGI_BREAK_NOREAD_VALIDATION` と `IZANAGI_BREAK_LOCK_COVERAGE` の既定 OFF状態でも、追加行はそれぞれ depth 0、depth 1 regionへ写る。別形の同じ罠を避けるため、closure edgeもdefault configurationだけに縮退させず、CMake macroもraw tokenで検査する。

## テスト

| node | 入力 | rc / verdict | 固定する命題 |
|---|---|---|---|
| `test_cli_accepts_registered_backoff_patch_and_reports_cmake_macros` | `silo-backoff-fixed.patch` | `0 / PASS` | backoff regionはclosure外。新規2 macroもclosureから未参照 |
| `test_cli_rejects_norw_patch_in_validation_root` | `broken-silo-norw-validation.patch` | `1 / FAIL` | guardが既定OFFでも `validationPhase`、depth 0との交差を検出 |
| `test_cli_rejects_lockskip_patch_in_depth_one_callee` | `broken-silo-lockskip-validation.patch` | `1 / FAIL` | `lockWriteSet`、depth 1との交差を検出 |
| `test_real_closure_contains_root_helpers_and_implicit_comparators` | submodule現物 | 適用なし | root、`lockWriteSet/0` depth 1、`WriteElement::operator</1` depth 1、`Tidword::operator</1`、`unlockWriteSet/1` depth 2を含む |
| `test_real_closure_excludes_callers_postvalidation_and_abort_backoff` | submodule現物 | 適用なし | `commit`、`writePhase`、`abort`、`Backoff::backoff`、`leaderBackoffWork` を含まない |
| `test_cli_missing_patch_is_error_not_pass` | 存在しないpatch | `2 / ERROR` | unreadableを非交差へ倒さない |
| `test_cli_unmappable_hunk_is_error_not_pass` | 不一致context | `2 / ERROR` | hunk mapping失敗を非交差へ倒さない |
| `test_missing_ccbench_root_is_error_not_empty_closure` | 存在しないroot | `ERROR` | 未初期化を空closureとして扱わない |

最初の3 nodeはすべて同じ `_invoke(patch)` を通し、CLI引数形を固定する。closureの2 nodeは `transaction.cc:383-493` などのsubmodule現物を直接解析し、古い fixtureやstubを使わない。

実測は親が `tools/run_tests.py` 経由で行い、緑を確認した JUnitだけを `tools/update_acceptance_duration_ledger.py:476-508` の `--add-only` へ渡す。手編集や推定時間は使わない。

## 未解決 / 裁定候補

- 「既存 fileを変更してはならない」「台帳追加はscope外」と、新規testの受入所要台帳登録必須が衝突している。登録先は既存の `orchestrator/tests/acceptance_duration_ledger.json:2,22161` であり、F902の正本手順も `docs/failures.md:23526-23537` で生成更新を要求している。
- 推奨裁定は、実測JUnitからの `--add-only` 生成差分だけを受入metadataの例外として認めること。この例外が認められなければ、新規2 fileは作れても台帳要件を同時には満たせない。
- AST化、別translation unitまでの一般化、他CMake file対応、gate新設は本scopeでは実装せず、必要になった時点の別裁定パッケージとする。

## 総括

raw-config unionのcall closureとin-memory post-image mappingで、guard既定OFFによる恒真化を防ぐ。  
正例は未参照CMake macroを含めてPASS、負例はdepth 0と1でFAILに固定する。  
未解決は、既存file不可触と受入所要台帳更新の直接衝突だけである。