# 1. 所見

1. **must-fix — 所有範囲を越える。** brief 16 行と plan 46、74、80 行は条件 gate の production file と既存 test の編集を予定するが、依頼の所有指定は patch、新規 driver、一次資料、fragment 等に限る（`request-md23.txt:27-29`、`request-common.txt:15-20`）。根拠: [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/condition_meaning_gate.py:82) は実際に登録を要する既存ファイル。**放置すると、台帳と gate の証拠が所有権違反の変更に依存する。** 修正案: 親が所有範囲の裁定を得るか、登録を別の所有者の作業として明示して依存関係を組み直す。

2. **must-fix — P3 の不変条件に反する P4 は brief 内で未解決。** brief 29 行は hot を「物理列の先頭 K 件」と定義する一方、30 行は ABORTED を列に残したまま hot から除く。根拠: [transaction.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/include/transaction.hh:343) は status だけを変え、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:543) の validation は物理列を使う。**放置すると、read-only の選択版や update の `later_ver` が stock と異なり、正しさの主張が崩れる。** 修正案: plan 12、26、34–36 行のとおり ABORTED を hot に残し、第 2 段で飛ばす。

3. **must-fix — seqlock の読み側の順序が足りない。** plan 8 行は前後の `seq` を acquire load とするが、後ろの acquire load だけでは、その前の記述子 load が後ろへ移動しないことを規定できない。根拠: [tuple.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/include/tuple.hh:30) への複数 atomic 記述子の追加と、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:102) の置換が対象。**放置すると、同じ偶数を確認したつもりで異なる更新世代の `{wts, ptr}` を採用し、数値と正しさの根拠を失う。** 修正案: payload load と二度目の seq load の間に必要な acquire fence を含む、C++ memory model 上の読み取り手順を明記し、生成コードと競合試験で確認する。atomic 化自体は plan の妥当な修正。

4. **must-fix — GC 安全の論証が read-only の古い snapshot を取り落としている。** brief 32 行の「切り離し点より古い版を選ばない」は成立しない。GC は古い版をすべて消さず、可視性を保つ anchor 版を残す。根拠: [transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:831) は `ver_` の *次* から切り、[begin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:42) は read-only の rts を公表する。plan 28 行も安全性を「重点」に留め、成立条件を証明していない。**放置すると、切断・再利用との競合で古い読みや use-after-reuse を見逃し、正しさの主張が過大になる。** 修正案: `rts` 公表、`MinRts`、切断 anchor、hot snapshot 採用、再利用の順を場合分けし、切断済み ptr を reader が dereference できないことを示す。証明できない場合は reader に再確認または保護を追加する。

5. **must-fix — K=2/4 の性能値には対応する正しさ検査がない。** brief 36 行と plan 62 行は trace を K=1/8 に限る。根拠: [version.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/include/version.hh:75) の列と異なり、K ごとに hot の境界、shift、cold への接続が変わる。**放置すると、K=2/4 の図中の利得を検査済み variant の結果として扱えない。** 修正案: K=2/4 も代表 cell で trace と判定器を通すか、その値を明示的に未検証の診断値に限定する。

6. **should — GC 間隔は snapshot 年齢の操作ではない。** brief 34 行は `gc_inter_us` だけを古さの軸にし、plan 95 行は名称の注意に留める。根拠: [begin](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:42) は `MinWts−1` で snapshot を決め、GC は [gc_versions](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:806) で後から回収する。**放置すると、ro 比率×「snapshot の古さ」の図は GC 間隔の効果を古さの効果と誤表示する。** 修正案: 実際の snapshot lag と探索深さを記録して年齢軸を作る。操作できないなら図と結論を「GC 間隔別」に限定し、依頼の年齢軸は未達と記す。

7. **should — 計算上限の見積りは親の実測値から一般化し過ぎている。** plan 66 行の 5.3 秒/run は別の forwarding 実験の 33 件/173 秒、55 件/258 秒から取るが、元の条件は K=3、GC は最大 1000 µs、Cicada の build 設定も今回の最良設定と異なる。根拠: [forwarding の一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/output/insights/2026-09-29/vhash-forwarding-prototype/README.md:112)、[baseline tuning](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md:200)。**放置すると、0.94 node 時間という見積りを下回る保証がなく、2 node 時間制限を超えうる。** 修正案: smoke で K=8・GC=100000 を含む遅い cell、build、trace の実所要を測り、**3 job の Elapse 合計**で再計算する。予備時間と縮小後の必要な図の範囲も示す。

