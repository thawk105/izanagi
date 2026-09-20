# [T-2700] receipt memo prewarm の早期起動 (T-2616) の効果を、同一 SHA の実受入で早期起動あり (E) / なし (L) の隣接対 7 組で対比較した — 7 対とも E (早期起動あり) が短く、最遅 shard の wall の対差は +22.0〜+122.3 秒 (対差の中央値 +33.5 秒、対率 6.9 %、条件別中央値差 +29.2 秒)、Wilcoxon 片側 exact p = 1/128 = 0.0078。機序指標 (配布開始の遅れ ΔD_0) は +24.9〜+40.7 秒で事前予測 (≈ 27 秒) と整合。事前に必要走数は確定できず (仮定依存)、有効 8 対の固定予算は上限 20 走で 7 対に留まった (未達)。E 腕に既知の間欠赤 3 走 (L は 0)、treatment 固有の失敗は 0

一次資料 (wave `dev-wave-t2700-prewarm-ab`、measurement tip `7447c9a35c769ff6b962d364ed5f9fd0c089c749` = local main `b7f970dfa` + docs commit `ca8adec7b` + 実装 commit `7447c9a35`、測定 2026-09-20 10:14〜17:55 JST)。段 1〜4 の逐語は同 dir の `s1-brief.md` / `s2-plan.md` / `s4-ruling.md`、段 3 相談・段 5 author・段 6 レビュー 2 本・fix 5 本・焦点再レビューの逐語は `verbatim/`、集計は `analysis/` (射影)、走ごとの記録は `runs/`、系列の log と最終状態は `series/`、履歴見積りは `history/`、変異は `mutation/`、launcher・集計器・見積り script の逐語と sha256 は `probe-source.md`。**受入証跡ではない** (land 用の受入受領証は段 9 の land が持つ)。実装は main に入れない (§8)。

## 1. 依頼・不変条件・結論

依頼 (command 引数、entry 1546 の T-2700 起票文、D1936 項 35): T-2616 (entry 1546) の早期起動の効果が n=1 (289.1 秒) で同時刻の対照が無い件について、まず必要走数を見積もり、次に同じ窓で早期起動あり / なしを交互に投入する対照走を計算ノードで取る (T-2766 の型 = D2164 決定 1: 同一 SHA の wave worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入し最遅 shard の wall を対で比べる)。効果量・分散が足りず必要走数を確定できないならその旨を残す。prewarm の義務化・launcher の自動検査・実装変更は含めない。新 gate・台帳・一般化は scope 外。規律 2 を緩めない。

不変条件を守った: 受理集合・hold・group・順序は変えていない。切替は測定用の opt-out (env `IZANAGI_T2700_EARLY_MEMO_OFF_V1` の exact token `t2700-early-memo-off` でだけ発火、他の非空値は `UsageError`、未設定 / 空 = 現行 E) で、実装は impl branch に置き main に入れない (D2164 決定 3 の型)。測定中は自分の他 job を走らせていない (D357。変異 final の完了後に測定を開始した)。判定規則・対数・取り直し規則は結果を見る前に固定した (`s4-ruling.md` §事前登録 + 系列規則 = `run-series.sh` v3 冒頭、焦点再レビュー後・測定前)。全測定走は同一 SHA・同一 worktree から直接投入し、投入直前・終了後の HEAD と clean を照合した (集計器が全走で検算)。

結論 (数値は §5〜§6、判定規則は事前登録どおり):

