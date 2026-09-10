## 結論

推奨は **(c) 両方**。ただし役割を分離する。

- (a): pin 済み 2 artifact に限定した、path・failure ID・必須参照 edge の構造検査。
- (b): SHA pin は「期待 digest と異なる bytes の検知」であり、再 pin 後の意味を保証しないという責務限定。

本回答ではファイルを変更しておらず、pytest / `check_docs` も実行していない。以下の nodeid は実装案であり、緑とは申告しない。

## 静的検算

- M1 の行番号は現状と一致する。command の pin 閉包は [tools/check_docs.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:389)、[test_check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:264)、[test_check_docs.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:318) の 3 面。ただし「cleanup family 全体の pin 閉包」と読める表現は不正確で、Skill 側にも [tools/check_docs.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:378)、[test_check_docs.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:261)、[test_check_docs.py:267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:267) の別の 3 面がある。
- M6 の「排他（交差ゼロ）」は誤り。pin 済み command は既に frontmatter、`$ARGUMENTS`、`docs/skill-self-improvement.md` への到達性を検査されている [tools/check_docs.py:4072-4107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4072)。pin 済み Skill にも file 閉包・frontmatter・exact description 検査がある [tools/check_docs.py:3513-3584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3513)。
- 「両者とも `literals=()`」も機構名として誤り。`literals=()` なのは cleanup Skill の呼び出しだけ [tools/check_docs.py:4491-4500](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4491)。command は同 API を通らず、別の digest 分岐で pin される [tools/check_docs.py:4502-4510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4502)。
- M5 は (a) について正しい。Python checker と test は command / dev-wave 文書の `TextLimit` 外。
- M7 で静的に確認できるのは 3959 / 4000 bytes、すなわち raw headroom 41 bytes [tools/check_docs.py:168-172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:168)。brief の 17-byte 予約を引けば 24 という算術は正しいが、その予約は現行の指定テスト範囲には定数・assert として現れない。したがって 24 bytes は checker が強制する現行値ではなく、brief 上の設計予約として扱うべき。
- P1 の「(c) ではなく (a) 主・(b) 従」は分類上矛盾する。(b) も実施するなら選択肢は `(c) 両方` であり、主従はその内訳である。

## (a) の最小実装プラン

### checker

1. [tools/check_docs.py:378-391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:378) の cleanup hash 定数群の直後に、次を追加する。

   - `CLEANUP_REQUIRED_REFERENCE_LITERALS`
     - command: `tools/audit_dangling_commits.py`、`docs/failures.md`
     - Skill: `.claude/commands/cleanup-branches.md`、`docs/skill-self-improvement.md`
   - `CLEANUP_REQUIRED_FAILURE_IDS`
     - command: `F26`, `F51`
     - Skill: `F26`, `F51`
   - `F<n>` 抽出 regex と `^### F<n>\.` heading regex。

   日本語の全文は pin せず、安定した住所 token だけを契約にする。

2. [tools/check_docs.py:3887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3887) の `_check_command_docs_guard` 直前に `_check_cleanup_reference_reachability(...)` を 1 関数追加する。

   処理は次に限定する。

   - `_visible_markdown_text` [tools/check_docs.py:1091-1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:1091) で comment / fence 内を除外する。
   - 上記 required literal と required ID が各 source の可視本文にあること。
   - `PATH_REF` [tools/check_docs.py:665-672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:665) で得た path が repo 内に実在すること。
   - command / Skill に現れる全 `F<n>` が `docs/failures.md` の可視な `### F<n>.` heading に exact 1 件到達すること。
   - failure ledger が読めない場合は `_safe_read_text` で fail-closed にする。

   現行 2 artifact から `PATH_REF` が拾うのは `.claude/commands/cleanup-branches.md`、`docs/failures.md`、`docs/skill-self-improvement.md`、`hooks/README.md`、`tools/audit_dangling_commits.py` の 5 件で、いずれも実在する。placeholder は拾わない。

3. Skill 本文を二重読取しないため、[_check_codex_skill_guard:3481-3494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3481) の返り値を `str | None` にし、[同:3616-3621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3616) で `skill_text` を返す。dev-wave / rulings 呼び出しは返り値を捨てたままでよい。

