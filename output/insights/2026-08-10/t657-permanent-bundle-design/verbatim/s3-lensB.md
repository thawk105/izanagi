## 前提

指定された brief、段 2 plan、先行設計 §5・§6・§8、freeze 恒久設計 §7・§8・§14、指定 consumer 群を読了した。ファイル変更・pytest は行っていない。

## real（実在の欠陥）

### 1. S1/S2 の分離が名前だけで、実質 S1 に寄っている

(a) 主張  
`SealPolicyAdapter` は宣言されているが、S1 の束縛 record も S2 の新 prediction seal も core schema に入っていない。prediction は「実在入力」とされる一方、digest の必須構成に含まれない。

(b) 根拠  

- [stage2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:131)
- [stage2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:148)
- [stage2-plan.md:247](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:247)
- 先行設計 [§6 S1:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:105)、[S2:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:139)

(c) 壊れ方  
g2 用の環境・freeze candidate に、旧 prediction bytes を組み合わせる。

- S2 なら、新世代用 prediction の事前封印が無いので拒否されるべき。
- S1 なら、旧 bytes と新世代の binding record が必要。
- しかし plan の共通検査はどちらも要求しない。旧 prediction のままでも環境 hash、freeze hash、bundle digest の最低限の検査は通る。

現行 selector 側も [s8b_selector_freeze.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_selector_freeze.py:1001) から [s8b_selector_freeze.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_selector_freeze.py:1018) まで v1 固定であり、S2 の世代分岐がない。

(d) 判定: **real**

---

### 2. `ruling_profile_sha256` だけでは unknown profile を検査できない

(a) 主張  
plan は unknown profile の X を拒否すると書くが、profile の raw bytes、path、namespace、canonical schema が resolver 入力に存在しない。

(b) 根拠  

- [stage2-plan.md:133](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:133)
- [stage2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:148)
- [stage2-plan.md:238](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:238)
- [stage2-plan.md:253](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:253)

(c) 壊れ方  
B が `ruling_profile_sha256` だけを持つ profile を指す。resolver は hash に対応する bytes をどこから読むか定義されていないため、次のいずれかになる。

- profile 内容を検査できず、unknown を受理する。
- 暗黙の固定 path を追加し、先送りしていた profile namespace を親が決める。
- profile を読めず、既知の unresolved profile まで X 不能になる。

(d) 判定: **real**

---

### 3. G-b は実装不能で、具体的規則は G-a 水準に留まる

(a) 主張  
plan は bundle ID の伝播を要求するが、G-b に必要な「binding 後に実走開始した」という因果・時系列・claim の型を定義していない。

(b) 根拠  

- [stage2-plan.md:141](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:141) で claim ID を入力から除外
- [stage2-plan.md:219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:219) は receipt の bundle identity のみ
- [stage2-plan.md:262](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:262) は side effect 前の bundle ID 検査のみ
- 先行設計 [G-b:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:151)
- 現行 submit receipt は [submit_floor.sh:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/pegasus/submit_floor.sh:353) から [submit_floor.sh:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/tools/pegasus/submit_floor.sh:367) まで bundle を持たない。

(c) 壊れ方  
新世代の floor を scratch で先に実走し、結果を見た後に bundle receipt を作って qsub する。後付け receipt の hash は正しく、submission も receipt 後である。

plan の identity 検査は通るが、実走開始時刻が binding より前だった証拠がない。G-b では拒否すべき入力が、G-a では受理される。どちらを採るかを未裁定のまま、受理集合だけが G-a に固定される。

(d) 判定: **real**

---

### 4. registered-inactive の型が validator の途中で消える

(a) 主張  
`ResolvedAuthorityBundle` に candidate / registered-inactive / active-official の型分離がなく、既存 validator に渡した時点で世代状態が消える。

(b) 根拠  

- [stage2-plan.md:90](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:90)
- [stage2-plan.md:162](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:162)
- freeze 設計が要求する四型分離: [freeze-permanent-design.md:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:177)
- 現行 resolver は inactive を拒否: [env_contract.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:691)
- protocol validator が受け取るのは SHA lookup だけ: [s8b_floor_contract.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_contract.py:105)、[s8b_floor_contract.py:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_contract.py:149)
- floor 側は `ExecutionEnvironmentContract` に縮約: [s8b_floor_campaign.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:356)、[s8b_floor_campaign.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_floor_campaign.py:381)

