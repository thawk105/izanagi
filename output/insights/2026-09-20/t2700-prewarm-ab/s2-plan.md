# 段 2 plan (親起草、軽量版) — [T-2700] prewarm 早期起動の E/L 隣接対

前提: brief (`s1-brief.md`) の (P1)〜(P6)。worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2700-prewarm-ab` (HEAD = local main `b7f970dfa`)。

## 1. 実装 (Codex author、unit worktree `.codex/worktrees/t2700-unit-impl`、base = wave tip)

### 1a. `orchestrator/tests/conftest.py`

- 定数 (`_EARLY_MEMO_JOB_ATTR` の隣、2305〜2311 付近): `_EARLY_MEMO_OPT_OUT_ENV = "IZANAGI_T2700_EARLY_MEMO_OFF_V1"`、`_EARLY_MEMO_OPT_OUT_TOKEN = "t2700-early-memo-off"`、`_EARLY_MEMO_OPT_OUT_ATTR = "_izanagi_t2700_early_memo_opt_out"`。
- 新関数 `_early_memo_opted_out() -> bool` (`_growth_holds_opted_in` 1885〜1897 と同型): env 未設定 / 空 → False、exact token → True、他の非空値 → `pytest.UsageError(f"{ENV} must be exactly {TOKEN!r}, empty, or unset")`。
- 新関数 `_configure_early_memo_opt_out(config) -> None`: `_early_memo_opted_out()` が True のときだけ `setattr(config, _EARLY_MEMO_OPT_OUT_ATTR, True)`。False なら属性を**置かない** (E 腕 = 現行と属性面まで同一)。
- `pytest_configure` (2925〜2945): `_growth_holds_opted_in()` の直後に `_configure_early_memo_opt_out(config)` を呼ぶ (UsageError は既存の except 経路で nonce 復元後に伝播)。
- `_early_memo_selected` (2314〜2331): 冒頭に `if getattr(config, _EARLY_MEMO_OPT_OUT_ATTR, False): return False` を足す。既存の判定順序・narrowing 集合は不変。
- 変更しない: `_start_early_memo_job` / `_wait_early_memo_job` / `_finish_early_memo_job` (2334〜2441)、`pytest_configure_node` (2528〜2560)、`pytest_xdist_node_collection_finished` (2564〜2640、L 経路 = `_EARLY_MEMO_JOB_ATTR` 不在で barrier が走る)、`_run_memo_prewarm_barrier` の stderr 行 (2475〜2484、witness)。

### 1b. `tools/pegasus/dispatch_compute.py` 119〜131

- `TASKS["tests"].env_allowlist` に `"IZANAGI_T2700_EARLY_MEMO_OFF_V1"` を 1 行追加 (コメント 1 行: 測定 wave の opt-out、main に入れない)。

### 1c. test

- `orchestrator/tests/test_real_repo_serialization.py` (6472〜6645 の隣、`_early_memo_cache_probe` 6423 を再利用):
  - 正例 (L): `mock.patch.dict(os.environ, {ENV: TOKEN})` の下で `_early_memo_opted_out()` True、`_configure_early_memo_opt_out(config)` が属性を置き、`_early_memo_selected(config)` が False、`pytest_configure_node(node)` を呼んでも `node.workerinput` に `izanagi_early_memo_paths` が入らず `.pending` も作られない。続けて `pytest_xdist_node_collection_finished(node, ())` で `_EARLY_MEMO_JOB_ATTR` 不在 → barrier が走る (probe の `calls` に resolve が記録される、prerequisites は `ids=()` だと False なので resolve 0 件 = 「L 経路の barrier に入った」は `_run_memo_prewarm_barrier` の hook 名で確認するか、`ids` に consumer node を 1 つ渡す)。
  - 負例 (E): env 未設定 / 空 → `_early_memo_opted_out()` False、属性なし、`_early_memo_selected(config)` True (既存 6641〜6645 と同じ引数)。
  - fail-closed: 他の非空値 → `pytest.UsageError` (message に env 名)。
  - 属性経由の証明: env に TOKEN があっても `_configure_early_memo_opt_out` を通らない synthetic config では `_early_memo_selected` が True のまま (既存 pin test が L 腕の受入で緑になる根拠)。
- `orchestrator/tests/test_pegasus_dispatch_compute.py` 6260〜6269 `test_tests_task_env_allowlist_is_exact`: 集合に 1 key 追加。request 生成に env が載る test は T-2766 の `IZANAGI_ACCEPTANCE_PAIRING_V1` の test (同 file、`grep -n PAIRING`) を同型で 1 本。

### 1d. 集計器 `t2700_ab_analyze.py` (Codex author、unit worktree の `probe-t2700/` → 親が job dir へ退避、repo に入れない)

入力: `--runs-root <job dir>/runs`、`--measurement-tip <sha>`、`--out <dir>`、`--pairs 6`。各 `runs/<NN>-<E|L>/` の `run.json` (launcher が書く: run / condition / pair_slot / tip_sha / tip_sha_after / submitted_at / finished_at / rc / dirty_lines / other_leaders / load1 / env / session_dir_origin) と `session/shard-{0,1,2}/{junit.xml, report.json, dispatch/izdw-shard-N.e*}` を読む。

- 走表: shard ごとに W (junit `<testsuite time>`)、timestamp、hostname、O = max `worker_occupancy[*].duration_s`、最忙 worker と items、F = W − O、H = `session_timeline.collection_finished_epoch_s` − timestamp epoch、D = min_w `first_test_started_epoch_s` − timestamp、tail = W − (max_w `last_test_finished_epoch_s` − timestamp)、terminal_counts (failed / error)、pytest_rc、witness = stderr の `IZANAGI_MEMO_PREWARM_V1` 行の list (hook, receipt_memo_s, barrier_s)。
- witness 判定: E = 3 shard とも `configure_node` 行が 1 本ずつあり `xdist_node_collection_finished` 行なし。L = shard-0 に `xdist_node_collection_finished` 行が 1 本、`configure_node` 行なし、shard-1/2 は行なし (consumer node 不在)。不一致は無効。env: E は `IZANAGI_T2700_EARLY_MEMO_OFF_V1` 不在、L は exact token (run.json の env)。
- 有効走: rc==0、3 shard とも failed == error == 0、report.json / junit.xml が揃う、tip_sha == tip_sha_after == measurement tip、dirty 0、witness 一致。
- 対: slot ごとに投入順の隣接 2 走 (期待順序 E,L / L,E / E,L / L,E / E,L / L,E)。無効走を含む slot は同順序で取り直した走で埋める (走番号は単調、集計器が順序と欠番を検算)。有効対が 6 に達した時点の対だけを判定に使う (超過分は表に残す)。
- 対統計: ΔW = W_max(L) − W_max(E)、r = ΔW / W_max(E)、ΔD_0、ΔO_0、Δtail_0、shard 別 ΔW_s。中央値 (対差・対率・条件別中央値差) を別量で。
- 検定: Wilcoxon 符号順位 exact (片側 H1: ΔW > 0、n ≤ 12 の全部分集合列挙で p を計算、0 差は除外)、対応のある t (t 統計量、df、両側 5 % の臨界値表 df 2〜11 を埋め込み)、σ_d の実測 (sd of ΔW)、MDE = t_crit × σ_d / √n、δ=27 に対する必要対数 (n = ((t_crit + t_0.8)·σ_d/27)²、表から)。判定 = brief (P4)。
- 記述的対照: `/work/1/SFC/tanab/.izanagi-acceptance-shards/` の測定窓内 (最初の投入〜最後の完了) の他 session の shard-0 W / D / hook 名 (tip は違う)。
- 出力: `analysis.json` (全量) と `analysis.md` (表)、`--selftest` (合成 runs で対表・検定・witness 判定の正例負例)。

## 2. launcher (親、job dir、`run-measure.sh` = T-2766 の launcher を改訂)

- usage `run-measure.sh <NN> <E|L> <slot>`。flock 直列化 → 門番 (他 session の受入待ち手 ≤ 1 かつ load1 < 30、100〜140 秒周期 2 回連続 + 0〜45 秒乱数) → HEAD == measurement tip かつ clean → RUN dir mkdir → env (`IZANAGI_ACCEPTANCE_SHARDS=3`、L だけ `IZANAGI_T2700_EARLY_MEMO_OFF_V1=t2700-early-memo-off`、`PYTHONDONTWRITEBYTECODE` unset) → `python3 tools/run_tests.py` → 終了後 HEAD / clean 再記録 → session の 3 shard の `junit.xml` / `report.json` / `dispatch/receipt.json` / `dispatch/shard-N/izdw-shard-N.{e,o}*` を sha256 付きで複製 → `run.json`。
- 系列 `run-series.sh`: 01-E(1) 02-L(1) 03-L(2) 04-E(2) 05-E(3) 06-L(3) 07-L(4) 08-E(4) 09-E(5) 10-L(5) 11-L(6) 12-E(6)。無効走が出たら親が同順序で取り直す第 2 系列を起動 (上限 16 走)。
- warm-up: 測定前に計算ノードで collect-only 1 走 (`PYTHONDONTWRITEBYTECODE=` を allowlist 経由、T-2766 の `run-warm2.sh`) で共有 FS の pyc を温める。

## 3. 検査

- 焦点走 (計算ノード、`--force-dispatch`): `test_real_repo_serialization.py` / `test_pegasus_dispatch_compute.py` / `test_run_tests_shards.py` / `test_run_tests_preflight.py` / `test_hold_inventory.py` (DW-O26: `_early_memo_selected` と allowlist の consumer)。
- 変異 matrix (独立 clone、計算ノード): M1 `_early_memo_opted_out` を恒真 (env 未設定でも True) → 負例 (E) と既存 `test_early_memo_narrowing_destinations_match_real_parser` が kill。M2 `_configure_early_memo_opt_out` が属性を置かない → 正例 (L) が kill。M3 `_early_memo_selected` の属性 check を削除 → 正例 (L) が kill。M4 allowlist の key を削除 → pin と request 伝播 test が kill。M5 他の非空値で UsageError を出さず False → fail-closed test が kill。
- 測定 tip = wave tip + docs commit (s1/s2/s4) + 実装 commit。実装 commit は impl branch `impl-t2700-early-memo-optout` に保存し、landing branch は main + 記録だけ (D2164 決定 3 の型)。