4. [tools/check_docs.py:4491-4510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4491) で cleanup Skill の返り値を捕捉し、`cleanup_text` 取得後、SHA 検査の直前に新関数を呼ぶ。SHA と参照到達性は独立 finding にする。

既存機構だけでは完結しない。

- `literals=` は raw substring の有無だけ [tools/check_docs.py:3585-3589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3585)、`exact_literals=` も raw count だけ [tools/check_docs.py:3604-3609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:3604)。target 実在性と hidden text を扱えない。
- `CODEX_FIRST_REFERENCE_LITERALS` は dev-wave reference だけを走査する [tools/check_docs.py:4109-4133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:4109)。
- `REQUIRED_REFERENCE_SECTIONS` と `_dispatch_reference_cell_errors` は dev-wave の H2 / table-cell grammar 専用 [tools/check_docs.py:435-454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:435)、[tools/check_docs.py:1813-1846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:1813)。cleanup を登録すると責務を混ぜる。

したがって「新 checker file・新台帳・新 gate は不要」には賛成だが、「既存 `literals=` の適用拡大だけで済む」には反対する。

### 負例テスト

[test_check_docs.py:255-380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:255) の fixture 群と、[同:6517-6689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:6517) の pin テスト群に追加する。

必要な nodeid 案は次のとおり。

- `orchestrator/tests/test_check_docs.py::test_cleanup_required_reference_is_rejected_after_repin[command-failures]`
- `...::test_cleanup_required_reference_is_rejected_after_repin[command-audit-tool]`
- `...::test_cleanup_required_reference_is_rejected_after_repin[skill-command]`
- `...::test_cleanup_required_reference_is_rejected_after_repin[skill-self-improvement]`
- `...::test_cleanup_required_failure_id_is_rejected_after_repin[command-F51]`
- `...::test_cleanup_dangling_failure_id_is_rejected_after_repin[command-F901]`
- `...::test_cleanup_missing_path_target_is_rejected[audit-tool]`
- `...::test_cleanup_hidden_reference_does_not_satisfy_contract[html-comment]`

fixture 側には次が必要になる。

- [_build_min_repo:710-766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:710) で、独立 literal として `### F26.` / `### F51.` を持つ最小 `docs/failures.md` を作る。現状は合成 command / Skill に F26/F51 がある一方、target ledger は作られていない。
- [_write_command_guard_docs:514-565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:514) 付近で `tools/audit_dangling_commits.py` と `hooks/README.md` の最小 target を作る。
- [test_check_docs.py:4778-4807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:4778) 付近に、temp repo 内の copied `tools/check_docs.py` の hash literal だけを更新する `_repin_cleanup_fixture(...)` を置く。

`_SYNTHETIC_CLEANUP_COMMAND` は command の全文逐語コピーなので、単に temp command から安全文を削ると、新検査より先に既存 SHA finding が出る。負例では必ず temp artifact を変異した後、temp checker の hash だけを再 pin し、

- SHA finding が出ないこと
- 新しい参照 finding が出ること

を assert する。実 test module の `_SYNTHETIC_CLEANUP_COMMAND` 自体を書き換えると baseline が攻撃状態になり、[test_check_docs.py:6539-6547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/orchestrator/tests/test_check_docs.py:6539) の独立 pin テストも壊れるため不可。

## 必須 literal の選定と P2〜P4

必須にするのは「意味」ではなく「住所」である。

- 必須: sole route となる canonical path、実行 helper path、failure ID、Skill→command の委譲 path。
- 必須にしない: 「正本は」「安全に」「必ず」等の自然文、段落全文、句読点・改行、`AGENTS.md` / `CLAUDE.md` のように別入口でも強制される重複 pointer。

恒真になる例は次のとおり。

- 「本文から発見した F ID がすべて実在する」だけにすると、F ID を全部削れば空集合に対する `all()` で通る。required ID 集合が必要。
- 本文から発見した path だけを検査すると、path 自体の削除で検査対象が消える。required literal が必要。
- raw literal は comment / fence に退避しても通る。可視本文に限定する必要がある。
- checker の contract から test fixture を自動生成すると、両方が同時に誤る自己整合になる。F26/F51 と期待 contract は test 側へ独立 literal で置く。

