### RB1

- **主張**: profile・module・code identity の検査は連続的な遮断ではなく、disable/swap-and-restore 後に原状復帰すれば outcome producer へ到達できる。
- **根拠**: `p3_b4_wiring_probe.py:420-423` は `sys.setprofile` を遮断対象に含めず、profile は code identity 一致だけで発火する (`:458-468`)。publish 前検査も現在の module/function identity だけを見る (`:471-483`)。負例は swap 中に検査してから復帰しており、swap→call→restore を試していない (`test_p3_b4_wiring_probe.py:445-482`)。
- **到達可否 / 判定**: **到達する** — `sys.setprofile(None)`、または inventoried function の `__code__` を seal 前から存在する非 inventory codeへ差し替え、呼出後に元へ戻せば ledger 0 のまま最終検査を通る。pre-bound original callable は profile が有効な間だけは閉じている。直接の `compile`/`exec`/新規 import は fail-closed。
- **成果物影響** (DW-G05): checkpoint/WAL 等を生成しても `blocked_outcome_attempts=[]` と `result.passed=true` を持つ証拠が公開され、適格 driver 集合を変える。
- **重大度**: must-fix
- **推奨 fix**: `sys.setprofile`/`threading.setprofile` と code/function 生成系 audit event を遮断する。swap-and-restore の間に実 writer を呼び、復帰後の publish が拒否される負例へ置き換える。

### RB2

- **主張**: 静的 resolver は aliased dynamic import・aliased/non-dotted `getattr`・`sys.modules` alias を unresolved と認識せず、証明経路が静かに合格し得る。
- **根拠**: 問題登録は直接構文だけを判定する (`p3_b4_wiring_probe.py:588-609`)。一方、module-level alias は binding として解決されるが、その callee が `importlib.import_module` かを問題化しない (`:497-522,610-615`)。試験は直接の `getattr(L, dynamic_name)` だけ (`test_p3_b4_wiring_probe.py:149-164`)。
- **到達可否 / 判定**: **到達する** — `loader = importlib.import_module; loader(name)` や `mods = sys.modules; mods[name].fn()` を既存 direct edge と同じ `main`/`drive_iteration` に足しても `issues` が空のまま `reachable=true` になり得る。
- **成果物影響** (DW-G05): `ambiguous_bindings=[]` とされた偽の静的 path が driver 選択・証拠参照に残る。
- **重大度**: must-fix
- **推奨 fix**: callee の解決後 canonical name でも dynamic import/getattr/sys.modules を判定し、未解決 local assignment・subscript・globals/vars 経路を証明関数内では一律 `StaticInventoryError` にする。

### RB3

- **主張**: import 副作用と seal 前から存在する thread の outcome 経路は閉じていない。
- **根拠**: 副作用走査対象は6 moduleだけ (`p3_b4_wiring_probe.py:56-65,670-678`) だが、runtime は追加 module とその推移閉包を import する (`:804-835`)。走査は direct top-level callだけで、function/class decorator 内を丸ごと飛ばす (`:647-667`)。thread census は前後集合の一致しか要求せず、既存 thread 数を0にしない (`:805,837-839`)。`threading.setprofile` は seal 後に開始する thread向けである (`:445-447`)。
- **到達可否 / 判定**: **到達する** — main 呼出前から待機する thread は census を通り、profile 無しで seal 後に producer を呼べる。import中に開始・終了する threadや、未走査 dependency の atexit/signal/finalizer も静かに残る。
- **成果物影響** (DW-G05): publish 前後に outcome が生成されても `thread_census.unchanged=true` と違反 ledger 0 の証拠になり得る。
- **重大度**: must-fix
- **推奨 fix**: fresh single-thread process を起動条件として強制し、全 runtime import closure を import 前に静的検査する。import前後の thread開始履歴と handler/finalizer registry を負例で固定する。

### RB4

