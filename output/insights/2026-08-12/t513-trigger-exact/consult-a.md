## 総括

- real 所見: **3 件**（#3、#5、#7）
- must-fix: **3 件**
- 最も危険: **#7 — exact 検査は binding 提示時だけ発火し、certified・oracle・floor を含む複数経路が binding 無しで materialized source を build へ運べる。**
- pytest / build は未実行。書込みも行っていない。32 mask と文字処理はファイルを作らないメモリ内 probe のみ実施し、「緑」とは判定していない。

以下、`I = b"\x20\x20"`、`E_m = emit_predicate(TriggerGateIR(m)).encode("utf-8")` と表記する。

### 1. Refuted — mask=20 の一般化は全 32 mask で成立する

`emit_predicate` は固定 ASCII 部品を `b" || "`相当で連結するだけで、改行や折返し処理がない。[reflux_ir.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/reflux_ir.py:131)–[reflux_ir.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/reflux_ir.py:141)。独立 literal 32 行も [reflux_ir_expected_goldens.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/reflux_ir_expected_goldens.py:24)–[reflux_ir_expected_goldens.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/reflux_ir_expected_goldens.py:56) に存在する。

全 `E_m` の byte 長と `0x0a` 個数は次のとおりだった。全て改行 0 個。

```text
0:72  1:134 2:134 3:196 4:133 5:195 6:195 7:257
8:136 9:198 10:198 11:260 12:197 13:259 14:259 15:321
16:130 17:192 18:192 19:254 20:191 21:253 22:253 23:315
24:194 25:256 26:256 27:318 28:255 29:317 30:317 31:379
```

最長でも `E_31` は 379 bytes、正規 hole は `I + E_31` の 381 bytes。`render_hole` も `implementation.split("\n")` の結果をそのまま挿入し、自動折返しをしない。[p3_s4_loop.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:176)–[p3_s4_loop.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:180)。

骨格 hole の実 bytes は [silo-backoff-trigger-gating-variant.patch:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:102) の

```text
2b 20 20 69 7a 61 ... 74 72 75 65 3b 0a
 +  SP SP i  z  a  ... t  r  u  e  ;  LF
```

したがって patch 制御 byte `0x2b` を除く正規 materialization は全 32 mask で `I + E_m`。

成果物影響: mask や長さに起因する正規 source の欠落・誤受理はなく、certified 値・レポート・台帳参照は変わらない。

### 2. Refuted — 複数行化は fail-open にならない

骨格の元 hole が複数行になっただけなら、`render_hole` はその全範囲を `implementation.split("\n")` で置換する。[p3_s4_loop.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:173)–[p3_s4_loop.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:180)。現在の `E_m` は単一行なので、materialized hole は依然 1 行になる。

一方、実際の materialized bytes が例えば

```text
I + E_m + b"\x0a" + b"second-line"
```

なら `parse_template_file` は 2 行を `hole_text` に入れ、`len(hole_lines) != 1` で拒否する。[diff_quarantine.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:613)、[pipeline.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:82)。壊れ方は fail-closed。

また計画した drift test は「骨格 hole が 1 行だけ」を pin するため、骨格を意図的に複数行へ変える場合は assertion 自体も更新が必要になる。[plan.md:213](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:213)–[plan.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:223)。

成果物影響: 将来の複数行設計を無調整で投入すると build admission が全拒否となり certified 値が欠落するが、複数行 source が誤って certified になることはない。

### 3. Real / must-fix — CRLF は raw-byte exact を迂回する

`parse_template_file` は `open(..., encoding="utf-8")` で `newline` を指定していない。[diff_quarantine.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:556)–[diff_quarantine.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:561)。Python の universal-newline 変換により、

```text
raw:     I + E_m + b"\x0d\x0a"
decoded: "  " + E_m.decode() + "\n"
hole:    "  " + E_m.decode()
```

となる。したがって計画の `hole_lines[0].encode() == I + E_m` は CRLF source を受理する。raw bytes では `0d` が余分なのに比較前に消えている。

さらに source identity 側も text mode で読み、preprocess 後の正規化出力を hash している。[source_digest.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/source_digest.py:580)–[source_digest.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/source_digest.py:590)、[source_digest.py:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/source_digest.py:640)–[source_digest.py:651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/source_digest.py:651)。trigger の `SourceBinding` は `src_token` とこの `source_bytes_sha256` だけを持つ。[trigger_gate_binding.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/trigger_gate_binding.py:136)–[trigger_gate_binding.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/trigger_gate_binding.py:139)。raw CRLF 差の防壁にはならない。

`_check_template_hole_invariant` の `content.rstrip("\r")` も CR を意味上無視する設計である。[diff_quarantine.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:350)。加えて `DiffQuarantine` の constructor でも CR を除いている。[diff_quarantine.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:287)。この invariant は admission から呼ばれておらず、raw-byte exact の代替にもならない。

