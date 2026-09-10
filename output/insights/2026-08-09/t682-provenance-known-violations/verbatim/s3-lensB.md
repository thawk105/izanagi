必読 7 ファイルは読了しました。worktree は clean です。read-only のため pytest・checker 本走は未実測で、以下は静的な mutation 論証です。実際の緑・赤は主張しません。

## 消費者の全列挙

`rg --hidden --no-ignore --glob '!.git/**'` で repo 全体を検索した結果、live code の consumer は次です。

- 台帳検証: `tools/check_ai_provenance.py:194-247`
- kind と SHA の照合・抑止: `tools/check_ai_provenance.py:1027-1038`
- stale の policy 分岐: `tools/check_ai_provenance.py:1049-1067`
- stale 適用: `tools/check_ai_provenance.py:1176-1199`
- stdout と rc: `tools/check_ai_provenance.py:2097-2141`
- checker 呼出しだけを行う wrapper: `tools/task_run_check.py:15-20`、`tools/pegasus/dispatch_compute.py:66-72`、`tools/dev_wave_land.py:1387-1404`
- hook は path/basename の制限だけ: `hooks/guard_bash.py:189-194`、`348-362`
- docs/receipt の kind parser、JSON serializer、他の台帳 import は見つからなかった。

`_ledger_policy_is_visible()` 以外の live な kind whitelist は確認できませんでした。`docs/decisions.md` や `output/insights` の該当文字列は記録・逐語であり、consumer ではありません。

## 新規テスト 6 本の mutation 追跡

| テスト | 検出できる変異 | 取り逃がす変異 |
|---|---|---|
| note 必須 | required-note 検査の削除、空白 note の許可 | note の内容の正確性 |
| anchored kind | substring 判定、duplicate/none/reserved の誤分類 | helper を production 経路へ接続し忘れる変異 |
| registered malformed | exact SHA/kind/output の抑止不整合 | synthetic の `NormalFinding` を mock して実分類を迂回 |
| unregistered malformed | production registry を使う場合の広すぎる抑止 | registry を空/別値へ monkeypatch した場合の production registry drift |
| stale | `_ledger_policy_is_visible()` の malformed 分岐欠落 | note を渡さず、note 検査で先に止まる実装 |
| acceptance language | 列挙済み invalid literal の受理 | 列挙外の新しい syntax を受理する変異 |

### B-01 — must-fix

**主張:** `test_ai_agent_acceptance_language_is_unchanged` は受理集合全体の不変性を保証しない。

**証拠**

`tools/check_ai_provenance.py:49-50,70-76`:

```python
ROLES = ("author", "reviewer", "researcher", "manager", "integrator")
IDENT = r"[a-z0-9][a-z0-9._-]*"

AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{IDENT}); "
    rf"model=(?P<model>{IDENT}); "
    rf"reasoning=(?P<reasoning>{IDENT}); "
    rf"role=(?P<role>{'|'.join(ROLES)})"
    rf"(?:; scope=(?P<scope>{IDENT}))?$"
)
```

`tools/check_ai_provenance.py:624-629`:

```python
match = AGENT_VALUE.fullmatch(value)
if not match:
    findings.append(
        f"{label}: AI-Agent の形式違反: {value!r} — "
        "product/model/reasoning/role (任意で scope) の順と許可値を確認する"
    )
```

プランは `s2b-plan.md:274-280` で有限個の valid/invalid 例を固定しています。

**具体的な失敗シナリオ**

次の一行変異は `ROLES` と `IDENT` を変更しません。

```python
rf"(?:; scope=(?P<scope>{IDENT}))?(?:; extra={IDENT})?$"
```

`extra=x` という新しい形式は受理されますが、列挙済みの全例は従来どおり同じ結果になります。定数比較と有限例の `fullmatch()`、`validate_message()` の両方を通過します。

**成果物影響**

受理集合が拡張され、従来なら形式違反だった trailer が `MALFORMED_AI_AGENT` finding になりません。未登録の新規違反が消えます。

**推奨対応**

