# [T-2825] 受入所要時間台帳の refresh と、隣接対による実効果の測定

branch `worktree-dev-wave-t2825-ledger-refresh-ab`。台帳 commit `26387b617` (Codex author)、main 取り込み `f4fdb0a9c`。
逐語・裁定・子の出力は `verbatim/`、走ごとの記録は `runs/`、機械集計は `analysis/`、変異は `mutation/`。

## 結論 (最初に読む)

測定 tip: A = `21641fee7` (旧台帳、sha `1edbb792…`)、B = `26387b617` (A + 新台帳 1 file、sha `27fd84c2…`)。計算ノード (Pegasus gen_S、48 worker)、
2026-09-21 10:04〜13:31 JST、投入 7 走 (うち無効 1 = infra)、有効 3 対。数値の出所は `analysis/analysis.md` / `analysis/analysis-compact.json`
(集計器 `t2825_ab_analyze.py` の逐語は `verbatim/probe-source.md`)。

1. **事前登録の判定 (W_0 = shard-0 の JUnit wall): (i) 方向一致・閾値以上。** 対差 ΔW = W_0(A) − W_0(B) は 147.8 秒 (対 1、30.6 %) / 200.7 秒 (対 2、39.2 %) /
   29.6 秒 (対 3、7.9 % = D357 の 1 走比較として「変化なし」)。対差の中央値 147.8 秒、対率の中央値 30.6 %、条件別中央値差 482.2 − 334.4 = 147.8 秒 (3 つは別量、
   今回は一致)。**3/3 一致は有意差判定ではない。** 10 % は保守基準で D357 からの導出ではない。
2. **W_max (補助) も (i)。** 有効 6 走とも最遅 shard は shard-0 (argmax = 0) だったので W_max = W_0。shard-1 は A 251.6〜253.0 → B 216.2〜218.9 秒、
   shard-2 は A 145.4〜146.1 → B 190.1〜195.2 秒 (割付の変化で shard-2 が約 45 秒伸びたが、shard-0 を超えていない)。
3. **shard-0 の構成は A / B で同一** (selected 4,149 件、sha `e34aab9e…` が全走一致)。台帳が変えたのは shard-1 ↔ shard-2 の割付 (1→2 が 4,679 node、
   2→1 が 5,256 node) と、shard 内の順序である。台帳予測負荷 (shard-0) は 7,749.5 → 6,877.9 秒、未登録は 367 → 132 件。
4. **O_max と `O_max − L`:** O_0 は各対で 148.2 / 200.9 / 29.1 秒減 (A 299.6〜437.9 → B 237.0〜270.5)。`O_0 − L_0` は A 73.4〜206.7 → B 14.7〜43.1 秒。
   F_0 (= W_0 − O_0) は A 72.7〜74.9 / B 73.2〜74.5 秒、pre 62.6〜64.4 秒、post 10.03〜10.07 秒で、条件差は見えない (差はほぼ全部 O_0 に入った)。
5. **L (事前登録の判定): 「事前登録した L 伸長の判定条件を満たさない」** (ΔL = L(B) − L(A) は +7.3 / −9.0 / +1.1 秒で、全対 > 0 でない)。
   ただし **L の node は全対で入れ替わった**: A は `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`
   (gw5、226.2〜239.0 秒)、B は `test_t080_failed_launch_preserves_receipt_refusal` (gw40、222.3〜246.3 秒)。固定した旧 L 候補 (上の b5 node) は B で 207.7〜230.6 秒。
   対 1 と対 3 は「L 増大を伴う差の縮小」(ΔL > 0 と `O_0 − L_0` の減少が同じ対)。
