# [T-1437] source_digest の macro 供給表を protocol 混在に対応させた — 実装記録と変異台帳

## 要約

`orchestrator/campaign/source_digest.py` は `EVOLVE_BLOCK_SOURCES` (silo/mocc 混在の固定
source tuple) に対し、defines を `genome.protocol` 単一からしか作っていなかったため、
`Genome("silo",...)`/`Genome("mocc",...)` の**両方**で `source_digest.resolve()` が
対称に fails-closed 停止していた。[T-1431] 床値 pilot の実投入で最初に踏まれ
(`output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`)、原因は
着手同日 land 済みの commit `ae958491` ([T-755]) が導入した regression だった (長期潜伏
バグではない)。本 wave は原因を3点 (source 単位の protocol 分離欠如・裸オプション未対応・
MQLOCK 死コード) に切り分けて修正し、変異事前登録5点と受入全走 (`verdict=child-green`) で
検証した。設計判断は `docs/decisions.md` の D93 precision addendum
({{D:source-digest-supply-precision}} → fold 後の実番号) を参照。

## 実測で確認した事実

`Genome("silo",{})`/`Genome("mocc",{})` それぞれで
`orchestrator.campaign.source_digest.assert_conditional_macros_covered()` を実機
(g++ 11.4.0、submodule init 済み) で直接呼び、対称に fails-closed することを実証した
(silo は `cc/mocc/transaction.cc` で `['MQLOCK','RWLOCK','TEMPERATURE_RESET_OPT']` 未知、
mocc は `cc/silo/transaction.cc` で `['NO_WAIT_LOCKING_IN_VALIDATION','NO_WAIT_OF_TICTOC',
'SLEEP_READ_PHASE','WAL']` 未知)。silo 側の実エラーは [T-1431] の実 job のエラーと逐語一致した。

## 実装の3本柱

1. **source 単位の protocol 分離**: `EVOLVE_BLOCK_SOURCE_PROTOCOLS` を新設し、
   `_worktree_defines`/`_head_defines` に `source_rel` 引数を追加。file ごとに owner protocol
   の CMakeLists.txt から defines を作る。registry と `EVOLVE_BLOCK_SOURCES` の exact-match は
   モジュール読み込み時に自己検査し、drift は `RuntimeError` にする。
2. **裸オプション・非対称 cache 名対応**: `ccbench_add_protocol(...)` の `OPTIONS` を
   balanced paren scan + section 境界解析で読み、`=` を伴わない裸 token (`RWLOCK` 等、
   CMake の `-DNAME` 相当) と、左辺 macro 名 ≠ 右辺 cache 変数名の非対称命名
   (cicada/oze の `INLINE_VERSION_OPT` 等) の両方を実 TU 供給集合へ反映する。
3. **MQLOCK 専用 registry**: `PROVEN_REPO_ABSENT_MACROS` (現状 `{"MQLOCK"}`) を新設し、
   repo 全体 (全 protocol の CMakeLists.txt・universal 定義・`#define`・6種の CMake 供給 call・
   `CMAKE_CXX_FLAGS` 経由の `-D`) を毎回実走査して供給源ゼロを自己検証する。検出すれば
   registry が stale と判定し fails-closed する。`CONTEXT_MACROS` (TU 注入で時々供給されうる
   macro 用) とは意味が異なるため流用していない。

## 段6 で踏んだ罠 (次の wave への申し送り)

- **段6 fix 自体が新規 regression を起こした。** MQLOCK registry のセミコロン区切り list 供給
  (`"FOO;MQLOCK"`) の見逃しを fix する際、`_repo_macro_token_matches` に generator expression
  (`$<...>`) 検出を追加したが scope が広すぎ、third_party (googletest) の無関係な token
  (`$<INSTALL_INTERFACE:GTEST_LINKED_AS_SHARED_LIBRARY=1>`) に誤反応し3テストが regression した。
  親が `tools/run_tests.py` の実機実行で検出し (codex 子は Pegasus dispatch 認証エラーで
  自己検証できなかった)、`"$<" in token and macro in token` へ scope を絞って解消した。
  **fix 自身の副作用を fix 直後に親が実測で確認する規律が有効だった。**
- **受入全走で初めて見つかった consumer 漏れ。** `tools/check_trace0_preprocess_identity.py`
  が `_head_defines` を直接呼んでおり、その test fixture (`_OPTIONS` 定数) が
  `ccbench_universal_definitions()` の中身を `target_compile_definitions(...)` 直書き形式
  (実 `cmake/Options.cmake` の `set(...PARENT_SCOPE)` 形式とは別の、同等に正当な CMake 慣習)
  で書いていたため、新設パーサが「マクロ供給表が空」で新規 fails-closed した。
  **段5/6 の焦点走 (`test_campaign.py` の `-k` フィルタ) はこの consumer を対象に含めておらず、
  受入全走 (フィルタなし全体走) で初めて発覚した。** production file (`source_digest.py`) を
  import する consumer の grep 網羅はしたが、consumer の **test fixture の内部構造**
  (synthetic CMake の書き方) までは検算していなかったのが穴。**「変更した production file を
  参照する consumer test も焦点走に含める」(DW-O26) は、consumer が独自の synthetic fixture を
  持つ場合、その fixture が新しい解析ロジックの前提と food かどうかも検算する必要がある**、
  という教訓として一般化できる。
- **codex 実装/fix 子は Pegasus queue へ dispatch できない既知制約を計3回再現した**
  (段5実装1回、段6 fix3で1回、いずれも `qstat -Q preflight` 系のエラー)。親が
  `tools/run_tests.py` で同じ焦点集合を必ず代替実行する運用が機能した。
- **変異matrixの expected_nodes は机上予測でなく実測で確定すべき、を再確認した。**
  5点中2点 (exact-match 無効化・MQLOCK self-check 無効化) は机上予測どおり単一 node だったが、
  残り3点 (source 単位 protocol 固定化・裸 option 代入削除・非対称 mapping 削除) は予測より
  広い node 集合を示した — 段5 fix が fake mocc fixture へ実の条件指令を追加した副次効果で、
  既存の周辺 guard 系テストも副次的に regression guard として機能するようになっていたため。
  probe 走 (expected_status=SURVIVED で登録) → 実測 → 実測値で本登録、の2段階が有効だった。
- **受入 lease の待ち手が長時間 (2.5時間超) 待機すると `tools/dev_wave_wait.py` 自身の
  main 更新と bytes 不一致になり `rc=70` (restart-required) で停止しうる。** 正しい fail-closed
  であり lease も適切に解放されるため、待ち手を再起動 (新しい attempt 番号で再投入) すれば良い。

## 変異台帳

`mutation-ledger.json` (`mutation_harness.py` の `--out` 出力そのもの)、
`mutation-spec.json` (最終登録した spec、`izanagi-dev-wave-mutation-spec/v1`)。

baseline PASSED、5/5 KILLED、SURVIVED 0、MISMATCH 0。

## 一次資料の所在 (repo 外、job dir)

`/work/1/SFC/tanab/dev-wave-jobs/2026-08-20_t1437-mocc-macro-protocol/` に段1〜6 の全 prompt・
codex 出力・裁定・受入 receipt を保全済み。
