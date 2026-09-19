# [T-2766] shard 内 pairing (collection 順 49〜96 位を最小 cost の 48 unit に) を同一 tip の実受入 (3 shard、計算ノード) で A/B 逐次交互の隣接対 3 組で対比較した — 3 対とも B (pairing on) が短く、最遅 shard の wall の対差は 101.7 / 112.9 / 144.3 秒 (対差の中央値 112.9 秒、対率の中央値 24.2 %、条件別中央値差 112.9 秒)、事前登録の判定は (i) 方向一致・閾値以上。効果は shard-0 だけに出て shard-1/2 は 1〜3 秒差、B では `[ccbench-current]` e2e の worker の 2 個目が cost 0.0 の partner になった (witness 3 shard × 4 走で一致)。A の律速 worker (386〜411 秒、13〜34 item) の中身は未観測で機序は未同定。採否は諮る (本 wave は採用しない、実装は main に入れず impl branch に保存)

一次資料 (wave `dev-wave-t2766-pairing-ab`、measurement tip `0eabe67bad429403a2eadfddcac4c1252d55dda3` = local main `a99425b66` + docs commit `ec6dd64c4` + 実装 commit `0eabe67ba`、測定 2026-09-20 02:03〜05:11 JST)。段 1〜4 の逐語は同 dir の `s1-brief.md` / `s2-plan.md` / `s4-ruling.md`、段 3 相談・段 5 author・段 6 レビュー・fix・焦点再レビューの逐語は `verbatim/`、集計は `analysis/` (射影)、走ごとの記録は `runs/`。**受入証跡ではない** (land 用の受入受領証は段 9 の land が持つ)。実装は main に入れない (§8)。

## 1. 依頼・不変条件・結論

依頼 (D2148 項 6、2026-09-18 ユーザー裁定「推奨通りで」、command 引数): shard 内 pairing を同一 tip の実受入で A/B 交互 3 対以上・計算ノードで対比較し、中央値差と対の数で記録する。replica (T-2710) の 52〜69 秒差は採用効果ではない。受理集合・成分粒度は維持し、実装を採用済みとして本番に入れない。改善認定は同 job の対でだけ行う。scope 外 = e2e の分割・別系列への移動・新 slot / FIFO。

不変条件を守った: 受理集合 (selected / hold / group / unit 境界) は変えていない。pairing は既定 off の opt-in (env `IZANAGI_ACCEPTANCE_PAIRING_V1` の exact token `t2766-min-cost-partners` でだけ発火、他の非空値は `UsageError`) で、未設定の経路は現行と同一順序・同一 property (G12 の固定 literal 負例、変異 M3 で固定)。測定中は自分の他 job を走らせていない (D357)。判定規則は結果を見る前に固定した (`s4-ruling.md` §事前登録)。全測定走は同一 SHA (`0eabe67ba`) で、投入直前・終了後の HEAD と clean を照合した。

結論 (数値は §5〜§6、判定規則は事前登録どおり):

