## 0. 結論と前提

実装単位 A／B を分けて進められる。P1・P2・P3・P7・P8・P9 は概ね賛成。P4 は「exact ID の事後記録」と「本走モデルの事前固定」を区別し、P5 は判定の意味を限定する必要がある。P6 は **「投入後 skip の B 過少計上を report が invalid として検出する」とは言えない**。

読み取りと保存済みデータの集計だけを行った。編集・commit・テスト・B-5 投入は行っていない。以下の新規関数名・test node 名は実装案であり、既存の所在と区別する。

参照の略記：

| 略記 | path |
|---|---|
| `D` | `orchestrator/campaign/b5_generator_contrast.py` |
| `R` | `orchestrator/campaign/b5_generator_contrast_report.py` |
| `L` | `tools/pegasus/b5_contrast_launch.py` |
| `J` | `tools/pegasus/p3_s4_loop_pegasus.sh` |
| `C` | `orchestrator/campaign/p3_s4_loop.py` |
| `P` | `orchestrator/campaign/pipeline.py` |
| `PR` | `docs/b5-generator-contrast-preregistration.md` |
| `OLD` | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/llm_round.py` |
| `PILOT` | `output/insights/2026-09-20/t2797-b5-contrast/` |
| `T0` | `output/insights/2026-09-21/t2797-tier0/README.md` |
| `BRIEF` | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/brief.md` |

以下の `D:555` 等は、この表の file:line を指す。

## 1. 実装単位 A：driver・job body・launcher

### 1.1 driver

変更箇所は `D:1`、`:43`、`:555`、`:710`、`:718`、`:840`、`:857`。

- `COHORT_REGISTERED = "b5-registered-v1"` を追加する。cohort を自由指定する CLI は足さず、purpose から定数を選ぶ。
- `run-series`／`run-block-stock` に `--purpose {pilot,registered}`、既定 `pilot` を追加する。
- `run_series`／`run_block_stock`／`_header` に keyword-only `purpose="pilot"` を通す。既存呼出しはそのまま成立させる。
- registered の探索系列では既存の座標検査に `block == (series-1)//4+1` を加える。stock は現行どおり `series=block`。
- module docstring を pilot 専用の説明から両 purpose の producer の説明へ変更する。「registered を出力できることは発効・投入認可を意味しない」を明記する。

`_header` の pilot 分岐は既存辞書と同じ値を返す。特に次を保持する。

- `cohort="t2797-beta-v1"`、`purpose="pilot"`。
- `limits` の既存 2 文を文字単位で保持。
- key の追加・削除なし。Tier0、予算、動作点、job、deadline の扱いも変更しない。
- registered のときだけ cohort／purpose と `limits` の第 2 文を変更する。例：`"Registered producer; cohort activation and actual execution order require external approval and evidence."`

「header bytes 不変」は、同じ HEAD・host・環境・deadline に固定した比較で保証する。実際の別 commit／別 job では `repo_head` 等が変わるため、実走間の header 全 bytes が同じとは主張しない。比較対象は `_json_bytes({...header, "schema": LEDGER_SCHEMA})` の生成結果とする（`D:175`、`:225`）。

A/B 消費点、生成器、handshake、endpoint は触らない（`D:112`、`:130`、`:599`、`:668`、`:792`）。

### 1.2 job body

変更箇所は `J:54` と `J:648` の B-5 分岐内に限定する。

- `IZANAGI_S4_B5_PURPOSE` 未設定は pilot。
- 設定済みなら `pilot|registered` だけ受け、空文字・未知値は既存 `refuse` で拒否する。
- B-5 mode が無いのに purpose だけ存在する場合も、既存の「B-5 env は mode を要する」検査へ含める。
- **既存の必須 env 配列へそのまま追加しない。** それでは purpose 未指定の pilot が壊れる。任意 purpose の検査を別に置く。
- `registered` の場合だけ `b5_argv+=(--purpose registered)`。未指定／明示 pilot は argv を増やさない。

これにより既存 pilot の argv は維持できる。非 B-5 の既存 3 経路へ purpose を渡すコードは置かず、既存呼出し部分を編集しない。K2 の受渡し、node-local lock、終了コード伝播も現状維持（`J:107`、`:655`、`:661`、`:666`）。

根拠となる既存 test は以下。

- `orchestrator/tests/test_p3_s4_loop_job_contract.py:1908`：既存経路の実 shell 呼出し。
- 同 `:2012`：pilot の期待 argv。
- 同 `:2040`：B-5 4 arm の呼出し回数・終了コード・lock。

### 1.3 launcher

既存 `pilot_jobs`／`validate_pilot_cap`／`launch`／pilot CLI を保存し、registered 専用入口を追加する（`L:112`、`:151`、`:218`、`:246`）。

入口案：

```text
b5_contrast_launch.py registered-schedule
b5_contrast_launch.py registered \
  --block B --stage S --walltime-factor K \
  --submit-trees MAP.json --expected-head FULL_OID \
  --ledger-root ABS --evidence-root ABS \
  --thirdparty-source-root ABS \
  --knowledge-manifest ABS \
  --knowledge-classification known_result_conditioned_derivative \
  --knowledge-de-novo-claim false \
  (--dry-run | --submit)
```

旧 CLI は先頭がこの 2 語でない場合に従来 parser へ渡す。既存 pilot 引数の必須条件を緩めない。

新規関数案：