他の端点:

- 末尾 LF がない source: hole は END より前なので影響なし。正規 hole は受理される。
- 通常の BOM `ef bb bf` はファイル先頭の frame 側に残り、hole には残らない。hole 自体へ `U+FEFF` を置いた場合は old/new とも拒否。
- 不正 UTF-8 は `_require` の `UnicodeError` 捕捉で拒否される。

修正は、admission 用だけ raw newline を保持する読取（`newline=""` または binary parser）を用い、`I+E_m+b"\r\n"` と CR-only source の拒否テストを追加すること。論理行 payload だけを契約にしたいなら、brief / plan の「byte exact」「一意な bytes」という主張をその境界まで明示的に狭める必要がある。

成果物影響: 未修正では CRLF materialized source が受理集合に残り、WAL の trigger binding と proof-chain 参照が「emitter が生成しない raw bytes」を exact と表示し得る。

### 4. Refuted — 比較変更そのものは受理集合を拡大しない

parsed logical hole `h` に対して、新受理条件 `h == I + E_m` なら必ず旧条件 `h.strip() == E_m` も満たす。したがって [plan.md:255](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:255)–[plan.md:293](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:293) の包含証明は成立する。

代表的な hole bytes は次のとおり。

| hole 形 | old | planned exact |
|---|---:|---:|
| `I + E_m` | pass | pass |
| `E_m` | pass | reject |
| `I + E_m + b"\x20"` | pass | reject |
| `b"\xc2\xa0" + E_m` (`U+00A0`) | pass | reject |
| `b"\xe3\x80\x80" + E_m`（全角空白 `U+3000`） | pass | reject |
| `b"\x09" + E_m` | pass | reject |
| `b"\x0b" + E_m` / `b"\x0c" + E_m` / `b"\x1c" + E_m` | pass | reject |
| `b"\x00" + E_m` | reject | reject |
| `b"\x01" + E_m` | reject | reject |
| `b"\xef\xbb\xbf" + E_m` (`U+FEFF`) | reject | reject |
| `I + E_m + b"\x0d\x0a"` | pass | pass（#3 の残穴） |

Unicode whitespace が old で通るのは、現行比較が Python `str.strip()` を使うため。[pipeline.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:79)–[pipeline.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:83)。NUL、SOH、BOM は `strip()` 対象でないので old でも通らない。

成果物影響: planned 比較により旧 reject が新規 certified になる source はない。意図した空白形だけが台帳・レポート候補から減る。CRLF の不変部分は #3。

### 5. Real / must-fix — drift assert は恒真ではないが locator が非一意

[plan.md:217](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:217)–[plan.md:223](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:223) の比較自体は恒真ではない。patch の独立 bytes と定数を比較するため、正しく marker を選べば indent drift を検出できる。

問題は `if_index` / `else_index` の決め方が未規定なこと。patch には同じ

```text
b"+#if BACKOFF_TRIGGER_GATING"
= 2b 23 69 66 20 42 41 43 ...
```

が 11 箇所ある。[patch:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:41)、[patch:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:79)、[patch:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:101)、[patch:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/patches/silo-backoff-trigger-gating-variant.patch:107) ほか。該当 unified hunk 内だけでも複数ある。

そのため generic な `.index(b"+#if ...")` や hunk 内検索では、現在の patch を誤選択して失敗するか、将来置かれた decoy block を選んで実 marker hole が壊れても assertion が通る。計画の「同じ行が別位置にあるだけでは通らない」という主張は、現状の pseudocode だけでは成立していない。[plan.md:226](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:226)。

修正案は次の順序を byte で一意に束縛すること。

```text
b"+  // EVOLVE-BLOCK-BEGIN " + MARKER_ID
b"+#if BACKOFF_TRIGGER_GATING"
b"+  izanagi_gate_pass = true;"
b"+#else"
...
b"+  // EVOLVE-BLOCK-END " + MARKER_ID
```

BEGIN / END の出現数も各 1 を assert し、その閉区間内だけで `#if` / `#else` を探すべきである。

成果物影響: 未修正では誤った patch 部位を pin しても検査済みと表示できる。実 hole drift が見逃されると正規 source が全 admission 拒否になり certified 集合が欠落するか、レポートの「骨格 bytes と pin が一致」という参照が偽になる。

### 6. Refuted — fixture 是正は正しさゲートの緩和・完全な自己参照ではない

既存 fixture は実際に `E_20 + b"\x0a"` と書き、骨格の `I` を持っていない。[test_campaign.py:5331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5331)–[test_campaign.py:5339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5339)。これを実 materializer 経路へ直すこと自体は期待値緩和ではない。

計画 helper は production parser / renderer / indent 定数を使うが、直後に独立 literal の

```text
assert hole_line == b"\x20\x20".decode() + predicate
```

