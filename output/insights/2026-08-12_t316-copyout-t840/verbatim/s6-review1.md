静的レビューの結論は **NO-GO** です。blocker はありませんが、copy-out の fd 束縛、AST 閉包、変異の単一理由性に must-fix が残っています。pytest・build は実行していません。

### 1. staging root が held fd に束縛されていない

- 重大度: must-fix
- 主張: staging は held parent fd から作成される一方、copy 時に pathname から再 open されます。中間 component が差し替わると、build が生成した staging とは別の regular binary を clean candidate へコピーできます。
- 根拠: staging fd は作成直後に閉じられています。[buildcache.py:1293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1293)、[buildcache.py:1498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1498)。その後 `_secure_copy_binary()` は path を渡され、[buildcache.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:392) の `os.open(path, O_NOFOLLOW)` で再 open します。[buildcache.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:192) の `O_NOFOLLOW` は final component にしか効きません。
- 成果物影響: source evidence と trace-diff が対象にした build tree とは異なる binary bytes が cache に publish され、認証済み選択の実行対象・digest・性能値を変え得ます。
- 提案: `_mkdir_open_at()` が返した staging fd を build 後まで保持し、parent fd/name の identity を再照合してから、その fd を `_secure_copy_binary()` に直接渡してください。

### 2. AST 閉包は単純な alias と動的 import を見失う

- 重大度: must-fix
- 主張: low-level helper を変数へ代入して呼ぶだけで call inventory から消えます。また、静的 binding のない `importlib.import_module()` と動的に組み立てた `getattr` の組合せも検出されません。
- 根拠: call 解決は直接の dotted name/leaf だけです。[test_p3_build_authority_cli.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:211)。dynamic import は `authority_sensitive` が真の場合だけ拒否され、`getattr` は既知 target または定数 attribute に限られます。[test_p3_build_authority_cli.py:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:285)。この audit helper に alias/dynamic の synthetic source を与えた静的 control は、双方とも `calls=[] / dynamic=[]` を返しました。
- 成果物影響: 未登録 issuer が coder authority を発行でき、その receipt を含む campaign も現行 consumer では `admission_status="admitted"` になり得るため、認証済み受理集合が広がります。[artifact_admission.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/artifact_admission.py:772)
- 提案: assignment alias を追跡するか、より小さく low-level helper identifier の import・alias・call を token/AST で全列挙してください。`importlib.import_module("...build_admission")` は静的 binding の有無にかかわらず拒否対象にします。

### 3. 除外は path-exact だが file 内では無制限

- 重大度: must-fix
- 主張: prefix/suffix/nested への拡張はありませんが、除外 file は parse 前に丸ごと skip されます。特に runnable な smoke driver に issuer を追加しても閉包検査は見ません。
- 根拠: exact membership 自体は正しいです。[test_p3_build_authority_cli.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:171)、[test_p3_build_authority_cli.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:376)。しかし除外判定後は source を読まず `continue` します。[test_p3_build_authority_cli.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:337)
- 成果物影響: excluded smoke driver 内の追加 issuer は検出されず、その driver が生成する WAL/campaign を現行 artifact admission が受理し得ます。
- 提案: file 除外ではなく、`(path, enclosing function, helper, call count)` の exact allowlist にしてください。smoke driver は `main` 内の既存 1 call だけを許可します。

除外 10 件は、現行 file-level scannerの下ではすべて実在 call があるため「必要」です。

| 除外 | 判定・実コード |
|---|---|
| `test_artifact_admission.py` | 必要 — [line 316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_artifact_admission.py:316) |
| `test_build_admission.py` | 必要 — [line 97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_build_admission.py:97) |
| `test_buildcache_v2.py` | 必要 — [line 121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:121) |
| `test_campaign.py` | 必要 — [line 84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_campaign.py:84) |
| `test_p3_autonomous_workload_trial.py` | 必要 — [line 77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_autonomous_workload_trial.py:77) |
| `test_p3_build_authority_cli.py` | 必要 — [line 590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_build_authority_cli.py:590) |
| `test_p3_exploration_namespace.py` | 必要 — [line 48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_exploration_namespace.py:48) |
| `test_p3_s4_loop_trigger_gating.py` | 必要 — [line 65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:65) |
| `test_s1_direct_comparison.py` | 必要 — [line 1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_s1_direct_comparison.py:1253) |
| `smoke_driver.py` | 裁定上必要だが file-wide 除外は不十分 — [line 69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:69) |

9 test path は production path を prefix で隠しません。問題は同一 file 内の追加 call と、非 test で runnable な smoke driver です。

### 4. capability 判定が monkeypatch 後の callable identity を見ている

- 重大度: must-fix
- 主張: `os.supports_dir_fd` は interpreter の original builtin を列挙するため、意味を保つ wrapper でも現在の identity 検査は拒否します。親実測の 3 赤と一致します。
- 根拠: 現在の callable を直接 membership 判定しています。[buildcache.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:98)。gate-order test は `os.fsync` と `os.rename` を delegate wrapper に置換します。[test_buildcache_v2.py:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1178)
- 成果物影響: production の認証済み受理集合は変わりませんが、wave の受入結果が 3 赤のままで変更を認証系列へ取り込めません。
- 提案: import 時の original `os.open/stat/mkdir/rename/unlink/rmdir` を capability membership の照合対象として snapshot してください。