- **主張**: B3 の ambient root と protected-root I/O 境界は、明示 `output_root` と複数 path を持つ filesystem event を覆っていない。
- **根拠**: protected roots は repo既定値と2環境変数だけ (`p3_b4_wiring_probe.py:233-246`)。production は明示 exploration root を無検証で優先し (`layout.py:370-379`)、official rootも引数から解決する (`layout.py:412-419`)、`run_campaign` は任意の `output_root` を受ける (`loop.py:232-247`)。さらに rename/link/symlink は第一引数だけを検査する (`p3_b4_wiring_probe.py:249-263,406-410`)。
- **到達可否 / 判定**: **到達する** — 環境変数に現れない実 campaign root を `TMPDIR` にすれば workspace がその配下へ作られる。外部 source から protected destination への `os.rename`/`os.link` も destination を検査しない。
- **成果物影響** (DW-G05): 実 campaign tree に fixtureやlinkを追加・削除しつつ、`outside_resolved_campaign_roots=true`・protected counters 0 の証拠を出せる。
- **重大度**: must-fix
- **推奨 fix**: ambient tempを使わず、production root policyが campaign配置を拒否する予約 namespaceを明示する。audit eventごとに全 source/destination と `dir_fd` を解決し、pre-opened fdも拒否する。

### RB5

- **主張**: `admission_reads.sha256` は admission が実際に読んだ bytes ではなく、後から同じ固定 pathを再読した値である。
- **根拠**: admission loader 自身は読んだ raw bytesから SHA を導く (`artifact_admission.py:473-479`)。probe は path集合だけを観測し (`p3_b4_wiring_probe.py:389-392,1489-1493`)、view解放後に固定 pathを再hashする (`:1508,1533-1540`)。overlayへの書込みは禁止されていない。
- **到達可否 / 判定**: **到達する** — admission後・再hash前に overlay bytesが変わると、証拠SHAは承認判定に使用した台帳SHAと異なるが publishできる。
- **成果物影響** (DW-G05): `admission_reads` の path→SHA参照が実際の承認根拠を指さず、証拠の再検証可能性が失われる。
- **重大度**: must-fix
- **推奨 fix**: `CertifiedCampaignView.decision.overlay_ledger_sha256` と、auditで実観測した pathから evidenceを構成し、現在ファイルの再読値とは照合だけ行う。

### RB6

- **主張**: identity evidence は裁定された domain separationを欠き、triggerでは sanctioned pathが使う実site cfgを測っていない。
- **根拠**: preimageを無接頭辞で直接 SHA-256する (`p3_b4_wiring_probe.py:1217-1218,1237-1238`)。production campaign IDも同じ SHA の先頭8桁を使う (`ident.py:180-189`)ため locator断片をそのまま漏らす。trigger projectionは常に `site_policy.OTHER` (`p3_b4_wiring_probe.py:1227-1239`)だが、実driverは `_current_site()` を使う (`p3_s4_loop_trigger_gating.py:793-810`)。
- **到達可否 / 判定**: **到達する** — 現 evidence hashの先頭8桁は実 campaign IDの `cfg_hash8` と同じ。Pegasus compute経路のprojection driftも検査外である。
- **成果物影響** (DW-G05): evidenceから実campaign locatorを再構成でき、かつ記録hashが実sanctioned cfgの参照にならないため identity分離証拠が無効になる。
- **重大度**: must-fix
- **推奨 fix**: versioned domain prefix＋NULを前置してhashする。triggerは実site resolverと同一の cfg構築関数を通し、site・contract・admission binding後の pairを記録する。

### RB7

- **主張**: static pathの最初の `main → drive_iteration` edgeのguardを捨て、machine-readable名は runtime passageと誤読できる。
- **根拠**: pathには caller/callee/path/lineだけを保存し、`conditional_edges` は後段 `drive_iteration → make_critic_digest` のguardだけを記録する (`p3_b4_wiring_probe.py:699-735`)。実3 driverの main→drive 呼出しはいずれも `if a.run_iteration` 配下 (`p3_s4_loop.py:1644-1675`, `p3_s4_loop_sort.py:624-642`, `p3_s4_loop_trigger_gating.py:1164-1182`)。testはsortのconditionalを空と固定する (`test_p3_b4_wiring_probe.py:127-146,595-603`)。
- **到達可否 / 判定**: **到達する** — CLI側edgeがdead/追加guard配下になっても、後段edgeが残れば `reachable=true` と `switchpoint_passage.passed=true` になる。
- **成果物影響** (DW-G05): sanctioned CLI条件を欠いたdriverが合格集合に入り、§5.1(i)のexact command・driver参照が誤る。
- **重大度**: must-fix
- **推奨 fix**: path上の全edgeについて逐語guardを記録する。check名を `static_candidate_plus_direct_switchpoint_call` 等へ狭め、top-levelにも runtime passage非主張を置く。

### RB8

