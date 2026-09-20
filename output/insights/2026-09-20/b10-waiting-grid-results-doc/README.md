# B-10 待ち方 grid の正式走 (report phase `978195.nqsv`、D1678 で「現行 report で閉じる」) の単独 results 稿 — 1 判定の一次資料全体 (report 成果物・3 campaign の record / lock / WAL・受領証・発効版 blob・裁定) から書き、README の results 表へ 1 行足した (docs のみ、台帳 ID 未起票)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- wave: `worktree-dev-wave-b10-waiting-grid-results` (背景 job b5b405ac、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b10-waiting-grid-results/`)
- 起点 local main: `947fd160a` (着手直前の local main、fresh worktree、origin/main より 11 commit 先)。**実装面 (repo 内) の差分 0**
  (results 稿 1 本・paper-story README 表 1 行・本 insight・worklog fragment のみ)。変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定は 0 件。再解析も 0 件。** 凍結物 (report 成果物・事前登録・3 campaign の record / lock / WAL・受領証) の bytes は 1 byte も変えていない
- ユーザー依頼の確定事項: 一次資料は D1678 が指す 2026-09-07 記録の report phase の判定 (report・受領証・事前登録 §9・WAL) を段 1 で同定して sha256 束縛、
  書き方は `results/2026-09-16-b10-static-tail-not-observed.md` と同型、「本稿が判定しないこと」を最初に、事前登録 §9 の見送り 5 項目 (再訪 = 査読要求) と
  制約 3 つ (D1092 / D1094 / D1097) を限定として列挙、右 tail の 2 cohort と合成しない、機序は指示値の平均に限定 (依頼文の語。D1097 の語は
  「主張」であり、稿と README では「待ち量についての主張は指示値の平均に限定し、機序は述べない」と書いた — 段 6 所見 4)、README の results 表へ 1 行、
  段 6 = read-only レビュー 1 本 + 焦点再レビュー。scope 外 = 図・追加測定・右 tail 稿の改訂

## 1. 一行で

稿 `docs/paper-story/results/2026-09-20-b10-waiting-grid-formal.md` は、3 campaign × 45 cell = 135 cell の集約判定 (3 族 Holm すべて `different`、方向は
`symmetric-modulo` が高い側、36 cell の 95% 区間は等価域 ±3.0% の内側 32 / 境界を跨ぐ 4 / 区間全体が外側 0、判定不能 0 (点推定は 36 cell とも
内側)、性能 cell 135/135・検証 slot 270/270、
`official_certification` `false`) を report 成果物の逐語として写し、事前登録 §9 の 9 項目 (D1678 が見送った 5 項目を含む) と制約 3 つを先頭の限定に置いた。
稿の数値の出所は §4 の一次資料だけで、版 (`2026-09-20.md`) と insight は照合にしか使っていない。

## 2. 段 1 の一次資料の同定と実測 (親、2026-09-20 13:3x〜14:0x JST、login node、読み取りだけ)

- **D1678** (`docs/decisions.md`、2026-09-07): 「B-10 正式走は 2026-09-07 に記録した report phase の判定をもって閉じる。§9 の 5 項目 (過抑制域の機序、ピーク位置、
  `binary` を含む ladder、用量反応、独立追試) は起票せず見送る。再訪条件 = 査読で当該項目の提示を要求されたとき」。
- **記録**: worklog entry 1288 (`docs/archive/worklog-phase3-0907-1288.md`)、insight `output/insights/2026-09-05/t1905-b10-report/README.md`
  (旧 path `output/insights/2026-09-05_t1905-b10-report/` は commit `7d1194601` で日付 dir へ移動。`output/insights/layout-index/2026-09-05.md` に対応表)。
- **report 成果物** (repo 内 tracked): `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` (606,952 bytes、
  `schema_version` `b10-backoff-shape-provenance/v2`、`records[]` 135、`judgement`、`preregistration`、完全性 2 field) と同 dir の
  `b10_backoff_shape_report_978195.nqsv-23409962b76b.md` (31,133 bytes、135 行の表 + 判定)。sha256 は insight `t1905-b10-report` §1 の値と一致 (§3)。
