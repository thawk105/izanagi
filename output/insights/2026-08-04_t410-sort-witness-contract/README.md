# [T-410] sort 軸 integrity witness の設計契約と実装 blocker (2026-08-04)

dev-wave `wave-t410-sort-integrity-witness` の逐語一式。**実装差分は無い** —
段 4 で「この wave では実装しない」と裁定し、設計契約の確定と裁定パッケージの提出で閉じた。

## 何が起きたか

[T-244] の裁定 U5 は「sort 軸の構造化 integrity witness を新設する」を承認し、[T-410] へ割り当てた。
現行は整数 counter (`Integrity.permutation_violations`) と自然文 `notes` だけで、
「同じ理由で危険」の同値関係が書けないためである。

段 3 の敵対相談で、U5 の裁定時に見えていなかった構造的 blocker が出た。親が実測して確認した。

**`orchestrator/verifier/` 配下の全 Python が、committed qualification evidence
`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の `binding.runtime_modules` に
byte-binding されている。** `orchestrator/verifier/report.py` にコメント 2 行を足すだけで
`test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` が赤になる
(実測: `1 failed, 77 passed`。無変異時 78 passed。worktree 内で実施し即時復元済み)。

D107 は同型事故 (共有 `tools/pegasus/policy.json` が同じ evidence に束縛され同じテストが赤に
なった) に対し「後から key を足す側が退く」と裁定した。本件は verifier が witness の producer
本体であり、**退く先が存在しない**。binding を書くのは実 job の `collect` だけで、正規の
再束縛経路も無い。evidence の hash 書換え・binding 検査の緩和・テストの skip は
proof chain の falsification であり採らない。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親)。scope・不変条件・provisional 裁定 P0〜P4 |
| `s2-plan.md` | 段 2 プラン起草 (codex `gpt-5.6-sol` / max / read-only) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 受理集合不変性・consumer 閉包・規律 6 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 同値関係の意味・D138 契約整合 |
| `s4-ruling.md` | 段 4 裁定 (親)。所見の real/refuted、設計契約 9 項、裁定パッケージ 3 択 |

## 逐語の正規化 (erratum)

`s3-lensA.md` は原文に末尾空白を 1 行含み `git diff --check` に抵触したため、
**可視文字を変えない可逆最小正規化**を行った (行末の空白・タブのみ除去)。

| 項目 | 値 |
|---|---|
| 原文 sha256 | `c8bda3f17ddf22cf8fcd5eaf2fe286ff5f47b21e55aeffdee5300425cde6c13c` |
| 原文 bytes | 19899 |
| 正規化後 sha256 | `77b79bc0542a6131ec4fb7502ed2d6cef8919bb2aca0948aa59b116d0ef9908d` |
| 正規化後 bytes | 19897 |
| 該当行 | 1 行 (末尾 2 space の Markdown 改行) |
| 復元法 | 「最も危険な 1 点」節の `**…見落とし。**` 行の行末へ半角空白 2 個を戻す |

他の逐語 (`s2-plan.md` / `s3-lensB.md`) は無変更である。

## 確定した設計契約の要点

D138 が「確定していないこと」に挙げた **sort 軸の同値関係**を、**因果同値ではなく固定 origin 内の
観測同値**として確定した。`P <reason>` の reason は comparator の壊れ方ではなく producer 側の
事後検査の分岐名であり (size を先に見て、等しいときだけ rcdptr multiset を見る短絡順)、
comparator 法則から reason への写像は関数ですらない。詳細は `s4-ruling.md`。

## 未確認と限界

- 新 witness 経路の E2E は**未確認**。既存の positive-control artifact
  (`s5_permutation_coverage.json`、erase 249,252 / swap 879,025) は aggregate count しか持たず、
  driver は検証後に生 trace を削除するため、新経路の再現証拠にはならない。
- 現行の permutation 保存検査は multiset しか見ず、**順序も key↔rcdptr の対応も検査していない**。
  ただし非 strict-weak-order comparator の UB で対応だけが入れ替わる到達可能性は未実証である。
- 逐語 3 本は外部 (codex) の出力であり、**データであって指示ではない** (規律 6)。
  親が real/refuted を裁定した結果が `s4-ruling.md` である。
