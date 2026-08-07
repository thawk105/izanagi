結論は **(b)** である。本 wave は D207 の可否判定を出さず、完全 dev-wave campaign を後から正しく実施できる装置・endpoint・凍結 protocol を作る。既定 effort は段 2/3=`max`、段 5=`high` のままとし、worker 契約は変更しない。[D207:9891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9891) [workers.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:5)

## A. scope の択一

| 案 | 裁定 | 理由 |
|---|---|---|
| (a) protocol 文書だけ | 不採用 | margin は凍結できても、T-181 literal、artifact 命名、receipt、endpoint との結線がなく、実走時に別解釈できる。 |
| **(b) 一般化＋endpoint＋凍結、実走なし** | **採用** | 現在の本当の blocker を除き、LLM 費用なしで legacy 回帰・schema・freeze の検出力まで実装できる。 |
| (c) (b)＋n=2 pilot | 不採用 | n=2 は非劣性も分散も判断できず、完全 wave を消費し、case・margin を pilot 結果に合わせる余地を生む。生死確認は合成 E2E で足りる。 |
| (d) 独立 `dev_wave_endpoint.py` | 不採用 | D207 が指定した A/B 装置と arm identity・replay の信頼根が分裂し、二つの verifier 間に fail-open seam ができる。 |

完成条件は次の四つとする。

1. T-181 を immutable legacy family とした case-family registry。
2. 完全 wave の structured artifact index、盲検 findings、fix-cycle、全 worker 資源の収集・replay。
3. margin・n・停止規則・解析集合を機械的に固定する protocol freeze。
4. LLM-free の合成正負 E2E と、命名構造が異なる独立 2 wave で artifact-role 正規化を検査する。候補は `dev-wave-t244-p3-u8-critic` の版番号型と、`t205-provenance-compute-wave` の並列 `u1/u2` 型である。これは schema の生死確認だけで、過去 Markdown から endpoint を復元したとは扱わない。[DW-G03](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/core.md:52)

T-181 は現在も `rc=24 / experiment_complete=false` であり、この一般化で認証済みに昇格させない。[README.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/README.md:58)

## B. 装置の一般化

### 構造

[定数群:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:43) の後に、以下を置く。

- `T181_LEGACY_FAMILY`: 現在の literal を参照する immutable adapter。
- `DEV_WAVE_REASONING_FAMILY`: frozen JSON からのみ構成する full-wave adapter。
- `_resolve_case_family(family_id)`: 未知 ID・欠落 field は fail-closed。未知 family を T-181 へ fallback しない。
- 現在の `SCHEMA_VERSION=2` と rc 20〜25 は変更しない。[rc:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:178) 新 family は独立した `family_schema_version=1` と rc 26 以降を使う。

既存関数・CLI は引数なしなら従来どおり T-181 wrapper を通す。新 family は新 subcommand と明示的 `--family dev-wave-reasoning-v1 --protocol ...` を必須にし、暗黙 default を置かない。

### literal ごとの扱い

| 現行値 | 扱い |
|---|---|
| `SESSION_IDS` [実装:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:55) | T-181 専用として byte-for-byte 保存する。dev-wave は `wave_id/pair_id/opaque_slot_id/worker_job_id` と worker receipt SHA を使い、架空の session ID を作らない。 |
| `PROMPT_SOURCE` [実装:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:69) | T-181 の値は不変。新 family は `sources[] = {role,path,sha256,bytes}` とし、brief、worker contract、base snapshot を protocol に固定する。 |
| `CASE_ARTIFACTS` [実装:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:111) | T-181 POS/NEG tuple は不変。新 family は後述の `artifacts[]` に `stage/role/generation/lane/job_id/sha256` を持たせ、basename を意味に使わない。 |
| `CASE_HASHES` [実装:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:122) | legacy 値を不変とする。新 family は全入力・artifact index・worker receipt・endpoint ledger の SHA 集合を case closure とする。一つでも欠落すれば endpoint は `null`。 |
| `CASE_NUMSTAT` [実装:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:142) | legacy oracle はそのまま。dev-wave に同じ numstat を捏造しない。`closure_kind` ごとに base commit、dirty/untracked 集合、submodule、artifact hash を検査し、非該当なら明示的 `not_applicable`。単なる検査 skip は禁止する。 |
| `EXPECTED_SCHEDULE` [実装:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:160) | 現行 10 slot は不変。新 family は frozen protocol の `n_pairs=15`、各 pair の 2 opaque slot、順序、arm-map commitment から検査する。実データから期待件数を導出しない。 |
| `KNOWN_FINDINGS` [実装:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:166) | T-181 codebook は不変。新 family は frozen oracle がある case だけ `oracle_findings[]` を持つ。一般の finding は盲検裁定による `equivalence_id` を使い、root-cause 文字列一致にしない。 |