1. **有効 7 対とも L (早期起動なし) が遅い。** 最遅 shard (7 対とも shard-0) の JUnit wall W_max の対差 ΔW = W_max(L) − W_max(E) = +122.3 / +23.3 / +22.0 / +39.4 / +41.8 / +33.5 / +29.1 秒 (対率 31.7 / 4.8 / 4.6 / 8.0 / 8.4 / 6.9 / 6.0 %)。対差の中央値 +33.5 秒、対率の中央値 6.9 %、条件別中央値差 med W_max(L) 513.6 − med W_max(E) 484.4 = +29.2 秒。Wilcoxon 符号順位 exact 片側 p = 1/128 = 0.0078 (両側 0.0156、m=7、W+ = 28)、対応のある t = 3.35 (df 6、両側 5 % 臨界値 2.447)、σ_d = 35.1 秒。事前登録の判定 = **「成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上)」+ 腕別失敗件数 E=3 / L=0**、対数は **未達 (7/8、上限 20 走で締切)**。
2. **機序指標が予測と整合する。** shard-0 の配布開始 (最初の test 開始) D_0 は E で 59.6〜60.6 秒 (7 走とも ≈ 60)、L で 84.9〜101.3 秒。ΔD_0 = +24.9 / +26.7 / +40.7 / +37.1 / +32.8 / +34.6 / +30.2 秒 (中央値 +32.8)。事前予測 (過去 session からの ≈ 27 秒、§2) の範囲。対 1 以外は ΔW ≈ ΔD_0 (ΔO_0 = −22.1〜+6.9 秒) で、**wall の差は配布開始の遅れがそのまま乗ったもの**。対 1 だけ最忙 worker の占有 O_0 が E 315.3 / L 413.7 秒 (ΔO_0 = +98.4) で、これは早期起動の機序ではない regime の差 (01-E の最忙 worker が他の E 走 (410〜425 秒) より 100 秒短い) が乗った対である。
3. **witness (腕の発火) は全走で事前登録どおり。** E は 3 shard とも stderr に `configure_node` 行 1 本 (receipt_memo_s 53.5〜58.6 秒 = collection と並走した解決)、L は shard-0 だけ `xdist_node_collection_finished` 行 1 本 (receipt_memo_s 28.6〜51.8 秒 = collection 通知後の同期解決) で shard-1/2 は行なし (consumer 不在を集計器が `selected` × consumer 集合で検算)。E では解決 (≈ 55 秒) が worker の collection (H ≈ 60 秒) に隠れて配布が ≈ 60 秒で始まり、L では collection 完了後に ≈ 30〜50 秒の同期解決が入る — これが ΔD_0 の正体。
4. **効果は shard-0 だけに出た。** shard-1 の ΔW = +0.8 / +3.1 / −0.6 / +0.7 / −6.2 / −2.0 / −1.5、shard-2 = −2.7 / +40.0 / −1.3 / +3.8 / −47.6 / −0.2 / −3.8 (shard-2 の ±40〜48 は 03-L / 11-E の shard-2 が単独で 241〜251 秒だった外れ)。shard-1/2 は consumer が無く L でも prewarm しないため、E の「shard-1/2 も ≈ 60 秒まで待つ」不利は W に現れなかった (両腕とも H ≈ 60 秒で collection が律速)。
5. **腕別の失敗 (推定対象 2)。** 20 投入のうち E 10 走 / L 10 走、無効は E の `red` 3 走 (08-E `test_real_repo_writer_drains_overlapping_reader_stream[legacy]`、14-E `test_s8b_floor_campaign.py::test_official_fresh_issues_certificate_and_binds_wall_ledger`、17-E `test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy]`、いずれも 25418 passed / 1 failed、他 wave の受入 session でも同じ赤が出ている既知の間欠 (lock relay の timing、`output/runs/` 一時 dir の scandir race)、早期起動とは無関係)。**treatment 固有の失敗 (`memo publication timeout`) は E / L とも 0 件。** 失敗を符号上の敗北に数える感度分析 (7 勝 3 敗、片側 p = 0.17) は有意でない — 成功走の速度差 (結論 1) と全投入の腕別失敗件数は別の推定対象であり、後者は「E に既知の間欠赤が 3 回当たった」以上の主張をしない。
6. **必要走数は事前に確定できなかった (§2)。** 観測 σ_d = 35.1 秒 (対 1 の +122 が押し上げ) で事後に判定規則の検出力を再計算すると、δ = 27 秒・7 対で 0.47 (正規)、0.34 (裾 model) — 事前の仮定 (σ_d 17〜25) より分散が大きく、7 対で p = 1/128 が出たのは効果が一貫して同方向だったことによる。8 対目は上限 20 走の締切で取れなかった (無効 3 走の取り直しに 6 走を使った)。
7. **実装は main に入れない。** 効果の有無にかかわらず本 wave の裁定 (`s4-ruling.md`) どおり、landing は記録 (本 dir + spool fragment) だけ。実装 commit `7447c9a35` は branch `impl-t2700-early-memo-optout` に保存 (§8)。**早期起動 (T-2616) は現行 main の挙動 (E) であり、本測定は「現行を止めると最遅 shard が ≈ 30 秒遅くなる」を示した。義務化・launcher の自動検査は scope 外 (D1936 項 35) で、次の一手は §7。**

## 2. 必要走数の事前見積り (結果を見る前、`s1-brief.md` / `s4-ruling.md`、script は `probe-source.md`)

### 2a. 機序の定量化 (過去 session、仮説形成用。tip も日付も違う記述的資料)

`/work/1/SFC/tanab/.izanagi-acceptance-shards/` の受入 session (計算ノード job の stderr の `IZANAGI_MEMO_PREWARM_V1` 行で経路を同定、Codex author の `t2700_history_estimate.py`、shard_count == 3 ∧ pytest_rc == 0 ∧ timeline 実在 ∧ timestamp offset 付きで絞る、`history/history.md`):

| 経路 | 抽出 | H = worker 記録の collection-finish 最大 (秒) | D = 最初の test 開始 (秒) | D − H | 解決所要 rm (秒) | W (秒) | F = W − O |
|---|---|---|---|---|---|---|---|
| L (`xdist_node_collection_finished`、09-14〜16、shard-0 だけ発火) | 122 shard / 122 session | 中央値 56.2 (p10 55.4 / p90 82.2) | 86.3 (p10 81.6 / p90 116.5) | 30.5 | 32.0 (p10 28.8 / p90 36.6) | 351.7 | 93.3 |
| E (`configure_node`、09-20 02:30〜08:01 の直近、3 shard とも発火、shard-0 の表) | 17 shard / 17 session | 中央値 60.0 (p10 59.5 / p90 67.8、最大 143.8) | 60.0 (p10 59.5 / p90 67.8) | 0.0 | 56.2 (p10 47.6 / p90 60.0、最大 143.1) | 476.0 (T-2766 の B 腕 4 走を含む) | 70.5 |

