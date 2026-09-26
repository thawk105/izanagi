# silo-function-policy 軸 — 既知最良との小比較 (2026-09-23、[T-2865])

- 位置づけ: D2235 項 7 (択 (b)) の小比較の記録。**報告カテゴリは「偵察 (preliminary)」** で、事前登録のどの構成でもない。段階 D (`output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`、D2234) と同じ固定 16 点・同じ偵察 driver・同じ計測構成に、既知最良の参照 3 本を同じ job に置いた。段階 E へ進むかはユーザー判断 (D2214・D2235 項 7) で、本記録はその材料である。可変状態の正本にはしない。
- wave: branch `worktree-dev-wave-t2865-silo-small-compare`、起点 local main `620a6bb13` (開始 gate rc=0)。計測は commit `9cd4099d7` (fix-1) の driver、CCBench PIN `e9e477ca` (段階 D と同じ)。wave 中に local main の pin は `68106660` へ進んだ ([T-2858]、D2236) が、`cc/silo`・`cmake/Options.cmake`・`include/backoff.hh` は 2 つの pin で差分がない (親が `git diff --stat` で確認)。
- 逐語 (`verbatim/`): 依頼、段 1 brief、段 3 相談 A・B、段 4 裁定、段 5 実装子の報告、段 6 レビュー・裁定・fix 子の報告、変異 matrix。

## 0. 要約

1. **既知最良は全 8 job で静的 10 µs (fixed10) だった。** 同 job の中央値は 3,944〜4,011 千 txn/s で、`B0-L-W0` (2,374〜2,533) と stock (1,343〜1,378) を大きく上回る。旧 pin の記録 (A-2 正式認証で fixed10 が `BACK_OFF=0` 比 +63.5%) と整合する (現 pin で約 +63%)。
2. **IR 16 点の、同 job の最良参照 (= fixed10) に対する比は 0.836〜1.069。** 16 点すべてが比較に適格 (null 0)。3% 線を越えたのは 3 点 (比 1.062〜1.069)。残り 13 点は 1.005 以下で、fixed10 と互角か負け。
3. 越えた 3 点はどれも、5 rep すべてが同 job の fixed10 の 5 rep すべてを上回った (例: 最小 4,188 > fixed10 の最大 4,072 千 txn/s)。同じ 3 点は段階 D (別 job・別ノード、abort0 比) でも上位 3 点で、throughput は 1% 以内で一致した。
4. **限定:** 3% 線は未較正の暫定値、16 点から最大を選ぶ多重選択は補正していない、再測はしていない (D2235「1 回」、ユーザーの計算承認も再測なし)。段階 D との一致は、同じ点を別 job で測った値の一致であって、事前に定めた再現判定ではない。固定テンプレートの部分空間の結果で、全 IR や LLM×C++ の空間については何も言わない。
5. 計算は計測 8 job の Elapse 合計 6,180 秒 (1.72 node 時間) + 検査 (§5)。ユーザー承認の上限 4.6 node 時間の内側。

## 1. 依頼と裁定

- 依頼: ユーザー直接起動の `/dev-wave` (逐語 = `verbatim/request.md`)。D2235 項 7 = 択 (b)。
- 計算の確認: 投入前に「計測 8 job 1.44〜1.84 + 検査で合計 約 2.06〜2.46 node 時間、walltime 上限で 約 4.6」を示し、ユーザーは「上限 4.6 h で承認 (推奨)」(再測なし) を選んだ (2026-09-23 21:5x JST)。
- 段 3 相談 2 本 (どちらも adopt_with_conditions) の must-fix を段 4 で採用した (`verbatim/s4-ruling.md`): fixed10 の実効 define を検査して止める、参照 3 本と abort0 のどれかが不適格なら最良参照比を null、集計で fixed10 の genome・source evidence・実効 define を照合、3% 超を探索的目印として扱う、再測はしない。

## 2. 実装 (単位と commit)

| 単位 | commit | 内容 |
|---|---|---|
| A | `7779e44b9` | `silo_policy_coverage.py`: `_source(backoff_fixed_patch=True)` (stock 木だけに `patches/silo-backoff-fixed.patch`、marker 確認)、`_build_variant(stock_backoff_fixed=N)`。`silo_policy_recon.py`: phase `compare`、role `fixed10`、実効 define 検査、`compare-aggregate` |
| 段 6 fix 1 | `9cd4099d7` | 巡回を job mod 6 に (job 7 が基本列に戻っていた)、BACK_OFF 重複 define を拒否、実 configure argv の test、`case_order` 照合 |
| 段 6 fix 2 | `c80514b74` | define 検査 test を `_one` が読む build dir で行う (焦点走 1 の赤、test の欠陥) |

