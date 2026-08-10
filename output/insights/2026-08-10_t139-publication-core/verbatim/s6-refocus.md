判定は **NO-GO** です。修正の中心部分は改善していますが、残 blocker は **4件**あります。

pytest・build・Monte Carlo simulation は実走していません。静的読解、Git object の SHA-256 照合、式の決定論的数値検算だけを行い、ファイルは変更していません。

## 焦点項目の検証

1. §7.4 本文は修正済みです。[publication-core.md:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:498) は成分ごとの `s_k=0` だけを縮退判定に使い、`6×6` 特異性を明示的に禁止しています。したがって `J=4,5,6` の108セルは恒真通過しません。ただし package に旧規則が残っています（blocker R2）。

2. RNG は一意に再生成可能です。

   - `seed_bytes` は raw 32 bytes：[publication-core.md:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:449)
   - ASCII domain、区切り、10進・前置ゼロなし：[publication-core.md:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:455)
   - `n=0`、reject ごとに増加、抽選ごとにreset：[publication-core.md:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:464)
   - W1/W2 は別 domain で独立抽選：[publication-core.md:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:473)
   - 1 dataset を6成分が共有：[publication-core.md:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:422)
   - 全6成分を同じ weak-null face、母平均0に置く：[publication-core.md:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:475)

   実装が二通りに分かれる RNG 上の曖昧さは残っていません。

3. dataset は `10 J × 1,000,000 = 1,000万` です。各セルの Clopper–Pearson 上限へ `δ_MC/360` を割り当てれば、セルがdatasetを共有して従属していても union bound は成立します。総数変更と Bonferroni は両立します。

4. 無効化は節番号でなく実体判定になり、予定済み core §7 の第2 erratumでは無効にならないと明記されました。[publication-core.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:51)

   同一データ再解析経路も閉じています。[publication-core.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:72) の「一度でも計算した後」は、計算したが公表しなかった場合も含みます。さらに新 core は無効化時点で未観測のdatasetだけを対象にでき、結果を一つも見る前に無効化の必要性が確定していなければなりません。ただし、無効化対象の実体列挙が追補A全体を覆っていません（blocker R1）。

5. source の三つ組は追加されています。[publication-core.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:38)

   Git object と作業木の双方で照合し、次が一致しました。

   - commit: `622bd786191d40bda388596fa2adbf119ee84c9a`
   - SHA-256: `f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec`

6. §8.1 本文は primary 側の識別子を定義しなくなりました。[publication-core.md:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:537) は公表側の一値だけを定め、[publication-core.md:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:541) は primary 側を `a13` に返しています。重複をC-2裁定へ返す構成も適切です。ただし package の要約が旧2値のままです（blocker R3）。

7. §5.3 の計算結果は次のとおりです。

   - `q(13,0.025)=3.449997401748…`
   - `c_B(13,0.025)=3.152681312170…`
   - 全 `J=4..13` の条件境界は `J=13`
   - 厳密な下限は `α*=0.01441501498…`

   したがって概数としての `0.0144150` と「最初に破れるのは `J=13`」は再現しました。ただし strict inequality と丸め値をそのまま同値条件にしたため、極小区間で誤判定します（blocker R4）。

   core は条件付きになっていますが、package は [package.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:63) で依然として無条件に記述しています。

8. C-1 の数値検算：

   - 必要条件：`d⁻ ≥ 1.220995636…`、表示値 `1.2210` は正しい。
   - 6成分同一の場合の十分条件：`d ≥ 1.562340730…`、表示値 `1.5623` は正しい。
   - `d⁻=1` なら候補全体で `L_J≥0.80` は不可能なので、`design_not_feasible` の結論は正しい。
   - ただし「全候補で `L_J=0`」は一般には誤りです。`J=13` で最弱成分だけが `d=1`、他5成分の失敗確率が0へ近づけば、`L_13→1−0.4237200514=0.5762799486` です。全6成分が `d=1` の場合に限れば `L_J=0` です。

9. C-2b は選択肢・推奨・成果物影響を備えています。[package.md:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:140)  
   追補B原文は `authority: none` の草案で、承認決定のfold前は発効しないため、段階1で再発行可能という前提は正しいです。[addendum-b.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-09_t139-addendum-b/addendum-b.md:12)

10. C-4 はC-2b未裁定のまま承認できないと明記され、整合しました。[package.md:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:179)

## 第1巡所見の対応表

