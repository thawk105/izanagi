| 所見 | 判定 | 独立根拠 |
|---|---|---|
| C-01 | **closed** | production は `finding value` を出力し、テストも selector と診断名を分離して同じ逐語を期待する。[production:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:568)、[test:1726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1726)、[test:1802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1802)。元の診断 oracle 不一致は静的に消滅している。 |
| D-01 | **closed** | C-01 と同根。production の逐語 `"prohibited character in finding value"` とテストの `expected_diagnostic` が一致し、旧 `"in value"` 期待は残っていない。[production:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:570)、[test:1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1742)。 |
| C-02 | **partial** | `Cf/Zl/Zp` と指摘された具体例は塞がれたが、「視覚上空の required note が通る」という根因は `Mn`・`Lo` の不可視文字へ移っている。[production:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:143)、[production:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:468)。 |

pytest は実行しておらず、その成否を上記判定の根拠にしていない。

### 回帰照合

- 読み取り専用の局所走査（Python 3.10.12、Unicode DB 13.0.0）では、登録済み 30 entry の note/value 60 field に `Cc/Cf/Zl/Zp` または明示 zero-width の該当は 0。追加 23 entry の 46 field も 0 だった。
- 既存 7 entry は source 上の commit/kind/ruling/note が不変。[tools/check_ai_provenance.py:175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:175)〜213。追加 field は既定値 `""` で、note の新検査は `MALFORMED_AI_AGENT` 限定なので既存挙動は変わらない。[同:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:158)、[同:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:561)。
- `2c192953…` は `MISSING_CODEX_AUTHOR`、value は既定の空文字で、note 検査の対象外。[同:291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:291)。note 自体にも新拒否集合の文字はなかった。
- `ROLES/IDENT/AGENT_VALUE` の production 定義には差分がなく、受理集合を拡張する変更はない。[同:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:50)。
- probe は旧 `.py`、repo 外控え、`.md` fence がすべて 3,648 bytes、SHA-256 `0128696a…55d` で byte 同一だった。証拠能力を与えない限定も残る。[probe_split_window.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md:3)、[同:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md:8)。

## F-01

- **重大度:** must-fix
- **主張:** `Cf/Zl/Zp` の追加後も、視覚上空の文字だけで required note を満たせる。C-02 の根因は閉じていない。
- **証拠:** 拒否条件は逐語で `unicodedata.category(char) in _PROHIBITED_REGISTRY_CATEGORIES`、集合は `{"Cc", "Cf", "Zl", "Zp"}`。[production:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:143)、[production:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:468)。必須判定は逐語で `and not spec.note.strip()`。[同:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:552)。局所再現では、sole note が U+034F COMBINING GRAPHEME JOINER (`Mn`)、U+FE0F VARIATION SELECTOR-16 (`Mn`)、U+3164 HANGUL FILLER (`Lo`) の各場合に、`_known_violation_registry()` が RuntimeError なしで registry map を生成した。現行負例表にもこの 3 文字はない。[test:1726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1726)。
- **失敗シナリオ:** malformed entry を `note="\u034f"` と正しい `expected_finding_value` で登録する。note 必須検査と文字検査を通り、finding は known violation として抑止される一方、公開行は `note=` の後が視覚上空になる。[production:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:582)、[production:1360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1360)。
- **成果物影響:** 台帳の受理集合が「説明 note のない malformed entry」を受け入れ、その finding を新規違反から既知違反へ移して抑止できる。
- **推奨対応:** category blacklist の追加だけでなく、note に少なくとも一つの可視・説明用文字を要求する正条件を pin する。U+034F、U+FE0F、U+3164 の sole-note 負例と、現行 30 note の正例を固定する。

## N-01

- **重大度:** nit
- **主張:** `Cf` 全拒否は、将来正当に使う可能性がある bidi 制御まで一括拒否する。
- **証拠:** [production:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:143) の `"Cf"`。現環境では U+061C ARABIC LETTER MARK、U+2066 LEFT-TO-RIGHT ISOLATE、U+2069 POP DIRECTIONAL ISOLATE がいずれも `Cf` で拒否対象だった。
- **失敗シナリオ:** 将来、混在方向テキストを明瞭に表示する note、または bidi isolate を含む実際の malformed trailer 値を逐語登録できない。
- **成果物影響:** 現行 30 entry は不変だが、将来の台帳受理集合は必要な bidi 表現まで拒否する。
- **推奨対応:** 本 wave の land 阻止理由にはしない。実需要が生じた場合は、`Cf` 全体ではなく spoofing/default-ignorable の固定集合または escaped 表現へ狭める。

## N-02

- **重大度:** nit
- **主張:** 受理集合が Python 内蔵 Unicode DB の版に暗黙依存する。
- **証拠:** `import unicodedata` と `unicodedata.category(char)` を使う一方、`unicodedata.unidata_version` の pin はない。[production:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:23)、[同:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:471)。今回の局所走査環境は Unicode DB 13.0.0。
- **失敗シナリオ:** interpreter 更新で従来 `Cn` だった文字が `Cf` 等として新規割当てされると、同じ registry bytes の受否が変わる。
- **成果物影響:** 現行 30 entry は影響なし。将来、同一台帳の受理集合が実行環境によって変わりうる。
- **推奨対応:** 現行 scope では nit。決定的契約が必要になった時点で Unicode DB 版または明示 code-point 集合を pin する。

## 総括

C-01 / D-01 の診断 oracle 不一致は静的に閉じている。  
登録済み 30 entry、既存 7 entry、`2c192953…`、probe 逐語移行に fix 起因の回帰は認めない。  
ただし C-02 の「名目 note」根因は `Mn/Lo` の不可視文字へ残っており、scope 内の note 必須保証を破る。  
F37 関門と `docs/dev-wave/` は評価・阻止理由に含めていない。

**NO-GO — F-01 により、視覚上空の sole-note を拒否できるまで land 不可。**