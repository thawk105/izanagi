# 段 1 brief — [T-235] network 境界で campaign ループを 2 つに割る

- wave: worktree `.claude/worktrees/dev-wave-network-split` / branch `worktree-dev-wave-network-split`
- 基準 main: `fe2a547`
- 受入環境: Pegasus gen_S 計算ノード (`tools/pegasus/dispatch_compute.py` 経由)。login は pegasus02
  (`site_policy.current_site()` = `PEGASUS_LOGIN`、`refuses_heavy_work()` = True を実測)

## 確定済みユーザー裁定 (command 引数、そのまま採用)

1. 計算ノードは外部 network 不可 (request 873903/873904、runbook §7.1)。よって `claude -p` は
   計算ノードで呼べない
2. supervisor 本体と LLM 4 役 (planner / coder / auditor / critic) は login 側
3. build / verify / bench は計算ノードへ dispatch
4. `dispatch_compute.py` の `TASKS` へ campaign 用 task 種別を 1 つ足す。D103 決定 5 が
   `tools/pegasus/*` の glob 許可を禁じているので、enum への明示追加が正しい経路

## 段 1 前提実測 (すべて本 wave で新規に取得。既存 docs を根拠にしていない)

- **M1**: `TASKS` は `tests` / `provenance` の 2 種。`_TaskSpec(child_script, env_allowlist,
  probe_imports)`。子は `_job_run` が `[sys.executable, repo_root/child_script, *argv]` で起動し、
  env は request の `environment` を allowlist で濾して上書きする
- **M2**: 分割線は設計上すでに存在する。`orchestrator/campaign/p3_s4_loop.py` の docstring は
  「ループ主導権はメインセッション、本 module は LLM を spawn しない」と明記し、
  `--run-iteration PROPOSAL.json` が 1 iteration の機械部分 (挿入→検疫→build/verify/bench→WAL→
  digest→停止判定) を回す口である。**新設ではなく、この口を network 越しに配線するのが本 wave**
- **M3**: `buildcache._run` は `configure` / `build` で `site_policy.refuses_heavy_work` を見て
  login を拒否する (D103 決定 4)。login = ビルド不可、compute = LLM 不可。
  **したがって Pegasus では campaign ループが現在どこでも回らない** (= DW-G04 の発火 artifact)
- **M4**: campaign 子の import 閉包は stdlib のみ (16 module を AST で走査、非 stdlib 0 件)。
  → `probe_imports=()` が正しい (provenance と同型)
- **M5 (blocker B2)**: `buildcache._v2_commands` の configure argv に gflags/glog の prefix も
  `FETCHCONTENT_SOURCE_DIR_*` も無い。pinned staging を持つのは `silo_ladder_rung1.py` だけ。
  ccbench は `find_package(gflags/glog REQUIRED)` + FetchContent (masstree/mimalloc/googletest) を
  要求するので、**計算ノードでは configure が落ちる見込み** (S1 で実測する)
- **M6 (blocker B1)**: `p3_s4_loop.PIN = "028f34d"` は現行 submodule HEAD `d706650`
  (= `pin.CURRENT_PIN`) と不一致。`patchharness.assert_pinned_clean` を両 pin で直接呼んで実測
  (`028f34d` → RuntimeError、`d706650` → OK)。**driver は今日 `--no-build` でも起動しない**
- **M7 (blocker B3)**: `p3_s4_loop.ENV_TAG = "linux-baremetal"` / `CLK = 1800` が module 定数。
  Pegasus の env_contract は `pegasus` / clocks_per_us=2100 (runbook §7.1)。そのまま走らせると
  **計測値に別環境のタグが付く** (規律: 計測層以外の数値を混ぜない)
