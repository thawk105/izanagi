# [T-2851] 段 1 brief (親、2026-09-22 JST、base main 8fd2a2f5c)

研究前進: EA&B 中心命題の第 3 仮説「探索時の勝者と未知 workload で採るべき候補は異なる」(gap-analysis §3・§4 P4、codex-consult-1 優先 3) を
HARKing なしで検定できる状態にする。完了判定 = 留保条件・比較対象・同等幅・CI・追試規則を固定した事前登録 v1 が main に着地し、
[T-2850] の探索開始より前に留保が効力を持つこと。計算投入・選択結果を使う評価走・runner 実装・gate/検査/台帳の追加は scope 外。

scope (変更面): 新規 `docs/unseen-condition-transfer-preregistration.md` (本書)、`docs/README.md` へ 1 bullet、spool fragment
(worklog 1 + decisions 1)、insight `output/insights/2026-09-22/t2851-transfer-prereg/`。コード・テスト・runner・phase doc は触らない。

確定済みユーザー裁定: D2212 (EA&B 第一候補・否定的結果も主要成果、計算は 1 タスク 2 node 時間以上で都度確認、旧系列は必須経路外、
凍結 chain を新設しない、TPC-C 必須)。依頼文 (本 wave の引数): p2_2_flag_opt を外さない、既存の事前登録の作法 (凍結・改訂契約) で作る。

不変条件: 絶対規律 1〜7 (trace-disabled で性能、別 build・別 run で検証、anomaly は即失格、測定事実は後から無効化しない)。
D1789 (発効後は bytes 不変・Erratum 追記のみ)、D1790 (測定時点版と解析規則版を別定数)、hash 自己参照禁止 (F36)。
8b holdout (読み比率 80/20・skew 0.9・rmw 0) の値を留保に使わず、`ycsb_<軸>=<値>` 書式の literal を本書に書かない (三軸走査 hit 回避、F1013)。

実測した前提 (調査子 2 本 + 親の検算):
- 学習条件 = 3 workload (読み比率 5/50/95) × skew 0.9・rmw 0・1,000,000 レコード・48 thread・max_ope 10・extime 3 (p2_2.py WORKLOADS/RECORDS…、pipeline.py S2_FLAGS)。
- 5 条件は CCBench 既存引数 (ycsb.hh の ycsb_rratio / ycsb_zipf_skew / ycsb_max_ope / ycsb_rmw、common.hh の thread_num) で変えられ改変不要。
- Pegasus = 1 socket 48 物理コア HT 無効 → thread は 48 が上限。
- p2_2_flag_opt = Silo 専用、workload 別 genome (s1_known_axes_freeze.EXPECTED_P2)。MOCC の既知最良は見つからず。
- Pegasus 正式 protocol の静的 backoff: wh 10 µs +63.5%、bal 5 µs +14.4%、rh 2 µs −5.78% (無 backoff = stock に負け)。
- 既知結果: rr20/80 (8b floor 較正)、rmw=true は rr50 で Silo stock と ability-probe 変種 (T139 rung1)、thread 1〜48 は SS2PL、
  skew 0 は cygnus 較正と SS2PL、max_ope 1/5 は trace 自己検査のみ、tuple 2M/4M は較正、TPC-C 実行 0 件。25/75・0.7/0.99・max_ope 20 は 0 件。

(P1)〜(P10) = 親の provisional 裁定・攻撃対象:
(P1) 操作的定義: 読み比率=ycsb_rratio、競合=ycsb_zipf_skew、thread 数=thread_num、txn 長=ycsb_max_ope、アクセス集合の重なり=ycsb_rmw
     (txn 内の読み集合と書き集合の重なり)。レコード数は 1,000,000 固定 (規律 4、較正値)。
(P2) 水準と配置: 読み比率 {25 (錨 wh)、75 (錨 rh)}、skew {0.7, 0.99}、thread {12, 24}、max_ope {5, 20}、rmw {1}。
     3 錨の周りで 1 因子ずつ動かす OFAT: 2 + 3×7 = 23 留保条件。錨 3 点 (学習条件) も同じ測定で測る → protocol あたり 26 cell。
(P3) 比較対象: R0 stock、R1 p2_2_flag_opt(錨) (Silo)、R2 強い静的設定(錨) = wh 10 µs・bal 5 µs・rh 無 backoff (stock と同一で重複除去)、
     各手法の選択結果 = [T-2850] の全 (課題, 手法, 独立探索) の選択を identity 重複除去して全部。MOCC は R0 のみ確定、R1/R2 相当は発効前の版で決める。
(P4) 留保の効力は本書の main 着地時点。候補凍結前は留保条件で stock を含め 1 走もしない。生成・選択の入力に入れない。
(P5) 測定: trace-disabled、1 job = (protocol, cell, cohort) を 1 node、n = 8 block、block 内は全候補 1 走ずつを hash 導出の固定乱順。
(P6) 推定量 = block 内 log 比の平均、95% t 区間 (df = n−1)、同等幅 δ = ln(1.03)。4 分類 (優越/退行/同等/判定不能)。cell 単位は無補正、
     多重性の防壁は全 cell の追試 (P7)。手法単位の比較は記述のみ。
(P7) 追試: 全 cell を第 2 cohort で再測定。原 cohort の最終 job の翌暦日 (JST) 以降、(protocol, cell) ごとに別 hostname。
     両 cohort で同じ分類のときだけ主要結果。統合で主張しない、第 3 cohort で決着させない。
(P8) 正しさ: 非 stock 候補 × 留保 cell ごとに trace-enabled 検証 1 本 (別 build・別 run、verifier 版は発効時固定)。anomaly 1 件で候補ごと失格。
(P9) 凍結: v1 初版。留保の効力 (着地) と測定の発効 (ユーザーの計算確認 + D) を分ける。着地後は留保集合の削除・変更不可、追加は別枠。
     測定の発効後は bytes 不変・末尾 Erratum。解析器 pin なし (scope 外)。
(P10) 閉じないもの: TPC-C の留保 (TPC-C の選択結果が出る前の版で追加)、cygnus 96 thread、レコード数軸、交互作用、手法単位の推測、認可・実装。

受入・実測環境: 計算ノード投入なし。検査は login の check_docs.py・三軸走査・受入全走 (land 前、tools/dev_wave_wait.py acceptance)。
分割方針: docs-only の軽量版。段 2 (codex plan) は省き、本 brief を plan とする。設計択一が割れるので段 3 は read-only codex 2 レンズ
(A: 統計設計と推論の妥当性、B: 留保の漏洩・HARKing・実行可能性と過剰)。段 5 は親が本文を書く (実装面なし、変異 matrix 免除)。段 6 は read-only review 1 本。
