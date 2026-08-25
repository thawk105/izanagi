---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1283-runner-main-blob
seq: 3
---

## 再発

### F28

- **再発: 2026-08-25** — dev-wave-t1283-runner-main-blob の段 4 で、親が事前登録した変異 5 件の
  うち 2 件の単一理由性が成立していなかった。型は F28 と同じ「事前登録を実測でなく設計から書いた」。
  (i) M2 (land の main/tip 一致検査を非帰属枝へ戻す) の殺し手として、負例の受領証へ**旧実装相当の
  tip 側 digest** を持たせれば拒否理由が一致違反へ分離されると書いたが、実装は digest を **main 側**
  blob と照合するため、一致検査が消えても digest 不一致で先に拒否される。分離の向きが逆だった。
  (ii) M5 (land が `tested_main` でなく `locked_main` を引く) の殺し手は fixture 上
  `locked_main == tested_main` であり、置換しても値が変わらず殺せなかった。
  **どちらも「その位置より手前に同じ入力を落とす検査があるか」をコードで辿れば実装前に分かる**もので、
  親は散文の推論で単一理由性を宣言していた。段 6 の敵対レビューが 2 件とも must-fix として検出し、
  訂正後の本走は 5/5 KILLED となった。
- 恒久対応の追補: 事前登録の単一理由性は、変異位置から**拒否が起きる地点までの分岐を 1 つずつ辿った
  根拠**を裁定文へ書く。「fixture がこう渡すから分離される」という宣言だけでは、照合先が逆でも
  文面が成立してしまう。あわせて過剰拒否の正例は、変異が置換する 2 つの値が fixture 上で
  **異なる**ことを確認してから登録する。

### F300

- **再発: 2026-08-25** — dev-wave-t1283-runner-main-blob の変異 **plan-only** が
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で `rc=125` になった。
  走行そのものは 1 件も始まっていない段階で落ちており、原因は 2026-08-25 の先行再発項と同じく
  **並行 wave が local main を進めた**ことである。
- **今回は防ぐ手段が取れた。** 直前の supersede は「待ち時間の使い方を正しても防げない型が存在する」で
  終わっていたが、観測点は `--source-repo` から `git rev-parse --git-common-dir` で導かれる
  primary worktree と source の 2 つだけである (`tools/mutation_worktree.py`)。したがって
  **対象 commit を checkout した独立 clone を `--source-repo` へ渡すと、観測点がその clone 自身の
  1 点に畳まれ、共有 main checkout が何回進んでも事後検査は成立する。**
  本 wave は `git clone --shared <wave worktree> <scratch>/src-clone` の後に対象 commit を
  checkout して渡し、probe と本走の 2 回とも完走した (本走 5/5 KILLED)。
  副次的な利点として、観測点が自分の作業ツリーから外れるため、**変異走行中も記録作業を進められる**。
- 恒久対応の追補: 並行 wave が常時走る機体では、変異 harness の `--source-repo` に共有 checkout や
  その worktree を渡さず、対象 commit だけを持つ独立 clone を渡す。
  この手順を `docs/dev-wave/mutation.md` の `DW-M05` へ 1 文で入れることを試みたが、
  L1.5 層の unique footprint が 9772 bytes となり予算 9566 bytes を 206 bytes 超えた。
  自己改善契約は予算のために安全義務を削ることを禁じ、予算値の引き上げを独立審査へ回すため、
  入口・reference への追記は行わず本項を正本とする。

### F273

- **再発: 2026-08-25** — dev-wave-t1283-runner-main-blob の受入全走 attempt 1
  (claimed main `d8f777a4`) が **16477 passed / 61 skipped / 1 failed** で戻り、唯一の赤が
  `test_codex_worker_launch.py::test_check_receipt_reads_v2_parent_attempt_field_sets_without_upgrade[wave-parent]`
  だった。本文は子 process の `returncode=2` (`NG: receipt truth table が不正`) で、
  同日の先行再発項と逐語一致する。
  台帳の再発検知どおり実測した — 受入時の並行 `codex_worker_launch.py run` は **11 本**、
  並行 `run_tests.py` は 11 本、login node の load average は 5.76 / 6.52 / 7.79。
  同ファイルの単独走 (`--force-dispatch`) は **202 passed / 8.20 秒 / rc=0** で緑。
  本 wave の差分は `tools/acceptance_launcher.py` / `tools/dev_wave_land.py` と両者の test だけで、
  `tools/codex_worker_launch.py` への到達経路は無い。よって実装差分へ帰属させない。
- 追加の観測: 同じ全走で、焦点走では決定的に落ちていた
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` (F57) は**緑だった**。
  F57 が記録する「大きい file 集合では緑・小さい集合で赤」という同居依存が、
  16539 item の全走と 291 item の単走の対比で再現している。
