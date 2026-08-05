# T-244 P3 裁定用設計案

必読ファイルはすべて読み取れました。起点は `3075a8fd270ba1f4016bc2c7d508f6ee0fea8fb8` です。結論は次のとおりです。

- N3 は ledger の受理規則として真です。ただし「sealed member row」と「物理 bench 実行」の一対一は証明しません。
- origin authority は、コード実行結果ではなく、commit 済みの名前付き artifact の raw bytes を preimage にするのが妥当です。
- production 起動は、公開 API の lazy-create ではなく、人間が承認し CLI が機械実行する二相 provisioning にすべきです。
- 単一候補でも、無課金の候補引き直しを塞ぐには `BatchReserved` 相当の新 FSM が必要です。これは D96 の受理集合変更です。
- 結線先は 8c が優位ですが、得られるのは pilot の生死実験であり、P3/P4・正式 H1/H2・certified 選択は閉じません。

静的検査だけを行い、ファイル変更・pytest 実行・緑の主張はしていません。

## 前提実測への訂正

N1、N2、N4、N5、N8〜N12 は実コードと一致しました。N3 は以下の条件付きで正しいです。

- 実際の SHA-256 入力は `salt bytes || member preimage` であり、member preimage は domain separator と `(candidate_wire_b64, query_ordinal, replicate_ordinal)` の canonical JSON です（[reflux_origin_ledger.py:594–619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:594)）。
- distinct 判定は candidate plaintext でなく `candidate_commitment` に掛かります（[reflux_origin_ledger.py:1102–1109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1102)）。
- seal 時には同じ wire の replicate ordinal が origin 全体で `0,1,…` と連続することも検査されます（[reflux_origin_ledger.py:1205–1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1205)）。

したがって、`R >= batch_cardinality_min`、I/Q 残量あり、salt が一意という条件下では、同じ wire を R 行並べて合法な batch を作れます。一方 D166 自身が、これは物理 query 数の証明ではないと固定しています（[decisions.md:8286–8290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8286)）。

N6 の分類には訂正が必要です。

- 完全に使える既存規則は `workload.descriptor_sha256` と `environment_contract_sha256` の2件です。
- `ccbench_commit_oid` は full 40-hex を要求するのに対し（[reflux_origin_ledger.py:80–82,177–180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:80)）、現 `CURRENT_PIN` は7文字です（[pin.py:26–28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/pin.py:26)）。gitlink と実 submodule HEAD はいずれも full OID `d706650cdb31e442bef45b9b4216951d4fb40969` なので部品はありますが、`CURRENT_PIN` をそのまま manifest 値にはできません。
- `role_bundle_sha256` は部品ありですが、fixture は mediated contract だけを effective prompt として hash し（[p3_autonomous_workload_trial.py:419–427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:419)）、production provider は role body と contract を結合して hash します（[claude_projected_provider.py:145–163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/claude_projected_provider.py:145)）。同じ意味の部品ではありません。
- `candidate_ir.schema_ref` には既に値規則 `izanagi-trigger-gate-ir/v1` があります（[reflux_ir.py:19–44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_ir.py:19)）。不足しているのは、その token が指す schema artifact bytes の束縛です。

従って親の4分類へ押し込むなら、正しくは「既存2 / 部品あり2 / 完全な preimage 規則なし5 / authority 入力4」です。さらに no-rule 5件のうち `candidate_ir.schema_ref` は「値規則あり・内容参照なし」と細分すべきです。

N7 の clocks 根本原因は正しいですが、修復範囲は clocks だけでは足りません。現 artifact は `linux-baremetal` と `2100` を同時に記録し、short pin も保持しています（[s8a_trigger_gating_coverage.json:2–5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:2)）。現 producer は `ENV_TAG` と `CLK` を別々に hardcode し（[s8a_trigger_coverage.py:63–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:63)）、run command に登録済み `numactl` も付けません（[s8a_trigger_coverage.py:165–173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:165)）。また現在の producer は `build_admissions` を出すのに、既存 artifact にはありません（[s8a_trigger_coverage.py:243–264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8a_trigger_coverage.py:243)）。

もう一点、D163 の「runtime を消せば新品になる」は現 v2 production には当たりません。公開 API はすべて `create=False` で（[reflux_origin_ledger.py:3105–3136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:3105)）、production 初期化も明示禁止です（[reflux_origin_ledger.py:2590–2594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2590)）。現在は削除すると単に起動不能になります。「削除後に新品」は private fixture、または将来 provisioning を素朴な `absent ⇒ genesis` にした場合の危険です。

## (1) origin authority の実体化

### 13 field の preimage 規則

manifest は13 top-level fieldを厳密に受理しますが、現 parser は hash の形式しか検査せず、参照先を dereference しません（[reflux_origin_ledger.py:235–267,364–410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:235)）。次を authority control plane の確定案とします。

