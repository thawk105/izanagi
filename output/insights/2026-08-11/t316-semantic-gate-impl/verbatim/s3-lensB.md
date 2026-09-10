静的レビュー結果は NO-GO。pytest・実測は行っていない。

## 所見

1. `[severity: blocker]` N1 の「denylist なら sort 軸に置ける」は、裁定範囲を越える。

根拠: `s1-brief.md:8-16,35-42`、`s2-plan-c.md:344-350`、`docs/worklog.md:2328-2332`、`docs/decisions.md:6235-6245`。通常の comparator は `storage_`/`key_` と `std::sort` だけを使うため denylist に触れない。一方、role 契約違反の coder は `std::system`、`execl`、`std::ofstream`、無限ループを raw comparator/hole に混入でき、role 文書だけでは機械的に止まらない（`.claude/agents/coder-v4-autonomous-sort.md:60-101,132-134`、`docs/phase3-s5-sort-runbook.md:77-112`）。

R1 の「合成が allowlist 選択へ化ける」という理由は typed comparator DSL には直接当たるが、有限 lexical denylistそのものが typed IR になるわけではない。この限定は親の主張どおり。ただし denylist は source DSL/IR 化でも strict copy-out でもなく、裁定された build 防壁の第三の選択肢である。

成果物影響: 未知の host effect を含む raw C++ が build・certified 選択・proof chain に残り、denylist適合だけでは build 段の安全性を証明できない。

修正提案: denylistを「測定済み4種に対する受理集合の縮小」と明記し、build 防壁の代替とは称しない。build防壁として採るなら DSL/IR または copy-out の選択をユーザー裁定へ返す。

2. `[severity: blocker]` R3-3 は本 wave が実際に踏んでいる。

根拠: R3-3 は `package.md:105-110` で canonical field mapping を要求している。計画は `coder.implementation` を scanner に渡す一方、`quarantine()` は rendered source と `working_diff` を生成し（`p3_s4_loop.py:192-243`）、auditor digest と既存 WAL は `working_diff` 側を参照する（`p3_s4_loop_sort.py:149-168`、`auditor_gate.py:5-15`）。`s2-plan-c.md:103-133` には、この三つの byte domain の対応付けがない。

成果物影響: scanner の拒否理由・WAL digest・auditor対象・実際に build された source が別 byte domain を指し、受理集合と proof chain の参照が一致しなくなる。

修正提案: scanner入力、rendered source、hole working diff、preprocess後 source の正本を一つに決め、canonical field・digest・WAL bindingを定義する。未定義のままなら「semantic gate」ではなく局所的 lexical pre-filter として扱う。

3. `[severity: blocker]` 「sandbox 非依存部分集合だから実装 wave を進められる」は成立しない。

根拠: `docs/worklog.md:2328-2332` は `[T-184]`、R3-3〜R3-9、R2-b を未解消のまま維持している。R3 は `package.md:92-136` で前提条件が揃うまで実装 wave を起票しないとしている。特に sort の非SWO・fairness/reward hack は新 gate の対象外であり、runbookも auditor静的目視だけを残している（`docs/phase3-s5-sort-runbook.md:182-193`）。

成果物影響: host effect の一部を拒否しても、candidate-controlled trace/stdout に基づく `certified`、`fitness_tps`、sort選択の偽装余地と proof chain の不確実性は残る。

修正提案: R2-bを実装するか、sortをcertified対象外/既知残余として台帳化するまで、certified安全性を主張しない。`[T-184]` と R3-1/2/4 も完了条件として残す。

4. `[severity: must-fix]` 単一 `quarantine()` seam は全 untrusted materializer の閉包ではない。

根拠: 計画自身が `s5_permutation_coverage.py` を scope 外にしている（`s2-plan-c.md:21-32,352-361`）。同処理は `subprocess.run` で buildcache 非経由の直接 build を行う（`s5_permutation_coverage.py:138-164`）。さらに registry は shell materializer と任意 binary path を意図的に閉じていない（`materializer_admission.py:11-13`）。buildcache の configure/build、pipeline trace、preprocess、nmも別の実行層である（`buildcache.py:723-738,1052-1066`、`pipeline.py:257-278,748-795`、`source_digest.py:320-342`）。

成果物影響: coder hole 以外の build/run 経路には sandbox execution receipt と strict copy-out がなく、そこから得た材料を certified/proof chain に入れる場合の host境界が未閉鎖になる。

修正提案: stage matrixで対象層を列挙し、非admissible materializerは selection/proof chain から機械的に除外する。build層を守る主防壁は裁定済みの DSL/IR または strict copy-out とする。

5. `[severity: must-fix]` N4 の恒真フィールドを残したまま、previewの意味 gate を閉じたことにはできない。

根拠: `p3_autonomous_workload_trial.py:652-673` は `forbidden_identifiers: []` を固定し、consumerはそれを読む（`autonomous_trial_completeness.py:607-624`）。計画も明示的にこの穴を scope 外にしている（`s2-plan-c.md:352-360`）。

