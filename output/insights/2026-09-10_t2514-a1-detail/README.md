# T-2514 — A-1 条件関門の失敗 detail 保存

- `authority: none` / `default_effect: no-state-change`。
- 正本: D1936項4、D1912、
  `output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md` §6/9。
- 対象は既存関門が生成したarm recordとadmissionの拒否時保存だけ。
  依存供給・source配線の根治、attempt-0004、過去attemptの変更は行わない。

## 範囲と所有

起動時のworktree一覧、repo handoff、外部handoff、稼働processに同名T-2514または後続A-1の
編集所有は観測されなかった。稼働T-2581の所有は`p3_s4_loop.py`とpin依存testであり、参照に限定した。
実装所有は`paper_story_a1_paired.py`と既存`test_paper_story_a1_paired.py`の2ファイル。
D95の別Codex author worktreeを使い、親は裁定・docs・統合・検査を担う。

## 段2・3・4

逐語は`plan.md`、`consult-a.md`、`consult-b.md`。3本ともsubprocess done=0、出力checker rc=0。
相談はread-onlyで静的検査のみ。blocking所見は無かった。

- 採用: 受領証から検証済みの`attempt/jobs/<workload>/raw`を明示引数で関門へ渡す。
- 採用: admissionが拒否したときだけ、greenを含む全supply/meaning recordとadmissionを保存する。
- 採用: 元の拒否本文を先に確定し、各recordのdigest取得・canonical化・path構築・保存を
  `Exception`境界へ置く。失敗は固定labelと例外型の追記に留め、後続recordの保存を続ける。
- 採用: D1912のfile単位の一時file・file fsync・replace・directory fsync。
  directory fsync失敗時には完全な最終fileが既に存在し得る。
- 不採用: 依存供給/source根治や新gateを本件の前提にすること。失敗証拠保存は独立して成立する。
- 親briefの存在しない関数名`_v3_workload_paths`を、正しい`_v3_job_roots`へ訂正した。

受理集合、reason codeの順序・重複、既存のcould-not-run拒否、成功経路は維持する。
保存の`BaseException`伝播はD1912の契約どおりで、拒否保持の破れには数えない。

## 変異事前登録

実装前に以下を外部handoffへ固定した。実装後に一意アンカーと期待失敗node集合を確定する。

| ID | 操作 | 判定対象 |
|---|---|---|
| M1 | 拒否分岐の保存呼び出しを除去 | 保存欠落のdiagnostic sensitivity pin。受理集合killには数えない |
| M2 | 保存Exception捕捉を狭める | 元PaperStoryError保持の破れ |
| M3 | admitted経路を誤拒否 | 従来の受理正例の破れ |

変更前のA-1単独走は182 passed、24.62s、bounded scope観測ピーク2218790912 bytes。
計測値ではなくテストrunnerの結果である。

## 実測の範囲

このwaveは性能測定を行わない。Lustre上の耐久性を過去のos.link probeから一般化せず、
今回のテスト環境で実際に検査した保存挙動だけを報告する。

## 実装・独立レビュー

Codex authorの逐語は`author.md`。所有2ファイルのみの変更を親がpatchで統合した。
productionは60行追加・1行削除、testは既存bytesを保った末尾298行追加。
author環境でのテストはqstat preflight失敗のrunner rc16、child_started=falseであり、実走結果ではない。
親環境のA-1単独走は196 passed / 32.31s、bounded scope観測ピーク2155323392 bytes。

独立レビュー逐語は`review-a.md`と`review-b.md`。双方done=0、出力checker rc=0、must-fix所見なし。
実ファイルのcanonical bytes照合がdetail保存を検査することと、未注入操作もException境界内であることを
静的に確認した。レビューが全故障点の実走証明になるとは扱わない。

## consumer検査と参照追従

最初のconsumer走は2 failed / 1202 passed / 4 skipped (計算ノード990058、58.65s)。
一件はA-1 no-touch manifestが未コミットの所有差分を検出したもの。期待値を変えずcommit後に再走する。
他方は同じrun_measurement/run_campaign呼出しが59行移ったため、build sink表の座標7209が古くなったもの。
別Codex fixがtest_ccbench_spawn_sites.pyの当該座標2か所だけを7268へ追従した。逐語は`fix.md`。
集合要素・scope/kind/owner・被覆の意味・受理拒否の判定内容は変更していない。
同fileでT-2417が所有する別probeの座標と説明は触っていない。

fix後の単独走の最初の試行はbounded localのMemoryMaxへ到達し、同時進行のread-only reviewの
生artifact増加により状態比較が変化したため自動fallbackが拒否された(rc16)。本体・test・submoduleを
照合して同じ検査をforce-dispatchへ再投入した。未完走をテスト成功・実装回帰のいずれにも数えない。

## 修正後の実測

- build sink単独: 44 passed / 34.84s (990073)。焦点レビューは`focus.md`、done0/出力checker0。
- commit後consumer再走: 1204 passed / 4 skipped / 60.49s (990080、child rc0)。前の2赤は解消。
- 実装anchor `4dc41b4c7952ee6a5e5c370939b16e7c03e767ce`の全史provenance: 9436件、新規違反なし、既知56件。
- 変異基準走: 3 passed。3変異とも期待node完全集合と一致、復元・wrapper終端rc0。
  rawは`mutation-result.json`、登録は`mutation-spec.json`、復元はwrapper receipt。
- M1はharness上KILLEDだが、本記録では保存欠落のdiagnostic sensitivity pin 1件として扱う。
  受理/拒否挙動のkillはM2/M3の2件であり、診断だけの変化をそこへ算入しない。
- check_codex_agents/check_docs/diff-checkは実装時点で通過。性能測定・attempt投入は行っていない。

## dev-wave 改善候補

終端で`docs/skill-self-improvement.md`を再読しhandoffへ候補1件を記録した。
read-only workerのrepo内artifact増加とbounded localテストを並走すると、MemoryMax後の状態比較が
変わり自動fallbackを阻む。今回の実測に基づき、該当並走ではforce-dispatchかworker完了後へ寄せる
DW-O18/O26の手順明確化候補とする。候補記録のみで、改善実装や次wave起動は追加しない。
