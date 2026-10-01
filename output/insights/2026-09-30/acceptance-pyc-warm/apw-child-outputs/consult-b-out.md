## 所見

1. **高 — 対照の受理集合一致は、現行 plan の K/H では成立しない。** plan §6 は `test_run_tests_shards.py` に新テストを追加し、§8 は K を base commit、H を実装後の tip とする。H の追加 nodeid が受入対象なら、K/H の login universe と observed universe は要素単位で一致しない。brief の「受理集合が K と一致」を判定条件にすると、正しい実装でも失格になる。**修正:** H と同じテストを持ち、`run_tests.py` の変更だけを戻した対照用 K を作る。両木の差分と nodeid 集合を投入前に記録する。

2. **高 — 約 40 秒短縮は未実測で、実受入への一般化もできない。** `meas/run-pair.sh` は `tools/run_tests.py` を直接起動する。md_2 README §4 の対照では、H の pre は 108.3〜111.2 秒、温の目安は約 65 秒だが、H の全 shard は login collection 完了前に始まり、事前登録判定は「判定不能」だった。`dev_wave_wait.py acceptance → launcher` を含む区間は測っていない。brief の成果目標と plan §8 の判定に対し、**修正:** 実受入の起動時刻、投入意図、shard 開始、login 完了を別々に記録し、「pre の短縮」と「受入全体の短縮」を別判定にする。約 38〜45 秒は見込み値と明記する。

3. **中 — 101〜102 秒の投入前区間の内訳は確定していない。** 生記録の起動→最初の intent は p1 K/H が 102.21/102.20 秒、p2 K/H が 101.30/102.30 秒で、brief の値に合う。一方、別走の probe は削除検査 34.21/88.71 秒、RuleOps 2.61/8.07 秒だった。これらを同じ走の内訳として引けない。probe の `tree_fingerprint` 54.58/93.39 秒は、明示 shard 経路の preflight 前には呼ばれない（`run_tests.py:2618–2659`）。brief の「約 100 秒の git 区間」への反論として、**修正:** 本番同一走の monotonic marker で各検査、session 作成、最初の intent を計測する。dispatch 側の準備が何秒かは現資料からは不明と記す。

4. **中 — 前倒しで常に pyc が揃うという余裕は測定条件に依存する。** 生記録の intent→`login-collection.log` は 85/93/92/108 秒、intent→shard 開始は通常約 26〜33 秒（p2 K の shard-2 は約 416 秒）。同時に login collection を約 101 秒前倒しでき、各所要が変わらなければ、通常 shard 開始まで約 19〜43 秒の余裕がある。しかし login の git 検査と pytest を並走させて双方が延びれば、一部 shard だけ温まる、全 shard が間に合わない、または preflight 延長が pre 短縮を上回り外側の wall が悪化する。brief P1 の断定に対し、**修正:** 前倒し対照で検査時間・collection 時間・shard 別 cache 状態を同時に測り、未完了 shard を除外せず報告する。

5. **中 — 素朴な待機案 (a) の比較値は過大である。** p1 と p2 H の shard は intent 後約 26〜33 秒に始まり、login log は intent 後 93/108 秒なので、log 完了までの追加待ちは約 60〜82 秒。比較すべき H の pre 108〜111 秒から温の約 65 秒への見込み短縮は約 43〜46 秒であり、brief の「待ち 70〜90 秒 対 得 72 秒」は別条件の冷 137 秒を混ぜている。(a) 単独の悪化見込みはなお約 14〜39 秒だが、値と理由を修正すべきである。**修正:** (c) に短い上限付き待機を足す案は別 arm として評価する。前倒しが完了済みなら待機費用はゼロに近く、未完了時は上限分の wall を払うため、無条件には採らない。

6. **中 — 対照は同時起動だけでは処置の効果を分離できない。** `run-pair.sh:56–73` 相当の K/H 同時起動では、両方の `git ls-files --deleted`、RuleOps、login collection が同じ login node で競合する。probe の削除検査だけでも 34.21 対 88.71 秒と揺れる。K と H の commit 差も実装以外に及びうる。p2 K の shard-2 は intent 後約 416 秒開始で、短い待ち行列の対象から外れる。brief の対照、plan §8 に対し、**修正:** コード差を限定し、対ごとの投入前検査時間と待ち行列を記録する。短い待ち行列の定義、許す起動差、主判定量（起動→統合 junit と shard 別 pre）、必要な差と無効条件を実走前に固定する。長い待ち行列の走を事後的に都合よく除かない。

7. **中 — 変更費用に対する採算はまだ示されていない。** plan §§1–6 は process 所有、signal handler、process group、stdout/stderr 用一時 file、deadline、複数の失敗経路と多数のテストを要する。得は短い待ち行列の初回受入での見込み約 38〜45 秒/shardで、同じ走の 3 shard に掛け算して外側が約 120 秒縮むわけではない。D987（`decisions.md:34741`）は実行器を変えた main 取り込み時の受領証再利用を拒否するので、並走 wave の再受入費用もある。brief の「全 wave が払う約 40 秒/shard」に対し、**修正:** 実受入の外側 wall で利益を確認してから採用し、land 時の再受入本数と node 時間を費用として併記する。D987 が直ちに全走行中 wave を再実行させる、という表現も条件付きに直す。

8. **低 — 安い cache 生成案と計算ノード先行 collection は、現根拠では有力でない。** D918（`decisions.md:33152–33186`）では `compileall` は rewrite cache を作れず、32.78→31.34 秒に留まった。全テストの pytest collection より安く、同じ rewrite cache を作る手段は射影資料から見つからない。計算ノードの 1 worker に書かせる案は D918 の子の bytecode 書込み禁止に抵触し、他 worker の待機も要る。D2046（`decisions.md:62586` 以降）の集合・worker 規律とも再検討が必要になる。plan の代案比較に対し、**修正:** この二案は現段階で不採用と明記する。投入前 git 検査の短縮は効果がありうるが、本件の実装 scope 外の別調査にする。

9. **低 — 2 node 時間未満の見積りには余裕が小さい。** md_2 README §4 の対照 12 job は計 4,058 秒＝1.13 node 時間。brief の追加受入 0.4〜0.7 node 時間を足すと 1.53〜1.83 node 時間で、再走や失敗時の余裕は 0.17〜0.47 node 時間しかない。**修正:** 対照と必要な受入の job 上限を投入前に積み上げ、再走が必要になれば common.txt §5 の 2 node 時間基準で改めて判断する。

## 反証できず

- 既存の login collection が同じ木に有効な pytest rewrite cache を書くこと。md_2 対照の終了後 pyc は H が 440、K が 0 である。
- 有効な submodule marker に限定すれば、plan が指摘した初期化との競合を避けられること（`run_tests.py:890–986`）。
- 前倒しによって、競合が小さい短い待ち行列の走では shard の pre が温の峰へ近づく可能性。
- md_2 README の「残り約 38 秒」は未測定の見込みであり、実測値との矛盾までは示せない。

## 総括

**現 plan のまま採用しない。** K/H のテスト集合を揃え、実受入の外側 wall を主指標にした対照へ直す。前倒し自体は有望だが、約 40 秒の利益と 2 node 時間以内の費用は未立証である。