| field | 確定案 |
|---|---|
| `authority_series_id` | SHA-256 field ではない。CLI が衝突困難な候補 token を作り、人間の approval commit が発行を成立させる。値は canonical manifest bytes にそのまま入る。全 authority 履歴で再利用禁止。driver/test は発行不可。 |
| `spec_content_sha256` | commit 済み `campaign-spec.v1.txt` の raw file bytes、改行を含む全 bytes の SHA-256。8c はその bytes を strict UTF-8 decode し、現在 inline の `CampaignConfig.spec_content`（[p3_autonomous_workload_trial.py:546–554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:546)）へ byte-equivalent に渡す。`GATING_SPEC` は別物で、role bundle 側へ入れる。 |
| `ccbench_commit_oid` | SHA-256 ではない。authority generation が捕捉した superproject H の `external/ccbench` gitlinkが指す full 40-hex commit OID。実行時 submodule HEAD との完全一致と dirty 無しを要求する。short pin は不受理。 |
| `axis_semantics_sha256` | commit 済み canonical JSON artifact の raw bytes の SHA-256。内容は marker/source/flag/base defines、5 reason の順序、32点 universe、wire bit 意味、`kUnset` fail-safe を含む。現実装の根は [axis_trigger_gating.py:22–51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/axis_trigger_gating.py:22)。 |
| `workload` | `descriptor_sha256 = SHA256(canonical JSON descriptor bytes)`。既存の正準化は [s8b_descriptor.py:36–43,194–205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_descriptor.py:36) に従う。bytes を名前付き artifact として保存し、`records` / `threads` が descriptor の `scale` と一致することも authority validator が検査する。 |
| `verifier_policy_sha256` | commit 済み verifier-policy JSON の raw bytes の SHA-256。`legacy+s2`、全 pass 必須、空 trace・非0 exit・非certified の fail-closed 写像、build admission policy を列挙する。現 gate は [pipeline.py:835–891,952–991](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/pipeline.py:835)。 |
| `environment_contract_sha256` | `ExecutionEnvironmentContract` 全 field の canonical JSON UTF-8 bytes、末尾 LF なしの SHA-256。既存規則をそのまま使う（[env_contract.py:145–160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/env_contract.py:145)）。activation 時には同じ canonical bytes を名前付き projection artifact として保存する。 |
| `candidate_ir` | `schema_ref` は schema ID だけでなく、推奨案では `{id,path,sha256}` の content-addressed ref にする。`sha256` は commit 済み JSON Schema の raw bytes。`canonical_emitter_sha256` は全32 wire と期待 C++ 一行を列挙した commit 済み truth-table artifact の raw bytesの SHA-256。現 emitter は [reflux_ir.py:99–127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_ir.py:99)。 |
| `role_bundle_sha256` | planner/coder/auditor/critic を role 名順に並べた commit 済み bundle JSON の raw bytes の SHA-256。各 entry は role file path/hash、mediated contract hash、production の effective-prompt hash、role/model/provider adapter hash、期待 executable hashを持つ。fixture hash は production origin に使わない。 |
| `recipient_projection_schema_sha256` | 4 role への入力 projection を role discriminator 付きで定める commit 済み JSON Schema の raw bytes の SHA-256。各 `_invoke` 直前に実 payload を検証する。role 出力 schema は role bundle 側に置く。 |
| `budget_policy` | SHA-256 field ではない。全数値と floor list を canonical object として manifest bytes に直接含める。順序・重複・codec feasibility は現検査を維持する（[reflux_origin_ledger.py:287–338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:287)）。 |
| `stock_certification_ref` | `{path,sha256}`。`sha256` は stock certification projection artifact の raw bytes。projection は raw measurement bundle の path/hash、full CCBench OID、env contract、build admission、実行 command、stock 結果を束縛する。 |
| `structural_zero_evidence_ref` | `{path,sha256}`。`sha256` は structural-zero projection artifact の raw bytes。同じ raw measurement bundleを根にしてもよいが、stock と zero の受理条件を別 projection にする。 |

最終的な `origin_id` は現行どおり、

```text
SHA256(
  b"izanagi-reflux-origin-manifest/v2\0"
  || canonical_manifest_bytes_without_trailing_LF
)
```

です（[reflux_origin_ledger.py:445–451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:445)）。authority generation validator は、manifest の文字列を信じず、各 ref の committed blob bytes を読み、再計算した値と比較しなければなりません。

**成果物影響:** 採用すると future `origin_id`、authority blob hash、proof chain の source refs が機械再導出可能になります。放置すると authority は値を自己申告でき、certified 選択・材料レポート・試行台帳はいずれも origin identity を信用できないため現在値のままです。

### 名前付き artifact とコード導出の択一

推奨は全6 leafについて「commit 済み名前付き artifact の raw bytes」です。コード導出は conformance check にだけ使います。

`s8b_ratified_freeze.py` は freeze source を frozen commit の blob bytes で検査し（[s8b_ratified_freeze.py:947–955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:947)）、closure artifact も generation tree・H tree・worktree bytes・履歴不変性まで検査します（[s8b_ratified_freeze.py:964–985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:964)）。つまり freeze 族の信頼根は「live code を実行して得た値」ではなく「名前と bytes が固定された blob」です。

コード導出だけを authority preimage にする案は却下を推奨します。

- Python source/AST hashは意味を変えない refactor で origin を分裂させ、import 先定数を取り逃がします。
- コードを実行して output を hash する案は、その generator 自身と実行環境が未記録の信頼根になります。
- 人間が authority 承認時に実際の preimage を読めません。
- emitter は入力が32点しかないので、32行 truth table artifact と live emitter の全点比較で実効的に検査できます。

`candidate_ir.schema_ref` だけは次の択一を残します。

1. **推奨:** manifest v3 で content-addressed `{id,path,sha256}` にする。origin ID 自身が schema bytes を束縛する。
2. v2 token を維持し、authority generation blob内に immutableな `token → path/hash` tableを置く。変更量は小さいが、単独の origin ID では schema bytes を特定できず、proof chain が authority blob hash に依存する。

推奨案1は manifest/authority の受理集合変更なので、新 D と D96 境界テストを同一変更単位に含めます。現 authority が空で production runtime も無い今が、移行コストの最も小さい時点です。

**成果物影響:** 名前付き artifact 案では source bytes の1-byte変化が origin IDまたはauthority generation hashへ反映されます。コード導出案では材料レポートから参照可能な preimage が残らず、proof chain が generator の現在挙動に依存します。

### `authority_series_id` と予算入力

