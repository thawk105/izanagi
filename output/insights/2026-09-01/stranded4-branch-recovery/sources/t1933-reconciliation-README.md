# T-1933 受入最長node短縮の2負結果を統合したreconciliation後継

- authority: none
- default_effect: no-state-change
- source tips: `209698aedc0bec681eb4f097a93da9e1d7cd9e88`, `7da26497763e53fca32301c0b9990b9fce989b42`
- reconciliation base main: `c384a90a0de357b0b4b00cddd3bbeef85576fa3e`

本書は可変状態の正本ではない。タスク状態はworklog、設計判断はdecisionsを正本とする。

## 統合結論

2本とも負結果であり、短縮達成を主張しない。現行固定argvでは、受理集合、assertion、live repository再観測、独立oracleを保ち、かつ最長nodeへ意味のある効果を持つ安全な共有境界を証明できなかった。

別案として試したT-080 process-memo groupingは、配線と変異検出には成功したが、paired full K=3中央値が244.810秒から245.707秒へ+0.897秒、+0.37%となり、D357の分類では変化なしだった。実装commit `2ffb32a0e`はremoval commit `1bafd884a`で撤去済みであり、reconciliation final treeへ再導入しない。

## 最長node waveの負結果

変更前baselineは固定4 node、固定順、`-n 0`、`--force-dispatch`で4 passed / 147.55秒だった。内訳はfloor snapshot 4.18秒、T-080 single-defect 86.57秒、draft-finalize 51.93秒、T-080 snapshot 2.61秒である。この147.55秒はserial sliceであり、acceptance全体や並列critical pathの代表値へ一般化しない。

snapshot再利用やT-080分岐前prefixには安全化の構造候補があるが、snapshot 2 nodeの全消去でも固定slice上限は6.79秒で、86.57秒nodeもscope外の全体最長140秒nodeも変えない。CoW cloneは安全境界と効果が未証明で、production履歴走査は所有外だった。optional rules、値源共有、worker/session跨ぎcache、grouping、case縮小、assertion変更は採らなかった。

## acceptance-fastest waveの負結果

default cache keyを共有する3関数/6 nodeを既存`real-repo` loadgroupへ寄せた。焦点走は実装前76.03秒、実装後75.77秒で同一worker化を確認したが、full結果は次のとおりだった。

| arm | fixed commit | run 1 | run 2 | run 3 | median |
|---|---|---:|---:|---:|---:|
| pre | `dcf9224a` | 244.810 | 241.432 | 284.232 | **244.810** |
| post | `2aa85c45` | 252.175 | 239.061 | 245.707 | **245.707** |

metricは3本のK=3 shardにおけるpytest JUnit session timeの最大値で、queue待ちは含まない。paired両armは各走exact 18,598 items、18,536 passed / 62 skipped、selected=finished、effective scheduler=`loadgroup`、赤0だった。

変異baselineはPASSED、3件すべてKILLED、SURVIVED/MISMATCH/TIMEOUTは0だった。これは`2ffb32a0e`でprocess-memo配線と独立goldenが効いた証拠であり、速度の証拠ではない。paired postは`2aa85c45`、撤去は`1bafd884a`で、3つのcommitの証明対象を混同しない。

## 共通の非主張とscope外

- duration allocator、runner変更、T-1934残差、新規測定、新規最適化は扱わない。
- skip、deselect、case縮小、assertion変更、timeout緩和で受入を短くしない。
- worker duration総和をwallまたはnode-hour短縮の代理にしない。
- 保存した旧acceptance receiptをreconciliationのfresh acceptanceへ流用しない。

## byte監査済みsource evidence

次の17本は固定source tipのblobを内容変更せず回収した。source READMEとsource worklogは同名artifact・task operationの衝突を避けるため証拠pathへ移し、decision/failureはactive spoolで原文を保つ。合成READMEとreconciliation worklogはderived artifactで、この17本には数えない。

| final path | source tip | source blob | 役割 |
|---|---|---|---|
| `sources/longest-node-README.md` | `209698aed` | `e3a6b6c6b51aa7f917eee585d71a49be31c18ba2` | longest原文README |
| `sources/acceptance-fastest-README.md` | `7da264977` | `06d5d70c7d8919ea1f92343f1403457272adf271` | fastest原文README |
| `sources/spool/2026-08-28-worktree-dev-wave-t1933-acceptance-longest-node-1.md` | `209698aed` | `0671276745c503c5edb485267537a27829c8d0d8` | longest source worklog |
| `sources/spool/2026-08-28-dev-wave-acceptance-fastest-1.md` | `7da264977` | `fcb27dfa45a00771cab8d3010ad0f683642ebc69` | fastest source worklog |
| `../../../docs/spool/failures/2026-08-28-worktree-dev-wave-t1933-acceptance-longest-node-2.md` | `209698aed` | `3c742c29f1ceeb5991002ea0a34e3f8be488b9a7` | F606再発 |
| `../../../docs/spool/decisions/2026-08-28-dev-wave-acceptance-fastest-2.md` | `7da264977` | `707753c088d85ed9c800eed7c523bbbd70f0c715` | no-effect decision |
| `verbatim/adjudication.md` | `209698aed` | `f74a9974c9e9a473dbc4739874139a80e51909c7` | longest裁定 |
| `verbatim/baseline-argv.md` | `209698aed` | `83ea6da865a87ef08720ae8f7c6bc62cda4addba` | baseline argv |
| `verbatim/brief.md` | `209698aed` | `4713c07b69ab4359ec9b3813345300c29df4f512` | longest brief |
| `verbatim/s2-plan-v2.md` | `209698aed` | `54beb8b905de2015f3808c7ac58b08b18ce31860` | longest plan |
| `verbatim/s3-correctness.md` | `209698aed` | `9ff4d125231fdfefd916bc04b5da82e28e85298e` | correctness review |
| `verbatim/s3-effectiveness.md` | `209698aed` | `941c0fc8b1f13d92c22ce637dbaf7e2a756da153` | effectiveness review |
| `paired-runs.json` | `7da264977` | `e3557adc037ad6ba681b19e5339b5e3d74a96129` | paired K=3 raw summary |
| `mutation-spec.json` | `7da264977` | `64564ca4a00adb1a048c15062e19aa9a9a38c86b` | mutation spec v1 |
| `mutation-report.json` | `7da264977` | `763ee58e6e66dde8e97a884d105a3acd93c108f8` | mutation report v4, repo head `2ffb32a0e` |
| `mutation-wrapper-receipt.json` | `7da264977` | `98342d4ac32b20e63bc5a54503f811c0c20bd89d` | wrapper receipt v1, resolved `2ffb32a0e` |
| `acceptance-receipt.json` | `7da264977` | `2c307d99688f014b60a760151e102bffe47b67c6` | 旧receipt v5, tested `dcf9224a..2aa85c45` |

repo外のworker receiptは各source handoffが指すjob directoryに残る。本後継はそれらをrepo内証拠17本へ含めたとは主張しない。
