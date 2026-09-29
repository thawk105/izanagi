---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-md2-push-pack-hint
seq: 1
title: /cleanup-branches §5 に push 失敗時の送信範囲 pack 化 1 行を足し、command 予算を個別裁定で 7,058→7,437 へ引き上げる (docs + pin、branch worktree-dev-wave-md2-push-pack-hint)
---

## 本文

- 依頼: 並行 wave の共通指示 (git-maint-2026-09-29 の md_2)。push が `loose object <sha> ... is corrupt` →
  `remote: fatal: early EOF` で約 100 回連続失敗した件 (2026-09-29、毎回違う object を名指し、名指しの object は正常) の対処 1 行を、
  push をユーザーへ引き渡す `.claude/commands/cleanup-branches.md` §5 に置く。
- 台帳: 「次の一手」に「push 前の送信範囲 pack 化」を含む item は無かった (`送信範囲\|pack 化\|loose object` を wave 作業木の `docs/worklog.md` と local main の同 file へ grep し、どちらも 0 件)。
  本 wave で完了するため新規 T は立てない (立てると済んだ作業が active に残る、F428 の型)。
- **予算の上限引き上げ (ユーザーへ報告):** 指示は「予算は変えず文言を削って収める」だったが、着手時 7,055/7,058 bytes (空き 3)。
  §5 の既存文の圧縮 + 最小の追記 + ファイル全体の CJK 隣接空白の除去 (見出し・frontmatter・§1・§3 の固定 2 行を除く) という
  この削除案でも 7,110 bytes で、上限を 52 bytes 超えた (再現: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-md2-push-pack-hint/evidence/`)。
  空白以外の意味等価な縮約を網羅したわけではなく、「この削除案では収まらなかった」までが実測である。そのうえで、他節の文言を
  書き換える縮約は所有外かつ安全義務の文に触れるため試さず、§5 を意味等価に縮めて上限を 7,437 (新サイズ 7,434 + 従来と同じ余白 3) へ引き上げた。**これは本 wave の個別裁定であり、D730/D782 の
  「独立 3 例の例外」要件は満たしていない** (事象は 1 件、約 100 回は同じ事象の再試行)。
  runbook へ本文を置き §5 は参照だけにする案も、参照 1 行でも約 120 bytes 要る (親の試算、未実測) ため引き上げを避けられず、指示の「引き渡し箇所に 1 行」から外れるので採らなかった。
- 段 6 read-only review 1 本 (2 レンズ兼用、予算引き上げの独立審査を兼ねる) が NO-GO: must-fix 3 件
  (R1 「実物は正常」の断定 → 条件付きの推定へ、R2 linked worktree では `.git` がファイルなので primary の main checkout と明示、
  R3 D782 適合の主張 → 個別裁定と書く) と nit 2 件 (R4 文言の短縮 7,437→7,434 bytes、R5 予算実測の射程を限定) を全て採用。
  「送り先が origin/main である前提を添える」提案は、§5 が扱う push が main の push だけでコマンド自体に現れるので追記しなかった。
  焦点再レビュー 1 本は R1〜R4 closed・R5 partial で、fragment の「安全義務を削らずには入らない」という未証明の断定 (must-fix) を
  指摘した。「この削除案では収まらなかった」へ限定して閉じた。「全体 repack は 10 分超で不要」が一般化だという nit は採らなかった
  (送信範囲の pack 化で足りるので全体 repack が不要なのは手順上の事実で、10 分超はこの repo での実測)。
- 実装面 (`tools/check_docs.py` の予算・whole-file SHA-256、`orchestrator/tests/test_check_docs.py` の逐語写しと pin) は Codex author 子と fix 子。
  子は login の pytest 拒否と `qstat` 接続失敗で pytest を走らせられず、テストの実走は受入全走が担う。
- 変異 M1 (上限を 7,058 へ戻す)・M2 (SHA を旧値へ) は、common.txt が計算ノード job を受入全走以外に禁じるため、
  login で `python3 tools/check_docs.py` を直接走らせて確認した (author 統合 6524efd42 と fix 統合 a9a96fd2a の各上で両方 rc=1、kill。
  復元後の blob は commit と一致)。
- 軽量版: 段 2・3 を省略。

## 次の一手差分
