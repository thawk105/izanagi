NO-GO。裁定内容と 23 件の登録・probe 移行は静的に一致しているが、land 前に 2 件の must-fix がある。

## 所見

### C-01 — must-fix — 新設テストの value 診断 oracle が production の、より具体的な文言と不一致

- 主張: production は gate を発火させて `finding value` を一意に示している。新設テスト側だけが `value` を期待するため、親実測の 6 failed を生んでいる。
- 証拠:
  - production: [tools/check_ai_provenance.py:567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:567)  
    `known provenance violation registry has prohibited character in finding value:`
  - test: [test_check_ai_provenance.py:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1776)  
    `assert f"prohibited character in {field}" in captured.err`
  - `field="value"` は [同ファイル:1735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1735) 以下の 6 parameter。
- 具体的な失敗シナリオ: 親実測どおり、value に NUL・U+001F・U+200B/U+200C/U+200D/U+FEFF を入れる 6 case は `main()==2` まで到達するが、診断 substring assert だけが不一致になる。
- 成果物影響: 台帳値や抑止集合自体は変わらないが、受入結果が 6 failed / 261 passed のままなので段 6/land の受理条件を満たせず、30 件台帳を監査済み成果として land できない。
- 推奨対応: 案 (a)。production は変更せず、テストの期待診断を note=`note`、value=`finding value` に分ける。例えば selector と診断名を別 parameter にする。案 (b) の `in value` は field の特定能力を弱めるため不採用。

### C-02 — must-fix — Unicode format 文字で「必須 note」を名目化できる

- 主張: helper は `Cc` と 4 文字だけを拒否するため、U+00AD などの `Cf` だけからなる、視覚上空に近い required note が registry を通る。
- 証拠:
  - 対象集合は [tools/check_ai_provenance.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:142) の `U+200B/U+200C/U+200D/U+FEFF`。
  - helper は [同ファイル:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:467) の  
    `char in _ZERO_WIDTH_REGISTRY_CHARACTERS or unicodedata.category(char) == "Cc"`。
  - required 判定は [同ファイル:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:551) の `not spec.note.strip()`。
- 具体的な失敗シナリオ（静的）: `note="\u00ad"` は `strip()` 後も非空、category は `Cf`、指定 4 文字にも含まれないため malformed entry の required note を満たす。U+2060 も同様。U+2028/U+2029 は note では既存 `splitlines()` に止められるが、`expected_finding_value` では通る。
- 成果物影響: registry の受理集合が「人間が読める非空一行 note」より広い。同 SHA・kind・値が一致すれば、視覚上空または表示順を操作する note を伴う finding が known violation として抑止され、公開台帳の説明値が誤認可能になる。現行 23 件の値は変わらない。
- 推奨対応: `Cc` に加えて少なくとも `Cf`, `Zl`, `Zp` を拒否し、note/value 両方へ U+00AD・U+2060・U+2028・U+2029 の負例を追加する。tab・LF・DEL も境界例として固定する。

## 裁定 §2.1 の 8 項目

| # | 静的照合 |
|---|---|
| 1 | 一致。`MALFORMED_AI_AGENT`、3-kind 集合、note-required 集合は [tools/check_ai_provenance.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:133)。 |
| 2 | 一致。`expected_finding_value: str = ""` は [同ファイル:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:145)。 |
| 3 | 裁定が明記した型・kind/value 対応・note 必須・Cc＋指定 4 zero-width は [同ファイル:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:530) 以下に実装。既存 note 改行検査の後、挿入直前。強度上の穴は C-02。 |
| 4 | 一致。完全な `label` を含む prefix 分類は [同ファイル:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1261)、接続は [同ファイル:1297](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1297)。 |
| 5 | 一致。非空 value の literal prefix pin は [同ファイル:1360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1360)。空なら従来条件だけ。 |
| 6 | 一致。malformed の常時可視化は [同ファイル:1396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1396)。 |
| 7 | 一致。ruling 2 本は [同ファイル:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:161)。worklog 番号なし。 |
| 8 | 一致。既存 7 件は [同ファイル:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:173)〜212、新規は 213 以降。HEAD と worktree の既存 7 `KnownViolationSpec` source segment は 7/7 byte-for-byte 同一だった。 |