発行主体は「人間が ratify した authority control plane」とするのが推奨です。CLI は候補 ID の生成と重複検査だけを行い、driver は選択、test は fixture namespace 以外の発行をしてはいけません。current parser は token 形式しか検査しないため（[reflux_origin_ledger.py:165–168,384–387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:165)）、全履歴での一意性は世代台帳側の追加義務です。

予算値を決めるために必要な入力は次です。値そのものは本設計では決めません。

- scientific claim が U3 の32点全測定か、単なる pilot liveness か。
- 「1 physical query」の定義。correctness-only、bench rep、再測定 round、control/evidence run のどれを数えるか。
- `R` を決める事前登録済み統計設計。within-run CVだけでなく、対象 env の between-run 分散、必要な検出力、欠測処理を入力にする。
- `E_min` に数える named evidence/control の一覧と、各項目が ledger row を消費するか。
- batch partition。サイズ列 `b₁…bₘ`、各 batch の原子性、失敗時 tombstone/no-refund 方針。
- provider/build/bench failureを予算内で何回まで許すか。無制限 retry は不可。
- `Kmax` が許す constraint class の意味と漏洩上限。
- origin cell数、同じ cell の再発行禁止、authority transition の単位。
- codec 上限。現実装は batch ごと最大2248行、`Qmax <= Imax × 2248`、floorを `Imax` 個以下の合法 batchへ分割できることを要求します（[reflux_origin_ledger.py:1964–1986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1964)）。

U3 用 floor の形は既裁定どおり、

```text
required_queries = 1 + 32 * R + E_min
```

を、

```json
{
  "formula_id": "q-lower-bound/base+perRound*R+Emin/v1",
  "base_queries": 1,
  "queries_per_round": 32,
  "rounds": "R supplied by authority",
  "evidence_min": "E_min supplied by authority"
}
```

として immutable に受け取ります（D147: [decisions.md:7208–7210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:7208)）。trigger-gating seriesでは、どの floor の `rounds` を driver が読むか曖昧にしないため、この formula ID の entry をちょうど1件にすることを authority validator が要求する案を推奨します。

単一候補×R pilotだけではこの `1+32R+E_min` を満たしません。pilot 後に `OriginSealed(aborted=False)` を送って certifiable を得る案は不正です。pilotは batch sealまでの livenessに限定し、originを継続するか、明示的に `aborted=True` で閉じる必要があります。

**成果物影響:** authority 採用後は I/Q/K と floor が origin ID に固定され、試行台帳の消費量を再計算できます。値を CLI や driver literal にすると run ごとに受理集合が変わり、proof chain と予算会計が成立しません。

### stock / structural-zero evidence

現 artifact はどちらの ref にも採用不可です。修復案は次です。

1. `s8a_trigger_coverage.py` が `env_contract.lookup(env_tag)` を一度だけ行い、`clocks_per_us`、`numactl`、calibration refをその objectから取る。現 registry は linux-baremetal=1800+interleave、Pegasus=2100+prefixなしです（[env_contract.py:169–193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/env_contract.py:169)）。
2. CCBench pin は captured H の full gitlink OIDを記録する。
3. raw resultに `environment_contract_sha256`、`calibration_ref`、`numactl`、source HEAD、producer sha、build admission receipts、各 run command/output digestを記録する。
4. 同じ raw bundleから、stock条件だけを射影した artifactと、structural-zero条件だけを射影した artifactを作る。
5. consumerが projectionを raw bundleから再計算して一致させる。projectionの `all_pass:true` 自己申告だけを受理しない。

repo は linux-baremetal を正式環境として定義し（[roadmap.md:323–331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/roadmap.md:323)）、2026-08-01時点に「使用可能だが今は使わない」と記録しています（[worklog-phase3-0801-102.md:7–10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/archive/worklog-phase3-0801-102.md:7)）。従って技術的な再測定経路の存在までは確認できますが、2026-08-05現在の予約・到達可能性は repo から確定できません。別 measurement task として人間が availability を確認すべきです。

linux-baremetal が使えない場合、Pegasus artifactを linux-baremetal originへ代用してはいけません。Pegasus の env contract/calibrationで別 originを発行するか、同じ linux-baremetal での再測定まで authority activationを止めます。

**成果物影響:** 再測定すると2 evidence refとそれを含む future origin IDが変わります。放置すると authority activationは拒否され、現在の certified 選択・材料レポート・試行台帳は不変です。

### 採用後の pin 閉包

最低限、次を同じ proof closure に含めます。

- authority generation document、その raw hash、13 field manifest、derived origin ID/cell key。
- spec、axis、verifier、IR schema/emitter truth table、role bundle、recipient schema、workload descriptor、environment projectionの path/hash。
- external CCBench full gitlink OIDと実行 submodule HEAD。
- stock/structural projection、その raw measurement bundle、calibration、build admission receipts。
- human approval record、active pointer、parent pointer、revocation tombstone、activation receipt。
- captured H の blob bytes、worktreeとの一致、導入後の履歴不変性。
- runtime genesis commitmentとauthority generation hash。
- producer側 origin proof、batchの3 receipt、sealed-batch projection、physical-query evidence manifest。
- source bytes変更、ref差替え、unlisted transition、duplicate cell/series、dirty worktree、revoked tipを実際に落とす境界テスト。

信頼根は、捕捉した Git H、human-only approval commit、immutable generation chain、full CCBench gitlink、git-common-dir runtimeのfsync/flockです。同じUIDによるGitとruntimeの協調改変、別 clone、Git rollbackは現 ledger自身も検出しないと明記しているため（[reflux_origin_ledger.py:11–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:11)）、残余として残します。

**成果物影響:** 閉包が揃うと origin proof から authority source/evidenceまで逆参照できます。どれかを外すと hash文字列だけが残り、P7 consumerが後から referentを検証できません。

## (2) production runtime bootstrap と authority 世代移行