6. **最大占有 worker の item 列 (機構の観測、1 走ごと):**
   - A: 190〜208 秒級の active_v2 系 node が rank 455〜463 で t ≈ 55 秒 (推定) から走り、同じ worker に 150 秒級または 40 秒級の node が直列で続く
     (01-A gw37: 42.4 秒 item → `test_t080_unactivated_chain_hit_is_invalid` 203.0 → `…active_v2_preserves_nonlayer2_receipt_refusal` 151.1、他 37 item 13.0 秒;
     05-A gw1: 小 item 21 個 8.0 秒 + 4 item → `unactivated_chain_hit` 191.7 → `active_v2_preserves` 152.4 → `delegated…[changed]` 37.8;
     06-A gw33: 55.0 秒 item → `failed_launch…` 202.1 → `v1_gate…` 40.5)。
   - B: 新台帳で 190 / 190 / 190 / 190 / 48 / 44 / 41 / 39 秒を得た active_v2 系 8 node が rank 14 / 15 / 16 / 17 / 40 / 41 / 44 / 96 (最初の配布窓 96 の内側) に入り、
     **全部が t = 0 (推定) から並んで走り、所要はそれぞれ 209.7〜246.3 秒** (A で先頭に立った node は 189.98〜208.09 秒)。最大占有 worker はその 1 本
     (`delegated_campaign_start_rechecks_receipt[missing]`、rank 96、213.0〜237.0 秒) の後に 20〜31 秒の item が 1〜2 個続く形
     (02-B / 04-B gw2、07-B gw1)。
   - **この観測は「active_v2 系 key の base 構築が t=0 の 5 本と同時に走ると L 自身が伸びる」可能性と整合する** (B で t=0 に並んだ 8 node は 209.7〜246.3 秒、
     A で t ≈ 55 秒から先頭に立った同系 node は 189.98〜208.09 秒。範囲どうしの比較であり、node ごとの対応づけはしていない)。copy 配置の内訳・builder / waiter の役割は実受入に計器が無く測っていない。**原因は断定しない。**
7. **参考値 (別欄、§7):** model 差 19.5 秒と観測 `O_max − L` 中央値 62.7 秒は判定に使っていない。実効果の上下限にも使っていない。
8. **台帳は land 対象。** land 時の再生成と測定 B の bytes 照合は §4b。

## 1. 依頼と不変条件

依頼 (逐語は `verbatim/T-2825-origin.md`): `--refresh` で台帳を最新の緑走 1 走の JUnit から再生成し (T-2724 追加 node を含む未収載 node の再登録、凍結 8 suite は据え置き)、
同一 tip の実受入で隣接対 (A = 旧台帳 / B = 新台帳、3 対以上、D357、T-2766 の事前登録の形) の shard-0 W / O_max / `O_max − L` / 最大占有 worker の item 列を測ってから land する。
参考値 (model 差 19.5 秒、観測 `O_max − L` 中央値 62.7 秒) は効果ではないので別に持ち、実効果に上下限を置かない。active_v2 系 key の base 構築が t=0 の 5 本と
同時に走ると L 自身が伸びる可能性を対の判定に含める。着手直前の local main から fresh worktree。門番 (leaders ≤ 1 ∧ load ≤ 60)。gate・台帳・一般化の追加は scope 外。

不変条件 (守ったこと): 凍結 8 suite の 426 entry は値・行 bytes とも不変。`…explicit_binding@real-repo` 0.19 も保持。全 shard を合わせた受理集合と group / unit 境界は不変
(**shard 別 selected は台帳が割付の重みなので変わりうる**。これは効果の一部として観測する)。値の合成・手編集なし。測定は 2 tree とも clean・HEAD 固定、投入前後に照合。
記録 commit は測定後。参考値は閾値・上下限・期待値に使わない。

## 2. 測定形 (なぜ固定 2 tree か)

