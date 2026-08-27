| 所見 | 親の判定 | 根拠 (file:line) |
|---|---|---|
| A1 | partial | old/new OID の正側投入自体は `tools/check_branch_rescue.py:983-999,1034-1044`。ただし `cat-file` の `missing` を `None` にした後、issue を出さず投入を省略する経路がある (`:543-548,997-998,1035-1038`)。m18/p06 の通常負例は有効 (`orchestrator/tests/test_check_branch_rescue.py:340-356`)。 |
| A2 | closed | production parser に child path option はなく (`tools/check_branch_rescue.py:1917-1936`)、注入は keyword-only の import seam に限定 (`:1733-1739`)。production CLI の拒否も固定 (`orchestrator/tests/test_check_branch_rescue.py:870-885`)。 |
| A3 | regressed | 全直接 child の env 設定はある (`tools/check_branch_rescue.py:209-224`) が、wrapper の shebang が `/usr/bin/env python3` で任意 PATH の Python を実行する (`:227-245`)。promisor missing も無 issue で捨てる (`:543-548,997-998`)。m25 は実際の missing object も wrapper 実行も通らない (`orchestrator/tests/test_check_branch_rescue.py:1038-1063`)。 |
| A4 | regressed | global config の観測は修正済み (`tools/check_branch_rescue.py:588-603`; m20 は `orchestrator/tests/test_check_branch_rescue.py:888-908`)。一方、有効な絶対期限を parser が扱わず (`tools/check_branch_rescue.py:615-637`)、rc=0 の `conservative-floor` へ落とす (`:1322-1355`)。追補 2 の網羅条件に反する (`s6-adjudication-addendum2.md:20-28`)。 |
| A5 | closed | prunable root は admin mtime を使わず assessment time の `conservative-floor` (`tools/check_branch_rescue.py:690-691,939-952`)。m21/p08 は前段拒否なく固有値を検査 (`orchestrator/tests/test_check_branch_rescue.py:706-731`)。 |
| A6 | closed | `--now` は production parser から消え (`tools/check_branch_rescue.py:1917-1936`)、時刻 seam は import 呼出しだけ (`:1733-1757`)。CLI 負例あり (`orchestrator/tests/test_check_branch_rescue.py:870-885`)。 |
| A7 | closed | 7 field、bare、locked/prunable、C-quote を処理 (`tools/check_branch_rescue.py:409-480`)。未知 field の撤去対象だけ completeness を失う (`:868-925`)。m19/p05 は固有分岐へ到達 (`orchestrator/tests/test_check_branch_rescue.py:911-977`)。 |
| A8 | regressed | ref/path の surrogateescape 化はある (`tools/check_branch_rescue.py:347-369`) が、snapshot digest が `ensure_ascii=False` の結果を strict UTF-8 encode する (`:1101-1103`)。非 UTF-8 ref で `UnicodeEncodeError` となり、外側の catch 対象外 (`:1897`)。現テストは snapshot を通らない (`orchestrator/tests/test_check_branch_rescue.py:980-996`)。 |
| A9 | partial | `fromtimestamp` の範囲外は集約済み (`tools/check_branch_rescue.py:719-725`)。しかし timestamp 自体は有効でも expiry 加算が overflow する経路は未処理 (`:675-687`)。テストは前者だけ (`orchestrator/tests/test_check_branch_rescue.py:999-1011`)。 |
| A10 | closed | 旧 headroom field は消え、26 field と標本由来 field が固定 (`tools/check_branch_rescue.py:70-97`; `docs/unreachable-object-ledger.md:12-41`)。閾値算術も検査 (`tools/check_branch_rescue.py:1517-1525`)。 |
| A11 | closed | 非空閉包と ledger-check の両 child、全直接 child env、repository control bytes を同一 fixture で確認 (`orchestrator/tests/test_check_branch_rescue.py:598-650,772-786`)。固定 child 起動は `tools/check_branch_rescue.py:1410-1427,1580-1588`。 |
| A12 | closed | candidate tip を main に戻し、過去 commit が reflog にしかない。A1 投入を丸ごと除去すれば closure assert が落ちる (`orchestrator/tests/test_check_branch_rescue.py:340-356`)。m18/p06 は単一理由性あり。 |
| A13 | closed | m26 用 future pack mtime と m28/p07 用 status fixture が分離され、前段拒否なく別々の assert へ到達 (`orchestrator/tests/test_check_branch_rescue.py:465-505`)。 |
| A14 | closed | 実装は依然として同一 OID の source だけを伝播 (`tools/check_branch_rescue.py:1356-1364`)。ただし本 wave では実装せず次へ送る、という親裁定どおり (`s6-adjudication.md:89-94`)。ここでの closed は裁定への適合を意味する。 |
| B1 | closed | 新 payload 全階層から field は消え、旧 landed checker 境界の検査だけ残る (`tools/check_branch_rescue.py:1441-1449,1677-1730`)。m24 の再帰 assert あり (`orchestrator/tests/test_check_branch_rescue.py:569-585`)。 |
| B2 | closed | 終端の一意性と最終行を検査 (`tools/check_branch_rescue.py:1600-1625`)。m22 は終端欠落だけで rc=2 になる (`orchestrator/tests/test_check_branch_rescue.py:1022-1035`)。 |
| B3 | partial | m23 の frontmatter 負例は単一理由性あり (`orchestrator/tests/test_branch_rescue_ledger.py:125-134`)。しかし fence 除外は backtick だけ (`:25-48`) で、CommonMark の tilde fence 内の偽 bullet を実行配線として受理する (`:51-92`)。 |
| B4 | closed | `gc_headroom_at_loss` は schema と文書の双方から消え、fanout/count/threshold/version に分離 (`tools/check_branch_rescue.py:70-97,1489-1525`; `docs/unreachable-object-ledger.md:31-36`)。 |
| 親 D2 | closed | locked の単独・理由付き両形式を受理 (`tools/check_branch_rescue.py:426-477`; `orchestrator/tests/test_check_branch_rescue.py:911-949`)。親 dogfood でも rc=0 (`parent-dogfood2.md:20-36`)。 |
| 親 D4 | closed | 親実走で対象 3 test file が 609 passed、`check_docs` も rc=0 (`parent-dogfood2.md:6-15`)。fix 報告の byte 一致と digest も整合 (`s6-fix3.md:75-83`)。 |

