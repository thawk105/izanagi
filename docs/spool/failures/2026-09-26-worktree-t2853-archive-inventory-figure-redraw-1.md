---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-t2853-archive-inventory-figure-redraw
seq: 1
---

## 再発

### F39

- **再発: 2026-09-26** — [T-2853] (1') wave で、`orchestrator/campaign/pipeline.py` の保全口に git の `subprocess.run` を 2 か所足したのに、段 1 brief の変更面の表と段 5 の実装子の所有 path に、production を静的走査して起動箇所を台帳に持つ `orchestrator/tests/test_ccbench_spawn_sites.py` (review 済み起動箇所の 2 つの登録簿) を入れなかった。親が統合 commit の後に起動箇所の登録を静的に確かめて焦点走に加え、焦点走 1 回目で 2 赤 (`('campaign/pipeline.py', '<module>._preserve_trace_directory'): 2` 未登録) として検出した (land 前、実害なし)。fix で git の起動を 1 helper (`_archive_git`) に寄せて登録した。同じ型は [T-2851] (受入 1 回目の赤 3 件、worklog のみに記録) に続く独立 2 例目。恒久対応は F39 の運用 (production の行・起動箇所を変える wave は、production を静的走査して位置を台帳に持つ test を閉包と焦点走に入れる) から変えない。

### F601

- **再発: 2026-09-26** — [T-2853] (1') wave の段 6 fix 1 で、保全時に source root の `git rev-parse HEAD` (40 桁) を `SourceEvidence.ccbench_commit` と**完全一致**で照合した。現行 pin `pin.CURRENT_PIN = "6810666"` は 7 桁で、build 側 `buildcache._verify_ccbench_commit` は前方一致で受理するので、現行 pin を使う driver では本番の保全 inventory が恒常的に `failed` になるところだった。親の実測 (pin 定数と campaign lock 30 件の桁数) と焦点再レビューが独立に検出し、fix 2 で build 側と同じ前方一致と、解決済みの完全 SHA (`ccbench_pin`)・宣言値 (`ccbench_pin_declared`) の併記に直した (land 前、実害なし)。F601 と逆向き (後段が厳しい完全一致を新設し、前段の緩い受理と食い違う) だが、恒久対応の「pin を渡す全呼び出しで、渡す値の桁数と受け手の照合方法を対で確認する」がそのまま当たる。恒久対応は変えない。