この fix は、snapshot を「platform capability の照合」にだけ用いる限り、規律 2 の緩和ではありません。現行判定が wrapper identity と platform capability を混同しています。in-process の関数差替え耐性まで守りたい場合は、security operation を original callable に固定し、test は内部 wrapper seam を patch する方が強いです。

### 5. M5 と M7 は単一理由性が成立しない

- 重大度: must-fix
- 主張: M5 は pathname 再 open へ戻しても後段の destination-entry identity gate に先取りされます。M7 は preflight を外しても欠落 constant の直接参照が例外になるため、「無防備に通る」変異ではありません。
- 根拠: destination entry は hash/fsync 後にも二度検査されます。[buildcache.py:1339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1339)、[buildcache.py:1355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1355)。M5 test 自身も最終的に `"destination entry"` の例外を期待します。[test_buildcache_v2.py:1056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/tests/test_buildcache_v2.py:1056)。M7 の constant は gate 後にも直接参照されます。[buildcache.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:113)、[buildcache.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:403)
- 成果物影響: mutation matrix/受入台帳が M5・M7 を実効 gate の `KILLED` と誤記し、実際には変わっていない fail-closed 受理集合を変化したものとして記録します。
- 提案: M5 は entry identity gate との両層変異を事前登録するか、identity recheck 自体へ再照準します。M7 は public build API が無防備な open まで進む変異にするか、early-diagnostic pin へ降格してください。

### 6. site binding は保存されるだけで消費されない

- 重大度: nit
- 主張: `_coder_entrypoint_site` は authority/context に保存されますが、admission 導出時には読まれません。「site-bound」はデータ保持としては真ですが、拒否 gate としては恒真ラベルです。
- 根拠: context への保存は [build_admission.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:165)。coder admission は authority nonce だけを読みます。[build_admission.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:538)
- 成果物影響: 現行 receipt/WAL/cache/選択値には影響せず、別 registered site への token 持込みも受理集合から除外しません。
- 提案: consumer が expected site と比較するまで「保存済み・未消費」と書くか、`build_run_context` に expected exact site を渡して照合してください。

### 7. directory 作成途中の失敗は cleanup matrix から漏れる

- 重大度: nit
- 主張: `_mkdir_open_at()` は mkdir 後の stat/open/fchmod で失敗し得ますが、caller の `*_created` flag は return 後にしか立たないため、その directory が残ります。
- 根拠: mkdir と後続操作は [buildcache.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1030)。flag 設定は [buildcache.py:1293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1293)、[buildcache.py:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1321) の return 後です。
- 成果物影響: nonce 付き staging/clean 残骸は完成名として受理されないため、認証済み選択・レポート・台帳値は変わりません。
- 提案: `_mkdir_open_at()` 内で作成済み entry を失敗時に削除するか、作成状態を例外にも伴わせて caller cleanup に渡してください。

## 総括

- blocker なし。
- 判定: **NO-GO**。staging fd 束縛、AST alias/dynamic 閉包、smoke 除外の call-site exact 化、既知 3 赤、M5/M7 の変異再照準が必要です。
- 規律 2: 新しい warning 化・例外握り潰し・production fail-open は見つかりませんでした。正常 binary の `0o700`/`nlink=1` hit は現在も通り、fresh は `0o500` になります。既知の過剰拒否は callable identity による親実測 3 赤です。
- 規律 1: named gate の順序は v2/legacy・fresh/hit とも `_recheck_source_evidence → _assert_trace_diff → _assert_no_trace_symbols` のままです。[buildcache.py:1327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1327)、[buildcache.py:1527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:1527)。fresh の発火点は copy 後へ移動しましたが publish 前で、失敗時は clean も破棄されます。trace/perf は引き続き compile-time `CCBENCH_TRACE` で分離されています。[buildcache.py:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:993)
- 主張: `host-security boundary`、`certified safety`、完全な成果物隔離、実行時 binary identity の主張はありません。buildcache/coder gate の限定は概ね正確です。ただし `build_admission` 冒頭の「production issuer inventory を close」は所見 2 が直るまで過大です。[build_admission.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:4)
- T-841: blocker なし。`ADMISSION_SCHEMA` と receipt key/body は不変です。[build_admission.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:31)、[build_admission.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:421)、[build_admission.py:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/build_admission.py:546)。cache preimage も不変です。[buildcache.py:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/buildcache.py:666)。WAL/COMMIT/freeze producer の変更はなく、sort source pin は固定 commit blob を読むため working-tree bytes を repinしません。[t080_freeze_migration.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-copyout-t840/orchestrator/campaign/t080_freeze_migration.py:857)

変異の単一理由性:

| 変異 | 判定 |
|---|---|
| M1 | 成立 |
| M2 | 成立。ただし FIFO anchor のみ。directory は `read(EISDIR)` に先取りされる |
| M3 | 成立 |
| M4 | 成立 |
| M5 | 先取りされる — destination-entry identity 再照合 |
| M6 | 成立 |
| M7 | 先取りされる — 欠落 constant の直接参照による fail-closed |
| M8 | 成立。ただし binary-intermediate のみ。metadata leaf は旧 `islink` 相当にも先取りされる |
| M9 | 成立。ただし registered-helper 経路だけで、所見 2 の alias 経路は閉じない |
| M10 | 成立 |
| M11 | 成立。ただし path exact のみで file 内 call は無制限 |
| M12 | 成立 |
| M13 | 成立 |

親の fix 方針への判定: **採用可。規律 2 の緩和ではありません。** import 時 original os 関数を capability membership の照合対象に限定して snapshot するのが最小修正です。pytest/build は本レビューでは実行していません。