8. **should — 壊し版の「到達」と検出の帰属は別である。** plan 52–54 行の B1 は古い版を返しても、同一 snapshot の別 key に新しい版を読む等の依存がなければ巡回にならない。B2 は update の validation (a) に止められ、ro でも単発の古い読みだけでは巡回を保証しない。根拠: [validation](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:543)、[read-only commit](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:929)、[先例の帰属規則](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/output/insights/2026-09-29/vhash-cicada-verifier/README.md:96)。**放置すると、壊し patch が発火しても「判定器が検出した」と誤記するか、検出 0 を誤って陰性とする。** 修正案: patch ごとに到達、変更、commit、trace の R、一致する巡回 witness を固定して照合し、B2 が止められた場合は検出 0 とその理由を記録する。B1/B2 で帰属できなければ、依頼の「1 本以上検出」は未達とする。

9. **should — inert 確認の対象 TU が曖昧。** plan 48 行は YCSB target を比較し、他 target は「必要に応じて」とするが、patch は共通の `include/ycsb.hh` と `tuple.hh` に及ぶ。根拠: [ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/include/ycsb.hh:55)、[tuple.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/include/tuple.hh:24)。**放置すると、macro なしで stock と同一という主張が、実際に使った全 TU を覆わない。** 修正案: 性能・trace に使う全 TU の同一 argv の前処理結果を比較し、対象一覧と hash を残す。性能 binary では TRACE、COUNT、`ADD_ANALYSIS` が全 TU で無効な compile command と binary hash を確認する。

10. **nit — 「全 site」表の表現が強すぎる。** plan 16–26 行の列リンクの store/CAS は、検索した範囲では `latest_` 初期化、`Version` 初期化・`set`・`strRelNext`、install の二つの CAS、GC tail 切断を覆う。ただし [scan](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:429) は列を変更しないが別の reader 入口で、[gc_records](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/external/ccbench/cc/cicada/transaction.cc:845) は Tuple 自体を削除する。TPC-C 等も同じ `read_internal` を通る可能性がある。**放置すると、監査表が全 reader・寿命経路の保証だと誤読される。** 修正案: 「版リンクの変更 site は全件」と範囲を明記し、scan、record 削除、YCSB 以外は別の寿命・適用範囲として扱う。hot lock と `gc_lock_` の逆順取得や validation の lock 持ち越しは、plan の scope を守れば静的には見つからず、この攻撃は**不成立**。

# 2. brief の P 項目ごとの判定

| 項目 | 判定 | 理由 |
|---|---|---|
| P1 | 修正 | 記述子のみは妥当。件数・wts・ptr の atomic 化と実サイズ確認が必要。 |
| P2 | 修正 | fallback は妥当。C++ の読み側 fence と寿命の論証が不足。 |
| P3 | 修正 | plan のリンク変更表は概ね全件。ただし P4 と衝突し、reader・再利用は別途証明が必要。 |
| P4 | 不成立 | ABORTED を hot から消すと物理列との一致が壊れる。 |
| P5 | 修正 | 物理的な直前版を `later_ver` にする plan の修正が必要。 |
| P6 | 修正 | 「古い版を選ばない」は不成立。anchor、切断、再利用の順の証明が必要。 |
| P7 | 修正 | macro 分離は妥当だが、gate 編集は現行の所有範囲外。 |
| P8 | 不成立 | GC 間隔だけでは snapshot 年齢を操作・表示できない。 |
| P9 | 修正 | 交互配置は妥当。0.94 node 時間の外挿は未成立。 |
| P10 | 修正 | K2/4 の正しさ、壊し版の巡回帰属が不足。巡回 0 の上限は indeterminate。 |

# 3. plan から削れるもの

- plan 54 行の **B3** は、B1/B2 の帰属不能が判明するまで作成対象から外せる。必要になれば壊し点と期待 witness を先に固定して追加する。
- plan 72 行の格子数や腕順を実装どおりなぞる細かな unit test は絞れる。優先すべき検査は、欠落・重複・build 混同の拒否と、実 C++ の hot 更新・GC 競合である。
- plan 66 行の 0.94 node 時間という確定的な結論は削り、smoke 後の実測に基づく投入判断へ置き換える。

## 総括

最大の問題は所有範囲外の gate 編集、seqlock の読み順序、GC と再利用の寿命証明である。brief の ABORTED 削除案は plan が正しく退けている。plan の版リンク変更 site は概ね拾えているが、それだけでは全 reader の安全を示せない。K2/4 の性能値を検査済みと扱うには追加 trace が要る。GC 間隔を snapshot 年齢と呼ぶ根拠はない。親の 0.94 node 時間は異なる実験からの推測であり、上限判定には遅い cell の smoke 実測が必要。今回は静的検査のみで、テスト・計測は実行していない。