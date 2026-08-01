# 段 6 敵対レビュー — レンズ B

判定は **NO-GO**。BLOCKER 4 件、MAJOR 5 件、MINOR 2 件。

## 所見

### B1. D116 はすでに衝突している

**重大度: BLOCKER**

**根拠:** 本 branch は [decisions.md:5475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5475) で `[T-244]` を D116 とした。一方、現在の main は [decisions.md:5462](/home/SFC/tanab/github/izanagi/docs/decisions.md:5462) で `[T-295]` を D116、同 `:5499` で D117 まで使用済みである。さらに並行 `[T-288]` branch も [decisions.md:5462](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t288-recipient-matrix/docs/decisions.md:5462) で別内容を D116 としている。現 checkout 内だけを見る `check_docs.py` はこの branch 間衝突を検出しなかった。

**放置影響:** phase/runbook/材料レポートが参照する `D116` が還流設計・事前登録・recipient matrix の三義になり、certified 選択の根拠と proof-chain の設計参照が別決定へ解決される。

---

### B2. D114 が禁じた「cross-generation 全体を機械拒否」の過大主張を D116 が再導入した

**重大度: BLOCKER**

**根拠:** D114 は [decisions.md:5374](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5374) で「`cross-generation 還流を機械的に禁止した`とは名乗らない」と明記し、`drive/providers/preview` 注入と `drive_iteration()` 直接反復を保証外としている。同じ正本の D116 は [decisions.md:5525](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5525) で「cross-generation 還流は 3 入口で機械拒否」と逆の主張をした。さらに現行 formal consumer は [layer3_report.py:346](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/layer3_report.py:346) で lock・WAL・whiteboard を読むだけで origin proof を要求せず、draft 自身も [README.md:343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:343) で P7 未実装と認めている。

**放置影響:** 注入 callable／driver 直接反復で作った originless 多世代 artifact が層 3 材料レポートへ入り、承認済み上限 1 の外で生成された variant が正式候補集合に混入する。

---

### B3. `critic=report-only` と既存 reflux on/off は同時に成立せず、ablation arm が偽になる

**重大度: BLOCKER**

**根拠:** D39 決定 4 の唯一のスイッチは [decisions.md:1110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:1110) および [p3_s4_loop.py:236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop.py:236) のとおり、赤 digest を **critic に見せるか**だけである。D116 draft は [README.md:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:181) で critic を report-only とし、出力を次世代制御へ戻さない。一方、現実装は [p3_autonomous_workload_trial.py:983](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:983) で critic の bool を次世代 `prior_reverse` にし、停止判定へ使う。8c は同 `:430` で `reflux=True` 固定で、off arm 自体を持たない。それでも P8 は [README.md:344](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:344) で reflux on/off の不破壊を要求する。

**放置影響:** bool を残せば on/off で停止理由・attempt 数・候補集合が変わり critic は report-only でなくなる。bool を外せば両 arm の生成・採否は同一となり、材料レポートの `reflux=on/off` treatment label が偽になる。

---

### B4. 「failed-singleton no-good cut」は一候補の赤から半空間を削る過剰一般化である

**重大度: BLOCKER**

**根拠:** draft は [README.md:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:99) で観測できたのは certified frontier から一 atom だけ変えた**その候補**の赤であり、相互作用・因果単調性は未証明と認める。しかし同 `:118` と `:130` では atom `r` を `C` に追加し、以後すべての `r=false` mask を `E=P∨C` で排除する。これは exact assignment 1 個を除外する no-good cut ではなく、座標全体を固定する cut である。D116 は [decisions.md:5500](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5500) でこの名乗りを決定化している。

**放置影響:** 初回 cut だけで最大 16/32 mask が verifier 前に消え、別 atom との相互作用で certified になり得た mask を探索不能にして、certified 選択値・性能値・全 attempt 台帳を系統的に変える。

---

### B5. D51 の逐次 provenance 出力が hidden constraint の公開面として取り残されている