- **事前登録 発効版 (v4)**: commit `77b33e37d2d63b1f83d10652792c3c93eba9fe8f` (2026-08-29) の `docs/b10-backoff-shape-preregistration.md`、git blob
  `ea910de32df83c1bb320cbe62344dc5fb3b94684`、35,820 bytes。§9 は **9 bullet** (過抑制域の機序 / ピーク位置の再現 / balanced workload の profile / 要求待ち量の
  分布の診断 / `binary` を含む ladder と用量反応 / 一般的な直交切り分け / 実要求待ち量・実待機時間の一致確認 / 乱数計算・撹拌器 overhead の分離 / 独立追試)。
  D1678 の 5 項目は bullet 1・2・5・9 に対応 (ladder と用量反応は 1 bullet)。作業ツリーの現行は v5 (39,278 bytes、2026-09-07 の artifact 束縛付け替え +
  §10 erratum) で、§0 に「v4 の下で完了した 135 cell は v4 のまま残る」。
- **report phase の投入** (repo 外 `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/23409962b76be959bb523a0cd5a31bc1/`): 受領証
  (`pegasus-b10-submit-receipt/v2`、request `978195.nqsv`、phase `report`、source `2a338449b`、prereg `77b33e37d`、job script sha `6f633ad0…`、
  `submitted_epoch` 1788581651 = 2026-09-05 13:14:11 JST、86,400 秒枠、gen_S)、job 結果 (`driver_rc` 0、`completed_epoch` 1788582054 = 13:20:54 JST)、
  `driver.stdout` 391 bytes (成果物 2 件の path)、`driver.stderr` 0 bytes。
- **3 workload campaign** (同 root `submissions/<nonce>/` と `official-output/campaigns/<id>/`):

  | workload | campaign | request | 投入 → 完了 (JST) | host | driver commit | 壁時計枠 |
  |---|---|---|---|---|---|---|
  | write-heavy | `…-write-heavy-formal-e3de15eb` | `965564.nqsv` | 09-01 21:02:12 → 09-02 01:05:47 | 未記録 (`not-recorded-legacy-v2`) | `0a07481b8` | 43,200 s |
  | balanced | `…-balanced-formal-143a3f74` | `974207.nqsv` | 09-03 20:29:45 → 09-04 00:09:45 | `bnode015` | `c7ed56589` | 43,200 s |
  | read-heavy | `…-read-heavy-formal-acf840c8` | `977647.nqsv` | 09-05 01:06:33 → 09-05 11:56:55 | `bnode088` | `2a338449b` | 86,400 s |

  各 campaign: record 封筒 45 file (`b10-backoff-shape-block-envelope/v1`、`record` + `record_sha256`)、`campaign.lock`、`runs/wal.jsonl` 135 行
  (build_start 15 + build_done 15 + verify_done 90 + commit 15)。verify_done は `workload.tag` legacy 15 + performance 75、全件 `certified` true・
  `verdict` serializable・`anomalies` 0。commit 行の `verify_configs` = `["legacy", "performance"]`、`verifier_evidence` 6 件、
  `commit_verification_receipt.lock_identity_sha256` = lock の sha256 (3 campaign × 15 行すべて)。record の `build_attempt_id` (各 15) は WAL に現れる。
- **事前登録束縛の一致**: 135 record の `preregistration_binding` は prereg commit / blob / spec sha (`9c594114…`) / patch sha (`36cd974c…`) / formula sha
  (`5b3d8dee…`) が 3 campaign で同値、`analysis_code_sha256` と `binding_sha256` が campaign ごとに違う (write-heavy `34072fb2…` / `f0f9b2a1…`、balanced
  `f6246360…` / `588aaa9c…`、read-heavy `b15c3548…` / `24d80d9a…`)。report の束縛は read-heavy と同値。旧 2 系列は D1588 (write-heavy、execution_host 不在を
  要求して射影) と D1636 項 4 (balanced) の限定受理で集約に入った。
- **legacy / performance の検査条件**: 固定 checkout (`2a338449b`) の `orchestrator/campaign/pipeline.py` — `CorrectnessWorkload` 既定 flag
  (4 thread・200 tuple・rr50・rmw true・max ope 5・extime 1、1 回) と `performance_correctness_workload` (性能条件と同一、5 回)。
- **祖先性**: `77b33e37d`・`2a338449b`・`0a07481b8`・`c7ed56589` はいずれも起点 main の祖先。解析コード sha `b15c3548…` = `2a338449b` の
  `orchestrator/campaign/b10_backoff_shape_sweep.py` blob の sha256。
- 活動を止める裁定は 0 件。関連する後続裁定 D1771 / D1834 (限定受理の束縛先を lock 記録値へ) は report の bytes を変えない (規律 7)。

