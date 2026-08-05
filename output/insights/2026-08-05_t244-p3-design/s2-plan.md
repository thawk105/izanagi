# T-244 P3 production 化・producer 結線 設計裁定案

静的検査のみを実施した。起点は `3075a8fd270ba1f4016bc2c7d508f6ee0fea8fb8`。実装・pytest・書き込みは行っておらず、緑は主張しない。

結論を先に示す。

- N3・N10・N13・N14 は実コード上で真。
- N6 には訂正が必要。`ccbench_commit_oid` は現状の `pin.CURRENT_PIN` をそのまま使えない。
- 推奨は、名前付き artifact の Git blob bytes を authority preimage とし、承認済み authority 世代だけを対象にした独立 provisioning CLI を設け、8c trial を「単一候補×予約済み replicate batch」の最初の非認定 production caller とする案。
- ただし、pre-query reservation、authority v3、production 初期化、report v3 は受理集合を変えるため、D96 の新 D・completeness・registry・境界テストを同一変更単位で扱う必要がある。

## 前提実測の判定

### N3：真

batch の distinct 判定対象は候補平文ではなく member commitment である。[reflux_origin_ledger.py:1102–1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1102)

commitment preimage は候補 wire に加えて `query_ordinal` と `replicate_ordinal` を含む。[reflux_origin_ledger.py:608–619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:608)

したがって、同一 wire でも ordinal の異なる R 行は異なる commitment となり、`cardinality >= 2` の合法 batch を構成できる。現行テストにも同一 wire を反復する正例がある。[test_reflux_origin_ledger.py:2247–2289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/tests/test_reflux_origin_ledger.py:2247)

ただし ledger が数える `sealed_queries` は evidence row 数であり、物理 workload 呼出し回数そのものではない。[reflux_origin_ledger.py:2–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2) このため「同じ wire の R 行を seal した」だけでは物理 R 回測定を証明しない。

### N10：真

`attempt == 1` と `retry == false` は LLM role event の試行回数を拘束する。[autonomous_trial_completeness.py:175–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:175) [autonomous_trial_completeness.py:242–272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:242)

bench replicate は対象外である。harness、report、journal、Layer 3、trial registry の現行 consumer に「1 generation = 1 物理測定」という pin は見つからなかった。[autonomous_trial_completeness.py:538–574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:538) [autonomous_trial_completeness.py:792–800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:792) [autonomous_trial_completeness.py:1015–1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:1015) [trial_registry.py:1298–1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/trial_registry.py:1298)

### N13：真

production runtime 初期化は単なる入口不足ではない。`_initialize_locked()` 冒頭が production store を明示的に拒否する。[reflux_origin_ledger.py:2590–2592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2590)

公開 API もすべて既存 runtime の取得だけを行い、作成経路を持たない。[reflux_origin_ledger.py:3105–3136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:3105)

したがって production 解禁には入口追加だけでなく、「誰が、どの承認物を根拠に禁止を解除できるか」という受理契約が要る。

### N14：真

genesis は authority blob の全 entry を列挙して全 origin head を作る。[reflux_origin_ledger.py:2595–2639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2595)

event 集合には後から origin を追加する型がない。[reflux_origin_ledger.py:503–536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:503)

replay も authority blob の完全一致と entry 数の一致を要求する。[reflux_origin_ledger.py:2293–2310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2293)

よって、最初の genesis と authority 世代設計は切り離せない。

---

## (1) origin authority の実体化

### 1.1 AuthorityManifest 13 field の preimage 規則

全 hash の共通規則を次で固定する案を推奨する。

> authority generation が捕捉した full 40-hex commit `H` に対し、`git cat-file blob H:<path>` が返す blob bytes 全体を、末尾 LF を含め一切再直列化せず SHA-256 する。

authority generation には各 field と対応する `preimage_refs` を保持させる。現行 manifest は hash だけで artifact path を持たないため、現在のままでは closure を再検証できない。[reflux_origin_ledger.py:236–267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:236)

