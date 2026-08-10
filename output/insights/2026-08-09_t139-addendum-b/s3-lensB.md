# 段 3 レンズ B 所見

静的読解の結論は、B は現状のままでは certified 選択・本走投入へ進めない。主因は exact-key の曖昧さ、`b03` の台帳境界、`b02` の適用先未確定である。

### B-01 exact-key が fenced code block で壊れる — [blocker]

[判定] grammar は fenced block を除外しない。予定本文をそのまま fenced block に入れると、`### b01` などが重複して解釈され、`{b01,b02,b03}` の一意な解決を保証できない。

[根拠: [addendum-a-reissue.md:57](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:57>), [addendum-a-reissue.md:58](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:58>)]  
「次の `## ` 見出しまで」「`### ` 見出しの先頭…トークン」だけを規定し、fence 内除外を規定していない。プラン自身も [s2-plan.md:19](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:19) に fenced block 内の `### b01` を含む。

[成果物影響] resolver が拒否し、B の受理集合が空になる。certified 選択、材料レポート、試行台帳の B 参照はいずれも成立しない。

[最小の直し方] 最終文書には構造見出しを一度だけ置き、field 本文の fence 内に `^## ` / `^### ` の行を置かない。grammar を A と異なる形へ変更してはならない。

### B-02 `b03` は「別台帳」のままか、a13 への実質的追加か — [blocker]

[判定] spending の合算は明示的に禁じているため、文字どおりの台帳融合とはまだ言えない。しかし、公開台帳を primary 予約 digest と同一 ordinal に必須従属させるため、a13 の利用契約を意味上拡張している。「a13 を変更しない」という断定は未証明である。

[根拠: [preregistration.md:248](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:248>)]  
core は「primary 系列と個別公表系列に**別々の累積台帳**」とする。一方、[s2-plan.md:96](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:96) は別台帳としつつ、[s2-plan.md:101](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:101)〜[s2-plan.md:102](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:102) で primary digest と ordinal の一致を必須化している。a13 は primary 側の予約を既に固定し、`k=1` 自体は自己申告で権威ではない（[addendum-a-reissue.md:925](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:925>)、[addendum-a-reissue.md:928](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-r4-env-probe/addendum-a-reissue.md:928>)。境界の採否も未確定と明記されている（[addendum-a-reissue.md:940](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:940>)）。

[成果物影響] 公開側の ordinal、FWER spending、primary 予約の権威関係が変わる。誤れば材料レポートの公開主張と両台帳の試行履歴が同じ累積族へ誤接続される。

[最小の直し方] 裁定パッケージで、`b03` の関係を「公開台帳から primary entry への read-only foreign key」と明記し、残高・entry・ordinal の累積は別 namespace であること、ledger path を呼び手が選べないことを固定する。認められないなら B で補わず新 core へ戻す。

### B-03 `b02` の「意味上の余剰」判定が粗く、適用先 gap を解消していない — [blocker]

[判定] `6 セル`、既存の Holm、familywise の語を field 本文に書くこと自体は余剰 field ではない。grammar が field key として見るのは見出しだけであり、a13 も一つの field 内に `familywise_alpha`、spending、ordinal を持つ。一方、セル identity、null、検定統計量、局所検定まで新規に選ぶのは B の権限外である。

[根拠: [preregistration.md:255](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:255>)], [s1-brief.md:28](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:28>)], [addendum-a-reissue.md:897](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:897>)]  
core は 6 セル全件を要求し、Q7 は Holm / closed testing を採用済み。a13 は `familywise_alpha` を一つの field 内に置く。対してプランは [s2-plan.md:162](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:162) で統計量・p 値・Holm 等を一括して「意味上の余剰」と扱い、[s2-plan.md:169](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:169) で未完結と認めている。

[成果物影響] `A_pub(1)=0.05` がどの p 値・family・区間へ適用されるか未定のままなら、core §16 の調整済み p 値・同時区間を材料レポートへ出せない。逆に B が統計手続きを新規定義すれば、受理集合と公表値が変わる。

[最小の直し方] 「本文の既存契約の参照・再掲」と「新しい推論規則の追加」を分離する。後者が必要なら B で埋めず、新 core と裁定へ返す。

