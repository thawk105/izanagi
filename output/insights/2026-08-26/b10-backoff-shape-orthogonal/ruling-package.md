# 裁定パッケージ — B-10 待ち方 / 待ち量の直交切り分け

本 wave が scope 外と裁定した real 所見と、予算制約で実装できなかった自己改善候補を、
ユーザーの裁定へ返す。**いずれも本 wave では実装していない。**

## A. scope 外と裁定した real 所見

### A-1. 実走での要求待ち量そのものを測る診断ビルドの新設

- 出所: 段 3 レンズ A の must-fix。
- 内容: thread・session ごとの要求待ち量の平均、`P(wait=0)`、分位点、自己相関、
  スレッド間同時値率を、性能 run とは別の診断ビルドで記録する。
- 本 wave の対応: 実装面を EVOLVE-BLOCK 合成枝の 1 行の外へ広げるので採らなかった。
  代わりに待機ループを逐語で再現した probe 相を足し、**実経過時間の平均**は測れるようにした。
  主張は「指示待ち量の平均を揃えた」に限定している。
- 判断が要る点: 分布の形そのもの (分位点・自己相関) まで実測する価値があるか。

### A-2. 旧 backoff consumer の campaign identity 移行、または v1 patch の別名凍結

- 出所: 段 3 レンズ B / 段 6 レビュー B の should-fix。レビュー B が全件検索で裏を取っている。
- 内容: 合成枝の式が v1 から v2 へ変わったため、同じ `BACKOFF_FIXED` でも
  preprocess 後ソース・`src_token`・variant 識別子が変わる。
  **現在の凍結成果物・WAL 参照は 1 件も壊れていない**が、旧 consumer を v2 patch で再走すると
  新しい識別子が同じ campaign に入り、8 件の WAL SHA pin を壊しうる。
- 本 wave の対応: `patches/README.md` に警告を書いた (「旧 campaign へ resume してはならない」)。
- 判断が要る点: 全 consumer の identity へ patch / 式 / 空間の版を足すか、
  v1 patch を別名で凍結して歴史的再現を残すか。

### A-3. 測定 helper を一回限りの capability token で封じる

- 出所: 段 6 レビュー B の should-fix。
- 内容: 現状「登録前に性能を見ていない」と機械的に言えるのは formal driver 経路だけである。
  driver を経由しない手動実行を repo 内の preflight で封じることはできない。
- 本 wave の対応: 事前登録と最終レポートの主張を formal driver 経路へ明示的に限定した。
- 判断が要る点: repo 内 preflight より強い外部権威を導入するか、限定表現で足りるとするか。

### A-4. Pegasus の write-heavy / balanced の between-run floor 取得

- 出所: 段 2 plan / 段 3 レンズ A。
- 内容: Pegasus には read-heavy の between-run floor しかない。
- 本 wave の対応: 判定を独立 3 ブロックの対比較へ変えたことで外部 floor への依存が消え、
  **B-10 の必要条件からは外れた**。参考線としては有用。
- 既存 driver あり。2 workload で 20〜30 分の見込み。次の一手へ登録済み。

### A-5. B-10 driver の専用 generator authority

- 出所: 段 6 レビュー B の should-fix。「B10 の人間所有の式が旧 magnitude sweep の生成物として
  帰属し、certified source の生成主体を区別できない」。
- 本 wave は一度実装したが、**受入全走の実測で取り下げた。**
  `GeneratorId` の閉集合へ member を 1 件足すと**方針の識別子の hash が変わり、
  それが campaign 識別子に焼かれているためすべての campaign の識別子が動く**。
  実測: `test_campaign_id_binds_admission_policy` が
  `readheavy-locont-fullsearch-27d737fd` → `...-b7eb9aa1`。受入で 65 件が赤になった。
- **既存の凍結成果物・campaign 群との対応が壊れるので、治療の害が病気より大きい。**
  期待値の hash を書き換えて緑にするのは、比較可能性を捨てることなので採らなかった。
- 判断が要る点: 生成主体の区別を、識別子を動かさない別の場所 (receipt の field 等) で
  与えるか、区別しないままにするか。

## B. 予算制約で実装できなかった自己改善候補

`docs/dev-wave/` の byte 予算 (L1 / L1.5) が満杯で、次の 3 件はいずれも入らなかった。
自己改善の契約は「予算値を上げる変更は通常の自己改善に含めず、理由付きの独立審査対象にする」と
定めているので、**予算を上げずに諦め、ここへ送る。**

### B-1. 子を投げる前に統合 commit する (DW-O01 相当)

- 本 wave の実測: 段 6 のレビュー 2 本が同時に rc=2・成果物ゼロで終わった。
  原因は fix 子が残した設定 file の未 commit 差分で、子は hook 配線 file が HEAD blob と
  一致していることを起動条件にする。**stage 非依存で、並列投入は全本が同時に落ちる。**
- 入れたかった文: 「投入前に統合 commit する。hook 配線 file が HEAD blob から drift していると
  stage 非依存で rc=2、成果物ゼロで終わる (並列投入は全本が同時に落ちる)。」

### B-2. 在庫 fix は同一 test 関数内の完全一致述語を全部照合する (DW-S06-B 相当)

- 本 wave の実測: **2 回起きた。** 1 回目は在庫の根の集合だけ直して同関数の第二 golden
  (`expected_local_evidence`) を落とし、2 回目は probe が足した起動点で同型の漏れが出た。
- 入れたかった文: 「在庫を直す fix には、同一 test 関数内の完全一致述語を**全部**照合させる。
  根の集合だけ直すと同関数の第二 golden が残って修正が発効しない。」

### B-3. 実測が新規 Pegasus 実行体を要するかを brief で判定する (DW-S01 相当)

- 本 wave の実測: 新設した投入スクリプト 2 本を計算ノードへ投げようとしたところ、
  機械防壁が「未登録 Pegasus 実行体」として拒否した。防壁は main 側の登録簿を読むため、
  **wave の作業ツリーで登録しても効かない。** 本 wave の実走が完了しない直接の原因である。
- 入れたかった文: 「実測が新規 Pegasus 実行体を要するかを brief で判定する。要するなら
  **その wave では実測できない** (機械防壁は main 側の登録簿を読む)。
  機構の着地と実測を別 wave へ分ける。」
- 本 wave では failures 台帳へ新規 F として記録した (fragment 済み)。

## C. 判断を仰ぎたい 1 点

**B 群の 3 件を入れるために `docs/dev-wave/` の byte 予算を上げるか。**
3 件とも本 wave で実際に事故として発火しており、B-2 は同一 wave 内で 2 回起きている。
予算を上げずに諦めると、同じ事故が次の wave でも起きる。
一方、予算は読み込みコストの上限として意図的に置かれたものなので、
上げる判断は独立審査に委ねるのが契約である。
