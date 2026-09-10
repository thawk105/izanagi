# 実装プラン v1

## 1. 採用する述語

merge result の regular-file blob を `R`、各親の同一 path の blob を `P1 ... Pn` とする。blob は decode せず、`bytes.split(b"\n")` により LF 区切りの bytes 列へ変換する。末尾の空要素を残すため、最終改行の追加・削除も差として扱える。

path を「merge 自身による著作行なし」とする条件は、次の連言とする。

1. result と全親に同じ mode の regular blob が存在する。
2. `R` の各 byte-line 値が、少なくとも1親に存在する。
3. 各 line 値について、`R` の出現回数が全親で利用可能な出現回数の合計を超えない。
4. すべての親について `Pi` が `R` の subsequence である。すなわち `R` は全親の共通 supersequence であり、各親の行順を保存する。

これは「各行がどこかの親にある」という集合包含より強い。親の行を削除した結果、親内部の順序を入れ替えた結果、親Aの一部と親Bの一部を選択して残りを落とした結果は、少なくとも1親を subsequence として埋め込めず実装面に残る。

shortest common supersequence までは要求しない。checker やテストのように同一の `)`、空行、`KnownViolationSpec(` が多数あるファイルでは、byte-line の LCS が別ブロックの同値行を同一視し、正当な独立追加の union まで落とせなくなるためである。

### 10件への適用結果

親の10件は従来の「行値がどこかの親にある」という意味では全件 novel 0 のままだが、上記の順序条件まで満たして実装面から外れるのは4件だけである。

| SHA | 現行 `--cc` path数 | 共通 supersequence | 新判定 |
|---|---:|---|---|
| `a5b7045b12` | 2 | 不成立 | 台帳に残す |
| `311d463f89` | 3 | 不成立 | 台帳に残す |
| `5823caf328` | 2 | 全pathで成立 | 撤去 |
| `8440a14850` | 2 | 不成立 | 台帳に残す |
| `e39a8d4656` | 2 | 不成立 | 台帳に残す |
| `3eaf2038ec` | 2 | 全pathで成立 | 撤去 |
| `387a1daab0` | 2 | 不成立 | 台帳に残す |
| `e86d363a87` | 1 | 不成立 | 台帳に残す |
| `0c0f3e71b3` | 2 | 全pathで成立 | 撤去 |
| `bf92f327ca` | 2 | 全pathで成立 | 撤去 |

`b9c07cc22d` は2つの実装面 pathを持ち、親にない18行があるため引き続き実装面となる。

## 2. `tools/check_ai_provenance.py`

### bytes/blob helper

[tools/check_ai_provenance.py:1539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1539) の `_combined_diff_paths()` 直後に、次を挿入する。

- combined raw recordから、各親とresultの mode・object IDを得る helper。
- 複数の blob IDを1回の `git cat-file --batch` で取得する helper。headerのsizeだけを読み、そのbyte数と末尾LFを厳密に検証する。blob本文は一度も decode しない。
- LFだけを区切りとして保持する `_byte_lines()`。
- bytes列の線形 subsequence 判定。
- 上記4条件を実装する `_has_merge_authored_lines()`。
- candidate群を「著作あり、または安全に除外不能」な path だけへ絞る `_merge_authored_paths()`。

Git protocol、object type、size、path対応が不正なら黙って免除せず `RuntimeError` とし、既存の [main例外処理:3059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:3059) により rc=2へ倒す。

### `_commit_paths()` の差し替え

[tools/check_ai_provenance.py:1587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1587) の merge 分岐を次の三段にする。

1. 現行どおり、全親との差分 path の積集合を求める。
2. 現行 `_combined_diff_paths()` を通し、combined patchが空の自明な pathを先に除く。
3. 残った pathだけを `_merge_authored_paths(commit, parents, combined)` へ渡す。

したがって `_combined_diff_paths()` は置換せず、直列の第一絞り込みとして保存する。特に [非競合shared-pathテスト:1481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1481) の既存挙動を変えず、combined patchが非空なのに親由来だけだった偽陽性だけを第二段で是正する。

