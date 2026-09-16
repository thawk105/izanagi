## 前提の検算

P1〜P3 を採用する。修正対象は `cache_key` の省略条件と、その回帰テストに限定できる。以下の行番号は HEAD `0c292eff6f39d797afac7481b89c94de43c07386` 基準。指定された７ファイルはすべて読めた。編集・pytest・probe は実行していない。

| brief の事実 | 検算結果 |
|---|---|
| 1. 可変 DEFAULT との比較 | 一致。`buildcache.py:622` が既定組、`:627` が key 関数の定義時既定、`:639` が呼出時の module global との比較。 |
| 2. production caller | s1 `:390`、s2 `:354-355`、s3 `:258`、s5 `:293` は cc/cxx を渡さない。pipeline `:1945→:2002`、backoff_profile `:273,:307→:857`、pegasus_floor_scoping `:214→:218` は site compiler を明示する。**between_run_floor `:316-323` は Pegasus 分岐だけ** site 解決し、それ以外は既定引数を使う。T2187 の直接 key 呼出 `:3925,:4346` も確認。 |
| 3. admission と hit | 概ね一致。ただし条件付き。`build_admission.py:633-675` の stock receipt は nonce・compiler 名を直接含まないが、`source_digest.py:249-260` の `source_bytes_sha256` を含む。compiler が preprocess 結果を変えれば receipt も変わり、衝突しない。両相の receipt 一致を実測する必要がある。hit 検査は `buildcache.py:3474-3512`、publish 競合拒否は `:3585`。 |
| 4. module global だけの monkeypatch | 一致。`build()` の省略引数は `:3411` で束縛済み。実編集後に新 Python process を起動する必要がある。回帰テストでは cc/cxx を明示する。 |
| 5. golden・既存 fake | golden を使うテストは `test_campaign.py:11177-11197`。**定義位置は `:11040-11042`、要素数は１**。compiler 分離テスト `:3184-3202`、fake `test_build_site_gate.py:290-331` は一致。 |
| 6. host・compiler | 本調査でも `pegasus02`、`g++-13` 不在、`g++-12` 12.3.0、`g++` 11.4.0 を確認。`_run` の拒否は `buildcache.py:3795-3796`。T2000 RESULT は３投入とも本走未到達と記す。 |
| 7. 編集面重複 | T548 の４ worktree、T2237 の１ worktreeについて、対象３ファイルが main と byte 一致。T548 の実 branch 名 `worktree-dev-wave-t548-versioned-dep-procurement` の main との差分にも対象３ファイルはない。作成時刻の前後関係は今回再検証していない。 |

実 checkout の HEAD は `511c9538e4e8efa54b45cda62e72389ed3b706ec`、status は空。`pin.py:28` の `CURRENT_PIN` は **`"511c953"`**。stock admission は文字列の完全一致を要求するので、probe の `ccbench_commit` は full SHA ではなく `CURRENT_PIN` を渡す。

M4（`package.md:91` 以降）の legacy 限定という結論は現物と整合する。ただし「既定変更で必ず偽 hit」ではなく、genome・commit・trace・source/admission 等の他の key 入力が一致する場合の欠陥である。

## 単位 P (再現 probe) の仕様

配置先は repo 外の次のファイルとする。

```text
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key/t785_legacy_cache_probe.py
```

CLI：

```text
python3 -B t785_legacy_cache_probe.py \
  --repo <絶対repoパス> \
  --cache-root <job内の専用cache絶対パス> \
  --phase seed|hit \
  --expect miss|hit \
  [--seed-json <同じ試行のseed.json>]
```

JSON は stdout、診断は stderr。`--expect` 不一致は JSON を出したうえで非ゼロ終了する。seed は専用 cache が空であることを要求し、hit 相は同じ root を再利用する。修正後も相の名前は `hit` とし、期待値を `miss` にする。

処理を次のように固定する。

1. `--repo` を import path の先頭に置き、import した `buildcache`・`source_digest`・`build_admission` の実 path がその repo 内であることを確認する。
2. 各相を別 process で起動する。`inspect.signature(buildcache.build)` から cc/cxx の既定値を取得し、module の `DEFAULT_*` と一致することを確認する。
3. genome は `Genome("silo", {"BACK_OFF": 1})`、`trace=False`、commit は `pin.CURRENT_PIN`、checkout は `<repo>/external/ccbench`。`jobs=1`、`site` は指定しない。
4. `source_digest.resolve_evidence(..., ccbench_dir=str(sub), cxx=build_cxx_default)` を呼ぶ。**固定の `"g++"` や未指定にはしない。** `buildcache.py:3644` の再検証も build の cxx を使うので、それと揃える。
5. `build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)` と `derive_build_admission(context, evidence)` を実行する。`STOCK_BASELINE`、`src_token=="stock"`、`tracked_clean is True` を確認する。
6. `buildcache._run` だけを差し替えて、production `build()` を呼ぶ。

