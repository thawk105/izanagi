結論は **NO-GO** です。静的検査のみで、blocker 1件、must-fix 4件、nit 1件を確認しました。pytest・build・実測は行っていません。

## 所見

### 1. [severity: blocker] 非ゼロ浮動小数・文字 literal の無退出 loop では gate が発火しない

根拠: `_is_true_condition()` は `true` または `_is_nonzero_integer_literal()` だけを真とします。[coder_effect_gate.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:384)、[coder_effect_gate.py:414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:414)。小数点・指数を含む数値は `int(...)` が失敗して false、char literal は `string` token 扱いです。

発火しない具体的入力:

```cpp
while (1.0) {}
for (; 0.5f ;) {}
while ('x') {}
```

これらは structural gate を通り、`scan_host_effects()` は空を返し、`write=True` なら source へ書かれます。[p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:241)、[p3_s4_loop.py:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:269)。正例・負例テストにも整数 literal しかありません。[test_coder_effect_gate.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:163)

成果物影響: 明示的な無退出 loop を含む候補が pre-build 受理集合に残り、source materialization 後の run を停止させ、試行台帳を timeout/欠落へ倒し得ます。

修正提案: 単一 token で contextual-bool が確定する全 core literal（非ゼロ浮動小数、非ゼロ char を含む）を扱い、上記3形を負制御へ追加してください。

### 2. [severity: must-fix] bytes 非反射テストが実 backoff WAL 経路を通らず、候補 value が反射する

根拠: 実 driver は `coder.value` から `BACKOFF_FIXED` を作り、reject WAL の `genome` に保存します。[p3_s4_loop.py:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:903)、[p3_s4_loop.py:929](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:929)、[p3_s4_loop.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:296)。critic も genome を表示します。[digest.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:683)

具体的入力:

- `coder.value = 913579`
- `implementation = double now_backoff = 913579; std::system("ignored");`

gate は host-effect reject しますが、WAL/critic に `BACKOFF_FIXED=913579` が残ります。新テストは実 driver を通さず固定 `_G` を `record_diff_reject()` へ渡しており、value sentinel を WAL 経路へ投入していません。[test_p3_s4_loop.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:778)、[test_p3_s4_loop.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:817)

成果物影響: reject WAL と critic report の genome 値が候補由来 value を反射し、「全投影に sentinel なし」という段4裁定と台帳内容が不一致になります。

修正提案: 実 `run_one_iteration(..., do_build=False)` の reject 経路を整数 sentinel で検査してください。genome を非反射の例外とする設計なら、段4裁定へ明示的に戻す必要があります。非反射を維持するなら reject report は opaque candidate label/hash に射影してください。

### 3. [severity: must-fix] critic render が安全な構造化理由まで捨てている

根拠: WAL digest は固定 `rule_id`、固定 `category`、位置・件数を持ちます。[p3_s4_loop.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:245)。しかし host-effect だけ evidence を描画せず、全 category を同じ remediation に潰します。[digest.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:689)。テストも rule ID の欠落を肯定しています。[test_p3_s4_loop.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:830)

具体的入力: `read();` と `connect();` はそれぞれ file-stdio/network で発火しますが、critic には同じ「host 効果 token を除け」しか返りません。

成果物影響: critic/planner が拒否 category を区別できず、次候補生成へ「なぜ落ちたか」が還流されないため、レポートの構造化拒否理由が失われます。

修正提案: candidate text は出さず、allowlist 済みの `rule_id`、`category`、件数を独立フィールドとして loader/render へ通してください。

### 4. [severity: must-fix] M8 は配線文字列を検査するだけで、受理集合上の変異 kill になっていない

根拠:

- 両 driver の AST テストは既知の `inspect.cleandoc()` 欠陥で SyntaxError になります。[test_p3_s4_loop.py:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:834)
- sort の別テストも helper の `call_count` しか固定していません。[test_p3_s4_loop_sort.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop_sort.py:190)
- mutable auditor の矛盾検査は純粋 helper のみに置かれ、driver 配線を証明しません。[test_auditor_gate.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_auditor_gate.py:78)

