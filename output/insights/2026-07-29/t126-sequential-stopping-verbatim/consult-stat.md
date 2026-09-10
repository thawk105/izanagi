判定は「plan をそのまま採用不可」です。SPRT 核と P2 延期判断は妥当ですが、production source 適格性、qualification lock、環境 enforcement、時間・順序テスト、mutation 帰属に blocker があります。

pytest・性能計測・編集は実施していません。worktree は clean のままです。

## Findings

### 1. source pair の headline 適格性を admission が落としている

- 判定: real
- Severity: blocker
- 型: [テスト代表性] [手順漏れ]

plan は near-floor・stable・低 abort・legacy+S2 だけで source を production admission し、再現・multi-boot なら promotable にします。[plan:78](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:78) [plan:185](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:185)

しかしこの source campaign は正本上、

- preliminary・断定 verdict なし
- 8a 由来なので headline 非対象
- 単一 campaign 値は候補提示だけ

です。[source report:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_report_p3-s8a-trigger-sweep.md:3) [source report:4](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_report_p3-s8a-trigger-sweep.md:4) D47 も 8a 軸を headline 集合から明示除外しています。[D47:1685](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/decisions.md:1685)

成果物影響:

- headline: この pair は SPRT が reproduced でも headline 不可。
- レポート: `promotion.json` は最低でも `source_headline_eligible=false` と正本参照を出すか、この source を fixture 専用に限定する必要がある。
- 台帳: source の experiment class / headline eligibility を identity に束縛しない限り、ledger 完整性だけで不適格 source が適格化する。

一般化した source-eligibility gate の追加は受理集合を増やすため、行うなら「裁定パッケージ候補」です。

### 2. 親の +3.417% / near_floor 数値自体への反証

- 判定: refuted
- Severity: none

WAL の 930,077 と 961,862 は実在し、両方とも reps=5・legacy+S2 COMMIT です。[variant:23](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:23) [baseline:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/runs/wal.jsonl:35)

静的再計算結果も `rel=0.0341745898`, `p=0.0121857804`, `near_floor=True` でした。したがって数値は正しいです。

ただし同じ9 committed点の36 unordered pair中、near-floor pair は3組あり、選択 pair は一意の事前登録比較ではありません。数値が証明するのは historical loader/admission seam の実在までで、再現性・boot independence・qualification・headline 適格性ではありません。

成果物影響:

- headline: 数値だけでは変更不可。
- レポート: historical input として引用可能だが「production-positive control」とは書けない。
- 台帳: BENCH_DONE/COMMIT refs は利用可能。source boot provenance は存在しない。

### 3. 実測 positive control 不在なのに activation hold が構造化されていない

- 判定: real
- Severity: blocker
- 型: [恒真ゲート] [手順漏れ]

設計 §8 は「既知の非再現 pair」での実走を要求します。[design:196](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:196) 一方、その floor 内 pair は通常の near-floor admission を通らず、既知 near-floor 非再現 pair も無い、という plan の診断は正しいです。[plan:217](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:217)

問題は、prose では `implemented-but-unqualified` とする一方、promotion predicate に qualification 状態や activation receipt がありません。[plan:7](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:7) [plan:182](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:182) コードを land した直後から、CLI を呼べば predicate 上は promotion 可能です。

成果物影響:

- headline: positive control 完了までは機械的に activation を拒否すべき。
- レポート: `implemented-but-unqualified` / positive-control 未実施を明示し、promotable を生成しない。
- 台帳: qualification receipt が無いなら production series を開始しない、または全 series を non-promotable namespace に隔離する必要がある。

「floor 内 pair を通す qualification-only series」は現 brief 外なので、明確に「裁定パッケージ候補」です。tracked pair を結果未知のまま初回 opt-in に回し、事後的に positive control と呼ぶのは不可です。

### 4. Pegasus での P2 不実施は正しいが、plan の wrong-env gate は未配線

- 判定: real
- Severity: blocker for live qualification / high for code plan
- 型: [恒真ゲート] [計測汚染] [手順漏れ]

