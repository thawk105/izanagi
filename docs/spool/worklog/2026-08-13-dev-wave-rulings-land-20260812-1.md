---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-rulings-land-20260812
seq: 1
title: 未 land の裁定 3 束を main へ着地させた — 既 fold の重複と stale carry を内容照合で切り分け、後発の束を優先した (docs のみ、branch worktree-dev-wave-rulings-land-20260812、計測なし)
---

## 本文

- **目的と結果。** ユーザー裁定が fragment のまま未着地だった 3 branch
  (`worktree-rulings-20260812-coarse-provenance` 64afbb63、`worktree-rulings6-20260812` 6d4223cb、
  `worktree-rulings7-20260812` c670d89b) を 1 本の wave branch へ merge し、fold 可能な形に整えて
  land した。着地したのは第 2 束・第 5 束・第 6 束の裁定と、codex hook trust の起票である。
- **不採用の branch。** `worktree-rulings5-20260812` (3fe1654b) は取り込んでいない。第 5 束の裁定が
  「rulings5 は逆向きに書いており不採用・本 wave が置き換える」と明記しており、ユーザー指示も同じ。
  branch は削除していない (削除はユーザー指示があるときのみ)。[T-948] の登録文は「fragment は 2 本とも
  回収する」と書いていたが、これは第 5 束の裁定より前に書かれたものであり、後発の裁定とユーザー指示を
  優先した。差異をここに残す。
- **`.claude/commands/rulings.md` の衝突は発生しなかった。** 同ファイルを触るのは rulings5 と rulings6
  だけで、rulings5 を取り込まないため原理的に競合しない。取り込み後の byte 数は 4,992 / 上限 5,000。
- **fold dry-run が出した赤を 4 型に切り分けた。** 古い branch の fragment を land する wave では、
  赤の型ごとに扱いが違う。実測は次のとおり。
  1. `receipt-replay` / `symbol-replay` — coarse-provenance seq 2 (decisions) は同一 content_sha256 の
     receipt が `FOLDED.md` にあり、本文は D320 として着地済み。削除した。
  2. 同 wave seq 1 (worklog) は**別 branch (`worktree-dev-wave-t499-triage`) が改変版を先に fold 済み**
     だった (receipt の content_sha256 `9d765127…`、本文は `docs/archive/worklog-phase3-0812-462-465.md`)。
     content hash が違うので replay 検査には掛からないが、再 fold すれば同題エントリの二重計上になる。
     内容差分を取り、救出が必要な [T-139] の統合更新だけを未 fold の seq 3 へ移し、seq 1 は
     取り込まないことにした。
  3. `transition-target` — 先行 fold が既に終端させた項が 20 件あった (T-513/679/687/689/691/694/725/
     751/837/864/868/871/872/873/874/881 と、後から land した T-748/T-886/T-920/T-921)。いずれも
     canonical か archive に着地済みであることを逐語で確認してから落とした。
  4. `transition-duplicate` — 同一 T を 2 つの fragment が更新する重複が 6 件あった
     (T-887/T-316/T-499/T-925/T-934/T-916)。fold は同一 T の二重操作を必ず拒否するため、後発の
     第 6 束を採り、第 5 束側の更新行を落とした (第 5 束の判断内容は同 fragment の本文に全文残る)。
  5. `base-mismatch` — carry 解決後の digest が変わった項が 7 件。**base を機械的に書き換えるのではなく、
     main 側の実体を carry 鎖まで解決して内容を読み、後から足された実測を消さないことを確認してから**
     現行値へ是正した。T-925/T-934/T-916/T-316/T-949 では、main が後から書いた実測 (棚卸し実施済み・
     余白 0・追加実測) への回答を更新文へ書き足している。
- **land が 2 回拒否し、2 回目で構造的な誤りが出た (実測)。** 1 回目は `rc=21`
  (`control-plane identity/binding changed during the provenance audit`) で、並行 wave が監査中に
  worktree / handoff を増減させたことによる再試行可能な混雑。main は 1 bit も動いていない。
  2 回目は **`rc=26` `declared fold verifier が拒否: landed-fold-owned-path`** で、これは混雑ではない。
  land が landed 区間の各 commit を検査し、**fragment path の削除と `docs/spool/FOLDED.md` の変更を
  「fold の署名」として拒否する**ためである (`tools/dev_waves/git_state.py` の
  `_landed_fold_output_path`)。既 fold の fragment 2 本を独立 commit で `git rm` していたのが該当した。
  「wave 側で fold してはならない」は文書上の規律であると同時に、この検査で機械的に強制されている。
