# [T-665] + [T-662] 起動値の機械束縛 — 実装 wave の逐語

wave = `dev-wave-t665-t662-launch-binding-impl`
branch = `worktree-dev-wave-t665-t662-launch-binding-impl`
裁定正本 (設計 wave) = `output/insights/2026-08-08_t665-t662-launch-binding/package.md`

## 何が入ったか

dev-wave が起動する codex 子の **model は全段**、**effort は段 6 の review / focus** が
docs 権威から導出され、caller は指定できない。実効値との照合は全 `turn_context` の
`payload` だけを見る。権威は job ごとに snapshot し、起動時点の commit と節 digest を
receipt へ固定する。

## 中核証拠 — land する経路を wave 内で実際に使った

段 6 の敵対レビュー 2 本を `tools/dev_wave_codex.py` で起動した receipt (schema v3)。

```
stage=review  lane=null
requested_model=gpt-5.6-sol   requested_effort=high   effort_authority=docs
recorded_model=gpt-5.6-sol    recorded_effort=high    recorded_turn_context_count=1
authority_snapshot.authority_commit=3cd457a46d4be06f5891bcb069595f5f69c86594
authority_snapshot.sections = DW-O01 / DW-S06-A / DW-S06-C の各 sha256
outcome=accepted
```

`--model` も `--reasoning` も渡していない。

## この wave が実際に学んだこと

1. **変異だけが中核主張の未証明を暴いた。** 対象テスト 623 全緑・敵対レビュー 4 本通過の状態で、
   段 6 effort の派生を別値へ置換する変異が生存した。期待値を派生関数自身から取る循環が原因。
   詳細は `mutation-analysis.md`。
2. **文書化した起動 route が実行不能だった。** 静的レビュー 4 本では出ず、dogfood の実起動で出た。
3. **親の実測が 2 件間違っていた。** top-level fallback の不在と、retry の受理判定。
   どちらも段 3 / 段 6 のレンズが指摘し、親が裏取りして撤回した。
4. **docs 予算が設計を 2 度動かした。** L1 も L1.5 も残 0 の状態から、`DW-O01` を
   833 → 821 bytes に収めて発火する契約文を通した。

## ファイル

- `mutation-spec.json` / `mutation-ledger.json` — 変異 1 走目 (9 件)
- `mutation-spec-correction.json` / `mutation-ledger-correction.json` — 訂正再走 (5 件)
- `mutation-analysis.md` — 2 走の突き合わせと親の判定

段 1〜6 の子成果物 (brief、プラン、レンズ 2 本、レビュー 2 本、fix 3 巡、裁定) は
repo 外の `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t665-t662-launch-binding-impl/` にある。

## 実装しなかったもの (ユーザー再裁定へ返した)

段 7 の集合等価 gate と期待 job 台帳の freeze (R2(a))、canonical stage matrix の発行、
sandbox の規範化、段別 resource 上限と retry policy、model×effort capability の起動前検査、
段 3 lane の完全な非循環化、raw `codex exec` を実行面で拒否する hook 配線。
理由は worklog エントリと `s4-ruling.md` に書いた。
