pytest は未実走。`premise_probe.py` の再実行も一時ディレクトリ不足で停止したため、緑とは扱わない。

[severity: must-fix] [攻撃シナリオ] 2 module を変更した commit で activation report を再生成すると、module blob hash が変わり、digest・trial ledger・receipt bytes も変わる。凍結 pin 不在から「producer 出力不変」は導けない。[根拠 `orchestrator/campaign/s8c_preregistration.py:1555-1609,1767-1771`; `orchestrator/campaign/trial_registry.py:1244-1246,1572-1575,2412-2414`; `docs/worklog.md:589-593`; `s2-plan.md:203-203`] [提案] FROZEN/g1 の不変と派生出力の変更を分離して brief を修正し、digest 波及を downstream テストまたは「再生成しない」証跡で明示する。凍結成果物の再発行不要という結論自体は妥当。

[severity: should-fix] [攻撃シナリオ] plan は direct caller の列挙自体はほぼ完全だが、`campaign.*` と `orchestrator.campaign.*` の別 module object、`load_contract_bytes`・`semantic_contract_sha256`・module-level `evaluate_all` の公開経路を「全 caller」に含めていない。[根拠 `s2-plan.md:64-117`; `orchestrator/campaign/s8c_preregistration_evidence.py:18-21,191-269,669-749`; `orchestrator/campaign/s8c_preregistration.py:1496-1539`; `orchestrator/campaign/p3_autonomous_workload_trial.py:37-87,2345-2350`; `orchestrator/campaign/trial_registry.py:27-43,1223-1228`] [提案] closure 表に間接 consumer と両 namespace を追加し、package-mode の loader/activation smoke を加える。固定 path、generation path、現行契約には CR/LF がなく、既存正常 caller の破壊は静的には見つからない。

[severity: should-fix] [攻撃シナリオ] 不正 path を含む契約は `validate_condition_freeze_at`／`prepare_revision` では `core.evidence_contract_sha256` を通って freeze-valid になり得る。後段 registry で初めて `contract-invalid` になるため、freeze と activation report の状態が分離する。[根拠 `orchestrator/campaign/s8c_preregistration.py:340-347,1332-1448,1672-1725`; `orchestrator/campaign/s8c_preregistration_evidence.py:191-269,677-694`] [提案] 「freeze は通るが effective にはならない」を明文化し、`activation_report_at` の回帰を追加するか、freeze hash 側でも schema/path 検査するか裁定する。

[severity: should-fix] [攻撃シナリオ] embedded CR/LF の実 Git fixture は `alias-target.txt` しか作らないため、guard なしでは framed request が missing になり、embedded alias 自体を実証しない。[根拠 `s2-plan.md:138-153`; `orchestrator/campaign/s8c_preregistration.py:963-978`; `premise_probe.py:20-32`] [提案] `alias-` と `-target.txt` を別 bytes で commit し、`alias-\n-target.txt`／CR でも新 reason が出ることを確認する。末尾 CR の alias test は現状の plain target で十分。

[severity: should-fix] [攻撃シナリオ] `test_contract_loader_accepts_normal_relative_paths` は guard を全削除しても緑になるため、新検査の mutation detection には数えられない。[根拠 `s2-plan.md:179-183`; `orchestrator/campaign/s8c_preregistration_evidence.py:168-188`] [提案] 正常系回帰として扱い、M01〜M12 の帰属は embedded/trailing の明示 reason・message assert に限定する。指定内容どおりなら M01〜M12 に静的な survivor はない。

[severity: should-fix] [攻撃シナリオ] `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` と invariant の candidate test は HEAD・実 worktree・実 Git 状態に依存し、T-714 と無関係な cross-wave 差分でも赤くなり得る。[根拠 `s2-plan.md:191-203`; `orchestrator/tests/test_s8c_preregistration_predicates.py:107-131`; `orchestrator/tests/test_s8c_preregistration_invariant.py:118-145`] [提案] mutation の first-failing nodeid から除外し、baseline／cross-wave review として別扱いにする。新規テストを tmp Git に置く配置は妥当で、重い real-repo group への追加は不要。

[severity: nit] [攻撃シナリオ] 不正契約で「evidence ref が一切構築されない」と誤読すると、実際には安全な `contract_ref` が loader 前に作られている。[根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:684-694`; `s2-plan.md:185-189`] [提案] テスト名を「malicious path の EvidenceRef 構築前」に修正する。新 exception は raw path を含まず、`repr(where)` と enum reason へ写像されるため、CR/LF によるログ行分断対策は妥当。[根拠 `s2-plan.md:119-134`; `orchestrator/campaign/s8c_preregistration.py:1844-1846`]

[severity: should-fix] [攻撃シナリオ] brief の (i)〜(iii) を「probe 実測」として監査しても、提示された probe は alias と `_safe_path` しか検査しない。[根拠 `brief.md:17-21`; `premise_probe.py:1-47`; `orchestrator/tests/test_frozen_artifacts.py:38-85`; `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1`] [提案] (i)〜(iii) は独立静的検査の結果として記録する。独立確認では (i)〜(iii) は真、(iv) は偽。

## 総括

- M01〜M12 は指定 assert 前提なら静的に全て検出可能で、pytest の緑は未確認。
- direct caller に漏れはないが、両 namespace と派生 consumer を closure に明記すべき。
- 最大の問題は module hash → activation digest → ledger/receipt への bytes 波及を不変とした brief。
- FROZEN_MANIFEST・g1 の pin 不在、現行契約の CR/LF 0 件、既存理由語 0 件は確認済み。