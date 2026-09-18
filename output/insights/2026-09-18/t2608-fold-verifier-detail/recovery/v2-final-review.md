## 総括

GO、must-fix 0件。固定HEAD `063a743d61dcc3707010fb714f677caccddcb167`への静的レビューのみ・未実走。受入・land成功の判定ではない。前回未受理レビューの結論は使用していない。

## 所見

real：なし。最小修正：不要。

refuted：

- **F266が残る疑い** — `tools/dev_waves/git_state.py:893` の親選択と、同`:759` の拒否条件を全7コミットに適用して確認。選択された差分に `M docs/spool/FOLDED.md`・fragment削除はない。
- **縮約で安全義務が落ちる疑い** — `docs/dev-wave/core.md:37` に次段停止・調査修正再検証・正式停止条件・迂回禁止を保持。同`:125` の受入結果固定も不変。`docs/dev-wave/operations.md:174` は再照合・ff-only・foldを同じ協調lock内に置き、同`:178` のpostcondition failure停止、同`:179` のrebase/force等禁止も保持している。規律2・verifier・checkerへの変更はない。

## 対応表

| 対象 | 判定 | 証拠 |
|---|---|---|
| F266：一括mergeの親列 | closed | `9c0300993` は順に `b2037abfa / 2b1015486 / 2975fcf6d`。trusted親はmainだけ。 |
| F266：全landed候補区間の親差分 | closed | 下表の全差分を既存実装と同じ `--no-renames` で確認。拒否署名0件。 |
| F266：旧失敗履歴の除外 | closed | `ceb258ff7` は固定HEADの祖先でない。旧mergeの両親はtrusted外で、第二親との差分にFOLDED変更があることも確認。 |
| F266：既存対処への接続 | closed | `operations.md:180`、再発fragment `docs/spool/failures/2026-09-18-dev-wave-t2608-fold-verifier-detail-2.md:13`。 |
| F946：修復と次wave、再試行不可と修復不可の区別 | closed | `core.md:38` と再発fragment同`:20`。許可範囲・正式停止条件を残した明確化。 |
| F946：経緯の記録 | closed | `docs/spool/worklog/2026-09-18-dev-wave-t2608-fold-verifier-detail-1.md:71` に旧受入・land拒否・継続・修復を区別して記録。 |
| 新tipの受入・land完遂 | partial | 本レビューでは未実走。履歴上の拒否原因解消までの判定。 |

全区間の選択差分：

| commit | 比較元の親 | 変更path数 |
|---|---|---:|
| `2975fcf6d` | `c8e8dc06f` | 2 |
| `08aa6cf99` | `c8e8dc06f` | 2 |
| `ad1f68a8a` | `ed4363204` | 2 |
| `9180c3c83` | `ad1f68a8a` | 17 |
| `2b1015486` | `e43f6d8da` | 19 |
| `9c0300993` | `b2037abfa` | 32 |
| `063a743d6` | `9c0300993` | 4 |

旧受入との差分の限界：`tools/spool_fold.py` と `orchestrator/tests/test_spool_fold.py` は `7a144e023` とblob一致。残る差分は自己改善4文書、既存資料5ファイルの末尾空白正規化、復元情報の追加。旧受入の25134 passed / 69 skippedは新履歴の受入証拠にはならない。文書予算checkerは未実走であり、その緑も本レビューでは主張しない。