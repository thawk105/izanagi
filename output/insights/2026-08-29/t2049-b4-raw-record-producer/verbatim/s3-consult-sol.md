## 重大な所見

### 1. `precursor_hash` の検査が恒真になっている

- **所見:** 両 arm の `precursor_hash` を同じ registry 行から生成するため一致検査は常に通る一方、その hash と実際に実行された campaign の precursor は束縛されない。
- **場所:** [s2-plan.md:406](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:406>)、[s2-plan.md:332](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:332>)、[p3_b4_analysis_ledgers.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:182)
- **なぜ欠陥か:** manifest block の registry 値を `H1`、on/off receipts が共有する実 WAL snapshot を `H2` とする。`H1 != H2` でも plan は source の両 arm に `H1` を書き、`initial_snapshot_sha256` は arm 間で `H2` が一致するので `contaminated=false` にする。request は proposal bytes/path を受けず、launcher sidecar にも attempt id や `initial_proposal_sha256` がないため、`H1` と `H2` の関係を検査する分岐が存在しない。
- **成果物への影響:** manifest が選んだ母集合とは別の precursor の結果を当該 block として受理でき、受理集合と B-4 verdict の両方を動かせる。
- **real / 要確認:** real（高）。

### 2. `assignment_observation` は実行 slot ではなく caller の append 順である

- **所見:** plan は実行順を観測せず、source artifact の publish 呼出順を無作為化 schedule 遵守の権威にしている。
- **場所:** [s2-plan.md:379](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:379>)、[s2-plan.md:418](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:418>)
- **なぜ欠陥か:** schedule が `[off,on]` なのに実走が `[on,off]` だった block でも、caller が off source を先に append すれば raw は `[off,on]` となり `assignment_followed=true` になる。逆に schedule どおり起動した並列 arm が逆順に完了して即 append されると、正しい走行を違反にできる。
- **成果物への影響:** 本来の protocol violation を成立・不成立へ進めたり、正しい標本を protocol violation に変えたりできる。
- **real / 要確認:** real（高）。

### 3. 事前発行された result path を無視するため file-drawer が残る

- **所見:** producer API は pre-run publication/receipt を受けず、caller が任意の `record_root` と registry/manifest bytes を組み合わせられる。
- **場所:** [s2-plan.md:110](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:110>)、[p3_b4_prerun_issuer.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_prerun_issuer.py:3)、[p3_b4_prerun_issuer.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_prerun_issuer.py:406)
- **なぜ欠陥か:** issuer が attempt `A` の result を `/planned/A` に固定しても、plan の API にはその対応表も issuer receipt も入らない。結果を見た後で `/chosen` を `record_root` として有利な campaign を書き、不利な `/planned/A` を空のままにしても、producer と consumer は同じ registry/manifest bytes を与えれば受理する。
- **成果物への影響:** 不利な実走を受理集合から落として有利な raw 文書だけを評価でき、verdict と全件報告を動かせる。
- **real / 要確認:** real（高）。

### 4. 同一の実試行を複数 block へ複製できる

- **所見:** final assembly は slot/source artifact の個数と source 自身の hash 一意性しか要求せず、campaign・iteration・consumed receipt の block 間再利用を拒否しない。
- **場所:** [s2-plan.md:385](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:385>)、[s2-plan.md:408](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:408>)、[s2-plan.md:491](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:491>)
- **なぜ欠陥か:** 1 件の有利な on 実行と不利な off 実行を、同じ campaign root・receipt・consumption record のまま異なる 201 個の `block_id` で append できる。source bytes は block binding と registry 由来 `precursor_hash` が異なるので sha256 は全件異なり、既存の source hash 重複検査にも当たらない。
- **成果物への影響:** 1 組の観測を最大 201 block の独立標本として数えられ、符号検定と B-4 verdict を任意方向へ動かせる。
- **real / 要確認:** real（高）。

### 5. arm ごとの local pair 検査は、最終 block の on/off pair を束縛しない

- **所見:** on source と off source が別々の receipt pair・admission record・model/prompt から来ても、各 append 内の `assert_b4_arm_pair` だけを通して最終 block に合成できる。
- **場所:** [s2-plan.md:72](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:72>)、[s2-plan.md:395](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:395>)、[s2-plan.md:332](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:332>)
- **なぜ欠陥か:** on は pair `P1` の selected receipt、off は同じ precursor snapshot 上で作った別 pair `P2` の selected receiptを使う。各 request は自分の peer と組めば通るが、source schema は `pair_id` を持たず、assembly は on/off の selected/peer receipt 対応や admission record、model、prompt の cross-arm 一致を検査しない。snapshot hash だけ同じなら `contaminated=false`、各 local check が pass なら `protocol_ok=true` になる。
- **成果物への影響:** 複数 pair から都合のよい on/off を選ぶ receipt shopping と model/prompt 交絡が残り、その差を treatment 効果として verdict に入れられる。
- **real / 要確認:** real（高）。