呼出形は次を基本とする。

```python
result = buildcache.build(
    genome,
    ccbench_commit=pin.CURRENT_PIN,
    trace=False,
    cache_root=str(cache_root),
    ccbench_dir=str(sub),
    jobs=1,
    admission=admission,
    build_context=context,
    source_evidence=evidence,
)
```

**cc/cxx は渡さない。** source 検証、admission、sidecar、trace diff、nm、copy/publish は差し替えない。

差し替え `_run` は configure/build の２種類だけを受理する。

- configure：argv を記録し、`-B` と `-DCMAKE_CXX_COMPILER=` を抽出する。その compiler で固定の極小 C++ を実コンパイルし、`<staging>/cc/silo/ycsb_silo.exe` に置く。
- ソース例は `#include <cstdio>` と `int main(){std::puts(__VERSION__);}`。`-x c++ - -O0 -o <binary>` で stdin から渡す。`__VERSION__` により compiler 差を binary にも残す。実行はしない。
- build：対応する configure があり、同じ staging に実 ELF が存在することを確認して記録する。cmake は起動しない。
- その他の呼出は失敗させる。`finally` で `_run` を元に戻す。

必要な JSON field：

| field | 内容 |
|---|---|
| `phase`, `expected_cached`, `observed_as_expected` | 相と期待判定 |
| `repo`, `repo_head`, `module_paths`, `buildcache_source_sha256` | import・編集対象の識別 |
| `defaults`, `build_signature_defaults` | module の `DEFAULT_CC/CXX` と定義時既定 |
| `ccbench_root`, `ccbench_head`, `requested_commit`, `genome`, `trace` | 実入力 |
| `source_evidence`, `admission_provenance`, `admission_receipt_sha256` | 実 evidence と admission |
| `cache_root`, `cache_key`, `build_dir`, `cached` | key は production `cache_key` の値と build_dir basename を照合 |
| `configure_argv`, `configure_compilers` | `BuildResult` が報告する compiler |
| `run_calls` | 差し替え `_run` の順序、`what`、argv、site。hit なら空 |
| `compile_calls` | 実コンパイル argv、要求 compiler、終了コード |
| `requested_compiler_versions` | cc/cxx の `--version` １行目と解決 path |
| `binary`, `binary_sha256`, `result_bin_sha256` | 独立計算 SHA-256 と result の一致 |
| `elf_comment` | `readelf -p .comment <binary>` の版文字列 |
| `seed_comparison` | seed との evidence、receipt、key、binary SHA の一致・不一致 |

stock の条件は `build_admission.py:633-635` の３条件に加え、実 evidence の検証と `:627` の trigger predicate 検査を通ること。clean は `source_digest.py:2307-2334` 上、tracked file の clean を意味し、untracked は除外される。

両 compiler の `source_bytes_sha256`／receipt が異なる場合は「衝突条件不成立」と記録する。receipt を固定したり検査を stub 化したりして再現を捏造しない。

## 親の実編集・復元手順

以下は親が実行する手順であり、本段では実行していない。開始時に対象ファイルと index が clean、同ファイルへの他者編集がないことを確認する。

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t785-legacy-cache-key
git status --short
git diff --exit-code
git diff --cached --exit-code

task_job=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key
task_trial=before
task_cache="$task_job/cache-$task_trial"
```

実編集用の shell 関数を、その親 shell 内で定義する。

```bash
set_probe_defaults() {
  python3 -B - "$1" "$2" <<'PY'
import pathlib, re, sys
p = pathlib.Path("orchestrator/campaign/buildcache.py")
data = p.read_bytes()
pattern = rb'^DEFAULT_CC, DEFAULT_CXX = "[^"]+", "[^"]+"$'
replacement = (
    f'DEFAULT_CC, DEFAULT_CXX = "{sys.argv[1]}", "{sys.argv[2]}"'
).encode()
updated, count = re.subn(pattern, replacement, data, flags=re.M)
assert count == 1
p.write_bytes(updated)
PY
}
```

編集後の検査も関数化してよい。`--stat` だけでは１行変異を証明できないため、byte 比較を併用する。

```bash
check_probe_defaults() {
  git diff --stat
  git diff --numstat
  git diff --unified=0 -- orchestrator/campaign/buildcache.py
  python3 -B - "$1" "$2" <<'PY'
import pathlib, subprocess, sys
name = "orchestrator/campaign/buildcache.py"
head = subprocess.check_output(["git", "show", "HEAD:" + name])
old = b'DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"'
new = f'DEFAULT_CC, DEFAULT_CXX = "{sys.argv[1]}", "{sys.argv[2]}"'.encode()
assert head.count(old) == 1
assert pathlib.Path(name).read_bytes() == head.replace(old, new, 1)
assert subprocess.check_output(
    ["git", "diff", "--name-only"], text=True
).splitlines() == [name]
assert subprocess.check_output(["git", "diff", "--cached", "--name-only"]) == b""
PY
}
```

期待する diff は１ファイル、１ insertion・１ deletion。

```bash
set_probe_defaults gcc-12 g++-12
check_probe_defaults gcc-12 g++-12

