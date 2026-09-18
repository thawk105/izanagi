## 所見

以下、`C/` は `orchestrator/campaign/`、`J/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2/`。実装前の計画レビューであり、テスト・計測は未実走。

### must-fix

1. **real — `input_sha256` は、現案では「実入力の証明」ではなく親が指定した JSON のハッシュである。**

   根拠: `J/plan.md:19,48,55,74,316`。現物の `C/p3_s4_loop.py:2254` は proposal を読み、role の起動・入力送達を観測しない。`--agent-inputs` を追加してもこの境界は変わらない。`mode=live` も出力生成が harness 内だったことを意味しない。

   **成果物影響:** 別の入力 JSON を渡しても、材料レポートに「この入力から生成された出力」という誤った対応が保存される。

   最小是正: `input_sha256` を「呼出し側が実入力として申告した保存 JSON の canonical hash」と定義し、`live/ingested` は記録方式と明記する。取得できる role 呼出し原文・追加指示・参照文書の版との対応を既存 provenance に残す。入力 key や manifest digest の一致は整合検査にはなるが、実送達の証明とは呼ばない。`ts` は記録時刻でよく、生成時刻は根拠がなければ不明とする。

2. **real — stage・入力・出力・WAL・digest の対応検査が契約として閉じていない。**

   根拠: `J/plan.md:25,53,56,119,264,310`。envelope の型検査と WAL ref の存在確認だけでは、`planner_proposed` に coder object を渡す、variant A に variant B の ref を付ける、別 digest を指定する誤対応を排除できない。現行 loader は `C/p3_s4_loop.py:2318,2350` で role schema と K2 の入力対応を検査している。manifest の射影元は `C/knowledge_manifest.py:490`、campaign への束縛は `C/p3_s4_loop.py:1545`。

   **成果物影響:** 実在するが無関係な一次証拠を参照する機序仮説が、双射を通過して材料レポートに載り得る。

   最小是正: 取込み口の既存計画に、stage と `--agent-output-key` の対応、対象 role 出力の schema、指定入力からの hash 再計算、K2 manifest の対象 campaign との整合を明記する。critic の digest は、保存された入力中の digest と指定 digest の bytes を照合する。variant に属する参照を謳う場合は、その WAL record の variant も一致させる。比較対象など別 variant の参照は、その用途を区別する。これらは記録の整合検査であり、正しさゲートを代替しない。

3. **real — 入力側防壁のテスト対象から `_prepare_knowledge_campaign` と入口の接続が漏れている。**

   根拠: `J/plan.md:80–88` は3関数だけを対象にする。現物では `C/p3_s4_loop.py:1531` が knowledge projection を作り、`:1238` が渡された `knowledge_input` をそのまま planner payload に入れる。

   **成果物影響:** 上流で AO を読み knowledge input に混ぜる変更が入っても、3関数単独の検査は通り、次 proposal とその後の評価対象が変わり得る。

   最小是正: 実際の planner-context 入口から knowledge 準備と builder までを対象に含める。AO reader は記録・renderer 側では利用でき、入力生成経路で呼ばれた場合だけ失敗させる。AO の不在・正常・不正を同じ対象 layout で切り替える検査と、上流 helper が AO を読み込む変異で赤になる検査を組にする。固定 state に無関係な AO file を置くだけでは、不変性が候補集合から自明になる。

4. **real — coder-2 の入力欠落を認めながら、完成件数は依然 AO 5 件で固定されている。**

   根拠: `J/plan.md:249–262` は coder-2 の取込み未完了を認める一方、`:283,286` は AO を一律 `+5` とする。凍結設計 `output/insights/2026-07-16_layer3-mechanism-wiring-design.md:26` は入力 hash を要求する。

   **成果物影響:** 件数を満たすために再構成入力を実入力扱いするか、正直な4件のレポートを不当に未成立とする圧力が生じる。

   最小是正: 原文回収不能なら**4 event を取り込み、coder-2 の欠落を明記する**。双射は「保存された AO 全件」に対して成立させ、役割出力の完全収集とは区別する。`input_sha256:null` の追加受理や再構成入力の実入力扱いは採らない。件数式を実取込み数へ訂正する。完全収集が必須という判断なら、その部分だけ未完了とする。

