単独段 dispatch: stage=consult; lane=luna; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair

必読事項の射影 (この列挙にある file が読めなければ即停止。**この停止規則は本射影 file 限定であり、自分で導出した path の不在では検査を打ち切らない**):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/diagnosis-pair-0001.md — 親の診断メモ (事実・機構の読み・provisional 裁定 P-A〜P-E)。**攻撃対象。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/brief.md — 親の段 1 brief。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/k2-loop-round4/verbatim/T-2795-pair-origin.md — ユーザー依頼の逐語 (停止規則を含む)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/evidence/attempt-0001/job.stderr — 実 job の traceback (逐語)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/orchestrator/campaign/campaign_claim.py — claim leaf (docstring と `acquire_claim`)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/decisions.md — D464 (19324 行〜)、D553 (22566 行〜)、D2172 項 3 (68552 行〜)、D2183 (69130 行〜) だけを読む。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/dev-wave/core.md — `DW-STOP`、`DW-G01`、`DW-S07`。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/skill-self-improvement.md — routing 節。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/docs/failures.md — `grep -n "^## F" ` で索引し、「実機で通していない」「説明と実装の食い違い」「生死実験」「launcher」「claim」に該当する F だけ読む (全文は読まない)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-19/k2-loop-round3/README.md — 3 巡目の記録 (pair 結果を追記する先)。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2795-k2-pair/output/insights/2026-09-20/t2795-pair-launcher/README.md — §0・§7。

## 依頼 (レンズ B: 停止の妥当性・記録の形・裁定パッケージへの攻撃)

前提 (レンズ A が別に攻撃中): stock 側 driver が `campaign_claim` の one-shot `O_EXCL` で拒否され、STOCK 成立は未確認、pair は不成立。
親の provisional 裁定は P-B (ユーザー指示に従い 4 巡目を投入せず、記録と裁定パッケージを残して正式停止)、P-C (裁定パッケージの択 (i)〜(iv))、
P-D (failures への記録型)、P-E (候補 10 の再評価値の扱い)。**これらを最も強い形で攻撃せよ。**

1. P-B: ユーザー指示「成立しなければその走を対照成立と認定せず報告して止める (再投入で救済しない、launcher 改修は scope 外)」は、
   「inert 不成立」を想定した文である。claim 排他という別原因での不成立にも同じ停止規則を適用するのが正しいか、それとも
   「直せる赤で終了しない」(DW-STOP) が勝ち、本 wave で launcher を直して再投入すべきか。**launcher 改修は scope 外と明記されている**点と、
   claim leaf は排他防壁 (D464 / D553) で受理集合の変更に当たる点を踏まえて判定せよ。親が本 wave でやってよいこと・やってはいけないことを分けよ。
2. P-C: 択 (i)〜(iv) のそれぞれについて「通してはいけない最も強い理由」を書け。加えて親が挙げていない択があれば示せ。
   最小差分・排他防壁の不変・D2183 の「同 campaign」の意味 (identity への影響) の 3 点で比較せよ。推奨を 1 つ選び、理由を書け。
3. P-D: failures の routing。既存 F への再発追記で済むか新 F か。該当しそうな F を索引から挙げて理由を書け。
   「実機で 1 job も通していない launcher を裁定と共に land した」を失敗と数えてよいか (T-2795 insight §0 は未測定を正直に書いていた)。
4. P-E と記録の形: round 3 README への追記節に書いてよいこと・書いてはいけないこと (数値の比較、「pair が取れた」風の表現、
   candidate の再評価値の位置づけ)。results 稿 (K2 3 巡稿と同形の単独稿 1 本まで) を本 wave で書くべきか (pair も 4 巡目も無い状態で)。
5. 親が見落としている記録先 (phase doc、claim-evidence 稿、D2172 / D2183 への追記の要否) があるか。

## 出力形式

markdown。見出しは `## 攻撃 1`〜`## 攻撃 5`、`## 成立しなかった攻撃` (成立しなかった項目は正直にそう書け。全項目を無理に成立させるな)、
`## 総括` (3〜6 行、P-B の当否を 1 行目に)。各主張に file:line または D/F 番号を付ける。書込みは禁止。テスト実測は親が行うので pytest 緑を要求しない。
予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
