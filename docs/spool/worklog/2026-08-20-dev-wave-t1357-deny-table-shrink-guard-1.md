---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1357-deny-table-shrink-guard
seq: 1
title: '[T-1357] DENY_TABLE の識別子削除を意味的 probe で検知する検査を追加した (コード + テスト + docs + 記録、branch worktree-dev-wave-t1357-deny-table-shrink-guard、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED 1 (既知残存、事前登録どおり)・MISMATCH 0)'
---

## 本文

- 2026-08-18 `/rulings` 全件第8回で「設計する」と裁定された [T-1357] を実装した。ratified 文言
  「禁止集合が縮んでいないことを意味で守る検査を設計する」は対象ファイルを名指ししておらず、
  起票本文の真の動機 (role 契約 pin の byte 同一性問題、`.claude/agents/coder-v4-autonomous-sort.md`
  側) とは別物である。本 `/dev-wave` 起動引数が `coder_effect_gate.py` の `DENY_TABLE` へ明示的に
  scope を narrow したため、段3 敵対相談レンズB がこの選定を検算し (real、ratified 文言と矛盾しない)、
  「完了報告は DENY_TABLE の局所成果に限定し role-contract pin/M6 全体の解決とは報告しない」ことを
  条件に採用した。真の M6 対象 (role adapter pin) は未着手のまま残る。
- 起動引数が引用した「`test_coder_effect_gate.py:151` が bounded loop 通過を明示的に固定している」は
  2026-08-15 時点の事実で、2026-08-18 commit `dc87fff7` (main 済み、[T-396] 裁定 B) が該当テストを
  削除済みだった。段3 レンズA/B・段6 レンズ1 が独立に `git show dc87fff7` で再検算し確認した。
  動機は T-396 §7 の DENY_TABLE 欠落項目表 + wave651 (2026-08-18) の一般教訓「pin は bytes 同一性
  しか証明しない」で再構成した。
- 段3 敵対相談レンズA が、`tools/mutation_harness.py` が実際に複数ファイル同時変異
  (`replacements` 複数指定) を過去 wave (t396.m6) で実行した実績を独立に発見し、
  「production + frozen literal の協調改変は harness の技術的射程内であり安易に scope 外と
  決めつけてはならない」と警告した。段4 裁定 ({{D:deny-table-shrink-guard}}) は、真の M6 対象
  (role-contract pin) が別途 scope 外のままであることと絶対規律5 (盛らない) を理由に、この協調改変を
  意図的な既知残存として scope 外に据えた上で、変異 t1357.m6 として実際に登録・実測し SURVIVED を
  確認した (隠さず記録)。
- 段6 敵対レビュー・レンズ1 が、実装済みの AST 自己参照防止 meta-test に2つの回避経路
  (最初の代入だけ検査し後続の再代入を見逃す、denylist 経由の別名参照が素通りする) を発見した。
  fix で denylist を allowlist (許可される Name は `"frozenset"` のみ) へ設計変更し、単一代入の
  強制を追加して解消した。焦点再レビューが解消と非破壊性 (155 passed) を確認した。
- 段6 レンズ2 が、総数96 sanity check のおかげで identifier 2箇所だけの中途半端な協調改変は
  むしろ検知されることを発見し、M6 (SURVIVED が正しい結果) の正確な境界を明確化した
  (production・frozen literal・総数96→95 の3箇所すべてを揃えたときだけ SURVIVED)。
- 変異matrix本走 (6件) は全件が事前登録どおり一致した (baseline 155 passed、M1〜M5 は各1 node
  だけ KILLED、M6 は 0 node で SURVIVED)。DW-M08 (テスト強化だけの wave の新旧比較義務) に従い、
  変更前 (旧) test_coder_effect_gate.py を一時的に書き戻し M1〜M5 の production 変異5件を同時適用
  して実走したところ 57 passed / 0 failed であり、旧テスト群がこれらの削除をすべて無検知だった
  ことを実測確認した (`git checkout --` で byte 一致復元、詳細は insight README §5)。
- 詳細な段1-6 の記録は `output/insights/2026-08-20_t1357-deny-table-shrink-guard/` を参照。
- 受入全走: `verdict=child-green`、13642 passed / 96 skipped / 0 failed (215.21s)、red/flake ともに
  0件、`tested_tip=6cc2c398d4ed2a8283c6874c3933e4f5f876713a`
  (`tested_main=b8fceb8c52af622bf3a66cc23626b7cd5356ca8f` は受入投入前に自前 merge 済みで
  lease 内の追加 merge は不要だった)。

## 次の一手差分

### 完了

- [T-1357] `coder_effect_gate.py` の `DENY_TABLE` (5 category・96 identifier) から個別 identifier が
  黙って削除されても検知できなかった穴を、意味的 probe (全96件) + AST 自己参照防止 meta-test で
  塞いだ。production の受理/拒否集合は不変。真の M6 対象 (role-contract pin) は未着手のため、
  T-1357 全体ではなく DENY_TABLE 局所成果としての完了である。
  remaining: none
  base: c6d3fb780013776d29b5f53a5806e27c700cc721d14b5dfad06223c68efa5974
