# 段 6 レビュー所見の裁定 (親、2026-09-19 23:19 JST)

一次資料: review-a-out.md (正しさ境界)、review-b-out.md (過剰・削除・実効性)、tmp/focus1-summary.md。

| # | 出所 | 所見 | 裁定 | 処置 |
|---|---|---|---|---|
| A1/B1 | must-fix | 新正例 `test_emitter_memo_copy_matches_fresh_build` に `@in_sealed_fixture_process` が無く、sealed build session の単一 OS thread 要求で失敗 (focus1 で実測) | **real** (親の裁定 §2 項 8 の指示ミス) | fix-U1: decorator を付ける |
| A2 | must-fix | `_emitter_memo_parent` の名前による祖先探索は、`--basetemp=/tmp/pytest-of-u/pytest-7/run-a` のような外側祖先を持つ配置で別 session の memo を拾う (構築側変異を隠しうる) | **real** (稀な配置だが session 境界の保証が無い) | fix-U1: `pytest-N` から `tmp_path` までの相対 path が `<test dir>` か `popen-gw<数字>/<test dir>` の標準形 (深さ ≤ 2) のときだけ採用し、それ以外は memo を迂回。key に `PYTEST_XDIST_TESTRUNUID` (あれば) を加える |
| A3 | must-fix | 新正例が実 repo の tracked 入力を fresh/seed/rebuild で繰返し読む。登録簿に無い。入力が走行中に変わると比較が壊れる | **should へ格下げ** | 読む入力は tracked で走行中不変 (既存 builder 利用 90 node も同じ未登録の読取り)。設計変更 (入力の共有取得) は正例 1 本のために過剰。B3 の 5→4 回で読取り回数は減る。報告に「未登録・tracked 入力の読取り」と明記 |
| A4/B4 | nit/should | 4 象限 test (R:1382/1403) は dispatch 枝も `_REPO` 非依存 (preflight 3 本 stub、dispatcher Mock、記録開始に到達しない) で全枝へ fixture を付けられる。約 42 s (単独) の追加削減 | **real** | fix-U3R: `test_login_headroom_and_queue_four_quadrants` に `_small_login_repo` を付ける (4 node)。R:477 (記録開始経路) と R:2314 (fingerprint 非到達) は除外を維持 |
| B2 | must-fix | focus1 (9 file 同走) と段 1 (file 単独) の差を「保守的」と断定できない | **real** (報告の言い方) | 報告では観測差とだけ書き、削減秒は A/B (同 job・同条件) で出す。focus1-summary.md の注記を訂正 |
| B3 | should | 正例の 5 回構築は 4 回 (fresh / seed / hit / marker 破壊後の再構築) で足りる。tracked file ごとの `git cat-file blob` は HEAD・index entries・worktree bytes の比較と重複 | **real** | fix-U1: 最後の `rebuilt-copy` を落とし 4 回に、`cat-file` を落とす、`str(g1)`/`str(topology)` は直接比較 |
| B5 | should | A/B script のコメントに `--basetemp` が残る。変異 harness は同 repo へ注入・復元 (走ごと fresh worktree ではない) だが、走ごとに新 pytest session なので memo は fresh | **real** | 親: script コメント訂正。報告に「走ごと新 session (pytest-N 採番) で memo fresh、worktree は同一」と正確に書く。A/B の集計は全走 rc を確認 |
| B6 | nit | metadata の `copied_files`/`copied_bytes` は恒常処理に不要 | **real** | fix-U1: 削除 |
| A(表)/B7 | — | author 報告の AST・caller 数は現物と一致 | 確認 | — |

fix 単位: fix-U1 (F のみ、author 木 awtt-u1-author)、fix-U3R (R のみ、author 木 awtt-u3r-author)。所有は素集合。既存 test の期待値は変えない。
