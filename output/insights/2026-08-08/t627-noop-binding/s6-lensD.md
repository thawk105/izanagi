結論は **NO-GO** です。`git diff` の未コミット4ファイルと指定ファイルを静的に読解しました。ファイル変更、pytest、import、probe、buildは一切実行していません。

## Must-fix 所見

### 1. N8が過剰決定で、adapterの返り値破棄が生き残る

深刻度: **must-fix**

根拠: 段4は「解決可能な正当edgeに対して `ec.is_valid_successor` を `False` へmonkeypatch」するよう要求しています。[s4-adjudication.md:106](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s4-adjudication.md:106)  
実装されたN8は代わりに `clocks_per_us` を変更した不正contractを作っています。[test_env_contract_activation.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:764) 実装報告もこの逸脱を明記しています。[s5-impl.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s5-impl.md:26)

次の誤実装は `is_valid_successor` を呼ぶためspy nodeを満たし、返り値を捨てます。N8ではclock差から `False`、実productionのpegasus g1→g2ではclock同値から `True` となるため、実装済みnodeを静的には全通過します。

```python
def _is_valid_activation_successor(predecessor, successor):
    predecessor_entry = _resolve_activation_entry(predecessor)
    successor_entry = _resolve_activation_entry(successor)
    if (
        predecessor_entry is None
        or successor_entry is None
        or predecessor.env_tag != successor.env_tag
    ):
        return False

    is_valid_successor(
        predecessor_entry.contract,
        successor_entry.contract,
    )  # 誤り: 返り値を捨てる

    return (
        predecessor_entry.contract.clocks_per_us
        == successor_entry.contract.clocks_per_us
    )
```

成果物影響: clock以外を不正変更したregistered edgeがcurrentとして受理され、certified選択・レポート・台帳が正当でないcontract hashを参照します。

修正案: N8を段4どおり、現物の解決可能なpegasus g1→g2を使い、`ec.is_valid_successor` だけを `False` へmonkeypatchする `test_production_successor_adapter_propagates_false_for_resolved_valid_edge` に変更する。adapterのexact `False` と同adapterを渡したloaderの拒否を検査してください。

### 2. 2 env固定により、集約述語と「最初の2件だけ」が全通過する

深刻度: **must-fix**

根拠: N6は2 envだけの81組合せです。[test_env_contract_activation.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:582) N3/N4もchanged envは2件だけです。[test_env_contract_activation.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:649) 3行を持つN11は2-env catalogとの集合不一致でtransition前に拒否されます。[test_env_contract_activation.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:887)

次の集約条件は1～2 envではD228と等価ですが、3 envでは誤ります。

```python
deltas = [
    successor.generation - predecessor.generation
    for predecessor, successor in pairs
]
if max(deltas) != 1 or sum(deltas) not in {1, 2}:
    raise ActivationRecordError("activation generation 遷移が exactly +1 でない")
```

これは2 envの全行列を通過しますが、3 envの `(+1,+1,-1)` を受理し、`(+1,+1,+1)` を過剰拒否します。

また、current loopの反復対象だけを次に変える誤実装も全通過します。

```python
for predecessor, successor in changed[:2]:
    # 現行の例外・exact-bool・False処理をそのまま実行
```

成果物影響: 3 env以上のactivationで3件目のdowngrade／不正successorを受理するか、正当な全env同時+1を拒否し、certified current集合とレポート・台帳headが誤ります。

修正案:

- `test_transition_three_env_matrix_matches_d228_rule`：3 env × generation `{1,2,3}`、期待値は同じD228式。
- `test_transition_rejects_when_third_changed_env_successor_is_false`：先頭2件 `True`、3件目 `False`。
- 併せて3 env全同時+1の正例を明示する。

### 3. generation/hashの片座標だけで「変化」を判定するgateが全通過する

深刻度: **must-fix**

根拠: gateは `(generation, contract_sha256)` のpairを比較します。[env_contract_activation.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:272) しかしpublic test fixtureではregistry pair検査により両座標が常に同時に変わるため、次のどちらへ縮退しても全nodeを通過します。

```python
# generation-only variant
if predecessor.generation == successor.generation:
    continue

# contract-hash-only variant
if predecessor.contract_sha256 == successor.contract_sha256:
    continue
```

generation-only／hash-onlyのresolver自体はN9が殺しますが、transition内のchanged分類はN9の射程外です。現状はregistry pair gateにmaskされています。[env_contract_activation.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:381)

成果物影響: registry pair gateとの同時退行時、同generation別hashまたは別generation同hashがsuccessor検査を迂回し、certified current・レポート・台帳へ誤った参照が流れます。

修正案: private gateを直接呼ぶ独立nodeを追加する。

