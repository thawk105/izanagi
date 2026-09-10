### 所見 1: プラン記載の closure コマンドは Git 2.34.1 で必ず失敗する
- 重大度: blocker
- 型: 到達不能な受理条件
- 根拠: `s2-plan.md:197-245` は `git rev-list --stdin` の stdin に `--not` を置く。M1 の Git 2.34.1 (`measurements.md:7-16`) で同じ形を read-only 実測すると `fatal: options not supported in --stdin mode` となった。pytest は実走していない。
- 成果物影響: 記載どおりの実装では branch preview が closure 計算前に rc=2 となり、rc=0/1/3 の受理集合が空になる。
- 提案: 負 root を full oid の `^<oid>` として stdin に渡す。fake subprocess だけでなく Git 2.34.1 実体で、この反例を固定するテストを追加する。

### 所見 2: §1 配線は worktree を detach する前なので、通常の掃除対象を自分で rc=2 にする
- 重大度: blocker
- 型: 発火しない保証
- 根拠: `s2-plan.md:254-257` は候補 branch が checkout 中なら `indeterminate`、`s2-plan.md:417-420` は preview を §1 に置く。一方、detach は `.claude/commands/cleanup-branches.md:30-37` の §3 である。独立実測時点では non-main local branch 31 本中 27 本が checkout 中で、現行 `ahead=0` 20 本中 18 本が checkout 中だった。
- 成果物影響: 現行削除候補で preview 前提を満たしうるのは最大 2/20、約 10%に留まり、worktree 掃除では gate が恒常的な停止点になる。
- 提案: occupancy・clean 検査後に全候補 worktree を detachし、root を再棚卸ししてから全候補を一括 previewし、その後に expected-tip CAS 削除する。

### 所見 3: 「全 commit landed」を rc=0 条件にする設計は実データ値域を満たしていない
- 重大度: blocker
- 型: 到達不能な受理条件
- 根拠: `s2-plan.md:182-189,341-360` は全 commit の conjunction と 1 回 8 秒の上限を要求する。D922 は60秒相当で8件中4件 landed、4件 indeterminate (`docs/decisions.md:33279-33283`)。独立して現在の ahead>0 branch 10本を計画値の8秒で検査すると、landed 1本、indeterminate 9本だった。内訳は timeout 6本、`closure-has-no-introduced-state` 3本。推測: 各 closure commit をさらに全件 conjunction する受理率は、この branch-tip の1/10を上回らない。
- 成果物影響: 非空 closure に対する rc=0 は実測で約10%以下となり、可視化結果を得た正常実行まで「停止」として扱われる。
- 提案: process の完全性と内容判断を分離する。rc=0 は「完全な可視化結果を生成」、技術的な不完全だけを rc=2 とし、`landed`、`not-landed`、`indeterminate`、通知は JSON の独立 fieldで表す。少なくとも command の `rc0以外停止` はやめ、既知 rc を結果表示として処理する。

### 所見 4: D978 を外したままでは gate が非空 closure の削除経路へ結線されない
- 重大度: blocker
- 型: 既裁定との不整合
- 根拠: 現行 command は `ahead=0` と `git branch -d` のまま (`.claude/commands/cleanup-branches.md:22-36`)。`ahead=0` の tip は main から到達可能なので deletion-loss closure は空である。D978 は非祖先でも landed なら対象に入れ、expected-tip CAS と直前再検査を要求し、現状維持を明示的に却下している (`docs/decisions.md:34613-34624`)。プランは rc 非許可の注意だけを追加する (`s2-plan.md:417-420`)。
- 成果物影響: gate が checker を必要とする非祖先 branch は既存条件で削除対象外となり、運用の受理集合は変わらない。
- 提案: D978 は既に裁定済みなので「別裁定」ではなく実装対象である。この wave で CAS 削除まで配線するか、別の実装 wave を明示的な先行条件とし、それまでは本成果物を未配線の可視化 tool と呼ぶ。