### provisioning

P1 の「公開 API 3本は create=False、lazy-createしない」は妥当です。runtime root は `git rev-parse --git-common-dir` の下へ固定されています（[reflux_origin_ledger.py:1432–1451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1432)）。この worktreeの `.git:1` は共有 repository の worktree metadataを指し、`commondir:1` は `../..` です。従って迷い込んだ1 API callによる lazy genesisは全 worktreeを汚します。一方、common-dir束縛を外すと新worktreeごとに新品予算を得られるため、束縛自体は維持します。

ただし、P1 の「既存 `_initialize_locked` の禁止を条件化する」は推奨しません。fixture-only関数はそのまま残し、production専用の別入口を作る方が安全です。Pythonのprivate tokenは権限境界ではないため、保護はCLIのauthority検証とactivation receiptで行います。

推奨コマンド契約は次です。

```bash
python3 -m orchestrator.campaign.reflux_origin_admin provision \
  --expected-head <40-lower-hex> \
  --expected-authority-generation-sha256 <64-lower-hex> \
  --expected-authority-blob-sha256 <64-lower-hex> \
  --expected-active-pointer-sha256 <64-lower-hex> \
  --expected-git-common-dir /work/1/SFC/tanab/izanagi/.git \
  --emit-activation-receipt -
```

禁止する引数は `--runtime-root`、`--authority-path`、`--origin-id`、I/Q/K override、`--force`、`--create-if-missing` です。runtime/authorityの場所と全 origin はactive generationからだけ導きます。

主体と順序は次です。

1. 人間が generation artifactをcommitする。
2. 別のhuman-only commitでapprovalとactive pointerを同時導入する。
3. 人間が上記CLIを実行する。driverは呼べない。
4. CLIはGit・source closure・nonempty origin set・transition・common-dirをread-only検査した後だけ、決定的なstaging directoryへgenesisを書く。
5. 全 file/directoryをfsyncしてからactive epoch名へatomic publishし、canonical activation receipt bytesを標準出力する。
6. 人間がそのreceiptをcommitする。
7. 公開APIは、committed receiptとruntime genesisが一致して初めて利用可能になる。

冪等性・失敗状態は次の契約にします。

- 検証失敗: runtime directoryを作らない。
- crash中のstaging: activeではない。同じexpected値ならexact resume、不一致ならfail-closed。自動削除しない。
- active epochが既に完全一致: 書き込みなしで同じreceiptを返す。
- active epochが存在して不一致: overwriteせず停止。
- committed activation receiptがあるのにruntimeが無い: **新品genesisを拒否**し、backupからのrestore/forensic専用経路へ送る。
- receiptがまだcommitされていないruntimeは公開APIから不可視なので、利用前の再provisionによる予算resetは起きない。
- testはtemp Git repository内の同じengine、または既存fixture seamだけを用い、共有production rootへ触れない。

現 `_initialize_locked` はorigin filesを順に書いてからruntime headを作ります（[reflux_origin_ledger.py:2595–2639](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2595)）。productionではこの直接公開形を使わず、stagingの完全なtreeをatomic publishする必要があります。

**成果物影響:** 採用するとruntime受理集合に「human-ratified generationの明示provision」だけが加わり、activation receiptがproof chainへ入ります。放置するとproduction callerは永久に起動不能です。一相の `absent⇒genesis` を採ると、runtime削除がcounter reset経路になります。

### authority 世代移行

現 authority loaderは、HEADのcommitted blobとworktree bytesの一致を要求し（[reflux_origin_ledger.py:1592–1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:1592)）、runtime replayはgenesisに焼いたauthority blob hashとorigin集合の完全一致を要求します（[reflux_origin_ledger.py:2277–2310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:2277)）。従ってauthorityへの1 origin追加でも現runtimeは全拒否になります。

`s8b_ratified_freeze.py` からそのまま再利用すべき構造は次です。

- captured Hに固定したpure resolution。
- generation/approval/active-pointer/revocation/cancellationの厳密schema（[s8b_ratified_freeze.py:60–141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:60)）。
- 列挙外JSON Pointer変化を拒否するtransition checker（[s8b_ratified_freeze.py:627–676](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:627)）。
- source/closure blobの履歴不変性。
- human approvalとactive pointerを同一commitの2 file追加だけに制限するpairing（[s8b_ratified_freeze.py:1173–1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:1173)）。
- pointer fork、番号飛び、disconnected chain、revoked tipをすべてno-activeへ倒すresolution（[s8b_ratified_freeze.py:1198–1296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/s8b_ratified_freeze.py:1198)）。
- consumerへdeep-immutable objectだけを返すloader。

origin ledger固有に作り直す部分は次です。

- 各generationを累積authority documentとし、transitionで旧 `origins[]` prefixのbyte-equivalenceとappend-onlyを要求する。
- origin ID、cell key、authority series IDを**全世代横断**で一意にする。現検査は単一registry内のduplicate cellだけです。
- runtimeを `epochs/<introducing-generation-sha256>/` に分ける。
- new generation provision時は差分originだけをgenesisし、旧originを新epochへ複製しない。
- origin IDから導入generation/epochを解決し、historical readは旧epochへ、writeはactiveで利用可能なepochだけへ送る。
- active pointer切替前に、outgoing epochの全originをterminalにする。
- activation receipt、runtime欠落、backup/restore、post-use revocationを扱う。
- active pointer cancellationで古いbudgetを再活性化しない。activation receipt発行後はcancellationで後退せず、revocation+forward successorだけを許す。

「既存originの予算を世代跨ぎで再束縛しない」は正しいです。しかし「seal-and-succeedのみ」は厳しすぎます。`OriginSealed` は `certifiable` と `aborted` の両terminalを明示的に持ち（[reflux_origin_ledger.py:521–528,1303–1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:521)）、単一候補pilotはformal floorを満たさないため、success-onlyにすると最初のpilot generationから永久移行不能になります。