- **恒久対応: 不要な fragment は「消す」のではなく「最初から持ち込まない」。** branch を main から
  作り直し、`git merge --no-ff --no-commit` の後 commit する前に `git rm` して、除外を merge commit
  自身の中で完結させた。検査は親が 2 つの commit では trusted な main 側の親とだけ差分を取るため
  (`_landed_commit_diff` の `len(trusted) == 1` 経路)、merge commit の差分は「追加のみ」になり通る。
  最初の試行は `backup-rulings-land-20260812-first-attempt` (37ec30e8) に残してある。
- **組み直した 2 回目も `rc=26` で止まり、別の構造的誤りが出た。** 累積差分は追加のみだったが、
  land は commit 単位でも検査する。3 branch を**順に** merge していたため 2 本目・3 本目の merge は
  **親が 1 つも tested main の祖先でなくなり**、検査が両親と差分を取って branch 基点以降に main で
  起きた fold の署名 (`M docs/spool/FOLDED.md`) を拾っていた。違反 commit の特定は land 本体と同じ
  `_landed_commit_diff` / `_landed_fold_output_path` を呼ぶ使い捨て script で行った。
  3 回目は main から 1 つの merge commit で 3 branch を同時に取り込み (親 4 つ、うち main だけが
  trusted)、除外と編集もその commit の中で完結させた。2 回目は
  `backup-rulings-land-20260812-second-attempt` (b686757e) に残してある。
- **これは wave 中の main 追い越しと同じ問題である。** 作業中に main が 7 commit 進み、その都度
  base digest が変わった。fold の base 検査は「別 wave が先に同じ項を書き換えていた場合に古い本文から
  作った更新で上書きするのを防ぐ」ためにあり、赤は不便ではなく退行の検出である。
- **受入は docs-only 免除。判定手順と証拠:** `git diff --name-only main` の出力は
  `.claude/commands/rulings.md` と `docs/**` だけで実装面ゼロ。実 repo の該当パスを読む test node は
  不存在 — `grep -rln "\.claude/commands" orchestrator/tests/` の唯一の hit
  `test_check_docs.py` は `_build_min_repo()` が tmp に合成した repo へ書き込むだけで実ファイルを
  読まず、`docs/spool/` 配下は `test_spool_tree_is_excluded_from_all_legacy_doc_scans` が
  legacy doc scan の対象外と固定している。代わりに `python3 tools/check_docs.py` (rc=0) と
  `python3 tools/spool_fold.py --dry-run` (rc=0、status=planned) を実走した。
- **段 8 自己改善の候補 (実施は見送り)。** 「古い branch の fragment を land する wave では fold の赤を
  上記 4 型で切り分け、内容照合してから落とす」は再現性のある手順で、`DW-O23` へ統合したい。ただし
  第 6 束が [T-934] / [T-916] の入口・reference 追記を「L2 経路の成立後に収容する」と裁定した直後で
  あり、同じ予算面へ本 wave が割り込むのは筋が悪い。L1.5 棚卸し wave の空き枠で扱う。

## 次の一手差分

### 完了

- [T-947] coarse-provenance の未 land fragment を land した。seq 3 (第 2 束 11 件) と seq 4
  (codex hook trust の起票と `[T-815]` 完了基準の訂正) が着地し、「修正まで codex-only dev-wave は
  投入しない」という現行運用制約が main の台帳へ入った。seq 1 / seq 2 は先行 fold 済みと実測したため
  取り込まず、seq 1 からは [T-139] の統合更新だけを救出した。
  remaining: none
  base: a699d9dc6dcc0c9e1b89895144b5cc6e10246053c3fe2e881702ba85f6514bdc
- [T-948] 第 5 束 (worklog + decisions + `.claude/commands/rulings.md` の出力節是正) を land した。
  `worktree-rulings5-20260812` は第 5 束の裁定とユーザー指示により不採用で、fragment も取り込んで
  いない (branch は削除していない)。command の byte 数は 4,992 / 上限 5,000 で予算内。
  remaining: none
  base: 9e3722bd750eddd12667dbecfbd22712380938ba5c64cb45aa4bcddc7f3e0bc5
