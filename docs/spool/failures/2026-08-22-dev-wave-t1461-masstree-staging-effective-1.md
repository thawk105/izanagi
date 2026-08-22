---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1461-masstree-staging-effective
seq: 1
---

## 再発

### F95

- **再発: 2026-08-22** — floor masstree staging 実効化 wave の変異本走で 4 回目の再発
  (初出 2026-08-04、再発 08-16/08-17/08-18 に続く)。今回は台帳を検索する前に
  「素の node id を expected_nodes から除外するが runner argv には `--deselect` を
  足さない」という不完全な回避を最初に試したため、除外してもテストは実行され続け
  failed_nodes に残り、MISMATCH (expected 側に無い extra 1 件) を再現した。台帳を検索して
  正しい回避策 (`--deselect=<素の node id>` を runner argv へ追加) を発見し、
  baseline PASSED・161/161 KILLED で収束した。[T-417] の恒久対応は依然未実施であり、
  4 回目の再発によって「散文の再発記録だけでは検知にならない」ことが追加で示された。

### F283

- **再発: 2026-08-23** — 同じ gate (`tools/pegasus/admission_registry.json:
  working bytes が HEAD blob から drift`) を、**codex 子の起動ではなく親の焦点走で**踏んだ。
  **引き金も現れ方も既載 2 件と異なる。** 段 6 の追加 fix で Codex `role=author` が
  同ファイルへ entry を 1 件足した直後、親が commit する前に焦点走を投入したところ、
  `orchestrator/tests/test_codex_worker_launch.py` が **70 件赤**になった。
  launcher を subprocess として起動するテスト族が、起動前検査で一律 `launcher_rc=2`
  (`outcome='launcher_error'`) を返すためである。commit 後の再走は 1646 passed / 0 failed。
- 新しい情報は 2 点。(i) **この gate は「子を起動できない」形だけでなく「テストが大量に赤くなる」
  形でも現れる。** 後者は赤の件数が多く失敗メッセージも実装差分と無関係なため、
  自分の実装差分の回帰と誤帰属しやすい。実際の判別点は launcher.stderr 先頭行 1 行だけである。
  (ii) 既載の恒久対応 (段 6 のレビュー子を投げる前に統合 commit を作る) は
  **レビュー子の投入だけを守っており、fix 後の親の焦点走を守っていない。**
  fix が hook 正本ファイルを触った場合は、焦点走の前にも統合 commit が要る。
- 再発検知: launcher 族が理由不明に大量赤になったら、まず
  `git status --porcelain` に `hooks/**` / `tools/pegasus_admission_registry.py` /
  `tools/pegasus/admission_registry.json` の未 commit 差分が無いかを見る。
