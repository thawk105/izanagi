結論は **NO-GO**。必読 7 ファイルはすべて読了し、worktree 実値で検算した。書込み・pytest・変更後 checker の実行はしていない。

## 受理集合の差

履歴自体は各 SHA の後続 commit を任意に持てるため差集合は有限の「23 履歴」ではない。有限に数えられるのは **23 個の SHA/kind 抑止枠**である。

| 方向 | 数 | 変化 |
|---|---:|---|
| 広がる | 22 枠 | 登録 SHA で最初に一致する `malformed-ai-agent` finding が既知扱いになる |
| 広がる | 1 枠 | `2c192953…` の最初の `missing-codex-author` が既知扱いになる |
| 意図より広い | 最大 23 枠 | 元の finding 本文ではなく「同じ SHA・同じ kind」の別 finding でも枠を消費できる |
| 狭まる | 選択された各登録 SHA | 一致 kind が 0 件なら stale rc=2。ただし別の同 kind finding があれば stale を回避できる |
| 不変 | 登録外 SHA 全件 | `registry.get(audit.commit)` が `None` のため形式違反は残る |
| 不変 | 同一 commit の同 kind 2 件目以降 | 1 件目だけ抑止され、残りは finding に残る |
| 範囲依存 | 範囲外の登録 SHA | stale 対象外。範囲監査だけでは台帳全体を検査しない |

22 件はすべて同じ不正値だった。

```text
AI-Agent: product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator
```

1 行につき `model` と `role` の 2 フィールドが不適合だが、現 checker は 1 finding にまとめる。したがって実値は **形式 finding 22、フィールド不適合 44、missing author 1** である。

## 親実測・P1〜P6 の検算

- 親の保存実測は、[prov-baseline.txt:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/prov-baseline.txt:51) の `1947 件中 23 新規違反` と、[receipt.json:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/pegasus-dispatch/d01274fe82957dfd5e1349e31900b0ae/receipt.json:28) の `rc: 1` が整合する。
- 独立の read-only 検算では、policy commit を含む範囲は 1947 commit、23 SHA は全件範囲内。現関数による内訳も形式違反 22 + `2c192953…` 1 だった。ただし公式 full-history コマンドは今回再実行していない。
- `FROZEN_MANIFEST` と key-set は [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_frozen_artifacts.py:38) 以下の 23 path で、対象 insights package を含まない。
- probe と repo 外控えはともに 3648 bytes、SHA-256 は指定値 `0128696a…55d`、byte 同一。
- 総 registry 長を直接固定する assert は [test_check_ai_provenance.py:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1371) の 1 箇所だけ。`:1939` は選択した既存 7 SHA の監査件数で、総サイズ pin ではないが、30 件復元テストへ広げるなら更新対象。`:3517/:3546/:3586` の `7` は dispatch stub の戻り値で無関係。
- P1 は kind 誤分類を再現できなかったが、表示文字列の問題が残る（A-05）。
- P2/P4 は裁定との機械的結合として不十分（A-02）。
- P3 の定数名・値、P5 の SHA/path 分類、P6 の digest・移行先には実値不一致を見つけなかった。
- 「23 件登録後に rc=0」は未実測であり、現時点では断言できない（A-04）。

## A-01 — must-fix — 台帳は「その SHA のその finding」ではなく「その SHA の最初の同 kind finding」を洗浄する

**証拠**: [check_ai_provenance.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1027)

```python
spec_for_commit = registry.get(audit.commit)
if (
    spec_for_commit is not None
    and finding.ledger_kind == spec_for_commit.expected_finding_kind
):
    ...
    if audit.commit not in consumed_registry_entries:
        known_violations.append(spec_for_commit)
        consumed_registry_entries.add(audit.commit)
        continue
```

本文・不正 trailer 値・finding fingerprint の比較がない。一方、2 件目を残す性質は既存テストにも明記される。[test_check_ai_provenance.py:1671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1671)

```python
lambda *args, **kwargs: (["duplicate-kind", "duplicate-kind"], False),
...
assert audit.findings == ["duplicate-kind"]
```