読み: L では controller が collection 通知の hook 内で同期 prewarm (≈ 30〜33 秒) を待つ間、配布が始まらない (D − H ≈ 30.5)。E では prewarm thread が collection と並走し (CPU を奪い合うぶん解決は ≈ 55 秒に伸びる — 候補説明)、worker は collection 完了後に memo 公開まで待つ (H に待ちを含む)。**機序からの予測: shard-0 の配布開始が ≈ 27 秒早まる (86.3 − 60.0)。** D − H は解決の純所要ではなく、配布時刻・純 collection・CPU 競合は追加計装なしでは分離できない (段 3 相談 A1)。E の標本は適合判定前の直近 N 件 (段 6 レビュー B7)。

### 2b. 分散と検出力

- 同一 tip・同夜・隣接走の W_max の分散 (T-2766): A 腕 sd 13.0 (n=3)、B 腕 sd 10.8 (n=4)、**実対差の SD 22.1 秒 (n=3)**。対差の SD σ_d は 17〜25 秒と見た (対内相関は未測定)。
- 判定規則そのもの (Wilcoxon 符号順位 exact 片側 p ≤ 0.05 ∧ 標本中央値 ≥ 15 秒) の検出力 (MC、`power_rule.py`、R=4000、`verbatim/power_rule-output.txt`): 正規誤差 δ=27 / σ_d=22 で **6 対 0.76、8 対 0.85、10 対 0.91**; δ=27 / σ_d=25 で 6 対 0.66、8 対 0.78; δ=20 / σ_d=22 で 8 対 0.59; 正規成分 SD σ + 両腕独立の遅延 (各 15 %、±30〜90 秒) の対称 model (σ は対差全体の SD ではない) では δ=27 / σ=22 で 8 対 0.50。偽陽性率 (δ=0) は全条件で ≤ 0.05。
- **結論 (事前): 必要走数は仮定 (δ、σ_d、裾) に依存し、現資料では確定できない。** 有効 8 対 (上限 20 走) を固定予算の探索測定として事前登録し、逐次検定・有意になるまでの追加はしない。事後 (§5): 観測 σ_d = 35.1 秒で 7 対の検出力は 0.47 (正規) / 0.34 (裾)。

## 3. 実装 (opt-out、Codex author、commit `7447c9a35`、impl branch `impl-t2700-early-memo-optout`)

| 面 | 変更 |
|---|---|
| `orchestrator/tests/conftest.py` | 定数 3 (`_EARLY_MEMO_OPT_OUT_ENV` / `_TOKEN` / `_ATTR`)、`_early_memo_opted_out()` (`_growth_holds_opted_in` と同型: 未設定 / 空 → False、exact token → True、他 → `UsageError`)、`_configure_early_memo_opt_out(config)` (True のときだけ config 属性)、`pytest_configure` の try 内で呼ぶ、`_early_memo_selected` の冒頭で属性を見て False (+24 行) |
| `tools/pegasus/dispatch_compute.py` | `TASKS["tests"].env_allowlist` に 1 key (+2 行) |
| `orchestrator/tests/test_real_repo_serialization.py` | `_early_memo_configure_probe` + test 4 本 (+86 行): L 正例 (実 `pytest_configure` → 属性 → 実 `pytest_configure_node` で早期 job が起動しない → 実 `pytest_xdist_node_collection_finished` の同期 barrier で両 cache が公開され reader が成功、stderr の hook = `xdist_node_collection_finished`)、E 負例 (未設定 / 空、外側環境から隔離、早期 job が起動し cache 公開)、fail-closed (他の非空値 → `UsageError`、両 nonce 復元)、属性経由の証明 (`pytest_configure` を通らない synthetic config では env があっても True = 既存 pin test が L 走で緑になる根拠) |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | exact pin +1 key、request 生成 + compute overlay の伝播 test (token / 空文字) (+36 行、fix1 で別 request.json に分けた) |

親の焦点走 (計算ノード、7 file: real_repo_serialization / pegasus_dispatch_compute / hold_inventory / pytest_collection_config / growth_test_holds_contract / run_tests_shards / run_tests_preflight): focus1 1041 passed / 2 failed (新 test の組み立て = stub scheduler の result.json と `_job_run` の排他生成の衝突、実装は無関係) → fix1 → **focus2 1043 passed / 1 skipped / 0 failed**。probe の隔離 (`_early_memo_cache_probe`) は `_repo_head` / cache path / `_resolve_now` / memo singleton / `_real_repo_locks` を差し替え、hook・prerequisites・barrier・cache writer / reader は実物 — 実 cache 公開・読取りの検査であり、実 repo lock / resolver の統合検査ではない (焦点再レビュー A5)。E 経路 (env 未設定 / 空) は patch の hunk 単位で現行と同一 (段 6 レビュー A)。

## 4. 変異 matrix (DW-M01、独立 clone `mutation-source` (D1009)、commit `7447c9a35`、runner = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_real_repo_serialization.py orchestrator/tests/test_pegasus_dispatch_compute.py -q -rf`、計算ノード)

