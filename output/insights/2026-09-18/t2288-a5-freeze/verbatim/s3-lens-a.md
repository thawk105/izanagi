**条件付きで採用可です。A-5 の授権不足は認めません。ただし、親追記の「48 h の隙間と timeout から終了→開始の分離が従う」は成立しません。** plan が訂正した brief の過大主張を復活させず、後続の実行 HEAD の制約と D2088 の記録先訂正を明記してください。

指定資料の静的検査のみ実施しました。plan の JSON 3 本について、seed・直列化後の bytes 数・SHA-256 は再計算して掲載値と一致しました。binder・測定・finalize は実行していません。

以下、`F` は指定 worktree の `orchestrator/campaign/floor_pair_driver.py`、`P` は `s2-plan.out.md`、`B` は `s1-brief.md` を指します。

1. **［情報］授権は十分。ただし既決の対象・統計を変更する授権とは区別する。**

   D2120 項 4 は、窓日時・campaign・seed・出力 path・集約対応を列挙して「AI が確定し、凍結 commit へ進む」と明記しています。§11.1 の無裁定既定値禁止にも「委任の下での確定はそれに当たらない」と直接回答しています。A-5 を再びユーザー承認待ちに戻す必要はありません。

   P1〜P8 は、plan の限定を伴えば既決の具体化・運用選択に収まります。追加 workload、別 contention セル、pair 別欠測閾値、統計関数変更、正常 summary だけへの間引きは含まれていません。120/30 秒等は「D2120 がその数値を指定した」とせず、今回の AI 選択として記録する扱いが適切です。

   D1638 原文は射影に無いため独立照合していません。上記結論は D2120 項 4 の直接の授権と D1641 決定 1〜3 によります。

2. **［must-fix］48 h 案でも、21.5 分を session wall time の上限とはできない。**

   親の式 `120 × 10 + 30 × 3 = 1290 秒` は、指定 timeout の合計です。session 全体の deadline ではありません。

   - `started_at` の取得と窓判定の**後**に、binary の解決・hash・trace symbol 検査があります。この区間を上式は含みません（F:2091、F:2111）。
   - `timeout_s` は `runner.measure_point` に渡されますが、driver 自身は呼出し全体を deadline で囲んでいません（F:1590）。
   - 通常の probe は `subprocess.run(timeout=...)` ですが、session 全体への制限ではありません。`run_window` は `probe_fn` を受け取り、`_probe_once` は timeout 値を渡すだけです（F:1622、F:1730、F:2205）。
   - **反例としての推測:** 開始記録後の filesystem 停滞、process の長時間停止などにより、各 subprocess の timeout 合計を超える wall time が生じ得ます。

   `measure_point` 内の records load が timeout 内か、起動・終了処理まで何秒で収まるかは、射影に runner 本体が無いため未確認です。「load は timeout 外」とも断定しません。どちらでも、driver に session 全体の上限が無いという穴は残ります。

   **48 h 案は運用上の余裕として採用可。** 保証できるのは許容された開始時刻同士の差 `>48 h` までです。終了→開始も確認するなら、後続の証拠確認者が実際の時刻から確認する、と記録してください。D1974 項 3・6 の責任を式で完了扱いにしてはいけません。

3. **［情報］8 日窓は「2 campaign」と矛盾しないが、独立性を増やさない。**

   D1641 決定 3 は campaign の最大継続時間を指定していません。各 workload に campaign ID 2 件、各 campaign に 1 pair・62 sample を固定する案は、D1695・D1697・D2089 と整合します。8 日は開始可能期間であり、8 日分の独立反復ではありません。

   D1641 の「24 時間以上離した」は、開始間か終了→開始かを逐語で定義していません。plan が開始帯の算術と実 campaign 分離を分けたのは適切です。終了→開始の確認は保守的な確認方法として説明し、既裁定の唯一の定義と断定しないでください。

   途中失敗後の再作成・測り直しを窓幅で正当化する余地もありません。create-only と予定外 retry の規則は維持されます（D1641 決定 3、§11.1 手順 7、F:2273）。