欠落・裁定外の production 実装は C-02 の強化余地を除き見つからなかった。

## 裁定 §2.2 — 更新 3 + 新設 8

更新 3 件はすべて存在する。

| 更新 | 証拠 |
|---|---|
| literal 30 件・全 field・順序・kind 集合 pin | [test_check_ai_provenance.py:1328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1328) |
| real commit findings を 30 SHA へ拡張 | [同ファイル:1406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1406) |
| empty registry の exact 30 finding・6/2/22 内訳 | [同ファイル:2361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2361) |

新設 8 件もすべて存在する。

| 新設 | 証拠・判定 |
|---|---|
| note 必須の正負対 | [同ファイル:1675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1675) |
| note/value 制御・zero-width 拒否 | [同ファイル:1743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1743)。診断 oracle は C-01。 |
| value 契約と同 SHA/kind・別値非抑止 | [同ファイル:1814](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1814) |
| full-label anchored 分類 | [同ファイル:1899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1899) |
| 登録 malformed の production 経路 | [同ファイル:1912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1912) |
| production registry 非差替えの未登録 rc=1 | [同ファイル:1949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1949) |
| malformed stale rc=2 | [同ファイル:1971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:1971) |
| 受理集合不変 reject matrix＋全 5 role 正例 | [同ファイル:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/orchestrator/tests/test_check_ai_provenance.py:2008) |

AST 差分では、削除された test 名は `seven→thirty` の 2 rename だけ。共有 test の変更は `_known_spec` と real-commit 更新だけで、新設は rename を除いて正確に 8 件だった。

## 23 entry の一件ずつ照合

TSV 順、full SHA、重複なし、kind/value を構造比較した。22 件はすべて malformed＋指定値、`2c1929...` だけ missing-codex-author＋空値。

| # | 登録 | path-kinds / note |
|---:|---|---|
| 1 | [`f277efd4…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:213) | [実装7＋md2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:1) — note 一致 |
| 2 | [`74b50196…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:224) | [merge、2 parents、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:12) — 一致 |
| 3 | [`7ec08816…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:235) | [test/probe/PBS/契約＋docs](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:15) — 一致 |
| 4 | [`1d099404…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:246) | [merge、2 parents、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:24) — 一致 |
| 5 | [`f1406c22…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:257) | [test/probe/shell](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:27) — 一致 |
| 6 | [`a567eb68…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:268) | [mutation-spec](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:32) — 一致 |
| 7 | [`ff264975…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:279) | [mutation-spec](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:35) — 一致 |
| 8 | [`2c192953…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:290) | [Python probe 1＋md9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:38) — kind/value/note 一致 |
| 9 | [`9af3e7a0…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:299) | [mutation-spec](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:50) — 一致 |
| 10 | [`6fa5bde0…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:310) | [mutation-ledger](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:53) — 一致 |
| 11 | [`2b3d06cb…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:321) | [submission receipt md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:56) — 一致 |
| 12 | [`30719e51…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:332) | [submission receipt md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:59) — 一致 |
| 13 | [`1fa2b75b…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:343) | [test/probe＋実測成果物](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:62) — 一致 |
| 14 | [`622bd786…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:354) | [実測成果物＋md4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:76) — 追補A/package/receipt note 一致 |
| 15 | [`c75fde90…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:365) | [merge、combined=docs/pegasus-runbook.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:90) — 一致 |
| 16 | [`c55ace29…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:376) | [worklog fragment](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:93) — 一致 |
| 17 | [`edf74c94…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:387) | [merge、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:96) — 一致 |
| 18 | [`7e3cc116…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:398) | [merge、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:99) — 一致 |
| 19 | [`66769067…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:409) | [merge、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:102) — 一致 |
| 20 | [`1f884f6f…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:420) | [worklog fragment](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:105) — 一致 |
| 21 | [`aaffa644…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:431) | [merge、combinedなし](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:108) — 一致 |
| 22 | [`6f5411ce…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:442) | [worklog fragment](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:111) — 一致 |
| 23 | [`797db5de…`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:453) | [worklog fragment](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/path-kinds.txt:114) — 一致 |

