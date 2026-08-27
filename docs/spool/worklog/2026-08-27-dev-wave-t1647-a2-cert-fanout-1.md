---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1647-a2-cert-fanout
seq: 1
title: [T-1647] A-2 certification の投入を workload 単位の独立 job へ分割した。作業中に D1139 が批准機構ごと撤去して実走の壁は消え、実機投入は D646 により次 wave となる (コード + docs、branch worktree-dev-wave-t1647-a2-cert-fanout、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「A-2 の 4-cell certification を実走して回収する」+ ユーザー補足
  「時間がかかりすぎ。可能な限り計算ジョブとして分割してどかっと計算ノードに投げるべき」。
  **実走はしていない。** 着手前の実測で依頼の前提が 2 つ覆り、本 wave の終端は
  「投入を分割して land するところまで」になった。詳細は
  `output/insights/2026-08-27_t1647-a2-cert-fanout/README.md`。

- **覆った前提 1: 塞いでいるのは D1028 ではない。** 台帳が「終端は
  enforcement-source-closure-unratified という正直な理由」と記録していた点は今も真だが、
  その解除に D1028/D1038 の非認証成果物型は使えない。D1070 が「非認証成果物型は批准 gate の
  定義域に含めない」と明記しており、非認証経路で回しても certified を名乗れない (絶対規律 2)。
  要るのは D905 の執行主体の着地である。実装は branch
  `worktree-dev-wave-t1629-ratification-broker` に存在し main 未着地。

- **覆った前提 2: 本 wave では実機投入できない。** D646 が「新設 Pegasus login-side 実行体を
  registry へ登録する wave は、同じ wave 内でそれを実機から起動できない」と定めている。
  段 1 brief が置いた「分割した投入を実機へ 1 回投げて配線を実測する」は撤回した。
  同じ終端を D1070 (未批准 closure で scheduler request を作らない) も指す。
  実際に `bash tools/pegasus/submit_paper_story_a2_certification.sh` を叩くと
  guard_bash が `未登録 Pegasus 実行体` で拒否することを実測した。迂回はしていない。

- **数値の読み方を 1 点訂正した。** 起票以来引き継がれていた「1 反復 695.95 秒」は
  **1 cell あたりではなく 4 cell 合計の 1 反復あたり**である。5 反復で 58 分、ビルドと性能測定を
  足しても 4 cell 全体で約 1 時間。そこへ 6 時間の枠を取っていた。したがって
  「時間がかかりすぎ」の実体は直列実行ではなく、**枠が実コストの 5〜6 倍であること**と
  **gate が閉じていて 1 秒も測れないこと**だった。**枠の右寸法化は本 wave では見送った** —
  正式な全工程の所要を一度も測っておらず、縮めると timeout の受理集合を未測定のまま狭める。

- **分割は既定の規範だった。** `docs/pegasus-runbook.md` の 2026-08-11 ユーザー裁定
  「独立なら既定で並行投入する。同じ protocol を別 workload で回すのは fan-out してよい典型」に
  照らすと、A-2 の 1 本直列のほうが逸脱である。同節の独立 3 条件のうち条件 1 (共有して奪い合う
  ものが無い) だけが不成立で、`jobs/<workload>/` を job 所有 subtree にし finalizer の親走査を
  やめることで成立させた。**並列度の上限は 2 である** — cell 単位に割ると stock/adopted の
  対照条件が壊れる。設計判断は {{D:a2-outer-certification-is-a-conjunction}} と
  {{D:job-local-closure-is-not-a-shared-parent-scan}}。

- **段 6 のレビューが「緑なのに実機で必ず死ぬ」実装を摘出した。** 焦点走 936 passed で緑だったが、
  campaign の出力 root が二重化しており実 producer は raw cell を 1 件も作れなかった。
  テストが実 producer を通さず期待側の layout を手で組み立てていたためである
  ({{F:focus-run-green-because-tests-bypassed-the-real-producer}})。
  レビューは他に、批准とは別の 2 つ目の障壁として **completion / acquisition の正規 producer が
  repo に存在しない**ことも摘出した ({{F:a2-completion-receipt-had-no-producer}})。
  real 6 件 + 親が裁定へ返さず格上げした 1 件の計 7 件を fix した。refuted は複数あり、
  逐語は insight の `verbatim/` に置いた。

- **変異は 8/8 KILLED、SURVIVED 0・MISMATCH 0。** 特に M1 (policy の論理積規則を
  `_protocol_preimage` の対象から外す) が KILLED であることは、**policy に書いた規則が
  「書いただけで発火しない飾り」ではない**ことの機械的証明である。M4 (raw の原子的 create-only を
  `exist_ok=True` へ退化) は、段 6 レビューが帰属不成立を指摘して負例を作り直した後に成立した。
  走行中の中断 3 件はいずれも親の手順不備 (runner argv の `-rf` 欠落、scratch の `rm -rf` 後に
  `git worktree prune` を怠った、計算ノード投入が受領証を出さず fail-closed 停止) で、
  erratum として insight に残した。

- **段 8 の後、作業中に前提が覆った。** main が 93 commit 進み、**D1139 (ユーザー裁定) で
  批准機構そのものが撤去されていた**。`enforcement_source_ratification.py` は削除され、
  `verify_ratified_contract_loader_binding` も無い。D1139 は D905 / D1039 / D1070 / D1071 を
  明示的に上書きし、D905 が命じた執行主体は「今後も作らない」と定めている。
  **したがって着手時に実測した終端はもう発火せず、「A-2 は D905 の着地待ち」という
  本 wave の当初の結論は無効である。** 段 4 で採用した login 側の批准 precheck は呼び先を失い、
  追随して撤去した。撤去したのは批准集合との照合だけで、D1139 が残すと定めた 3 検査には
  触れていない (保護対象 5 file と `hooks/` の差分ゼロを親が実測)。
  `ratified_qsub` は `exact_qsub` へ改名し、qsub argv の exact 検査は残した。
  **分割そのものは D1139 の影響を受けない。**
  変異は M7 (批准 precheck を外す) を撤回して 7 変異で回し直し、
  **baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0** を得た。
  撤回理由は「殺せなかったから」ではなく、変異させる行が廃止で消えたためである。

- **ユーザーへ返す裁定候補が 1 件ある。** 新設 login-side 実行体の admission 分類について、
  runbook は「grandfather は当該 4 本限りで、他 entry を `local-ok` にするには実測が要る」と
  書くが、B-10 の 2 本は実測なしに `local-ok` + `static login-side submitter classification` で
  登録されている。本 wave は B-10 と同形で登録した。**規則と先例のどちらが正か**を返す。
  どちらに倒れても本 wave の land は成立する (実機投入は D646 により次 wave のため)。

## 次の一手差分

### 更新

- [T-1647] **P1・実走可能。次 wave で実機投入する**: A-2 の 4-cell certification 実走。
  **投入側の分割は本 wave で着地した** — workload ごとの独立 job、job 所有 subtree、
  exact 2-job group receipt、`finish-group` producer。
  **批准の壁は D1139 で撤廃されたので、残る制約は D646 だけである** —
  新設 login-side 実行体は registry の追加が main へ land するまで起動できない。
  本 wave が land すれば次 wave で実機投入でき、そこで初めて 4 cell の実測が取れる。
  枠は 06:00:00 のまま据え置いた (全工程の所要が未実測のため)。
  base: 14f1c974b9bec8161352f247afacd51d9944cdb2336c98bc54444430b49bb49c

### 新規

- {{T:a2-fanout-first-live-verification}} **P1・新規**: A-2 fan-out submitter の実機初回検証と
  4-cell certification の実走。D646 に従い、registry の追加が main へ land した後に別 wave で行う。
  **D1139 で批准の壁が消えたため、配線確認だけでなく実測そのものへ進める。**
  rr5 / rr50 を 2 job へ fan-out し、両 job の終端後に login 側から `finish-group` を 1 回走らせる。
- {{T:login-side-admission-rule-vs-precedent}} **P2・ユーザー裁定待ち**: 新設 login-side 実行体の
  admission 分類について、runbook の「grandfather は 4 本限り、他は実測が要る」という規則と、
  B-10 の 2 本が実測なしに `local-ok` で登録されている先例が食い違う。どちらが正かを裁定する。
- {{T:a2-walltime-right-sizing-after-first-full-chain}} **P3・新規**: A-2 の枠 (elapstim 06:00:00) の
  右寸法化。正式な全工程 (ビルド + 小構成 correctness 4 回 + 5 反復 + 性能 20 回 + cooldown) を
  1 度実測してから決める。現在の根拠は 4 cell 各 1 反復の verifier 時間だけで、5 反復 58 分は
  線形換算である。律速は walltime ではなく RSS (rr50-stock で 20.29 GB / 閾値 32 GB)。
- {{T:attempt-level-measurement-selection}} **P2・新規**: attempt 単位の測定値選別の余地を塞ぐ。
  `automatic_retry: false` は記録されるだけで consumer が無く、attempt を何個でも preregister して
  良い attempt だけ materialize できる。fan-out の交差束縛は workload を跨ぐ混成は防ぐが、
  attempt 全体の選別は防がない。