台帳 path は conftest (`_ACCEPTANCE_DURATION_LEDGER_PATH`) と `tools/acceptance_shards.py` の双方で固定で、env による切替は無い (追加は scope 外)。
したがって依頼の「同一 tip」は literal には作れず、**D2177 (T-2802 の型) の固定 2 tree**で代替した: A = 着手時 local main `21641fee7` の clean worktree
(`.codex/worktrees/t2825-base-a`)、B = wave 木の `26387b617` (A + 台帳 1 file)。**D2068 の「同一 tree 内で交互」条件は満たさない** (path・pyc・page cache・node の差は残る)。
投入は `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入 (待ち手・lease・merge なし)。

## 3. 入力の確定 (D2107)

- 選定締切 2026-09-21 08:47:26 JST。締切時点で新しい順に `20f4f4af…` (08:44、shard-1 に failures 1 → 緑でない)、`f233cd43…` (08:36、shard-2 の JUnit 無し → 未完走)、
  **`9d955ce2…` (08:20、3 shard 緑、26,808 件、tested_main `5efd69367`) = 最新の適格走**。
- collection 一致: wave 木 (= main `21641fee7`) の `--collect-only -q` (26,808 件) と入力走の `login-collection.log` が nodeid 多重集合で完全一致 (重複 0・差 0)、
  `IZANAGI_` marker 行 53 行も一致。入力 hash は `input/SHA256SUMS`。性能値による選び直しはしていない。
- 1 走入力の限界 (D2107): 入力走では active_v2 系 3 node が 189.2 / 191.5 / 192.0 秒、他 4 node が 38.5〜47.9 秒、shared_base 0.004 秒 (`input/t2724-nodes-input.json`)。
  **この 1 走の 190 秒群と 40 秒群が B の順位を決める。builder / waiter の役割を所要だけで断定しない。**

## 4. 再生成の結果 (B commit)

`preserved_frozen=426 / replaced=23813 / added=2366 / removed=140 / excluded_frozen_suite=629`、entry 24,379 → 26,605、被覆 26,587 / 26,808 = 99.1756%。
sha256 `1edbb792…` → `27fd84c2…`。検算 (a)〜(j) は `ledger-evidence/verify.md` / `verify.json` (検算 script は `verbatim/probe-source.md` の `verify.py`)、removed 140 件は `ledger-evidence/removed.txt` (main collection に 0 件、凍結 0 件)。
同じ入力の `--refresh --check` は一致 (決定的)。

**「未収載 334 unit の再登録」の実態:** T-2817 `ledger-model.json` の `missing_ledger_nodes` 334 件のうち **202 件が登録され、132 件は据え置き**になった。
132 件はすべて凍結 8 suite 内 (`test_real_repo_serialization.py` 66、`test_sort_swo_oracle.py` 37、`test_p3_s4_loop_sort.py` 29) で、D2107 の「凍結 8 suite 据え置き」の帰結である
(334 件は旧台帳に 0 件登録)。内訳は `t2817-334-split.json`。**「334 件を再登録した」とは書かない。** T-2724 の 8 node は 8/8 登録。

## 4b. land 時の再生成と測定 B の照合 (事前登録 §9、D2107)

記録の前に local main `d99c556df` を取り込んだ (merge `f4fdb0a9c`)。main 側では T-2344 (`b820bbaa7`) が `--add-only` で 433 件を足しており
(nodeid_count 24,379 → 24,812)、台帳だけが競合した。Codex fix 子が **main の台帳の現物を base に、測定 B と同じ入力で `--refresh` を再走**した結果:

- **生成 bytes は測定 B と完全に一致** (sha256 `27fd84c2…`)。したがって land される台帳は測定した B そのもので、本 insight の測定結果は land される台帳についての観測である。
- 落ちた node は 312 件 = T-2344 が足し入力 JUnit に無い 172 件 (入力走の collection に 0 件、取り込み後の collection に 172 件 = 現 main で台帳未登録に戻る node)
  + main 側に残っていた旧名 140 件 (§4 の removed と同じ、取り込み後の collection にも無い)。取り込み後の collection は入力走に対し +252 / −27 node。凍結 prefix は 0 件。名前は `ledger-evidence-land/dropped.txt` / `dropped-t2344.txt`。**次の add-only wave が再登録する型** (D2107)。
- 取り込み後の collection (27,033 件、login の `--collect-only -q`) に対する被覆は 26,560 件 = 98.25 % (g5 の閾値 90 % を上回る)。
- 凍結 426 entry は main の台帳と生成後で値・行 bytes とも一致、同じ入力の `--refresh --check` は一致 (`ledger-evidence-land/verify.md`)。

## 5. 測定手順 (実際に実行した手順)

- 温め: 両 tree で計算ノード collect-only 1 走 (`PYTHONDONTWRITEBYTECODE=` 空)。A = request 14737.nqsv (09:48〜09:51 JST、pyc 0 → 398)、B = request 14739.nqsv (09:52 JST、pyc 398 → 398、B は wave 木で段 4 前に login collect を
  走らせていたため before が 398)。記録は `warm-A.json` / `warm-B.json`。HEAD / clean は前後一致。page cache・fixture の warm は主張しない。
- 系列: 既定列 `01 A 1` / `02 B 1` / `03 B 2` / … で開始 (09:53 JST)、03-B の infra 赤で停止 (11:25) → 分類 → `04 B 2` / `05 A 2` / `06 A 3` / `07 B 3` で再開 (11:34〜13:31)。job dir の flock で直列、門番 = 他 session の受入 leader ≤ 1 (argv 先頭一致で計数) ∧ load1 ≤ 60、
  周期 100〜140 秒乱数・2 回連続 + 0〜45 秒 jitter・RUN 作成直前に再判定。投入台帳 `submissions.log` と `runs/` の突合が合わないと未投入で止まる (rc=98 / rc=99)。
- 受入 session: 01-A `684b2cb9…`、02-B `41fd024b…`、03-B `cef90d58…`、04-B `ba97dc42…`、05-A `b25973f0…`、06-A `b299f808…`、07-B `f8ce28ee…` (`/work/1/SFC/tanab/.izanagi-acceptance-shards/` 配下)。
  3 shard の junit / report / login-collection の sha256 は `runs/<走>/session-SHA256SUMS`、投入台帳は `submissions.log`。
- 測定中に自分の他 job は走らせていない (D357)。変異・温めは系列開始前に終えた。
- 集計: `t2825_ab_analyze.py` (Codex author + fix 2 巡、job dir で実行、repo へは `verbatim/probe-source.md` の逐語だけ)。

## 6. 走表・対表・判定

事前登録は `verbatim/s4-ruling.md` §事前登録 1〜9 (mtime 08:53:39 JST、系列開始 09:53 JST より前)。走表は `analysis/analysis.md` の機械集計から作った。
W は JUnit testsuite time (秒)、O は report の `worker_occupancy` 最大 (所要の和であって実時間ではない)、L は最長 testcase の time、F = W − O。
投入 → 完了は login 側の外側 wall (queue 待ちを含む。所要の正は JUnit time)。

| 走 | 条件 | slot | 投入 → 完了 (JST) | shard-0 node | W_0 | O_0 (worker、item 数) | L_0 (worker) | O_0 − L_0 | F_0 | pre | post | W_1 | W_2 | W_max (argmax) | 他 leader / load1 | 有効 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01-A | A | 1 | 10:04:04 → 10:13:42 | bnode023 | 482.215 | 409.5 (gw37、40) | 238.951 (gw5) | 170.6 | 72.7 | 62.6 | 10.04 | 253.009 | 146.084 | 482.215 (0) | 1 / 27.21 | 有効 |
| 02-B | B | 1 | 10:22:18 → 10:43:42 | bnode021 | 334.439 | 261.3 (gw2、10) | 246.282 (gw40) | 15.0 | 73.2 | 63.0 | 10.07 | 216.164 | 191.105 | 334.439 (0) | 1 / 9.14 | 有効 |
| 03-B | B | 2 | 10:59:26 → 11:25:05 | — | — | — | — | — | — | — | — | — | — | — | 1 / 16.85 | **無効** (infra、§6) |
| 04-B | B | 2 | 11:52:51 → 12:16:20 | bnode015 | 310.663 | 237.0 (gw2、10) | 222.300 (gw40) | 14.7 | 73.6 | 63.5 | 10.06 | 218.557 | 195.168 | 310.663 (0) | 1 / 13.65 | 有効 |
| 05-A | A | 2 | 12:19:14 → 12:39:51 | bnode026 | 511.326 | 437.9 (gw1、28) | 231.272 (gw5) | 206.7 | 73.4 | 62.8 | 10.03 | 251.621 | 145.398 | 511.326 (0) | 1 / 11.94 | 有効 |
| 06-A | A | 3 | 12:42:13 → 13:04:28 | bnode015 | 374.494 | 299.6 (gw33、12) | 226.247 (gw5) | 73.4 | 74.9 | 64.4 | 10.03 | 251.765 | 146.057 | 374.494 (0) | 1 / 9.75 | 有効 |
| 07-B | B | 3 | 13:07:13 → 13:31:17 | bnode015 | 344.931 | 270.5 (gw1、11) | 227.380 (gw40) | 43.1 | 74.5 | 64.4 | 10.03 | 218.885 | 190.109 | 344.931 (0) | 0 / 12.68 | 有効 |

- 03-B の赤 3 件 (`test_t810_coordinator.py` の prepare_group 系) は本文が `cannot read worktree registration: file is absent`
  (`/work/1/SFC/tanab/izanagi/.git/worktrees/diag-login-check-wall/gitdir`) で、別 session が走行中に撤去した worktree 登録を読んだ結果 (F633 の再発)。
  本 wave の差分 (台帳 1 file) から到達しない (同 test file は台帳を参照しない)。単独再走 (request 14912.nqsv、同一 tip) は 3 passed in 4.38 s。
  事前登録 §3 どおり infra に分類して走だけを無効化し (`runs/03-B/classification.json`)、対 2 を同順序 (B,A) で取り直した (04-B / 05-A)。

| 対 (slot / 試行) | 走 | W_0(A) | W_0(B) | ΔW | r | D357 (1 走比較) | ΔO_0 (B−A) | ΔL_0 (B−A) | Δ(O_0 − L_0) (B−A) |
|---|---|---|---|---|---|---|---|---|---|
| 1 / 1 | 01-A, 02-B | 482.215 | 334.439 | **147.776** | **30.6 %** | ≥ 10 % | −148.2 | +7.3 | −155.6 |
| 2 / 1 | 03-B | — | — | — | — | 無効 (infra) | — | — | — |
| 2 / 2 | 04-B, 05-A | 511.326 | 310.663 | **200.663** | **39.2 %** | ≥ 10 % | −200.9 | −9.0 | −191.9 |
| 3 / 1 | 06-A, 07-B | 374.494 | 344.931 | **29.563** | **7.9 %** | 変化なし | −29.1 | +1.1 | −30.3 |

- 集計 (別量): 対差の中央値 147.776 秒、対率の中央値 30.6 %、条件別中央値差 med W_0(A) 482.215 − med W_0(B) 334.439 = 147.776 秒。
- 判定: 有効 3 対、全対 ΔW > 0、med r = 30.6 % ≥ 10 % → **(i) 方向一致・閾値以上**。W_max (補助) も同値で (i)。
- L: 全対 ΔL > 0 でない → 「事前登録した L 伸長の判定条件を満たさない」。対 1 / 対 3 = 「L 増大を伴う差の縮小」。
- 隣接対は同 job・同 allocation ではない (逐次に別々の 3 shard を投入)。shard-0 の node は対内で異なる (対 3 だけ両走 bnode015)。
- 同時刻の条件: 投入時の他 session の受入 leader は 0〜1、load1 は 9.1〜27.2。A の W_0 (374.5〜511.3) は T-2817 の参照受入 (351.4、別 tip・別時刻) より長いが、
  tip・node・時間帯が違うので比較しない。
- 条件別・shard 別の中央値 (有効対の採用走が母集団、偶数個は中央 2 値の算術平均): A (01 / 05 / 06) shard-0 W 482.215 / O 409.508 / L 231.272 / F 73.398 /
  pre 62.758 / post 10.032、B (02 / 04 / 07) shard-0 W 334.439 / O 261.287 / L 227.380 / F 73.618 / pre 63.496 / post 10.063。

## 7. 参考値 (効果ではない、別欄)

- model 差 19.5 秒: T-2817 §5 (a) の固定所要 list-scheduling model で、中央値のある未収載 333 node 全部に中央値を与えた場合の `O_max_model` の差。**実 wall の予測ではない。**
- 観測 `O_max − L`: 保存済み 21 session の中央値 62.7 秒、Job B 65.0 秒。**最大占有 worker と L の差であって再登録の効果ではない。**
- これらは判定の閾値・上下限・期待値に使っていない。

## 8. 変異 matrix (DW-M01、独立 clone D1009 `mutation-source` main = `26387b617`、`tools/mutation_worktree.py --runner-mode dispatch`)

runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_update_acceptance_duration_ledger.py orchestrator/tests/test_acceptance_schedule_order.py -q -rf`。
spec は probe (sha `1015f7cf…`、本 dir に置かない。生成器で決定的に再生成できる) / final (`mutation/mutation-spec-final.json`、sha `6429930d…`)、
生成器は `make_mutation_spec.py` (Codex author、逐語は `verbatim/probe-source.md`)。結果は `mutation/mutation-{probe,final}-results-compact.json` (原本 sha を記録した射影) と wrapper receipt。

