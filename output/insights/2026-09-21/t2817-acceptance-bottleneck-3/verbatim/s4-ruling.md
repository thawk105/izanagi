# 段 4 裁定 — [T-2817] 受入律速の再同定 (第 3 回) と collection 差の分解診断 (2026-09-21 01:2x JST、結果を見る前に固定)

段 3 相談 (`codex/s3-consult-out.md`、gpt-6-astra / medium / read-only、所見 11 = 高 6・中 5、判定「修正後 GO」) を親が裁定した。裁定 inbox (`rulings-inbox/2026-09-21-rulings-full27-verdicts.md`、00:5x JST) に本 wave の対象 T (T-2817 / T-2273 / T-2444 / T-2495 / T-2560) の更新は無い。

## §1 所見の裁定 (real / refuted、採否、scope)

| # | 判定 | 採否 | 反映 |
|---|---|---|---|
| 1 scheduler no-op は collection 一致検査を消す | real | 採用 | probe scheduler は実 `LoadGroupScheduling` instance の `schedule` だけを差し替え、差し替え先は元の前段 (`collection_is_completed` の assert → 再呼出しなら return → `_check_nodes_have_same_collection()` と失敗通知 → `self.collection` 設定) をそのまま行い、workqueue の構築と初期配布だけを省く。不一致は probe 出力に `collection_mismatch=true` で残す |
| 2 S1 でも controller の同期 memo prewarm が発火する | real | 採用 | S1 の名を「xdist + 通常 memo prewarm (controller 同期)」に改める。controller 側 `pytest_xdist_node_collection_finished` の入口/出口を node ごとに計時し、S2 − S1 を「plugin + memo の同期→早期並走への切替」の複合差として読む (§4) |
| 3 計時区間が段差と対応しない | real | 採用 | 列を分ける: process 起点 (`/usr/bin/time` の wall と probe module import 時刻)、`pytest_configure` 時刻、`pytest_sessionstart` 時刻、JUnit 起点 (`--junitxml` を全 xdist 段に付け junit の timestamp を読む)、worker の collection 入口/出口 (`pytest_collection` wrapper)、最後の `pytest_itemcollected`、`pytest_collection_finish` 入口/出口、shard plugin の `collection_finished_epoch_s` (S2/S3、`config._izanagi_acceptance_shard_state` から workeroutput へ写す)。並び替え費用は modifyitems wrapper で独立同定せず「最後の itemcollected → collection_finish 入口」の区間 (hold 処理・plugin・並び替えを含む複合) として記録 |
| 4 S2/S3 の出力先共用で反復が失敗する | real | 採用 | 走ごとに `job-out/<cell>/` を固有にし、その下に `session/shard-0/`、`junit.xml`、`probe.json`、`out`/`err`/`time`、`tmp/` (TMPDIR) を置く |
| 5 (P1) 全面省略は依頼 (1) を満たさない | real | 採用 ((c) 条件付き) | Job B = 現行 tip の A 条件 replica 1 走 (shard-0 相当、`-n 48 --dist loadgroup` + shard plugin + 観測 plugin) を別 node で。probe は T-2786 版を出発点に A 条件専用の最小版へ削り、KEYS/TIP の固定を外して key は観測値として記録。job 内に smoke 段 (narrowed、`-n 2`) を置き、smoke が spans を出せなければ A 走を投入せず `incomplete.json` を書く。中央値・改善効果は主張しない。旧 `7975385b5` の値はその tip の命題として保持 |
| 6 offline 並びから O_max の変化は導けない | real | 採用 | N3 は仮説のまま。「rank 差は collection 順の近似差」は撤回し、cardinality 順・partner 挿入・real-repo suffix・動的配布を再現していないと書く。効果量は §5 の固定所要 list-scheduling model の値に限定し、model 値と明記 (D357: 実 wall の予測値ではない) |
| 7 加法分解と相方の混同 | real | 採用 | 各走で `F = pre + post + 残差` を閉じてから要約。`P_L = O_L − L` (L の worker の相方、21/21 で 0.0) と `O_max − L` (各走の差の中央値 62.7、中央値の差 93.5) を区別。`worker_occupancy.duration_s` は report duration の和と書く。`pre − receipt_memo_s` は shard-0 21 件で中央値 4.6 秒、「重複実行を含む差」であり独立成分・削減可能量と呼ばない |
| 8 pairing 群 ≠ 既定 on 後の同条件群 | real | 採用 | 母集団を「保存資料中の pairing property あり 21 session (T-2766 opt-in 期間の B 走を含む、tip 非同一、投入元未照合)」と限定。最大占有 worker の構成は全称を避け実際の node 列で示す |
| 9 `--maxfail=1` は「他の効果なし」が強すぎる | real | 採用 | S1/S2 の lever を `--no-loadscope-reorder` に置換 (成功 collection の比較に限定)。S3 − S2 は「ledger 読込 + workerinput 配送 + worker 側検証 + 並び替え + pairing property 付与 + その並走影響」の複合差と書く |
| 10 比較単位と反復の限界 | real | 採用 | S0 に共通起点 → 全 process の collection 終了 (cohort) 指標を追加し process median は参照列に残す。worker ごとの入口/出口を保持し `max(出口) − max(入口)` と各 worker の待ちを区別。順序反転 2 走は記述的反復に限定 (外乱除去の証明に使わない) |
| 11 (P4) の読取り専用条件と同 checkout 参照 | real | 採用 | `IZANAGI_TASK_RUN_SIDECAR` unset、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、TMPDIR / JUnit / log を走別に固定。pyc の温めは `python3 tools/run_tests.py orchestrator/tests --collect-only -q -p no:cacheprovider` (login、T-2710 job 6 の形)。参照受入は Job A/B と**同 SHA** で README commit の前に 1 走投入し、README 後の最終受入 (land 用) は別 SHA の観測として併記 |