## 3. 一次資料の sha256 照合表 (稿 §4 が全桁を委ねる表。親が現物から計算、手打ちなし)

repo 内:

| 資料 | sha256 |
|---|---|
| `output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json` | `a4390603f20fbc8fdb74c482a17ae880f292e340e79846c31f5d923d71789fca` |
| 同 dir `b10_backoff_shape_report_978195.nqsv-23409962b76b.md` | `e237d17db4f02818ea27049165fa90da4c19adea1bc8bca9b165b73b77e8e768` |
| 発効版 blob `ea910de32…` の内容 (35,820 bytes) | `f43997a7d2350a9bdcd53e34dbf9b4b0648c9c659dd6111d0adcd08d29d6bdb2` |
| `docs/b10-backoff-shape-preregistration.md` (現行 v5、39,278 bytes) | `7918bc12e60b48de56e0e0c3526f1b166e4e1bab9258bf1bf87bda567bfe847b` |
| `output/insights/2026-09-05/t1905-b10-report/README.md` | `18ec79f65c9ed687699f8b53bc97e8f863b346df0476d27a7afe787b32748b65` |
| `output/insights/2026-08-31_t1905-b10-formal-run/README.md` | `97ee119ef259a3b00eefc815a940b80944a621ab4ee1a329a5e4282be3b67eba` |
| `output/insights/2026-09-05/t1905-b10-trial-cell/README.md` | `d777fbae56c98500dbbaa40c1162d5e15ba97ba80a14de17672490ba7ad3dcb7` |
| `output/insights/2026-09-07/t1905-b10-readheavy-admit/README.md` | `73780ea912bcaddc8f031edb5c89130bc1c7cc592e60a576bab42c1bfe25f672` |

repo 外 (`/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/`):

| 資料 | sha256 |
|---|---|
| write-heavy 受領証 / job 結果 (`4911e336…` / `965564.nqsv`) | `002f7eb55ff1658422cfe77b6000100dc112e14ceb0037be22b4ded54671fb5d` / `b747bb47fed94f07bf23f80bedd1e67cca3e6208ca186d0a7aed12830460333d` |
| balanced 受領証 / job 結果 (`c42191d4…` / `974207.nqsv`) | `54748afd205895605a6005c1956e96a36c66ad1057a7bcd79d44cbc6782da75b` / `eaf8ade5d30f3770b6725882be1a66c17bff5cd1fb336026e746afc1cfd1efbe` |
| read-heavy 受領証 / job 結果 (`4537eb09…` / `977647.nqsv`) | `f055cf2dbc957b3cb9d21d5682b916cc691d2ecf8eb9229cb8ef9815a60e6ed0` / `11e1a4792c540f75b34996fd85d205f0ff5f5308c68bf0d3e0535d35aac91a1f` |
| report 受領証 / job 結果 (`23409962…` / `978195.nqsv`) | `93a1cd74ce279c6c8c876a7ab60fb772b216f25cf59f4eff70d0b0e2b8b429b4` / `d5d4a0ee4c503c1b4b6a811f998949f7a76434a575c4ed8d0bfad849eafd082b` |
| write-heavy `campaign.lock` / `runs/wal.jsonl` / record meta digest | `0a32c22b8afedd6b5542d0ec1da6cba713e55d77fd83cc878d173e568ee91674` / `e2c457291128fc53b990757dd54ae4fe61a5881fc9b66c03995ddbf0c87afc16` / `6cb14801e858cedd955d983267436585d75c713be48d79b50b0076fd99845b71` |
| balanced `campaign.lock` / `runs/wal.jsonl` / record meta digest | `087e46dfc825b4db6b1fba585e339f989ea94b8e68c14bbb9cb7088fa7ad86b9` / `ed78d48073047acd1543df886c11486260c4c8d08e780a07535553b2d33bec1d` / `8e5f0b48ba9e635e3d0e4e6c9c312c7436008dbe1a34f91a5763300920c37bad` |
| read-heavy `campaign.lock` / `runs/wal.jsonl` / record meta digest | `5abdfe110ac418b9d98a541ce7bfc3b4aa8975a97fbd6e82b5570f76330180b7` / `00e4f9408c5b4167a98dbdbcd3837da694e94133c609f58b315d5356f3e259fe` / `27195442abce632ffae7a7241abd3cd8e765fe63fb590a62a37d4166049400c8` |