具体的入力: machine-pass＋matching digest の `AuditorVerdict` を、生成後に `verdict="pass"`、`violations=[{"type": 1}]` へ矛盾変異する。現 helper は拒否しますが、driver を旧 `verdict != "pass"` 分岐へ戻すと `pass` として build へ進みます。

成果物影響: mutation ledger が M8 を KILLED と記録しても、trigger/sort driver の sink 再検証欠落による受理集合拡大を実際には証明できません。

修正提案: sort/trigger 両実 driver に上記の事後変異 auditor を入力し、例外または no-build を検査してください。AST 修正は配線 meta-test に留め、behavioral kill の代替にしないでください。

### 5. [severity: must-fix] 入力長上限がなく、loop 検査が二乗時間になる

根拠: 全 token を materialize した後、`_strip_parentheses()` は外側の括弧を1組ずつ剥がし、そのたびに残り全体を再走査・slice します。[coder_effect_gate.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:366)、[coder_effect_gate.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:491)。proposal loader に `implementation` の長さ制限もありません。[p3_s4_loop_sort.py:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop_sort.py:304)

具体的入力: `while (` の後に `N` 個の `(`、`true`、`N` 個の `)` を置く深い括弧列。判定は理論上 reject でも、`N` に対して二乗時間となり、bounded time 内に gate が発火しません。

成果物影響: reject WAL を書く前に iteration が停止し、campaign 台帳が候補 reject ではなく欠落・driver timeout になります。

修正提案: hole の byte/token 上限を scanner 前に fail-closed で設け、括弧除去を両端 index または一度の depth 計算で線形化してください。

### 6. [severity: nit] module 冒頭の `assert` は `python -O` では保証にならない

根拠: rule ID/category/identifier 一意性は `assert` のみです。[coder_effect_gate.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:96)。通常テストには独立検査があります。[test_coder_effect_gate.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:89)

具体的条件: 重複 rule ID を含む policy source を `python -O` で読み、`system();` を走査する。拒否自体は発火しますが、重複 rule ID/category は import 時に検出されません。

成果物影響: 現行受理集合は変わりませんが、WAL/report の rule attribution が曖昧な状態で起動できます。

修正提案: runtime invariant とするなら明示的な `if ...: raise RuntimeError(...)` にしてください。現行 table は一意であり、これは今回の blocker ではありません。

## 検出力・既存契約の照合

deny category の削除は次で対応しています。

| category/rule | 殺すテスト |
|---|---|
| process-shell | measured `system`/`execl` と `posix_spawnp` — [test_coder_effect_gate.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:20)、[同:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:65) |
| file-stdio | measured `ofstream` と `read` — 同上 |
| network | `connect` — 同上 |
| sleep-block-thread | `sleep_for` — 同上 |
| escape-hatch | `__asm__` — 同上 |
| unconditional-loop | literal-loop 負制御 — [test_coder_effect_gate.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:163) |

そのほか、以下は静的に問題なしと判断しました。

- scanner spy は `edited_text` を渡す変異を引数不一致で殺し、written source とも束縛しています。[test_p3_s4_loop.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:212)
- named 正常集合（sort 15件＋nosort、trigger 32 wire、backoff 正常形、sort fixture）は deny token を含まず、受理は維持されています。
- `write=True` は machine pass 後だけ書き込み、trigger は canonicalize 後の同じ predicate を scan/render しています。新しい迂回は見つかりませんでした。
- machine reject 時の auditor skip は reject object をそのまま返すため fail-open ではありません。helper は現コード上、受理集合を拡大しません。
- `git diff HEAD` の既存テスト期待値・WAL golden は変更されておらず、新設 assertion の追加だけです。既存 `DiffRejectSubtype` 値、campaign identity schema、WAL loader の文字列透過契約にも変更はありません。
- `bool open = false;` のような exact-token 過剰拒否は残りますが、段3で既知化された保守的縮小で、指定された現行正常集合には発火しません。

## 総括

- **NO-GO。**
- 非ゼロ浮動小数・char literal の明示的無退出 loop が pre-build gate を通る blocker があります。
- bytes 非反射テスト、critic の構造化理由、M8 の behavioral kill、scanner の有界性も未充足です。
- 親既知の2件のテスト赤とは独立した静的所見であり、fix 後の焦点再レビューが必要です。