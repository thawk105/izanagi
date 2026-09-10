静的レビューの結論は **NO-GO**。pytest は実行しておらず、親の 74 passed を所見ゼロの根拠にはしていない。

### 1. must-fix — list item 相対の 4-space fence で `remaining` decoy が通る

**根拠:** `FENCE_OPEN_RE` は raw 行頭の indent を 0〜3 文字に限定している（[tools/spool_fold.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:64)）。一方、item 継続行は 2 spaces 以上なら許される（[tools/spool_fold.py:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:350)）。4-space opener を fence と認識できないまま、末尾の `  remaining: none` を trailer field と数える（[tools/spool_fold.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:383)、[tools/spool_fold.py:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:448)）。

CommonMark では、`- ` の list container indent 2 spaces を除いた後の 2-space fence、すなわち raw 4-space opener は有効であり、未閉鎖 fence は enclosing list item の終端まで続く。[CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/)

**失敗シナリオ:**

````markdown
- [T-001] 初期処置だけ終了。後続作業は明日
  base: <正しい64hex>
    ```yaml
  remaining: none
````

`remaining` は Markdown 上では未閉鎖 fence 内だが、実装は opener を見落とす。末尾 field として除去後、既存 `_strip_base` が前方の base を抽出し、完了を受理する。現テストは raw 2-space opener しか固定していない（[test_spool_fold.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:835)）。

**成果物影響:** 残件のある T が active 集合から消え、後続 wave の作業集合と完了記録が誤る。

**推奨:** completion item の list-container 幅を考慮した fence state を使う。4-space/5-space、backtick/tilde、未閉鎖 fence の負例を追加する。top-level 用 tokenizer を単純に 5 spaces へ広げると `check_docs.py` と別の過剰不可視化になるため避ける。

### 2. must-fix — replay guard が「同一追記」ではなく raw block の部分文字列を拒否する

**根拠:** 対象 block 全体を raw 文字列として保存し（[tools/spool_fold.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1438)、[tools/spool_fold.py:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1472)）、`append.suffix in original` だけで replay と判定している（[tools/spool_fold.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1475)）。仕様は同一 suffix の再投入拒否であり、任意の既存部分文字列や不可視な例示の拒否ではない（[spec2.md:71](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/spec2.md:71)）。項目24は実際に先頭行へ追記済みの完全一致だけを検査する（[test_spool_fold.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1217)）。

**失敗シナリオ:** 対象 item の continuation に `<!-- 発火記録: D2 -->` という例示があり、初回の suffix ` 発火記録: D2` を追記する。raw block には同じ byte 列があるため `deferred-append-duplicate-suffix` となる。より単純には、fixture の既存本文に含まれる ` seed` を suffix にしても初回追記が拒否される。

**成果物影響:** 正当な発火記録を含む fragment と同時 pending の worklog・phase3・receipt がすべて生成されない。

**推奨:** 少なくとも不可視 continuation と既存 prose を replay 履歴から除外し、T-358 の追記単位として exact 比較できる境界を定義する。現形式から過去の任意 suffix 境界を復元できないなら、raw substring を仕様充足とみなさず親へ返す。既存 prose の部分文字列、comment/fence 内一致を正例として追加する。

### 3. must-fix — N15 は downstream gate による診断 kill になる

**根拠:** 項目15は空 suffix を先、空白 suffix を後に同一テスト内で処理する（[test_spool_fold.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1040)）。N15 で parser を緩和して空文字を `_DeferredAppend` にすると、`"" in original` が必ず真になり（[tools/spool_fold.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1475)）、`deferred-append-duplicate-suffix` が発火する。`_raises` は error code の完全一致を要求する（[test_spool_fold.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:169)）。

**失敗シナリオ:** N15 注入後も空 suffix は downstream gate で拒否される。しかし期待した `deferred-append-shape` ではないため node は赤くなり、後続の空白 suffix ケースへ到達しない。受理集合は空 suffix について変わっていないのに KILLED となる。

**成果物影響:** mutation matrix が suffix shape gate の検出力を偽って KILLED と記録する。

**推奨:** 空と空白を別 node に分ける。空文字変異は parser と空文字 substring mask の両層変異として事前登録し、実際に plan が受理へ変わることを oracle にする。空白ケースも独立に走らせる。

### 4. must-fix — N01 と P02 は現コード上で単一理由に帰属できない

**根拠:** N01 の cardinality 分岐直後に無条件の `remaining[0]` がある（[tools/spool_fold.py:454](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:454)、[tools/spool_fold.py:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:465)）。P02 は `更新` と `見送り` が別制御経路で、`見送り` は line 591 で早期 `continue` する（[tools/spool_fold.py:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:550)、[tools/spool_fold.py:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:591)）。項目7は両操作を一 fixture に混ぜている（[test_spool_fold.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:896)）。

**失敗シナリオ:**

- N01 の条件だけを無効化すると、欠落入力で `IndexError` になり、入力は依然受理されないまま node が赤くなる。
- P02 で completion 側の条件を `更新` へ広げるだけでも項目7は赤い。別 branch の `見送り` gate が注入されていなくても「更新/見送りを検出」と誤認できる。

**成果物影響:** mutation レポートが未検証の gate を検証済みとして扱い、受入 proof chain の帰属が不正になる。

**推奨:** N01 は欠落時に安全に no-issue へ進む複数 anchor を登録する。P02 は更新と見送りを別変異・別正例 node に分割する。

全登録変異の静的判定は次のとおり。

| 変異 | 判定 |
|---|---|
| N01 | 要修正。単純 gate 無効化は `IndexError` の偽 kill |
| N02 | 帰属可。各非 canonical 値が実際に受理へ変わる |
| N03 | 帰属可。重複の一方が残って plan が受理へ変わる |
| N04 | 登録 fixture への帰属可。ただし所見1の別 variant は未封鎖 |
| N05 | 帰属可。除去省略で canonical に `remaining:` が残る |
| N06 | 帰属可。禁制語付き完了が受理へ変わる |
| P02 | 要分割。更新と見送りは別 branch |
| N07 | 帰属可。項目10/11/12の exact splice が位置差を検出 |
| N08 | 帰属可。項目19の最初の正例が過剰拒否へ変わる |
| N09 | 帰属可。target 不在が no-op 受理へ変わる |
| N10 | 帰属可。完了記録へ実際に追記可能になる |
| N11 | 帰属可。曖昧 target が last-wins 受理へ変わる |
| N12 | replay fixture への帰属可。ただし gate の過剰拒否は所見2 |
| N13 | 帰属可。順序違反 fragment が受理へ変わる |
| N14 | 帰属可。逐次正例が `missing` の過剰拒否へ変わる |
| N15 | 要修正。所見3の downstream mask による診断 kill |

### 5. must-fix — 項目25と除外 resume 候補の代替 oracle が実装されていない

**根拠:** 事前登録は項目25で `operations` / `deferred_appends` を直接検査すると明記する（[mutation-prereg-2.md:42](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/mutation-prereg-2.md:42)）。実際の項目25は rendered worklog の active 集合しか見ず（[test_spool_fold.py:1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:1235)）、parse 結果を検査しない。resume の代替も「phase write 非発生」を要求している（[mutation-prereg-2.md:45](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/mutation-prereg-2.md:45)）が、既存 resume test は final bytes と `resumed_paths` だけで、append fixture でも write spy でもない（[test_spool_fold.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:716)）。

**失敗シナリオ:**

- 実装が append を完全に捨てても active は保存されるため、項目25単体は緑になる。
- append-as-operation 変異は inactive な T-050 により先に `transition-target` で赤くなる（[tools/spool_fold.py:1299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1299)）。
- resume が同じ `after_bytes` を再書込みしても、最終 bytes と `resumed_paths` を維持すれば既存 test は緑のままになる。

**成果物影響:** active 分離と resume 非再書込みを mutation/acceptance 証拠として認証できない。

**推奨:** `_parse_worklog_delta` の返値を直接検査し、append が `operations` に不在かつ `deferred_appends` に存在することを固定する。resume は append を含む phase target を既に after 状態にし、`_atomic_write` の phase 呼出しが 0 件であることを検査する。

## 総括

must-fix:

- 4-space の list-relative 未閉鎖 fence による `remaining` decoy bypass。
- raw substring replay guard による正当 suffix の過剰拒否。
- N15 の downstream mask／診断 kill。
- N01 の crash kill と P02 の非単一帰属。
- 項目25・resume の代替 structural oracle 欠落。

nit:

- なし。

静的に一致を確認できた点として、追記位置は先頭行末、fragment ごとの適用は逐次、`_strip_base` と `_insert_deferred` 本体は無変更だった。項目12は4形状すべてで before/after 全 bytes を exact splice 比較しており、位置や active 集合だけを見る恒真 oracle ではない（[test_spool_fold.py:967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:967)）。25項目に無条件の literal 恒真 test はないが、項目25は上記の破損実装を許す。