record meta digest = 45 封筒の `record_sha256` を sorted して改行で連結し末尾にも改行を付けた ascii の sha256。read-heavy の値は
`t1905-b10-readheavy-admit` insight の meta digest と一致。3 workload の受領証 sha256 は各 45 record の `submission_receipt_sha256` と、
report の受領証 sha256 は provenance の `submission.receipt_sha256` と一致。

## 4. 親の機械照合 (job dir `artifacts/`、使い捨て script、出力は同 dir の `.out` / `.md`)

- `tables.py`: `judgement.families[].differences` 54 個は `records[].median_tps` から `symmetric-modulo / constant − 1` で再計算して全一致、順序は
  block-major (block-1 μ 2→100、block-2、block-3)。18 cell の `effect` = 3 block の平均、区間 = 平均 ± 4.302652729911275 × 標本標準偏差 / √3 で
  再計算して不一致 0 (許容 1e-9)。`equivalence_relation` の集計 = 内側 32 / 境界を跨ぐ 4 / 外側 0、単純再判定との不一致 0。`status` は全件 `estimable`。
  曝露は `backoff_call_count ≥ 10,000` で met 126 / indeterminate 9 (`none`)。`throughputs` 675 個、`unstable` 0、`cv` 最大 0.0336
  (balanced block-1 adaptive)、`settled` true は各 workload の block-1 `none` の 3 件、`performance_binary_sha256` / `build_attempt_id` は workload
  あたり 15 個ずつ相異。
- `sums.py`: raw p × 2^18 = 6702 / 70 / 2 (write-heavy / balanced / read-heavy)、Holm p × 2^18 = 6702 / 140 / 6。対差の和は 3 族とも正
  (+0.11203 / +0.13168 / +0.08773)、負の対差 5 / 2 / 0。
- `crosscheck.py`: 稿 §2.6 の 135 行 × 12 列 (中央値・CV・abort 率・abort 回数・呼び出し回数・毎秒呼び出し・名目総待ち量・認証・unstable・曝露) を
  report .md の表と key (workload, host, block, point) で照合して不一致 0。
- `claims_check.py`: 受領証 sha256 = record の `submission_receipt_sha256` (3 workload × 45)、report 受領証 = provenance の値、WAL commit 行 15 ×
  3 campaign の `verify_configs` / `verifier_evidence` 6 件 / `lock_identity_sha256` = lock sha256、record の `build_attempt_id` ⊆ WAL、いずれも一致。
- 自己点検で直した箇所 (レビュー前): `cv` 最大 cell の帰属 (balanced block-1 adaptive、登録 cell の最大は block-3 symmetric-modulo-mu5 0.0279)、
  §3 限定 2 の「残り 4 bullet」→ 5 bullet。
- `tools/check_docs.py` 違反なし。`git diff --cached --check` OK。三軸語走査 (`s8b_holdout_freeze search`) の hit は既存の holdout 候補 file 群のみで
  本稿・README は含まれない。

## 5. 段 6 — 独立 read-only レビュー 1 本と焦点再レビュー (codex `gpt-6-astra` / `medium`、read-only)

逐語は本 dir の `verbatim/` (`s6-review-1.md`、`s6-focus-1.md`、`s6-focus-2.md`。markdown の行末空白だけを除いた可逆正規化。原文 sha256・byte 数・
除去行数は `verbatim/whitespace-errata.json`、原文は job dir `codex/`)。

