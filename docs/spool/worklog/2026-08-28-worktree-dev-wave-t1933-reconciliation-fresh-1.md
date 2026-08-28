---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1933-reconciliation-fresh
seq: 1
title: [T-1933] 停止branch 2本の負結果を削除履歴なしでfresh再構成した (docs-only、branch worktree-dev-wave-t1933-reconciliation-fresh、変異matrix免除)
---

## 本文

- stopped reconciliationの第一親mainは`c384a90a0`だった。fresh reconstructionはinitial main `9538fe32c`上で固定OIDから17 source blobだけを再構成し、最初の受入preflightでcurrent main `9ca1de05d`をwave-side merge `c5d1ae2bc`としてrefreshした。source tip `209698aed`と`7da264977`、旧merge、実装、撤去、停止tipはmergeせず全て非祖先のまま保った。
- source worklog 2本は同じT-1933 baseから「完了」と「更新」を競合適用するためactive fold入力にせず、原文blobのままinsightの`sources/spool/`へ保存した。longest failureとfastest decisionはtask state operationを持たないため原文のままactive spoolに残した。
- 同名README 2本は原文blobを別pathへ保存し、合成後継で両負結果を保持した。imported evidence 17本は固定source tipのblobと一致し、derived 2本を加えたfinal追加pathはexact 19本である。
- longest側の結論は「現行固定argvでは安全かつ実効的な短縮案なし」で、短縮達成を主張しない。fastest側のT-080 process-memo groupingはpaired K=3中央値244.810→245.707秒、+0.37%で変化なしと反証され、実装`2ffb32a0e`は`1bafd884a`で撤去済みである。
- source側の実装`2ffb32a0e`、撤去`1bafd884a`、旧merge2本、停止tipをfresh ancestryへ含めず、refresh mainに対するfinal code/test差分は0。duration allocator、runner、T-1934残差、skip/deselect/case縮小/assertion変更を持ち込んでいない。
- docs-onlyのためD95 authorは不要、実装面差分0のため変異matrixを免除した。fresh full acceptanceとland前検査は免除しない。
- commit前のexact manifestは19/19 pathが全て`A 100644 blob`、source evidenceは17/17が固定tip blobと一致した。`git diff --check`、`check_docs`、`check_codex_agents`、spool dry-runはgreenで、dry-runはdecisionをD1259へ割り当てる`status=planned`を返した。関連testはrequest `956948.nqsv`で737 passed / 3 skipped / 赤0。旧走の値をfresh full acceptanceへ流用せず、wave側では実foldしない。
- 最初のfresh full acceptanceはtip `c5d1ae2bc`で5 error / 18,688 passed / 62 skippedとなりreceiptを発行しなかった。同じtipの失敗file焦点再走はrequest `957073.nqsv`で20 passed / 赤0となり再現しなかったため、O18に従いfull acceptanceを同じ実装差分で1回だけ再走する。
- 一次資料は`output/insights/2026-08-28_t1933-acceptance-longest-node/`。

## 次の一手差分

### 更新

- [T-1933] **P1**: 現行固定argvでは安全かつ実効的な短縮案を証明できず、T-080 process-memo groupingもpaired K=3で+0.37%の変化なしとして撤去済み。次に再開するなら、fixed-tip full artifactのcritical workerでwallを実際に決める単体処理を先に同定し、その処理自体の安全な短縮だけを検討する。
  base: 9bbe0554008ba25e21f3643030def27979f83361e0b704685aa96986863df9db
