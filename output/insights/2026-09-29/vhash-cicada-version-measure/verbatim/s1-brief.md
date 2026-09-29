# 段 1 brief — md_2 Cicada 版探索・版保持の実測 (2026-09-29 03:45 JST、base 51f896352)

**研究前進:** VHash 論文 (paper-story-vhash 2026-09-29 版 §8/§9、出典メモ §29 段階 1) の H1・H2・H4 の上限見積り。stock Cicada で (a) 1 アクセスで辿った版数と目的の版の位置 (先頭 K 版より奥の割合、K=1,2,3,4,8)、(b) 奥へ行った読み取りのうち選択的 forwarding で避けうる上限、(c) GC 回収境界の遅れ・生存版数・保持時間を、長い tx 2 型 × gc_inter_us 3 値で図 3 枚 + 一次資料にする。完了判定 = 一次資料 (条件表・生出力所在・図・限界・確かめた/確かめていない) が揃い、全数値が生出力 JSON と照合可能。

**確定済み (実測・原典):**
- 版は新しい順の単方向リスト。辿る箇所 = read_internal / update (blind write) / validation (precheck・install・read-set 検査・write-set 検査 b)。timestamp = (rdtscp+boost)<<8|tid → wts 差から µs。
- 原典 CCBench 論文 §7.2: 長い tx = read phase 末の人工遅延、1 worker が担当、長短で ops 数・読み書き比同じ、YCSB-A・skew 0・1M records・10 ops、遅延 0〜10 ms、GC 間隔 10^0〜10^6 µs。
- stock (pin 511c9538) に使える長い tx の仕組みが無い: batch_* は宣言・表示のみ (旧 batch 分岐は 2023-07 公開時点でコメントアウト)、WORKER1_INSERT_DELAY_RPHASE=1 は未定義の `thid` と `WORKER1_INSERT_DELAY_RPHASE_US` を参照 (ビルド失敗は段 5 後の smoke で実測する)。
- patches/ledger.json は D18 第 4 類 ability probe 専用で entry 数 1 固定 (silo_ladder_rung1_contract.py:517)。既存 instr-* は README だけに登録。
- Cicada の Pegasus calibration は無い (registered/ に ycsb_cicada.exe 0 件)。Cicada 用 driver・trace も無い。

**親の provisional 裁定 (攻撃対象):**
- (P1) 1 本の計器 patch `patches/instr-cicada-version-lifetime.patch` に 2 macro を置く: `IZANAGI_CICADA_VLIFE` (計器) と `IZANAGI_CICADA_LONGTX` (長い tx の配線: batch thread = thid>=thread_num が batch_max_ope 個の操作を短い tx と同じ分布・読み比で実行 / thread 1 が read phase 末 (commit() 冒頭の既存位置) で FLAGS_worker1_insert_delay_rphase_us だけ待つ)。両方既定 0 で stock と前処理結果・命令列が一致。stock の壊れた WORKER1_INSERT_DELAY_RPHASE 分岐は触らず insight に記録 (上流修正は人間判断)。
- (P2) md_2 の「ledger.json の entry」は実施しない (契約で赤)。patches/README.md の表行 + 節だけで登録。
- (P3) driver は前例 (silo_policy_coverage.py / s3_mocc_lock_coverage.py) の慣行で `orchestrator/campaign/vhash_cicada_vlife.py`、materializer 登録簿と condition_meaning_gate の DefineSpec・分岐 witness に 2 macro を登録、sub-command `smoke` / `measure`、生出力 JSON は `output/insights/2026-09-29/vhash-cicada-version-measure/raw/`。作図 `tools/plotting/plot_vhash_cicada_vlife.py` (login で実行)。代案 = repo 外 probe。
- (P4) 位置の定義 = 物理位置 (latest から数えた next の回数、pending/aborted も数える)。forwarding 機会の見積り = 奥へ行った update-tx の read で、その時点の対象キーの先頭 K 版のうち committed 版 v_k について max(wts(v_k), L_T, ts+1) < min(e_k, U_T) となるものがあるか。L_T = 既読版 wts の最大、U_T = 既読版それぞれの「読んだ時点で直上にあった最も近い committed 版の wts」の最小 (後から入った writer・pending・書き込み側制約・一意性を無視 → 上限)。read-only tx (rts=MinWts-1 の固定 snapshot) は「対象外」として別計数。
- (P5) GC: leader の MinRts 公開ごとに遅れ = (rdtscp − MinRts>>8)/clk µs と公開間隔、回収時に版の生成からの経過と「上書きされてからの経過」(直前版の wts 基準)、生存版数 = chain へ install した数 − GC が切り離した数 (thread 別 counter を公開時に採取)、chain 長は read 64 回に 1 回全長を数える。
- (P6) 条件: 48 threads、YCSB {A: rratio 50 skew 0 (論文 §7.2), B: rratio 95 skew 0.9 (read-only 多・競合)} × 長い tx {なし, 待機 1 ms, 待機 10 ms, 操作数 1000} × gc_inter_us {10, 1000, 100000} = 24 条件 × 3 反復、extime 3 s。4 job (checkout 4 本) に割る。見積り ≈ 4 job × 12 分 + smoke 20 分 ≈ 1.1 node 時間 (< 2)。
- (P7) レコード数: calibrator 方針 D15 第二基準 (Masstree で飽和しない場合、maxrss が L3 の 4 倍を超える最小 N) を smoke job で N ∈ {1M, 2M, 4M} の stock build maxrss と lscpu の L3 から決め、決め方を一次資料に書く。1M は論文 §7.2 と同じ。

**不変条件:** 計器・長い tx 入り build の throughput を性能値にしない (規律 1)。既定 build は stock と前処理・`.text` 一致を witness で示す (D20)。正しさ主張をしない (Cicada は検査器未対応、common 4)。submodule gitlink・paper-story-vhash・ledger.json を触らない。計算は合計 2 node 時間未満。

**DW-O13 (witness の到達可能性):** 既定 build の `.text` 一致は、touched TU に `__LINE__` を展開する macro (ERR 等) があると挿入行で崩れうる。前例 instr-mocc は `#line` で行番号を戻した。plan は touched TU ごとに `__LINE__`/`__FILE__` 依存を列挙し、一致が到達可能な挿入形を示すこと。

**成果物:** patch + README 行・節、driver + test、DefineSpec・materializer 登録、作図、一次資料 `output/insights/2026-09-29/vhash-cicada-version-measure/README.md` (図・raw)、spool fragment (worklog・failures 候補があれば)。

**分割:** 実装は Codex author 1 単位 (patch と driver は bytes 契約で結合するため分けない)。段 2 plan 1 本、段 3 consult 1 本 (2 レンズ兼務)、段 6 review 1 本 + 焦点。受入全走は段 7 後。実測環境 = Pegasus gen_S (worklog 所在 / runbook)。