read-only 実測では `hostname=pegasus02`、`PBS_JOBID/PBS_NODEFILE` は未設定です。runbook は login node で重い性能計測を禁止し、qlogin/qsub の計算ノードだけを許可します。[runbook:252](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/pegasus-runbook.md:252)

さらに Pegasus は `allow_resume=False` です。[env_contract:180](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/env_contract.py:180) plan は1起動1 roundなので、round 2以降は別 process resume となり Pegasus 契約と両立しません。[plan:81](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:81)

加えて、再利用予定の S8a `_eval_one` は `ENV_TAG="linux-baremetal"`、CLK/NUMA も固定です。[s8a:84](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/s8a_trigger_sweep.py:84) `env_contract` 自身は enforcement を行わず、driver 側責務です。[env_contract:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/env_contract.py:6) 現 plan の「wrong env は indeterminate」は、実機を識別する経路が示されていません。Pegasus 上で S8a 定数をそのまま使えば、誤って `linux-baremetal` と記録して自己整合してしまいます。

成果物影響:

- headline: 本 wave の live qualification / production activation は不可。
- レポート: code landing 時は環境未検収と Pegasus 非対応を明示。
- 台帳: contract hash・hostname の記録だけでは enforcement にならない。wrong host は series directory 作成前に拒否する必要がある。

Pegasus 対応の常駐 single-process driver は別設計になるため「裁定パッケージ候補」です。本 wave は plan どおり linux-baremetal 待ちが妥当です。

### 5. 「multi-boot だけ promotable は過剰 gate」という攻撃

- 判定: refuted
- Severity: none

設計は同一 boot 内で完結した系列を `same-boot` とし、α/β の名目値を主張しないと規定します。[design:87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:87) headline gate も same-boot を拒否します。[design:109](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:109)

各 observed round に非空 boot-id を必須化する前提なら、

`same-boot でない` ⇔ `distinct observed boot-id >= 2`

なので plan の predicate は同値で、受理集合変更ではありません。

成果物影響:

- headline: multi-boot 条件は維持してよい。
- レポート: ただし表現は「multi-boot」であり、「boot-independent」とは書かない。
- 台帳: 全 round の boot-id と distinct count を保持し、欠損は拒否する。

### 6. multi-boot・30分・無作為化は independence の証明ではなく、しかも挙動テストが欠落

- 判定: real
- Severity: high
- 型: [計測汚染] [テスト代表性] [手順漏れ]

設計が要求する三点は、roundごとの順序無作為化、round間時間分離、boot記録です。[design:87](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:87) それでも残存相関は消えないと明記されています。[design:239](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:239)

plan は1,800秒と order seed を置きましたが、

- 「前 round の COMMIT」が二候補のどちらか未規定。後に完了した COMMIT の最大時刻でなければ30分未満になり得る。
- 「決定論的な順序」とだけ書かれ、seed→各 round permutation の exact algorithm が無い。
- 提案テスト・mutation 一覧に interval enforcement と order randomization の変異が無い。[plan tests:236](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:236) [plan mutations:255](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:255)

成果物影響:

- headline: interval/order gate が無検出で消えると名目 SPRT を使えない。
- レポート: order algorithm/version、各順序、実間隔、interval compliance、残存相関の限定を出す必要がある。
- 台帳: `max(COMMIT_ts)`、次 round start、exact permutation を再計算可能に記録する。

最低限、1799.999/1800.000境界、二候補の遅いCOMMIT選択、早期起動が完全無書込、固定順序 mutation、seed/order vector の独立 oracle が必要です。

### 7. SPRT 核は合っているが、境界 mutation は等価で kill 不可能

- 判定: real
- Severity: high
- 型: [恒真ゲート] [テスト代表性]

strict `LLR > ln9` / `< -ln9` と Rmax=8 indeterminate は設計一致です。[design:64](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/output/insights/2026-07-15_sequential-stopping-design.md:64) ただし plan の `>`→`>=`、`<`→`<=` mutation は無効です。[plan:257](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:257)

n round 後の likelihood ratio は `(9/5)^s(1/5)^f` です。有限整数 s,f では 9 または1/9に等しくならないため、256系列すべてで strict/inclusive の停止点・判定が同じでした。これは F28 の等価 mutation 型です。[F28:371](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/failures.md:371)

