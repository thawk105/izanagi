# [T-2792] A-1 balanced5 sized attempt-0002 (認可済み独立再現) — 認可 record の作成・投入・完走・受領証・results 稿の記録 (2026-09-20)

- authority: none
- default_effect: no-state-change
- 裁定: D2172 項 2 (2026-09-20、択 1 = exact な認可 record を gate の入力に取り、attempt-0002 を 1 attempt 限定で認可。研究目的 = 同一配置
  (同 seed・同物理順) の反復)。gate の設計は D2178 (commit `886c19259`)、追補 (事前登録 §6.1 / §6.4 の別版) は commit `ec696308a`。
  依頼文の逐語は `verbatim/T-2792-origin.md`。
- 対象 study: `paper-story-a1-20260901-balanced5-sized-v1` (policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`、sha256
  `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`; 事前登録 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`、
  sha256 `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`)。attempt-0001 は 2026-09-18 (entry 1636、稿は entry 1680 で着地した
  `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`)。
- **本 wave は認可 record の作成・投入・待ち・complete・materialize・results 稿・記録だけを行った。実装面の差分はゼロ (変異 matrix 免除)。**
  事前登録・policy・source 契約・追補・patch・job body・attempt-0001 の公開 leaf と稿と図 9 の bytes は変えていない。gate 緩和・先行 attempt の
  証拠移動・policy / base の変更は行っていない。
- 成果物: (1) 公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` (README.md / receipt.json / result.json /
  .complete.json、materializer が submit-tree に排他作成したものを byte 保持で複製、sha は `.complete.json` と一致)、(2) results 単独稿
  `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` (attempt-0001 稿の値を §2.7 に並記、プールしない)、
  (3) `docs/paper-story/README.md` の results 表へ 1 行、(4) 本 dir (受領証・逐語・検算)。
- この文書は記録であって、A-1 の充足・formal 化・昇格・attempt 間の再現性・3 本目の認可のいずれも判定しない (§6)。

## 1. 結論 (1 行ずつ)

1. **全層が実機で通った。** authorize-rerun rc 0 (18:10:34 JST) → submit rc 0 (18:11:16 JST) → 3 job とも driver rc 0 / shell rc 0 / status
   `finished` (18:22:12 / 18:25:34 / 18:28:57 JST) → complete rc 0 (18:30:06 JST) → materialize rc 0 (18:30:21 JST、兄弟 dir)。親が実行した
   4 command (authorize-rerun / submit / complete / materialize) の stdout / stderr はいずれも 0 bytes (job dir の `*.stdout` / `*.stderr`)。3 job の
   scheduler stdout は 885 / 875 / 881 bytes、stderr は 557 / 556 / 556 bytes (`receipts/job-std*-*.txt`)。attempt root の `receipts/` には
   submission.json と completion.json だけがあり failure 受領証は無い。どの層も落ちなかったので、停止条件 (再投入せず報告して止める) は発動していない。
2. **認可 record と gate は設計どおりに働いた。** record (`attempt-0002.authorization.json`、`source_commit` = submit-tree HEAD `fec4a8187`) を置いた
   状態で、attempt-0001 が bench 到達済みの base に対する同 study の group 投入が受理され (rear gate の解除)、materialize の公開先 gate は
   兄弟 dir `…-attempt-0002` を受理した。record は投入日でなく定数値 `2026-09-20` を `decided_on` に持つ (今回は投入日と同じ日付)。
3. **3 workload とも `valid=true` / `errors=[]`、`complete=true` / `all_workloads_terminal=true`、各 30 対。** 6 arm の verifier は全て
   `serializable … 0 anomalies` (規律 2 の判定は既存 verifier のまま)。
4. **登録済み解析の分類は 3 workload とも `resolved-above-floor`** (B = baseline 平均の 3%)。符号は write-heavy 正、balanced 正、read-heavy 負。
   **`variance_plan_breach` は write-heavy と read-heavy で true** (標本 sd が計画 sigma の 1.207 / 1.081 倍。balanced は 0.872 で false)。
   分類は breach の有無で変わらない (mean・h・B だけで決まる)。
5. **登録した同一配置で測定された**: schedule receipt の `root_seed` / `effective_root_seed` / `seed_counter` / `group_bits` / block の arm 順 12 個が
   3 workload とも attempt-0001 と一致。campaign id も同じ。異なるのは node (bnode035 / 039 / 040 対 107 / 108 / 109)、時刻帯、bench 相の順序
   (balanced → read-heavy → write-heavy 対 read-heavy → write-heavy → balanced)、source commit (driver 1 本の 143 行追加・3 行削除 = 認可 record の生成・照合、
   submit / materialize への接続、CLI 分岐)。
6. **これは `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` の非認証 lane の結果である。**
   workload をまたぐ結論・2 attempt のプール・再現判定は作らない (事前登録 §7.2、D1993 項 6)。
7. 再投入はしていない (認可は attempt-0002 の 1 attempt のみ)。sized の attempt は 2 本 (attempt-0001、attempt-0002) で、attempt-0001 の公開先と
   pilot の公開先には何も書き足していない。

## 2. 投入の形 (attempt-0001 と同形、差は認可 record と兄弟 dir)

### 2.1 経路

- submit-tree: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree` = local main `fec4a818741e5464fffcd11e4b094c125dfe5280`
  の detached worktree (着手直前の local main)。submodule 再帰初期化 (ccbench `511c9538` / shirakami `fb14e659` / googletest `f8d7d77c`)、
  `status --porcelain --untracked-files=all --ignore-submodules=all` は作成直後・hydrate 後とも 0 行、`git worktree lock`。投入後は submit-tree の
  既存 tracked bytes を変えていない。書き込みは materialize が新規 leaf (兄弟 dir) へ出力したものだけ。記録用 wave worktree (`.claude/worktrees/dev-wave-t2792-a1-sized-attempt2`、同じ SHA) と分離。
