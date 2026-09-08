## 変異 m01〜m13 の殺傷力

- **m01 — 殺せる。** `test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned` の `orchestrator/tests/test_backoff_extended_sweep.py:506` が、`(2000, 4000, 9998)` と literal `(2000, 4000, 9999)` の不一致で赤になる。
- **m02 — 殺せる。** 同 test の `:520-524` が、生値 `(2000, 4000, 9999)` と wire 値 `(4000, 6000, 11999)` の不一致で赤になる。run-path の `:1371-1375` も赤になる。
- **m03 — 殺せる。** 同 test の `:510-512` が、T2266 の `"descriptive_backoff_shape_only"` と T2418 literal の不一致で赤になる。
- **m04 — 殺せるが assert ではなく error。** 同 test の disclosure 構築 `:553-562` が `KeyError` になり、`:563` の assert へ到達しない。欠落自体は確実に検出する。
- **m05 — 殺せる。** `test_t2418_run_path_uses_exact_five_genomes_and_shared_campaign_call` の `:1382` が T2266 slug を拒否する。`:1384-1385` の scale/trial も不一致になる。
- **m06 — 殺せる。** `test_t2418_prebuild_requires_five_distinct_trace_disabled_binaries` の `:1080-1093` で重複 SHA が例外を出さず、`pytest.raises` が赤になる。`test_t2418_binary_identity_rejects_incomplete_or_malformed_bindings` の最初の負例 `:1118-1119` も赤になる。
- **m07 — 殺せる。** run-path test の `:1386` が `PerfConfig.reps == 4` を literal `5` と比較して赤になる。
- **m08 — 殺せる。** `test_b10_run_kind_routes_t2418_through_job_submit_and_finalizer` の `:1637` が job の `case` literal 欠落で赤になる。
- **m09 — 殺せる。** 同 test の `:1652` が finalizer 内の `"len(commits) != 5"` 欠落で赤になる。
- **m10 — 殺せる。** 同 test の `:1644-1647` が submitter の T2418 転送条件と exact 不一致になる。
- **m11 — 殺せるが意図した assert ではない。** run-path test は `:1334-1336` で `total=5, committed=4` を返すため、未完走時に materializer を呼ぶ変異は `:1339-1346` の `run_workload` 中に予期しない例外となる。ただし事前登録で想定した CLI test `:1411-1447` は `run_workload` を stub しており、この呼出条件を観測していない。
- **m12 — 殺せない。** report test は `:681-683` で materializer が返したパスをそのまま読むため、T2266 stem へ変えても通る。CLI test の `:1419-1423` は正しい名前を手組みしており、production materializer を通らない。最小追加は `Path(paths["dat"]).name` と `Path(paths["json"]).name` を T2418 literal に exact 比較する assert。
- **m13 — 指定どおりの一箇所変異では殺せない。** `backoff_extended_sweep.py:855` の `tuple(tps)` を単に `tps` に変えても、凍結入力の `tps` は既に tuple であり、比較相手も `:860` で tuple 化されるため結果が変わらない。最小追加は list-form `tps` を直接 `reps_for` に渡す正例。一方、過去事故そのものに相当する「`:860` の capture 側 tuple 化を外す」変異は現行の凍結-view test が殺せる。

## 恒真な assert

T2418 の反復数・時間について、期待値を `p2_2.REPS` / `p2_2.EXTIME` から作る箇所は残っていない。`test_backoff_extended_sweep.py:517-518` は共有定数そのものを literal `5` / `3` に固定し、run-path は `:1386-1387`、report は `:704-705` と各 point の `:720` で独立 literal を使っている。

ただし次は生産機構の独立 oracle ではない。

- `:1059-1060` の build 数・SHA 数は、5 genome と「canonical ごとに固有 SHA を返す」stub が既に含意している。validator の実効性は後続の重複・欠落・不正型テストが担っている。
- T2418 fixture は `:314` で production の `t2418_genomes` から候補を作り、loader も `backoff_extended_sweep.py:1016-1020` で同じ生産関数から expected を作る。この report test 単体では誤った5点集合も自己整合するが、別の literal projection `:520-524` が補っている。
- CLI test `:1411-1447` は `run_workload` を stub し、report を手組みするため、materialization の完走 guard と stem を通らない。
- shell routing test `:1628-1656` は `bash -n` と source literal の照合であり、`case`、qsub 環境転送、finalizer を実行してはいない。登録済み m08〜m10 は殺せるが、機構全体の実行証明ではない。
- run-path test `:1310-1389` は prebuild と `run_campaign` を stub している。配線検査としては有効で、SHA gate 自体は `:1022-1150` の別テストが通している。

## 凍結 view の実通し