- probe 走 (全件 SURVIVED 登録): baseline PASSED (145 件 63.4 秒)、P0 SURVIVED、M1 / M2 / M3 は MISMATCH = 赤 node を観測。観測 node を final の期待へ写した。
- final 走: **baseline PASSED、KILLED 3 / SURVIVED 1 (等価 P0)、MISMATCH 0、matching 4/4**、wrapper receipt は `shared_snapshot_matches` / `terminal_ledger` /
  `teardown_completed` = true、`resolved_commit` = `26387b617`。

| ID | 変異 (台帳 1 file) | 期待 = 観測 node | 単一理由 |
|---|---|---|---|
| P0 | 非凍結 entry 1 件の値を変える (等価) | — (SURVIVED) | 非凍結値を exact に読む test は無い (D1152 の性質述語) |
| M1 | 凍結 entry `test_masstree_manifest_rejects_one_byte_change` の値 0.12 → 0.13 | `test_t1574_changed_suite_ledger_node_delta_is_exact` | 値を exact に読む実台帳 test はこれだけ |
| M2 | 凍結 suite に偽 key `test_critic.py::test_t2825_mutation_stale` を追加 (count +1) | 同上 | count 整合で g7e / conftest の検証は通る |
| M3 | 非凍結 3,265 件の連続削除 (被覆 86.996%) | `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` | 凍結・`@real-repo`・g6 の比較 key を保護 |