### 所見 A1 が閉じていない理由
- 重大度: blocker
- 根拠: `tools/check_branch_rescue.py:543-548,983-999,1034-1038`
- 再現: candidate または撤去 worktree の reflog old/new OID が promisor commit で、ローカルに無い状態にする。`GIT_NO_LAZY_FETCH=1` により `cat-file` は `missing` を返すが、実装は issue を出さず正側投入を省略する。
- 成果物影響: 削除で失われる可能性がある reflog-only commit が閉包から消え、rc=0 になり得る。
- 提案: reflog OID の type が `None` なら `promisor-object-missing` 等を記録して rc=2 にする。blob 等と判定できた OIDだけを安全に除外する。

### 所見 A3 が閉じていない理由
- 重大度: blocker
- 根拠: `tools/check_branch_rescue.py:209-245,543-548`; `orchestrator/tests/test_check_branch_rescue.py:1038-1063`
- 再現: PATH 先頭の directory に正規 Git への symlink と任意の `python3` を置く。直接 Git は正規 symlink を使うが、landed checker の子孫 Git 用 wrapper は `/usr/bin/env python3` から任意 executable を起動する。また m25 fixture は object を欠落させないため lazy fetch 経路自体を通らない。
- 成果物影響: read-only gate が任意コードを実行でき、promisor 欠落も rc=2 にならない。
- 提案: wrapper は固定 interpreter と absolute に解決した Git だけを使う。実際に promisor object を欠落させた fixture で、wrapper を外す変異、object DB 不変、missing issue と rc=2 を検査する。

### 所見 A4 が閉じていない理由
- 重大度: must-fix
- 根拠: `s6-adjudication-addendum2.md:20-28`; `tools/check_branch_rescue.py:615-637,1322-1355`
- 再現: loose candidate に有効な絶対表現、例えば `gc.pruneExpire=2030-02-01` を設定する。相対 duration の regex に一致せず、未知形と同じ `conservative-floor`、rc=0 になる。
- 成果物影響: `conservative-floor` の受理事由が追補 2 の網羅された 4 事由を超え、期限契約が縮退する。
- 提案: Git が受理する絶対期限を別分岐で安全に解釈し、determinate な固定 cutoff を導く。相対、絶対、never、未知形を独立 fixture にする。

### 所見 A8 が閉じていない理由
- 重大度: must-fix
- 根拠: `tools/check_branch_rescue.py:347-369,1101-1103,1897`; `orchestrator/tests/test_check_branch_rescue.py:980-996`
- 再現: `for-each-ref` に `refs/tags/nonutf8-\xff` を含める。`os.fsdecode` は surrogate を保持するが、snapshot digest の UTF-8 strict encode で `UnicodeEncodeError` が送出される。
- 成果物影響: 従来の定義済み rc=2 より悪い traceback 終了となり、Git が扱える repo を受理できない。
- 提案: canonical digest も `ensure_ascii=True` の ASCII bytes で計算し、非 UTF-8 ref を含む end-to-end fixture を snapshot と JSON 出力まで通す。

### 所見 A9 が閉じていない理由
- 重大度: must-fix
- 根拠: `tools/check_branch_rescue.py:675-687,719-725,1897`
- 再現: timestamp を `253402214400`、reflog expiry を `30.days.ago` とする。`fromtimestamp` は 9999-12-31 として成功するが、`timestamp + span` が `OverflowError` になる。
- 成果物影響: parse failure が定義済み JSON と rc=2 に集約されず、未定義終了する。
- 提案: expiry 加算と UTC 直列化までを範囲検査し、overflow を `reflog-parse-error`、rc=2 に変換する負例を足す。

### 所見 B3 が閉じていない理由
- 重大度: must-fix
- 根拠: `orchestrator/tests/test_branch_rescue_ledger.py:25-48,51-92,125-143`
- 再現: §1 の本文に `~~~` fence を置き、その中だけに rescue command と audit/ledger の条件を満たす 2 bullet を置く。tilde fence は除外されないため `_has_cleanup_execution_edges()` が true になる。
- 成果物影響: 実行 caller が消えても、コード例だけで配線検査が通る。
- 提案: backtick と tilde の両 CommonMark fence を除外し、否定語 blacklist ではなく明示的な実行命令形を正側条件にする。

## 総括

- closed: 14 件
- partial: 3 件
- regressed: 3 件
- この実装を land してよいか: **NO-GO**
- fix 子の申告と自分の判定が食い違った所見: **6 件**
- 親 dogfood E6 の差は偶然ではない。branch-only では worktree HEAD/index が恒久負側へ入る一方 (`tools/check_branch_rescue.py:953-962`)、`--retire-worktree` 併用時は正側へ移り (`:862-863,923-938`)、意図した機構と一致する (`parent-dogfood2.md:73-93`)。
- 本レビューは静的検査のみ。pytest を含むコマンドは実走していない。