### 関数単位

- `_snapshot_spec()` [実装:599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:599)、`build_snapshot()` [実装:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1263)、`verify_snapshot()` [実装:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1359)  
  legacy wrapper は変更せず、別の `_family_snapshot_spec()` と `verify_family_snapshot()` を追加する。新 verifier は任意 caller の `spec` 差込みを許さず、protocol SHA に結合された spec だけを読む。

- `render_prompt()` [実装:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1533)  
  T-181 の rollout 抽出は不変。dev-wave は既存 session から prompt を復元せず、frozen brief と worker contract の bytes を検査する。arm 名・effort・schedule path が agent-visible 文面へ漏れたら reject。

- `collect_run()` [実装:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:2781)  
  直接 Codex run 用として残す。新 `register-wave-event` / `collect-wave-endpoint` は worker launcher receipt の `job_id/wave_id/reasoning/attempts` と SHA を取り込み、hash-chain 化した `wave-events.jsonl` を作る。

- `_validate_schedule()` [実装:3575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:3575)  
  現行 10-slot 検査を残し、別の `_validate_family_schedule()` を追加する。15 pair の欠落、重複、片 arm、順序破れ、case hash 非一致を区別して返す。

- `_load_adjudication()` [実装:3649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:3649)  
  legacy の二読者契約は維持する。新 family は二読者の一致だけで finding を消さず、不一致を arm 盲検の第三読者へ送り、未解決なら endpoint 欠落とする。

- `_aggregate_token_usage_observations()` [実装:3931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:3931)、`_aggregate_verified()` [実装:4005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4005)  
  legacy 集計を分岐内で書き換えず、`_aggregate_dev_wave_verified()` を追加する。endpoint 不完備時に quality/decision を `null` にする現行性質は継承する。[実装:4136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4136)

- `_replay_manifest()` [実装:4388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4388)  
  `producer_kind=direct-codex-run` と `producer_kind=dev-wave` を明示 dispatch する。完全 wave を単一 `collect_run` に見せかけない。

- `make_packets()` [実装:4787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4787)  
  T-181 の `same-owner-advisory` は legacy のまま残す。新 family は外部 custodian の署名 commitment がない限り `blind=true` を出さない。現在の same-owner masking は盲検の根拠にしない。[README.md:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/README.md:76)

- parser/main [実装:5200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:5200)  
  `freeze-protocol`、`verify-protocol`、`register-wave-event`、`collect-wave-endpoint`、`analyze-dev-wave` を追加する。解析 command に margin や n の override option は設けない。

### 後方互換の機械保証

既存 72 test は期待値を変更せず全て残す。特に literal allowlist [test:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:725)、numstat [test:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:737)、fake E2E [test:1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1382)、retry/resource [test:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2040)、incomplete-null [test:2122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2122) を回帰線とする。

加えて、編集前に独立 fixture `orchestrator/tests/fixtures/codex_reasoning_ab/t181-legacy-golden.json:1` を固定し、次を新設する。

- `test_t181_legacy_cli_golden_bytes_and_rc_matrix`
- `test_unknown_family_fails_closed_without_t181_fallback`
- `test_t181_default_parser_and_aggregate_are_byte_stable`

fixture は production 関数で test 実行時に再生成しない。POS/NEG の受理・拒否 corpus、schedule 10 slot、定数 digest、rc 20〜25、現在の incomplete result を literal で持つ。ソース文字列の存在だけを見る既存型 [test:2957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2957) は新保証に使わない。

MF-1〜MF-9 は「過去に mutation が通った」証明ではなく、新 family の攻撃 inventory として扱う。[focus1.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/output/insights/2026-07-30_t181-reasoning-ab/focus1.md:15)

## C. endpoint の定義

現状の `s5-impl*.md` / `s6-rev*.md` / `s6-fix*.md` には共通の typed field がない。したがって、過去 Markdown の glob や見出し解析を primary gate にすることは DW-O13 を満たさない。[DW-O13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/operations.md:74)

各 prospective wave に次の実成果物を作る。

