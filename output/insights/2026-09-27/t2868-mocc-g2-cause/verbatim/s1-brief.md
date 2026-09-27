# [T-2868] 段 1 brief (親) — MOCC read-heavy literal 候補の G2 6 件の原因切り分け

- 研究前進: VLDB 稿の「正しさゲートが探索の候補を実際に reject した」実例に t2849-mocc-conn §4 の 6 件を使えるかを決める。完了判定 = 6 件それぞれについて (i) verifier の誤検出 (ii) literal 差し込みの意味変更 (iii) MOCC 本体の欠陥 の 3 分岐を、排除 / 支持 / 未決の証拠水準つきで表にした insight。
- 起点: local main `339d7c188` の fresh worktree `worktree-dev-wave-t2868-mocc-g2`、開始 gate rc=0 (job dir `startup-gate.log`)。job dir = `/work/SFC/tanab/tmp/t2868-mocc-g2-20260927/`。
- 材料: `output/insights/2026-09-27/t2849-mocc-conn/README.md` §4、保全 trace `/work/1/SFC/tanab/izanagi-repro-archive/t2849-mocc-conn-20260926/main/<campaign>/…/performance/<rep>/{inventory.json,archive/trace_<thid>.log.zst,patch/ccbench.diff.zst}`、digest `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2849-mocc-conn/trees/m-rh-{bo,random,sweep}/output/exploration/campaigns/<campaign>/s4_loop_digest.txt`。anomaly の campaign 6 件 = bo `c90fb5b6` (5 µs)・`4b49eb95` (135)、random `5fb08b9c`・`a1b31b3b` (10・651)、sweep `0add62d7`・`da63cf3f` (5・20)。
- 既往: stock MOCC (pin 511c9538 系の e9e477ca、10,000 record・rr50・zipf 0.9) で同形 G2 が witness off のとき再現 (T-1892 5/42、T-2774 7/120、T-2779 通常 5/120・BACK_OFF=1 2/120)、診断 patch (validation の版再読 + cold 側 abort) で 0/120 (片側 p=0.030、2 変更を束ねた介入)。静的候補 (a) = validation の版と lock counter の別読み (T-2757 §3.2)。D2148 項 13: 上流へは観測と限界の報告まで、送信は人間、診断 patch 取込・pin 前進・certified 昇格は認可しない。

## 親の実測 (brief 前)

1. literal は `patches/silo-backoff-fixed.patch` の `include/backoff.hh` `Backoff::backoff()` 内 hole で `now_backoff` (abort 後の spin 量) だけを差し替える。MOCC の呼出しは `cc/mocc/transaction.cc` の abort 経路 (read/write set を消した後、`#if BACK_OFF`) と leader の `leaderBackoffWork`。validation・lock・trace hook の source は差し込みの diff に入らない (保全 patch の実 diff は未照合 → 段 5 probe で照合)。
2. witness 6 件 (digest): 全件 G2・長さ 2・両辺 rw。commit 版の組 (epoch, tid) = (63,592/593)、(56,759/760)、(71,917/918)、(66,3535/3538)、(50,4070/4071)、(1,328/329)。key は 0〜3 と 0x61。最後の 1 件は epoch 1 (走行開始直後)。
3. trace は per-thread `trace_<thid>.log` (C/R/W/X/I/P/E 行、`orchestrator/verifier/parse.py` 冒頭)。bo `c90fb5b6` の保全は performance 4 反復 + legacy 1 で、digest の「rep 5」とどの保全 dir が対応するかは未同定。inventory に verifier argv (`python3 -m orchestrator.verifier <dir> --json --expected-commits N --protocol mocc --ccbench-root <patched pin C>`) と verifier module の sha256 が残る。
4. 比較の検出力: candidate 6 件 / 反復数 (未集計、概ね 100 前後) に対し stock 0/35 反復 (7 slot × 5)。この差は有意でない見込みで、stock 0 件は「stock では出ない」の証拠にならない。

## scope

- 段 A (再検査、計算ノード): 6 件の anomaly 反復を保全 trace から同定し、(a) 保全時の verifier を同じ argv で再実行して witness が再現するか、(b) verifier を使わない独立抽出 (生の C/R/W 行) で 2 取引の読み版・書き版と、関わる key の版の連鎖 (直前・直後の W 行) を示し rw 辺 2 本が trace と整合するか、(c) 保全 patch の diff が template + literal だけか、を 1 job で出す。
- 段 B (追加走、段 A の後): literal を実行しない stock 本体を同じ cell (48 thread・1,000,000 record・rr95・zipf) で N 反復 trace + verify する最小の対照を設計し、実測単価で見積もる。合計 2 node 時間以上ならユーザー確認。
- (P1) 親の provisional 裁定・攻撃対象: literal は abort 後の待ち時間だけを変える timing 介入で、MOCC の validation の意味を変えない。したがって分岐 (ii) は「意味の変更」としては静的に排除でき、残るのは「timing が本体の間隙を露出させた」か否か。
- (P2) 親の provisional 裁定・攻撃対象: 段 B の対照は BACK_OFF=0 (backoff 呼出しがコンパイルで消える stock 本体) が最小。literal を一切実行せずに literal 小値と同等以上の throughput 域を作れる。stock 適応 backoff の反復追加は throughput 域が違うので対照にならない。
- (P3) 親の provisional 裁定・攻撃対象: hook の記録誤り (trace が実際に読んだ版と違う版を書く) は trace だけでは排除できず、本 wave では「未決」として残す。

## 不変条件

- 規律 2: reject は reject のまま。verifier・判定条件・受理集合を 1 文字も変えない。再検査の結果がどうであれ、元の slot 判定を書き換えない (規律 7、追記のみ)。
- 規律 1: trace-enabled build は正しさ検査にだけ使い、その throughput を性能主張に使わない。
- D16/D18/D20・D2148 項 13: CCBench を repo 内で改変しない。上流送信・診断 patch 取込・pin 前進はしない。
- 切り分けが済むまで論文の主張に使わない。gate・検査・台帳・一般化の追加は scope 外。

## 成果物

- insight `output/insights/2026-09-27/t2868-mocc-g2-cause/README.md` (CCBench 本体の欠陥と判断した場合は `output/README.md` の形式)、worklog fragment、job dir の生成物 (repo 外)。
- 実装面は repo 外の probe だけ (Codex author)。repo のコード変更は 0 の見込み。

## 分割

- 段 2 plan 1 本 (read-only)、段 3 敵対 1 本 (過剰・削除 + 正しさ境界)、段 5 author 1 本 (段 A probe、段 B は段 A 後に同じ木で)、段 6 read-only レビュー 1 本。
