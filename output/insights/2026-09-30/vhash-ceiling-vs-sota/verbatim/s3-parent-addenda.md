# 段 3 に渡す親の追加事実と provisional 案 (2026-09-30 21:5x JST)

## 親の追加実測 (git apply fuzz なし、1 patch ずつ、pin 68106660 の tar 展開物)
- pin → instr-cicada-trace.patch → cicada-ro-gcflag-variant.patch → cicada-interval-gc-variant.patch: 当たる
- pin → instr-cicada-trace.patch → cicada-ro-gcflag-variant.patch → cicada-forwarding-variant.patch: 当たる
- (新 workload patch は未作成なので、その上への適用は未確認)
- 注意: 複数 patch を 1 回の git apply に並べると、失敗しても途中の file が書き換わった (親が一度踏んだ)。driver と検査は 1 patch 1 呼び出し。

## 計算の枠 (更新)
- ユーザー方針: 1 job 5 分目安で多数を並行投入。同じ点の比較腕は同じ job 内で順序均衡 (処置と node を 1 対 1 にしない)。1 node 1 job、node local $TMPDIR、共有 repo 状態に書かない。
- 1 タスク合計が 2 node 時間を超えそうなら、腕や点を削るか、投入前に land 調整役へ 5 点 (目的・見積り・分割・割付け・削った計算) を添えて相談し GO を得る。天井の判断に要る腕を削るより相談を優先してよい (依頼元経由のユーザー委任、2026-09-30)。

## 親の provisional 案 (攻撃対象)
- (P4) 天井の上限: P1〜P3 に「R から長い読み手を除いた走行」(R−LR: 同じ binary・同じ通常 worker 47 本・batch_th_num=0) を腕として足す。R−LR / R は、長い読み手が R に課す費用の総量 = 長い読み手の版保持を攻める機構が取り戻しうる利得の上限、と読む。これが 1.5 未満なら「長い読み手の版保持を攻める機構はこの点で 1.5 倍に届かない」と書く。hot 配置のように長い読み手と無関係な一般の高速化は、この上限の外である (別に書く)。
- (P5) job の組み方: build は build 専用の 1〜2 job で全 binary (perf・diag・trace) を作り、共有の一時領域 (/work/SFC/tanab/tmp/vhash-ceiling-2026-09-30/bin/) に sha256 付きで置く。計測 job は build せず binary を node local $TMPDIR へ写し、sha256 を照合してから走らせる。予備は「点 × round」を 1 job にし、両 GC 間隔と全腕を同じ job で順序均衡させる (P2 なら 6 腕 × 2 間隔 × 約 13 s ≒ 160 s)。プランの「点 × 間隔 × round の 24 job がそれぞれ build」は build 起動費用 (1 本 22.6 s × 腕数 + 依存物) が正味の走行を上回るので採らない方向。
