---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t810-harness
seq: 1
title: T-810 の測定装置を作り始めた — 実測は §9 の 2 段承認で塞がれており実装が 0 byte だった、敵対 5 本が blocker 14 を摘出 (コード + docs、変異 13/16 一致、branch worktree-dev-wave-t810-harness)
---

## 本文

- **依頼はユーザーの直接指示**: 「[T-810] の実測を実施してください。設計の事前固定どおり、
  同一 binary・同一 workload を N ノードへ同時投入して分散を取得してください。目的・N・割付け・
  推定量は設計から変更せず、結果は成果物へ流入させない台帳へ記録してください。単独性確認を適用し、
  T-139 の pilot / 本走 job と 8b の計測が流れている間はキュー投入を控えてください。」

- **依頼の前提が成立していなかった。**protocol §9 は投入を **2 段の承認関門**で塞いでおり、
  第 1 段 (builder + 生死確認) の前提だけで実装 7 部品・凍結 artifact・受入・予算 receipt・
  並走ガード・**人間の承認 ID** が要る。worklog (442) の land は「docs のみ・実装差分ゼロ」で、
  `tools/` にも `orchestrator/` にも T-810 の実装は 1 byte も無かった (grep 0 件)。
  **したがって実測は投入できない。**親は scope を「測定装置の構築」へ切り替え、
  **キューへ T-810 の測定を 1 件も投入していない**。
  ユーザー確認を要する scope 変更であり、land 報告で明示して確認を仰ぐ。

- **事前登録値の食い違いを 1 件解消した。**worklog (451) の次の一手は `N12・R12` と書くが、
  同じ行が正本と名指す protocol 本文は **N=13・R=10** である。裁定パッケージ s4 §5 Q3 (a) の
  数字が、段 6 焦点レビューによる assurance 計算式の訂正より前の stale 値だったことが原因。
  **正本の本文どおり N=13・R=10 で凍結した。**

- **敵対検証は 5 本 (段 3 で 2、段 6 で 2、焦点 1)、すべて NO-GO から入り全部 NO-GO を返した。**
  blocker 14 + must-fix 11。**摘出された穴はほぼ全部が「測ったあとに結果を選び直せる」方向**で、
  protocol §5.4 と §6 が名指しで禁じている失敗そのものだった。主なもの:
  (i) 分類 receipt が attempt の実ファイルへ束縛されず、非完走 slot に実行記録を残したまま
  **偽の `terminal_reduced` を作れた** = 13 ノードから都合のよい 12 を事後選択できた。
  (ii) F 分位が SciPy の有無で切り替わり、等号境界の golden が 1 ULP 下だったため
  **環境差だけで `refuted` と `underdetermined` が反転**しえた。
  (iii) golden が runtime を拘束せず (loader は list 長しか見ていなかった)、
  **同じ digest のまま別実装**を使えた。
  (iv) `estimate.json` の値を再計算しておらず **でたらめな τ が通った**。
  (v) 承認 receipt が caller の自己発行で、外部権威になっていない。

- **親自身の誤りが 4 件。**すべて子または焦点レビューが正した。
  (i) 段 1 の provisional 裁定「走査面から `.claude/` を除く」は**実在 path で反証された** —
  `.claude/worktrees/<別 wave>/` の下に freeze・WAL・activation が実在する。さらに親の
  「158,011 file / 185 秒」は **main checkout の topology の値**で、入れ子 worktree を持たない
  standalone checkout には一般化できなかった。除外ではなく
  **「入れ子 worktree を含まない静穏な専用 checkout への束縛」**へ置換した。
  (ii) `pre_release_invalid` の node receipt を「全 13 slot」と読んだが、protocol §6.2 は
  **「到達したノードの分だけ必須」**である。artifact と protocol を正として訂正した。
  (iii) 終端状態の分類器を validator と参照 estimator の**二か所に置き順序が逆**になった。
  estimator 側を削除して 1 実装へ集約した。
  (iv) fix 統合 commit `1892d8b1` の題名「blocker 9 件と must-fix 7 件を閉じる」は**過大**だった。
  焦点レビューの実判定は **closed 8 / partial 7 / regressed 1**。fix 子は一貫して `partial` と
  申告していたのに親が断定へ変えた。commit `772fb0d4` の本文で訂正済み。

- **回帰を 1 件出して閉じた。**fix 1 巡目が `terminal_reduced` で**脱落 slot の実在記録を拒否**
  するようになっていた。protocol §5.4「完了 12 + 脱落 1 の記録」と §6.2「失敗時も実在する
  receipt を削除しない」に反し、**証拠の削除を強いる**向きだった。3 巡目で閉じた。

- **正例が過剰拒否を捕まえた。**fix 1 巡目の実走は 14 failed / 62 passed で、**うち 8 件が正例**
  だった。原因の 12 件は単一で、**validator 自身の `git status` が一時 `index.lock` を作成・削除し、
  validator が封印する `.git` root metadata を変えていた** (観測が観測対象を汚す)。
  `GIT_OPTIONAL_LOCKS=0` で観測を非変異化し、検査は緩めていない。