- `test_transition_gate_rejects_same_generation_hash_substitution_when_other_env_advances`
- `test_transition_gate_checks_generation_change_even_when_hash_is_reused`

いずれも別envに正当な+1を含め、全体no-op拒否で偶然赤にならないfixtureにしてください。

### 4. M2とM4の期待kill帰属がDW-M03を満たさない

深刻度: **must-fix**

根拠: M2は非減少を許す変異なので、現行の拒否条件に対する実コードは次です。

```python
if successor.generation < predecessor.generation:
    raise ActivationRecordError(...)
```

この変異では `(+2,-1)` の `+2` は通りますが、`-1` が残存gateで拒否されます。したがって段4が期待killに挙げる `test_transition_rejects_compensating_plus_two_minus_one` は緑のままです。[s4-adjudication.md:139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s4-adjudication.md:139) 正しいkill nodeは次の2件です。

- `test_transition_rejects_skip_even_when_successor_predicate_accepts`
- `test_transition_matrix_matches_d228_rule`

またM4で `changed[:1]` に縮退した場合、N3は不正edgeを受理して赤になりますが、N4はall-True recordを変異前後とも受理し、call-countだけで赤になります。[test_env_contract_activation.py:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:667) DW-M03上、N4はkillではなく観測pinです。[mutation.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/dev-wave/mutation.md:16)

成果物影響: mutationレポートと台帳が、maskされたfixtureや受理集合不変の赤をkillとして記録し、実在しない検出力を根拠にgateを承認します。

修正案: M2から `compensating_plus_two_minus_one` を外し、M4のsemantic killをN3だけにする。N4はdiagnostic/structural sensitivity pinとして別枠に記録する。

## 指定された誤実装の攻撃結果

以下は実走結果ではなく、制御フロー上の静的判定です。

```python
# generation-only resolver: N9のwrong-hash subcaseが殺す
def resolve_generation_only(row):
    try:
        return GENERATIONS[row.env_tag][row.generation - 1]
    except (KeyError, IndexError, TypeError):
        return None


# contract-hash-only resolver: N9のgeneration/env mismatchが殺す
def resolve_hash_only(row):
    for sequence in GENERATIONS.values():
        for entry in sequence:
            if entry.contract.contract_sha256 == row.contract_sha256:
                return entry
    return None


# 前段の集約実装: N5/N6が殺す
if max(deltas) != 1 or sum(deltas) < 0:
    raise ActivationRecordError(...)


# 最初の1件だけ: N3が受理集合差で、N4がcall-countで赤
for predecessor, successor in changed[:1]:
    ...


# literalな返り値破棄: 現N8が殺すが、must-fix 1の変種は生存
is_valid_successor(old_contract, new_contract)
return True


# catalog ordinal: N7が殺す
positions = {
    env_tag: {
        generation: ordinal
        for ordinal, (generation, _hash) in enumerate(sequence)
    }
    for env_tag, sequence in registered_contracts.items()
}
if positions[env][successor.generation] != positions[env][predecessor.generation] + 1:
    raise ActivationRecordError(...)


# 指定された過剰拒否: N2が殺す
if predecessor.generation != 1:
    raise ActivationRecordError(...)
```

catalog ordinal、指定の `predecessor.generation != 1`、最初の1件だけ、既知の `max/sum` 集約は所期nodeで検出されます。一方、adapterの部分的再判定、3-env集約、最初の2件、pairの片座標分類が生存します。

## M1〜M10の帰属監査

| 変異 | 置換実在・期待kill・mask判定 |
|---|---|
| M1 | `if not changed:` は一意。N1、all-noop、issuer-noopはいずれも受理集合差で赤。registry/head/ever-activeのmaskなし。 |
| M2 | 数値条件は一意。skip単独とN6は正しい。`(+2,-1)` はdowngradeにmaskされるため期待killが誤り。 |
| M3 | M2と同じ一意行を別走行で除去。downgrade、N5、N6はいずれも赤。登録pairとheadは整合し、maskなし。 |
| M4 | loopは一意だが、実置換は `changed[:1]` 等で書く必要がある。N3はsemantic kill、N4はcall-count pin。 |
| M5 | adapterのreturn siteは一意。literal `return True` はN8で赤。ただしN8 fixtureが過剰決定で、別の返り値破棄が生存する。 |
| M6 | `_resolve_activation_entry` 内の完全な `or ...contract_sha256...` 行でanchorすれば一意。比較断片だけならpost-load再照合にも出現する。[env_contract.py:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:411) [env_contract.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:538) N9のwrong-hash subcaseはdirect adapterなので単一理由。 |
| M7 | annotationはprivate gate・validator・loaderの3箇所にある。[env_contract_activation.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:262) 単一置換ではなく、各signatureとNone fallbackを一意anchorへ分解する必要がある。N10自体は正しい。 |
| M8 | exact-bool条件は一意。non-bool `1` の受理集合が変わるため期待nodeは正しい。False用診断を維持する変異にする必要がある。 |
| M9 | 数値条件は一意だがprivate gateにcatalog引数がなく、catalog ordinal変異は単一siteでは実装不能。[env_contract_activation.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:257) multi-site変異として事前登録し直せばN7は正しく殺す。 |
| M10 | `changed.append(...)` を挿入anchorにすれば一意。[env_contract_activation.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:289) N2はg2→g3で受理集合が縮小して赤。maskなし。 |

