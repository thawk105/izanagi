# 1. 所見

1. **must-fix — H1 の判定と今回の計測を分ける。** brief `s1-brief.md:5-6` は「H1 を測る」とし、plan `plan.md:64-68` は throughput を主に集計する。一方、未発効の評価草稿が定める H1 の主指標は **commit 当たりの LLC load miss** であり、対象 cell と反復数も異なる（W 相対 `docs/vhash-evaluation-preregistration-draft.md:235-237,367-385`）。放置すると、Cicada 内での探索的な throughput 差が、草稿の H1 判定に昇格して図と論文の主張を変える。**修正案:** 今回は「構成 B の実装と探索的な同時刻比較」と明記する。草稿の H1 判定を主張するなら、別途その主指標と確認段を満たす。

2. **must-fix — 全ての性能腕に正しさゲートがない。** brief `s1-brief.md:35-36` と plan `plan.md:62,68` は K=1/2/4/8 の性能値を扱うが、trace は K=1/8 に限る。K ごとの配列境界と挿入経路は異なり、モデル検査だけでは実機の並行実行を代替できない（W 相対 `external/ccbench/cc/cicada/transaction.cc:100-122,479-530`、`CLAUDE.md:64-69`）。放置すると K=2/4 の数値が、検査済みの構成 B の図に混ざる。**修正案:** 性能値を採否や headline に使う K は全て trace と判定器に通す。未検査の腕は「未検証の診断値」と個別に表示する。

3. **must-fix — `gc_inter_us` を snapshot 年齢と呼べない。** brief `s1-brief.md:34-35`、plan `plan.md:64,95` は GC 間隔だけを古さの軸にするが、ro snapshot は MinWts 由来、回収境界年齢は MinRts 由来で別量である（W 相対 `output/insights/2026-09-29/vhash-readonly-share/README.md:69-84`）。GC 間隔を変えると版の数や更新の進捗も動く。放置すると「古い snapshot ほど hot が効く」という図の読みが交絡を含む。**修正案:** 軸名を「GC 間隔」にし、各 cell の実測 snapshot 年齢、版探索位置、更新 commit/s、版生成量を診断走で併記する。年齢を測れない場合、年齢に関する結論は書かない。

4. **should — 長い ro tx を外すと md_15 の最も深い領域を試せない。** brief `s1-brief.md:34`、plan `plan.md:95` の省略は規模を抑える選択として成立する。ただし md_15 では長い ro tx を入れた 45 走全てで 3 秒間の MinRts 公開が 0 回となり、ro read の深い位置も増えた（W 相対 `output/insights/2026-09-29/vhash-readonly-share/README.md:206,274-279`）。放置すると「read-only 側の伸びしろ」を通常の短い YCSB 全般へ一般化してしまう。**修正案:** 通常 YCSB の短い tx に限る結論とする。長い固定 snapshot は後続課題に明示し、この wave の成功条件にはしない。

5. **should — ro 比率の図には実現負荷の内訳が要る。** plan `plan.md:44,64` は生成済み手続きを ro または書込み付きに変える。元の生成器は各操作を独立に選び、先頭操作に `ronly_` を設定する（W 相対 `external/ccbench/include/ycsb.hh:55-84,97-113`）。指定率を変えると read の割合だけでなく update 数、版の生成量、abort も変わる。放置すると ro 指定率と throughput 利得の相関を「深い read の効果」と誤って帰属する。**修正案:** 指定率と実現率、ro/update commit/s、abort 率、read の位置分布を cell ごとに残し、因果的な内訳とは書かない。md_15 もこの交絡を明記している（W 相対 `output/insights/2026-09-29/vhash-readonly-share/README.md:79-84`）。