- 実装面の全ハンクは Codex author (gpt-6-sol、medium) が子 worktree で書き、親は所有 path の差分だけを統合した。段階 D の `initial`/`remeasure`/`aggregate` の挙動は不変。
- **fixed10 = 「元の適用方法」:** CCBench の stock 木に `patches/silo-backoff-fixed.patch` (Options.cmake の `CCBENCH_BACKOFF_FIXED` と `include/backoff.hh` の静的待機の分岐) を当て、`BACK_OFF=1, BACKOFF_FIXED=10` + `locks._BASE` で build する。関数方策の骨格 patch は当てない (D2160 の identity と同じ形)。値 10 µs の出所は `output/s1-freeze/known_axes_freeze.json` の write-heavy `backoff_fixed_best`、A-2 正式認証 `rr5-fixed10`、D2160、`docs/unseen-condition-transfer-preregistration.md` の R2 (いずれも旧 pin `d706650c` / `511c9538`)。本走がその現 pin での再評価になる (設計 insight 2026-09-21 §5)。
- patch 未適用のまま `-DCCBENCH_BACKOFF_FIXED` を渡すと無言で適応 backoff に落ちうるので、trace1・trace0 の両 build で owner TU の compile command に `-DBACKOFF_FIXED=10` と `-DBACK_OFF=1` がちょうど 1 個ずつあることを確かめ、無ければ `backoff-fixed-not-effective` で verify・bench へ進まない。本走では 8 job とも両 build で成立した。

## 3. 実測

### 3.1 構成

- Pegasus gen_S、1 job = 1 ノード、`tools/pegasus/dispatch_compute.py --task generic` (walltime 30 分、待ち上限 3600 秒)、計測用 detached worktree 8 本 (`.claude/worktrees/t2865-recon-{0..7}`)。
- 各 job = IR 2 点 (段階 D と同じ `job_of` の 8 組) + abort0 + stock + `B0-L-W0` + fixed10 の 6 方策。実行順は基本列 [IR, IR(bit 反転), abort0, stock, B0-L-W0, fixed10] を job 番号 mod 6 だけ左へ巡回した (参照の位置を job 間で分散するだけで、候補ごとの位置の交絡は残る)。
- 各方策: 4 段検査 (IR・abort0) → TRACE=1 build → legacy verify と性能構成 verify → 両方 certified のときだけ TRACE=0 build → owner TU の trace0 確認 → bench 5 回 (1M records / 48 threads / skew 0.9 / rratio 5 / rmw false / max_ope 10 / 3 秒、numactl interleave)。段階 D と同じ。
- 結果 = `output/env/pegasus/calibration/silo_function_policy_recon/compare/compare-{0..7}.json`、集計 = 同 dir の `compare-aggregate.json` (login で実行、照合エラー 0)。投影 JSON は作っていない。

### 3.2 参照 (同 job の 5 rep 中央値、千 txn/s と abort 率)

| job | request | node | abort0 | stock | B0-L-W0 | fixed10 |
|---|---|---|---|---|---|---|
| 0 | 21389 | bnode032 | 2,464 (0.785) | 1,378 (0.126) | 2,509 (0.779) | 3,972 (0.383) |
| 1 | 21390 | bnode038 | 2,429 (0.784) | 1,343 (0.117) | 2,394 (0.787) | 3,944 (0.385) |
| 2 | 21391 | bnode021 | 2,495 (0.777) | 1,359 (0.123) | 2,533 (0.782) | 4,011 (0.380) |
| 3 | 21393 | bnode021 | 2,540 (0.777) | 1,356 (0.120) | 2,486 (0.784) | 4,008 (0.381) |
| 4 | 21392 | bnode044 | 2,389 (0.783) | 1,374 (0.125) | 2,374 (0.787) | 3,958 (0.385) |
| 5 | 21394 | bnode004 | 2,522 (0.776) | 1,373 (0.124) | 2,503 (0.777) | 4,009 (0.381) |
| 6 | 21395 | bnode017 | 2,417 (0.783) | 1,373 (0.126) | 2,431 (0.787) | 3,983 (0.382) |
| 7 | 21396 | bnode017 | 2,435 (0.784) | 1,355 (0.119) | 2,401 (0.784) | 3,975 (0.383) |

- 参照 3 本の中で最良は全 job で fixed10。fixed10 の job 間の幅は 1.7% (3,944〜4,011)。abort0 と `B0-L-W0` はほぼ同じ (段階 D と同じ観察)。

### 3.3 IR 16 点 (点 ID は LSRM、段階 D §2.1 の因子定義)

