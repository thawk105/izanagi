# [T-785] 段 4 裁定 — plan v2 と変異事前登録

基準: wave worktree HEAD `0c292eff6f39d797afac7481b89c94de43c07386`。入力 = `s1-brief.md` (段 2 後追記込み)、`artifacts/dev-wave-t785-legacy-cache-key/s2-plan.md`、`s3-a.md` (sol)、`s3-b.md` (luna)。
段 4 直前の再走査: wave 開始後に main へ入った裁定は D2064 (throughput field 改名)・D2065 (到達不能 object) の 2 件で本件と無関係。`docs/dev-wave/mutation.md` の変更は「変異 `--spec` も checkout 外必須」で、段 6 の変異走行に適用する。対象 source (`buildcache.py`・`source_digest.py`・`build_admission.py`・`test_campaign.py`) は main 側で未変更。

## 1. 所見の裁定

| ID | 裁定 | 採否 | 扱い |
|---|---|---|---|
| S-1 / L-4 前半 | real (親が `pipeline.py:1991-2006` を現物確認: legacy 分岐は cc/cxx を渡さず定義時既定を使う。compiler を載せた `common` は build_v2 分岐だけ) | 採用 | 記録の caller 表を訂正。コード変更なし |
| L-4 後半 | real (`s1_verify_extime_calibration.py:376-395` は generator receipt 付きの生成物 build で stock control ではない) | 採用 | 記録の訂正のみ |
| S-2 | real | 採用 | probe の判定を §3 の 3 判定へ接続する |
| S-3 | real だが L-7 の縮小で対象の変異 7・8 と第 3 テストを登録しないため解消 | 不要化 | — |
| S-4 / L-5 | real (`g++` と `g++-11` は同一実体 `/usr/bin/x86_64-linux-gnu-g++-11`。`g++-9` は `BUILD_FLAGS` の `-std=c++20` を受けない) | 採用 | 候補から `g++-11` と `g++-9` を外し、realpath と版の両方が異なる組だけを数える |
| L-1 | real (隔離 session の guard は heredoc・関数・複合 command を拒否する) | 採用 | 親手順は §4 の単文列にする。一時変異は親の Edit tool で 1 行だけ変える |
| L-2 | real | 採用 | seed 後に必ず復元し clean を確認してから次の変異へ |
| L-3 | real | 採用 | 衝突する組が 1 つも無ければ単位 F を実装しない (§5) |
| L-6 | real (NIT) | 採用 | `buildcache.py:3644` → `:3645-3646` |
| L-7 | 採用 (scope 縮小) | 採用 | 新規回帰テストは 1 本、変異は 3 本 |
| L-8 | real (NIT) | 採用 | 記録では「T-785 に起因すると確認された研究停止は無い」と書く |

scope 外の real 所見でユーザー裁定へ返すものは無い。既知の限界として記録だけに残すもの: 要求名が同じまま実体・版が替わる場合 (PATH・symlink 更新) は legacy key の対象外 (build_v2 は toolchain manifest で保護済み)。s1/s2/s3/s5 と非 Pegasus の between_run_floor は evidence 側に独立の `"g++-13"` 既定を持つ。`s8b_floor_campaign.py:20` の legacy 記述は古い。いずれも実装しない。

## 2. provisional 裁定の確定

- **P1 確定:** `cache_key` の省略条件を歴史的既定の literal 組 (`"gcc-13"`, `"g++-13"`) へ切り離す。caller・build_v2・hit 時検査は変更しない。
- **P2 修正して確定:** probe は repo 外、Codex author 作。`buildcache._run` だけを差し替える。判定は §3。compiler 組は §4 の evidence 走査で決める。
- **P3 修正して確定:** 回帰テストは `test_campaign.py` の `test_cache_key_separates_compiler_request_name` 直後に 1 本。module の `DEFAULT_CC`/`DEFAULT_CXX` を差し替え、cc/cxx を明示する。既存の golden (`_T816_GOLDEN_CK0`) と compiler 名分離テストを再利用する。

## 3. 単位 P (再現 probe) の仕様

所有 path: impl worktree 直下の `t785_legacy_cache_probe.py` (untracked、commit しない。親が job dir へ退避して実行する)。