- **review 1** (14:08 → 14:16 JST、rc=0): **must-fix 3 / should-fix 3 / nit 1、「止める」。** 数値表・判定値・sha256 は全一致 (各族の全 2^18 符号反転を
  独立列挙して該当数 6702 / 70 / 2 を再現、54 対差・18 cell の効果と区間・36 cell の分類 32 / 4 / 0、135 行 × 16 列、WAL 135 件の内訳、3 meta digest、
  4 件の epoch → JST)。所見は数値を説明する散文に集中した:
  1. must-fix — 題名・§2.7「効果量は全 36 cell が等価域の内側か境界上」は区間の分類を誤って伝える (境界を跨ぐ 4 cell は区間の一部が外。例: write-heavy μ 2 の
     区間 [−3.29%, +4.78%])。→ 「95% 区間は内側 32 / 境界を跨ぐ 4 / 区間全体が外側 0、点推定は 36 cell とも内側」へ。
  2. must-fix — §2.6「μ が大きいほど abort 率が下がり throughput が下がる」は write-heavy で偽 (μ 2 → 5 で上がる)。→ 実測に基づく記述へ (§4 の `monotone.py`)。
  3. must-fix — 「3 workload は別 job・別 node・別日」は write-heavy の host 未記録なので確定できない。→ 「別 job・別日。balanced と read-heavy の host は
     異なり、write-heavy は未記録」へ (§0.1・§1.3・§3 限定 6・限定 15)。
  4. should-fix — README 行「機序は指示値の平均に限定」は D1097 の主語 (主張) と違う。→ 「待ち量についての主張は指示値の平均に限定し機序は述べず」へ。
  5. should-fix — §2.6 列説明「名目総待ち量 (参照点は無し)」は `zero-loop` = 0 に反する。→ 「`none` / `adaptive` は `null`、`zero-loop` は 0」へ。
  6. should-fix — §1.4 に D1588 が記録するもう 1 本の write-heavy campaign (45 件 SHA 不一致で測定不能、「選択の余地は無い」) の開示が無い。→ D1588 への帰属付きで
     追記 (独立監査していないと明記)。
  7. nit — README 行「台帳 ID 未起票」は稿にない運用情報。→ **refuted**: 同表の既存行 (K2 3 巡稿) と同じ表の運用欄で、稿の命題ではない。
  親の brief への異議: (P1)(P3) 異議なし、(P2) 集約単位は妥当だが「別 node」は導けない (所見 3)、brief の不変条件「機序は指示値の平均に限定」は D1097 の
  「主張」の置換 (所見 4)。裁定: 1〜6 real 採用、7 refuted。修正は job dir `artifacts/fix_r1.py` (稿 11 + README 1、exact 置換)。観点 16 の任意提案 (3 種の job
  script sha256) も §1.3 に 1 文追加。
- **focus 1** (14:20 → 14:23 JST、rc=0、`DW-O16` の対応表): **closed 6 / partial 1 / regressed 0、新規 must-fix 1 + should-fix 1、NO-GO。** 親が新たに書いた
  派生値 (a)〜(g) は独立再計算で全一致 (abort 率 18 系列の狭義単調減少、read-heavy 6 系列の単調減少、最大 μ の表、`adaptive` < 登録 12 cell 最小 × 9 block、
  write-heavy μ 2 の区間、点推定 36 cell の内側、job script sha256 3 種)。新規所見: (1) must-fix — §2.6「balanced では μ 2 または μ 5 が最大で単調ではない」は
  過剰一般化 (balanced は 6 系列中 4 系列が狭義単調減少、2 系列が非単調)。→ 系列を名指して書き分けた。(2) should-fix — 本 insight の冒頭「機序は指示値の平均に
  限定」と §1 / §4 の「境界 4」が修正前の表現のまま。→ 依頼文の語であることを明記し、区間と点推定を区別した表現へ。修正は `artifacts/fix_r2.py` (稿 1 + insight 3)。
- **focus 2** (14:25 → 14:26 JST、rc=0、射程は前巡の新規所見 2 件): **closed 2 / regressed 0、新規所見なし、GO。** (a) balanced の狭義単調減少は
  4 系列のみ、(b) 残り 2 系列は μ 5 で一意に最大 (4,200,819 / 4,199,083 tps)、(c) write-heavy 6 系列は非単調、(d) read-heavy 6 系列は狭義単調減少 —
  いずれも `records[].median_tps` からの独立再計算で一致。修正文は「機序でも採用根拠でもない」と明記され、新たな優劣・推奨を持ち込んでいない。
- 段 6 の費用: codex 3 本 (review 1、focus 2)。3 巡は `DW-O16` の上限内で、残る所見は 0。

## 6. 段 7 以降の記録と運用の気づき

- 3 巡の所見はすべて「数値は合っているが、数値を説明する散文の量化が一次資料に当たっていない」型だった (F1 の near-miss 再発として failures fragment に記録)。
  機械照合 (表・対差・区間・sha256) は散文の量化を検査しない。次の単独 results 稿では、量化語 (「すべて」「単調」「別 X」「上」) を書く前に record から
  機械で確かめる script (本 wave の `monotone.py` 相当) を段 5 の起草時点で回す。
- README は `--owned-path` に入れず、peer 通知 (T-2610 wave の land で main が `947fd160a` → `d4af98f15`) は自分の ref で読み直した。README の差分は
  2026-09-19 の B-7 行の書き換えと stale 注記で、本 wave の挿入位置 (results 表の最終行 = K2 3 巡稿の直後) とは別位置。
- 受入・land の結果は job dir (`acceptance-*.log`、`land-*.json`) と land の受領証に残す。本 insight には書かない。
