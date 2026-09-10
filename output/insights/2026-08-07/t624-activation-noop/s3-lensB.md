判定は **NO-GO**。数値上の世代差分は検査できますが、裁定 D が問題にした contract 実体の rollback/no-op は保証できず、20 行のテストにも検出力の穴があります。

### [M1] 世代番号だけでは、裁定 D の rollback/no-op を塞げない

**主張:** `Mapping[str, int]` の差分だけを見ても、「番号が進んだ先が旧較正へ戻る」経路は残ります。「no-op を拒否する保証」とは呼べません。

**根拠:**

- 予定署名と全判定条件は contract hash/`GenerationEntry` を入力に持ちません。[s2-plan.md:60](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:60)、[s2-plan.md:102](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:102)
- 具体例: `g1=A（旧較正）`, `g2=B`, `g3=A` と再束縛された状態で、`{"pegasus": 2} → {"pegasus": 3}` は `True` です。contract は B から旧 A へ戻っています。
- `validate_generations` と合成すれば duplicate hash と不正 successor は拒否できますが、現プランは合成しません。[env_contract.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:302)、[env_contract.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:308)
- D176 自身が逆引き index は module 属性として再束縛可能で authority ではないと明記しています。[decisions.md:8691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:8691)
- 同じ generation の contract 差替えも見えません。例えば env-a の g1 を A→A′へ差し替え、env-b だけ `1→2` にすると、番号射影 `{"a":1,"b":1} → {"a":1,"b":2}` は `True` です。

**成果物影響:** 将来 consumer がこれを受理 gate にすると、`activation_serial` は進み、レポートと試行台帳は新しい `activation_state_sha256` を参照する一方、run の contract hash は旧較正へ戻り得ます。certified 選択が「新 state 下の run」と表示されても、実際の較正契約は旧値になります。

### [M2] `is_valid_successor` と新述語が独立したまま land する

**主張:** 片方だけ、または互いに無関係な入力へ両方を呼んでも「妥当な遷移」と結論できる public API ができます。

**根拠:**

- `is_valid_successor` は contract 対の calibration path/SHA だけを検査します。[env_contract.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:202)
- 新述語だけなら、`{"ghost": 10**100} → {"ghost": 10**100 + 1}` を受理します。未知 env、存在しない generation、不正 successor のすべてを見ません。
- `is_valid_successor` だけなら、record mapping の全 env 据置、skip、downgrade、env 集合変更を見ません。
- 両方を別々に呼んでも、数値 mapping と検査した contract 対が同じ `GenerationEntry` を指す保証がありません。
- プラン自身が registry 登録・generation 実在を保証しないと明記しています。[s2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:131)
- D196 が警戒したのも、部分実装を後続が活性化保証と誤読することです。[decisions.md:9510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:9510)

**成果物影響:** 将来 consumer が新述語だけを「valid activation transition」として使うと、受理集合に ghost env、不在 generation、不正 contract successor が入ります。レポートと台帳に同じ activation 参照が記録されても、certified run の contract をその参照から一意に再構成できません。

命名もこの穴を増幅します。現行の数値関係だけを表すなら、提案は **`has_nonempty_unit_generation_delta`** の 1 つです。`is_valid_activation_mapping_transition` は D197 の state 全体まで検証するように読めます。

### [S1] 入力は `GenerationEntry` が必要だが、actual record schema は scope 外

**主張:** 3 候補のうち、contract 遷移を判定する data-layer 入力としては `GenerationEntry` が最も不足が少ないです。contract hash だけでは `+1` を計算できず、int だけでは contract 実体を見られません。ただし record schema と authority まで本 wave に入れるのは scope 拡張です。

**根拠:**

- `GenerationEntry` は generation と exact contract を同時に保持します。[env_contract.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:163)
- D197 の activation state は「全 env の active contract 集合」に加えて serial と直前 hash を含みます。[decisions.md:9530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:9530)
- 現プランは serial、state hash、previous hash、generation 実在を明示的に検査対象外としています。[s2-plan.md:213](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:213)