- **親が閉じないと裁定したもの (ユーザー裁定へ返す)。**
  (a) 承認 receipt の外部 trust root — 署名方式は設計択一。**偽の trust root を作って
  「外部権威がある」と装う方が危険**なので作らず、`/limitations/approval_receipt_trust_root_absent`
  で機械可読に宣言した。(b) 測定窓の静穏要件 — 完全な非流入検出は coordinator が到達できる
  全 checkout の静穏を要する。(c) protocol §9.1 item 2 の凍結列挙が §3.2 と §7 を落としている件
  (本 wave は上位集合を凍結した)。(d) 未記録 exec の不存在は (b) の単一 mediation 点まで閉じない。

- **後続 wave へ送ったもの。**(a) N-job barrier / 共有 release / 取り消し marker / 開始ばらつき /
  完了 verifier、(b) T-810 専用 PBS wrapper、(c) runner policy module (単独 mediation が無い限り
  receipt-only なので (b) と同じ wave へ)、(d2) 測定ノード上の repo 不在、(f) 並走ガード機械化、
  (g) 予算 admission、least-authority な root 粒度、最終走査後の TOCTOU、
  未凍結手続き (build/qsub argv・raw→log・§5.1 副次量・§7 下流 consumer)。

- **変異 matrix は 16 件中 13 件が期待どおり。**3 件 (M3・M4・M6) は **MISMATCH だが超過検出**で、
  いずれも変異は KILLED、**期待 node は実測 node の部分集合**だった。原因は本 wave が新設した
  「loader 完了時に golden conformance を実行する」結合で、凍結物と推定の破壊が後段へ波及する
  (M3 = 48 node、M6 = 41 node、M4 = 3 node)。
  **期待 node を実測に合わせて書き直しての再走は行わない** — 事前登録を結果に合わせる事後調整に
  なるため。`DW-M03` に従い **M3 と M6 は過剰決定 (冗長 gate) として単独変異の証拠から外し**、
  M4 は予測不足として記録する。M1 (wave 前の実コードに実在する
  `git ls-files --others --exclude-standard` と同型) と M16 (正例) はともに期待どおり。

- **セッション事象。**(i) `tools/run_tests.py` は `--overall-grace` を渡せず既定 300 秒に固定される。
  gen_S 滞留時は焦点走が必ず rc=16 (`queue-wait-timeout`) で落ちる (1 走を空費、
  request `905030.nqsv`)。回避は `tools/pegasus/dispatch_compute.py` の直接使用。
  (ii) 段 3 レビュー B の 1 回目は成果物 11,095 bytes・`validator_rc=0` ながら
  `evidence_status=invalid` で不受理。job-id が prompt 内容から導かれるため prompt を
  別ファイルにして再投入で解決。(iii) codex 実装子は sandbox が socket を塞ぐため計算ノードへ
  dispatch できず、テストのある実装 wave では「実装済み・未実走」が既定の完了形になる。
  prompt に先回りして書くと子が緑を偽装せず素直に申告する (実際に 5 子すべてで機能した)。

- **受入全走を 2 走し、land は main 側の赤で塞がれていることを実測で確定した。**
  1 走目 (request `905180.nqsv`、583 秒) は **6 failed / 9201 passed / 20 skipped**。
  うち 4 件は本 wave の追加が所有外 consumer へ波及したもので、いずれも機械的な同期漏れだった
  (policy registry の literal 期待値、admission registry と runbook §7.0 投影表、
  新規テストの自走 harness、`orchestrator/campaign/` の相対 sibling import 不変条件)。
  **子は 3 回とも「所有外への波及可能性」を報告書に列挙しており、うち registry の literal 固定は
  事前に名指しされていた。**親が焦点走だけで進めず先に全走を回していれば 1 巡減らせた。
  2 走目 (560 秒) は **2 failed / 9205 passed / 20 skipped** で、
  **残る 2 件は `orchestrator/tests/test_t793_report.py` の main 由来の赤だけ**である。
- **main 由来の赤の帰属を実測で確定した。**`docs/decisions.md` に `D305` が入ったのに
  T-793 の公表承認レポートの期待値が `("D292",)` を literal で固定しており、
  supersession scan が `("D292", "D305")` を返して不一致になる。
  両ファイルを変更したのは main の祖先 commit (`427da17c` と `c820722a`) だけで、
  **本 wave の 8 commit はいずれにも触れていない** (`git log <range> -- <path>` で実測)。
  **親はこれを直さなかった** — T-793 が所有する公表層の fail-closed な報告 gate であり、
  正しい直し方が「期待値へ D305 を足す」なのか「scan の範囲を狭める」なのかは
  その wave の文脈なしに判断できないため。{{T:t793-d305-supersession-expectation}} として起票する。

