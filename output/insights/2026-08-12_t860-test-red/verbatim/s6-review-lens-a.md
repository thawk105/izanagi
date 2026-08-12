## 総括

現行実装そのものに、例外の握り潰し・skip 化・golden 比較の迂回は見つかりませんでした。3 node は実際に厳密 bytes 比較へ、残る 1 node は plan 構造判定へ到達します。

ただし、中心となる import provenance／global-state 復元契約を既存テストが検出できないことと、親 brief の受入・証拠表現に 2 件の過剰主張があります。判定は **blocker なし、must-fix 3 件、nit 2 件、現状 NO-GO** です。

pytest は実行していません。read-only の import probe と静的検査だけを行いました。

## Blocker

無し。

## Must-fix

### M1. fixture 自身から import したことと復元契約がテストで固定されていない

- 位置: [test_spool_fold.py:2948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:2948)、[test_spool_fold.py:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:1561)、[test_spool_fold.py:3023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:3023)
- 何が壊れるか: 4 node は fold 結果だけを検査し、`dev_waves.launch_authority.__file__` が fixture 配下か、終了後に元の `sys.path`・`dev_waves*` module object が戻ったかを観測していません。今回の修正の中心契約が恒真ではないものの、未固定です。
- 再現条件: [test_spool_fold.py:2959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:2959) を `ROOT / "tools"` に変えても、現在は fixture と checkout の source bytes が同じなので4 nodeの結果は変わりません。親 brief が明示的に却下した「別 repo の `dev_waves` を食わせる」実装を受理できます。また cleanup を弱めても、各 node 内に終了後状態の assert はありません。
- 仮判定: **real**。変異実走はしていませんが、観測点が存在しないことは静的に確定します。
- 成果物影響: 受理集合が「fixture ではなく別 checkout を参照する実装」まで含み、3 台帳 golden の import provenance 参照を誤って証明済みと扱います。

fixture origin、既存 module object、例外経路後の復元を直接検査する positive control が必要です。

### M2. 「4 node は bytes 厳密 golden」という親 brief の証拠分類が誤っている

- 位置: [brief.md:40](/work/1/SFC/tanab/dev-wave-jobs/t860-test-red/brief.md:40)、[brief.md:56](/work/1/SFC/tanab/dev-wave-jobs/t860-test-red/brief.md:56)、実体は [test_spool_fold.py:3000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:3000)
- 何が壊れるか: 最初の3 node は `_failures_after(repo) == expected` の byte-exact 判定ですが、N37 は `status`、fragment、GC path、target path の構造判定だけです。[test_spool_fold.py:3026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:3026) 以降に `after_bytes` の比較はありません。
- 再現条件: N37 の worklog target bytes を、列挙された path/statusを維持したまま変更する変異は、この node の assert では検出されません。
- 仮判定: **real**。
- 成果物影響: レポートと変異 matrix が「byte golden 4件」と過大計上し、worklog bytes に対する受理集合を実際より狭いものとして記録します。

「failure ledger の byte-exact 3件＋real canonical plan 構造1件」と訂正するか、本当に4件目も bytes 証拠が必要なら別途 pin すべきです。

### M3. 全走受入条件が既知 baseline と矛盾している

- 位置: [brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/t860-test-red/brief.md:50)
- 何が壊れるか: brief は「全走でも緑」を要求しますが、提示された main baseline は 2 failed / 9123 passed です。「絶対0 failed」なのか「既知2 node以外の新規失敗なし」なのかが非一意です。
- 再現条件: 修正後全走で同じ2 nodeだけが失敗した場合、前者なら不受理、後者なら受理になります。
- 仮判定: **real**。
- 成果物影響: wave commit の受理集合と全走結果のレポート値が判定者によって変わり、未解消 failure を誤って「全走緑」と記録する可能性があります。

既知2 nodeの完全な nodeid と baseline commit を固定し、「差分 failure なし」として扱うか、絶対緑を要求するかを親が明記する必要があります。

## Nit / backlog

### N1. `sys.modules` 全体は復元されず、import cache も残る

