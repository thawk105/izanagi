## 総括

- 試作は下記 **8 変更群・abort 条件化の有無による 2 版**とする。最難関は、依存閉包を固定しながら S の前処理 bytes を stock に一致させる点。
- **P5 の最小変更だけでは S は一致しない。** 現行 patch に、abort 以外の無条件の宣言削除・処理変更がある。
- shadow は **patch ごとに独立した root × 登録簿 3 種**のファイルコピーを推奨。判定 logic は byte 同一を検査する。
- 基本 matrix は **96 cell**。推奨実走は基本から **56 cell＋abort 対照 4 cell＝60 cell**。
- gate 1 要求を仮に 5–20 秒と置くと、準備・build 込み約 **6–22 分**。未計測の見積りなので途中保存と予算打切りを設ける。
- brief のずれは、登録簿の行番号、S の残差の範囲、abort 条件化と runner 契約の衝突、DLR の従属性の一般化。
- 予算切れでも「warm-up が除く拒否」「patch が除く拒否」「登録簿・runner に残る拒否」を分けて途中結論を残す。
- この段では資料読解のみ実施。ファイル変更、configure、前処理、build、selftest は未実行。

**1. 計画の前提と、現物からの修正**

以下では `G=orchestrator/campaign/condition_meaning_gate.py`、`R=tools/pegasus/run_ss2pl_lock_study.py`、`P=patches/ss2pl-lock-protocol-study.patch` と略す。行番号は今回読んだ現物に対する番号。

判定順は次のとおり。

1. request・capture の契約検査。
2. requested、control の順に configure。
3. requested、control の owner entry 選択。
4. requested、control の順に、compile define・compiler の確認、前処理、依存情報収集。
5. 両結果の compiler identity 比較。
6. comparable argv 比較。
7. 非 inert の場合、build-root 依存 builtin 検査、依存閉包比較、bytes 相違の確認。
8. inert の場合、bytes 完全一致、次いで限定された source-root 置換の検査。

根拠は G:1851–1950、2216–2330、2471–2712。したがって、**argv drift の予測が正しくても、pristine ではその前の前処理で失敗する**。companion を stock に渡した場合は、さらに前の configure が失敗する。

brief の修正点は以下。

| 項目 | 現物による修正 |
|---|---|
| SS2PL 登録簿 | G:160–176。target は 161/165/170/174、KIND companion は 167。184–199 ではない |
| 宣言済み差分の順序 | R:88 付近の辞書は bomb、transaction、util の順。abort は「1 件目」ではない |
| P2 の DLR | 現行 patch でも IMPL=0 に DLR 分岐がある。DLR は「意味がない」のではなく、まず marker による argv drift で拒否される |
| P3/P5 の S 一致 | abort 条件化だけでは不足。後述の無条件差分が残る |
| stock-lock 検査 | `validate_default_stock_lock_absence` は R:1492–1656。1492–1500 だけでは結果判定まで読めない |
| 空 TU | `CompileOptions.cmake:30–33` は `-Wall -Wextra -Werror`。`-Wpedantic` は付与していない。実効 argv と build で最終確認する |

**2. 試作 patch：8 変更群**

主版を `ss2pl-lock-protocol-study-define-only.patch`、abort 除去を無条件のままにする対照版を `ss2pl-lock-protocol-study-define-only-abort-unconditional.patch` とする。新しい実験用 define は追加しない。追加 define による argv・登録簿への影響を避け、両版の差分を abort の小範囲だけに固定できる。

| # | 現行 patch の位置 | 変更後 |
|---|---|---|
| 1 | P:19–46 | `_ss2pl_dlr_marker` 分岐を撤去し `OPTIONS DLR1` 固定。`SOURCES transaction.cc util.cc wfg.cc` を無条件指定。4 軸 define と YCSB 専用 define は維持 |
| 2 | P:135–187 | `ss2pl_lock.hh` を include guard 化。DLR marker 整合性 `#error` を撤去。default・値域検査の後、`rwlock.hh`、`ss2pl_study_lock.hh` を順に無条件 include。alias だけ `#if SS2PL_LOCK_IMPL == 1` |
| 3 | 新規 hunk：stock `include/rwlock.hh:8` の class～終端 | **include 群と `using namespace std;` は無条件のまま**、`class ReaderWriteLock` だけ `#if !defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0` で囲む。既存 `#pragma once` は保持 |
| 4 | P:194–689 | study header を include guard 化。P:196–206 の依存 include は無条件。enum、class、template、関連関数・変数すべてを `#if SS2PL_LOCK_IMPL == 1` 内へ |
| 5 | P:696–715 | WFG header を include guard 化。`<cstdint>`、`<string>` は無条件。enum と全宣言を `#if SS2PL_WFG_DIAG` 内へ |
| 6 | P:2236–2655 | `wfg.cc` の header include の後、残りの include・namespace・定義を `#if SS2PL_WFG_DIAG` で囲む。WFG=0 の object 生成を plain build で確認 |
| 7 | P:1340–1342、1586–2105 | transaction の WFG header include を無条件化。既存 DLR 分岐 5 組を `SS2PL_DLR` の値比較へ置換 |
| 8 | P:1428 前後の abort 増分削除 | 主版では非 YCSB に増分を戻す。対照版は現行どおり無条件除去 |

