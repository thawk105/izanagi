# 段 6 裁定 1 — 2026-09-30 23:58 JST

入力: review-a.md (NO-GO)、review-b.md (条件付き GO)、焦点走 f1 (統合 commit `61aaf3714`、38 file: 3,860 passed / 10 failed / 5 skipped、赤の本文 focus-f1-reds.txt)。
親の実測: buildcache.py:3678-3700 の出口再照合は `resolve_evidence` に要求を渡さず、`proof_source_snapshot` の一致を要求する (A1 real)。pipeline.py:2235 は各反復で `res.verify_result = None` にし、成功時に戻さない。方策 driver は `result.certified` と WAL の abort 記録だけで history を作る (A2 real)。

## 所見の裁定

| 所見 | 裁定 | 処置 (fix 単位) |
|---|---|---|
| A1 出口再照合が要求を知らず必ず不一致 | real must-fix | 単位 1: buildcache の出口再照合に入口と同じ実効要求を渡す。要求ありの新規 build と cache hit の双方の test |
| A2 成功結果が driver に届かない | real must-fix | 単位 1: 要求つきの検証反復では、`verify_payload` (WAL の verify_done 記録に載る dict) に `gate_witness` 節 (= `result_to_dict(verify)["gate_witness"]` そのもの) を足す。要求なしの payload は 1 byte も変えない。単位 2: driver は当該 build attempt の verify_done 記録を WAL から読み、**全記録**に gate 節があり required=True・版 ≥ 2・D5 pass で、かつ `result.certified` のときだけ certified 行。記録 0 件・節の欠落は拒否コード |
| A3 全反復への照合 | real (A2 と同時に閉じる) | 同上 (全 verify_done 記録を照合) |
| A4 証拠種別が実態を表さない | real should-fix | 単位 2: `model_evidence_kind` は呼出し経路から明示する閉じた値 (`registered`・`fixture`・`unregistered`)。未登録を fixture と呼ばない |
| B1 登録外場面の反例で拒否 | **refuted** | 反例はどの場面で出ても仕様の違反であり、拒否は安全側 (規律 2)。段 4 裁定の「登録外の場面は記録だけ」は場面の**存在**を拒否しない意味で、反例の扱いではない。実装を維持し、この解釈を test 名か docstring 1 行で明示する (単位 2) |
| B2 flag 強制式の重複 | real should-fix | 単位 1: 小さな純粋関数 (例 `pipeline.effective_gate_witness_requirement(genome, requested)`) に一本化し、loop・pipeline・buildcache の呼出しはこれを使う |
| B3 版 ≥ 2 を key 完全一致が狭める | real should-fix | 単位 2: 現行 8 計数の存在と値を検査し 8 項だけ投影、追加 key は許す。追加 key を持つ正例 test |
| B4 coder 入力の再読込検査 | nit | 採らない |
| B5 M5 の bytes 試験の期待が現行出力由来 | real should-fix | 単位 1: 要求なしの snapshot serialize を、repo 内の既存 fixture か test 内の固定 literal bytes と比較する (現行出力から期待を組み立てない) |
| f1 赤 perf 閉包 (`test_official_perf_closure`) | real (自分起因) | 単位 2: `_REVIEWED_PERF_FILES` へ足した新 driver の行を外す (新 driver は perf file と判定されない。実測の赤: "Extra items in the right set")。既存の期待値は変えない |
| f1 赤 `test_reflux_campaign_issuer::test_signature_keeps_context_keyword_only_after_verify_fanout_hosts` | real (自分起因) | 単位 1: 既存 test は `run_campaign` の末尾 2 引数を (`verify_fanout_hosts`, `result_evidence_context`) に固定している。新 keyword を `verify_fanout_hosts` より前に置く (production 側を直す。test は変えない) |
| f1 赤 新 test 8 件 | real | 各単位: 赤の本文 (focus-f1-reds.txt) に従い、test の組み立て (J1 の反例に閉路を与える、capability の fixture を既存 test の build admission の作り方に合わせる、numactl の型など) を直す。production を test に合わせて緩めない |

## 変異の登録 (段 6 の real 所見に対して、fix 前)

| id | 変異 | 赤になるべき test |
|---|---|---|
| M13 | buildcache の出口再照合に要求を渡さない | 要求ありの build (新規・cache hit) が出口で止まらない test |
| M14 | 要求つき反復で verify_payload に gate 節を載せない | driver の WAL 照合で certified 行にならない test と、pipeline の payload test |
| M15 | driver が verify_done 記録の一部 (最後の 1 件など) だけを照合する | 2 件目の記録の gate 節が required=False の組で certified 行にならない test |

## 規模

単位 1 の production 追加は累計 ≤ 350 行、単位 2 は累計 ≤ 600 行 (段 4 裁定のまま)。