| field | 確定案となる preimage | 現状分類・根拠 |
|---|---|---|
| `spec_content_sha256` | `reflux_origin_contracts/t178_pilot_spec.v1.json` の Git blob bytes | 規則なし。現在は inline dict。[p3_autonomous_workload_trial.py:546–558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:546) |
| `ccbench_commit_oid` | submodule gitlink の full 40-hex OID。SHA-256 field ではなく OID 値そのもの | 部品あり・集約規則なし。`CURRENT_PIN` は7文字。[pin.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/pin.py:28) manifest は40文字を要求。[reflux_origin_ledger.py:80–81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:80) |
| `workload_descriptor_sha256` | canonical workload descriptor bytes | 既存規則あり。[s8b_descriptor.py:36–43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_descriptor.py:36) [s8b_descriptor.py:194–205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_descriptor.py:194) |
| `axis_semantics_sha256` | `trigger_gating_axis.v1.json` の Git blob bytes | 規則なし。現在はコード定数。[axis_trigger_gating.py:22–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/axis_trigger_gating.py:22) |
| `verifier_policy_sha256` | `legacy_plus_s2_verifier.v1.json` の Git blob bytes | 規則なし |
| `environment_contract_sha256` | `ExecutionEnvironmentContract` の既存 canonical bytes | 既存規則あり。[env_contract.py:83–160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/env_contract.py:83) |
| `candidate_ir.schema_ref` | `repo:<path>@sha256:<64hex>`。hash は `trigger_gate_ir.schema.v1.json` の blob bytes | 現行の単純 token は bytes を pin できない。[reflux_origin_ledger.py:375–377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:375) 現在の schema/encoder はコード内。[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_ir.py:19) |
| `candidate_ir.canonical_emitter_sha256` | 全32 mask の wire/predicate 対応を持つ `trigger_gate_emitter.golden.v1.json` の blob bytes | 規則なし。実装はコード。[reflux_ir.py:99–127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_ir.py:99) |
| `recipient_projection_schema_sha256` | 全 untrusted role payload を規定する `recipient_projection.8c.v1.schema.json` の blob bytes | 規則なし。現在は coder payload 等が inline。[p3_autonomous_workload_trial.py:1495–1512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1495) |
| `role_bundle_sha256` | ordered role list、各 role 本文 blob hash、mediated contract hash、合成規則を含む `role_bundle.8c.v1.json` の blob bytes | 部品あり・集約規則なし。provider は実 role 本文と contract を合成する。[claude_projected_provider.py:140–163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/claude_projected_provider.py:140) |
| `authority_series_id` | 人間が承認する generation record 内の stable identifier。自動 hash 発行しない | authority が値を入れる |
| `budget_policy` | 人間承認済み generation record 内の canonical policy object | authority が値を入れる |
| `stock_certification_ref` / `structural_zero_evidence_ref` | 各 evidence artifact の `{path, sha256}`。13 field の数え方では authority-supplied reference 群 | authority が値を入れる |

`AuthorityManifest` の top-level は13 fieldであり、`candidate_ir` と二つの evidence reference はそれぞれ composite field として数える。[reflux_origin_ledger.py:236–249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:236)

#### N6 の訂正

親 brief の「既存3 / 部品あり1 / 規則なし5 / authority 値4」はそのままでは正しくない。`ccbench_commit_oid = pin.CURRENT_PIN` は7文字であり、manifest が要求する40文字 OIDを満たさない。patch harness は prefix を実 HEAD に解決できるが、その解決規則は manifest preimage として固定されていない。[patchharness.py:162–183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/patchharness.py:162)

訂正版は以下。

- 既存規則あり：2  
  `environment_contract_sha256`、`workload_descriptor_sha256`
- 部品あり・集約/解決規則なし：2  
  `ccbench_commit_oid`、`role_bundle_sha256`
- 規則なしの composite：5  
  spec、axis、verifier、candidate IR、recipient projection
- authority が値を入れる：4  
  series、budget、stock reference、structural-zero reference

**成果物影響:** 採用すると authority blob の各 hash が独立して Git blob まで逆引き可能になる。放置すると `origin_id` は生成できても、後日同じ preimage を再構成できず proof chain が閉じない。

### 1.2 名前付き artifact とコード導出の比較

#### 推奨：commit 済みの名前付き artifact file

`s8b_ratified_freeze.py` は捕捉 commit の Git blob bytes と記録された path/hash の一致を検証し、live file や履歴との不一致を fail-closed にする。[s8b_ratified_freeze.py:914–985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:914)

さらに transition は許可されない変更・追加・削除をすべて拒否する。[s8b_ratified_freeze.py:627–676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:627)

この前例に合わせ、semantic artifact とコードの一致は境界テストで検証する。

- IR schema：artifact schema に対して encoder 出力を全32 maskで検証
- emitter：golden の全32 entry と `encode_wire()` / predicate emitter を比較
- role bundle：実 provider が読み込んだ role bytes・contract bytes・順序を比較
- recipient projection：planner/coder/auditor/critic の全 payload builder を schema 検証

#### 却下：コードから直接導出

`inspect.getsource()`、module source hash、runtime 定数の JSON 化などは推奨しない。

