# T-173 段6 round 3 裁定

## 結論

focused re-review の NO-GO を受理する。round 2 の parser 改良は既知の raw `##` 形には効いたが、
CommonMark 同値見出しと未検査 H2 を含む受理集合を安全に閉じられていない。これ以上 parser を拡張せず、
Codex Skill と共有 cleanup command の raw bytes 全体を SHA-256 で固定する。

## accepted findings

- Skill / command の hand-written Markdown parser は削除し、whole-file digest 契約へ置換する。
- metadata の exact text、regular-file、UTF-8、closure、interface、budget 検査は維持する。
- 1 byte 変更、追加 H2、closing-hash / leading-space / setext H2、無効 backtick info、
  metadata policy 変更を恒久 control とする。
- parameter registry と duplicated clause fixture は撤去し、独立 literal digest と明示的な named tests に縮約する。
- legal rewrap も自動受理せず、意図的な digest 更新と review を要求する。

## round 上限

これは最終 fix round（3/3）である。修正後に read-only focused re-review を一度行うが、
新しい fix round は開始しない。残件があれば親が mutation / acceptance 結果と併せて最終裁定する。
