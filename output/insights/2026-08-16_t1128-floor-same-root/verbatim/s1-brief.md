# 段 1 brief — [T-1128] 床値の oracle 依存 root と build の source root を同一 tree へ揃える

wave: `dev-wave-t1128-floor-same-root` / branch `worktree-dev-wave-t1128-floor-same-root`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1128-floor-same-root`
base: local main `330f67d0` / 2026-08-15 22:40 JST

## 1. 確定済みユーザー裁定 (前提。覆せない)

- 2026-08-15 の /rulings 33 件束で `T-1094` は **(a) 実装しない** = 見送り。床値の残作業は
  本タスク `T-1128` へ集約された。control = ユーザー
  (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-15-rulings-full-33rulings.md:20`)。
- したがって **`FETCHCONTENT_SOURCE_DIR_*` の配線を復活させてはならない**。この欠陥は
  SOURCE_DIR の要否とは独立である (D413)。
- `T-1129` (P2、`third_party_source_contract` へ ignored file 検査を足す) は本 wave の scope 外。
  触らず台帳へ返す。`T-1130` (D152 の clone が git 強化設定下で走るか) も scope 外。
- D152 の供給方法は「未測定」であって不成立ではない。不成立として扱わない。

## 2. scope

床値 (`s8b_floor_campaign`) の `sort_best` cell について、**SWO oracle が検証する masstree tree と、
その cell の binary が実際にコンパイルされる masstree tree を同一の物理 tree にする**。
設計と実装、および単体テストまでを本 wave で完了する。床値の本走 (12 cell・測定・report) は行わない。

scope 外: ignored file 検査 (T-1129)、`FETCHCONTENT_SOURCE_DIR_*`、S5 / `p3_s4_loop_sort` /
`T-1095` の修復、床値本走。

## 3. 成果物影響 (DW-G05)

放置した場合: 床値 `sort_best` cell が発行する oracle attempt record と phase marker
(`sort-swo-oracle-dependency.json`) は「共有 cache の masstree に対して comparator の SWO を
検証した」と主張するが、測定される binary は別 tree の masstree に対してリンクされる。
**certified 選択の根拠になる床値 cell の correctness 主張が、実際に測った実体を覆っていない。**
加えて汚染のない clean な cache では `config.h` が存在せず oracle が UNAVAILABLE になるため、
床値 `sort_best` cell は 0 件になる (F319 が示した通り、これまで通っていたのは cache が
過去の build の生成物で汚染されていたためである)。

## 4. 不変条件 (違反したら停止)

- **I1** `FETCHCONTENT_SOURCE_DIR_*` を渡す配線を新設・復活させない。
- **I2** `silo_ladder_rung1.third_party_source_contract` の pinned-clean 判定を変更しない
  (T-1129 の scope)。
- **I3 (凍結 pin 閉包・F301 の再発面)** `orchestrator/campaign/s1_direct_comparison.py` を編集すると
  `orchestrator/tests/test_s8b_oracle_manifest.py:40, 86-91` の golden bytes literal に含まれる
  materializer sha256 と、その canonical bytes 上の gate hash が古くなる。編集した場合は
  **実ファイルの sha256 から独立に計算して差し替える** (production serializer の出力から
  再生成しない)。同 pin は `orchestrator/tests/test_s8b_oracle_report.py:54, 217` にもあるが
  こちらは実行時計算なので不変。編集面 path を key にした pin 検索の結果は本節が正本。
- **I4** `orchestrator/tests/test_sort_swo_oracle.py:1268-1271` は
  `resolve_oracle_environment` の source に `/work/` literal が無いこと、
  `IZANAGI_SORT_SWO_CXX` と `IZANAGI_SORT_SWO_MASSTREE_ROOT` を残すことを要求する。
  resolver を触るならこの 3 条件を保つ。機体固有 literal を書かない。
- **I5 (規律 2)** oracle gate を緩めない。依存が解決できないときは
  `OracleEnvironmentResolutionFailure` → `OracleStatus.UNAVAILABLE` の閉じた失敗のままとし、
  pass や skip へ落とさない。`_FloorOraclePreflightError` の
  `detail_code` / `outcome` 閉集合を緩めない。
- **I6** masstree の HEAD 照合 (共有 policy pin `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`) と
  `config.h` の sha256 記録は残す。新 root でも同じ強さの identity を主張できること。
- **I7** 実測していない主張を書かない。計算ノードで測るなら dispatch を使い、単独性を確認する。
  probe は repo へ入れない。

## 5. 変更面のアンカー (実測。分類文でなく実物)

