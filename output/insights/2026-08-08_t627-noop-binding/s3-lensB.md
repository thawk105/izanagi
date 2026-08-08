静的レビューの結論は **NO-GO** です。required callable＋production adapter という設計方向は親 brief の P2 より強いものの、提案テストを全通過する誤実装を複数構成できます。

ファイル変更、pytest、import、probe、build は一切実行していません。以下は `sed` / `rg` による静的読解と制御フロー追跡だけに基づきます。

## Must-fix 所見

### 1. successor 判定が「全変更 env」に量化されていない実装を殺せない

深刻度: **must-fix**

根拠: 意図は変更した各 env に callback を適用することです。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:24) 一方、false/spy node はいずれも変更 env が 1 個だけで、複数同時 +1 node は受理だけを見ます。[s2-plan.md:298](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:298) [s2-plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:305)

次の generation 主体・「1 edge が通ればよい」実装は全提案 node を通ります。`None` fallback も全テストが明示的に predicate を渡すため検出されません。

```python
def _wrong_generation_dominant(
    predecessor_rows,
    successor_rows,
    *,
    activation_serial,
    is_valid_registered_successor=None,
):
    predecessor_by_env = {row.env_tag: row for row in predecessor_rows}
    changed = []

    for successor in successor_rows:
        predecessor = predecessor_by_env[successor.env_tag]
        if (
            predecessor.generation,
            predecessor.contract_sha256,
        ) == (
            successor.generation,
            successor.contract_sha256,
        ):
            continue
        if successor.generation != predecessor.generation + 1:
            raise ActivationRecordError(
                "activation generation 遷移が exactly +1 でない: "
                f"serial={activation_serial} env_tag={successor.env_tag}"
            )
        changed.append((predecessor, successor))

    if not changed:
        raise ActivationRecordError(
            f"activation transition が全 env 据置の no-op: serial={activation_serial}"
        )

    # 誤り: predicate が無ければ generation だけで受理し、
    # あっても最初の changed env だけを witness にする。
    if is_valid_registered_successor is None:
        return

    predecessor, successor = changed[0]
    try:
        result = is_valid_registered_successor(predecessor, successor)
    except Exception as exc:
        raise ActivationRecordError(
            f"registered successor 判定中に例外: serial={activation_serial}"
        ) from exc
    if type(result) is not bool:
        raise ActivationRecordError("registered successor 判定値が exact bool でない")
    if not result:
        raise ActivationRecordError(
            "generation/hash 束縛済み contract が正当な successor でない"
        )
```

これは単一変更 env の false、spy、non-bool、exception node をすべて満たします。複数同時 +1 では最初の env が `True` なら、2 個目が `False` でも受理します。

成果物影響: 複数 env activation の後半に不正 successor があっても受理され、certified 選択・レポート・台帳が正当でない contract を current として参照します。

修正案:

- `(1,1)→(2,2)` で env-a は `True`、env-b は `False` を返し、env-b で拒否される node を追加する。
- callback の呼出し列を exact assert し、全 changed env に各 1 回、据置 env に 0 回を要求する。
- `validate_activation_records` と `load_activation_state` の predicate 省略が `TypeError`、serial 1 に明示した非 callable が `ActivationRecordError` になることも固定する。

### 2. catalog 内の hash 順だけを見る実装が全 node を通る

深刻度: **must-fix**

根拠: 現行 `_registered_index` は tuple 内の generation 順・連番を検証せず、generation を dict key に変換するだけです。[env_contract_activation.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:226) 合成 `CATALOG` は偶然 generation 順です。[test_env_contract_activation.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:52)

次の contract-hash/catalog-ordinal 実装は、提案 fixture 上では数値 `+1` と同じ結果になります。

```python
def _wrong_hash_order_gate(
    predecessor_rows,
    successor_rows,
    *,
    registered_contracts,
    activation_serial,
    predicate,
):
    positions = {
        env_tag: {
            contract_sha256: index
            for index, (_generation, contract_sha256) in enumerate(sequence)
        }
        for env_tag, sequence in registered_contracts.items()
    }
    predecessor_by_env = {row.env_tag: row for row in predecessor_rows}
    changed = []

    for successor in successor_rows:
        predecessor = predecessor_by_env[successor.env_tag]
        if (
            predecessor.generation,
            predecessor.contract_sha256,
        ) == (
            successor.generation,
            successor.contract_sha256,
        ):
            continue
        if (
            positions[successor.env_tag][successor.contract_sha256]
            != positions[successor.env_tag][predecessor.contract_sha256] + 1
        ):
            raise ActivationRecordError(
                "activation generation 遷移が exactly +1 でない"
            )
        changed.append((predecessor, successor))

    if not changed:
        raise ActivationRecordError("activation transition が全 env 据置の no-op")

    for predecessor, successor in changed:
        result = predicate(predecessor, successor)
        if type(result) is not bool or not result:
            raise ActivationRecordError(
                "generation/hash 束縛済み contract が正当な successor でない"
            )
```

