---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1300-new-l2-section
seq: 3
---

## 新規

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

## 再発

### F355

- **再発: 2026-08-18** — 本 wave で `tools/dev_wave_wait.py producer` が出力 0 bytes・rc=0 で
  早期終了する事象を 3 回観測した。いずれも producer は生存しており (`ps` の経過時間で確認)、
  成果物も `.done` も無かった。arming 前の pid file 実在確認は済ませていた。
  **F355 で未特定だった根本原因を本 wave で特定した**: この session では背景 Bash 自体が
  約 10 分で終了させられ、その子である待ち手が巻き添えで死ぬ。背景に投げた焦点テスト走行も
  同じ約 10 分で打ち切られ、dispatch した計算ノード側の成果物収集の途中でログが途切れた。
  対応として、実行系は codex 子と同じく runner と launcher を `.sh` へ外出しして
  `nohup setsid` で detach し、死活判定は producer の pid と `.done` の mtime だけで行った。
  旧走行の `.done` (rc=1) が残っていて新走行の結果と取り違えかけたため、mtime の照合も要る。