| # | 位置 | 事実 |
|---|---|---|
| A1 | `orchestrator/campaign/s8b_floor_campaign.py:1582-1611` | `_resolve_floor_oracle_dependency(cache_root)` — 共有 third-party cache root (引数または `_THIRD_PARTY_CACHE_ENV`) を解決する |
| A2 | `orchestrator/campaign/s8b_floor_campaign.py:1429-1579` | `_verify_floor_oracle_dependency_source` — git root 一致・HEAD == policy pin・`config.h` の sha256 を取る |
| A3 | `orchestrator/campaign/s8b_floor_campaign.py:1330-1342` | `_FloorOracleDependencyBinding{source_root, expected_head, observed_head, config_sha256}` と `private_dict()` の 4 field |
| A4 | `orchestrator/campaign/s8b_floor_campaign.py:2019-2028` | 呼び出し + `sort-swo-oracle-dependency.json` marker 書き出し |
| A5 | `orchestrator/campaign/s8b_floor_campaign.py:2043-2069` | `floor_prepare` が `oracle_dependency_root=_dependency.source_root` を `prepare_fn` へ渡す |
| A6 | `orchestrator/campaign/s1_direct_comparison.py:592-597` | `prepare_cell(..., oracle_dependency_root, oracle_compiler, oracle_phase_marker)` |
| A7 | `orchestrator/campaign/s1_direct_comparison.py:621-622` | `fixed_sub = ROOT/external/ccbench`、`cache_root = repo_output_root()/s1-build-cache` |
| A8 | `orchestrator/campaign/s1_direct_comparison.py:671-709` | `sort_best` 枝: `resolve_oracle_environment(sub, compiler=, dependency_root=)` → `check_materialized_sort_swo` → UNAVAILABLE/REJECT/PASS。**build より前に走る** |
| A9 | `orchestrator/campaign/sort_swo_oracle.py:1102-1210` | resolver。既定候補列は `argument` → env → `ccbench/build/_deps/masstree-src` (1134-1138) → ancestor cache 8 世代 (1141-1146)。選択条件は `<root>/config.h` が regular file であること |
| A10 | `external/ccbench/cmake/ThirdParty.cmake:35-88` | `FetchContent_Declare(masstree GIT_TAG b3c5d054...)`、`masstree_build` target が `WORKING_DIRECTORY ${masstree_SOURCE_DIR}` で `bootstrap.sh; configure; make; ar` を実行 = **source tree の中に `config.h` と archive を吐く**。`GIT_TAG` は共有 policy pin と同一値 |
| A11 | `orchestrator/campaign/buildcache.py:1344-1350` | v2 build dir = `<root>/contracts/<contract_sha256>/<digest>`。digest は genome・src_token・toolchain・admission 依存 = **cell ごとに別 dir、よって `_deps` も cell ごとに別** |
| A12 | `orchestrator/campaign/buildcache.py:1551-1567` | legacy 経路の bdir = `<root>/<cache_key>`、configure argv は `cmake -S <sub> -B <bdir> ...` |
| A13 | probe 実測 (worklog 560 / insight) | `oracle_dependency_root=<cache>/masstree`、`configure_source_root=/scr/<job>/ccbench-c1-build/_deps/masstree-src`、`same_root = false`。SOURCE_DIR 無し configure は rc=0 / 5.520 s、`masstree_build` は rc=0 / 10.676 s で `config.h` 10,448 bytes と archive 2,466,926 bytes を生成 |

## 6. 親の provisional 裁定 (すべて攻撃対象)

- **(P1)** 揃える向きは **oracle を build 側の tree へ寄せる**。build を cache tree へ寄せるには
  SOURCE_DIR 配線が要り I1 に反するため取れない。したがって oracle の `dependency_root` は
  「その run で build が実際に展開した `_deps/masstree-src`」でなければならない。
- **(P2)** 物理 tree を 1 本にする手段の第一候補は、**job-local な FetchContent base dir を
  1 個決め、床値の全 cell build と依存 build がそれを共有する**こと。
  `FETCHCONTENT_BASE_DIR` は `FETCHCONTENT_SOURCE_DIR_*` とは別の変数であり I1 に触れない、
  というのが親の読みである。**ここは最も割れやすい点なので重点的に攻撃せよ。**
  代替は「cell ごとの build dir 配下 `_deps/masstree-src` を、その cell の oracle root にする」
  (物理 tree は cell ごとに別だが oracle と build は各 cell 内で一致する)。どちらが
  「同一 tree へ揃える」の要求を満たすか、証拠として何を主張できるかを file:line で詰めること。
- **(P3)** 順序: oracle は build より前に走る (A8) ので、oracle 実行前に
  **masstree だけを build する段**が要る。`cmake --build <dir> --target masstree_build` が
  その最小手段である (A10、A13 で実測済み)。この段の所在 (床値 campaign 内か、buildcache の
  seam か、別 helper か) を決めること。
- **(P4)** 新 root でも identity 主張の強さを落とさない: `_deps/masstree-src` は
  `GIT_TAG` = 共有 policy pin と同じ SHA の git checkout なので、A2 の HEAD 照合はそのまま効く
  (親の読み。plan は実物で確認すること)。`config.h` sha256 の記録も残す。
- **(P5)** 本 wave の検証は (i) 単体テスト、(ii) 変異 matrix、(iii) 受入全走 とする。
  計算ノードでの end-to-end 実証 (`same_root = true` の 1 job probe) は、
  plan が「単体テストだけでは設計の生死が決まらない」と判断した場合にだけ dispatch で行う。
  行う場合、probe は repo へ入れず codex author が書き、単独性を確認してから測る。
- **(P6)** 床値以外の consumer (`p3_s4_loop_sort:174-176` は resolver を引数なしで呼ぶ、
  `test_sort_swo_oracle.py:20` は module import 時に解決する) を壊さない。
  resolver の既定候補列を変えるなら、これらへの影響を file:line で示すこと。

## 7. 並列分割方針

- 段 2: プラン起草 1 本 (read-only codex)。
- 段 3: 敵対 2 レンズ並列 — (α) I1/I2 の scope 逸脱と SOURCE_DIR 復活の検出、
  (β) 正しさ防壁 (規律 2/3) と identity 主張の弱体化、および P2 の設計択一。
- 段 5: 実装子 1 本 (編集面が 2〜3 module に閉じるため分割しない)。
- 段 6: 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。

## 8. 受入・実測の環境

- 単体テスト・受入全走: 本 worktree (login node)。`tools/run_tests.py` の受入形。
  受入 lease は `tools/dev_wave_wait.py acceptance` で claim する。
- 計算ノード実測 (P5 で成立した場合のみ): dispatch 経由。機体固有情報は
  `docs/pegasus-runbook.md` を正本とする。
