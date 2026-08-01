# T-244 規律 3 還流設計 v1 — 段 2 起草案

結論は、**whiteboard の 5 field は増やさずに成立するが、親 brief (P3) の「動的 constraint 文を coder の `gating_spec` へ追記する」案は採れない**、である。動的制約は trusted machine 内の固定 5-bit IR として保持し、planner/coder には固定 schema だけを見せる。multi-generation は本設計の実装・検証が終わるまで D114 の上限 1 を維持する。

## A. 設計本体

### 1. recipient matrix

現行の共通 payload は [p3_autonomous_workload_trial.py:601–618](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:601) である。

| recipient | 現行 | 設計 v1 | 差分 |
|---|---|---|---|
| planner | descriptor、`current_perf`、leading indicators、whiteboard。[同:816–825](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:816) | descriptor、固定目標、generation 番号、固定 `candidate_ir_schema_sha256` のみ | `current_perf`、leading indicators、whiteboard を外す。前世代の accept/reject・constraint・残予算も見せない |
| coder | 固定 `gating_spec`、planner の axis/direction/magnitude、`baseline`、whiteboard。[同:843–860](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:843) | 固定 byte 列の `gating_spec_v2`、固定 5-bit IR schema、planner の 3 field | `baseline`、whiteboard、動的 constraint 文を外す。出力を自由な一行 C++ から正準 5-bit mask へ閉じる |
| auditor | `working_diff` 全文、digest、source context、pre-build digest。[同:897–905](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:897) | machine が constraint を適用した**実効 diff**、raw/effective IR の SHA、固定 obligation、source context | hidden constraint mask、前失敗理由、raw coder 自然文は見せない。auditor は veto のみで constraint producer にならない |
| critic | harness outcome、metrics、critic digest 全文。[同:957–967](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:957) | origin seal 後の audit-only recipient。full verifier evidence と constraint proof ref を読む | `reverse_recommended` を次 iteration の制御に戻さない。現行の `prior_reverse` 配線 [同:923–950](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:923) と [同:980–983](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:980) は 8c multi-generation では report-only 化する |
| trusted machine | preview、diff、auditor verdict、harness/WAL、loop state を個別に処理 | 加えて origin manifest、予約台帳、hidden constraint mask、last certified frontier、raw/effective IR を保持 | failure→constraint 変換、正準 emitter、予算予約の唯一の主体 |
| 公開 API/report | outcome、stop reason、複数 subtype を区別しうる | active window 中は固定二値のみ。詳細は trusted control WAL、公開 class は seal 後最大 1 | adaptive oracle の応答 alphabet を閉じる |

Whiteboard は [p3_s4_loop.py:108–118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop.py:108) の

`iteration / direction / magnitude / result / delta_pct`

の 5 field のままとする。constraint は第 6 field ではなく別の origin control state に置く。したがって「whiteboard を増やさない」は成立する。ただし、8c の generator projection から whiteboard 自体を外す。D39 の保存形式は変えず、8c の recipient だけを D116 が狭める。

なお現行 loader は未知 key を拒否するが、`direction` / `magnitude` / `result` の値域を閉じていない [p3_s4_loop.py:371–404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop.py:371)。親 brief の「型は閉じている」は field 名に限った記述へ訂正する。

### 2. 固定 constraint IR と最大公開 bit 数

対象 universe は、実装済み列挙空間 [axis_trigger_gating.py:41–51](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/axis_trigger_gating.py:41) の 5 atom とする。

```text
0 lock-conflict
1 update-absent
2 readvali-tid
3 readvali-locked
4 node-vali
```

1 は「その abort reason では backoff 必須」を表す。`kUnset`、`insert-node`、`scan-node` は v1 では常に true とし、動的 universe に含めない。insert/scan の structural-zero 証拠が対象 workload で再確認できなければ origin を開かない。

- generator の raw mask を `P_t`
- 累積 constraint mask を `C_t`
- machine が実際に emitter へ渡す mask を `E_t = P_t ∨ C_t`

とする。動的な自然文は生成しない。固定 `gating_spec_v2` は全世代で byte-for-byte 同一であり、machine が enum 順に一意の C++ 式を emit する。