| 関数 | 責務 |
|---|---|
| `registered_schedule()` | 純粋・決定論的に 108 系列の block／series／arm 順と、117 job の stage 配置を返す |
| `registered_jobs(...)` | block／stage を選び、ledger／evidence root と K2 を具体化 |
| `registered_walltimes(k)` | Decimal で W／W_stock を算出し秒数と scheduler 書式を返す |
| `launch_registered(...)` | job 単位の tree を既存検査へ通し、dry-run／submit を行う |

`PilotJob` を無理に汎用化せず、registered 側の小さな dataclass を置く。既存 `_validate_job` は write-heavy／series 1／block 1 を要求するため、registered から呼んではならない（`L:112`）。

submit-tree mapping は job ID → absolute repo path とする。例：

```json
{
  "b1-write-heavy-r01-llm": "/.../submit-trees/b1-write-heavy-r01-llm",
  "b1-write-heavy-stock": "/.../submit-trees/b1-write-heavy-stock"
}
```

各 tree に既存 `validate_submit_tree` を適用し、共通 expected HEAD、CCBench pin、clean 条件を保持する（`L:79`）。arm 単位の mapping は同 stage 内の 4 系列を区別できないので使わない。選択 job 間の tree は distinct とし、map 全体でも job ごとの割当を固定する。

出力は次のように分離する。

```text
<ledger-root>/b5-registered-v1/block-1/write-heavy/r01/llm/
<evidence-root>/b5-registered-v1/block-1/write-heavy/r01/llm/
<ledger-root>/b5-registered-v1/block-1/write-heavy/block-stock/
```

pilot root と混ぜず、ledger／evidence は全 submit-tree・common repo の外へ置く。既存の freshness・出力分離の検査を registered 経路にも適用する（`L:131`、`:166`、`:227`）。新しい承認 gate は作らない。

K2 は LLM job だけに既存 4 env を渡す。random／sweep／stock には渡さない（`L:195`、`D:506`）。registered には `IZANAGI_S4_B5_PURPOSE=registered` を明示する。

walltime は文字列から `Decimal` として読み、有限な `0 < k ≤ 4.06` を要求する。新しい下限 1 等は裁定なしに足さない。

```text
W       = ceil(Decimal("21259") × k)
W_stock = ceil(Decimal("5447") × k)
HH = seconds // 3600
MM = seconds % 3600 // 60
SS = seconds % 60
elapstim_req=HH:MM:SS
```

日付時刻 API を使わず、24 時間で wrap させない。`k=2` は `11:48:38`／`03:01:34`、`k=4.06` は `23:58:32`／`06:08:35`。pilot の literal `08:00:00`／`03:00:00` は変更しない（`L:209`）。

dry-run は環境・argv・cwd・job ID を出力し、mkdir／qsub は行わない。submit は選択 stage 全件の構築と既存検査を終えてから投入し、途中失敗は既存同様その場で返す。自動 retry／stage 自動進行は足さない（`L:218`）。

### 1.4 report を変更せず読める条件

| 条件 | 既存 consumer | producer／schedule 側の満たし方 |
|---|---|---|
| purpose 一致 | `R:198` | 全 header が `registered`、report も `--purpose registered` |
| cohort | `R:205`、`:520` | 非空の同一定数 1 個 |
| 探索 block | `R:213` | series 1–4／5–8／9–12 を block 1／2／3 |
| stock 座標 | `R:214` | `series=block`、mode `block-stock` |
| 予算・session 契約 | `R:207`、`:211` | 現行 A／B／N_eval、verify mode、3 rounds を保持 |
| slot 所有 | `R:278` | 既存 `slot_key` を変更しない |
| 系列・campaign 一意性 | `R:472`、`:476` | 108 系列＋9 stock の job 分離、既存 fresh identity |
| workload 内構成一致 | `R:467` | 全 arm で同 HEAD／pin／perf／Tier0 |
| 評価件数と B | `R:297` | 消費点を変更しない。ただし N1 の例外は第 6 節 |

report は実 arm 順と block 間隔を検証しない（`R:505`）。schedule と運用記録がその証拠であり、検査済みと誤記しない。

## 2. 実装単位 B：LLM 巡 tool

### 2.1 置き場と一般化

新規 `tools/b5_llm_round.py` と `orchestrator/tests/test_b5_llm_round.py` を B の所有とする。

理由は、処理が scheduler 固有の投入ではなく、保存済み JSON／prompt／Claude 会話記録の変換だからである。`tools/pegasus/` 配下へ置いて submitter の `local-ok` を借りる設計にはしない。

`docs/pegasus-runbook.md:468` によれば、`tools/pegasus/` 外の未登録 path に一律登録義務はなく、外側 path を `local-ok` 登録することもできない。したがって新 tool の admission 登録は不要。ただし未登録を資源実測済みの証拠とは呼ばず、既存拒否 path の別名 wrapper にもしない。実装面であり Codex author が必要（`docs/ai-provenance.md:44`）。

一般化する箇所：

| 試走版 | 本走版 |
|---|---|
| `OLD:21` の REPO 絶対値 | `Path(__file__)` から repo root |
| `OLD:32` の job／materials／ledger | `--ledger-root`、`--materials-root` |
| `OLD:36` の manifest 絶対値 | `--knowledge-manifest`。束で固定した同じ manifest を渡す |
| `OLD:76` の round2 file 比較 | resolved manifest と束に保存した射影の hash／bytes を使用 |
| `OLD:103` の `series.json` 依存 | `SeriesLedger.header/events` を読む |
| `OLD:154`、`:204`、`:280` の workload／系列固定 | header の `workload`／`series`／`purpose`／`cohort` |
| `OLD:162`、`:284` の動作点文字列 | `C:1848 calibrated_perf(workload)` から整形 |
| `OLD:282` の欠測 CV を 0 と表示 | 欠測は `null`／欠測と表示。0 を捏造しない |