遷移負例ではenv集合とregistry pairがexactで、期待headはfixtureのtailに合わせられています。transitionを弱めてもhead serial/state hashは通り、`ever_active` はcurrent hash包含しか要求しないため、M1〜M5・M8〜M10を救済しません。[env_contract_activation.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:375) [env_contract_activation.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:403)

## Should-fix 所見

### 5. M6/M7/M9は実行用anchorへ落とし込まれていない

深刻度: **should-fix**

根拠: DW-M04は置換ごとの一意性assertを要求します。[mutation.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/dev-wave/mutation.md:22) M6は比較断片が2箇所、M7は複数signatureとfallback、M9はcatalogをprivate gateへ運ぶmulti-site変異です。

成果物影響: mutation harnessが注入なしで停止するか別層まで変更し、mutationレポートと台帳のM6/M7/M9参照が不成立になります。

修正案: M6は先頭の `or` を含む完全行、M7/M9は各累積置換を別anchorとしてspec化し、各置換直前にcount=1をassertする。

### 6. 診断・観測だけの赤をkillから分離する必要がある

深刻度: **should-fix**

根拠:

- N11のmissing-env subcaseでouter exact集合検査を除去しても、private transitionが「env対応不一致」で拒否しcallbackは0回です。`match="env 集合"` だけが赤になるため、このsubcaseは診断pinです。[test_env_contract_activation.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:887)
- M8を単純に `if not result:` へ一行置換すると、exact `False` は引き続き拒否されるのに診断が変わり、次が副次的に赤くなり得ます。これらはM8 killに合算できません。
  - `test_transition_rejects_plus_one_when_bound_contract_successor_is_false`
  - `test_transition_rejects_when_second_changed_env_successor_is_false`
  - `test_production_successor_adapter_returns_false_when_is_valid_successor_is_false`
- N4と `test_successor_predicate_receives_exact_generation_hash_rows` は受理集合不変の観測pinです。

成果物影響: mutationレポートのkill件数と台帳参照が、受理集合ではなく診断文・call traceの変化で水増しされます。

修正案: N11のmissing/extraを別nodeにし、missing側はdiagnostic pin、extra側は `KeyError` 漏出を防ぐfail-closed nodeとして扱う。M8変異はexact `False` の既存診断を維持し、観測nodeはkill集計外へ分離する。

## N6・正例・期待値の健全性

N6の期待値はD228本文の `all(delta in {0,1}) and any(delta == 1)` をtest内で直接計算しており、production実装やhelper predicateをoracleにしていません。[decisions.md:10665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/decisions.md:10665) `_chain` は登録済みrowとheadを構築するだけなので循環参照ではありません。callableをexact `True` に固定したことでsuccessor層も非阻害です。

ただし網羅性は「2 env、generation 1〜3」に限定され、3 env以上の集約／量化変異を証明しません。これはmust-fix 2の穴です。

要求された正例はすべて存在します。

- 一部据置＋1 env前進: [test_env_contract_activation.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:509)
- 複数env同時+1: [test_env_contract_activation.py:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:519)
- g1→g2→g3: [test_env_contract_activation.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:543)
- serial 1単独: [test_env_contract_activation.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:329)
- [T-657]形のlinux-baremetal据置＋pegasus g1→g2: [test_env_contract_activation.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:925) およびissuer正例 [test_env_contract_activation.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:1417)

working-tree commit hashやdirty hashを期待値へ焼き込んだ箇所はありません。`_chain` が生成record自身のstate hashをexpected headへ渡すのはtransition帰属をhead gateから隔離するためであり、揮発するworking-tree期待値ではありません。固定された `INITIAL_STATE_SHA256`／`INITIAL_BYTES` はchecked-in初期authorityのgoldenです。

## 総括

**判定: NO-GO**

**must-fix: 4件**  
should-fix: 2件

adapter返り値破棄、3 env以上の集約・量化縮退、generation/hash片座標gateが実装済みnodeを通過します。またM2/M4のmutation帰属にはmask／受理集合不変の誤計上があります。pytest等は実走しておらず、本判定は `git diff`・ソース・テスト・裁定文の静的読解だけに基づきます。