- **M8 (既存被覆)**: `orchestrator/tests/test_pegasus_dispatch_compute.py` は
  `set(DC.TASKS) == {"tests","provenance"}` を exact 比較で固定し (`:1404`)、
  `(task, child_script)` の parametrize (`:1560`)、未知 task 拒否 (`:1411`/`:1430`)、
  親子二層 fail-closed (`:1657`/`:1668`) を既に持つ。
  **純増検出力**は「campaign entry の child_script / env_allowlist / probe_imports が
  仕様どおりであること」と「campaign の probe source が版数のみになること」の 2 点だけである

## scope (P1: 親の provisional 裁定。攻撃対象)

- **S1 (生死実験、DW-G01)**: 使い捨て probe を 1 本だけ計算ノードへ投げ、
  `buildcache` の v2 configure が gen_S 計算ノードで通るか / どこで落ちるかを実測する。
  既存 driver を使い、新機構は作らない。**この結果が S2 の env_allowlist を決める**
- **S2 (実装)**: `TASKS` へ `campaign` を追加する。child_script = `orchestrator/campaign/p3_s4_loop.py`
  (P2)、probe_imports = `()` (M4 で確定)、env_allowlist = S1 の実測が要求する集合 (P3)。
  テストは M8 の純増 2 点のみ追加し、exact-set assertion を更新する
- **S3 (docs)**: network 境界の分割を decisions に 1 件、runbook §7 のチェックリストに 1 行

## scope 外 (実装しない。裁定パッケージへ返す)

- B1 (`PIN` 陳腐化)、B3 (`ENV_TAG`/`CLK` の Pegasus 対応)、B4 (`default_perf` が配線規模で
  Pegasus calibration ではない)、および B2 の恒久対応 (`buildcache` への pinned staging 注入)。
  B2 は producer write-path を変え `configure_argv` を provenance へ流すため `DW-O09`/`DW-O10` の
  閉包が要る。本 wave では**実測して所在を確定するだけ**にする

## 成果物影響 (DW-G05)

- S2 を実装しない場合: Pegasus 上で campaign を回す sanctioned 経路が存在しないままになり、
  certified 選択・材料レポート・試行台帳の**どの値も生成できない** (M3 により login/compute の
  両方で停止する)。受理集合は変わらないが、受理集合を埋める試行が 0 のまま固定される
- S1 を実装しない場合: env_allowlist を推測で決めることになり、計算ノードで configure が落ちる
  経路を wave 内で検出できない (= 非発火 feature を land する)
- B1〜B4 を本 wave で実装しない影響: campaign task は **transport としては発火するが、
  P3 段 4 の実 iteration はまだ完走しない**。この射程を worklog に明記する

## 不変条件 (緩めない)

- 正しさゲート・verifier・diff 検疫・freeze/pin 契約に触れない。`cache_key` / `_v2_identity` /
  `contract_sha256` の pre-image を変えない (M5 の注入を入れないので今回は自明に不変)
- `tools/pegasus/*` の glob 許可を作らない (D103 決定 5)。task は閉じた enum への明示追加だけ
- login で build / pytest 全走 / bench を実走しない。qsub は F49 (ii) の有効性検査 3 点つき
- push / remote 操作をしない

## 並列分割方針

- 段 2 planner 1 本 (read-only)。段 3 敵対 2 本 (A = 分割線と受理集合・provenance、
  B = 発火性と dispatch 契約の実効性)。段 5 実装子 1 本 (`dispatch_compute.py` と
  `test_pegasus_dispatch_compute.py` のみ所有)。段 6 レビュー 2 本

## provisional 裁定 (攻撃対象)

- **(P1)** scope を S1 + S2 + S3 に限り、B1〜B4 を裁定パッケージへ送る
- **(P2)** child_script は `orchestrator/campaign/p3_s4_loop.py`。
  代案 = 新設の薄い entry (`tools/run_campaign_step.py`) / `silo_ladder_rung1.py`。
  P2 は「既存 seam を使う」を理由に選んだが、B1/B3 により今日は完走しないので、
  **非発火 feature になっていないか**が最大の攻撃点
