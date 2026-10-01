# 段 1 brief — dev-wave-vhash-ceiling-vs-sota (md_42、T-2962)

作業木: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-ceiling-vs-sota (起点 local main d79fd3524)
依頼の逐語: /home/SFC/tanab/.claude/jobs/1423eb16/request-md_42.txt (と同 dir の common.txt 相当は /work/1/SFC/tanab/tmp/vhash-2026-09-29/common.txt)

## 研究前進 (1 行)
VHash 論文の芯 (D2322 項 1 = 保持の側) が「長い読み手で版が溜まる負荷 C で、修正済みの最良 Cicada (SOTA) より大きく速い」を満たしうるかを、人の試作の利得の天井で安く測り、継続/撤退の推奨を一次資料に出す (完了判定 = 事前記述を commit した後の 30 秒比較の比の中央値と基準の照合)。

## 確定済みの裁定・依頼の枠
- 比較相手 R = md_11 の観測最良 genome `B0 O1 P0 R1 W0` + ro-gcflag 修正 (`IZANAGI_CICADA_RO_GCFLAG=1`)。stock S は修正の効果を分ける対照として同じ round に置く (D2322 項 2)。名前は「md_11 の観測最良設定 + 修正」。
- 基準 (研究投資の基準、評価計画の統計判定は置き換えない): 代表点 30 秒比較の比 (腕/R) 中央値 ≥1.5 かつ隣接 ≥1.3 → 継続材料。有望点でも <1.2 で縮むのが境界年齢・版数だけ → 主論文候補から外す推奨。1.2〜1.5 は大きな残存費用の実測時だけ追加試作 1 度。stock だけに勝つ・GC 間隔を悪くした相手だけに勝つ・長い読み手が完了しなくなる・正しさ欠陥、の勝ちは数えない。
- 読み続ける tx を RA の外で前進させる試作はしない。区間 GC 試作 (md_18) に勝っても「SOTA に勝った」と書かない。
- 計算: 1 job 5 分目安で多数並行 (ユーザー 2026-09-30、記憶 measurement-must-split-across-nodes)。同じ点の比較腕は同じ job 内で順序均衡 (処置とノードを 1 対 1 にしない)。1 ノード 1 job・ノードローカル $TMPDIR・共有 repo 状態に書かない。合計 < 2 node 時間 (smoke 後に積算し直し、超えるなら腕か長時間点を削る。正しさ検査は削らない)。

## 実測済みの前提 (親、2026-09-30 20:2x、git apply fuzz なし、pin 68106660 の tar 展開物)
- (P1) 当たる: pin→`cicada-ro-gcflag-variant.patch`→`cicada-interval-gc-variant.patch`、pin→ro-gcflag variant→`cicada-forwarding-variant.patch`。
- 当たらない: `instr-cicada-version-lifetime.patch` (batchR の生成を含む計器) + 区間 GC / + 前進 C、区間 GC + 前進 C、`cicada-ro-gcflag-workload.patch` + 前進 C。
- 区間 GC の `--cicada_igc_debug_mode=3` (剪定を呼ばず install 経路は同じ) は patch に実装済み (variant.patch の mode==3 分岐)。mode 1 = 外すが再利用しない (既定)。
- hot v2 (md_37) は branch `worktree-dev-wave-vhash-hot-block-v2` にあり main 未着地。E の修理 (md_39) は main 未着地。→ (P2) 段 4 直前に再確認し、未着地なら hot 腕と待機型 2 点は「欠測」と書く (依頼どおり。旧 E・hot v1 で代用しない)。

## scope (成果物)
1. 最小の workload patch `patches/cicada-ceiling-workload.patch` (新 macro 1 個、既定 inert): batchR (1 worker が 1,000 read の read-only tx を続ける) と tx 単位の ro 指定率を、3 系統の木 (pin→V、pin→V→IGC、pin→V→FWD) と trace 木に fuzz なしで当たる形で全腕共通に作る。長い読み手の完了数は perf build でも出す (P3: 既存の per-thread commit 数を終了時に出すだけで hot path に計数を足さない案)。
2. 新 driver `orchestrator/campaign/vhash_ceiling_vs_sota.py` (smoke / verify / prelim / diag / compare / aggregate) と test。点 P1〜P4・腕 S / R / R+C-min(K=1、P2・P3) / R+IGC mode 3・mode 1 (P1〜P3)。
3. 作図器 `tools/plotting/plot_vhash_ceiling_vs_sota.py` と test (作図は login)。
4. 一次資料 `output/insights/2026-09-30/vhash-ceiling-vs-sota/README.md`: 事前記述 (C・M・SOTA、SOTA の穴、基準、腕ごとの発火条件、点の選び方、GC 間隔の固定規則、有望点・隣接点の選択規則、job 分割と見積り) を計測投入前に commit。後に表・図・推奨。
5. spool fragment (worklog・decisions・必要なら failures)、patches/README.md の節。条件 gate への新 macro 登録と、その pin 閉包の追随。

## 不変条件
- 規律 1: 性能値は TRACE・COUNT・VLIFE を外した build。throughput build に計数 macro を混ぜたら driver が拒否する。
- 規律 2: 各腕 (R・R+IGC mode 1・R+C) と新 workload の組を trace build + 判定器 (`orchestrator.verify --protocol cicada`) に掛け、巡回 0・integrity 0・C 行 = commit 数・READ_WTS_MISMATCH 0 を満たさない腕は失格。上限 indeterminate を certified と書かない。
- 所有外 (hot v2・md_39・既存 `cicada-forwarding-*`・`cicada-interval-gc-*`・`cicada-ro-gcflag-*`・M 計装・f_T・md_40/41・external/ccbench gitlink・paper-story-vhash) は編集しない。
- 既存 patch は使うだけ。新 patch は既定 0 で stock と同じ前処理結果 (inert)。

## 分割方針
- 段 5 は単位 A (patch + 条件 gate 登録 + 閉包) と単位 B (driver + 作図器 + test) の 2 子。B は A の macro 名・出力行の契約だけに依存 (契約は plan v2 で固定)。
- 計測は smoke 1 job → verify / prelim / diag を点・反復で割って同時投入 → 30 秒比較を反復で割って同時投入。

## 受入・実測環境
- 計測は Pegasus gen_S (`tools/pegasus/dispatch_compute.py --task generic`)、job 一時 file は `/work/SFC/tanab/tmp/vhash-ceiling-2026-09-30/`。受入は `tools/dev_wave_wait.py acceptance --lease-optional`、land は調整役「manager: parallel land」経由 (common.txt §6)。
