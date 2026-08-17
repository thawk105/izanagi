## 総括

静的敵対レビューでは、production helper 自体に明白な誤りは見つからなかった。  
ただし親 brief の「探索 campaign は必ず repo 外」は反証された。既定経路は repo 内 `output/` を返す。  
M-2 と M-4 の期待失敗 node は完全集合でなく、このままでは変異 matrix が成立しない。  
repo 外テストは Git 非所属を明示せず、lock pin も source HEAD と同値なので、誤った source-repo fallback が生存する。  
8c E2E は新 fallback を通る形だが、v2 lock は production でなく test helper が直接生成している。  
除去した monkeypatch が担っていた Git-success の full-chain 被覆は残っていない。  
pytest は実走していない。以下は差分、全 callsite、tracked lock 32 件の全件静的検査による。

## must-fix

[重大] orchestrator/campaign/layout.py:293 — 「探索 campaign は必ず repo 外」は偽。明示 `output_root` は無検査で返り、環境変数未設定時も 306 行で `repo_output_root()`、すなわち repo 内 `output/` を返す。repo 外強制は環境変数経路の 329 行だけである — 成果物影響: 8c が常に 0 試行で倒れるという brief の影響記述が過大で、実際の既定 8c は Git HEAD 経路を使う。

[重大] orchestrator/tests/test_layer3_report.py:1666 — repo 外 v2 test は campaign に Git ancestor がないことを assert していない。さらに期待 pin は 56〜66 行で source HEAD から作られるため、fallback を `return _git_head(_DEFAULT_OUTPUT_ROOT.parent)` に壊しても全 assertion が通る — 成果物影響: lock が束縛した版ではなく生成時 source HEAD を材料レポートへ記録する退行が検出されない。

[重大] orchestrator/tests/test_layer3_report.py:1720 — M-2 の期待 node が不足している。lock-first 変異は `test_git_backed_campaign_head_precedes_v2_lock_authority` だけでなく、repo 内でも Git を呼ばず pin を返すため `test_source_repo_internal_git_failure_does_not_use_lock_authority` も落とす — 成果物影響: 期待 node 完全集合との不一致で mutation harness が正しい KILLED 判定を確定できない。

[重大] orchestrator/tests/test_p3_autonomous_workload_trial.py:2464 — M-4 は focused test に加え、この E2E の pin 完全一致 assertion も落とす。hex64 は completeness を通るが、2473 行の hex40 pin 比較で落ちる — 成果物影響: 失敗 node の取りこぼしにより変異証拠が不正確になり、段 6 を閉じられない。

[高] orchestrator/tests/test_p3_autonomous_workload_trial.py:157 — 8c E2E の custom drive は標準 `trigger.drive_iteration` を通らず、209〜211 行で test helper の `build_v2_lock` を直接書く — 成果物影響: 標準 8c producer が v1 lock を作る退行はこの E2E 単独では検出されず、実 trial は layer3/completeness で停止してレポートを生成できない。

[高] orchestrator/tests/test_layer3_report.py:1744 — v1 負例も `tmp_path` が source repo 外であることを assert していない。repo 内 temp base では 184 行の内側判定だけで再送出され、M-5 が実行されず緑になりうる — 成果物影響: repo 外 v1 を placeholder で誤受理する退行が環境依存で生存する。

## nit

[中] orchestrator/tests/test_p3_autonomous_workload_trial.py:2362 — `_git_head` monkeypatch 除去により、Git 由来 hex40 を 8c の render から completeness まで通す統合被覆が消えた。focused test は `build_report` までである — 成果物影響: 実際に到達可能な repo 内既定 8c の full-chain 退行が関連テスト全走まで局所化されない。

[低] orchestrator/tests/test_layer3_report.py:1676 — 同一 node 内で先に `build_report`、後に `render` を呼ぶため、M-1/M-4 では前者の失敗で後者へ到達しない — 成果物影響: render 入口の fallback 証拠が独立せず、失敗時にどちらの入口が壊れたか判別できない。

## 変異登録への修正提案

[重大] orchestrator/tests/test_layer3_report.py:1666 — 修正後の M-1 期待完全集合は `test_external_v2_campaign_uses_lock_authority_for_build_and_render` と `test_three_workload_build_positive_admission_passes_real_layer3_chain` — 成果物影響: wave 前の直呼びへ戻す退行が focused と 8c の両成果物入口で検出される。