- **(P3)** env_allowlist は S1 の実測で決める。事前案は
  `{IZANAGI_GFLAGS_INSTALL, IZANAGI_GLOG_INSTALL, CMAKE_PREFIX_PATH, IZANAGI_TEST_NPROC}`
- **(P4)** 本 wave は DW-C00 の軽量版に該当しない (受理集合を埋める経路を新設するため)。
  段 2・3 と段 6 の敵対子を省かない

---

## S1 実測結果 (DW-G01 生死確認 — qsub 不要で login 上で決着した)

段 1 の前提実測を進めた結果、**S1 は計算ノードへ probe を投げる前に login 上で決着した**。
generic な `buildcache` 経路は今日 Pegasus で ccbench を build できない。独立した blocker が 5 件ある。

| # | blocker | 実測方法と結果 |
|---|---|---|
| B1 | `p3_s4_loop.PIN = "028f34d"` が現行 submodule HEAD `d706650` と不一致 | `patchharness.assert_pinned_clean` を両 pin で直接呼んだ。`028f34d` → RuntimeError、`d706650` → OK。`main()` は `--no-build` でも無条件にこれを通るので **driver は今日どの flag でも起動しない** |
| B2 | configure argv に gflags/glog prefix と `FETCHCONTENT_SOURCE_DIR_*` が無い | `buildcache._v2_commands` を読解。pinned staging を持つのは `silo_ladder_rung1.py` だけ。ccbench は `find_package(gflags/glog REQUIRED)` + FetchContent 3 件を要求し、計算ノードは network 不可・gflags/glog 不在 |
| B3 | `ENV_TAG = "linux-baremetal"` / `CLK = 1800` が module 定数 | source 実測。Pegasus の env_contract は `pegasus` / clocks_per_us=2100。そのまま走らせると計測値に別環境タグが付く |
| B4 | `default_perf()` = records 100k / threads 4 / reps 2 は配線規模 | docstring が「性能比較用 calibration ではない」と明記。Pegasus calibration は別値 |
| B5 | `DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"` が Pegasus に不在 | `_toolchain_manifest` を直接呼んで `BuildError: toolchain cc が PATH に存在しない: 'gcc-13'` を実測。login の実体は gcc 11.4.0、`module avail` に gcc-13 系なし (intel / nvhpc / cuda のみ) |

**この結果が意味すること (段 4 で再裁定する新事実):**

- network 境界の compute 半分を塞いでいるのは **dispatch enum ではなく build 経路の環境可搬性**である。
  `TASKS` に campaign を足しても、`p3_s4_loop.py` を指す限り **発火しない feature** になる (DW-G04 抵触)
- 逆に、transport 自体は小さく独立している。`tests` task が `tools/run_tests.py` という薄い
  sanctioned entry を指すのと同型に、campaign も**薄い entry + 閉じた driver enum**にすれば
  D103 決定 5 を守ったまま複数 campaign driver を 1 task で扱える
- queue / 予算は green (gen_S ENA/ACT、149 JSV 中 56 run、SFC 残 367.65 point)。
  **投入していない** — 投げる前に login で決着したため (DW-G01 の「最安」)

## (P2) 改訂 — child_script の 3 候補 (段 2/3 の攻撃対象)

- **(P2-a)** `orchestrator/campaign/p3_s4_loop.py` を直接指す。ユーザー記述の seam に最も近いが
  B1/B3/B5 により今日は発火しない
- **(P2-b)** 薄い sanctioned entry `tools/run_campaign.py` を新設し、その中に閉じた driver enum を
  持つ (`tests` → `run_tests.py` と同型)。`dispatch_compute.py` 側の enum は 1 個増えるだけで済み、
  driver 追加のたびに `tools/pegasus/*` を触らなくてよい
- **(P2-c)** 今日 compute で動く driver (`silo_ladder_rung1.py`) を指す。発火するが
  「ループを割る」という依頼の中身にならない