| 点 | job | throughput | abort 率 | ÷ fixed10 | ÷ B0-L-W0 | ÷ stock |
|---|---|---:|---:|---:|---:|---:|
| 0000 | 0 | 3,906 | 0.502 | 0.983 | 1.557 | 2.835 |
| 0001 | 1 | 3,881 | 0.389 | 0.984 | 1.621 | 2.889 |
| 0010 | 2 | 3,817 | 0.554 | 0.952 | 1.507 | 2.809 |
| 0011 | 3 | 4,030 | 0.439 | 1.005 | 1.621 | 2.970 |
| 0100 | 4 | 3,624 | 0.288 | 0.916 | 1.527 | 2.638 |
| 0101 | 5 | 3,353 | 0.237 | 0.836 | 1.339 | 2.441 |
| 0110 | 6 | 3,959 | 0.371 | 0.994 | 1.629 | 2.883 |
| 0111 | 7 | 3,792 | 0.314 | 0.954 | 1.579 | 2.797 |
| 1000 | 7 | 3,967 | 0.463 | 0.998 | 1.652 | 2.927 |
| **1001** | 6 | 4,229 | 0.346 | **1.062** | 1.740 | 3.080 |
| 1010 | 5 | 3,498 | 0.538 | 0.872 | 1.397 | 2.546 |
| 1011 | 4 | 3,972 | 0.430 | 1.004 | 1.673 | 2.891 |
| 1100 | 3 | 3,997 | 0.236 | 0.997 | 1.608 | 2.946 |
| 1101 | 2 | 3,668 | 0.194 | 0.914 | 1.448 | 2.699 |
| **1110** | 1 | 4,215 | 0.342 | **1.069** | 1.761 | 3.138 |
| **1111** | 0 | 4,243 | 0.290 | **1.068** | 1.691 | 3.079 |

- 16 点すべてが legacy・性能構成の両 verify で serializable、trace0 clean、5 rep 有効。high-abort 除外 0。
- 3% 線を越えた 3 点はいずれも L=1 (lock 競合で即 abort せず試行 4 回まで待機 0 で再試行)。L=1 の 8 点は 0.872〜1.069、L=0 の 8 点は 0.836〜1.005。3 点の 5 rep の最小値は同 job の fixed10 の最大値を上回った (1001: 4,217 > 4,020、1110: 4,206 > 4,001、1111: 4,188 > 4,072)。
- 段階 D (初走 8 job、abort0 比) でも上位 3 点は 1001・1110・1111 (1.775・1.768・1.708) で、throughput は 1,001: 4,218 → 4,229、1110: 4,257 → 4,215、1111: 4,238 → 4,243 千 txn/s。

## 4. 段階 E の判断材料と限定

- **言えること:** 固定 16 点のテンプレート部分空間 (未調整、定数は段階 C の手書き方策から結果を見る前に固定) に、同 job の既知最良 (現 pin で再評価した静的 10 µs) を 6〜7% 上回る点が 3 つあった。いずれも L=1 (lock 競合への応答を変える軸で、静的・適応 backoff の値空間には無い次元) を持つ。abort0 比の段階 D の二値より強い問い (既知最良との比較) に対する探索的な肯定である。
- **言えないこと:** 統計的な優位 (再測なし、多重選択の補正なし、3% 線は Pegasus で未較正)、全 IR・LLM×C++ の空間の地形、別 workload (balanced・read-heavy・TPC-C) への転移、fixed10 以外の静的値 (5 µs・20 µs など、現 pin で掃いていない) より良いか。L=1 の効果を backoff 値の軸だけで再現できないかも確かめていない。
- 再測をするなら、越えた 3 点の別 job 再測 (1 点 1 job、約 0.21 node 時間ずつ) が最小の追加。段階 E の判断と併せてユーザーへ返す。
- **firewall (手順書 §3-D):** 本 insight と `compare-aggregate.json` には点 ID・因子・比・順位が載る。段階 E / F の coder・planner の入力 (leakproof_context・planner direction・whiteboard) へ流さない。本 insight を読んだ事実は段階 E / F の campaign provenance に情報源として記録する義務を残す。本 wave は投影 JSON を作らず、後段へ渡すものは段階 D の `projection.json` のまま。
- 診断 build は NON_ADMISSIBLE で、certified 候補とは称さない (D2226 項 5)。verify の certified は各有限履歴についての判定。

## 5. 検査と計算ノードの使用

### 5.1 段 6 の経緯

