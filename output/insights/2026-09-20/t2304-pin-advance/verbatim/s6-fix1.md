## 変更の要約

tracked 11 file と probe 1 file を変更しました。commit は作成していません。

| file | 変更 |
|---|---|
| `test_dynamic_backoff_transitions.py` | 現 checkout の `PIN_FULL` を更新 |
| `test_t2187_adaptive_const_probe.py` | 現行 pin 更新、t2417 producer fixture 内だけ旧系列 pin を注入 |
| `tools/pegasus/probes/t2187_adaptive_const_probe.py` | `PIN_FULL` のみ更新 |
| `test_s8b_protocol_builder.py` | 旧 bytes／SHA を保持し、新 builder golden を追加 |
| `test_s8a_trigger_sweep.py` | policy SHA・campaign ID を新 epoch に追随 |
| `test_campaign.py` | representative・backoff・S6・cache key の新 epoch を追加 |
| `test_autonomous_trial_completeness.py` | 旧 current を T816 として保持し、current ID と epoch 対を更新 |
| `test_p3_s4_loop_trigger_gating.py` | OTHER／COMPUTE の新 epoch を追加 |
| `test_p3_s4_loop_sort.py` | ordinary campaign の新 epoch を追加 |
| `test_s8b_floor_campaign.py` | clone の gitlink を選択対象 protocol の pin に合わせる fixture 修正 |
| `orchestrator/campaign/buildcache.py` | docstring の実測範囲を更新 |
| `tools/dev-wave-probe/t2304_shape_probe_job.sh` | 再作成し、`T2304_CMAKE` 優先の1行を追加 |

変更した test 9 file は、test 関数数・assert 件数をすべて維持しています。skip／xfail の追加、期待値の反転・緩和はありません。

## 族ごとの対応表

赤 node 数は、親の一覧に対する静的な原因説明です。修正後の合格数ではありません。

| 族 | 対応 | 説明できた赤 |
|---|---|---:|
| 1 | dynamic backoff の checkout pin 更新 | 75 errors |
| 2 | t2187 の実 checkout 照合更新、t2417 producer 3件を旧系列 fixture に固定 | 4 failed |
| 3 | builder bytes／SHA／freeze 結果 SHA 更新 | 3 failed |
| 4 | synthetic receipt の policy SHA と S8A ID 更新 | 6 failed |
| 5 | campaign／cache key の epoch 追加 | 4 failed |
| 6 | autonomous の current golden と epoch 対更新 | 57 failed |
| 7 | 族2の production pin 更新で certification の前段拒否を解消する構成 | 24 failed |
| 8 | trigger 2件・sort 1件の ID 更新 | 3 failed |
| 9 | versioned protocol の pin に fixture checkout を整合 | 3 failed |
| 10 | 旧実測と新 CMake 3.25.0 実測を区別して記載 | 対象なし |
| 11 | CMake 選択用 probe 改訂 | 対象なし |
| **合計** | | **104 failed／75 errors** |

補足：

- t2187 file に campaign ID literal はありません。分類表で混在していた `p3-t178-…`／`p3-s5-sort-…` は autonomous／sort 側で対応しました。
- S8A は指定の `load_effective_reasons` 4件に加え、`mismatched_receipts[…-outer SHA]` も旧 policy SHA によって目的の拒否判定へ到達していませんでした。
- t2417 fixture 内で `probe.PIN_FULL`／`probe.CURRENT_PIN` を旧値にするため、これらを参照する合成 artifact も旧系列に揃います。analysis の production 定数は変更していません。

## 再計算した golden 値

再計算コードは [t2304_recalculate.py](/tmp/t2304_recalculate.py)、全出力は [t2304_golden_after.json](/tmp/t2304_golden_after.json) にあります。test 関数は実行せず、production 関数を直接呼びました。

policy は次の preimage を `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)` で正準化し、UTF-8 の SHA-256 を独立計算しました。

```text
schema = build-admission-policy/v1
repo_stock_pin = e9e477c
coder_authority = cli-opt-in
generator_registry = sorted(GeneratorId.value)
review_registry = sorted(ReviewId.value)

SHA256 = db6bc9ea80440a5e0d162319b0d91efab9fb3783a959bc3a2931601e253ca18a
```

resolver の返す SHA と一致しました。

以下の campaign ID は、各 test と同じ config に対する `str(ident.campaign_id(cfg))` の結果です。契約 fixture は test と同じ `GENERATIONS[tag][0].contract` を使いました。

