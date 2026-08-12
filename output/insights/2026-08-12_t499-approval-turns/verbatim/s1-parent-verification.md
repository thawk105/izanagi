# 親の独立検算 — [T-499] (A)(B)

段 2 子の所見のうち、親が一次資料を直接開いて確認した事実だけを並べる。
子出力 (`s2/.../attempt-0001.output.md`) は `check_codex_output` rc=1 で**不受理**
(原因 = 親 prompt の「ASCII のみ」指示により見出しが `## Soukatsu` とローマ字化)。
よって子出力は根拠にせず、下記の親実測だけを段 4 の根拠とする。

## (A) 側

| # | 事実 | 一次資料 (親が直接確認) |
|---|---|---|
| A-1 | canonical path `output/s8b-oracle-spec/` は不在 | `ls` / `git ls-files` |
| A-2 | reviewed spec を書く **production 経路はゼロ**。書き手は test 側のみ (fixture に加え `test_s8b_oracle_manifest.py:266,1104,1154` にも直接 writer がある) | `grep -rn "SPEC_REL"` |
| A-3 | `output/s8b-oracle-spec/` にファイルが 1 つでもあれば `assert durable_files == []` が失敗。schema version による分岐は無い | `test_s8b_oracle_manifest_contract.py:127-143` |
| A-4 | D302 は「durable 発行 0 件を機械確認したうえで schema version を据え置く。durable 発行後にこの決定を変えるなら再発行が要る」と明記 | `docs/decisions.md` D302 却下選択肢 |
| A-5 | `build-approved` は spec の producer ではなく consumer。CLI 入力は `--output` のみ | `s8b_oracle_manifest.py:1170-1254` |

**A-2 の訂正**: brief の初稿は「書き手は fixture のみ」と書いたが、test module 内にも直接 writer が
ある。**production 経路ゼロという結論は変わらない**が、逐語の inventory は不正確だった。

## (B) 側

| # | 事実 | 一次資料 (親が直接確認) |
|---|---|---|
| B-1 | v2 世代 record `holdout_freeze.v2.g<N>.json` は不在 | `git ls-files output/s8b-freeze` |
| B-2 | pointer が指す世代が index に無ければ `pointer-generation` で必ず拒否。live pointer ゼロなら `no-active` | `s8b_ratified_freeze.py:1231-1256` |
| B-3 | **世代導入 commit G は「非 none の `AI-Agent` trailer」が必須**。`AI-Agent: none` なら `generation-commit-none` = 「AI 生成物の provenance 虚偽」として拒否 | `s8b_ratified_freeze.py:551-570` |
| B-4 | **approval / pointer 導入 commit A は逐語 `AI-Agent: none` が必須**。満たさなければ `user-commit-trailer` で fail-closed | `s8b_ratified_freeze.py:524-547` |
| B-5 | 世代候補の producer は**存在する** (`generate-v2-candidate --floor-result --budget`)。ただし candidate path 止まりで、canonical generation path への promote 経路は無い | `s8b_holdout_freeze.py:46,1561-1602` |
| B-6 | その producer の前提が 2 つとも未成立: `BUDGET_APPROVAL_SHA256 = None` → `budget-approval-not-ratified`、および floor result に `mode=official` かつ `eligible_for_refreeze=true` を要求 | `s8b_holdout_freeze.py:49,1161-1163,1256-1259` |
| B-7 | official の受理集合は**空のまま**で、pilot 成果物は `eligible_for_refreeze=false` のため再凍結に使えない。解禁 gate は [T-088] official guard | `docs/phase3.md:118-123` |
| B-8 | D328 は `HELD=True`、解除は explicit-user-command-only。保留 check_id 21 件に `s8b-holdout.*` / `s8b-oracle.known-axes-*` を含む | `freeze_verification_hold.py:14-65` |
| B-9 | provenance 規約は「Git 操作の機械的代行は記録しない」。この経路なら `AI-Agent: none` は正当だが、それは**ユーザーが承認内容を確定した場合**であり、AI が承認判断を行ったことにはならない | `docs/ai-provenance.md` 記録単位 |

## B-3 と B-4 の含意 (本 wave の核心)

機構は **「世代は AI が作ってよい / 承認は人間だけ」を C1-6 として機械強制**している。
両検査は同一 module 内で対になっており、片方だけを満たす commit は必ず fail-closed になる。

したがって (B) は「対象が無いから今できない」だけでなく、**対象が揃っても AI は承認 commit を
作れない**。作るには (i) `AI-Agent: none` と偽って provenance 虚偽を犯すか、
(ii) `_assert_user_commit` を緩めるかの二択しかなく、どちらも規律 2 / 信頼境界の違反である。
