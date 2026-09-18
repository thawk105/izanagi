# 段 1 brief — [T-2774] stock mocc (RWLOCK 版、e9e477ca) の静的反例候補 (a) を計算ノードで実走検証する

作成 2026-09-18 06:35 JST (06:50 JST に語彙を中立化し、実行 argv の綴りを pilot の現物へ訂正)。

前置き: 対象は学術研究用 DB ベンチマーク CCBench の並行性制御 (MOCC) の直列化可能性検査である。セキュリティ製品でも攻撃ツールでもなく、外部からの入力も扱わない。「DB 研究チームが自分のベンチマーク実装の並行バグ (非直列化可能な実行) を再現して原因を突き止めるための実験計画とコードレビュー」である。
base = local main `d2ebef7a4` (worktree `worktree-dev-wave-t2774-mocc-torn-read-probe`、clean)。

## 研究前進
- 進む主張: D2114 項 2「指定した二つの CC 実装 (Silo / MOCC) で合成・評価手順を実証した」。その前提は D2114 理由節「mocc は確実な第 2 成功例ではない (G2 anomaly 5/42 が実装由来か hook 由来か未確定)」の解消。T-1892 (42 走) は原因 3 分岐 (1 実装 / 2 hook / 3 verifier 仮定) を分けられず、T-1943 (1 cell) は `no-g2` で分岐に触れなかった。
- 完了判定: 固定 cell で G2 が再現した走ごとに discriminator の結論 (`supported` / `contradicted` / `indeterminate`) が付き、「(a) の順序と整合する証拠が得られた / 得られなかった」を 1 行で言える。加えて対照 build による必要性確認 (2 load の間の順序 (interleaving)を閉じた build で G2 率が 0 か) が採られれば「根因候補 → 根因 (この cell で)」へ 1 段上がる。certified 昇格判定・pin 前進・変異探索の解禁は変えない。
- 土台ではない (直接の実測)。

## scope (依頼の逐語に対応)
0. **実在欠陥の局所修正 (repo、Codex author):** 生死確認 job `4936.nqsv` (06:29 JST、9 秒で終端) は hydrate 段 `mocc_trace_pilot.sh:1534` で `fetch_third_party: unsupported operand type(s) for |: 'type' and '_LiteralGenericAlias'` により rc=2。原因 = T-548 (09-16) で `fetch_third_party.py` が driver (`silo_ladder_rung1`) を import するようになり、推移的に `orchestrator/verifier/parse.py:71` の module 直下 alias `bool | Literal[...] | None` (3.10 専用の実行時式、2026-08-20 導入) へ到達。1534 行だけが素の `python3` (計算ノードでは 3.10 未満)。checker (1756) / verifier (2203) / discriminator は ≥3.10 選択済み。他 script (`b4_binary_record.py`、`s3_mocc_lock_coverage.py`) は `sys.executable` で同型なし → 単発。修正 = hydrate 呼び出しに既存と同型の ≥3.10 interpreter 選択 (import 可否 + `sys.version_info >= (3, 10)`) を先行させ、契約 test を 1 本足す。`orchestrator/verifier/` は触らない。failures へ F (T-548 回帰、テスト緑・実 job 断線の 4 件目)。
1. **腕 A (依頼の本体、新規コード 0):** `tools/pegasus/submit_mocc_trace.sh --t1943-g2-discriminator` を固定 cell で N 本投入し、G2 走の `discriminator.json` を集計する。生死確認 1 本 (request `4936.nqsv`、06:28 JST 投入) → 6 本 × batch。N の下限 = 24 (P(≥1 G2) ≈ 0.95 @ 0.119)、上限 = 42 (T-1892 と同数、≈ 0.995)。
2. **腕 B (対照 build による必要性確認、job dir の probe、Codex author):** validation の版→counter 別読み (1010〜1024) と cold 読みの counter→body→版 (322〜352) の順序を揃える最小の診断 patch (対照 build) (job dir、repo へ入れない) を e9e477ca に当て、同 cell を K 本走らせて verifier の G2 率を測る。0/K なら (a) の必要性が対照 build による必要性確認で示される (memory: 機構の必要性は対照 build による必要性確認で確かめる)。同じ runner で patch 無し (stock) K 本も同一 node・同一 build 条件で並べる (同時刻の対照)。
3. **仮説 cell (観測のみ):** 依頼の「多 thread・hot key・小 value で確率が上がる」は固定 cell (48 thr・skew 0.9・10,000 rec・64 byte 行) で既に高側にある。cell を変えると discriminator (`EXACT_WORKLOAD` 束縛) は使えないので、verifier の G2 率だけを腕 B の runner で 1〜2 cell (例: records 1,000 / skew 0.99) 取る。主結論には使わない。
4. insight (docs のみ) `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` + spool fragment (worklog / decisions)。CCBench 改変は insight 構造化まで (D16 の「本物のバグ修正 → master 還元」は人間判断)。

## 確定済みユーザー裁定・不変条件
- 規律 2 (verifier を緩めない)・規律 3 (構造化)・規律 7 (旧判定は不変)。(b) absent 非検査は同梱しない。probe は job dir、repo へ入れない。[T-2772] と独立 (同 wave が `patches/` と登録簿へ書く、本 wave は触らない)。gate・検査・台帳・一般化の追加は scope 外。
- 止める裁定の検索: D2104 項 13 (非 silo の between-run 実測保留) は性能実測の話で TRACE=1 正しさ実走は射程外 (T-1892 / T-1943 の先例)。D1360 (stock 専用経路は解禁しない) — 本 wave は trace-hook 付き e9e477ca を使う。D2134 項 2 は「実走未確認、還元判断はユーザー確認待ち」— 本依頼がその確認。

