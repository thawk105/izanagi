## 1. 所見

1. **blocker｜plan §5・§3 Driver。** 根拠: `output/insights/2026-09-29/vhash-readonly-share/README.md:192-199`、`orchestrator/campaign/vhash_cicada_vlife.py:346-361`、plan:72-82。md_15 で公開待ちの 76〜77% を見た S95 は**既定 genome・skew 0**、T95 は**調整済み genome・skew 0.9**である。プランは調整済み genome だけで両 skew を走らせるため、S の追試にならない。また、(b) に予定する「長い ro の slot が min になる時間」は既存計器から得られない。保持者は公開時だけ採取され、stock の wait10msR は公開 0 回だった。**修正案:** 主格子に S95 と T95 の元の genome を含める。公開 0 回でも観測できる等間隔の slot・MinRts 標本を最小限追加するか、(b) は公開再開後の保持者割合と「時間は未測定」という限界に縮める。

2. **major｜plan §5 の結論。** 根拠: `vhash-readonly-share/README.md:22-28,86-108,204-213`、`vhash_cicada_vlife.py:346-361`、plan:54,82。stock と variant の**公開回数・公開間隔の対応差**は (a) の headline にできる。境界年齢と終了時生存版は更新数・公開時点にも左右されるので診断値である。(b) は slot を固定したまま残る境界保持として示せるが、現行計器の「同値再公開の割合」と「公開時の保持者内訳」だけでは、保持**時間**や解消可能量を推定できない。**修正案:** headline を「公開停止の解除」と「公開頻度の対照差」に絞り、境界・版数・throughput は別指標として反復点とともに示す。md_15 の D-C は介入前の機会量としてのみ引用する。

3. **major｜plan §3 Driver・§5。** 根拠: `patches/instr-cicada-version-lifetime.patch:212-216,346-390`、`external/ccbench/include/ycsb.hh:55-79,102-109`、plan:56,80。計器なし build で `ycsb_rratio` を変えるだけでは手続き単位の ro 率にならない、という段 2 の指摘は正しい。ただし新 workload knob を計器 build の既存 VLIFE 書換えと重ねると、二重抽選または異なる retry 分布を作りうる。**修正案:** 両 build に同じ手続き生成 patch を適用し、計器 build の `izanagi_ronly_pct=-1`、`izanagi_long_kind=0` とする。待機位置、worker 1 の ro 固定、実現 ro 試行率・commit 率を照合する。実装後の分布一致は**未確認**。

4. **major｜plan §5 の「同時刻対照」。** 根拠: plan:77-80、`docs/pegasus-runbook.md:1432-1450,1498-1503`。同一 job 内の交互走行は近接時刻の対照として妥当だが、診断 job と性能 job は別時刻・別 build であり、両者を一つの対応差として扱えない。3 反復で AB・BA・AB と交替すると先行 arm も偏る。ノードを分けた条件の絶対水準差にも node 効果が残る。**修正案:** 各条件の stock/variant を同一 job・同一 node で対にし、順序を事前固定した均衡配置にする。集計は条件内の対差または比に限定し、診断と性能を別系列として報告する。md_18・md_20・md_21 の計測との非同居は、割当後のノードと実行時刻で確認する。専有は保証されない。

5. **major｜plan §5 の反復・所要。** 根拠: `vhash-readonly-share/README.md:234-239,268-269`、`vhash-gc-connection-prototype/README.md:118-119`、plan:60,77-80。144 走×2 build 種の実行本体 864 秒という計算は合う。一方、md_15 の 1,237 秒は**258 走を4 jobで実行した本計測だけ**であり、smoke・判定器・新 workload build を含まない。「1 node 時間前後」は未確認。3 対の 95% CI で小さい throughput 差を判断する力も乏しく、md_14 は3反復の差が揺れの内側だった。**修正案:** S95/T95 の gc10 と wait10msR を先に走らせ、公開効果と計測所要を実測してから拡張する。throughput は3対の生点・範囲を示し、小差は検出不能と判定する。2 node 時間判定には smoke・build・verify・再走余地を含める。

6. **major｜brief P4・plan §3 Patch。** 根拠: `external/ccbench/cc/cicada/transaction.cc:934-938`、`patches/instr-cicada-trace.patch:119-130`、`patches/instr-cicada-version-lifetime.patch:848-879`、plan:40-42。両計器 patch は clear の**前**を変えるが、`read_set_.clear(); node_map_.clear(); return true;` は共通して残る。段 2 の「2 patch が必要」という結論は静的根拠だけでは成立しない。**修正案:** `node_map_.clear()` の後を小さい文脈として狙う**単一 patch**を先に試す。この位置なら flag を立てる時機は変わらない。clear 前へ移して1 fileにする案は参照解放前の `mainte()` となるため採らない。三形への厳密適用と macro 0 の前処理一致は**未確認**。

7. **major｜plan §3 verify。** 根拠: `external/ccbench/cc/cicada/transaction.cc:934-955`、`patches/instr-cicada-trace.patch:119-130`、plan:58。巡回なし・commit 件数一致だけでは、追加した ro 経路を実際に踏んだ証拠にならない。特に小さい検査 workload では timer 未満のまま終わりうる。**修正案:** trace 走で ro commit と、variant 側で実際に GC flag を上げた回数または公開回数の増分を記録し、非ゼロを受入条件にする。`READ_WTS_MISMATCH=0` と判定器の indeterminate 上限も保持する。