- import/dependency closure を漏らしやすい
- Python・serialization 実装差に依存する
- 「実装を実装自身で証明する」自己参照になりやすい
- freeze 族の exact Git blob model と異なる
- reviewer が意味内容を artifact 単位で承認できない

コード由来 hash を補助 provenance として持つことは可能だが、authority preimage の trust root にはしない。

**成果物影響:** artifact 案は authority と verifier が独立した共通 preimage を持つ。コード導出案では build/runtime 差で authority hash が揺れるか、依存漏れのまま一致したことになる。

### 1.3 authority_series_id と予算入力

#### 発行主体

`authority_series_id` の発行主体は人間 reviewer とする。CLI は generation の作成・検証を行えるが、series や予算値を推測・自動採番してはならない。driver と test には発行権限を与えない。

同一 series の世代列全体で `cell_key` と `origin_id` の再利用を禁止する。さもなければ新 generation 発行が予算 reset 経路になる。現行 `cell_key` は workload/axis/verifier/environment だけから構成される。[reflux_origin_ledger.py:454–462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:454)

#### 値を決めるための入力

値そのものはこの設計では決めない。必要入力は以下。

1. origin/cell の科学的同一性と source closure
2. origin 当たり最大 iteration/batch 数 `Imax`
3. member row／予約 query の最大数 `Qmax`
4. 公開可能な constraint hash 数・漏洩上限 `Kmax`
5. 最小 batch cardinality `Bmin`
6. 1 round の物理 replicate 数
7. 自動再測定 round の最大数
8. early stop、失敗、tombstone、no-refund の規則
9. floor tuple の `B0`、`q_round`、`R`、`E_min`
10. candidate生成失敗、評価失敗、provider失敗をどこまで課金するか
11. 物理 query と evidence row の完全性規則
12. codec 上限・storage上限

現行 workload pipeline は1 round 内複数 repsと、自動の追加 roundを既に持つ。[p3_autonomous_workload_trial.py:566–573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:566) [stability.py:58–90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/stability.py:58)

#### immutable floor の形

値は authority record から受け取り、caller 側に literal として重複させない。

\[
F = B_0 + q_{\text{round}}\times R + E_{\min}
\]

最低限の制約は次。

\[
\max(2,B_{\min}) \le F \le Q_{\max}
\]

\[
B_{\min}\le C_{\text{codec}}
\]

\[
Q_{\max}\le I_{\max}\times C_{\text{codec}}
\]

\[
\left\lceil\frac{\max F}{C_{\text{codec}}}\right\rceil
 \le \min\left(I_{\max},\left\lfloor\frac{Q_{\max}}{B_{\min}}\right\rfloor\right)
\]

\[
K_{\max}\le K_{\text{codec}}
\]

現行 parser も floor を `base + per_round * rounds + evidence_min` として扱い、`max(2,batch_min)` 以上かつ `qmax` 以下を要求する。[reflux_origin_ledger.py:210–232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:210) [reflux_origin_ledger.py:287–338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:287)

**成果物影響:** authority の予算値が certified selection の探索量と proof の受理集合を決める。放置すると caller literal の変更や generation 再発行で floor を回避できる。

### 1.4 stock certification / structural-zero evidence

現在の候補は採用不可。

- artifact は `linux-baremetal` かつ `clock_mhz=2100`。[s8a_trigger_gating_coverage.json:2–5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:2)
- environment registry は `linux-baremetal=1800`。[env_contract.py:169–178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/env_contract.py:169)
- 原因は producer の `ENV_TAG` / `CLOCK_MHZ` hardcode。[s8a_trigger_coverage.py:63–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:63)
- hardcode は trace 実行と出力にも伝播する。[s8a_trigger_coverage.py:165–173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:165) [s8a_trigger_coverage.py:243–245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:243)

また、現 artifact の workload は 8c の ycsb-a/b/c と同一 cell ではない。[s8a_trigger_coverage.py:74–84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:74)

#### 解消案

1. `s8a_trigger_coverage` が `ExecutionEnvironmentContract` を引数として受ける。
2. `ENV_TAG` / `CLOCK_MHZ` literal を削除し、build/run/output のすべてに同じ contract を渡す。
3. origin ごとに次の二 artifact を再測定して commit する。
   - `reflux_stock_certification.<origin>.v1.json`
   - `reflux_structural_zero.trigger-gating.<origin>.v1.json`
4. 両者に full OID、environment contract hash、workload descriptor、verifier policy、build admission、positive/negative control を記録する。
5. authority loader が `{path,sha256}` だけでなく内容も dereference して manifest と照合する。現行 `EvidenceReference` は path/hash の形式しか検証しない。[reflux_origin_ledger.py:197–205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:197) [reflux_origin_ledger.py:270–275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:270)

