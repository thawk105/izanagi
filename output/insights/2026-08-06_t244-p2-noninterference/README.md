# [T-244] P2 — critic 境界の候補識別子射影 (U-1〜U-3 実装 wave) の逐語

branch `worktree-dev-wave-t244-p2-noninterference`。実装 commit は `a506633e`、
受入を測った tip は `9b687e68` (main `7c2a2cf1` 取り込み) と `5fe11936` (main `7fa861a0` 取り込み)。

前 wave (2026-08-05、実装しない裁定) の逐語は
`output/insights/2026-08-05_t244-p2-noninterference/` にある。本 wave はその
裁定パッケージ U-1〜U-3 が確定したことを受けた実装 wave である。

## ファイル

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。前提実測 M1〜M6 を含む。**M2 の 1 点が段 2/3 で是正された** (下記) |
| `s2-plan.md` | 段 2 codex プラン (v1)。段 3 が複数の BLOCKER を出したため、そのままは採用していない |
| `s3-lensA.md` | 段 3 敵対レンズ A (恒真性・残余容量・正しさ防壁)。NO-GO |
| `s3-lensB.md` | 段 3 敵対レンズ B (全層被覆・整合・実行可能性)。NO-GO |
| `s4-adjudication.md` | **段 4 裁定 (正本)**。所見 19 件の real/refuted、名乗りの上限、必須是正 8 件、変異事前登録、裁定パッケージ V-1〜V-4 |
| `s6-reviewR1.md` | 段 6 敵対レビュー 1 (検査の実効性・正しさ防壁)。NO-GO、must-fix 5 |
| `s6-reviewR2.md` | 段 6 敵対レビュー 2 (整合・波及・後方互換)。NO-GO、must-fix 4 |
| `s6-refocus.md` | fix 後の焦点再レビュー。所見ごとの closed / partial / regressed 表 |
| `mutation-spec.json` | 変異 spec (期待 node 補正後の v2) |
| `mutation-ledger.json` | 変異本走の台帳。**19/19 KILLED、node 完全一致、SURVIVED 0** |
| `mutation-ledger-run1-erratum.json` | 初回走行の台帳。KILLED 9 / MISMATCH 10 / SURVIVED 0。**消さずに残す** |

## 親の誤りとして残すもの

1. **段 1 brief の M2 が 2 点誤っていた。** `critic/digest.py` の verify-abort 節を
   screening と誤記し、liveness `extra` の `build_attempt_id` /
   `build_admission_receipt_sha256` という識別子チャネル 2 本を棚卸しから落としていた。
   段 2 プランと段 3 レンズ B が独立に是正した。実装はレンズ B の棚卸しに従っている。
2. **段 4 裁定の 1 件を段 6 で撤回した。** 「対応する `BUILD_START` の無い非空候補 ID を
   例外で拒否する」と裁定したが、これは public な exploratory / custom drive 経路の
   受理集合を狭め、既存の `test_claude_transport.py` 3 件を `complete` → `partial` に落とした。
   親 brief の不変条件「現行の受理集合を狭めない」に反するため、
   **候補に依存しない固定 sentinel への射影**へ変更した。撤回の根拠は実測である。
3. **変異の期待 node 登録が 10 件で狭すぎた** (F87 の再発)。初回走行の MISMATCH 10 件は
   すべて「登録した node は実際に赤くなったが、他にも赤くなる node があった」であり、
   変異の見逃しではない。初回台帳を erratum として残し、実測どおりに再登録して再走した。

## 名乗りの上限 (段 4 決定 (3))

名乗ってよい: 8c critic recipient 境界の **campaign-local pseudonymization** (cap=1) /
宣言済み declassification を除いた **critic sink 等価性の regression 検査** (no-build 経路) /
auditor 開示の **自己申告 annotation** / **IR emitter・golden の変更検出 ID** (checkout 限定)。

名乗らない: origin-scope ID、non-interference、indistinguishability、P2 の充足・部分充足、
cap-lift、build 経路の閉鎖、proof chain 保全、U-1 / U-2 / U-3 の「完了」。

## 実測

| 対象 | 結果 |
|---|---|
| 焦点 9 file (fix 後) | 615 passed / 0 failed (request 892135.nqsv) |
| 変異 matrix | 19/19 KILLED、node 完全一致、SURVIVED 0 (固定 HEAD `9b687e68`) |
| 受入全走 (tip `9b687e68`) | 6681 passed / 20 skipped (request 892239.nqsv、1032.67s) |
| 受入全走 (tip `5fe11936`、land 直前) | **6702 passed / 20 skipped** (request 892302.nqsv、1034.75s) |

いずれも Pegasus 計算ノードで `tools/run_tests.py` 経由の dispatch により実測した。