- 位置: [test_spool_fold.py:2950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:2950)、[dev_waves/__init__.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/tools/dev_waves/__init__.py:3)
- 何が壊れるか: cleanup 対象は `dev_waves*` だけです。read-only probe では `sys.path` と `dev_waves*` は復元されましたが、`ctypes`、`decimal`、`queue`、`socket` 等15 moduleと `sys.path_importer_cache` 3 entryが新たに残りました。
- 再現条件: これらが未ロードの process で context 内 importを行う。
- 仮判定: **real**。ただし現在残るものは標準ライブラリで、成果物影響は確認できません。
- 成果物影響: 現行の certified 値・レポート・3台帳には直接影響を書けないため **nit/backlog**。

将来 `dev_waves` が別 top-level packageへ依存すると、その moduleも残ります。依存が未導入なら `_load_rotate_limit` は fail-closed ですが、環境に導入済み・事前 cache 済みなら環境依存で黙って成功し得ます。

### N2. rglob は source/schema 限定ではなく、複製コストは package 全体に線形

- 位置: [test_spool_fold.py:2987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:2987)、主張は [author.md:4](/work/1/SFC/tanab/dev-wave-jobs/t860-test-red/author.md:4)
- 何が壊れるか: filter は「regular fileかつ `__pycache__` 外かつ suffix が `.pyc` 以外」であり、source/schema限定ではありません。将来の log、fixture、binary、symlink先も対象になり得ます。
- 再現条件: `tools/dev_waves/` に `.pyc` 以外の大きい生成物を置く。
- 仮判定: **real**。
- 成果物影響: 現時点ではテスト時間・I/Oだけなので **nit/backlog**。certified 値や3台帳の受理集合は変わりません。

現在の追加量は15 files・340,604 bytesです。4 node合計で60 file copy、複製 payload 1,362,416 bytes。`copyfile` に加えて source/destination を再読する byte-exact確認まで数えると、追加の論理I/Oは約5,449,664 bytesです。既存 fixture payload 9,133,033 bytes/nodeに対して約3.73%増で、wall timeは未計測です。package importもmodule cacheを消すため4回繰り返されます。

`"__pycache__" not in source.parts` と `source.suffix != ".pyc"` の現在の除外判定自体は正しいです。

## 攻撃したが破れなかった点

- **golden到達:** [test_spool_fold.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_spool_fold.py:240) は `plan_fold` の実 target bytesを返します。3件の assert は context 内で実行され、失敗時も例外は抑制されません。**refuted**。
- **例外を飲む経路:** `@contextmanager` は `yield` を catch せず `finally` だけを持つため、assert／fold例外はcleanup後に再送出されます。probeでも例外伝播を確認しました。**refuted**。
- **入れ子・既存module復元:** 入れ子 context、事前ロード済み `dev_waves*`、内側例外をprobeし、module object・key集合・`sys.path` が復元されました。**refuted**。ただし間接module漏れはN1。
- **xdist worker間干渉:** `sys.path`／`sys.modules` はprocess単位なのでworker間では共有されません。同一worker内でpytestが別testをこの同期的な `with` 区間へ割り込ませる経路もありません。**refuted**。
- **thread干渉:** helper自体はprocess-globalなので一般にはthread-safeではありませんが、4 callerと `plan_fold` に並行thread起動経路はありません。現行再現条件なしとして **refuted**。
- **fixture閉包:** 現行 `tools/dev_waves/` の15 tracked filesは相対import＋stdlibで閉じており、symlinkもありません。不足時は [spool_fold.py:1894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/tools/spool_fold.py:1894) で `SpoolValidationError` になります。現行について **refuted**。
- **検出力の直接緩和:** diffは既存4 callを囲んだだけで、期待bytes、status、path assert、test名、skip/xfail条件は変更していません。恒真化した既存assertは見つかりません。**refuted**。
- **production変更なし:** commitの変更先は `orchestrator/tests/test_spool_fold.py` 1ファイルのみです。productionのcross-checkout結合は残りますが、ユーザー裁定内で既知の残余所見です。**refuted**。
- **caller漏れ:** `_copy_real_canonical_family` と `_fixture_tools_imports` のcallerは指定4 nodeだけでした。「このhelper利用者は4件」の狭い主張は **refuted**。ただし全走だけでは、[test_check_docs.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t860-test-red/orchestrator/tests/test_check_docs.py:37) のmodule-scope汚染により同型孤立赤の不存在は証明できません。
- **module-scope汚染の新設:** 今回の変更はmodule scopeで `sys.path` を変更せず、呼出区間後に完全なlist内容をslice復元します。この不変条件は現行コードでは守られています。**refuted**。