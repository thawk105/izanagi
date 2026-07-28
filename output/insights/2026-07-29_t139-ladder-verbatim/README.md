# [T-139] dev-wave 2026-07-28〜29 逐語凍結

`authority: none` / `default_effect: no-state-change` — 凍結スナップショット。可変状態の正本
(worklog 末尾・現行 phase doc) ではない。

親台帳 = `../2026-07-29_t139-silo-degradation-ladder-design.md` (全所見の裁定は同 §9)。

## payload と sha256

- `parent-brief.md` — 段 1 親 brief (provisional 裁定 (P1)〜(P5) 込み)
  `14dccac357574116bb1bccea3778a3610c362a4839eee7c70fcbb15e84066fa2`
- `s2-plan.md` — 段 2 codex プラン起草 (gpt-5.6-sol, reasoning=max, read-only)
  `948d4b6e13ce6e3536267f77347976f98a1836e84166eaeb325cab25bb76967d`
- `s3-lensA.md` — 段 3 敵対相談 (正しさ境界)
  `e19a2ba257b1938e7b3befe7402fbe7c56938a6ee4d039fba23d76a6647aa6ab`
- `s3-lensB.md` — 段 3 敵対相談 (整合・実効性)
  `0ca4d34969bd1d790c8327c65c120e55dc2f42846f0a70d241a64f15a7750029`
- `s6-r1.md` — 段 6 敵対レビュー (主張の正しさ・過大性)
  `86a14ef5d061f23db69da9120425925d2130a5e894468bf3672d1e6113ac7c65`
- `s6-r2.md` — 段 6 敵対レビュー (記録整合・再現性・規約)
  `c8ef42a6652d9174709086ec1e88e21cc9cbd381849503bb2882c90b71ed7d75`
- `s6-focus.md` — 段 6 焦点再レビュー (closed/partial/regressed 表)
  `db9263f4c24615c1aac836e242021dcbbb63ded4a7f57e9f9033714981393e35`
- `handoff-final.md` — 専用 handoff の最終 snapshot (段 4 裁定・DW-O12 訂正・fix round 2 込み)
  `a060cab5b9a2173fc7d8c4f3d4bbf3aae32fac789d44a82de59718feacd4eef5`
- `t139-probe-degradation.patch` — 使い捨て probe patch (候補 A/B、裸マクロ、既定 OFF)
  `5fa7bb628a4fa1d4524db8cfb8588be4d5f342f386ae7bc1e9e222a469077b3c`
- `t139_probe_correctness.py` — correctness leg driver (login node)
  `eddd822f36434a15515e1fb0ffbb28fde4920ca597139b526263762061f33712`
- `t139-probe-correctness.json` — correctness leg 結果
  `c2f136d8a148530ac3e110cfba0fe539f2cf6fed808f716065dfa725e595725d`
- `t139-probe-correctness.provenance.json` — 同 post-hoc provenance (段 6 R1-6 応答)
  `e9c9b194b59e738edb8f78324947df1348bcbd5db4357f3296b73566dfa63348`
- `t139_probe_gap.sh` — gap leg PBS ジョブ (job 873583。実測 = `output/env/pegasus/t139-probe/`)
  `67b26fd5167687091b55371003ed0f8ebc0c565cc8be22c238b577a49580ca6c`

**射影規則 (F12 型リーク防止):** 本 dir の内容 (劣化機構の具体・stock 逐語・レンズ/レビュー
所見) を coder / planner / axis-proposer の入力へ射影してはならない。rung recovery 実験では
「stock の挙動」が答えに相当するため、rung 実装の所在と機構名も入力に含めない。現状の防壁は
planner/coder の tools:[] 構造遮断 + 親の自己規律であり、machine-readable role field と射影
gate は恒久実装の要件 (親台帳 §6-5)。

注 1: 段 2/3 の codex 子は worktree 基準ずれ (origin/main = 588f6a0) の tree を読んだ。差分は
T-160 の docs のみで所見の実質へ影響しない。s2-plan の「D94 新設」は誤り (D94 は T-160 が
使用済み、次の空きは D95)。
注 2: `s3-lensA.md` が参照する worktree 内 handoff パスは、DW-O20 に従い handoff を job tmp へ
移した後は存在しない (凍結時点の逐語をそのまま保存 — 最終状態は `handoff-final.md`)。