独立の有理数列挙による exact OC は次です。

| 真の p | reproduced | not-reproduced | indeterminate | E[N] |
|---:|---:|---:|---:|---:|
| 0.5 | 7.812500% | 78.906250% | 13.281250% | 4.4140625 |
| 0.7 | 33.892516% | 39.182670% | 26.924814% | 5.5495663 |
| 0.9 | 84.741876% | 4.275010% | 10.983114% | 5.2008869 |

成果物影響:

- headline: truncated OC と independence 条件を伴わない α/β 表現は禁止。
- レポート: この exact 表を設計 insight へ追記してから初回運用するという §8 条件を履行する。
- 台帳: policy・停止 prefix・LLR は WAL から独立再計算可能にする。

全系列テストは production helper と同じ式から期待値を生成せず、literal OC/count と独立 `Fraction` oracle を使う必要があります。境界 mutation は受理集合を実際に変える threshold/increment mutation へ差し替えるべきです。

### 8. 「driver が consumer を呼ぶので未配線ではない」はまだ証明されていない

- 判定: real
- Severity: high for production activation
- 型: [恒真ゲート] [手順漏れ]

現行 Layer 3 は campaign の材料射影だけで、比較・promotion field を持ちません。[layer3_report:369](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_report.py:369) schema も閉じています。[schema:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/campaign/layer3_schema.json:5)

plan はこれを変更せず sidecar `promotion.json` を作り、measurement driver が呼ぶことだけで「未配線ではない」としています。[plan:171](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:171) [plan:191](/home/SFC/tanab/github/izanagi/.codex/dev-wave-t126-jobs/plan/output.md:191) これは T-126 専用 promotion artifact の生成経路にはなりますが、どの headline renderer がそれを唯一の authority として必須消費するかが未規定です。

既存テストが保証するのも near-floor flag と警告文字列までです。[test_stability:189](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_stability.py:189) [test_campaign:2800](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/orchestrator/tests/test_campaign.py:2800)

成果物影響:

- headline: `promotion.json` を読まない別 renderer が存在しないこと、または T-126 headline authority がこの artifact だけであることを明文化・E2E固定するまで activation 不可。
- レポート: rejected status のとき headline field自体が生成されない負例が必要。
- 台帳: ledger 完整性だけでは consumer closure の証拠にならない。

なお親 brief の「現時点で単発値が自動 headline 昇格し得る」という表現は過大です。現 source report は明示的に headline 非対象で、現 Layer 3 に promotion 判定自体がありません。実在する穴は「将来の promotion authority が未実装」であり、「現在の自動昇格成功経路」ではありません。

## 本 wave で名乗れる範囲

| 状態 | 裁定 |
|---|---|
| code landing | 条件付き可。`implemented-but-unqualified` のみ。独立OC oracle、実効 mutation、interval/order/env/source eligibility の負例、consumer authority を備え、親が実際に検査した後に限る |
| T-126 完了 | 不可。設計 §8 の実測 positive control と insight の exact OC 追記が未了 |
| production-ready | 不可 |
| production activation | 不可。qualification、headline-eligible source、resume可能な実測環境、consumer closure が不足 |
| Pegasus 対応 | 本 wave scope 外。現1-round-per-process設計は `allow_resume=false` と不整合 |

Pegasus login node では pytest 自体は runbook 上可能ですが、g++-13依存群は検出力を得ず skip され得ます。[runbook:260](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t126-sequential-stopping/docs/pegasus-runbook.md:260) 後続の親実走は rc=0だけでなく node数・skip理由を記録すべきであり、本レビューの非実走を green に数えてはいけません。

## 総括

SPRT の式、Rmax=8、same-boot拒否、P2を実測なしで閉じない二段階判断は生存しました。一方、現 plan は headline 非適格な8a sourceを promotion可能にし、qualification holdをコードで強制せず、wrong-env・30分・順序無作為化の実効テストも欠き、等価 mutation を KILL 対象にしています。

したがって段4へ返す裁定は、コード landingのみ `implemented-but-unqualified` で条件付き可、T-126完了・production activation は不可、です。