**重大度: MAJOR**

**根拠:** D51 は [decisions.md:1919](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:1919) で campaign の `reports/` に iteration ごとの `proposal_path/auditor_diff_digest/variant/outcome` を逐次書くことを必須化した。実装も [p3_s4_loop_trigger_gating.py:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:503) で毎 iteration 書く。D116 は公開 API/report を active window 中は二値にするとする一方、P2 の検査は [README.md:338](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:338) の「untrusted role payload 比較」だけで、D51 report、driver 戻り値、artifact path を閉じない。32 状態しかないため effective variant/digest は総当たり可能であることも同 draft `:183` が認めている。

**放置影響:** P2 が合格しても caller が逐次 provenance から `C/E` を復元して次 query を適応選択でき、台帳上の 1-bit/query 上限と候補 batch の非適応性が偽になる。

---

### B6. 裁定済みなのに「裁定まで」と主張する living consumer と実行時文字列が残った

**重大度: MAJOR**

**根拠:** D116 は [decisions.md:5477](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5477) で設計軸の裁定済み状態を記録した。しかし現行 phase doc は [phase3.md:463](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3.md:463) で「設計択一として未解決」「D106 残余 1 の裁定まで」と主張し、その直後 `:471` では D116 で確定したと書く。実コードにも [p3_autonomous_workload_trial.py:191](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:191) と同 `:205` に同じ古い理由が残る。freshness 例外は同 `:696` から report/journal の `error.message` / `fatal_error.message` に入る。

**放置影響:** stale campaign の材料 `report.json` と `attempts.jsonl` が「未裁定」を停止理由として保存し、実際の blocker である P1〜P10 未充足との参照対応が壊れる。

---

### B7. 「機械検査可能な前提条件 10 件」は機械 predicate になっていない

**重大度: MAJOR**

**根拠:** D116 見出しと [decisions.md:5517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5517) は 10 件を機械検査可能とするが、draft の P3 は [README.md:339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:339) で deletion/rollback を必ず赤にする一方、同 `:243` では外部 anchor と authority を未解決としている。推奨する repo 内 registry だけでは repo/ledger 全体の rollback を自己検出できない。P6 は「名乗りを超えるなら」という条件文で、現状は名乗っていないため既に vacuous true となり「満足ゼロ」と矛盾する。P10 は人間裁定そのもので機械検査ではない。また `V7` は [mutation-ledger.json:207](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-generation-gate/mutation-ledger.json:207) の **mutation ID**であり、P1〜P10 の充足を測る「計測 ID」ではない。

**放置影響:** cap-lift guard の真偽を決定できず、fail-open なら generations 2〜10 が未充足のまま受理され、fail-closed なら受理集合が永久に `{1}` のままになる。

---

### B8. runbook の 3.3 は現在選択された Pegasus 運用では実行不能

**重大度: MAJOR**

**根拠:** runbook は [phase3-s8c-autonomous-trial-runbook.md:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:87) で build/verify/bench を含むコマンドを直接提示する。Pegasus 正本は [pegasus-runbook.md:254](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/pegasus-runbook.md:254) で login node の build/bench を禁止し、同 `:428` で「campaign dispatch task は未実装、sanctioned 経路なし」と明記する。最新 worklog も [worklog.md:1448](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/worklog.md:1448) で同じ不可能性を実測済みである。P8 はそれでも「runbook 3 手順の全経路」を要求する。

**放置影響:** 3.3 は campaign WAL・certified result を生成できず、login node で強行すれば環境契約外の測定値が材料レポートと certified 選択へ混入する。

---

### B9. 中央 draft が insights の authority marker 契約を満たさない

**重大度: MAJOR**