通常順の catalog では skip、downgrade、`(+2,-1)` をすべて拒否します。しかし次の現行型上は受理可能な catalog では、`g1→g3` を hash 上の隣接として受理します。

```python
{
    "env-a": ((1, H_A1), (3, H_A3), (2, H_A2)),
    "env-b": ((1, H_B1),),
}
```

成果物影響: 任意 catalog を使う loader consumer は generation skip を検証済み `ActivationState` として受け取り、台帳・レポートへ skipped generation を記録できます。

修正案: generation 順でない catalog を渡した `g1→g3` を、predicate=`True` でも generation gate の理由だけで拒否する node を追加する。catalog 自体に順序制約を足す場合でも、transition は `new.generation == old.generation + 1` を直接検査することを別 node で固定すべきです。

### 3. `(+2,-1)` 一例だけでは別の集約述語が生き残る

深刻度: **must-fix**

根拠: D228 は env ごとの条件です。[decisions.md:10665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/decisions.md:10665) 提案されている相殺負例は `(+2,-1)` の 1 本だけです。[s2-plan.md:304](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:304)

例えば次の「最大 delta が 1、総和が非負」という集約実装は全提案ケースを満たします。

```python
def _wrong_aggregate_gate(
    predecessor_rows,
    successor_rows,
    *,
    activation_serial,
    predicate,
):
    predecessor_by_env = {row.env_tag: row for row in predecessor_rows}
    pairs = [
        (predecessor_by_env[successor.env_tag], successor)
        for successor in successor_rows
    ]
    changed = [
        pair for pair in pairs
        if (
            pair[0].generation,
            pair[0].contract_sha256,
        ) != (
            pair[1].generation,
            pair[1].contract_sha256,
        )
    ]
    if not changed:
        raise ActivationRecordError(
            f"activation transition が全 env 据置の no-op: serial={activation_serial}"
        )

    deltas = [
        successor.generation - predecessor.generation
        for predecessor, successor in pairs
    ]
    if max(deltas) != 1 or sum(deltas) < 0:
        raise ActivationRecordError(
            "activation generation 遷移が exactly +1 でない"
        )

    for predecessor, successor in changed:
        result = predicate(predecessor, successor)
        if type(result) is not bool or not result:
            raise ActivationRecordError(
                "generation/hash 束縛済み contract が正当な successor でない"
            )
```

判定は次のとおりです。

| delta | 誤実装 | 提案期待 |
|---|---:|---:|
| `(0,0)` | 拒否 | 拒否 |
| `(+1,0)` | 受理 | 受理 |
| `(+1,+1)` | 受理 | 受理 |
| `(+2,0)` | 拒否 | 拒否 |
| `(-1,0)` | 拒否 | 拒否 |
| `(+2,-1)` | 拒否 | 拒否 |
| **`(+1,-1)`** | **受理** | **拒否** |

成果物影響: 一方の env を進めながら別 env を downgrade する record が受理され、certified 選択・レポート・台帳の activation head が不正な混成状態を指します。

修正案: predicate=`True`、exact catalog/head の `(1,2)→(2,1)` を独立負例として追加する。さらに 2 env×3 世代の全組合せについて、期待値を `all(delta in {0,1}) and any(delta == 1)` から直接生成する振る舞い表が望まれます。

### 4. production adapter は「呼んだこと」しか検査されず、返り値を捨てられる

深刻度: **must-fix**

根拠: 設計は `is_valid_successor(...)` の返り値をそのまま返すことを要求します。[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:145) しかし production node は exact contract objects を受け取ったことだけを検査します。[s2-plan.md:310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:310) false node は synthetic callable を直接 loader に渡すため、adapter を通りません。[s2-plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:305)