### 6. crash と入口停止の分類は artifact から識別不能である

- **所見:** 「consumption 済み・WAL suffix 無し・iteration 不変」を `stopped-before` とする条件は、receipt 消費後かつ最初の WAL write 前の crash と同一である。
- **場所:** [s2-plan.md:341](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:341>)、[p3_s4_loop.py:1518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1518)、[p3_s4_loop.py:1556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_s4_loop.py:1556)
- **なぜ欠陥か:** `consume_b4_iteration_authorization()` の直後、`check_stop()` が continue を返してから最初の WAL frame 前に process が落ちると、永続物は consumption record、旧 iteration、WAL suffix 無しである。plan の stopped-before 条件と区別できず、newline 未終端時だけを crash とする規則ではこの crash を拾えない。
- **成果物への影響:** raw status はどちらも `missing` だが、§7.1 が要求する crash・停止理由・予算消費の報告が誤る。
- **real / 要確認:** real（高）。

### 7. `anomaly_class` が treatment precursor ではなく treatment 後の ABORT reason を表す

- **所見:** source schema は registry の `digest_red_classes` を落とし、`anomaly_class` に WAL terminal reason を入れるため、D824 の詳細 anomaly と別の量を報告する。
- **場所:** [s2-plan.md:144](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:144>)、[s2-plan.md:213](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:213>)、[s2-plan.md:273](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:273>)、[verbatim-d824.md:8](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/verbatim-d824.md:8>)
- **なぜ欠陥か:** precursor が `verify-red` と `liveness` を持ち、両 arm の次 synthesis が COMMIT した場合、plan は `anomaly_class=null` とする。逆に次 synthesis が無関係な理由で ABORT すると、その後段 reason を precursor anomaly class として記録する。
- **成果物への影響:** primary verdict は変わらないが、§7.1 の各行報告と「どの詳細 anomaly の増分効果か」という B-4 報告が虚偽になる。
- **real / 要確認:** real（高）。

### 8. §7.1 が要求する model hash が schema にない

- **所見:** `model_snapshot` は非空文字列であって hash ではなく、source artifact は model hash を保持しない。
- **場所:** [s2-plan.md:183](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:183>)、[s2-plan.md:264](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:264>)、[verbatim-prereg-7.md:8](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/verbatim-prereg-7.md:8>)
- **なぜ欠陥か:** receipt の `model_snapshot="..."` をそのまま保存すると model identifier は残るが、§7.1 の `model/prompt/projection hash` のうち model hash は存在しない。raw schemaにもこれらは投影されないため、後段で復元できない。
- **成果物への影響:** verdict は直接変わらないが、各行の必須報告項目が欠落し、cross-arm model 同一性の監査もできない。
- **real / 要確認:** real（高）。

### 9. ledger が許す正当な ratio を producer が新たに拒否する

- **所見:** ledger は任意の正の既約有理数を `reference_tps` として受理するが、plan は有限十進でない値を producer 固有の拒否へ落とす。
- **場所:** [s2-plan.md:361](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:361>)、[p3_b4_analysis_ledgers.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_analysis_ledgers.py:263)
- **なぜ欠陥か:** `reference_tps=[1,3]` は ledger/manifest の値域に適合し、完全性再生成も通る。しかし JSON number token で `1/3` を exact に表せないため plan は `decimal_not_terminating` で拒否し、正当な 201-row manifest から raw を作れない。
- **成果物への影響:** 事前登録上は適格な母集合が producer 追加条件で実行不能となり、raw artifact と verdict が永久に生成されない。
- **real / 要確認:** real（契約上は確定。将来の実 registry で非有限十進が現れるかは要確認）。

## nit

### binary float を「経由しない」という記述は字義通りには成立しない