(c) 壊れ方  
pegasus g2 の valid な登録済み・未活性 record を候補として渡す。

- 現行 `resolve_by_contract_sha256()` のままなら [env_contract.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:691) で拒否され、candidate を扱えない。
- その拒否を候補用に緩めると、返るのは通常の `ExecutionEnvironmentContract` であり、候補性が消える。
- さらに `validate_protocol()` の出力は `contract_sha256` を持つ普通の dict だけで、generation・issuer・bundle 所属を持たない。

つまり「候補を受理する」か「current と同じ権限として受理する」かの二択になる。

(d) 判定: **real**

---

### 5. 段 2 の literal 除去が g0 authority の出所を失わせる

(a) 主張  
stage 2 は `_ACTIVATION_HEAD_*` を production authority から除去するが、g0 の serial 1 を record から選ぶ互換経路を定義していない。

(b) 根拠  

- [stage2-plan.md:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:261)
- R3 不変条件: [s1-brief.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:36)
- 現行 authority loader は literal を渡す: [env_contract.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:524)、[env_contract.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract.py:528)
- 現行 catalog validator は末尾を active head として検査: [env_contract_activation.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:408)

(c) 壊れ方  
serial 2 の正しい未活性 suffix を追加した状態で literal を削除する。

- catalog の末尾を選べば g2 が active になり R3 を破る。
- serial 1 を選ぶ規則を持たなければ g0 の `lookup()` / current admission が失敗する。
- 既存 consumer の切替は stage 3 なので、stage 2 の独立 green 条件を満たせない。

実際の今 wave が g2 を活性化したとは確認していないが、段階設計は R3 を機械的に保証していない。

(d) 判定: **real**

---

### 6. E/F/B/Q の lineage と Q receipt が束縛されていない

(a) 主張  
A/X の制約は書かれているが、E/F/B/Q の導入 commit の exact diff、parent、immutability、Q の検査内容が未定義。Q は digest に含まれない。

(b) 根拠  

- topology: [stage2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:43)、[stage2-plan.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:47)
- A 検査の列挙: [stage2-plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:60)
- digest の必須項目: [stage2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:148)
- stage 4 の mutation 集合: [stage2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:263)
- 既存 freeze 設計では A が report hash まで束縛する: [freeze-permanent-design.md:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:285)

(c) 壊れ方  
Q commit に「検査 pass」とだけ書き、B の正しい digest を指す A をその Q の子として作る。A の parent、diff、trailer、B digest は検査を通るが、Q の内容は再計算されない。

さらに B を merge で導入しても、B の導入形状を検査する規則がない。Q/B の差し替えは B digest の最低限項目を変えない限り X の判定に現れない。

(d) 判定: **real**

---

### 7. consumer の出口に bundle 型が届かない

(a) 主張  
指定された五 consumer の列挙自体はあるが、claim、journal、marker、budget、job-result、report の具体 schema が bundle-aware になっていない。

(b) 根拠  

- 先行設計が要求する claim / job / receipt 層: [calibration-freeze-joint-generation-design.md:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:200)、[calibration-freeze-joint-generation-design.md:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:208)
- plan は `campaign_lock` だけを具体化: [stage2-plan.md:228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:228)
- `ClaimRecord` に bundle field がない: [campaign_claim.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/campaign_claim.py:34)
- oracle claim identity は manifest/freeze/schedule のみ: [s8b_oracle_driver.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_oracle_driver.py:879)
- run marker は freeze SHA のみ: [s8b_run_marker.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_run_marker.py:32)、[s8b_run_marker.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_run_marker.py:101)
- budget ledger も bundle を持たない: [s8b_budget.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_budget.py:208)
- verdict CLI は prediction/oracle/freeze を独立引数で受ける: [s8b_verdict.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_verdict.py:822)、[s8b_verdict.py:847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_verdict.py:847)
- report は family resolver を直接呼ぶ: [s8b_oracle_report.py:1750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_oracle_report.py:1750)