`extra=`、末尾 token、順序違い、未知フィールドを明示的な reject matrix に追加し、直接の `AGENT_VALUE.fullmatch()` と production の `validate_message()` の双方で拒否を固定してください。`ROLES` / `IDENT` の拡張は不要です。

### B-02 — must-fix

**主張:** malformed stale テストは、note を渡さないと `_ledger_policy_is_visible()` を一度も検査しない。

**証拠**

プランの stale テスト案は `s2b-plan.md:269-272` で note を指定していません。

既存 fixture は `orchestrator/tests/test_check_ai_provenance.py:266-274` のとおりです。

```python
def _known_spec(
    commit: str,
    finding_kind: str = "missing-ai-agent",
) -> provenance.KnownViolationSpec:
    return provenance.KnownViolationSpec(
        commit=commit,
        expected_finding_kind=finding_kind,
        ruling="worklog(284) 2026-08-07 /rulings",
    )
```

一方、プランの note-required 検査は `s2b-plan.md:104-115` で、malformed kind の空 note を拒否します。

**具体的な失敗シナリオ**

テストが `_known_spec(clean, "malformed-ai-agent")` を使うと、stale 判定前に empty-required-note の rc=2 になります。期待する

```text
finding=malformed-ai-agent reason=expected-finding-missing checker-regression-suspected
```

には到達しません。その結果、`_ledger_policy_is_visible()` の malformed 分岐を削除しても検出できません。

**成果物影響**

malformed entry が stale のとき、正しい `expected-finding-missing` ではなく registry schema error になり、checker regression と台帳破損を区別できません。

**推奨対応**

stale 用の `KnownViolationSpec` に非空・単一行 note を明示し、`tools/check_ai_provenance.py:1184-1199` の stale 診断を実経路で固定してください。

### B-03 — must-fix

**主張:** synthetic registered テスト単体では実 repo の 22 件を保証しない。production registry を monkeypatch した unregistered テストも閉集合性を証明しない。

**証拠**

プランの synthetic 案は `s2b-plan.md:257-267` です。

現行テストも `orchestrator/tests/test_check_ai_provenance.py:1421-1428` で registry を置換しています。

```python
monkeypatch.setattr(
    provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(known),),
)
```

抑止は `tools/check_ai_provenance.py:1027-1038` の実 registry と exact SHA/kind に依存します。

**具体的な失敗シナリオ**

`_normal_commit_audit()` を mock して malformed `NormalFinding` を返す形なら、production の分類 helper を接続し忘れても synthetic テストは通る構造になります。また、unregistered テストが registry を `()` や一件の synthetic spec に置換したままだと、実際の 30-entry registry の誤登録・広すぎる導出を検査しません。

**成果物影響**

22 件の実 finding が `ledger_kind=None` のまま残り rc=1 になるか、逆に列挙外 SHA が known 扱いされます。

**推奨対応**

- registered テストは実 `_normal_commit_audit()` と `main()` を通す。
- unregistered テストの少なくとも一例は production `KNOWN_PROVENANCE_VIOLATIONS` を変更せず、30 件の集合外 SHA を使う。
- `s2b-plan.md:220-226` の empty-registry real 30 件 exact finding list を必須の独立 oracle として残す。

### B-04 — nit

**主張:** 「台帳サイズに依存する assert は `:1371` だけ」というプランの説明は不正確。

**証拠**

プランの主張は `s2b-plan.md:228-238`。

実際には `orchestrator/tests/test_check_ai_provenance.py:1937-1945` にも台帳依存があります。

```python
production = provenance._audit_history(commits)
assert production.findings == []
assert len(production.known_violations) == 7
...
assert len(audit.findings) == 7
```

一方、`orchestrator/tests/test_check_ai_provenance.py:3517,3546,3586` の `7` は、

```python
return 7
```

および dispatch mock の return code であり、台帳件数ではありません。

**具体的な失敗シナリオ**

`:1371` だけを 30 に更新し、`:1925` の commit 入力や `:1939` の期待値を更新し忘れると、既存 7 件だけでテストが成立し、新規 23 件の検出・抑止を検査しません。

**成果物影響**

台帳は 30 件でも、real/empty-registry control は 7 件のままになります。dispatch の `7` を誤って 30 に変更すると、別の site/dispatch 契約を壊します。

