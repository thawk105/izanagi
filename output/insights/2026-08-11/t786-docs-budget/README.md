# [T-786] docs 予算棚卸し wave — 逐語と変異台帳

wave branch = `worktree-dev-wave-t786-docs-budget`。base = main `c172b369` を取り込んだ `9d9b7021`。
実装 anchor commit = `c7cc0fd1`。

## 何をした wave か

`docs/dev-wave/**` の L1 / L1.5 / L2 単節予算と `.claude/commands/*.md` の byte 予算に対し、
意味等価な縮約で枠を作り、予算超過で滞留していた候補の入庫可否を一括で判定した。
**予算定数は 1 bytes も変更していない** ([T-127] の「上限を上げず空ける」)。

入庫 8 件 / 未入庫 6 件。未入庫分の審査結果と引き上げ可否は `verbatim/package.md` が正本。

## 実測 (親、計算ノード dispatch)

| 予算 | 開始 | 終了 | 上限 |
|---|---:|---:|---:|
| L1 unique footprint | 10,625 | 10,606 | 10,625 |
| L1.5 unique footprint | 9,554 | 9,564 | 9,566 |
| `DW-O09` (L2 単節) | 935 | 997 | 1,000 |
| `DW-O18` (L2 単節) | 615 | 733 | 1,000 |
| `.claude/commands/rulings.md` | 4,991 | 4,996 | 5,000 |
| `.claude/commands/dev-wave.md` | 9,497 | 9,498 | 9,500 |

縮約で空けた総量は 588 bytes (L1 3 箇所 49 / L1.5 12 箇所 213 / rulings 10 箇所 187 /
dev-wave command 5 箇所 139)。

## 変異 matrix

`mutation-spec.json` (sha256 `21c54a52...`) / `mutation-ledger.json`。
**6/6 KILLED、MISMATCH 0、SURVIVED 0。** repo_head = `c7cc0fd1`。

新設した `_check_dev_wave_waiter_consumer_pins` の 6 分岐を production 側で 1 つずつ潰し、
対応する negative control が赤になることを実測した。特に **M5 (打消し語検査を殺す) が
`decoy-optional` に殺された**ことが、この検査が「literal がそこにあるか」だけを見る恒真な
検査でないことの実証である (段 3 の 2 レンズが独立に指摘した恒真性への回答)。

期待 node は静的に完全集合を導出できた (needle 対応表と production 分岐が 1 対 1)。
先行の probe spec は 1 走もせず harness の preflight で停止したため (期待 node が
collection に不在)、無駄走行と erratum は発生していない。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief。**(P1) は誤りで、段 3 で撤回した**
- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lensA.md` — 段 3 レンズ A (安全義務の削除・弱化)。**判定 NO-GO、blocker 3 件**
- `verbatim/s3-lensB.md` — 段 3 レンズ B (恒真性と被覆層)
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/s5-impl-prompt.txt` / `s5-impl-out.md` — 段 5 実装子
- `verbatim/s6-fix-prompt.txt` / `s6-fix-out.md` — 段 6 fix 子
- `verbatim/package.md` — 入庫可否と引き上げ可否の審査結果 (裁定パッケージ)

## この wave で得た知見

1. **待ち手正本へ結線しても [T-757] / [T-738](c) は 0 bytes で解消しない。**
   `tools/dev_wave_wait.py` は今も `--pid` を受理し、pid-file が producer 自身の産出かを検証せず、
   `/proc` 不読時は starttime 照合なしの PID-only へ降格する (段 3 レンズ A の A-3)。
2. **縮約 wave では reflow も pin を壊す。** `DW-S06-C` の reasoning 文は行単位の exact 一致で、
   D2 巻き戻し構造の正規表現は `段 2 プラン前` を空白込み literal で見る。改行位置の変更だけで
   2 度 `check_docs` を赤にした。
3. **「余白 0 だから 1 件も入らない」は成り立たない。** 層合計の余白がゼロでも、L2 単節予算で
   完結する候補は既存 slack だけで入る ([T-784] は `DW-O09` を 935 → 997 にしただけで入った)。
4. **子の receipt が未採用でも作業物は tree に残る。** 段 6 の fix 子は出力完全 (`## 総括` あり)
   ながら `evidence_status=invalid` で未採用になった。親が実走と独立監査を経て採用した。
