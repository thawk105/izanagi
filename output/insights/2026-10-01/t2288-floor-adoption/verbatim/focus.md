## 対応表

| 所見番号 | closed/partial/regressed | 根拠 |
|---|---|---|
| 1 | closed | [README:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:40)、[D fragment:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/spool/decisions/2026-10-01-dev-wave-b4-floor-adopt-2.md:39)、[worklog:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/spool/worklog/2026-10-01-dev-wave-b4-floor-adopt-1.md:21) が事前無作為化を未確認と明記。spec 3本の algorithm・seed と対応する6窓の header は一致し、実行順の確認とは区別されている。 |
| 2 | closed | [README:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:43) と [D fragment:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/spool/decisions/2026-10-01-dev-wave-b4-floor-adopt-2.md:37) は記録時刻の順序に限定し、結果を見る前の選定の証明ではないと明記。 |
| 3 | partial | [README:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:56) の digest 内11件、lstat 失敗10件、そのうち材料レポート9件／resolver直接呼出し1件はログと一致。ただし、digest 外の追加記述と未確認件数に以下の問題が残る。 |

## 新規所見

1. **should — digest 外の2件とも「同じ lstat 失敗の詳細が残る」とする根拠が不足。**
   [README:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:60) のうち、`test_outputs_contain_no_combining_diacritic_codepoints` は [ログ:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:22) の見出しから [ログ:208](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:208) の例外まで確認できる。一方、`test_cli_clean_subprocess_runs_twice_and_refuses_overwrite` の名前は [ログ:244](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:244) の失敗一覧にしかない。[冒頭:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b4-floor-adopt/verbatim/focus-with-entry.log:19) は切断された出力断片と `AssertionError` で、test 名も lstat の記述も残っていない。CLI の原因は推定と明記するか、断定を支える資料が必要。

2. **should — 「25件は個別未確認」が追加記述と整合しない。**
   [README:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/output/insights/2026-10-01/t2288-floor-adoption/README.md:137) と [worklog:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-floor-adopt/docs/spool/worklog/2026-10-01-dev-wave-b4-floor-adopt-1.md:15) に旧記述が残る。digest から省略された25件には、今回原因を確認した上記 combining-diacritic test も含まれる。「digest では25件省略」と「原因を個別確認していない残り」を分け、worklog の11件も digest 内と限定する必要がある。

## 総括

**NO-GO — 所見1・2は closed、所見3は partial。**

`review.md` の正規化表は一致した。原文3514 byte／保存版3506 byte、削除空白は3・6・9行目に各2個、11行目に3個。記載どおり空白を戻して末尾改行1 byteを除くと、原文とbyte単位で一致し、SHA-256も `c4fc9b234ea280ac0022d5a45bf22f52cc65772f1ba04e42fea3735e083a3a4f` に復元できた。

静的検査のみ。テスト・書き込み・委任は行っていない。
