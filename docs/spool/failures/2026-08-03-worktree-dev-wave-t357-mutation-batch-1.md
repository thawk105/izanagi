---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: worktree-dev-wave-t357-mutation-batch
seq: 1
---

## 新規

### {{F:bundle-launcher-env-normalization}}. 計算ノードへの手書き投入器が sanctioned job script の環境正規化を写さず、無変異の全走が 19 件赤になった [誤前提] [テスト代表性]

- 事象: 変異 harness を計算ノードの 1 ジョブへ束ねる生死確認で、使い捨て投入器から走らせた
  **無変異 baseline の全走が 19 failed / 5244 passed** になった。失敗はすべて
  `orchestrator/tests/test_t126_pegasus_tools.py`。harness は「baseline が緑でない」で
  fail-closed 停止し、tree は clean のまま残った。
- 根本原因: 失敗は `TypeError: dataclass() got an unexpected keyword argument 'slots'`。
  `slots=True` は Python 3.10 以降の機能である。外側 pytest は `/usr/bin/python3.10` (3.10.12) で
  走っていたが、**テストが起動する入れ子 subprocess だけが 3.10 未満の python を掴んでいた**。
  計算ノードの既定 PATH は
  `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin` を `/usr/bin` より
  前に持つ。正規経路の `tools/pegasus/dispatch_compute.py` の `_job_script` は `command -v` で
  python3.10 を選び `export PATH="$(dirname "$selected"):$PATH"` を行うが、手書き投入器は
  この 1 行を写していなかった。
- 誘発要因: 「transport を変えるだけ」という認識。実際には投入器が内側 suite の実行環境を決めており、
  **環境正規化を写し漏らすと内側の suite が同じ suite でなくなる**。
- 恒久対応: 計算ノードで走らせる新経路は、`_job_script` の interpreter 選択・version/module probe・
  PATH 先頭化を**逐語で写すか、`_job_script` 自体を再利用する**。
  実体は {{D:mutation-transport-ruling-package}} の共通前提 5 (clean child env・stdin・cwd・子 rc)
  と、同 D の推奨 (a) = 正規 job script の再利用。
  手書き投入器を採る場合は、harness 起動直前に `command -v python3` / 選択 interpreter / `PATH` /
  hostname を job stdout へ出す診断を必須にする (本 wave の再走ではこれで原因を即断できた)。
- 再発検知: 計算ノードで走る新しい実行形を足すレビューでは、
  「`_job_script` にあってこの経路に無い環境操作は何か」を逐語で棚卸しさせる。
  内側で subprocess を起動するテストがある suite では、**外側 interpreter の version だけを見て
  等価と判断しない**。
- 近縁: F32 (変異 harness の復元・単一走行)、F41 (親のテスト cwd と偽赤)、
  F57 (全走でだけ落ちる失敗)