次の実装は全提案 node を通ります。

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

    # spy は exact objects を観測できる。
    is_valid_successor(
        predecessor_entry.contract,
        successor_entry.contract,
    )

    # 誤り: 判定結果を捨てる。
    return True
```

成果物影響: `is_valid_successor=False` の contract edge でも production adapter が `True` を返し、invalid contract が current として certified 選択・レポート・台帳へ流れます。

修正案:

- `ec.is_valid_successor` を `False` 返却へ monkeypatch し、adapter 自体が exact `False` を返す node を置く。
- 同じ adapter を渡した full loader が successor 診断で拒否するところまで確認する。
- generation/hash/env のいずれかをずらした `ActiveContract` が解決失敗となり、`is_valid_successor` 自体は呼ばれない direct adapter 負例も追加する。

### 5. 3 record の正当な前進連鎖が表だけで、node がない

深刻度: **must-fix**

根拠: `g1→g2→g3` は受理集合表と正例一覧に明記されています。[s2-plan.md:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:211) [s2-plan.md:228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:228) しかし新規 node 一覧には serial 3 の正例がなく、serial 3 は途中 no-op 負例だけです。[s2-plan.md:296](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:296)

例えば正しい `+1` 検査の後に次を入れても、全提案 node は通ります。

```python
if predecessor.generation != 1:
    raise ActivationRecordError(
        "activation generation 遷移が exactly +1 でない"
    )