linux-baremetal で現在再測定できるかは repo だけでは確定できない。コードは Pegasus login node での重い実行を拒否し、single-tenant 条件を要求するが、利用可能な linux-baremetal host や予約状態は記録していない。[s8a_trigger_coverage.py:94–130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:94) [s8a_trigger_coverage.py:236–240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:236)

#### pin 閉包

採用後の closure は次。

1. manifest 内の exact evidence `{path,sha256}`
2. captured commit `H` と authority generation の `preimage_refs`
3. 人間 approval と active pointer
4. runtime genesis の authority generation/blob hash
5. loader による captured Git blob の dereference
6. environment/full OID/workload/verifier/build receipt/controls の semantic validation
7. artifact と producer 実装の boundary・mutation test
8. producer proof sidecar
9. report/completeness/formal consumer による sidecar と sealed batch の再照合

現行 baseline では 2100 と1800の不一致により実際に拒否される検査になる。

**成果物影響:** 再測定・closure 採用後は stock/zero evidence が authority から実 artifact まで追跡可能になる。放置すると authority を実体化しても evidence reference が現在の environment cell と一致せず、production admission は fail-closed のままになる。

---

## (2) production runtime bootstrap と authority 世代移行

### 2.1 bootstrap の推奨案

親 P1の「公開 API は create=False のまま、独立した冪等 provisioning、禁止は条件化」は方向として妥当。ただし、単に `_initialize_locked()` を CLI から呼べるようにするだけでは不足する。

現行初期化は origin files を先に `O_EXCL` で作り、最後に runtime head を作る。[reflux_origin_ledger.py:2554–2587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2554) 中途 crash 後の単純再試行は既存 file で失敗し、冪等ではない。

#### command 契約

推奨する明示 command は以下。

```text
python3 -m orchestrator.campaign.reflux_origin_admin provision-genesis \
  --activation-head <40hex> \
  --authority-generation-sha256 <64hex> \
  --approval-sha256 <64hex> \
  --authority-blob-sha256 <64hex>
```

後継世代は別 command とする。

```text
python3 -m orchestrator.campaign.reflux_origin_admin provision-successor \
  --activation-head <40hex> \
  --authority-generation-sha256 <64hex> \
  --approval-sha256 <64hex> \
  --authority-blob-sha256 <64hex> \
  --parent-active-pointer-sha256 <64hex> \
  --parent-runtime-state-commitment <64hex>
```

`--runtime-root`、`--fixture`、`--force`、`--reset` は設けない。runtime root は既存の git-common-dir 束縛からのみ導出する。

#### 誰が genesis するか

- authority generation・approval の発行：人間
- 実際の fsync/provisioning：人間が起動する admin CLI
- driver：既存 runtime を読むだけ
- test：fixture 専用 genesis のみ

#### 禁止の条件付き解除

`_initialize_locked()` は production boolean を受け取らず、admin loader だけが生成できる private `_ProvisioningAuthorization` を要求する。

authorization の成立条件は次。

1. authority generation と approval が captured `activation-head` で exact blob として存在
2. active/revocation chain が一意で、未取消
3. authority registry が非空
4. 全 preimage/evidence closure が検証済み
5. generation/blob/approval hash が command 引数と一致
6. successor の場合、親 runtime が terminal かつ state commitment 一致
7. runtime active pointer が未作成、または完全一致

公開 API から到達可能な `create=True` や boolean bypass にはしない。

#### crash-idempotent な状態遷移

推奨 layout は authority generation ごとの epoch。

```text
<git-common-dir>/izanagi/reflux-origin-ledger/v3/
  authority.lock
  epochs/<authority-generation-sha256>/
  staging/<authority-generation-sha256>/
  runtime-active.json
```

挙動は次。

- 何もない：staging に完全構築、fsync 後に atomic rename
- 同一 staging が途中：既存内容を検証して再開
- divergent staging：fail-closed。自動削除しない
- epoch 完成・pointer 未作成：同じ provisioning receipt を再返却
- pointer と epoch が完全一致：already-provisioned
- pointer があるのに epoch 欠落・不一致：再 genesis せず拒否

#### lazy-create の却下

production root は git worktree root ではなく git-common-dir 配下で、全 worktree に共有される。[reflux_origin_ledger.py:1432–1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1432)

公開 read/commit API の lazy-create は、ある worktree の試行が全 worktree 共有状態を暗黙に変更するため不採用。一方で root を各 worktree に移す案も、worktree を切るだけで新品予算を得る回避経路になるため不採用。git-common-dir 束縛は維持する。

