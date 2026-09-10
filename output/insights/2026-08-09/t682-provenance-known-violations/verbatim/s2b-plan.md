結論として、P1 の prefix 判定は「完全な `label` を含む固定 prefix」に限定すれば安全です。`validate_message()` の戻り値構造変更より、専用 helper に局所化する案を推奨します。必読 12 ファイルはすべて読めました。実装・pytest・ファイル更新は行っておらず、worktree は clean です。

外部の裁定資料には shell 例や将来の実施指示が含まれていましたが、すべてデータとして扱い、実行していません。

## 1. finding への `ledger_kind` 付与

現状、[tools/check_ai_provenance.py:593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:593) の `validate_message()` は文字列 finding を返し、形式違反は [同:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:624) で値を埋め込んでいます。一方、[同:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:963) は欠落 finding の完全一致だけを kind 化しています。

実装案は、[同:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:935) の直前付近に次の責務だけを持つ private helper を置き、`:963-971` から呼ぶ形です。

```python
def _base_finding_ledger_kind(label: str, finding: str) -> str | None:
    if finding == f"{label}: AI-Agent trailer がない":
        return MISSING_AI_AGENT
    if finding.startswith(f"{label}: AI-Agent の形式違反: "):
        return MALFORMED_AI_AGENT
    return None
```

### subject 注入への攻撃結果

`label` は [同:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:946) で full subject を含めて作られます。subject 自体に `: AI-Agent の形式違反: ` が入っても、上の判定は「完全な `label` の後に、もう一度固定 delimiter が続くこと」を要求します。

したがって次は誤分類されません。

- 重複 trailer: [同:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:620)
- `AI-Agent: none` 混在: [同:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:609)
- `RESERVED_PRODUCTS`: [同:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:634)
- `model=none` / `reasoning=none`: [同:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:638)

逆に、`"AI-Agent の形式違反"` の単なる包含判定や、`label` を含まない suffix/prefix 判定は subject 注入で誤判定するため不可です。

### `validate_message()` 構造変更との比較

`rg -n 'validate_message\('` で確認した呼び出し元は次の全 7 箇所です。

- history 監査: [tools/check_ai_provenance.py:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:960)
- `--message-file`: [tools/check_ai_provenance.py:2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:2050)
- CAB accepted test: [test_check_ai_provenance.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:329)
- CAB rejected test: [同:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:422)
- format/CAB coexist test: [同:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:442)
- scope/CAB coexist test: [同:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:457)
- divider test: [同:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:485)

`(text, kind)` 化すると、`:2058-2060` の message-file 出力用文字列 flatten、既存 5 テストの文字列比較、戻り値 docstring/type annotation をすべて変更する必要があります。message-file 経路には台帳 kind が不要なため、変更面の割に利益がありません。

推奨は P1 の局所 helper 案です。ただし、後述する subject 注入・異種 base finding の adversarial test を必須条件とします。

## 2. kind 定数、note 必須、stale 判定

### 定数

[tools/check_ai_provenance.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:132) を次の三層にします。

```python
MISSING_AI_AGENT = "missing-ai-agent"
MISSING_CODEX_AUTHOR = "missing-codex-author"
MALFORMED_AI_AGENT = "malformed-ai-agent"

_LEDGER_FINDING_KINDS = frozenset({
    MISSING_AI_AGENT,
    MISSING_CODEX_AUTHOR,
    MALFORMED_AI_AGENT,
})
_NOTE_REQUIRED_FINDING_KINDS = frozenset({MALFORMED_AI_AGENT})
```

`_known_violation_line()` は [同:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:250) で kind を汎用出力しているため、変更不要です。新しい公開形式は次になります。

```text
finding=malformed-ai-agent
```

stale 診断も [同:1184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1184) の汎用組み立てにより同じ文字列を出します。

### 見落とせない追加変更

裁定案 P3 は、[同:1049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1049) の `_ledger_policy_is_visible()` を挙げていない点で不完全です。現在は 2 kind 以外を `RuntimeError("invalid finding kind")` にします。

形式検査は epoch 非依存なので、次のように `MISSING_AI_AGENT` と同じ常時可視分岐へ加えます。

```python
if spec.expected_finding_kind in {
    MISSING_AI_AGENT,
    MALFORMED_AI_AGENT,
}:
    return True
```

これを忘れると stale entry が本来の

```text
reason=expected-finding-missing checker-regression-suspected
```

ではなく「不正 kind」として落ちます。