1. **有効 3 対とも B が短い。** 最遅 shard (3 対とも shard-0) の JUnit wall W_max の対差 ΔW = W_max(A) − W_max(B) は 101.7 秒 (対 2、A→B) / 112.9 秒 (対 3、B→A) / 144.3 秒 (対 4、A→B)、対率 r = 22.4 % / 24.2 % / 30.0 % (各対とも D357 の 1 走比較で |r| ≥ 10 %)。対差の中央値 112.9 秒、対率の中央値 24.2 %、条件別中央値差 med W_max(A) 465.5 − med W_max(B) 352.7 = 112.9 秒。事前登録の判定 = **(i) 方向一致・閾値以上** → 採否の裁定パッケージをユーザーへ返す (§7)。3/3 一致は有意差判定ではない。
2. **効果は shard-0 だけに出た。** shard-1 の W は A 232.3 / 233.2 / 233.8 vs B 230.6 / 231.8 / 232.5、shard-2 は A 173.0 / 171.0 / 170.4 vs B 174.4 / 171.7 / 171.4 で 1〜3 秒差。shard-0 の残差 F = W − O は A/B とも 69〜70 秒 (T-2710 の warm cache 受入 67 秒と一致、warm-up 成立)。差はすべて最忙 worker の占有 O に入る: A 385.6 / 395.9 / 410.8 秒 vs B 283.0 / 282.3 / 265.9 秒。
3. **B の発火と実配布 (witness):** B 4 走 × 3 shard の全 12 shard で、junit property の被覆 100 %、rank 48〜95 の item 集合 = partner 集合、head の (cardinality, cost) 多重集合と partner の cost 多重集合が `selected` + 台帳からの独立再計算と一致 (partner 48 unit の台帳 cost は 0.0〜0.001、shard-0 は 0.0 が 29 個)。shard-0 で台帳 cost 最大の singleton unit `[ccbench-current]` (台帳 240、実測 197〜219 秒) は 4 走とも worker gw5 が走らせ、その 2 個目の unit は `test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases` (partner、台帳 0.0、実測 0.0 秒) だった。A 側の witness は無く (property 0 件を検証)、A の律速 worker の中身は未観測。
4. **A は同時刻の他 wave の受入 (待ち手経由 = 本番 A 相当) の分布の内側、B はその外側 (下)。** 02:11〜05:07 JST の他 wave 9 session の shard-0 W は 378.8〜563.3 (中央値 481.1)、最忙 worker は 8〜92 item / 309〜434 秒。本 wave の A (454.7 / 465.5 / 480.6) は分布内、B (362.3 / 353.0 / 352.7 / 336.3) は全 9 session より短い (tip は wave ごとに違うので記述的対照)。
5. **機序は未同定。** pairing が変えるのは realized order の 49〜96 位だけで、相方 (T-2710 で ≈ 20 秒) の除去では 100 秒超の O の差を説明できない。A の律速 worker (13〜34 item、386〜411 秒) の item 列は A に witness が無いため復元できない。T-2710 §6 の説明仮説「cost 2 位以下の重い unit (t080 系、shared base を待つ) が base 構築と同時に走らなくなる」と整合するが、本 wave では検証していない (§7 の限界)。
6. **順序依存の赤は観測しなかった。** B 4 走とも 3 shard 緑 (failed / error 0)。「順序依存 test の不在」ではなく「今回の B 走で順序依存失敗を観測しなかった」まで。
7. **実装は main に入れない。** 効果の有無にかかわらず本 wave の裁定 (`s4-ruling.md` P2) どおり、landing は記録 (本 dir + spool fragment) だけ。実装 commit `0eabe67ba` は branch `impl-t2766-pairing-optin` に保存 (§8)。採否の裁定は §7。

## 2. 実装 (opt-in、Codex author、commit `0eabe67ba`、impl branch `impl-t2766-pairing-optin`)