- hydrate (`tools/pegasus/fetch_third_party.py hydrate`、cache `/work/1/SFC/tanab/izanagi-thirdparty-cache`、5 本とも pin 一致): (a) submit-tree の
  既定 staging root、(b) job dir `third-party-hydrated` (`--third-party-source-root`)。`verbatim/hydrate-default.json` / `verbatim/hydrate.json`。
- 起動 script (`run-hydrate.sh` / `run-authorize.sh` / `run-submit.sh` / `run-watch.sh` / `run-stepc.sh` / `run-stepm.sh` / `detach.sh`) と
  抽出・検算 script (`extract.py` / `draft_check.py` / `compare_schedule.py` / `compare_binding.py` / `raw_vs_leaf.py` 等) は実行可能 script なので
  repo へは複製せず job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/` に残す (逐語は `verbatim/*.py.txt`)。argv は以下に逐語で写す。
- authorize-rerun (`run-authorize.sh`、submit-tree を cwd に): `python3 -B -m orchestrator.campaign.paper_story_a1_paired authorize-rerun --study-id
  paper-story-a1-20260901-balanced5-sized-v1 --attempt-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002
  --expected-head fec4a818741e5464fffcd11e4b094c125dfe5280 --decision D2172 --decision-item 2 --decided-on 2026-09-20` (entry 1736 / 認可 wave
  insight §1 項 5・8 の逐語。`--decided-on` は定数 `V3_SIZED_RERUN_AUTHORIZATIONS` の値)。
- submit (`run-submit.sh`): `python3 -B -m orchestrator.campaign.paper_story_a1_paired submit --study-id paper-story-a1-20260901-balanced5-sized-v1
  --expected-head fec4a818741e5464fffcd11e4b094c125dfe5280 --attempt-root <上の attempt root> --third-party-source-root
  /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/third-party-hydrated`。
- complete (`run-stepc.sh`): `… complete --study-id … --expected-head fec4a8187… --attempt-root <attempt root>`。
- materialize (`run-stepm.sh`): `… materialize --expected-head fec4a8187… --raw-result <attempt>/raw/results/result.json --raw-receipt
  <attempt>/raw/results/receipt.json --job-terminal <attempt>/raw/job-terminal.json --completion-receipt <attempt>/receipts/completion.json
  --destination <submit-tree>/output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002` (attempt-0001 と同じ argv 形、宛先だけ兄弟 dir)。
- 監視 (`run-watch.sh`): 60 秒ごとに `qstat` 一覧の行頭 RequestID で 3 request の生存を見て、全消滅で終了 (`verbatim/watch.log`)。待ち手は
  `tools/dev_wave_wait.py producer` 1 本。

### 2.2 attempt-0001 との差

- 認可 record (base 直下 `attempt-0002.authorization.json`、sha256 `8204f9759e51fc2b357fbad5d7edaf5464974fc1cee2e4862749d4598c43d685`) を submit の
  前に置いた。attempt-0001 には無い。
- materialize の宛先が兄弟 dir。attempt-0001 の leaf (policy の `materialization_relative_path` そのもの) は既存のまま。
- source commit が `d2ebef7a4` → `fec4a8187`。束縛 9 file のうち driver 1 本だけが異なり (`886c19259` の +143 / −3。変更行の所属 (新版の AST で帰属): module 定数 (`V3_SIZED_RERUN_AUTHORIZATIONS` 等) 15 行、新設した `_exact_v3_rerun_authorization` (51 行) / `_rerun_authorization_digest` (4 行) / `run_authorize_rerun` (41 行)、既存の `_assert_no_prior_v3_bench_start` (8 行) / `_run_submit_v3` (1 行) / `_exact_materialization_destination` (15 行) / `_run_materialize_v3` (2 行) / `_parser` (4 行) / `main` (2 行)。合計 143 行。
  推定量・分類・測定の関数に変更行は無い)、他 8 本は bytes 同一 (`verbatim/extract-attempt2.md` と稿 §1.5)。

## 3. 時系列 (JST、`date` / mtime / NQSV accounting / WAL ts から。推定値なし)

| 時刻 | 事象 | 出所 |
|---|---|---|
| 18:04:06 | wave worktree 作成 (HEAD = local main fec4a8187、clean)、開始 gate rc 0 (18:05) | `date`、`verbatim/startup-gate.log` |
| 18:08:34 | submit-tree 作成完了 (detached)、submodule 初期化、lock | dir mtime |
| 18:09:45 / 18:09:49 | hydrate 2 箇所 rc 0 | `verbatim/hydrate.log` |
| 18:10:34 | authorize-rerun rc 0、record 作成 | `verbatim/authorize.log`、record mtime |
| 18:11:15 → 18:11:16 | submit rc 0 (intent 18:11:15、submission 受領証 18:11:16)、qstat 可視性 `QUE` 18:11:15 | `verbatim/submit.log`、受領証 mtime、`receipts/qstat-visibility-*.json` |
| 18:11:15 / 18:11:16 | request 作成 13220 (write-heavy) / 13221 (balanced) / 13222 (read-heavy) | job.stderr の NQSV accounting |
| 18:11:23 / 18:11:23 | write-heavy (bnode035)・read-heavy (bnode040) 開始 | 同上、receipt `accounting.started_epoch_s` |
| 18:11:16 → 18:16:47 | balanced (bnode039) は request 作成 (18:11:15) から開始 (18:16:47) まで記録上 5 分 31 秒。投入直後の `qstat -f` は Pre-running (遷移 18:11:16)、監視 log は 18:12:11〜18:16:12 に PRR、18:17:12 に RUN | `qstat -f 13221.nqsv` (Current State = Pre-running、State Transition Time 18:11:16、Execution Hosts bnode039)、NQSV accounting、`verbatim/watch.log` |
| 18:13:22 | ready barrier write-heavy / read-heavy (両 arm の build + verify 完了) | `receipts/barrier-ready-*.json` mtime |
| 18:18:44 | ready barrier balanced、bench-go、bench-start 3 本同時 | `receipts/barrier-ready-balanced.json` / `bench-go.json` / `barrier-bench-start-*.json` mtime |
| 18:18:44 → 18:22:07 → 18:25:29 → 18:28:52 | bench 相が balanced → read-heavy → write-heavy の順に直列 (bench lock)。`schedule_wall_s` 202.64 / 404.95 / 607.07 | WAL `ts`、schedule receipt |
| 18:22:12 / 18:25:34 / 18:28:57 | job 終端 balanced / read-heavy / write-heavy (driver rc 0)。NQSV Elapse 329 / 856 / 1058 S | `receipts/job-terminal-*.json` mtime、NQSV `Ended Request Time` |
| 18:29:14 | 監視が 3 request の消滅を観測、待ち手 rc 0 | `verbatim/watch.log` |
| 18:30:05 → 18:30:06 | complete rc 0 (receipt `recorded_epoch` 18:30:05) | `verbatim/stepc.log`、receipt.json |
| 18:30:21 | materialize rc 0 (公開 leaf 4 file、兄弟 dir) | `verbatim/stepm.log`、leaf mtime |

投入から全終端まで 17 分 41 秒 (18:11:16 → 18:28:57)、balanced の scheduler 待ちを含む。materializer の accounting は CPU 合計 9080.5 / 9081.9 /
9108.7 s、elapsed 1050.02 / 321.32 / 847.45 s。attempt-0001 は 13 分 (06:30 → 06:43)。

## 4. 3 job と受領証

| workload | request | node | intent 内 arm | verify (variant / baseline) | driver rc | scheduler terminal |
|---|---|---|---|---|---|---|
| write-heavy | `13220.nqsv` | bnode035 | fixed10 / no-backoff | serializable 0 anomalies (458889 commits) / 0 anomalies (510621 commits) | 0 | `request-disappeared-after-visibility` |
| balanced | `13221.nqsv` | bnode039 | fixed5 / no-backoff | 0 anomalies (481088) / 0 anomalies (509412) | 0 | 同上 |
| read-heavy | `13222.nqsv` | bnode040 | fixed2 / no-backoff | 0 anomalies (471051) / 0 anomalies (523733) | 0 | 同上 |

- 認可 record: schema `paper-story-a1-paired-rerun-authorization/v1`、`source_commit` `fec4a8187…`、`decision` `{D2172, 2, 2026-09-20}`、
  `authorization_sha256` `9ccd38c995d225d151e4572c7f878f908f46ff90f0a95b886cc20819e152e40c` (`receipts/attempt-0002.authorization.json`)。
- submission 受領証: schema `paper-story-a1-paired-group-submission/v1`、route `direct-qsub-workload-fanout`、intent sha256
  `6bc38262ad4d309154808c234ad601394e4872c2e87f224c91b684c868c897ea`、3 request とも投入直後の qstat 可視性 `QUE` / queue `gen_S`。
- completion 受領証: schema `paper-story-a1-paired-group-completion/v1`、group terminal `raw/job-terminal.json` sha256
  `a9bc5f9a150533fd3900140bd2dea1b307c9706e2862158a3a98499a6af6cb38`。scheduler terminal は 3 本とも「投入時に可視、終端後に qstat から消失」形
  (state / exit_status は未観測として記録、成功は driver_rc=0 / shell_rc=0 / status=finished で独立に確定)。
- 公開 leaf `.complete.json`: README.md `034cd1fd2f5004b1faac27d7e5e629a88c29f1e89dfd5fd1af9e6eadc50b53a1`、receipt.json
  `98c35cca4fe0e9f12559b8f9dc3acb4c6c5c4c597e5f5cc01a6449533918ecbf`、result.json `b7e0518e197500f2daf875e841acabf63f5eddb82bc14e072dd28e3431fe5f74`。
  publish 機構は `a1-exclusive-claim-check-then-renameat2` (attempt-0001 と同じ fallback)。
- result.json: schema `paper-story-a1-paired-result/v3`、`policy_sha256` = 上の policy sha、`source_binding.evidence_level = source-routed-trace0`、
  束縛 file 9 本 (attempt-0001 と同じ集合、driver 以外は同じ working sha256)。
- 各 file の byte 数・mtime・sha256 は `MANIFEST.tsv`。複製は `receipts/` (認可 record / intent / submission / completion / group terminal / 各 job
  terminal / barrier 7 本 / non-certifying observation / qstat visibility 3 本 / 各 job stdout・stderr)。campaign.lock / WAL / schedule receipt は
  複製しない (原本 path と sha256 は `receipts/non-certifying-observation.json` と稿 §5.2 が持つ)。

## 5. 登録済み解析の出力 (公開 leaf の result.json の値を表示桁に丸めたもの。descriptive のみ。逐語は稿 §2.1)

| workload | contrast | n | 対差平均 (variant − baseline) tps | 記述区間 tps | B tps (3%) | baseline 平均 tps | 標本 sd / 計画 sigma | 分類 | breach |
|---|---|---:|---:|---|---:|---:|---|---|---|
| write-heavy | fixed10 − no-backoff | 30 | +1,538,451.47 | [1,497,017.256, 1,579,885.678] | 72,952.123 | 2,431,737.433 | 80,148.44 / 66,403.45 (1.207) | resolved-above-floor | true |
| balanced | fixed5 − no-backoff | 30 | +548,138.23 | [522,585.849, 573,690.618] | 110,832.746 | 3,694,424.867 | 49,427.36 / 56,697.44 (0.872) | resolved-above-floor | false |
| read-heavy | fixed2 − no-backoff | 30 | −560,565.60 | [−602,312.344, −518,818.856] | 305,064.861 | 10,168,828.700 | 80,752.99 / 74,668.49 (1.081) | resolved-above-floor | true |

- 30 対の生値からの再計算 (mean / sd / h / B / 分類、全 30 対の差の一致、raw と arms の一致) と、WAL / campaign.lock / schedule receipt の現物
  digest と記録値の比較は `verbatim/extract-attempt2.md` に記録した。`verbatim/draft-check-1.txt` の 113 項目 ok / 問題 0 は、稿中の sha256 全件が
  既知集合 (leaf 4 file・raw・受領証・intent・認可 record・WAL 現物の再計算値と、result.json / receipt / policy / 束縛 file / schedule receipt の
  記録値) に属すること、§2.1 / §2.7 / §2.2 / §2.3 / §2.4 / §1.4 の値が稿中に逐語で存在すること、seed / group_bits / block 順が attempt-0001 と
  一致することの機械照合の出力であり、表の行への帰属や散文の量化語は保証しない。raw と公開 leaf の result.json の差は
  `materialization_evidence` と `limitations` 5 項目めだけ (`verbatim/raw-vs-leaf.txt`)。
- 派生値 (登録量ではない): 対差平均 / baseline 平均 = +0.633 / +0.148 / −0.055。符号は attempt-0001 (+0.694 / +0.116 / −0.056) と同じだが、
  **2 attempt をプールせず再現判定もしない** (稿 §2.7)。

## 6. 言わないこと

- **A-1 の充足・formal 化・昇格は判定しない。** policy は `formal=false` / `promotion_prohibited=true` のままで、これは事前登録・policy・追補の編集だけで
  反転させない。
- **attempt 間の再現性・反復間の安定性 (attempt-0001 稿 L-A1S-4 の解除) は判定しない。** 稿 §2.7 の並記は 2 つの観測を横に置くだけで、差・比・
  合成区間・「再現した」の判定を含まない。解除の可否は追補が定めるとおり別の裁定に属する。
- **`variance_plan_breach = true` の原因を帰属しない。** 標本 sd が計画 sigma を超えた事実だけを記録する (稿 L-A1S2-8)。
- **性能の優劣を主張しない。** 表は登録済み解析の descriptive 出力であり、workload をまたぐ結論・headline 値・C1 の再現判定にはしない。
- **3 本目の attempt の要否・認可を言わない。** 認可は attempt-0002 の 1 attempt 限り (追補 §6.4 項 4)。本 attempt の値は再投入・3 本目の理由にならない。
- **submit-tree と耐久 base は本 wave では撤去しない** (原本の所在。撤去は別途の掃除判断)。
- **`docs/paper-story/README.md` の stale 注記は足していない** (依頼の scope = results 表へ 1 行のみ)。2026-09-20 版の「A-1 は認可されたが gate で
  止まった」は本 wave の時点で古くなっている。本 wave は results 表への 1 行追加までを行い、版の記述の更新は scope 外である。

## 7. 一次資料

- 公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` (README.md / receipt.json / result.json / .complete.json)。
- durable authority (repo 外) `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0002/` と
  base 直下の `attempt-0002.intent.json` / `attempt-0002.authorization.json` (複製は `receipts/`、sha256 は `MANIFEST.tsv` と稿 §5.2)。
- 稿 `docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md`、README の results 表の行。
- 認可 gate の実装 wave `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md`、追補
  `output/insights/2026-09-20/t2792-a1-sized-preregistration-amendment/README.md`、gate 拒否の記録 `output/insights/2026-09-19/a1-sized-attempt2/README.md`。
- attempt-0001: `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md`、公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/`、稿
  `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`。
- 裁定: D2172 項 2、D2178、D2156、D2120 項 3、D2044 項 8、D1993 項 6、D1631、D12。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/` (起動 script、log、待ち手、抽出・検算 script の原本、handoff)。

## 8. 段の記録 (dev-wave 軽量版)

- 段 1 brief = `verbatim/brief.md`、段 4 裁定 = `verbatim/adjudication.md` (実装しない、段 2・3・5 省略、変異免除)。開始 gate rc 0
  (`verbatim/startup-gate.log`)。
- 実測は親 (authorize-rerun / submit / 監視 / complete / materialize / 抽出 / 検算)。稿は親が書いた (docs-only、DW-C00)。
- 段 6 = read-only codex review 1 本 (一次資料から事実を再抽出する docs-only の規則、DW-C00)。prompt と出力は `verbatim/prompt-review.md` /
  `verbatim/out-review.md` (出力は行末 ASCII 空白 13 箇所を whitespace 検査のため可逆正規化した。原文 sha256・byte 数・行番号・除去 suffix は
  `verbatim/whitespace-normalization.json`、可視文字は不変)、裁定は §9。
- 受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証)。

## 9. 段 6 レビューの裁定

read-only codex review 1 本 (gpt-6-astra / medium、16 call、424 秒、`verbatim/prompt-review.md` / `verbatim/out-review.md`)。数表 (§2.7 の 6 行 × 8 数値、
§2.1 の再計算、§2.3 / §2.4、job 表、identity preimage の 4 箇所差、leaf / 追補 / 受領証の digest) は全件一致。所見 10 件の裁定:

| # | 分類 (子) | 裁定 | 処置 |
|---|---|---|---|
| R-1 attempt-0001 の限定 20 件を「そのまま成り立つ」と継承 (L-A1S-4 の本数・L-A1S-16 の node が偽になる) | must-fix | real | 稿 §3 冒頭を「読み替えの下で参照」に改め、L-A1S-4 / 16 / 18 / 20 の読み替えを明記。README 行も同じ |
| R-2 driver 差分の所属関数を hunk header で書いた (`_v3_group_intent` 等 4 関数は文脈行で変更なし) | should | real | `-U0` 差分の new 側行番号を新版 AST で帰属 (`verbatim/driver-diff-functions.txt`): 定数 15 + 新設 3 関数 96 + 既存 6 関数 32 = 143 行。稿 §1.5 / §3 / §4.3 / §5.5、README 行、本 insight §1 / §2.2 を改めた |
| R-3 「stdout / stderr はいずれも空」の対象が不明 (job の stdout は 875〜885 bytes) | should | real | 親の 4 command の出力 (0 bytes) と job の scheduler stdout / stderr (bytes) を分けて書いた。failure 受領証の不在は `receipts/` の内容 (2 file) を根拠に書いた |
| R-4 §2.7 の並記値の出所を旧稿としていた (系列規則は一次資料だけ) | should | real | 出所を attempt-0001 の公開 leaf result.json に改め、旧稿は「一致する」に降格 (§2.7、§5.5) |
| R-5 「113 項目 ok」の保証範囲を広く書いた | should | real | 再計算・現物比較は `extract-attempt2.md`、draft-check は存在照合 + 配置比較、と分けて書いた (§5) |
| R-6 「他 2 job は 7 秒」「6 record」「Pre-running 5 分 31 秒」の起点・件数 | should | real | request 作成 (NQSV accounting) と scheduler start の時刻を並べ、「各 6 record、計 12 record」、監視 log の PRR / RUN 観測を分けて書いた (稿 §1.4 / §2.5、本 insight §3) |
| R-7 self digest の定義に `authorization_sha256` 自身の除外が無い | nit | real | 稿 §1.4 に明記 |
| R-8 図の将来の束縛方式と別 wave の動作を記録で確定していた | should | real | 稿 §2.6 を「図は本 wave の対象外」に、本 insight §6 を「版の更新は scope 外」に改めた。§10 の裁定パッケージ候補 (ユーザー手番) は残す |
| R-9 「投入後 1 byte も書かない」が materialize の新規 leaf と衝突 | should | real (表現) | 本 insight §2.1 を「既存 tracked bytes を変えない、書き込みは新規 leaf だけ」に改めた。brief (`verbatim/brief.md`) は逐語のまま残し、ここに読み替えを記す |
| R-10 brief の「起点に含まれることを定数と実在で確認」は祖先性の確認として書く、射影 `README-results-series-rules.md` は追加行を含んでいた | 記録 | real | merge-base の祖先検査で `886c19259` / `ec696308a` が `fec4a8187` の祖先であることを確認 (rc 0)。射影の切り出しが行挿入の後だったのは親の手順誤り。brief は逐語のまま残し、ここに記す |

- refuted 0。scope 超過の所見 (図・3 本目の認可・gate / 台帳の追加) は無し。「判定しない」の線は越えていない (子の確認)。
- 子が確認できないと書いた事項: hydrate の pin 一致・submit-tree の detached / clean・再投入不在の全履歴 (射影外。本 insight §2.1 と job dir の log が持つ)、
  lock 待ちの内訳の個別計装 (無い。稿は「lock 待ちを含む」とだけ書く)。
- fix 後に `draft_check.py` を再走 (`verbatim/draft-check-2.txt`)、`check_docs` 緑。焦点再レビュー子は起動せず (must-fix は継承文 1 件で、是正案の逐語をそのまま適用した)。

## 10. 裁定パッケージ候補 (実装せず記録。ユーザー手番)

1. **attempt-0001 稿の限定 L-A1S-4 (単一 attempt を反復間の安定性へ一般化しない) の扱い。** attempt-0002 が完走し、稿 §2.7 に 2 attempt の並記
   (6 cell とも `resolved-above-floor`、符号 + / + / − が一致、`variance_plan_breach` は attempt-0002 の 2 workload で true) がある。追補は「解除の
   可否は attempt-0002 の測定が存在してから、別の results 稿と裁定で扱う」と定める。択: (a) 2 attempt の並記を「同一配置の反復で分類と符号が一致した
   観察」として版・claim-evidence へ書き、L-A1S-4 は「2 attempt の観察に基づく限定」へ書き換えた新しい限定として次版で扱う (プールも再現判定もしない
   まま)、(b) 据え置き (並記の事実だけを results 表と本 insight に留める)。推奨は (a) — 事前登録は attempt 間の比較規則を持たないので、
   統計的な再現判定は事前登録なしには作れず、書けるのは観察までである。いずれも本 wave では行っていない。
2. **attempt-0002 の図 (fig9 と同形の単独図、または 2 attempt 並記図) の要否。** 依頼 scope 外。作るなら本稿を `caption_source` にし、2 attempt を
   1 panel に重ねる形は D1993 項 6 (プール禁止) との整合を裁定してから。

## 11. 記録前の機械走査と受入

- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、出力の原本は job dir の `three-axis-scan.txt`): rc 1、hit は rr80 / rr20 とも
  既存 4 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/{journal.jsonl,manifest.json,result.json}`、
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) だけで、本 wave の新規 file (稿・leaf・本 dir) に hit は無い (entry 1746 と同じ既知 hit)。
- **事故 (自分起因、受入 1 走を無駄にした):** 記録 commit `094ac8a1c` で走査の出力を `verbatim/three-axis-scan.txt` として本 dir に写したところ、
  その file 自身が走査の正規表現名 (三軸語) を含むため holdout hit になり、受入 attempt 1 (19:35〜20:00 JST) が赤 25 件 (`test_s8b_oracle_driver` の
  t080 系 `IZANAGI_FREEZE_HOLD` と `test_s8b_floor_campaign` の `clean scan 拒否`、25 件すべての message がこの file を名指し) で rc 70。走査の
  出力 file を repo に置いてはならない (走査結果は本節の要約で足りる)。fix commit で file を削除し、走査を再走して hit が既知 4 file に戻ることを
  確認してから受入を取り直した。F1013 (機械生成の生出力を insight に入れて holdout hit) の同型再発として failures fragment に追記した。
- `tools/check_docs.py` 違反なし、whitespace 検査 rc 0、`tools/spool_fold.py --dry-run` status planned、稿の機械照合 `draft-check-2.txt`
  113 ok / 0 問題。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が投入元として名指す submit-tree `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2792-a1-sized-attempt2/submit-tree` (detached `fec4a8187`、main の祖先) は、2026-09-30 の掃除 wave で回収せずに撤去する。公開 leaf 4 file は repo の `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` に byte 一致で在る。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