入力構築・K2 診断・文法・proposal 検査は既存関数を使う（`OLD:134`、`:145`、`:236`、`:249`）。新しい検査体系を作らない。

### 2.2 知識射影と prompt

K2 knowledge 本文は `PR:173` の manifest／source を維持する。workload 別に変わるのは **動作点の説明を含む leakproof context** であり、既知知識の集合を workload ごとに選別しない。

`PILOT/llm/leakproof-context-b5.md:42` の動作点表、`:59` の測定手順、冒頭の試走説明をパラメータ化する。共通説明・文法・whiteboard の意味は保持する。出力は親の束へ次の 3 file として保存する。

```text
knowledge/leakproof-context-write-heavy.md
knowledge/leakproof-context-balanced.md
knowledge/leakproof-context-read-heavy.md
```

動作点の max_ope は `calibrated_perf` が明示する 10 を書き、「CCBench 既定だから」という依存表現を外す（`C:1852`、`P:159`）。

prompt template は新 tool が使う固定資材として B が所有する。候補は `tools/b5_llm_round_templates/` の planner／coder／critic と context template。親の束にはその bytes と hash を写す。

### 2.3 subcommand と入出力

| subcommand | 入力 | 出力 |
|---|---|---|
| `context --workload W` | 固定 context template、`calibrated_perf(W)` | workload 別 context |
| `inputs --a A` | header、request-A、該当系列 events、K2、必要なら critic-(k−1) | request 写し、planner-input、coder skeleton、planner prompt |
| `coder --a A` | planner 逐語 JSON、skeleton | coder-input、coder prompt |
| `proposal --a A` | planner／coder 出力、保存済み入力 | proposal 保存、既存検査後に handshake の inputs → proposal の順で公開 |
| `reject --a A --reason TEXT` | 原提案番号・理由 | 既存 `proposal-A.rejected.json` |
| `critic --evaluation K --job ID --window TEXT` | slot-K、digest、当該系列台帳 | critic-input、critic prompt |
| `record-models ...` | 明示指定した transcript／meta file | 巡・role ごとの model 記録 |

`inputs` の a と k は分ける。前処理拒否で a が増えても k は増えない（`D:668`、`OLD:112`）。初回診断 key は置かず、k≥2 は同じ 6 field の診断を両入力へ渡す（`D:477`）。

親 session の起動や Agent 呼出しはこの tool に入れない。

### 2.4 exact model ID 記録

`record-models` は全 project の探索をせず、親が特定した各 subagent の `.jsonl`／`.meta.json` を引数で渡す。JSONL は行単位で読み、assistant 発話の `message.model` を全件集約する。最初の ID だけ採らない。

記録先例：

```text
<materials-root>/round-A/models-planner.json
<materials-root>/round-A/models-coder.json
<materials-root>/critic-K/models-critic.json
```

schema 案：

```json
{
  "schema": "b5-llm-model-record/v1",
  "cohort": "b5-registered-v1",
  "workload": "write-heavy",
  "series": 1,
  "a": 1,
  "evaluation": 1,
  "role": "planner-v4",
  "agentType": "planner-v4",
  "toolUseId": "...",
  "models": ["claude-opus-5"],
  "assistant_messages": 3,
  "transcript": {"path": "...", "sha256": "..."},
  "metadata": {"path": "...", "sha256": "..."}
}
```

これは発効束用の記録で、campaign ledger の field 追加ではない。親の設定・版は別の構成記録へ保存する。

P4 の限界は明記すべきである。

- `model: opus`／`effort: high` は role frontmatter の事実（各 role file `:5`）。
- `claude-opus-5` は観測した応答 ID。alias が将来も同じ ID を返すことは、この記録器では保証しない。
- 複数 ID、欠落、未完了 transcript を単一 exact ID に丸めない。
- client 内部形式であり、安定 API・暗号学的 attestation・実入力送達の独立証明ではない。
- 束には「予定 exact ID」と「実走後に採取する観測 ID」を別に記す。実走前の記録を捏造しない。

P4 はこの限定付きで賛成。alias 起動を exact ID の機械的 pin と呼ぶ案には反対する（`PR:190`）。

### 2.5 fixture

最小 transcript：

```json
{"type":"user","message":{"role":"user","content":"fixture"}}
{"type":"assistant","message":{"role":"assistant","model":"claude-opus-5","content":[]}}
{"type":"assistant","message":{"role":"assistant","model":"claude-opus-5","content":[]}}
```

meta は `{"agentType":"planner-v4","toolUseId":"toolu_fixture"}`。別 ID 混在、assistant 不在、model 欠落、壊れた JSONL／meta も用意する。

prompt 回帰は二段にする。

1. 試走 round-1 の request、planner／coder 出力、context、prompt 内の K2 JSON を fixture として用い、元 template に対応するパラメータを与えた renderer が同じ prompt bytes を出すことを確認する。
2. registered template は試走ラベル・workload／series・context の変更を明示した期待値と照合する。**試走専用文言を除去した本走 prompt と、試走 prompt 全 bytes の同一性を同時に要求しない。**

旧ラベルや絶対 path は fixture データにのみ残す。本走 template に埋め込まない。

