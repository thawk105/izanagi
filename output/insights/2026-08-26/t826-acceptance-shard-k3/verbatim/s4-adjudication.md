# 段 4 裁定 — 受入全走の高速化

親が段 2 plan、段 3 の 2 レンズ、および**親自身の実測 2 走**を突き合わせて裁定する。
段 1 brief の前提は実測で覆ったので、`s1-brief-addendum.md` と本書が有効な scope である。

## 1. 親が新たに取った実測 (一次資料)

現 tip = local main `b253e0b7`、実装差分ゼロ。`IZANAGI_ACCEPTANCE_SHARDS` だけを
2 と 3 に切り替えて 2 走した。受入 receipt は作らず計測として投入した。
session root は `/work/1/SFC/tanab/.izanagi-acceptance-shards/b18df44f...` (K=2) と
`.../40fc419d...` (K=3)。

| 層 (D713) | K=2 | K=3 |
|---|---|---|
| pytest wall (最遅 shard) | **285.52 秒** | **160.92 秒** |
| 最遅 worker | 211.99 秒 | 101.70 秒 |
| その shard の `W/48` | 203.9 秒 | 94.7 秒 |
| 残差 (wall − 最遅 worker) | 73.53 秒 | 59.22 秒 |
| 直列総仕事量 (全 shard) | 16609.9 秒 | 10830.1 秒 |
| 結果 | 1 failed (非帰属) / 17390 passed | 17391 passed / 0 failed |

- **K=2 → K=3 で pytest wall が 124.60 秒 (43.6%) 縮む。** D1019 が記録した走間ばらつき
  32.27 秒の 3.9 倍であり、ノイズでは説明できない。
- **総仕事量自体が 1.53 倍縮む** (16609.9 → 10830.1 秒)。1 ノードあたりの同時実行数は
  どちらも 48 worker で同じなので、これは node あたりの総負荷が下がったことによる
  競合の減少である。K は容量を増やすだけでなく仕事量そのものを減らす。
- **`real-repo` の排他鎖は消えている。** K=2 の `group_to_workers` は `real-repo` を
  40 worker に分散しており、`5ac63895` の細分化が効いている。
