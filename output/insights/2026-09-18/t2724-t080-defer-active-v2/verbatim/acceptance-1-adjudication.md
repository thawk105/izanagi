# 受入1の判定（2026-09-18 22:49 JST）

- d899c86aaで25153 passed / 69 skipped / 12 setup errors。child rc1、waiter rc70、成功receiptなし。
- 原因は全12node共通のmodule fixture `_clean_detached_source_snapshot_template` が呼ぶ
  `probe._repo_snapshot(REPO_ROOT)`。Gitの未追跡走査 `ls-files --others --exclude-standard -z` が30秒を超えた。
  原traceはshard0 dispatcher.logとdispatch/shard-0/izdw-shard-0.o6425。
- 当該fixture/testとtools/pegasus/probes/t1259_qsub_env_delivery_probe.pyに今回の差分はない。
  T-080の委譲や新接続fixtureを呼ぶ前ではなく、別moduleのsetup自身で停止している。
  署名だけでなく実argv・setup stack・変更差分を照合した。I/O遅延の個別要因までは分離していない。
- DW-O18により同tipの同fileを正規runnerで1回だけ単独再走する。非再現なら受入を1回再走する。
  test/timeout/除外/hold登録を変更せず、再赤時は同tipでさらに回さない。
- 再走判断と赤の事実をworklog fragmentへ追記する。検査を緩める実装修正は今回行わない。

## 単独走の終端

- 同tipの正規runner単独走もrc1、51 setup errors。同じrootの同じGit argvが30秒でTimeoutExpired。
- 単独走で非再現を示せなかったため、受入2は投入しない。DW-O18の同tip再走上限に従って正式停止。
- 別件T-2790（D2148項12）のfixture待機上限の設計・検証が既存の後続手番。本waveでtimeout/hold/除外を変更しない。
- main land未実施のため、今回対象の清掃は保全へ切り替える。全成果と生logを保存する。