推奨は次です。

- 通常移行: outgoing originsがすべて `certifiable`。
- 非常移行: `aborted` originを含む場合、人間のrevocation/incident tombstoneを必須にし、未使用予算を失効させる。
- どちらも旧originを新epochへ再bindしない。
- aborted cellの再発行は既定拒否。同じcellを再試行する例外を設けるなら、別の明示裁定とreplacement recordを要求する。

**成果物影響:** 採用すると旧counter/proofは旧epochに固定され、新originだけが新budgetを得ます。放置するとauthority更新はblob mismatchによる全拒否のままです。旧originを新generationへ複製すると、試行台帳のQ/Iが新品になりproof chainが分岐します。

### 公開 authority reader と snapshot

公開 readerは追加を推奨します。ただし `OriginSnapshot` にすべてを載せる案は却下します。

```python
read_authority(origin_id) -> AuthorityBinding
```

`AuthorityBinding` は次を返します。

- immutable `AuthorityManifest`
- `manifest_sha256`
- `origin_id`
- `cell_key`
- immutable `BudgetPolicy`
- `introducing_generation_sha256`
- `authority_blob_sha256`
- `active_pointer_sha256`
- `activation_receipt_sha256`
- generation/revocation status

現 `OriginSnapshot` はcounterとconstraint classだけです（[reflux_origin_ledger.py:539–551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:539)）。ここには `cell_key`、authority generation hash、budget policy hashだけを追加し、manifest/budget object自体はreader側に一元化する案を推奨します。

open batchは別のopaque recovery readerに分け、公開してよいのは `batch_id`、phase、cardinality、query ordinals、commitment hashesまでです。`replicate_ordinal`、candidate bytes、result/constraint plaintext、origin-wide `replicate_counts` は出しません。D166が示すとおり、`replicate_ordinal==0` の件数はdistinct wire数を漏らします（[decisions.md:8266–8270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8266)）。

manifestとbudgetは既にcommit済みauthorityの情報なので、新しいseal前漏洩ではありません。危険なのはopen batchの実行依存情報です。producerはreplicate ordinalを自身のdurable journalとpost-seal `SealedBatch` から再構成し、global mapをreaderへ出してはいけません。

**成果物影響:** readerはauthority参照の重複実装を除き、producer proofへgeneration/blob hashを供給します。read-onlyなのでledgerのevent受理集合は変えません。open batch plaintextまで載せるとseal前projectionの受理情報が増えます。

## (3) 結線先と batch 形状

### N3 と physical query の境界

N3はledger上は確定です。同一candidateのR行は、query/replicate ordinalとsaltが異なるためdistinct commitmentになります。ただし現 ledgerの `sealed_queries` はevidence付きrow数であり、物理実行数ではありません。

現 benchは1 measurement pointの中で `reps` 回 `run_once` を呼びます（[runner.py:396–477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/calibrator/runner.py:396)）。各runのstdout/perf fileは一時directoryとともに削除されます（[runner.py:346–393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/calibrator/runner.py:346)。さらにcampaign側は最大3 roundの自動再測定を持ちます（[pipeline.py:294–385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/pipeline.py:294)）。

従って現 driverへ単に `reps=R` と `R member rows` を足すだけでは、次の偽装が可能です。

- 同じaggregate evidence digestをR行へ複製する。
- adaptive remeasureで実際はRを超えて実行し、選ばれたroundだけを課金する。
- raw repが消えた後、`tps[]` の長さだけを物理実行証明と名乗る。
- failed repを黙って間引く。

推奨するmeasurement shapeは「authorityが指定したexact Rを1 roundだけ走らせ、`require_all_reps=True`、unstableなら受理せずtombstone」です。これは不安定値を通す緩和ではなく、再測定で救済せず厳しい側へ倒すものです。代案として既存adaptive roundを維持するなら、最大round数Mをauthority入力とし、`M×R` slotを事前予約して未使用suffixをtombstoneする必要があります。

各repについてcreate-only `PhysicalQueryReceipt` を残し、少なくとも以下を束縛します。

- origin/batch/query/replicate ordinal
- candidate commitment
- binary SHA-256、full CCBench OID
- workload descriptor、env contract、numactl、command
- build/admission receipt
- stdout/stderr/perf raw digests、return code、throughput
- reservation receipt、start/finish、result evidence digest

formal consumerはR個のreceiptが相異なり、sealed member rowへ全単射することを検査します。

**成果物影響:** 採用するとproof chainにR個の物理receiptが入り、sealed rowの水増しをconsumerが拒否できます。放置するとqueries_used/sealed_queriesだけが増え、材料レポートや試行台帳は物理測定回数を証明できません。

### completeness / report / registry の調査結果

`attempt==1` / `retry==false` はrole invocationにだけ掛かります（[autonomous_trial_completeness.py:175–195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:175)）。bench repを増やしても、このpinは踏みません。

他consumerにも「1 generation = 1 physical measurement」というpinはありません。

- reportはgenerationごとに1 `harness` objectを持ちますが、bench payloadの `tps` はlistです。
- completenessのharness必須fieldは outcome/variant/stop_reason/iteration/ranだけです（[autonomous_trial_completeness.py:538–563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/autonomous_trial_completeness.py:538)。
- trial registryのbindingにはreplicate/origin fieldがなく（[trial_registry.py:103–129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/trial_registry.py:103)）、formal workloadはH1=rr80/H2=rr20です（[trial_registry.py:41–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/trial_registry.py:41)）。
- Layer-3はbench_done rowを読むだけで、repとのledger全単射を検査しません。

