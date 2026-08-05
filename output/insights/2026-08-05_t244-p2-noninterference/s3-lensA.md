判定は **NO-GO** です。段2案は schema allowlist と字面 tripwire であり、D121 が要求する情報量ベースの非干渉を検査していません。pytest は実行せず、静的確認と32候補の軽量列挙だけを行いました。

## BLOCKER

### B1. 現行 `variant` が実際に 5-bit wire を運ぶのに、32件すべて検査を通る

D121 は「32状態の SHA は総当たり可能」と明記しています。[README.md:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:243) [README.md:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:262)

現行コードでは、wire から正準 predicate が一意に生成され、固定 genome とともに 12-hex ID へ入ります。[reflux_ir.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:99) [reflux_ir.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:117) [p3_s4_loop.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:237) [p3_s4_loop_trigger_gating.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:533)。その ID は critic payload に無加工で入ります。[p3_autonomous_workload_trial.py:1649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1649)

静的列挙結果は次のとおりです。

- 32 wire → 32個すべて異なる `diffq-*` ID。
- ID 内に自分自身の5文字 wire が出現するものは0件。
- `wire="10100"` は `variant="diffq-9088c66480b5"`。

したがって、以下を有効な common fields に足した payload は段2検査を通ります。

```json
{
  "harness_result": {
    "outcome": "rejected",
    "variant": "diffq-9088c66480b5",
    "verdict": null,
    "metrics": {
      "throughput_ops_sec": null,
      "abort_rate": null,
      "latency_ns": null,
      "llc_miss_rate": null,
      "ipc": null
    },
    "stop_reason": "continue"
  },
  "critic_digest": "variant=diffq-9088c66480b5"
}
```

禁止文字列は一つも含みませんが、32件の表引きで `10100` に一意復号できます。段2の「baseline は赤にならない」[plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:17) は安全の証拠ではなく、**全候補を見逃す実測**です。

正しい一般化は「常に5 bit」ではなく、

```text
I(W; ID | 公開 codebook) ≤ H(W) ≤ 5 bit
```

です。現在の diffq 経路は写像が単射なので、uniform な wire なら5 bit全部を漏らします。一方、`variant=None`、非一様分布、衝突では5 bit未満です。build 経路の単射性は別途固定 origin ごとに確認が必要です。

`genome.canonical()` や `src_token` を critic が知らないという反論も成立しません。genome は世代内で固定され、rejection digest 自身が genome と src_token を描画します。[p3_s4_loop_trigger_gating.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:533) [digest.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:583) [digest.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:642)。また非干渉保証を、公開コードの codebook を adversary が事前計算していないことには依存させられません。

### B2. P1 の auditor 例外は D121 の recipient matrix に反する

親 brief は auditor に `working_diff` と `diff_digest` の双方を許可しています。[brief.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:38)。段2も両 path を明示的に除外します。[plan.md:62](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:62) [plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:67)

しかし D121 §4① は auditor に許すのを「raw IR から生成した diff のみ」とし、実効 mask・両 SHA を禁止しています。[README.md:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:243)。現行 payload は実際に両方を渡しています。[p3_autonomous_workload_trial.py:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1557)

「diff を見せる以上 digest は冗長」は、recipient matrix を変更する根拠になりません。正しい declassification は次です。

- auditor は raw wire の正準 emitter から独立再生成した raw diff を観測してよい。
- その raw diff 自体が最大5 bitを運ぶことは、意図した開示として会計する。
- diff SHA、実効 diff、実効 mask、禁止集合依存値は渡さない。

さらに CandidateMaterial は同じ `preview_result` から diff と SHA を取り、その値との一致を根拠に例外化します。[plan.md:76](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:76)。将来 producer が実効値へ変われば、検査の「正解」も同時に変わり、実効 diff をそのまま安全認定します。これは独立検査ではなく自己参照です。

payload 変更が必要なら実装せず裁定へ返す、という brief 自身の不変条件が発火しています。[brief.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:28)

### B3. allowlist が D121 の許可入力ではなく「現行 field の写し」になっている

D121 の設計後 matrix は、

- planner から性能・LI・whiteboardを外す
- coder から baseline・whiteboardを外す
- critic は未裁定

としています。[README.md:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:241)

一方、段2 allowlist は現行の `leading_indicators`、`baseline`、`whiteboard`、`critic_digest` をそのまま承認しています。[plan.md:58](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:58)

critic の recipient policy が未裁定なのに、安全な critic allowlist は定義できません。また P3 の「role 許可入力だけの関数」[brief.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:46) で、「許可入力」を現行 key 集合そのものと定義すると循環します。秘密を許可 key の値へ符号化した瞬間、その値まで「許可入力」になってしまいます。

### B4. schema closure は値の情報依存を制約せず、許可面に十分な容量が残る

段2自身が semantic copy、数値、長さ、順序、許可 field 内の別コードを捕捉不能と認めています。[plan.md:89](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:89)。その時点で非干渉検査ではありません。

