# [T-548] gflags / glog を versioned な共通調達経路へ移す

- 日付: 2026-09-16
- wave: `dev-wave-t548-versioned-dep-procurement`
  (branch `worktree-dev-wave-t548-versioned-dep-procurement`)
- 起点 main: `262c2993e` → 段 5 前に `d97c423bd` (134 commit) → 段 6 前に `e667c8c13` (72 commit) を取り込み
- 実装 commit: `0165027e0` (37 file、+418/−360)、merge `99c9b9222`、fix `b9187e920` (10 file)、
  merge `4b73b5a95` (main 84 commit)、受入待ち手の post-claim merge `a792c92f8`、fix `b86c6628d` (1 file)
- 裁定の一次資料: 2026-08-16 /rulings 全件 第 3 回 索引 19 (択 (b))。
  逐語は `verbatim/ruling-t548.md`。

## 何をしたか

機体固有の絶対 path (`/work/SFC/tanab/github/{gflags,glog}`) で repo に書かれていた gflags / glog の
locator を消し、url + 40 hex pin で指す調達記述にした。既存の cache / hydrate 機構
(`tools/pegasus/fetch_third_party.py`) が FetchContent 3 本と同じ手順で 2 本を運び、
旧 locator を読んでいた consumer 21 本 (job body 15・Python 5・data 1) をすべて hydrate 済み
staging root 配下の解決へ付け替えた。旧経路 (`verify-deps`) は廃止した。

設計の正本は {{D:gflags-glog-versioned-procurement}}。実装しなかった検証層の限界は
{{D:no-use-time-verify-source-gate}}。

## 段 1 で実測した事実 (login node、2026-09-16)

- 素の CCBench configure は `cmake/Findgflags.cmake:9` → `CMakeLists.txt:33` で
  `Could NOT find gflags`、rc=1。**module mode が走って失敗し、config mode へは落ちない。**
- `-DCMAKE_PREFIX_PATH=<残骸 prefix>` を足すと `Found gflags: …/libgflags.a` で rc=0。
- `~/.cmake/packages/gflags` 1 件・`glog` 27 件の残骸 registry が実在し、最小 cmake project の
  probe は config mode で緑になる (本番の反証にならない)。
- system に gflags / glog は無い。pin 済み source 2 本は現存し HEAD は policy と一致。
- **[T-2625] は既に成立していた** (job 999363)。通したのは親の一回限りの env 回避で、
  それは裁定が択 (c) として却下した形そのもの。段 1 brief の「止まっている」は誤りで、段 3 が突いた。

## 裁定の経緯 (段 3 → 段 4 → 追補 1〜5 → 段 6 → 追補 1〜4)

段 2 plan は「1 consumer だけ結線 + opt-in 入口」を推した。段 3 の 2 レンズが独立に、
それが D1737 の却下状態を作り裁定の「同一 wave」にも反すると結論し、親は plan を不採用にして
全 consumer の付け替えへ scope を広げた。段 4 の裁定は `verbatim/stage4-ruling.md`。

**実装子は段 5 で 5 回、段 6 で 1 回、fail-closed で停止した。6 回とも親の欠陥を指していた。**

| 停止 | 指した欠陥 | 追補 |
|---|---|---|
| A-1 | 廃止命令の test 削除を禁止文が塞いでいた + consumer 列挙が 134 commit 分陳腐化 (`b4_binary_record.py` が着地) | 段 4 追補 1 |
| B-1 | T-126 の shell と Python が共有 fixture で結合、所有が素集合でなかった | 段 4 追補 2 |
| C | `test_ccbench_spawn_sites.py` の起動本数 pin・行番号 pin | 段 4 追補 3 |
| B-2 | `test_mocc_trace_job_contract.py` の値本数 pin (18) | 段 4 追補 4 |
| B-3 | silo 凍結 evidence の `pbs_job` binding (現行 bytes と一致で束縛) | 段 4 追補 5 |
| F1-1 | 契約テストが mocc にも env 既定の解決行を要求 = B3 の不具合を期待値が固定 | 段 6 追補 1 |
| (受入) | 凍結 prereg `protocol-r33.json` が `oracle_n_pilot.sh` の sha を記録し test が live 比較 (受入で決定的赤) | 段 6 追補 4 |

追補の逐語は `verbatim/stage4-erratum-{1..5}.md`、`verbatim/stage6-erratum-{1..4}.md`。
親の側の失敗型は {{F:stage1-consumer-enumeration-stale-by-stage5}}、
{{F:ownership-split-by-filename-misses-fixture-coupling}}、および F370・F736 の再発。

## 凍結値の扱い (D200 の先例)

すべて親が算出し、実装子が編集後 file から算出する経路を塞いだ。

| 対象 | 歴史値 | 現行値 |
|---|---|---|
| `tools/pegasus/policy.json` | `b1c42e49…` (据え置き) | `3a3c7d607de77e23368f9ce382b41e6e524de3ee1e2809e7c6d890ada95a6c90` (変更前 bytes に 2 行の置換だけを適用して実装前に算出) |
| `tools/pegasus/silo_ladder_rung1.sh` (`pbs_job`) | `318c2b12…` (= 変更前 main の bytes。本 wave で歴史化) | `99687368a1fdf10d8f699be3a32afd2814f51d98bcad5fbdf6a1862ca72b456f` |
| `tools/pegasus/submit_silo_ladder_rung1.sh` (`submitter`) | `e12ac658…` (= 変更前 main の bytes。段 6 fix で歴史化) | `6990ad4470aba09b8c62224f33a453c330a0be4fbb913cf1e477bb882659412b` |
| `tools/pegasus/oracle_n_pilot.sh` (prereg `protocol-r33.json` の `job_script_sha256`) | `566698b3…` (= 変更前 main の bytes。prereg の記録値、D1790 の形で定数化) | `3ceaabd1b8b3759fb24b136f44256e8ae76115dd6d1a283bc205c86de01a0ed1` |

