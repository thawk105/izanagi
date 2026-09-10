## 前提の確認

射影された全資料を末尾まで読んだ。Web 検索、書き込み、pytest、checker、親の 3 script の実行はしていない。独立した算術計算と文書の静的検査だけを行った。

`n = 201` は正しい。

- 許容域は `0 <= t <= 0.8`。iid 3 値モデルでは `A=0.60` を固定すると分布は `t` だけで一意に決まる。
- 親の格子は許容域を走査しているが、連続性だけでは格子間の下振れを排除できない。
- 独立検算では `x=t/0.8` と置き、検出力を次数 n の Bernstein 多項式として厳密な整数演算で評価した。`x=0.5` で二分した両区間の全 Bernstein 係数が `0.80` を超え、最小係数は `0.8011950120679608` だった。したがって格子間を含む全域で `0.80` を割らない。
- 数値的な最小点は `t=0.00855694` 付近、検出力 `0.8017431154`。本文の「約 0.009、約 0.8017」と一致する。
- `n <= 198` は `t=0` での最大でも `n=197` の `0.7968415728`。`n=199` は `t=0.009` で `0.7948311634`、`n=200` は `t=0` で `0.7868478242`。よって最小値は 201。

§5 固定表は header、separator、10 データ行の計 12 行、10 ラベル、各 2 セルを保持している。v2 から変わった行は n の `199` から `201` だけで、primary と各 sentinel も残る。checker の緑は主張しない。

## 対応表

|前回の残 must-fix|判定|根拠|
|---|---|---|
|1. tie 全域での n 再設計|closed|iid 3 値モデルと許容 `t` 全域が固定され、`n=201` は連続域でも正しい。§5.1 の旧概算 prose も §5.1.1 に統一された。|
|2. 無作為化と統計モデル|closed|2 割当を各 `1/2`、block 間独立、実走前固定、sharp null、遵守結果 `assignment_followed` が明記された。実装・consumer 不在時は §6 が発効を止める。|
|3. registry 違反の洗い落とし|partial|件数を入力に加え最優先で protocol violation にする規則は閉じた。ただし registry の理由 enum 自体と、入力件数が凍結 registry から正しく導出されたことの束縛がない。|
|4. verdict の全域性|partial|floor 値域、arm 別 treatment、欠落・型違反は改善した。一方、検証前に branch 1 が field を読む順序、負の violation count、manifest 非入力、汚染と protocol violation の優先関係が未閉鎖。|
|5. `analysis_invalid` の理由 enum|partial|理由 enum と protocol violation へ写す根拠は追加されたが、`registry_violation_count < 0`、不正な `reference_tps`、hash/id の型域などを覆わず、enum が全域でない。|
|6. 参照 provenance と信頼区間|partial|snapshot/receipt hash と `theta` の Clopper-Pearson 区間は追加された。ただし期待する manifest が関数入力に無く比較不能で、`reference_tps` の値も receipt に束縛されない。前段の「A の厳密な信頼区間」とも矛盾する。|

## 残る must-fix

1. **入力検証を verdict 分岐より先に完了し、invalid enum を全域化する。** 少なくとも負の `registry_violation_count`、不正な `reference_tps`、hash/id の欠落・型違反を理由へ追加する。  
   成果物影響: 負の違反件数が有意性分岐まで進んだり、負の参照値が arm の勝敗を反転させたりして、成立を誤って得られる。

2. **`analysis_manifest` と registry の期待値を純関数へ束縛する。** manifest の immutable projection または内容 hash と期待する ID・参照値・hash、registry hash と違反件数を入力または明示的な不変 closure に含める。registry の理由 enum も列挙する。  
   成果物影響: 現在の 3 引数だけでは、同じ入力がある manifest では有効、別 manifest では mismatch になるため、参照差替えや違反件数の過少申告を検出できない。

3. **汚染と protocol violation の関係と優先順位を §7.1 と一致させる。** `protocol_ok` が contamination を含むかを固定し、両方が同時に真の場合を逐語で決める。  
   成果物影響: 同じ汚染記録が adapter により「判定不能」と「protocol violation」のどちらにもなり、4 分類の集計が変わる。

4. **信頼区間の記述を全箇所で `theta` に統一する。** 「A の点推定と厳密な信頼区間」は `A_hat` と tie 件数、`m`、`theta` の区間へ改め、`m=0` の区間も固定する。  
   成果物影響: `theta` の区間を `A` の区間として報告し、異なる母数への推論を誤表示する。

## nit

親の格子 script は算術結果こそ正しいが、「連続だから密な格子で近似できる」だけでは全域保証にならない。今回用いた Bernstein 係数の厳密境界を再現可能な証拠として残すとよい。算術結論への影響はない。

## 総括

`n=201`、無作為化、sharp null、§5 固定表は閉じた。registry 違反 1 件で実験全体を失格にする規則も恒真拒否ではなく、遵守した registry では件数 0 が可能である。

ただし verdict はまだ真に全域な純関数ではなく、manifest/registry の束縛、汚染の優先順位、CI の母数表記に成果物を変える曖昧さが残る。現版は追加 fix が必要である。