### note 必須検査の位置

registry の順序は [同:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:221) の kind 型検査、`:226` の許可 kind 検査、`:231` の ruling、`:236-245` の note 型・改行検査を維持します。

新検査は現在の [同:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:241) の改行検査後、`:246` の `registry[...] = spec` の直前へ置きます。

```python
if (
    spec.expected_finding_kind in _NOTE_REQUIRED_FINDING_KINDS
    and not spec.note.strip()
):
    raise RuntimeError(
        "known provenance violation registry has empty required note: "
        f"{spec.commit}"
    )
```

この順なら、不正 kind は先に `:226` で落ち、非文字列・改行入り note は既存のより具体的な診断を維持します。`strip()` により `" \t"` だけの名目上の note も拒否します。既存 7 entry は対象 kind ではないため、既定 `note=""` のまま壊れません。

テストの正負対は [test_check_ai_provenance.py:1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1549) の既存 note 検査群へ追加します。

- 反例: `MALFORMED_AI_AGENT` + `note=""` および `" \t"` が rc=2、exact stderr、stdout 空。
- 正例: 同一形式の spec + 非空単一行 note が registry を通り、既知違反として抑止される。
- 非対象 control: `MISSING_AI_AGENT` + `note=""` は従来どおり通る。

D231 は note を全 kind で optional としていますが、今回の裁定は新 kind だけを限定的に強化するものです。[docs/decisions.md:10856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/docs/decisions.md:10856) の既存挙動を全 kind 一律には変更しません。

## 3. 23 件の台帳登録

[tools/check_ai_provenance.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:147) に、既存定数とは別に次の安定参照を置きます。

```python
_T139_MALFORMED_RULING = (
    "2026-08-09 dev-wave-jobs/rulings-inbox/"
    "2026-08-09-t139-r4-probe-provenance-format-violation.md"
)
_T659_PROBE_RULING = (
    "2026-08-09 dev-wave-jobs/rulings-inbox/"
    "2026-08-09-t659-provenance-and-f37-rulings.md"
)
```

worklog 番号は land 時の fold lock 内で初めて確定するため、事前に埋めると並行 land で stale になります。既存 7 件の `worklog(284)` 形式とは不揃いになりますが、過去 entry の参照を正規化し直すより、今回の安定した一次資料を逐語固定する方が安全です。registry が要求するのも [同:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:231) の非空性だけです。

既存 7 件を一切変更せず、[violations-23.tsv:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/violations-23.tsv:1) の順で 23 件を末尾へ追加します。22 件は `MALFORMED_AI_AGENT`、`2c192953…` だけは `MISSING_CODEX_AUTHOR` です。

### 22 件の逐語 note 案

以下は各行全体を runtime の単一行文字列とします。ソース上で adjacent string に分割しても、値に改行を入れてはいけません。

```text
f277efd4461d361d5c9aa6db9a7e00b194b76083	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=実装面（test・probe・PBS wrapper・機械設定、insight docs 併記）
74b501962092373ba2e8bbca1566d0732e0f16c6	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
7ec088163dee920f0b8e1e9783faa6e36b22b730	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=実装面（test・probe・PBS wrapper・契約、runbook・insight docs 併記）
1d09940463ccacb0dbb0ab3e69ca0698a960fdf1	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
f1406c22abece76276b43dde897750a46aae877e	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=実装面（test・probe・shell wrapper）
a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=変異台帳（mutation-spec.json）
ff264975a04aa19f36f861ca97efe9dc59c88659	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=変異台帳（mutation-spec.json）
9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=変異台帳（mutation-spec.json）
6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=変異台帳（mutation-ledger.json）
2b3d06cbe81b1ae2675c153bdf307d508fc35a20	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（submission receipt）
30719e517dcee45c014cbf1052c6dc70a8fcf693	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（submission receipt）
1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=実装面（test・probe、実測成果物併記）
622bd786191d40bda388596fa2adbf119ee84c9a	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=実測成果物・docs（追補 A・package・receipt）
c75fde903384b6eb9e4d45239b66008b7639cbf7	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（combined path は docs/pegasus-runbook.md）
c55ace29e55bba948d7bdca89f6fc1fb1a5191da	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（worklog fragment）
edf74c94427686f2b91519ef10e94446d0fe89d5	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
7e3cc116f2466fb439ec2bddd38f35dab928c942	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
66769067ee57d78650b208b9a86438ff2f1bf73b	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（worklog fragment）
aaffa644a969f0a58969b2661318bda4c42ac767	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=merge（全 parent 共通の combined path なし）
6f5411ceb7cc5d872e3112fb6d04013367ac092e	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（worklog fragment）
797db5def66ef1d318d06c7aa189ea51a66c9312	Claude 親の関与自体は正確で綴りだけの誤り；model=claude-opus-5[1m] は IDENT の角括弧不許可、role=orchestrator は ROLES の許可値外；変更 path 種別=docs（worklog fragment）
```