#2 の形は次とする。

```cpp
#ifndef CCBENCH_SS2PL_LOCK_HH_INCLUDED
#define CCBENCH_SS2PL_LOCK_HH_INCLUDED

// 現行 default と値域検査。
// SS2PL_DLR 未定義時は試作では 1 を既定にする。

#include "../../../include/rwlock.hh"
#include "ss2pl_study_lock.hh"

#if SS2PL_LOCK_IMPL == 1
using ReaderWriteLock = SS2PLStudyLockT<SS2PL_LOCK_KIND, SS2PL_DLR>;
#endif

#if SS2PL_LOCK_IMPL == 0 && SS2PL_DLR == 2
#error "SS2PL_DLR=2 with stock lock is outside this prototype"
#endif
#endif
```

stock header の**中身全部**を条件化する案は選ばない。IMPL によってその header 経由の依存まで変わる恐れがあるため、class のみを条件化する。stock clone 自体は変更せず、patched clone に適用する patch hunk として追加する。

同様に study header の include まで IMPL 条件内に入れると、外側を無条件 include にしても閉包差が残り得る。宣言・定義と依存 include を分離する。ただし、無条件に増えた標準 header の出力が S の stock 比較に残る可能性はあり、**この構造だけで S 一致を保証しない**。

DLR 分岐の変更箇所は以下の 5 組。

| stock transaction.cc | 現行 patch | 試作 |
|---|---|---|
| 172/178 | 1586/1595/1611 | `#if SS2PL_DLR == 0` / `#elif SS2PL_DLR == 1` |
| 263/269 | 1645/1655/1664 | 同上 |
| 309/314 | 1804/1810/1822 | 同上 |
| 411/413 | 2020/2022/2027 | 同上 |
| 436/438 | 2096/2098/2103 | 同上 |

IMPL=0 用の DLR2 fallback は削除し、上記 `#error` に集約する。B/D の実 arm は IMPL=1 だが、gate の DLR=2 要求は companion がないため **IMPL=0 で比較され、`preprocess-failed` となる**。本 wave は S/phase1 に限定し、B/D が通るとは書かない。

abort 主版は元の増分位置に以下を戻す。

```cpp
#if defined(SS2PL_WORKLOAD_YCSB) && SS2PL_WORKLOAD_YCSB
// 増分は workload 側が所有する。
#else
  ++result_->local_abort_counts_;
#endif
```

両版の差分はこのブロックだけにする。YCSB の処理は同じだが、tpcc の bytes と静的所有権検査の結果が変わる。

**S がなお red となる理由**

最小試作の期待値を green にしてはいけない。以下は abort とは独立した残差である。

| 現物 | S に残る変更 |
|---|---|
| P:100–122 | `common.hh` の legacy workload の DEFINE/DECLARE 削除。transaction は common を include する |
| P:720–759 | include 位置と constructor の出力形の変更 |
| P:1500 前後 | `begin()` の 1 行定義から複数行への変更 |
| P:1634–1845 | `update()` の `return_status`、条件構造、局所 scope、return の変更 |
| P:1913–1917 | `delete_record()` に無条件で追加した `break` |
| P:1990–2019、2048–2095 | stock にあった既取得ロック検査を IMPL=1 内へ移動 |
| P:2120–2143 | `unlockList()` の loop に追加した brace |

S の一致まで試す追加版が必要なら、上記を別 revision として明示する。具体的には common の legacy 宣言を非 YCSB に戻し、constructor と関数の stock 経路を元の出力形に戻し、study/WFG 用の変更をその条件内に置く必要がある。`update`、`delete_record`、`read_lock`、`write_lock`、`unlockList` の各 stock 経路も復元対象になる。