[重大] orchestrator/tests/test_layer3_report.py:1684 — M-2 期待完全集合を `test_git_backed_campaign_head_precedes_v2_lock_authority` と `test_source_repo_internal_git_failure_does_not_use_lock_authority` に修正する — 成果物影響: official 値変更と official fail-open の両方を mutation 証拠へ残せる。

[高] orchestrator/tests/test_layer3_report.py:1720 — M-3 期待完全集合は `test_source_repo_internal_git_failure_does_not_use_lock_authority` のみ — 成果物影響: repo 内 Git 障害時の受理集合拡大を単一理由で検出できる。

[重大] orchestrator/tests/test_layer3_report.py:1680 — M-4 期待完全集合を focused repo 外 v2 node と 8c E2E node の 2 件へ修正する — 成果物影響: hex64 の誤 provenance が材料レポートへ残る退行を全入口で記録できる。

[高] orchestrator/tests/test_layer3_report.py:1744 — M-5 は外側 branch の明示 assertionを追加後、`test_source_repo_external_v1_without_authority_stays_fail_closed` のみを期待する — 成果物影響: pin 不在の v1 campaign が偽の hex40 で受理されることを確実に防ぐ。

[高] orchestrator/tests/test_layer3_report.py:1766 — M-6 期待完全集合は `test_explicit_generated_from_head_still_wins` のみ。既存 `"fixed"` 呼出し群は値を検査しておらず追加 node にはならない — 成果物影響: caller 指定 provenance を無視する退行を正確に検出する。

[重大] orchestrator/campaign/layer3_report.py:187 — M-7 として lock pin の代わりに source repo HEAD を返す変異を追加する。現 fixture では source HEAD と pin が同じため生存するので、両者を意図的に異ならせた helper-level test が必要 — 成果物影響: report が lock 束縛版でなく現在版を記録して再現参照を変える退行を捕捉できる。

[中] orchestrator/campaign/layer3_report.py:183 — M-8 として `except Layer3ReportError` を `except Exception` に広げる変異を追加し、外部 v2 でも予期しない例外が authority で隠されないことを検査する — 成果物影響: 実装障害を成功レポートとして隠し、不完全な層 3 成果物を発行する fail-open を防ぐ。

## 調べたが問題なし

[問題なし] orchestrator/campaign/layer3_report.py:179 — 明示値、campaign Git HEAD、repo 外 v2 pin、再送出の実装順は段 4 裁定どおりで、呼出し前に campaign path は 436 行で resolve 済み — 成果物影響: production の意図した受理集合変更は repo 外 v2 のみに限定される。

[問題なし] orchestrator/tests/test_layer3_report.py:1729 — authority は正例で非 None、v1 負例では 1754 行で None を明示確認し、例外負例は 1741、1763 行で同一例外 object まで検査する。広すぎる例外捕捉はない — 成果物影響: fixture の型違いや別原因の失敗を契約成功として数えない。

[問題なし] orchestrator/tests/test_layer3_report.py:1771 — 明示値優先 test は `_git_head` を呼んだ瞬間に `AssertionError` を出し、最終値も `"fixed"` と照合するため恒真ではない — 成果物影響: caller 指定 provenance の保存契約を直接守る。

[問題なし] orchestrator/campaign/p3_autonomous_workload_trial.py:1754 — 8c finalizer は absolute campaign path を使い、1762〜1766 行で明示 `generated_from_head` を渡さない。親 process の cwd や明示値による迂回はない — 成果物影響: Git 非所属なら実際に新 fallback へ到達する。

[問題なし] orchestrator/campaign/autonomous_trial_completeness.py:344 — 成功する campaign-chain は 361〜365 行で v2 authority を必須にする。標準 drive も `p3_s4_loop_trigger_gating.py:818` から既定 `require_environment_contract=True` を通る — 成果物影響: 成功済み 8c 成果物へ v1 lock が混入することはない。

[問題なし] orchestrator/campaign/campaign_lock.py:211 — `git ls-files` で tracked `campaign.lock` を全 32 件列挙し、`campaign-lock/v2` と `authority` を全件検索した結果はいずれも 0 件だった。検索結果は途中で切っていない — 成果物影響: 現存 tracked official artifact について v2 lock による値差はない。