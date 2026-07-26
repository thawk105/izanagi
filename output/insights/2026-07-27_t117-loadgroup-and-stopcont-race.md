# [T-117] 全走の床の内訳を実測し、flake の単一の根を特定した (2026-07-27)

[T-057] (2026-07-26) の続き。全走 75 秒の床として記録していた「real-repo loadgroup の直列
69 秒」の**内訳を計算ノードで実測**し、原因が writer 排他ではなく oracle gate の重複解決だった
ことを確定した。あわせて、全走ごとに 1 件出ていた「3 種の別々の flake」が**単一の本番競合**
であることを実測で特定した。本 wave の修正はテストのみ (本番 0 byte)。

一次資料: probe = job 871615 (bnode005)、全走 = job 871616 (L1) / 871619 (L2)。
先行記録 = `output/insights/2026-07-26_t057-test-suite-speed.md`。

## 1. 計測環境

- gen_S 経由の計算ノード (48 core)。単独性はノード上で確認 (loadavg 0.07、非 root は常駐 daemon のみ)。
- 対象 = `orchestrator/tests` 全走 (`-q -n <N> --dist loadgroup --durations=0`)。
- probe は **repo 非改変**: plugin を repo 外 (job tmp) に置き `PYTHONPATH` + `-p` で読み込み、
  `subprocess.Popen` を包んで node ごとの本数・時間・argv を記録、`call` 相だけ cProfile。

## 2. 律速の内訳 — writer 排他ではなかった

group instance の合計は並列度に依らず 68.9 / 69.1 / 69.5 秒 (`-n 16 / 32 / 48`) で、直列鎖である
ことが確認できる。直列実行での内訳 (profile 上乗せなし):

| node | wall | subprocess | 内容 |
|---|---|---|---|
| `test_cli_subprocess_returns_rc_2_on_gate_refused` | 10.88s | 1 | 本番 CLI を子 process で起動 (子が receipt 解決を自前で払う) |
| `test_run_block_broken_binding_manifest_...` | 10.84s | 289 | receipt 解決の初回 miss + active 世代解決 |
| `test_real_freeze_gate_lists_floor_and_budget_null` | 8.81s | 247 | receipt 解決 (`search_repository` 2 × 2.25s + `inspect_receipt_history` 2.87s) |
| `test_run_block_refusal_writes_no_campaign_...` | 4.35s | 39 | **active 世代解決だけ** |
| `test_gate_check_broken_binding_manifest_...` | 4.32s | 39 | 同上 |
| `test_nonnull_floor_without_active_generation_is_refused` | 4.32s | 39 | 同上 |
| `test_active_resolution_and_manifest_structure_...` | 4.31s | 39 | 同上 |
| 残り 26 instance | 計 5.4s | — | s1 freeze / protocol builder / repo scan 等 |

writer として列挙されている `test_p3_s4_loop*` の 4 node は durations に出ない (< 0.005 秒)。
**D63 が直列化の理由とした writer 排他は、現在の律速ではない。**

### 4.4 秒の正体 (cProfile)

```
gate_check → s8b_ratified_freeze.load_ratified_freeze → resolve_active_generation
  → _collect_records → _immutable_introductions (16 回) → _blob_oid_by_commit (16 回)
  → _git ["cat-file","--batch-check"] × 39 本 = 4.39s
```

record path 16 本それぞれについて全 commit (712) 分の `<commit>:<path>` を batch-check へ流す。
**コストは (path 数 × commit 数) に比例する** = T-116 の receipt 解決と同型で、commit を積むほど
悪化する。実 repo の現在の結果は `RatifiedFreezeError(reason="no-active")` (v2 未発効) で、
4 node が同じ 4.4 秒を独立に払っていた。

## 3. L1 = active 世代解決の memo (テストのみ、commit 1211b0a)

`orchestrator/tests/real_repo_ratified_memo.py` を追加 (receipt memo と同型)。

- 初回 miss は本番 loader へ委譲し、**戻り object も送出された例外 object も再構築せず**
  そのまま返す/再送出する。例外は型を問わず同一 object で再送出する — 本番 gate は
  `RatifiedFreezeError` と他 `Exception` で refusal 文字列を書き分けるため、型を潰すと受理集合が動く。