## 8c との関係 (phase3.md の現行 gate)

`docs/phase3.md` §8 の 8c (駆動のセッション非依存化 = planner/coder/auditor を orchestrator から
呼ぶ) は **未着手・条件付き**で、「8b の前向き設計と層3最小 E2E を 1 cycle 回してなお反復運営が
律速なら実装する」と gate されている。**supervisor 本体の実装は本 wave の scope に入れない** —
本 wave が触るのは transport (dispatch task 種別) と分割線の記録だけである。

## B5 の訂正・補強 (段 3 起動前に親が追加実測)

B5 は当初 login node 上の `command -v` / `module avail` だけを根拠にしていた。**計算ノードへの
一般化は当時未実測だった**ので、次を追加で確認した。

- `docs/pegasus-runbook.md:297` が「`g++-13` は**ログインノードにも計算ノードにも無い**
  (計算ノードには `g++-12` が在る)」を既往実測として記録している。
  これは docs であって一次資料ではないので、**段 4 では「既往記録あり・本 wave 未再実測」**として扱う
- 既存の Pegasus campaign script は B5 を動的解決で回避している:
  `tools/pegasus/floor_campaign.sh:692-693` が `CC_PATH=$(command -v gcc)` /
  `CXX_PATH=$(command -v g++)` でノード上の実体を選び、`:745` / `:814` で
  `-DCMAKE_C_COMPILER` / `-DCMAKE_CXX_COMPILER` へ渡している。
  `certify_calibration.sh:401,466,506` と `t141_region_profile.sh` も同型
- したがって **B5 の恒久対応は「buildcache の cc/cxx を site 由来で解決する」形**になり、
  `cache_key` は既定と異なる cc/cxx を pre-image へ織り込む (`buildcache.py:132`) ので
  **Pegasus 産バイナリは別 cache key になる = 偽 hit しない**。この性質は本 wave の scope 外だが、
  裁定パッケージの実装案として記録する

## dispatch task の consumer 閉包 (親が独立に洗った。段 2 プランの取り残し検査用)

`TASKS` へ 1 種別足したとき追随が要る面:

- `tools/pegasus/dispatch_compute.py` — `TASKS` 本体、`main()` の `--task choices=tuple(TASKS)`、
  `_interpreter_probe_source`、`_job_run` の二層照合
- `hooks/guard_bash.py:161-169` `_SANCTIONED_PATHS` — 既存 2 entry
  (`tools/run_tests.py` / `tools/check_ai_provenance.py`) はいずれも
  **「login では自分で計算ノードへ dispatch し、compute では実処理する」自己 fail-closed entry** である。
  新 task の child もこの形にしないと第二防壁の exact path 列挙に載らない
- `tools/run_tests.py:829-831` / `tools/check_ai_provenance.py:1018-1020` — 既存の自己 dispatch 呼出の形
- `orchestrator/tests/test_pegasus_dispatch_compute.py` — exact-set assertion と parametrize
- `docs/pegasus-runbook.md` §8 チェックリスト
- `tools/dev_waves/checker.py` — rc=16 (infra) 分岐

**この閉包は (P2-b) 案 (`tools/run_campaign.py` を薄い sanctioned entry として新設) が既存 2 entry と
対称になることを示す。段 2 プランがこれを漏らしていないかを段 3 レンズ B で検査する。**

---

## 訂正 1 — B1 の射程は狭い。かつ (P2-a) は driver を取り違えていた

段 3 起動前に campaign driver 族を横断して PIN を実測した結果、**B1 は `p3_s4_loop.py` 固有であり、
現行軸の兄弟 driver には当たらない**ことが判明した。親の当初記述は過大な一般化だったので訂正する。