保存済み round-1 prompt の現在の SHA-256 は planner `e091ab00…b6b03b`、coder `41e95b41…e93c9d`。採取時は full hash と raw bytes を保存する（`PILOT/llm/round-1/planner-prompt.md:1`、`coder-prompt.md:1`）。

## 3. 親の採取：§12 対応表

共通 hash 規則は `sha256(raw bytes)`。JSON を読み直して再整形した hash を元 file の hash と呼ばない。重み配列だけは既存 `weights_sha256` の正準化規則も併記する（`D:92`）。対象 commit 自身を含む束の自己参照は作らない（`PR:31`）。

| §12 項目 | 値の出所・採取方法 | draft 時点の扱い |
|---|---|---|
| 認可日・D・対象 commit | `PR:538`、D2200 項1、完成後の land commit | 本走認可日／D は未確定。対象 snapshot と将来の発効 commit を区別 |
| 事前登録 raw hash・保存先 | `PR` 全 bytes を hash、測定版の保存先を明示 | 文書固定。本文は編集しない |
| repository・CCBench・文法 | `git rev-parse HEAD`、`C:118 PIN`、hole grammar の定数／bytes | full OID と内容 hash |
| 環境・較正 | `env_contract.lookup` が返す `calibration_ref`／contract hash | 実際に選ばれる generation を記録。mtime で選ばない |
| toolchain | job prebuild の `toolchain_manifest`（`J:603`、`:623`）、較正 record、compiler 絶対 path と `--version`、Python 版、Claude Code 版 | login の gcc を compute の gcc と読み替えない |
| 実行 script・生成器・解析 | D／C／P／L／J／R、新 LLM tool・templates、直接依存する生成／文法／統計資材 | file bytes／sha と実装所在 commit |
| exact model・設定 | role 3 file、親設定の hash、Claude Code 版、前節の採取器と実例 | 予定値・既観測値・本走後採取を区別 |
| 全役割 prompt | B の templates、生成済み planner／coder／critic prompt、親 template | 初回実測 stock 未取得の本走 prompt は未生成。fixture を実入力と呼ばない |
| 知識射影 | `PR:173` の manifest/source、workload 別 context | knowledge source と context の hash を別々に保存 |
| schema・初回入力・欠測 | role 本文、`D:451`、`:477`、`OLD:137`、`:270` | 初回は空 whiteboard・診断 key 無し。未測 stock の数値を補完しない |
| random 重み・preimage | `python3 -B -m orchestrator.campaign.b5_generator_contrast weights-material --out …`、`D:112` | 1000 整数、M、配列 hash、file hash、preimage 文法 |
| sweep 全順序 | `D:130 sweep_order(w,r)` を 3 workload×12 系列で採取 | 各 28 点全順序と先頭10点。既存別 sweep driver を使わない |
| 108 系列 schedule | 新 `registered-schedule` | 108 系列＋9 stock job の stage 配置、36 arm 順、p=4 |
| session ID | `D:156 slot_key` | stock-start 1、search a=1..30、score 1..5、block-stock 1..5、attempt 0..2 の命名規則。未発生枠を実測件数に数えない |
| correctness／Tier0／bench | 下表、`D:506`、`C:2178`、`P:409`、`:1343` | exact 値と runtime path の置換規則を保存 |
| walltime | 新 `registered_walltimes`、D2217 | k 候補ごとの秒数／argv、最終 k は未承認 |
| D39 改訂・総 wall | `PR:146`、`:526`、`:554` | 文書固定／明示承認待ち。発効済みとしない |
| 既知結果差分・§10 実装所在 | `PILOT/README.md:153`、`T0:118`、本 wave の (b)(c) 結果 | Tier0 live 確認は未実施のまま明記。後段校正の手番 |

36 sweep 順と schedule の生成は軽い資料採取であり、本走投入ではない。親が生成出力を保存し、同じ bytes の再生成と独立の件数・順序照合を行う。

### exact 実行契約

| 経路 | 固定値・引数 | 所在 |
|---|---|---|
| legacy trace | tuple=200、threads=4、rr50、skew=.9、rmw=true、max_ope=5、extime=1、1回 | `P:146` |
| 動作点 trace | tuple=1,000,000、threads=48、rr5／50／95、skew=.9、rmw=false、max_ope=10、extime=3、5回 | `C:1848`、`P:193` |
| trace argv | `[numactl prefix] binary -key=value … -clocks_per_us=…`、trace dir を env に設定 | `P:409`、`:438` |
| verifier | `verify_trace_dir_with_capability(trace_dir, expected_commits=…, genome=…, source_evidence=…, build_admission=…, receipt_* …)` | `P:484`、`:613` |
| Tier0 | `--thread_num=4 --ycsb_tuple_num=200 --extime=1 --ycsb_rratio=50 --ycsb_zipf_skew=0.9 --ycsb_rmw=true --ycsb_max_ope=5`＋clocks、timeout32、perf false | `C:2178`、`:2228` |
| bench | trace-disabled、同動作点、5 rep、既存 measure_point 経路 | `P:1343`、`orchestrator/calibrator/runner.py:1085` |
| 品質再測定 | CV>0.05 で静定再測、最大3 round、最低 CV round を採用 | `P:1411`、`orchestrator/calibrator/stability.py:58`、`analyze.py:22` |
| ledger 品質 | rep 数不一致／unstable／settled 不成立は品質欠測 | `D:classify_session`、既存 test `test_b5_generator_contrast.py:109` |

verifier はこの経路では Python API 呼出しであり、存在しない verifier CLI を exact argv として捏造しない。API の実引数と、その先の実装版・既定 mode を採取する。

