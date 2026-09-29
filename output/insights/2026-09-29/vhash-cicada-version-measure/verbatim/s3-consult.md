## レンズ A の所見

1. **must-fix** — forwarding 判定を read 時点で確定すると、その後の read が既読集合の許容区間を狭めることを反映できない。例えば最初の深い read では候補の可視区間が `[100,200)` で成立しても、後続 read の上限が 90 なら同じ transaction に共通の timestamp はない。候補と区間を保持し、transaction の read phase 終了時に全既読版との共通区間で判定する必要がある。根拠: `s2-plan.md:21,25`、`external/ccbench/cc/cicada/transaction.cc:108-125`。**放置時: 図 2 の forwarding 候補率が過大になる。**

2. **must-fix** — その判定を直しても「実現可能な forwarding の上限」とは呼べない。pending 版の後日 commit、後続 writer、write-set と node-set の検査を外しており、候補率は明示した制約下の楽観的な値である。逆に、対象 read 時点の先頭 8 版だけで判定すると、その後に先頭へ入る版を使う方式は対象外になる。「どの方式に対する上限か」を限定すること。根拠: `s2-plan.md:25,72`、`external/ccbench/cc/cicada/transaction.cc:481-600`。**放置時: H2 の上限という結論が図 2 の数値から導けない。**

3. **must-fix** — 物理位置と探索 hop は別指標にする方針は正しいが、先頭 8 版の採取のために追加で鎖を辿れば、stock の read が実際には辿らない版まで触る。特に pending 待機と aborted の読み飛ばしがあるため、「訪問した版数」と「選択版の位置」を、追加走査を除いた元の制御フローで記録する必要がある。根拠: `external/ccbench/cc/cicada/transaction.cc:99-125`、`s2-plan.md:8,23`。**放置時: 図 1 の探索長と図 2 の K 比率の意味が混ざり、計器によって版の滞留や abort も変わりうる。**

4. **must-fix** — GC 境界年齢の `rdtscp − (MinRts >> 8)` は実時間の遅れではない。timestamp には clock boost と thread ID が入り、差が負になる場合もある。境界年齢、全 worker の flag 待ち時間、公開間隔、detach までの時間を別々に測り、負差と欠測を明示すること。根拠: `external/ccbench/cc/cicada/include/time_stamp.hh:19-38`、`external/ccbench/cc/cicada/util.cc:281-323`、`external/ccbench/cc/cicada/transaction.cc:806-909`。**放置時: 図 3 が GC の「遅れ」を誤った単位と機序で示す。**

5. **should** — 生存版数 `N + install − detach` は鎖に接続された論理版数としてなら使えるが、INSERT、DELETE 後の record 回収、inline 版、`REUSE_VERSION` の物理実体数を表さない。上書き後の保持時間も、後継版の `wts` から求めるなら壁時計の保持時間ではない。対象 build の各 option と、計数対象から外した経路を raw に固定すること。根拠: `s2-plan.md:27`、`external/ccbench/cc/cicada/transaction.cc:708-719,806-864`、`external/ccbench/cc/cicada/include/transaction.hh:173-234`。**放置時: 図 3 の生存数・保持時間を物理メモリ量や実時間と誤読する。**

6. **should** — read-only は `begin()` で得た `rts` をその試行中は使う一方、`commit()` は `mainte()` を通らない。GC は全 worker の flag を待つため、read-only 比率の高い条件では `gc_inter_us` の設定値だけでは境界公開頻度を説明できない。read-only 試行率、flag 待ち、実公開間隔を条件別に残すこと。根拠: `external/ccbench/cc/cicada/transaction.cc:34-39,91-96,934-957`、`external/ccbench/cc/cicada/util.cc:284-323`。**放置時: 図 3 の差を長い tx の効果と誤帰属する。**

7. **should** — 論文 §7.2 の遅延型は「一つの worker が、短い tx と同じ操作数・読み書き比で、read phase 末に待つ」。worker1 の毎 tx 遅延はその実装例として妥当だが、batch 型は 49 番目の worker を追加し、1000 ops に変える別条件である。さらに YCSB は retry ごとに `begin()` し、1000 ops は探索・validation・abort に非線形の負荷を加える。2 型の発生回数、実行操作数、abort、実際の tx 継続時間を記録すること。根拠: `ccbench-paper.txt:1043-1056`、`external/ccbench/include/ycsb.hh:55-79,102-169`、`external/ccbench/cc/cicada/ycsb_cicada.cc:32-43`。**放置時: 図 1・3 の差を「tx の長さ」だけに帰せない。**

8. **should** — 既定 build の witness は到達可能だが、`#line` で論理行を戻すだけでは十分と事前確定できない。共有 `ycsb.hh` の変更は他 protocol の TU にも届き、前処理の論理行比較が一致しても `.text` は toolchain、path、定義値に依存する。gitlink `68106660` を preimage とした隔離 build で、Cicada の全 touched TU と共有 header を読む代表 TU の前処理、および stock と既定 patch の `.text` を実測すること。根拠: `s2-plan.md:3,33`、`external/ccbench/include/ycsb.hh:55-106,146`。**放置時: D20 の inert 証拠が成立せず、図の前提である stock Cicada との同一性が未確認になる。**

