## 前提の確認

指定された 9 資料と `docs/phase3-s4b-runbook.md` を末尾まで読んだ。Web 検索、書き込み、pytest、checker、親の 3 script の実行は行っていない。算術だけを独立に再計算した。

fix 後全文は checkout の対象文書と SHA-256 が一致した。

- tie 率 0 に限定すれば `n = 199` は正しい。棄却境界 `W >= 114`、実 alpha `0.0234432338`、検出力 `0.8037139604`。`n <= 198` の最大検出力は `n = 197` の `0.7968415728` なので、199 が最小である。
- ただし tie 率 0 は最悪ではない。例えば iid 分布
  `P(tie)=0.01, P(on勝)=0.595, P(off勝)=0.395`
  は `A=0.60` を満たすが、`n=199` の検出力は約 `0.7948684892` で 0.80 未満になる。
- `check_tie_monotone.py` は tie 率を `0.0, 0.1, ..., 0.7` しか調べないため、この反例を見落とす。非 tie 成功確率の上昇だけで、非 tie 数の減少と離散的な棄却境界を無視している。
- `p_on` と `p_off` の排他性は正しい。二項確率変数を `W'` とすると、
  `P(W' >= W) + P(W' <= W) = 1 + P(W'=W) > 1`
  なので、両方が同時に 0.025 以下にはならない。
- verdict の 6 分岐は、各条件を外部から評価できると仮定すれば全て到達可能である。ただし実際の入力契約には割当遵守情報がなく、現状のままでは全域な純関数として実装できない。
- §6 の前提条件 9 は末尾追加なので既存番号をずらしていない。runbook の「前提条件 3」は引き続き閉じた critic invocation を指し、§8 見出しも `負の対照 (前提条件 7)` のままである。
- §5 固定表は、header・separator・10 データ行の計 12 行、10 ラベル、セル分割を保持している。値も意図どおりで、primary は `未記入`、n は 199、owner セルには開始時刻の sentinel が残る。静的には fail-closed であるが、checker の PASS は主張しない。

## 対応表

|項目|判定|根拠|
|---|---|---|
|レビュー A 1|partial|`A` と `A_hat` を分離し、`A_min` gate を外した点は閉じた。tie 率 0 の算術も正しいが、許容される tie 分布全体で 0.80 を保証しない。信頼区間の構成法も未固定。|
|レビュー A 2|partial|実走前の独立無作為化と違反分類は追加された。ただし二つの割当を確率 1/2 ずつ選ぶことと、検定対象が sharp な label-exchangeability null であることが明記されていない。|
|レビュー A 3|closed|`p_on` と `p_off` を分離し、方向ごと alpha 0.025 とした。不成立分岐は到達可能で、両尾は排他。|
|レビュー A 4|partial|4 分類と優先順、`m=0`、`analysis_invalid` の行き先は追加された。一方、割当遵守が入力に無く、§7.1 と contamination の分類が矛盾する。|
|レビュー A 5|regressed|適格性述語と選択関数は増えたが、bootstrap、registry の生成元・凍結時点・予定件数が未固定。さらに registry 上の protocol violation を manifest から除外して成功判定から外せる新経路が生じた。|
|レビュー A 6|closed|全 attempt の registry と分析 manifest を分離し、適格性、順序、先頭 n、n 未満、余剰行、再生成 exact equality を定義した。|
|レビュー A 7|partial|祖先選択、0 件、同着複数、receipt 不特定時の扱いは閉じた。ただし純関数入力には reference 値しかなく、snapshot hash と receipt hash が束縛されない。|
|レビュー A 8|closed|tie は `rejected` と `aborted` の間だけ、`missing` は下位、と逐語で一意になった。|
|レビュー B 1|regressed|台帳分離と先頭 n は改善。ただし append 順を生成する凍結済み schedule がなく、registry の違反行を分析 verdict から洗い落とせる。|
|レビュー B 2|closed|全 status pair の順位解釈が一意になり、§4 の reject に fitness を付けない規則とも整合する。|
|レビュー B 3|partial|floor、arm 別 hash、enum、boolean は追加された。ただし割当遵守が引数外、floor の値域検査がなく、`treatment_fired` の arm 別意味も未定義。|
|レビュー B 4|closed|上下の片側 p 値を別定義し、不成立分岐を到達可能にした。|
|レビュー B 5|partial|tie 率 0 では 199 が正しいが、「tie 率 0 が最悪」が偽なので、許容分布全体に対する 0.80 保証は閉じていない。|
|レビュー B 6|closed|将来 pilot 条項を現契約から削除し、新しい事前登録で4項目を再凍結する場合だけに限定した。|
|レビュー B 7|closed|primary セルを `未記入` に戻し、§6 前提条件 9 に実装・consumer・生成器・割当検査を追加した。番号参照も壊れていない。|
|レビュー B 8|closed|§5.1.1 から可変な現在地の再掲を除き、§7.2 と §10 を正本として明示した。|

