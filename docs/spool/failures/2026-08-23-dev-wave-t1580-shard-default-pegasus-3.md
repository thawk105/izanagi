---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-t1580-shard-default-pegasus
seq: 3
---

## 新規

### {{F:shard-dispatch-marker-lost}}. 子 process の出力を退避した機構が、別 tool の「外側ログに marker がちょうど 1 本」という再試行契約を静かに壊していた [ドリフト] [テスト代表性]

- 事象: 受入全走の shard 分割 (D710) は、各 shard の dispatcher の stdout / stderr を
  `shard-N/dispatcher.log` へ退避する。この結果、`tools/pegasus/dispatch_compute.py` が出す
  `IZANAGI_DISPATCH_OUTCOME_V1` marker が外側の受入ログに 1 本も現れなくなった。
  消費側の `tools/dev_wave_wait.py` の `_retry_evidence_reason()` は外側ログ中の marker を数え、
  0 本なら `dispatch-attestation-missing` を返して**再試行しない**。よって分割走では、
  現行の単一走が持っていた「queue 待ちタイムアウト + pytest child 未起動なら 1 回だけ自動再試行」
  という回復が失われていた。分割は既定無効の opt-in だったため、この破れは発火しないまま残った。
- 根本原因: producer 側が自分の出力先を変えたとき、その出力を前提にしている**別 tool の受理条件**を
  照合しなかった。分割機構のテストは分割の内側 (割付け・併合・6 段 gate) を厚く検査していたが、
  「外側ログの marker 本数」という機構の外にある契約は検査対象に入っていなかった。
  D710 自身が「receipt は shard の完全性を証明しない」と限界を書いていたが、
  待ち手の再試行契約が同時に壊れることは書かれていなかった。
- 検出: 既定有効化 wave の段 3 敵対相談 (レンズ B) が静的に構成し、親が消費側コードの
  `_retry_evidence_reason()` と marker producer を一次資料で照合して確認した。
  本番での発火実績はない (opt-in のまま使われなかったため)。
- 恒久対応: {{D:aggregate-no-verdict-attestation}} — 全 shard が「未起動かつ queue-wait-timeout」を
  証明できるときだけ、外側 stderr へ集約 marker を 1 本出す。親が保持する `child_started == True` が
  1 件でもあれば出さない。`orchestrator/tests/test_run_tests_shards.py` の
  `test_aggregate_no_verdict_attestation_*` と `test_parallel_*_attestation*` が、
  消費側述語 (key 集合・型・`reason` の許容集合・marker 本数・行末形式) を全部照合する。
- 再発検知: 変異 M7 (起動済み証拠があっても放出する) と M8 (恒常的に不発火にする) が
  それぞれ 2 node / 7 node を KILL する。**子 process の出力を退避する機構を足すときは、
  その出力を数えている consumer の受理条件を先に列挙する。**

### {{F:acceptance-isolated-import}}. 受入 launcher の isolated mode を前提にしない module 冒頭 import が、既定化した瞬間にテスト 0 件で受入を落とした [ドリフト] [テスト代表性]

- 事象: 受入 shard 分割を既定有効にした最初の受入全走が、テストを 1 件も走らせずに
  `ModuleNotFoundError` で落ちた (rc=70、`classification=acceptance-command`、
  `raw_child_rc=1`)。落ちたのは `tools/acceptance_shards.py` の module 冒頭 import である。
- 根本原因: 受入 launcher (`tools/acceptance_launcher.py` の `_run_blob`) は runner blob を
  **`python3 -I` (isolated mode = `-E` + `-s`)** で起動するため、user site-packages が無効になる。
  当該 module は「login 側の分割 orchestration」と「計算ノードの test process 内 plugin」の
  2 役を持ち、前者は user site の依存を要求してはならないのに、module 冒頭で無条件に import して
  いた。分割が opt-in だった間はこの経路が受入 launcher 配下で踏まれず、欠陥は発火しなかった。
- 検出: 既定化 wave の受入全走 1 回目。静的レビュー 2 本と焦点走 (172 node) は
  いずれもこれを検出できていない — 焦点走は isolated mode で走らないためである。
- 恒久対応: 冒頭 import を失敗許容にし、不在時は hook decorator を等価な no-op へ倒す
  ({{D:shard-default-on-pegasus}} の実装)。回帰テストは source 文字列検査ではなく挙動で pin し、
  isolated mode の子 process で当該 module を import して rc=0 を観測する
  (`orchestrator/tests/test_run_tests_shards.py`)。
- 再発検知: 同テスト。**受入 launcher 配下で初めて踏まれる経路を既定にするときは、
  isolated mode で import graph 全体が解決できるかを先に実測する。**
  焦点走の緑は受入 launcher 配下の緑を含意しない。