commit前の [_message_file_paths():1640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:1640) は変更しない。既存テストのコメントどおり、preflightは引き続き保守的にCodex authorを要求する。

### 特殊 object/path の扱い

| ケース | 処理 |
|---|---|
| binary | Gitがbinaryとして出したもの、または参加blobにNULを含むものは順序述語を適用せず必ず残す。 |
| UTF-8 decode不能 | NULを含まなければLF区切りbytesとして処理する。decodeしない。 |
| resultで削除 | result entry不在なので必ず残す。空列の空虚な成功にはしない。 |
| merge中の新規追加 | いずれかの親にentryがなければ必ず残す。 |
| rename | 現行 `--no-renames` を保存し、delete/addとして扱う。delete側が残るためrename推定による免除は作らない。 |
| gitlink | mode `160000` は行述語の対象外として必ず残す。 |
| symlink | mode `120000` はtarget文字列が親由来でも必ず残す。 |
| mode変更のみ | resultと全親のmodeが完全一致しなければ必ず残す。 |
| octopus merge | 全親に対して同じsubsequence条件を連言する。親数に対する探索はなく、既存4親fixtureも扱える。 |

### 計算量とGit問い合わせ数

1 pathあたりの計算量は `O(|R| + Σ|Pi|)`、メモリも同程度。共通 supersequenceの最短化問題は解かないため、親数に関する指数計算はない。

射影履歴には5346 commit中1492 merge、parent edge合計2986、最大4親がある。現行の親取得、親別path差分、candidate別`--cc`問い合わせは保存する。その上で、combined candidateがあるmergeごとに、

- combined raw metadata取得 1回
- 全unique blobの `cat-file --batch` 1回

の最大2回を追加する。最悪上限は2984 Git subprocessだが、combined candidateが空のmergeでは追加0回である。親またはpathごとの `git show` は使わない。

## 3. 台帳と逐語ミラー

是正採用時は53件から49件、`missing-codex-author` は19件から15件になる。

| 撤去SHA | checker entry | mirror `expected` | checkerで孤児になる定数 |
|---|---|---|---|
| `5823caf328a5985476cd2f6f7aa0d13daa5b08f6` | [736-741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:736) | [2054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2054) | `_T567_MERGE2_RULING`, `_T567_MERGE2_NOTE` [206-224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:206) |
| `3eaf2038ec2ac3e7965c2a1eedcadb1ed1266626` | [815-820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:815) | [2125-2140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2125) | `_T1476_MERGE3_RULING`, `_T1476_MERGE3_NOTE` [292-305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:292) |
| `0c0f3e71b3208370be8d4e7e20a84a2152afe4b2` | [846-851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:846) | [2177-2193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2177) | `_T1458_MERGE3_RULING`, `_T1458_MERGE3_NOTE` [333-348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:333) |
| `bf92f327cadfbe626e37cab73d55abe80d3994dd` | [852-857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:852) | [2194-2220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2194) | `_T1458_MERGE5_RULING`, `_T1458_MERGE5_NOTE` [349-374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:349) |

ミラーテスト側では、`5823...` 撤去によりローカル変数 `t567_merge2_ruling` / `t567_merge2_note` [1897-1915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1897) も孤児になるため同時に削除する。他の3件は `expected` 内へ逐語でinlineされており、テスト側の対応する定数はない。

残る6 SHAと `b9c07cc22d...` のエントリ・ruling・noteは変更しない。片側だけ先に削除すると [known-violation-stale判定:2143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/tools/check_ai_provenance.py:2143) によりrc=2となるため、checker台帳、孤児定数、mirror expectedを同一commitで更新する。

## 4. テスト設計

既存ファイルのmergeテスト群 [1431-1743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1431) へ追加する。新設test fileは作らないため自走harness追加は不要。