python3 -B "$task_job/t785_legacy_cache_probe.py" \
  --repo "$PWD" --cache-root "$task_cache" \
  --phase seed --expect miss > "$task_job/$task_trial-seed.json"

set_probe_defaults gcc g++
check_probe_defaults gcc g++

python3 -B "$task_job/t785_legacy_cache_probe.py" \
  --repo "$PWD" --cache-root "$task_cache" \
  --phase hit --expect hit \
  --seed-json "$task_job/$task_trial-seed.json" \
  > "$task_job/$task_trial-hit.json"
```

各 command の失敗時も復元へ進むよう、親の実行 wrapper は `try/finally` または shell trap を設ける。復元前にも「変更は上記１行だけ」を確認し、想定外の変更があれば上書きしない。

```bash
git checkout -- orchestrator/campaign/buildcache.py

python3 -B - <<'PY'
import pathlib, subprocess
name = "orchestrator/campaign/buildcache.py"
assert pathlib.Path(name).read_bytes() == subprocess.check_output(
    ["git", "show", "HEAD:" + name]
)
PY

git diff --exit-code
git diff --cached --exit-code
git status --short
```

修正後は **F を含み、DEFAULT が `gcc-13/g++-13` の HEAD** を基準に同手順を繰り返す。未 commit の F を `git checkout --` で消さないこと。`task_trial=after` と専用の新 cache root を使い、hit 相の `--expect` だけ `miss` に変える。

| 観測 | 修正前 seed | 修正前 hit | 修正後 seed | 修正後 hit 相 |
|---|---|---|---|---|
| 要求 cxx | g++-12 | g++ | g++-12 | g++ |
| `cached` | false | true | false | false |
| `_run` | configure/build | ０回 | configure/build | configure/build |
| key | K0 | K0 | K12 | K11 ≠ K12 |
| binary SHA | B12 | B12 | B12′ | B11 ≠ B12′ |
| `.comment` | 12 系を含む | 12 系が残る | 12 系を含む | 11 系を含む |

`.comment` は複数行になり得るため、単一文字列への完全一致では判定しない。修正前の核心は「新しい configure compiler を報告しながら、seed binary をそのまま返す」こと。

## 単位 F (修正) の差分案

`orchestrator/campaign/buildcache.py:635-639` を次のように変更する。

```diff
-    既定ツールチェーンは省いて旧キーを温存 (src_token と同型の後方互換規則)。"""
+    歴史的ツールチェーン ("gcc-13", "g++-13") だけは省いて旧キーを温存する。
+    この省略条件は DEFAULT_CC/DEFAULT_CXX から独立させ、既定変更後の
+    新ツールチェーンが歴史的キーへ衝突することを防ぐ。"""
 ...