| 面 | 検査後に残る符号化容量 |
|---|---:|
| `whiteboard` | 現行 cap=1・fresh state では0 bit。ただし多世代化後、値域を3×3×3へ閉じても1 entryあたり `log2(27)≈4.755 bit`。iteration不整合や自由文字列を許せば無界 |
| `descriptor_binding` | 64-hex SHAが3本なので、値を独立再計算しなければ768 bit |
| `harness_result` | `variant` だけで wire 最大5 bit。5個の有限 float/None は物理的に約320 bit |
| `critic_digest` | 長さ上限のない文字列なので無界。32種類の1文字、または長さ1〜32だけで5 bit |
| `leading_indicators` | 2個の有限 float/None で約128 bit。label を exact pin しなければ文字列分は無界 |

根拠となる現行生成点は、descriptor digest [s8b_descriptor.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/s8b_descriptor.py:194)、metrics [p3_autonomous_workload_trial.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:692)、whiteboard [p3_s4_loop.py:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:295) です。

例えば `k=effective_mask∈[0,31]` として、以下はいずれも禁止字面を含まず通過します。

- nested hash: `descriptor_binding.output_sha256 = sha256(bytes([k]))`
- float 下位 bit: `IPC_overall = 1.0 + k * 2^-52`
- 文字列長: `critic_digest = "A" * (k + 1)`
- None pattern: 5 metrics の `None/value` 組合せで5 bit
- list 順序: `n` 要素の順列で `log2(n!)` bit
- payload 外: invocation の有無、停止位置、時刻、artifact size

現行では cap=1 のため whiteboard と前世代 LI が実質 dormant です。これを現在値だけで検査すると、多世代開放時に初めて開くチャネルを検証できず、まさに恒真化します。

## MAJOR

### M1. payload 外の P2 観測面は開いたまま

D121 は D51 provenance、driver 戻り値、artifact path、report、時刻等も観測面に含めています。[README.md:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:263) [README.md:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:424)

現行 D51 provenance は proposal path、auditor digest、outcome、variant を保存します。[p3_s4_loop_trigger_gating.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)。trial report は harness outcome 全体を保持して返します。[p3_autonomous_workload_trial.py:1643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1643) [p3_autonomous_workload_trial.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1283)

名乗りの上限は次です。

> 8c `_invoke` 入力の schema allowlist と、4種の禁止文字列に対する lexical tripwire（auditor raw-diff declassification あり）

「payload 射影面を閉じた」「P2 の部分実装」は過大です。P2 predicate と cap-lift 判定は引き続き false 固定でなければなりません。

### M2. `IR_SCHEMA_ID_SHA256` は IR schema/emitter SHA ではない

現行にあるのは文字列 `SCHEMA_ID` だけです。[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:19)。wire 幅・bit順・enum対応・emitter は別コードにあります。[reflux_ir.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:22) [reflux_ir.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:117)

段2もこの誤称を認識しています。[plan.md:139](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:139)。`SCHEMA_ID` を据え置いたまま emitter や bit 対応を変える mutant は検査を通ります。canonical schema bytes、emitter bytes、32 golden のどれを identity とするか裁定し、独立 pin するまで「IR SHA 検査」と数えてはいけません。

### M3. 事前登録 mutant がすべて直接コピー型に偏っている

M8〜M12 は wire、diff、SHA の逐語コピーだけです。[plan.md:188](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:188)。最低でも次を赤にする mutant が必要です。

- 現行 `diffq_variant_id` codebook
- `sha256(wire)` / base64
- float mantissa
- string length
- None pattern
- whiteboard/list ordering
- C を変えても同じ公開入力なら serialized observation が同一、という relational mutant

ただし mutant 追加だけでは字面 checker を非干渉 checker に昇格できません。先に secret/public/declassification を型として分離する必要があります。

## MINOR

### N1. P4 の命名分離は有用だが、安全性の根拠ではない

入力 digest と verdict echo の内部名分離 [plan.md:116](/work/1/SFC/tanab/dev-wave-jobs/t244-p2-noninterference/stage2/plan.md:116) は保守性には有効です。ただし wire 上と provenance 上では依然 `diff_digest` が観測されるため、情報量は1 bitも減りません。P4 は反証対象というより、非干渉とは独立した hygiene です。

### N2. dict key 順序は現行 headless sink ではチャネルにならない

provider 直前の canonical JSON は `sort_keys=True` なので、dict key 順序は現行経路では0 bitです。[s8b_prediction_runner.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/s8b_prediction_runner.py:214) [claude_projected_provider.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:253)。一方、list 順序、nullable 値、時刻は残ります。将来 provider が変わってもこの正規化が sink 契約として維持されることを pin すべきです。

## 実装前の必須是正

1. critic policy と auditor raw-diff declassification を裁定し、`diff_digest` 例外を撤回する。
2. secret `S` と公開入力 `P` を定義し、許可した開示以外は `Obs(role,P,S1) == Obs(role,P,S2)` を serialized sink bytes で検査する。
3. payload projector の入力型から `C`・実効 mask・実効 diffを排除し、同じ producer が作る CandidateMaterialを正解扱いしない。
4. provenance・戻り値・artifact・report・invocation有無まで観測面を閉じるまでは P2 を未充足のまま維持する。

## 総括

**NO-GO**。
BLOCKER は **4件**。
段2案は lexical tripwire であり、非干渉検査ではない。
P2 充足・多世代 cap-lift の根拠として land してはならない。