凍結 evidence (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`) は 1 byte も変えていない。

## 段 6 レビューと fix

レビュー A (正しさ境界) / B (実効性)。逐語は `verbatim/stage6-review-{a,b}.md`、裁定は
`verbatim/stage6-ruling.md`。

- **must-fix 4 件 (すべて本 wave の回帰か、本 wave で消えた検査):**
  B1 silo (submit / job が gflags / glog を運ばず、job の scratch 上書き後の env を新しい解決行が読む)、
  B2 T-126 (submit helper が一時展開先を `__file__` 基準で root と誤認)、
  B3 mocc (自己 hydrate が gflags 段より後)、P-1 (cache root の fail-closed 検査が乗り物ごと消えた)。
  波及 2 件 (fixture の `output/env` が実 dir になり symlink 負例が衝突、`t293_perf_site_probe.py` の呼出し追従)。
- **レビュー A の must-fix A-1 (使用直前の `_verify_source` 相当) は不採用。**
  {{D:no-use-time-verify-source-gate}}。
- 焦点再レビュー (fix 後): 6 所見すべて closed、新しい穴なし。派生値 3 件は原データと一致。
  変異 M10 の裁定文の記述が実際の spec と食い違っていた (spec は正しい形)。

## 非帰属赤 (DW-O18)

- `orchestrator/tests/test_p3_s4_loop.py` を自走 harness 単体で走らせると TypeError 112・
  ExecutionGuardError 6 (148/263)。fix 前の wave tip `99c9b9222` (clean) でも同じ。
  自走 harness では受入 harness の fixture 注入が無い構造的な赤で、本 wave に帰属しない。
- `test_pegasus_floor_tools.py` の時間境界 node 2 件が単位 B の全走で赤、選択再走で緑。
  login node の負荷依存。受入全走で判定する (下記)。

## 完了条件の生死証拠 (段 4 裁定 §3、login node `pegasus02`、2026-09-16T21:56+09:00、HEAD `b86c6628d`)

逐語は `verbatim/liveness-final.log`、`liveness-fetch.json`、`liveness-hydrate.json`、
`liveness-ccbench-configure.log`、`liveness-ccbench-noprefix.log`。load は 35 / 64 / 72。

1. **fetch** (login、network) rc=0。永続 cache `/work/1/SFC/tanab/izanagi-thirdparty-cache` に
   gflags `e171aa2d…` / glog `8f9ccfe7…` が pin どおり入り、既存 3 本は不変。
2. **hydrate** (offline) rc=0。staging に 5 本 (masstree `b3c5d054…`、mimalloc `02a2f5df…`、
   googletest `f8d7d77c…`、gflags `e171aa2d…`、glog `8f9ccfe7…`)、すべて clean。
3. **fresh build**: staging の gflags → `prefix/lib/libgflags.a`、glog (gflags prefix を参照) →
   `prefix/lib/libglog.a`。configure / build / install の 6 手すべて rc=0。残骸 prefix は使っていない。
4. **本番と同じ finder で実 CCBench configure**: `-DCMAKE_PREFIX_PATH=<新 prefix>` で rc=0、
   `-- Found gflags: <新 prefix>/lib/libgflags.a`、`-- Found glog: <新 prefix>/lib/libglog.a`。
   両方とも今回建てた prefix 配下 (grep で 1/1)。module mode は library と header の両方を要求するので
   (`Findgflags.cmake` の `find_library` + `find_path`)、header も同 prefix から解決されている。
5. **負例** (prefix 無し): rc=1、`Could NOT find gflags (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)`、
   call stack は `cmake/Findgflags.cmake:9` → `CMakeLists.txt:33`。config mode へ落ちない。

**射程の限定:** login node の 1 時刻・1 host で、この pin・この build option・この install layout で
成立した。**計算ノードでの job 完走・driver 本走・T-2625 の再取得・walltime 充足は含意しない。**
hydrate 時の検証 (origin・非 shallow・index bit) が job 使用時点まで保証されるとも主張しない
({{D:no-use-time-verify-source-gate}})。

## 受入全走

- attempt 1 (tip `4b73b5a95`): 24,222 passed / 23 error / 1 failed。error 23 はすべて setup の
  `subprocess.TimeoutExpired` (`git archive` / `git -C <wave 木> ls-files`)、同時受入 3 本。非帰属。
- attempt 2 (post-claim merge `a792c92f8`): 24,243 passed / 3 failed。2 件は計算ノード bnode042
  (1 分 load 43.77) での launcher timeout、非帰属。1 件 (`test_r33_protocol_document_loads_from_repository`)
  は本 wave に帰属 → 段 6 追補 4 (fix `b86c6628d`)。
- 逐語は `verbatim/acceptance-attempt{1,2}-child.log`。**land 対象 tip への最終受入は段 7・8 の
  commit 後に投入し、結果は受入 receipt と land 結果 JSON が正本** (DW-O12)。

## 既知の限界・次の一手へ

- 各 job body の inline python は既存の orchestrator import を持つものがある
  (`certify_calibration.sh:227`、`mocc_trace_pilot.sh:1496`、`t141_region_profile.sh:1104`)。
  計算ノードの既定 python3 では import できない (F88)。本 wave 由来ではなく、調達経路の本題でもない。
- `docs/pegasus-runbook.md:679` の測定表に `verify-deps` の行が残る (歴史記録なので触っていない)。