path 種別を取り違えた note はない。merge 7 件はすべて実際に 2 parents で、combined path は `c75fde...` の runbook 1 件だけだった。

## Reward hack・値 pin

Reward hack は静的差分から見つからなかった。

- `ROLES`、`IDENT`、`AGENT_VALUE`、`ForwardCorrectionSpec` は HEAD と AST 同一。[production:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:50)
- skip・xfail の追加なし。既存テスト削除はなく、2 件の名称変更は裁定どおり `seven→thirty`。
- production に `try/except` の追加なし。新しい `return` は分類 helper 内だけで、監査の早期素通り経路ではない。
- 検査順は、既存 note 改行検査の後に新条件を追加しただけ。弱い分岐の前倒しなし。
- empty-registry control は exact 30 finding を固定しており、抑止集合の恒真化もしていない。

値 pin は有効である。

- 非空 value は同 SHA・同 kind に加えて [production:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:1363) の prefix を要求するため、別値 finding は `findings` に残り、entry は stale になる。
- 空 value は `not spec.expected_finding_value` で従来の SHA＋kind 条件へ戻る。既存 7 件は source segment も逐語不変。
- 22 件の実値の `repr()` は  
  `'product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator'`。`[` と `]` は regex に渡されず、literal `startswith()` なので問題ない。
- 値に `'` がある場合、例 `"bad'value"` の `repr()` は `"bad'value"` と double quote を選ぶ。しかし finding 生成側も matcher 側も同じ `repr()` を使うため一致する。両 quote や backslash も同じ deterministic escape になる。
- closing quote 後に ` — ` まで prefix に含めるため、期待値を単なる先頭部分として持つ別値も一致しない。

## 文字検査の適用範囲

| 文字 | malformed note | expected value |
|---|---|---|
| tab、LF、DEL | `Cc` で拒否。LF は note の既存改行検査でも拒否 | `Cc` で拒否 |
| U+200B〜U+200D、U+FEFF | 明示集合で拒否 | 明示集合で拒否 |
| U+2028/U+2029 | `splitlines()` が note を拒否 | 現状は許可 — C-02 |
| U+00AD、U+2060 等 `Cf` | 現状は許可 — C-02 | 現状は許可 — C-02 |

`MISSING_CODEX_AUTHOR` の note には helper は効かない。[production:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/tools/check_ai_provenance.py:559) が `_NOTE_REQUIRED_FINDING_KINDS` に限定しているためで、[裁定 §2.1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t682-provenance-known-violations/s4-adjudication.md:40) の「必須 note」限定とは一致する。`2c1929...` の現行 note 自体には問題文字はない。

## Probe 移行

静的・byte 比較はすべて一致した。

- 元 path、digest の対象限定、外部控えは [probe_split_window.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md:3)〜10。
- B-06 限定「証拠能力を与えない」「既存テストより弱い」「裁定で証拠外」は [同ファイル:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t682-provenance-known-violations/output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.md:8)。
- HEAD の元 `.py`、repo 外控え、fence 内 82 行はすべて 3,648 bytes、SHA-256 は指定の `0128696a...55d`、byte-for-byte 一致。末尾 LF も一致。
- `.py` は削除状態、`.md` は新設状態。
- `verbatim/README.md` は存在せず、新設されていない。

テストは本レビューでは再実行していない。実測として扱ったのは、親提示の 6 failed / 261 passed と、その 6 件すべてで `main()==2` が成立している事実だけである。

## 総括

- C-01: production 診断を維持し、新設テストを `finding value` に合わせる。
- C-02: `Cf/Zl/Zp` を拒否して、視覚上空の required note と Unicode separator value を塞ぐ。

NO-GO — C-01 と C-02 の修正・親による再実走が完了するまで land しない。