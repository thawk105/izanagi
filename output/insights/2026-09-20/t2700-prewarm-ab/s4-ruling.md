# 段 4 裁定 — [T-2700] prewarm 早期起動の E/L 隣接対 (plan v2・事前登録・変異登録)

段 3 相談 (`verbatim/s3-consult.md`、gpt-6-astra medium、2 レンズ 1 本、07:43〜07:49 JST): must-fix 7 (A1〜A4、B1〜B3)、should 3 (A5、B4、B5)、nit 2 (A6、B6)。裁定 inbox 再走査: local main は着手 tip `b7f970dfa` から不動 (07:50 JST)。

## 所見の裁定 (real / refuted、採否)

| # | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A1 介入の範囲と H / D の意味 | real | 採用 | 介入 = 「T-2616 の早期 memo 機構全体 (receipt + oracle の早期起動と全 worker の待ち) の有無」と定義し直す。H = worker が記録した collection-finish の最大時刻 (E では早期待ちを含む)、D = 最初の test 開始。D − H を解決の純所要と呼ばない。配布時刻・純 collection・CPU 競合は追加計装なしでは分離できないと明記 |
| A2 検出力が判定規則に対応しない | real | 採用 | 判定規則そのもの (Wilcoxon 片側 exact p ≤ 0.05 ∧ 中央値 ≥ 15 秒) を MC で評価 (`power_rule.py`): 正規誤差 δ=27 / σ_d=22 で 6 対 0.76・8 対 0.85・10 対 0.91、L 側 15 % の裾を混ぜると 8 対 0.50。T-2766 の実対差の SD は 22.1 秒。**必要対数は仮定 (δ、σ_d、裾) に依存し現資料では確定できない — insight にその旨と感度表を残す。目標は有効 8 対 (上限 20 走) の固定予算とし、逐次検定・有意になるまでの追加はしない** |
| A3 exact・同順位・0 差・閾値の意味 | real | 採用 | 平均順位、0 差除外 (m = 非 0 数)、m = 0 → 判定不能、SD = 0 は記述値のみ、相談の反例 4 件を集計器の selftest に固定。15 秒は**便宜的な探索閾値** (機序予測 27 秒の約半分、300 秒目標の 5 %) であり母効果 ≥ 15 秒の証明ではないと明記。片側は事前固定 (機序が改善方向を予測) だが両側 p も併記。各単走差を D357 の「改善実績」に数えない |
| A4 E 固有の失敗を捨てる選択バイアス | real | 採用 | (P6) を撤回。推定対象を 2 つに分ける: (1) 成功走に条件付きの速度差 (対統計)、(2) 全投入の腕別の成功 / 失敗件数。treatment 関連失敗 (E の `memo publication timeout` 等) が 1 件でもあれば「受入短縮を支持」を無条件には出さず「成功走に条件付きの速度差 + E に失敗 k 件」と書く。失敗走は attempt として全件残し、slot は同順序で取り直す。感度分析として「失敗 = 符号上の敗北」の符号検定だけを別枠で出す (∞ を Wilcoxon / t / SD に混ぜない)。両腕失敗・原因不明・成果物欠損・上限到達の扱いを §事前登録に規定 |
| A5 前提実測の標本選択 | should | 採用 | 歴史データは仮説形成に限定。抽出数・除外・条件を表にし、原因説明 (CPU 競合、tip 差) は候補説明と書く。再現用 script は Codex author が `t2700_history_estimate.py` として書き直す (shard_count == 3 ∧ pytest_rc == 0 で絞る) |
| A6 tail の定義 | nit | 採用 | `tail = W − (max_w last_test_finished − timestamp)` に統一 |
| B1 configure 結線と M1 の帰属 | real | 採用 | test は実 `pytest_configure` → 属性 → 実 `pytest_configure_node` の結線を通す (無関係な configure helper は隔離可、対象 helper・判定・結線は stub しない)。L 正例は実 consumer ID を与え、同期 hook 復帰時に cache が実在し reader が成功するまで確認。M1 の期待 kill を新 E 負例に訂正、M6「`pytest_configure` の呼出し削除」を追加。変異は独立 clone のディスク上の conftest に当て、`_load_suite_conftest` が読む `__file__` と一致させる |
| B2 E の unset と存在しない先行 test | real | 採用 | launcher は E で `IZANAGI_T2700_EARLY_MEMO_OFF_V1=` (空文字) を**明示 export** し、request の overlay で compute 側の残留を消す。集計器の検算は「E = 不在または空、L = exact token」。伝播 test は `test_pegasus_dispatch_compute.py` の bytecode env 伝播 test (6747〜6765) を型にし、空文字も request に載ることを検査。PAIRING test は main に無い (T-2766 は impl branch) — plan §1c の参照を訂正 |
| B3 集計器の入力契約・有効走・witness | real | 採用 | §事前登録の「成果物 layout」「有効走」「witness」に固定。junit `timestamp` は offset 付きだけ受理 (naive は失敗)。timeline 欠損は無効走。失敗走でも run.json と存在する log を保存 (launcher は既にそう動く)。witness の stderr は receipt の `result.pbs_jobid` と file 名の job 番号を突き合わせる。L の shard-1/2 に consumer が無いことは測定 SHA の `selected` と `RECEIPT_MEMO_CONSUMER_NODES` / oracle の registry から集計器が検算 (履歴からの断定はしない) |
| B4 非再入性・E 負例の隔離 | should | 採用 | 1 config 1 configure の契約。E 負例と UsageError 負例は新 config を使い `mock.patch.dict(os.environ, ...)` で外側の L 環境 (受入走の worker env に token がある) から隔離する |
| B5 L 経路の生存 | should | 採用 | L 経路は変更しない。B1 の実 cache 正例で固定。「L では起こらない」を一般化しない |
| B6 規模と非 landing 運用 | nit | 採用 | 維持。再現資料 (測定 SHA、実装 commit、launcher・集計器の逐語と hash、事前登録版) を insight に残す |