要件を満たしている。`_t2418_certified_view` は `test_backoff_extended_sweep.py:369` で実際に `artifact_admission._immutable_records` を通し、report test は `:668-671` で `tps` が tuple、`leading_indicators` が `MappingProxyType` になったことを exact に確認している。その view を `:681` から production の capture・loader・materializerへ渡している。

したがって、過去の `list == tuple` 欠陥を再現する capture 側の正規化欠落は検出できる。ただし m13 の記述どおり incoming `tuple(tps)` だけを外す変異は、上記のとおり凍結入力上で等価になる。

## 既存挙動の非変更

差分上、`EXTENDED_SWEEP_US`、全 `T2266_*` 定数、codec、`_require_distinct_static_binary_hashes`、`WORKLOADS`、`MEASUREMENT_SEEDS` に変更はない。

`_prebuild_backoff_binaries` は末尾に default-false の `require_all_t2418_binary_hashes` を追加しただけで、既存引数と `require_all_binary_hashes` の式・T2266 呼出条件は維持されている（`backoff_extended_sweep.py:321-327,363-366,1415-1416`）。

`run_campaign` 呼出しは `backoff_extended_sweep.py:1423` の1か所だけ。差分の `diff --git` は以下の4ファイルだけで、禁止 file は含まれない。

- `orchestrator/campaign/backoff_extended_sweep.py`
- `orchestrator/tests/test_backoff_extended_sweep.py`
- `tools/pegasus/b10_backoff_grid.sh`
- `tools/pegasus/submit_b10_backoff_grid.sh`

## 要件 1〜7 の充足

1. T2418 専用 SHA gate と prebuild 配線は充足している。
2. `declared_use_class` / `reps` / `extime_s` / `records` / `threads` は search config（`backoff_extended_sweep.py:632,649-652`）、JSON（`:1152,1164-1167`）、`.dat` provenance（`:1258,1270-1273`）の3か所にある。
3. run-path の flags・identity・5/3 と report の disclosure・rep 数は独立 literal で固定されている。
4. report test は実際の凍結 view を通している。
5. T2418 view の T2266 consumer 拒否は `test_backoff_extended_sweep.py:743-759` で検査されている。
6. `run_campaign` は1か所のまま。
7. `_require_distinct_t2418_binary_hashes` は指定された全拒否条件を実装し、`:1113-1116` に通る正例、`:1118-1150` に長さ・型・trace・genome 束縛・SHA形式・重複・相異数の負例がある。

実装自体は7項目を満たすが、受入テストには m12 と、字面どおりの m13 に上記の穴がある。

## must-fix

- **主張:** m12 が生存し、専用 artifact stem をテストできていない。**場所:** `backoff_extended_sweep.py:1247,1506`、`test_backoff_extended_sweep.py:681-683,1419-1423`。**成り立たなくなる条件:** materializer の stem だけを `t2266-backoff-static-tail-*` に変更した場合。**成果物への影響:** 完走した探索 report がT2266名で残る一方、CLI/PBS はT2418名を見つけられず投入を失敗扱いにする。**最小の是正:** report test に返却された `.dat` / `.json` の basename を独立 T2418 literal と比較する2 assertを追加する。

## nit

- **主張:** m13 の事前登録位置が過去欠陥を再現していない。**場所:** `backoff_extended_sweep.py:855,860`、`test_backoff_extended_sweep.py:668-671`。**条件:** incoming `tuple(tps)` だけを外し、capture 側 tuple 化を残した場合。**最小の是正:** list-form bench の正例を追加するか、今後の変異定義では capture 側の tuple 化を対象にする。
- **主張:** m11 は意図した CLI oracle ではなく、予期しない例外で偶発的に殺される。**場所:** `test_backoff_extended_sweep.py:1334-1346,1411-1447`。**条件:** 未完走 materialization が将来 no-op 化された場合、現在の直接的な非呼出契約は失われる。**最小の是正:** materializer を spy に差し替え、4/5では0回、5/5では1回を assert する。
- **主張:** T2418 の positive prebuild assert は stub の構成を再確認しているだけ。**場所:** `test_backoff_extended_sweep.py:1033-1060`。**条件:** gate が成功入力を検査せず返しても両 assert は通る。**最小の是正:** 現状の負例を主たる oracle と明記するか、冗長な2 assertを削って `:1116` の「例外なし」を正例として扱う。

## 総括

must-fix は1件。実装された探索経路と要件1〜7は静的には成立しているが、m12 は明確に生存し、m13 は事前登録された字面どおりでは凍結入力上の等価変異になる。m01〜m10は殺せ、m11も別 test の例外で殺せる。本レビューではテストを実行しておらず、緑とは判定していない。