4. **［must-fix］brief の seed 無害性・実測時間の一般化は、plan の訂正を最終記録へ反映する。**

   B/P4 の「side 順序だけ」「同一 bytes なので有利な選択は存在しない」は削除が必要です。HMAC は sample 順・side 順・candidate/reference 順を決めます（F:1352、F:1366、F:1378）。

   main の取り込み時点を変えれば source_commit と seed を変えられるため、**順序の選別余地があるという攻撃は成立**します。また HMAC 入力には spec hash もあり、日付や直列化の変更でも順序が変わります。同一 binary でも時間変動・欠測・分子分母への観測値の割当ては残ります。ただし、今回実際に有利な seed を選んだ証拠はありません。

   P:533 の「親 commit や path を試行選別しない」は適切です。結果を見ない理由で親を確定し、最終 bytes を固定する運用で進められます。公開式は再現性を与えますが、選別不能性を証明しません。

   B/P2・P5・P8 も、P:547〜563 の限定を採用してください。

   - 1240 rep × 3.5〜4.5 秒は約 1.21〜1.55 h。probe・検査・I/O 等を含む上限ではありません。
   - 較正と異なる node、affinity、負荷、records 数、binary 構成で時間は変わり得ます。**ユーザー提示の BACK_OFF=0→1 差も、同じ時間分布を仮定できない反例候補**です。この binary 差自体は射影から独立確認していません。
   - NUMA 1 node の較正記録は将来の割当てを保証せず、`[]` と `None` の下流での同値性も driver の射影だけでは証明できません。
   - 120/4.5 ≈ 26.7 は算術であり、timeout 発生率や欠測の偏りの保証ではありません。

5. **［情報］hash・HEAD blob・祖先性は事前性を単独では閉じない。**

   凍結済みの期待 hash を維持すれば、日時・ID・命名の変更は bytes 不一致になります。しかし、変更した spec を後続 commit に入れ、期待 hash も差し替えれば、現在 HEAD との一致と source_commit の祖先性は再び満たせます。祖先性はその間の変更内容を制限しません（F:14、F:22、F:614、F:1285）。

   したがって plan の「3 spec と期待列を測定前の同じ commit に記録し、その pin を後続が使う」が必要です。「機械的に後変更不能」とは記録しないでください。窓を失った場合も旧記録を残し、途中結果に応じた延長・差替えをしない扱いが適切です（P:512、D1974 項 6、§5.1 floor 追補(b)(f)）。

6. **［must-fix］後続申し送りに、2 窓と finalize の HEAD 整合条件を加える。**

   plan は「HEAD が進んでも plan bytes は条件付きで不変」と説明していますが、**それは window 成果物の finalize 可否とは別です。**

   run 時の header は `loaded_head`・`runtime_head` を保存し、finalize は両方について、その finalize が読み込んだ `spec.loaded_head` との exact 一致を要求します（F:2247、F:2700、F:2721）。

   そのため、同じ spec bytes のまま w1 を HEAD A、w2 を HEAD B で実行しても、同じ finalize へ通るとは限りません。後続 wave には、少なくとも各 spec の両窓と finalize を同じ実行 HEAD に揃える手順を明記してください。凍結 commit 自体で実行する必要はありません。header の書換えや検査緩和で解消してはいけません。

7. **［must-fix］D2088 の「spec の非保証欄」の扱いは、明示的な訂正として残す。**

   D2088 は `reps=5` の AI 選択を「spec の非保証欄と本決定に残す」としています。一方、plan は schema に受け皿が無いとして decisions/insight へ置きます（P:480）。

   schema を変えず外部文書へ記録する解決には賛成です。ただし「逐語どおり履行済み」とせず、**当該欄が無いため、凍結 spec の path/hash に対応付けた決定記録へ残す訂正**だと新 D に明記してください。D2088 は AI 委任下の決定で、凍結前の追記も認めています。新しいユーザー裁定は不要です。