- **ユーザー裁定 (2026-08-12、発話「免除入れて」) により、この 2 件を受入の免除として land した。**
  免除の証拠は次の 3 点で、いずれも実測である (memory の「証拠なしの免除をしない」に従う)。
  (i) **赤の nodeid は 2 件のみ**で、`orchestrator/tests/test_t793_report.py::test_actual_head_d292_reference_is_reported_fail_closed`
  と `::test_deny_only_report_contains_authority_and_both_submission_denials`。
  (ii) **帰属**: `git log 23c8e7c4..HEAD -- docs/decisions.md` が返すのは `427da17c` のみ、
  `-- orchestrator/tests/test_t793_report.py` が返すのは `c820722a` のみで、**どちらも main の祖先**
  (`git merge-base --is-ancestor` で確認)。本 wave の 8 commit はいずれにも触れていない。
  (iii) **単調性**: 本 branch は main へ ff-only で載る差分であり、
  **land しても main の赤は 1 件も増えない** (受入 2 走目 = 2 failed / 9205 passed、
  1 走目 = 6 failed / 9201 passed から本 wave 由来の 4 件が消えた形)。
  すなわちこの免除は失敗を隠しておらず、テストも防壁も弱めていない。
  **恒久化しない** — {{T:t793-d305-supersession-expectation}} が閉じるまでの限定免除である。

## 次の一手差分

### 更新

- [T-810] **P3・測定装置の第 1 slice を実装、実測は未投入**: protocol §9 の 2 段承認関門と
  実装 0 byte により**実測は投入できない**。本 wave は §9.1 item 2 (凍結事前登録 + digest) と
  item 1 の (d1) repo 外 root 方針注入・(e) §6.3 の単一 fail-closed validator を実装した。
  **§9.1 は充足していない。**残りは {{T:t810-coordinator-and-wrapper}} と
  {{T:t810-guard-and-budget}}、および {{T:t810-approval-trust-root}} の裁定。
  正本 = `docs/pegasus-node-variance-protocol.md` + `output/insights/2026-08-12_t810-harness/`
  base: 85992df6dabb02e4b84fe4ec20634724e9bab3206c5ba8d8a8b8d0dd834c95cf

### 新規

- {{T:t810-coordinator-and-wrapper}} **P3・新規 ([T-810] 段 4/6 の scope 外裁定)**:
  §9.1 item 1 の (a) N-job group barrier・共有 release・取り消し marker・coordinator 側の
  開始ばらつき測定・N 件 exact な完了 verifier、(b) T-810 専用 PBS wrapper、
  (c) runner policy module、(d2) 測定ノード上の repo 不在を実装する。
  **(c) は単独 mediation 点が無い限り receipt-only にしかならない**ため (b) と同じ wave に置く。
  素材として `tools/mutation_fanout.py` の group manifest・qstat identity parser・orphan 検出がある。
- {{T:t810-guard-and-budget}} **P3・新規 ([T-810] 段 4 の scope 外裁定)**:
  §9.1 item 1 の (f) 並走ガードの機械化 (割当てジョブ状態の exact parser・未知状態の拒否・
  A 系優先・競合時の取り下げ) と (g) 予算残枠との突合による投入 admission を実装する。
- {{T:t810-approval-trust-root}} **P2・新規・ユーザー裁定待ち ([T-810] 段 6)**:
  承認 receipt に署名と外部 trust root が無く caller が自己発行できる。これが残る限り、
  artifact と receipt を一緒に差し替えるだけで凍結全体が恒真化する。
  署名方式と trust root の置き場所を決める。現状は
  `/limitations/approval_receipt_trust_root_absent` で機械可読に宣言してある。
- {{T:t793-d305-supersession-expectation}} **P1・新規 ([T-810] 受入全走で実測)**:
  `orchestrator/tests/test_t793_report.py` の 2 件が **main 単独で赤**である。
  `docs/decisions.md` に `D305` が入ったのに期待値が `("D292",)` を literal で固定しており、
  supersession scan の `("D292", "D305")` と不一致になる。
  変更したのは main の祖先 commit (`427da17c` / `c820722a`) だけで、[T-810] wave は無関係。
  [T-810] は 2026-08-12 のユーザー裁定「免除入れて」で限定免除して land したが、
  **赤は main に残ったままである。**期待値へ D305 を足すのか、
  scan の範囲を狭めるのかは公表層 (T-793 / D291) の文脈で決める。
  閉じるまで後続 wave も同じ限定免除を要する。
- {{T:run-tests-overall-grace}} **P3・新規 ([T-810] セッション事象)**:
  `tools/run_tests.py` の `_default_dispatch` が `dispatch_compute.dispatch(...)` を
  grace 引数なしで呼ぶため `--overall-grace` を渡せず、既定 300 秒に固定される。
  queue 滞留時に焦点走が必ず rc=16 で落ちる。flag を通す小改修。