**推奨対応**

`:1371` は総台帳長、`:1939` と `:1943` は選択 commit の ledger control、`:3517/:3546/:3586` は child rc と分類して監査表を修正してください。

### B-05 — must-fix

**主張:** 新しい nested `.md` は現行 `check_docs` の placeholder 検査対象外である。

**証拠**

`tools/check_docs.py:1227-1230`:

```python
families = (
    (ARCHIVE_DIR, "docs/archive", "worklog-*.md"),
    (INSIGHTS_DIR, "output/insights", "*.md"),
)
```

`tools/check_docs.py:1265`:

```python
members = sorted(directory.glob(pattern))
```

`glob("*.md")` は `output/insights/verbatim/*.md` を再帰列挙しません。

**具体的な失敗シナリオ**

`verbatim/probe_split_window.md` や nested `README.md` に `<反映>` が混入しても、現行 placeholder guard は見ません。現在の probe に hit がないこととは別問題です。

**成果物影響**

新 `.md` の docs debt、placeholder、誤った逐語内容が `check_docs` の rc に反映されません。親が更新する README/package も同じ nested directory のため、同じ死角に入ります。

**推奨対応**

nested verbatim を再帰走査する専用 guard、または対象を明示する別検査とテストを追加してください。対応しない場合は「check_docs が検査する」と説明せず、対象外であることを成果物に明記してください。

### B-06 — nit

**主張:** probe の `.py`→`.md` は実行能力を失わせる処置ではなく、主に path-based provenance 判定を変える形式移行である。

**証拠**

probe は `output/.../probe_split_window.py:14-17` で repo を import path に追加し、`probe_split_window.py:45-50` などで実際の Python API を呼びます。

```python
REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "orchestrator"))
from campaign import env_contract as contract
from campaign import env_contract_activation as activation
```

`tools/check_ai_provenance.py:701-714` は `.py` を suffix で実装面とし、`.md` は suffix に含めません。

先例自身も `firing-evidence-script.md:3-9` で欠陥品であること、外部の executable copy を記録しています。

**具体的な失敗シナリオ**

fenced block を一度コピーして `.py` に戻せば実行できます。移行で変わるのは checker の path 分類と tracked executable copy の有無であり、コードの安全性や probe の証拠能力ではありません。

**成果物影響**

新しい `.md` は実装面 finding を生まなくなりますが、probe が production 経路を検証する証拠になるわけではありません。実際、`README.md:29-42` は probe を証拠として引かないよう明記しています。

**推奨対応**

移行を「履歴 artifact の実装面是正」と限定し、SHA・fence 内 bytes・非証拠の説明を固定してください。実行が必要な場合だけ、承認済みの repo 外 copy と hash 照合を使ってください。

### B-07 — must-fix

**主張:** 22 件の note は機械的な nonblank 条件は満たすが、「内容が正確で綴りだけの誤り」の 1 件ずつの説明としては情報量が不足する。

**証拠**

裁定は `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-09-t139-r4-probe-provenance-format-violation.md:12-15` で、

```text
追加 kind の entry は note を必須とし、「内容は正確で綴りだけの誤り」である理由を
1 件ずつ書く。
```

プランの note は `s2b-plan.md:148-171` でほぼ共通して、

```text
Claude 親の関与自体は正確で綴りだけの誤り；
model=claude-opus-5[1m] は IDENT の角括弧不許可、
role=orchestrator は ROLES の許可値外；
変更 path 種別=...
```

です。`tools/check_ai_provenance.py:250-257` は note をそのまま stdout に出すだけです。

**具体的な失敗シナリオ**

SHA と path category だけを差し替えた note を誤った commit に付けても、registry 検査は通ります。人間が後から見ても、その commit の実 trailer、実際の combined path、他の finding の有無を確認できません。

**成果物影響**

rc は変わりませんが、stdout の唯一の説明 field が copy-paste になり、22 件の裁定参照の監査価値が下がります。

**推奨対応**

各行に、当該 commit で観測した trailer literal、`_commit_paths()` に基づく path/merge 結果、内容が正確と判断する commit 固有の事実を入れてください。全件で literal が同じなら、その事実を各行で明示し、差分が path 以外にないことを示してください。

