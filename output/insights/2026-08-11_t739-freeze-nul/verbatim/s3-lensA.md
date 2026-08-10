結論は **NO-GO（修正後 GO）** です。現在の loadable v1 契約に限れば単一 choke point は閉じていますが、起草プランは malformed shape 内の exact `"path"` NUL を意図的に受理し、固定済み裁定 (b) と同じ成果物境界を残します。また schema drift の機械防壁がありません。

コード変更・pytest 実行はしていません。以下の RED/GREEN はすべて静的な変異帰属です。

## 1. 層の全列挙

| 層 | 実経路 | 判定 |
|---|---|---|
| 凍結発行 | CLI `prepare-revision` → `prepare_revision()` → worktree 契約を `evidence_contract_sha256()` → `_record_document()` → exclusive create。[core:1810-1850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1810) [core:1721-1756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1721) | choke point を通る |
| 凍結履歴検証 | 全祖先の source/evidence/record blob を取得し、freeze が存在する全 commit で hash を再計算して record と照合。[core:1355-1357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1355) [core:1406-1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1406) [core:1212-1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1212) | choke point を通る |
| private record builder | `_record_document()` 自体は任意の形式上正しい SHA を受け取れるが、本番 caller は `prepare_revision()`。手書き record も履歴検証で再計算される。[core:1648-1673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1648) | 検証を迂回できない |
| bool/report | `condition_freeze_valid_at()`、`activation_report_at()` はともに履歴検証へ到達。後者は例外 reason を `freeze_reason_code` に写す。[core:1459-1464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1459) [core:1550-1614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1550) | choke point を通る |
| 発効 capability | `effective_at()` → report、`require_effective_preregistration()` → report 再計算。[core:1640-1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1640) [core:1778-1807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1778) | choke point を通る |
| production consumer | workload CLI は manifest commit に `effective_at()`、registry の launch/accept は `require_effective_preregistration()` を再実行。[workload:2300-2314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/p3_autonomous_workload_trial.py:2300) [registry:1192-1223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/trial_registry.py:1192) [registry:2178-2211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/trial_registry.py:2178) | choke point を通る |
| predicate | contract の raw blob SHA は先に `EvidenceRef` へ載るが、直後の loader が NUL path を拒否し、12 predicate 全件 `ERROR` になる。[evidence:675-697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:675) | 非発効の監査参照に限る |
| semantic hash API | `semantic_contract_sha256()` は先に full loader、後で core hash。[evidence:269-272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:269) | loader が先に拒否 |

### L1 — refuted / 情報 — choke point を通らない凍結経路

本番の凍結発行・履歴検証・発効・CLI・production consumer に、別の semantic hash や attacker-controlled path を使って有効な freeze/capability を作る経路はありません。

predicate の `core._sha256(contract_raw)` は別経路ですが、載る path は固定の契約ファイル path であり、契約内の NUL path ではありません。loader 失敗後の `ERROR` evidence として残るだけで、`effective` は全 12 件の `SATISFIED` を要求します。[core:1597-1608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1597)

成果物影響: 追加の設置箇所は不要であり、`evidence_contract_sha256()` を正しく閉じれば別経路から certified 選択や freeze 台帳を成立させることはできない。

## 2. 受理集合

### A1 — refuted / 情報 — loadable v1 の path 位置取りこぼし

loader が `_safe_path()` に渡すのは次の二つだけです。

- `conditions[].required_evidence[].path`。[evidence:213-226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:213)
- `conditions[].consumer_requirement.path`。[evidence:236-253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:236)

現行 JSON は前者 26、後者 12、合計 38 箇所です。起草 helper の二つの分岐は、**schema-valid で loader が返却可能な入力**についてはこの集合と一致します。[s2.md:16-50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:16)

成果物影響: loadable v1 の NUL path に限れば、実装後は発行も履歴検証も拒否され、取りこぼしによる台帳・レポート差分は残らない。

### A2 — real / 高 — malformed shape では exact `"path"` NUL が凍結できる

