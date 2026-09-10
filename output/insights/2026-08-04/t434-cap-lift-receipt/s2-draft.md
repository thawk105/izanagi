現時点では有効な receipt を発行できない。前提 10 件のうち充足済みは P10 のみで、P6 は `NOT_IMPLEMENTED`、残りも未充足だからである（[docs/worklog.md:1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1316)、[docs/decisions.md:7413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:7413)）。以下は独立実装 wave に渡す設計案であり、本 wave ではファイル・定数・gate を一切変更しない。

## receipt schema 案

### 1. 形

receipt は strict canonical JSON とし、未知 key・重複 key・非 UTF-8・非正準 bytes を拒否する。例示は次のとおり。

```json
{
  "approved_max_generations": 2,
  "decision": "APPROVED",
  "prerequisite_statuses": [
    {"id": "P1", "status": "SATISFIED"},
    {"id": "P2", "status": "SATISFIED"},
    {"id": "P3", "status": "SATISFIED"},
    {"id": "P4", "status": "SATISFIED"},
    {"id": "P5", "status": "SATISFIED"},
    {
      "id": "P6",
      "status": {
        "kind": "RESULT",
        "value": "P6Derived"
      }
    },
    {"id": "P7", "status": "SATISFIED"},
    {"id": "P8", "status": "SATISFIED"},
    {"id": "P9", "status": "SATISFIED"},
    {"id": "P10", "status": "SATISFIED"}
  ],
  "ruling_ref": {
    "entry_id": "DNNN",
    "ledger_blob_sha256": "<64 lower hex>",
    "ledger_path": "docs/decisions.md"
  },
  "schema_version": "izanagi-cap-lift-receipt/v1",
  "scope": "p3-autonomous-workload-trial",
  "target_revision": "<40 lower hex commit id>",
  "witness_sha256": "<64 lower hex>"
}
```

`prerequisite_statuses` は可変状態の新しい正本ではなく、人間が承認した時点の分類を receipt に凍結した写しである。P1〜P10 の規範上の定義は D121 の列挙に残す（[docs/decisions.md:5842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:5842)）。

### 2. field 契約

| 名前 | 型・語彙 | 値の出所（一次資料） | 検証法 | 偽造・陳腐化の検出法 |
|---|---|---|---|---|
| `schema_version` | const string `izanagi-cap-lift-receipt/v1` | 将来の receipt schema | exact 一致 | 未知版は推測せず拒否 |
| `scope` | const string `p3-autonomous-workload-trial` | D114 の 3 入口と段 8c supervisor | 別 producer・別実験への流用を拒否 | scope 変更は raw receipt hash と人間導入 commit の履歴検査で検出 |
| `decision` | const string `APPROVED` | receipt を導入する人間 commit | status の意味評価が全件通った場合だけ受理 | 文字列だけでは承認証拠に数えない。人間 commit の履歴契約と組み合わせる |
| `target_revision` | 現行 repository object format に合わせた `^[0-9a-f]{40}$` の full commit OID。短縮 SHA 禁止 | 承認対象となる candidate revision | Git commit として存在すること、receipt 導入 commit の唯一の親がこの commit であることを確認 | 別 revision への付け替え、親違い、非 commit OID、approval 後の関連 closure drift を拒否 |
| `approved_max_generations` | exact JSON integer、`2..MAX_GENERATIONS`。bool 禁止 | 人間裁定と対象 revision の `MAX_APPROVED_GENERATIONS` | 対象 revision の定数、実行時定数、要求 budget の三者を照合。実行は `requested <= min(receipt, current constant)` | receipt より大きい cap への無承認拡張を拒否。CLI 既定値 literal `1` は維持する（[p3_autonomous_workload_trial.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:133)、[同:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1720)） |
| `prerequisite_statuses` | 長さ 10、ID は `P1`〜`P10` をこの順で一度ずつ。P6 以外は `SATISFIED` / `FAILED` | D121 決定 (7)、P4/P6 の改訂は D150 | witness 内の同じ status 列との byte-equivalent な一致と、P ごとの証拠再評価を要求 | 全件を申請者が `SATISFIED` と書いただけでは通さない。証拠閉包・評価器・対象 revision のいずれかが不一致なら拒否 |
| P6 の `status` | discriminated union。`kind=RESULT` の値は `P6Derived` / `P6NotDerived` / `P6NotApplicable` / `P6ContractError`。`kind=NON_APPLICABILITY` の値は `NOT_IMPLEMENTED` / `NOT_CLAIMED` のみ | D138 の 4 値型と D150 の二分（[D138:6744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:6744)、[D150:7396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:7396)） | `kind` ごとに別 enum として検証し、二つの語彙を混ぜない | `P6NotApplicable` は実行結果の一値、`NOT_CLAIMED` は非適用理由であり同義扱いしない。第三の非適用語を拒否 |
| `ruling_ref` | exact object。`ledger_path` は const、`entry_id` は `^D[1-9][0-9]*$`、blob hash は 64 lower hex | cap-lift と D96 手続を記録する将来の新 D | `target_revision:docs/decisions.md` の raw blob hashを照合し、指定見出しが一意に存在することを検査 | 行番号を保存しない。別 D への差替えと台帳 bytes の改変は検出できる。ただし裁定文の意味が十分かは path・D 番号・hash だけでは証明できず、人間審査を要する |
| `witness_sha256` | `^[0-9a-f]{64}$` | 下記 witness manifest の strict canonical raw bytes | 固定位置から bytes を再取得して SHA-256 を再計算し、receipt の status/cap と witness 内の写しを比較 | hash 自体は意味的充足を証明しない。証拠 closure の再評価まで通らなければ拒否 |

