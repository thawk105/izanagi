必須 3 ファイルはすべて全文を読めた。結論として、T-327 は「宣言物を一切作らず、checkout から発効状態を導出する judge」と「条件契約の世代別 hash ledger」に分けるのが安全である。sandbox は read-only のまま使用し、ファイル変更・pytest 実走は行っていない。

## 先に訂正すべき前提

- [brief.md](/work/1/SFC/tanab/dev-wave-jobs/t327-prereg-activation/brief.md:3) の P1〜P6 は整合している。ただし P2 の発効 commit と §5 manifest を相互に hash 参照させると自己参照になる。文書には manifest の path と 6 cell 内容だけを置き、後続 commit の manifest が「最後の文書変更 commit」を記録する二段構成にする。
- [phase3-8c-preregistration.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:44) は generation budget 裁定を未解決としているが、[archive worklog](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0803-122.md:8) で T-324 は裁定済みである。§6 条件 11 は、実装後の現在地では唯一 SATISFIED にできる候補である。
- 同文書 [123-133 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:123) の「1〜12 はいずれも未充足」「自動発効しない」は裁定後には誤り。
- 条件 9 の「Layer 3 は任意 CLI」の診断も古い。[p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:1029) は report publish 前に生成し、[1216-1225 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:1216) は深い chain 検査も呼ぶ。ただし T-325 の正式 registry acceptance にはまだ結線されていないため、条件 9 自体は未充足と判定する。
- 条件 12 の「Pegasus を拒否」も古い。同ファイル [980-1026 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:980) は transport opt-in を受ける。一方、単一 allocation/node/process の実 consumer は依然ない。
- D124 の送り先 `[T-321]` は明白な誤参照で、[decisions.md:6073-6076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/decisions.md:6073) は前方訂正で T-327 に直すべきである。
- 現 checkout には `orchestrator/campaign/trial_registry.py` が存在しない。並行 branch tip `de6e1b` では実装されているが、その `:4-6` は arm を「宣言しただけで実際に走った arm は認証しない」、`:128-129` は `certifying=False / arm_binding="declared-only"` と明記する。したがって条件 2 を T-325 の存在だけで green にしてはならない。

## 発効モデル

発効状態は保存しない。純関数の最終式を次に固定する。

```text
effective(H) =
    condition_freeze_valid(H)
    AND section5_all_typed_and_filled(H)
    AND exact_predicate_ids(H) == {C01, ..., C12}
    AND every(predicate.status == SATISFIED)

activation_commit(H) =
    git rev-list -1 H -- docs/phase3-8c-preregistration.md
```

- `H` は CLI 起動時に一度だけ捕捉した HEAD。
- `approval.json`、`active.json`、承認 commit、activate/revoke コマンドは作らない。
- `check` CLI は発効を「起こす」のではなく、既に導出される状態を観測するだけ。
- `UNSATISFIED`、`EVIDENCE_UNDEFINED`、`ERROR`、`NOT_EVALUATED` はすべて false。`NOT_APPLICABLE` は設けない。
- 成功時だけ private seal 付き `EffectivePreregistration` を返す。公開 constructor は置かず、将来の launcher は bool でなくこの型を要求する。
- `ActivationReport` は `observed_head`、`activation_commit`、freeze generation/hash、§5 所見、C01〜C12 の所見と証拠 path/blob hash/reason code を持つ。

P6 により今 wave では launcher を止められない。CLI と invariant test は真の consumer だが、production enforcement ではない。この限界は文書と worklog に明記し、T-325 land 後の gate 結線を独立タスクにする。

## Markdown の正規化規則

### §5 の抽出

現構造は [79-91 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:79) の H2、2 列 GFM 表、9 data row である。