また、bench の `require_all_reps`／`require_settled` の既定値と、B-5 driver が採用を拒否する条件を分けて記す。B-5 が pipeline 全体の qualification policy を有効にしたと誤記しない（`P:1348`、`:1419`）。

generator の hash seed と、測定 binary の seed は別欄にする。現行 B-5 argv に明示 seed は無い（`D:506`、`P:438`、`PR:337`）。

## 4. P2 schedule の検証

L=llm、R=random、S=sweep-matched とする。block 内位置 j=1..4 に対し、LLM 位置ごとの順序を次の交互割当に固定する。

| LLM 位置 | j=1,3 | j=2,4 |
|---|---|---|
| 1 | LRS | LSR |
| 2 | RLS | SLR |
| 3 | RSL | SRL |

`pos(w,b)=((w_idx+b−1)%3)+1` なので、各 workload は 3 block で LLM 位置 1／2／3 を各1回使う。各 block 内で該当する2順序を各2回使うため、全12系列では6順序が各2回となる（`PR:327`）。

各 stage では LLM 位置がその stage に一致する workload がちょうど1個あり、その4系列が LLM job となる。前 stage の全 job 終了後に次 stage を投入すれば、同時 LLM は最大4。単に「投入時だけ4本」ではなく、前 stage の終了を待つ点が必要である（`T0:120`）。

- 各 stage：探索12 job。
- stage1 のみ：workload ごとの block-stock 3 job を追加、最大15 job。
- 全体：探索108 job＋stock9 job。
- stock の header は series=block。探索系列番号の先頭値を stock series に入れない（`R:214`）。
- 次 block は前 block の全 job 終了後にさらに1時間待つ手順なら、最終測定→初回測定の1時間条件を保守的に満たす（`PR:333`）。
- 実開始・終了と測定境界は既存 job／ledger 記録から採取する。新しい runtime 検査は作らない。

stage 同期の calendar wall は、queue を除き、

\[
\sum_{b=1}^{3}\sum_{s=1}^{3}\max_{j\in(b,s)}T_j+2\times3600
\]

となる。全 job が要求上限まで使う配置上の上限は `9W+7200`。k=2 で108.295時間、k=4.06 で217.78時間。これは予測実消費ではない。node Elapse 総和は別に `ΣT_j` で数える（`PR:528`）。

代替案は、同じ36個の arm 順を維持し、各対の先行 arm 終了後に次 arm を固定順で投入、LLM は4本枠で運用する方法。stage barrier の待ちを減らせるが、親の進行管理が複雑になる。P8 と scope を優先し、今回は P2 を採用する。block 間隔・親数・完了観測は手順として固定する。

## 5. (b) rep 1 高値：P5 の計算と評価

### 計算手順

`PILOT/ledgers/<arm>/events/*.json` から `stock-start`／`evaluation-result`／`score-session` のみを採り、同じ観測を持つ `pipeline-submitted` を二重計上しない（`P:1456`、`R:356`）。

各 session の採用 round の `bench_payload.tps` を x として、

\[
d=\left|\frac{\mathrm{median}(x_{2:5})}{\mathrm{median}(x_{1:5})}-1\right|
\]

を計算する。分母は元の5 rep median に固定する。

CV は `statistics.stdev / statistics.mean`、標本標準偏差 n−1。5 rep／4 rep それぞれについて `CV>0.05` を比較する。閾値は pipeline から呼ぶ `remeasure_until_stable` の既定値で、between-run floor 3% とは別物（`P:1411`、`stability.py:58`、`analyze.py:239`）。

保存すべき field は tps、median_tps、cv、rounds、cv_history、unstable、settled、arm、logical_slot、a／b、元 file path／hash。品質判定の反実仮想で4 repを使う場合、`classify_session(..., expected_reps=5)` を呼んではならない。それは常に rep 欠落を検出してしまう。

### 保存済みデータの読み取り集計

| 集合 | 件数 | median 相対差の最大 | 1%以上 | CV 5% 境界変更 |
|---|---:|---:|---:|---:|
| 試走全 session | 53 | 0.6960% | 0 | 0 |
| LLM 評価9–10＋score1–5 | 7 | 0.3337% | 0 | 0 |

全53件の `rounds` は1。したがって今回は採用 round だけで「第1 round に再測定が必要になるか」の比較ができる。複数 round だった場合、採用 round の tps と CV 履歴だけから全 round の rep1 除外後を再現できるとは限らない（`P:1461`）。

最大差の元 file は `PILOT/ledgers/random/events/000016-evaluation-result.json:1`。lock 待ちがほぼ無い7件の定義は `PILOT/README.md:197`。

較正の within-run 10 rep について、rep1／残り9 rep median−1 は rr5 `+7.0138%`、rr50 `−3.3512%`、rr95 `+2.6023%`。一律に rep1 が高いとは言えない。元 record は `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json:14`。

### P5 への意見

今回のデータは P5 のどちらにも該当しないため、**現行5 rep構成を維持する判断に賛成**。

ただし「いずれか1件が1%超なら warm-up が必要」との因果的断定には反対する。1%は floor の1/3という管理上の感度基準であり、warm-up 原因の証明ではない。閾値を超えた場合の結論は「session 定義変更の要否を設計付きで再提示する」とするのが適切。