`approved_max_generations` は裁定 (175) の最小 4 field への追加を推奨する。これが無いと「2 世代を承認した receipt」で 10 世代まで許せるかを consumer が判定できない。

`approved_by` や自由記述の `reason` は v1 receipt に入れない。文字列を自己申告しても人間性や正当性を検証できないためである。承認者の事実は後述する導入 commit と `ruling_ref` から検証する。

### 3. P6 の受理写像

D138 が参照する 4 値名は既存設計正本に明記されている（[P6 contract:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/insights/2026-08-03_t244-p6-contract/README.md:118)）。cap-lift validator の既定は次とする。

- `NOT_IMPLEMENTED`、`P6NotDerived`、`P6ContractError` は拒否。
- `P6NotApplicable` は cap-lift への写像が現行裁定から一意に書けないため、追加裁定まで拒否。
- `P6Derived` は、意味的充足契約と実 witness の再評価が通った場合だけ候補になる。
- `NOT_CLAIMED` は D150 上は免責だが、多世代開放を許すかは未裁定である（[docs/decisions.md:7441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:7441)、[docs/worklog.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:97)）。V1 裁定までは拒否する。

この表現は [T-433] の未確定 field を要求しない。T-433 が後で意味的充足契約を確定しても、receipt は同じ P6 union と汎用 evidence closure のまま使える。

### 4. witness manifest

`witness_sha256` の実体は `izanagi-cap-lift-witness/v1` とし、少なくとも次を束縛する。

- `approved_max_generations` と P1〜P10 の status の receipt と同一な写し。
- D121・D138・D150・cap-lift 用新 D の規範 bytes。
- P ごとの実 artifact、入力 digest、評価結果、評価器 source hash。
- receipt validator と consumer 6 面の source/schema closure。
- 全 evidence path の target revision 上の raw SHA-256。

`target_revision` は witness 自身には重複格納しない。witness が同じ target commit に含まれるため、commit OID を witness に書くと自己参照になる。receipt が `target_revision` と `witness_sha256` を対で束縛する。

各 P の最低検証対象は次とする。現行 tree に実成果物が無いものは、path 名や test node 名を仮置きせず「検証不能」として `SATISFIED` を禁止する。

| P | `SATISFIED` と書くための照合 |
|---|---|
| P1 | 固定 5-bit IR、全 32 mask の独立 golden、production emitter、自由 `implementation` を拒む実入口、WAL/report identity の一致。現状は IR 部品だけで production 未結線（[docs/worklog.md:1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1317)）。 |
| P2 | untrusted role が受け取る全 observable surface の閉集合と、実効 diff / IR SHA が出ないことの負例。現状は 0-bit end-to-end 証明の閉集合自体が未定義（[docs/decisions.md:6796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:6796)）。 |
| P3 | authority manifest、単一 in-flight、CAS、crash replay、削除耐性を同一 ledger の durable event から再生し、producer/P7 consumer まで到達すること。設計・裁定だけでは不可。 |
| P4 | batch cardinality、query/replicate ordinal、全候補事前 commit、seal 前結果非公開、早期停止 tombstone、evidence digest の完全一致。P4 は無条件義務（[docs/decisions.md:7378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:7378)）。 |
| P5 | 実入口で provider/drive/preview 注入、role session 共有、未予約 token が拒否され、journal と再検証器が同じ結果を返すこと。現状は部分実装（[docs/worklog.md:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/worklog.md:1323)）。 |
| P6 | D138 の 4 値出力そのもの、source witness、validation matrix、generator closure、正負 calibration、未知 witness-kind の拒否を再評価する。空 handler・恒真 assert・test node 名だけは証拠に数えない。 |
| P7 | formal consumer の実入口が origin proof 欠落・改変・別 origin splice を拒否する正負 artifact。helper 単体の未接続テストは不可。受理集合を狭めるため D96 必須。 |
| P8 | 1 世代運転、runbook 3.1/3.2、reflux on/off ablation の既存受理結果と proof chain が、結線前後で不変である対照 artifact。3.3 は対象外。 |
| P9 | whiteboard の値域と iteration/WAL の全単射、未知値・欠落・重複・順序逸脱の負例。単なる schema 宣言では不可。 |
| P10 | 予算値・origin authority・軸 (iii) の三裁定を、該当 D/worklog の exact bytes と導入履歴に照合する。これは人間 gate であり、機械は裁定文の存在・同一性までしか証明できない。 |