5. **real — brief の研究前進と完了説明が現行防壁に反する。plan の訂正を brief に反映すべきである。**

   根拠: `J/brief.md:10–11,68–70` の非 null delta・whiteboard 2件に対し、`C/p3_s4_loop.py:1213` は非 null を拒否し、`:2483` は checkpoint 不在時に新規 state を作る。`J/plan.md:90,274–293` の反証は妥当。

   **成果物影響:** 材料レポートや insight に、存在しない campaign-local 履歴と改善幅が記載される。

   最小是正: 「別走行を含む2巡の記録」と「本 campaign の whiteboard」を区別し、件数は現物、delta は null とする。また `J/brief.md:86` の非主張へ「機序仮説は LLM の帰属記録であり、機序の実証ではない」を追加する。通常 report の `certifying_input=false` と `acceptance_receipt=null` は現行 `C/layer3_report.py:908` のまま保持する。

6. **real — attempt-0002 は、文言上の「再投入なし」から逸脱している。評価未実施だけでは例外を導けない。**

   根拠: `J/rulings/D2120-koumoku1.md:25–29` は「評価 job 1 本」と「再投入なし」を併記する。`J/handoff.md:33–35` は preflight 拒否後の別 job 投入と、親による予算未消費判断を記録している。

   **成果物影響:** 「投入1本・裁定内で完遂」と記すと、試行台帳の投入回数と認可への適合状態が事実と異なる。

   最小是正: 段4では「投入2本。attempt-0001 は7秒で preflight 拒否、driver 未起動・campaign 未接触。親判断で attempt-0002 を投入」と残す。「再測定・再抽選ではない」と「再投入禁止への適合」は分ける。測定事実を消さず、裁定本文も書き換えない。

   **裁定パッケージ候補:** この逸脱の扱い。preflight 失敗を今後一律に予算外とする一般規則は、本 wave で設計しない。

### refuted・nit

7. **refuted — AO を `runs/` に追加しただけで admission の束縛が変わる、という疑い。**

   根拠: `C/artifact_admission.py:1286–1301` は lock と WAL の個別 bytes を hash する。`C/layer3_report.py:807–814` も同じ2ファイルと照合する。未知 file のディレクトリ全体 hash ではない。一方、`:224` の `artifact_refs` は全 file を列挙する。

   **成果物影響:** AO 追加で材料レポートの artifact 参照は増えるが、それ自体で admission・certified 判定・既存 digest の bytes は変わらない。

   最小是正: plan の独立 writer と早期 return を維持し、取込み前後で WAL・lock・loop_state・digest・knowledge receipt の bytes 不変を確認する。現計画の「WAL 不変」だけより対象を明確にする。writer の実装前なので、副作用ゼロの実証済みとは扱わない。

8. **refuted — 未評価 proposal-3 の ID が WAL namespace と衝突する、という疑い。**

   根拠: `J/plan.md:76,119,257–258` の実際の決定は ID 生成ではなく `variant=null`。全 AO を一次配置に入れる契約は `:106`。

   **成果物影響:** 採用案なら未評価出力も AO 双射に残り、架空の評価済み variant 参照を作らない。

   最小是正: null 方針を維持する。planner/coder に非 null を指定する取込みについては、対象 WAL に存在することを明記する。双射だけでは WAL との対応は保証されない。

9. **refuted — harness による critic 節抽出が role 契約に反する、という疑い。**

   根拠: `.claude/agents/critic.md:33–37` は4項目を要求するが、見出し表記を禁止・固定していない。`J/plan.md:133` の決定論抽出は、親の自由な節切りを退けている。

   **成果物影響:** raw 全文と抽出結果が機械的に対応すれば、追加節を失わずに帰属 view を作れる。

   最小是正: prompt の見出し指定を保存入力に含め、抽出は原文の範囲選択に限定する。見出し欠落・重複を拒否し、読取り時にも raw からの再抽出一致を確認する。`raw_markdown` の併記だけでは、改変された attribution との不一致を防げない。uncertainty も一次配置に保持する。

10. **refuted — 親が file を指定できること自体で「harness だけが書く」に違反する、という疑い。**

    根拠: 凍結設計 `output/insights/2026-07-16_layer3-mechanism-wiring-design.md:26–32` の条件は、永続面の書き手と生成入力経路の分離である。外部出力を harness が受け取ること自体は禁止していない。

    **成果物影響:** 記録の出所を申告以上に扱わず入力側へ還流させなければ、取込み口の存在だけで certified 選択は変わらない。

    最小是正: 所見1・2の整合検査と主張限定を行う。書き手が harness であることを、内容の真正性・LLM の実生成・機序の正しさの保証へ拡張しない。

## 総括

専用 AO writer、報告層への分離、proposal-3 の `variant=null`、critic の決定論抽出は妥当です。段4では、**申告入力と実送達の区別、記録間の対応検査、knowledge 経由を含む入力防壁、4件取込み時の完了範囲、brief の誤前提、再投入の逸脱記録**を修正してください。

正しさゲートの変更・迂回は不要です。コード編集・テスト・計測・commit・push は行っていません。