| 入力・式 | 新 golden |
|---|---|
| representative `_cfg()` | `readheavy-locont-fullsearch-c301cc73` |
| backoff `config_for(write-heavy)`、commit=`dff0f1e` | `backoff-sweep-silo-write-heavy-sweep-6297b00c` |
| 同 balanced | `backoff-sweep-silo-balanced-sweep-21777a4d` |
| 同 read-heavy | `backoff-sweep-silo-read-heavy-sweep-611a783b` |
| backoff 現行 write-heavy | `backoff-sweep-silo-write-heavy-sweep-4b8f83c9` |
| 同 balanced | `backoff-sweep-silo-balanced-sweep-080a1603` |
| 同 read-heavy | `backoff-sweep-silo-read-heavy-sweep-f9c15ce6` |
| S6 `config_for(balanced)` | `p3-s6-sort-sweep-balanced-sweep-c691213c` |
| 同 write-heavy | `p3-s6-sort-sweep-write-heavy-sweep-33edc1ec` |
| S8A `config_for(balanced, EFF3)` | `p3-s8a-trigger-sweep-balanced-sweep-8ee9d0be` |
| 同 write-heavy | `p3-s8a-trigger-sweep-write-heavy-sweep-49fa575c` |
| autonomous fixture-completeness／ycsb-a | `p3-t178-ycsb-a-workload-conditioned-autonomous-d567badf` |
| 同 ycsb-b | `p3-t178-ycsb-b-workload-conditioned-autonomous-5d0213d9` |
| 同 ycsb-c | `p3-t178-ycsb-c-workload-conditioned-autonomous-38cdb6b4` |
| autonomous trial-a／ycsb-a | `p3-t178-ycsb-a-workload-conditioned-autonomous-cc0440a2` |
| autonomous trial-b／ycsb-a | `p3-t178-ycsb-a-workload-conditioned-autonomous-385d8a2d` |
| trigger `_campaign_cfg_for_site(default_cfg(), OTHER)` | `p3-s8a-trigger-loop-s8a-trigger-autonomous-10220031` |
| 同 PEGASUS_COMPUTE | `p3-s8a-trigger-loop-s8a-trigger-autonomous-6856dc81` |
| sort `default_cfg(reflux=True)` | `p3-s5-sort-loop-s5-sort-autonomous-fa3db023` |

`EFF3 = ["lock-conflict", "readvali-tid", "readvali-locked"]`。autonomous は各 workload の descriptor、`generations=1`、S8A generator context を渡す既存 `_campaign_for` の構成です。

cache key の式・入力：

```text
g0 = silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0
commit = dff0f1ef2a4b84746f6463839e85b24301f4b16d
admission = 現行 pin の stock admission

buildcache.cache_key(g0, commit, False, admission=admission)
= silo_23cc2a2610_t0
```

builder は `build_protocol_document(seed, env, stock_configuration="stock_common", extime_s=5, wired_min_rel_floor=floor)` を呼び、返された canonical bytes を `hashlib.sha256` でも照合しました。

| seed／env／floor | bytes | SHA-256 |
|---|---:|---|
| `golden-master-seed`／`linux-baremetal`／`0.05` | 775 | `481fdf8e1ead63ef485a231ea92f3b8ee25c2df63c03688d7689cf56aeb40e1b` |
| `2026-07-18T17:16:12+09:00`／`pegasus`／`0.03` | 774 | `62f1387dba4f191ec4545cf533671ece52532139237f275fa87351a0e9e812db` |

golden document の旧版との差は `ccbench_pin` のみです。test 内では独立 literal を維持しています。

## 説明できなかった赤

なし。これは親ログとコードによる原因説明であり、修正後の pytest による確認は未了です。

## 実走結果

- `python3 -c` による golden 再計算：成功。変更後の再計算も同一結果。
- 追加 literal と再計算出力の全照合：成功。
- 変更 Python 11 file の `python3 -m py_compile`：成功。
- probe の `bash -n`：成功。退避版との差は環境変数選択の1行のみ。
- `git diff --check`：成功。
- 凍結成果物、docs、analysis の旧 pin、`p3_s4_loop.py`：差分なし。
- pytest：**未実走、実行 node 0件**。

## 未了・懸念

- 親側で修正後の焦点走・受入検証が必要です。
- 新 pin の CMake 3.22.1 は未確認です。改訂 probe は作成済みですが、本体は実行していません。
- 旧 campaign lock／receipt に対する現行 policy の拒否は維持しています。既存系列の再開や successor protocol の reseal は本修正で解決したとは扱いません。
- `git add`／`commit`／`checkout`／`stash` は実行していません。

## 総括

指定11族の修正と golden 再計算を完了しました。歴史値・凍結成果物・検証述語を保持し、構文検査と静的照合は成功しています。pytest 合格は未確認です。

自動実行審査の `guard_bash` が pytest 直接実行を拒否しました。理由は「Pegasus ログインノードでは重い処理を直接実行せず、計算ノードを使うこと」です。迂回していません。