- 実 repo 以外の root は `AssertionError` で fail-closed。patch 先は本番 driver が保持する
  module object。session cache は持たない (opt-in node は全て単一 loadgroup = 単一 process)。
- **正規注入 seam が使えないことを確認した (D78 / DW-O14)**: `gate_check(ratified_error=)` は
  `_gate_check_core` を通らない早期 return の別枝で floor/budget/manifest refusal を積まない。
  `run_block` に注入引数は無い (自身で解決する)。どちらも観測 refusal 集合が変わる。
- **正本 payer を残した**: `test_nonnull_floor_without_active_generation_is_refused` は memo を
  使わず、実走査を毎 session 1 回必ず行う (node 順序に依らず検出力を保つ)。
  `test_ratified_memo_has_a_real_resolution_payer` が機械固定する。
- positive control 5 本 (委譲 1 回 / 戻り値同一 / 例外 object と型の保存 / patch 先 module /
  実 repo 以外の拒否)。control は共有 memo を `cache_clear()` せず stub 由来の別 cache を注入する
  — clear すると同一 worker の opt-in node が 4.4 秒を再び払う (receipt memo の control では実際に
  これが起きており、直列 probe で 2 回目の実解決を観測した)。

**実測 (job 871616)**: group chain **69 → 43.8 秒**、work 605 → 500 秒 (−105 秒)。
単一 process で 3 node が 4.3 秒 → 0.01〜0.02 秒、payer は 4.30 秒を維持。

| 状態 | n16 | n32 | n48 | n32 warm |
|---|---|---|---|---|
| [T-057] 最終形 (4e0169e) | 74s | 75s | 77s | 75s |
| **+ L1 (1211b0a)** | **69s** | **71s** | **72s** | **71s** |

## 4. wall が 5 秒しか動かなかった理由 = 二本目の直列鎖

L1 後に律速を再測すると `test_dev_waves_integration.py` が**ファイル丸ごと 1 group**
(`pytestmark = xdist_group("dev-waves-integration")`) で **直列 67.2 秒**あり、これが新しい
wall の正体だった。74 node / 最重 3.4 秒の平坦分布なので、割れれば ~5 秒相当になる。

**教訓**: 「床」を 1 本の鎖で説明してはいけない。group を縮めても次の group が出てくるので、
律速は毎回 group 単位の直列和を全部並べて確認する (`--durations=0` の nodeid 末尾 `@<group>` で集計できる)。

## 5. L2 = 締切引き上げは仮説ごと棄却された (commit 1bdd8a3 → revert 476eb27)

全走 4 回で毎回 1 件落ちていた dev_waves 系 flake を「テスト側の締切が高並列下の実時間より
短い」と考え、worker 既定 3 → 60 秒、integration の per-wave 5 → 30 秒 / check 15 → 60 秒 /
待ち 20 → 180 秒へ上げた。結果 (job 871619):

| 状態 | n16 | n32 | n48 | n32 warm | 失敗数 |
|---|---|---|---|---|---|
| L1 (1211b0a) | 69s | 71s | 72s | 71s | 1 / 1 / 0 / 2 |
| L2 (1bdd8a3) | **96s** | 71s | 72s | 71s | 2 / 2 / 1 / 0 |

**flake は減らず (4 → 5 件)、n16 の wall は 69 → 96 秒へ悪化した**ので revert した。
締切を伸ばすと後述の競合の失敗が遅くなるだけである (60.09 秒待って赤)。

副産物として踏んだ罠 2 件を記録する。(a) schema に `per_wave <= total <= waves * per_wave` の
制約があり、既定を上げると旧既定を直書きした `total_timeout=waves * 5` が budget-invalid で
落ちる (22 件で発現)。(b) テスト内で独自 `SupervisorProfile` を組む node は ceiling も直書きしている。

## 6. flake の単一の根 = SIGSTOP/SIGCONT ハンドシェイクの競合 (本番、未修正)

L2 で落ちた node は形が揃っていた。

