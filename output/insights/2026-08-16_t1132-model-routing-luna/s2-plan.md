結論は、`flip trick` ではなく I3 を解く明示的な stage 分割を推奨します。`flip trick` は I1/I2 を表面上維持しますが、`--lane sol` と `--lane luna` の意味が逆転します。また、brief の変更面には reasoning 変更に必須の `docs/dev-wave/workers.md` と関連 pin/test が欠落しています。

## 現行実装の検算

| stage | 現行 model | effort の束縛 |
|---|---|---|
| plan | `other_model` = sol | caller 指定、契約は max |
| consult/sol | `consult_models[0]` = sol | caller 指定 max |
| consult/luna | `consult_models[1]` = luna | caller 指定 max |
| author | `other_model` = sol | caller 指定 high |
| review | `other_model` = sol | docs 由来 high |
| fix | `other_model` = sol | caller指定、段5契約を継承して high |
| focus | `other_model` = sol | docs 由来 high |

- I1 は runtime invariant です。[launch_authority.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:31) が3値を抽出し、[同:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:396) が `other == consult lens 1` を拒否付きで強制しています。
- I2 は brief の表現ほど強くありません。[test_dev_wave_launch_authority.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:98) は現行 docs に対する正例 assert で、`snapshot_authority()` 自身は2モデル同一を拒否しません。現行 repo 全体では exact docs pin とこのテストにより守られますが、runtime invariant ではありません。
- I1 のテスト側対応は同ファイル [102–105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:102) にもあります。
- I3 は [derive_launch():426–433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:426) のとおり、consult 以外をすべて単一 `other_model` に送るため成立しています。
- review/focus だけが docs-bound effort です。[launch_authority.py:438–445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:438) と [dev_wave_codex.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:26)。author/fix は [同:167–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:167) の caller 指定のままです。

なお、変更は [D241:11243–11247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:11243)、[D243:11309–11321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:11309)、[D266:12259–12270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/decisions.md:12259) の値を覆します。`high→max` は D207 の「引き下げ禁止」には反しませんが、D243/D266 の明示値とは衝突するため、段4で後継のユーザー裁定として supersede を記録する必要があります。

## 推奨案 — I3 を解き、段2/5だけ luna、段6 model は sol

### DW-O01

[operations.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/operations.md:14) を次へ置換します。

```text
`<model>`: 段 3 は `--lane sol`=`gpt-5.6-sol`、`--lane luna`=`gpt-5.6-luna`、段 2/5 `gpt-5.6-luna`、段 6 `gpt-5.6-sol`。
```

結果は plan/author=luna、consult=名前どおりの混成、review/fix/focus=sol です。

### launch_authority.py

[launch_authority.py:31–35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:31)

- 現行 regex を削除せず legacy v1 として残す。
- 上記4値を `consult_sol`、`consult_luna`、`plan_author`、`stage6` として読む v2 regex を追加する。
- live の `snapshot_authority(commit=None)` は v2 だけを許可し、明示的な historical `commit=` では v1/v2 の双方を許可する。

これは必須の後方互換です。[codex_worker_launch.py:2852–2873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:2852) が過去 receipt の authority commit を現行 parser で再構築するため、単純に regex を置換すると旧 v3 receipt が検証不能になります。

[launch_authority.py:64–72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:64)

- `other_model` を `plan_author_model` と `stage6_model` に分割する。
- `as_dict()` は現在と同じ commit/section/digest のままとし、receipt schema を不要に変更しない。
- legacy v1 は両フィールドを旧 `other` で初期化する。

[launch_authority.py:389–417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:389)

- legacy v1 では現行 I1 (`other == consult_sol`) を維持する。
- v2 では旧 I1を意図的に壊すと明記し、代わりに `stage6_model == consult_sol` を強制する。
- v2 には `consult_sol != consult_luna` の明示拒否を追加し、I2 を正例 assert から live runtime invariant へ昇格する。

[derive_launch():421–452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:421)

- `consult`: 現状どおり named lane。
- `plan` / `author`: `plan_author_model`。
- `review` / `fix` / `focus`: `stage6_model`。
- `lane` の許容集合は変えない。

したがって、旧 I1 は段2/5について「壊す」案です。追加コードで段6だけを旧安全側へ束縛し直します。I2 は壊さず、むしろ runtime 強制へ強化します。

### reasoning effort

brief にない必須面です。

[workers.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:23)、[同:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:47)、[同:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:65)