| 面 | 最大容量 |
|---|---:|
| hidden constraint state | 5 bit。ただし trusted state の保存容量であり公開量ではない |
| planner→coder の direction×magnitude | `log2(9) ≈ 3.17 bit/世代` の容量は残る。ただし planner に failure 情報を渡さないため、failure に条件づけた情報量は 0 bit |
| planner/coder に見える動的 constraint / result | 0 bit/世代 |
| untrusted API の query result | 二値固定なので最大 1 bit/実 query |
| 1 origin window | `Qmax=2` なので最大 2 bit |
| seal 後の class 公開 | `none` または 5 atom の 6 状態、最大 `log2(6) ≈ 2.585 bit` |
| window 全体の保守的上限 | `2 + log2(6) ≈ 4.585 bit` |

この上限を成立させるため、公開 report に総 constraint 数、詳細 stop reason、自然文 reason、未公開 atom の hash を載せない。5 値の単純 SHA は辞書攻撃できるため、未公開 constraint は trusted state にのみ置き、公開側は opaque ID と machine-owned nonce を含む commitment だけにする。

#### 前 wave と同じ攻撃

- **候補 B の 3.17-bit 符号化:** planner→coder の物理容量は残るが、planner は whiteboard、結果、constraint、metrics を読まない。したがって符号化する failure class を持たない。provider が role 間で隠れた session state を共有する場合はこの前提が壊れるため、その invocation は fail-closed にする。
- **候補 C の padding:** malformed、duplicate、既知 forbidden identifier、role-invalid、dry/no-op を含め、すべて query slot を先に消費する。2 件を既知 class で padding すれば origin はそこで枯渇し、3 件目を照会できない。window の roll-over はなく、新 origin には人間管理の registry 更新が必要である。
- **constraint 文チャネル:** 例えば `kReadValiLocked のとき true 必須` は、それだけで 5-class 中の一つ、最大 `log2(5) ≈ 2.322 bit` を coder へ漏らす。順序、空白、同義語、コメントによる padding も可能である。よって P3 の動的追記は不採用とし、固定 schema＋hidden mask＋正準 emitter に置き換える。

### 3. accept-reject query の総予算

設計 v1 の規範値は、**一つの事前登録済み workload × treatment cell の origin ごとに**次とする。

```text
Imax = 2  総 generation/iteration 予約
Qmax = 2  総 candidate query
Kmax = 1  seal 後に公開できる exact constraint class
```

2 世代は「失敗を constraint 化し、次の一手へ一度だけ効かせる」最小の cross-generation window である。A/B/C の別 workload は別 origin にできるが、同じ cell を trial 名や run-root だけ変えて複製することはできない。

計数規則は次のとおり。

1. planner 呼び出し前に iteration と query の slot を同時に原子予約する。
2. malformed role output、preview reject、auditor reject、duplicate、infrastructure failure、provider crash も消費し、返却しない。
3. `preview()` や direct `drive_iteration()` にも一回限りの予約 token を要求する。token の再利用は拒否する。
4. 3 件目は provider・preview・build のいずれにも到達させず fail-closed にする。
5. 早期停止時は残 slot を tombstone として消費し、公開 transcript は常に 2 slot とする。停止位置そのものを追加記号にしない。
6. API 応答は `accepted | rejected` の二値だけとし、subtype は active window 中に返さない。

現行 `wal.append()` の flock は一 record の追記だけを覆う [wal.py:283–378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/wal.py:283)。`read → count → wal.log` では TOCTOU が残る。実装時は同じ flock を保持したまま count 検証・reservation append・fsync を行う専用 primitive が必要である。

### 4. constraint producer

producer は **trusted machine の固定 translator のみ**とする。planner、coder、auditor、critic は producer ではない。

v1 が `must-backoff(r)` を作れる条件を次へ閉じる。

1. candidate は正準 5-bit IR である。
2. last certified frontier から、未拘束 atom `r` を一つだけ `true→false` にした singleton relaxation である。
3. diff quarantine、syntax gate、auditor gate は通過している。
4. 同一 origin・commit・verifier policy で、WAL に `verify_done` と terminal `abort` があり、`certified=false`、`verdict=non-serializable`、integrity は clean、構造化 anomaly が存在する。
5. machine は失敗した singleton relaxation の `r` を constraint 集合へ追加し、次候補では必ず true に戻す。