従って既存consumerとの衝突ではなく、必要なconsumerが存在しないことが問題です。opt-in report v3に `reflux_origin`、`physical_queries[]`、`origin_proof_ref` を追加し、completenessが全単射を検査する必要があります。formal trial registryはこのpilot v3をcertifyingとして受けず、現状の非certifying状態を維持します。

**成果物影響:** report v3/completenessを採用するとpilot report・journalの受理集合が増えますが、formal trial registryとcertified選択は増えません。consumerを足さずfieldだけ追加するとD164型の恒真保証になります。

### 8c driver の変更位置

8cを宿主にする場合、次の順序にします。

1. `run_trial()` のkeyword-only引数（[p3_autonomous_workload_trial.py:1685–1704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1685)）へ `reflux_origin_id: str | None` と `expected_authority_generation_sha256: str | None` を追加する。
2. CLIの `--max-generations` 周辺（[p3_autonomous_workload_trial.py:1928–1956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1928)）へ `--reflux-origin-id` と `--expected-authority-generation-sha256` を追加し、[呼出し位置:2002–2019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:2002)へ転送する。R/I/Q/KはCLI引数にしない。
3. opt-in時はworkloadをsingletonにする。origin manifestが1 workload descriptorを持つため、A/B/Cを1 originで回さない。
4. campaign identity生成（[p3_autonomous_workload_trial.py:587–611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:587)）後、provider/run-root/build副作用より前にauthority manifest、cell key、spec、CCBench、axis、verifier、env、role bundle、projection schemaを再導出して一致させる。
5. planner呼出しより前（[p3_autonomous_workload_trial.py:1455–1485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1455)）に `BatchReserved` をcommitする。
6. coder 1回は維持する（[p3_autonomous_workload_trial.py:1513–1531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1513)）。得た同じwireをR個のquery/replicate slotへbindして `BatchCommitted` する。
7. preview/auditorへ進む。現在public run-rootへ書くproposal（[p3_autonomous_workload_trial.py:1586–1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1586)）、provider raw、attempt journal、campaign WALはpreseal private stagingへ置く。
8. drive（[p3_autonomous_workload_trial.py:1606–1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1606)）で既存legacy+S2 correctness gateを一切緩めず、exact R physical receiptsを生成する。
9. drive後に `artifact_admission.require_admitted_campaign()` を呼び、immutable admission viewを取得する（[artifact_admission.py:723–738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/artifact_admission.py:723)）。
10. admitted evidenceだけから `BatchResultsPrepared`、`BatchSealed`、`read_sealed_batch` を行う。
11. producer origin proofを書き、preseal stagingを公開する。
12. outcome/metricsを受け取るcriticはseal後へ移す。現在はsealの無いままdrive直後に呼ばれます（[p3_autonomous_workload_trial.py:1647–1678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1647)）。
13. 最後にLayer-3をrenderする。現finalizerは全workload終了後です（[p3_autonomous_workload_trial.py:1278–1351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1278)）。Layer-3はcampaign配下の全fileをartifact refsへ含めるので、origin proofを先に置けば閉包へ入ります（[layer3_report.py:149–154,367–474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/layer3_report.py:149)）。

既定の非reflux経路はreport v2、role count、attempt journal、proposal bytesを不変に保ちます。既存期待値を変更せず、opt-in v3を別schemaとして追加します。

**成果物影響:** 採用すると8c pilotのreport/journal/Layer-3 refsにorigin予算と物理repが結線されます。正式H1/H2・trial registry・certified選択は不変です。放置すると8cはorigin IDもbudgetも知らないままです。

### pre-query reservation と caller先行の択一

| 案 | 評価 |
|---|---|
| 現FSMのまま、coder後・preview前に `BatchCommitted` | evaluation前freezeにはなるが、coder後・commit前にkillして新run-rootで候補を引き直せる。D163 3(a)を閉じないため却下。 |
| callerが独自reservation journalを持つ | ledger外のrootを複製すればbudgetを回避できる。authority rootと同じ耐削除性を再実装することになるため却下。 |
| ledger v3に `BatchReserved` を追加 | planner/coderより前にI/Qをno-refund消費できる。推奨。ただしFSM/event/reportの受理集合変更。 |

推奨v3 FSMは次です。

```text
IDLE
  → BatchReserved
  → BatchCommitted / BatchBound
  → BatchResultsPrepared
  → BatchSealed
  → IDLE
```

`BatchReserved` は `batch_id`、iteration、cardinality、origin-contiguous query ordinals、`request_binding_sha256` を持ち、ここでI/Qを増やします。request bindingはauthority generation、origin、trial binding、workload descriptor、generation、provider invocation IDs、Rを束縛し、run-root名を含めません。

candidate生成に失敗してもrefundしません。v3 memberは `candidate` と `unbound` のtyped commitmentを持ち、seal前はkindを公開せず、seal後にunboundをtombstoned rowとして開きます。合法な5-bit dummy wireで代用する案はreplicate countとconstraint classを汚すため却下します。全terminal pathはreservedを含む同じ4 event topologyにします。

processがreservation後に死んだ場合、同じoperation IDのexact replayか、保存済みresponseの続行だけを許します。raw responseが無ければroleを再呼出しせずunbound/tombstoneで閉じます。現在のrun-root fresh-only契約ではresumeできないため、recovery stateはcommon-dirのproducer stagingへ置く必要があります。

これは `OriginEvent` unionとD166の3-event形を変えます（現 union: [reflux_origin_ledger.py:531–536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:531)、D166: [decisions.md:8272–8278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:8272)）。従って単一候補であっても新D、ledger/runtime v3、境界テストが必要です。D96の「受理集合変更はdecisionと境界テストを同一変更単位」は [decisions.md:4271–4279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/docs/decisions.md:4271) に従います。

