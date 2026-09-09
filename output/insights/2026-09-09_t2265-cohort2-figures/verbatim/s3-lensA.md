### 所見 1

- **主張**: `extime 6`・schema v3 は、旧 H1–H7 の確認ではなく別測定としてのみ成立し、旧事前登録に基づく確認的判定と呼べば凍結破りになる。
- **根拠**: `docs/dynamic-backoff-preregistration.md:27-29` は前向き固定の対象を「**本 grid**」と限定し、同 `:71-85` は `extime = 3 秒`・「結果 schema v2」を固定する一方、`s1-brief.md:78-79` は「**置き換えでも再測定でもなく、別の観測長の companion 集合**」と明記する。この逐語が両者を分ける境界である。それにもかかわらず `plot_dynamic_backoff.py:2-10` は H1–H7 と判定域を旧文書により frozen と称し、`s2-plan.md:161,164` は新測定を H1–H7 の確認的判定へ昇格可能としている。
- **これが本当なら何が壊れるか**: 図と provenance の H1–H7 `status` が旧凍結条件の判定に見え、insight・worklog の参照する試験と実際の値の母集団がずれる。
- **確度**: real

### 所見 2

- **主張**: P1 は新しい別試験の前向き登録にはなりうるが、旧凍結を解消せず、現在の plan では成果物への束縛が外付けなので半分は見せかけである。
- **根拠**: `s2-plan.md:154` は登録文書の commit を submit tree に取り込まないとし、`:162` は SHA を台帳と insight にだけ記録する。ところが作図器は JSON の `prereg_sha256` を読むだけで (`plot_dynamic_backoff.py:268-291`)、provenance にもその旧 SHA だけを書く (`:1709-1711`)。新 companion 文書の SHA を入力または provenance に束縛する経路はない。旧文書自身は、本走が登録文書を含む commit を指し、JSON がその SHA を持つ契約である (`docs/dynamic-backoff-preregistration.md:21-25`)。
- **これが本当なら何が壊れるか**: 図の provenance は旧 `extime 3` 登録を指す一方、insight・台帳だけが新登録を指し、「どの登録が値を束縛したか」という参照が分裂する。
- **確度**: real

### 所見 3

- **主張**: 親の「legacy 7 腕だから §10 は当てはまらない」という読みは、字面を守る代わりに本 wave を cohort 2 の性能測定ではなくしてしまう。
- **根拠**: cohort 2 文書は「時間 cap の値と比較方法は計装ではなく CC 本来の機構」であり、cohort 2 cell は別 CC 設定だと明記する (`docs/backoff-counterfactual-cohort2-preregistration.md:112-113`)。cohort 2 は cap `9223372036854775807` の p0/p1/p2 (`:153-164`) だが、性能側 `cw-as-dyn` は cap `10240`、policy field なしである (`plot_dynamic_backoff.py:102-116`)。したがって、真に legacy 7 腕なら §10 の policy 腕禁止には当たらないが cohort 2 の trace-disabled 対応物でもない。逆に cohort 2 の性能対応物と主張するなら、§10 の「**policy 腕の trace 無効な性能測定。…独自の事前登録が要る。本書は覆わない**」がそのまま当たる (`:366-369`)。
- **これが本当なら何が壊れるか**: legacy 性能 H1–H7 と cohort 2 診断を一つの図群に置いても、両者を同じ機構の性能と局所 ITT として結ぶ判定は成立しない。
- **確度**: real

### 所見 4

- **主張**: projected evidence 上で未充足または未立証なのは、`extime 6` 確認試験の事前登録束縛、実ノードの環境・較正、そして測定する A+B+C 実行体の correctness 適格性である。
- **根拠**: 旧登録は `extime 3`・schema v2 (`docs/dynamic-backoff-preregistration.md:71-85`)。規律 7 はコード同一性を不要とする一方、事前登録・凍結・環境契約・較正・correctness gate を残す (`CLAUDE.md:97-105`)。計測はノード確保、単独性、外乱検知を環境 runbook に従わせる (`CLAUDE.md:150-156`) が、plan が示すのは固定値 `clocks_per_us=2100` と qsub argv で、live calibration や割当環境の成立証拠ではない。直前 insight の認証は既定 seed・48 thread の cohort 2 policy≠0 実行体だけで、12 seed、24 thread、まして legacy 7 腕全体を覆わない (`README.md:171-188`)。ただし trace-disabled 分離と「採用根拠にしない」という規律 1・2 の限定は brief が満たしている (`s1-brief.md:75-77`)。
- **これが本当なら何が壊れるか**: raw な未認証記述値は得られても、確認的 H 判定、環境間比較、正しさ・採用判定への受理集合には入れられない。
- **確度**: plausible

