---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-dev-wave-vhash-cicada-gc-records-fix
seq: 1
title: [T-2908] stock Cicada の TPC-C (Delivery を含む並行走行) の gc_records ERR を、原因を実測で確かめてから直した。修理後に見えた scan の空 key も直し、並行下の削除を含む trace が初めて判定器に通った (insight + patch 2 本 + README 節 + CCBench local branch、branch worktree-dev-wave-vhash-cicada-gc-records-fix)
---

## 本文

- 依頼は起動時に読んだ `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt` (21:43 JST の版)。同 file は 21:59 に VHash 親セッションが別依頼 (hot 配置) で上書きし、親セッションが誤りを認めて本 wave の継続を確認した。本文は一次資料の `verbatim/request-md_23.txt` に逐語 ({{F:request-file-overwritten}})。
- 並走 wave md_19 (cicada build issues fix) の依頼も同じ欠陥を項目 3 に含んでいた。開始時に peer で分担を合意し、本 wave が専任、md_19 は build 不具合 2 件だけで [T-2908] に触らない。
- 結果 (一次資料 `output/insights/2026-09-29/vhash-cicada-gc-records-fix/README.md`、設計判断 {{D:cicada-gc-records-fix}}): 診断で 10/10 が「後発の削除版が read set 再検査で abort し aborted のまま最上段に残る」形。修理 1 (gc_records が aborted を読み飛ばす) と、修理 1 で表に出た修理 2 (scan の key を Tuple の複写から取る) を CCBench local branch `izanagi-cicada-gc-records-fix` (F `25898d00` → `dd6ea514` → `81fc4a84`) と `patches/fix-cicada-gc-records.patch`・`patches/fix-cicada-gc-records-scan-key.patch` に置いた。最終 patch で修理版 F × t4 10/10・t8 10/10 完走、同じ job の無修理は t4 5/5・t8 4/5 が ERR、修理版 trace は巡回 0・存在履歴違反 0・C 行 = commit 数、M・R2 は判定不変。上流 CI の format・build を CCBench の branch tip で手元通過。
- 事前登録から外れた点: ASan の確認は「rc=0 かつ ASan 報告 0」で登録したが、修理版 3/3 は実行中の AddressSanitizer 報告 0 で完走し、終了時の LeakSanitizer (解放しない領域) で rc=1 になった。文言は満たさず、実質 (実行中のメモリ誤用 0) は満たすと一次資料に書いた。
- 段 6 で fix 2 巡 (scan の空 key の修理、INLINE_VERSION_OPT の予備と CI build script の親検査)、焦点再レビュー 2 巡。段 4 追補裁定で修理 2 を scope に入れた (依頼の完了判定の trace 項目に必要なため)。
- 計算は計算ノード合計 1,024 秒 (診断・確認 7 job・CI build 1 job、受入を除く)。受入全走は land 前に行う。
- Codex (gpt-6-sol、medium): 診断 author 1、plan 1、相談 2、author 1、レビュー 2、fix 2、焦点再レビュー 2。

## 次の一手差分

### 完了

- [T-2908] stock Cicada の gc_records ERR を原因特定のうえ修理し、修理版で F cell × 4・8 thread が毎回完走、並行下の削除を含む trace が判定器に通った ({{D:cicada-gc-records-fix}}、一次資料 `output/insights/2026-09-29/vhash-cicada-gc-records-fix/README.md`)。push と pin の前進は {{T:cicada-gc-records-fix-push}} へ移した。
  remaining: none
  base: 6e6ff069486b5413bc28158753f3683473d9fe4b855327e6c7a26db28e5199c9

### 新規

- {{T:cicada-gc-records-fix-push}} **P2・人間の手番**: CCBench の local branch `izanagi-cicada-gc-records-fix` (tip `81fc4a84cc855a3f98374e40e2ba7e3330c2614d`、F `25898d00` の子 2 commit = gc_records の修理と scan の key の修理) を別名 branch として push し (force しない、D16)、GitHub の CI (build・format) の緑を確かめる。手元では CI と同じ手順で format (clang-format 14、213 file) と build (CI image、全 protocol) が通っている。branch の所在は wave 木の submodule git dir と bundle (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/fix.bundle`)。主 checkout の submodule git dir へは land 後に bundle から非 force で fetch する (一次資料 §7)。並走 md_19 の branch と 1 本にまとめるかは人間の判断 (行は重ならない)。その後の pin 前進 (gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN`・patch の厳密適用・D297) は別 wave で、前進したら `patches/fix-cicada-gc-records*.patch` は不要になる。それまでは delete を含む並行 TPC-C の Cicada を使う実験は 2 本の patch を pin C (→ 計装) の後に当てる。
- {{T:cicada-abort-insert-uaf}} **P3・新規**: stock Cicada の `abort()` が INSERT した tuple を `delete` した直後に `writeSetClean()` が同じ tuple の `continuing_commit_` へ書く use-after-free (`cc/cicada/transaction.cc` の abort と `include/transaction.hh` の writeSetClean)。insert を含む tx が abort すれば削除の有無に依らず起きる (ASan で M cell の stock 2/2、修理版 3/3)。Release では解放直後の同じ thread の書き込みで実害は小さいと見込む (推測) が未定義動作。直し方の候補 = writeSetClean で INSERT 要素の tuple に触れない、または abort の削除を writeSetClean の後へ回す。CCBench の変更なので Codex author・上流 CI・push は人間。根拠: 一次資料 `output/insights/2026-09-29/vhash-cicada-gc-records-fix/README.md` §6。
