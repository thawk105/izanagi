静的監査のみを行い、pytest は実行していない。結論は、案 A も H1 も単独では NO-GO。A の「immutable archive + hash resolver + current 型」と、H1 の「旧 blind seal を保持した実行束縛 envelope」を組み合わせる必要がある。

## 所見

### 1. successor contract が attestation 無効化まで許している

- `[severity: must-fix]`
- 攻撃シナリオ: g2 を新較正へ更新すると同時に `attestation_mode="none"`、`single_process=False` にする。hash は新しく一意で、env tag・世代番号・path/SHA・current 一意性はすべて案 A の検査を通る。その後 protocol を g2 hash で発行すれば current 完全一致にもなるが、実行経路は v1 receipt を発行して実測 attestation を行わない。
- 根拠: `s2-plan.md:148-155` の構築検査には predecessor→successor の差分制約がない。`orchestrator/campaign/env_contract.py:123-139` は `none` を正規値として許し、`orchestrator/campaign/s8b_floor_campaign.py:2765-2778` は `none` なら probe を通さず receipt を作る。D143 が許可したのは較正の取り直しであって契約全 field の変更ではない (`docs/decisions.md:6976-6980`)。
- 提案: 同一 `env_tag` の successor は、ユーザーの別裁定がない限り `calibration_ref.path/sha256` 以外を predecessor と完全一致させる transition predicate を必須化する。特に `attestation_mode=="required"`、isolation、clocks、numactl を固定する。
- 検査を殺す変異: `g2 = replace(g1, attestation_mode="none", isolation_policy=...)` が activation 前に必ず赤になること。
- **成果物影響**: certified 選択が attestation なしの run を受理し、材料レポートと試行台帳には一見正しい g2 hash だけが残る。

### 2. history resolver の「検証専用」は命名規約でしかない

- `[severity: must-fix]`
- 攻撃シナリオ: oracle driver、receipt issuer、certified selector の `require_current()` を `resolve_by_contract_sha256(g1)` に置換する。g1 内部の hash・receipt・single-contract closure はすべて整合するため、履歴証拠が current campaign に流入する。
- 根拠: 案 A は public な resolver と current API を並置し (`s2-plan.md:136-145`)、呼出不能性を文章で宣言するだけ (`s2-plan.md:189-202`)。現行 issuer は汎用 `ExecutionEnvironmentContract` を受け取り、current provenance を要求する型ではない (`orchestrator/campaign/execution_guard.py:284-310`)。
- 提案: `HistoricalContract` と `CurrentContract` を別型にし、receipt/build/launch/selection issuer は後者だけを受け取る。`CurrentContract` は closure 検証済み activation からのみ構築する。実 production callsite を `require_current`→history resolver に変える mutation を必須にする。
- **成果物影響**: g1 証拠が g2 の certified 選択へ混入し、材料レポートと試行台帳の世代境界が虚偽になる。

### 3. `GENERATIONS`・`REGISTRY`・bundle activation が三重権威になる

- `[severity: must-fix]`
- 攻撃シナリオ: lifecycle を g2 current にし `REGISTRY` も g2 へ向けるが、g2 bundle/journal/silo closure は未完成のままにする。generic campaign は `lookup()` だけで g2 receipt を発行できる。案の closure test は pointer 反転後に走るため、その commit 自体が既に実行可能状態を公開する。
- 根拠: 二つの mapping が別々に定義される (`s2-plan.md:131-134`) が、「sole current と REGISTRY が同一」という invariant がない。段3で pointer を反転し (`s2-plan.md:279`)、closure 検査は段4 (`s2-plan.md:280`)、sentinel は段5 (`s2-plan.md:281`) である。generic campaign は receipt の後にそのまま campaign ID/layout を作り、bundle を読まない (`orchestrator/campaign/loop.py:139-144`)。
- 提案: `REGISTRY` を独立データにせず、検証済み activation record から導出する。`require_current` 自体が complete bundle/closure capability を要求し、closure receipt がない g2 は pointer 値にかかわらず issuer へ渡さない。
- 検査を殺す変異: pointer だけを g2 に変えた状態で、実 `run_campaign` が最初の receipt より前に拒否すること。
- **成果物影響**: closure 不完全な世代で試行台帳が開始され、後から selector/silo 参照が解決不能になる。