### 所見 5

- **主張**: 親は作図器の互換条件である旧 `repo_head` 同一性を、規律 7 上の測定開始条件へ過剰一般化している。
- **根拠**: 規律 7 は「新しい測定はいつでも開始できる。開始条件に、過去の承認済み状態とのコード同一性を置かない」とする (`CLAUDE.md:100-105`)。一方、作図器が要求するのは、選んだ診断 JSON と性能 JSON の identity が同一であることだけである (`plot_dynamic_backoff.py:1274-1276`)。これは既存診断と一緒にこの作図器へ入れるための consumer 契約であって、新規測定一般の科学的開始条件ではない。
- **これが本当なら何が壊れるか**: plan は「測れるか」と「既存診断と同じ invocation で描けるか」を混同し、新しい正直な測定経路を不要に排除する。
- **確度**: real

### 所見 6

- **主張**: `714〜731 + 168×3 ≈ 1220秒` は概算としては妥当だが、上限や所要保証を支える外挿ではない。
- **根拠**: `s1-brief.md:117-123` と `s2-plan.md:78-85` は、168 process が直列に各ちょうど 3 秒延び、build 7 本、prologue、起動・終了、I/O の固定費が同じだと仮定している。旧成果物は schema v2、新成果物は A+B+C の schema v3 なので build 条件は完全同一でなく、7 job 同時実行時のノード・filesystem・scheduler 外乱も 504 秒の加算には含まれない。2400 秒枠には大きな余裕があるため運用上の目安としては合理的である。
- **これが本当なら何が壊れるか**: 固定費や外乱が増えれば job が見積りを超え、欠測により n=7 が n=6、さらに 5 以下なら図生成停止へ変わる。
- **確度**: plausible

### 所見 7

- **主張**: `clocks_per_us=2100` が全成果物で一致する確率は高いが、それは全ノードが実際に同じ較正値である証拠ではなく、固定値を書いているためである。
- **根拠**: `s2-plan.md:107-109` は値を node calibration でなく hard-selected contract と認める。したがって同一コード経路なら、ノード分散だけで identity が落ちる確率は実質 0 であり、既存 bnode 群の JSON がすべて 2100 なのも独立な実測裏付けではない。実クロックが異なっても field は 2100 のまま通り、少なくとも診断図の elapsed 軸はこの値で換算される (`plot_dynamic_backoff.py:1488-1492`)。逆に field が一つでも異なれば全入力 equality が落ちる (`:1274-1276`)。
- **これが本当なら何が壊れるか**: 物理較正ずれは検出されず診断時間軸を歪め、field 自体が違えば図全体が拒否され、後から 1 本を除くかという受理集合問題が生じる。
- **確度**: real

### 所見 8

- **主張**: 「`8bdf173cc` の detached checkout からしか成立しない」は偽であり、detached かどうかは `repo_head` に符号化されない。
- **根拠**: brief の断定は `s1-brief.md:68-69`。plan 自身も PBS が `rev-parse HEAD` を採るとの説明しかしていない (`s2-plan.md:91-93`)。同じ commit を先端に持つ通常 branch の clean worktree は同じ full SHA を返すため、正直な別経路である。JSON を後編集して SHA を偽装する経路も技術的にはあるが、それは正直な経路ではない。
- **これが本当なら何が壊れるか**: 測定値は変わらないが、投入元に関する plan・worklog の必要条件と再現手順が不当に狭くなる。
- **確度**: real

### 所見 9

