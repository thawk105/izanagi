---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-07
wave: dev-wave-t597-budget
seq: 2
---

## 再発

### F146

- **再発: 2026-08-07** ([T-597] wave、独立 2 例)。docs-only の縮約に対する fix が、
  同じ wave 内で新しい不整合を 2 回生んだ。(1) `DW-S09` の 2 文削除を 1 文で復元したところ、
  成功 status 集合 (`landed` / `already-landed`) を `core.md` と `operations.md` で
  **二重管理する退行**を作り、焦点再レビューが検出した。`DW-O23` を参照する形へ変えて解消。
  (2) `DW-S06-C` から対応表要求の文を削除したことで、`docs/failures.md` の本 F 自身が
  担い手として指す `DW-S06-C` が **stale になった**。現在の担い手は `DW-O16` である
  (条件 16 = 焦点再レビュー直前に必読、かつ「表なしで root cause が閉じたと判定しない」まで持つ)。
  canonical の既存 bytes は通常 fold では置換できないため、本追記で現担い手を明示する。

### F155

- **再発: 2026-08-07** ([T-597] wave)。変異本走を `--runner-mode local` +
  `python3 tools/run_tests.py <対象 module> -rf` で組み、M2 が rc=16
  (`bounded scope の memory.max / memory.oom.group を走行中に attest できない`) で 3 度止まった。
  **本 F の恒久対応 (`--runner-mode dispatch` + `--force-dispatch` の既定 recipe) を知らずに
  runner argv を自分で組んだ**ためで、原因も対処も本 F がすでに書いていた。
- **親の根本原因の誤帰属を訂正する (2 段階の誤り)。** まず「共有ログインノードの外乱」と判断し、
  静穏窓 (生存中の予約 0) でも再現したので撤回した。次に「変異対象が変異 harness 自身なので
  fail-closed 分岐を消すと入れ子実行が増えて外側 scope が倒れる」という自己参照仮説を立て、
  これを一次資料へ根本原因として書いた。**この仮説は検証していない。**
  本 F が `_SCOPE_ATTEST_SECONDS = 1.0` の race として原因を特定済みで、
  親は既定 recipe を試さないまま独自仮説を root cause として記録していた。
  **「既存 F の恒久対応を試す前に新しい根本原因を立てない」** を実運用の教訓として残す。
- 検出力の実測自体は有効である。narrow 走行 (対象 nodeid のみ、`DW-O19` の復元規律に従う) で
  M1/M2/M3 とも kill node ちょうど 1 件、変更前テストでは M2/M3 とも素通りを確認した。
  その後、本 F の既定 recipe で本走をやり直した結果を変異台帳の正本とする。

### F156

- **再発: 2026-08-07** ([T-597] wave、独立 2 例)。(1) 静穏窓待ちの launcher が `.done` を
  投入直前でなく**静穏窓到達後**に消す作りだったため、待ちが前回投入の残骸を掴んで即座に返り、
  変異本走が完走したと誤って報告した。(2) 受入全走の launcher では、投入直後に
  `pgrep -f <script 名>` で PID を採ったところ、**自分の起動ラッパー**の PID を掴んでいた
  (コマンド行に script 名が含まれるため)。ラッパーは即終了するので待ちが即座に返り、
  再び「完走した」と誤報した。
- 追加の恒久対応: PID は待ち手側が `pgrep` で推測せず、**生産者 script 自身が `echo $$` で
  書き出したファイル**から読む。`.done` の除去は script 冒頭 (投入経路に入った直後) に置き、
  条件待ちの後ろへ回さない。
