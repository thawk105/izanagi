### B-1 委任先の完全会計は、この移行の最小要件ではない

**重大度: must-fix**

**根拠:** 依頼は「何が記録されたかを読んで受理規則を明文化する」ことを要求しているが、委任を許可することまでは要求していない。brief が追加した「委任先も会計して accepted」は、L5 の実在欠陥への対処方法を P1 に固定している。L5 は検査の失敗ではなく、子を観測対象に入れないことによる素通りである。

| 案 | 差分・consumer の負担 | 依頼との整合 |
|---|---|---|
| P1：委任を許して会計 | plan 見積り700〜1,100行。V6、親子関係、usage、sealed evidence 再検証、ledger と各テスト | 満たし得るが、孫・終了競合・guard は未確定 |
| P1′：禁止を指示し、証跡で検出して拒否 | plan 見積り180〜320行。launcher と再検証・回帰中心。子会計用field・ledger拡張は不要 | ultra を維持し、未会計の委任を受理しない最小候補 |
| P1″：権威段だけ max | 値変更は小さいが、新たな段別規則になる | 全段 ultra の裁定と非同値。max が委任しない証拠もない |
| prompt だけで禁止 | 数行 | 検査の素通りが残り、実測欠陥を修復しない |

**放置時の成果物影響:** model・effort 移行の完了条件に未裁定の委任会計機構が入り、受領証とledgerの変更が本体を支配する。

**推奨:** P1′を段4で採用する。禁止文だけで閉じず、root の委任操作を実証拠から検出して拒否し、sealed evidence 再検証でも同じ規則を適用する。観測済み `collab_tool_call` は早期拒否の入口に使えるが、「これが無いから委任なし」とは断定しない。root rollout の委任呼出しも検査する。

新しい拒否理由を既存の閉じたreason集合へ追加するなら、旧readerとの互換性を確認する。「fieldを増やさないからschema検討不要」でもない。拒否までに消費した子tokenを完全会計したとは報告しない。また、事後拒否は委任先の書込みを防ぐ機構ではない。

### B-2 拒否案の浪費頻度は、3 probeからは推定できない

**重大度: should**

**根拠:** `nodeleg_probe.sh`・`maxthr1_probe.sh`・`maxdep0_probe.sh` はすべて「子をちょうど1つ起動せよ」と明示している。3/3のSPAWNEDは設定による禁止の不成立を示すが、通常作業や禁止prompt下での委任率を示さない。逆にL1は委任禁止の短いPONG依頼を完了しているが、これも研究作業の代表標本ではない。

`token-summary.txt` の委任あり完了probeは、root＋子で57,667、57,675、58,242、149,544 token。これは**早期拒否時の費用実測ではない**。

**放置時の成果物影響:** 根拠のない高い拒否率を理由にP1を選ぶ、または拒否費用をゼロとして週枠を過小見積りする。

**推奨:** 禁止prompt下の委任確率を未知の `p` として扱う。9起動なら期待拒否数は `9p`。感度例はp=10%で0.9件、p=50%で4.5件であり、推定値ではない。完了probeの単価を仮置きすると、それぞれ約5.2〜13.5万、26〜67万tokenが不受理attemptに費やされる。実waveの初回結果で更新し、黙った再試行やeffort低下は行わない。

### B-3 削る対象は例示値と汎用会計機構であり、権威pinの追随ではない

**重大度: should**

**根拠:** D2229決定2は権威literalとその独立期待値の更新を要求し、決定5は例示値・過去記録の更新を禁じている。したがって、期待値変更を一括して「意味がない」とするのも誤りである。