| driver | PIN の実体 | 起動可否 |
|---|---|---|
| `p3_s4_loop.py:67` | `PIN = "028f34d"` (literal、歴史的凍結) | **B1 で停止** |
| `p3_s4_loop_sort.py:86` | `PIN = pin.CURRENT_PIN` (= `d706650`) | 起動する |
| `p3_s4_loop_trigger_gating.py:60` | `axis_trigger_gating.py:27` の `PIN = pin.CURRENT_PIN` | 起動する (`:500` `assert_pinned_clean`) |
| `silo_ladder_rung1.py:47` | `d706650cdb31e442bef45b9b4216951d4fb40969` | 起動する |

**さらに重要な取り違え:** ユーザーが挙げた **LLM 4 役 (planner / coder / auditor / critic)** に
対応するのは `p3_s4_loop.py` ではない。同 file の `load_proposal_file` は
`planner, coder, prior_rev` の 3 値しか返さない (auditor 無し) のに対し、
`p3_s4_loop_sort.py:395` と `p3_s4_loop_trigger_gating.py:566` は
**`planner, coder, auditor, prior_rev` の 4 値**を返す。段 8a trigger-gating が現行軸である。
したがって **(P2-a) が指すべき driver は `p3_s4_loop.py` ではなく
`p3_s4_loop_trigger_gating.py` (現行軸) または driver 族**であり、当初の (P2-a) 記述は誤りである。

**訂正後も結論は変わらない部分:** B2 (staging 不在)、B3 (`ENV_TAG="linux-baremetal"` /
`CLK=1800` — `p3_s4_loop_trigger_gating.py:76-77`、`p3_s4_loop_sort.py:87-88` で**族全体に共通**)、
B5 (gcc-13 不在) は依然として全 driver に当たる。よって
**「Pegasus 上で campaign が妥当な計測値を出せない」という生死判定そのものは維持される。**
変わったのは「どの driver が起動段階で死ぬか」であって「completion するか」ではない。

**この訂正が (P2) に与える影響:** 単一 driver を `child_script` に固定する案 (P2-a) は、
**現行軸が sort → trigger-gating と移ってきた事実**と噛み合わない。軸が増えるたびに
`tools/pegasus/dispatch_compute.py` を編集することになり、D103 決定 5 が守ろうとした
「`tools/pegasus/*` を安易に触らない」という趣旨と逆行する。
→ **(P2-b) 薄い sanctioned entry + 閉じた driver enum を支持する第 3 の独立根拠**である。

## 訂正 2 — 親が段 3 前に追加で確定した条件 dispatch の判定

- `BuildResult.configure_argv` / `build_argv` は `s8b_floor_campaign.py:988-1013` と
  `s8b_ratified_freeze.py:183,1655` へ流れる = 凍結成果物族の入力。
  → **B2 の恒久対応は `DW-O09`/`DW-O10` を発火させる** (scope 外にした判断の裏付け)。
  → **本 wave は `buildcache` を触らないので O09/O10 は発火しない**
- `env_allowlist` は `_dispatch_impl:983-986` で **親環境から allowlist key だけを通す濾過**である。
  `s3_lock_coverage.py:24` は「裸マクロ `IZANAGI_BREAK_*` は `CCBENCH_` 名前空間外ゆえ
  pipeline からは定義不能 = 規律 2 の構造的防壁」と明記している。
  allowlist は **login 側の環境が計算ノードの子へ届く新チャネル**なので、
  **consumer の file:line が実在する変数だけ**に限る (推測ゼロ)
- 既存テストは `:1404` exact-set と `:1558-1560` parametrize がともに literal 列挙で、
  `:1580` が `argv[1] == str(_REPO / "tools" / script)` と `tools/` を固定している。
  → child_script が `orchestrator/campaign/...` だと既存テスト構造で表現できない
- `walltime` は `dispatch(..., walltime=)` の引数かつ CLI `--walltime` (`:1422`, `:1509`)。
  長時間 campaign の walltime は **enum ではなく caller が渡す**のが正しい配線