| 第1巡所見 | 状態 | 修正後の照合 | 放置時の成果物影響 |
|---|---|---|---|
| C-B1 `6×6` 特異性 | **partial** | core §7.4 はclosed。一方packageに「`s_k = 0` や特異共分散…非棄却」が残る | 旧要約を採ると108セルが `x=0` となり、材料レポートのstress受理表示が変わる |
| C-B2 RNG再生成不能 | closed | raw seed、domain、counter、reject、共有関係まで固定 | なし |
| C-B3 無効化経由の再解析 | closed | 計算済み・未公表も禁止。未観測dataset限定 | 同一データの第2棄却集合は作れない |
| C-B4 ordinal所有とC-4 | closed | C-2bへ分離し、C-4をその裁定に条件付けた | 未裁定なら承認・台帳生成へ進まない |
| C-Nit §5.3無条件記述 | **partial** | coreは条件付きだがpackageは「全候補で `q>c_B`。したがって…」と無条件 | coreを使えば受理集合は不変。packageの承認範囲を誤表示するためnit |
| C-Nit「本書には数値を書かない」 | closed | 「spending数値は書かない。stress定数は書く」へ訂正 | なし |
| C-Nit 段4表からA6脱落 | closed | 段4裁定表へA6が追記済み | 監査参照の欠落なし |
| C-Nit seed namespace分離喪失 | out-of-scope | provenanceと乱数domainを分離する段4裁定を維持 | 現行値・受理集合は不変。将来はversion literal更新が必要 |
| D-blocker 1 source束縛 | **partial** | 三つ組は追加。ただし無効化条件の「6成分の定義」「cluster適格条件・代表値」では `a07` workload argv、`a08` arm/source/build identity、`a09` exact scheduleの変更が明示的に覆われない | 異なるarm・workload・scheduleのデータを同じ公表coreへ受け、表の推定値・p値と台帳のsource参照が分岐する |
| D-blocker 2 C-1 scalar化 | **partial** | 必要 `1.2210`／十分 `1.5623` は修正。ただし「他5成分がどれほど強くても…全てで `L_J=0`」が誤り | `design_not_feasible` は不変だが、記録される検出力下界が誤るため残差はnit |
| D-blocker 3 stress恒真通過 | **partial** | coreはclosed。packageに旧「特異共分散→非棄却」が残る | C-B1と同じ。stress受理集合を誤って拡大する |
| D-blocker 4 primary `ledger_kind` 越権 | **partial** | coreはclosed。ただしpackage要約は「`ledger_kind` は閉じた2値」のまま | primary entryを公表側が名付け直し、試行台帳のkey・予約参照が分岐する |
| D-blocker 5 C-2の選択肢不足 | closed | C-2bに選択肢・推奨・影響を独立記載 | 未裁定ならC-4へ進まない |
| D非blocker「本書には数値を書かない」 | closed | spending値と手続定数を区別 | なし |
| D非blocker RF欄とsource receipt schema | closed | 公表表の派生欄として維持。source raw schema変更の主張なし | source validatorの受理集合は変わらない |
| D非blocker §10.4の11変異 | closed | 公表側consumer/validatorの将来要件として維持 | sourceの受理集合は変わらない |
| D非blocker `analysis_admission`誤解決 | closed | resolver未実装を§11で明示し、現時点のactive gateを主張しない | 現在の投入・台帳受理集合は変わらない |

## 残 blocker

1. **R1 — 追補A変更に対する無効化閉包が不足。**  
   [無効化6項目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/publication-core.md:56) は、追補Aの `a07` workload identity、`a08` arm/source/build identity、`a09` schedule identityを明示的には覆いません。  
   **成果物影響:** 同じ公表coreが異なる測定対象の `Y_j` を受け、材料レポートの推定値・p値と試行台帳のsource参照が分岐します。

2. **R2 — package が `6×6` 特異性枝を残している。**  
   [package.md:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:55) の「`s_k=0` や特異共分散…非棄却」は、修正後§7.4と矛盾します。  
   **成果物影響:** package側を仕様として読むと `J=4..6` の108セルが恒真通過し、FWER支持表示を誤って受理します。

3. **R3 — package が primary側を含む2値 `ledger_kind` をなお要約している。**  
   [package.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-publication-core/output/insights/2026-08-10_t139-publication-core/package.md:34) の「閉じた2値」は、core §8.1の公表側一値・primary側非定義と矛盾します。  
   **成果物影響:** primary予約のkeyを公表coreが越権定義し、正しい予約の拒否・二重予約・試行台帳参照の分岐を起こします。

4. **R4 — §5.3 のstrict境界を丸め過ぎている。**  
   真の境界は `0.01441501498…` です。例えば `α_pub=0.01441501` は本文の `>0.0144150` を満たしますが、実際には `J=13` で `q>c_B` を満たしません。  
   **成果物影響:** この狭い範囲を `p02` が選ぶと、材料レポートが「primary passなら6下限すべて正」という誤った表示を付けます。

残るnitは、packageの無条件な§5.3要約と、「`d⁻=1` なら全候補で `L_J=0`」という過大な数値主張です。後者は `L_J≥0.80` の受理集合を変えないため blocker には数えません。

## 総括

**NO-GO — 残 blocker 4件。**