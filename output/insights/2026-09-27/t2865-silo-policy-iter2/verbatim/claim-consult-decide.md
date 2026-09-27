## 決定

**(B) 止める。** iteration 3 は `eval-exception` の未評価試行として残し、iteration 2 の certified pair だけを評価済みとする。claim を退避しての再投入は行わない。

## 根拠 (file:line)

- [campaign_claim.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/campaign_claim.py:383) と [campaign_claim.py:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/campaign_claim.py:421): 同一 identity path の claim は `O_EXCL` で作る。既存ファイルがあれば所有者の死亡を判定する前に拒否する。
- [loop.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/loop.py:370) と [loop.py:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/loop.py:409): 新しい pair job は同じ campaign identity で claim 取得へ進む。D2205 の session は**一つの process 内の候補→stock**を共有する設計であり、次の job へ認可を持ち越さない（[decisions.md:70353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/decisions.md:70353)）。
- [decisions.md:69413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/decisions.md:69413) と [decisions.md:70384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/decisions.md:70384): DEAD 所有者の再取得と claim の退避は、one-shot claim を維持する今回の修復案から却下されている。D2187 が述べる「手動回収だけが裁定済み経路」（[decisions.md:69402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/decisions.md:69402)）を、**正常終了した job の後に毎回 claim を退避する反復運用**の許可とまでは読めない。A はその追加裁定なしには選べない。
- [decisions.md:19326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/decisions.md:19326): D464 の生存判定は同一 protocol の *別 path* との競合を扱う。一方、今回の拒否は既存の**同一 identity path**によるものなので、親報告どおり所有 process が終了していても解消しない。

## 実施手順

1. 親の実測を根拠に、iteration 2 の candidate certified・stock certified-stock と、iteration 3 は build 前の `ClaimError` で測定なし、という区別を記録する。iteration 3 の proposal を certified と扱わない。
2. `31899.nqsv` の再投入と claim の移動を止める。残り walltime を理由に正しさゲートや claim を迂回しない。
3. 次の修復 task に「**job 間で同じ campaign identity の one-shot claim が残るため、2 本目の pair job が通らない**」と渡す。D2205 の同 job session 修復とは別の問題として、運用方針の裁定を求める。

## 総括

親報告の job 終了を前提としても、現行コードでは次の pair job は同一 path の claim に拒否される。系列 B の確定結果は評価済み **1 iteration** と未評価 proposal までである。今回は read-only の相談のため、ファイル変更や再投入は行っていない。