親の見送り裁定は8件で崩れる。うち6件は継続へ戻すべきで、2件は見送り理由の修正が必要である。これは静的資料だけの判定であり、テストは実行していない。

## 所見

### B1 / T-224

- 一次資料: T-224 は、DW-S06-A、DW-G05、`failures.md` のF9という3作業を持つ。[worklog-phase3-0801-80.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-80.md:57)
- 破綻: T-328 の所有記録が列挙するのは T-341/T-345/T-346/T-264/T-279/T-317 で、T-224 は含まれない。[worklog-phase3-0803-122.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0803-122.md:69) 現行worklogのT-328被覆一覧にもない。[worklog.md:1758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/worklog.md:1758) 特にF9追記は `docs/dev-wave/**` のbyte不足では説明できない。
- 失われるもの: 親の実測主張を敵対レンズへ渡す義務、G05の到達系列、F9の再発記録。
- 推奨: T-224を継続へ戻す。T-328へ移すなら、少なくとも3作業をT-328のscopeへ明記し、F9追記は別に完了確認すること。

### B1 / T-371

- 一次資料: 現行記録はT-371を「T-189系が所有」と再割当している。[worklog.md:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/worklog.md:85)
- 破綻: T-189の最終scopeでは許可リスト部分は完了扱いで、残作業は有効なmodel routingの比較実験だけである。非対応組の組合せ表・事前検査は含まれない。[worklog-phase3-0803-135.md:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0803-135.md:190)
- 失われるもの: model×reasoning非対応組を起動前に拒否する検査。既知の不正組合せを受付け続ける。
- 推奨: T-371を継続へ戻す。T-189のnext actionへ組合せ表を明記してから移管するならよい。

### B2 / T-256

- 一次資料: 当初の発火条件は「同族の第2例が出た時点で族として閉じる」だった。[worklog-phase3-0801-87-88.md:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-87-88.md:320)
- 破綻: 後続のbroken checkpointで、raw例外がsupervisor契約を貫通する事例が「F68型」として記録されている。[worklog-phase3-0801-99.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-99.md:38) 後続例を個別修正したことは、第2例の発生自体を取り消さない。
- 失われるもの: `_read_regular_at` を含む同族経路の例外正規化。別の到達経路でraw `OSError` が再び契約外終了しうる。
- 推奨: T-256を継続へ戻し、DW-G03どおり族閉鎖を実施する。

### B3 / T-284

- 一次資料: 元記録は重複JSON keyの非対称をP3新規項目としている。[worklog-phase3-0801-98.md:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-98.md:74) D113も「塞がない。裁定パッケージへ送る」としている。[decisions.md:5300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/decisions.md:5300)
- 破綻: 「scope外」は実施しない裁定ではない。裁定待ちへ送った項目を、裁定済みとして見送っている。
- 失われるもの: submitは重複keyを拒否する一方、jobはlast-winsで受理するproducer/consumer間の受理条件不一致。
- 推奨: T-284を継続または裁定待ちへ戻す。

### B3 / T-245

- 一次資料: 元記録自体が「取り込み済みとなった `codex/p3-autonomous-trial` の」で途切れている。[worklog-phase3-0801-86.md:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0801-86.md:54)
- 破綻: 内容を復元できないことは、実施しない裁定・未成立条件・別ID所有のどれでもない。T-207完了から、欠落した後半まで完了したとは導けない。
- 失われるもの: 欠落した残余そのもの。内容不明を理由に落とすと、回収不能になる。
- 推奨: T-245を証拠回収・内容再構成タスクとして継続へ戻す。破棄するなら、人間の明示的な破棄裁定が必要。

### B3 / T-199

- 一次資料: 元記録は、実装面の境界、brief行数、裁定反転履歴という3件の具体的なP3 backlogを保持している。[worklog-phase3-0731-73.md:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0731-73.md:168)
- 破綻: 元記録にはT-328も「外出し後」という発火条件もない。T-328のscopeにもT-199は含まれない。[worklog-phase3-0803-122.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0803-122.md:69)
- 失われるもの: 実装可能面の境界、brief長とdispatch条件の矛盾、裁定反転履歴の整理。
- 推奨: T-199を継続へ戻す。T-328後という依存関係を採るなら、一次記録へ根拠と発火条件を新設すること。

### B3 / T-326 — 文言修正

- 一次資料: 裁定は択(b)、すなわち新verifier経由だけを強化し、`layer3_report` 本体は観測として残すものだった。[worklog-phase3-0803-124.md:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0803-124.md:21)
- 破綻: 「本体強化を独立waveへ送った」と書くと、択(a)相当の将来作業が所有済みに見える。独立waveが必要なのは択(a)を採る場合であり、所有先IDもない。
- 失われるもの: 実害は作業消失より、存在しない将来waveへの誤った期待。
- 推奨: 見送りは維持してよいが、理由を「択(b)採用により本体強化は実施せず、観測のみ保持」へ直す。

### B2 / T-156 — 文言修正

- 一次資料: 本来の発火条件は、8b descriptor拡張を設計するとき、またはTPC-C級workload corpusを採るときであり、その前にworkload別分布を測ることまで定義されている。[worklog-phase3-0727-26-0728-32.md:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/archive/worklog-phase3-0727-26-0728-32.md:585)
- 破綻: 台帳の「条件成立まで保留」だけでは、何をもって再発火するか復元できない。
- 失われるもの: descriptor拡張時の再起票契機と、set-size分布を先に測る順序。
- 推奨: 見送りは維持してよいが、上記の発火条件を台帳へ明記する。

高優先の残りでは、T-328直接割当のT-345/T-346/T-317/T-341/T-279/T-264/T-282/T-359は一次記録で被覆を確認でき、T-328自体もland待ちとして残っている。T-246自身は見送り台帳にいるが、T-283/T-242はそれぞれ本番開放・正式系列という独立した未成立条件を持つため、所有鎖の消失にはならない。[worklog.md:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-task-inventory/docs/worklog.md:1776)

## 総括

1. 「見送るな」: `T-199`, `T-224`, `T-245`, `T-256`, `T-284`, `T-371`
2. 文言だけ直せば足りる: `T-156`, `T-326`
3. 検証して崩せなかった: 52件
4. 未検証: なし（0件）