**根拠:** [output/README.md:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/README.md:72) は、プロセス監査・裁定 snapshot を insights に置く場合、冒頭に `authority: none` / `default_effect: no-state-change` を明示するよう要求する。新規 [draft README:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-reflux-design/README.md:1) には両 marker がなく、未裁定値と「現在ゼロ」を持つ。D116 は [decisions.md:5512](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5512) でこの directory を「本文と逐語の正本」として参照する。

**放置影響:** D116・将来の材料レポートが、非権威の凍結証拠か更新される設計状態か判別できない同一 path を参照し、`I/Q/K`・origin authority・P1〜P10 の意味が commit 未指定のまま漂流する。

---

### B10. 主実験文書の実体 path が存在しない

**重大度: MINOR**

**根拠:** [phase3-main-experiment.md:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-main-experiment.md:45) は `campaign/p3_s4_loop.py` を参照するが、repo-root 相対では存在せず、実体は [orchestrator/campaign/p3_s4_loop.py:236](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop.py:236) である。draft 内の basename-only file:line はすべて一意に実体へ解決できたが、同様に repo-relative path ではない。

**放置影響:** 主実験の ablation 合流点参照が機械的に辿れず、材料レポートの treatment provenance が壊れた path を保持する。

---

### B11. X1〜X7・I2/I3 の carry/close 対応が成果物にない

**重大度: MINOR**

**根拠:** 前 package は [generation-gate README:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-generation-gate/README.md:67) に X1〜X7、同 `:92` に I2/I3 を列挙する。新 draft は P3/P5/P9 へ内容を吸収したが ID 対応表を持たず、worklog 差分もまだない。現 worklog では [worklog.md:1486](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/worklog.md:1486) が T-244 を「設計 wave 待ち」のまま、X6 は T-288、I2/I3 は T-291 として別途保持している。

**放置影響:** T-244 を一括完了にすると、X6 の 100 倍単位ずれが未解消のまま proposal／採用 variant を変え、I2/I3 の残留変異・pin 取りこぼしが mutation 台帳や証拠参照から脱落しうる。

## 静的確認で反証できなかった点

- 現 checkout の差分は docs 4 ファイルと新規 insights のみで、production の受理集合は現時点では変わっていない。したがって本 wave 自体についての D96 違反は確認しなかった。
- D39/D45/D51/D96/D106/D114/D116、参照された insight directory、file:line の行範囲は実在した。例外は B10 の repo-relative path と、B7 の `V7` の種別誤認である。
- `python3 tools/check_docs.py` は rc=0、`git diff --check` も rc=0。変更対象に適用される byte・最長行予算違反は検出されなかった。`docs/README.md` の地図は `phase3-s*.md` と insights の総称導線を持つため、新規個別列挙は不要である。
- runbook 3.1/3.2 の 1 generation コマンド形は維持されている。破綻しているのは現在の Pegasus 運用に対する 3.3 と、それを P8 の「全経路」と数える点である。
- pytest、build、計測は実行していない。

## 総括

**(a) 判定: NO-GO**

**(b) BLOCKER: 4 件。** D116 採番衝突、D114 保証限界の反転、report-only と reflux ablation の両立不能、単一 red から半空間を削る偽 no-good cut。

**(c) 最小の修正:**

1. local main を取り込み、land 直前の最大番号から再採番して全 `D116` 参照を更新する。
2. D116 の「cross-generation を3入口で拒否」を D114 と同じ限定表現へ直し、phase とコード中の「裁定まで」を「D116 前提未充足」へ更新する。
3. no-good cut を exact mask 1 個の除外へ縮めるか、座標 cut に必要な correctness 単調性を独立実証する。
4. 8c の treatment、合流点、critic 出力、停止判定を一つの契約として定義し、report-only と on/off のどちらを残すか決める。
5. D51 provenance／driver 戻り値を含む全公開面を P2 に入れ、P1〜P10 を具体的な schema・node ID・receipt・外部 anchor に落とす。
6. runbook 3.3 を T-276/T-277 完了まで明示 blocked とし、insights marker と X1〜X7・I2/I3 の worklog 対応表を追加する。