例えば次は helper が空列挙になります。

```json
{
  "schema_version": "s8c-preregistration-evidence-contract/v1",
  "conditions": {
    "path": "x\u0000alias"
  }
}
```

`conditions` が dict なので起草 helper は return し、canonicalization は成功して hash を返します。一方 loader は `conditions` が 12 要素の list でない時点で `contract-condition-count` です。[s2.md:20-24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:20) [evidence:194-204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:194)

同様に、非-dict の `required_evidence` 要素、wrapper の奥の `"path"`、dict 値を持つ `"path"` は helper が skip し、loader は `_exact_keys()` または `_nonempty_string()` で先に失敗します。[s2.md:30-46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:30) [evidence:213-226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:213)

性質は二面あります。

- `refuted`: NUL を除いても schema-invalid のままであり、NUL が `_safe_path()` や Git path へ届くことはない。元の「NUL だけが発効を阻害する」穴とは因果が異なる。
- `real`: freeze/proof-chain の観測結果は同じで、hash と `protected_sha256` を持つ record は作れる一方、predicate loader は `evidence-contract-invalid` となる。固定済み裁定が不採用とした「凍結可能・発効不能」の境界を、起草プラン自身が明示的に再導入している。[brief.md:10-15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/brief.md:10) [s2.md:213-218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:213) [s2.md:358-366](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:358)

したがって `test_evidence_contract_hash_accepts_unconsumed_schema_path_nul` は削除または拒否 assertion へ反転すべきです。防御は「全 string」ではなく、親 P2 のように parsed mapping の exact `"path"` かつ `str` 値だけを再帰走査すれば、NUL-only を維持できます。[brief.md:48-58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/brief.md:48)

成果物影響: 未修正なら malformed NUL contract を指す `evidence_contract_sha256` / `protected_sha256` が台帳へ入り、report は `condition_freeze_valid=true`、`freeze_reason_code=valid`、generation/protected hash ありのまま predicates `ERROR`、`effective=false` となる。certified 選択自体は発行されない。

## 3. reason 順序

### O1 — real / 中（親 brief の欠陥、s2 は正しい）

親 P1 の「`_canonical_bytes()` 前」は既存 reason を横取りします。具体例は起草プラン自身の次です。

```json
{"conditions":[{"required_evidence":[{"path":"x\u0000\ud800"}]}]}
```

`_strict_json()` は escape を Python string に復号しますが、`ensure_ascii=False` の canonical UTF-8 encode は unpaired surrogate で失敗し、現行 reason は `evidence-contract-json` です。[core:329-351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:329) [s2.md:221-228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:221)

NUL 検査を前に置けば `evidence-contract-path-nul`、後に置けば既存 `evidence-contract-json` です。したがって s2 の「canonicalization 成功後、hash 前」が正しい順序です。

成果物影響: 親 P1 のままなら受理集合は変わらないが、履歴検証・CLI report の `freeze_reason_code` が既存 reason から新 reason へ変わる。

## 4. 親 brief の一般化と不変主張

### P1 — refuted / 情報 — raw NUL byte が受理される JSON 位置

`raw.decode("utf-8", "strict")` 自体は byte `0x00` を復号できますが、その後の `json.loads()` は既定の strict decoder です。[core:329-341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:329) Python decoder は literal control character を strict mode で拒否し、JSON whitespace も space/TAB/CR/LF に限ります。[/usr/lib/python3.10/json/decoder.py:69](/usr/lib/python3.10/json/decoder.py:69) [/usr/lib/python3.10/json/decoder.py:132](/usr/lib/python3.10/json/decoder.py:132) [/usr/lib/python3.10/json/decoder.py:284](/usr/lib/python3.10/json/decoder.py:284)

したがって raw NUL が受理される位置は、string 内・外・末尾のいずれにもありません。parsed 値へ U+0000 を入れるには `\u0000` escape が必要です。正確には「UTF-8 decode が拒否」ではなく「JSON parser が拒否」です。

