静的検査のみ。pytest・mutation harness・bench は実走しておらず、緑判定はない。

## 1. 「将来の backstop」への枠組み転換

### [real] V1 は適用範囲を過度に広げている

record 1 件の現行 loader が遷移検査を呼ばないこと自体は正しい。しかし「現行本番では一度も呼ばれない」は maintenance issuer を落としている。

[issue_env_contract_activation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t673-transition-pbt-package/tools/issue_env_contract_activation.py:158) は、現在 state に serial 2 候補を追加し、同じ `validate_activation_records()` で遷移を検査した後に create-only publish する。さらに side branch の `677d0952` には、linux-baremetal g1 / pegasus g2 の実 serial 2 と head=2 更新が既に存在し、land の人間手番待ちである。

したがって正確な表現は「現行 checkout の定常 loader では未発火。ただし issuer 経路は到達可能で、serial 2 は実装済み・未 land」である。「抽象的な遠い将来」ではない。

成果物影響: V1 を現状維持の主要根拠にすると、目前の activation edge を存在しないものとして裁定させる。

### [refuted] それでも「現在未検出の direct `[:N]` 穴」と呼ぶ反証は成立しない

現行 env は 2 個で、serial 2 でも変化するのは pegasus 1 個だけである。正整数 N の直接 `[:N]` 族では、M=2 に効くのは最大でも N=1 であり、既存 4-env fixture は静的には N≤3 を検出する。N≥2 は現行入力では恒等である。

また env 集合変化は既裁定で拒否され、新 env の実需が出るまで別機構を設計しない。M>4 へ増やす具体的計画は確認できなかった。従って「現在の構成に対して PBT が必須」という反証もできない。

成果物影響: 現状維持の根拠は「遷移が呼ばれない」ではなく、「M≤2で、現実に効く direct positive-prefix 変異は既存 fixture の射程内」と書くべきである。

## 2. 選択肢提示の中立性

### [real] 9 択への平坦化はユーザーの問いを薄めている

A / A′ / B1 / B2 / C1 / C3 / D / E / F は同じ階層の択一ではない。

- A と F はほぼ同じリスク受容案。
- D は production 防壁、E は運用、loader/issuer pin は統合テストであり併用可能。
- C1 の「族全体を殺す唯一の実装可能案」は、同じ表の C3・D と矛盾し、誘導的。
- B2 の「ユーザーの問いそのもの」という語も、B2 を優遇する。
- A′ は 5/8/64 とされたが、side commit にあるのは A′-8 だけ。B1 の掃引値から A′-64 の恒久 LOC・保守費を「追加費用ゼロ」で導出できない。

是正は、本文をまず「A: 現状維持 対 B2: PBT」の二択比較に戻し、A′/B1/C1/C3 を対照実験、D/E/F/integration pin を「直交する追加策」の付録へ分離すること。

成果物影響: 平坦な9択のままでは、ユーザーは何を一つ選び、何を併用できるのか判断できない。

### [real] B2 は PBT 一般の価値を測る候補になっていない

B2 が生成するのは `env_count=2..64` だけで、不正位置・delta・predicate 結果の形は固定されている。しかも `@example(env_count=64)` が、登録した N≤63 の kill を単独で決める。Hypothesis が生成する残りの例は、今回の mutation frontier にほぼ追加検出力を与えない。

これは「Hypothesis で包んだ bounded size sweep」の評価であり、shrinking や複数入力軸の組合せ探索を含む PBT 一般の評価ではない。

成果物影響: B1/B2 が同じ frontier でも、「PBT に価値がない／ある」へ一般化してはならない。

## 3. 絶対規律 2 / 3 と偽陽性

### [real] F を終端に使えば、T-627 と同じ「残穴を説明して閉じる」を繰り返す

docstring はリスク受容の記録にはなるが、検出・拒否・構造化 signal を一切増やさない。「閉鎖」「保証」「規律を満たした」という語は禁止すべきである。A を採るなら、少なくとも M≥5、env 集合機構の導入、または対象 loop の変更を再裁定 trigger として所有者付きで固定する必要がある。

成果物影響: trigger のない F は、正しさ gate を増やさず将来の再訪責任だけを散逸させる。

### [real] C1 は正しさより source shape を守る gate である

C1 は関数名、loop が正確に2本、変数名、iterator が exact `ast.Name` であることを要求する。変数 rename、helper extraction、`tuple(changed)`、診断用 loop 追加など意味保存 refactor で赤になる一方、loop body の意味や callback 弱化までは検査しない。

C3 も private gate、tuple subclass、現行 signature に依存し、`tuple(successor_rows)[:N]` や `islice` なら sentinel を失って逃げられる。自己 sentinel node は production の保証ではない。