**erratum (DW-M02):** M3 は段 4 で「sorted 順の先頭から削除」と登録したが、実装は「g6 が順序比較に使う key を保護した、被覆 ≤ 0.87 を満たす最短の連続区間」になった
(先頭 `test_g7_controller_reads_ledger_only_for_enabled_loadgroup`、末尾 `test_recovery_waits_for_external_exclusive_wal_lock`)。登録との差を残し、変更後の spec に対して
単一理由を確かめた (`s4-ruling.md` 追補 3)。

## 9. 段 3・段 6 の所見と裁定 (逐語は `verbatim/`)

- 段 3 相談 (1 本、高 3 / 中 3、修正後 GO): 開始 t の観測可能性、入力の collection 一致と最新性、有効走・無効対の規則、shard 構成の変化、warm の対称化、land の bytes 照合。
  全件採用し、段 4 の事前登録に反映した (相談の「変異 matrix 適用外は妥当」だけ refuted = D95 決定 2 により台帳は実装面)。
- 段 6 レビュー A (実効性、must-fix 2 / should 2) と B (過剰・削除、must-fix 3)。fix 1 巡目で 5 件、焦点再レビュー 1 巡目の残件 (履歴削除による迂回、走番号の単調性、中央値の定義) を
  fix 2 巡目で閉じ、焦点再レビュー 2 巡目が **GO・残 must-fix 0**。
