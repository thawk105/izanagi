# 段 1 brief — [T-2710][T-2273] 受入 wall の律速 b5 群の本体と固定費を反復・対比較で分解する (実測のみ、実装ゼロ)

作成 2026-09-18 10:48 JST (file mtime)。基準 commit `24ede1d11` (local main、fresh worktree)。原文は書き換えず、訂正は README と `s4-ruling.md` で行う。

## 研究前進 (土台)

受入全走の最遅 shard は 2026-09-17 09:00 以降の 92 session で wall 中央値 369.1 秒 (固定費 = wall − 最大 worker 占有 の中央値 67.2 秒、最長 node の中央値 273.3 秒、91/92 走で `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`)。「テスト全体 5 分」の上限を超え続け、全 dev-wave の land が受入 attempt ごとに 6〜10 分を払う。第 22 回 /rulings 項 3 は「AI が D357 の反復・対比較で b5 群の本体と固定費を分解し、shard 内 pairing (上限 5.8%) と e2e の分割 / parametrize 縮約の効果を実測で持ってから諮り直す」と定めた。本 wave の最小差分 = その実測値・分解表・裁定パッケージ案を insight に置くこと。完了判定 = (i) 同一 tip・同一条件 3 走以上の中央値による分解表、(ii) pairing と最長 node 除外の対比較差 (中央値と全走の値)、(iii) 分割 / 縮約の model 値と、その前提になる実測成分、(iv) 次の諮り直しの裁定パッケージ案 (採る / 採らない案と費用対効果)。

## scope