- DW-S05-A: `reasoning=high` → `reasoning=max`。
- DW-S06-A: `reasoning=high` → `reasoning=max`。
- DW-S06-C: `reasoning=high` → `reasoning=max`。
- DW-S06-B は [57–58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/docs/dev-wave/workers.md:57) の継承を保ち、第二の literal を置かない。

この最小案では review/focus は実引数まで docs-bound になりますが、author/fix は引き続き caller 指定です。段5まで機械束縛する拡張は、`DW-S05-A` を authority snapshot に追加し、`dev_wave_codex.py`、receipt stage validation、旧 receipt schema 互換まで変更する必要があります。D266 が意図的に段5 pin を見送っていることもあり、本 wave の既定案には含めません。

### check_docs.py

[check_docs.py:264–267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:264)

- `DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL` を新しい4値の権威行へ更新。
- [3846–3898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:3846) の exact-one、権威行外 slug 不在検査は維持する。

[check_docs.py:347–374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:347)、[同:4049–4073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:4049)

- S06-A/C の定数名を `...HIGH...` から `...MAX...` へ変更する。
- exact sentence、finding 文、expected 値をすべて max へ同期する。
- S02/S03=max と O16 の effort 不在検査は不変。
- S05 pin は追加しない。

## `flip trick` の具体形と問題

現行:

```text
`<model>`: 段 3 のみ 2 本で `gpt-5.6-sol`→`gpt-5.6-luna`、他段 `gpt-5.6-sol`。
```

flip:

```text
`<model>`: 段 3 のみ 2 本で `gpt-5.6-luna`→`gpt-5.6-sol`、他段 `gpt-5.6-luna`。
```

この案は次の理由で現行 I1/I2 を通ります。

- I1: parser が `sol` と名付けた第1 capture は実際には luna になり、`other` も luna なので [396–397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:396) を通る。
- I2: 第1・第2モデルは依然異なるため [test:98–101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:98) を通る。
- [derive_launch():426–433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_waves/launch_authority.py:426) により、`--lane sol` が luna、`--lane luna` が sol になる。
- [dev_wave_codex.py:187–214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:187) は job id と下流 argv に元の lane 名を残し、[codex_worker_launch.py:1722–1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/codex_worker_launch.py:1722) も receipt に `lane=sol, requested_model=luna` と記録します。拒否にはなりませんが、レンズ帰属が逆転します。
- 権威行だけを変える文字どおりの docs-only 変更は、[check_docs.py:3877–3898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/check_docs.py:3877) の旧 exact pin に拒否されます。land 可能にするには checker とテストも変更するため、「launcher code を変えない案」であって「repo の docs-only 案」ではありません。

### 実在する lane call site

静的 grep では `/work/1/SFC/tanab/dev-wave-jobs` の `.sh` に143箇所、126ファイルありました。新 authority を使って再実行・転用した consult call は、各 `sol` が luna、`luna` が sol に反転します。`†` の6箇所は review に lane を渡しており、現状でも [dev_wave_codex.py:162–166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/tools/dev_wave_codex.py:162) に rc=2 で拒否されるため、flip による追加悪影響はありません。過去 worktree を絶対指定する履歴 script は遡及的には変わりませんが、この件数自体が lane 名を意味的 interface として使っている証拠です。

<details>
<summary>grep 結果（root = /work/1/SFC/tanab/dev-wave-jobs）</summary>