**成果物影響:** int mapping を先に正本化すると、後の record が contract-hash mapping を採用した際、レポートの state projection と試行台帳の generation projection が別物になります。裁定候補は、単位 1 の文言だけを land し、単位 2 は hash-bound な record/entry 形が決まるまで保留することです。

### [M3] `Mapping` 入力の受理結果が安定していない

**主張:** 「key 集合比較 → 値検査 → delta 検査」という順序だけでは、任意の `Mapping` に対する純述語になりません。値 snapshot の有無と `keys()`/`__iter__` の選択が未指定です。

**根拠と具体値:** 実装順の記述は [s2-plan.md:77](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:77) のみで、以下の結果はこうなります。

- 通常の `before is after`、例えば同じ `{"env-a": 1}` を両引数へ渡す場合は、全 delta 0 なので `False`。これは狭い意味では正しいですが、表には alias fixture がありません。
- `d["env-a"] = d` という自己参照 dict は exact-int 検査で `False` になるはずです。
- 同一の custom Mapping が、before snapshot 時は `1`、after snapshot 時は `2` を返せば、`f(m, m)` でも `True` になり得ます。値を再読する実装なら、呼出し回数に応じた値で結果を任意にできます。
- `keys()` が `{"env-a"}`、`__iter__` が `"env-b"` を返す Mapping は、どちらを materialize するかで `True`、`False`、`KeyError` のいずれにもなり得ます。プランから結果を確定できません。
- `{"Env-A":1} → {"Env-A":2}` や `{"é":1} → {"é":2}` は exact-str なので `True` です。しかし実 contract の env_tag は lowercase ASCII slug に限定されています。[env_contract.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:33)、[env_contract.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:104)
- NFC `"é"` と NFD `"e\u0301"`、または大文字小文字が before/after で異なれば key 集合不一致で `False`。現行 slug domain では両者とも無効なので、これは過剰拒否ではありません。
- `IntEnum` は `int` 派生ですが `type(v) is int` ではないため `False`。既存 `GenerationEntry` も exact-int を要求するので、現行 schema 上は意図どおりです。[env_contract.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:170)
- 巨大な正整数には上限がなく、存在確認もないため `10**100 → 10**100+1` は `True` です。

canonical な登録済み env＋exact JSON int という本来の domain について、明確な過剰拒否例は見つかりません。問題は主に過剰受理と、generic `Mapping` を掲げながら結果が snapshot 方法に依存する点です。

**成果物影響:** issuer が custom/mutable Mapping を渡せると、同じ論理状態の replay で受理結果が変わります。発行時は受理された activation ref が、レポート再検証や試行台帳 replay では拒否され、proof chain が再現不能になります。

### [M4] 20 行を全部通る誤実装があり、DW-M03 の単一理由性も不足する

**主張:** 表は「各 env の delta」を検査したことを証明しません。

**根拠:** shape/type gate をそのまま置き、最後だけ次にする誤実装は 20 行すべての期待値と一致します。

```python
return 1 <= sum(after[k] - before[k] for k in keys) <= len(keys)
```

しかし `{"a":1,"b":2} → {"a":3,"b":1}`、delta `(+2,-1)` を `True` にします。skip と downgrade が相殺される fixture がありません。[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:145)

さらに `type(v) is int` を `isinstance(v, int)` へ変える変異は、現行 `False→True` fixture では殺せません。`False` が非正値なので positivity gate が別理由で拒否し続けます。`True→2` なら exact-int だけを撃てます。