- `evidence` モード: `--repo <abs> --cxx <name> --out <abs>`。`build()` は呼ばない。`source_digest.resolve_evidence(genome, pin.CURRENT_PIN, ccbench_dir=<repo>/external/ccbench, cxx=<name>)`、`build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)`、`derive_build_admission` を実行し、`admission_provenance`・`admission_receipt_sha256`・`source_bytes_sha256`・`src_token`・`tracked_clean`・要求 compiler の `shutil.which` と realpath と `--version` 1 行目を JSON へ書く。
- `build` モード: `--repo <abs> --cache-root <abs> --expect hit|miss --out <abs> [--seed-json <abs>]`。plan §単位 P の手順 1〜6 のとおり production `buildcache.build(genome, ccbench_commit=pin.CURRENT_PIN, trace=False, cache_root=..., ccbench_dir=..., jobs=1, admission=..., build_context=..., source_evidence=...)` を **cc/cxx を渡さずに** 呼ぶ。evidence の `cxx` は `inspect.signature(buildcache.build)` の cxx 既定を使う。差し替え `_run` は plan のとおり (configure で argv 記録と極小 C++ の実コンパイル、build で存在確認、他は失敗、`finally` で復元)。
- genome は `Genome("silo", {"BACK_OFF": 1})`。`--repo` を import path 先頭に置き、import した module の実 path が repo 内であることを assert する。`--out` と `--cache-root` は repo 外必須、`--out` は既存なら上書きせず非 0。`build --expect miss` の seed 相は cache root が不在か空であることを要求する。
- JSON field は plan の表に加え、次の 3 判定を**機械的に**出す (S-2):
  - `collision_precondition`: seed JSON が与えられたとき、seed と今回で `admission_receipt_sha256` が一致し、かつ要求 cxx の realpath と `--version` 1 行目がともに異なる。
  - `reproduced_false_hit`: `collision_precondition` かつ cache key 一致・`cached=true`・差し替え `_run` の呼出 0 回・binary sha256 が seed と一致・`configure_argv` の cxx が seed と異なる・ELF `.comment` が seed の compiler 版を含む。
  - `fix_demonstrated`: `collision_precondition` かつ cache key 不一致・`cached=false`・今回の要求 cxx で実コンパイルした・ELF `.comment` が今回の compiler 版を含む。
- 終了コード: JSON を書けたら 0。`--expect` と `cached` が不一致なら JSON を書いたうえで 3。例外は非 0 (JSON を書けた範囲で `error` field に型名と要約)。

## 4. 親の手順 (単文列、DW-O19)

A. **evidence 走査 (変異なし):** `g++-12`、`g++`、`clang++` の 3 本で `evidence` モードを走らせる。receipt が一致し realpath・版が異なる組を選ぶ。C compiler は同族 (`gcc-12`/`gcc`/`clang`)。
B. **修正前再現 (組 X→Y、cache root は job dir 配下の新 path):**
  1. `git status --porcelain --untracked-files=all` が空。
  2. Edit tool で `buildcache.py:622` を X 組へ 1 行変更。
  3. `git diff --numstat` が `1 1 orchestrator/campaign/buildcache.py` の 1 行だけ、`git diff --unified=0 -- orchestrator/campaign/buildcache.py` が当該行だけ。
  4. `build --expect miss` (seed)。
  5. `git checkout -- orchestrator/campaign/buildcache.py`、`git hash-object orchestrator/campaign/buildcache.py` と `git rev-parse HEAD:orchestrator/campaign/buildcache.py` の一致、porcelain 空。
  6. 2〜5 を Y 組で繰り返し、4 を `build --expect hit --seed-json <seed>` にする。
  7. `reproduced_false_hit=true` を確認。
C. **修正後確認:** 単位 F の統合 commit 後、同じ組 X→Y・新しい cache root で B を繰り返し、hit 相を `--expect miss` にする。`fix_demonstrated=true` を確認。
各 JSON と probe 本体 (sha256・byte 数) は job dir に保全し、insight には引用と path だけを書く。probe は repo へ入れない。

## 5. 停止・分岐条件

- A で衝突する組が 1 つも無い → **単位 F を実装しない**。測った receipt と realpath・版を記録し、「この host の在庫では再現未成立」として段 7 へ進み、ユーザーへ未再現を報告する (L-3)。
- B で `reproduced_false_hit=false` → 同上。原因を JSON から読み、差し替え範囲を広げて再現を作らない (規律 2・F29)。
- probe の例外 → 本文を読み、probe 側の欠陥なら同じ単位 P を job-id を変えて修正させる。production 側の検査を緩めない。

## 6. 単位 F (修正) の仕様

所有 path: `orchestrator/campaign/buildcache.py` (`cache_key` の docstring と `tc` の 1 行、`:625-644` の範囲内だけ)、`orchestrator/tests/test_campaign.py` (`test_cache_key_separates_compiler_request_name` の直後へ新規テスト 1 本だけ)。