- **現在の律速は最長単体テストである。** K=2 の最長単体は 165.17 秒
  (`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)、
  K=3 では 100.32 秒
  (`test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`)。
  K=3 の wall 160.92 秒 ≒ 最長単体 100.32 + 残差 59.22 であり、**K=3 で既に単体の床に
  達している**。
- 重い単体は 3 file に集中する。K=2 の file 別上位は
  `test_s8b_floor_campaign.py` 1926.1 秒、`test_s8b_oracle_driver.py` 1738.7 秒、
  `test_t126_pegasus_tools.py` 1107.9 秒。上位 15 node で総和の 12.8%。

## 2. 親 brief の provisional 裁定の処分

段 2 plan と 2 レンズが独立に同じ向きで反証した。親は全件を受け入れる。

| # | 裁定 | 理由 |
|---|---|---|
| (P1) | **refuted** | flock は `pytest_runtest_protocol` しか覆わず、collection / import / 登録外 fixture を覆わない。かつ「これから外す」という把握が誤りで、`5ac63895` で既に外れている。 |
| (P2) | **real (必要条件としてのみ)** | lock は `/tmp` で host local。ただし別 invocation・別 worktree・collection 窓を閉じる十分条件ではない (sol #4)。 |
| (P3) | **refuted** | T-991 の 2 経路修理は real だが、閉包完全性検査は手書き inventory の内部整合しか見ない。登録外の実 repo reader/writer が実在する。 |
| (P4) | **refuted** | 222.68 秒は `5ac63895` 前の tip の値。現 baseline は上表のとおり。 |
| (P5) | **refuted** | 残差を「K で縮まない固定費」と断定する根拠がない。実測でも 73.53 → 59.22 秒と動いた。 |
| (P6) | **refuted** | K>4 は成分を割らずに他成分を分けられる。ただし K の上限は別の理由 (下記 3-C) で 3 に止まる。 |
| (P7) | **保留** | s8c 群への転用可能性。下記 3-B のとおり本 wave では実装しない。 |

## 3. scope の裁定

### 採用 A — 受入経路の shard 数を明示 3 にする (本 wave の実装本体)

**決定:** `tools/dev_wave_wait.py` の acceptance 経路が launcher を起動するとき、
site が Pegasus LOGIN であるときに限り `IZANAGI_ACCEPTANCE_SHARDS=3` を子の環境へ入れる。

**根拠:**
- 上表のとおり pytest wall が 285.52 → 160.92 秒 (43.6% 減) になる。実装量は最小で、
  受理集合を 1 node も変えない (どちらの走も collected 17455、選択合計も一致)。
- D724 が K=3 を却下した理由は「床が動かない」であり、その床は
  `5ac63895` (2026-08-26 13:19) が取り除いた。**却下の前提が実測で覆っている。**
  D724 自身が「明示 `2` / `3` は admission ブロックを迂回する」経路を残しており、
  本決定はその sanctioned な経路を使う。既定値 (run_tests.py) は変えない。
- ユーザー裁定「計算 job の queue 待ちは考慮しなくてよい」に整合する。
  dispatch 本数が 2 → 3 に増えるが、queue 待ちは目標から外れている。

**なぜ既定値 (`run_tests.py`) を変えないか:** D838 (**ユーザー裁定**、2026-08-25) が
「受入の実行器 `tools/run_tests.py` を tested main の blob へ束縛する」と決め、
その代償として「当該 file を直す wave は受入を通せない」を明示的に受容している。
`tools/acceptance_launcher.py:436-439` が実装しており、実際 D838 以降 `run_tests.py` は
1 度も変更されていない。**既定値の変更は本 wave では実装せず、下記 4 の裁定パッケージへ送る。**

**成果物影響 (DW-G05):** 受入全走は certified 選択・材料レポート・試行台帳を守る門である。
本変更は shard 数だけを変え、受理集合・選択集合・恒久除外・保留の適用を変えない。
実装しない場合、受入全走は 285 秒 (4.8 分) のまま 5 分上限に張り付き、wave あたりの
再走コストが残る。

### 採用しない B — s8c 群の細分化

**決定:** 実装しない。次の一手へ送る。

**理由:** K=3 では `s8c-preregistration-candidate` の鎖が 96.64 秒で、makespan を決める
shard-0 の最遅 worker 101.70 秒を下回る。**割っても wall は動かない。** かつ sol の
所見 1〜4 が示すとおり、この群が守っている閉包はそもそも閉じていない (登録外の
実 repo writer が同 file 群に実在する)。閉包が確定していない排他を差し替えてはならない
という D358 の原則は、この点については今も成立する。

### 採用しない C — K を 4 以上へ上げる

**決定:** 実装しない。

**理由:** (i) K の受理値 `{1,2,3}` は `run_tests.py` にあり D838 で凍結されている。
(ii) K=3 で既に最長単体テスト (100.32 秒) + 残差 (59.22 秒) の床に達しており、
K=4 以上の余地は単体を速くしない限り存在しない。物理と制約が一致している。

### 採用しない D — duration 重み割付 (D1019 の再訪)

**決定:** 実装しない。

**理由:** D1020 の引き金 (`最長排他鎖 < 総仕事量/(48K)`) は K=2 の shard-0 では成立するが、
**K=3 では利得が消える**。K=3 の仕事量は 4544.9 / 3441.5 / 2843.2 秒で、完全に均衡させると
容量は 75.2 秒になるが、最長単体 100.32 秒がそれを上回るため makespan は動かない。
採用 A を入れた後の regime では D1019 の結論 (利得 0.0 秒) が再び成立する。

### 採用しない E — 残差 (固定費) の削減

**決定:** 実装しない。次の一手へ送る。K=3 の wall 160.92 秒のうち 59.22 秒 (36.8%) を
占めるので、A 実装後の最大の残件である。

## 4. ユーザーへ返す裁定パッケージ

1. **受入の既定 shard 数を 2 から 3 へ上げるか。** 実測で 43.6% 短縮。実装は
   `run_tests.py:295` の 1 行だが、D838 (ユーザー裁定) により当該 file を直す wave は
   受入を通せない。運用としてどう land させるかはユーザー判断が要る。
   本 wave の採用 A は既定値を変えずに受入経路だけで同じ効果を得る回避策であり、
   焦点走やその他の経路は K=2 のままになる。
2. **登録外の実 repo 接触を閉じるか** (sol 所見 1〜4)。
   `test_t810_coordinator.py` が無 lock で linked-worktree registry を読み、
   前 wave の a4k2 で実際に偽赤 (rc=1) を起こしている。閉包・zero-write・lock identity の
   3 点は独立の wave を要する規模である。
3. **最長単体テスト (100〜165 秒) を速くするか。** A 実装後の床を決める。
   上位は `test_s8b_oracle_driver.py` / `test_s8b_floor_campaign.py` に集中する。

## 5. 変異事前登録 (DW-M01)

実装が `tools/dev_wave_wait.py` の acceptance 経路に限られるため、次を事前登録する。
各変異は「無効化時の赤理由が一つに絞れる」ことを実装子が確認してから登録を確定する。

| # | 位置 | 変異 | 期待 |
|---|---|---|---|
| m01 | 環境注入 | `IZANAGI_ACCEPTANCE_SHARDS` の注入を丸ごと削除 | KILLED (K が既定 2 に戻ることを検査するテストが赤) |
| m02 | 値 | 注入値を `"3"` から `"2"` へ変更 | KILLED |
| m03 | 値 | 注入値を `"4"` へ変更 (受理外の値) | KILLED (run_tests が rc=16 になる経路を検査) |
| m04 | site gate | Pegasus LOGIN の判定を恒真化 (常に注入) | KILLED (非 Pegasus site で注入しない正例が赤) |
| m05 | site gate | Pegasus LOGIN の判定を恒偽化 (常に非注入) | KILLED (m01 と同じ検査で赤) |
| m06 | 環境の合成 | 既存 `os.environ` の継承をやめ注入値だけを渡す | KILLED (他の環境変数が保たれる検査が赤) |
| m07 | 適用範囲 | acceptance 以外の launcher 起動経路にも注入 | KILLED (経路限定を固定する検査が赤) |

正例 (通る形): Pegasus LOGIN で acceptance 経路を起動すると子の環境に
`IZANAGI_ACCEPTANCE_SHARDS=3` が入り、既存の環境変数が全て保たれ、argv は
`["python3","tools/run_tests.py"]` のまま 1 文字も変わらない。

## 6. 段 5 への指示

実装単位は 1 本 (編集面が `tools/dev_wave_wait.py` とその consumer test に閉じる)。
`tools/run_tests.py`、`tools/acceptance_launcher.py`、`orchestrator/tests/conftest.py`、
`tools/acceptance_shards.py` は**編集しない**。