を置く。[plan.md:169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:169)–[plan.md:175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t513-trigger-exact/plan.md:175)。したがって renderer が無 indent、4-space、複数行へ壊れれば helper と assertion が一緒に追随して通る構造ではない。

emitter についても production import のない 32 literal が別ファイルにあり、独立性検査の意図も明記されている。[reflux_ir_expected_goldens.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/reflux_ir_expected_goldens.py:24)、[test_reflux_ir.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_reflux_ir.py:274)。crossed-binding テストも mask 20 source / mask 21 binding と既存 WAL error を維持するため、pipeline から検査呼出しを消す変異を隠さない。[test_campaign.py:5377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5377)–[test_campaign.py:5418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5418)。

ただし raw patch 側の独立性は #5 の locator 修正が前提。また、これらのテストが守るのは binding lane だけで、全 build 経路の自己参照問題は #7 に残る。

成果物影響: fixture 是正そのものは production 受理集合や verifier 期待値を緩めず、certified・レポート・台帳値を実装に合わせて安売りする変更ではない。

### 7. Real / must-fix — exact admission を迂回する build 経路が複数ある

`_require_materialized_trigger_predicate` の呼出しは [pipeline.py:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:777) の 1 箇所だけ。一方 `pipeline.evaluate` は `trigger_gate_binding=None` を許し、[pipeline.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:766) の条件全体を飛ばして [pipeline.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:830) / [pipeline.py:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:836) の build へ到達する。

つまり generic BuildAdmission は通っても、trigger predicate exact admission は optional である。例えば materialized hole が `b"\x09"+E_20` でも binding を省略すれば、この関数は一度も呼ばれない。

確認できた production 経路:

| 経路 | 静的な bypass | 影響先 |
|---|---|---|
| s8a trigger sweep | `quarantine(write=True)` 後、binding 無しで `run_campaign`。[s8a_trigger_sweep.py:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8a_trigger_sweep.py:451)、[s8a_trigger_sweep.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8a_trigger_sweep.py:464) | `outcome="certified"` と sweep report。[s8a_trigger_sweep.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8a_trigger_sweep.py:479)、[s8a_trigger_sweep.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8a_trigger_sweep.py:701) |
| S-1 direct comparison | system_gate / ident_all を materialize した後、binding 無しで `pipeline.evaluate`。[s1_direct_comparison.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_direct_comparison.py:530)、[s1_direct_comparison.py:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_direct_comparison.py:819) | certified 判定と session ledger。[s1_direct_comparison.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_direct_comparison.py:590)、[s1_direct_comparison.py:852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_direct_comparison.py:852) |
| S8b oracle | `prepare_cell` 系 materializer 後、manifest identity は照合するが exact predicate binding 無しで `evaluate`。[s8b_oracle_driver.py:1396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8b_oracle_driver.py:1396)、[s8b_oracle_driver.py:1424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8b_oracle_driver.py:1424) | official oracle WAL / certified result。manifest identity は既存 bytes への独立防壁だが、emitter exact の証明ではない |
| S8b floor | 同じ prepared materializer から generic admission を作り、`build_v2` を直接呼ぶ。[s8b_floor_campaign.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8b_floor_campaign.py:1191)、[s8b_floor_campaign.py:1206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8b_floor_campaign.py:1206) | binary store / manifest / floor result。[s8b_floor_campaign.py:3186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s8b_floor_campaign.py:3186) |
| S-1 extime calibration | trigger source を materialize 後、`buildcache.build` を直接呼ぶ。[s1_verify_extime_calibration.py:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_verify_extime_calibration.py:341)、[s1_verify_extime_calibration.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/s1_verify_extime_calibration.py:358) | calibration binary / report |

対照的に新しい trigger loop は schema marker を config に入れ、binding を `run_campaign` へ渡しているため、この lane だけは exact 検査へ到達する。[p3_s4_loop_trigger_gating.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop_trigger_gating.py:475)、[p3_s4_loop_trigger_gating.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop_trigger_gating.py:595)。

現在の通常 producer は quarantine 内で predicate を正準化してから書くため、既存正常走が直ちに汚染済みという所見ではない。[p3_s4_loop.py:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/p3_s4_loop.py:221)。しかし「既 materialized source の直接投入」という T-513 の脅威モデルに対し、binding 省略がそのまま bypass になる。

must-fix は、`BACKOFF_TRIGGER_GATING=1` / trigger axis を build gateway 側で検出して semantic admission を必須化するか、上記全 consumer に expected mask/binding を結線すること。floor/calibration の直接 build には共有 validator が必要である。実装範囲を拡張しないなら、成果物主張を「schema-marked trigger exploration lane のみ」に狭める裁定が必要。

成果物影響: 未修正では `b"\x09"+E_m`、`I+E_m+b"\x20"`、#3 の CRLF などが別 consumer から build・verify を経て certified 判定、レポート、session ledger、oracle/floor manifest に到達できるため、「build admission の穴を閉じた」という成果物参照は成立しない。