## 実測した前提 (段 1 前)
- 現物 (`transaction.cc` @ e9e477ca): cold 読み = tidword → counter spin → absent → body → tidword 再読 (lock は tidword に無い)。validation = tidword 比較 → counter 読みの 2 load。writePhase = memcpy → publish → unlockCLL。**(a) の順序は現物で成立。**
- **派生 (P1):** validation の2 load の間の順序 (interleaving) (段 4〜5) だけで torn body 無しに両辺 rw の長さ 2 cycle が commit できる (W: lock x → validate y / R: lock y → x 版 T0 → [W publish + unlock] → x counter 空き)。42 走の 5 件の形 (長さ 2・両辺 rw・別 thid・同 epoch・tid 差 1) と一致。discriminator の対応 = `supported` ⇔ 旧版を本当に読んだ (validation 2 load の間の順序 (interleaving)のみ)、`contradicted` ⇔ payload が新 (読み段の2 load の間の順序 (interleaving)も踏んだ)。**どちらも実装由来の証拠**であり、hook 由来 (分岐 2) は `contradicted` の一部にしか残らない。
- witness (`ae6880f7`) は value 先頭 8 byte に (magic<<48 | producer txid) を刻む。YCSB 行は `alignas(64) id_ + val_[4]` = 64 byte なので stamp は id_ 領域、8 byte 整列 load は x86 で原子的 → `contradicted` は「版は旧、payload は新」の明確な不一致として出る。
- 既存経路の実績: T-1943 job は起動 151 秒で discriminator.json まで到達。T-548 (09-16) の調達変更後は compute 未実走 → 生死確認を先に投入済み。
- (P2) 「小 value で確率が上がる」の向きは疑わしい: validation 2 load の間の順序 (interleaving)に value size は無関係、読み段の tearing は大きい value ほど起きやすい。本 wave は value size を変えない (witness が 8 byte 以上を要求、cell 固定)。
- (P3) 腕 B の K と node 配分: K=24 stock + 24 fix を 2 node に分け、1 node ≈ build 2 分 + 24 × (3 秒 + verify ≤ 2 分) ≈ 50 分。walltime 01:30:00。generic dispatch は env を渡さない (cache root・scratch は argv)、`PBS_JOBID` 不在、pristine staging の masstree は `config.h` 不在 (warm-up build 1 回)。

## 成果物の形
- insight README: 束縛 (source_oid・binary sha・policy sha・request ID 一覧)、腕 A の表 (走 × verdict × discriminator 結論 × comparisons)、腕 B の表 (arm × K × G2 件数 × CI)、(a) との整合の判定 1 行、限界 (cell 固定・K の検出力・対照 build による必要性確認は十分条件でない)、CCBench 側への扱い (D16、人間判断)。probe は job dir に保全し sha256 + byte 数で同定。
- repo の実装面差分 = scope 0 の job script 局所修正 + 契約 test 1 本だけ → その単位に変異 matrix (負例: 素の `python3` へ戻す / 選択条件の版比較を外す、正例: 既存の checker/verifier gate の等価変異は SURVIVED 期待にしない) を登録。probe (job dir) は matrix 対象外。受入全走は免除しない。

## 並列分割
- 段 2 plan 1 本 (read-only)、段 3 レンズ A = 正しさ境界 (P1 の順序論証・discriminator の対応表・対照 build (診断 patch) の正しさ)、レンズ B = 実効性 (job script 修正の鎖の網羅・runner の投入形・env・時間・検出力・cell 固定の帰結)。段 5 author 2 本 (unit 1 = job script 修正 + test、repo / unit 2 = probe patch + runner、job dir)、段 6 review 2 本 + fix。腕 A の再生死確認は unit 1 の後、batch はその緑の後。

## 変更面 (実アンカー)
| 面 | path | 種別 |
|---|---|---|
| job script 修正 | `tools/pegasus/mocc_trace_pilot.sh` 1534 行の hydrate 呼び出し (前に interpreter 選択 block を置く) | repo 実装面 (unit 1) |
| 契約 test | `orchestrator/tests/test_mocc_trace_job_contract.py` (hydrate interpreter gate の test を 1 本追加、既存 marker 抽出 test と同型) | repo 実装面 (unit 1) |
| failures | `docs/spool/` の failures fragment 1 (T-548 回帰) | 新規 docs |
| insight | `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md` (+ `verbatim/`) | 新規 docs |
| spool | `docs/spool/<fragment>` (worklog 1、decisions 0〜1) | 新規 docs |
| probe patch | job dir `probe/mocc-close-version-counter-gap.patch` (対象 `cc/mocc/transaction.cc` @ e9e477ca の 316〜356、1008〜1039) | repo 外 |
| probe runner | job dir `probe/t2774_probe.py` (checkout e9e477ca → patch → cmake TRACE=1 (T-1943 と同 argv) → K 走 → verifier) | repo 外 |
| 腕 A 成果物 | job dir `attempts-A/` + worktree `output/env/pegasus/mocc-trace/job-staging/<PBS_JOBID>/` (tool 所有 untracked、受入前に job dir へ退避) | repo 外 / 一時 |