**成果物影響:** 採用すると承認済み authority にだけ production runtime genesis receipt が作られ、通常 driver の受理集合は「active receipt がある runtime」に限定される。放置すると authority が非空になっても production caller は必ず初期化拒否になる。

### 2.2 authority 世代移行

現状では authority blob bytes が変わると replay が全拒否する。[reflux_origin_ledger.py:2293–2297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2293)

runtime を消して genesis し直せるような単純解禁を行えば、counter を失った新品 runtime になる。現行は production genesis 自体が禁止されているため直ちに実行可能な攻撃ではないが、禁止を無条件解除した瞬間に成立する。

#### s8b からそのまま適用できる構造

- captured commit に対する純粋解決
- exact schema、path、sha
- generation と `supersedes`
- 人間 approval
- active pointer chain
- revocation tombstone
- transition allowlist
- no-active、fork、gap、revoked の fail-closed
- immutable public value

根拠は [s8b_ratified_freeze.py:60–141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:60)、[s8b_ratified_freeze.py:1001–1021](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:1001)、[s8b_ratified_freeze.py:1063–1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:1063)、[s8b_ratified_freeze.py:1198–1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:1198)。

#### origin ledger 固有に作り直す部分

1. generation entry は新規 `added_origins` だけを持つ。
2. origin は誕生 epoch に恒久的に route する。
3. 世代列全体で origin/cell の重複を拒否する。
4. 旧 epoch と counter を保持し、新 authority blob にコピー genesis しない。
5. successor activation は親 epoch の全 origin が terminal seal であることと、親 state commitment の一致を要求する。
6. open/prepared batch があれば移行を拒否する。
7. runtime epoch の存在・health・provisioning receipt を active chain に含める。
8. activation 後の revocation は新規 write を停止するが、親 generation への rollback や予算 refund はしない。

推奨は「epoch router」。累積 authority 全体を毎世代新 genesis する案は旧 origin の counter resetか、現行 event/hash model にない imported-terminal genesis を必要とするため却下する。

#### 「seal-and-succeed」の解釈

既存 origin の予算を新世代へ再束縛しない点は妥当。ただし successor を「科学的成功した origin だけ」に限定すると、正当な abort が一つあるだけで authority 列全体が永久停止する。

推奨解釈は次。

- predecessor origin は `certifiable` または `aborted` のどちらでもよい
- いずれも terminal seal と no-refund が必要
- “succeed” は科学的成功ではなく、移行 transaction が terminal state を確認して成功すること

これは未裁定事項として残す。

**成果物影響:** epoch router では旧試行台帳・budget counter・proof chain が不変のまま新 origin だけが追加される。累積再-genesis を許すと旧予算が新品化し、certified selection の探索上限が無効になる。

### 2.3 公開 authority reader

追加を推奨する。ただし `OriginSnapshot` にすべてを混ぜない。

#### 推奨 API

```text
read_authority_binding(origin_id) -> AuthorityBinding
```

返す値：

- manifest
- cell key
- budget policy
- authority blob hash
- authority generation hash
- active pointer hash
- birth epoch

authority は commit 済みの公開情報なので、reader 自体は秘密を増やさない。ただし projected role payload に渡すことは禁止する。

`OriginSnapshot` は mutable state に限定する。[reflux_origin_ledger.py:539–551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:539)

open batch は recovery 用の別 `OpenBatchHandle` とし、次だけを返す。

- opaque batch id
- phase
- cardinality
- 次の query ordinal

seal 前に次を返さない。

- member commitment
- candidate wire
- replicate ordinal の配列
- result
- constraint hash count

D166 の seal 前 projection 制限に合わせ、planner/coder/auditor/critic の recipient schema が manifest/budget/open-batch field を拒否する。projected provider は neutral cwd と明示 payload だけを role に渡すため、この境界を schema 化できる。[claude_projected_provider.py:253–273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/claude_projected_provider.py:253)

**成果物影響:** producer は authority 値を literal で複製せず runtime binding を参照できる。一方、role projection を拒否しなければ seal 前の batch/予算情報が auditor・critic に漏れ、D166 の受理境界を壊す。

---

## (3) 結線先と batch 形状

### 3.1 8c に単一候補×R replicate batch を作る変更

8c は ycsb-a/b/c の pilot workload のみを持つ。[p3_autonomous_workload_trial.py:171–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:171) formal H1/H2 は trial registry 側の別系列であり、8c registry は非認定である。[trial_registry.py:46–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/trial_registry.py:46) [trial_registry.py:124–129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/trial_registry.py:124)