複数 bit 変更、trace integrity failure、liveness/infrastructure failure、auditor の自然文判断、role-invalid から atom を推測してはならない。これらは query を消費して origin を seal する。

現行 verifier は anomaly を構造化するが、通常 verify の `abort_reasons` は常に空である [report.py:42–75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/verifier/report.py:42)。したがって anomaly 文から LLM に atom を推測させる設計にはしない。将来 LLM を補助的に通す場合も、machine が上記条件から同じ atom を独立再導出できた場合だけ採用し、不一致なら seal する。

### 5. origin binding

現行 `ident.canonical_preimage()` は `spec_content`、`ccbench_commit`、`search_tag`、`search_config`、`trial` を含む [ident.py:76–103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/ident.py:76)。`generation_budget` も `search_config` に入る [p3_autonomous_workload_trial.py:426–455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:426)。

これは個別 campaign の同一性には十分だが、global budget には不十分である。`trial`、`generation_budget`、search tag 等を変えれば別 campaign ID を作れるためである。

そこで CampaignConfig より一段上に `reflux-origin/v1` を置く。origin preimage は次を含む。

- human/authority が発行した immutable series ID
- `spec_content` SHA、CCBench commit、axis/search semantics
- workload descriptor SHA、records、threads
- verifier policy、environment contract
- candidate IR schema と正準 emitter の SHA
- role bundle・recipient projection schema の SHA
- `Imax/Qmax/Kmax`
- stock certification と structural-zero evidence の artifact reference

次は含めない。

- `run_root`
- `trial`
- invocation ID
- provider 呼び分け
- 一回の CLI `generation_budget`
- process 分割や resume 名

各 CampaignConfig の `search_config` には `reflux_origin_id`、`reflux_policy_sha256`、`candidate_ir_schema` を追加する。これにより個別 campaign は現行 `canonical_preimage` にも束縛される一方、trial の異なる campaign も同じ origin ledger を共有する。

新 origin は、通常の programmatic caller が任意 JSON を渡して発行できてはならない。tracked allowlist または署名済み registry に manifest SHA がある場合だけ admission する。raw driver を直接呼んだ artifact は作れても、origin reservation proof のないものは正式 8c report / certified proof chain に入れない。

### 6. report と WAL

`WAL_STAGES` は現在閉じた列挙である [model.py:21–32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/model.py:21)。実装時は terminal でない `STAGE_REFLUX_CONTROL = "reflux-control"` を追加し、固定 variant `"reflux-origin"` を使う。

実際の呼出形は次に合わせる。

```python
wal.log(origin_layout, "reflux-origin", STAGE_REFLUX_CONTROL, env_tag, payload)
```

これは現行シグネチャ [wal.py:499–506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/wal.py:499) と一致する。

| event | payload |
|---|---|
| `origin-opened` | schema version、origin ID、manifest path/SHA、policy SHA、I/Q/K 上限、IR/projection SHA |
| `slot-reserved` | slot seq、one-use token SHA、campaign ID、`canonical_preimage` SHA、run/invocation ref、workload、generation、予約後 counter |
| `query-bound` | slot seq、proposal artifact SHA、raw IR SHA、effective IR SHA |
| `constraint-added` | opaque constraint ID、`singleton-relaxation-red/v1`、source refs、旧/新 state commitment。exact atom は trusted state のみ |
| `query-result` | slot seq、公開二値、`verify_done` / `abort` record ref、effective diff SHA |
| `slot-tombstoned` | 早期 fail-closed 後の未使用 slot を無返却消費したこと |
| `origin-sealed` | 消費 counter、control WAL bytes/SHA、state commitment、公開する最初の atom または `none` |

source ref は少なくとも `campaign_id / variant / stage / record_ordinal / payload_sha256` を含める。`STAGE_ABORT` は従来どおり正式な不採用記録とし、global control event の代用にはしない。

`records_by_stage()` は同一 stage の最後の record しか返さない [wal.py:586–601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/wal.py:586)。control report validator は `wal.read_records()` を順序付きで読み、event grammar、連番、予約前 query の不存在、counter の単調性を検査する。

現行 report 生成面 [p3_autonomous_workload_trial.py:651–758](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:651) は schema v2 とし、次を追加する。