(P1) 支持、(P2) 条件付きで採用 (A1 / B3 の修正込み)、(P3) → 8 対 / 上限 20 走、(P4) A3 の修正込みで採用、(P5) M1 訂正 + M6 追加、(P6) 撤回 → A4 の規則。

## plan v2 (段 5 の正本)

### 1. conftest (`orchestrator/tests/conftest.py`)

- 定数 (`_EARLY_MEMO_JOB_ATTR` 2305〜2311 の隣): `_EARLY_MEMO_OPT_OUT_ENV = "IZANAGI_T2700_EARLY_MEMO_OFF_V1"`、`_EARLY_MEMO_OPT_OUT_TOKEN = "t2700-early-memo-off"`、`_EARLY_MEMO_OPT_OUT_ATTR = "_izanagi_t2700_early_memo_opt_out"`。
- `_early_memo_opted_out() -> bool` (`_growth_holds_opted_in` 1885〜1897 と同型): 未設定 / 空 → False、exact token → True、他の非空値 → `pytest.UsageError(f"{ENV} must be exactly {TOKEN!r}, empty, or unset")`。
- `_configure_early_memo_opt_out(config) -> None`: True のときだけ `setattr(config, ATTR, True)`。False は属性を置かない (1 config 1 configure)。
- `pytest_configure` (2925〜2945) の try 内、`_growth_holds_opted_in()` の直後に `_configure_early_memo_opt_out(config)`。
- `_early_memo_selected` (2314〜2331) の冒頭に `if getattr(config, _EARLY_MEMO_OPT_OUT_ATTR, False): return False`。
- 変更しない: `_start_early_memo_job` 以降の早期経路、`pytest_configure_node`、`pytest_xdist_node_collection_finished` (L 経路)、`_run_memo_prewarm_barrier` の stderr 行。comment は 2 行以内 (T-2700 の測定用 opt-out、main に入れない)。

### 2. allowlist (`tools/pegasus/dispatch_compute.py` 119〜131) と pin

- `TASKS["tests"].env_allowlist` に `"IZANAGI_T2700_EARLY_MEMO_OFF_V1"` を追加 (comment 1 行)。
- `test_pegasus_dispatch_compute.py::test_tests_task_env_allowlist_is_exact` (6260〜6269) に 1 key 追加。request 生成に (a) exact token、(b) 空文字、が載り未登録 key が落ちる test を 6747〜6765 の型で 1 本。

### 3. test (`orchestrator/tests/test_real_repo_serialization.py`、`_early_memo_cache_probe` 6423〜6470 を再利用)

