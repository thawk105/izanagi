# [T-677] 失敗診断の中継到達を機械検査する — 一次資料

wave: `dev-wave-t677-relay-reach` / branch: `worktree-dev-wave-t677-relay-reach`
実装 commit: `575fb77a` / 受入済み tip: `8093445e` (受入時 main `1fb283a4`)

## 何をしたか

受入全走を計算ノードへ dispatch すると、親へ中継されるのは子 stdout/stderr の末尾 64 KiB
だけである。失敗が多い全走では失敗診断の本体が中継から丸ごと消える。pytest セッションの
終端に bounded な失敗診断ダイジェストを出し、その到達を機械検査で固定した。

編集面は `orchestrator/tests/conftest.py` と新規
`orchestrator/tests/test_pytest_failure_digest.py` の 2 本のみ。dispatcher・production・
`tools/run_tests.py`・`pytest.ini` はいずれも無編集。

## 実測 (前提。既存 artifact から取得、repo 無改変)

| 走行 | child stdout | 中継から欠落 |
|---|---|---|
| 緑の全走 | 8,808 bytes | 4,712 bytes (成功中継は 4 KiB 枠) |
| **110 failed の全走** | **523,987 bytes** | **458,452 bytes (87.5%)** |
| 他 5 例 | 95,214〜213,154 bytes | 29,678〜147,618 bytes |

110 failed の走行では `=== FAILURES ===` の見出しごと消え、末尾の
`short test summary info` と最終行だけが残っていた。

**注意:** これは generic な切り詰めの再現であって、launcher 固有の診断消失の実測ではない。
当該ログに `test_codex_worker_launch` は含まれない。

## 保証の範囲

**pytest セッションが完走した場合に限る。** 次は pytest hook の到達範囲外であり、
裁定パッケージとして起票した。

- xdist worker の internal error / pre-item crash (report が生成されない)
- SIGKILL・OOM kill・PBS walltime 打ち切り・pytest 起動前の rc=16
- dispatch の中継が best-effort であること (BrokenPipe・relay error を握る)

## 検証

- 受入全走: **7629 passed, 20 skipped** (22 分 55 秒、tip `8093445e`)
- 変異 matrix (すべて diagnostic sensitivity pin。受理集合は変えない):
  - Arm A2 (新テストあり): M1〜M7 **全 KILLED**
  - Arm B (新テスト抜き): M1〜M7 **全 SURVIVED**
  - → 7 変異すべてを新テストだけが検出する (DW-M08 の帰属)
- 段 6: 敵対レビュー 2 本 → fix 3 巡 (上限) → 焦点再レビュー

## ファイル

| path | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (実測・provisional 裁定 P1〜P5) |
| `s2-plan.md` | 段 2 プラン (親の P2 を反証し `pytest_unconfigure` を採用) |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、scope、変異事前登録) |
| `s6-fix-rulings.md` | fix 1 巡目 F1〜F10 |
| `s6-fix2-rulings.md` | fix 2 巡目 F11 (in-tree 一時ファイル) |
| `s6-fix3-rulings.md` | fix 3 巡目 F12〜F15 (恒真検査の撤去ほか) |
| `mutation-spec-A2.json` / `mutation-spec-B.json` | 変異 spec (両 arm) |
| `mutation-ledger-A.json` | Arm A 初回 (期待 node が実測より狭く MISMATCH) |
| `mutation-ledger-A2.json` / `mutation-ledger-B.json` | 確定台帳 |
| `verbatim/` | codex 子の出力そのまま (敵対 2 + 実装 + レビュー 2 + fix 3 + 再レビュー) |
