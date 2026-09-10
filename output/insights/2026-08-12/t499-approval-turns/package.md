# [T-499] 凍結・承認手番 (A)(B) — 実施可否の実測と裁定パッケージ

wave: `dev-wave-t499-approval-turns` (2026-08-12)。実装面 diff ゼロ、docs のみ。

## 何を確かめたか

ユーザーは第 5 束 (2026-08-12、authority: user) で「T-499 の凍結・承認手番
(oracle 仕様の承認 SHA 記入・freeze v2 pointer 設置) は AI へ委任」と裁定した。
本 wave はその実施を試み、**承認対象そのものが未生成であるため実行できない**ことを実測した。

検証は 4 系統が独立に一致した。

| 系統 | 成果物 | 受理 |
|---|---|---|
| 段 2 プラン子 (codex plan, reasoning=max) | `verbatim/s2-plan-rejected.md` | **不受理** (`check_codex_output` rc=1) |
| 段 3 レンズ A (codex consult sol) | `verbatim/s3-lens-a.md` | rc=0 / 8,027 bytes |
| 段 3 レンズ B (codex consult luna) | `verbatim/s3-lens-b.md` | rc=0 / 7,281 bytes |
| 親の一次資料検算 | `verbatim/s1-parent-verification.md` | — |

段 2 子が不受理になったのは**親の prompt 不備**である。NFC 由来の事故を避けるつもりで
「ASCII のみ」と書いたところ、子が字義どおり守って見出しまで `## Soukatsu` とローマ字化し、
validator の `^## 総括` に当たらなかった。子の作業自体は健全だったため、再投入せず
**親が全所見を一次資料で検算**して採用した (子出力は根拠に使っていない)。

## 結論

- **(A)** reviewed bytes と、その内容である研究設計値が未確定のまま
  `APPROVED_SPEC_SHA256 = None`。canonical path も production の生成経路も無い。
- **(B)** budget pin / production official floor result / canonical generation record の
  **三者不在**。v2 candidate producer 自体は実在するが、その入力が揃っていない。

レンズ A は全 126 ref・dangling commit・全 worktree・dev-wave job 保存域まで探索し、
reviewed spec・v2 世代・budget approval の**いずれも存在しない**ことを確認した。

## 親が撤回した 2 つの主張

段 1 brief で親が挙げた実施不能の根拠のうち、2 つは検証で誤りと判明したため撤回した。

1. **「AI は承認 commit を作れない」** — `_assert_user_commit` が検査するのは非 merge・
   逐語 `AI-Agent: none`・祖先性であり、内容を誰が選んだかではない。ユーザーが exact bytes を
   確定した後の機械的な Git 代行なら `AI-Agent: none` は正当に成立する。
   今回使えないのは exact bytes が無いからにすぎない。
2. **「(B) は D328 と衝突する」** — D328 は正しさゲートと admission を明示的に対象外としており、
   承認連鎖の構造検証はそこに入る。さらに別 wave の敵対相談
   (`output/insights/2026-08-12_freeze-chain-hold-sweep/verbatim/s3-consult-sol.md:110-120`) は
   [T-499] A/B を保留の**明示的 keep 集合**へ入れるよう要求している。
   **(A)(B) の fail-closed は、緩めずに保つべき正しさ境界である。**

## 副産物として確定した設計事実

- 機構は「世代は AI が作ってよい / 承認は人間だけ」を C1-6 として対で機械強制している
  (`s8b_ratified_freeze.py:524-570`)。世代導入 commit G は非 none の `AI-Agent` trailer が必須で、
  `AI-Agent: none` なら「AI 生成物の provenance 虚偽」として拒否される。
- D302 は「hash は識別子にすぎず、承認は内容の再導出を伴う」としている。
  **hash 記入だけを「承認完了」とは書けない。**
- `output/s8b-oracle-spec/` の contract test は、D302 の「durable 発行 0 件を機械確認したうえで
  schema version を据え置く」決定を守る番人である。設置するなら schema 再発行の判断が伴う。

## 裁定へ返した項

Q1 = (A) の進め方 (親推奨 = 事前登録が固まるまで待ち、producer と schema 再発行の設計を先行)。
Q2 = (B) の進め方 (親推奨 = 前提 2 つを先行タスクとして起票し、揃った後に AI が機械準備を担う)。
控えは repo 外 inbox `2026-08-12-t499-approval-turns-blocked.md`。
