---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1179-official-trust-root
seq: 3
---

## 新規

### {{F:review-claim-unverified-before-fix}}. レビューの「main 比の回帰」を裏取りせず fix を投げ、main 由来の期待値を書き換えさせた [捏造/幻覚] [手順漏れ]

- 事象: 段 6 の焦点再レビューが「M-finalize-pending の再開不能は main 比の回帰である」と
  must-fix を出した。親はこの主張を一次資料で確かめないまま fix 子を投入し、
  「main では完了できた」という誤った前提を prompt に明記した。子は指示どおり実装を直し、
  同時に「対象 test 関数と旧失敗期待は main に存在した」と報告した。親が
  `git show 699c9cae:orchestrator/tests/test_s8b_floor_campaign.py` を読んで初めて、
  main 自身が当該再開の失敗を固定していると分かった。**回帰ではなく main の既存挙動**だった。
  fix 1 巡ぶんを全破棄した。
- 根本原因: 敵対レビューの所見を「real か refuted か」の裁定を経ずに fix 指示へ直送した。
  レビューが挙げた根拠 file:line は**変更後の作業木**のもので、
  「main ではこうだった」の部分だけ一次資料が示されていなかったのに、親がそれを見落とした。
  加えて親は自分の prompt に「main 由来の既存テストの期待値を変更してはならない」と書きながら、
  同じ prompt で main 由来の期待値の書き換えを具体的に指示していた。
- 恒久対応: memory `primary-source-includes-failures-ledger` と同型の規律として、
  **レビューが「main 比の回帰」と主張したら、fix を投げる前に `git show <main>:<path>` で
  main 側の実挙動を確かめる**。段 4 裁定 (DW-S04) の real/refuted 裁定は段 6 の所見にも適用され、
  段 6 の fix は裁定を経た所見にだけ投げる。
- 再発検知: fix 子の完了報告に「裁定・プランと食い違った点」欄を必須にしてある
  (本 wave の実装子・fix 子 prompt はいずれも同欄を持ち、実際にこの食い違いを表に出した)。
  この欄が空でない fix 巡は、親が一次資料で照合するまで統合しない。

### {{F:docs-write-during-mutation-run}}. 変異走行中に docs を編集して harness を rc=125 で止めた [手順漏れ] [計測汚染]

- 事象: 変異 probe (11 走) の走行中に、親が同じ作業木の
  `docs/phase3-8b-restart-runbook.md` を編集した。`tools/mutation_worktree.py` の事後検査が
  「source/main 共有木の観測 bytes が変化した」を検出し、`rc=125` で中止した。
  11 走ぶんの計算ノード時間が無駄になった。
- 根本原因: 「変異走行中は tree へ書かない」を、テスト投入とコード編集の話だと解釈し、
  docs 執筆を待ち時間の埋め合わせに使えると誤認した。wrapper が守るのは
  **共有木の status bytes の不変**であって、変更が tracked file か docs かを区別しない。
- 恒久対応: memory `no-tree-writes-during-mutation-run` の適用範囲に docs 執筆を明記する。
  変異走行中の待ち時間は tree の外 (job dir の handoff・報告文) にだけ使う。
- 再発検知: `mutation_worktree.py` の事後検査そのものが fail-closed で発火する
  (本件はその検査が実際に止めた)。検知は既にあり、欠けていたのは走行前の待避判断である。