### B-04 `b01` と `b02` の joint consistency がない — [must-fix]

[判定] `b01=1` と `b02` の domain `{0,1}` は整合するが、裁定項目は別々に提示されている。`b01` が 1 より大きくなった場合、`b02` に `k=2` 以降の値がなくなる。

[根拠: [s2-plan.md:28](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:28>)], [s2-plan.md:59](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:59>)], [s2-plan.md:206](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:206>)]  
`b01` は ordinal `2` 以降を拒否し、`b02` は domain `{0,1}` とするが、承認質問は cap と spending を別項目にしている。

[成果物影響] candidate admission、公開 spending、台帳の ordinal 集合が不整合になり、certified 選択と材料レポートの受理集合が変わる。

[最小の直し方] `K=1 ↔ domain={0,1}` を一つの joint ruling として固定する。別の K を採るなら B 内で全 `A_pub(k)` を定義する。

### B-05 §13 の否定検査 7・8 に対する時相境界が不足 — [must-fix]

[判定] 現案を「測定開始前の binding resolution failure」と読む限り、直接違反ではない。ただし、entry 不在や digest 不一致を実行後に検出した場合の扱いが明記されず、§9 の新分類や予備置換へ漏れる余地がある。

[根拠: [preregistration.md:307](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:307>)], [preregistration.md:308](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:308>)], [s2-plan.md:108](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:108>)]  
core は閉集合外 field、環境復帰の恒真化、開始後失敗の開始前 infra failure 化を kill する。プランは mismatch 時に「本走投入を拒否する」とするが、測定開始後の経路を明示していない。

[成果物影響] 開始後の失敗を予備で置換できる読みになると、試行台帳の全 attempt、certified 状態、材料レポートの失敗主張が変わる。

[最小の直し方] 「entry の解決失敗は投入前の admission deny。開始後の不一致は §9 の既存分類へだけ写し、予備置換・ordinal 解放・新 failure code を行わない」と明記する。

### B-06 `authority: none` でも実質発効に読める — [must-fix]

[判定] brief は非発効を宣言しているが、プランは normative な `reject` / `reserve` 文を先に置く構成で、未承認 B を consumer が契約として読む余地を残す。A と同じ強度の発効条件を逐語で持たせる必要がある。

[根拠: [s1-brief.md:48](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:48>)], [s2-plan.md:177](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:177>)], [addendum-a-reissue.md:37](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:37>)]  
brief は「承認する決定が canonical 台帳へ fold された後にのみ効力」とする。A は同じ発効点と自己 digest 禁止を明記している。`authority:none` 単独では十分でなく、core 自身も「拘束力がないという意味ではない」と説明する（[preregistration.md:24](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:24>)）。

[成果物影響] 未承認の `K=1`、`0.05`、公開 ledger root が投入 gate に入り、certified 選択・材料レポート・試行台帳の provenance が先取りされる。

[最小の直し方] A §0 と同じく、承認 manifest、fold commit、発効前の no-state-change、自己 digest 禁止、core triple を前置きし、未承認 B を resolver が消費してはならないと明記する。

## 親の実測の追試

読み取り専用で確認した結果、core 三つ組は正しい。

- `git cat-file -t 88d68f...` は `commit`。
- その commit の core blob を `git cat-file blob ...:path | sha256sum` した値は、`ac939af4...cd60e9` と一致。
- 現在の `HEAD=7552e322...` に対する `git merge-base --is-ancestor 88d68f... HEAD` は成功。
- commit の diff は `docs/decisions.md` に D234 を追加し、`docs/spool/FOLDED.md:525` に `D:t139-paired-prereg-gate → D234` を追加している。

したがって、この checkout における「F は D234 を fold した commit」「F は HEAD の祖先」は反証されない。ただし、これは現在の HEAD に対する事実である。

### B-07 `F が HEAD の祖先` の一般化は不可 — [must-fix]

[判定] 現在の測定結果は正しいが、将来の checkout に対する不変条件ではない。core 自身が `measurement_head` を実 checkout から導出し、毎回祖先検査する契約になっている。

