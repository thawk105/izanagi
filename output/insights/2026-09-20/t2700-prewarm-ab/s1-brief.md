# 段 1 brief — [T-2700] receipt memo prewarm 早期起動の実受入 A/B 対比較 (必要走数の見積り + 対照走)

wave `dev-wave-t2700-prewarm-ab`、branch `worktree-dev-wave-t2700-prewarm-ab`、着手 tip = local main `b7f970dfa` (2026-09-20 07:20 JST、fresh worktree、起動 gate rc=0)。専用 handoff は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/HANDOFF.md`。

## 研究前進 (土台)

受入全走の最遅 shard の wall が 1 wave あたり 6〜8 分を占め、T-2616 (entry 1546) は receipt memo の prewarm を collection 前の thread へ移して 289.1 秒 (n=1) を得たが同時刻の対照が無く、D1936 項 35 は「prewarm 等は効果を先に測る」と定める。完了判定 = (1) 必要走数を過去 session の実測から見積もり、(2) 同一 SHA・同一窓で「早期起動あり (E) / なし (L)」を交互に直接投入した隣接対を見積り数だけ取り、事前登録の規則で対差・中央値・方向を記録する。効果が示せなくても、必要走数が確定できなくても、その旨を insight に残すことが成果物 (依頼文)。

## scope と確定済みユーザー裁定

- 依頼 (command 引数): まず何走必要かを見積もる → 同じ窓で E/L を交互投入する対照走を計算ノードで取る (T-2766 の型 = D2164 決定 1: 同一 SHA の wave worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入し最遅 shard の wall を対で比べる)。prewarm の義務化・launcher の自動検査・実装変更は含めない (D1936 項 35)。新 gate・台帳・一般化は scope 外。規律 2 を緩めない。
- 既存被覆 (純増だけ書く): D518 (prewarm barrier は test 実行前)、D2061 / D2062 (早期 prewarm の発火条件と待ち = T-2616 の設計)、D357 (受入 wall の主張は同一 tip 反復の中央値)、D1620 (測定面 = 最遅 shard の wall)、D2164 (直接投入の型と impl branch 運用)。entry 1546 は E の 1 走 (289.1 秒) だけで対照なし。**本 wave の純増 = (i) 過去 session からの機序の定量化と必要走数の見積り、(ii) E/L の同一 SHA 隣接対 n 組、(iii) 腕の witness (stderr の `IZANAGI_MEMO_PREWARM_V1` 行の hook 名)。**

## 前提実測 (brief 前、`/work/1/SFC/tanab/.izanagi-acceptance-shards/` 2026 session の stderr + report.json + junit)

- 早期起動なし (L 経路 = `pytest_xdist_node_collection_finished` で controller が同期 prewarm、09-14〜16 の 177 session、shard-0 だけ発火): session 開始 → collection 完了 H 中央値 56.3 秒、→ 配布開始 (最初の test 開始) D 中央値 86.9 秒 (p10 81.8 / p90 120.6)、D − H = 30.5 秒 (p10 25.6 / p90 40.4) ≈ prewarm の解決所要 rm 32.6 秒 (p10 28.8 / p90 42.6)。この間 worker は idle。
- 早期起動あり (E 経路 = `pytest_configure_node` の thread、09-20 の 13 shard、3 shard とも発火): H ≈ D 中央値 60.0 秒 (sd 1.8)、rm 中央値 55.5 秒 (collection と並走するぶん解決が遅い: 全 1030 shard の中央値 55.3、p90 70.8、最大 279.6 秒)。
- **機序からの効果予測: shard-0 の配布開始が ≈ 27 秒早まる (86.9 − 60.0)。shard-1/2 は L では発火せず (consumer node が無い) E では 60 秒まで待つので E が ≈ 4 秒不利だが、shard-0 が最遅 (W 476 vs 236 / 200) なので W_max には効かない。** これは日付も tip も違う記述的推定であり、本 wave の測定で置き換える。
- 分散 (同一 tip・同夜・隣接走の W_max、T-2766): A 腕 sd 13.0 (n=3)、B 腕 sd 10.8 (n=4) → 対差の SD σ_d ≈ √2 × 11.8 ≈ 17 秒。L の D は load で伸びる裾を持つ (sd 13.9) ので σ_d は 20 秒程度まで見る。
- 検出力 (Monte Carlo、対応のある t 両側 5 %、`power.py`): δ=27 / σ_d=17 → 4 対 0.58、5 対 0.76、**6 対 0.87**、8 対 0.97。δ=27 / σ_d=20 → 6 対 0.75、8 対 0.91。δ=20 / σ_d=17 → 6 対 0.64、8 対 0.81。全 n 対同符号の片側 exact p = 1/2ⁿ (6 対 0.0156)。P(全 6 対が正 | δ=27, σ=17) = 0.71。
- **見積りの結論: 有効 6 対 (12 走) を目標にする。** 予測効果 (27 秒) に対し検出力 0.75〜0.87、T-2766 の 3 対 (検出力 0.35) では不足。8 対は所要 (1 走 ≈ 8〜25 分、門番待ち込み) が 5 時間超になるので、6 対で足りなければ (σ_d が 25 秒超なら) その旨と追加必要数を insight に残す。
- 現行コードに早期起動を止める切替は無い (`conftest.py` `_early_memo_selected`: shard mode + 非 narrowing で無条件 True)。既存 test (`test_real_repo_serialization.py` `test_early_memo_starts_before_worker_collection_notification` 等) が発火を pin しているので、無条件に止める変異は L 腕の受入を赤にする。
- T-2766 の 01-A は E 腕の `memo publication timeout` (早期待ち 120 秒超過、rc=16) で無効になった。全 1030 shard の rm 最大 279.6 秒はこの失敗型の存在を示す。

## 不変条件

1. 受理集合・hold・group・順序を変えない。L 腕の切替は prewarm の**起動時点**だけを変え、prewarm の内容 (解決結果・cache path・fail-closed) は変えない。
2. 切替は既定 off の opt-out (env exact token、他の非空値は `pytest.UsageError`、`_growth_holds_opted_in` と同型)。E 腕 (env 未設定) の挙動は現行と同一で、既存 test は両腕で緑。切替の実装は main に入れない (impl branch 保存、D2164 決定 3 の型)。
3. 測定中は自分の他 job を走らせない (D357)。E/L は逐次・交互、1 対 = 隣接 2 走、同一 SHA の wave worktree から直接投入、走行中は worktree に 1 byte も書かない。
4. 判定規則は結果を見る前に固定する (§事前登録)。D357 の 10 % 規則は 1 走比較の規則であり、機序予測 (≈ 6 %) がそれを下回るので本 wave の閾値は秒で置く。
5. 実装面 (conftest の切替・allowlist・test・集計器) は Codex author が書く。親は brief・裁定・commit・投入・記録だけ。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) **L 腕の実現 = env opt-out を `pytest_configure` で読み config 属性へ置き、`_early_memo_selected` が属性を見る。** 直接 env を読むと既存 test (synthetic config `_ReceiptHookConfig`、`pytest_configure` を通らない) が L 腕の受入で赤になる。属性経由なら synthetic config には効かず、両腕とも同一 SHA で緑。env は `tools/pegasus/dispatch_compute.py` `TASKS["tests"].env_allowlist` に足す (exact pin test を同 commit で更新、T-2766 と同型)。代案 = worktree 2 本 (base と revert commit) → 同一 SHA を破り pyc warm も 2 本要るので不採用。
- (P2) **指標 = 最遅 shard の JUnit wall W_max (主)、配布開始 D_0 = shard-0 の min(worker first_test_started) − session 開始 (副、機序の直接観測)、witness = stderr の `IZANAGI_MEMO_PREWARM_V1` 行 (E: 3 shard とも `configure_node`、L: shard-0 だけ `xdist_node_collection_finished`、`configure_node` 行なし)。**
- (P3) **対数 = 有効 6 対で固定終了、上限 16 走。** 順序は E,L / L,E / E,L / L,E / E,L / L,E。無効走 (rc≠0・赤・receipt 不発行・witness 不一致・同一 SHA 不成立) を含む対は同順序で取り直す (slot を消費しない、T-2766 と同型)。逐次検定・途中終了はしない。
- (P4) **判定 = Wilcoxon 符号順位 (片側、exact、H1: ΔW = W_max(L) − W_max(E) > 0) の p ≤ 0.05 かつ 対差の中央値 ≥ 15 秒 → 「効果を支持」。** p ≤ 0.05 だが中央値 < 15 秒 → 「方向は支持、大きさは機序予測の半分未満」。p > 0.05 → 「n=6 の範囲で効果未確立」(σ_d の実測から必要対数を再計算して併記)。対応のある t 統計量と MDE は記述的に併記。
- (P5) **段構成 = 軽量版 + 敵対相談 1 本 (2 レンズ: 統計・事前登録 / 実装境界・test の pin・env 伝播) + 段 6 レビュー 1 本 + 変異 matrix (3〜4 件)。** 段 2 は親が起草する。
- (P6) **E 腕の `memo publication timeout` (rc=16) は無効走として取り直すが、件数を副次観測として記録する** (E 固有の失敗型で L には無い)。

## 事前登録 (段 4 で確定)

- 指標: W_s = shard s の JUnit `<testsuite time>`、W_max = max_s W_s、O_s = `worker_occupancy` の最大 duration、F_s = W_s − O_s、H_s = `session_timeline.collection_finished_epoch_s` − junit `timestamp`、D_s = min_w first_test_started − timestamp、tail_s = W_s − max_w last_test_finished。対ごとに ΔW = W_max(L) − W_max(E) (正 = 早期起動が短い)、ΔD_0 = D_0(L) − D_0(E)、ΔO_0、Δtail_0。
- 有効対: 隣接 2 走がともに緑 (failed / error 0、pytest rc 0、3 shard の report.json と junit.xml が揃う)、同一 SHA、witness が腕と一致。
- 判定: (P4)。同時刻の他 wave の受入 (待ち手経由) の shard-0 W を記述的対照として併記 (tip は違う)。

## 成果物

- 実装 (Codex author、impl branch `impl-t2700-early-memo-optout`): `orchestrator/tests/conftest.py` (env 定数・opt-out 判定・`pytest_configure` で属性・`_early_memo_selected` の属性 check)、`tools/pegasus/dispatch_compute.py` allowlist 1 行、test (`test_real_repo_serialization.py` に正例・負例・UsageError・属性経由で synthetic config に効かないこと、`test_pegasus_dispatch_compute.py` の pin 更新)。
- 集計器 (Codex author、job dir、repo に入れない): 走表・対表・witness 検算・Wilcoxon exact・t 統計量・σ_d 実測・必要対数の再計算。
- 記録: `output/insights/2026-09-20/t2700-prewarm-ab/README.md`、spool fragment (worklog / decisions)。landing は docs-only。

## 変更面 (実アンカー)

| 面 | file:line | 変更 |
|---|---|---|
| 発火判定 | `orchestrator/tests/conftest.py:2314-2331` `_early_memo_selected` | 冒頭で opt-out 属性を見て False |
| 属性付与 | `orchestrator/tests/conftest.py:2925-2945` `pytest_configure` (`_growth_holds_opted_in()` の直後) | env exact token → `setattr(config, <attr>, True)`、他の非空値は UsageError |
| opt-in 判定の型 | `orchestrator/tests/conftest.py:1885-1897` `_growth_holds_opted_in` | 同型で新関数 |
| controller hook | `orchestrator/tests/conftest.py:2559-2560` `pytest_configure_node` → `_start_early_memo_job` | 変更なし (判定が False なら呼ばれない) |
| L 経路 | `orchestrator/tests/conftest.py:2585-2630` `pytest_xdist_node_collection_finished` | 変更なし (prerequisites で shard-0 だけ同期 prewarm) |
| env 伝播 | `tools/pegasus/dispatch_compute.py` `TASKS["tests"].env_allowlist` | key 1 つ追加 |
| pin | `orchestrator/tests/test_pegasus_dispatch_compute.py` `test_tests_task_env_allowlist_is_exact` | 集合に 1 key 追加 |
| 既存 pin test | `orchestrator/tests/test_real_repo_serialization.py:6472-6645` | 変更なし (synthetic config は属性を持たない) |
| witness | 各 shard の `dispatch/shard-N/izdw-shard-N.e*` の `IZANAGI_MEMO_PREWARM_V1` 行 (`conftest.py:2475-2484`) | 変更なし (launcher が複製) |
| timeline | `report.json` `session_timeline` (`tools/acceptance_shards.py`) | 変更なし (集計器が読む) |

## 模擬 / 実の差と前提実測

- 上記「前提実測」はすべて実 session の成果物から取った (集計 script は job tmp `prewarm_stats.py` / `head_stats.py` / `dist_start.py` / `power.py`、insight に写す)。
- queue / 他 wave: 07:34 JST 時点の稼働 wave 数と受入 leader 数は launcher の門番が投入直前に記録する。