成果物影響: C1/C3 を correctness closure として land すると、偽陽性で開発を止めながら別構文の縮退は通す。

## 4. コスト提示

### [real] 恒久コストが大幅に未計上

不足しているのは少なくとも次である。

- PR ごとの累積 CI 時間、collection・shard への影響
- failure triage、counterexample 再現、誤検出解除に要する人時間
- production refactor と同時に誰が private test を更新するか
- B1/B2/A′が既存テストの private `_chain` / `_validate` に依存する結合費
- C1 の private 関数名・変数名・loop構造、C3 の private signature・tuple subclass 結合
- Hypothesis/Python/pytest 更新時の再測定、lock・wheel mirror・脆弱性対応
- `database=None` と version依存の `derandomize` 列による過去失敗再現性
- 候補再materialize、mutation spec anchor drift、side commit再作成の費用
- false-positive 一件を許す基準と、修正 SLA

562行全体を land するわけではないが、B2単体でも115行と新しい依存宣言・配布機構を恒久所有する。

成果物影響: 一回の focal 秒数とLOCだけでは、land後の総所有費を著しく過小表示する。

## 5. 数値の誤用

### [real] V1/V2/V3 は推奨を決める証拠として不足

- V1 は checkout の瞬間値で、issuer と未 land の serial 2 を表さない。
- V2 は一つの `changed[:1]` と特定 scope の検出数で、欠陥侵入確率や N>1 の価値を測らない。
- V3 は別AST先例の in-memory測定であり、本件C1の保守性・恒真耐性を示さない。
- frontier は選んだ mutant に対する境界であり、実害確率ではない。

B2 の 3.25秒・6.3MB・117 file・推移依存3個も、単発のmaterialize費にすぎない。計算ノードは外部network不可で、job directoryには再構築用wheel/lock/正式な依存宣言がない。実際の配置には Hypothesis 6.165.2 と3推移依存があるが、offline供給、cache miss、更新、全node展開は未測定である。

成果物影響: 「install 3.25秒だからB2は安い」は削除し、「network利用可能環境での一回値」と限定する。

## 6. D を scope 外にした判断

### [real] 実装しない判断は正しいが、比較から実質排除するのは不誠実

本番編集禁止なので、この wave で D を実装・測定しないのは正しい。しかし裁定パッケージは、その制約により「最も直接的かもしれない解」を測定対象から除外した事実を前面に出すべきである。

提案文:

> D は本 wave の本番編集禁止により未実装・未測定であり、不採用ではない。loop の期待件数と処理件数を通常の `if` で照合する走査完全性 guard は、direct `[:N]` 単一-site変異を fail-closed にできる可能性がある。これは D245 の集約量による遷移正否判定とは別の健全性検査である。runtime overhead、診断、multi-site変異耐性を別 wave で比較するまで、B/C より劣るとは裁定しない。

成果物影響: D を小さく「将来候補」とだけ書くと、編集禁止が結論を現状維持へ誘導した事実を隠す。

## 7. 推奨

### [real] 現時点では「Aを条件付き採用、B2はlandしない」が最も誠実

対象を正整数の直接 `[:N]` 族に限定すれば、現行 M=2 に実害を持つ範囲は既存 fixture の静的射程内である。serial 2 は目前だが env 数を増やさず、この結論を変えない。対して B2 は明示 `@example(64)` が検出力の中心で、PBT固有の追加価値を示さないまま依存・保守面だけを増やす。

ただし単なる「docstringで終端」ではなく、`registered env 数 >= 5`、env集合変更機構の設計開始、または直接slice以外の実欠陥観測を再裁定 trigger とする。その時点ではB2を自動採用せず、まずDとの比較を要求する。

成果物影響: 現行成果物を変えず、不要なCI依存を避けつつ、M>4へ進む前に未検出域を再度gateへ戻せる。

## 総括

裁定パッケージに必ず書かせるべきことは次の5件。

1. 「loader未発火」と「issuer到達可能・serial 2実装済み未land」を分離し、M=2という本当の根拠を書く。
2. 本文はA対B2の二択に戻し、他案は対照実験または併用可能な追加策へ分ける。
3. B2のfrontierは明示M64例が決めており、PBT一般の効用測定ではないと明記する。
4. F/C1/C3をclosureと呼ばず、private結合・偽陽性・offline依存運用を恒久コストへ含める。
5. Dは「禁止により未測定、不採用ではない」とし、M≥5等の再裁定triggerと所有者を固定する。

**推奨案: Aをtrigger付きで採用し、B2は現時点でlandしない。**