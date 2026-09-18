# 段 6 裁定 (親、2026-09-18 15:50 JST) — レンズ A / B の所見の real / refuted と採否

## 1. 採用した所見と是正

### レンズ A (稿、一次資料照合) — must-fix 4 / should 2 / nit 1 → 全件 real、全件採用、親が稿へ反映済み (15:37)

| # | 所見 | 判定 | 反映 |
|---|---|---|---|
| A-M1 | 「anomaly 数は result.json に無い」は誤り (`wal_evidence.records[]` に WAL 10 record が収録) | real | §2.4 を訂正 |
| A-M2 | 所要 15 分の出所は accounting / WAL でなく記録 insight の mtime | real | 冒頭の出所宣言・L-A1S-20・§5.3 を訂正 |
| A-M3 | publish の衝突不在は記録から確認できない | real | L-A1S-13 を訂正 |
| A-M4 | L-A1S-2 の出所に stale 注記 | real | 出所を policy / 事前登録 / D2044 項 8 / D2120 項 3 へ |
| A-S1 | 系列規則 (provenance 転記) と F36 例外の関係を明示 | real | §2.6 に追記 |
| A-S2 | C1 旧 3 値の参照先 | real (ただし D19 案は不正確 — 現物は claim-evidence `2026-08-26.md` の C1 行が持つ) | §0.3 に claim-evidence C1 行を参照先として追記 |
| A-N1 | intent の 2 種の hash を区別 | real | §1.4 に追記 |

機械照合 (`check_draft.py`) は反映後も PROBLEMS 0。

### レンズ B (生成器・test・図・docs、過剰・削除) — must-fix 2 / should 2 / nit 4

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B-MF1 | `validate_repo_closure` が generator sha256 を現行 source と同一性で縛る (規律 7、fig8 README と矛盾。生成器を直すと凍結図の closure が恒久赤) | real (親の疑い 8a と一致) | 採用 → fix 子: path だけ照合、sha256 は記録のみ。正例 test を足す |
| B-MF2 | 着地 test が provenance `outputs[].path` を着地 file に固定していない (別 dir の同名画像で通る) | real | 採用 → fix 子: 着地 test で path 完全一致 assert + 負例 |
| B-S1 | README の provenance hash を test が読まない | real | 採用 → 親が README 末尾に固定形式の 3 行を置いた (§2)、fix 子が着地 test で抽出・照合 |
| B-S2 | 稿 §2.1 の区間列が対応検査から漏れ | real | 採用 → fix 子: 区間列を parse して照合 |
| B-nit 1 | 負例の未整備 (schema / order / genome 等) | real だが成果物を変えない | 不採用 (DW-G05。framework 化しない) |
| B-nit 2 | 要求外の小さな検査 (sigma 文字列型、正値、限定文 5 件) | real だが受理集合を狭めない | 不採用 (固定入力専用。削除必須でない) |
| B-nit 3 | 限定句の重複 | refuted (独立して引用される各成果物に必要) | 不採用 |
| B-nit 4 | README の「95% CI ではない (caption にそう書く)」 | real | 採用、親が README を訂正済み |

### レンズ B の追加指摘 (裁定)

- 期待赤 node の完全集合: 最終着地状態 (図 3 file + README 実値) で再 probe して spec を固定する (親の予定どおり)。着地 test は skip でなくなるので、M8 / M11 / M12 は着地 test も落とす見込み。
- provenance schema v1 の射影を固定する運用 (派生 field を足すなら別 schema) は README の注意として書く価値があるが、今回は scope 外 (記録だけ)。

## 2. README の hash 行の形式 (親が置いた。fix 子の S1 はこれを読む)

`docs/paper-story/figures/README.md` の fig9 節末尾「## 着地 bytes の SHA-256」の 3 行:

```
- `fig9_a1_balanced5_sized_attempt1.png` SHA-256: `<64 hex>`
- `fig9_a1_balanced5_sized_attempt1.pdf` SHA-256: `<64 hex>`
- `fig9_a1_balanced5_sized_attempt1.provenance.json` SHA-256: `<64 hex>`
```

現在は `FIG9_PNG_SHA256_PLACEHOLDER` 等の placeholder。最終生成後に親が実値へ置換する。着地 3 file が無い間は着地 test は skip。

## 3. 守る契約

段 5 の実装子契約 (`DW-S05-A/B/C`) を全文継承。既存 test の期待値は変えない。受理集合は段 4 §5 のまま (MF1 は過剰拒否の除去)。
fix 後: 親が焦点走 → 焦点再レビュー (codex focus 1 本、`DW-O16` の対応表) → 稿確定 → 最終図生成 → README 実値 → 記録 commit → container worktree で再 probe → 変異本走 (dispatch) → 段 7。