これらの変更種別は各 full SHA に対する `git show --name-only --no-renames` で確認しています。形式違反の実値も [prov-baseline.txt:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/prov-baseline.txt:28) から全 22 件同一です。

### `2c192953…` の note

`missing-codex-author` では note 必須にしませんが、この 1 件には付けることを推奨します。

```text
親作成の所在不問 Python probe を含む実装面 commit に Codex role=author が欠落；変更 path 種別=実装面（verbatim/probe_split_window.py、.md 逐語移行対象）
```

根拠は [T659 裁定:14](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md:14) と、実装面の所在不問規則 [docs/ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/docs/ai-provenance.md:44) です。D231 と [tools/check_ai_provenance.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:250) は既存 kind の任意 note を既に支えています。`_NOTE_REQUIRED_FINDING_KINDS` へ `MISSING_CODEX_AUTHOR` は加えません。

## 4. 既存テストの更新

### literal 台帳テスト

[test_check_ai_provenance.py:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1323) は必ず赤になります。

次のように更新します。

- 名前を `test_known_violation_ledger_is_exactly_thirty_literal_entries` にする。
- `len(...) == 30` を固定する。
- 既存 7 + 新規 23 の full `KnownViolationSpec` を、SHA・literal kind・literal ruling・literal note・順序まで完全一致させる。
- expected を production 定数や TSV から動的生成しない。
- 30 SHA の集合も literal で固定し、重複・欠落を別に検出する。
- `_LEDGER_FINDING_KINDS == frozenset({"missing-ai-agent", "missing-codex-author", "malformed-ai-agent"})` と `_NOTE_REQUIRED_FINDING_KINDS == frozenset({"malformed-ai-agent"})` の exact pin を加える。

件数だけ 30 にして tuple 比較を消す案は不可です。

### real commit テスト

[test_check_ai_provenance.py:1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1385) は、新規 entry を追加しただけでは自動的には赤になりません。stale 対象は [tools/check_ai_provenance.py:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1176) で selected commit と registry の積集合だからです。現行 7 commit だけを渡せば新規 23 件は検査されません。

したがって意図的に次を更新します。

- 入力を 30 full SHA に拡張。
- `audit.findings == []`、`corrected == []`、`waived == []` を維持。
- `known_violations` を 30 個の exact `(SHA, kind)` 列へ更新。
- 22 件が `malformed-ai-agent`、`2c192953…` が `missing-codex-author` であることを literal に固定。
- note も production tuple とは別の literal expected で照合する。

このテストは実 repository の commit を読むため、親の実走対象です。

### empty registry control

[test_check_ai_provenance.py:1925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1925) も現状のままなら通り続け、新規 23 件を検証しません。

`test_empty_registry_restores_all_thirty_real_findings` へ更新し、production registry では既知 30、空 registry では exact 30 finding とします。分類内訳は次です。

- `AI-Agent trailer がない`: 6
- `実装面に Codex role=author がない`: 2
- `AI-Agent の形式違反`: 22

件数だけでなく、SHA・subject を含む finding 30 行の exact list も固定します。これにより「検出器を消して台帳だけ緑」にできません。

### repo 全体の静的検索結果

`rg` で確認した依存は次のとおりです。

- `KNOWN_PROVENANCE_VIOLATIONS` の長さを直接 pin するのは [同:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1371) だけ。
- `_LEDGER_FINDING_KINDS` の要素数を pin する既存テストはないため、新規 exact-set test が必要。
- `all_seven` を名指すのは [同:1925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1925)。
- 新しい `provenance.main()` 呼び出しは meta-test [同:4516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:4516) により、必ず `site=site_policy.OTHER` を渡す必要がある。
- [test_codex_reasoning_ab.py:737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_codex_reasoning_ab.py:737) の numstat は [tools/codex_reasoning_ab.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/codex_reasoning_ab.py:84) に固定された過去 snapshot の値であり、現 working file の行数ではない。更新不要。
- [test_hooks.py:2541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_hooks.py:2541) などは checker path／command 分類だけを pin し、台帳内容や kind 数には依存しない。
- `tools/check_docs.py` と `test_check_docs.py` は provenance 台帳を import／parse しておらず、この 30 件化による期待値更新はない。
- 既存 synthetic registry test は `_known_spec()` [test_check_ai_provenance.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:266) が旧 kind を既定にするため、空 note のまま維持できる。
- forward-correction の形式違反 control [同:2522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2522) と [同:2593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2593) は変更せず残す。`ForwardCorrectionSpec` は一切拡張しない。