1. `test_real_b9c07cc22d_with_novel_lines_remains_implementation_surface`

   exact SHA `b9c07cc22d483a9103dac208a83446872161ffad` に対し、`_commit_paths()` が次の2 pathを返すことを固定する。

   - `orchestrator/tests/test_check_ai_provenance.py`
   - `tools/check_ai_provenance.py`

   これにより、著作行が1行でもあれば従来どおりCodex author契約が発火する負例とする。

2. `test_merge_reordered_parent_lines_remains_implementation_surface`

   両親が同じ実装fileを変更するfixtureを作り、merge結果を「全行値は親由来だが、親内の一意なsentinel行を逆順にした」内容でcommitする。次をすべてassertする。

   - 旧集合包含条件ならnovel 0。
   - `_combined_diff_paths()` では非空。
   - 親の少なくとも1つがresultのsubsequenceにならない。
   - `_commit_paths()` は対象pathを返す。
   - Claude-only messageへのauditは `missing-codex-author`。

3. `test_merge_parent_order_union_has_no_authored_lines`

   両親が同じanchor位置へ別々の一意なblockを追加して競合させ、resultを親順序を保存した単純unionにする。次をassertする。

   - merge commandは競合を返す。
   - combined patchは非空。
   - resultは両親の共通 supersequence。
   - 全result行は親由来。
   - `_commit_paths()` は空。
   - Claude-only mergeのaudit findingも空。

4. [invalid UTF-8 fixture:1548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1548) は削除せず、新しいblob loaderを実際に通過することをコメントとassertで固定する。`UnicodeDecodeError` が発生せず、novel lineを含むため対象pathが残ることを維持する。

5. [octopus fixture:1595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:1595) は4親すべてを新述語へ渡し、`merge-authored line` により `tools/resolution.py` が残ることを維持する。

6. pure helperのparametrizeを同じmergeテスト群へ追加し、binary、result deletion、親entry欠落、gitlink、symlink、mode不一致がすべて「著作ありまたは除外不能」へ倒れることを固定する。batch protocolの切断・size不一致は `RuntimeError` になる負例も置く。

射影された現行ファイルには `REAL_REPO_SERIAL_NODES` というsymbolは存在しない。実在するreal-repo直列テストは [test_known_violation_ledger_matches_real_commit_findings:2290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-known-violation-review-20260823/orchestrator/tests/test_check_ai_provenance.py:2290) だが、対象リストは `8ceebcd...` までで今回の4 SHAを含まない。したがってそこは変更せず、`b9c...` は独立したexact-SHA regression testにする。

pytestは実行していない。今回行ったのは指定資料とGit objectのread-onlyな静的比較だけである。

## 5. D721との関係

本プランはD721の射程内であり、現行裁定に反する、と判断する。

[D721:3-15](/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/D721.md:3) の中心理由は、最終形だけでは自動解決と手動解決を区別できず、親由来行だけの手動競合解決にも編集上の判断がある、というものだった。本述語も最終resultと親blobしか見ない。さらに必須のnovel 0正例は、競合後に手でunionを書き込むfixtureであり、D721が明示的に却下した正例と同型である。

共通 supersequence化により旧形状述語より偽陽性候補を10件から4件へ狭められるが、「手動unionをCodex author不要にする」という本質は変わらない。したがってD721を維持したまま実装・台帳撤去をlandしてはならない。段4でD721を明示的にsupersedeする再裁定が得られた場合だけ、上記変更へ進む。再裁定がなければコード変更0、台帳撤去0が正しい終端である。

## 総括

- (a) 採るべき述語: combined diff非空のregular-file pathについて、resultの全byte-lineが親由来で、出現数が親の総容量内にあり、かつ全親のbyte-line列を順序どおり含む共通 supersequenceである場合だけ「著作行なし」とする。
- (b) 想定撤去件数: 再裁定後に4件、D721が維持されるなら0件。
- (c) 最大のリスク: 最終blob比較では手動競合解決という編集上の判断を観測できず、D721が拒否した受理集合の拡大を再導入すること。
- (d) D721への判断: 射程内で明確に反するため、実装前にD721をsupersedeするユーザー再裁定が必須。