ただし「新 gate に consumer が全くない」という親の主張は部分的に refuted される。`passed` は `p3_autonomous_workload_trial.py:1773-1785` で実際に pre-audit reject へ接続されている。恒真なのは `forbidden_identifiers` フィールドである。

成果物影響: preview/journal/completion evidence は effect finding を持たないまま `forbidden_identifiers=[]` を記録し、拒否理由と台帳上の参照が食い違う。

修正提案: そのフィールドを廃止するか実際の finding schemaへ接続し、`_preview`からcompletion consumerまでの負制御を追加する。少なくともN4未解消を成果物へ明記する。

6. `[severity: must-fix]` 親の M2 は実 driver の実測ではない。

根拠: `probe_premises.py:36-56` は `L.quarantine()`、`parse_auditor_dict()`、`assert_digest_matches()` を直接呼ぶだけで、`S._quarantine_and_audit()` や buildを呼んでいない。backoffも骨格適用失敗後に `assert_value_literal_consistent()` だけを測っている（`probe_premises.py:69-83`）。実 driverの順序は `p3_s4_loop_sort.py:149-168` と異なる。

成果物影響: auditor pass後に実際に build/admissionへ進むこと、WAL記録、driver固有の拒否理由は未検証であり、親の4/4実測から certified経路を一般化できない。

修正提案: 「shared seamのprobe」と「driver E2E」を分離して記録する。sortは実際の `_quarantine_and_audit()` の no-build 経路、triggerは既存全call site、backoffはpin一致後の実経路を別々に検証する。

7. `[severity: must-fix]` 変異の帰属が W-1 と W-2 で分離されていない。

根拠: 計画の4注入＋auditor passテスト（`s2-plan-c.md:279-291`）は、machine gateが先に拒否する現在の順序（`p3_s4_loop_sort.py:149-166`）では必ずW-1の赤になる。これでは auditor deny-only composer を削除しても、同じ注入テストは赤のまま残り得る。純粋関数のmeta-test（`s2-plan-c.md:293-306`）だけではdriverからcomposerを外す変異を検出できない。

成果物影響: mutation ledgerが「auditor bypassを殺した」と誤帰属し、実際には生存しているW-2配線欠落を見逃す。

修正提案: W-1は host-effect subtype を検査し、W-2は正常machine-pass＋auditor reject/uncertainを実driverで検査する。machine reject＋auditor passは非拡大性だけの別テストに分離する。

8. `[severity: must-fix]` W-2のauditor deny-onlyはbackoff経路には存在しない。

根拠: 計画のW-2配線対象はsortとtriggerだけ（`s2-plan-c.md:183-208`）。backoffのproposal schemaは `require_auditor=False`（`p3_s4_loop.py:945-960`）で、実経路も `quarantine()` 後に直接 `run_campaign()` へ進む（`p3_s4_loop.py:890-915`）。

成果物影響: backoffではauditor出力による拒否境界もdigest echoの消費もなく、W-2を全軸の保証として読むと受理集合とproof chainの説明が過大になる。

修正提案: backoffは「auditorなし・machine gateのみ」と明記するか、auditor producer/schema/materializer接続を別裁定で設計する。存在しないauditorを暗黙に保証済みとしない。

## 親の主張で refuted / 正しいもの

- `N1`の「denylist自体はtyped IRではない」は正しい。ただし「だから裁定不要」は誤り。
- `N2`は、現行のcanonical trigger predicateに限れば妥当。`reflux_ir.py:113-141`、`trigger_gate_binding.py:98-202`、`p3_s4_loop_trigger_gating.py:406-416` が既存の閉じた経路を形成する。probe自体はtriggerを実測していない。
- `N3`のsubmodule pin不一致と、backoffがvalue/literal契約しか測れていない点は正しい。
- 5候補ファイルに対するlive byte pinなしという主張は確認できる。T080のSHAは現在のworktreeではなくmigration basis commitを検査する歴史記録（`t080_freeze_migration.py:760-766,1071-1087`）。ただしrole/adapterにはrole本文のhashがある（`.codex/role-adapters/coder-v4-autonomous-sort.json:163-185`、`auditor.json:230-235`）ため、「pinが一切ない」と一般化するのは誤り。
- 既存WAL/loader/rendererの再利用（`s2-plan-c.md:135-163`）は適切。`SYNTAX_CONTRACT_FORBIDDEN` はtrigger emitterの内部drift検査で候補受理gateではない（`axis_trigger_gating.py:53-64`、`p3_s4_loop_trigger_gating.py:163-167`）。`build_admission.py`もsource effect検出器ではない（`build_admission.py:2-13,424-468`）。R3-8/R3-9を新たに踏んだとは判断しない。

## 総括

NO-GO。denylistは限定的な受理集合縮小であり、裁定済みbuild防壁でも完全な意味境界でもない。  
R3-3、[T-184]、R2-bなどのblockerは未解消で、N4・materializer閉包・変異帰属にも未閉鎖がある。  
実装するなら「測定済みlexical defense-in-depth」として範囲を明示し、certified安全性の主張を保留すべきである。