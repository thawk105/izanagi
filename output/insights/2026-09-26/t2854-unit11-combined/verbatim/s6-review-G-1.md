## 対応表

| 記録レビューの所見 | 判定 | 再レビューの根拠 |
|---|---|---|
| **must-fix:** Codex 子の合計誤り | **closed** | [insight:129–130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:129) と [worklog:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:15) は集計対象を明記した。一次 receipt の `actuals` を再合算すると、**9 本で 136 calls・1,735.253981586 秒**、記録レビューを除く **8 本で 116 calls・1,546.093949975 秒**。記載の丸め値と一致する。 |
| **should:** worklog 更新本文から旧事実が脱落 | **partial** | 単位 1〜5、存在履歴、各証拠 path、[T-156]・[T-2855]、計算の確認線は [新本文:25–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:25) に戻った。ただし [旧本文:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/archive/worklog-phase3-0923-1852.md:653) の「C 単独の pin 前進は [T-2858] で承認済み（D2227 項 1）」が残っていない。 |
| **should:** F109 の恒久対応を言い過ぎ | **closed** | [failures:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/failures/2026-09-26-dev-wave-t2854-unit11-combined-3.md:13) は実測の 21 組を転記したことと、artifact を直接入力する対策が未実施であることを区別した。[selftest.py:215–244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:215) も転記した組から合成 row を作っている。 |
| **nit:** trace 容量の単位 | **closed** | [insight:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:70) は **39,437,099 byte ≈ 38 MiB** と記す。保持された 8 file の実サイズ合計は **39,437,099 byte = 37.610148 MiB**。`kept-traces-sha256.txt` の 8 件は実ファイルとすべて一致した。 |

## 旧本文と新本文、回帰

[旧本文:633–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/archive/worklog-phase3-0923-1852.md:633) と [新本文:25–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:25) を行ごとに照合した。単位 1・2 の各 6 変異と公開 branch、単位 3 の 6 変異・mocc 存在違反 0 と認定の留保、単位 4・5 の実装と拒否条件、trace 保持先、段 2 への存在契約の留保、[T-156]・[T-2855]、2 node 時間の確認線は保持されている。新しい単位 11 の branch、C2′、結合確認、4 変異、D297 拒否、非認定の記述も [insight:14–18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:14) と一致する。これらへの脱落・不一致の攻撃は**不成立**。

新しい所見は次の 2 件。

- **should — 旧承認の事実を復元する。** 上表のとおり、C 単独の pin 前進に関する既承認が新本文から落ちた。C2′ の承認待ちとの区別を残す必要がある。
- **should — 4 択の総括を修正する。** [worklog:50–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:50) は択 4「当面は何もしない」を挙げた直後に「いずれも既裁定の変更か作り直しを要する」とする。しかし [insight:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:107) は択 4 に必要な既裁定変更を「なし」と明記する。これは更新で生じた回帰。C2′を pin に入れる場合に限定した文へ直せる。

新たな **must-fix** と **nit** はない。

## 判定

**NO-GO（記録の受理）。** 数値と元の must-fix は修正済みだが、worklog の旧承認の脱落と 4 択の矛盾が残る。

## 総括

一次資料の再集計は **9 receipt＝136 calls・1,735.254 秒、記録レビューを除く 8 receipt＝116 calls・1,546.094 秒、trace 8 file＝39,437,099 byte**。記録の数値修正は正しい。残る修正対象は worklog の 2 箇所。