## 置き場所と改訂契約

### 置き場所

- schema: `orchestrator/campaign/cap_lift_receipt_schema.json`
- reader/verifier: `orchestrator/campaign/cap_lift_receipt.py`
- witness: `output/cap-lift/witnesses/<witness-sha256>.json`
- receipt: `output/cap-lift/receipts/<receipt-raw-sha256>.json`
- 任意の失効 tombstone: `output/cap-lift/revocations/<receipt-raw-sha256>.json`

cap-lift は campaign 単位でなく複数 campaign に効く人間承認なので、個別 `campaigns/<id>` や保護外の `exploration/autonomous-trials` へ正本を置かない。現行説明でも後者の journal は正式 proof chain ではない（[output/README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/README.md:24)、[同:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/README.md:49)）。

### 誰が書くか

1. 独立実装 wave が candidate revision `G` に schema、validator、witness、D96 の新 D、境界テスト、consumer 結線、必要な再事前登録を置く。この時点では receipt 不在なので、多世代要求は必ず拒否される。
2. 人間が `G` を確認し、`A` で receipt 一ファイルだけを追加する。
3. `A` は非 merge、親がちょうど `G`、diff が receipt の create-only 追加だけ、commit message が逐語 `AI-Agent: none` を一度だけ持つことを要求する。
4. runtime HEAD は `A` の子孫でなければならない。

これは既存の ratified-freeze が採る「approval を candidate から分離」「strict canonical JSON」「人間 commit の導入履歴検査」と同型である（[s8b_ratified_freeze.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:106)、[同:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:404)、[同:525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:525)、[同:1173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/s8b_ratified_freeze.py:1173)）。

`AI-Agent: none` は repository の provenance 契約を第三者が再検証できるが、暗号学的な本人確認ではない。悪意ある committer まで threat model に含めるなら、署名済み commit と許可鍵 registry が別途必要であり、現行一次資料からその trust root は書けない。

### 凍結・改訂

- receipt と witness は content-addressed、create-only、in-place 編集禁止。
- consumer は「最新」を探索せず、CLI/API で明示された receipt SHA だけを読む。
- 同じ path に別 bytes が履歴上一度でも現れる、削除後に再導入される、導入 commit が複数ある場合は拒否。
- revision、status、cap、裁定の変更は新しい witness と新しい receipt を発行する。
- 旧 receipt の効力を止める場合は人間 commit で revocation tombstone を追加する。新 receipt の存在だけで旧 receipt を暗黙失効させない。
- witness closure のどれかが runtime HEAD で変われば stale として拒否し、関係のない commit だけなら継続利用できる。
- P4 の無条件性を緩める裁定は D150 決定 (2-b) の遷移契約を満たし、新 receipt を発行しなければ既存判定へ作用させない（[docs/decisions.md:7391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:7391)）。

## consumer 結線 6 面

### 1. runbook

- **現状の file:line:** 3 入口の上限 1、P1〜P10、P4/P6 の扱いは [docs/phase3-s8c-autonomous-trial-runbook.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:104) と [同:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:118)。成果物と完全性 CLI は [同:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:131) と [同:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-s8c-autonomous-trial-runbook.md:150)。
- **結線案:** 多世代コマンドだけ `--cap-lift-receipt-sha256 <64hex>` を必須にし、固定 path を導出する。事前確認、実行、事後 completeness 再検証の三箇所で同 SHA を使う。1 世代例と literal default `1` は変えない。
- **receipt 不在・不整合時:** コマンドを開始しない。要求 budget を暗黙に 1 へ下げず、明示エラーで停止する。事後に不整合が判明した run は protocol-invalid とし、再実行まで主張・集計へ入れない。
- **実装 wave に送る事項:** runbook の例、エラー診断、revocation/stale の復旧手順を validator と同じ変更単位で更新する。