- **残す:** 現行docsを検査するmodel・effort期待値、負例生成の置換元、Codexだけのultra語彙追加。古い値のままなら移行後docsを誤って拒否する。
- **変えない:** V1/V2の過去形式fixture、合成workersの意図的なmedium/high/low、`test_s8b`の例示、過去受領証・worklog、実験道具・role adapter・Claude effort。planのこの判断は妥当。
- **縮める:** `test_dev_wave_codex.py:99–101` のmaxをすべてultraへ付け替える必要はない。任意値転送の既存例を残し、ultraの転送正例を必要最小限追加する。
- **P1′なら削除:** V6の委任数・親子field、ledgerの子孫会計、全sessions探索cache、子のusage合成。委任を受理しない契約では成果物への必要性を示せない。
- **追加しない:** digest固定値テスト、daemon停止用の新機構、`REASONING_XHIGH_*`の改名。digest影響の確認と既存運用で足りる。

**放置時の成果物影響:** 検査対象の意味を変えずにfixture ID・保守箇所だけが増え、実在する移行不整合の確認が薄まる。

**推奨:** 5節の旧medium拒否は小さいparametrizeでまとめる。DW-G03の独立2例は局所的なL5修復の前提ではないが、L5一例から任意深度の汎用委任frameworkへ広げる根拠にもならない。

### B-4 planは値の漏れを補ったが、完了証拠の一覧が不足している

**重大度: must-fix**

**根拠:** `.claude/commands/rulings.md:58` はeffortを渡さず、`tools/dev_wave_codex.py:214–218` はplan/consultの明示指定を必須としている。brief P2の「DW-S03へ自動追随」は誤りで、planの訂正が必要である。next-tasksの既定ultra・model明示もplanには入っており、ここは「planの漏れ」ではない。

一方、planには次の完了証拠を一組として残す契約が足りない。

- L1のサブスク認証・rc・header・実所要への参照。
- 改訂docsから導出した起動器実走の `recorded_model`・`recorded_effort`・`outcome`。
- 委任のmodel/effort/cwd、call上限、sandbox、guardについて、確認済みと未確認の区別。
- next-tasks実走のmodel/effort・rc・所要と1800秒との比較。
- root／子／拒否attemptを区別したtoken実測、およびD2229決定4型の切替時点。

**放置時の成果物影響:** dev-waveだけ成功してrulingsが引数不足で停止する、またはnext-tasksの疎通・週枠記録なしで移行完了と報告する。

**推奨:** rulingsに `--reasoning ultra` とDW-S03参照を足す。外部scriptは原本退避・author成果物の設置・差分記録を維持する。本段では外部script現物は参照範囲外なので、行番号と変更量はplan依拠である。上記証拠は既存fragmentへ記録し、新しい台帳は作らない。

### B-5 「受理集合が変わるから全9段必須」は規則の読み過ぎ

**重大度: should**

**根拠:** `docs/dev-wave/core.md:9–13` のDW-C00は受理集合変更時の独立敵対検証を要求するが、全9段はユーザー明示時としている。briefの括弧内理由だけでは全9段を導けない。ただし本waveはultra語彙と委任受理規則を変えるため、軽量版の無検証移行にも該当しない。

| 要素 | このwaveでの判定 |
|---|---|
| 独立敵対検証 | 省けない。設計択一・受理集合変更がある |
| 段6レビュー | 実装waveのDW-S06-Aに従い2本を残す |
| author 2単位 | 必須ではない。P1′なら一単位へ統合可能 |
| fix・focus | 所見とfixが発生した場合に実施。空の儀式的起動は不要 |
| 変異matrix | 実装差分ゼロではないので免除不可 |
| 受入全走 | 縮小受入をlandが再検証する条件なしには免除不可 |

**放置時の成果物影響:** 必須でない分割・起動で週枠を消費する一方、「小変更」を理由に必須の受入を落とす可能性がある。

**推奨:** P1′なら一人のauthorへ値変更と局所拒否を集約する。二単位を保つ場合は共有するlauncherテストの所有を一方へ固定する。変異は新pin・ultra受理・委任拒否・sealed再検証に絞る。本consultの「テスト禁止」は守るが、後段の受入免除を意味しない。