- `artifact-index.json`: `artifacts[].{artifact_id,stage,role,generation,lane,worker_job_id,attempt,path,sha256,completion_receipt_sha256}`
- `blind-adjudication.json`: `findings[].{finding_id,phase,source_artifact_ids,source_span_sha256,equivalence_id,severity,real,must_fix,dw_g05_impact,resolution}`
- `cycle-ledger.json`: `cycles[].{generation,trigger_finding_ids,fix_job_ids,integration_sha256,state}`
- `wave-endpoint.json`: 上記三 ledger の SHA と、検証済み endpoint 値・観測状態

### must-fix 件数

Primary は、段 5 実装後・最初の固定 `max` downstream review generation の

`wave-endpoint.json.endpoints.must_fix.initial_unique_count`

とする。これは `blind-adjudication.json.findings[]` のうち、

- `phase == "post_impl_review_0"`
- `real == true`
- `must_fix == true`
- `dw_g05_impact` が構造化済み
- `resolution == "resolved"`

を `equivalence_id` で一意化した件数である。段 3 自身が treatment なので、段 3 が出した「must-fix」という文字列の件数は primary にしない。固定 downstream assessor にすることで、弱い段 3 が finding を少なく書いて良く見える経路を閉じる。

全 fix 後までの `total_unique_count` も記録するが、review 機会数が arm 間で異なるため burden/safety 指標とし、同数の観測機会を持つ initial count を一次とする。CRITICAL/HIGH の candidate-only finding と、control 段 3または frozen oracle が捕捉したのに candidate 段 3が落とし downstream へ残った finding は hard harm とする。

`must-fix` の文字列一致は、`blocker`、`NO-GO`、`land 不可`、日本語の同義表現や暗黙の G05 影響を落とす。一方で「must-fix ではない」、引用、過去所見、見出し、summary 数を誤って数え、同一 root cause の言い換えも二重計上する。現行 verdict に typed `must_fix` はあるが [実装:4933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4933)、dev-wave downstream 用には provenance と意味的 equivalence を追加する必要がある。

### 命名揺れ

basename から role を推測しない。

- `s5-impl.md`、`s5-implB.md`、`s5-impl-u1.md` は明示された `role=implementation` と `generation/lane` で整理する。
- 同じ generation の並列 `u1/u2` は一巡であり、二巡にしない。
- `s6-fix-ruling.md` は `role=ruling` であり fix worker 出力に数えない。
- 歴史 artifact を fixture 化する場合も、arm reveal 前に明示 mapping を作り hash 固定する。自動 filename importer の結果を primary に使わない。

### fix 巡回数

`wave-endpoint.json.endpoints.fix_cycles` は `cycle-ledger.json.cycles[].generation` の distinct 数から取る。

一巡とは「resolved real finding 群を契機に一つ以上の DW-S06-B fix job を dispatchし、統合・焦点再レビューまで進めた generation」である。[workers.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/workers.md:52) 同一 generation の並列 worker、technical retry、複数出力ファイルは一巡のままにする。

観測状態を分ける。

- `observed_complete, count=0`: 初回 downstream review と裁定が完了し、fix dispatch なしで正常終了。
- `observed_complete, count>=1`: 実巡回数。
- `not_applicable, count=null`: 実装段を持たない 4→7 path。
- `censored, count=null`: review/cycle ledger が成立する前に中断。

したがって「完走して fix 不要だった 0」と「fix を観測できる前に終わった wave」を区別できる。後者を 0 と補完しない。

### 資源

既存値は **job 単位の raw receipt としては使えるが、full-wave 集計としてそのままは使えない**。

- `cli_reported`、token、attempt は worker launcher receipt の全 `attempts` を使う。[codex_worker_launch.py:1401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_launch.py:1401)
- `model_calls` は turn 数ではなく `token_count` event 件数である。[codex_worker_ledger.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_worker_ledger.py:475) 名称・意味を変更しない。
- allocation 後の段 2、3、5、downstream review、全 fix、失敗・retry を含める。最終 attempt だけにしない。現行 apparatus の全 attempt resource ledger [実装:4120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4120) を継承する。
- wall は `worker_wall_sum_s` と campaign の `end_to_end_elapsed_s` を分ける。並列 worker の wall を単純加算した値を所要時間と呼ばない。

**代理 endpoint は置かない。** 段 2 plan に固定 max reviewerを当てる件数や T-181 型検出率は診断値にはできるが、実装・fix 巡回・retry を通らないため、D207 が排除した「弱い起草が巡回を増やし総消費を上げる」経路を排除できない。[D207:9906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9906)

## D. 事前登録の形