refuted 0。scope 外の real 所見 0 (終了後 10.0 秒は観測として記録、原因追跡の追加走はしない。ledger refresh・memo prewarm 短縮・conftest 改変は行わない)。

## §2 (P1)〜(P4) の確定

- (P1) → (c)。Job B を追加 (§3)。L の内訳 (base 構築 / verify / copy) と最大占有 worker の実行列 (active_v2 系 key の base 構築を含む) を Job B の A 条件 1 走で取り、旧式 (entry 1676) へ無理に足さず別々に報告。
- (P2) → 所見 1〜4・9・10 の修正版 (§3 Job A)。
- (P3) → 所見 6・7 の修正版 (§5)。
- (P4) → 所見 11 の修正版。Job A と Job B は独立 (共有する path・lock・観測対象なし: Job A は wave 木を読むだけ、Job B は replica session を受入共有 root に作る) なので runbook §7.5 に従い**別 node へ並行投入**。参照受入は両 job 終了後。

## §3 計測行列 v2

### Job A (計算ノード 1 node、`dispatch_compute.py --task generic`、walltime 00:40:00、cwd = wave 木)

共通: `PYTHONDONTWRITEBYTECODE=1`、`IZANAGI_TASK_RUN_AUTO_RECORD=0`、`unset PYTEST_ADDOPTS PYTEST_XDIST_TESTRUNUID IZANAGI_TASK_RUN_SIDECAR PYTHONPYCACHEPREFIX IZANAGI_TEST_RUNNER_EXCLUSIONS_V1 IZANAGI_ACCEPTANCE_SHARDS`、`TMPDIR=<cell>/tmp` (node-local `/scr` 配下、末尾で job-out へ回収)、`PYTHONPATH=<probe dir>` (probe plugin の import 用)、`-p no:cacheprovider`。python は `python3.10`。pyc は投入前に login で温めた wave 木の `__pycache__` を読む (R 腕なし)。