- 差分: `tc = "" if (cc, cxx) == ("gcc-13", "g++-13") else f"|cc={cc}|cxx={cxx}"`。docstring は「歴史的ツールチェーン (gcc-13, g++-13) だけを省いて旧キーを温存し、省略条件を DEFAULT_CC/DEFAULT_CXX から独立させる」旨へ書き換える。named constant を足すかは author の判断でよいが、`DEFAULT_*` を参照してはならない。
- 新規テスト `test_cache_key_default_toolchain_change_does_not_alias_historical_key`: 既存 `_admission_for` で stock でない src_token と stock の 2 形を使ってよい。(a) `DEFAULT_*` 未変更で `cache_key(..., cc/cxx 省略)` を歴史キー H とする。(b) `monkeypatch.setattr(buildcache, "DEFAULT_CC", "gcc-12")` 等で既定を `gcc-12`/`g++-12`、次に `gcc`/`g++` へ替え、それぞれ `cache_key(..., cc=<新既定>, cxx=<新既定>)` が H と異なり、互いにも異なる。(c) 既定を替えた状態でも `cache_key(..., cc="gcc-13", cxx="g++-13")` が H と一致する。修正前は (b)(c) が赤、修正後は緑になること。
- 既存テストの期待値を変えない。現行入力の key を変えない。

## 7. 変異の事前登録 (B-057)

| ID | 対象 (F 後の `buildcache.py` の `tc` 行) | 期待 |
|---|---|---|
| M1 | 比較先を `(DEFAULT_CC, DEFAULT_CXX)` へ戻す | KILLED: `test_cache_key_default_toolchain_change_does_not_alias_historical_key` |
| M2 | 常に `f"|cc={cc}|cxx={cxx}"` を付ける | KILLED: `test_source_digest_silo8_variant_id_and_t343_cache_break_are_explicit` (golden) |
| M3 | 常に `""` にする | KILLED: `test_cache_key_separates_compiler_request_name` と `test_cache_key_default_toolchain_change_does_not_alias_historical_key` |

赤理由は各 1 つ (key 値の変化) で、同じ入力を拒否する前後の層は無い。実装後に単一理由性を確かめ、成立しなければ登録を外して再照準する (DW-M01)。

**erratum (段 5 投入後・実装完了前、親):** `DW-M08` の「期待 node は完全集合」に合わせ、変異走行の対象を `orchestrator/tests/test_campaign.py` の 4 node (上記 3 node と `test_cache_key_separates_trace_genome_and_commit`) に絞り、各変異の期待 KILLED 集合を完全集合として書き直した。当初 M3 は 1 node だけを挙げていたが、新規テストの (b) も「既定を替えた要求が歴史キーと一致する」で赤になるため 2 node に訂正した。M1 = {新規テスト}、M2 = {golden テスト}、M3 = {compiler 名分離テスト, 新規テスト}。`test_cache_key_separates_trace_genome_and_commit` はどの変異でも緑のはず (trace・genome・commit の軸は `tc` と独立)。

## 8. 成果物影響 (DW-G05)

放置時: 既定 toolchain を替えた後、legacy 経路 (s1/s2/s3/s5、pipeline の legacy 分岐、backoff_profile、between_run_floor、pegasus_floor_scoping) の `BuildResult.configure_argv` が示す compiler と実 binary の compiler が食い違ったまま、検査結果・性能値が台帳とレポートへ入る (前処理出力が compiler 間で一致する組に限る)。

## 9. 並列分割と検査

- 直列: 単位 P → 親 A・B → (再現時のみ) 単位 F → 親の統合 commit → C。
- impl worktree は 1 本 (`/work/1/SFC/tanab/izanagi/.codex/worktrees/t785-impl`、branch `impl-dev-wave-t785`、wave HEAD から作成) を P と F で共用する。F 投入前に probe file を退避して消す。
- 焦点走: `orchestrator/tests/test_campaign.py`、`test_build_site_gate.py`、`test_buildcache_v2.py`、`test_p3_s4_loop.py`、`test_p3_s4_loop_sort.py`、`test_real_repo_serialization.py`、および consumer の `test_t2187_adaptive_const_probe.py`、`test_backoff_profile_pegasus.py`、`test_between_run_floor.py`、`test_pegasus_floor_scoping.py`。受入全走は免除しない。
- 段 6 レビュー 2 本は実施する (正しさ防壁に触るため)。
