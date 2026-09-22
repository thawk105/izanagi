単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 焦点再レビュー (B4 partial の根拠と具体的な抜け): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-focus.md
- 段 6 裁定 (B4 の採用と fix の制約): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s6-ruling.md
- 前段 fix2 の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-fix2.md
- 段 5 author の prompt (実装子契約。fix はこれを全文継承する): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-prompt.md
- 段 4 裁定 (R9 の規模上限): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md

## あなたの役割と権限

あなたは Codex の fix 子である。s5-author-prompt.md の「あなたの役割と権限」「検査と報告の義務」をすべて継承する。今回編集してよいのは
`orchestrator/tests/test_verifier.py` の新規 v3 試験と helper (段 5 以降に足した部分) だけ。production と既存試験は 1 byte も変えない。
docs・commit・branch 操作はしない。試験の期待を緩めない。R9 (test_verifier.py の差分が wave 起点から 800 行以内) を守る。

## 直すこと (B4 の残り)

`_v3_paths` の packed / tuple の肯定 assertion が `not isinstance(parsed, _LegacyTrace)` の枝の内側にあり、parser が予期せず legacy を
返すと検査全体が飛ばされる。**compact を期待する設定 (通常 fixture の packed / tuple) では、まず parser の戻り値が compact
(`_CompactTrace`) であることを肯定 assertion し、その後に packed / tuple の表現を確かめる**。意図的に overflow で legacy へ落ちる fixture
(`expect_packed=False` などで明示している試験) だけは legacy を許す。この区別は試験側で明示の引数にし、既定は「compact を要求」にする。

確かめ方: 修正後、production を変えずに「v3 の file を常に legacy へ落とす」退行 (例: `_parse_file_to_columns` で v3 の場合に
`_ParsedFileNeedsLegacy` を返す) を**一時的に**手元で入れて、新規 v3 試験の少なくとも 1 本が赤になることを確かめ、必ず元に戻す
(戻したことを `git diff -- orchestrator/verifier` が空であることで確かめて報告に書く)。

## 実走の義務

`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` (素の自走 runner) を最終版で実際に走らせ、結果を逐語で報告する。全件緑になるまで直す。
上の一時的な退行を入れた状態の自走結果 (赤になった試験名) も報告する。pytest の直接起動と run_tests.py は使えないので試さなくてよい。

## 出力形式

Markdown。「変更 (file:line と差分行数、R9 の累計)」「B4 の充足 (file:line)」「一時退行での確認 (赤になった試験名、復元の確認)」
「実走結果 (逐語)」「未解決」、最後に `## 総括` (5〜10 行)。
