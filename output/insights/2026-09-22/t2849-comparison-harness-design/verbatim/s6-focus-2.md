## 閉鎖表

対象は `0e56356bdce07c80b0ce88fa21bb8ec014f4b0c8`。指定差分と一次資料を静的に照合した。書込み・テスト・計算投入は行っていない。

以下、設計＝`output/insights/2026-09-22/t2849-comparison-harness-design/README.md`、決定片＝`docs/spool/decisions/2026-09-22-dev-wave-t2849-comparison-harness-design-2.md`、作業片＝`docs/spool/worklog/2026-09-22-dev-wave-t2849-comparison-harness-design-1.md`、B5＝`docs/b5-generator-contrast-preregistration.md`。コードの短縮名は `orchestrator/campaign/` 配下。

| ID | 判定 | 根拠 |
|---|---|---|
| F1 | closed | planner情報のない拒否をwhiteboardへ入れる案を撤回し、兄弟keyの拒否列をa・固定分類だけに限定した。架空のdirection / magnitudeが不要になった（設計:153–154,356；決定片:14；作業片:18,30；`p3_s4_loop.py:1420–1439`）。継承照合の表現にはG1の明確化余地がある。 |
| F2 | closed | 初期点・探索の機械故障上限超え／未解決を、endpointの有無によらない系列終了・score欠測と明記した。品質欠測との区別も一致する（設計:195–201,235；決定片:15；作業片:18；`b5_generator_contrast.py:810–821`；B5:143–144）。 |
| F3 | closed | 直接識別子の出現を定義・registry登録に限定し、間接利用とdriverの有無を未確認とした。検索でも対象は同じ2出現だった（設計:335；作業片:18；`genome.py:124,211,217–220`）。 |
| F4 | closed | `CURRENT_PIN`の7桁prefixと完全SHAを区別した。両定数およびHEADの`external/ccbench` gitlinkとの対応を確認した（設計:318；作業片:19；`pin.py:31`；`s8b_approved.py:67`）。 |

## 新規所見

**G1・should・対象：継承照合を「B-5のまま」とする範囲**

- **確認済み：** 設計:153はwhiteboard行の文脈だが、設計:356・決定片:14・作業片:18では「whiteboardと継承照合はB-5のまま」と広く書かれている。一方、設計:155はcurrent_perfの選択対象へ初期点を追加する。既存の継承照合はwhiteboardだけでなくcurrent_perf / baselineも照合し、その期待値はstock-startとevaluation-resultだけから作る（`b5_generator_contrast.py:462–484`）。
- **解釈：** 「不変」はwhiteboardの照合規則を指すと読めば設計は成立する。ただし、照合関数全体を変更不要と読む余地が残る。未実装なので、実際の不具合は確認していない。
- **放置した場合の影響：** 関数全体をそのまま再利用すると、初期点を反映したcurrent_perf / baselineが不一致となり、LLM系列が探索前に終了しうる。
- **修正案：** 「whiteboardの5 field・iteration=b・その継承照合は不変。current_perf / baselineの期待値には初期点を加える」と§11・決定片・作業片にも明記する。新しいgateや検査の追加は不要。

## 反証済み

- **whiteboardの事実記述は一致する。** `evaluation-result`だけを並べ、iteration=bを要求し、certifiedならsuccess、それ以外はfailとなる（設計:91,153；`b5_generator_contrast.py:451–461,796–807`）。
- **certified・品質欠測でもwhiteboardはsuccessとなる。** これはB-5の既存挙動であり、正常fitnessやendpoint資格を与える意味ではない（設計:68,153,194；`b5_generator_contrast.py:440–444,799`）。
- **投入前の拒否eventの所在は正しい。** handshake拒否、proposal読取り・schema等の不合格、slot未投入の各経路に`proposal-rejected`がある（設計:154；`b5_generator_contrast.py:750–752,782–785,806–807`）。
- **兄弟keyに新たな外部情報源はない。** 初期点列のvは共通初期点そのもの、拒否列は自系列のaと固定分類だけで、拒否候補の値・自由文・他系列の観測は入れない設計である。機械的遮断の証明ともしていない（設計:154,163–165,183–184）。
- **公平性と正しさゲートは維持される。** 消費fieldの違いを含む構成比較という限定、全armのA上限、Tier0前後のA/B区別、anomaly即rejectは訂正で変わっていない（設計:39,45,74–76,145,210–211,226–235；B5:109–118）。
- **F2の反例は解消した。** 正常な初期点があっても後続slotの機械故障上限超えで系列欠測となり、初期点を再計測して正常scoreへ戻す読み方は排除された（設計:197,235；`b5_generator_contrast.py:810–816`）。
- **R3・R4・R5・R7の閉鎖を壊す差分はない。** 局所探索と失敗点再提出、参照genomeの入口、K0/K2のcoder契約差、項番号と節番号の区別・非LLM四手法の記述は維持される（設計:60,82,103,124,130,145,175–177,357；決定片:14–15,24）。
- **三文書の主要な訂正は同期している。** §12の旧案は経緯として残り、直後に撤回が明記されている。現行仕様との矛盾ではない（設計:371–372；決定片:14–15；作業片:17–18,30）。
- **scopeの拡張は見られない。** 兄弟keyは既存記録の入力射影として位置づけられ、汎用台帳・新しいgate・一般化の追加にはなっていない（設計:147–154,351–357；決定片:13；作業片:29–31）。

## 総括

**GO。must-fix 0件、should 1件（G1）。**
F1〜F4はすべてclosed。今回の訂正による必須修正相当の退行は認めない。