`docs/dev-wave/*.md` は増やさず、規範データを次に置く。

- `output/insights/2026-08-07_t595-reasoning-ab/preregistration.json:1`
- `output/insights/2026-08-07_t595-reasoning-ab/case-registry.jsonl:1`
- `output/insights/2026-08-07_t595-reasoning-ab/public-schedule.json:1`
- `output/insights/2026-08-07_t595-reasoning-ab/protocol-freeze.json:1`
- `output/insights/2026-08-07_t595-reasoning-ab/mutation-preregistration.json:1`

外部 custodian は worktree 外に private arm map を持ち、公開側にはその SHA と署名公開鍵だけを置く。

### 凍結する設計

- Estimand: **joint downshift**。
  - control `MM`: 段2=`max`、段3=`max`
  - candidate `HH`: 段2=`high`、段3=`high`
  - 段5=`high`、モデル、worker contract、他段、base snapshot は同一固定
- `n=15` randomized pairs、計 30 完全 dev-wave。親の観測 SD≈1.6、margin 1、必要 9〜15 pair の上限を採る。[brief.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:47)
- paired 差は `d_i = HH_i - MM_i`。全 count endpoint で小さい方が良い。
- `must_fix.initial_unique_count`: 片側 95% paired-t 上側信頼限界 `<= +1.0`。
- `fix_cycles`: 同じく上側信頼限界 `<= +1.0`。
- CRITICAL/HIGH の candidate-only downstream finding、または candidate 段3の survived miss: margin 0、1 件でも reject。
- `log(cli_reported_HH / cli_reported_MM)`: 上側信頼限界 `< 0`、すなわち総 token 節約を要求する。`model_calls` と wall は sensitivity であり、品質失敗を救済できない。
- 全 co-primary gate を通る intersection-union 判定。exact within-pair sign-flip は事前指定 sensitivity とし、primary failure を覆さない。

### 割付と盲検

- 各 pair は同じ brief SHA、base commit、snapshot、model pin から独立 worktree を二つ作る。
- secret seed の commitment を先に凍結し、実行順は control-first 7、candidate-first 8 に均衡化する。
- worker と outcome reader には opaque slot だけを見せる。ファイル名、mtime、path、effort、資源集計を verdict freeze 前に見せない。
- 二名の固定 max readerが独立裁定し、不一致は第三の blind readerへ送る。endpoint と reader ledger の freeze 後にだけ arm map を reveal する。
- 現行の `same-owner-advisory` [実装:4853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4853) は新 campaign では `blind` と認定しない。外部署名 custodian が用意できなければ実走を開始しない。

### 停止規則と解析集合

- 成功方向の中間 peeking・早期停止なし。
- model output 前の機械的 infrastructure failure だけ、pair 丸ごと既存上限内で再試行できる。
- treatment 開始後の failure、incomplete、protocol breach を都合よく再走・除外しない。endpoint 欠落なら非劣性不成立。
- CRITICAL/HIGH harm は candidate reject として停止できるが、非劣性成功とは書かない。
- 予算・queue・custodian 不備による停止は `experiment_complete=false / decision=null`。
- Primary ITT: allocation 後に treatment が開始した全 pair。
- Per-protocol complete-pair 集合: sensitivity のみ。
- Resource 集合: failure、retry、pair-invalidated を含む allocation 後の全 attempt。
- complete-case だけを primary にすること、事後の case 交換、margin/n 変更は禁止する。

### command と改変不能性

```bash
python3 tools/codex_reasoning_ab.py freeze-protocol \
  --protocol output/insights/2026-08-07_t595-reasoning-ab/preregistration.json \
  --case-registry output/insights/2026-08-07_t595-reasoning-ab/case-registry.jsonl \
  --public-schedule output/insights/2026-08-07_t595-reasoning-ab/public-schedule.json \
  --mutation-manifest output/insights/2026-08-07_t595-reasoning-ab/mutation-preregistration.json \
  --output output/insights/2026-08-07_t595-reasoning-ab/protocol-freeze.json \
  --require-no-run-receipts

python3 tools/codex_reasoning_ab.py verify-protocol \
  --freeze output/insights/2026-08-07_t595-reasoning-ab/protocol-freeze.json \
  --phase pre-run
```

freeze は canonical JSON SHA、case/schedule/private-map commitment、model/commit/worker-contract hash、mutation manifest hash、custodian signature を結合する。全 prelaunch event、worker receipt descriptor、artifact index、endpoint manifest が同じ `protocol_sha256` を持たなければ reject する。`analyze-dev-wave` は freeze から margin/n を読むだけで CLI override を持たない。

