---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2237-sort-cache-twin-close
seq: 2
---

## 再発

### F428

- **再発: 2026-09-16** — [T-2237] の carry が「裁定済み (D1548) → 実装待ち」と言い続けたが、実体は双子の [T-2253] が
  2026-09-05 に実装・land して 完了 にしていた (`8f54a601c`)。同じ作業を指す別 ID が閉じ、こちらだけ残った点は 2026-09-14 /
  2026-09-15 の再発と同型である。**新しい面は検索鍵である。** 2026-09-15 の再発は「carry 本文が名指す別 T 番号を検索鍵へ足す」を
  教訓にしたが、[T-2237] の本文は双子の T 番号を 1 つも名指さない — [T-2253] の方が後から採番され、その本文が
  「同じ主題の項を登録したら同一作業として統合する」と逆向きに書いていた。**両項を結ぶ鍵は共有の D 番号だけ**で、
  段 1 で済を露見させたのは `git log --all --grep=D1548` が [T-2253] の commit に当たったことだった。統合の機会は 2 回あり、
  2026-09-04 の /rulings 第 6 回は [T-2237] の状態語だけを直し、2026-09-05 の実装 wave は自分の ID だけを閉じた。
  実害は wave 1 本の段 1 までで止まり、実装子は起動していない。局所修復として本 wave の worklog エントリで [T-2237] を
  `完了` にした。**機械防壁は無いままである** — 同じ D 番号を根拠に持つ active 項の重複を見る検査は無い。

### F945

- **再発: 2026-09-16** — [T-2237] を閉じる docs-only wave の受入 attempt 2 (tip `ba0d7e762`) と attempt 3 (tip `4b135deb7`) で
  同型が続けて出た。attempt 2 は `test_t1259_qsub_env_delivery_probe.py` 40 件 (`git ls-files --others --exclude-standard -z` 22 件・
  `git status --porcelain=v1` 18 件、いずれも wave worktree に対する 30 秒 TimeoutExpired) に加え、同じ窓で `git archive` の timeout と
  real-repo lock 待ち超過 (`test_s8c_preregistration_predicates.py` 5 件)、launcher timeout (`test_codex_worker_launch.py` 7 件) が並んだ
  (24,067 passed / 52 赤、同時受入 4 本)。同 tip・同 3 file の単独再走は 480 passed / 105 秒で非再現。attempt 3 は同 file 17 件
  (`git ls-files --others` だけ、24,111 passed、投入時 load 38、同時受入 3 本)。**単独では同 argv が 12.4 秒 (load 30、未追跡 0 件、
  tracked 25,837 件) で完走し**、30 秒境界の 4 割を静穏時に既に使っている。wave の変更は docs 3 file で、当該 fixture・probe・
  Git 呼出しは変更していない。恒久対応は既報どおり変えず、窓を選んで受入を再走した。