#### CLI と初期 binding

parser に repeatable option を追加する案。

```text
--reflux-origin ycsb-a=<64hex>
--reflux-origin ycsb-b=<64hex>
--reflux-origin ycsb-c=<64hex>
```

追加位置は parser 定義。[p3_autonomous_workload_trial.py:1932–1956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1932)

`run_trial()` への転送は main 呼出し部。[p3_autonomous_workload_trial.py:2002–2019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:2002)

run-root 作成前に selected workload と mapping が完全一致することを検証する。[p3_autonomous_workload_trial.py:1746–1792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1746)

fixture provider / no-build mode は origin proof を生成できないものとして拒否する。

prepared identity 構築時に `AuthorityBinding` を読み、spec/full OID/workload/env/axis/verifier/IR/role/projection の完全一致を検証する。[p3_autonomous_workload_trial.py:1402–1412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1402)

#### batch 生成

現行 coder 呼出し前。[p3_autonomous_workload_trial.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1475)

1. authority policy から R と最大 remeasurement round を取得
2. pre-query reservation を durable commit
3. planner/coder を呼ぶ
4. coder の単一 wireを取得。[p3_autonomous_workload_trial.py:1513–1531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1513)
5. 同じ wire に対して ordinal と CSPRNG salt の異なる予約済み member commitments を作る
6. preview/auditor より前に candidates-committed
7. workload を各予約 row に対応付けて実行
8. 未使用 suffix は tombstone
9. Layer 3 admission 後、results-prepared、seal、proof sidecar
10. seal 後に critic/report

現行 tombstone は terminal suffix と replicate canonicality を検証できる。[reflux_origin_ledger.py:1205–1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1205)

#### 物理 replicate evidence

現在の pipeline は aggregate `tps`、notes、command を WAL に載せるだけで、各 process run と ledger row の1対1証明はない。[p3_autonomous_workload_trial.py:427–452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:427)

runner/pipeline の各物理実行点に、create-only `rep_evidence` を出す。

- query ordinal
- replicate ordinal
- exact command hash
- stdout/perf artifact hash
- return code
- metrics projection
- environment receipt
- binary/build-admission digest

instrument 位置は [runner.py:346–479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/calibrator/runner.py:346) と workload pipeline 呼出し部。[p3_autonomous_workload_trial.py:294–350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:294)

自動再測定・correctness gate は緩めない。worst-case rows を先に予約し、実行しなかった suffix を tombstone にする。

**成果物影響:** journal/report に同一候補の R 個の物理 evidence と sealed batch が結び付く。放置すると合法 batch は作れても物理 query floor を証明できず、材料レポートは proxy count しか持たない。

### 3.2 予算束縛：二案の比較

#### 案A：caller の制御流だけを batch 先行にする

coder 後、preview/evaluation 前に batch commit する。

これは coder 後の適応的評価は抑えるが、coder 出力後・commit直前に process を kill し、新 run-root で引き直す無課金経路を塞げない。D163 決定3(a)の反例が残る。

単独案として却下。

#### 案B：FSM に pre-query reservation event を追加

推奨。

候補に影響する最初の role 呼出しより前に、iteration/query budget を durable に消費する。予約後の provider失敗、candidate不成立、process kill でも refundしない。

必要な一様 event path は例えば以下。

```text
BATCH_RESERVED
→ CANDIDATES_COMMITTED
→ RESULTS_PREPARED
→ BATCH_SEALED
```

candidate が作られなかった予約 row には「未 materialize」の terminal representation が必要であり、stock wire を偽装して埋めてはならない。

これは ledger の event 集合と受理集合を変更し、D166 の現行3-event uniform pathも変えるため、D96 の新 D 対象。[reflux_origin_ledger.py:503–536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:503)

実際の producer は案Bに加えて案Aの batch先行制御も行う。両者は代替ではなく補完関係である。

**成果物影響:** reservation 採用時は kill-before-commit でも `Qmax/Imax` が減り、試行台帳に失敗予約が残る。caller 制御だけでは certified selection の候補引き直し上限が実効化しない。

### 3.3 commit-reveal と単一候補 batch

現行は preview 結果で auditor の skip/実呼出しを分岐する。[p3_autonomous_workload_trial.py:1533–1584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1533)

実呼出し時の raw response は即時 fsync される。[p3_autonomous_workload_trial.py:935–938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:935)

単一候補では、複数候補の「どれを選んだか」は漏れない。しかし少なくとも次の1 bit は漏れる。

> その候補が preview/pre-audit を通過し auditor 呼出しまで進んだか。