D28 の対象は1 run内の冒頭区間の破棄であり、5個の独立 run のうち最初の run を捨てることとは同一ではない。また、rep1 が最大でも4 rep median と5 rep median は一般に同じではない。`PILOT/README.md:185` の「fitness は動かない」は厳密には訂正対象で、今回確認できたのは「動くが最大0.6960%、P5基準未満」である。

## 6. (c) N1：到達条件と report への伝播

### 通常到達しない理由

`C:2604` で投入印を書き、`:2608` で `run_campaign` を呼ぶ。`:2618` の B-5 duplicate 分岐は `summary.skipped>0` に依存する。

`orchestrator/campaign/loop.py:755` 以下では、

1. 既存 WAL の terminal variant を取得。
2. retryable abort を除外。
3. `done` をその集合で初期化。
4. 同 variant が `done` に存在すれば skip（`:876`）。
5. source identity 解決失敗時にも、stock variant が既に `done` にあれば skip（`:820`）。

B-5 は1呼出し1 genome。slot key に cohort／arm／workload／series／kind／n／attempt が入り（`D:156`）、子の `search_config["b5_slot"]` に反映される（`C:3700`）。同じ値の再提案でも slot が違い、retry でも attempt が違う。したがって **fresh・単一 writer の正規運用では既存 terminal を持たず、skip 条件を満たさない**。

これは絶対的な到達不能証明ではない。既存 campaign の持込み、同じ slot の直接再起動、identity／layout の異常等の前提破れを含めれば到達可能性は残る。新たな衝突網羅検査等は作らない。

### 到達した場合

初回 attempt が投入後 skip になった通常の N1 ケース：

| 段階 | 帰結 | 所在 |
|---|---|---|
| 子 | `duplicate-skip` を返す。stock 経路は `skipped` | `C:2618`、`:2379` |
| 分類 | stdout の token を見て `submitted=False` | `D:364` |
| B | `submitted` が false なので増えない | `D:646` |
| 台帳 | `pipeline-submitted` event を追加しない | `D:657` |
| 探索終端 | `proposal-rejected` を記録し `unclassified-missing`、scoreなし | `D:796` |
| report の B 照合 | evaluation-result 件数も terminal B も同じだけ少ないので、この照合は通る | `R:297` |
| sidecar 回収 | `proposal-rejected` が terminal と扱われるため、投入印を回収しない | `R:313` |
| score | endpoint／score不成立により `unclassified-missing` | `R:413` |
| 比較 | `invalid` が別に無ければ `indeterminate-missing` | `R:132`、`:535` |

つまり **N1 自体から invalid が出るとは限らない。B の過少計上は残り、比較は欠測として落ちる**。

先行 attempt で B を既に消費し、retry attempt が skip した場合は `submitted_once` を保持するため挙動が異なる（`D:663`）。「常に B が1少ない」と一般化せず、初回投入 skip と区別する。

別要因で invalid が出る場合、`R:532` は workload／arm で影響を絞る。LLM の invalid はその workload の2比較、random の invalid は LLM対random、scope不明の invalid は広く波及する。欠測も、LLM系列なら両比較、baseline系列なら該当比較に効く。`conditional_superiority` は両比較の連言なので、1比較の欠測でも workload の優越は成立しない（`R:545`）。

**成果物影響の1行：**
「N1 到達時は投入済み B が過少記録され得て report の invalid では検出されないが、当該系列は score 欠測となり、それを含む登録比較の優越判定は成立しない。」

P6 の「コードを変更せず記録」は賛成。この既存不整合と影響を段4で明示的に扱う。

## 7. 費用・k・総 wall 倍率

### 7.1 実測と換算を分離する

重要な訂正：B-8 の約220秒／496秒は **extime 10秒の trace** の検査時間である。B-5 は3秒なので、その秒数をそのまま5倍して B-5 session 費に置く根拠はない。

出所：

- B-8 extime10：`output/insights/2026-09-21/t2807-b8-effective/README.md:94`、`:112`。
- balanced 716万–732万 commit／約217–222秒：同 `verbatim/verify-records.txt:2`。
- read-heavy 約1970万–1995万 commit／約492–501秒：同 `:12`。
- B-5 write-heavy の固有費直接実測：約499–510秒：`PILOT/README.md:197`。
- balanced 3秒 trace の過去較正：無backoff 4,178,321 commit、fixed5 1,581,009 commit：`output/env/pegasus/calibration/a2_perf_verify_cost_t48_skew0p9_rr50_rmw0.json:43`、`:82`。この record の古い verifier wall を現行単価と混ぜない。

session 費は次で分解する。

\[
C_w = C_{\rm build}+C_{\rm legacy}
 +5(C_{\rm trace,w}+C_{\rm verifier,w}+C_{\rm surrounding,w})
 +C_{\rm bench,w}+C_{\rm Tier0}
\]

verifier は `commit数×現行単価` を**換算**として置き、trace 数・edge 構造・候補・環境差の限界を添える。単価は約25–31µs/commitが上記 balanced／read-heavy の実測由来。全 workload 共通の保証値ではない。

| workload | 中心の材料 | 必要な限定 |
|---|---|---|
| write-heavy | B-5 直接実測510秒/session＋Tier0差分 | Tier0前、候補依存、retryなし |
| balanced | 3秒 trace 158万–418万 commit×現行単価、周辺費追加 | genome／verifier版差を跨ぐ換算 |
| read-heavy | B-8の10秒 traceを3秒相当に換算した約590万 commit | 別対象からの時間比例という仮定。B-5実測ではない |