1. UTF-8 のみ。CRLF/CR を LF、Unicode を NFC にする。
2. fenced code 内を除き、ATX H2 の数字 prefix `5` と `6` を同定する。見出し全文には依存しない。
3. §5/§6 の欠落、重複、逆順、H3 化、Setext 化は明示的 parse error。別節へ沈黙してフォールバックしない。
4. §5 は header を正規化後に `欄` / `値` の exact 2 列、delimiter は GFM の 3 個以上の `-` と alignment marker だけ許す。
5. table splitter は backslash escape と backtick code span 内の `|` を列区切りにしない。raw HTML、複数表、結合セル風記法は拒否する。
6. 欄名は Markdown delimiter を除き、NFC、前後 trim、連続空白を 1 ASCII space にする。重複・空欄を拒否。
7. 欄名集合 hash は欄名を UTF-8 byte 順に sort した canonical JSON に domain separator を付けて計算する。行の並べ替えだけでは変わらない。
8. 値は単なる「非空」で埋まったと扱わない。`未記入` と現在の括弧付き variant は UNFILLED、それ以外も field ごとの型 schema を通らなければ INVALID。
9. 値の推奨形式は単一 code span 内の canonical JSON。budget、env、floor、seed/schedule、検定方式、未既知性 receipt、swapped map、manifest、責任者/開始予定を別 schema にする。
10. 6-cell manifest 行は `path + 6 cell の宣言内容` を持たせるが manifest 自身の hash や prereg commit は文書に埋めない。後続 manifest が activation commit を記録することで自己参照を避ける。

### §6 の抽出

現構造は [93-121 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:93) の H2 と、折返しを含む top-level ordered list 1〜12 である。

- fenced code 外の `0〜3 spaces + ASCII number + "." または ")"` だけを top-level marker とする。
- 番号は exact `1..12`。欠番、重複、13 番、nested list による置換を拒否。
- 各項目は次の top-level marker までの全 continuation line を含む。太字の先頭句だけを hash してはならない。
- NFC、改行・tab・連続 Unicode 空白を 1 space に正規化し、balanced な emphasis/code-span delimiter だけを除く。文字、数字、句読点、inline-code の内容は保存する。
- link、image、HTML comment、reference definition、unclosed fence/code span は意味を隠せるため拒否する。
- 改行位置、空白量、太字化だけは同じ hash。語、数値、否定、句読点、条件順の変更は別 hash。
- status paragraph と後続 H3 は条件 hash に含めない。
- canonical JSON は `[{number:1,text:"..."},...,{number:12,...}]`。番号も hash preimage に含める。

## 条件 ledger

推奨 path は `output/s8c-preregistration/condition-freeze.v1.gN.json`。

各 generation は次の exact schema とする。

```json
{
  "schema_version": "s8c-prereg-condition-freeze/v1",
  "normalization_version": "s8c-prereg-markdown/v1",
  "generation_number": 1,
  "supersedes_sha256": null,
  "source_path": "docs/phase3-8c-preregistration.md",
  "section5_field_names_sha256": "...",
  "section6_conditions_sha256": "...",
  "evidence_contract_sha256": "...",
  "condition_set_sha256": "...",
  "revision_reason": "T-327 initial automatic-activation contract"
}
```

- g2 以降の `supersedes_sha256` は直前 generation の normalized condition hash ではなく、record の raw bytes SHA-256。
- current record 自身の SHA、導入 commit、activation commit は field に置かない。いずれも外から導出する。
- side-by-side の連番 file とし、既存 file を上書きしない。mutable JSONL tip は採らない。
- strict JSON、duplicate key/NaN/unknown key/noncanonical encoding を拒否する。
- HEAD ancestry 内で各 generation path の blob が一種類だけ、導入 commit が一意・非 merge、削除再追加なしであることを検査する。
- g1 後の各 parent→child で §5 欄名 hash、§6 条件 hash、推奨する evidence contract hash のいずれかが変わったら、同じ child commit でちょうど次の gN が追加されなければならない。
- 変更後に元へ戻しても、中間 commit の無記録変更を検出して赤にする。
- gN 追加なのに保護対象 hash が変わっていない場合も spurious revision として拒否する。
- shallow repository、replace refs、grafts を拒否。履歴走査は `git cat-file --batch` を使い、commit ごとに subprocess を起動しない。
- namespace 内の未知 file、approval、active pointer、revocation を closed-world 違反として拒否する。