```text
2026-08-13_t1048-trigger-freeze-epilogue/run-consult-a.sh:9(sol)
2026-08-13_t1048-trigger-freeze-epilogue/run-consult-a2.sh:9(sol)
2026-08-13_t1048-trigger-freeze-epilogue/run-consult-b.sh:9(luna)
2026-08-13_t1050-s8b-admission/run-s3-lensA.sh:9(sol)
2026-08-13_t1050-s8b-admission/run-s3-lensB.sh:9(luna)
2026-08-13_t1050-s8b-admission/run-s3-lensB2.sh:9(luna)
2026-08-13_t1050-s8b-admission/run-s6-reviewA.sh:9(sol) †
2026-08-13_t1050-s8b-admission/run-s6-reviewB.sh:9(luna) †
2026-08-13_t1053-t1066/run-s3-lensA.sh:10(sol)
2026-08-13_t1053-t1066/run-s3-lensB.sh:10(luna)
2026-08-13_t907-t908-t910-acceptance-integrity/run-s3-lensA.sh:8(sol)
2026-08-13_t907-t908-t910-acceptance-integrity/run-s3-lensB.sh:8(luna)
2026-08-13_t968-floor-rep-integrity/run-s3-lensA.sh:8(sol)
2026-08-13_t968-floor-rep-integrity/run-s3-lensB.sh:8(luna)
2026-08-14_acceptance-bottleneck/run-consult-luna.sh:9(luna)
2026-08-14_acceptance-bottleneck/run-consult-sol.sh:9(sol)
2026-08-14_t1076-waiter-bytes/run-s3-lensA.sh:9(sol)
2026-08-14_t1076-waiter-bytes/run-s3-lensB.sh:9(luna)
2026-08-14_t1092-receipt-diagnostics/run-consult-luna.sh:10(luna)
2026-08-14_t1092-receipt-diagnostics/run-consult-sol.sh:10(sol)
2026-08-14_t817-epoch/run_s3.sh:7(sol),19(luna)
2026-08-15_t1038-tracked-handoff/run_s3.sh:8(sol),21(luna)
2026-08-15_t1087-acceptance-red-check/run_consult_a.sh:8(sol)
2026-08-15_t1128-floor-same-root/run-s3-luna.sh:8(luna)
2026-08-15_t1128-floor-same-root/run-s3-sol.sh:8(sol)
artifacts/dev-wave-hooktrust-t1067/run-consult-luna.sh:14(luna)
artifacts/dev-wave-hooktrust-t1067/run-consult-sol.sh:14(sol)
dev-wave-8c-formal-consumer-wiring/run-s3-lens-a.sh:9(sol)
dev-wave-8c-formal-consumer-wiring/run-s3-lens-b.sh:9(luna)
dev-wave-acceptance-critpath/run-consult-a.sh:6(sol)
dev-wave-acceptance-critpath/run-consult-b.sh:6(luna)
dev-wave-acceptance-critpath/run-consult.sh:11(sol),23(luna)
dev-wave-backlog-triage/run-lens-a.sh:7(sol)
dev-wave-backlog-triage/run-lens-b.sh:7(luna)
dev-wave-exec-loc-and-usage-fixes/codex/run-s3-lensA.sh:6(sol)
dev-wave-exec-loc-and-usage-fixes/codex/run-s3-lensB.sh:6(luna)
dev-wave-login-unreclaimable/run-consult.sh:9(sol),20(luna)
dev-wave-login-unreclaimable/run-consult2.sh:9(sol),20(luna)
dev-wave-parallel-dispatch/run-lens-a.sh:7(sol)
dev-wave-parallel-dispatch/run-lens-b.sh:7(luna)
dev-wave-t139-a12-stress-check/run-s3.sh:10(sol),21(luna)
dev-wave-t139-land2-q4/run-s3-lensA.sh:7(sol)
dev-wave-t139-land2-q4/run-s3-lensB.sh:7(luna)
dev-wave-t139-manifest-land2-s2/run_s3b2.sh:9(luna)
dev-wave-t139-manifest-land2-s2/run_s3c.sh:11(luna)
dev-wave-t139-manifest-land2/run_s6.sh:8(sol),9(luna) †
dev-wave-t139-q1-canonical-decision/run-s3-lensA.sh:10(sol)
dev-wave-t139-q1-canonical-decision/run-s3-lensB.sh:10(luna)
dev-wave-t184-followup/run_replay_A146.sh:8(luna),15(luna),22(luna),43(luna)
dev-wave-t316-copyout-t840/run-s3-lensA.sh:9(sol)
dev-wave-t316-copyout-t840/run-s3-lensB.sh:9(luna)
dev-wave-t316-r2-oracle/run_s3.sh:12(sol),22(luna)
dev-wave-t316-r2-oracle/run_s3a2.sh:10(sol)
dev-wave-t338-rf-validator/run_s3a.sh:8(sol)
dev-wave-t338-rf-validator/run_s3b.sh:8(luna)
dev-wave-t396-hole-allowlist/run-s3a.sh:7(sol)
dev-wave-t396-hole-allowlist/run-s3a2.sh:7(sol)
dev-wave-t396-hole-allowlist/run-s3b.sh:7(luna)
dev-wave-t402-flock-exechost/logs/launch_s3a.sh:7(sol)
dev-wave-t402-flock-exechost/logs/launch_s3b.sh:7(luna)
dev-wave-t499-approval-turns/s3/run-a.sh:7(sol)
dev-wave-t499-approval-turns/s3/run-b.sh:7(luna)
dev-wave-t513-trigger-exact/run-consult-a.sh:8(sol)
dev-wave-t513-trigger-exact/run-consult-b.sh:8(luna)
dev-wave-t657-stage0-fold/launch-s3-luna.sh:7(luna)
dev-wave-t657-stage0-fold/launch-s3-sol.sh:7(sol)
dev-wave-t657-stage0-rulings/run-s3-luna.sh:7(luna)
dev-wave-t657-stage0-rulings/run-s3-sol.sh:7(sol)
dev-wave-t657-stage0-rulings/run-s6-luna.sh:7(luna) †
dev-wave-t657-stage0-rulings/run-s6-sol.sh:7(sol) †
dev-wave-t756-trace-v2/run-s3-lens1.sh:10(sol)
dev-wave-t756-trace-v2/run-s3-lens1b.sh:10(sol)
dev-wave-t756-trace-v2/run-s3-lens2.sh:10(luna)
dev-wave-t781-spool-feasibility/launch-stage3-a2.sh:9(sol)
dev-wave-t812-lease-self-renew/run_s3_luna2.sh:11(luna)
dev-wave-t812-lease-self-renew/run_s3_luna3.sh:11(luna)
dev-wave-t816-step4/run-s3a.sh:7(sol)
dev-wave-t816-step4/run-s3b.sh:7(luna)
dev-wave-t817-verifier-epoch/s3/run-a.sh:9(sol)
dev-wave-t817-verifier-epoch/s3/run-b.sh:7(luna)
dev-wave-t827-slow-tests/run_s3b.sh:8(luna)
dev-wave-t8b-restart-residue/run-adv-a.sh:10(sol)
dev-wave-t8b-restart-residue/run-adv-b.sh:10(luna)
dev-wave-t904-hashobject-sep/run-s3a.sh:9(sol)
dev-wave-t904-hashobject-sep/run-s3a2.sh:9(sol)
dev-wave-t904-hashobject-sep/run-s3b.sh:9(luna)
dev-wave-t922-measure-happypath/run-s3sol2.sh:8(sol)
dev-wave-t950-acceptance-floor/run-consult-a2.sh:7(sol)
dev-wave-t950-acceptance-floor/run-consult-a3.sh:7(sol)
dev-wave-t950-acceptance-floor/run-consult.sh:8(sol),14(luna)
dev-wave-t983-snapshot-fixture/run-consult-a.sh:7(sol)
dev-wave-t983-snapshot-fixture/run-consult-b.sh:7(luna)
dev-wave-testops-observation/logs/s3-a.sh:8(sol)
dev-wave-testops-observation/logs/s3-b.sh:8(luna)
growth-tests/run-consult-luna.sh:6(luna)
growth-tests/run-consult-sol.sh:6(sol)
t-codex-hook-trust/run-stage3a.sh:6(sol)
t-codex-hook-trust/run-stage3a2.sh:6(sol)
t-codex-hook-trust/run-stage3b.sh:6(luna)
t1027-acceptance-reds-checker/run-consult-a2.sh:8(sol)
t1062-acceptance-scheduler/run-consult-luna.sh:11(luna)
t1062-acceptance-scheduler/run-consult-sol.sh:11(sol)
t1109-admission-grammar/run-consult.sh:6(sol),18(luna)
t499-triage/run-review-a.sh:10(sol)
t499-triage/run-review-b.sh:10(luna)
t810-harness-s2/s3-lensA-launch.sh:6(sol)
t810-harness-s2/s3-lensB-launch.sh:6(luna)
t810-harness/s3/runA.sh:9(sol)
t810-harness/s3/runB.sh:9(luna)
t810-node-variance/launch-s3b-r3.sh:20(luna)
t810-node-variance/launch-s3b-retry.sh:19(luna)
t897-trigger-admission/run-s3a.sh:8(sol)
t897-trigger-admission/run-s3a2.sh:8(sol)
t897-trigger-admission/run-s3b.sh:8(luna)
t905-guard-bytes-pin/run_stage3.sh:11(sol),24(luna)
t925-l15-budget/run-s3.sh:9(sol),20(luna)
t945-resume-mode/run-s3-lensA.sh:9(sol)
t945-resume-mode/run-s3-lensB.sh:9(luna)
t945-resume-mode/run-s3-lensB2.sh:9(luna)
t953-oracle-residue/run-consult-a.sh:8(sol)
t953-oracle-residue/run-consult-b.sh:8(luna)
t956-hooks-guard/run-s3a.sh:8(sol)
t956-hooks-guard/run-s3a2.sh:8(sol)
t956-hooks-guard/run-s3b.sh:8(luna)
t979-cheap-history-scan/run-consult.sh:10(sol),24(luna)
wave-t987-oracle-spec-design/run-s3.sh:8(sol),21(luna)
```

