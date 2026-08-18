---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1300-new-l2-section
seq: 3
---

## 新規

### {{F:background-bash-early-return}}. 背景 Bash と待ち手が約 10 分で空返りし、生きている子を完了扱いにしかけた [誤前提] [セッション死・救出]

- 事象: 本 wave の session では、背景で走らせた `tools/dev_wave_wait.py producer` が
  出力 0 bytes・rc=0 で早期に終了する事象を 3 回観測した。いずれも producer は生存しており
  (`ps` の経過時間で確認)、成果物も `.done` も存在しなかった。同じ形で、背景に投げた
  焦点テスト走行も約 10 分で打ち切られ、dispatch した計算ノード側の収集途中でログが途切れた。
- 根本原因: この session の背景 Bash が一定時間で終了させられる。待ち手はその子プロセスなので
  巻き添えで死ぬ。待ち手の rc=0 と「完了通知」だけを見ると、生きている producer を
  完了と誤認して次段へ進む。pid file 実在を確認してから張る作法
  (本 wave が収容した待ち手規則) を守っていても防げない。
- 恒久対応: 収容した `DW-C01` の待ち手規則に加え、実行系は codex 子と同じく runner と launcher を
  `.sh` へ外出しして `nohup setsid` で detach し、**死活判定は producer の pid と `.done` の
  mtime だけで行う**。待ち手の rc と harness の完了通知は判定に使わない。
  これは `docs/dev-wave/core.md` の `DW-C01` と `docs/dev-wave/operations.md` の `DW-O01`
  (完了は `.done` と exit code だけで判定し通知を判定にしない) が既に持つ規律の実行系への拡張である。
- 再発検知: `.done` の mtime が投入時刻より古ければ前走行の残骸であり、完了と数えない。
  本 wave では実際に旧 `.done` (rc=1) が残っていて、新走行の結果と取り違えかけた。

### {{F:mutation-scope-misses-real-repo-gate}}. 変異 runner の scope に実効 gate の node が無く 4 件が静かに生存した [テスト代表性] [恒真ゲート]

- 事象: docs の受理集合を変える変異 4 件 (条件行削除・発火条件文の改変・参照先すげ替え・
  節本文の空化) が、runner scope (`orchestrator/tests/test_check_docs.py`) では
  SURVIVED になった。失敗 node は 0 件だった。
- 根本原因: これらを唯一検出する `test_real_repo_clean` が変異 container で実行されない。
  skipif は無く、dispatch 経路で collect されないまま緑になる。期待 node に
  `test_real_repo_clean` を書いても、走らないので永久に一致しない。
- 恒久対応: `DW-M02` の「実効 gate へ再照準」を実行し、統合 commit 後の一時変異 +
  `tools/check_docs.py` 直呼びで 4 件とも rc=1 (違反 2 / 1 / 2 / 1 件) を実測して証拠とした。
  復元は `git checkout --` で行い、復元後 rc=0 と clean tree を確認した (`DW-O19`)。
  初回 matrix は erratum として保存し、実測 node で残り 4 件を再登録して再走した。
- 再発検知: 変異 matrix で SURVIVED が出たら、期待 node が runner scope 内に**実在して
  走っている**かを `--junitxml` か実走ログの collected 件数で確かめる。
  0 件失敗の SURVIVED は「gate が無い」ではなく「gate が走っていない」を先に疑う。
