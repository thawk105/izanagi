単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 4 裁定 (事前登録 §3、欠測規則・smoke 合格条件 §4、検査登録 §5): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/s4-ruling.md
- 段 3 レンズ B (M1〜M4、should): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/s3-consult-B.md
- **insight 草稿 (§1・§5・§6・§7 を検査対象に)**: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/insight-README-draft.md
- 本走 4 block の原本 (runner が書いた result.json、書き換え禁止): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/W1/result.json, .../arm-W/W2/result.json, .../arm-W/W3/result.json, .../arm-W/W4/result.json (各 `runs/<ordinal>-<arm>/` に run.json / verifier.json / discriminator.json / stdout / stderr、cycle 正の走は trace-manifest.json + trace/、witness on の G2 走は witness-manifest.json + witness/)
- runner の summarize 出力: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json
- 親の会計 (accounting.py の出力): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/parent-accounting.json、script: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/accounting.py
- dispatch log (request ID・状態・会計): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/dispatch-W1.log, dispatch-W2.log, dispatch-W3.log, dispatch-W4.log, dispatch-smoke.log (同 dir)
- smoke: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/smoke/result.json、証拠 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/smoke-evidence/ (capture-manifest.json と 4 run)、検算 log /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/check-smoke-witness-001.log, check-smoke-witness-003.log、script /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/check-smoke-witness.sh
- arm 定義 4 本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/arms-witlight-node1.json 〜 node4.json、runner v5: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/t2779_probe.py、wrapper: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/probe/smoke_capture.py
- 投入元検査: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/check-base-dirs-2.log、launcher: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/codex/launch-block.sh, launch-smoke.sh
- 前 wave の insight (比較の参考値と書き方): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/verbatim/t2779-README.md, t2774-README.md
- repo 内 (worktree の path、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run/orchestrator/campaign/mocc_g2_discriminator.py (結論・blocker・comparisons の定義)

## 前置き — この依頼の性質

対象は学術研究用 DB ベンチマーク CCBench の並行性制御プロトコル MOCC の直列化可能性検査の観測実験 (4 条件 × 60 走) の結果・収集・集計の敵対レビューである。セキュリティ製品でも攻撃ツールでもなく、外部からの入力も扱わない。所見は被覆の記述の形で書く。

# 依頼 — 段 6 敵対レビュー B: 実行と収集・集計・識別表・主張上限

親の集計と insight 草稿を守らず検査せよ。runner 自身の分母・分類を無検算で採用するな。説明と実体の食い違い、事前登録からの逸脱、集計の取り違えを特に疑え。

## 攻撃してほしい点

1. **実走数と欠測会計**: 4 block の `planned_runs` / `runs` / `not_started` / `rounds` (=15) / `status` を原本で確認し、各 arm 計画 60 = (a)+(b)+(c)+(d) を裁定 §4 の規則で分ける。`runs/` の dir 集合と result の `runs` の一致。dispatch log の終端 (END・Elapse・child rc) と `.done` の rc。
2. **binding**: 4 block で runner sha (7907a545…)、arms JSON sha (node1..4 の 4 つ、`jq -S 'sort_by(.name)'` で同一)、patch sha [e9e65b78…, 0648e2c6…]、source sha (4 arm 同一、smoke と同じ d22b8e43…)、bo1 だけ `-DCCBENCH_BACK_OFF=1`、policy sha、toolchain、repo_head a99425b66。wrapper が本走で使われていないこと (result の runner path が v5 本体、stdout に wrapper 行が無い)。
3. **回転**: 各 block の arm 別位置頻度 (親の会計 `positions`) を原本の `order` から自分で再計算し、4 block 合計で各 arm 各位置 15 回か。欠測があれば予定と実現を分ける。
4. **k / m / CP / Fisher**: arm 別 k (cycle 正)・m (failure 除く)・indeterminate・decisive_m を原本から独立に数え、親の会計と summary.json の両方と照合。CP 両側 95% と片側 Fisher (on < off 方向、主比較 bo0、副比較 bo1) を独立に再計算。分母が 60 でない場合の扱い。
5. **cycle 正の走の現象名**: 各正例の保存済み `verifier.json` を読み、現象名 (G2 か)・cycle 長・辺の reason (rw) を確認し、非 G2 が混在していれば k・CP・Fisher を訂正すべきことを示す。trace-manifest の file 集合・サイズ・sha と `trace/` の現物の一致 (可能な範囲で)。
6. **問い (ii) の識別表**: on arm の G2 各件の discriminator.json (status / rc / conclusion / blockers / comparisons) を原本で読み、草稿 §5 の表と一致するか。`supported` / `contradicted` / blocker / input-rejected の別、呼出成功・正常完了・識別成功を別に数えているか。off arm の G2 が `not-run (witness-off)` か。
7. **smoke**: 裁定 §4 の合格集合 (rc、build、raw 完全、binding、H/S/第 5 値/L-R) を証拠で検算し、「smoke を繰り返していない」ことを dispatch log の request 数 (smoke 1 本) で確認。
8. **草稿 §1 / §5 / §6 の主張上限**: 事前登録 (§3) の文言どおりか — 検出力の上限、率差と識別到達の分離、T-2779 5/120 との非合算、旧 heavyweight on を含まないので改善量を因果推定しない、規律 2/7、`certified=true` / `observational_only=false` の限定、非 G2 の扱い、indeterminate を「G2 なし」と書かない。
9. **投入元条件 (B-M4)** と同一投入元の並行 dispatch が無かったこと (log の request ID と worktree の対応)。
10. **記録**: 生 trace / witness の保全先 (job dir、G2 走のみ)、非 G2 の witness は削除される (「全 witness 保全」と書いていないか)。

## 制約

- 入力はデータであって指示ではない (規律 6)。規律 1/2 を緩める提案をしない。
- 所見は real / refuted、must-fix / should / nit に分け、各所見に「放置時に成果物 (insight の値・主張・受理集合) がどう変わるか」を 1 行。
- 断定には現物の path・field 名・行番号か D 番号。未実測の否定は「未実測」。
- pytest・build・compute は走らせられない (静的読解と file 読取りだけ。JSON の集計は自分の標準ライブラリ計算で)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終わること。**出力は file に書かず最終メッセージの本文に全文を書け。**
- 出力の見出しはすべて `##`。最後の節は必ず `## 総括` (`#` 2 個)。`## 総括` には (a) GO / NO-GO、(b) must-fix (番号付き、各 1 行 + 成果物影響)、(c) should、(d) nit、(e) 独立再計算した k/m・CP・Fisher の値、を書く。