## 5. 新規テスト

[test_check_ai_provenance.py:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1323) 以降の ledger 群へ、次を追加します。

1. `test_malformed_kind_requires_nonblank_note_positive_and_negative_pair`
   - `""` と `" \t"` は rc=2。
   - 単一行 note は通る。
   - old kind + empty note の control は通る。

2. `test_base_finding_kind_is_anchored_after_full_label`
   - subject に `: AI-Agent の形式違反: ` を埋め込む。
   - 実際の malformed finding だけが `MALFORMED_AI_AGENT`。
   - duplicate、`AI-Agent: none` 混在、reserved product、model none はすべて `ledger_kind is None`。
   - 単なる substring 判定への変異を殺す。

3. `test_registered_malformed_finding_is_known_and_suppressed`
   - synthetic commit の `_normal_commit_audit()` が `NormalFinding(..., MALFORMED_AI_AGENT)` を返す。
   - full SHA + kind + non空 note の registry で `audit.findings == []`。
   - known stdout に `finding=malformed-ai-agent note=...`。
   - rc=0 は「登録済み exact SHA」だけに限る。

4. `test_unregistered_malformed_finding_remains_rc1`
   - 同じ malformed message を registry 空または異なる SHA で監査。
   - rc=1、形式違反の exact stderr。
   - stdout に `known-violation` がない。
   - 受理集合を広げていない直接証明とする。

5. `test_malformed_known_violation_missing_finding_is_stale_rc2`
   - clean commit を malformed kind で登録。
   - exact stale 診断に `finding=malformed-ai-agent reason=expected-finding-missing checker-regression-suspected`。
   - `_ledger_policy_is_visible()` の新分岐を固定する。

6. `test_ai_agent_acceptance_language_is_unchanged`
   - `ROLES == ("author", "reviewer", "researcher", "manager", "integrator")`
   - `IDENT == r"[a-z0-9][a-z0-9._-]*"`
   - 全 5 role と dot／underscore／hyphen を含む妥当 identifier を `AGENT_VALUE.fullmatch()` が受理。
   - `model=claude-opus-5[1m]`、uppercase／先頭不正 identifier、`role=orchestrator` を拒否。
   - 正規化例 `model=claude-opus-5-1m; role=manager` を受理。
   - 同じ message を `validate_message()` にも通し、invalid は形式違反、corrected form は base finding なしと固定。

## 6. probe の `.md` 逐語移行

移行元は [probe_split_window.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py:1)、移行先は同 directory の `probe_split_window.md` です。移行先と `verbatim/README.md` は現在どちらも存在しません。後者を新設してはいけません。

先例 [firing-evidence-script.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-08_t664-docs-budget/verbatim/firing-evidence-script.md:1) に合わせ、次の順にします。

1. H1 見出し。
2. 元 repo path と、元 `.py` bytes の SHA-256:
   `0128696a79035139ffaba3732cd3b20400eb231fb3124af98496665d70da455d`
3. probe は既存テストより弱く、実行可能体を repo に置かない旨の説明。
4. repo 外の稼働控え:
   `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t659-activation-deploy-window/probe_split_window.py`