6. **must-fix — 0.94 node 時間は投入判断に使える実測見積りではない。** plan `plan.md:62,66` の列挙は dependency 1、perf 5、COUNT 4、TRACE 3 の **13 build 構成**だが、計算は 11 build 相当である。先例の Elapse は 173/33=5.24、258/55=4.69、174/33=5.27 秒/recordで、いずれも build 込み（W 相対 `output/insights/2026-09-29/vhash-forwarding-prototype/README.md:122-129`）。5.3 秒の run 単価と build 単価をそこから独立に推定できず、新しい K=8 と GC=100000 の費用も未観測である。放置すると 2 node 時間未満という判断と台帳の見積りが過度に確かに見える。**修正案:** 現値は仮置きと明記する。計算ノードで対象 patch の build、K=8・GC=100000 の代表 run、trace/判定の Elapse を測って、全 job・smoke・失敗再走を含む合計を再計算する。仮定だけを直しても 13×3×30 秒なら **3,552 秒**であり、3,372 秒ではない。

7. **should — 5 round を cell ごとに一つの node へ置くと node 効果を見分けられない。** plan `plan.md:64,68,96` の対内巡回は同時刻対照として有効だが、3 job に cell を分けるため各 cell の反復は同一 node に閉じる。5 点では草稿の確認段の区間・判定語も使えない（W 相対 `docs/vhash-evaluation-preregistration-draft.md:367-385`）。放置すると node 固有の差と K の効果を分けられず、中央値だけから有意・一般化を主張しうる。**修正案:** この規模なら探索値として対の比の全点・中央値・範囲を示し、有意とは書かない。node をまたぐ再現が必要なら、cell ではなく round を node に割る。

8. **should — COUNT の比較相手が抜けている。** plan `plan.md:43,64` は K の COUNT 48 走だけで「探索長・hit・書込み費用」を報告するが、stock の同条件 COUNT がない（W 相対 `external/ccbench/cc/cicada/transaction.cc:100-122,479-530`）。放置すると探索長の改善量や追加費用を、異なる build の値から推測する図になる。**修正案:** 比較量を示す cell だけ stock と K の同じ診断計器を揃える。全 12 cell での lock 時間計測は削り、update 中心と深い ro の代表 cell に絞れる。

9. **must-fix — 壊し版の「到達」と「検出」を同一視できない。** brief `s1-brief.md:36` は B1/B2 の検出を完了条件にする。plan `plan.md:52-54` も B1 の古い read から巡回を期待するが、単発の古い read は必ずしも巡回を作らない。B2 は update validation や PENDING の最終状態に左右される（W 相対 `external/ccbench/cc/cicada/transaction.cc:108-122,543-570`）。先例でも初回の壊し本走は検出しても帰属できなかった（W 相対 `output/insights/2026-09-29/vhash-cicada-verifier/README.md:162-170`）。放置すると「判定器が hot の取り違えを検出した」という正しさの主張が、別経路の巡回に依存する。**修正案:** 壊し点、誤読が commit した事象、巡回の依存辺との対応を先に固定し、帰属できない検出は成功と数えない。B3 の追加は帰属不足を具体的に確認した後だけでよい。

10. **must-fix — gate の既存ファイル変更は依頼の所有範囲外である。** brief `s1-brief.md:16`、plan `plan.md:46,74,80` は production 3 件と既存 test 4 件を U1 に割り当てるが、依頼の所有は新規 patch・新規 driver・自身の一次資料と fragment 等に限る（`request-md23.txt:27-29`）。先例 D2288 は「必要最小の所有外登録」を別途裁定しており、その裁定を今回の所有許可へ自動的に拡張できない（W 相対 `docs/decisions.md:73641-73650`）。放置すると並走中の `condition_meaning_gate.py` や台帳 test を上書きし、land 時に登録集合と site 件数が壊れる。**修正案:** gate 登録自体は必要最小の閉包として維持し、今回の所有境界で誰が統合するかを親の段 4 で明示する。既存差分を読んだ上で登録行だけを統合し、先例のファイル一覧を一括コピーしない。

11. **nit — driver の置き場への攻撃は不成立。** plan `plan.md:60` の `orchestrator/campaign/` は CCBench の patch、build、gate、計算ノード起動を担う今回の driver に適合する（W 相対 `orchestrator/campaign/vhash_forwarding_prototype.py:29-41,769-803`）。D2285 が `tools/` を選んだ理由は CCBench を使わない独立微小計測だからで、今回とは前提が違う（W 相対 `docs/decisions.md:73578-73589`）。放置しても成果物は変わらない。**修正案:** 置き場は維持し、既存の private helper 依存だけ明示する。