さらに現行 critic payload は seal 前に連続値 metrics を受ける。[p3_autonomous_workload_trial.py:1647–1670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1647) したがって漏洩は1 bitだけではない。

推奨変更：

- machine preview は correctness gate として維持
- auditor は常に同じ shape で呼ぶか、sealまで隔離 staging に置く
- critic は Layer 3 admission、ledger seal、proof write の後に移動
- proposal/raw response の公開も seal 後
- reservation により oracle query の反復回数を no-refund で束縛

単一候補化は適応性を減らすが、P4・axis iii anti-oracle や storage privacy を閉じない。

**成果物影響:** seal 後 role 化で recipient projection から事前 metrics が消える。現状のままでは proof chain が成立しても auditor/critic の観測を通じた候補選別 bit と連続 metrics が残る。

### 3.4 結線先の択一

#### 推奨：8c 自律 trial

理由：

- coder による単一 wire が既にある
- workload execution、journal、report、completeness、Layer 3 admission が同じ driver にある
- 非認定 pilot と明示されている。[p3_autonomous_workload_trial.py:1298–1305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1298)
- single-candidate×replicate の liveness host として境界が明確

制限：

- ycsb-a/b/c のみ
- H1/H2 は走らせられない
- formal trial registry の certifying 値を変えない
- cap=1を維持

#### 非推奨：E 段 loop

E loop の proposal loader は planner/coder/auditor verdict と diff digest を要求し、既に candidate/audit 済みの proposal を入力にする。[p3_s4_loop_trigger_gating.py:649–681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:649)

そのため、pre-query reservation や candidate commit-before-evaluation を実現するには proposal topology 自体を大きく作り直す必要がある。[p3_s4_loop_trigger_gating.py:701–764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:701)

最初の production caller としては8cより変更面が広く、却下する。後続の正式 H1/H2 producer 候補としては別途裁定可能。

**成果物影響:** 8c採用でも certified selection、正式材料レポート、trial registry の certifying flag は変えない。E loopを先に選ぶと proposal/auditor contract まで同時に受理集合変更となる。

### 3.5 durable cross-reference

ledger event 自体へ trial/report field を追加する必要はない。producer 側 create-only artifact に置く親 P7案を支持する。ledger receipt は event hash と resulting state commitment を既に返せる。[reflux_origin_ledger.py:561–569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:561)

#### sidecar

```text
<run-root>/origin-proofs/<workload>.g<generation>.json
```

field 案：

```json
{
  "schema_version": "izanagi-reflux-origin-proof/v1",
  "trial_id": "...",
  "campaign_id": "...",
  "workload": "...",
  "generation": 0,
  "origin_id": "...",
  "cell_key": "...",
  "authority_generation_sha256": "...",
  "authority_blob_sha256": "...",
  "authority_active_pointer_sha256": "...",
  "runtime_epoch_id": "...",
  "runtime_genesis_sha256": "...",
  "batch_id": "...",
  "batch_commit_event_sha256": "...",
  "batch_seal_event_sha256": "...",
  "seal_state_commitment": "...",
  "sealed_batch_sha256": "...",
  "candidate_artifact_ref": {"path": "...", "sha256": "..."},
  "result_evidence_refs": [
    {
      "query_ordinal": 0,
      "replicate_ordinal": 0,
      "path": "...",
      "sha256": "..."
    }
  ],
  "layer3_admission_ref": {"path": "...", "sha256": "..."}
}
```

#### 書き込み位置

Layer 3 admission finalize 後。[p3_autonomous_workload_trial.py:1278–1282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1278)

その後に ledger seal、sidecar create-only/fsync、report 構築の順にする。report 構築は直後に始まる。[p3_autonomous_workload_trial.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1283)

journal には `run-finish` より前に `origin-proof` event を追加する。[p3_autonomous_workload_trial.py:1322–1329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1322)

generation/cell と report top-level に `origin_proof_ref {path,sha256}` を載せる。origin-enabled report は既存 v2を暗黙拡張せず v3にする。[p3_autonomous_workload_trial.py:139–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:139)

completeness は sidecar を dereference し、authority binding、sealed batch、journal、report、Layer 3 admission の完全一致と bijection を検査する。

**成果物影響:** proof chain に origin/authority/batch/seal/report の durable cross-reference が加わる。ただし formal consumer が承認されるまでは certified selection や trial registry の値を変えない。

---

## D96 と実際に発火する検査

production initializer、authority generation schema、reservation event、report v3/completeness はいずれも受理集合を変える。新 D、report v3、completeness、trial registry、境界テストを同一変更単位にする。[decisions.md D96:4269–4296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:4269)