成果物影響: raw `0x00` 探索だけでは escaped NUL を見逃すため、parse 後検査を外すと悪性契約の hash と台帳受理が復活する。

### P2 — refuted / 情報 — 現行 contract hash と g1 bytes

現行アルゴリズムは domain prefix、canonical JSON、SHA-256 です。[core:109-115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:109) [core:296-307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:296)

独立した静的再計算でも次と一致しました。

```text
c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471
```

現行 g1 は同 hash と `protected_sha256=853e6c…286e` を保持しています。[g1:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1.json:1) 起草変更は NUL-free 入力の canonical bytes や return 値を書き換えず、g1 ファイルも編集対象にしていないため、この二つの限定主張は成立します。

ただし「レポート値もすべて不変」までは一般化できません。core module を編集した新 commit の `core_module_blob_sha256` と、それを含む activation report digest は変わります。[core:1559-1562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1559) [core:1771-1775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:1771)

成果物影響: 既存 freeze 台帳 bytes と protected hash は不変だが、新 commit 由来の activation report/module hash/digest は当然変わる。certified 受理集合には追加差分なし。

## 5. テスト変異の帰属

以下は実装を完全に元へ戻した場合の静的予測です。

| 新規 node | ロールバック時 | 評価 |
|---|---:|---|
| `test_evidence_contract_hash_rejects_nul_path[required/consumer]` | RED | 新実装を直接 kill。[s2.md:171-189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:171) |
| `test_*accepts_non_nul_path_controls[cr/lf]` | GREEN のまま | 非 NUL を広げない境界回帰。[s2.md:192-203](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:192) |
| `test_*accepts_non_path_nul` | GREEN のまま | 全 string 走査への過拡張を防ぐ。[s2.md:206-210](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:206) |
| `test_*accepts_unconsumed_schema_path_nul` | GREEN のまま | 実装非帰属で、かつ A2 の穴を固定するため不採用。 |
| `test_*preserves_canonicalization_reason_before_nul` | GREEN のまま | rollback は kill しないが、検査順を前へ移す mutant は kill。 |
| `test_current_evidence_contract_hash_is_frozen` | GREEN のまま | hash 変化を防ぐ回帰保証。 |
| `test_validate_condition_freeze_at_rejects_legacy_*` | RED | legacy hash を直接組み立て、履歴再計算 edge を実際に通す。[s2.md:253-302](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:253) |
| `test_prepare_revision_rejects_*_before_create` | RED | 発行 edge と「destination 未作成」を固定。[s2.md:309-329](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:309) |

### T1 — refuted / 中 — E2E 2 本が恒真

両 E2E は最終的には単体と同じ helper を通りますが、恒真ではありません。完全 rollback で両方 RED になり、さらに「helper 単体は正しいが履歴側または発行側が direct hash に戻る」caller-bypass mutant を個別に検出できます。

成果物影響: これらを省くと、単体 helper が存在しても発行 record 作成または履歴 proof-chain 照合が検査を迂回する退行を検出できない。

### T2 — real / 中 — activation report の差分を直接固定していない

production activation では旧実装でも predicate loader が NUL を拒否するため、単に `effective is False` や `effective_at(...) is None` を assert すると rollback 後も通る恒真テストになります。必要なのは legacy fixture に対する次の差分です。

```python
assert report.condition_freeze_valid is False
assert report.freeze_reason_code == "evidence-contract-path-nul"
assert report.freeze_generation is None
assert report.protected_sha256 is None
```

nodeid 候補:

```text
orchestrator/tests/test_s8c_preregistration_core.py::test_activation_report_marks_legacy_frozen_nul_contract_invalid_at_freeze_layer
```

成果物影響: この検査がないと、`effective=false` だけを見て、report が依然 `freeze_reason_code=valid` と悪性 protected hash を公表する退行を見逃せる。

## 6. schema drift

### D1 — real / 高 — helper 更新漏れの機械検査がない