| cell | 形 | 期待 rc |
|---|---|---|
| warm | 1 process `python3.10 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider` (page cache の温め、参照列) | 0 |
| S0-{a,b} | 48 process 同時 `--collect-only -q` (T-2243 L 腕の形)。共通起点 `cohort_start` と各 process の start/end epoch | 0 |
| S1-{a,b} | `python3.10 -m pytest <abs>/orchestrator/tests -n 48 --dist loadgroup --no-loadscope-reorder --junitxml=<cell>/junit.xml -p t2817_probe_plugin -p no:cacheprovider -q` (shard plugin なし、通常 memo prewarm は controller 同期で発火) | 0 (collection 不一致なら非 0、probe 出力に記録) |
| S2-{a,b} | S1 + `-p tools.acceptance_shards` + env `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1={"session_root":"<cell>/session","shard_count":3,"shard_index":0}` (`<cell>/session/shard-0/` を事前作成) | 0 か shard plugin の sessionfinish 起因の非 0 (probe.json は testnodedown ごとに書き、sessionfinish の失敗に依存しない) |
| S3-{a,b} | S2 から `--no-loadscope-reorder` を外す (ledger 読込・配送・並び替え・pairing 有り = 受入 shard の argv 形) | 同上 |

順序: warm, S0-a, S1-a, S2-a, S3-a, S3-b, S2-b, S1-b, S0-b。各 cell 前後に単独性 (`others=`、`stale_pytest=`)、loadavg、MemAvailable、Lustre client stats (可読なら)。`IZANAGI_MEMO_PREWARM_V1` と `IZANAGI_EFFECTIVE_SCHEDULER_V1` の行は stdout/stderr から集計器が拾う。

probe plugin (`t2817_probe_plugin.py`) の計時点は §1 所見 3 のとおり。controller 側は `pytest_sessionstart`、`pytest_configure_node` (node ごと)、`pytest_xdist_node_collection_finished` の入口/出口 (node ごと、ids 件数)、scheduler 差し替え関数内の「全 node 登録完了」時刻と一致検査結果、`triggershutdown` 相当 (最初の `pytest_testnodedown`)、`pytest_sessionfinish`。worker 側の値は `config.workeroutput` へ、controller は `pytest_testnodedown` で回収し `probe.json` を都度書く。

### Job B (計算ノード 1 node、generic、walltime 00:50:00、Job A と並行)

1. smoke: `python3.10 tools/run_tests.py orchestrator/tests/test_s8b_oracle_driver.py -k "shared_base" -n 2 --dist loadgroup -p t2817_replica_plugin -p no:cacheprovider` 相当 (narrowed。観測 plugin が build/copy/git/issue/verify の span を ≥ 1 件出すことだけを確認。出なければ A 走を投入せず終了)。
2. A 条件 1 走: T-2786 runner の A 条件の形 (`run_tests.py orchestrator/tests -n 48 --dist loadgroup --junitxml=<session>/shard-0/junit.xml -p tools.acceptance_shards -p no:cacheprovider -p t2817_replica_plugin`、SPEC env = shard 0/3、session は `acceptance_shards.create_session(repo, 3)`)。replica session の id を `job-out/` に記録し、親の受入成果物の読み取りから除外する。
3. 解析: key ごとの build (copy / git / issue) span、verify span、copy→test span、L の node の timeline、最大占有 worker の item timeline、builder の worker。T-2786 の成分名を保つが、5 要素 key は観測値として記録する。

### 参照受入 (両 job 終了後、同 SHA)

`tools/dev_wave_wait.py acceptance` で 1 走 (3 shard)。shard-0 の `pre` / W / O_max / L / P_L / F / memo / 終了後を Job A の S3、Job B の A 走と併記する。README commit 後の最終受入 (land 用) は別 SHA の観測として追記のみ。

## §4 読み方 v2 (結果を見る前に固定)