# 2. brief の P 項目ごとの判定

1. **P1 — 修正。** 記述子のみは妥当。ただし K が大きいほど全 100 万 Tuple に領域を配るため、`N×(8+16K)` は目安にすぎない。実 RSS と cache miss を分けて報告する（W 相対 `external/ccbench/cc/cicada/include/tuple.hh:24-110`）。
2. **P2 — 修正。** fallback 方針は成立。plan の atomic 記述子と seq 再確認後の ptr 利用を実装条件にする（W 相対 `external/ccbench/cc/cicada/transaction.cc:100-122`）。
3. **P3 — 修正。** 物理列の先頭 K 件という不変条件に統一し、install と GC の公開箇所を全て監査する。plan の方向は妥当（W 相対 `external/ccbench/cc/cicada/transaction.cc:479-530,806-843`）。
4. **P4 — 不成立。** ABORTED を hot から消すと物理列との対応と `later_ver` が崩れる。plan の「残す」を採用する（W 相対 `external/ccbench/cc/cicada/transaction.cc:100-122,543-570`）。
5. **P5 — 修正。** 直前の**物理版**を `later_ver` とする条件付きで成立。cold 開始位置も境界事例で確認する（W 相対 `external/ccbench/cc/cicada/transaction.cc:100-122,543-570`）。
6. **P6 — 修正。** 同じ版を選ぶという説明だけでは再利用競合を閉じない。plan の hot lock 内の切断・除去と、再利用前の参照消滅を検証する（W 相対 `external/ccbench/cc/cicada/transaction.cc:806-843`）。
7. **P7 — 修正。** inert と gate 登録は必要。3 macro と COUNT の全 cell 計測は縮められる。登録の所有境界は所見 10 のとおり（W 相対 `docs/decisions.md:73641-73650`）。
8. **P8 — 修正。** 長い tx を外す判断は規模上成立するが、GC 間隔を snapshot 年齢と見なす部分は不成立。短い YCSB と GC 間隔別の結果に限定する（W 相対 `output/insights/2026-09-29/vhash-readonly-share/README.md:72-75,274-279`）。
9. **P9 — 修正。** 同じ round の stock 対照と巡回は成立。5 round・node 割付・見積りから強い統計主張は成立しない（W 相対 `docs/vhash-evaluation-preregistration-draft.md:367-385`）。
10. **P10 — 修正。** K=1/8 だけの trace では全性能腕を支えない。壊しの発火、commit、巡回への帰属も別判定にする（W 相対 `output/insights/2026-09-29/vhash-cicada-verifier/README.md:162-170`）。

# 3. plan から削れるもの

- `plan.md:43,64` の全 cell×全 K の COUNT 48 走は、代表 cell の stock 対照付き診断へ縮められる。探索長と lock 費用の図に必要な比較だけ残す。
- `plan.md:54` の B3 は常設の壊し本数から外し、B1/B2 が発火しても帰属できない場合の条件付き追加にできる。
- `plan.md:64` の K 4 水準は探索には有用だが、予算超過時は **K=1/8 と stock、ro=0/95、GC=10/100000** を先に残す。削った K の最適値や曲線形状は主張しない。
- `plan.md:46,74` の gate 連動ファイルは、実際に新 macro・新起動 site を登録する箇所だけ変更する。既存 test の期待集合に現れないファイルまで先例どおり編集する必要はない。

## 総括

この wave は、構成 B を Cicada 内で初めて動かし、短い YCSB における K 別の性能と費用を探索的に示せる。草稿の H1 主判定や「snapshot が古いほど効く」という因果的結論には、現 plan の指標と軸では届かない。投入前に K 全腕の正しさ方針、実 Elapse に基づく総 node 時間、所有外 gate 登録の統合担当を確定させる。今回は指定どおり静的検査のみで、テストと計測は実行していない。