-    tc = "" if (cc, cxx) == (DEFAULT_CC, DEFAULT_CXX) else f"|cc={cc}|cxx={cxx}"
+    tc = "" if (cc, cxx) == ("gcc-13", "g++-13") else f"|cc={cc}|cxx={cxx}"
```

現行 DEFAULT はこの literal 組と等しい。したがって、現行状態のすべての正規入力について旧・新の条件式の真偽が同じで、`tc`、raw pre-image、SHA-256、返却 key が byte 単位で同じになる。省略引数の束縛も変更しない。admission の型検査と他の軸はそのままである。

この主張は、runtime で DEFAULT を別値へ差し替えた状態を含まない。その状態で動作を変えることが修正の目的である。

## 回帰テスト案

追加位置は `test_campaign.py:3202` の直後、variant_id 節の前。既存期待値は変更しない。

1. **`test_cache_key_default_changes_do_not_alias_toolchains`**

   同一 genome・commit・admission で、明示 compiler 組ごとの key を取得する。DEFAULT を順に歴史的組、`gcc-12/g++-12`、`gcc/g++` へ monkeypatch し、各組を明示して再計算する。

   ```python
   assert keys_after_default_change == keys_before_default_change
   assert len(set(keys_for_each_requested_default)) == 3
   ```

   `trace=False/True` と stock/non-stock token を parameterize する。修正前は DEFAULT と一致した組だけ suffix が消え、固定組の key 不変 assertion が失敗する。修正後は両 assertion が成立するはずである。

2. **`test_cache_key_preserves_historical_toolchain_preimage`**

   独立に raw pre-image を組み立てて期待 key を計算する。省略対象は literal の歴史的組だけにする。

   対象組：

   ```text
   gcc-13 / g++-13
   gcc-12 / g++-12
   gcc    / g++
   gcc-12 / g++-13
   gcc-13 / g++-12
   ```

   stock/non-stock と trace 両値を検査し、各 `cache_key(...) == expected` を assert する。historical 組では cc/cxx 省略呼出も同じ期待値になることを検査する。これは現行互換性と、片側 compiler だけを比較する誤修正を覆う。

3. **`test_cache_key_separates_each_compiler_request_name`**

   cc だけ違う組、cxx だけ違う組を parameterize し、それぞれ key が異なることを assert する。既存 `test_cache_key_separates_compiler_request_name` は残す。

hit 経路の新しい fake テストは追加しない。単位 P が実 admission・実 filesystem・実 compiler で hit を検証し、既存 legacy hit テストもある。

`_fake_legacy_build` は `_run` に加えて commit 検査と source_digest 一式を stub 化し、ELF ではない bytes を書く。今回の再現の代わりにはならない。

## 変異 matrix の事前登録候補

対象は F 後の `buildcache.py:639` 相当。１変異ずつ適用し、元に戻して次へ進む。

| 変異 | 期待 KILLED node |
|---|---|
| 比較対象を `(DEFAULT_CC, DEFAULT_CXX)` に戻す | `test_cache_key_default_changes_do_not_alias_toolchains` |
| `tc = ""` にする | 同上、および `test_cache_key_separates_each_compiler_request_name` |
| 常に toolchain suffix を付ける | `test_cache_key_preserves_historical_toolchain_preimage`、既存 golden テスト |
| 歴史的組を `gcc-12/g++-12` に替える | `test_cache_key_preserves_historical_toolchain_preimage` |
| `cc == "gcc-13"` だけで省略する | 同上の `gcc-13/g++-12` case |
| `cxx == "g++-13"` だけで省略する | 同上の `gcc-12/g++-13` case |
| 非省略 suffix から cc を落とす | `test_cache_key_separates_each_compiler_request_name` の cc 差 case |
| 非省略 suffix から cxx を落とす | 同上の cxx 差 case |

ここでの KILLED は事前期待であり、実測結果ではない。各 node は先に無変異で通ることを確認し、import error や実行環境エラーを KILLED に数えない。

## 焦点テスト集合と影響範囲

production の legacy 入口は次のとおり。

| consumer | 呼出位置・形 |
|---|---|
| `pipeline.py` | `:2002`。site 解決または caller 指定 compiler を渡す |
| `backoff_profile.py` | `:857`。runtime.cc/cxx |
| `between_run_floor.py` | `:324`。Pegasus 分岐は明示、それ以外は省略 |
| `pegasus_floor_scoping.py` | `:218`。site 解決組 |
| `s1_verify_extime_calibration.py` | `:390`。省略 |
| `s2_verify_calibration.py` | `:354-355`。省略 |
| `s3_lock_coverage.py` | `:258`。省略 |
| `s5_permutation_coverage.py` | `:293`。省略 |
| `tools/pegasus/probes/t2187_adaptive_const_probe.py` | build `:3941,:4334`、直接 key `:3925,:4346`。同じ明示 cc/cxx |
| `tools/pegasus/probes/t1683_rr5_cost_probe.py` | `:248`。明示 cc/cxx |
| `orchestrator/manual_probes/test_t2000_legacy_build_probe.py` | `:1876`。手動実 probe |

検索で `cache_key` の別名 import は見つからなかった。

直接 key／legacy build を扱う主要テストは以下の６ファイル。

- `test_campaign.py`
- `test_build_site_gate.py`
- `test_buildcache_v2.py`：legacy sidecar、fresh/hit、namespace 分離も含む
- `test_p3_s4_loop.py`
- `test_p3_s4_loop_sort.py`
- `test_real_repo_serialization.py`

consumer を介する確認対象は `test_t2187_adaptive_const_probe.py`、`test_backoff_profile_pegasus.py`、`test_between_run_floor.py`、`test_pegasus_floor_scoping.py`。これらには build stub があるため、通過しても実 hit の証拠とはしない。

`test_s1_verify_extime_calibration.py`、`test_s5_permutation_coverage.py`、`test_pegasus_calibration_workload.py`、`test_ccbench_spawn_sites.py` には source 文字列の順序・呼出面検査もある。単純な grep hit を実 key テスト数に数えない。

再走は次の順でよい。

1. 新規３テスト、既存 cache_key ２テスト、既存 golden node。
2. 上記主要６ファイルと consumer 確認４ファイル。
3. 変異 matrix。各変異に対応する node に絞る。
4. 親の既定 acceptance と既存の完了検査。

実行入口は `python3 tools/run_tests.py <対象>` とし、pytest を直接起動しない。build_v2 不変の焦点 node は既存 `test_v2_toolchain_version_change_is_cache_miss`（`:2302`）と `test_v2_never_hits_legacy_entry`（`:2879`）。

## 対案 A との比較

A は `tc = f"|cc={cc}|cxx={cxx}"` とする案。

| 項目 | P1 | A |
|---|---|---|
| 歴史的 `gcc-13/g++-13` | key 不変 | pre-image が変わる |
| 現行の非歴史的 compiler 組 | key 不変 | key 不変 |
| DEFAULT の将来変更 | 新組を key に含める | 同左 |
| 現行 golden 値の変更 | ０件 | １件 |
| 既存の固定 golden assertion | 変更０ node | 静的に変更が必要な１ node |
| cache の再利用 | 現行 entry を維持 | 歴史的組の entry が新 key から参照されなくなる |

数えた golden は `_T816_GOLDEN_CK0` の１要素、`silo_2b19d78065_t0`。参照は `test_campaign.py:11193` の１か所。古い `_PRE_T343_GOLDEN_CK0` と `_T343_GOLDEN_CK0` は過去値なので書き換えない。`_GOLDEN_VID` の８値も影響しない。

既存の他の key テストは主に相対比較・動的 key 計算であり、固定 golden の更新箇所は増えない。ただし、全テスト未実行なので「失敗は必ず１ node だけ」とは断定しない。

cache の現物は、**本 worktree の既定 root `external/ccbench/build-variants` が存在せず、その root 内の対象 entry は０件**。caller 指定 root、他 worktree、計算ノード上の cache の総数は未集計である。したがって「legacy cache を全無効化」は訂正すべきで、A の影響数は「全 root にある歴史的組の entry 数」。非既定組の entry は変わらない。

## リスクと未確定点

- **source digest の compiler 間一致は未実測。** stock token が同じでも receipt の source bytes digest が違えば衝突しない。単位 P の両相で確認する。
- **probe の証明範囲。** 実 buildcache・admission・検査・実 compiler の組合せによる偽 hit を証明する。ccbench 全体の cmake build 成功や性能は証明しない。
- **site 解決。** `compilers_for_current_site()` は `buildcache.py:1861-1865` で compute だけ `gcc/g++`、それ以外は DEFAULT。P1 によって現在の両組の key は不変。probe からはこの関数を呼ばず、build の省略引数経路を再現する。
- **caller の追加前提。** s1/s2/s3/s5 は source evidence 側にも別途 `"g++-13"` の既定がある。DEFAULT の実編集だけで各 CLI 全体が必ず動くとは主張しない。今回の probe は evidence の cxx を build の定義時既定へ明示的に揃える。
- **build_v2 への波及なし。** `_v2_identity` は `buildcache.py:1319-1328` で cc/cxx と toolchain hash を独立に含み、legacy `cache_key` を使わない。floor の実入口は `s8b_floor_campaign.py:4694,:7340-7342` で build_v2 を選ぶ。`:20` の legacy build 記述は現行の呼出実体を表していない。
- **同名 compiler の更新。** PATH・symlink・compiler version が変わって要求名が同じ場合は、この修正の対象外。
- **復元事故。** post-fix 再現は F を含む clean HEAD を基準に行う。同時編集を検出したら `checkout` で消さない。

キャッシュ列挙用の読み取り Python は自動レビューに拒否されたが、単純な `ls -ld` で既定 root の不在を確認できた。追加承認は不要だった。

## 総括

P1 の literal 組への切離しを採用する。現行 key・golden を維持しながら、将来の DEFAULT 変更による省略対象の移動を止められる。

実施順は、単位 P 作成 → 親の実編集による偽 hit 実測 → 復元 → F と回帰テスト → 新 cache で同手順の miss 実測 → 変異 KILLED 確認。現段階では静的検算のみ完了しており、再現成功・テスト緑・KILLED は未確認である。