結果後の条件緩和は、記録なしなら lineage 検査、記録ありなら activation commit の更新によって検出する。旧 manifest の `prereg_commit` は新 activation commit と一致しなくなり、旧 measurement HEAD は新 commit の子孫でないため条件 8 が赤になる。Git 履歴自体を完全に作り直す攻撃は外部署名 anchor がなければ検出できない、という限界は残す。

## 8b 機構の再利用境界

|既存面|再利用するもの|8c へ流用しないもの|
|---|---|---|
|[s8b_holdout_freeze.py:27-74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:27)|`HOLDOUTS` の実値、規模、`search_repository`、positive control|8c 固有の軸値複製、`output/s8c-*` の scan 除外|
|[同:179-212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_holdout_freeze.py:179)|tracked/untracked 全 file の git 列挙という事実|「新 artifact は hash だけだから多分安全」という推定|
|[s8b_ratified_freeze.py:398-416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_ratified_freeze.py:398)|strict JSON、canonical bytes、typed error の設計パターン|private helper の直接 import|
|[同:319-338,469-494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_ratified_freeze.py:319)|H 固定、shallow/replace/grafts 拒否、一意導入、immutable history|`AI-Agent: none` を要求する user-commit 判定|
|[同:1198-1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/s8b_ratified_freeze.py:1198)|連番・前 hash chain の考え方|approval、active pointer、revocation、明示 activation commit|
|[freeze-permanent-design.md:93-104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/freeze-permanent-design.md:93)|side-by-side generation|G/R/A/X の人間承認 topology|
|[8b design §8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8b-descriptor-design.md:255)|8b 所有項目を変える場合の再凍結・ユーザー承認|8c 条件充足そのものへの都度承認|

8c の条件改訂が同時に holdout、gate、floor、判定基準など 8b 所有事項を変える場合は、8c ledger を追加しても 8b §8 の承認を迂回できない。

## 12 述語の証拠契約

配置は新設 `s8c_preregistration_evidence.py` の予定行である。

