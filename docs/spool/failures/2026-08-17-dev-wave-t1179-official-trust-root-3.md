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
- **併発した二次障害:** この中止で dispatch の orphan hold が武装し、以後この worktree の
  scheduler command が全面停止した (焦点走が `rc=16`、reason=`orphan-hold`)。
  解除は hold JSON 自身が書いている手順どおりに行った — `qstat` で対象 request の不在を
  **出力内容で**確認 (rc は不在でも 0)、source の clean と HEAD を確認、hold を手動削除。
  手動 `qdel` は使っていない (それは別ラッチを武装させ、解除がユーザー手番になる)。
  **変異走行を中止させると、テスト実行系まで巻き添えで止まる**という結合を記録しておく。

## 再発

### F95

- **再発: 2026-08-17** — [T-1179] の本 wave でも同じ 2 空間問題を踏んだ。
  今回の接尾辞は xdist の loadgroup 由来で、対象は
  `test_real_seal_protocol_to_floor_official_core_e2e` である。
  素の node id で登録すると観測側が `@real-repo` 付きで `MISMATCH`、
  接尾辞付きで登録すると preflight が「pytest collection に実在しない」で停止した。
  [T-417] の恒久対応は依然未実施である。
  **新しい事実は、回避策が既に本エントリの 2026-08-16 再発として台帳に書かれていたのに、
  親が変異走行の前に failures 台帳を引かなかったこと**である。そのため 1 走 (9 変異 + baseline)
  を無駄にした。台帳の指示どおり runner argv へ `--deselect <素の node id>` を足し、
  期待集合から同じ node を除いて再走したところ、baseline PASSED・9/9 KILLED・
  MISMATCH 0 で一度で通った。memory `primary-source-includes-failures-ledger` の
  「一次資料には failures 台帳を含める」は、**計測を投入する前**にも適用される。
