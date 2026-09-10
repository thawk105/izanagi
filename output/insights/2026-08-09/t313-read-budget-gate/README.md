# [T-313] 常時読量 gate — dev-wave 逐語 (2026-08-09)

`authority: none` / `default_effect: no-state-change`

一次裁定 (worklog (140) = 2026-08-03 パッケージの択 1) の実装 wave。逐語は `verbatim/`、
ユーザーへ返す設計択一は `package.md`、変異の実測は `mutation-ledger.json`。
可変状態の正本は `docs/worklog.md` 末尾。

| ファイル | 段 | 内容 |
|---|---|---|
| `verbatim/s1-brief.md` | 1 | 親 brief。provisional 裁定 (P1)〜(P6)。成果主張が過大で段 6 が訂正 |
| `verbatim/s2-plan.md` | 2 | codex プラン起草 (read-only)。明示 U/C marker 方式 |
| `verbatim/s3-lensA.md` | 3 | 敵対レンズ A — 正しさ境界・受理集合・迂回路 (NO-GO) |
| `verbatim/s3-lensB.md` | 3 | 敵対レンズ B — 実効性・整合・費用対効果 (NO-GO) |
| `verbatim/s4-ruling.md` | 4 | 親の裁定。real/refuted 表、プラン v2、変異事前登録 M1〜M12 |
| `verbatim/s5-impl.md` | 5 | 実装子の完了報告 (Codex role=author) |
| `verbatim/s6-fix.md` | 6 | fix 1 巡目 (191 failed の分類と修復) |
| `verbatim/s6-revA.md` | 6 | 敵対レビュー A — 正しさ境界・迂回路 (NO-GO) |
| `verbatim/s6-revB.md` | 6 | 敵対レビュー B — テスト検出力・変異耐性 (NO-GO) |
| `verbatim/s6-fix2.md` | 6 | fix 2 巡目 (レビュー blocker 4 件) |
| `verbatim/s6-fix3.md` | 6 | fix 3 巡目 (負例 helper の anchor 一意化) |
| `verbatim/s6-refocus.md` | 6 | 焦点再レビュー。`DW-O16` の所見別対応表 (NO-GO) |
| `mutation-ledger.json` | 6 | 変異 matrix の台帳 (baseline PASSED / 12 変異 / SURVIVED 0) |

## この wave が確かめたこと

1. **一次裁定の「択 (1)」は 3 層すべてに現在値の上限を置く案である。** 裁定文の要約だけを読むと
   L1.5 (wave クラス依存層) の扱いが落ちる。指す先のパッケージ本文まで開いて確定させた。
2. **剪定述語は既に存在した。** 「発火実績 + 機械検査での義務代替」は
   `docs/skill-self-improvement.md` の routing 3 に逐語である。したがって本 wave は
   `docs/dev-wave/**` の予算を 1 byte も使わずに実装できた。
3. **実装後も予算で止まっている項目の大半は書けない。** 新 gate を通るのは L2 へ置ける 2 件だけで、
   L1/L1.5 側の項目は層上限に当たる。親 brief の「解放がここに集中」は過大だった。
4. **本 wave 以前から存在した欠陥を 1 件見つけた。** dispatch の範囲記法が注記や URL 内の
   `~` でも展開し、読んでいない中間節を読了済み edge として捏造していた。
5. **変異 matrix は SURVIVED 0。** ただし 4 件は過剰決定 (期待 node は発火したが他 node も落ちた) で、
   冗長 gate として単独変異の単一理由の証拠から外した。期待値を実測へ合わせる書き換えはしていない。

## この wave が閉じていないこと

- 参照 cell の完全 grammar 化 (`path 全文: section` で規範上の全冊読了を 1 節分としてしか計上できない)。
- 表外の自然言語による条件性の意味変更 ([T-316] の所有)。
- 新規 L2 節の admission control (受理上限が `20,191 + 1,000N` で N に上限がない)。
- 指標が unique footprint であって event 加重読量でないこと、L0 command / self doc /
  Codex skill が scope 外であること。
- 外部 supervisor が実際に `DW-CTX` を読む結線。