read-heavy の較正 `within_run.median≈10.24M tps` は **trace-disabled** 値である（`between_run_noise_t48_skew0p9_rr95_rmw0.json:13`）。3秒で約3070万 commit と見積もっても、それを trace commit の実測と呼ばない。これは高費用側の感度試算にだけ使う。

### 7.2 候補を出す式

拒否なしの1系列について、

```text
T_nonllm,w = C_stock,w + 10 C_search,w + 5 C_score,w + setup
T_llm,w    = T_nonllm,w + H_w
T_block,w  = 5 C_stock,w + setup
```

H は試走10巡の実測7,360秒、又は10×600–780秒の範囲。A=30 の場合は最大30機会であり、10巡だけの見積りを上限保証にしない（`PILOT/README.md:199`、`T0:129`）。

必要倍率は両方を見る。

\[
k_{\rm need}=\max\left(
 \frac{\max T_{\rm series}}{21259},
 \frac{\max T_{\rm block-stock}}{5447}
\right)
\]

安全余裕・retry・再測定をどこへ何秒足したかを列で残す。品質再測定は bench 部分の追加であり、session 全体の verify を無条件に3倍しない（`P:1411`）。

感度試算として `C_write=510`、`C_balanced=750`、`C_read=850秒`、H=7,800秒を仮定すると、read-heavy LLM は約21,400秒＋setup。**k=2 は十分余裕のある候補**になる。ただしこれは計算例で、採取結果から確定した予測ではない。

高費用側を `C_read=4,700秒` と仮定すると、LLM系列は約83,000秒＋setupで限界に近く、block-stock は23,500秒となり、`k=4.06` の22,115秒を超える。したがって **系列の86,400秒だけでなく stock 側も成立条件**である。

結論は「read-heavy が収まらないと確定した」ではなく、**現資料では収まる見込みを作れるが保証できず、trace commit 推定と stock 費の採取が k の選択を左右する**。不足を n／correctness／session timeout の変更で回避しない。

### 7.3 総 wall 倍率

予測実消費は workload ごとの session 費を用いて、

\[
E \approx \sum_w
  \{36C_{\rm stock,w}+360C_{\rm search,w}
       +180C_{\rm score,w}+15C_{\rm blockstock,w}\}
 +36H+\text{setup・失敗・retry・再測}
\]

とする。各 workload は合計591 session、全体1773（`PR:502`）。

総 wall 倍率の分母を明示する案は、試走 job Elapse 合計61,261秒を論理 session 比で外挿した

\[
E_{\beta,\rm scaled}=61261\times1773/53\approx569.25\ {\rm h}
\]

とすること。これは共有lock込み write-heavy 試走の比例外挿であり、node-local／workload差を直した予測 E とは別欄。上の感度例なら固有費約346時間＋親待ち78時間＝約424時間に追加費を足す。例えば総 wall 管理上限を600時間と提案するなら、分母比約1.054倍と書く。**この600時間は候補例で、承認値ではない。**

要求 walltime の総和 `108W+9W_stock` は予約容量であり、実消費上限の提案と混同しない。k=2 の予約容量は約1302.8 node時間。calendar wall、予約容量、Elapse総和、親の能動作業時間を別々に記載する。

P7 に賛成。最終再提示は、採取した中心推計・保守推計を並べて k=2／3／4.06 の候補から選ぶ。`k_need>4.06` なら束の成立を妨げる事実としてそのまま提示する。

## 8. 変異 matrix 候補

下表の新規 node は計画名。既存 report file を編集せず、A の既存 test file から consumer を呼んで接続を検査する。

| 変異 | 落ちるべき test node |
|---|---|
| registered でも purpose=pilot | `test_b5_generator_contrast.py::test_registered_header_consumed_by_existing_report` |
| registered cohort を pilot にする | 同 `::test_purpose_cohort_mapping` |
| pilot limits 文を変更 | 同 `::test_pilot_header_bytes_unchanged` |
| purpose を run-block-stock へ渡し忘れ | 同 `::test_registered_block_stock_header` |
| block算式を1ずらす | `test_b5_contrast_launch.py::test_registered_schedule_coordinates_and_orders` |
| LLM位置の workload 回転を外す | 同 `::test_registered_schedule_llm_max_four` |
| 2順序交互をやめる | 同 `::test_registered_schedule_six_orders_twice` |
| stage2にもstockを入れる | 同 `::test_registered_stage_job_counts` |
| series番号をtree map keyから落とす | 同 `::test_registered_job_specific_submit_trees` |
| ceilをfloorへ変更／stockにも21259使用 | 同 `::test_registered_walltime_decimal_boundaries` |
| randomへK2を流す | 同 `::test_registered_environment_exact` |
| dry-runでmkdir又はrunnerを呼ぶ | 同 `::test_registered_dry_run_has_no_side_effects` |
| pilot argvにpurposeを追加 | 既存 `test_four_qsub_argv_and_explicit_environment_are_exact`、job test `test_b5_actual_shell_one_driver_and_trap_rc` |
| shellでpurpose検査を外す | `test_p3_s4_loop_job_contract.py::test_b5_purpose_invalid_before_prebuild` |
| shellでregisteredを渡さない | 同 `::test_b5_registered_purpose_reaches_driver` |
| balancedでもrr5を表示 | 新 `test_b5_llm_round.py::test_context_uses_calibrated_workload` |
| aをkとして扱う | 同 `::test_rejected_opportunity_preserves_evaluation_number` |
| 初回へ診断追加／片側だけ診断 | 同 `::test_initial_and_inherited_inputs` |
| null CVを0にする | 同 `::test_critic_missing_metrics_remain_missing` |
| inputsより先にproposal公開 | 同 `::test_proposal_publication_order` |
| 最初のassistant modelだけ採る | 同 `::test_models_collect_all_assistant_ids` |
| metaのagentType／toolUseIdを落とす | 同 `::test_model_record_metadata_and_raw_hashes` |
| prompt JSONの並び／改行を変更 | 同 `::test_pilot_round1_prompt_bytes` |
| commentだけ変更 | 対応する等価変異は SURVIVED |