**成果物影響:** 採用するとbudget消費点が候補生成前へ移り、ledger v3の受理event列とI/Q値が変わります。caller先行だけではcommit前killが無課金のままなので、試行台帳のbudget値は実呼出し数を上限化しません。

### commit-reveal と単一候補の漏洩

単一候補にすると、複数候補間の勝者・順位・exact mask patternは漏れなくなります。しかし残るbitは明確です。

```text
既知の候補 wire が rejected constraint set の member か否か
```

すなわち1 candidateについてのaccept/reject membership bitです。R回反復しても、候補集合としては同じ1 bitです。ただしthroughput、CV、abort率、失敗タイミング等のR個の数値は、別のより大きなside channelです。

現実装にはseal前の漏洩点があります。

- preview pass/failでauditor skipと実呼出しが分岐する（[p3_autonomous_workload_trial.py:1533–1577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1533)）。
- 実呼出しrawを即時fsyncする（[p3_autonomous_workload_trial.py:904–939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:904)）。
- proposal fileがcoder wireとauditor verdictをseal前に保存する。
- campaign WALがverify/bench結果をseal前に保存する。
- criticへoutcome/metricsを直接渡す。

対策は、candidate/proposal/provider raw/WAL/physical receiptsを固定topologyのpreseal stagingへfsyncし、次roleへのprojectionから隔離することです。drive後はLayer-3を先に公開せず、admission validatorのimmutable viewだけを得てsealし、origin proof生成後にartifactを公開します。criticはseal後です。

ただし同じUIDのraw storage observerを防ぐには、別OS identity、暗号化vault、remote brokerのいずれかが必要です。現ledgerもseal event fsync後・head commit前のraw leakageを受容残余としています（[reflux_origin_ledger.py:20–23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:20)）。この設計だけで「seal前漏洩ゼロ」やP4充足を名乗ってはいけません。

**成果物影響:** 採用するとproducer artifactの公開時点とcritic入力時点がseal後へ移りますが、correctness verdictの条件は変えません。放置するとproposal/raw/WALの存在だけでmembership bitやmetricsがseal前に観測可能です。

### 結線先の択一

| 観点 | 8c autonomous trial | E段 loop |
|---|---|---|
| reservationを置ける最上流 | planner前に置ける | proposal受取時点では遅い |
| candidate生成の所有 | planner/coderを所有 | 外部proposalが既に生成済み |
| auditor | 内部でskip/callを制御 | proposal fileがauditor verdictとdiff digestを必須にする（[p3_s4_loop_trigger_gating.py:649–680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:649)） |
| report/proof配置 | trial/report/journalを所有 | loop WAL中心でtrial cross-refを別実装 |
| workload | ycsb-a/b/cのみ（[p3_autonomous_workload_trial.py:171–175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/p3_autonomous_workload_trial.py:171)） | E campaign形 |
| formal H1/H2 | 実行不能 | 現状のproposal契約のままでは正式系列に直結しない |

推奨は8cです。E段はproposal fileを受け取る前にcandidate materializationとauditorが済んでいるため、reservationを有効にするにはE driverだけでなく外部proposal producerまで改造する必要があります。

8c成果は「ycsb-a/b/cのうちsingleton1点で、単一candidate×Rのbudgeted sealed batchが生きた」というpilotに限ります。rr80/rr20、on/off/swapped formal arm、trial registry、certified selectionへの前進として数えません。`MAX_APPROVED_GENERATIONS=1` も変更しません。

**成果物影響:** 8c採用時はexploratory pilot reportとproof chainだけが増えます。Eを選ぶとproposal生成・auditorをreservation前へ移す追加producerが必要で、現材料レポート・試行台帳には直結しません。

### durable cross-reference

P7の配置は親P7どおりproducer側を推奨します。ledgerはtrial/campaign/reportを知らないままにします。

書き込み先は、seal/read-back後、Layer-3 render前の

```text
<campaign_root>/reports/reflux_origin_proof.json
```

とします。schema案は次です。

```json
{
  "schema_version": "izanagi-reflux-origin-proof/v1",
  "trial_id": "...",
  "campaign_id": "...",
  "workload": "...",
  "generation": 1,
  "origin_id": "...",
  "cell_key": "...",
  "authority_manifest_sha256": "...",
  "authority_generation_sha256": "...",
  "authority_blob_sha256": "...",
  "authority_active_pointer_sha256": "...",
  "runtime_activation_receipt_sha256": "...",
  "batch_id": "...",
  "batch_commit_operation_id": "...",
  "batch_commit_event_sha256": "...",
  "batch_prepare_operation_id": "...",
  "batch_prepare_event_sha256": "...",
  "seal_operation_id": "...",
  "seal_event_sha256": "...",
  "seal_resulting_state_commitment": "...",
  "sealed_batch_projection_sha256": "...",
  "physical_evidence_manifest_ref": {
    "path": "...",
    "sha256": "..."
  }
}
```

`seal_resulting_state_commitment` には、そのseal直後を表す `EventReceipt.resulting_state_commitment` を使います（receipt fields: [reflux_origin_ledger.py:561–569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-design/orchestrator/campaign/reflux_origin_ledger.py:561)）。別originの後続commitで変わり得る `current_state_commitment` だけをseal commitmentとしてはいけません。

trial report v3のgeneration recordには、

```json
"origin_proof_ref": {
  "path": "<campaign-relative path>",
  "sha256": "<raw proof bytes sha256>"
}
```

を置き、attempt journalにはpost-seal `origin-proof` eventを1件置きます。completenessはproofをdereferenceし、trial/campaign/workload/generation、3 event receipt、sealed batch、physical evidenceの全一致を検査します。formal P7 consumerが未実装の間は「producer proof artifactを出した」とだけ名乗ります。