### 所見 5: 台帳追記は削除後の手作業だけで、空台帳を異常として検出できない
- 重大度: blocker
- 型: 発火しない保証
- 根拠: `s2-plan.md:397-409` は削除成功後に追記し、tool 自身は編集しない。追加予定箇所は command の現 line 37 後 (`s2-plan.md:415-421`) なので、書き手は dispatcher を実行する AI と推測される。失念・中断・削除直後の障害を照合する receipt はなく、台帳テストも空台帳の rc=0 を正常系としている (`s2-plan.md:493-499`)。
- 成果物影響: 一度も追記されなければ `--ledger-only` は永久に rc=0となり、削除済み object の期限通知は一件も生成されない。
- 提案: 単なる「台帳が非空」検査は、削除履歴ゼロの正常状態を拒否するため作れない。削除前に durable な `prepared` entryを記録し、CAS 削除後に `pending` へ遷移させ、missing-ref の prepared entryを通知対象にする。これを採らないなら T-1826 は設計メモに留め、裁定へ返す。

### 所見 6: `/cleanup-branches` は期限通知の発火条件を満たす既存経路ではない
- 重大度: blocker
- 型: 発火しない保証
- 根拠: 通知は cleanup §1 の手動起動時だけ (`s2-plan.md:399-405`)。現行 command に定期起動点はない (`.claude/commands/cleanup-branches.md:9-20`)。射影資料には cleanup の実行日履歴がなく、実行間隔は推定不能。gc 窓は既定2週間で、loose object は6268/6700 (`measurements.md:7-27`)。古い loose objectでは loss 下界が assessment 時点になる設計でもある (`s2-plan.md:306-315`)。
- 成果物影響: cleanup 間隔が2週間超、または loss 下界が即時なら、最初の通知より先に object が失われうる。
- 提案: 発火間隔を実測できる既存経路へ、削除を止めない通知として接続する。該当経路を示せない現状では DW-G04 を満たさないため、T-1826 の通知実装は設計メモに留め、発火点を裁定へ返す。

### 所見 7: coded surface の列挙は妥当だが、scope 外の境界が成果物に固定されていない
- 重大度: must-fix
- 型: scope の取り残し
- 根拠: M8 は現用面を command と `tools/dev_wave_cleanup.py` に限定する (`measurements.md:117-127`)。Skill は command を全文読みそのまま実行するため、Skill 入口は覆われる (`.agents/skills/cleanup-branches/SKILL.md:10-17`)。一方、raw `git branch -d` は機械的に阻止されない。`tools/dev_wave_cleanup.py` の空 closure は main が tip を保持し続ける条件付きであり、main が検査後に移動して残存 reflog/rootも保持しない場合、D978 型非祖先削除へ拡張した場合、保持 rootを同時削除する場合には空でなくなる (`s2-plan.md:535-541`)。
- 成果物影響: command/Skill 外の削除面には新 gate が一切効かず、P1 の免除条件が将来崩れても再配線されない。
- 提案: 保証名を「cleanup dispatcher の可視化」に限定する。raw 手動削除と universal enforcement は裁定へ返す。`dev_wave_cleanup.py` には ancestry-only 契約が変わった時点で再評価する明示的な follow-up 条件を残す。

### 所見 8: tracked 台帳は監査索引としては使えるが、延命しない事実が prose にしかない
- 重大度: should-fix
- 型: その他
- 根拠: 延命しない警告は `s2-plan.md:366-370` にあるが、台帳 schema と tool JSON に機械可読な同値 field はない。SHA を tracked blobへ書いても Git の到達可能性は変わらない。`check_docs.py` は実装時の予定実行に含まれるだけで (`s2-plan.md:501-511`)、新規 docs file の予算・lint通過は未実測である。
- 成果物影響: object の保持集合は一切増えず、JSON consumer が proseを読まない場合に「記録済みだから保持済み」という誤認が残る。
- 提案: tracked file は監査索引として維持してよいが、entryと出力に固定値 `object_retention_provided: false` を持たせ、未検証の rescue refを `rescued` にしない。`check_docs.py` の通過確認までは docs 配置を受理しない。

## 総括

- blocker の数: 6
- must-fix の数: 1
- プランを実装してよいか: NO-GO
- rc=0 の実データ到達可能性についての結論: 記載どおりでは stdin の `--not` が Git 2.34.1で失敗するため branch preview の rc=0 は到達不能。そこを直しても、現行 ahead=0 候補では独立実測時点の最大候補が2/20程度で、しかも closure は空のため受理はほぼ空集合由来である。非空 closure では計画値8秒の実測が1/10 landedであり、実用的な受理条件として DW-O13 を満たしていない。