- **L 正例 (結線 + 実 cache)**: `mock.patch.dict(os.environ, {ENV: TOKEN})` → 新 config (probe と同型) に対し**実 `suite.pytest_configure(config)`** を呼ぶ (無関係 helper `_emit_runner_exclusion_receipt` / `_configure_acceptance_duration_ledger` / `_configure_receipt_memo_session` / `_configure_oracle_environment_memo_session` / `_configure_receipt_memo_run_id` / `mark_pytest_session_enforcing` は必要なら `mock.patch.object` で隔離してよいが `_configure_early_memo_opt_out` と `_early_memo_selected` と `pytest_configure_node` は本物) → 属性 True → 実 `suite.pytest_configure_node(node)` を呼んでも `node.workerinput` に `izanagi_early_memo_paths` が無く `.pending` も無い → `suite.pytest_xdist_node_collection_finished(node, ids)` に実 consumer ID (`RECEIPT_MEMO_CONSUMER_NODES` の 1 つと oracle の consumer 1 つ、prerequisites が True になる形) を渡すと同期 barrier が走り、復帰時に両 cache file が実在し `probe.calls == [["resolve"], ["resolve"]]`、reader (`receipt._make_receipt_memo().get(...)` か `read_existing`、既存 test 6513〜6560 の形) が成功する。
- **E 負例**: 新 config、`mock.patch.dict(os.environ, {ENV: ""})` と key 削除の 2 case → `_early_memo_opted_out()` False、実 `pytest_configure` 後も属性なし、`_early_memo_selected(config)` True (既存 6641〜6645 と同じ引数)、`pytest_configure_node` で早期 job が起動する (既存 6472〜6511 の形)。
- **fail-closed**: `{ENV: "yes"}` → 実 `pytest_configure` が `pytest.UsageError` (message に env 名) を出し、既存 except 経路で nonce が復元される (既存 nonce 復元 test の形があれば同型)。
- **属性経由の証明**: `{ENV: TOKEN}` があっても `pytest_configure` を通らない synthetic config では `_early_memo_selected` True (既存 pin test が L 腕の受入で緑になる根拠)。
- 既存 test (6472〜6660) は変更しない。

### 4. 集計器 `probe-t2700/t2700_ab_analyze.py` と履歴見積り `probe-t2700/t2700_history_estimate.py` (Codex author、標準 library のみ、親が job dir へ退避、repo に入れない)