9. **should** — 登録簿の数 pin は plan が挙げた箇所を同時に更新する必要がある。一方、未登録 campaign module は現 hook の `_pegasus_admission_entry` では管轄外 `None` となるため、plan の「必ず拒否」は言い過ぎである。exact command の probe と driver 自身の計算ノード確認を採用すること。根拠: `s2-plan.md:47-51,65`、`hooks/guard_bash.py:614-629,1033-1058,1272-1282`。**放置時: テスト在庫が赤になるか、login での計測を hook が防ぐという誤った前提が残る。**

## レンズ B の所見

1. **should** — 図 3 枚のために恒久的な campaign driver、DefineSpec、materializer 登録をすべて増やす必要性は弱い。repo 外の一回限りの probe と immutable な raw JSON、plotter でも研究結果は得られる。ただしその案では再実行手順と build 権限の証拠が弱まる。恒久 driver を選ぶなら、build・実行・raw 保存に必要な最小機能に絞ること。根拠: `s2-plan.md:35-51`、`md_2.txt:15-39`。**放置時: 登録面の整備に時間を使い、2 node 時間以内に必要な実測と図が揃わない可能性が増す。**

2. **should** — 三 build のうち stock と既定 patch の build は D20 witness に必要で、有効 patch build も計測に必要である。一方、壊れた既存 delay macro の追加 build は本研究の数値に不要で、静的な「未定義参照の疑い」として留められる。失われるのは「現 toolchain でビルド失敗した」という実測証拠だけである。根拠: `s2-plan.md:39`、`external/ccbench/cc/cicada/transaction.cc:919-929`。**放置時: smoke の時間と build 面積が増え、図のための計算予算を圧迫する。**

3. **should** — 24 条件×3 反復は、H1/H2/H4 の初回上限見積りには広い。まず論文対応の skew 0・read 比 50 で長 tx 2 型と GC 3 値を測り、read-only 多・高 skew 条件は機序確認として追加する段階方式がよい。削れば B 条件への一般化は失うため、条件表に明記する。根拠: `brief.md:12-19`、`s2-plan.md:58-59,74`、`ccbench-paper.txt:1047-1057`。**放置時: 実測の完了可能性が下がり、未完の条件を混ぜた図になりうる。**

4. **should** — 3 候補 N の calibration は規律 4 の選定根拠を残すため必要だが、各 N で長い本走を行う必要はない。stock build の短い maxrss probe で選び、1M から変わった場合は論文との非同一性を明記する。反復 3 回は図のばらつき確認として維持し、smoke 後に総 node 時間を再計算する。根拠: `brief.md:18-20`、`s2-plan.md:39,41,75`、`common.txt:25-29`。**放置時: 「2 node 時間未満」は推測のままで、投入後に予算を超える。**

5. **nit** — brief の「stock に長い tx の仕組みが無い」は、batch worker の起動自体は既存 runner にあるため強すぎる。正確には「stock の YCSB workload が batch worker の操作数を変えず、既存 delay 分岐は未確認の不正な参照を含む」。また「read-only snapshot は固定」は一試行中に限り、retry の `begin()` で取り直す。根拠: `brief.md:7-10`、`external/ccbench/common/runner.hh:279-299`、`external/ccbench/include/ycsb.hh:55-59,102-113`、`external/ccbench/cc/cicada/transaction.cc:34-39`。**放置時: 一次資料が stock の機能と GC 停滞機序を過度に単純化する。**

## brief と plan への修正提案

1. patch の基点を、親が確認した gitlink `68106660686232781bca3be792a750d3e19d7a8a` に統一し、plan 冒頭の `511c9538` preimage 指示を直す。根拠: `brief.md:4,22`、`s2-plan.md:3,7`。
2. forwarding は read ごとの候補・可視区間を保存し、read phase 終了時に全既読版の共通 timestamp を判定する。図と本文の名称を「観測時点の楽観的候補率」にする。根拠: `s2-plan.md:21,25,58`。
3. 図 1 は「元の探索が辿った hop」と「観測開始ポインタからの物理位置」を分離し、追加サンプル走査の頻度と観測者効果を一次資料に記す。図 3 は境界年齢、公開間隔、detach、論理生存版数を分ける。根拠: `s2-plan.md:23,27,57-59`。
4. 条件表には通常 48 worker と batch 時の総 49 worker、read-only 率、実際の長 tx 回数・継続時間、各 build option、選定 N と論文の 1M との差を載せる。まず縮小条件で予算と計器の安定性を確かめる。根拠: `s2-plan.md:31,39,69-75`。
5. stock／既定 patch の D20 witness と登録簿・在庫 pin の検査は残す。未登録 module の hook 経路は推測で可否を決めず exact probe で確認する。根拠: `s2-plan.md:33,45-51,65`、`hooks/guard_bash.py:614-629`。

## 総括

**条件付き GO。**

- forwarding 判定を transaction 全体の既読集合でやり直し、主張を楽観的候補率に限定する。
- GC の時間・生存数の定義と、計器の観測者効果を一次資料に固定する。
- gitlink 基点と D20 witness を修正・実測する。
- 縮小条件の smoke 後に 2 node 時間未満を再計算してから本走する。