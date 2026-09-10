# [T-287] checkpoint 値チャネル wave の逐語資料

branch `worktree-dev-wave-t287-checkpoint-values`、実装 commit `02a5cf9`、記録 commit `b4a70cb`。
base main = `3d24878`。

## この directory の中身

| file | 内容 |
|---|---|
| `adjudication-package.md` | 裁定パッケージ (残余 4 件 + 親 brief の訂正 5 点)。**ユーザー裁定待ち** |
| `mutation-spec.json` | 事前登録変異 M1〜M7 (`DW-M01`)。spec sha256 = `5681bd653546fbde479a74d7c8235d71c3bdfaf5a8272c0d72aff9923ec20c70` |
| `mutation-ledger.json` | 本走台帳。**7/7 KILLED、MISMATCH 0、SURVIVED 0、baseline PASSED** |
| `mutation-ledger-v1-erratum.json` | 初回本走の erratum (`DW-M02`)。M1 が MISMATCH で停止した記録 |

## 変異 matrix の結果

| ID | 変異 | 種別 | 実測赤 node 数 | 判定 |
|---|---|---|---|---|
| M1 | `magnitude` から `large` を削除 | kill (受理集合の**縮小** = 過剰拒否の正例) | 4 | KILLED |
| M2 | membership 検査を恒真化 | kill (拡大) | 4 | KILLED |
| M3 | `type(value) is str` を削除 | diagnostic sensitivity pin | 2 | KILLED |
| M4 | `result` に `"ok"` を追加 | kill (拡大) | 4 | KILLED |
| M5 | `direction` に `"grow"` を追加 | kill (拡大) | 5 | KILLED |
| M6 | **末尾 entry だけ検査**する | kill (拡大) | 2 | KILLED |
| M7 | 許可値リストを `result` 集合に固定 | kill (診断の虚偽) | 1 | KILLED |

M6 / M7 は段 6 の焦点再レビューが「fix 1 巡目の後も生存する」と静的に指摘した変異である。
2 巡目 fix で閉じ、本走で実測 kill を確認した。

## 変異事前登録の 2 度の再照準 (`DW-M01` / F28、`DW-M02`)

**初回登録の M1 は成立しなかった。** 経緯を残す。

1. **1 回目 (表記ゆれ)** — M1 = `result` から `"rejected"` を削除。本走で mutant 自体は kill された
   (rc=1、期待 8 node がすべて赤) が、`status=MISMATCH` で停止した。原因は
   `test_drive_iteration_checkpoint_survives_across_calls` 等 3 node が記録側で **`@real-repo`
   接尾辞付き**になることを事前登録が知らなかったことだけである (`DW-M08` の「突き合わせ前に
   同じ形式へ正規化する」= F33 と同型)。
2. **2 回目 (harness が表現できない)** — 接尾辞を付けて再登録したところ、今度は preflight が
   「期待 node が pytest collection に実在しない」で停止した。**`tools/mutation_harness.py` は
   preflight で素の pytest node id を要求し、突き合わせで `@real-repo` 付きを観測する。**
   両者は同時に満たせないため、real-repo 直列化対象 node を kill 集合に含む変異は
   **原理的に登録できない**。これは harness 側の穴であり、別タスクとして起票した。
3. **再照準** — `DW-M01` の「確認できなければ登録せず実効 gate へ再照準する」と `DW-M03` の
   「過剰決定なら単一理由へ差し替える」に従い、real-repo node を巻き込まない
   **`magnitude` の `large` 削除**へ差し替えた。期待 node は推測せず、
   一時変異の注入 → 焦点 3 file 実走 → 復元 (`DW-O19`) で **実測**して確定した (4 node)。
   復元後は `git diff HEAD` が 0 行であることを確認済み。

## 受入実測 (すべて Pegasus gen_S 計算ノード)

| 検査 | 結果 | request |
|---|---|---|
| 焦点 `test_p3_s4_loop.py` (fix 前) | 69 passed | 882046.nqsv |
| 受入全走 (fix 前) | 5390 passed / 19 skipped | 882047.nqsv |
| 焦点 3 file (fix 2 巡後) | 154 passed | 882069.nqsv |
| 受入全走 (fix 後) | 5393 passed / 19 skipped | 882064.nqsv |
| M1 再照準の赤 node 実測 | 4 failed / 150 passed | 882078.nqsv |
| `tools/check_docs.py` | rc=0、違反なし | (login node、機械検査のみ) |
| `tools/check_ai_provenance.py` full | rc=0 | 実装 commit 後 |

codex 実装子は Pegasus ログインノード規律に従い pytest を実走せず、緑の主張もしなかった。
**実測はすべて親が計算ノードで行った。**