既存テストの基盤は `test_b5_contrast_launch.py:133`、`test_b5_generator_contrast.py:304`、`test_b5_generator_contrast_report.py:267`、`test_p3_s4_loop_job_contract.py:2040`。

変異の実測・焦点走・受入は親が指定経路で実施する。この plan の静的確認を KILLED／green と報告しない。

## 9. 所有 path と実行順序

### 素集合

| 所有 | path |
|---|---|
| A | `orchestrator/campaign/b5_generator_contrast.py` |
| A | `tools/pegasus/b5_contrast_launch.py` |
| A | `tools/pegasus/p3_s4_loop_pegasus.sh` |
| A | `orchestrator/tests/test_b5_contrast_launch.py` |
| A | `orchestrator/tests/test_b5_generator_contrast.py` |
| A | `orchestrator/tests/test_p3_s4_loop_job_contract.py` |
| A | `tools/pegasus/admission_registry.json` の既存 launcher の reason 更新だけ |
| B | 新 `tools/b5_llm_round.py` |
| B | 新 `tools/b5_llm_round_templates/` |
| B | 新 `orchestrator/tests/test_b5_llm_round.py` と専用 fixture |
| 親 | `output/insights/2026-09-22/t2797-effect-bundle/` |
| 親 | `docs/spool/` fragment |

launcher の登録は現状「4 fixed pilot jobs」と記述されているので reason の更新が必要（`admission_registry.json:34`）。class／evidence は既存 static submitter 分類を維持するなら runbook 投影表の変更は不要（`docs/pegasus-runbook.md:497`）。分類を変える場合はこの計画から勝手に広げず、理由を相談へ返す。

変更しない path は R、C、P、事前登録、role 定義、既存 report test。Tier0／lock／親数／待機時間の作り直しはしない。

### 接点

B が読む契約は既存 header の `schema, cohort, purpose, arm, workload, series, block, perf_config` と、既存 request／slot／events。新しい ledger field を要求しない（`D:555`、`:668`、`:804`）。

A が B に依存する箇所は無い。親が schedule の LLM job と ledger root／materials root／固定 manifest を対応づける。

順序：

1. 段3で P4の事前固定限界、P5の判定表現、P6の非検出、P7の費用換算を攻撃する。
2. 段4で purpose／cohort、schedule順序、tool CLI／出力 schema、費用分母を固定する。
3. A／B は上記所有で実装。接点を変える必要が生じたら先に親へ返す。
4. 親は並行して (b)(c)、環境／較正／旧資料の hash を採取する。
5. A／B 統合後、親が新 CLI の schedule・sweep・prompt資料を生成し、実装 bytes を束へ記録する。
6. 焦点走・変異・受入後に draft JSON／表を完成。Tier0 live 未実施等の限界も埋める。
7. land 後の対象 commit を名指し、k／総 wall の候補と残る限界を1行で再提示する。

D2202 の先例は厳密には「status だけを変更」ではなく、**実験構成値を変えず status を effective にし、承認情報の effective 節を追加する**形である（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/verbatim/d2202.md:6`）。今回は draft までとする。

## 総括

- **計画の要点：** A は pilot 互換を保った registered producer／stage launcher、B は既存 K2 射影を用いる LLM 巡 tool。親が §12 の JSON＋表、schedule、費用、(b)(c) を束ねる。report／pipeline／子の評価経路は変更しない。
- **P1：賛成。** 発効対象の投入・prompt生成経路を具体化する最小実装に限定する。
- **P2：賛成。** 6順序×2、系列の対応、同時LLM≤4を満たす。時間同期と1時間間隔は手順・実行記録で担保する。
- **P3：賛成。** purpose既定pilot、registered cohort定数、pilot header／argv保持。stockのseries=blockに注意。
- **P4：条件付き賛成。** exact ID 記録は実装するが、aliasの将来解決先を保証する機械pinではない。欠測・複数ID・client内部形式を明示する。
- **P5：結論に賛成、基準の解釈を修正。** 読み取り集計は53件で最大差0.6960%、CV境界変更0件。現行構成を維持する。閾値超過をwarm-up原因の証明とはしない。
- **P6：記録のみの方針に賛成、帰結を訂正。** N1はB過少計上をinvalidにせず通す場合がある。比較はscore欠測で判定不能になる。
- **P7：賛成。** B-8引用値は10秒trace。commit数・3秒動作点・verifier版を分けて換算し、seriesとstock双方からkを求める。k=2を中心候補、3／4.06を感度候補とし、未確定費用から承認値を先決めしない。
- **P8：賛成。** 親起動の自動化は作らず、系列ごとのfresh親と手順templateを固定する。
- **P9：賛成。** draft構成とraw hashを保存し、事前登録本文を維持する。将来のeffective節と自己参照禁止を区別する。
- **未確定：** read-heavyのB-5 trace費・stock費、費用余裕と総wall倍率、alias起動と予定exact IDの運用上の扱い、Tier0 live確認、最終land commit、本走認可日／D。これらを「取得済み／承認済み」で埋めない。