### 4. 案 A は blind seal を再発行し、H1 は分割表を書き換えられる

- `[severity: must-fix]`
- 攻撃シナリオ: 案 A で `APPROVED_MASTER_SEED` や `wired_min_rel_floor` を変更し、g2 golden も更新して新 protocol・新 selector predictions を発行する。較正移行を理由に実験設計と予測まで選び直せる。H1 では逆に `master_seed` や `formula` を「環境束縛側」へ移してから変更すれば、design projection の一致が恒真化する。
- 根拠: 案 A は g2 protocol と selector evidence を新規生成する (`s2-plan.md:278-279`) が、g1 design との equality を要求しない。protocol の18 key は `orchestrator/campaign/s8b_floor_contract.py:34-40`、自由値の正本は `orchestrator/campaign/s8b_approved.py:45-58`。H1 の防壁は可変な key 分割そのものに依存する (`parent-design-candidate.md:28-38`)。D143/D155 は selector 再発行を裁定していない。
- 提案: legacy 移行では「新 protocol の `contract_sha256` を g1 値へ戻した canonical bytes が旧 protocol bytes と完全一致」を要求する。`env_tag` を含む残り17 key は不変とし、可変 partition を設けない。旧 predictions を execution-binding envelope から再利用するか、再封印を別のユーザー裁定へ返す。
- 検査を殺す変異: `APPROVED_MASTER_SEED += "-changed"`、または partition へ同 key を移す変更が必ず赤になること。
- **成果物影響**: certified 選択の予測・採否が較正とは無関係に変わり、材料レポートと selector journal が別実験を同じ移行として記録する。

### 5. `historically_verified` を将来も実行できる機構がない

- `[severity: must-fix]`
- 攻撃シナリオ: 将来 protocol/formula を v3 に更新し、current validator の v2 定数を置き換える。g1 contract は hash resolver で解決できても、現行コードは v2 predicate を実行できず拒否する。逆に schema/formula 検査を飛ばせば「内部 hash が合うだけ」の恒真な history verifier になる。
- 根拠: 現行 validator は単一の `PROTOCOL_SCHEMA`/`FORMULA_ID` とだけ比較する (`orchestrator/campaign/s8b_floor_contract.py:25-32,122-135`)。段2は versioned predicate の実行を要求する (`s2-plan.md:296-308`) が dispatch/retention を設計せず、git object 消失時は保証外ともしている (`s2-plan.md:338`)。
- 提案: `(schema, formula, predicate_version)` による閉じた verifier dispatch と、g1 の実 artifact replay を恒久 trust root にする。未知版・実装削除・source/data 消失はいずれも明示 `unresolved` とし、current verifier への fallback を禁止する。
- 検査を殺す変異: v2 dispatch entry を削除して g1 full proof replay が赤になること。
- **成果物影響**: 旧 certified 参照が再び解決不能になり、材料レポートの historical verification と台帳の proof-chain 参照が失われる。

### 6. closure 検査に空集合・自己申告集合の恒真化穴がある

- `[severity: must-fix]`
- 攻撃シナリオ: bundle の selector file 宣言を空にする、origin records を0件にする、または g1 を `GENERATIONS` から削除する。宣言集合だけを正本にした exact-set、`len(set(hashes)) <= 1`、登録世代の列挙検査はいずれも緑になりうる。さらに bundle schema は selector までしか持たないのに、段3は silo/origin も closure 済みと扱う。
- 根拠: bundle の列挙は calibration/protocol/selector まで (`s2-plan.md:167`)。single-contract と mutation 群は `s2-plan.md:204-216`、silo/origin 追加は `s2-plan.md:279`。origin ledger は production consumer 未配線と段2自身が認める (`s2-plan.md:26,76,337`)。現行 frozen test は別の独立 keyset を持つことで自己申告を避けている (`orchestrator/tests/test_frozen_artifacts.py:87-149`)。
- 提案: bundle 外の独立 frozen required-role/keyset、非空 cardinality、literal g1 trust roots、producer→loader→issuer の実 entrypoint mutation を必須化する。silo/origin が activation 必須でないなら closure から外し、保証したと名乗らない。bundle は canonical path・no-symlink・read-once bytes を返す。
- 検査を殺す変異: `selector_files=[]`、`records=[]`、`GENERATIONS["pegasus"]=(g2,)` の各一行を独立に赤へする。
- **成果物影響**: bundle が緑でも selector/silo/ledger 参照が欠落し、certified 選択と材料レポートの closure が部分集合になる。

