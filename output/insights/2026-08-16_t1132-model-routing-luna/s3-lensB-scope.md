編集・pytest・checker実走はしていません。以下は read-only 静的検算です。

### 1. 証拠ゼロで段2/5を変える根拠

- **[real（推論は refuted）]** 下流検査があるため段2/5のリスクが段6より低い、という非対称性自体は妥当です。しかし「検出されうる」は「品質が同等」の代替ではありません。D207も、弱い plan が後段の must-fix／fix 巡回を増やし、品質とコストを悪化させる経路を明記しています（`docs/decisions.md:9907-9909`）。
- **[real]** 段2/5に適用可能な品質比較証拠は依然ありません。D266は、認証済み再走があっても観測対象は段6 focused reviewだけで、段2・段3・段5の観測行はゼロと明記しています（`docs/decisions.md:12272-12286`）。したがって現 wave の production routing 変更は **NO-GO** が妥当です。
- **[refuted（部分）]** briefの「T-184/T-189がともに未着手」は不正確です。T-184は reasoning面だけ採用済みで resource/retry が残り（`docs/phase3.md:1069-1086`）、T-189の比較実験設計が未完了です（`docs/phase3.md:1191-1195`）。正しい表現は「段2/5の品質同等性を示す証拠がない」です。

### 2. D241/D243/D266 と supersede

| 案 | 実際に衝突する決定 |
|---|---|
| modelだけ段2/5を luna 化 | D241の「段2/5/6は sol」（`docs/decisions.md:11245-11247`） |
| planの `high→max` まで実施 | 上記に加え、D243（`docs/decisions.md:11311-11321`）とD266（`docs/decisions.md:12261-12270`） |

- **[real]** 段2プランは「D241/D243/D266の値を覆す」と書いています（`s2/output.md:21`）。ただし model-only 案ではD243/D266の effort値は変わらず、D241だけが直接衝突します。三つすべてを覆すのは `high→max` も含む案に限られます。
- **[real]** 「段4で supersede を記録する」は手続き違反です。段4ができるのは real/refuted と scope を裁定し、scope外の実装案をユーザー向け裁定パッケージへ返すことまでです（`docs/dev-wave/core.md:72-76`）。D243も、例外の採用根拠を人間の明示裁定としています（`docs/decisions.md:11316-11321`）。段4は「supersede候補」として返し、ユーザー承認後にのみ後継決定を記録すべきです。

### 3. 「luna max」の解釈

- **[refuted]** 2026-08-08の `luna@max` は段3のモデル指定でした（`output/insights/2026-08-08_t182-luna-stage3-hybrid.md:18-26`）。段3は元々 `max` なので、これを段5/6にも自動適用する根拠にはなりません。D241は reasoning/sandboxを変更しないとしています（`docs/decisions.md:11245-11247`）。
- **[real]** 品質リスクを最小化する順序は、既存 effortを保った model-only swap です。段2は現状 `max`、段5/6は `high` のままにすれば変更変数が一つで、D243/D266とも衝突しません。
- **[real]** `workers.md` の段5を `max` に書き換えるだけでは、実際の段5/fix effortは束縛されません。`dev_wave_codex.py` は非 review/focus の `--reasoning` を callerから受け取り、そのまま渡しています（`tools/dev_wave_codex.py:167-175`, `:233-234`; `tools/codex_worker_launch.py:1877-1896`）。したがって段5を本当に `luna@max` にするなら、planが認める通り authority・receipt・検査まで追加変更が必要です（`s2/output.md:70-77`）。

### 4. flip trick と近道

- **[real（snapshotとして）]** プラン内の一覧は `(sol)` 72件＋`(luna)` 71件で143箇所、ユニーク126ファイルです（`s2/output.md:117`, `:123-248`）。ただし現在のjob treeには今回の `s3a/run.sh:5` と `s3b/run.sh:5` が追加されており、現時点の同条件grepは145箇所・128ファイルです。143は当時のスナップショット値です。
- **[real]** flipの危険性という結論は妥当です。parserは位置で `sol/luna/other` を抽出し（`tools/dev_waves/launch_authority.py:31-35`）、laneからモデルを選ぶため（`tools/dev_waves/launch_authority.py:426-433`）、flipすると `--lane sol` が実際には lunaになります。job ID・lane・receiptの帰属名は元のlaneを保持します（`tools/dev_wave_codex.py:206-214`, `tools/codex_worker_launch.py:1722-1727`）。
- **[refuted]** briefのI2をruntime invariantと呼ぶのは強すぎます。現行runtimeは `other == consult_sol` しか拒否せず（`tools/dev_waves/launch_authority.py:396-397`）、consult両laneの相違は主に正例testで確認されています（`orchestrator/tests/test_dev_wave_launch_authority.py:98-105`）。
- **[real]** flip以外の有効なdocs一行近道はありません。自然な4値行は現行regex/checkerで解釈不能・拒否され、worker docsだけの `high→max` は実引数を変えません（`tools/check_docs.py:264-267`, `:3877-3898`）。decision本文だけを変えてもruntimeは変わりません。raw `codex exec -m luna` はDW-O01・receipt契約の迂回です。

### 5. 今回の依頼とD241

- **[real（新規性あり）]** 段2/5だけを対象にする点は、段3全置換だったD241と完全同一ではありません。下流検査によるリスク差を問う新しい質問として提示すること自体は可能です。
- **[real]** ただしD241は結果として段2/5/6を明示的にsolへ固定しています（`docs/decisions.md:11245-11258`）。よって今回の変更は「D241の論理を適用するだけ」ではなく、D241の段2/5部分を再開・supersedeする提案です。現在の条件文だけで自動的に権限が生じるわけではありません。

## 総括

- **NO-GO（現 wave）**: 下流検査は品質同等性の証拠ではなく、段2/5の適用可能な比較証拠はない。  
- **real**: P2の核心は正しいが、T-184は部分完了、T-189のみ未完了。  
- **real**: model変更はD241、effort変更まで行えばD243/D266とも衝突し、明示的ユーザー裁定が必要。  
- 条件付きGOなら、まず既存effortを保つ model-only swapに限定するのが最保守的。  
- flipは意味逆転のfootgunであり、143件という数は現時点では145件へ更新が必要。