- `test_stdout_stderr_combined_cap_...`: 子が **`stdout_bytes=0`** のまま 60.09 秒 (= 締切) 生存。
  最初の反復 (`total = cap-1`、上限超過なし) で落ちており、上限判定そのものは無関係。
- `test_fake_manifest_wave_index_is_bound_to_wNNN_namespace`: tamper した子が非 0 終了する前に
  29.5 秒 (= 締切) 経過し、reason が `NONZERO_EXIT` ではなく **`TIMEOUT`**。
- `test_export_is_create_only_...`: run が `completed` ではなく `failed`。
- [T-057] が「3 種の別々の flake」として記録した 3 件も同じ形である。

機序 (`tools/dev_waves/worker.py`):

1. `_spawn_stopped` の `preexec_fn` は、exec 前に `os.closerange(...)` で exec-error pipe を閉じ、
   最後に `os.kill(os.getpid(), signal.SIGSTOP)` で自分を停止する。
2. 親の `subprocess.Popen(...)` は exec-error pipe が閉じた時点で返るので、**子が SIGSTOP を
   実行する前に返り得る**。
3. 親は identity を耐久化して `_signal_cont_verified` → `os.kill(pid, SIGCONT)` を送る。
   `_identity_matches` は identity (pid + start_ticks) と pgid だけを検査し、
   **`/proc/<pid>/stat` の状態が `T` (停止) になるのを待っていない**。
4. 2 の窓で SIGCONT を送ると **SIGCONT は空振りする** (SIGCONT は未来の停止には効かない)。
   子はその後 SIGSTOP で止まり、誰も起こさないので per-wave 締切まで停止し続け、
   1 byte も出さずに kill される。

高並列では親が先に走る確率が上がるため、xdist の全走で 1 走 1〜2 件という頻度になる。
**本番でも同じ窓があり**、発火すると wave が理由不明の TIMEOUT で失敗する (fail-closed なので
正しさは壊れないが、無人継続の信頼性を損なう)。

**本 wave では本番を触っていない**: ユーザーが「測定前に本番へ触る回数は [T-096] + [T-102] の
1 回に留める」と明示しているため。テスト側で締切を伸ばして隠すことも行わない (本番の競合が
見えなくなる)。修正案 = CONT 前に子が `T` になるのを有界に待つ (または `T` を観測するまで
CONT を再送する) + 停止観測の positive control。→ 裁定へ。

## 7. 次の lever (順序が重要)

1. **[T-105] `_run_artifact_bytes` の `FileNotFoundError` 素通し**: 本 wave の全走 (n16) で実発火。
   裁定済みだが順序が「[T-011] の後」。§6 と同じ理由で本番は触っていない。
2. **§6 の競合修正** → これが先。次の 3 の前に必要。
3. **`dev-waves-integration` group の分割**: 直列 67.2 秒 = 現在の wall の正体。temp repo ごとに
   隔離されている (runtime dir・socket・pid はすべて temp 由来、pgrep 系の広域 kill は無い) ので
   分割自体の障壁は低い。ただし分割は子 spawn の同時数を増やし **§6 の競合の発火確率を上げる**
   ため、2 の後に行う。
4. **real-repo group の reader/writer 分離**: 残 chain 43.8 秒 → 最重 node ~13 秒が見込める。
   ただし D63 が「read/patch の group 分割」を**却下済み** (co-location が保証機序)。flock で
   保証を作り直す設計は新機序 = 防壁変更なので裁定が必要。リスクは 43 node の read/write 分類。
5. **`_NPROC_CAP` (現 32)**: L1 実測は n16=69 / n32=71 / n48=72 秒。n16 が最速かつ低負荷だが差は
   2〜3 秒で、律速が group 直列である間は cap を動かしても意味が小さい。3・4 の後に再評価する。
6. **receipt 解決 6.5 秒の内訳**: 4.5 秒は `s8b_holdout_freeze.search_repository` を 1 回の
   `verify_receipt` 内で 2 回呼んでいる分 (holdout 2 件)。T-116 の続きの折り畳み候補 (本番)。
