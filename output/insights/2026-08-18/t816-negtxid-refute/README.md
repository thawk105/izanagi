# 負txid false-green (ruling-inbox 2026-08-12 finding#1) の反証調査

## 依頼

`orchestrator/verifier/parse.py:213` の負txidパース欠陥を修正する依頼。根拠は
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-blockers-summary.md`
の「段3が挙げた、裁定後に実装へ回すreal所見」1件目:

> 負の txid で false-green certified になる (既存の穴)。`C -1 0 2 1 0 0` / `E -1` は
> `expected = max(txid)+1` の式で `missing = -1` となり違反が立たない
> (`orchestrator/verifier/parse.py:213`)。これは v2 化とは独立に、現行 v1 parser でも
> 成立する。`txid >= 0` の構文検査と負例が要る。

台帳にT番号が無く、[T-816] の大きい裁定待ちに巻き込まれて未起票のまま埋もれていたという
認識のもとでの依頼だった。

## 親の直接実測 (2026-08-18, main HEAD `a31832d9a021a907907266647ea49b9b7f0b5de5`)

1. `orchestrator/verifier/parse.py` の C タグ処理に `if txid_i < 0: raise ParseError(...)`
   が既に存在する (現行行番号で概ね178-181行)。
2. `C -1 0 2 1 0 0\nE -1\n` を含む trace を作り、現行 `parse_trace_dir()`
   (`orchestrator.verifier.parse`) に直接通したところ、
   `ParseError: ...txid must be a non-negative integer: -1` が即座に raise された。
   false-green は再現しない。
3. `git log -S"txid_i < 0"` により、このチェックは commit `fb5e74a1`
   (2026-08-12, "feat(verifier,pin): trace を v2 専用にし ccbench pin を 511c953 へ
   前進 ([T-816] 手順 4)") で追加されたと判明。後続の是正commit `a80daf83`
   ("fix(verifier,pin): 敵対レビュー所見7件を閉じ、校正artifactの再pinを撤回する
   ([T-816])", 同日) はこのチェックを retract していない (このチェックを含まない diff)。
   ruling-inbox の該当ファイルは 2026-08-12 時点のスナップショット
   (「実装差分: ゼロ」と明記) であり、**同日中の後続実装で副作用的にこの穴が
   塞がれたと見られる**。
4. `orchestrator/tests/test_verifier.py:269-282`
   `test_negative_txid_is_rejected_before_gap_math_can_cancel_it` が既に同じ入力
   パターンを `verify_trace_dir()` 経由で pin している。docstring:
   「{-1, 1} は旧 max(txid)+1-len(txns) だと欠番を相殺できた。構文で拒否する。」
   — ruling文と同じ機序を過去形で明記した回帰テストが既にある。
5. 密連番 gap-check ロジック自体 (`expected = max(txns.keys())+1; missing = expected
   - len(txns)`) は commit `36a11936` (2026-07-02, "verifier: 部分trace/整合破れの
   偽陰性をintegrityで塞ぐ") から存在する。つまり 2026-07-02〜2026-08-12 の約6週間、
   構文レベルでは負txidによるこの穴が main に実在した。
6. ただし実 CCBench trace-hook は txid を「commit直前のfetch_add (0始まり)」でのみ
   採番する (`patches/README.md:385`「txid = グローバル単調id (TRACEビルド限定の
   atomic)」、および parse.py 自身のインラインコメント)。実 trace が負txidを含むことは
   構造的にありえない。**過去のreal mutation/evaluation走行がこの穴を通過した実例は
   ない** — 穴は「手で細工した/破損したtraceに対する構文防御の欠落」であり、
   実CCBench出力に対するfunctionalなfalse-greenではなかった。

## 稼働中waveとのfile衝突確認

`git -C .claude/worktrees/<wave> diff --stat main...` を4 worktree
(s8c-c12-c04-c11 / t1352-c07-result-judge / t1353-c03-c08 / t688-job-kill-evidence-r2)
+ 2 job-dir worktree (t1348-c09-c10-consumer 相当 / t1363-c06-budget-consumer)
に対して実行。いずれも `orchestrator/verifier/parse.py` /
`orchestrator/tests/test_verifier.py` を編集していない。

## 独立敵対チェック (fresh subagent, general-purpose, model opus)

親の結論を疑わせるため、親の投資済み文脈を継承しないfreshなsubagentへ「反証を試みよ」と
依頼した (agentId a8c3fb7e8674731d2、168997 tokens、tool_uses 54、所要 903635ms)。

**結果:**

1. **負txid系の再現は不可。** 13通りの手動variant (負値の組み合わせ、他フィールドへの
   負値混入、順序入れ替え等) と、追加の全数探索1554通りで追試したが、現行mainで
   false-greenを再現できなかった。親の結論を追認。
2. **副次所見: 別種の既知false-greenパターンを提示。** 「末尾txid丸ごと欠落」
   (trace中の最大txidに対応する trx が丸ごと存在しない) は `missing_txids == 0` /
   `certified == True` のfalse-greenを**現に**作る。ただしこれは負txidとは無関係の
   別ベクトルで、後述のとおり既知・テスト済み・実経路では緩和済み。
3. **軽微な所見: 非有界メモリ。** `parse.py` の `missing_sample = sorted(set(range(
   expected)) - set(txns.keys()))[:5]` (現行348-350行付近) は `expected` が
   巨大 (概ね1.4×10^8以上) だと `set(range(expected))` の構築でメモリを食い、
   ログインノードのプロセスが判定前に落ちうる。txidが1.4億に達するには単一run内で
   1.4億txnをcommitする必要があり、calibratorのレコード数最小化原則
   (絶対規律4) の下では非現実的な規模。対応不要と判断する。

## 親による副次所見の追加検証

副次所見 (末尾txid丸ごと欠落) について、それが「新規の未対応バグ」なのか
「既知の設計上のtrade-off」なのかを独立に確認した。

1. `orchestrator/tests/test_verifier.py:882-940` に「既知偽陰性のcharacterization」と
   題したセクションがあり、以下が既に存在する:
   - `test_characterization_tail_txid_gap_is_false_green` — witnessなしoptional API
     でのfalse-green (`certified=True`) を明示的にassertし、docstringで
     「意図した後方互換」と明記。
   - `test_characterization_tail_txid_gap_is_indeterminate_with_commit_witness` —
     同じtraceに `expected_commits=` (commit witness) を渡すと
     `verdict=="indeterminate"` / `certified=False` になることを確認。
   - `test_characterization_txn_tail_loss_is_indeterminate` /
     `test_commit_count_witness_detects_removed_trace_file` — 近縁の欠落パターン
     (FN-2、trace file丸ごと削除) は別の機構 (v2 framing、commit-count witness) で
     既に捕捉されることを確認。
   すなわちsubagentが「発見」した挙動は、repoの設計者が既に認識・特性化・テストで
   固定化した**意図的な** library-API限定の挙動であり、未発見のバグではない。
2. `verify_trace_dir()` の実呼び出し元を `grep -rn "verify_trace_dir("
   orchestrator/` で全数確認した (テスト・verifier本体を除く):
   - `orchestrator/campaign/pipeline.py:1118` — 変異評価の本番pipeline
     (Phase 3の実 correctness 判定経路)。`expected_commits=
     trace_result.commit_count_witness` を渡している。witnessが欠落・不正な場合は
     `pipeline.py:1032-1112` の複数分岐で `"trace-no-commit-witness"` 等の理由で
     fail-closed rejectする (黙って通さない)。
   - `orchestrator/campaign/silo_ladder_rung1.py:2867` — raw trace再計算による
     再現性監査。ここでの `verify_trace_dir()` 呼び出し自体は `expected_commits`
     を渡していないが、同じ関数内の2855行目で別途
     `_validate_correctness_commit_witness()` (定義: 828-839行目) を呼んでおり、
     これはCCBenchのraw stdoutから独立に読んだ commit count witness と、記録済み
     verifier.jsonのtxn数を直接比較し、不一致ならDriverErrorを送出する。つまり
     `verify_trace_dir()`自身のmissing_txids判定がblindでも、周辺コードが同値の
     witness照合を独立実装して穴を塞いでいる。
   **結論:** 実在する2つの本番呼び出し経路は、いずれも (経路もwitnessの配線方法も
   異なるが) 独立にwitness照合を課しており、末尾txid欠落によるfalse-greenは
   実運用上到達しない。

## 結論

- 依頼された負txid false-greenの穴は**既に修正済み・既に回帰テスト済み**。
  追加の実装・テストは不要 (既存テストと重複するだけで純増検出力がゼロになる)。
- 過去の実mutation/evaluation走行がこの穴を通過した実例はない
  (実trace-hookが負txidを構造的に出力しえないため)。
- 敵対チェックが提示した副次所見 (末尾txid欠落) は、既に characterization test で
  文書化・pinされた意図的挙動であり、実本番経路2つで独立に緩和済み。新規対応は不要。
- 受入全走: green (verdict=child-green, red_nodeids=[], flake_nodeids=[],
  tested_main=tested_tip=`a31832d9a021a907907266647ea49b9b7f0b5de5`)。

工数: 親の直接実測 (git log / grep / python3直接実行、複数回)、subagent 1本
(general-purpose, opus, 168997 tokens, tool_uses 54, 903635ms)、受入全走1回
(green, queue待ち込み)。
