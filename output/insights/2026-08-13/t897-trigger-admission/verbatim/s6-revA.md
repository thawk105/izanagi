結論は **NO-GO** です。N01〜N14 の既知カタログは裁定どおり処理されますが、自前字句解析にカタログ外の fail-open があり、変異テストの帰属にも不成立があります。

### F1 — raw string／行継続内の偽 marker block を受理する

severity: **must-fix**

file:line 根拠: [_cpp_block_comment_ranges](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:169)、[_visible_directives](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:219)、[exact block の即受理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:266)

`_visible_directives` が除外するのは block-comment range だけで、文字列・raw string の range は渡されません。このため、例えば次の raw string の内容に凍結 block を入れると、実コードではないのに `begins=1, ends=1`、block exact と判定されます。

`R"tag(\n<FROZEN_TEMPLATE_BLOCK_BYTES>)tag"`

さらに C++ の行継続はコメント認識より前に処理されますが、この scanner は code/line-comment 状態で処理しません。次の bytes も scanner 上は block comment が 0 件で、凍結 block を受理しますが、C++ では `/\`＋改行＋`*` が `/*` となり、block 全体がコメントです。

`/\\\n*\n<FROZEN_TEMPLATE_BLOCK_BYTES>*/`

実際の静的分岐確認では、raw-string decoy、行継続 comment とも `block_comments=()`、BEGIN/END 各 1 件でした。偽 block のほかに marker を削除した実効 skeleton を置いても、骨格 token 検査は「marker 0 件」の分岐でしか走らないため捕捉しません。

**成果物影響:** report/台帳が canonical mask の source と記録しても実バイナリは markerless、pristine、または別述語となり、certified 選択と receipt/source SHA の意味的帰属が壊れます。

### F2 — 同じ字句解析が正当な exact-block source を過剰拒否する

severity: **must-fix**

file:line 根拠: [quote の単純開閉](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:190)、[未終端扱いの block range](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:214)、[marker 0 件時の reject](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:253)

例えば、有効な raw string `R"tag("/*)tag"` を正準 block より前に置くと、scanner は raw payload 中の `"` で文字列が閉じたと誤認し、続く `/*` から EOF までを block comment にします。実際の正準 BEGIN/END は 0 件に消え、骨格 token により reject されます。

同様に `// \\\n/*\n` は C++ では行継続後の単一 line comment ですが、scanner は物理改行で line-comment を終了し、次行の `/*` を未終端 block comment と誤認します。

個別構文の評価は次のとおりです。

- `//` 内の `/*`、`/*` 内の `//`、通常の文字列・文字リテラル内の `/*`: 行継続がなければ正しく無視。
- raw string: delimiter と payload を認識せず、fail-open／fail-closed の両方がある。
- 行継続: string 状態の `\`＋1 byte しか扱わず、翻訳フェーズ全体としては不正確。CRLF 継続も LF が残る。
- `"""`: C++ に三重引用構文はなく、単純に quote 状態が反転する。正当な raw string の代替処理にはならない。
- trigraph: 変換しない。現行ビルドは `-std=c++20` なので通常は live な意味差ではないが、`-trigraphs` 等を許すと `??/` による同型の行継続を見落とす。

**成果物影響:** 本来受理集合に属する exact-block source が `build-error` となり、候補が certified 選択から欠落し、report/台帳の比較集合と件数が縮みます。

### F3 — 追加テストの変異帰属が複数箇所で成立しない

severity: **must-fix**

file:line 根拠: [N07 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:363)、[frame 負例群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:319)、[noncanonical block 群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:440)、[実装側の複合検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:261)、[裁定の M4〜M7](/work/1/SFC/tanab/dev-wave-jobs/t897-trigger-admission/s4-adjudication.md:131)

帰属不成立は次のとおりです。

- `N07-nul` は BEGIN の marker ID 内へ NUL を入れています。NUL 検査を削除しても BEGIN 0／END 1 となり、一意性検査が先に reject します。NUL 検査の単独 kill node ではありません。
- M4 の「1 物理行制約」は独立実装されていません。空 hole・複数行 hole は同じ membership 検査だけで reject されるため、M4 の削除 anchor が存在しません。
- M6 の「CR payload を残す処理」も実装されていません。CRLF/CR は block frame 比較による拒否であり、事前登録された M6 を単独注入できません。
- frame 比較だけを削除しても、N01、N05、N09〜N11、N14、CRLF は block 長の変化で hole の固定 offset がずれ、membership 検査が引き続き reject します。直接の frame kill として使えるのは、同長変異の N02 や CR-only などに限定されます。
- F1/F2 の raw string、行継続の正負例がありません。N03 は単純な `/* ... */` しか覆いません。

M1/M2、M3、M5、M8、M9、M10、M11 については、それぞれ call-site、外周空白、mask 31、非 ENOENT、markerless skeleton、重複 pair、pristine 正例に対応する node が存在します。

**成果物影響:** mutation 台帳の期待 node 完全集合と KILLED 判定が誤り、検出力のない validator を受入済みとして記録したまま不正 source が certified/report 経路へ入ります。

## 総括

凍結定数は正しいです。patch の `+BEGIN` から `+END` までを包含し、各追加行の `+` と context 行の先頭 1 byte を剥がした結果は **1,209 bytes**、SHA-256 は `2fa8ad5bb205c6b199e9dd6699e2f7f9c8b3868ac1d173606ffba6e90358379a`。定数と完全一致し、双方とも END 行末の LF を含みます。[定数](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/axis_trigger_gating.py:27) [patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/patches/silo-backoff-trigger-gating-variant.patch:86) [golden test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:570)

N01〜N14 のコード追跡結果は以下です。

| ID | 実装 | 裁定 |
|---|---|---|
| N01〜N11 | reject | 一致 |
| N12 | accept | 一致。段 4 RP-2 の scope 外 |
| N13〜N14 | reject | 一致 |

BOM/NUL/decode の順序は、marker 0 件でも exact 骨格 token が残る入力なら、その直前の token 検査で reject されるため穴はありません。marker と両骨格 token のすべてを別 bytes に壊した入力は sanitation 前に no-op になりますが、裁定が定めた exact signature の外です。

`_visible_directives` の `comment_index` は、helper が生成する開始順・非重複の range に対しては正しいです。C++ block comment は入れ子にならず、helper 自身も重複・逆順 range を生成しません。問題は走査の単調性ではなく、F1/F2 の range 生成自体です。

`require_build_admission` は live source と `_source_map(expected_source)` を sealed body・policy 検査より先に評価するようになり、例外優先順位は変わります。[呼出し点](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:798) ただしこれは段 4 の指定順です。既存 node では `test_receipt_validation_binds_source_root` が追加の ENOENT no-op を経由して従来と同じ source/root mismatch になり、期待結果が変わる nodeid はありません。

no-op 条件も裁定どおりです。source root が通常 file なら `NotADirectoryError` が第二の `except OSError` に入り reject、root/target の切れた symlink は `FileNotFoundError` となり no-op です。

pristine 過剰拒否 control は残っています。[pristine 正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:297)

pytest、Web 検索、ファイル編集は行っていません。静的コード追跡と in-memory の byte 分岐確認のみです。