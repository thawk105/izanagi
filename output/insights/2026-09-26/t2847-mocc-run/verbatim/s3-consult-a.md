## 所見

**F01 — must-fix — 停止時の発火診断が成立していない。** [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:11) は SIGTERM handler での `T2847_FIRED` 出力を提案するが、既存 runner は timeout 時に子を強制終了し、通常終了時の destructor 出力を保証しない（[s3_mocc_mutation_proof.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/s3_mocc_mutation_proof.py:205)、[trace.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/include/trace.hh:49)）。handler 案も、数値整形と atomic の lock-free 性を含む実装契約が未定義である。停止は verdict なし、部分 trace の検証結果は参考欄、発火診断が取れなければ「診断欠落」と事前固定すべき。停止を「未発生」や「検出」に換算しない。

**F02 — must-fix — 多層発火の分類規則が矛盾する。** [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:63) は「期待した counter の N/I」を期待層で検出としつつ、他 counter も動けば別層で検出とする。V13/V15 の 4 thread は旧記録でも巡回・X・version dup が併発する（[設計書](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/output/insights/2026-09-22/t2847-verifier-detection-design/README.md:244)）。一 cell に両分類が付く。主分類は「期待層 X/P が正なら期待層で検出」、併発層は別欄とし、期待層がなく別層だけ正の場合に限り「別の層で検出」と定義するのが一意。

**F03 — should — V25 の `changed` と `committed` だけでは deadlock 発生を証明しない。** [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:17) の gate は、upgrade と RLL 再取得による自己待ち・CLL 重複を避ける方向で妥当である（[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:739)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:835)）。ただし `vioctr>0` は逆順保持の機会、`committed>0` はその取引が完走した証拠に留まる。停止を worker 間の相互待ちに帰属するには、停止時の各 worker の待機先と保持 lock を別途照合する。完走 S は「lock 順違反を発火させた完走履歴」と記し、deadlock の実証とは分ける。

**F04 — should — V34 の到達条件が粗い。** 4 site の `temp >= threshold` と `!(temp < threshold)` は同じ整数比較の真偽を持ち、971 行の `||` も plan の括弧で保たれる（[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:297)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:971)）。しかし合算 `reached>0` では 4 site 全部の評価を示せない。site 別 reached と境界評価数を出し、境界未評価なら「境界を実測した」と書かない。cold=21 は温度上限 20 より大きく境界評価は期待できない（[tuple.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/include/tuple.hh:12)、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:942)）。W の 6 cell は regime・thread の対照としては足りるが、4 site の境界対照とは言えない。

**F05 — should — 既存 4 本の S は五分類を埋められない。** 親 brief の「発火証拠がない S＝未発生」は根拠不足であり、plan の「発火未確認」に直す判断は正しい（[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/brief.md:20)、[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:5)）。ただしその場合、brief の「6 行を五分類で埋める」完了条件とは両立しない。V16 cold は source 上の未到達とできるが、default を含む他の S は「発火未確認」を独立状態として残すか、診断を追加する必要がある。旧記録の S を未発生の証拠として流用しない。

**F06 — should — pin C の旧期待への一般化は限定する。** 旧 patch と pin C は、P の sort 前後、X の writePhase 入口・書込前・公開前という計装位置と理由が一致する（[旧計装 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/instr-mocc-lock-coverage.patch:16)、[pin C](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:991)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/external/ccbench/cc/mocc/transaction.cc:1183)）。旧 `multiset` と pin C の `unordered_multiset` は要素数・重複度の比較という意味では同じで、pin 候補 patch と pin C は後者で一致する。しかし並行 schedule、巡回数、version dup 数、S/N の実測結果までは移せない。brief の pin C 先行 6 走も default の限定記録であり、hot/cold への外挿は不可。

**F07 — should — V16 の「早期解放」には副作用の帰属欄が要る。** patch は hot update で writer lock を外し、CLL 要素は残したまま、abort または publish 前に再取得する（[hot-update patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-hot-update-unlock.patch:19)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-hot-update-unlock.patch:38)）。X が検出する保持破れは狙いどおりだが、同一 tuple に複数回アクセスする経路や abort 時の lock 状態も変わりうる。hot の I/N を「X だけが原因」と一般化せず、X・version dup・巡回を別々に保存する。