- **主張**: `main(argv)` は返却後も process-wide guardを残すため、同一interpreter内の既存driver受理集合を変更する。
- **根拠**: guardは「one-way」でrestoreしないと明記され (`p3_b4_wiring_probe.py:266-267`)、audit/profileを装着する (`:1444-1457`)一方、最後は通常returnする (`:1605-1607`)。解除処理は存在しない。
- **到達可否 / 判定**: **到達する** — in-process callerがprobe後に既存 `run_one_iteration`/`pipeline.evaluate` を呼ぶと、inventory profileにより新たに拒否される。専用CLI processが直ちに終了する場合だけ影響しない。
- **成果物影響** (DW-G05): 同一processで後続driverを扱うrunnerでは既存runtime受理集合が狭まり、「既存driver不変」という参照条件が崩れる。
- **重大度**: must-fix
- **推奨 fix**: fresh dedicated processでしか実行できない契約を機械強制する。in-process APIを残すなら、publish後境界と後続処理禁止を型・entrypointで閉じる。

### RB9

- **主張**: 実装子の「12 consumer」は不正確で、新testは既存plain-runner gateを確実に赤にする。
- **根拠**: 新testは `test_source_and_test_are_the_only_worktree_changes` で終わり、`__main__` harnessがない (`test_p3_b4_wiring_probe.py:610-628`)。既存gateは全 `test_*.py` を列挙し、self-runnerかREADME allowlistを要求する (`test_plain_runner_coverage.py:44-74`)が、当該名はallowlistにない。作者列挙の `test_frozen_artifacts.py` は固定output 23件だけをhashし (`test_frozen_artifacts.py:154-178`)、新2fileのconsumerではない。
- **到達可否 / 判定**: **到達する** — filesystem列挙なのでuntracked状態でも新testを検出し、offenderになる。さらに作者列挙からは `test_login_headroom.py:1602-1643`、`test_p3_s4_loop.py:1107-1119`、`test_reflux_ir.py:274-298`、`test_t1286_commit_receipt.py:657-700`、`test_s8b_oracle_report.py:5488-5508`、`test_t338_submission_gate_unit5.py:490-516` のsource走査も漏れている。
- **成果物影響** (DW-G05): repository development gateが赤のため、新probe証拠をB-4の受理済み成果物としてlandできない。
- **重大度**: must-fix
- **推奨 fix**: 新test自身に `pytest.main([__file__, ...])` を呼ぶplain runnerを追加する。consumer表は参照関係から再生成し、無関係なfrozen-artifact gateを外す。

### RB10

- **主張**: child isolationは有効だが、cleanup failureが元の失敗を隠す経路と、失敗時temp残置を検査していない。
- **根拠**: childはclean envと `-I -B` を実際に渡し (`test_p3_b4_wiring_probe.py:24-55`)、自己検査もある (`:82-97`)。一方、view生成失敗時は `rmtree(..., ignore_errors=True)` (`p3_b4_wiring_probe.py:1083-1085`)、check失敗中のfinallyは `_release_probe_view()` のcleanup例外で元例外を置換し得る (`:1484-1487,1099-1101`)。該当負例はない。
- **到達可否 / 判定**: **到達する** — permission/raceによるcleanup errorで元check例外がマスクされる。ただしchildは非zeroとなり、JSONも公開されないため偽緑にはならない。
- **成果物影響** (DW-G05): 通常のB-4 evidence値・受理集合は変わらず、失敗診断と隔離temp残置だけなので **nit**。
- **重大度**: nit
- **推奨 fix**: primary exceptionを保持し、cleanup errorをcause/ExceptionGroupとして併記する。cleanup failure時もevidence 0件・temp残置が明示診断されるtestを足す。

## 総括

- must-fix 9件、nit 1件。
- nominal pathで実campaign outcomeを直接読む箇所はoverlay以外に確認しなかったが、B3の未知rootとI/O bypassは未閉鎖。
- pre-bound original callable、直接 `compile`/`exec`/新規import、通常の `subprocess.Popen` はguard有効中は閉じている。
- swap-and-restore、既存thread、aliased dynamic resolution、`os.fork` 系は静かに合格し得る。
- `record_diff_reject` のprivate wrapperは既存3 callerをrebindしておらず、別processの通常driver挙動自体は変更していない。
- `-I -B` とclean envはコード上有効。child失敗も概ねreturn codeで捕捉される。
- evidenceの限定文は概ね裁定に沿うが、identity locator漏洩と `switchpoint_passage` のmachine-readable表現は広すぎる。
- pytestは1 nodeidも実行しておらず、緑とは判定していない。