### 7. 案 B/C は別名の二重権威であり、案 D は非適合

- `[severity: must-fix]`
- 攻撃シナリオ:
  - B: legacy mapping の `261cec…` を g2 manifest へ差し替える。history 側で protocol 内包 hashとの再照合を欠けば、旧 protocol を新 calibration で「検証済み」にできる。
  - C: `pegasus` を historical-only と宣言しても、残った `lookup("pegasus")` caller が旧契約を launch する。逆に lookup が historical tag を拒否すれば旧 history verifier まで止まる。
  - D: registry を g2 に反転すると、旧 protocol は直ちに current hash 不一致になり、P3を満たせない。
- 根拠: B の legacy mapping と current 側だけの二重照合は `s2-plan.md:237-241`。C の lifecycle/hard-coded consumer 問題は `s2-plan.md:254-260`、実 caller は `orchestrator/campaign/loop.py:72-75`、`orchestrator/campaign/silo_ladder_rung1.py:3519-3527`。D の破断は `s2-plan.md:262-268`。
- 提案: B/C は安全な同格候補として提示せず、Aの hash authorityへ正規化する。Bを残すなら protocol SHA→manifest SHA→embedded contract SHA の全辺を再計算する。Cを残すなら current/history 型分離をAと同じ水準で実装する。Dは非適合 negative control とする。
- **成果物影響**: Bは旧材料レポートを誤った較正へ再束縛し、Cは旧世代を新 trial ledgerへ流し、Dは旧参照を解決不能にする。

### 8. 実投入 wrapper が新 namespace を読まない

- `[severity: must-fix]`
- 攻撃シナリオ: A の `contracts/<g2-hash>/floor_protocol.json` を完成させても、Pegasus の正規 wrapper は旧固定 path を driver へ渡す。current は g2、protocol はg1となり、実投入だけが必ず拒否される。
- 根拠: 段2の inventory は wrapper を発見している (`s2-plan.md:59`) が、実装位置と移行手順 (`s2-plan.md:169-177,274-281`) から落ちている。wrapper は `PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"` を固定している (`tools/pegasus/floor_campaign.sh:880-897`)。
- 提案: wrapper は検証済み activation bundle を一度解決し、その protocol path/hash/bundle hash をdriverと job-result の双方へ渡す。自由な path 引数や自動 fallbackは禁止する。
- **成果物影響**: 修正なしでは floor campaign が開始できず、certified 選択・材料レポート・試行台帳はいずれも生成不能。

### 9. 8c/P3 下流は scope 外だが、裁定パッケージに必要