**F08 — nit — 規律 1・2 の設計上の境界は概ね保てる。** 新 patch を transaction.cc 単独、裸の `#if` macro、未定義で元コード、TRACE=1 の別 build とする設計は妥当（[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/codex/s2-plan.md:15)、[CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/CLAUDE.md:58)）。ただし macro を gate に登録するだけでは genome から供給不能とは言えない。`screening_driver` は genome flags と登録簿の共通部分を gate request にする（[screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/orchestrator/campaign/screening_driver.py:112)）。既定値 0 に加え、実際の genome 生成側で新 macro が探索軸に入らないことを確認する。壊し patch の baseline 混入、verifier 受理拡張は plan 本文には見当たらない。

## cell ごとの期待の出所

| 行 | cell | 根拠ある事前期待 | pin C での限界 |
|---|---|---|---|
| stock W/U | hot・cold・default × t1/t4 | S、非空、X/P と他 integrity 0。job 内対照が前提 | pin C の先行 certified は一部 cell だけ。各 cell を再実走 |
| V13 lockskip | W の 3 regime × t1 | writer lock 省略により X、巡回なしなら I（[patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-lockskip-validation.patch:4)） | default t1 の先行値以外は旧 pin 由来。X の発火自体も実走確認 |
| V13 lockskip | W の 3 regime × t4 | X を期待。旧 pin は N・version dup 併発 | N の発生・件数は schedule 依存。default の pin C 先行 N も別 run |
| V14 permutation | W の 3 regime × t1/t4 | sort 後の `pop_back` を P `size-changed` が検出し、巡回なしなら I（[patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-permutation-erase.patch:4)） | P の機構期待は移せる。全 6 cell の I・巡回 0 は旧 pin の記録で、pin C では未確定 |
| V15 early unlock | W の 3 regime × t1 | 入口 X は通常 0、保持中の X を期待（[patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/patches/broken-mocc-early-unlock.patch:18)） | I は巡回なしの場合。hot/cold は旧 pin 由来 |
| V15 early unlock | W の 3 regime × t4 | 保持中 X、旧 pin は N・version dup 併発 | N は必然でない。別層は併発欄へ |
| V16 hot unlock | U hot × t1/t4 | hot update の解放で X。旧 pin の t1 は I、t4 は I＋version dup | pin C のこの patch の先行実走なし。t4 の verdict・件数を固定しない |
| V16 hot unlock | U cold × t1/t4 | 温度 ≤20、閾値 21 なので変異枝未到達、stock 同様 S を期待 | stock 異常なら帰属不能 |
| V16 hot unlock | U default × t1/t4 | 旧 pin は S | 温度と schedule 次第で発火しうる。S なら「発火未確認」 |
| V25 | W hot × t4 | 逆順保持の発火、相互待ちによる停止は仮説。完走 prefix の S・X/P=0 は条件付き（[設計書](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/output/insights/2026-09-22/t2847-verifier-detection-design/README.md:194)） | 停止に verifier verdict なし。worker 間待ちの帰属は別証拠が必要 |
| V25 | W hot × t1、cold/default × t4 | hot t1 は自己再取得を gate で除いた完走対照。cold/default は S または停止の観測枠 | gate の発火頻度も停止有無も未実測 |
| V34 | W の 3 regime × t1/t4 | 4 述語は値ごとに等価なので非空 S・X/P 等 0（[設計書](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/output/insights/2026-09-22/t2847-verifier-detection-design/README.md:208)） | 各 site と境界の到達は site 別診断が必要。cold の境界は到達不可 |

全行で stock が N/I、空、または integrity 不良なら同 cell の変異帰属は保留する（[前回裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s4-ruling.md:78)）。証人なし verifier の S は commit trace の完全性まで保証しない（[設計書](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mocc-run/output/insights/2026-09-22/t2847-verifier-detection-design/README.md:50)）。

## 未確認点

- 新規 V25/V34 patch はまだ存在しないため、無効枝の前処理結果、gate の厳密な実装、診断位置、TRACE=0 の除去は実物で再監査が要る。
- V25 の指定 W で gate が何回成立し、停止が worker 間待ちかは静的には決まらない。
- 既存 4 本の pin C hot/cold と V25/V34 は未実走。旧記録と brief の先行記録を今回の結果には算入できない。
- 計算ノードのテスト・build・計測は本相談では実行していない。

## 総括

pin C への直接適用は、旧 4 patch の変更箇所と X/P 計装の意味について静的には支持できる。投入前に直すべき中心は、**停止時の診断契約**と**多層同時発火の一意な分類規則**である。既存 4 本で S が出た場合の「発火未確認」も、完了表の正式な状態として扱う必要がある。