probe 走 (全件 SURVIVED 期待で観測 node を集める、spec sha256 `98309905…`、`mutation/mutation-spec-probe.json` / `mutation-expected-nodes.json`) → final 走 (期待 node 登録、spec sha256 `fb4f3bb9…`、`mutation/mutation-spec-final.json` / `mutation-final-results.json`)。**baseline PASSED、6/6 KILLED、期待 node 完全一致 (MISMATCH 0)、wrapper rc=0。**

| # | 変異 (1 理由) | 位置 | kill した node (完全集合) |
|---|---|---|---|
| M1 | opt-out 判定を恒真 (未設定でも True) | `_early_memo_opted_out` の `return False` | `test_early_memo_opt_out_default_configure_starts_job[unset/empty]` (2) |
| M2 | 属性を置かない | `_configure_early_memo_opt_out` の `setattr` | `test_early_memo_opt_out_configure_keeps_synchronous_cache_barrier` (1) |
| M3 | `_early_memo_selected` の属性 check 削除 | 同関数冒頭 2 行 | 同上 (1) |
| M4 | allowlist の key 削除 | `dispatch_compute.py` `TASKS["tests"].env_allowlist` | `test_tests_task_env_allowlist_is_exact` + `test_early_memo_environment_request_and_child_overlay[token/empty]` (3) |
| M5 | 他の非空値で UsageError を出さず False | `_early_memo_opted_out` の `raise` | `test_early_memo_opt_out_invalid_configure_fails_closed` (1) |
| M6 | `pytest_configure` の呼出し削除 | `pytest_configure` の 1 行 | L 正例 + fail-closed (2) |

段 6 レビュー A の静的帰属と probe の観測 node は完全一致した。

## 5. 測定手順・走表・対表・判定

