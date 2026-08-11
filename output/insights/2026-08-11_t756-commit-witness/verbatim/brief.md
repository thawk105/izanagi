# 親 brief — [T-755] Q1(a) / [T-756] trace 完全性 v2 (単独 wave 先行)

```text
wave: dev-wave-t756-trace-v2 / branch worktree-dev-wave-t756-trace-v2
base: 0c0fbf25 (local main と乖離 0)
ccbench pin: d706650cdb31e442bef45b9b4216951d4fb40969 (本 wave では 1 bit も動かさない)
ユーザー裁定: [T-755] Q1〜Q3 全問 (a) — trace v2 化を単独 wave で先に land、移植の初手は mocc、案 B 偵察は解禁しない
command 引数: 規律 1 (D14 契約) と規律 2 を厳守、cross-protocol 比較の実測は射程外
```

## 1. 対象の負債 (一次資料で確認済み)

`orchestrator/tests/test_verifier.py:601`–`638` の characterization 2 本が、現行 verifier が
**certified にしてしまう**ことを意図的に assert している。

- **FN-1 (末尾欠番)**: 欠番検査が `expected = max(txid)+1` (`verifier/parse.py:217`–`223`) のため、
  txid 最大側の trx が丸ごと消えると欠番ゼロ扱いになり cycle 相手が消えて certified。
- **FN-2 (trx 尾部欠落)**: C 行が R/W 件数を持たない (`external/ccbench/include/trace.hh` schema)
  ため、「R/W ゼロの trx」と「切り詰められた trx」を区別できず certified。

## 2. scope

- **S-1 (実装)**: **独立 witness による完全性検査**。verifier に「期待 commit 数」を渡し、trace 内の
  committed txn 数と不一致なら integrity 違反 → `certified=False` (indeterminate) に倒す。
  witness は trace-hook 由来ではなく **CCBench 自身の counter** (`common/result.cc:48`
  `commit_counts_:`、`displayAllResult` 内で無条件出力) を pipeline が渡す。
  `batch_commit_counts_` が非 0 の run は帰属不能として fail-closed。
- **S-2 (実装)**: `test_characterization_tail_txid_gap_is_false_green` を反転する
  (witness 付きで indeterminate を期待する形へ)。positive control (欠落を注入して赤) と
  negative control (完全な trace で緑) を対で置く。
- **S-3 (返す)**: **C 行 R/W 件数 + txn 終端マーカー = 真の trace 形式 v2 は本 wave の権限外**。
  実測した理由: (i) `external/ccbench` の trace-hook は D16 により submodule `izanagi-trace`
  行きで、変更は gitlink 前進を伴う。(ii) `orchestrator/campaign/s8b_approved.py:67`
  `CCBENCH_FULL_SHA` は**承認定数**で `orchestrator/tests/test_s8b_approved.py:58`–`64` が実
  gitlink と照合する (追認禁止)。(iii) `origin/izanagi-trace` は d706650 のままで push は人間手番。
  (iv) `s8b_floor_campaign.py:488` が live gate として同定数を要求する。
  → `test_characterization_txn_tail_loss_is_false_green` は反転せず、残債の帰属注記だけ更新し、
  裁定パッケージで新 pin 承認手順込みでユーザーへ返す。

## 3. 不変条件

- **規律 1**: 本 wave は C++ を 1 byte も変えない。gitlink・承認定数・凍結 bytes を動かさない。
  よって TRACE=0 翻訳単位も perf 較正も不変。
- **規律 2**: v1 の受理集合を**緩めない**。増えるのは拒否側だけ。witness を optional にした結果
  production が witness なしで通れるなら、それは fail-open であり不可。
- **規律 3**: 不一致は「期待 / 実測 / 差」を構造化して integrity へ載せ、次手が読める形にする。

## 4. 親の provisional 裁定 (攻撃対象)

- **(P1)** FN-1 は「独立 witness」で閉じる。裁定 Q1 は *wave 分割* の裁定であって機構の裁定ではなく、
  「C 行件数 + 終端マーカー」は 2026-07-02 台帳のコメント由来である。witness は T marker より強い
  (欠落位置に依らず、thread file 丸ごと欠落も検出する)。