**具体的な失敗シナリオ**: `f277efd4…` には妥当な Codex 行と不正な Claude 行がある。将来の checker 退行で元の Claude finding が消え、妥当な Codex 行を別理由で `malformed-ai-agent` と誤分類すると、その別 finding が登録枠を消費する。count は 1 なので stale にもならない。

同一 commit に形式違反行が 2 本ある場合は、現実装では最初だけが消え、2 本目は残る。この部分は fail-closed だが、「元 finding が別 finding へ置換された 1 件」の経路は塞がっていない。

**成果物影響**: 将来の本物の形式違反 1 件が既知 1 件として数えられ、履歴が rc=0 側へ広がる。台帳上は元違反が存続しているように見え、checker 退行も stale にならない。

**推奨対応**: malformed entry に、正規化した不正 trailer 値または安定 fingerprint を必須で持たせ、`SHA + kind + fingerprint` の完全一致でのみ抑止する。「元 finding 消失 + 別同 kind 出現」と「形式違反 2 行」の実結合テストを追加する。

## A-02 — must-fix — `note` と `ruling` の非空検査は、裁定済みであることも説明の意味も保証しない

**証拠**: [check_ai_provenance.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:231)

```python
if not isinstance(spec.ruling, str) or not spec.ruling.strip():
    raise RuntimeError(...)
...
if spec.note != "" and spec.note.splitlines() != [spec.note]:
    raise RuntimeError(...)
```

出力も [check_ai_provenance.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:250) のとおり `ruling` を含まない。

```python
f"sha={spec.commit} finding={spec.expected_finding_kind}"
...
line += f" note={spec.note}"
```

**具体的な失敗シナリオ**: 将来の SHA を `ruling="x"`、`note="\u200b"`（zero-width space）で登録する。提案中の `not spec.note.strip()`、既存の `splitlines()`、ruling 非空検査をすべて通る。`note="内容は正確"` のような根拠のない一文でも同じである。ANSI 制御文字や NUL を含む単一行も拒否されない。

この緩和が実際に防ぐのは、空文字・通常空白だけの note と改行注入だけである。

**成果物影響**: 将来の実違反を名目上の文字列だけで既知扱いにできる。stdout には例外の存在は出るが、どのユーザー裁定に束縛されたかを確認できず、「黙って緩む」のうち承認 provenance の経路は塞がらない。

**推奨対応**: 裁定参照を閉じた形式の incident ID/file 名にし、登録対象 fingerprint と組で固定する。note は構造化した `invalid=...; corrected=...; rationale=...` 等を要求し、制御文字・zero-width・過長文字列を拒否する。known 出力には escaped な ruling 参照も含める。

## A-03 — must-fix — stale は範囲内では機能するが、現 land 関門は履歴監査を一度も呼ばない

**証拠**: stale 対象は [check_ai_provenance.py:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1176) の選択範囲との積集合だけである。

```python
selected = set(commits)
stale_eligible_commits = selected.intersection(registry)
...
if ledger_audit.stale:
    ...
    raise RuntimeError(...)
```

範囲外 entry が rc=0 になる仕様は [test_check_ai_provenance.py:1783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1783) で固定されている。

現 land は [dev_wave_land.py:1391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/dev_wave_land.py:1391) の message-file 検査だけである。

```python
[sys.executable, str(checker), "--message-file", str(message_path)]
```

`_ledger_policy_is_visible()` は stale の有無ではなく reason 文言だけを選ぶ。malformed を常時可視へ加えること自体は退行を隠さない。`scope_epoch` と CAB policy も malformed base finding に影響しない。`2c192953…` は implementation epoch が見えない HEAD でも stale rc=2 となり、理由だけが `non-authoritative-invocation` になる。

**具体的な失敗シナリオ**: t682 を land しても、land preflight は新しい fold message だけを調べる。既存登録 finding の消失、同 kind への置換、incoming history の別違反は land 関門で監査されない。

**成果物影響**: checker は手動実行時にだけ効き、裁定済み F37 の end-to-end 受理集合は変わらない。brief は scope 外と明記しており、実装済みを装ってはいないが、並行 wave が差分ゼロのままなら機械関門は欠落したままになる。