- Job A 各 cell: `pre_junit = max_w(cf_exit) − junit_timestamp` (受入の `pre` と同定義)、`pre_entry = max_w(cf_entry) − junit_timestamp`、`wait_w = cf_exit − cf_entry` (worker ごと、median / max)、`collect_w = last_itemcollected − collection_entry`、`modify_w = cf_entry − last_itemcollected` (複合)、`wall_proc` (`/usr/bin/time`)、controller の `t_all_collected − t_sessionstart`、memo 行、rc。S0: `cohort_wall = max(end) − cohort_start`、process wall median (参照)。
- 段差 (同 half 内の対比較、a/b の 2 値と平均): `Δ10 = pre_junit(S1) − cohort_wall(S0)` = 「xdist 起動 + 48 worker 同時 collection + controller 通知」の差 (xdist の純増と呼ばない); `Δ21 = pre_junit(S2) − pre_junit(S1)` = 「shard plugin + memo の同期→早期並走への切替 (worker 待ち)」の複合差、`wait_w` を併記; `Δ32 = pre_junit(S3) − pre_junit(S2)` = 「ledger 読込・配送・検証・並び替え・property 付与」の複合差。`wall_proc` の段差は別列 (controller の configure 段の費用を含む)。
- 受入 `pre` との整合: 参照受入 shard-0 の `pre` と S3 の `pre_junit` の差が 10 秒以内 (便宜的閾値) なら「S3 は受入 `pre` を同 SHA・同 node 条件で再現した」と書き、段差を受入 `pre` の内訳の**候補**として提示する。10 秒超なら条件差 (node、同時 3 shard、session 生成、dispatcher 経路) として差を記録し、内訳の候補とは呼ばない。どちらでも削減可能量は書かない。
- Job B: 成分は T-2786 §4 と同じ名 (copy / git / issue / verify / copy→test / slot 待ちは無し)。L の node と最大占有 worker の item 列を timeline で示す。値は「現行 tip `<SHA>` の 1 走の観測」であり中央値でない。T-2786 の値との差は条件差 (tip、key 集合、pairing、node) を列挙して併記し、旧値を無効化しない (規律 7)。
- 前提実測 (21 session) の要約は所見 7・8 の限定に従って書き直す。

## §5 効果量の見込みの書き方 (実装しない、D1936 項 35)

- ledger 未収載 (N3): author の `t2817_ledger_model.py` で固定所要 list-scheduling model を出す。規則: 48 worker、unit = loadgroup scope、順序は conftest と同じ (既知 cost 降順 → 上位 48 → 次の 48 は最小 cost → 残り cost 降順、未収載は既知の 96 番目)、所要 = 21 session shard-0 の junit の node 別中央値の unit 和 (無い node は ledger 値、それも無ければ既定)、配布 = 先頭から空いた worker へ (list scheduling)、共有 base の相互作用なし。出力 = (a) 現行 ledger のまま、(b) 未収載 8 node に実測中央値を与えた ledger、の 2 つの model O_max と最大 worker の item 列。**model 値であり実 wall の予測ではない**、D2107 の refresh 入力でも採用案でもない、と併記。
- memo prewarm (N4): D2185 で現行維持が裁定済み。短縮策は提示せず、同 job で確認した値 (S2/S3 の `wait_w` と memo 行) だけ書く。
- 終了後 10.0 秒: 観測のみ (候補列挙は相談の「見つからなかったこと」を引用)。
- T-2243 §5 (a)(b)(c)(e) は再掲せず参照。

## §6 変異・検査

- 実装面差分ゼロ (probe は job dir、repo へ land しない) → 変異 matrix 免除 (DW-S04)。代わりに author は集計器と model script の合成入力での正例・負例 (各 label / 各 model 規則) を報告に貼る。
- 受入全走は免除せず: 参照受入 1 走 (同 SHA) + 最終受入 1 走 (land 用)。
- 親の login 生死確認: Job A probe plugin を narrowed 対象 (`orchestrator/tests/test_hooks.py` 等 1 file) で `-n 2` に載せ、scheduler 差し替え・計時・workeroutput 往復・probe.json 書出しが通ることを見る (run_tests.py 経由、login local で走る場合のみ。dispatch されるなら計算ノードでの smoke に任せる)。Job B は job 内 smoke 段で代替。

## §7 段 5 の分割

Codex author 2 本並列 (workspace-write、別 worktree、所有 path 素集合):
- author-A (`author-t2817-probe-a`): `tools/t2817_collection_stage_probe.sh`、`tools/t2817_probe_plugin.py`、`tools/t2817_collection_stage_aggregate.py`、`tools/t2817_ledger_model.py`。
- author-B (`author-t2817-probe-b`): `tools/t2817_replica_runner.py`、`tools/t2817_replica_plugin.py`、`tools/t2817_replica_analyze.py`。
親は起動器の終端 commit 後に 7 file を `W/probe/` へ複製して走らせ、repo には逐語 `.txt` だけを置く。