- 入力契約: `--runs-root <dir>` に `runs/<NN>-<E|L>/run.json` と `runs/<NN>-<E|L>/session/{SHA256SUMS, shard-{0,1,2}/{junit.xml, report.json, dispatch/receipt.json, dispatch/izdw-shard-N.e<job>, dispatch/izdw-shard-N.o<job>}}`。`--measurement-tip <sha>`、`--target-pairs 8`、`--max-runs 20`、`--out <dir>`、`--consumer-nodes <json>` (測定 SHA の `RECEIPT_MEMO_CONSUMER_NODES` と oracle consumer の nodeid list、親が conftest から書き出す) 、`--other-sessions-root <dir>` (任意、記述的対照)。
- 走表 (shard ごと): W、timestamp (offset 必須)、hostname、O・最忙 worker・items、F、H、D、tail、terminal_counts、pytest_rc、shard_count / shard_index / effective_scheduler、`selected` の digest、witness 行 (hook, receipt_memo_s, oracle_environment_memo_s, barrier_s)、job 番号 (receipt `result.pbs_jobid` と stderr file 名の一致)。SHA256SUMS を再計算して照合。
- 有効走: run.json の rc == 0、`tip_sha == tip_sha_after == measurement_tip`、dirty 0、3 shard の report / junit / receipt / stderr が揃う、各 report の `pytest_rc == 0` ∧ failed == error == 0 ∧ shard_count == 3 ∧ shard_index 一致 ∧ scheduler == loadgroup、timeline 実在、junit timestamp に offset、`selected` digest が全有効走で shard ごとに同一、投入・完了時刻が前走と重ならず単調、env が腕に一致 (E: 不在または空、L: exact token)、witness が腕に一致 (E: 3 shard とも `configure_node` 1 行・`xdist_node_collection_finished` 0 行、L: shard-0 に `xdist_node_collection_finished` 1 行・`configure_node` 0 行、shard-1/2 は consumer が無ければ 0 行 (consumer の有無は `selected` × consumer list で検算し、有れば 1 行を要求))。
- 無効走の分類: `treatment-failure` (E の `memo publication timeout` / `IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1` を stderr に含む)、`infrastructure` (rc=16 で上記以外、receipt 不発行)、`red` (test 赤)、`artifact` (成果物欠損 / sha 不一致 / witness 不一致 / SHA 不一致)、`unknown`。
- 対: slot ごとに期待順序 (E,L / L,E / E,L / L,E / E,L / L,E / E,L / L,E) で、投入順に隣接する有効 2 走の最初の組。有効対が `--target-pairs` に達した時点で確定、超過走は表に残すが判定に使わない。未達 (上限到達) は達成対数で判定し「未達」と明記。
- 対統計: ΔW = W_max(L) − W_max(E)、r = ΔW / W_max(E)、ΔD_0、ΔH_0、ΔO_0、Δtail_0、shard 別 ΔW_s。中央値 3 種 (対差・対率・条件別中央値差)。
- 検定: Wilcoxon 符号順位 exact 片側 (H1: ΔW > 0、平均順位、0 差除外、全列挙)、両側 p も併記、対応のある t (統計量、df、臨界値表 df 2〜19)、σ_d、感度: 観測 σ_d と δ ∈ {15, 20, 27} で規則の検出力を MC (seed 固定、正規 + 裾 model) で再計算。
- 判定 (事前登録): 下記 §事前登録。
- 失敗の集計: 腕別の投入数・成功数・失敗種別。感度分析 (失敗 = 符号上の敗北の符号検定) を別枠。
- selftest: 合成 runs で有効 / 無効の各分類、対の組み方 (取り直し・超過・未達)、Wilcoxon の反例 4 件 (`+40×5, −45×1` → p = 17/64 = 0.265625 未確立、`10,20,30,40,50,−60` → 14/64 = 0.21875 未確立、`+5〜+10 × 6` → 1/64 方向のみ、`0,0,12,20,30,40` → m=4 → 1/16 = 0.0625 未確立)、timestamp の naive 拒否、witness の job 番号不一致の拒否。
- `t2700_history_estimate.py`: `/work/1/SFC/tanab/.izanagi-acceptance-shards/` を読み、hook 別 (L = `xdist_node_collection_finished`、E = `configure_node`) に shard_count == 3 ∧ pytest_rc == 0 ∧ timeline 実在で絞った H / D / W / O / F / tail / rm の分布と、抽出数・除外数・日付範囲を表にする (brief の前提実測の再現、`--e-limit N` で E の直近 N shard)。

### 5. launcher (親、job dir) の改訂点

- E: `export IZANAGI_T2700_EARLY_MEMO_OFF_V1=` (空文字、request に載せて compute 側の残留を消す)。L: exact token。`env.txt` に記録。
- 複製 layout は §4 の入力契約に固定。失敗走も run.json と存在する log を残す (既存)。
- 順序: 01-E(1) 02-L(1) 03-L(2) 04-E(2) 05-E(3) 06-L(3) 07-L(4) 08-E(4) 09-E(5) 10-L(5) 11-L(6) 12-E(6) 13-E(7) 14-L(7) 15-L(8) 16-E(8)。無効走は同順序で取り直し (上限 20 走)。

## 事前登録 (結果を見る前に固定)

- **介入:** T-2616 の早期 memo 機構全体の有無 (E = 現行 = 早期起動あり、L = opt-out = collection 通知時の同期 prewarm)。同一 SHA、同一 worktree、直接投入、逐次・交互。
- **推定対象 (2 つ):** (1) 成功走に条件付きの速度差: 隣接有効対の ΔW = W_max(L) − W_max(E)。(2) 全投入の腕別成功 / 失敗件数と失敗種別。
- **指標:** W_s、W_max、O_s、F_s、H_s、D_s、tail_s (定義は plan v2 §4)、ΔW、r、ΔD_0、ΔH_0、ΔO_0、Δtail_0。
- **対数:** 有効 8 対で固定終了。投入上限 20 走。逐次検定・途中終了・有意になるまでの追加はしない。上限到達時は達成対数で判定し「未達」と明記。
- **判定 (成功走の速度差):** m = 非 0 の ΔW の数。m = 0 → 判定不能。Wilcoxon 符号順位 exact 片側 p (H1: ΔW > 0) ≤ 0.05 ∧ 標本中央値 ΔW ≥ 15 秒 → 「成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上)」。p ≤ 0.05 ∧ 中央値 < 15 秒 → 「方向は支持、大きさは探索閾値未満」。p > 0.05 → 「n の範囲で効果未確立」。いずれも両側 p、t 統計量、σ_d、観測 σ_d での検出力再計算を併記。15 秒は便宜的な探索閾値であり母効果の証明ではない。
- **失敗の扱い:** E または L に treatment 関連失敗 (E: `memo publication timeout` 型) が 1 件でもあれば、上の判定に「+ 腕別失敗件数」を必ず併記し、無条件の「受入短縮を支持」を書かない。失敗走の slot は同順序で取り直す。両腕失敗・原因不明は `unknown` として件数に残す。感度分析: 失敗を符号上の敗北 (E 失敗 = ΔW < 0、L 失敗 = ΔW > 0) とした符号検定を別枠で報告 (対統計には混ぜない)。
- **記述的対照:** 測定窓内の他 wave の受入 session (tip は違う) の shard-0 W / D / hook 名。主解析の停止条件にしない。
- **必要走数の見積り (事前):** 仮定依存で確定できない。感度表 (`power_rule.py` の出力) を insight に載せ、測定後に観測 σ_d で再計算する。