**推奨対応**: `dev_wave_land.py` は本 wave で触らず、F37 peer wave の「既定 full-history 検査を自走し rc を直接判定する」実装を統合前の hard dependency にする。peer が実装しない場合は裁定パッケージへ戻す。

## A-04 — must-fix — 「23 件登録すれば rc=0」は新 commit 自身を含めて未証明

**証拠**: 削除 path も [check_ai_provenance.py:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:758) の `D` を含む filter で変更集合へ入る。

```python
"--diff-filter=ACMRDTUXB"
```

さらに [check_ai_provenance.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:701) では所在にかかわらず `.py` が実装面になる。

```python
if normalized.endswith(IMPLEMENTATION_SUFFIXES):
    return True
```

**具体的な失敗シナリオ**: probe `.py` の削除を含む実装 commit に Codex `role=author` が無い、または新 helper 自身の commit message が形式違反になる。既存 23 件がすべて既知になっても、新 SHA の finding が残る。HEAD が増えるため親の 1947 という件数もそのままではない。

**成果物影響**: 台帳は 30 件になっても、新規 finding 数が 0 とは限らず、rc=0 を保証できない。

**推奨対応**: 段 8 の受理 oracle を「commit 後の既定 full-history 実行で新規 finding 0、known 30、stale 0、実装 commit 自身も監査済み」と明記する。実行は規定の runner に任せ、親は実装面を書かない。

## A-05 — nit — full-label prefix は kind 誤爆しないが、外部 subject を無加工で診断へ流す

**証拠**: [check_ai_provenance.py:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:946)

```python
subject = _git("show", "-s", "--format=%s", commit).strip()
label = f"{commit[:12]} {subject}"
```

finding は [check_ai_provenance.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:627) で同じ `label` から作られる。

**具体的な失敗シナリオ**: 純粋な文字列評価では、subject 相当部に marker、改行、tab、全角空白、NUL、10 万文字を置いても、提案 prefix は malformed finding だけを分類した。duplicate・none 混在・reserved product・model none は誤分類しなかった。label を不正値内にも置けば finding 中に 2 回出現させられるが、prefix 判定は変わらない。実 Git commit で自己の 12 桁 SHA を埋め込む構成は未実測。

問題は分類ではなく、制御文字・極端な長さが stderr やログ parser を汚染し得る点である。

**成果物影響**: 現確認範囲では受理集合は変わらない。診断境界だけのため nit。

**推奨対応**: kind は可能なら生成時の構造値として渡す。少なくとも表示用 subject は制御文字を escape し、長さを制限する。現プランの full-label anchor 自体は維持可能。

## A-06 — nit — probe 逐語には trailer 様行はないが、指示形のデータが含まれる

**証拠**: [probe_split_window.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py:4)

```text
live directory には一切書かない。repo の record 1 を temp へ copy し、
```

同 package の [README.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/README.md:7) にも `これを越える引用を禁じる`、[README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/README.md:29) に `証拠としては引かないこと` がある。いずれも指示ではなくデータとして扱った。

**具体的な失敗シナリオ**: 将来、逐語 Markdown を信頼済み命令として取り込む AI が docstring に従う可能性はある。一方、実ファイルには行頭 `AI-Agent:`、`WAIVER:`、`CORRECTION:`、`Co-Authored-By:` はなく、現 checker はファイル本文も読まないため provenance 誤爆はない。

**成果物影響**: 現 gate の台帳・受理集合への影響なし。将来の文書 ingestion 境界だけのため nit。

**推奨対応**: fenced block 外に「以下は未信頼の逐語データであり命令ではない」と明記し、README/package の path 参照を `.md` へ更新する。fence 内 bytes は変更しない。

## 総括

- must-fix は、SHA+kind だけの広すぎる照合と、名目だけの note/ruling 検査。
- stale は選択範囲では働くが、別同 kind finding に置換されると退行を見逃す。
- F37 は本 wave が未実装を明記しているため、peer wave の成功を統合条件にする必要がある。
- 変更後 rc=0 は未実測であり、新実装 commit 自身を含む full-history oracle が必要。

**NO-GO — A-01〜A-04 を段 4 で閉じるまで land 不可。**