(c) 壊れ方  
bundle verifier を producer と preflight に追加しても、claim/marker/budget/report が freeze SHA と protocol SHA だけを記録し続ける。

同じ freeze bytes に対して環境世代だけを差し替えた二つの bundle を作ると、旧 claim identity、run marker identity、budget identity、verdict 入力は同一のままである。bundle record を差し替えても、これらの出口の結果は変わらない。新 verifier は存在するが、権限を最終成果物へ伝えていない死んだコードになる。

(d) 判定: **real**

---

### 8. P1 の「freeze 文書を一切改訂しない」は authority precedence を壊す

(a) 主張  
旧文書は freeze family resolver を consumer の単一入口として記述したまま、新文書は上位 bundle resolver を production authority とする。P1 はこの衝突を解消しない。

(b) 根拠  

- P1: [s1-brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:50)
- 旧文書の単一 resolver: [freeze-permanent-design.md:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:297)
- 旧 migration も全 consumer を family resolver へ切り替える: [freeze-permanent-design.md:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:320)
- plan 自身が危険性を認める: [stage2-plan.md:274](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:274)

(c) 壊れ方  
ある consumer が旧 family resolver、別の consumer が上位 resolver を使う。freeze は同じでも environment tip が異なると、片方は `new env + old freeze` を受理し、もう片方は拒否する。混在防止の正本が二つになる。

plan の cross-reference 案は提案に留まり、成果物・完了判定に入っていない。

(d) 判定: **real**

---

### 9. P2 の bundle digest 範囲が不足している

(a) 主張  
P2 は「freeze 世代 + environment candidate の組」を digest の中心とするが、S1/S2 の prediction 選択、Q、保証 profile、claim 時系列を区別できない。

(b) 根拠  

- P2: [s1-brief.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:52)
- plan の digest 定義が「少なくとも」としか書かれていない: [stage2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:148)
- S1 でも prediction の適用可否が可変選択になる: [calibration-freeze-joint-generation-design.md:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:132)

(c) 壊れ方  
同一の freeze/environment pair に対し、異なる prediction binding、異なる Q、異なる保証宣言を付ける。digest の必須 preimage が同じなら、異なる実験権限が同一 bundle identity に潰れる。結果を見た後に prediction の適用を選んでも、digest はそれを表さない。

(d) 判定: **real**

---

### 10. 設計文書が可変状態を再掲している

(a) 主張  
brief と plan が現在の台帳・HEAD 状態を再掲しており、将来の正本と競合する。

(b) 根拠  

- 現在の activation head を事実として再掲: [s1-brief.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:25)
- 現在の floor commit/hash を再掲: [s1-brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:28)
- record 件数 0 という現在状態も再掲: [s1-brief.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:26)
- plan も M1〜M4 の現在状態を固定文として再掲: [stage2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:7)、[stage2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:11)

(c) 壊れ方  
serial 2 や新 HEAD が導入された後も、brief の serial 1・G1 hash・record 0 が残る。読者がこれを設計上の現在値として使うと、台帳と二重の active source になり、g0/g1 の判定対象を誤る。

(d) 判定: **real**

---

## 先送り3件以外に必要な裁定

### A. 上位 bundle の A/X 実行主体と A の意味

(a) 主張  
plan は上位 A/X を「人間」と明記するが、既存 R13/R14 は freeze family 側の裁定であり、上位 bundle への適用は未確認。

(b) 根拠  

- [stage2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:48)
- [stage2-plan.md:72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:72)
- 既存 R13 は family pointer の X: [freeze-permanent-design.md:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design.md:424)

(c) 壊れ方  
A を digest 確認だけの人間承認にするか、Q の semantic review まで人間に要求するかで、同じ B が受理・拒否に分かれる。X を AI が実行できるかでも信頼境界が変わる。

(d) 判定: **real（裁定漏れ。適用範囲は未確認）**

### B. lockstep・rollback・revocation の新 bundle 政策

(a) 主張  
plan は環境と freeze の同時切替、rollback/fork の拒否を既定値としている。

(b) 根拠  

- [stage2-plan.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:75)
- [stage2-plan.md:264](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:264)