```text
reflux.origin_id
reflux.manifest_sha256
reflux.policy_sha256
reflux.budget.{iteration_max,query_max,class_max,consumed}
reflux.campaign_preimage_sha256
reflux.control_wal.{path,bytes,sha256,event_count}
reflux.sealed
reflux.public_disclosure.{count,atom_id_or_none}
reflux.source_refs[]
```

自然文 failure reason、全 constraint mask、詳細 stop subtype は generator-safe report に複製しない。

### 7. 受容する残余と再開条件

受容する残余は以下である。

- planner/coder への failure-conditioned channel は 0 にできるが、外部 caller の二値 oracle は最大 2 bit 残る。
- timing、ファイル生成時刻、CPU 時間等の analog side channel は本予算で閉じない。
- `must-backoff` は構文上の保守化であり、実行時挙動の数学的単調性までは証明しない。各 candidate の verifier は省略できない。
- failure→constraint 変換は clean verifier red の singleton relaxation に限る。他の failure は理由を次候補へ運ばず seal する。
- 5-atom IR は trigger-gating/YCSB 限定であり、別 axis へ一般化しない。
- trusted control ledger を同一 UID の悪意ある caller から秘匿する保証は現行 in-process 構造にない。必要なら別 service/ACL が要る。
- generic WAL の最終 SHA は外部 anchor なしには全面改竄を防がない。
- raw human-supervised driver は残るが、正式 8c origin proof を発行できない境界とする。

不採用 A〜D の再開条件は次のとおり。

| 案 | 再開条件 |
|---|---|
| A: 現状維持 | multi-generation を恒久的に行わないと人間が裁定する場合の containment としてのみ。規律 3 の設計解としては再開不可 |
| B: class を planner のみへ | planner→coder チャネルを固定・非適応にし、role 間の非干渉と class 情報量未満の総 disclosure を機械証明できる場合 |
| C: 非重複 window 集合 | 軸 (iii) を導入し、候補 batch を結果取得前に immutable に凍結、duplicate/known-class も予算消費、結果は batch seal まで非公開にできる場合 |
| D: planner/coder 双方へ class | D39/D45 を supersede する新たな人間裁定と、class が gate 探索へ使えない形式的根拠が得られた場合。現状では再開不可 |

## B. 単調性と gate 探索耐性

### 単調性の厳密な定義

時点 `t` の constraint atom 集合を `C_t ⊆ U` とする。

```text
C_t ⊆ C_{t+1}
A(C_t) = {m ∈ {0,1}^5 | C_t ⊆ m}
A(C_{t+1}) ⊆ A(C_t)
```

すなわち、

- constraint は追加のみで、削除・弱化・expiry・success による解除をしない
- constraint に適合して verifier へ進める実効 mask の集合は広がらない
- iteration/query/disclosure counter は減らない
- run-root、trial、process 分割で `C_t` や counter を初期化しない
- mapping 不能時は constraint 無しで探索継続せず、origin を seal する

この単調性は constraint による安全受理集合についての主張である。provenance、environment、diff quarantine 等の別 gate はさらに候補を拒否できるが、constraint を上書きして受理を広げてはならない。

### 規律 2 に対して弱める部分

絶対規律 2 は、最適化圧力が correctness gate を攻撃する前提である [CLAUDE.md:65–69](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/CLAUDE.md:65)。

本設計は次を弱める。

- generator は failure class、whiteboard result、metrics、動的 constraint を読まない
- hidden constraint は raw proposal をより保守的な mask へ閉包するため、generator が理由を無視しても過去に失敗した relaxation を再実行できない
- failure class の自然文、表記揺れ、順序、padding を channel として使えない
- query は origin 全体で 2 回、応答は二値、別 run-root で回復しない
- class を公開するのは origin seal 後で、同 origin には後続 query がない

### 弱めない部分

- 外部 caller は自分が指定した singleton relaxation の accept/reject から、その atom に関する 1 bit を得られる。
- 2 query の範囲で二つの atom は試せる。
- timing、crash 位置、artifact size が観測可能なら追加推論が可能である。
- 人間が新 origin を正式発行すれば、新しい予算が生じる。
- shared-memory provider や同一 session の再利用があれば planner→coder の 3.17-bit channel が再び実情報を運びうる。
- 5 atom 全体を探索不能にした証明ではない。より強く閉じるなら軸 (iii) の事前 batch freeze が必要である。