- **投入形:** 測定走は待ち手 `tools/dev_wave_wait.py acceptance` を使わず、wave worktree (HEAD = `7447c9a35`、clean) から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` (空 argv の受入形、Pegasus LOGIN の明示 shard mode → `_dispatch_result(shard_count=3)`) を直接投入した (D2164 決定 1)。E は `IZANAGI_T2700_EARLY_MEMO_OFF_V1=` (空文字を明示 export、request の overlay で compute 側の残留を消す)、L は `=t2700-early-memo-off`。`PYTHONDONTWRITEBYTECODE` は明示 unset。
- **launcher** `run-measure.sh` v2 (親、`probe-source.md`): job dir の flock を最初に取り (直列化)、門番 (他 session の `dev_wave_wait.py … acceptance` 待ち手 ≤ 2 かつ 1 分 load < 30、100〜140 秒周期で 2 回連続 + 0〜45 秒乱数 → 再判定) が開いてから HEAD == measurement tip と clean (`--untracked-files=all --ignore-submodules=none` = 0 行) を照合し、RUN dir を作って投入。終了後に clean / HEAD を再記録、session の 3 shard の `junit.xml` / `report.json` / `dispatch/{receipt,request,result}.json` / job の stdout・stderr を sha256 付きで複製 (file ごとに ok / missing-at-origin / copy-failed / hash-mismatch を `artifacts.txt`)、`run.json` v2 (`worktree_realpath`、warm の tip / rc を含む)。**門番の leaders 上限は投入前・結果を見る前に 1 → 2 へ緩めた** (09:09〜10:12 の 63 分、他 wave 2 本の受入待ち手がほぼ常時 2 本で開かず。`series/s1.log` 冒頭に記録)。
- **系列** `run-series.sh` v3 (親、事前登録): 走ごとに集計器 `--series-state` が次の走番号・slot・腕を返す。slot k の順序は k が奇数なら E,L、偶数なら L,E。slot 内のどちらかが無効 (単走検算・系列検算とも) なら同 slot を同順序で直ちに取り直す。有効 8 対 or 20 走で締切。投入前 abort (RUN dir なし) は番号を消費せず停止。
- **warm-up:** 測定前に collect-only 1 走 (`run-warm.sh`、`PYTHONDONTWRITEBYTECODE=`、login の admission が通り local で 51 秒、pyc 394 個、tip 7447c9a35 を記録) で共有 FS の `orchestrator/tests/__pycache__` を温めた。系列は warm の rc=0 と tip 一致を投入前条件にした。
- **集計:** `t2700_ab_analyze.py` (Codex author + fix2〜5、`probe-source.md`) — 走レベル (SHA・dirty・複製・hash・receipt の job 番号 / child_rc / outcome / request 引数 / request.json の sha256 束縛・junit 時刻 ±300 秒・env・witness・consumer) と系列レベル (selected digest の全走一致・時刻の非重複と単調・worktree 一致・slot 進行順) の検算、対統計、Wilcoxon exact、t、感度 MC、失敗集計、記述的対照。`--selftest` PASS。原本 `analysis.json` / `analysis.md` は job dir、本 dir の `analysis/analysis-compact.json` は射影 (`_projection` に原本 sha256 と落とした field)、`analysis/analysis-tables.md` は表部。
- **測定の外乱:** 同時刻に別 wave `dev-wave-t2802-floor-attempt-recovery` が同型の測定系列 (直接投入) を走らせ、他 wave の受入待ち手も 0〜3 本あった (門番は受入待ち手しか数えない)。対は隣接走なので両腕が似た外乱を受けるが、同一 allocation ではなく node も対内で異なる。

### 走表 (shard-0 = 最遅 shard、W = JUnit testsuite time、H = worker 記録の collection-finish 最大、D = 最初の test 開始、O = 最忙 worker の占有、F = W − O、rm = shard-0 の receipt memo 解決所要 (stderr)、時刻 JST、`runs/<NN>-<X>/`)

| 走 | 条件 | slot | 投入 → 完了 | shard-0 node | W_0 | H_0 | D_0 | O_0 | F_0 | W_1 | W_2 | witness (hook) | rm_0 | 他 leader / load1 | 有効 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | E | 1 | 10:14→10:35 | bnode016 | 386.3 | 60.0 | 60.0 | 315.3 | 71.0 | 244.2 | 206.1 | configure_node ×3 | 58.6 | 1 / 4.73 | 有効 (対 1) |
| 02 | L | 1 | 10:42→10:56 | bnode021 | 508.6 | 60.4 | 84.9 | 413.7 | 94.9 | 245.0 | 203.3 | xdist_node_collection_finished (shard-0 のみ) | 28.6 | 2 / 10.64 | 有効 (対 1) |
| 03 | L | 2 | 10:59→11:24 | bnode021 | 505.2 | 59.8 | 86.5 | 408.6 | 96.6 | 246.6 | 241.4 | 同上 | 30.5 | 1 / 4.27 | 有効 (対 2) |
| 04 | E | 2 | 11:27→11:37 | bnode035 | 481.9 | 59.8 | 59.8 | 412.0 | 69.8 | 243.5 | 201.5 | configure_node ×3 | 53.5 | 1 / 3.52 | 有効 (対 2) |
| 05 | E | 3 | 11:40→12:06 | bnode002 | 481.0 | 60.6 | 60.6 | 410.3 | 70.7 | 247.7 | 202.0 | configure_node ×3 | 54.2 | 1 / 1.31 | 有効 (対 3) |
| 06 | L | 3 | 12:11→12:32 | bnode004 | 503.0 | 58.3 | 101.3 | 388.2 | 114.8 | 247.1 | 200.7 | 同上 | 45.7 | 0 / 2.88 | 有効 (対 3) |
| 07 | L | 4 | 12:45→13:05 | bnode083 | 511.6 | 59.8 | 109.6 | 391.8 | 119.8 | 254.2 | 203.6 | 同上 | 51.8 | 2 / 13.16 | 有効 (対の相方 08 が無効 → 不採用) |
| 08 | E | 4 | 13:16→13:37 | bnode018 | (487.9) | (69.9) | (70.1) | (405.9) | — | — | — | configure_node ×3 | — | 0 / 9.88 | **無効 `red`** (括弧の値は複製 junit / report から親が読んだ参考値、集計器は対に使わない): `test_real_repo_writer_drains_overlapping_reader_stream[legacy]` 1 件 (25418 passed) |
| 09 | L | 4 | 13:39→14:01 | bnode021 | 533.9 | 59.4 | 96.7 | 427.1 | 106.8 | 245.4 | 207.2 | 同上 | 39.9 | 1 / 13.92 | 有効 (対 4、取り直し) |
| 10 | E | 4 | 14:03→14:12 | bnode105 | 494.5 | 59.6 | 59.6 | 424.4 | 70.0 | 244.7 | 203.4 | configure_node ×3 | 55.0 | 0 / 6.23 | 有効 (対 4) |
| 11 | E | 5 | 14:15→14:25 | bnode024 | 495.1 | 60.4 | 60.5 | 424.6 | 70.5 | 246.5 | 251.2 | configure_node ×3 | 54.0 | 1 / 12.47 | 有効 (対 5) |
| 12 | L | 5 | 14:28→14:49 | bnode019 | 536.9 | 59.3 | 93.2 | 431.5 | 105.4 | 240.3 | 203.6 | 同上 | 37.0 | 2 / 13.86 | 有効 (対 5) |
| 13 | L | 6 | 14:52→15:01 | bnode004 | 478.0 | 58.9 | 91.7 | 376.2 | 101.8 | 245.9 | 247.4 | 同上 | 35.4 | 2 / 8.23 | 有効 (相方 14 が無効 → 不採用) |
| 14 | E | 6 | 15:04→15:14 | — | — | — | — | — | — | — | — | — | — | 2 / 14.09 | **無効 `red`**: `test_s8b_floor_campaign.py::test_official_fresh_issues_certificate_and_binds_wall_ledger` 1 件 (`output/runs/.s1-current-provenance-*` の scandir race) |
| 15 | L | 6 | 15:21→15:31 | bnode011 | 517.9 | 59.3 | 94.7 | 413.1 | 104.7 | 246.6 | 202.5 | 同上 | 38.1 | 2 / 9.54 | 有効 (対 6、取り直し) |
| 16 | E | 6 | 15:41→15:56 | bnode016 | 484.4 | 60.0 | 60.0 | 413.8 | 70.5 | 248.6 | 202.7 | configure_node ×3 | 57.5 | 2 / 8.65 | 有効 (対 6) |
| 17 | E | 7 | 16:33→16:54 | — | — | — | — | — | — | — | — | — | — | 2 / 14.99 | **無効 `red`**: `test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy]` 1 件 (門番待ち 37 分の後の投入) |
| 18 | E | 7 | 16:56→17:18 | bnode007 | 484.5 | 60.1 | 60.1 | 414.4 | 70.1 | 247.8 | 204.7 | configure_node ×3 | 54.3 | 2 / 2.12 | 有効 (対 7、取り直し) |
| 19 | L | 7 | 17:21→17:42 | bnode003 | 513.6 | 60.0 | 90.3 | 412.8 | 100.8 | 246.3 | 200.8 | 同上 | 33.6 | 1 / 3.89 | 有効 (対 7) |
| 20 | L | 8 | 17:45→17:55 | bnode026 | 521.7 | 58.9 | 95.4 | 416.3 | 105.4 | 237.4 | 226.8 | 同上 | 38.4 | 1 / 4.39 | 有効 (slot 8 の 1 走目、上限 20 で締切 → 対に入らない) |

投入 → 完了は login 側の外側 wall (queue 待ちを含む。所要の正は各 shard の JUnit time)。赤 (failed / error) は有効 17 走で 0。08 / 14 / 17 の shard 別値は `runs/<NN>-E/` の複製 (junit / report) から読める (集計器は無効走の shard 指標を対に使わない)。

### 対表と判定

| 対 | slot / 順序 | 走 (E, L) | W_max(E) | W_max(L) | ΔW = L − E (秒) | r = ΔW / W_max(E) | ΔD_0 | ΔO_0 | Δtail_0 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 / E,L | 01, 02 | 386.3 | 508.6 | **+122.3** | 31.7 % | +24.9 | +98.4 | 0.0 |
| 2 | 2 / L,E | 04, 03 | 481.9 | 505.2 | **+23.3** | 4.8 % | +26.7 | −3.4 | 0.0 |
| 3 | 3 / E,L | 05, 06 | 481.0 | 503.0 | **+22.0** | 4.6 % | +40.7 | −22.1 | +0.3 |
| 4 | 4 / L,E (取り直し) | 10, 09 | 494.5 | 533.9 | **+39.4** | 8.0 % | +37.1 | +2.7 | 0.0 |
| 5 | 5 / E,L | 11, 12 | 495.1 | 536.9 | **+41.8** | 8.4 % | +32.8 | +6.9 | +0.3 |
| 6 | 6 / L,E (取り直し) | 16, 15 | 484.4 | 517.9 | **+33.5** | 6.9 % | +34.6 | −0.7 | 0.0 |
| 7 | 7 / E,L (取り直し) | 18, 19 | 484.5 | 513.6 | **+29.1** | 6.0 % | +30.2 | −1.6 | 0.0 |

- 対差の中央値 = +33.5 秒、対率の中央値 = 6.9 %、条件別中央値差 = med W_max(L) 513.6 − med W_max(E) 484.4 = +29.2 秒 (3 つは別量)。ΔD_0 の中央値 = +32.8 秒。
- 事前登録の判定: m = 7 (0 差なし)、Wilcoxon 符号順位 exact 片側 p (H1: ΔW > 0) = 1/128 = 0.0078 ≤ 0.05 ∧ 標本中央値 33.5 ≥ 15 秒 → **「成功走で早期起動が最遅 shard の wall を短縮 (探索閾値 15 秒以上)」**。両側 p = 0.0156。対応のある t = 3.35 (df 6、両側 5 % 臨界値 2.447)。σ_d = 35.1 秒。15 秒は便宜的な探索閾値 (機序予測 27 秒の約半分) であり母効果 ≥ 15 秒の証明ではない。片側は事前固定 (機序が改善方向を予測)。各単走差を D357 の「改善実績」には数えない。
- 対数: 有効 7 対、上限 20 走で締切 → **未達** (事前登録どおり達成対数で判定)。
- 隣接対は同 job / 同 allocation ではない (別々に 3 shard を dispatch した逐次の隣接対)。node は対内で異なる (対 3 の 05 bnode002 / 06 bnode004 等)。D104 決定 4 の「同一 allocation 内の paired 比較」を満たしたとは書かない。

### 記述的対照 (他 wave の待ち手経由の受入、10:14〜17:55 JST の窓、`analysis/analysis-compact.json` `descriptive_control`)

他 session 42 件 (すべて E 型 = `configure_node`、tip は wave ごとに違う) の shard-0: W 中央値 491.4 (353.8〜636.8)、D 中央値 60.8 (59.0〜94.5)。本 wave の E 7 走 (481.0〜495.1、01-E だけ 386.3) はこの分布の内側、L 7 走 (503.0〜536.9) は中央値より上だが分布の内側 (最大 636.8 は別 tip)。同等性の証明ではない。除外 1038 session (timeline 無し 949、report.json 無し 89) は集計器の窓・条件の外。

## 6. 失敗の集計と witness

- **腕別投入と失敗 (解析締切 = 20 走目、締切後の走 0):** E 10 走 = 成功 7 / `red` 3、L 10 走 = 成功 10。`treatment-failure` (`memo publication timeout` / 両 memo の fail-closed prefix / `publication-timeout`) は E / L とも 0。`infrastructure` (receipt 不発行・rc=16) 0、`artifact` 0、`unknown` 0。
- **E の `red` 3 件はいずれも既知の間欠赤:** `test_real_repo_writer_drains_overlapping_reader_stream[legacy]` (08、他 wave の session で 09-18 12:05 / 09-20 05:10 にも)、`test_official_fresh_issues_certificate_and_binds_wall_ledger` (14、`output/runs/.s1-current-provenance-*` の一時 dir の scandir race、過去 session 41 回)、`test_real_repo_upgrade_writer_drains_overlapping_reader_stream[legacy]` (17、08 と同族)。3 走とも他の 25418 件は緑で、W_0 は 08 で読める (H_0 69.9 / D_0 70.1 = E の形)。E に 3 / L に 0 は偶然でも起こる比率 (3 件の赤が 9 本の E 走に全部入る確率 ≈ 0.12) で、これ以上の主張はしない。
- **感度分析 (失敗 = 符号上の敗北):** 7 勝 3 敗、符号検定片側 p = 0.17 (対統計には混ぜない)。成功走の速度差 (§5) は「成功走に条件付き」の推定であり、失敗率込みの運用上の効果とは区別する。
- **witness の主張範囲:** stderr の `IZANAGI_MEMO_PREWARM_V1` 行は barrier の join 後に出る (起動時刻・成功単独の証拠ではない)。「E で早期起動が発火し、L で発火せず同期経路に入った」までを証言し、集計器は receipt の job 番号と file 名で対応づけた。E で解決が 53.5〜58.6 秒かかるのに配布が ≈ 60 秒で始まるのは、解決が worker の collection (H ≈ 60 秒) と並走して隠れるため — これが T-2616 の狙いどおり働いた、という読み。
- **検算の記録:** 全 20 走で `tip_sha == tip_sha_after == 7447c9a35`、dirty 0、`worktree_realpath` 同一、warm tip 一致、有効走の `selected` digest は shard ごとに全走同一、投入・完了時刻は非重複・単調、SHA256SUMS 再計算一致、receipt.request.sha256 == sha256(request.json)。

## 7. 限界と次の一手

限界:

- 有効 7 対で 8 対に未達。観測 σ_d = 35.1 秒は事前仮定 (17〜25) より大きく、対 1 (+122.3、最忙 worker の regime 差) が押し上げた。対 1 を除く 6 対は +22.0〜+41.8 (中央値 +31.3) で機序指標と同じ幅。
- 隣接対は同 allocation でなく node も対内で異なる。同時刻に別 wave の測定系列と受入が並走した。他 wave の記述的対照は tip が違う。
- 直接投入と待ち手経由の差 (lease / merge / receipt / launcher) は測定対象外。W_max は queue 待ち・開始ずれを含む受入総経過時間ではない。
- warm-up は bytecode cache だけ (page cache・fixture の warm は保証しない)。両腕で同じ warm 状態から開始した。
- 「配布開始の遅れ ≈ 30 秒が最遅 shard の wall にそのまま乗る」は本夜の regime (最忙 worker ≈ 410〜430 秒、collection ≈ 60 秒) での観測。collection が解決 (≈ 55 秒) より短い regime では E の待ちが現れ、差は縮む。
- E の `red` 3 件は既知の間欠であり本 wave の変更とは無関係だが、E 腕にだけ当たった理由は未同定 (偶然の範囲)。
- Wilcoxon exact は符号対称性・独立性を前提とし、交互順は位置効果を均衡させる工夫であって無作為割付ではない。

次の一手 (本 wave では起票のみ、実装しない):

- **早期起動 (T-2616) は現行 main の挙動であり、本測定は「止めると ≈ 30 秒遅くなる」を 7 対で示した。義務化 (opt-out の禁止) や launcher の自動検査は D1936 項 35 の範囲外で本 wave は行わない。** 現行を維持するだけでよく、追加実装は不要。
- 300 秒目標 (T-2273) の次の律速は最忙 worker の占有 (E で 410〜425 秒、W の 85 %) であり、T-2766 の pairing (最忙 worker を 100 秒級で短縮) と本 wave の早期起動は独立に効く (T-2766 の A 腕は早期起動あり)。採否は T-2766 の裁定パッケージ。
- E の解決が collection と並走して 55 秒に伸びる (L の同期解決は 30〜40 秒) 点は、collection が短くなる将来の regime で E の待ちとして現れうる。追加計装 (配布時刻・純 collection・CPU 競合の分離) は本 wave の scope 外。

## 8. 再現資料・成果物対応

- **実装:** commit `7447c9a35c769ff6b962d364ed5f9fd0c089c749` (branch `impl-t2700-early-memo-optout`、親 `ca8adec7b` ← main `b7f970dfa`)。差分 4 file (+148 行)。累積 patch の sha256 は `probe-source.md` (`codex/s5-author.patch` = job dir)。impl branch の所有者は本 wave、用途 = 再測定の起点。再訪 / 撤去は次の裁定時 (ユーザー指示なしに消さない)。
- **集計器・launcher・見積り script:** `probe-source.md` (逐語 + sha256)。再集計: `python3 t2700_ab_analyze.py --runs-root <job dir>/runs --measurement-tip 7447c9a35c769ff6b962d364ed5f9fd0c089c749 --consumer-nodes <job dir>/consumer-nodes.json --target-pairs 8 --max-runs 20 --other-sessions-root /work/1/SFC/tanab/.izanagi-acceptance-shards --out <dir>`。consumer 集合は `consumer-nodes.json` (conftest の `RECEIPT_MEMO_CONSUMER_NODES` 8 / `ORACLE_ENVIRONMENT_CONSUMER_NODES` 26、抽出元 sha256 付き)。
- **raw 成果物 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2700-prewarm-ab/`):** `runs/<NN>-<E|L>/{run.json, env.txt, artifacts.txt, chain.log, gate.log, child.log, session/{SHA256SUMS, shard-{0,1,2}/{junit.xml, report.json, dispatcher.log, dispatch/{receipt,request,result}.json, dispatch/izdw-shard-N.{e,o}<job>}, junit.xml, login-collection.log}}` (本 dir の `runs/` は run.json / env.txt / artifacts.txt / chain.log / gate.log / SHA256SUMS の写し)、`analysis/analysis.{json,md}` (原本、sha256 は `analysis/analysis-compact.json` の `_projection`)、`aborts/` (投入前停止の記録 = 門番 log)、`s1.log` / `s1.state.*.json` (系列)、`codex/` (prompt・log・artifact・patch)、`mutation-*` (spec・台帳・receipt・独立 clone)、`focus/` (焦点走・dogfood の log)、`history/`、`verbatim/`、`warm.*`。元 session (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/`) の path は各 `run.json` の `session_dir_origin`。
- **事前登録:** `s4-ruling.md` §事前登録 (段 4) + 系列規則 (`run-series.sh` v3 冒頭 = `probe-source.md`、焦点再レビュー後・測定前に固定) + 門番 leaders 上限の緩和 (投入前、`series/s1.log`)。
- **段構成と工数:** 軽量版 + 段 3 相談 1 本 (2 レンズ) + 段 6 レビュー 2 本 + 焦点再レビュー 1 本。codex 子 10 本 (consult 1、author 1、fix 5、review 2、focus 1、すべて gpt-6-astra medium)。計算ノード job = 焦点走 2 + 変異 14 (probe 7 + final 7) + 測定 20 走 × 3 shard。warm は login local。wave の所要 07:06〜(段 9 完了時刻は worklog)。

## 9. レビュー・裁定の逐語

- 段 3 相談 (2 レンズ 1 本、gpt-6-astra medium、07:43〜07:49): `verbatim/s3-consult.md` — must-fix 7 (A1 介入の範囲と H/D の意味、A2 検出力と判定規則の不一致、A3 exact・同順位・閾値、A4 E 固有失敗の選択バイアス、B1 configure 結線と M1 帰属、B2 E の unset と存在しない先行 test、B3 集計器の契約)、should 3 (A5、B4、B5)、nit 2 (A6、B6)。全件 real・採用 (`s4-ruling.md`)。
- 段 5 author (08:03〜08:17): `verbatim/s5-author.md` (sandbox で pytest 起動不能 → 親の焦点走)。fix1 (伝播 test の組み立て): `verbatim/s6-fix1.md`。
- 段 6 レビュー A (正しさ境界、08:34〜08:40): `verbatim/s6-reviewA.md` — must-fix 2 (A1 treatment-failure の検出先、A2 締切後の混入)、should 2 (A3 slot 進行順、A4 selftest 被覆)、nit 1 (A5 probe 隔離の説明)。E 不変・L 経路・env 全段・M1〜M6 帰属 = 支持。レビュー B (過剰・削除・手順・統計、08:34〜08:38): `verbatim/s6-reviewB.md` — must-fix 4 (B1 取り直し規則、B2 締切、B3 束縛検算、B4 複製失敗と不発行の区別)、should 3 (B5 裾 model の説明、B6 warm 前提、B7 履歴の scheduler/SHA)、nit 3 (B8〜B10)。全件 real・採用。
- fix2 (集計器・履歴、08:42〜08:52): `verbatim/s6-fix2.md`。焦点再レビュー (08:54〜08:58): `verbatim/s6-focus.md` — closed 10 / partial 1 (B3 request 引数) / regressed 1 (B1 系列制御) / docs 3 → GO 不可 → fix3 (`--series-state`、request 引数必須化): `verbatim/s6-fix3.md` → 実物互換の残件 (receipt.request に repo_root が無い) → fix4 (`verbatim/s6-fix4.md`)。測定 01-E 後に集計器が run.json の `+0900` を拒否 (偽陰性) → 投入前に系列を止めて fix5 (`verbatim/s6-fix5.md`、`±HHMM` 受理) → 01-E は有効に再判定され 02-L から再開。
- 親の裁定 (段 6): 焦点再レビューの docs 行き 3 件は本 README に反映 (§3 probe 隔離の説明、§2b 裾 model = 両腕独立の対称 model、§6 witness の主張範囲)。`s4-ruling.md` の「L 側 15 % の裾」は誤りで、末尾の訂正注記を参照。
- 変異 probe の観測 node と final の期待 node は完全一致 (§4)。
