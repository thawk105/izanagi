---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: worktree-dev-wave-t2202-missing-population-caveats
seq: 1
title: [T-2202] 欠測 attempt を含む母集団から出た数値主張 23 箇所に、主張ごとの但し書きを付けた (docs + insight、branch worktree-dev-wave-t2202-missing-population-caveats、実装面 0・変異 matrix 免除)
---

## 本文

- ユーザー依頼は [T-2202] の実装 (D1529、裁定済み)。**単位は文書でなく「数値主張とその母集団」**とし、
  本題の但し書きだけを書き、gate・検査・台帳・一般化は足さなかった。対象は command 引数のとおり
  `docs/paper-story/` と材料レポート (insight README) で、`docs/paper-story/` は該当 0 件
  (段 3 が再帰・別表記込みで再実測)、実体は insight README 8 file と設計文書
  `docs/b10-multinode-formal-run-design.md` の 23 箇所だった。追加 163 行・削除 0 行の純挿入。

- **設計文書を対象に含めたのは親の仮定である。** 段 3 レンズ B は「引数の字義では対象外」と real
  判定したが、D1529 の理由節が名指しする「balanced 約 6 時間半」「約 25 時間」の担い手は
  設計文書だけなので含めた。除外を望むなら同文書の 5 箇所だけを戻せる。

- **形は「主張直後の blockquote」にした。** 段 2 plan は全 file を EOF 追記と起草したが、段 3
  レンズ B が「値を読んだ読み手が同じ節で但し書きに届かない」を最重要所見とし、親が採った。
  例外は a6 certification insight で、file 自身が「追記でのみ訂正」と宣言しているため EOF 節にした。
  verbatim の行番号参照は削除済み worktree の絶対 path を指す歴史記録で、tests / tools / hooks に
  対象 README の pin は無いことを実測した。

- **段 3 敵対 2 本 (母集団帰属・閉包 / 形・規律 7・参照・scope) と段 6 レビューが親と plan を
  合計 7 点で覆した。** (1) brief に無い `2026-09-02_t2191-verifier-parallel` insight と、
  road-and-balanced の 1.7-2.1 倍・3.1 倍の再掲、f241 insight の 13.7〜17.5 時間再掲が閉包漏れ。
  (2) brief の「road-and-balanced は表の『打ち切り』で開示済み」は退けられた。
  (3) plan が対象とした `16.90M / 1425.4 秒` は完了変種の値で欠測由来でない (refuted)。
  (4) **「24 反復」(road-and-balanced 2 箇所、設計文書 §4) は値の誤り** — 一次資料は read-heavy
  `verify_done=22` (legacy 4 + performance 18)。但し書きに「誤りのまま」と書き、訂正は起票に留めた。
  (5) **「5 時間 5 分」を request `965996` の壁時計と断定していた** — scheduler の Elapse は 20950 秒
  (約 5 時間 49 分) で、計測区間は現記録から確定できない。6 箇所を「判定不能」へ直した。
  (6) 旧誤値 (23 分・3.83 時間・3.1 倍) へ無限定の「無効ではない」を使わない。
  (7) 「287 / 197 反復」の完全性主張は plan が対象としたが、観測母集団そのものの数で派生値でなく
  表自身が打ち切りを開示しているとして親が対象外にした。

- **絶対規律 7 に従い、過去の値・判定は 1 行も書き換えていない。** 但し書きは「値を無効にしない・
  欠測を除いた再計算はしていない」を全箇所に含む。

- 受入・検査: `check_docs.py` 違反なし (編集前 `fbd10fd6c`、編集後 `1b7822110` + 本 diff)。
  `test_check_docs.py::test_real_repo_clean` 単独走は成長 hold (`docs_bytes`、opt-in なし) で
  1 skipped (request `977072.nqsv`)。三軸語走査 rc=0。受入全走は記録 commit 後に投入する
  (本エントリの時点では未実施)。結果は受入受領証を正とし、land がそれを読む。

- 一次資料: `output/insights/2026-09-04_t2202-missing-population-caveats/README.md`
  (段 1〜4・段 6 の逐語は同 `verbatim/`)。

## 次の一手差分

### 完了

- [T-2202] 欠測 attempt を含む母集団から出た数値主張 23 箇所 (insight README 8 file + 設計文書) に、
  主張ごとの但し書きを付けた。`docs/paper-story/` は該当 0 件。設計文書を対象に含めたのは親の仮定
  (除外なら 5 箇所を戻す)。scope 外の担い手は {{T:missing-population-caveat-ledgers}} に持ち越す。
  remaining: none
  base: 84d082b9fd8e340aeb95f0d03b586d94f71532b5c7dbff72bf96f7b63dd0a784

### 新規

- {{T:b10-read-heavy-24-iterations-erratum}} **P3・新規**: 「read-heavy の所要が 24 反復ぶん残っていた」
  「全 24 反復が certified」(`output/insights/2026-09-03_t1905-b10-road-and-balanced/README.md` 2 箇所、
  `docs/b10-multinode-formal-run-design.md` §4 blockquote) は値の誤りで、一次資料は
  `verify_done=22` (legacy 4 + performance 18)、表の本規模も 5+5+5+3 = 18。[T-2202] は但し書きで
  「誤りのまま」と明記したが訂正していない。追記訂正で直す (規律 7、削除 0 行)。あわせて
  「5 時間 5 分」の計測区間 (request `965996` の Elapse は 20950 秒) を一次資料から確定する。
- {{T:missing-population-caveat-ledgers}} **P3・ユーザー裁定待ち**: [T-2202] の対象外に残った同じ主張の
  担い手 — `docs/decisions.md` (D1480 / D1485 / D1489 / D1509 / D1554)、archive worklog
  (1186 / 1187 / 1189 / 1190 / 1197-1198 / 1211 / 1223) — に同じ但し書きを付けるか。台帳は
  追記 (新 D または H2 直後の blockquote) でしか書けない。付けないなら記録のみで終端する。