これは P5 の「最小変更」の見積りを超える。**最初の計算ノード job は上記 8 群の試作を測り、この不足自体を採否材料にする**。S を通すためだけに追加修正を重ね、試作の内容を途中で曖昧にしない。

util.cc、bomb_ss2pl.cc は別 TU であり、transaction の include 先として参照されていない。gate は target 全体の source を前処理しないため、両 `.cc` の直接差分は owner 閉包に入らない。一方、**bomb 差分の説明に現れる common.hh の変更は owner 閉包に入る**。実測 receipt の dependency identities でもこの区別を確認する。

**3. runner の静的契約**

| 契約 | 主版の予測 | 対照版・注意点 |
|---|---|---|
| `validate_abort_counter_ownership` R:1061–1094 | **拒否**。`#if` を評価せず、abort 内の増分を 1 個数える | 無条件除去版は transaction=0、workload=2 の期待を満たす見込み |
| `_study_lock_header_declarations` R:1334–1489 | raw header 内の宣言を抽出できる | guard 内だから宣言が見えない、とはならない |
| `validate_default_stock_lock_absence` R:1492–1656 | 前処理後に study の宣言が消えれば識別子不在を観測できる見込み | baseline での一般名除外、util の axis label の位置など、完全な入力が必要 |
| `_validate_compile_definitions` R:911–937 | 8 define の値が期待 cache と一致すれば受理する見込み | `DLR1` と `SS2PL_DLR=0` の意味的矛盾を検査するコードはない |

abort 増分を macro 展開や helper へ隠して静的走査を通す変更はしない。主版の拒否を runner 層の費用として記録する。

stock-lock 不在検査には transaction 1 本の結果だけを渡さない。S の tpcc compile entries から、stock に実在する TU を列挙し、runner の token scan と baseline calibration に沿った入力を作る。新規 `wfg.cc` は stock にないため、既存 TU 群と別欄にする。無条件 source 追加による build graph 差も残す。

これらの Python 検査自体は login で実行可能。ただし不在性検査の入力取得には前処理が必要であり、合成入力の成功を実木の不在性と混同しない。

**4. shadow 登録簿**

ファイルコピー方式を推奨する。patch 内容ごとに独立した root を用意する。

```text
shadow/<patch-id>/<registry-id>/
  orchestrator/campaign/condition_meaning_gate.py
  patches/ss2pl-lock-protocol-study.patch
```

`patch-id` は `current`、`redesigned`、`abort-unconditional`。shadow 内の patch は元の相対名のまま置き、対応する試作の内容をコピーする。これにより `patch_rel` の書換えを不要にできる。入力元の試作名、コピー先、sha256、byte 数を receipt に残す。

登録簿は次の 3 種。

| ID | target | KIND companion | gate source の変更 |
|---|---|---|---|
| O | ycsb | IMPL=1 | なし |
| T+ | tpcc | IMPL=1 | G:161/165/170/174 の target だけ |
| T− | tpcc | なし | 上記＋G:167 を空 tuple に置換 |

O は「現行登録簿の target/companion」を意味する。試作 patch の O cell でも patch declaration の参照先はその試作に対応させる。現行 patch の O は repo の実 module と byte 同一であることを確認する。

読み込みは実 package を先に import してから行う。

```python
name = "orchestrator.campaign._t2737_gate_<unique_id>"
spec = importlib.util.spec_from_file_location(name, shadow_gate_path)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
```

`module.__package__ == "orchestrator.campaign"` を確認する。shadow root を `sys.path` の先頭に入れて実 package を置き換えない。各 cell の capture、request、record、admission は**同じ module instance**で生成する。G は exact type と record integrity を検査するため、別 shadow の record を混ぜない。

受領証には以下を残す。

- repo gate と shadow gate の sha256、`difflib.unified_diff`。
- 許可した 4 target 行と companion 行以外が byte 同一という検査結果。
- SS2PL の 4 spec と、非 SS2PL spec が不変という検査結果。
- `source_digest.__file__`、import された関数・型の module 所在地。
- `Path(module.__file__).resolve().parents[2] / spec.patch_rel` の絶対 path と sha256。
- `_patch_changed_paths(spec)` の結果と、対応 patch の `diff --git` paths の一致。

行番号固定の単純置換ではなく、期待する SS2PL block の完全一致を確認して置換する。未知の入力には失敗させる。

プロセス内の `_DEFINE_SPECS` 書換えは短く実装できるが、G:243 の `MappingProxyType` の背後を変えることになり、cell 間の状態漏れや参照 patch の所在を監査しにくい。今回はファイル方式を採る。