- **(P2)** witness は pipeline 境界で**必須**にする。`_run_trace` が既に C 行数を数えている
  (`campaign/pipeline.py:277`–`285`) ので、同関数で stdout 側 witness も返し、欠落は既存
  `trace-no-abort-counts` と同型の fail-closed abort にする。
- **(P3)** S-3 は実装しない (権限外)。親が不採用にはせず裁定パッケージで返す。

## 5. DW-G05 成果物影響

S-1 を入れない場合: 部分 trace (末尾切り・thread file 欠落・ofstream silent drop) が
certified serializable のまま `pipeline.evaluate` の COMMIT と fitness を得る。結果として
certified 選択・材料レポート・受理集合が「serializability を実際には確立していない winner」を
名指しできる。S-3 を入れない場合: trx 内の R/W 行だけが落ちる形の部分 trace は依然 certified になる
(残債として台帳に残す)。

## 6. 事前確認済み条件

- **DW-O08**: `git submodule update --init` 実行済み (fresh clone、d706650 で clean)。
- **DW-O09 (2026-08-11 07:40 自己訂正。当初の「0 件」は誤り、F30 型の見落し)**: path 検索
  (`grep` で `orchestrator/verifier/*` / `campaign/pipeline.py`) では freeze 4 件
  (`known_axes_freeze` / `measurement_freeze` / `holdout_freeze` / `floor_protocol`) に
  `verifier` の出現 0 で、`known_axes_freeze` の generator sha pin は `s1_known_axes_freeze.py`
  のみ。gitlink を動かさないので `ccbench_pin` も不変。**しかし path を key にしない pin が 1 件
  実在する** — `result_to_dict(verify_trace_dir(...))` の**出力形状**が凍結証拠へ pin されている。
  - `output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/verifier.json`
    が `integrity` の**固定 key 集合**込みで記録されており、
    `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1060`–`1062` が
    `assert recomputed == recorded_result` で**完全一致**を要求する。
    `campaign/silo_ladder_rung1.py:2842`–`2857` も同じ照合を `DriverError` で行う。
  - **したがって不変条件が 1 本増える: witness を渡さない `verify_trace_dir` 呼び出しの
    `result_to_dict` 出力は byte 単位で現行と同一でなければならない。** 新 key を無条件に
    足す設計は不可 (再凍結には計算ノードでの ladder probe 再走が必要で、本 wave の射程外)。
  - 帰結として **(P2) は「witness は API では optional、pipeline 境界で必須」へ確定**する。
    optional 側が fail-open にならない保証は、pipeline 側の必須化 + 変異で示す。
- **DW-O10**: 出力 bytes が変わる producer = WAL の verify payload (将来 run のみ、凍結成果物なし)。
- **DW-O13**: witness 入力の実在 = `external/ccbench/common/result.cc:48`。既存 consumer が
  2 箇所ある (`orchestrator/calibrator/benchparse.py:59`、`campaign/s2_verify_calibration.py:88`)
  ので、新しい 4 本目の regex を足さず既存経路を再利用するのが既定。
- **invariant の静的裏取り**: `include/ycsb.hh:165`–`167` が `tx.commit()` 成功後に
  `local_commit_counts_` を 1 回だけ増やし、`cc/silo/transaction.cc:693`–`699` の `commit()` は
  `validationPhase()` 成功時に必ず `writePhase()` を呼び、その冒頭 (`:584`–`:596`) で
  `emit_commit` を 1 回だけ出す。早期 return は無い → **C 行数 ≡ `commit_counts_`** は
  silo/YCSB で構造的に厳密。

## 7. 成果物と分割

成果物 = verifier + pipeline の差分 / 反転済みテスト + 対の control / 変異 matrix /
S-3 の裁定パッケージ / spool fragment。
段 3 は 2 レンズ (sol=規律 2 の fail-open 面、luna=invariant の反例と workload 依存)。
段 5 は 1 lane (verifier core・pipeline 結線・tests は相互依存が強く分割の利が無い)。
