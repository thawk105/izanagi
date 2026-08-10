判定は **NO-GO**。blocker は 5 件です。pytest・テストスイートは実走しておらず、文書・コード・Git blob・SHA-256 の静的照合だけを行いました。

## Blocker

1. source study の束縛が閉じていない

[publication-core.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:30) は base core だけを pin していますが、同文書は追補 A の `a10`・`a11`・`a13` を規範的に参照しています。source core 自身も [preregistration.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:17) で core 単独では不完結としています。

さらに無効化対象が §§3・5・7・16 だけで、適格 cluster や admission を動かしうる §§9・12・15 と追補 A の変更を覆いません。合成後 digest を pin しない判断自体は妥当でも、代替の依存閉包が不足しています。

**成果物影響:** 同じ公表 core から、異なる `J`・適格 cluster 集合・source binding・台帳参照を受理でき、固定表と試行台帳を一意に再生成できません。

2. C-1 が `a10` の6成分式を誤って scalar 化している

[package.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:72) は  
`L_J = max(0, 1 − 6(1−power))` としていますが、一次資料の式は [addendum-a-reissue.md:684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:684) の `1 − Σ p_k(J)` です。`d⁻` は6成分の最小値にすぎず、残り5成分の power が同じとは限りません。

したがって「`d⁻ ≥ 1.5623` でなければ必ず `design_not_feasible`」は必要条件ではなく、全6成分を同一最悪値に置いた十分条件を誤って必要条件にしています。

**成果物影響:** 実際には適格な pilot を `design_not_feasible` と判断するようユーザーを誘導し、本走・材料レポート・試行台帳を誤って生成不能にします。

3. stress check が `J=4..6` で恒真通過する

[publication-core.md:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:149) は `6×6` 共分散の正定値を要求しないと正しく規定しています。一方 [publication-core.md:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:409) は `6×6` 共分散が特異なら非棄却として数えます。

`J≤6` では rank は最大 `J−1<6` なので、全 synthetic dataset が特異です。よって `J=4,5,6` の全セルは実際の公表手続きを試さず `x=0` になります。

**成果物影響:** 実手続きが名目水準を破っても stress check が通り、材料レポートへ誤った FWER・同時被覆表示を付けられます。

4. 新 core が primary 側の `ledger_kind` を越権定義している

[publication-core.md:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:444) は `{primary_series, individual_publication}` を新 core 自身が定める閉じた enum としています。しかし追補 A `a13` の primary 正本は [addendum-a-reissue.md:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919) の `(family_root, ordinal)` であり、`primary_series` という識別子を持ちません。

また `individual_publication` は既に追補 B 草案 [addendum-b.md:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:148) が規定しています。どちらが正本か未確定です。

**成果物影響:** primary entry の key 形状と公表 entry の正本が実装ごとに分岐し、正しい既存予約を拒否するか、同一 ordinal を二重予約します。

5. C-2 は最重要の予約所有者を選択肢にしていない

[package.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:112) の推奨 (a) は現 B と追補 P を併存させますが、同じ entry をどちらが予約するかは [package.md:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:120) の「注意」に埋もれています。「現 B から外す／P を参照だけにする」には選択肢・推奨・個別の成果物影響がありません。

しかも前者は、今回変更禁止の追補 B bytes に触れる案です。C-2(a) を選んでも問題は閉じません。

**成果物影響:** `main_admission` を閉じる文書と公表台帳 entry の所有者が決まらず、本走投入と試行台帳生成が一意に決まりません。

## Blocker 以外の所見

- [package.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:36) の「本書には数値を書かない」は誤りです。core は `B=1,000,000`、`δ_MC=0.001`、seed、360セル等を固定しています。  
  **成果物影響:** 公表値自体は変わりませんが、ユーザーが承認する数値範囲を package が誤表示します。

- `RF_point`・`RF_confidence_set`・`interval_shape` は公表表の派生欄であり、source raw receipt の必須欄ではありません。source validator が raw から再計算する構成なので、§6.1 だけから source receipt schema 変更とは認定しません。

- §10.4 の11変異は公表側 consumer/validator の要求として読め、source の受理集合変更にはなっていません。

- `analysis_admission` が既存 resolver に誤解決される現在経路はありません。現コードは resolver API 自体を exportせず、既存 envelope parser も明示呼出しと一意な `## fields` を要求します。追補 P の書式は未定ですが、P が未作成で admission が閉じた現段階では、それ単独を blocker には数えません。

## 一次資料照合

次は一致しました。

- source core の commit と、commit blob／作業木双方の SHA-256。
- stress 入力の実ファイル SHA-256。
- `family_root = 88d68f91…` と追補 A `a13`。
- `a10` の6成分順、`T_k`、`J_max=13`、候補 `{4..13}`。
- `κ=0.20` と3状態名の綴り。
- Q7 の「Holm / closed testing、BH 不採用」と R5 (a)+(d) の正分母 guard。
- 自己 digest の混入なし。`authority: none`、段階1、未凍結・未承認の表示も一貫。
- `d1782b04…` は base core に既知 erratum の2操作を適用した合成後期待値であり、現草案自身の digest ではありません。

roadmap の限定例外については、新 study が新規 paired measurement を要求しないという説明は成立します。ただし C-3 がユーザー裁定を求めているため、未裁定事項を既成事実にはしていません。

## 総括

**NO-GO — blocker 5件。**