**5. cell matrix と期待 reason_code**

1 cell は「arm の 1 軸について supply と meaning を評価する単位」。基本総数は、

`2 arm × 4 軸 × 2 patch × 3 登録簿 × 2 staging 状態 = 96`

abort 対照版まで全面展開すれば 144 cell になるが、全面展開は不要。

以下は warm-up 後の予測。軸順は IMPL / KIND / DLR / WFG。

| patch | 登録簿 | S | phase1 |
|---|---|---|---|
| 現行 | O | O / C / O / O | D / E / A / D |
| 現行 | T+ | M / C / M / M | D / E / A / D |
| 現行 | T− | M / M / M / M | D / B / A / D |
| 試作 | O | O / C / O / O | E / E / E / E |
| 試作 | T+ | M / C / M / M | E / E / E / E |
| 試作 | T− | M / M / M / M | E / B / E / E |

| 記号 | `reason_code` |
|---|---|
| O | `owner-tu-unresolved` |
| C | `configure-failed`：stock の未使用 companion cache 警告 |
| D | `dependency-closure-drift` |
| A | `compile-command-drift` |
| M | `stock-inert-mismatch` |
| B | `preprocess-bytes-identical` |
| E | `requested-default-preprocess-different` |

試作の E は無条件 include による閉包固定が実効を持つという予測であり、実測結果ではない。S の M は前節の既知残差による。

pristine の予測は次の規則で全 cell を定義できる。

- S/O：warm 後と同じ O/C/O/O。前処理へ進まない。
- S/T+：`preprocess-failed` / C / `preprocess-failed` / `preprocess-failed`。
- S/T−：全軸 `preprocess-failed`。
- phase1：patch・登録簿を問わず全軸 `preprocess-failed`。
- 上記 `preprocess-failed` は stderr に masstree の `config.h` 不在が現れることまで確認する。

meaning は R と同じ `declaration=None` を渡すため、全 cell で `unestablished / meaning-witness-undeclared` の予測。supply green と runtime meaning 成立は区別する。

推奨実走は以下の **60 cell**。

| 対象 | 数 |
|---|---:|
| 主 2 patch × 全登録簿 × 両 arm × 4 軸、warm 後 | 48 |
| 現行 patch/O/phase1、pristine | 4 |
| 試作/T−/S、pristine | 4 |
| abort 無条件除去版/T−/S、warm 後 | 4 |
| 合計 | **60** |

pristine を現行 phase1 だけにすると、stock の前処理が warm-up で可能になる対照が弱い。試作/T−/S の対を追加する。S/O は owner 選択で止まるため、その代わりにならない。

T+ と T− の非 KIND 3 軸は同じ比較なので、warm 部分の 12 cell は理論上重複する。ただし異なる shadow の record を family に流用しないため、通常は実行する。削る場合は「family 未完測」と明示し、4 軸 admission を作らない。

予測と異なる場合の読み方も固定する。

- 試作 E が D：条件内の依存 include が残る、または条件が依存探索へ影響している。
- 試作 E が A：DLR marker 以外の define・option 差が残る。
- T− の KIND が E：IMPL=0 でも KIND が前処理に影響する経路がある。
- S が green：common と transaction の既知残差が実際に消えた理由を bytes・選択条件で説明する。
- warm 後も `config.h` 不在：warm-up と gate が異なる staging を参照している可能性。
- C が消える：stock configure が companion を消費した理由を調べる。次の拒否まで到達しただけの可能性もある。

**6. probe の実装順**

`t2737_gate_probe.py` は指定の引数に `--selftest` を加える。`--cells` は既知の cell ID、または `recommended`、`login-precheck` を受け付け、未知 ID・重複 ID は拒否する。

1. **入力・来歴**
   - R:728 の `validate_required_commands`、R:782 の `verify_canonical_submodule` を呼ぶ。
   - runner、gate、probe、全 patch、shadow diff、canonical HEAD を記録。
   - `c++` の解決先、realpath、version、hostname、PBS job ID を保存。
   - `discover_pbs_jobid` は前 wave と同じ環境変数→同 hostname の compute-visible receipt→unknown の順。取得元も保存する。

2. **staging**
   - hydrate 済みの専用 staging を使用。共有の永続 cache を pristine と呼ばない。
   - `masstree/config.h` がないことを pristine cell の直前に確認する。
   - `_validate_thirdparty` の結果と各 FetchContent path の realpath を記録。
   - scratch、build、shadow など実行の親 directory 名に `wfg` を入れない。patch 内の本来のファイル名は変更しない。

