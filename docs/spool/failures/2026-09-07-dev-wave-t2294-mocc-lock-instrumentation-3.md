---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2294-mocc-lock-instrumentation
seq: 3
---

## 新規

### {{F:duplicate-directive-passes-set-dedup-test}}. 負例 patch の裸 directive が 2 site に重複し、実 patch 束縛 test が set() で重複を許していた [恒真ゲート] [テスト代表性]

- 事象: `broken-mocc-early-unlock.patch` が同じ `#if IZANAGI_BREAK_MOCC_EARLY_UNLOCK` を unlock site と relock site の 2 箇所に置いた。
  production の condition gate (`_instrument_declared_owner_source`) は owner file 内で directive がちょうど 1 回であることを要求し、
  driver は early 変異の build 前にそこで停止する。段 5 の test `_patch_added_branch_declaration` は `len(set(matches)) == 1` で
  重複を畳んでいたため緑のまま、その後は directive 1 個の合成 source を検査していた。段 6 敵対レビュー B が静的に発見。
- 根本原因: test が「実 patch の directive 集合」と「production gate が要求する一意性」を別々に見て、実 patch を production の
  関数へ通していなかった。
- 恒久対応: `len(matches) == 1` へ戻し、実 patch を materialize して production の uniqueness 関数へ通す node
  `test_broken_mocc_patches_have_unique_production_condition_witnesses` を追加 (合成重複 source で `compile-time-branch-start-not-unique`
  になる負例と対)。early-unlock は file scope の constexpr 1 箇所 + `if constexpr` 2 site へ書き換え ({{D:mocc-lock-coverage-instrumentation}})。
- 再発検知: 同 node と変異 M15 (directive 重複) の KILLED。

### {{F:condition-gate-red-on-unused-cmake-variable-warning}}. condition gate は configure 成功でも stderr 非空を red にし、driver が渡した未使用 CMake 変数の警告で compute 走が停止した [手順漏れ]

- 事象: compute 1 回目 (job 979769) が `condition gate rejected IZANAGI_BREAK_MOCC_LOCK_COVERAGE: red/red` で 52 秒後に停止。
  login で同じ引数で gate を呼ぶと supply / meaning とも `configure-failed`、detail は CMake の「Manually-specified variables were
  not used by the project: RULE_LAUNCH_COMPILE」警告。driver の `_common_configure_args` が silo driver に無い `-DRULE_LAUNCH_COMPILE=`
  を渡していた (gflags / glog の install build から流用)。
- 根本原因: gate は fail-closed で正しい。driver 側が「CCBench の project が使う変数だけを渡す」という gate の暗黙契約を知らず、
  driver は gate の status しか出力しないため理由が見えなかった。login の生死確認は CMake の警告を無視して build を通していた。
- 恒久対応: driver から未使用変数を除去 (fix-2)。`patches/README.md` の driver 節に「CCBench が使わない CMake 変数を configure に渡さない、
  gate は configure の stderr 警告を fail-closed で red にする」と明記。gate の red は driver で再現せず、
  `_require_condition_gate` と同じ関数列を login で呼んで supply / meaning の全記録を出す probe (job dir の `gate-probe.py`) で読む。
- 再発検知: compute JSON の `condition_gates` に 3 macro の green record が残ること (consumer test は all_pass を要求)。
