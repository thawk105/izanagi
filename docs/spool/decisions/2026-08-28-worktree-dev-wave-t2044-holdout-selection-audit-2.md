---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: worktree-dev-wave-t2044-holdout-selection-audit
seq: 2
---

## {{D:t2044-holdout-selection-claim-cap}}. 測定前固定を証明できない floor-backed 主張は non-certifying を上限とする

**決定 (ユーザー指示の記録):** 一回性撤去後、適格な複数の fresh floor result から値を見て使用 result を選ぶ経路を防ぐ実装は無い。測定前固定の既存 proof が示されない floor-backed candidate、再凍結、oracle / 8c 公開物、論文主張は advisory / non-certifying を上限とする。

同一 oracle / 8c judge 入力を固定したとき floor 数値が winner / conclusion の計算入力でない、という狭い非干渉は別に維持する。現 commit の official / budget blocker、create-only、ratification、source hash、`eligible_for_refreeze` を測定前固定の証拠へ昇格させない。規律 2 は緩めない。

**理由:**
- official / budget blocker は A/B を一律拒否するだけで、使用 result を値を見る前に固定しない。
- candidate は caller 指定 `--floor-result` から生成され、事前固定 identity との equality predicate が無い。
- candidate path/hash を ratified g1 へ自動束縛する参照は 0 件で、ratified `floor` と `floor_source.result.floors` の投影一致も検査しない。
- source path/hash は選んだ B を正しく名指しできるが、その名指しが値を見る前だったことを証明しない。
- D893 は同一試行識別子の複製を対象とし、異なる fresh A/B は D1124 の禁止面である。T-469 の機構も未実装である。

**却下した選択肢:**
- 現在到達不能なので守られていると記録する — blocker 解消後の選択経路を防がない。
- create-only candidate を選択防壁と数える — 初回に B を選んだ後の上書きだけを止める。
- floor 数値が oracle / 8c の直接入力でないことから強い certified claim 全体を許す — artifact provenance、admission、publish 可否と測定前固定の欠落を落とす。
- 本 wave で新しい guardrail、署名、台帳、nonce、one-shot 代替を実装する — ユーザー指定 scope 外で、将来実装には D95 Codex author が必要である。