| 行 | 契約上の役割 | DW-M03 判定 |
|---|---|---|
| all-env-no-op | ∃ delta=1 のみ違反 | 単独理由 |
| single-env-plus-one | 最小正例 | 正例 |
| mixed-stay-and-plus-one | 全 env +1 への過剰縮小を検出 | 正例 |
| multiple-env-plus-one | exactly-one への過剰縮小を検出 | 正例 |
| skip-plus-two | delta集合違反＋∃不成立 | 過剰決定 |
| mixed-plus-one-and-skip | delta集合だけ違反 | 単独理由 |
| downgrade | delta集合違反＋∃不成立 | 過剰決定 |
| mixed-plus-one-and-downgrade | delta集合だけ違反 | 単独理由 |
| env-added | key集合だけ違反 | 意味上は単独。削除変異後の挙動は走査方向依存 |
| env-removed | key集合だけ違反 | 同上 |
| empty-mappings | 非空＋∃不成立 | 過剰決定。非空 gate は ∃ に論理的に包含される |
| non-int-before | exact-int 違反 | 入力理由は単独だが、変異後は例外処理順に依存 |
| non-int-after | exact-int 違反。float delta は 1 | 単独理由 |
| non-str-key | exact-str のみ違反 | 単独理由 |
| zero-generation | positivity のみ違反 | 単独理由 |
| negative-generation | before と after がともに非正 | side 別には過剰決定 |
| mapping-proxy-plus-one | exact-dict 過剰拒否を検出 | 正例 |
| bool-is-not-int | exact-int 2 件＋`False` の positivity | 過剰決定。`isinstance` 変異を殺せない |
| before-not-mapping | Mapping gate | list は後段の集合不一致でも拒否され得るため、単独 kill 不成立 |
| after-not-mapping | Mapping gate | 同上 |

単独理由 fixture がない、または不十分なのは、明示的 nonempty、bool-vs-int、before/after の Mapping gate、side 別 positivity、単純 skip/downgrade 行です。

加えて 20 case を 1 本の `for` test にすると、最初の失敗後は後続行を観測できません。[s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:170) 変異帰属には各 case を独立 node にする必要があります。

**成果物影響:** aggregate-delta 誤実装や bool 漏れが変異台帳で生存したまま「検出力あり」と記録され、skip+downgrade を含む record が受理集合へ入ります。その record を参照する certified 選択・レポート・試行台帳は、単調な activation chain という主張を失います。

### [M5] 波及表の「direct source SHA pin 0 件」は反例がある

**主張:** AST 順序と public-surface の主張は静的に支持されますが、source SHA pin 0 件は誤りです。

**根拠:**

- module-level 順序検査は AST の `lineno` で `validation < index/registry` を比較しており、固定行番号ではありません。[test_env_contract.py:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:558) この点はプランどおりです。
- `env_contract.py` に `__all__` はなく、public symbol 完全集合の検査も見つかりません。`vars(ec)` の検査は生 dict の露出だけ、`hasattr` は `register` 2 名だけです。[test_env_contract.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:362)、[test_env_contract.py:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_env_contract.py:675) 新 public 関数だけで赤になる網羅 gate は静的には見つかりません。
- 一方、凍結済み silo artifact は `env_contract.py` の path と source SHA を直接固定しています。[silo_ladder_rung1.json:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67)
- evidence test はその歴史 binding と現行 runtime binding が異なることを明示的に要求します。[test_silo_ladder_rung1_evidence.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249)
- T419 の manifest/result にも role-key の `env_contract_sha256` が固定されています。[manifest.json:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/env/pegasus/t419-probe-causality/0_888740.nqsv/manifest.json:105)
- path hit だけで pin なしと結論してはいけないことは `DW-O09` 自身が禁じています。[operations.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/dev-wave/operations.md:46)

**成果物影響:** 歴史 artifact は更新してはいけません。新 commit では T-126 code identity と silo `runtime_modules_sha256` が変わり、旧 submit receipt の再 collect は source drift で拒否されます。波及表を「live runtime 再計算＋歴史 pin は保持」と訂正しないと、歴史 proof を現行 SHA へ貼り替える誤処理か、旧 receipt の受理可能性の過大報告につながります。

## 総括

**NO-GO**。数値 projection だけの public `is_valid_*` は裁定 D の contract rollback/no-op を保証しない。  
GO 条件は、同じ入力内で generation と contract hash/`GenerationEntry` を束縛し、successor 検査と合成すること。  
テストは `(+2,-1)`、alias、`True→2`、Mapping 境界を単独 fixture 化し、各 case を独立 node にすること。  
歴史 source pin を 0 件扱いせず分類すること。pytest は実行しておらず、以上は静的検査のみ。