- `[severity: should-fix]`
- 攻撃シナリオ: 将来 P3 producer を接続した際、旧 prereg contract は単なる `lookup` と `load_ratified_freeze` の到達性だけで充足判定するため、current capabilityやcampaign contract hashを束縛しないまま試行を開始できる。
- 根拠: prereg contract は `run_trial -> env_contract.lookup -> receipt` を要求する (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:430-486`)。ratified generation も production reachability の対象 (`同:24-39`)。一方、現状は D163 により producer 未接続・P3 FAIL (`docs/decisions.md:8077-8087,8134-8136`)。
- 提案: 今回は実装済みと数えず、P3再開時に `CurrentContract`、bundle hash、campaign identity、trial-registry acceptance まで prereg contract を更新する裁定項目として返す。
- **成果物影響**: 現在値は不変だが、未処置のまま再開すると将来の試行台帳と certified acceptance が contract 世代を束縛しない。

### 10. D155 の観測者効果 blocker を migration entry condition にしていない

- `[severity: must-fix]`
- 攻撃シナリオ: self-gate を通らなかった attempt artifactを直接 `registered/` へ複製し、path/SHAだけをg2世代へ登録する。案Aの構築検査は通り、後でcurrentへ反転できる。
- 根拠: D155 は CLI publish 以外を loader/hook が拒否しないと明記する (`docs/decisions.md:7706-7711`)。さらに現 probe のままでは再取得しても通らない (`同:7713-7720,7730-7731`)。段2の pending 登録条件は path存在とSHA一致まで (`s2-plan.md:148-155,278`)。正規 CLI の self-gate は publish 前に発火する (`orchestrator/calibrator/cli.py:608-627,629-654`)。
- 提案: R-1 probe 実装・因果実測・CLI accepted publish receipt・独立 self-comparison・current exception集合空、の全てをU-2 entry conditionにする。直接追加した calibration は hashが正しくても activation不能とする。
- 検査を殺す変異: rejected attempt の bytes を generationへ直接登録して activationが必ず赤になること。
- **成果物影響**: 不整合較正なら campaign は再び attestation で停止し、例外登録なら不正な run が certified 候補と台帳へ入る。

### 11. rollback 設計は commit 内中断と activation 後を扱っていない

- `[severity: must-fix]`
- 攻撃シナリオ: 段3で journal/predictionsをcreate-only発行した後、bundleまたはpointer更新前に中断する。まだcommitがないため「commit全体をrevert」は使えず、再試行は既存 predictions を拒否する。さらに段3 commitは段4検査前にcurrentを公開するため、最初のg2 receiptが出た後のrevertはその台帳を消せない。
- 根拠: 計画のrollback記述は commit単位だけ (`s2-plan.md:277-280`)。現 seal は HEAD一致・clean worktree・既存predictions不在を要求する (`orchestrator/campaign/s8b_prediction_runner.py:1547-1555`)。pointer反転がclosure検査より先なのは `s2-plan.md:279-280`。
- 提案: generation固有staging rootとcreate-only abort tombstoneを設け、中断したsealは削除・再利用せずabandonedとして保持する。closure receipt取得後だけactivationを発行する。activation後にg2 receipt/certified resultが一件でも出たらrollbackではなくrevocation＋forward fixとする。
- **成果物影響**: 中断世代の参照が孤児化し、revert後も試行台帳にg2 receipt、current選択にg1という分裂状態が残る。

### 12. 親の lookup call 数は実callと束縛を混同している

- `[severity: nit]`
- 攻撃シナリオ: import aliasをcallとして数えるinventoryでは、実consumer移行の完了判定を誤る。
- 根拠: 親は20 callとする (`parent-closure-measured.md:14-15`) が、実callは直接16件＋alias経由2件で18件。段2の列挙 `s2-plan.md:24,29` と静的検索結果が一致する。
- 提案: 「実call」「alias/import binding」「wrapper」の三分類を固定し、移行チェックは実call18件を対象にする。
- **成果物影響**: 現在の受理集合・値は変わらないが、consumer closure の完了件数を誤報する。

## 親推論の判定

N1 は現在のコードについては反証できない。contract hash は calibration ref を含む全 field から導出され (`orchestrator/campaign/env_contract.py:94-102,145-160`)、単一 current lookup (`同:180-205`) と protocol 内包hashの一致が必須 (`orchestrator/campaign/s8b_floor_contract.py:138-151`)、旧bytesはhistory blobと一致必須 (`orchestrator/campaign/s8b_floor_campaign.py:1411-1416`) だからである。同じ旧artifactで両条件を保つ第三の道はない。

ただし「数値世代列Aだけが唯一」は定理ではない。H1やcontent-addressed archiveも実装表現としては可能だが、いずれも旧bindingと新bindingを同時保持するため、論理的には世代分離である。

P3 はそのままでは反証される。「current eligibility不要」は正しいが、parse・内部hash一致だけのverifyでは不十分であり、versioned predicateとproof-chain全辺の再実行可能性まで必要である。

## 総括

- **NO-GO** — must-fix が未解消のまま案A/H1を裁定へ出せない。
- 推奨は A の immutable hash authority/current型と、H1の厳密な execution-binding envelope の併用。
- H1単独はresolver・issuer・ledger・activationを閉じず、A単独はblind sealを守らない。
- 所見: **must-fix 10 / should-fix 1 / nit 1**。
- 親の実測反証: **1件**（lookup実call 20→18）。
- 親の推論反証: **1件**（P3の「verify可能なら十分」）。
- N1と「論理的な多版分離が必要」は未反証。
- 不可逆リスク境界は段3 pin-closure commit、意味的不可逆点は最初のg2 receipt/certified台帳発行。