```

これにより現在想定された `g1→g2` は通り、`g2→g2` の途中 no-op は別途拒否されますが、正当な `g2→g3` だけが拒否されます。

成果物影響: serial 3 以降の正当な活性化が拒否され、certified 選択は旧 contract に固定されたままレポート・台帳 head を更新できません。

修正案: `(1,1)→(2,1)→(3,1)` の全リンクを synthetic predicate で許可し、terminal が g3、ever-active が g1/g2/g3 をすべて含むことを exact assert する正例 node を追加する。

## Should-fix 所見

### 6. serial 2 の env 集合不一致における評価順序が node で固定されていない

深刻度: **should-fix**

根拠: プランは catalog/env 照合後に transition を呼ぶとしています。[s2-plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:117) 現行 env 集合テストは serial 1 だけです。[test_env_contract_activation.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:451) `ActivationRecordError` は loader の公開失敗契約であり、issuer もその型だけを捕捉します。[env_contract_activation.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:34) [issue_env_contract_activation.py:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/tools/issue_env_contract_activation.py:213)

成果物影響: serial 2 の env 追加・欠落で callback、`KeyError` 等が先に発火すると、issuer の拒否レポートと例外契約が変わります。

修正案: serial 2 で env を一つ欠落／追加し、env 集合の `ActivationRecordError`、callback 0 回、head 判定未到達を assert する。

### 7. 段 1 probe の「hash 据置」ケースは実際には通常前進と同一

深刻度: **should-fix**

根拠: probe の `rows()` は generation から hash を必ず再生成します。[s1-probe.py:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:32) そのうえ H ケースは C ケースと同じ `[(1,1),(2,1)]` です。[s1-probe.py:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:82) [s1-probe.py:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:87)

成果物影響: 親 probe を hash 束縛の実測根拠として参照すると、試していない hash 分離変異がレポート・台帳上は検査済みに見えます。

修正案: H を削除して通常前進との重複を明記するか、g2 に g1 hash を明示して canonical state hash を再計算する真の wrong-hash probe に置き換える。段 2 の独立 wrong-hash nodeは維持する。

## 同一入力束縛の判定

親 brief の P2、すなわち plain registry 投影だけでは不十分です。`registered_contracts` は任意 caller が構成でき、現行 `_registered_index` は `is_valid_successor` を一切検査しません。[s1-brief.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-brief.md:64) [env_contract_activation.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:226)

段 2 の「必須 callable＋exact production adapter」なら、保証を次のように限定する限り設計上は成立します。

- generic loader は「caller が供給した catalog/predicate に対して妥当」なだけ。
- production authority は `_load_authority_snapshot` と issuer が exact adapter を渡す合成全体で成立する。
- `ActivationState` 単体や任意 predicate を渡した direct call を production-authoritative と呼ばない。

より強くするなら、検証済み `GENERATIONS` snapshot から catalog と adapter closure を同時生成し、closure が同じ snapshot を捕捉する構成がよいです。これなら `_REGISTERED_CONTRACT_CATALOG` と、呼出し時に module-global `GENERATIONS` を読む adapter の分裂も避けられます。

## D228 rollback 経路

この wave は一般の contract rollback を塞ぎません。

- `is_valid_successor` は変更 field が calibration path/SHA の組だけかを見るため、時間方向や較正の新旧を知りません。[env_contract.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:208)
- source 世代列の通常初期化は隣接検査と hash 一意性を持ちますが、module 属性の再束縛までは authority にできません。[env_contract.py:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:304)
- reverse index は本 wave で変更されず、resolver は module-global index を読みます。[env_contract.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:627)

ただし、親 brief は「contract 実体 rollback の一般対策」を明示的に scope 外としています。[s1-brief.md:57](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-brief.md:57) D228 自体も同じ射程外を明記しています。[decisions.md:10688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/decisions.md:10688) したがって、現状の文書を「一般 rollback 防止」とまでは読まない限り、この点単独では must-fix に数えません。

最終説明には「検証済み production generation snapshot に対する record-level edge を束縛するだけで、世代列・module binding・reverse index の再束縛や較正 freshness は保証しない」と再掲するのが安全です。

## mask・変異帰属

提案 node の帰属は次のとおりです。

| node | 単一理由性・mask 判定 |
|---|---|
| `accepts_one_plus_one...` | 正例。catalog/head とも適合 |
| `accepts_multiple_simultaneous...` | 正例だが、全 changed env の callback 実行を見ない |
| `rejects_all_env_noop` | catalog/head は正しく、no-op gate 単独 |
| `rejects_noop_in_middle...` | pair 1 は正常、pair 2 の no-op 単独 |
| `rejects_skip...` | g3 登録済み、callback=`True` のため numeric gate 単独 |
| `rejects_downgrade...` | 両世代登録済み、callback=`True` のため numeric gate 単独 |
| `rejects_compensating...` | callback=`True` で単一理由。ただし変異集合が不足 |
| `rejects_plus_one...false` | generation/catalog/head 正常、callback false 単独 |
| `predicate_receives_exact...` | 1 changed env の入力だけを確認。複数 env 量化を証明しない |
| `wrong_contract_hash` | registry gate 専用。transition 変異の kill node ではない |
| `rejects_non_bool...` | 正常 +1 なので返り値型だけ |
| `wraps_successor_exception...` | 正常 +1 なので callback 例外だけ |
| `production_successor_adapter...` | 正例だけ。返り値伝播と不一致入力を検査しない |
| `issue_main_rejects_noop...` | target 不在・head/catalog 正常なら no-op gate 単独 |

head hash は各負例の tail に合わせる計画なので、transition 無効化時には head gate は救済しません。`ever_active` は各 registry-valid row を先に加え、`ActivationState.__post_init__` は current hash の包含だけを見るため、これも transition 変異を mask しません。[env_contract_activation.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:297) [env_contract_activation.py:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract_activation.py:77)

既存 fixture の再著述については、次の帰属になります。

- valid-suffix test を正当な pegasus g2 前進に直す案は、head pin 単独理由を回復します。
- historical resolver を forward chain に直す案は、旧 g1 の ever-active 保持を独立に検査できます。
- issuer success を linux-baremetal 据置＋pegasus g2 に直す案は [T-657] の実 record 形を通します。

## 正例と境界

意図された実装なら、次は静的に受理できます。

- 一部据置・一部 +1: `(1,1)→(2,1)`。
- 複数 env 同時 +1: `(1,1)→(2,2)`。
- [T-657] の linux-baremetal g1 据置＋pegasus g1→g2。pegasus g2 は g1 から calibration path/SHA だけを置換しており、現行 `is_valid_successor` の許可差分に一致します。[env_contract.py:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:242)
- forward 後の pegasus g1 historical 解決。全 record の hash を `ever_active` に累積するためです。
- serial 1 単独。predecessor rows が存在せず、predicate は callable 検査だけで呼ばれません。

`g1→g2→g3` も述語上は受理できますが、must-fix 5 のとおり、その過剰拒否を検出する node がありません。

## 総括

**判定: NO-GO**

**must-fix: 5 件**  
should-fix: 2 件

required callable＋production adapter への設計変更自体は妥当です。しかし現テスト案では、generation 主体の 1-witness 実装、hash/catalog 順実装、別形の集約実装、adapter の返り値破棄、g2 以降の過剰拒否がすべて生き残ります。pytest・probe・import は実走しておらず、本判定は静的読解のみです。