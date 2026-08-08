# 到達不能監査への repo 外同一実体抑止 (wave dangling-audit-offrepo-authority)

2026-08-08 のユーザー裁定 (b)+(c) を実装した wave の一次資料。裁定の原文控えは repo 外
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md`。

## 逐語

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (段 3・段 4 の指摘で 1 箇所訂正済み) |
| `s2-plan.md` | 段 2 プラン (codex gpt-5.6-sol, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 A = 正しさ境界と masking (sol, max)。NO-GO、blocker 4 |
| `s3-lensB.md` | 段 3 敵対相談 B = 整合と実効性 (luna, max)。NO-GO、blocker 1 |
| `s4-adjudication.md` | 段 4 裁定・plan v2・変異事前登録 M01〜M10 |
| `s5-impl.md` | 段 5 実装子の報告 (sol, high) |
| `s6-reviewR1.md` | 段 6 敵対レビュー R1 = 述語の正しさ (sol, high)。NO-GO、blocker 2 |
| `s6-reviewR2.md` | 段 6 敵対レビュー R2 = 検出力と全層被覆 (luna, high)。NO-GO、blocker 4 |
| `s6fix.md` `s6fix2.md` `s6fix3.md` | 段 6 fix 3 巡の報告 |

## 変異台帳 2 走

`mutation-spec-v1.json` / `mutation-ledger-v1.json` が 1 走目、`-v2` が本走。
どちらも anchor commit は `fd97fe93`、runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_audit_dangling_commits.py -q -rf`。

- **1 走目 = 8 KILLED / 2 MISMATCH / SURVIVED 0** (330 秒)。MISMATCH は M07 と M10 で、
  いずれも**実測 node が事前登録の上位集合** (期待側の欠落ゼロ) だった。親の事前登録が狭すぎた
  ことによるもので、実装の欠陥ではない。**erratum として消さずに残す** (`DW-M02`)。
- **本走 = 10 KILLED / 0 MISMATCH / 0 SURVIVED / 0 TIMEOUT** (625 秒)、baseline PASSED。

### 受理集合 kill と diagnostic pin の区別 (`DW-M08`)

| ID | 変異 | 区分 |
|---|---|---|
| M01 | landed 参照の連言を落とし bytes 一致だけで抑止 | 受理集合 kill |
| M02 | bytes 比較 (hash + chunk の両層) を落とす | 受理集合 kill |
| M03 | 実行 mode 一致検査を落とす (両層) | 受理集合 kill |
| M04 | 探索根が worktree の祖先でも受理 | 受理集合 kill |
| M05 | CLI root 指定時に env root も併合 | 受理集合 kill |
| M06 | wrapper が `excluded_prefixes` を既定へ握り潰す | 受理集合 kill |
| M07 | 抑止節の出力を消す (findings と rc は不変) | **diagnostic sensitivity pin** |
| M08 | 到達不能側の mode 検査を緩め symlink も blob 扱い | 受理集合 kill |
| M09 | 探索未実施の表示を消す (findings と rc は不変) | **diagnostic sensitivity pin** |
| M10 | 抑止述語を恒偽にする (過剰報告の正例) | 受理集合 kill |

M07 / M09 を kill と数えないのは、受理集合を変えずに構造化シグナルだけを消す変異だからである。
段 6 レビュー R2 が同じ区別を求め、親が実走で確定した。

## 実 repo 実測 (段 5 後、anchor `42419ebe` 時点)

- 探索根なし: **8 commit / 28 (commit,path) 対**、wall 14.1 秒。
- 探索根あり (`--offrepo-root /work/1/SFC/tanab/dev-wave-jobs`):
  **抑止 2 対 / 残 6 commit / 26 対 / bytes 一致だが landed 参照なしの注記 11 対**、wall 13.8 秒。
- 抑止された 2 対はどちらも [T-574] の `probe_g2_consumers.py` で、裁定が「構造的な偽陽性」と
  名指しした対象そのものである。[T-409] と [T-213] の残骸は裁定 (c) のとおり報告に残り、gc を待つ。