[根拠: [s1-brief.md:35](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-09_t139-addendum-b/s1-brief.md:35>)], [preregistration.md:410](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:410>)], [D234:11051](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/decisions.md:11051>)]

[成果物影響] 現在の certified 値は変わらないが、snapshot の主張を将来の admission 証拠として再利用すると、非祖先 checkout を誤って受理し得る。

[最小の直し方] 「レビュー時 HEAD に対して確認」と限定し、B 本文には HEAD を pin せず、投入時の resolver に祖先検査を委ねる。

### B-08 pin 閉包の「hit 0 件 ⇒ pin なし」は一般化できない — [must-fix]

[判定] `T-139` mainrun path が `FROZEN_MANIFEST` にないことは確認できる。さらに role ledger・コード側の exact path/digest・既存 key registry も検索し、今回の mainrun path の hit は見つからなかった。しかし、`FROZEN_MANIFEST` の path hit 0 だけから「pin なし」とは結論できない。

[根拠: [test_frozen_artifacts.py:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/orchestrator/tests/test_frozen_artifacts.py:38>)], [test_frozen_artifacts.py:87](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/orchestrator/tests/test_frozen_artifacts.py:87>)], [operations.md:51](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/dev-wave/operations.md:51>)]  
manifest は 23 件の exact path 集合で、コメントも恒久的な freeze-family membership ではないとする。operations は generator source hash、role 名 key、key→canonical path、output 外 review ledger を別途検索し、「path hit 0 を pin なしと結論してはならない」と明記する（[operations.md:53](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/dev-wave/operations.md:53>)）。role ledger の key は role 閉集合である（[review_ledger.py:13](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/orchestrator/codex_roles/review_ledger.py:13>)）。

[成果物影響] 未発見の key-side pin があれば、docs 追加が凍結検査・generator provenance・review ledger を壊す。見逃しは certified 選択、材料レポート、試行台帳の受理証拠を誤らせる。

[最小の直し方] 「既知の pin 面を列挙した結果、T-139 mainrun に関する hit なし」と限定し、各面を live / golden / historical に分類した閉包表を成果物へ残す。

### B-09 `K=1` は導出値ではなく governance proposal — [nit]

[判定] プランは governance 裁定だと認めているため致命的ではないが、「exact bytes の候補が 1 本だから最小 cap」という論理は成立しない。現在の候補 identity 数と、系列全体の将来 ordinal 上限は別物である。

[根拠: [s2-plan.md:34](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:34>)], [s2-plan.md:36](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:36>)], [addendum-a-reissue.md:913](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:913>)]

[成果物影響] `K=1` を事実値として扱うと、候補 ordinal の受理集合と公開台帳の将来範囲を狭める。

[最小の直し方] `K=1` を「承認を要する提案値」とだけ記し、core や a13 からの数学的導出とは書かない。

### B-10 実装面ゼロ — [nit]

[判定] 現プランにコード・テスト・script・機械設定の要求は見つからない。validator、resolver、台帳は後続 producer wave の契約として言及されているだけである。

[根拠: [s2-plan.md:12](</work/1/SFC/tanab/dev-wave-jobs/t139-addendum-b/s2/s2-plan.md:12>)], [preregistration.md:369](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:369>)], [D234:11067](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-addendum-b/docs/decisions.md:11067>)]

[成果物影響] 現時点の実装面・受理集合への影響はない。ここで parser や validator を追加すると、直ちに本 wave の凍結境界違反になる。

[最小の直し方] 将来実装への参照を契約説明に限定し、今回の成果物を docs のみに保つ。

実走・build・pytest・その他のテストは行っていない。行ったのは文書読解と読み取り専用の Git 検査・検索だけである。

## 総括

- blocker 件数: 3 件。
- 最も重い 1 件: `b03` の primary 予約への従属が、別台帳・a13 非変更・canonical ledger 権限の境界を未解決のまま通す点。
- 親が採るべき道: B は `authority:none` の裁定パッケージに留め、exact-key の最終 bytes と joint ruling（b01/b02/b03）を固め、family/statistic gap が残るなら新 core へ戻す。