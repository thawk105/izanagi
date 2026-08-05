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
- **セッション異常 2 件。** (1) 変異 spec の `category` に `positive-control` と書いて harness が
  `category が未知` で停止した。受理集合は `negative` / `positive` / `both-layers` である。
  (2) **変異走行の開始直後に親が docs fragment を書き、harness が untracked を検出して中止した。**
  走行中は同じツリーで独立な文書作業もできない。記録を先に commit してから再走した。
- **親の手続違反 1 件。** 最初の main 取り込みで `git merge --no-edit` を使い、provenance trailer の
  無い merge commit を作った (`DW-O17` は自動 message と `--no-edit` を禁じている)。
  `git reset --hard` で取り消し、message file → preflight → `commit -F` へ戻した。
- **受入全走が 1 度赤になった。** 初回は 6,205 passed / **1 failed** で、失敗は
  `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`。
  新設テストが自走 harness も allowlist 記載も持たず、素の runner で 0 件実行の偽緑になりうる
  状態だった (F42 の型)。**偽緑ガード側は緩めず**、テストファイルに自走 harness を足して解決した
  (`python3 orchestrator/tests/test_audit_dangling_commits.py` が実際に 8 本を実行する)。
  子は計算ノードへ dispatch できず全走を回せないため、**親の受入全走が最後の網になった。**
- **land 直前に、監査が常時鳴る発生源を特定した。** local main を取り込んだ tree で実走すると
  1 件報告された。出所は main に既に land しているテスト
  `orchestrator/tests/test_s8c_preregistration_invariant.py` の `_candidate_commit()` で、
  **実 repo の object store へ `git commit-tree` で合成 commit を作る**。内容は
  「HEAD + その時点の index/worktree」で、どの ref からも参照されないため即座に到達不能になる。
  つまり wave が作業中に受入を走らせるたび、その未 commit 作業を内容とする到達不能 commit が残り、
  本監査は必ず報告する。この repo は常に並行 wave が走るため**実質的に常時鳴る**。
- **これを受けて入口の rc 規律を直した。** 実装は当初「rc≠0 は停止」と書いていたが、これは
  敵対レビュー A-9 が求めた原文より厳しい。A-9 は「rc=0 のときだけ削除へ進む。**rc=1 は報告・
  救出判断**、rc=2 は全削除停止」であり rc=1 を停止にしていない。常時鳴りと合わさると cleanup が
  事実上いつでもブロックされ、**鳴り続ける gate は無視されるようになるため安全上も逆効果**である。
  原文どおり 3 分岐へ直した。監査の判定ロジックは変えていない (報告自体は正しい)。
  テスト衛生の問題は scope 外として裁定へ返した。
- **入口は 3,983 bytes で実効上限ちょうど、余裕ゼロである。** 次に入口を触る者は先に予算を作る必要がある。
- **エージェント工数。** codex 子 6 本 (段 5 実装 1、段 6 レビュー 2、fix 3)。段 2・3 は軽量版のため省略。
- **実測 (2026-08-05、worktree `dev-wave-cleanup-submodule-recurrence`、
  branch `worktree-dev-wave-cleanup-dangling-audit`)。**
  受入全走 = **6,304 passed / 0 failed / 19 skipped** (602.05s、入口 rc 規律の修正後・local main
  `473d73fa` 取り込み後の最終走行)。その前段の走行は 6,206 passed / 0 failed。
  `tools/check_docs.py` = 違反なし。`check_ai_provenance.py` = 1,283 件で違反なし。
  `tools/audit_dangling_commits.py` の実走 = **要確認 0 件 (rc=0)**。
  変異 matrix = baseline PASSED、6 本中 5 本が期待どおり単一 node で KILLED。
  M02 のみ MISMATCH (条件 2 を落とすと merge control も同時に赤 = 過剰決定) で、
  初回 ledger を erratum として残し、期待値を実測に合わせた M02B を再走して KILLED 一致。
  逐語と変異台帳は `output/insights/2026-08-05_cleanup-dangling-audit/`。

## 次の一手差分