## 変異登録 (DW-M01、独立 clone、計算ノード、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_real_repo_serialization.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf`)

| # | 変異 (1 理由) | 位置 | kill を期待する検査 |
|---|---|---|---|
| M1 | `_early_memo_opted_out` を恒真 (未設定でも True) | 同関数の `if value in (None, ""): return False` | 新 E 負例 (未設定 / 空で属性なし・selected True・早期 job 起動) |
| M2 | `_configure_early_memo_opt_out` が属性を置かない | 同関数の `setattr` | L 正例 (実 configure 後の属性・結線) |
| M3 | `_early_memo_selected` の属性 check を削除 | 同関数冒頭の 1 行 | L 正例 (属性ありで早期 job が起動しないこと) |
| M4 | allowlist の key を削除 | `dispatch_compute.py` `TASKS["tests"].env_allowlist` | exact pin と request 伝播 test |
| M5 | 他の非空値で UsageError を出さず False | `_early_memo_opted_out` の `raise` | fail-closed 負例 |
| M6 | `pytest_configure` の `_configure_early_memo_opt_out(config)` 呼出しを削除 | `pytest_configure` の 1 行 | L 正例 (実 `pytest_configure` を通す結線検査) |

probe 走 (全件 SURVIVED 期待で観測 node を集める) → final 走 (期待 node 完全集合を登録) の 2 段 (T-2766 と同じ)。

## 段構成

軽量版: 段 5 author 1 本 (所有 = conftest / dispatch_compute / test_real_repo_serialization / test_pegasus_dispatch_compute / probe-t2700/*)、段 6 レビュー 2 本 (正しさ境界 / 過剰・削除 = DW-S06-A の必須 2 本) + fix + 焦点再レビュー 1 本 (必要時) + 変異 matrix + 焦点走。実装は impl branch `impl-t2700-early-memo-optout` に保存し landing は docs-only (D2164 決定 3 の型)。

## 訂正注記 (段 6 焦点再レビュー後、測定前・2026-09-20 09:00 JST。本文は段 4 時点の逐語のまま)

- 上表 A2 の「L 側 15 % の裾を混ぜると」は誤り。`power_rule.py` の裾 model は正規成分 SD σ に**両腕独立** (各 15 %、+30〜90 秒 / −30〜90 秒) の遅延を混ぜた対称 model で、σ は対差全体の SD ではない (段 6 レビュー B5、焦点再レビュー)。
- 変異登録 M6 の期待 kill は L 正例に加え fail-closed 負例 (`test_early_memo_opt_out_invalid_configure_fails_closed`) も含む 2 node、M4 は exact pin + 伝播 test の token / empty の 3 node (probe の観測で確定、README §4)。
- 事前登録の「対数 8 / 上限 20」に、焦点再レビュー後の系列規則 (slot 内無効なら同 slot を同順序で直ちに取り直す、`--series-state` が唯一の判定主体、投入前 abort は番号を消費しない) を加えた (`run-series.sh` v3、README §5)。門番の leaders 上限は投入前に 1 → 2 へ緩めた (README §5)。
- treatment-failure の検出先は stderr だけでなく stdout / child.log を含み、両 memo の fail-closed prefix と `publication-timeout` を扱う (レビュー A1)。
