# 段 1 brief — [T-1974] 段階 P: 計算ノード側の子の実行 bytes を tested main の blob へ束縛する

## scope

受入全走が計算ノードで走らせる子 (`tools/run_tests.py`) の**実行 bytes** を tested main の blob へ
束縛する機構を入れる。**実行器 `tools/run_tests.py` は 1 byte も編集しない。**
編集面は `tools/acceptance_launcher.py`、`tools/pegasus/dispatch_compute.py`、および両者のテスト
(`orchestrator/tests/test_acceptance_launcher.py` ほか) だけ。

## 確定済みユーザー裁定

- **D1151** (main の `docs/decisions.md:38624`、着地済み): 実行器束縛 (D838) は外さない。
  実行器を変更せず main blob の材料を運ぶ変更を先に着地させ、その後で再裁定する。
  `tools/run_tests.py` の既定分割数 3 への変更も再裁定まで保留。
- D838: 受入の実行器を tested main の blob へ束縛する。D440: 判定器は main 束縛・待ち手は tip 束縛。
- D397: dispatch の `env_allowlist` へ key を足すときは consumer 実在・値の意味論・単調性を実測記録。
- D859: 被検査コードが書けない結果チャネルを設計する。
- 設計 6 点 (i)〜(vi) は `docs/archive/worklog-phase3-0827-1028.md` の [T-1974] 項が正本。

## 不変条件 (破ったら停止)

1. `tools/run_tests.py` の bytes 不変。編集すると D838 の等値要求で自分の受入が通らない。
2. 受領証 (`dev-wave-acceptance-receipt/v5`) の field 集合・意味を変えない。land は main 側 bytes で
   走り `_ENV_PROJECTION_FIELDS` を exact set で照合するため、field 追加は自分の land を落とす。
3. P 自身の受入は main の**旧** launcher が実行するので申告を要求しない。P の受入は落ちない。
4. dispatcher は launcher 所有の manifest がある走行にだけ束縛を適用する。恒久的な暗黙 fallback を
   作らない (manifest 無し = 現行挙動)。
5. hash する bytes と子の stdin へ渡す bytes は同一 buffer とし、期待 digest を子へ転記しない。
6. `tools/acceptance_shards.py` は編集しない (稼働 wave `dev-wave-t1886-realrepo-closure-split` が
   tip で +67 行を所有)。

## 成果物の形

コード 2 file + テスト、insight `output/insights/2026-08-27_t1974-runner-main-blob-binding/`、
worklog / decisions の spool fragment、変異 matrix、受入受領証、land。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 申告 channel は launcher が所有する repo 外 directory と session nonce。dispatcher が
  shard ごとに 1 file を書き、launcher が `0..K-1` の完全一致を要求する。
  *成果物影響:* 実装しないと段階 Q が発効させる対象が無く、受入受領証の実行 digest が
  計算ノード子の実体を指さないまま残る。
- **(P2)** 材料は launcher の `os.environ` → (実行器は無変更で継承) → login 側 dispatcher が
  `os.environ` から読み、request payload の専用 field へ載せる。計算ノード側の `env_allowlist` は
  `requested_env` にしか掛からないので D397 の key 追加は不要。
  *成果物影響:* この経路が無いと実行器の編集が要り、D1151 に抵触して着地できない。
- **(P3)** K (shard 数) は launcher が所有する exact 値。dispatcher の自己申告を authority にしない。
  *成果物影響:* K を子側から取ると、shard を 1 本落とした走行が緑で通り受領証が偽になる。
- **(P4)** 束縛の適用対象は `TASKS["tests"]` の受入 shard 子だけ。provenance / mutation / generic は対象外。
  *成果物影響:* 対象を広げると変異 harness と provenance 監査の dispatch が同時に落ち、wave が止まる。
- **(P5)** 残余として、dispatcher 自身は tip 側 bytes なので、実行器と dispatcher の**両方**を編集する
  wave は捕まらない。母集団は実測で 24 件中 6 件 (25.0%)。閉じるのは段階 R。
  *成果物影響:* 残余を明記しないと、束縛が実際より強いという誤った保証を台帳へ書くことになる。
- **(P6)** dispatch しない authoritative 受入は launcher 側で fail-closed (段階 R まで)。
  *成果物影響:* fail-open にすると bounded local 経路が束縛を素通りし、機構が恒真になる。

## 環境

Pegasus LOGIN で親が編成、テスト実走は計算ノードへ dispatch。login node の pytest は hook が拒否する。
2026-08-27 10:00 JST 実測: `site=PEGASUS_LOGIN`、`dispatch_possible=True` (queue `gen_S`、待ち 0・実行 39)。

## 変更面の実アンカー

| # | アンカー | 実測した内容 |
|---|---|---|
| 1 | `tools/acceptance_launcher.py:20` | `_RUNNER_PATH = "tools/run_tests.py"` |
| 2 | `tools/acceptance_launcher.py:51-62` | `_RUNNER_BOOTSTRAP` (stdin の bytes を `exec`、`__file__` は argv[1]) |
| 3 | `tools/acceptance_launcher.py:436-449` | main/tip blob 等値検査、実行後の main blob 再取得と照合 |
| 4 | `tools/acceptance_launcher.py:199-232` | `_run_blob` は `env=` を渡さない → 子は launcher の環境を継承 |
| 5 | `tools/acceptance_launcher.py:36-42` | `_ENV_PROJECTION_FIELDS` は 4 key の exact set |
| 6 | `tools/pegasus/dispatch_compute.py:113-130` | `TASKS["tests"]`: `child_script=("tools","run_tests.py")`、`env_mode="inherit"`、`env_allowlist` 7 key |
| 7 | `tools/pegasus/dispatch_compute.py:1009-1021` | `child_argv = [sys.executable, repo_root/tools/run_tests.py, *argv]` を `stdin=DEVNULL` で起動 |
| 8 | `tools/pegasus/dispatch_compute.py:988-993` | `unexpected_env` は `requested_env` の key だけを allowlist と照合 |
| 9 | `tools/run_tests.py:1340` | `dispatch_kwargs["intent_shard_index"] = intent_shard_index` (shard index は既に dispatch へ渡る) |
| 10 | `tools/dev_wave_land.py:1021-1052` | launcher は tested main の blob にだけ束縛。tip 等値要求は無い |
| 11 | `tools/dev_wave_land.py:960-961` | 受領証 argv は `["python3","tools/run_tests.py"]` に exact pin |

## 並列分割方針

編集 file が 2 本で相互依存 (manifest の生産者と消費者) が強いため、段 5 は 1 単位で投入する。
段 3 の敵対相談と段 6 のレビューは 2 本並列。