したがって本案は gate 探索を**消去せず、generator 内では遮断し、外部 caller では二値 2 query へ上限化する**設計である。

## C. docs 編集面の地図

### 新規正本

| file:line | 変更 |
|---|---|
| `output/insights/2026-08-01_t244-reflux-design/README.md:1+` | 本回答の A/B、脅威モデル、bit 会計、origin/WAL schema、再開条件を設計本文 v1 として置く |
| [docs/decisions.md:5461+](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5460) | D116 を追加。「設計択一のみ確定。実装・多世代運転・効果実証は未了。D114 上限 1 は維持」を明記 |
| [docs/worklog.md:1700+](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/worklog.md:1699) | append-only の新 entry で設計 land と残余を記録。過去 entry は書き換えない |

### 「T-244 本体は未解決」とする現行箇所

| file:line | land 後の一行 |
|---|---|
| [docs/phase3.md:463–471](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3.md:463) | 「D116 で還流設計 v1 は確定した。機械配線・多世代運転・効果実証は未了であり、D114 の承認上限 1 を維持する」 |
| [docs/decisions.md D106:4854–4873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:4854) | 残余 1 に D116 supersede 注記を追加し、「設計択一は解消、実装残余へ移行」とする。同時に [4869](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:4869) の誤記 `D112` を `D114` に直す |
| [docs/decisions.md D114:5302](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5302) | 見出しは歴史を保ち「本決定時点で未解決、D116 が設計 v1 を supersede」と注記する |
| [docs/decisions.md D114:5307–5308](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5307) | 「D114 は解決しなかった。後続 D116 が設計のみ確定した」と時制を限定する |
| [docs/decisions.md D114:5363–5365](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/decisions.md:5363) | 保証限界を「設計は D116、実装と cross-generation 解禁は未了」へ更新する |
| [docs/phase3-s8c-autonomous-trial-runbook.md:98–114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:98) | 「設計裁定待ち」を「D116 実装・origin reservation・境界試験待ち」に置換し、最大 1 は変えない |
| [同 runbook:167–175](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-s8c-autonomous-trial-runbook.md:167) | 「T-244 本体未解決」を「設計 v1 確定、現行 supervisor 未実装」に置換する |
| [docs/worklog.md:595–680](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/worklog.md:595) | 歴史 entry なので変更しない。新しい末尾 entry から supersede する |
| [docs/worklog.md:1486–1491](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/worklog.md:1486) | in-place 変更せず、末尾で「設計 wave 完了、実装待ち」へ状態遷移を記録する |

追加の整合修正として、[docs/phase3-main-experiment.md:40–47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/docs/phase3-main-experiment.md:40) の「critic の機序帰属を coder/planner へ戻す on arm」には、8c では D116 が supersede し、hidden machine constraint を使うとの注記が必要である。旧 human-supervised preregistration の履歴は削除しない。

`docs/archive/**`、過去 worklog、前 wave の [裁定パッケージ](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/insights/2026-08-01_t244-generation-gate/README.md:35) は凍結した歴史なので書き換えない。`docs/failures.md` の T-244 出現は失敗型の再発記録であり、現在状態の主張ではないため変更不要である。

過大表現を避ける共通文言は次とする。

> D116 で還流設計 v1 の択一を確定した。constraint machinery、origin-global accounting、多世代運転、効果実証は未了であり、D114 の承認上限 1 を維持する。

## D. 実装しない判断の検証

親 brief (P1) の**結論は正しいが、理由は狭く言い直す必要がある**。

通常 8c 経路では同じ validator が三入口を拒否する。

- `_run_workload()` は config/layout/provider より前に検査する [p3_autonomous_workload_trial.py:761–783](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:761)
- `run_trial()` は run-root 作成より前に検査する [同:990–1025](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:990)
- CLI は checkout/build 準備より前に検査する [同:1090–1133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:1090)
- validator 自体は承認上限 1 を強制する [同:184–193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:184)

一方、「multi-iteration artifact が一つもない」という広い前提は誤りである。例えば [p3-s8a loop_state.json:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/loop_state.json:2) は iteration 2 を持つ。ただしこれは D114 の保証外である direct human-supervised loop の artifact で、二件とも `success`、trusted failure→constraint の発火証拠ではない。