## 残る must-fix

1. **tie を含む最悪検出力を再設計する。** 少なくとも `t=0.01` で検出力は約 0.79487まで下がる。現在の契約は block 同質 iid も要求していないため、許容分布を先に定義してから全域で n を求める必要がある。§5.1 の「分散上限から概算」という旧 prose も、§5.1.1 の「厳密検定から直接導出」と統一すること。  
   成果物影響: 目標検出力を満たさない実験が `n=199` を満たした設計として受理され、検出力の報告値が誤る。

2. **無作為化と統計モデルを完全に固定する。** 各 block の二つの permutation を確率 1/2 ずつ選ぶこと、block 間独立性、検定する sharp null、対立側で許容する tie・異質性の範囲を明記する。  
   成果物影響: 同じ `A=0.60` でも実装者が仮定する分布により p 値の正当性と必要 n が変わる。

3. **registry から protocol violation を洗い落とせる経路を閉じる。** arm digest を受けた precursor は registry で violation になる一方、manifest では不適格となり、verdict の最優先分岐に届かない。registry 全体の violation を verdict 入力へ渡すか、実験全体を開始前に失格とする必要がある。  
   成果物影響: 違反 attempt を後続の適格行で置換して「成立」を得られ、台帳と実験 verdict が食い違う。

4. **verdict を実際に全域な純関数にする。** 入力へ割当 schedule と遵守結果を追加し、floor の有限・非負条件、各 boolean の不正値、欠落 field、`treatment_fired` の arm 別意味を定義する。§7.1 の「off 汚染は判定不能」と verdict の「contaminated は protocol violation」も統一する。  
   成果物影響: 同じ raw record が adapter 実装により別分類となり、負または NaN の floor では tie と有意判定まで変わりうる。

5. **`analysis_invalid` の分類根拠を固定する。** protocol violation へ倒すこと自体は fail-closed であり、成立を容易にはしない。ただし analysis 契約違反を実験 protocol violation と呼ぶなら、理由 enum と §7.1 との対応を明記する必要がある。  
   成果物影響: 台帳上の「protocol violation」と「判定不能」の件数および最終分類が実装ごとに変わる。

6. **参照点の provenance と信頼区間を演算契約へ含める。** `reference_snapshot_hash`、receipt hash、`PerfConfig`、`env_tag` を入力または manifest に束縛し、`A` の「厳密な信頼区間」の対象母数と構成法を固定する。  
   成果物影響: reference の差替えで certified 同士の tie が変わり、CI 手法の選択で報告区間が変わる。

## nit

なし。`probe_section5.py` には前レビューで求められた自己検査が追加されており、静的内容に新たな nit は見つからなかった。

## 総括

fix は、順位、上下尾、pilot、固定表、§6 gate、可変状態の正本化を閉じた。しかし着地承認には至らない。

決定的なのは、`n=199` が tie 率 0 に限れば正しい一方、「tie 率 0 が最悪」という前提が反例で崩れること、および registry 上の protocol violation を analysis manifest から除いて成立判定へ到達できる新しい経路である。verdict の入力不足と §7.1 の分類矛盾も残るため、現差分は追加 fix が必要である。