| 巡 | 入力 | 直したもの | 裁定 |
|---|---|---|---|
| 1 | レビュー A (NO-GO、must-fix 2) | job 7 の巡回漏れ (6 要素へ slice 7 で基本列に戻る)、BACK_OFF 重複 define を有効と判定、実 configure argv の test、`case_order` 照合 | `verbatim/s6-ruling-1.md` |
| 2 | 焦点走 1 回目の赤 (21338.nqsv、1 failed / 804 passed / 5 skipped) | 新 test の stub が `_one` の読む build dir に compile_commands.json を書かず、owner TU を読めない例外経路で status だけが一致していた (test の欠陥)。stub が受け取った build dir に書く形へ | `verbatim/s6-fix-2.md` |

- 焦点走 2 回目 (fix 2 後、変更 test 2 + consumer 3 file): 1 回目の投入は gen_S が自分の計測 8 job で埋まって queue-wait-timeout (子は未起動)、投げ直した 21493.nqsv で 161 passed / 2 skipped。1 回目 (fix 1 前) は inventory 4 群と consumer を含む 11 file で、赤は上の 1 件だけ。

### 5.2 変異 matrix

- 事前登録 13 本 (段 4 で 9 本、段 6 裁定 1 巡目の fix 前に 4 本、`verbatim/s4-ruling.md` §4・`verbatim/s6-ruling-1.md`)。計測を終えた計測木 3 本 (detached `c80514b74`、clean) に `tools/mutation_harness.py --runner-mode dispatch --detached` を直接当てた。runner = `run_tests.py --force-dispatch orchestrator/tests/test_silo_policy_recon.py orchestrator/tests/test_silo_policy_coverage.py -q -rf`。spec 生成の道具は wave の job dir の `make_specs.py` (repo 外、各 anchor が対象 file に 1 回だけ現れることを検査)。
- probe (全件 SURVIVED 期待、2026-09-23 23:12〜09-24 00:15 JST): 基準走は 3 本とも PASSED、13 変異すべてで赤 node を観測し、どの変異も事前登録した kill 点の test **1 件だけ**を落とした。期待 node はこの観測の完全集合 (`verbatim/mutation/observed-nodes.json`)。
- **final (KILLED 期待、2026-09-26 10:11〜10:17 JST): 13 / 13 KILLED、期待 node と完全一致 (MISMATCH 0・SURVIVED 0)、基準走は 3 本とも PASSED。**

| ID | 壊したもの | 落ちた node (final、完全一致) |
|---|---|---|
| m-fx-flag | fixed10 の genome の BACKOFF_FIXED 値 | `test_compare_fixed10_genome_and_build_args` |
| m-fx-patch | stock 木への backoff patch の適用 | `test_source_backoff_fixed_patch_materializes_markers` |
| m-fx-define | trace1 の実効 define 検査 | `test_compare_fixed10_define_check_rejects_missing_define` |
| m-fx-argv | `_build_variant` の genome への BACKOFF_FIXED | `test_build_variant_passes_backoff_fixed_to_configure` |
| m-backoff-dup | BACK_OFF の一意性 | `test_compare_fixed10_define_check_rejects_duplicate_back_off` |
| m-cmp-max | 分母 = 参照 3 本の最大 | `test_compare_aggregate_uses_best_reference` |
| m-cmp-null | 参照不適格時の null | `test_compare_aggregate_null_when_reference_ineligible` |
| m-cmp-order | case 列の照合 | `test_compare_aggregate_rejects_wrong_order` |
| m-case-order | `case_order` の照合 | `test_compare_aggregate_rejects_case_order_mismatch` |
| m-cmp-fxflags | fixed10 の genome flags の照合 | `test_compare_aggregate_rejects_fixed10_flag_mismatch` |
| m-cmp-floor | 比 > 1.03 | `test_compare_aggregate_floor_boundary` |
| m-rotation / m-rotation-mod | 巡回 (0 固定 / mod なし) | `test_compare_cases_rotate_by_job` |

### 5.3 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| 計測 job 0〜7 | 21389〜21396.nqsv | 770・776・771・779・772・768・775・769 秒 (計 6,180) |
| 焦点走 1・2 | 21338・21493.nqsv | 107・92 秒 (queue-wait-timeout の 21397 は子なし) |
| 変異 probe 3 本 | (runner 内の dispatch) | runner 所要の合計 5,343 秒 (計測直後の混雑で待ち行列込み、上限値) |
| 変異 final 3 本 | (同) | runner 所要の合計 461 秒 |

- 計 12,183 秒 ≈ 3.38 node 時間 (変異は待ち行列込みの上限値)。ユーザー承認の上限 4.6 node 時間の内側。受入全走は本記録の commit の後に行い、結果は land の受領証に残る。
- 2026-09-24〜26 は session が中断していた (変異 probe は中断前に完了、final は再開後に投入)。
