### R1 「読んだ版の記録が正しい」は診断の射程より広い

重大度: **should**。README の[18行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:18)と[150行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:150)は、版の記録全般の正しさを確かめたように読める。原本 JSON の全35 run で `diag_fidelity.SEL_REG`・`SEL_COMMIT`・`REG_FUTURE` と `read_wts_mismatch` が0なのは一致する。ただし診断 patch が比べるのは保存した wts と、登録時・commit 時に読み取った wts であり、README 自身も[74〜75行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:74)で body と書き換え途中を観測できないと認めている。

推奨訂正文: 「commit した読みについて、選択時・登録時・commit 時に比較した版の wts に食い違いは観測されなかった」。§7 も同じ射程に揃える。

### R2 §9 の NQSV Elapse は指定された JSON だけでは照合できない

重大度: **nit**。README の[174〜185行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-best-config-verify/output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md:174)の Elapse は合計すると正しく **1,165秒**。ただし `evidence/*.json` にあるのは `started_at`・`ended_at` で、NQSV の request ID と Elapse の field はない。開始時刻は概ね整合するが、表の秒数を JSON 原本からは確定できない。

推奨訂正文: §9 に「Elapse の出典は job dir の NQSV 記録。`evidence/*.json` の時刻は起動器の実行時刻」と明記し、該当記録への参照を添える。

## 総括

- §3.2 の件数・割合・範囲、§4 の32行すべての commit 数・trace 行数・巡回数・判定器秒、§5 の3正例の数値は、fix 後の JSON と一致した。
- stock **32 run／異なる条件30**、正例3本、診断値の全件0、正例の帰属 **21・18・49組**も一致した。
- `SEL_COMMIT=0` から再利用なしとする論証は、wts の一意性と patch の比較位置を前提に、README が記す観測時点の範囲で成立する。帰属の数え方も起動器と一致する。
- 合否、C1 の扱い、J2 の事前投入判断は記録どおり。certified や md_11 の3秒・traceなし条件を検査済みとする記述は見つからなかった。
- **R1 の表現を直してから commit することを推奨する。** R2 は証拠の参照を明確にする改善であり、数値の不一致を示すものではない。