### 2. 事前登録文書

- **現状の file:line:** 主実験への拘束力は [docs/phase3-main-experiment.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-main-experiment.md:1)、旧 on/off 還流定義は [同:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-main-experiment.md:40)。過去の実質改訂・既知結果開示の作法は [同:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-main-experiment.md:116) と [同:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/phase3-main-experiment.md:234)。同文書の bytes は [output/s1-freeze/known_axes_freeze.json:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/output/s1-freeze/known_axes_freeze.json:623) が pin する。
- **結線案:** 本 wave では変更しない。将来、同文書の明示的な再事前登録手続として、既知結果台帳、承認 cap、valid receipt 必須条件、多世代 on/off arm、receipt 不一致時の判定不能を改訂する。文書には特定 receipt hash を自己参照させず、「対象 revision を人間 receipt が承認していること」を条件化する。
- **receipt 不在・不整合時:** 多世代 cell は事前登録に適合しない。後付け receipt、1 世代データへの格下げ、記述統計への流用を認めない。
- **実装 wave に送る事項:** 直接追記ではなく、ユーザー承認を伴う再事前登録、known-result 境界の開示、S-1 freeze の再生成・repin・closure 検査を一単位にする。現行 bytes の単独編集は禁止。

### 3. journal

- **現状の file:line:** `AttemptJournal` は append-only/fsync（[p3_autonomous_workload_trial.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:461)）。`run-start` は budget を記録するが receipt は無い（[同:1624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1624)）。consumer は event kind を閉じている（[autonomous_trial_completeness.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:40)）。
- **結線案:** 新 event を増やさず、`run-start.cap_lift_receipt` に receipt body + `receipt_sha256` の detached canonical projection を置く。budget=1 では field 不在、budget>1 では必須とする。
- **receipt 不在・不整合時:** `run_trial()` の upfront 検査では run root/journal 作成前に拒否する。開始後に bytes が消失・変異した場合は terminal report を公開せず、残った journal を不完全試行として保持する。
- **実装 wave に送る事項:** journal/report の完全一致、receipt raw bytes の再読、status/cap/target の改変負例を追加する。新 event 方式を採る場合は `_EVENTS` と順序契約の変更が増えるため非推奨。

### 4. report

- **現状の file:line:** supervisor report は [p3_autonomous_workload_trial.py:1168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1168) で構築され、`run-finish` と journal hash を束縛して completeness 後にだけ書く（[同:1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1201)）。
- **結線案:** report schema version を上げ、budget>1 では top-level `cap_lift_receipt` を必須にする。値は `run-start` の detached projection と exact 一致させる。
- **receipt 不在・不整合時:** `_write_json_atomic()` に到達させない。保存済み report の独立再検証時に receipt/witness が消失・revoked・stale なら report を不受理にする。
- **実装 wave に送る事項:** journal と report の片側だけの挿入、receipt SHA・target・cap・P status の一箇所改変、検査後の receipt 交換をすべて負例にする。

### 5. 層 3

- **現状の file:line:** build cell は supervisor report より先に Layer 3 を生成する（[p3_autonomous_workload_trial.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1027)）。renderer は `campaign.lock.search_config` を読む（[layer3_report.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:390)）一方、現行 v3 schema に cap receipt field は無い（[layer3_schema.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_schema.json:5)）。
- **結線案:** `_campaign_for()` の `search_config` に `cap_lift_receipt_sha256` を入れ、campaign ID の preimage に束縛する（現行 budget の結線点は [p3_autonomous_workload_trial.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:503)）。新規 Layer 3 は v4 とし、budget>1 のとき detached receipt を top-level 必須 field にする。
- **receipt 不在・不整合時:** renderer は `Layer3ReportError` とし、create-only 出力を作らない。歴史 v2/v3 は読み取り可能なまま残すが、多世代承認の証拠には使わない。
- **実装 wave に送る事項:** schema v4、renderer の再読、campaign lock → Layer3 → supervisor report の三者一致、fresh rebuild 深比較を更新する。現行 v2/v3 を再生成しない契約も維持する（[layer3_report.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/layer3_report.py:16)）。

### 6. producer + completeness gate

