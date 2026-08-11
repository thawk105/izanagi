静的再レビューの結論は **NO-GO** です。production 側の段 6 所見はすべて閉じていますが、`BACKOFF_FIXED` の非整数帰属に blocker があり、11 件の変異登録も現状のままでは成立しません。pytest・build・実測は行っていません。

## 1. 所見対応表

| 元所見 | 判定 | 根拠 |
|---|---|---|
| レビュー1-1 非ゼロ浮動小数・char literal loop | `closed` | float/hex-float/char/string の単一 true literal を扱う。[coder_effect_gate.py:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:443)、[coder_effect_gate.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:502)。指定形を含む負制御あり。[test_coder_effect_gate.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:165) |
| レビュー1-2 bytes 非反射と実 driver WAL | `closed` | 親裁定の「自由記述 bytes のみ非反射」は設計上妥当。例外は固定文言、WAL は genome と固定 digest だけを保存する。[p3_s4_loop.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:812)、[p3_s4_loop.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:289)、[test_p3_s4_loop.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:813)。ただし非整数値の帰属欠陥は下記 blocker。 |
| レビュー1-3 critic の構造化理由 | `closed` | 既定値付き `rule_id/category/finding_count`、allowlist loader、renderer が接続済み。[digest.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:173)、[digest.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:348)、[digest.py:715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:715) |
| レビュー1-4 M8 が behavioral kill でない | `closed` | sink は mutable auditor を再検証し、両実 driver を矛盾 auditor で検査する。[auditor_gate.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/auditor_gate.py:190)、[test_p3_s4_loop.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:934)。変異 spec は sort しか変異しないため、帰属登録は別途不成立。 |
| レビュー1-5 入力上限・二乗時間 | `closed` | 256 KiB／4096 token 上限と、1 回の括弧対応走査＋slice に変更済み。[coder_effect_gate.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:106)、[coder_effect_gate.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:390)、[coder_effect_gate.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:570) |
| レビュー1-6 `python -O` assert | `closed` | 3 invariant とも明示的 `RuntimeError`。[coder_effect_gate.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:111) |
| レビュー2-1 critic の「計算のみ」 | `closed` | 通過が計算のみ・host 安全性を意味しないと明記。[digest.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:722) |
| レビュー2-2 V-8 未閉鎖層列挙 | `closed` | 指定された materializer、buildcache/CMake、cache/WAL/COMMIT/freeze、恒偽 field を全件列挙。[coder_effect_gate.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:15) |
| レビュー2-3 V-1 byte-exact binding | `closed` | materialized marker hole を再抽出し、indent 除去後に scanner 入力と bytes 比較。[test_p3_s4_loop.py:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:221) |
| レビュー2-4 V-6 S6 provenance | `closed` | `error`、log、永続 provenance JSON の3投影を検査。[test_s6_sort_sweep.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_s6_sort_sweep.py:431) |

親裁定の成果物影響: 宣言済み `BACKOFF_FIXED` を表示し続けることで certified 選択・fitness・WAL/report の帰属を保持し、自由記述 implementation/literal だけを非反射にできる。ただし次の非整数欠陥を閉じる必要があります。

## 2. 新規所見・退行確認

### [severity: blocker] 非整数 `coder.value` が別の `BACKOFF_FIXED` genome に帰属する

role policy は 1..1000 の有限な `int|float` を許可します。[policy.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/codex_roles/policy.py:483)。loader も `float` 化します。[p3_s4_loop.py:1005](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:1005)

一方、genome は `int(coder.value)` へ切り捨てますが、整合検査は元の float と hole literal を比較します。[p3_s4_loop.py:910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:910)、[p3_s4_loop.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:831)。したがって `value=20.5` と `now_backoff=20.5` は整合検査を通り、実行 bytes は 20.5、WAL genome は `BACKOFF_FIXED=20` になります。

成果物影響: certified 選択・fitness・レポート・台帳が実際に走った backoff 値とは異なる genome に帰属します。

### [severity: must-fix] 変異 spec の期待 node・分類が成立していない

M1–M4/M10 は、一意な identifier の削除・追加でも緑のままの一意性 test を赤として登録しています。[mutation-spec.json:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/mutation-spec.json:17)、[test_coder_effect_gate.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:91)。M7 は受理集合でなく spy 引数だけ、M9/M11 は受理集合を変えない診断 pin です。

成果物影響: 現 spec の matrix は KILLED ではなく MISMATCH／誤分類となり、semantic gate の検出力を成果物の監査証拠として確定できません。

### [severity: nit] `codex_roles` 赤を「subset 実行由来」と断定できない

対象 test は top-level `from codex_roles import policy` を使います。[test_p3_s4_loop.py:1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:1447)。repo-root の通常 import path では `codex_roles` は存在せず、`orchestrator/` を追加した場合だけ解決します。したがって差分外の既存欠陥という判断は正しい一方、subset 固有ではなく、環境・実行順依存のテストです。

