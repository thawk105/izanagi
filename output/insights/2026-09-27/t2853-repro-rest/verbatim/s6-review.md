## 所見

- **M1・must-fix** — [README.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:118)、同:122、125、149–159 と [worklog fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/spool/worklog/2026-09-27-wave-t2853-repro-rest-1.md:20)。一次資料は計画稿 §1・§7 の GM1 と B-10 の `verbatim/elapse.log`。fig2b・fig6・fig11 は別系列の Elapse を当てた**試算**なのに、確認を確定した「不要」と記す。**放置時の影響:** 投入形での再見積り前に、D2212 項 4 の確認不要が確定したものとして扱われる。**修正案:** 3 図の確認欄と総括的な列挙を「暫定で不要」に戻し、投入単位の全 job を含む Elapse 見積りで投入前に判定すると明記する。

- **M2・must-fix** — [README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:24) と [worklog fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/spool/worklog/2026-09-27-wave-t2853-repro-rest-1.md:20)。一次資料は [S-1a 結果稿:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/docs/paper-story/results/2026-09-20-s1a-nine-pair-direct-comparison.md:130)。fig4 を「4.18〜9.83」と要約すると、判定に必要な floor を除いた 144 session の値 4.18 が、正典 306 session の下限に見える。本文 §3.2 の正典の試算は **8.88〜9.83**。**放置時の影響:** ユーザーに示す fig4 の所要下限を 4.70 node 時間過小に記録する。**修正案:** 結論と fragment は「正典 8.88〜9.83」とし、4.18〜4.62 は判定を再現しない標本だけの参考値として本文に限る。

- **S1・should-fix** — [README.md:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:88)。一次資料は `dev-wave-t2850-trace-concurrent-verify/glue-v3/`、`trial-v2/submit_all.py`、`jobs-trial-v2.jsonl`。この 3 箇所で保全指定を見つけなかったことから「trace は残っていない」までは導けない。**放置時の影響:** 未走査の保存先に trace がある場合、写しの完全性判断から外れる。**修正案:** 「指定した 3 箇所に trace 保全設定は見つからず、試走 v2 の保全先は特定できなかった」と、調べた範囲に限定する。

## 照合済み

- 7 manifest の `verify.ok=true`、不一致 0。組別の file・bytes は copy.log、dryrun.log、保存先 README と一致し、合計 **9,041 file・47,843,910 B**。recheck.log は 7 組・9,041 行すべて rc=0。dryrun の対象 7 組では symlink・hardlink・`.git` は各 0。
- NQSV 会計と図・Request ID の対応は一致。fig2c は **10,741 s = 2.98 node 時間**、fig8 は **2,518 s**、fig8b cohort 2 は **2,514 s**、両 cohort は **1.40 node 時間**。fig13 は本走 3 job の 65,962 s と集約 job の 16 s を分けて確認し、計 **65,978 s = 18.33 node 時間**。
- fig2c の WAL 時刻差 1,276 s は約 **36%**。B-10 の単価 **104.5〜115.6 s/variant**からの fig2b **0.70〜0.77**、fig4 正典 **8.88〜9.83**・標本だけ **4.18〜4.62** は算術上一致する。§3.3 の **39.08〜40.10**、**11.87〜11.94**、**3.39**、**2.10〜2.17** も一致する。
- 計画稿からの fig2c **1.06 → 2.98**、fig2b **0.27 → 0.70〜0.77**、fig8b の暫定値から Elapse への更新、fig13 の未判定から **18.33** への更新は、出所の区別を保っている。

## 総括

**NO-GO。** 写しと主要な会計値は照合できたが、投入前確認の判定を試算から確定している箇所と、fig4 の所要を過小に読ませる要約は、ユーザーへ見積りを渡す前に修正が必要。