保守が破綻するのは、日本語全文、全 path・全 ID の exact set、repo-wide の「正本らしい自然文」を pin した場合である。正当な言い換えや failure 追加のたびに checker 改訂が必要になる。

裁定は以下。

- P2: **一部支持**。同じ checker / gate 内に収める方針は支持するが、新規 1 関数は必要。
- P3: **支持**。F173 は 1 件であり、[DW-G03:55-58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/dev-wave/core.md:55) により repo-wide 一般化は不可。
- P4: **反対**。repo-wide の自由形式 path lint は採らないが、pin 済み 2 artifact へ既存 `PATH_REF` を適用する狭い path 到達性は入れる。`PATH_REF` は既に placeholder / glob を除外する設計で、実際の `<runbook §7.2 の dir>` は match しない。

## (b) の文書位置と byte 予算

置き場所は [docs/skill-self-improvement.md「検査と commit 境界」:77-84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/skill-self-improvement.md:77)。ここが `check_docs.py` の保証範囲を定義する既存の正本である。

83〜84 行の 239-byte block を、次の 226-byte / 2 行へ置換する。

> whole-file SHA-256 pin は期待値と違う byte だけを検知し、義務の意味を保証しない。  
> 他の lint も予算・dispatch 等の構造に限る。意味は敵対監査と人間レビューで担保する。

現ファイルは 5997 / 6000 bytes、上限は [tools/check_docs.py:173-175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:173)。置換後は 5984 bytes、行長も 55 / 49 chars で 100-char 上限内。追加ではなく既存責務文の精密化なので予算を増やさない。

command には置かない。raw headroom 41 bytes、brief 予約込み 24 bytesに対し、かなり縮めた「pin は byte 改変検知だけで、意味を保証しない。」でも改行込み 66 bytesで入らない。安全文を削って捻出すれば F173 を再演する。

なお歴史記録としては、既に [F173:4384-4385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/failures.md:4384) と [check_docs.py:7-10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/tools/check_docs.py:7) が同じ限界を述べている。(b) はそれを運用契約の正本へ昇格させるものになる。

## 恒真化リスク

D30 は C++ / shell の意味を text parser で完全再現する軍拡を退け、path のような構造検査へ責務を限定している [docs/decisions.md:657-660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/decisions.md:657)。D45 は機序語を含む自然文 lint を、恒真化と偽陰性の錯覚を理由に明示的に退ける [docs/decisions.md:1565-1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-pin-semantic-gap/docs/decisions.md:1565)。

本案はその却下理由には直接当たらない。検査対象は有限の typed reference graph であり、「文が正しい意味を持つか」ではなく、

- source に address token が可視にあるか
- target file があるか
- target ID heading が一意にあるか

だけを判定するためである。

ただし address token を無関係な可視段落へ移せば通る残存偽陰性はある。そのため本案を「意味保証」と呼んではならず、(b) と敵対レビューを残す。全文 literal を採用して「F173 の意味を機械が守る」と主張する案なら、D30 / D45 と同根として却下すべきである。

## DW-G05

放置すると certified 選択・レポート・試行台帳の値は変わらないが、F26 への到達手段を失った、または実在しない F ID を持つ cleanup 手順が AI 作業手順の受理集合に残る。

## 推奨

**(c) 両方**を選ぶ。

- (b) 単独は M2/M3 の受理集合を一切変えず、再発阻止力がないため落とす。
- (a) 単独は address の構造しか守らないのに「意味検査」と過大解釈される余地を残すため落とす。
- repo-wide 一般化は独立 2 例がなく、DW-G03 に反するため落とす。

実装時期は P5 のとおり、次に cleanup-branches 系を変更する wave への相乗りでよい。成果物影響が手順書の受理集合に限定され、単独 wave を研究成果より優先する根拠は弱い。

## 総括

T-675 の最小修復は、pin 済み command / Skill の 2 artifact にだけ、可視な必須 address・path 実在性・F26/F51 heading 到達性を検査する 1 関数を追加すること。そのうえで SHA pin の責務限定を `docs/skill-self-improvement.md` の既存 2 行を縮約置換して明記する。自然文の意味は機械保証せず、F173 を再現する「削除＋再 pin」負例で address gate の実効性だけを証明する。