8. **［nit／情報］命名・集約・規律 2／7 は概ね適切。**

   spec 名への campaign 成分追加は可読性の選択として採用できます。D1641 決定 3 の成果物命名規則を spec にも必須化した、と説明するのは拡大解釈です。plan はこの区別を既に保っています（P:486、precheck README:96）。

   窓は JSONL、summary は JSON という現行の別形式です。「すべて単一 JSON 文書」とは説明せず、既存 format ID を維持してください（F:67、D1641 決定 3）。

   期待 spec 3 組を独立して固定し、3 cell × 2 窓の全入力を最大化する案は §5.1 floor 追補と整合します。binder 緩和、新 gate、manifest 新設、正常入力への間引きは見当たりません。旧仮置き値を先例にしないことも、過去の precheck 成功を無効化することとは別です。D2090 の method 差だけを拒否理由にしない規律も維持してください。

9. **［情報］走査器への混入源は、旧資料の転載と識別子の継承。**

   仮置き JSON は directory・window ID・campaign ID・出力 path に `precheck-placeholder-*` を含み、2030 年日時とゼロ seed も持っています。これらを継承しない現 plan は適切です。旧 branch 名や precheck の見出しを insight へ転載する場合にも一般語が混入します。

   三軸語については、取得 argv・旧 workload JSON・別用途の説明を同じ insight に転載する箇所が危険です。plan は「三軸 conjunction 検査」と「仮置き語の別走査」を区別しています。実際、旧 precheck insight は当該一般語を含んだまま search rc=0 と報告しています（README:1、README:141）。

   scanner 本体は射影外のため、正規表現の細部は独立検証していません。新しい spec/insight に対する実走結果を採用し、旧 search 成功を流用しないでください。

insight／D fragment の「主張しないこと」には、少なくとも次を残すべきです（F:12〜23、D1974 項 6、D2069 項 4〜5）。

- 期待集合・seed 選択・凍結の事前性の機械証明。
- n=62、実 campaign 分離、対象集合の意味的一致の機械保証。
- 統計的独立性、残存標本の被覆確率、contention 域の網羅性。
- session wall time 上限、将来環境の同一性、別 node 並走・admission・実走成功。
- binary の将来可用性、trace 不在の完全検出、実行中 module bytes の commit 対応。
- 成果物の削除・改変防止、床値生成・採用・§5 発効。

## 総括

**(a) must-fix 一覧**

- 48 h と per-rep/probe timeout から終了→開始の分離を証明する主張を撤回する。
- seed の無害性・1.6 h 上限・NUMA／並走保証について、plan の訂正を最終記録へ反映する。
- 各 spec の両窓と finalize の HEAD 整合条件を後続申し送りへ加える。
- D2088 の非保証記録先を、schema 上の制約による明示的訂正として D に残す。

**(b) ユーザーへ返すべき裁定事項**

現案の範囲ではありません。A-5 は D2120 項 4 の委任で確定できます。既決の対象集合・統計・欠測規則・時間分離要件そのものを変更したくなった場合は別です。

**(c) 採用してよい plan の値**

- 3 spec、各 1 cell・1 pair・2 campaign・各窓 62 sample、既決の perf／較正／binary／統計。
- campaign 成分を加えた spec 名、提示した各 ID・窓出力・summary・集約対応。
- seed 導出式と source_commit＝凍結 commit の親。ただし試行選別しない。
- `timeout_s=120`、`probe_timeout_s=30`、`numactl_argv=[]`、`extra_env={}`、`use_perf=false` を今回の運用選択として採用。
- 親の **w1＝9/19〜9/27、w2＝9/29〜10/7（UTC、半開区間）**も採用可。48 h は余裕であり終了時刻の保証ではない。変更後は spec hash と plan を再計算する。