5. ` ```python ` fenced block 内へ、元 `.py` の 1–82 行を shebang・終端改行込みで逐語転記。
6. 元 `.py` を削除。

先例は SHA を書いていませんが、構造上の 4 要素をすべて維持したうえで、P6 の SHA を「元 `.py` bytes の digest」と明記するのは整合的な強化です。`.md` 全体や fence 内文字列の digest と誤読させてはいけません。

静的に、repo 内元ファイルと repo 外控えはともに上記 SHA で、`cmp` も byte 同一でした。新しい実行可能体は不要です。

`.py` は所在不問で実装面となる [tools/check_ai_provenance.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:701) うえ、削除 path も [同:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:758) と [同:780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:780) で変更集合へ入ります。この移行 commit 自体に Codex `role=author` が必要です。

### `check_docs` との整合

ここは依頼文の前提と実コードに差があります。実コードは `output/insights/**/*.md` を再帰走査していません。

- 対象族定義: [tools/check_docs.py:1227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_docs.py:1227)
- 実列挙は `INSIGHTS_DIR.glob("*.md")`: [同:1265](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_docs.py:1265)
- exact placeholder は [同:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_docs.py:110) の 3 語だけ。
- `insights-path:` scope は [同:1319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_docs.py:1319)。
- debt occurrence は [同:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_docs.py:1425) で固定。
- `verbatim` 名でも免除しないテスト [test_check_docs.py:3539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_docs.py:3539) は、top-level の `output/insights/new-verbatim.md` を対象にしており、nested directory の意味ではありません。

したがって新しい `verbatim/probe_split_window.md` は現行 placeholder guard の対象外です。仮に将来再帰化されても、逐語本文には `<反映>`、`<受入結果を反映>`、`<受入全走結果を反映>` がなく、`KNOWN_PLACEHOLDER_DEBTS` 追加も不要です。

親が docs として直す対象は次の 3 箇所だけです。

- [README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/README.md:29)
- [README.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/README.md:39)
- [package.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/package.md:38)

凍結記録である [docs/worklog.md:2049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/docs/worklog.md:2049)、[archive:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/docs/archive/worklog-phase3-0809-326.md:31)、[archive:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/docs/archive/worklog-phase3-0809-326.md:468) は誰も触りません。

## 7. 段 5 の所有ファイルと順序

段 5 実装子が触ってよいのは次の 4 path だけです。

- `tools/check_ai_provenance.py`
- `orchestrator/tests/test_check_ai_provenance.py`
- `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` の削除
- `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md` の追加

最後の `.md` は narrative docs ではなく、裁定済みの probe 実装面移行成果物としてのみ実装子の所有です。README、package、worklog、archive、spool、commit は実装子の権限外です。

依存順序は次です。

1. `MALFORMED_AI_AGENT`、kind 集合、note-required 集合を追加。
2. full-label anchored の kind 分類 helper と `_ledger_policy_is_visible()` を更新。
3. registry の note 必須検証を、kind／note の既存検査後へ追加。
4. ruling 定数を追加し、既存 7 件を保持したまま 23 件を登録。
5. literal 30 件、real history、empty registry の既存テストを更新。
6. adversarial・note 正負対・registered/unregistered・stale・受理集合不変テストを追加。
7. probe `.py` を `.md` fenced verbatim へ移行。
8. 親が README/package を更新し、実測・docs 検査・commit・commit 後 provenance 監査を担当。

## 総括

- 推奨実装順序
  - kind 定数・分類・stale 可視性 → registry note 強制 → ruling 定数・23 登録 → 既存／新規テスト → probe 逐語移行 → 親の docs・実測・commit。

- 親が段 4 で裁定すべき択一点
  - P1: **修正採用**。完全な `label` を含む prefix を専用 helper に局所化し、subject 注入と異種 base finding の test を必須化。`validate_message()` 構造変更は却下。
  - P2: **修正採用**。`not note.strip()` を用い、`:226` の kind 検査と既存 note 型・改行検査の後、registry 代入直前へ置く。
  - P3: **修正採用**。定数名・値は案どおり。ただし `_ledger_policy_is_visible()` の常時可視分岐追加を必須化。
  - P4: **採用**。日付 + `dev-wave-jobs/rulings-inbox/<filename>` を固定し、予測不能な worklog 番号を使わない。既存 7 件との表記差は許容。
  - P5: **修正採用**。上記 22 逐語 note を使い、`2c192953…` にも任意の説明 note を付ける。ただし `missing-codex-author` 全体を note 必須にはしない。
  - P6: **修正採用**。先例の構造を保ち、SHA は「元 `.py` bytes」の digest と明記。既存の repo 外 byte 同一控えを使い、新規実行可能体は作らない。

- 最も危険な落とし穴 3 件
  - 新 kind を集合へ足すだけで `_ledger_policy_is_visible()` を更新せず、stale を不正 kind と誤診断すること。
  - subject 内の marker を考慮せず substring 判定を使い、重複・none・reserved/model-none finding まで台帳 kind 化すること。
  - literal test と real/empty-registry control を件数だけ緩める、または probe 移行を docs 扱いして親が直接実装・凍結記録まで書き換えること。