現行 baseline に対して実際に発火する検査は次。

1. **authority readiness:** 現 authority registry は `origins: []` なので nonempty activation check が拒否する。[reflux_origin_authority_v2.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_authority_v2.json:1)
2. **full OID:** 現 `CURRENT_PIN` は7文字なので40文字 manifest OID check が拒否する。
3. **evidence/environment:** 現 s8a artifact の2100と registry の1800が一致せず拒否する。
4. **provisioning:** active generation/receipt がない現 baseline では production public API は引き続き失敗する。空 authority を渡す admin CLI も拒否する。
5. **physical query binding:** 現 reportは per-replicate evidenceを持たないため新 completeness が拒否する。
6. **privacy readiness:** 現行の conditional auditor raw fsync と seal 前 critic metrics を topology checker が拒否する。
7. **durable proof:** 現 report v2は `origin_proof_ref` を持たず、v3 completeness が拒否する。
8. **reservation crash:** 実装後、reserve fsync直後・coder前で killし、再実行しても旧 query budgetが残ることを fault-injection で確認する。現 v2には reservation event がないため、現 baselineは schema段階で拒否される。
9. **same-wire positive/mutation:**同一 wireの ordinal 0/1を受理し、ordinal reset/gap、duplicate commitmentを拒否する。これは candidate平文 distinct を誤って再導入していないことも検査する。
10. **epoch reset:** active pointerが指す旧 epoch fileを欠落させた場合、新 genesisせず拒否する。authority blob差替え、fork、gap、revoked successorも拒否する。

同一 UID が git-common-dir 全体と履歴を協調削除・書換えする脅威については、repo 内 file だけの検査では恒真でない保証を作れない。外部 monotonic anchor がない限り防げないと明記する。

---

## 名乗りの上限

本設計を実装しても名乗ってよいのは次まで。

> 承認済み authority 世代に対する production provisioning と、非認定8cにおける single-candidate×reserved-replicate producer liveness／wiring。

名乗ってはならないもの：

- P3充足・部分P3
- P4またはaxis iii anti-oracle
- P7 formal consumer 完了
- ledger単体による物理 query floor証明
- discipline 3 reflux 完了
- 多世代開放
- certified selection
- cap引上げ
- formal H1/H2通過

D114の cap=1は維持し、D166のP4 FAILも変わらない。

## 総括

**1. 親 brief N1〜N12 の誤り。** N6のみ訂正が必要である。`ccbench_commit_oid` は現行 `pin.CURRENT_PIN` の7文字 prefixをそのまま使用できず、manifestが要求するfull 40-hex OIDへの解決・pin規則が欠けている。このため分類は「既存3／部品あり1」ではなく「既存2／部品あり・集約規則なし2／規則なし composite 5／authority値4」とする。N3とN10は実コード上で真であり、その他N1〜N12には今回の指定範囲で覆す証拠を見つけなかった。

**2. 推奨の1行要約。** (1) authorityは捕捉commit上の名前付きGit blob bytesをpreimageとし、人間承認の世代・予算・再測定evidence closureを固定する。(2) 公開APIをcreate=Falseのまま維持し、人間が承認済み世代を指定して起動するcrash-idempotent provisioning CLIとepoch routerで世代移行する。(3) 8cを最初の非認定callerとし、LLM呼出し前のpre-query reservation、単一wire×R replicate、per-run evidence、seal後critic、producer proof sidecarを一体で結線する。

**3. この設計を実装しても閉じない残余。** formal H1/H2、P4/axis iii anti-oracle、P7 formal consumer、D164のcritic独立性、同一UIDによるgit-common-dir全削除・履歴書換えへの外部monotonic anchor、linux-baremetal再測定資源の実在確認、複数候補の正式D96 package、正式certified selection、cap引上げ、多世代discipline 3 refluxは閉じない。

**4. ユーザー裁定が要る択一。** (R1) authority composite preimageを提案した名前付きartifact群で固定するか、コード導出にするか、(R2) `candidate_ir.schema_ref`をcontent-addressed ref文字列へ拡張するか独立hash fieldを追加するか、(R3) successor前提のterminal sealに`aborted`も認めるかcertifiable成功だけに限定するか、(R4) epoch routerを採用するか累積authority再-genesis型を新event込みで設計するか、(R5)公開readerをstatic `AuthorityBinding`とopaque recovery handleに分離するか、(R6)最初のproduction callerを8cにするかE段loopを先に全面改修するか、(R7) reservation失敗行をnullable/unmaterialized terminal rowで表すか専用terminal event型にするか、の7件である。