事後に protocol を編集すると SHA が変わり、既存の最初の prelaunch receipt と一致しない。新しい freeze を作っても campaign ID と既存 receipt chain が結合できないため、旧 run の再解釈には使えない。

## E. 変異事前登録の候補

各 test は有効な正例を一つ通し、その fixture の一 field だけを変えた負例を public validator/CLI へ通す。ソース文字列 assert は使わない。

| # | 変異点 | 殺す test |
|---:|---|---|
| 1 | family resolver／parser [実装:5200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:5200): 未知 family を T-181 へ fallback | `test_unknown_family_fails_closed_and_t181_golden_is_unchanged` を [test:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:725) の後に追加 |
| 2 | snapshot closure [実装:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1359): artifacts の一 SHA を検査対象から削除 | `test_generic_case_closure_rejects_one_stale_artifact_hash` |
| 3 | schedule validator [実装:3575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:3575): 14/15 pair、重複 slot、片 arm 欠落を受理 | `test_family_schedule_requires_exactly_15_complete_pairs` |
| 4 | launch identity [実装:1719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:1719): protocol SHA または opaque slot を identity から除外 | `test_protocol_or_slot_swap_breaks_launch_identity` |
| 5 | packet/reveal [実装:4787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4787): same-owner を external blind と認定、または verdict freeze 前 reveal | `test_dev_wave_family_requires_external_custodian_and_postfreeze_reveal`。既存二読者検査 [test:2378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2378) も併用 |
| 6 | artifact normalizer: basename の `fix`/`implB`/`u1` から role・巡回を推測 | `test_artifact_roles_ignore_filenames_and_group_parallel_lanes`。t244 version 型と t205 u1/u2 型を正例にする |
| 7 | adjudication [実装:4909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4909): `"must-fix"` 部分文字列または root text で count/dedup | `test_must_fix_count_uses_resolved_typed_equivalence`。否定文、同義日本語、同一原因二表現を含める |
| 8 | cycle aggregation [実装:4005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4005): censored を 0、並列二 file を 2 巡と数える | `test_fix_cycle_states_distinguish_zero_censored_and_parallel_files` |
| 9 | resource aggregation [実装:4120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4120): final attempt だけ残す、`model_calls` を turns と表示、並列 wall sum を elapsed とする | `test_full_wave_resources_include_every_attempt_with_original_semantics`。既存 retry 正例 [test:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2040) を拡張 |
| 10 | aggregate decision [実装:4136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/codex_reasoning_ab.py:4136): endpoint 欠落、harm、blind breach があっても NI decision を出す | `test_incomplete_or_harmful_campaign_nulls_noninferiority_decision`。既存 incomplete-null test [test:2122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:2122) と対応 |

## F. 反対意見

1. **この scope は D207 の endpoint を満たした結果を一件も出さない。** n の根拠も非 paired の歴史分散であり、15 pairでも信頼限界が広ければ判断不能になる。満たすには外部 custodian、30 本の完全 wave、全 endpoint の typed ledger、凍結解析の完了が必要である。margin を後から広げてはいけない。

2. **joint `MM` 対 `HH` は、段 2 と段 3の個別寄与を識別しない。** 「両方同時に下げてよいか」には答えるが、片方だけの可否や interaction は答えない。個別裁定には、同じ 15 case で `MM/HM/MH` の45 wave、interaction まで見るなら `MM/HM/MH/HH` の60 waveが必要である。

3. **盲検 findings の意味的同定は完全には機械化できず、基礎装置の T-181 自体も未認証である。** SHA・bijection・field 実在は機械保証できるが、`real/must_fix/equivalence/G05 impact` は独立 reader と第三裁定に依存する。また T-181 数値を根拠に使うなら、最終版装置による10 run再走が別途必要である。旧 mutation 12/12 はその代替にならない。

本回答は read-only の静的プランであり、pytest・実走・緑は主張しない。

## 総括

- scope は **(b)**：legacy 不変の case-family 一般化、full-wave endpoint、protocol freezeまで。実走はしない。
- 最大 risk は、semantic must-fix 裁定と外部 custodianが必要な盲検境界、および30 waveでも判断不能になり得る点。
- 段4では **joint 30 wave** と **段別帰属45〜60 wave** を択一する。現依頼には joint を推奨する。
- 完全 campaign が成立するまで D207 は未充足であり、段2/3の既定 `max` は一切変更しない。