| 面 | 変更 |
|---|---|
| `orchestrator/tests/conftest.py` | 定数 4 つ (`_ACCEPTANCE_PAIRING_ENV` / `_ACCEPTANCE_PAIRING_TOKEN` / `_ACCEPTANCE_PAIRING_PROPERTY_PREFIX` / `_ACCEPTANCE_PAIRING_HEAD_UNITS = _ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS // 2`)、`_acceptance_pairing_opted_in()` (`_growth_holds_opted_in` と同型: 未設定 / 空 → False、exact token → True、他 → `UsageError`)、`_pair_initial_distribution_units(ordered_units, unknown_cost)` (realized = cardinality 安定 sort (xdist 3.8.0 `loadscope.py` `schedule()` と同一式) → head 48 固定 → 候補中 `(effective_cost, realized 位置)` 昇順 48 を partner → rest (realized 順) → 再 sort で scope 列不変を検算、不成立は `UsageError("acceptance pairing infeasible …")`、unit < 96 は無変更)、`_reorder_acceptance_items_by_duration(items, durations, workerid="")` が opt-in 時だけ後段関数を呼び全 item の `user_properties` に `izanagi_acceptance_pairing_v1_{scope,rank,partner,worker}` を extend、hook が `workerinput["workerid"]` を渡す (+78 −3 行) |
| `tools/pegasus/dispatch_compute.py` | `TASKS["tests"].env_allowlist` に `IZANAGI_ACCEPTANCE_PAIRING_V1` (login → 計算ノードの request env 伝播、+2 行) |
| `orchestrator/tests/test_acceptance_schedule_order.py` | G12 (9 本、+275 行): 正例 (実 `LoadGroupScheduling` の dequeue trace [48:96] = 固定 partner 列、[:48] 不変、rest 元順、property 4 種)、負例 (未設定 / 空文字 = 固定 literal collection 列・identity・marker・selected 不変・property 不在、別値 = `UsageError`、cardinality 不成立 (2 item unit 49 個の fixture) = `UsageError`)、境界 (unit < 96 無変更、nproc 16/32/48 で collection 同一)、junit 到達 (pytester `-n 1 --dist loadgroup`、skip にも property、worker = gw0)、hold / selected / real-repo suffix の保全 (**局所検査**: hook の yield 前後を通すが実 shard plugin の `allocate` / digest は通していない — レビュー A must-fix 1。統合の証拠は §4 の A/B 実受入の緑であり、実 selected / digest の A/B 同一性の統合 test の代替ではない)、実配布の反例 (3 item 初期 unit の worker は最初の `_reschedule` で 2 個目を飛ばされ後で rest を受ける、2 item の worker の 3 個目も rest) |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | exact pin に 1 key 追加、request 生成に token が載る test 1 本 (+21 行) |

親の焦点走 (計算ノード、6 file: schedule_order / dispatch_compute / hold_inventory / run_tests_shards / real_repo_serialization / run_tests_preflight): 初回 (job 10757) 968 passed / 3 failed (test harness `_OptionConfig` の `config.args` 欠落、`verbatim/focus1-summary.txt`) → fix1 (Codex、test file だけ、`verbatim/s6-fix1.md`) → **971 passed / 1 skipped / 0 failed** (`verbatim/focus2-summary.txt`)。

## 3. 変異 matrix (DW-M01、独立 clone `mutation-source` (D1009)、commit `0eabe67ba`、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_acceptance_schedule_order.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf`、計算ノード)

probe 走 (全件 SURVIVED 期待で観測 node を集める、spec sha256 `810d380c…`、`mutation-spec-probe.json` / `mutation-expected-nodes.json`) → final 走 (期待 node 登録、spec sha256 `22713c0d…`、`mutation-spec-final.json` / `mutation-final-results.json` / wrapper receipt / attempts)。**baseline PASSED、6/6 KILLED、期待 node 完全一致 (MISMATCH 0)、wrapper rc=0 (共有木不変)。**

| # | 変異 (1 理由) | 位置 | kill した node (完全集合) | 帰属 |
|---|---|---|---|---|
| M1 | partner 選択の sort key を昇順 → 降順 | `_pair_initial_distribution_units` の `entry[1]["cost"] … unknown_cost` | G12 正例・worker 数非依存・配布反例・cardinality 負例・junit 到達 (5) | 固定 partner 列の不一致 (cardinality 負例は partner が 2 item 側に移り検算が通るため) |
| M2 | head 幅 `width` 48 → 47 (共通幅) | 同関数 `width = _ACCEPTANCE_PAIRING_HEAD_UNITS` | G12 正例・worker 数非依存・配布反例・junit 到達 (4) | head の完全一致と partner 境界 |
| M3 | opt-in 判定を恒真 | `_acceptance_pairing_opted_in` | G12 off 負例 (unset / empty)・hold 保全 [A]・既存 G6 / G8 / G10 (6) | 未設定で固定 A collection 列が変わる |
| M4 | cardinality 検算を削除 | 同関数の `if scopes(sorted(paired, …)) != scopes(paired)` | G12 cardinality 負例 (1) | 指定例外が出ない |
| M5 | property 付与を削除 | reorder 関数の `if "pairing_rank" in unit:` | G12 正例・hold 保全 [B]・junit 到達 (3) | property 4 種の欠落 |
| M6 | allowlist の key を削除 | `dispatch_compute.py` `TASKS["tests"].env_allowlist` | exact pin・request 伝播 test (2) | 実 allowlist の欠落 (全段伝播の検出とは呼ばない) |