- レビュー B が見つけた「334 → 202 / 132」は §4 に反映した。

## 10. 限界・言わないこと

- 固定 2 tree なので path・pyc・page cache・node の差は残る。D2068 の同一 tree 条件は満たさない。
- 各 test の開始時刻は観測していない。item 列の「推定開始」は同 worker の junit 並び順で先行 time を累積した値で、item 間の空白は未観測。
- copy 配置・builder / waiter の因果、L が伸びた原因は計器が無いので主張しない。
- 1 走入力なので、台帳値は入力走の 1 標本。走ごとに 2 倍動く node がある (D2107)。
- 3/3 の方向一致は有意差判定ではない。対 3 は対率 7.9 % で、1 走比較としては「変化なし」だった。A の W_0 は 374.5〜511.3 秒と幅が広い。
- 隣接対は同 job・同 allocation ではない (逐次に 3 shard を別々に投入)。D104 決定 4 の同一 allocation の paired 比較は満たさない。
- land 後の main は測定した A / B と別の tree (T-2344 ほかの 97 commit を含む)。台帳の bytes は測定 B と同一だが、land 後の受入 wall を本 insight は測っていない。
- shard 別 selected は変わりうる。W_0 の短縮を受入全体の短縮と読み替えない (W_max を併記)。

## 11. この dir の中身

