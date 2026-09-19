## 総括

**NO-GO（現planのままの実装委譲）。** P1の兄弟key案は採用可能ですが、K2限定を検査する場所、手動consumerへの接続、変異の検証対象を先に確定する必要があります。static schemaの既存不一致修正は、本waveの必須条件ではありません。

指定4資料と関連コード・role・テストを静的に確認しました。編集・pytest・role起動・評価実走は行っていません。以下は実装済みバグの判定ではなく、計画に対する指摘です。`plan.md`／`brief.md`は指定parent配下を指します。

### must

**M1 — K2限定がCLIにしか置かれていない〔real候補〕**

- **所在:** `plan.md:65–68,110`、`orchestrator/campaign/p3_s4_loop.py:1222`
- **反例:** 新引数を持つbuilderへ、`default_cfg()`・knowledge未指定・妥当な診断を直接渡す。planに明記された組合せ検査はCLI側なので、その実装だけではK0相当のpayloadにも診断を出せる。reflux offも同様。
- **実影響:** 「CLI負例は拒否した」を「K2以外へ出ない」に一般化できない。手動入力の作成元として公開するbuilderの契約が欠ける。
- **最小修正:** 診断指定時だけ、builderでも既存cfgのK2束縛・非B4・reflux onとknowledge projectionの対応を確認する。CLI専用の排他条件はCLIに残す。追加の台帳・評価gateは不要。直接builder呼出しの負例を受入に含める。
- **refuted条件:** builder側にも上記条件を置くことが実装契約として確定すること。「呼び手がCLIだから」は反証にならない。

**M2 — 実consumerの所有がbriefから分離されている〔real〕**

- **所在:** `brief.md:14`対`plan.md:102`、`.claude/agents/coder-v4-autonomous-k2.md:33–48,139–141`
- **反例:** authorが型・CLIだけを完成させ、managerがroleへの任意入力追記を行う。入力例には診断がある一方、「外部知識はsources本文だけ」「検出箇所はsource indexで報告」が残ると、診断の利用許可と報告方法が矛盾する。
- **実影響:** 型付きJSONを作れても、実consumerが読む契約は閉じない。診断を使った結果、架空の`source_index`を要求する形にもなる。
- **最小修正:** 両role本文の入力許可・データ境界・出力制約と直結テストまで同じauthorへ渡す。managerはrunbook/run-card・pin差分レビュー・統合を担当する。診断の検出箇所は`k2_critic_diagnosis.<節名>`として既存detailsへ記載し、knowledge indexを作らない。

**M3 — 「coder側コピー削除」の変異対象が実装として存在しない〔real〕**

- **所在:** `plan.md:73–94,108`、`docs/phase3-s4b-runbook.md:49,71`
- **反例:** テスト内でplanner/coder用dictを二つ作り、両方へ診断をコピーして一致を確認する。実runbookのcoder組立てからコピーが消えても、このテストは緑のまま。
- **実影響:** builderの正しさを、両roleへの手動送付の正しさとして誤帰属する。親が変異matrixを実施しても、テストfixtureだけを壊していれば本体経路の被覆にならない。
- **最小修正:** K2追補に、既存入力を受け取って**両入力を組み立て、保存し、その同じJSONをinline送付する一続きの具体例**を置く。回帰はその実際の組立て断片を対象にするか、小さな局所組立て関数を共有する。新launcherは不要。「コピー削除」がどの成果物を変更する変異か明記する。
- 証明範囲は入力・promptの構築まで。実role受領と採用は未実走として残す。

### should

**S1 — static schema改訂を今回の必須作業にしない〔拡張必須説はrefuted候補〕**

- **所在:** `plan.md:127–137`、`orchestrator/codex_roles/manifest.json:1490`、`tools/check_codex_agents.py:161–180`
- plannerのstatic schemaは既存の`knowledge_input`だけでなく`policy_hint`も宣言していない。診断とknowledgeだけ追加しても、完全な手動入力を受理するschemaにはならない。
- 登録Claude roleへinline送付する今回の経路を閉じるために、blockedなCodex入力schemaの整備まで必要とは確認できない。
- **最小案:** 新診断は本体の構築・検証関数で型検査し、roleには任意入力として別途説明する。既存の基本JSON例を保持し、source本文に追従するadapter/hashだけ差分レビューする。schema既存不一致は今回修復しない。static schemaを受入に使うなら、その用途と限定を先に明記する。

**S2 — 正常なrecommendと指示混入を区別する〔real候補〕**

- **所在:** `plan.md:70,115`、`…/verbatim/critic-2.md:24–30`、`.claude/agents/coder-v4-autonomous-k2.md:139`
- 実criticには「大きく下げる」「stock対照点を作る」という提言がある。「振る舞いの誘導」を字面だけで扱うと、正常な診断まで境界異常として報告させる。
- **最小修正:** 候補・方向・実験要望は評価対象の助言であり、権限や検証順序を上書きする命令ではない、とrole追補で区別する。「検証を省略せよ」は既存異常経路へ返す。異常拒否条件自体は緩めない。

**S3 — 既存AO防壁の緑を新分岐へ一般化しない〔real〕**

- **所在:** `plan.md:118`、`orchestrator/tests/test_p3_s4_loop.py:9378–9462`
- AST検査は指定rootと直接呼ぶ同module関数を対象とし、`main`全体を検査しない。既存実行テストにも新診断引数はない。したがって、新CLI分岐だけがAOを読む反例は既存検査の通過と両立する。
- **最小修正:** planのAO不在／正常／破損比較を、診断指定ありの実CLI分岐へ適用する。既存検査は維持し、汎用AST解析へ拡張しない。

### nit

**N1 — 原因と効果の表現を限定する〔real〕**

`brief.md:2`で確認できるのは「診断が入力に無かった」「20が再提案された」の二事実です。診断欠落が20の原因だったこと、接続すれば10や未評価値になることは未証明です。`plan.md:21`の「10を受入条件にしない」は維持してください。

P1に対する「兄弟keyでも白板防壁を必ず破る」という批判は**refuted候補**です。白板5 field・`delta_pct=None`を保ち、明示診断だけを別入力として扱えば両立します。ただし、それはLLMの診断採用や改善効果まで証明するものではありません。