## 4. 測定手順 (実際に実行した手順)

- **投入形:** 測定走は待ち手 `tools/dev_wave_wait.py acceptance` を使わず、wave worktree (HEAD = `0eabe67ba`、clean) から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` (空 argv の受入形、Pegasus LOGIN の明示 shard mode → `_dispatch_result(shard_count=3)`) を直接投入した。理由: 待ち手は claim 直後に local main を取り込む (post-claim merge、runbook §7.3) ため隣接 2 走でも tip が変わり「同一 tip」を破る (段 3 相談 A1)。差 = lease / merge / receipt / launcher の main blob 実行が無いだけで、dispatch・shard child・`tools.acceptance_shards`・session dir は受入と同一経路。**測定対象は直接投入による実受入 shard の W / O であり、待ち手経由の受入総経過時間ではない** (レビュー B)。
- **launcher** `run-measure.sh` (親、`probe-source.md`): job dir の flock を最初に取り (直列化)、門番 (他 session の `dev_wave_wait.py … acceptance` 待ち手 ≤ 1 かつ 1 分 load < 30、100〜140 秒周期で 2 回連続 + 0〜45 秒乱数 → 再判定) が開いてから HEAD == measurement tip と clean (`--untracked-files=all --ignore-submodules=none` = 0 行) を照合し、RUN dir を作って投入 (未投入停止は `aborts/` へ)。終了後に clean / HEAD を再記録、session の 3 shard `junit.xml` / `report.json` を sha256 付きで複製 (`runs/<走>/SHA256SUMS`)、`run.json` を書く。B は `IZANAGI_ACCEPTANCE_PAIRING_V1=t2766-min-cost-partners`、A は unset。`PYTHONDONTWRITEBYTECODE` は明示 unset (計算ノード既定 "1"、`env.txt` に `PYTHONDONTWRITEBYTECODE_SET=no` を記録)。`output/pegasus-dispatch/` (gitignore 済み、dispatch 自身の制御 file) は clean 判定の対象外。
- **warm-up:** login の admission が headroom 0 (user cgroup 16 GiB に対し 15.3 GiB 使用) で local を出さなかったため、`PYTHONDONTWRITEBYTECODE=` (空 = 「書かない」指定を外す) を allowlist 経由で計算ノードへ渡した collect-only 1 走 (job 10843 の次の走) で共有 FS の `orchestrator/tests/__pycache__` を温めた (391 pyc、うち pytest 書換 364、`run-warm2.sh`)。A/B とも同じ warm 状態から開始した (shard-0 の F ≈ 69〜70 秒が warm 受入の 67 秒と一致)。page cache・fixture の warm は保証しない。
- **順序:** 対 1 = A,B / 対 2 = B,A / 対 3 = A,B。無効対は同順序で追加 (slot を消費しない)。有効 3 対で固定終了、測定走上限 12。実行列: 01-A (無効、§5) → 02-B → (03-B は門番待ち中に止め、未投入) → 03-A → 04-B → 05-B → 06-A → 07-A → 08-B。投入時刻は走番号順に単調 (集計器が検算)。
- **集計:** `t2766_ab_analyze.py` (Codex author、job dir、repo へ入れない、逐語と sha256 は `probe-source.md`) — 走表・対表・3 種の中央値・witness の独立検算 (被覆、rank 48〜95 = partner、head の (cardinality, cost) 多重集合と partner の cost 多重集合を `selected` + 台帳から `isclose(rel 1e-9)` で再計算、worker 別 item 列 → unit 列、2 個目 unit、台帳 cost 最大 unit と実測最長 unit)、tip / clean / 順序 / 欠番 / 上限 / 複製 / 投入時刻 / env の検算、事前登録の判定。`--selftest` PASS。出力の原本 (`analysis.json` 89 MB、`analysis.md` 84 MB、item 列全件を含む) は job dir、本 dir の `analysis/analysis-compact.json` は item 列 (`worker_item_sequences` 等 24 field) だけを落とした射影 (原本 sha256 と落とした field は同 file の `_projection`)、`analysis/analysis-tables.md` は原本 md の表部 (先頭 75 行)。

## 5. 走表 (shard-0 = 最遅 shard、W = JUnit testsuite time、O = 最忙 worker の占有、F = W − O、時刻 JST)

| 走 | 条件 | slot | 投入 → 完了 | shard-0 node | W_0 | O_0 | F_0 | 最忙 worker (item 数) | W_1 | W_2 | W_max | 他 leader / load1 | 有効 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-A | A | 1 | 02:03:24 → 02:08:24 | bnode011 | — | — | — | — | — | — | — | 1 / 5.78 | **除外**: rc=16 `dispatch-infrastructure` — 3 shard とも xdist worker が receipt memo prewarm の `TimeoutError: memo publication timeout` (`IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1`) で INTERNALERROR、`report.json` 無し (`runs/01-A/chain.log`)。A 側の環境要因で pairing とは無関係。対 1 を無効にし slot 1 を同順序で取り直した |
| 02-B | B | 1 | 02:11:16 → 02:18:10 | bnode014 | 362.281 | 292.0 | 70.3 | gw35 (4) | 258.847 | 205.937 | 362.281 | 1 / 19.84 | 有効 (対 1 は 01-A の無効で不採用) |
| 03-A | A | 1 | 03:04:47 → 03:13:10 | bnode009 | 454.716 | 385.6 | 69.1 | gw46 (34) | 232.251 | 173.024 | 454.716 | 1 / 5.41 | 有効 |
| 04-B | B | 1 | 03:15:17 → 03:36:02 | bnode012 | 353.010 | 283.0 | 70.0 | gw40 (15) | 230.621 | 174.426 | 353.010 | 0 / 2.04 | 有効 |
| 05-B | B | 2 | 03:38:32 → 03:50:58 | bnode011 | 352.669 | 282.3 | 70.4 | gw40 (68) | 231.829 | 171.746 | 352.669 | 1 / 2.15 | 有効 |
| 06-A | A | 2 | 03:53:27 → 04:17:33 | bnode011 | 465.540 | 395.9 | 69.7 | gw1 (13) | 233.172 | 171.044 | 465.540 | 0 / 1.89 | 有効 |
| 07-A | A | 3 | 04:20:10 → 04:45:18 | bnode011 | 480.574 | 410.8 | 69.8 | gw1 (24) | 233.817 | 170.415 | 480.574 | 0 / 3.78 | 有効 |
| 08-B | B | 3 | 04:48:01 → 05:10:53 | bnode017 | 336.250 | 265.9 | 70.3 | gw14 (116) | 232.475 | 171.382 | 336.250 | 0 / 3.56 | 有効 |

投入 → 完了は login 側の外側 wall (queue 待ちを含む。所要の正は各 shard の JUnit time)。shard-1 / shard-2 の node は `runs/<走>/run.json` の `session_dir_origin` (job dir の原本) と `analysis/analysis-compact.json` の `receipt`。他 leader = 投入時点の他 session の `dev_wave_wait.py … acceptance` 待ち手の本数 (検索式は `run.json` の `gate.leader_query`)。B 4 走の 3 shard × 4 = 12 shard の witness はすべて一致 (§6)。赤 (failed / error) は A / B とも 0。

### 対表と判定

| 対 | slot / 期待順序 | 走 | W_max(A) | W_max(B) | ΔW (秒) | r = ΔW / W_max(A) | D357 (1 走比較) |
|---|---|---|---|---|---|---|---|
| 1 | 1 / A,B | 01-A, 02-B | — | 362.281 | — | — | 無効 (01-A) |
| 2 | 1 / A,B (取り直し) | 03-A, 04-B | 454.716 | 353.010 | **101.706** | **22.4 %** | ≥ 10 % |
| 3 | 2 / B,A | 05-B, 06-A | 465.540 | 352.669 | **112.871** | **24.2 %** | ≥ 10 % |
| 4 | 3 / A,B | 07-A, 08-B | 480.574 | 336.250 | **144.324** | **30.0 %** | ≥ 10 % |

- 対差の中央値 = 112.871 秒、対率の中央値 = 24.2 %、条件別中央値差 = med W_max(A) 465.540 − med W_max(B) 352.669 = 112.871 秒 (3 つは別量。今回は対 3 が中央なので対差と条件別中央値差が一致した)。
- 事前登録の判定: 有効 3 対、全対 ΔW > 0、med r = 24.2 % ≥ 10 % → **(i) 方向一致・閾値以上**。閾値 10 % は本 wave 独自の保守基準 (D1260 の採用条件と同型) で D357 からの導出ではない。3/3 一致を有意差判定にしない。
- 隣接対は同 job / 同 allocation ではない (別々に 3 shard を dispatch した逐次の隣接対)。node は対内で異なる (対 3 は 05-B / 06-A とも shard-0 が bnode011、対 4 は 07-A が bnode011 / 08-B が bnode017)。D104 決定 4 の「同一 allocation 内の paired 比較」を満たしたとは書かない。

### 同時刻の対照 (他 wave の待ち手経由の受入、02:11〜05:07 JST、`/work/1/SFC/tanab/.izanagi-acceptance-shards/` の 93 session 集計と同じ定義、記述的)

他 wave の 9 session の shard-0: W = 452.7 / 563.3 / 378.8 / 474.5 / 504.1 / 387.5 / 481.1 / 481.2 / 489.1 (中央値 481.1、最小 378.8、最大 563.3)、最忙 worker は 8〜92 item / 309.1〜433.2 秒、赤 0〜1。本 wave の A 3 走 (454.7 / 465.5 / 480.6) はこの分布の内側、B 4 走 (362.3 / 353.0 / 352.7 / 336.3) は全 9 session より短い。tip は wave ごとに違うので同等性の証明ではない。T-2710 の 93 session (2026-09-17〜18、W 中央値 369.0、最忙 worker item 2 個) とは regime が違う (本夜は最忙 worker が 8〜34 item / 386〜434 秒)。

## 6. witness (B の発火と実配布、`analysis/analysis-compact.json` の各 shard `witness`)

- 検算 (B 4 走 × 3 shard = 12 shard すべて): property 付き testcase 数 == `selected` 件数 (skip 込み)、rank が 0..unit 数−1 を被覆、rank 48〜95 の item 集合 == partner="1" の集合、head (rank 0〜47) の (cardinality, cost) 多重集合 == `selected` + 台帳から再計算した realized order の先頭 48、partner の cost 多重集合 == 候補中最小 48 (`isclose`)、rank 順の cardinality が非増加、worker property の集合と item 数 == `report.json` の `worker_occupancy`。A 3 走 × 3 shard は property 0 件。
- partner 48 unit の台帳 cost: shard-0 = 0.0〜0.001 (0.0 が 29 個)、shard-1 = 0.0〜0.001 (0.0 が 2 個)、shard-2 = 0.0〜0.001 (0.0 が 5 個)。
- shard-0 の台帳 cost 最大の singleton unit `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` (台帳 240.0、実測 219.1 / 215.2 / 213.4 / 196.9 秒) は B 4 走とも gw5 が走らせ、2 個目の unit は rank 49 の `orchestrator/tests/test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases` (partner、台帳 0.0、実測 0.0 秒)。**意図した相方の除去は実配布で成立した。** ただし B の shard-0 の最忙 worker は gw5 ではなく gw35 / gw40 / gw40 / gw14 (266〜292 秒、4 / 15 / 68 / 116 item) で、律速はこの e2e の worker ではない。
- 台帳 cost 最大の unit は `real-repo` group (台帳 550.0 だが実測 10〜11.5 秒、gw0) で、台帳と実測の乖離が大きい。shard-1 の最忙は 4 走とも gw0 の `p3-b4-material-report` group (50 item、167〜170 秒)、shard-2 の最忙は 105〜141 秒の多 item worker で、shard-1 / 2 では A/B の差が出ない (§1 結論 2)。
- 主張範囲: property は「collection 変換の発火」と「item → 実行 worker」の対応を証言し、worker 別の列は JUnit 出現順からの復元 (初期配布の送信順ではない)。「全 worker の 2 個目が最小」は主張しない (実 scheduler の反例は G12 で固定)。A の実配布は `worker_occupancy` (item 数・占有) だけ。

## 7. 採否の裁定パッケージ (提案。採用済み判断ではない) と残存限界

前提: 実受入 (直接投入) の隣接対 3 組で B が 102〜144 秒短く、最忙 worker の占有が A 386〜411 → B 266〜292 秒。機序は未同定。B でも 300 秒目標 (T-2273) には届かない (336〜362)。実装は opt-in で impl branch にあり、採用 = 既定 on (env 不要) にする変更が別途要る。

| 択 | 内容 | 受理集合 | 費用 | 失う / 残る不確実性 |
|---|---|---|---|---|
| (a) 採用 | opt-in を既定 on (env gate と property を外すか、property は残す) にして main へ入れる。採用 wave で待ち手経由の実受入 (A = 採用前 main、B = 採用後) を隣接対 3 組で再測定し、効果が消えていれば land しない | 触れない (順序だけ) | 実装 wave 1 本 (Codex author、G12 の負例を既定 on 用に書き直す) + 受入 3 対 | 機序未同定のまま採る。regime (本夜 A ≈ 455〜481) が変われば効果量は変わりうる。property を残すなら junit が 4 property × item 分 (≈ 数百 KB / shard) 増える |
| (b) 条件付き採用 | (a) の前に機序調査 1 wave (A に witness を付けて律速 worker の item 列を取り、T-2710 §6 仮説 = 49〜96 位の t080 系 unit の shared base 待ちを検証) | 触れない | 調査 wave 1 本 (impl branch の opt-in を A 側にも witness だけ付ける変異で再測) | 採用が 1 wave 遅れる。機序が分かっても効果量は変わらない |
| (c) 見送り | opt-in のまま impl branch に置き、300 秒目標は別の律速 (T-2786 base 構築の内訳) を先に | — | 0 | 毎受入 100 秒級の短縮を使わない |

推奨は **(a)** (効果は 3 対とも同方向で 100 秒級、受理集合に触れない、撤去は並べ替えの削除だけ)。(b) は (a) の採用 wave に「A 側 witness」を足す形で相乗りできる。

残存限界・未実測:

- 機序未同定 (§1 結論 5)。A の律速 worker の中身は未観測。
- 隣接対は同 allocation でなく、node も対内で異なる。同時刻の他 wave の対照は tip が違う記述的対照。
- 有効 3 対 (上限 12 走のうち 8 走投入、1 走無効)。3/3 は有意差判定ではない。regime 依存 (本夜は最忙 worker が多 item の regime で、T-2710 の 2 item regime とは違う)。
- 直接投入と待ち手経由の差 (lease / merge / receipt / launcher) は測定対象外。W_max は queue 待ち・開始ずれを含む受入総経過時間ではない。
- 順序依存の赤は B 4 走で観測しなかっただけ。hold / selected の保全 test は局所検査 (§2)。
- warm-up は bytecode cache だけ。page cache・fixture の warm は保証しない。
- 01-A の `memo publication timeout` は環境要因として除外したが原因は未調査 (receipt memo prewarm の共有 FS 待ち)。

## 8. 再現資料・成果物対応

- **実装:** commit `0eabe67bad429403a2eadfddcac4c1252d55dda3` (branch `impl-t2766-pairing-optin`、親 `ec6dd64c4` ← main `a99425b66`)。差分 4 file (+373 −3 行)。patch の sha256 (fix1 後の累積、`codex/s5-author.patch` = job dir): `git diff a99425b66 0eabe67ba -- orchestrator/tests/conftest.py tools/pegasus/dispatch_compute.py orchestrator/tests/test_acceptance_schedule_order.py orchestrator/tests/test_pegasus_dispatch_compute.py` で再生成できる。impl branch の所有者は本 wave、用途は採否裁定後の採用 wave の起点、再訪 / 撤去は採否の裁定時 (ユーザー指示なしに消さない)。
- **台帳:** `orchestrator/tests/acceptance_duration_ledger.json` (tip `0eabe67ba`、sha256 `1edbb7929a7b341e050fd37ea32f19c93f4d63d8f95afd760018b7cf7ac3273a`、24,379 nodeid)。
- **集計器・launcher:** `probe-source.md` (逐語 + sha256: `t2766_ab_analyze.py` `c5ac201f…` 45,368 byte、`run-measure.sh` `7e46d632…`、`run-series.sh` `32277084…`、`run-warm2.sh` `16fa4ce7…`、`run-mutation.sh` `68b6783b…`)。再集計: `python3 t2766_ab_analyze.py --runs-root <job dir>/runs --ledger <台帳> --out <dir> --measurement-tip 0eabe67bad429403a2eadfddcac4c1252d55dda3`。
- **raw 成果物 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/`):** `runs/<NN>-<X>/{run.json, env.txt, chain.log, gate.log, child.log, session/shard-{0,1,2}/{junit.xml, report.json, dispatch/receipt.json}, session/SHA256SUMS}` (本 dir の `runs/` は run.json / env.txt / chain.log / SHA256SUMS の写し)、`analysis/analysis.{json,md}` (原本、sha256 は `analysis/analysis-compact.json` の `_projection`)、`aborts/` (未投入停止の記録)、`codex/` (prompt・log・artifact)、`mutation-*` (変異の spec・台帳・receipt)、`focus/` (焦点走の log)。元 session (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/`) の path は各 `run.json` の `session_dir_origin`。
- **変異:** `mutation-spec-final.json` (sha256 `22713c0d…`)、`mutation-final-results.json`、`mutation-final-results.json.wrapper-receipt.json`、`mutation-final-attempts.json`、`mutation-spec-probe.json` (sha256 `810d380c…`)、`mutation-expected-nodes.json`。
- **起動手順:** §4。順序 (A,B / B,A / A,B) と slot は `run-series2.sh` (job dir) のとおり。

## 9. レビュー・裁定の逐語

- 段 3 相談 (2 レンズ 1 本、gpt-6-astra medium、21:39〜21:45): `verbatim/s3-consult.md` — must-fix 5 (A1 同一 tip、A2 判定規則、A3 witness の独立再構成、B1 cardinality 負例、B2 A 不変検査)、should 7、nit 1。すべて real・採用 (`s4-ruling.md`)。
- 段 5 author: `verbatim/s5-author.md` (pytest は sandbox で起動不能 → 親の焦点走)。fix1 (test harness): `verbatim/s6-fix1.md`。
- 段 6 レビュー A (正しさ境界): `verbatim/s6-reviewA.md` — must-fix 2 (hold 保全 test が実 shard plugin を迂回、集計器の 2 個目 unit)、should 3、nit 1。レビュー B (過剰・削除・実効性): `verbatim/s6-reviewB.md` — must-fix 4 (直列化、tip / clean 照合、順序 / 再試行 / 上限、複製成果物)、should 6、nit 2。
- fix2 / fix3 (集計器): `verbatim/s6-fix2.md` / `verbatim/s6-fix3.md`。焦点再レビュー: `verbatim/s6-focus.md` — closed 7 / partial 3 / regressed 1 (ロック前の RUN dir 作成) → launcher を改訂 (flock を最初に、RUN dir は投入直前に `mkdir`、未投入停止は `aborts/` へ、複製 / JSON 失敗は rc 96 / 97、`PYTHONDONTWRITEBYTECODE` の明示 unset と記録)、集計器 fix3 (投入時刻の単調性・逐次性、bytecode env の検査)。
- 親の裁定 (段 6): A-must1 は real だが対表・判定を変えないので fix せず §2 で test の射程を「局所検査」と限定した。N1 (cardinality 検算の縮約) / N2 (Markdown の JSON 重複) は成果物不変のため不採用。
- 変異 probe の観測 node と final の期待 node は完全一致 (§3)。