- **現状の file:line:** 共通 validator は [p3_autonomous_workload_trial.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:249)。direct `_run_workload()`、公開 `run_trial()`、CLI の検査位置はそれぞれ [同:1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1245)、[同:1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1554)、[同:1740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/p3_autonomous_workload_trial.py:1740)。completeness の二 gate は run-envelope [autonomous_trial_completeness.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:438) と campaign-chain [同:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/campaign/autonomous_trial_completeness.py:1030)。
- **結線案:** CLI は receipt SHA、二つの programmatic API は同じ SHA 引数を明示必須にする。環境変数・自動探索・provider 例外は作らない。3 入口は build/config/journal の副作用前に同じ pure verifier を呼ぶ。completeness は保存済み SHA から receipt/witness を独立に再読する。
- **receipt 不在・不整合時:** `generations>1` を常に拒否し、1 へ downgrade しない。定数だけ monkeypatch/変更しても開かない。budget=1 は receipt 不在で従来どおり受理し、余分な receipt 指定は曖昧性を避けて拒否する。
- **実装 wave に送る事項:** 現行の「定数だけを 2/3 に monkeypatch して多世代を通す」テスト（[test_p3_autonomous_workload_trial.py:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_p3_autonomous_workload_trial.py:644)、[test_autonomous_trial_completeness.py:808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/orchestrator/tests/test_autonomous_trial_completeness.py:808)）を receipt fixture 必須へ更新する。欠落・偽 hash・P4 非適用・P6 `NOT_IMPLEMENTED`・wrong parent・AI commit・revoked・witness drift を境界テストにする。

この結線は現在の multi-generation 受理集合を広げ、同時に「定数だけ変えれば通る」集合を receipt 必須へ狭める。したがって実装 wave は D96 の「新 D + 境界テストを同じ変更単位に置く」を必ず満たす（[docs/decisions.md:4269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-cap-lift-receipt/docs/decisions.md:4269)）。本 wave ではその機械 gate を新設しない。

## 設計択一

1. **receipt と witness の構成**

   - A: 一つの巨大 receipt に全 evidence を埋め込む。
   - B: 小さい人間 receipt と content-addressed witness を分離する。
   - **推奨: B。** 人間判断と機械証拠を分離でき、journal/report/Layer3 には小さい detached projection だけを運べる。

2. **人間承認の実証**

   - A: `approved_by` 文字列だけを receipt に書く。
   - B: 非 merge・親一意・receipt だけを追加・逐語 `AI-Agent: none` の導入 commit を検証する。
   - C: 署名済み commit と許可鍵 registry を新設する。
   - **推奨: B。** 現行 repository の既存契約と整合する。暗号学的本人性が必要なら C は独立裁定にする。A は不採用。

3. **receipt の選択**

   - A: `latest.json` / 最大 cap / 最新 commit を自動選択する。
   - B: caller が receipt SHA を明示し、固定 path を導出する。
   - C: active pointer の人間承認連鎖を新設する。
   - **推奨: B。** 選択規則が最小で、古い receipt の暗黙再活性化を避けられる。A は不採用。C は複数同時 policy が必要になった場合だけ再検討する。

4. **journal 結線**

   - A: `run-start` に receipt projection を加える。
   - B: 新しい `cap-lift-admission` event を追加する。
   - **推奨: A。** 既存 event 閉集合と開始順を増やさず、run/report envelope の比較に直接載せられる。

5. **Layer 3 の表現**

   - A: `workload.search_config` の receipt SHA だけに依存する。
   - B: campaign identity に SHA を束縛したうえで、v4 top-level に detached receipt を明示する。
   - **推奨: B。** 材料レポート単体から承認対象・cap・P status を監査でき、fresh rebuild でも照合できる。

6. **`NOT_CLAIMED` の cap-lift 可否**

   - A: T-434 で global/per-run の意味を先取りする。
   - B: schema は二語彙を保持し、V1 裁定までは admission を拒否する。
   - **推奨: B。** [T-433] と並行する未確定判断を receipt field へ埋め込まず、D150 の fail-closed を維持する。

7. **事前登録の順序**

   - A: receipt 発行後に文書を直接追記し、既存 freeze を放置する。
   - B: candidate revision に正式な再事前登録と freeze 再発行を含め、その revision を人間 receipt が承認する。
   - **推奨: B。** 自己参照を避け、承認対象 revision が事前登録 bytes まで含む。A は S-1 pin を破るため不採用。

## 総括

cap-lift receipt は、小さい content-addressed 人間承認 record と、P1〜P10 の再評価可能な witness manifest に分ける。  
人間承認は申請文や test 名でなく、対象 revision を親に持つ create-only の人間 commit で発効させる。  
6 consumer は同じ receipt SHA を journal・report・campaign identity・Layer 3 へ投影し、欠落・不一致・陳腐化時は多世代要求そのものを拒否する。  
現状は P10 以外が未充足なので receipt 発行不能であり、`MAX_APPROVED_GENERATIONS = 1` は不変。pytest は実行していない。