proof自身にLayer-3 hashを入れると循環するため入れません。外側のtrial reportがorigin proofとLayer-3双方を参照します。

**成果物影響:** 採用するとpilot report・Layer-3 artifact refs・proof chainにorigin/authority/batch/sealの耐久参照が追加されます。放置すると後のP7 consumerは過去pilotをauthority blobやseal eventへ遡って結び直せません。

## D96 手続、発火条件、名乗り

次はすべて新Dと境界テストを伴う受理集合変更です。

1. manifest v3のcontent-addressed `candidate_ir.schema_ref`。
2. active authority generation/approval/pointer/activation receipt。
3. production provisioning。
4. runtime/event v3の `BatchReserved` とtyped unbound member。
5. opt-in autonomous report v3、completenessのphysical-query/proof全単射。
6. 将来、複数candidateを正式report/trial registryへ通す変更。

既存v2 ledger golden、既存report v2、`attempt==1/retry==false`、legacy+S2 correctness、formal trial registryの期待値は変更しません。新schemaを並立させます。

恒真な検査を避けるため、現 baseline に対する発火条件を明示します。

| 検査 | 現 baseline で実際に発火する条件 |
|---|---|
| authority nonempty/active | 現 `reflux_origin_authority_v2.json:1` は `origins:[]` なのでprovisionがdirectory作成前に拒否する。 |
| full CCBench OID | 現 `CURRENT_PIN="d706650"` をmanifestへ使うと40-hex gateで拒否する。 |
| s8a evidence | 現 artifactのlinux-baremetal/2100、numactl欠落、short pin、build admission欠落で拒否する。 |
| production role bundle | fixtureのcontract-only effective hashをproduction bundleとして使うと、production provider算出値と不一致になる。 |
| reservation trace | 現8c opt-in相当traceはplanner eventがreservationより先なのでv3 trace checkerが拒否する。 |
| physical-query closure | 現runnerはper-rep rawを削除し、adaptive roundを許し、receiptを出さないのでv3 consumerが拒否する。 |
| origin proof | 現completeness event universeとreport v2にproof event/refが無いのでv3 consumerが拒否する。 |
| formal workload | ycsb-a/b/c reportはrr80/rr20 bindingを満たさずformal registryに入らない。 |

一方、positive production provision、generation transition、runtime削除後のrestore拒否は、現 baselineにnonempty authorityもactivation receiptもproduction runtimeも無いため、今は正側へ発火できません。temp repositoryのratified fixtureと、最終的には実authority・実pilotが必要です。それまでは「検査が緑」と報告してはいけません。

本設計を実装し実pilotまで成功して名乗ってよい上限は、次の2つです。

- 「ratified origin-authority control planeと明示production provisioningを実装した」
- 「8c exploratory workload 1点で、単一candidate×Rのreserved/sealed batch、physical receipts、durable origin proofを生成した」

「P3充足」「P3の部分実装」「P4充足」「規律3の還流を実現」「軸(iii)の反oracle性を満たした」「formal H1/H2」「certified選択へ前進」は名乗れません。P3/P4、cap-lift、formal consumerはFAILのままです。

## 総括

**1. N1〜N12の誤り。** 明確な誤りはN6です。完全に使える既存規則は3件でなく2件で、`ccbench_commit_oid` の現値は7文字のためmanifest不受理です。また `candidate_ir.schema_ref` にはtoken値規則が既にありますが、schema bytesへの参照がありません。N7のhardcode原因は正しいものの、numactl・full OID・build admission・artifact鮮度も修復対象です。N3はledger semanticsとして正しく、Rがbatch minimum以上等の条件と「物理query証明ではない」という限定が必要です。

**2. (1)(2)(3)の推奨。** (1) 13 fieldをcommit済み名前付きartifactのraw bytesへ束縛し、人間ratified authorityがseries/budget/evidenceを発行する、(2) 公開APIはcreate=Falseのままhuman-triggered二相provisioningとepoch別authority世代台帳を導入する、(3) ledger v3のpre-query reservationを伴う単一candidate×Rの8c pilotを先行し、physical receiptsとproducer origin proofをreport v3で検証する、を推奨します。

**3. 実装しても閉じない残余。** 正式H1/H2 driver、複数candidateのD96変更、1-bit membership oracle、同UID/raw-storage observer、別clone・Git rollback・runtime backup/restore、formal P7 consumer、authority evidenceのlinux-baremetal再測定、R/E_min/Imax/Qmax/Kmax/batch値の人間裁定、aborted cell再発行方針、schema/backendとしてのLLM実体束縛、P3/P4/cap-lift/certified選択が残ります。

**4. ユーザー裁定が要る択一。** (1) `candidate_ir.schema_ref` をmanifest v3のcontent-addressed refにするか、v2 tokenとgeneration外部表を維持するか（前者推奨）、(2) authority activationを二相provisioning+committed receiptにするか一相にするか（二相推奨）、(3)世代移行をcertifiable-onlyにするか、aborted+human revocationを非常移行として認めるか（後者推奨）、(4)同一cell再発行を全面禁止するか明示replacement例外を設けるか（既定全面禁止推奨）、(5)公開readerをauthority bindingとminimal snapshotへ分離するかfull manifest/open batchをsnapshotへ載せるか（分離推奨）、(6)pre-query `BatchReserved` をledger v3へ入れるかcaller制御だけで済ませるか（ledger v3推奨）、(7)exact R・1 round・unstable拒否にするか、最大M roundを全予約するか（前者推奨）、(8)結線先を8cにするかE段にするか（8c推奨）、(9)linux-baremetalを再確保してevidenceを取り直すか、別envの別originへ切り替えるか（同一cellを使うならlinux-baremetal再測定推奨）。