- **主張**: fixture が legacy performance と cohort 2 diagnostic の組合せを通すことは、実測成果物が通ることを意味しない。
- **根拠**: plan 自身が test は全 CLI 経路を走らせず、実データ固有の bbox は未確認と認める (`s2-plan.md:42`)。実物では rep・job ID・15 identity field・schema・cell order が一致する必要がある (`plot_dynamic_backoff.py:1242-1281`)。さらに性能 parser は各 JSON に完全な 168 点ではなく 1〜168 row を許す (`:480-496`) ため、regular file の存在だけでは complete block を証明しない。fixture はこれらを意図的に整えた入力である。
- **これが本当なら何が壊れるか**: 実物では fail-closed で図が一枚も出ないか、欠点により n が下がって H の受理集合が `inconclusive` に変わりうる。
- **確度**: real

### 所見 10

- **主張**: 出来上がる図が支持できるのは extime 6 の legacy 7 腕における限定的な対内性能記述だけであり、cohort 2 の局所 ITT や policy 腕の性能を支持しない。
- **根拠**: 言ってよいのは、Pegasus gen_S、Silo、YCSB 3 workload、1M records、threads 6〜48、6または7 block、trace-disabled、extime 6 での系列・対内 log 比である。言ってはいけないのは、旧 extime 3 H1–H7 の確認、`+4.9%` の trace-disabled への一般化、policy 0/1 の run 全体効果、全 workload/thread への効果、正しさ・採用・fitness、他環境への一般化である。直前 insight はこれらを明記する (`README.md:140-150,185-188`)。brief と plan は「未認証」「extime 3 を置換しない」は持つが、legacy 7 腕が cohort 2 の別 CC 設定であるという最重要限定を落としている。図の caption にもこの断絶はない (`plot_dynamic_backoff.py:1609-1621`)。
- **これが本当なら何が壊れるか**: insight・worklog が性能 H と ITT 主判定を相互補強する証拠として参照すると、図が答えていない因果・性能主張へ一般化される。
- **確度**: real

### 所見 11

- **主張**: 外部 JSON・trace・CCBench は、形式検査を通りながら値と provenance を歪める余地がある。
- **根拠**: 規律 6 は CCBench、出力、trace を指示でなくデータとして扱うよう要求する (`CLAUDE.md:88-95`)。作図器の `repo_head`、`prereg_sha256`、driver/PBS SHA などは入力 JSON から読み、主に入力同士を比較するだけで (`plot_dynamic_backoff.py:253-338,1274-1276`)、実際の prereg file や checkout と照合しない。性能値は正・有限、`median_tps` 一致を検査するだけ (`:399-438`)。trace は directional success を再計算するが (`:616-636,792-798`)、この作図器では cohort 2 解析器の LCG assignment-integrity や `counterfactual_preregistration` を検査しない。CCBench pin は bytes の同一性であって、そのコードや出力の正しさの証明ではない。
- **これが本当なら何が壊れるか**: 自己整合的に加工された JSON や trace が任意の図・H 判定を作り、provenance も偽の由来をそのまま再掲できる。
- **確度**: real

### 所見 12

- **主張**: P2 の `985851` 選択は再現可能ではあるが、結果生成後に作られた規則なので事前凍結ではない。
- **根拠**: brief は既に存在する 12 本から「図を見る前」に選ぶとしている (`s1-brief.md:98-100`) が、直前 insight は 12 本すべての完走と解析済み outcome を既に報告している (`README.md:96-138`)。job ID 最小という規則自体は outcome-blind でも、結果存在後に多数の候補規則から選んだ事実は変わらない。診断図は 1 file、n=1 であり (`plot_dynamic_backoff.py:1535-1605`)、選択 seed により軌跡と方向的中率が変わる。
- **これが本当なら何が壊れるか**: H1–H7 の性能値は変わらないが、diagnostic 図の軌跡・方向的中率と、それを代表例として扱う insight の参照が変わる。
- **確度**: real

## 総括

現 plan のままは測らず、投入前に `extime 6` を「未認証の記述的な別測定」とするか「新規確認試験」とするかを固定し、後者なら新登録を実成果物へ正直に束縛したうえで、legacy 7 腕を cohort 2 policy 性能と結び付けないことが必要である。