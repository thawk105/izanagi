---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-cleanup-dangling-audit
seq: 1
title: 消えたブランチの未 land 作業を検出する監査を land した — 前セッションの実装は provenance 契約で land 不能と判明し Codex author で書き直し、誤検出の真因は merge の差分の取り方だった (コード + docs、branch worktree-dev-wave-cleanup-dangling-audit)
---

## 本文

- **ユーザー裁定「1,2,4 推奨通り。3 は取り込む価値がありそうなら取り込み」** (2026-08-05、一次資料は
  `dev-wave-jobs/rulings-inbox/2026-08-05-cleanup-branches-dangling-commit-gap.md`) を受けた実装を
  land した。裁定事項 1 = cleanup-branches が「ブランチごと消えた未 land 作業」を検出できない穴を塞ぐ。
- **前セッションの実装 `e8d0c44c` は land しないと裁定した** ({{F:implementation-blocked-by-provenance-after-the-fact}})。
  検査は緑だったが実装面に Codex `role=author` が無く、main へ入れると full-history 監査が恒久的に
  赤くなる。裁定パッケージの選択肢 (1) を採り、旧 commit を参照案として渡したうえで現行 main の上に
  Codex 実装子が書き直した。旧 branch `worktree-cleanup-submodule-recurrence` は land せず残る。
- **親の手続違反を 1 件自己検出した。** 最初の main 取り込みで `git merge --no-edit` を使い、
  provenance trailer の無い merge commit を作った。`DW-O17` は自動 message と `--no-edit` を
  禁じている。`git reset --hard` で取り消し、message file → preflight → `commit -F` へ戻した。
- **誤検出の真因はレビュー 2 本とも見落とし、親の実測が特定した** ({{F:merge-parentwise-diff-inflates-changed-paths}})。
  親が段 6 で実走して 3 件の誤検出を観測し、当初「main の履歴に一度も現れていない path だけ報告する」
  案を出したが、**レンズ A / B の両方が「path 再利用時の見逃しを広げる」と反証した**。
  その後に親が測り直したところ、真因は `git diff-tree -m` が merge の取り込み側を丸ごと
  「その commit の変更」に数えていたことだった (1 merge で 123 path、combined diff なら 3 path)。
  combined diff へ変えると報告は 3 件 → **0 件**になり、履歴による抑止は一切不要になった。
  **誤った修正案を実装前に捨てられたのは、敵対レビューと親の再実測の両方があったためである。**
- **敵対レビュー 2 本はどちらも NO-GO** (A = blocker 1 / must-fix 5、B = blocker 1 / must-fix 4)。
  両者の中核は「同名 path があれば land 済みとみなす安全述語が誤り」で、既存ファイルへの変更・
  削除・同名別内容・gitlink 更新を見逃す点である。**これはユーザー裁定が定めた設計そのもの**
  なので実装で覆さず、(a) 出力の断定をやめ「要確認の到達不能変更」とし、(b) 検出対象外を
  `--help` と 0 件時出力に明示して**誤った安心だけを閉じ**、(c) 設計変更 5 件は推奨付きで
  裁定パッケージへ返した (`dev-wave-jobs/rulings-inbox/2026-08-05-dangling-audit-design-scope.md`)。
- **レビューが refuted した疑いも 4 件記録する。** 実装が repo を書き換える (I5 違反)、
  positive control が恒真・自己オラクル、入口の byte 捻出が安全義務を摩耗させた、
  既存経路と重複し純増検出力ゼロ — いずれも反証された。
- **入口の実効上限は 4,000 ではなく約 3,983 である。** 負例テストが +17 byte 追記して
  「違反ちょうど 1 件」を要求するため。**テストの期待値は緩めず**、意味を変えない重複記述だけを
  削って 3,982 byte に収めた。安全義務は 1 つも削っていない。
  whole-file SHA-256 の pin は `tools/check_docs.py`・`test_check_docs.py` の期待値・
  同 test 内の whole-file fixture の**独立 3 箇所**にあり、同時更新しないと赤になる。
- **実行場所を runbook §7.0 の手順で分類した。** 専用 scope の cgroup charged memory を
  sampling して 3 回、観測ピーク 53.8 MiB、certified peak = 53.8 + 128 = **181.8 MiB**、
  規範値 512 MiB 未満で **`local-ok`**。入力規模は到達不能 127 commit / local branch 11 /
  main tree 8,954 path、wall 2.9 秒。メモリは main tree の path 集合と branch tip 数で増えるため、
  桁で増えたら再分類が要る。
- **セッション異常 1 件。** 変異 spec の `category` に `positive-control` と書いて harness が
  `category が未知` で停止した。受理集合は `negative` / `positive` / `both-layers` である。
  spec を直して再投入した。

## 次の一手差分