静的調査では次の artifact / measurement ID は見つからなかった。

- 8c の正規 multi-generation report
- clean verifier red を持つ singleton gate relaxation
- その failure を 5-atom constraint へ写した machine proof
- origin-global reservation を発火させる既存 artifact

したがって `DW-G04` を満たすコード面はなく、**今すぐ実装すべき小さい面は提案しない**。X4 の whiteboard 値検査や WAL reservation は将来の必須前提だが、今回それを発火させる artifact path / measurement ID がないため、本 wave の実装候補にはしない。

将来、発火 artifact が得られた場合の配線地図は次になる。

| file:line | 将来の変更 |
|---|---|
| [axis_trigger_gating.py:41–64](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/axis_trigger_gating.py:41) | 固定 5-bit IR、atom ID、正準 emitter、非対象 reason=true 契約 |
| [p3_autonomous_workload_trial.py:158–163](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:158) | 動的文を持たない固定 gating spec v2 |
| [同:261–284](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:261) | 自由 C++ 文字列 parser を閉じた bitmask parser へ変更 |
| [同:426–455](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:426) | origin ID / policy SHA を search_config へ束縛 |
| [同:816–983](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:816) | recipient matrix、machine closure、critic report-only 化 |
| [同:990–1055](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_autonomous_workload_trial.py:990) | admission token と origin reservation |
| [p3_s4_loop_trigger_gating.py:384–430](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:384) | effective IR だけを build、source WAL ref を返す |
| [同:468–518](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop_trigger_gating.py:468) | direct driver の正式 8c 経路に one-use reservation token を要求 |
| [p3_s4_loop.py:356–404](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/p3_s4_loop.py:356) | 5 field のまま exact type/enum/iteration 整合を閉じる |
| [ident.py:76–103](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/ident.py:76) | 現行 campaign preimage は維持し、別 helper で origin preimage を定義 |
| [model.py:21–32](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/model.py:21) | `reflux-control` stage |
| [wal.py:283–378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/campaign/wal.py:283) | lock 保持中の count-check-reserve primitive |
| [test_p3_autonomous_workload_trial.py:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/tests/test_p3_autonomous_workload_trial.py:94) | origin 分割、第三 query、no-refund、padding、注入 seam、固定 recipient の境界試験 |
| [test_p3_s4_loop.py:260](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/tests/test_p3_s4_loop.py:260) | whiteboard 5 field 維持と値域閉包 |
| [test_p3_s4_loop_trigger_gating.py:1030](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t244-reflux-design/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1030) | reservation token、singleton mapping、raw/effective provenance |

本回答は read-only の静的読解結果であり、pytest、`check_docs.py`、ビルドは実行していない。試験結果についての主張はしない。

## 総括

**(a) 設計 v1 の骨子（5 行）**

1. trigger-gating を固定 5-bit IR に閉じ、failure は trusted machine だけが `must-backoff` constraint へ変換する。  
2. constraint mask は単調増加し、planner/coder には固定 schema だけを渡して理由・結果・metrics を渡さない。  
3. 一 origin は `Imax=2 / Qmax=2 / Kmax=1`、全失敗・padding・分割 invocation を無返却で数える。  
4. human-issued origin と原子的 control WAL で run-root / trial / programmatic 分割を同じ台帳へ束縛する。  
5. D116 は設計のみを確定し、実装・多世代運転・実証までは D114 上限 1 を維持する。  

**(b) 親 brief の誤っていた前提:** P3 の動的 `gating_spec` は理由チャネルになる。whiteboard は field 名だけ閉じ、値域は未閉包である。`search_config` への budget 追加だけでは別 campaign ID による reset を防げず、`records_by_stage()` は last-wins で control ledger に使えない。また direct multi-iteration artifact 自体は存在するが、選定設計を発火する failure artifact ではない。

**(c) 未解決の設計択一:** 実装前に、`I/Q=2・K=1` の保守的定数を正式採用するか、より多い iteration が必要なら軸 (iii) の batch freeze を先に併設するかを決める必要がある。あわせて origin authority を tracked registry で担うか、別 service/ACL へ分離するかは未決である。