- 実測と設計案まで。**実装面差分ゼロ** (受入 runner・conftest・test・allocator は 1 byte も変えない)。probe / harness は Codex `role=author` が worktree に書き、親が実行前に job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2710-b5-wall-decomposition/`) へ退避して repo からは消す。
- 受理集合は変えない (D2068 / D2128)、保留検査は復帰させない、成分粒度は変えない (D2121)、8 条件の整備 wave は起こさない。分割 / 縮約は**案**として裁定パッケージに書くだけで実装しない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 確定済みユーザー裁定

- 第 22 回 項 3 (a)〜(d) (fragment: branch `worktree-rulings-all-20260918` の `docs/spool/decisions/2026-09-18-rulings-all-20260918-1.md`、未 fold): t080 e2e 群は毎走を暫定維持、8 条件へ投資しない、(b)(d) は D2121 により不採用案として残す、T-2767 は P3 のまま。
- D357: 同一 tip・同一条件 3 走以上を逐次に取り中央値で述べる。1 走同士の差 10% 未満は「変化なし」。**測定中は自分の他 job を同時に走らせない**。
- D2121: 最遅 shard の wall = 最長 node + 相方 (約 20 秒) + 固定費 (約 66 秒)。次の対象は最長 node の単体所要と相方。
- D2128: 別系列化は 8 条件成立まで採らない。D2068: fixture 側の高速化 3 案は採らない。
- 前 wave (archive 1628、`output/insights/2026-09-17/t2710-t080-series-inquiry/`) と T-2750 (`output/insights/2026-09-17/t2750-component-granularity/`) の実測は再測しない (純増だけ取る)。

## 不変条件

- 規律 2: probe は正しさ gate (verifier / receipt / hold) を触らない。計測は (a) 観測 wrapper (実物へ委譲、DW-O14)、(b) 選択 (deselect)、(c) 並べ替え (collection 順) だけで行い、test 本文・assert・fixture の意味を変えない。
- 計測は計算ノード (Pegasus gen_S、`tools/pegasus/dispatch_compute.py --task generic`)。login は解析と selftest のみ。
- 受入全走は段 9 の land 前に 1 回 (結果は land の受領証)。

## 前提実測 (brief 前、login、inline)

1. 92 session (2026-09-17 09:00〜09-18 10:38 JST、shard-0): wall 中央値 369.1 (310.8〜677.1)、固定費 67.2 (65.0〜103.3)、最長 node 273.3 (200.0〜557.7)。最長 node は 91/92 で `single_defects…_b5[ccbench-current]`、1 走は `…_g7` (525.9 秒)。
2. M 関連 file (`test_s8b_oracle_driver.py`、`conftest.py`、`tools/acceptance_shards.py`、台帳) は 2026-09-17 `df2da88ee` 以降変更なし → 92 session は test 内容が同一 (tip は異なる)。
3. 受入 plugin (`tools/acceptance_shards.py::pytest_collection_modifyitems`, trylast) は allocator で **deselect するだけ**で順序は変えない。cost 順の並べ替えは `orchestrator/tests/conftest.py::_reorder_acceptance_items_by_duration` (loadgroup 時、unit = xdist scope、cost 降順、未知 cost は 96 位の cost) が担う。xdist LoadScopeScheduling は各 worker に workqueue 先頭から 2 unit を配る (#277) ので、worker k は unit k と unit 48+k を持つ (順位説明は G11 により一般化しない)。
4. `[ccbench-current]` は `migration.verify_receipt` を 5 回呼ぶ (positive_held / positive_released / checkout_only / result / released)。他 3 param は 2 回。台帳は 240 / 220〜230 秒で差が小さい → 本体 (verify) より base 取得・copytree の固定部が大きい可能性 (実測で決める)。
5. `_t080_stub_free_e2e_repo` = shared base の取得 (`_T080SharedBases.get`: flock 待ち + 初回だけ `_build_t080_stub_free_e2e_repo`) + `shutil.copytree(base → tmp_path)`。M の 11 node は key (r_trailer / extra_r_path / issue_receipt / distinct_basis_blob) ごとに base を共有する。

## 親の provisional 裁定 (攻撃対象)

- (P1) 受入 shard-0 の代理として **replica** (production allocator `tools.acceptance_shards.allocate` で shard-0 を選択 + conftest の cost 順 + `-n 48 --dist loadgroup`、1 計算ノード) を使う。実受入形 (`run_tests.py --force-dispatch`、3 shard 同時) の 3 走は走らせず、replica A の値が 92 session 分布の内側にあることと段 9 の land 受入 1 走で較正する。
- (P2) 条件は 5 つ: S1 = `[ccbench-current]` 1 node 単独 (`-n 1`)、S = M 11 node だけ (`-n 11`)、A = replica shard-0 そのまま、B = A + pairing (workqueue 49〜96 位を最小 cost の 48 unit に入れ替え、T-2766 の形)、C = A − `[ccbench-current]` (最長 node 除外 = 分割 / 縮約が最長 node に届いたときの wall の上限)。各 3 走。job 1 = S1×3 + S×3、job 2〜4 = A/B/C の Latin square (A,B,C / B,C,A / C,A,B)。**job は逐次** (D357)、1 job 内も逐次。
- (P3) 分割 / parametrize 縮約の効果は、S1・S・A で実測した成分 (base 取得 = lock 待ち + build、copytree、verify_receipt 各 call、その他、teardown) から算術で出す **model 値**とし、直接実測は C の wall を上限として添える。「実装すれば X 秒」とは書かない。
- (P4) 固定費の定義を 2 層に分ける: shard 固定費 = wall − 最大 worker 占有 (T-2750 と同じ)。node 固定費 = base 取得 + copytree + teardown。本体 = test call のうち verify_receipt 等の検査部分。
- (P5) 観測 wrapper は `orchestrator.tests.test_s8b_oracle_driver` の `_build_t080_stub_free_e2e_repo` / `_T080SharedBases.get` / `_t080_stub_free_e2e_repo` と `orchestrator.campaign.t080_freeze_migration.verify_receipt` に掛け、実物へ委譲して所要 (monotonic) と worker id・nodeid を JSONL に書く。DW-O14 の「差し替えでない観測 wrapper」。held module (`enforce_held_functions`) は pytest session 内で import されるので probe は plugin (`-p`) として乗る。
- (P6) B の並べ替えは conftest の並べ替え後 (trylast) に unit 単位で行う。unit の切り方は conftest `_acceptance_loadgroup_scope` と同じ。実 scheduler の配布順は controller 側の `pytest_runtest_logreport` の worker_id と start/stop で観測し、最長 node の worker が 2 個目に何を得たかを記録する (G11 の確認を含む)。

## 模擬 / 実の差

- replica は受入 runner の恒久除外 token・env・task-run 記録・同時 3 shard (他ノードでの lustre 共有) を持たない。A の値と 92 session 分布・land 受入の照合で差を書く。
- S1 / S は M 以外の負荷が無い「競合なし」の regime で、受入の値ではない。競合の膨らみは A − S で出す。

## 成果物の形

- `output/insights/2026-09-18/t2710-b5-wall-decomposition/README.md` (結論・分解表・裁定パッケージ案・限界)、`s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、`s4-ruling.md`、`probe-source.md` (probe の逐語と sha256)、`probe-outputs/` (集計表と生 JSONL の要約)。
- spool fragment: worklog 1、failures は新規事故があれば、decisions は 0 (裁定パッケージは提案であり採用済み判断ではない)。
- 実装面 commit なし → 変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## 並列分割方針

- 段 2: plan 1 本 (codex read-only、`gpt-6-astra`/medium)。段 3: consult 2 本 (レンズ A = 計測設計の妥当性・交絡・D357 適合・replica の忠実度、レンズ B = 分解の解釈と裁定パッケージ案の攻撃・受理集合と規律 2 の射程)。
- 段 5: author 1 本 (probe: plugin + runner + 集計)。段 6: fix は必要な回だけ、review は数値の再計算照合 1 本 (DW-O16)。
- 親: launcher / detach、計算ノード投入、集計の検算、insight、記録。

## 変更面 (実アンカー)

| 面 | path | 種別 |
|---|---|---|
| insight | `output/insights/2026-09-18/t2710-b5-wall-decomposition/**` | 新規 docs |
| spool | `docs/spool/worklog/2026-09-18-t2710-b5-wall-decomposition-1.md` (+ failures があれば) | 新規 docs |
| probe (repo 外) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2710-b5-wall-decomposition/probe/` | 実装面、commit しない |

条件 dispatch: DW-O08 / O09 / O10 不成立 (freeze・oracle gate・凍結 bytes に触れない、docs path の pin も新規 dir のため無し)。DW-O13 不成立 (gate・検証を新設しない)。DW-O14 成立 (観測 wrapper、上の P5)。