3. **clone**
   - R:802 の `clone_network_free` で stock、current、redesigned の 3 本を作る。
   - R:814 の `_apply_patch` で current と主試作を適用する。
   - abort 所有権検査は例外を receipt に保存し、予測された拒否で matrix 全体を中止しない。

4. **pristine cell**
   - warm-up・plain build より先に実行。
   - 個々の失敗後も残りを評価し、cell ごとに JSON を保存する。

5. **warm-up**
   - redesigned clone の独立 build directory を R:1928 の `_configure` で構成。
   - `cmake --build <warm-dir> --target masstree_build --parallel <jobs>` を 1 回。
   - config.h と archive の生成、所要、staging の参照先を記録。
   - 同じ staging を stock/current/redesigned の configure に渡す。

6. **warm cell**
   - R:1988–2003 の `configure_args` をそのまま再現する。
   - `_expected_cache(arm, backoff=1)` と `_condition_request_inputs` を使用。
   - **arm の他の 3 軸を configure_args に追加しない。** runner は軸 cache を除外し、要求軸と登録 companion だけを渡している。
   - 同じ shadow で以下を実行する。

```python
captured = gate.capture_define_inputs(
    source, stock_root=stock, configure_args=configure_args)
request = gate.make_define_request(
    driver_id=f"tools.pegasus.run_ss2pl_lock_study:{arm}",
    macro=macro, requested_value=requested, default_value=default,
    stock_comparison=requested == default)
supply = gate.evaluate_define_supply_effectuation(
    captured, request=request, cxx="c++", cmake="cmake")
meaning = gate.evaluate_define_runtime_meaning(
    captured, request=request, declaration=None, cxx="c++")
```

   - supply、meaning の `canonical_json()` をそのまま保存。
   - 4 軸完了後、同じ module の record で `require_condition_gate_family(..., use_class="raw-measurement")` を呼び、canonical JSON を保存。
   - 一部 cell しか選択しなかった組は full-arm admission を報告しない。

7. **plain build**
   - 主試作で S と phase1 を各 1 回、別 build directory で構成する。
   - `ycsb_ss2pl.exe` を build。
   - `_target_compile_entries`、`_validate_compile_definitions`、cache、binary hash、実効 warning flags を保存。
   - S の `wfg.cc` object が compile されたことも記録。
   - condition admission と plain build 成功は別欄にする。trial は実行しない。

8. **abort 対照**
   - 主試作の全 cell と build の後、redesigned clone から主 patch を reverse apply し、無条件除去版を apply。
   - 前後の source/patch hash と 2 版の差分を保存し、capture を取り直す。
   - T−/S の 4 cell と abort 所有権検査を実行。
   - この版の build は未実施として明記する。主版の binary をこの版の build 結果として扱わない。

各 cell に `expected_reason`、`observed_reason`、経過秒、patch/registry/staging ID、canonical record の所在を持たせる。通常の gate red は実験結果であり、probe 内部エラーと区別する。最上位例外・予算打切りでも、前 wave と同じ atomic replace 方式で途中結果を残す。

所要は供給評価 1 要求につき最大で configure 2 回＋前処理 2 回。meaning は declaration がないので前処理を増やさない。ただし compiler/CMake identity、依存 hash の費用もある。最初の数 cell で実測所要を更新する。

残り時間が不足した場合は、重複する T± 非 KIND、O の試作非 inert の重複確認の順に落とす。pristine/warm 対、KIND の T± 対、DLR の現行/試作対、plain build と runner 契約を優先する。未完了 cell を緑で補完しない。

**7. selftest・login 前検査・投入形**

selftest は tmp を必要としない合成 bytes と辞書で構成する。

- 許可 target/companion 差分を受理。
- 登録簿外の 1 byte 変更を拒否。
- 非 SS2PL spec の変更を拒否。
- matrix の ID 一意性、全基本 cell 数 96、予測 reason の既知集合、推奨選択数を検査。
- pristine cell が warm-up より前になる順序を検査。
- 不正 cell ID を拒否。
- 合成 source の `#if 0` 内増分も abort token 走査に数えられることを確認。

親は次の順で実行する。

```text
python3 -B <job-dir>/probe/t2737_gate_probe.py --repo-root <repo> --selftest
python3 -B <job-dir>/probe/t2737_gate_probe.py <必要引数> --cells login-precheck
```