### B-6 L6〜L8は観測した面へ限定して書き直す

**重大度: must-fix**

**根拠:**

- **L6:** 「このCLI・起動経路・明示spawn依頼で試した3設定は止めなかった」まで。「設定では委任を止められない」一般には拡張できない。
- **L7:** deleg1のroot・子による指定pathへのtouch拒否は直接証拠。TUIの観測も合わせて、全起動経路・全path・孫の権限が親以下だとは証明していない。
- **L8:** rootでのguard拒否は子のguard証明ではない。子の拒否記録0件は、guard無効も有効も示さない。受動観測の予定も完了証拠ではない。
- **追加実測:** root stdoutがroot単独、fork-allでtoken_countが複製されなかったことは測定した例について有効。ただしresponse_itemは複製されるため、P1のspawn探索は継承履歴を新規spawnと誤認し得る。孫は未実測、788fileは件数であってscan所要ではない。

**放置時の成果物影響:** 未検証のguard・子孫会計を「保証済み」とする受領証や決定記録が残る。

**推奨:** 各主張へprobe・path・深さ・実行面を添え、未測定を保持する。子guardを未確認のままP1の安全性完了を宣言しない。P1′でも拒否はsandbox保証を代替しない。これはfailuresの **[捏造/幻覚]・[権限逸脱]・[テスト代表性]** に対応する論点である。

### B-7 週枠はtoken実測と残量を分ける

**重大度: should**

**根拠:** token-summaryの9起動への単純外挿は、PONG相当で127,719、委任probe相当で519,003〜1,345,896 raw token。研究作業の予測区間ではなく、cached分を含み週枠換算率も不明。
**放置時の成果物影響:** `docs/failures.md:28585` F1050と`docs/archive/worklog-phase3-0926-1866.md:7`のように、429から系列欠測・6比較判定不能へ波及し得るが、前例はClaudeでCodexと同一枠とは示されていない。
**推奨:** wave実測へroot・子・拒否分と利用可能な週枠情報を併記し、tokenだけから「あと何wave可能」と断定しない。新しい予算frameworkは不要。

## 推奨する最小 plan

**P1′を採用し、astra・ultraを維持する。** 委任を許すことを完了条件から外し、「委任証拠のあるattemptを受理しない」と明文化する。以下は追加・削除合計の概算で、実装済みの値ではない。

| 単位 | 変更file | 行数見積り |
|---|---|---:|
| Codex author 1単位：値の移行 | `tools/check_docs.py`、`tools/dev_waves/effort_levels.py`、対応する`test_check_docs.py`・`test_dev_wave_launch_authority.py`・`test_effort_levels.py`・`test_dev_wave_codex.py` | 100〜180 |
| 同単位：委任検出・拒否 | `tools/codex_worker_launch.py`、`orchestrator/tests/test_codex_worker_launch.py`。live検査・sealed再検証・拒否理由互換性を含む | 180〜320 |
| 同単位：外部script改訂原稿 | worktree内の未commit一時file。親が`/work/1/SFC/tanab/scripts/next_tasks_consult.sh`へ設置 | 差分4〜8 |
| 親：規範と記録 | `docs/dev-wave/operations.md`・`workers.md`、`.claude/commands/rulings.md`、既存形式のdecisions/worklog fragment | 規範12〜18、記録30〜60 |

合計約326〜586行。P1のV6・ledger・子孫探索は含めない。拒否検出の完全性やschema互換性がこの範囲で閉じなければ、受理規則を緩めず段4へ返す。

## 総括

**推奨はP1′。P1は実在欠陥への対処として成立するが、今回の移行には大きすぎる。** prompt禁止だけでは小さすぎ、権威段maxは既裁定と非同値である。rulingsの明示effort、next-tasks疎通、週枠実測、guardの未確認表示は削れない。

静的検査のみ実施。ファイル変更・テスト・CLI実走・子エージェント起動は行っていない。