- **所見:** WAL frame を最初に `wal.parse_line()` へ渡すため、`fitness_tps` を含む数値は一度 Python `float` に decode される。
- **場所:** [s2-plan.md:134](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:134>)、[s2-plan.md:359](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:359>)、[wal.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/wal.py:327)
- **なぜ欠陥か:** 同じ bytes の二度目の parse で lexeme を保存するので出力 token 自体の float round-trip は避けられるが、「binary float を経由させない」という plan の保証は前段 schema gateには当てはまらない。
- **成果物への影響:** 現計画だけから token 変化の系列までは示せないため、verdict 影響ではなく保証文の過大記述に留まる。
- **real / 要確認:** real（低影響）。

### 統合正例が authority 分岐を一度も通らない

- **所見:** 201 block の唯一の統合正例が全 arm 未到達であり、実行済み arm の treatment・protocol・contamination・throughput 導出を実証しない。
- **場所:** [s2-plan.md:451](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s2-plan.md:451>)
- **なぜ欠陥か:** 全 source が `terminal-record-absent` なら、難しい外部証拠の束縛を一切成功させなくても 402 件組立てと `indeterminate` まで到達する。
- **成果物への影響:** 実装が実行済み campaign を全拒否しても plan の代表的な E2E 成功条件を満たせる。
- **real / 要確認:** real（テスト計画上）。

## 親 brief 自身の欠陥

### 親 brief も registry 値の転記と実 precursor の束縛を取り違えている

- **所見:** brief は `initial_proposal_sha256` を「唯一の権威」とするだけで、campaign/WAL/receipt がその proposal から生じたことを要求していない。
- **場所:** [s1-brief.md:65](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s1-brief.md:65>)、[s1-brief.md:93](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s1-brief.md:93>)
- **なぜ欠陥か:** producer が registry の `H1` を正確に写しても、実行対象 snapshot が `H2` なら母集合束縛は破れている。brief の P1-b は「定数を書けば通る」だけを攻撃し、「正しい registry 値を無関係な試行へ貼る」経路を落としている。
- **成果物への影響:** brief に忠実な実装でも別 precursor の outcome を受理し、verdict を動かせる。
- **real / 要確認:** real（高）。

### 既存 pre-run issuer の commitment を入力契約から落としている

- **所見:** brief は sealed registry/manifest だけを入力とし、既に存在する issuer receipt と全 scheduled attempt の planned result mapping を producer の束縛対象にしていない。
- **場所:** [s1-brief.md:45](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s1-brief.md:45>)、[p3_b4_prerun_issuer.py:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_prerun_issuer.py:8)
- **なぜ欠陥か:** issuer 自身が `formal_launcher_not_wired_to_require_this_receipt` と `caller_result_paths_are_not_proven_formal_producer_paths` を明示しているのに、brief はその開口を producer scope へ伝えていない。その結果、plan は任意の `record_root` を採用した。
- **成果物への影響:** 事前に予定した結果 path と実際に評価する raw artifact が分離し、file-drawer と結果選択が残る。
- **real / 要確認:** real（高）。

### 「402 campaign root」という前提は現 launcher の identity と一致しない

- **所見:** brief は 201×2 個の campaign root を前提にするが、現 launcher は proposal/block/attempt を campaign identity に入れず、driver と arm の固定 config から campaign id を導く。
- **場所:** [s1-brief.md:96](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2049-b4-raw-record-producer/s1-brief.md:96>)、[p3_b4_launcher.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_launcher.py:523)、[p3_b4_launcher.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2049-b4-raw-record-producer/orchestrator/campaign/p3_b4_launcher.py:580)
- **なぜ欠陥か:** campaign id は proposal path を driver へ渡す前に固定 config から決まり、proposal path は identity field ではない。同じ driver/arm の複数 block は同一 root の別 iterationになりうるため、「root 1 個が arm 試行 1 件を同定する」という brief の設計根拠が成立しない。
- **成果物への影響:** block/iteration の同定が抜けたまま同一 root の観測を再利用でき、受理集合と verdict を汚染する。
- **real / 要確認:** real（高）。

## 総括

plan は D1240 の「分類と commit receipt 検証に同じ lock bytes を使うこと」と固定 absence digest、off receipt を一律 false にしない点、screening を treatment に足さない点は守っている。

しかし主要な正しさ境界は閉じていない。`precursor_hash` は実 campaign との束縛がなく恒真、割当遵守は append 順、result path は issuer commitment から切断され、同一試行の複製と cross-pair shopping が可能である。この状態では producer が作る 201 block は「事前固定した 201 個の試行」ではなく「registry のラベルを付けた 201 個の選択可能な証拠」になるため、B-4 verdict の権威 producer としては受理できない。静的検査のみで、pytest は実行していない。