`login-precheck` は clone/apply、Python 契約検査、configure、前処理だけを行う。warm-up、build、trial は呼ばない。永続 cache を使う場合は `staging_state=preexisting` と記録し、pristine の証拠に数えない。

S の bytes 比較は主試作/T−/IMPL=0 の gate record を取得したうえで、追加診断として patched/stock を同じ共通 configure_args で configure し、tpcc の transaction entry を各 1 件選ぶ。compile argv から `-c` と出力指定を除いて `-E -P` を付け、両 stdout を保存して `cmp` する。

この最小試作では不一致を予測する。差分の先頭、共通 header の宣言、transaction 各関数、root path の差を記録する。診断のために空白を除去した結果を gate の bytes 一致として扱わない。

投入形は以下。

```text
python3 tools/pegasus/dispatch_compute.py \
  --task generic --walltime 00:30:00 -- \
  python3 -B <job-dir>/probe/t2737_gate_probe.py \
  --repo-root <投入worktreeの絶対path> \
  --patch-current <現行patchの絶対path> \
  --patch-redesigned <主試作patchの絶対path> \
  --shadow-root <job-dir>/shadow \
  --scratch-root <job-dir>/scratch \
  --gflags-prefix /work/1/SFC/tanab/ss2pl-study-deps/gflags-install \
  --glog-prefix /work/1/SFC/tanab/ss2pl-study-deps/glog-install \
  --thirdparty-root <専用pristine-staging> \
  --jobs 48 --output <結果JSONの絶対path> --cells recommended
```

abort 対照版は主試作と同じ directory の固定名から取得し、その存在と hash を開始時に検査する。generic dispatch の clean env を前提に、依存設定は全て引数で渡す。runner は実ファイル位置から `ROOT` を `sys.path` に追加する。

**8. insight の表と結論の境界**

詳細 matrix は次の形にする。

| cell | patch sha | 登録簿 | staging | arm/軸 | requested/default/companion | owner target | 予測 | supply 実測 | meaning | 秒 | receipt |
|---|---|---|---|---|---|---|---|---|---|---|---|

裁定用には以下の 1 表に集約する。

| 案・比較 | 成立した比較 | 成立しない比較 | 必要な変更層 | 費用・隙間 | 証拠 |
|---|---|---|---|---|---|
| (iii) warm-up | pristine→warm で前処理到達が変わった範囲 | target 不在、companion 警告、argv/閉包/bytes 差 | runner の準備手順候補 | staging の共有に依存。warm-up だけでは admission を保証しない | 対 cell |
| (ii) IMPL/DLR/WFG | 試作で green になった非 inert 比較 | S の残差、B/D | patch | DLR2/IMPL0 は scope 外。plain build と意味の成立は別 | 現行/試作対 |
| (ii) KIND | companion ありの非 inert 比較 | companion ありの S、なしの非 inert | 登録簿と軸設計。runner への波及は未裁定 | 直交性の要求が残る | T+/T− |
| (ii) inert stock 比較 | tpcc の owner entry を解決できた範囲 | ycsb stock 対照、最小試作の bytes 一致 | 登録簿＋patch | **tpcc を認証しても実測 YCSB TU の認証にならない** | O/T 対 |
| abort 条件化 | workload 別の増分位置を再現した範囲 | runner の raw source 所有権検査 | patch＋runner 契約 | 条件化版が静的検査を破る。両版 red なら abort 単独の因果は証明できない | 2 版対 |

採否は書かない。「必要な比較が全部成立した」「runner が動く」とも書かない。特に phase1 の 4 軸 gate は、phase1 の全 define を同時に入れた TU の比較ではなく、runner と同じ個別軸比較である。

残る確認点は次のとおり。

- `c++` が計算ノードで前 wave と同じ実体に解決されるか。PATH 名だけで同一としない。
- include guard の残渣が 0 byte か、既存 pragma の出力が同じか。compiler ごとに記録する。
- root-location-only は「残差なし・置換 1 回以上・code-owned dependency の root builtin あり」を全て要求する。bytes 完全一致なら不要。
- 閉包の `root_dependent_builtin_paths` と実際の出力 path を保存し、単なる path 正規化で不一致を隠さない。
- 無条件 include による S の出力増加と、IMPL 間の閉包固定が両立するか。
- shadow の相対 import と patch 解決先が意図した実体か。
- stock companion の configure 失敗を owner 不在と誤分類しない。
- 30 分内に全 cell が終わらなければ、完了範囲・未実施 cell・未証明の比較を明記する。