8. **minor｜brief「実物の読み」・P1、plan §1。** 根拠: `external/ccbench/cc/cicada/transaction.cc:859-888`、`external/ccbench/cc/cicada/util.cc:281-323`、brief:12-17,24、plan:1-11。brief の「GC flag は版安全に効かない」は強すぎる。flag は境界公開と回収実行を起動する。安全の根拠は slot が tx 中に保守的であることと GC の切断条件であり、P1 は YCSB・`group_commit=0`・slot 不変という範囲に限定すべきである。**修正案:** 段 2 の条件付き表現を採用する。

9. **minor｜brief の親実測・plan P4。** 根拠: brief:17、plan:42、`patches/instr-cicada-trace.patch:119-130`、`patches/instr-cicada-version-lifetime.patch:844-879`。親の probe が示したのは trace と vlife の相互適用だけで、**新 variant patch の三形適用も意味の一致も未確認**である。**修正案:** 親実測をその範囲に明記し、単一 variant patch の厳密適用を別に実測する。

## 2. 削除・縮小の提案

| 要素 | 判定 | 無いと結論・図・判定がどう変わるか |
|---|---|---|
| ro commit 後の `mainte()` と inert macro | **残す** | (a) の介入そのものが消える。根拠: `transaction.cc:859-893,934-955`。 |
| 小モデルの slot・flag・GC 切断と危ない slot 更新 | **残す** | 版安全の根拠と壊し正例が消える。根拠: `vhash-gc-connection-prototype/README.md:60-67`。 |
| 小モデルの独立 module | **縮小** | 新しい Cicada slot 状態は既存 `gc_floor` と同一視できないため小さな専用 module は妥当。ただし既存 `model.py` の探索器と `judge.py` の J1 を使える範囲で再利用し、履歴 adapter 以上の新しい汎用基盤は作らない。根拠: `tools/vhash_forwarding_model/gc_connection.py:11-20`、`judge.py:30-51`、plan:15-22。 |
| flag だけ／`mainte()` 全体の二形、clear 前 `mainte()` の追加場面 | **縮小／削除** | 本実装と stock、危ない slot 更新で主要判定は出る。flag だけは因果を示す小さな対照に限る。clear 前場面は slot 不変なら壊し正例にならず、結論を変える見込みが示されていない。根拠: plan:24-30。 |
| 2 本の variant patch | **削除候補** | 共通の clear 後文脈へ1本を当てられれば同じ介入になる。厳密適用は未確認。根拠: `trace.patch:127-130`、`version-lifetime.patch:876-879`。 |
| 新 C++ 壊し正例 | **削除** | 小モデル正例と md_14 の保持版変化の実測が既にある。今回の C++ では安全版の実発火、保持版の変化 0、判定器を優先する。根拠: `vhash-gc-connection-prototype/README.md:60-67,121-131`。 |
| 24 条件の全面格子、gc 1 ms、ro 50%、調整済み skew 0 | **縮小** | 主結論には S95/T95 の gc10、ro0 対照、wait10msR が必要。残りは診断の拡張であり、初回から全面実行しても結論の種類は増えにくい。根拠: `vhash-readonly-share/README.md:185-208`、plan:70-80。 |
| `smoke`・`verify`・計測 driver | **残す／縮小** | 適用・発火・正しさ・値の出典に必要。ただし独立 subcommand を増やすこと自体は成果物を変えない。既存 helper を使い、必要な実行入口だけにする。根拠: plan:52,58。 |
| 時間平均生存版の新計器 | **削除** | (a) の主判定は公開回数と間隔で足りる。終了時生存版を診断値と明記すればよい。根拠: `vhash_cicada_vlife.py:312,346-361`、plan:54。 |
| 4 panel・全条件 95% CI・全格子 fixture | **縮小** | 3反復の狭い差の判定力は乏しい。公開と境界の対照図、throughput の反復点、raw からの再生成で足りる。根拠: plan:60、`vhash-gc-connection-prototype/README.md:118-119`。 |
| 登録簿と必要な gate | **残す** | build 条件の意味と所有範囲の監査に必要。ただし新 patch／driver が実際に触れる entry に限る。`patches/ledger.json` は1件固定なので追加しない。根拠: `condition_meaning_gate.py:82-90`、`patches/README.md:874-879`。 |

## 3. P1〜P5 への判定

- **P1: 修正。** slot と snapshot を変えない YCSB、`group_commit=0` の範囲では支持する。flag は公開と回収を起動するため、無条件に版安全と無関係とは言えない。
- **P2: 修正。** slot を tx 中に上げる正例は md_14 の実測に対応する。flag 単独の早期上げは危険の正例と決めつけない。∞ への一時解除による反例はモデルで到達確認するまでは**未確認**。
- **P3: 同意。** clear 後の `mainte()` が最小の介入である。実測では ro 経路と flag 発火の両方を確認する。
- **P4: 反対。** 2 file 必須という段 2 の判断には同意しない。共通の clear 後文脈を使う1 fileを先に厳密適用で試す。成否は**未確認**。
- **P5: 修正。** 手続き単位の ro 指定と長い ro を両 build で一致させる必要がある。S/T の元条件を含む小さい主格子を先に走らせ、所要と効果を見て拡張する。

## 総括

この wave がまず示すべき差は、**固定 snapshot のまま ro commit に `mainte()` を加えると、公開 0 回の条件で公開が再開するか**である。その後も長い ro の slot が境界を押さえる時間は別問題で、現行計器だけでは測れない。主格子の S 条件、両 build の workload 一致、variant 経路の実発火を直せば、(a) の結論は判定可能になる。計測時間、単一 patch の適用、判定器結果は未確認である。