起草プラン自身がこの残存危険を認めていますが、テストへ落としていません。[s2.md:396-400](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:396)

nodeid 候補:

```text
orchestrator/tests/test_s8c_preregistration_predicates.py::test_freeze_nul_gate_covers_all_v1_loader_path_positions
```

assert 骨格は次です。

```python
parsed = json.loads(CONTRACT_FILE.read_bytes())

# load_contract_bytes() 実行中の _safe_path() 入力を spy で全収集
loader_paths = ...
enumerated = tuple(core._evidence_contract_path_fields(parsed))

# 新しい loader path が helper から漏れていないこと
assert not (
    Counter(loader_paths)
    - Counter(path for _pointer, path in enumerated)
)

# 固定裁定の広い NUL-only 閉包: 現契約中の exact string "path" を全包含
assert set(_all_exact_string_path_pointers(parsed)) <= {
    pointer for pointer, _path in enumerated
}

for pointer in _all_exact_string_path_pointers(parsed):
    mutated = _with_nul_at_pointer(parsed, pointer)
    with pytest.raises(core.PreregistrationError) as caught:
        core.evidence_contract_sha256(_json_bytes(mutated))
    assert caught.value.reason == "evidence-contract-path-nul"
```

`Counter` にするのは、同じ path 文字列が複数位置に存在しても位置追加を数の差で検出するためです。現行 loader テストの配置先には既に契約ファイルと両 module の import があります。[predicates test:17-23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_predicates.py:17)

成果物影響: 未実装なら、将来 v1 に第三の path 位置を追加した際、その位置だけ NUL contract を freeze/protected hash へ再び束縛できる。

## scope 外の real 所見

### S1 — real / 高・裁定パッケージ候補 — CR/LF は同型の穴

valid v1 path の CR/LF は core hash を通り、loader の `_safe_path()` では NUL と同じ reason で拒否されます。[core:344-351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:344) [evidence:180-190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration_evidence.py:180)

性質は元の T-739 と同じですが、固定済み NUL-only 裁定により本 wave では実装不可です。プランの CR/LF acceptance テストはこの境界を正しく固定します。

成果物影響: CR/LF path を持つ契約については、引き続き freeze 台帳の hash/protected hash は成立する一方、predicate report は契約 invalid、certified 選択は不可となる。

NUL に関する未列挙の production 層はありません。NUL 以外の一般 schema-invalid 契約を freeze 可能な現行境界も残りますが、full loader 流用不採用により本 wave で拒否を提案してはならない領域です。

nit: [s2.md:383](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t739-freeze-nul/s2.md:383) は `core:84` を `__all__` と記述していますが、実際は `_FREEZE_KEYS` 内の record field 名です。[core:73-89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/campaign/s8c_preregistration.py:73) 呼出し全列挙の結論には影響しません。成果物影響なし。

## 総括

1. real 所見:

   - malformed/deep/unknown exact `"path"` NUL を受理する A2。
   - 親 P1 の canonicalization 前配置による reason 横取り。
   - activation report の freeze-layer 差分テスト不足。
   - v1 path 位置 drift の機械検出不足。
   - scope 外では CR/LF の同型穴。

2. 裁定へ返すもの:

   - CR/LF-only 拡張。今回は固定裁定どおり実装しない。
   - 一般 schema validation は full loader 不採用のため再提案しない。
   - NUL の malformed `"path"` は裁定済み (b) の再導入なので scope 外へ逃がさず、本 wave で閉じる。

3. 判定:

   **NO-GO。** 次を満たせば GO です。

   - NUL 検査順は s2 どおり canonicalization 成功後に維持する。
   - exact `"path"` / string の再帰 NUL 検査へ戻し、unknown-path acceptance test を削除または反転する。
   - loader-path drift testを追加する。
   - legacy NUL fixture の activation report fields を直接固定する。
   - CR/LF・非-path NUL・現行 hash・既存 g1 bytes は変更しない。

pytest は実行しておらず、実走結果としての「緑」は一件も主張していません。