成果物影響: certified/report/WAL は変わりませんが、受入結果の緑赤が ambient `sys.path` に依存します。

### 指定された退行面

- 正常集合50点を静的列挙した最大値は **379 bytes／64 tokens**。全件 finding 0 で、上限から十分離れています。対象の固定 test は [test_coder_effect_gate.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:236) です。
- 通常 `for`、range-for、data-dependent `while`、false literal は通過します。[test_coder_effect_gate.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:151)。literal-true＋`break` の保守的拒否は既知契約です。
- critic 新フィールドはすべて既定値付きで、repo 内 constructor は keyword 引数です。[digest.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:185)。指定 consumer の互換破壊は見つかりません。
- `git diff fe893069~1 HEAD` では既存 test assertion、WAL golden、campaign identity の変更なし。test 差分の唯一の削除は import 文の整形で、期待値変更 blocker はありません。
- D-2 の security claim は docstring/comment/例外文で維持されています。両 commit message も gate を測定済み4種の defense-in-depth と明記しています。ただし `ff3afec2` の `BACKOFF_FIXED` 帰属主張は、上記非整数欠陥があるため現状では過大です。

## 3. 変異11件の帰属判定

| 変異 | 殺す test／mask／単一理由性 | 判定 |
|---|---|---|
| M1 `system` 削除 | `system` 単体 test は実在し mask なし。[test_coder_effect_gate.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:22)。ただし登録した process probe は `posix_spawnp` なので緑、一意性も緑。seam 等の実際の赤を未列挙。 | **登録し直すべき** |
| M2 `ofstream` 削除 | 測定4種 test が単一理由で殺す。structural 層の mask なし。ただし一意性 test は緑で、seam の赤が未列挙。[test_p3_s4_loop_sort.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop_sort.py:142) | **登録し直すべき** |
| M3 `connect` 削除 | network probe と critic category test が殺す。[test_coder_effect_gate.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:67)、[test_p3_s4_loop.py:874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:874)。一意性 test は緑。 | **登録し直すべき** |
| M4 `read` 削除 | `read` は sleep-block でなく **file-stdio**。[coder_effect_gate.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:62)。file probe と critic test が殺し、mask なし。親の名称と期待 node が誤り。 | **登録し直すべき** |
| M5 loop 判定無効化 | 測定 `while(true)`、全 literal、deep-parenthesis、両 seam が同じ理由で赤。[test_coder_effect_gate.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:165)。parameterized node の suffix と seam node が spec に不足。 | **登録し直すべき** |
| M6 scanner 常時 pass | sort/backoff seam と scanner spy が実在し、structural gate は測定入力を mask しない。[p3_s4_loop.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:241)。critic/nonreflection の追加赤が spec に不足。 | **登録し直すべき** |
| M7 `edited_text` 走査 | spy は引数差で赤になる。[test_p3_s4_loop.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:259)。しかし同 fixture の骨格自体には deny finding がなく、正常候補の「受理→過剰拒否」を示していない。meta pin が behavioral 不在を覆っている。 | **登録し直すべき**。behavioral 正例を追加するか structural pin に格下げ |
| M8 旧 verdict 分岐 | sort の exact anchor は behavioral test で殺され、mask なし。[test_p3_s4_loop.py:934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:934)。ただし spec は sort だけを変異し、trigger call は未変異。[mutation-spec.json:131](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t316-semantic-gate-impl/mutation-spec.json:131) | **登録し直すべき**。M8-sort／M8-trigger に分離 |
| M9 例外へ implementation 反射 | projection test と S6 provenance test が単一の leak 理由で殺す。[test_p3_s4_loop.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:813)、[test_s6_sort_sweep.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_s6_sort_sweep.py:431)。受理集合は不変。 | **登録し直すべき**。KILLED でなく diagnostic sensitivity pin |
| M10 `sort` 追加 | 現行15候補の正例が behavioral に殺し、mask なし。[test_coder_effect_gate.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_coder_effect_gate.py:246)。一意性 test は緑で、多数の正常 sort driver 赤が未列挙。 | **登録し直すべき** |
| M11 subtype 文字列変更 | seam、driver WAL→loader→render が文字列 drift を検出する。[test_p3_s4_loop_sort.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop_sort.py:142)、[digest.py:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:374)。受理集合／fail-closed は不変で、実際の赤は登録2 nodeより多い。 | **登録し直すべき**。diagnostic sensitivity pin |

## 総括

**NO-GO。** 段 6 のレビュー所見そのものは production/test 上すべて閉じています。  
しかし非整数 `coder.value` が切り捨て genome に帰属する blocker があり、親の帰属裁定を現コードでは一般に正当化できません。  
さらに変異11件は expected node、behavioral 帰属、kill/diagnostic 分類が未確定で、現 spec のまま本走できません。  
親実測の `codex_roles` 赤は本 wave 差分外ですが、subset 固有ではなく import-path 依存として別途是正が必要です。