|ID・予定行|SATISFIED に必要な実証拠|最小 negative control|現状見込み|
|---|---|---|---|
|C01 `:120-159`|`s8b_holdout_freeze.HOLDOUTS` を入力に、正式 binding ごとに `_campaign_for`、`_perf_for`、`_descriptor_for` を実行し、3 経路すべてが 1m/48 と同じ workload projection を返す。|`_perf_for.records` だけ 100k に戻す。|現行 [505-561 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:505) は 100k/4 なので赤。|
|C02 `:160-204`|sealed trial binding の arm が run-start journal、terminal report、campaign-ID preimage、proposal path、全 invocation ID に入り、6 cell の全 identifier が injective。production sink までの data-flow も確認。|proposal path だけ arm を除き on/off を衝突させる。|T-325 は declared-only なので EVIDENCE_UNDEFINED。|
|C03 `:205-249`|§5 の manifest path/content、T-325 の strict manifest loader、exact 6 Cartesian cells、committed registry の manifest hash/prereg commit/trials、HEAD までの strict prefix history。|1 cell を削除、または manifest 外 trial を registry に足す。|T-325 land と実 manifest/registry が揃うまで未充足。|
|C04 `:250-289`|任意の 1 crash から実験全体 6 cell を `indeterminate` にする terminal policy、同一 prereg experiment/trial の二度目の開始を registry が拒否する code path。|1 crash 後も残り 5 cell を certifying に保つ。|現行 [1118-1164 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/p3_autonomous_workload_trial.py:1118) は cell 単位 partial なので赤。|
|C05 `:290-329`|committed schedule artifact に master seed、6 cell order、arm、holdout、`search_space_sha256`、`initial_state_sha256`。seed からの独立再生成が exact bytes と一致し、全 arm の後二 hash が同じ。|off arm 1 件の initial-state hash を 1 bit 変更。|schedule schema/artifact がないため未定義。|
|C06 `:330-374`|§5 budget 値、8c 専用 ledger の manifest/freeze/schedule binding、全 6 arm の事前予約、実 bench 秒精算、予算不足時に未実施 arm 全体を対称に indeterminate にする production consumer。|swapped/H2 の予約を外す、または不足後に別 arm だけ継続。|`--max-wall-seconds` は代替不可。`s8b_budget.py` の考え方は再利用可だが、その存在だけでは赤。|
|C07 `:375-419`|H1/H2 別 floor artifact の path/hash/env/measurement head、実 bytes の verifier、formal judge の exactly 3 conditions、exact 6-cell result table、production consumer。|H2 floor または結果表 1 cell を削除。|8c floor 成果物・judge 不在で未定義。|
|C08 `:420-464`|導出した activation commit と actual manifest `prereg_commit` の完全一致、run-start/report/manifest の 3 field 一致、measurement HEAD の子孫性、historical manifest/registry bytes。単なる古い祖先は不可。|manifest に activation commit の親 commit を入れる。祖先検査だけなら通るが C08 は落ちる。|T-325 land 前は未定義。|
|C09 `:465-504`|正式 authority である registry acceptance が全 build report に `assert_campaign_layer3_chain` 相当を必須実行し、欠落/no-build を certifying にしない。|formal acceptance から layer3 call を 1 個除く。|producer 側は改善済みだが正式 acceptance 側が未結線なので赤。|
|C10 `:505-554`|supervisor の `input_payload_sha256`、`raw_response_path/sha256`、provider payload/envelope、proposal bytes/hash、campaign WAL の build/bench record、Layer 3 `artifact_refs/source_refs/admission_decision` を一つの authoritative verifier が再読して結ぶ。|raw response または proposal の 1 byte を変え、記録 hash は据え置く。|現行は proposal hash と supervisor↔campaign 全 chain が閉じず赤。|
|C11 `:555-589`|tracked [worklog:8-11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/archive/worklog-phase3-0803-122.md:8) の blob/正規化 ruling hash と、「budget=1 formal 禁止、複数世代・critic 還流・標本設計を先行」の exact policy。|ruling を budget=1 許可へ反転、または先行条件を削除。|SATISFIED 候補。`MAX_APPROVED_GENERATIONS=1` の存在自体は証拠にしない。|
|C12 `:590-634`|§5 env、`env_contract.lookup`、calibration、実 allocation attestation/reservation、single node/process/no-resume を強制する launcher wrapper の production call path。|`single_process=False` または `allow_resume=True`、もしくは wrapper call を削除。|[env_contract.py:6-9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/campaign/env_contract.py:6) 自身が「宣言だけでは強制しない」と明記するため赤。|

C06/C07/C09/C10/C12 は、consumer が見つからなければ `EVIDENCE_UNDEFINED` にする。「consumer がないので反例もない」という全称命題にはしない。

## ファイル別の配置計画

### 新設コード

- `orchestrator/campaign/s8c_preregistration.py:1-770`

  - `:1-45` path、schema、domain separator、closed ID 集合。
  - `:46-105` typed findings、`ActivationReport`、sealed `EffectivePreregistration`。
  - `:106-240` fenced-code-aware Markdown lexer、H2/table/list parser。
  - `:241-330` normalization、field-name/condition/combined hash、§5 typed extraction。
  - `:331-525` HEAD snapshot、git blob reader、generation/history/revision verifier。
  - `:526-610` exact conjunction を独立再計算する純関数。
  - `:611-700` create-only `prepare-revision`。新 gN 以外を書かない。
  - `:701-770` `check` / `prepare-revision` CLI。`approve` / `activate` / `revoke` は置かない。

- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:1-300`

  - `:1-15` schema/normalization version。
  - `:16-110` field-name 個別 hash → §5 value schema/evidence key。欄本文は複製しない。
  - `:111-300` C01〜C12 の required artifact kinds、field paths、consumer requirements、negative-control ID。
  - JSON の意味 canonical hash を gN が pin する。formatting-only JSON 変更では hash を変えない。

- `orchestrator/campaign/s8c_preregistration_evidence.py:1-690`

  - `:1-119` contract loader、Git/code/artifact probe 共通部。
  - `:120-634` 上表の C01〜C12。
  - `:635-690` exact registry と全所見収集。import/API 不在を success でなく EVIDENCE_UNDEFINED にする。
  - holdout の実値は import し、三軸 canonical literal をこの source に複製しない。

### 新設 artifact

- `output/s8c-preregistration/condition-freeze.v1.g1.json:1`

  親が条件文と §5 schema を確定した後、generator で一行 canonical JSON を作る。手入力しない。本文、axis 値、approval field、self hash を含めない。

### 新設テスト

- `orchestrator/tests/test_s8c_preregistration_core.py:1-450`
- `orchestrator/tests/test_s8c_preregistration_predicates.py:1-420`
- `orchestrator/tests/test_s8c_preregistration_invariant.py:1-180`

### 既存 docs の変更

[phase3-8c-preregistration.md:3-4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/docs/phase3-8c-preregistration.md:3) の現行は「凍結機構は使わず、git commit した 1 枚」。差分は「8b の approval/pointer 型凍結は使わないが、8c 条件契約の hash ledger は使う」と限定して書き換える。

同ファイルではさらに次を行う。

- `:24-35` に `observed HEAD`、`activation commit`、後続 manifest との二段 binding を記載。
- `:44-48` を T-324 裁定済み、cap-lift 実装は未完へ訂正。
- `:79-91` の前に §5 value JSON grammar と UNFILLED/INVALID の区別を追加。
- `:95-121` は normative な 12 条件を弱めず、現在地の古い診断だけを訂正してから g1 を発行。
- `:123-124` の静的「全件未充足」を削除し、状態は CLI report から導出すると記載。
- `:126-133` を自動発効式、ledger 改訂、approval 不要、production gate 未結線の限界へ全面置換。

[output/README.md:20-24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/output/README.md:20) は現在 s8b freeze までしか列挙しない。ここへ `s8c-preregistration/` を「条件契約 hash の immutable generation、発効宣言物ではない」と追加し、[36-39 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/output/README.md:36) に lifecycle を追記する。

- `docs/spool/decisions/2026-08-04-dev-wave-t327-prereg-activation-1.md:1-45` を新設し、自動発効、条件 ledger、8b approval 非流用、D124 の T-321→T-327 erratum を前方決定として記録する。`docs/decisions.md` の既存 bytes は直接変更しない。
- `docs/spool/worklog/2026-08-04-dev-wave-t327-prereg-activation-1.md:1-50` は完了段でのみ作る。実測した test/checker 結果だけを書き、T-325 後の launcher gate follow-up を新規 task として残す。事前に green 文言を置かない。

### 誤操作抑止 hook

[guard_write.py:106-116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/hooks/guard_write.py:106) は s8b namespace だけを拒否する。

- `:117-128` に s8c namespace の直接 Write/Edit 拒否を別 branch で追加する。理由文に「人間承認」を入れず、「generator の exclusive-create 経路へ限定する誤操作抑止」とする。
- `:145-147` の fails-closed token 集合へ `output/s8c-preregistration` を追加。
- [hooks/README.md:53-57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/hooks/README.md:53) に、これは認証・発効条件ではなく Codex にも未配線である旨を追記。
- [test_hooks.py:184-204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/tests/test_hooks.py:184) の後へ、s8c 直書き拒否と namespace 外許可のテストを追加。

hook は Bash を完全には止めず、正しさの層には数えない。正しさは generation history verifier が担う。

### テスト運用文書

[orchestrator/tests/README.md:128-163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/tests/README.md:128) の pytest-only allowlist に上記 3 ファイルを追加する。

### 明示的に変更しないファイル

- `orchestrator/campaign/p3_autonomous_workload_trial.py`
- `orchestrator/campaign/trial_registry.py`
- `orchestrator/campaign/s8b_holdout_freeze.py`
- `orchestrator/campaign/s8b_ratified_freeze.py`
- `orchestrator/tests/test_frozen_artifacts.py`

既存 `FROZEN_MANIFEST` の 23 path と既存 freeze bytes は不変とする。

## 実装単位と依存順

|単位|所有ファイル|依存|
|---|---|---|
|A: parser/freeze core|`s8c_preregistration.py`、`test_s8c_preregistration_core.py`|なし|
|B: evidence predicates|evidence contract JSON、`s8c_preregistration_evidence.py`、predicate test|A、T-325 land/rebase|
|C: docs authority|8c prereg doc、output README、decision/worklog spool|A の正規化契約と親択一|
|E: 誤操作抑止|guard_write、hooks README、test_hooks|A の namespace/path 確定|
|D: publication/invariant|g1 artifact、invariant test、tests README|A→B→C→E|

順序は `A → T-325 land/rebase → B → C → E → D`。C の条件文確定より先に g1 を作ってはならない。A と T-325 land 待ちは並行可能だが、同じ所有 file を持つ単位はない。

## pytest nodeid 計画

### Core/parser/freeze

- `test_current_markdown_shape_extracts_field_set_and_conditions_1_to_12`
- `test_heading_detection_survives_title_reword_and_rejects_missing_duplicate_or_wrong_level`
- `test_table_lexer_handles_escaped_pipe_and_code_span`
- `test_layout_only_changes_preserve_normalized_hash`
- `test_word_number_punctuation_or_order_change_changes_condition_hash`
- `test_parser_rejects_gap_duplicate_extra_nested_item_and_unclosed_fence`
- `test_section5_placeholder_and_arbitrary_nonempty_text_are_not_filled`
- `test_generation_chain_accepts_one_recorded_revision`
- `test_generation_chain_rejects_unrecorded_change_even_after_revert`
- `test_generation_chain_rejects_gap_fork_bad_supersedes_unknown_key_and_noncanonical_json`
- `test_generation_history_rejects_mutation_delete_readd_and_merge_introduction`
- `test_revision_record_must_share_commit_with_protected_contract_change`
- `test_generation_schema_has_no_self_hash_commit_or_activation_field`
- `test_prepare_revision_is_exclusive_create_and_changes_only_destination`
- `test_cli_exposes_no_approve_activate_or_revoke_command`

### Predicate tests

- `test_predicate_registry_is_exactly_c01_through_c12`
- `test_evidence_undefined_is_never_satisfied`
- `test_condition_negative_control[c01]` … `test_condition_negative_control[c12]`  
  各 param は前掲表の最小変異を実行する。
- `test_c08_rejects_older_ancestor_as_current_activation_commit`
- `test_names_cli_or_declared_capability_do_not_satisfy_predicates`
- `test_effective_requires_freeze_typed_section5_and_all_twelve`
- `test_effective_preregistration_constructor_is_sealed`

### Real invariant

- `test_real_condition_freeze_tip_matches_current_protected_markdown`
- `test_real_activation_report_is_an_independently_recomputed_closed_world_conjunction`
- `test_s8c_namespace_is_not_added_to_holdout_scan_exclusions`
- `test_t327_tracked_files_add_no_holdout_conjunction_hits`
- `test_existing_repository_positive_control_remains_live`
- `test_cli_exit_status_matches_derived_report_without_activation_record`

既存 [test_s8b_repo_scan_invariant.py:21-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t327-prereg-activation/orchestrator/tests/test_s8b_repo_scan_invariant.py:21) の `rr80=[] / rr20=[]` と positive count > 0 もそのまま受入に含める。

## 変異事前登録候補

1. C01 の `_perf_for` だけ 100k に戻す → `test_condition_negative_control[c01]`。
2. C02 の proposal filename から arm を除く → `[c02]`。
3. C03 の manifest から 1 cell を削除 → `[c03]`。
4. C04 を crash cell だけ indeterminate にする → `[c04]`。
5. C05 の off arm 初期状態 hash を 1 bit 変更 → `[c05]`。
6. C06 の不足処理で次 arm を継続 → `[c06]`。
7. C07 の H2 floor または result row を削除 → `[c07]`。
8. C08 を exact activation commit でなく任意祖先へ緩和 → `[c08]`。
9. C09 の formal acceptance から Layer 3 検査を外す → `[c09]`。
10. C10 の raw/proposal bytes 再読を削除 → `[c10]`。
11. C11 の budget=1 禁止を許可へ反転 → `[c11]`。
12. C12 の `allow_resume` を true にする → `[c12]`。
13. `EVIDENCE_UNDEFINED` を SATISFIED と同値にする → `test_evidence_undefined_is_never_satisfied`。
14. conjunction を C01〜C11 だけにする → exact registry/effective test。
15. §6 の太字先頭句だけ hash し continuation を落とす → semantic-change test。
16. raw Markdown bytes を直接 hash する → layout-only test。
17. table を単純 `split("|")` にする → escaped-pipe test。
18. `supersedes` を前 record raw hash でなく condition hash にする → bad-supersedes test。
19. 中間の変更→revert を HEAD 比較だけで見逃す → unrecorded-history test。
20. gN の既存 path 上書きを許す → immutable-history test。
21. approval/active file を namespace で受理する → CLI/closed-world tests。
22. `output/s8c-preregistration/` を holdout scan 除外へ足す → scan-exclusion test。
23. combined hash から evidence contract hash を外す → protected-contract revision test。
24. 任意の非空 §5 値を filled にする → typed-section5 test。

## 親が裁定すべき設計択一

1. **§5 の欄数。推奨: g1 前に補う。** 現在の 9 欄には schedule artifact と generation/feedback/sample plan の明示欄がない。二つを追加してから初期 freeze するのが最も自然。9 欄のままなら、C05 等は未定義のままにし、T-295 で g2 改訂する。無関係な欄へ押し込まない。
2. **evidence contract も chain 対象にするか。推奨: 対象にする。** 条件文だけを pin すると、結果後に predicate 実装を緩める別経路が残る。raw checker bytes ではなく、データ化した証拠契約 hash を pin すれば自己 pin を避けられる。
3. **activation commit。推奨: brief P2 を厳守。** 最後の文書変更 commit を使う。prose-only 変更でも manifest 再 binding が必要になるが安全側。latest gN introduction commit を使う案は P2 の変更裁定が必要。
4. **条件 9 の green 基準。推奨: formal registry acceptance での再検査必須。** producer publish 前の呼出しだけを green にすると、別 acceptance 経路が Layer 3 を省略できる。
5. **P6 の production gap。推奨: T-327 は brief どおり CLI+invariant で閉じるが、同じ docs 記録で T-325 後の sealed-type gate task を必ず起票する。** これをしない場合、「発効状態は正しく導出できるが formal launch を止めない」という最大リスクが残る。

## 検証方針

実装後は Pegasus ログインノードから pytest を直接起動せず、`tools/run_tests.py` で targeted tests、既存 repo scan、全走を計算ノードへ dispatch する。その後 `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、commit 後に provenance checker を実行する。

このプラン作成中に実行したのは `rg`、`nl`、`git show/diff/log/status` などの静的読取だけである。pytest を走らせておらず、green とは報告しない。worktree は確認時点で clean だった。

## 総括

- 発効は approval/active artifact でなく、freeze・typed §5・C01〜C12 の exact conjunction から自動導出する。
- 条件契約は side-by-side gN と前 record raw hash で凍結し、無記録変更・中間変更→revert も検出する。
- 8b の Git/strict-schema 技法は再利用するが、人間承認・pointer・revocation は8cへ持ち込まない。
- 12 条件は実 artifact field または production code fact に結び、証拠や consumer 不在は必ず未充足とする。
- T-325 は現 checkout 未着地かつ arm は declared-only なので、land 前提で再 line-up が必要。
- 最大のリスクは P6 による launcher 未結線であり、sealed-type gate の後続タスクを必須とする。
- 親の主要裁定点は、§5 欄追加、evidence contract の chain 化、条件9の正式 acceptance 基準である。
- read-only 制約を守り、変更・pytest 実走・green 主張は行っていない。