### B-08 — must-fix

**主張:** FROZEN_MANIFEST 非包含・byte 同一・placeholder 無しの実測から、4 path の所有境界や全 freeze 境界までは導けない。

**証拠**

`orchestrator/tests/test_frozen_artifacts.py:38-85` の manifest に対象 package はありません。また `:87-89` 自身が keyset を、

```text
暫定・独立 key-set pin
...
独立改竄境界でも、恒久 freeze-family membership でもない
```

と限定しています。

プランの 4 path は `s2b-plan.md:324-333` の作業規約であり、実 diff から観測した事実ではありません。

**具体的な失敗シナリオ**

親が README/package 以外を編集する、または implementation child が別 path を触ると、現在の provenance checker はその所有者境界を検査しません。worktree は現時点で clean なので、この境界は未実測です。

**成果物影響**

親の実装面直接編集や凍結記録の変更が、4 path assertion だけでは検出されません。FROZEN_MANIFEST 外であることも「他の pin がない」証明にはなりません。

**推奨対応**

実装後の diff で child 4 path と親 docs path を別々に exact allowlist 照合し、freeze inventory は「この manifest にない」という限定表現にしてください。

### B-09 — must-fix

**主張:** 「23 件を登録すれば checker は rc=0」は無条件には成立しない。

**証拠**

現在の `_normal_commit_audit()` は `tools/check_ai_provenance.py:963-970` で missing trailer にしか kind を付けません。

```python
MISSING_AI_AGENT
if finding == f"{label}: AI-Agent trailer がない"
else None
```

抑止は `tools/check_ai_provenance.py:1027-1038` で exact SHA と exact kind の両方が必要です。stale は `:1049-1067` の policy 分岐を通り、history main は `:2073-2082` と `:2097-2141` で rc を決めます。

**具体的な失敗シナリオ**

- helper が malformed finding に kind を付け忘れると、23 entry があっても finding は残り、静的には rc=1 経路です。
- `_ledger_policy_is_visible()` に malformed 分岐がないと、stale entry は invalid kind の実行不能扱いになり、静的には rc=2 経路です。
- 同一 commit に別の finding があれば、`_known_violation_audit()` はそれを残します。

**成果物影響**

`KNOWN_PROVENANCE_VIOLATIONS` の件数だけ増えても、`known_violations` の件数、未抑止 finding、stale 診断は別の値になり得ます。

**推奨対応**

結論を「23 件の exact classification、note 検査、policy 分岐、他 finding の不存在がすべて成立した場合に限り rc=0」と限定してください。実装後は real 30 件、empty registry、stale、unregistered の各経路を通す必要があります。

### B-10 — nit

**主張:** 30 entry の literal 固定は保守負担ではあるが、この台帳では無意味な赤ではなく正しい固定である。

**証拠**

プランは `s2b-plan.md:193-200` で SHA・kind・ruling・note・順序を literal 固定し、現行テストも `orchestrator/tests/test_check_ai_provenance.py:1371-1382` で件数と完全 tuple を固定しています。

**具体的な失敗シナリオ**

裁定済み entry の追加・削除・note・ruling・順序変更を production だけ変更すると、literal test が失敗します。ただしそれは台帳の意図的変更を見逃さないための赤です。

**成果物影響**

test-local の記述量と merge conflict は増えますが、registry の closed set は保持されます。

**推奨対応**

expected を production/TSV から生成せず、旧 7 件・T139 22 件・T659 1 件の literal group に分け、最後に順序付き tuple として比較してください。literal 固定自体は維持すべきです。

**GO / NO-GO: NO-GO。**

## 総括

- B-01: acceptance language test は列挙外の parser 拡張を取り逃がす。
- B-02/B-03: malformed stale と production registry の実経路を明示的に固定する必要がある。
- B-05/B-07: nested `.md` の検査死角と、22 note の説明不足が残る。
- B-08/B-09: 親の所有境界と「登録すれば rc=0」という一般化は未証明。
- pytest・全履歴 checker は read-only のため未実測。