- `README.md` — 本書。
- `verbatim/` — 依頼の逐語 (`T-2825-origin.md`)、段 1 brief (`s1-brief.md`)、段 4 裁定・事前登録・追補 (`s4-ruling.md`)、codex 子の prompt と出力
  (段 3 相談、段 5 author L / P / M、段 6 review A / B、fix1 / fix2 / 台帳 fix、焦点再レビュー 1 / 2)、probe・生成器・検算 script の逐語 (`probe-source.md`)。
- `analysis/` — 集計器の Markdown 出力 (`analysis.md`) と JSON の射影 (`analysis-compact.json`、原本 sha と落とした field は `_projection`)。
- `runs/<走>/` — `run.json` (条件・tip・門番値・時刻)、`chain.log`、`gate.log`、`env.txt`、`child.log`、`tracked-diff.stat`、
  `session-SHA256SUMS`。03-B は `classification.json` と単独再走 `rerun-t810.log`。
- `input/` — 入力 JUnit の sha256 (`SHA256SUMS`) と T-2724 8 node の入力値。
- `ledger-evidence/` — 段 5 の再生成の検算 (verify.md / json、refresh.log、coverage.log、determinism.log、removed.txt、status.txt)。
- `ledger-evidence-land/` — land 前の main 現物からの再走と B 照合 (verify.md / json、refresh.log、dropped.txt、dropped-t2344.txt、check.log、main-sha256.txt)。
- `mutation/` — final spec、期待 node、結果の射影、wrapper receipt。
- `acceptance/` — 最終受入の赤の単独再走 log (§13)。
- `measurement-tips.json` (A / B の tree と SHA)、`warm-A.json` / `warm-B.json`、`submissions.log` (投入台帳)、`t2817-334-split.json`。

## 12. 再現手順

1. A = `21641fee7`、B = `26387b617` の clean な木を用意し、`measurement-tips.json` の形で固定する。
2. `verbatim/probe-source.md` の 5 file を job dir の `probe/` に置き、`bash probe/run-warm.sh A` → `B` → `bash probe/run-series.sh` (赤は親が分類)。
3. `python3 probe/t2825_ab_analyze.py --job <job dir> --collection <入力走の login-collection.log> --out <out>`。
4. 台帳の再生成は `python3 tools/update_acceptance_duration_ledger.py --refresh <入力 3 JUnit>` (入力 hash は `input/SHA256SUMS`)。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の codex 子の出力 11 file、`analysis/analysis.md`、`runs/03-B/rerun-t810.log` の行末空白 (U+0020) だけを除いた (可視文字は不変)。
原文の sha256・byte 数・除いた位置と文字列は `verbatim-normalization.json` にあり、そこから原文へ戻せる。三軸語の機械走査
(`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は repo 全体の既存 file の hit で rc=1 だったが、本 dir の file は 0 件、placeholder (`{{`) も 0 件。

## 13. 最終受入の記録

- attempt 1 (tip `a30e92141`、2026-09-21 13:58〜14:11 JST、session `519cfb05…`): 赤 1 件 `test_dev_wave_cleanup.py::test_remove_child_rejects_clean_filter[named-x]`。
  本文は `occupancy result is indeterminate or inconsistent; attempts=3 retry_count=2 ... {"error":"missing","source":"cwd","pid":"2521396"}` (rc=22、期待 20) で、
  占有検査が `/proc/<pid>/cwd` を読む間に別 process が消えた一過性の競合。同 test は台帳を参照せず本 wave の差分から到達しない。単独再走 (request 15060.nqsv) は
  1 passed in 4.41 s。DW-O18 に従い非帰属として受入を 1 回だけ再投入した。
- attempt 2 (tip `4c1228926`、待ち手の post-claim merge で local main `f646e7e85` を取り込み `639a1d956`、2026-09-21 14:44〜14:53 JST、session `c8899d10…`):
  **child-green** (26,964 passed / 69 skipped、赤 0・flake 0)。取り込み後も台帳は測定 B と同じ bytes (`27fd84c2…`)。
- 本節を足した commit 以後の受入は本 dir を含む tip に対して走るので、その結果は本 dir に書かない (受領証は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/acceptance-receipt-*-green.json`、land の結果は fold 後の worklog)。