</details>

## 影響テスト

- [test_dev_wave_launch_authority.py:82–110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:82): 新 matrix を `plan==author==consult/luna`、`review==fix==focus==consult/sol` として明示。I2 assert は維持する。
- [同:129–145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:129): 3 slug の位置依存 cross-check を4 role の対応へ更新。
- [同:284–310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_launch_authority.py:284): `len(models)==3` と全位置 swap を廃し、legacy v1→v2 migration、historical v1 の再構築、plan/authorだけの変化を検査する。
- 同ファイルへ、v2 の同一 consult model 拒否、stage6≠consult-sol 拒否、live legacy 拒否／historical legacy 許可を追加する。
- [test_check_docs.py:6918–7247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:6918): model pin negative 群を再検査し、特に [7243–7247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:7243) の time-invariant literal を新権威行へ更新。旧行 fail／新行 pass の対を追加する。
- reasoning pin は [6267–6297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:6267)、[6331–6467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:6331)、[6504–6724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:6504)、[6752–6867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_check_docs.py:6752) の S06 high/max、定数名、decoy、finding を反転する。
- [test_dev_wave_codex.py:96–133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_dev_wave_codex.py:96): author/fix の代表 caller 値を high→max。lane の forwarding/no-model-override assert は維持。
- [test_codex_worker_launch.py:1805–1828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_codex_worker_launch.py:1805) と [2033–2056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_codex_worker_launch.py:2033) は derived 値を使うため基本的に追随する。[3361–3410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-model-routing-luna/orchestrator/tests/test_codex_worker_launch.py:3361) に legacy receipt→新 authority 後も検証可能、を追加する。
- grep で見つかる `test_codex_worker_launch.py:1348` の sol は schema v2 診断 fixture、role/provenance 系の sol literal は別 routing 面なので変更対象外です。