(c) 壊れ方  
environment だけ successor になる入力、freeze だけ successor になる入力、障害復旧の rollback 入力を、ユーザー裁定なしに一律拒否する。これは既存 family の lockstep 裁定を上位 bundleへ自動継承したことになる。

(d) 判定: **real（追加裁定が必要）**

### C. literal pin 喪失と長寿命 process の旧権限

(a) 主張  
plan は source-side pin を失い data-side pin へ移すことを受け入れているが、その loss acceptance は先送り3件とは別の明示的な運用判断でもある。

(b) 根拠  

- [stage2-plan.md:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:110)
- [stage2-plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:116)
- [stage2-plan.md:114](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:114)

(c) 壊れ方  
X 後も process-local `AuthorizedContract` が旧 state を保持し、旧環境権限で書き込む。これを許すか、即時拒否するか、restart のみ許すかで受理集合が変わる。

(d) 判定: **real（ユーザー受入が必要）**

## refuted（調査したが成立しなかった疑い）

### 1. 先送り3件をすでに一方へ裁定した、という疑い

(a) 主張  
plan が S1、G-b、機械的副作用検査を既に採用したのではないか。

(b) 根拠  

- profile は unresolved と明記: [stage2-plan.md:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:242)
- unresolved profile の X は拒否: [stage2-plan.md:253](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:253)
- policy 段は未定義: [stage2-plan.md:265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:265)

(c) 構成  
unresolved profile のまま X まで進めようとすると plan 自身が拒否する。副作用の cache/restart も裁定待ちと書かれている。

(d) 判定: **refuted**。ただし、上記の通り分離契約が不十分なことは real。

### 2. 現 wave が R3 をすでに破っている、という疑い

(a) 主張  
段 2〜4 の candidate 生成が pegasus g2 を active にする。

(b) 根拠  

- brief は activation record/literal を触らない: [s1-brief.md:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/s1-brief.md:36)
- stage 3 は active pointer を現状のままとしている: [stage2-plan.md:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:226)
- stage 4 も g0 resolver 不変としている: [stage2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:263)

(c) 構成  
serial 2 suffix と E/F/B/Q/A を追加しても X 前は current state が変わらない。実際の activation は記述されていない。

(d) 判定: **refuted**。ただし stage 2 の literal 除去には別途 real な g0 bridge 欠落がある。

### 3. 旧 branch の成果を merge/cherry-pick している、という疑い

(a) 主張  
「旧 branch の成果を使う」が merge の言い換えではないか。

(b) 根拠  

- [stage2-plan.md:283](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:283)
- [stage2-plan.md:294](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:294)
- 先行設計も再導出と明記: [calibration-freeze-joint-generation-design.md:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md:249)

(c) 構成  
旧 branch の commit/hash を取り込む手順、cherry-pick、merge は記載されず、test vector と考え方の再導出に限定されている。

(d) 判定: **refuted**

### 4. P3 が完全に誤りで、stage 4 以降をすでに完了判定できる、という疑い

(a) 主張  
plan の topology test が、先送り裁定まで決めている。

(b) 根拠  

- stage 6 は policy-specific acceptance を未定義としている: [stage2-plan.md:265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:265)
- policy 世代間変更も未定義: [stage2-plan.md:266](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-permanent-bundle-design/stage2-plan.md:266)

(c) 構成  
topology の静的 mutation は検査できても、unresolved profile の X は拒否される。したがって成功する activation の完了条件までは定義されていない。

(d) 判定: **refuted**。P3 は広すぎるが、policy-independent な一部まで未定義にする必要はない、という plan 側の修正要求は成立する。

## 総括

最も重い指摘は次の3件。

1. registered-inactive の世代型が validator・verdict・admission で消え、候補と active の区別を保てない。
2. S1/S2・G-a/G-b/G-c を開いたままにしたつもりでも、prediction binding、profile bytes、claim 時系列が schema に存在せず、実際には branch を実装できない。
3. E/F/B/Q の lineage と claim/journal/marker/budget/report の出口が閉じておらず、新 verifier が死んだコードになり得る。

結論は、**現 plan のまま後続実装へ進めてはならない**。docs-only の修正・追加裁定待ちであり、少なくとも上記3点が解消されるまで実装 wave の開始条件を満たさない。