## 受理集合と DW-M01

| 案 | pass/fail の変化 | DW-M01 |
|---|---|---|
| 権威行だけ flip | 新行が現行 `check_docs` に fail。land不能 | 実装案として不成立 |
| checker同期済み flip | 旧権威行 fail、新 flip 行 pass。新 authority の receipt model 対応も反転 | 必要 |
| 推奨 I3 分割 | live v2 pass、live v1 fail、historical v1 は pass。stage別 receipt model 集合も変更 | 必要 |
| S06 high→max pin | worker docs の high が fail、max が pass。review/focus receipt effort も変更 | 必要 |
| S05 文書だけ high→max | launcher は unbound のため high/max とも CLI 受理。運用契約だけ変更 | 単独では受理集合不変 |
| S05まで機械束縛 | author/fix の caller effort を拒否し docs 値だけ受理。receipt/schema互換面も変更 | 必要、別scope推奨 |

段4では少なくとも次を事前登録します。

- 旧 model 権威行が live で拒否され、新行だけ通る。
- historical v1 authority/receipt は引き続き再構築できる。
- plan/author を sol へ戻す変異、stage6 を luna へ送る変異、consult lane を逆転する変異をそれぞれ独立に kill する。
- S06-A/C を high に戻す変異を exact pin が kill する。
- 新しい正常 matrix が過剰拒否されない正例を置く。

編集・pytest・checker 実走は行っていません。worktree は clean のままです。

## 総括

- I1 は runtime 強制、I2 は現状では正例 test 強制、I3 は単一 `other_model` による実装制約です。
- `flip trick` は I1/I2 を通す一方、143個の lane literal の意味を逆転させるため採用非推奨です。
- 推奨は model authority を consult／段2・5／段6へ分割し、段2・5=luna、段6=sol とする案です。
- reasoning 変更には brief が落とした `workers.md`、S06 pin 群、dry-run test の更新が必要です。
- model/pin の受理集合が変わるため DW-M01 が必須で、実装前に D241/D243/D266 の supersede 裁定も要ります。