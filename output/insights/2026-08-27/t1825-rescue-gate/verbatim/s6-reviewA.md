### 所見 1: 削除される branch の reflog-only commit が正側 root から消え、閉包を過小報告する
- 重大度: blocker
- 向き: 過小報告
- 根拠: tools/check_branch_rescue.py:845, tools/check_branch_rescue.py:990
- 再現: `topic` を commit C1 から `main` へ強制移動してから `--branch topic` を実行する。C1 は candidate reflog だけが保持するが、reflog file は parse されず丸ごと `continue` され、正側には現在 tip の `main` しか入らない。閉包は空、rc=0 になり得る一方、`git branch -d topic` は reflog も消すため C1 が到達不能になる。
- 成果物影響: C1 は `deletion_loss_closure` と台帳候補の両方から完全に欠落する。
- 提案: candidate reflog の old/new OID を検査して commit 到達可能なものを `removed_source_oids` に加え、読取・parse 不能は rc=2 にする。

### 所見 2: 任意の landed checker / audit tool を起動でき、read-only 契約を直接破れる
- 重大度: blocker
- 向き: 正しさ以外
- 根拠: tools/check_branch_rescue.py:1253, tools/check_branch_rescue.py:1417, tools/check_branch_rescue.py:1752
- 再現: `--ledger-check --audit-tool /abs/mutate.py` を指定し、同 script で `git update-ref` 後に正常な「要確認 0 件」出力を返す。audit は snapshot 終了後に実行されるため変更は再検査されず、rc=0 も可能である。landed checker も任意 path を実行でき、rc=2 で検出しても既に行った変更は戻らない。
- 成果物影響: ref、index、config、object、任意の作業 file を変更でき、「This command is read-only」が偽になる。
- 提案: test 用 path 注入を production CLI から除去し、固定 child の完全な subprocess 契約を検査する。必要なら read-only sandbox を子孫全体へ適用する。

### 所見 3: partial clone では `cat-file` が lazy fetch し、object database を変更し得る
- 重大度: blocker
- 向き: 正しさ以外
- 根拠: tools/check_branch_rescue.py:216, tools/check_branch_rescue.py:424, tools/check_branch_rescue.py:455
- 再現: promisor remote を持つ blobless / sparse clone で、index が参照する未取得 object を `_cat_types()` に渡す。環境に `GIT_NO_LAZY_FETCH` がなく、`cat-file --batch-check` が object を取得して pack、lock、一時 file を object database に作成し得る。
- 成果物影響: 単なる preview が network I/O と `.git/objects` の永続変更を起こす。
- 提案: 全 Git 子孫に `GIT_NO_LAZY_FETCH=1` を固定し、promisor missing は issue として fail-closed にする。partial clone fixture で object database 不変を検査する。

### 所見 4: global / system の実効 gc 設定を捨てるため、期限下界が未来へずれる
- 重大度: blocker
- 向き: 過小報告
- 根拠: tools/check_branch_rescue.py:216, tools/check_branch_rescue.py:666, tools/check_branch_rescue.py:1177
- 再現: repository local では未設定、global config に `gc.pruneExpire=now` を設定する。checker は global/system config を無効化して既定の 2 weeks を採り、最近の loose commit に未来の確定期限を出す。通常環境の Git は global 設定を使うため、branch 削除直後から prune 可能である。
- 成果物影響: `loss_possible_not_before`、reflog/worktree expiry、gc.auto proximity が実際の cleanup 環境より安全側へずれる。
- 提案: cleanup と同じ実効 config 全 scope を観測する。安全上読めない scope がある場合は既定値へ倒さず rc=2 にする。

### 所見 5: prunable worktree の期限を administrative directory 自体の mtime から計算している
- 重大度: blocker
- 向き: 過小報告
- 根拠: tools/check_branch_rescue.py:581
- 再現: target が消えた unlocked worktree で、Git の expiry 判定対象になる admin file を期限より古くし、admin directory だけを新しい mtime にする。Git 2.34.1 では直ちに prune 可能でも、実装は directory mtime に `gc.worktreePruneExpire` を加えて未来を返す。
- 成果物影響: prunable HEAD/index/reflog が保持する commit の `loss_possible_not_before` が真の最早喪失時刻より未来になる。
- 提案: Git 2.34.1 の `should_prune_worktree` と同じ administrative file、欠損、lock、expiry の判定を再現する。

### 所見 6: hidden な `--now` が任意の未来時刻を受理し、全 retention floor を偽装できる
- 重大度: blocker
- 向き: 過小報告
- 根拠: tools/check_branch_rescue.py:1571, tools/check_branch_rescue.py:1751
- 再現: loose candidate に `--now 2099-01-01T00:00:00Z` を指定する。`max(now, mtime + pruneExpire)` により 2099 年の determinate deadline と rc=0 を出せるが、実際の Git clock では現在から prune 可能である。packed、alternate、mtime 取得失敗の保守 floor も同じ注入時刻になる。
- 成果物影響: `loss_possible_not_before` が任意に未来へ移動し、期限通知も遅延する。
- 提案: production CLI から `--now` を除去し、時刻注入は import 時の test seam に限定する。残す場合は system clock との差を厳格に拒否する。

### 所見 7: worktree porcelain の有効な `bare` record と C-quoted path を受理できない
- 重大度: must-fix
- 向き: 実環境で成立しない
- 根拠: tools/check_branch_rescue.py:322
- 再現: bare common repository に linked worktree を作ると、一覧に HEAD を持たない `bare` record が現れ、unknown field または incomplete record になる。また newline 等を含む有効な worktree path は quoted 表現になり、`Path(...).is_absolute()` 判定で拒否される。
- 成果物影響: 該当 repository では候補に関係なく rc=2 となり、閉包を一度も描けない。
- 提案: Git 2.34.1 の全 record variant をモデル化し、bare record を HEAD/index root として扱わない。path は NUL 形式が利用可能ならそれを使い、不能なら Git の quote 規則で復号する。

### 所見 8: CLI と ref parser が Git の有効な refname 集合より狭い
- 重大度: must-fix
- 向き: 実環境で成立しない
- 根拠: tools/check_branch_rescue.py:36, tools/check_branch_rescue.py:309, tools/check_branch_rescue.py:1766
- 再現: Git が受理する `topic+rescue` のような branch は ASCII allowlist により rc=64 になる。また permanent `refs/*` に非 UTF-8 byte を含む有効な refname があると、`for-each-ref` の出力を strict UTF-8 decode して rc=2 になる。
- 成果物影響: Git が扱える branch/ref を持つ repository の一部が checker の受理集合から外れる。
- 提案: branch 妥当性は `git check-ref-format --branch` 相当で判定し、refname は byte-safe な可逆表現で inventory と JSON に格納する。

### 所見 9: 範囲外 reflog timestamp が定義済み rc へ集約されず例外終了する
- 重大度: must-fix
- 向き: 実環境で成立しない
- 根拠: tools/check_branch_rescue.py:553, tools/check_branch_rescue.py:631, tools/check_branch_rescue.py:1712
- 再現: old/new OID、identity、timezone は正常で、timestamp が `253402300800` の reflog 行を置く。`int()` と表面検査は通るが `datetime.fromtimestamp()` が `ValueError` を送出し、外側の catch 対象外なので rc=1相当の traceback 終了になる。
- 成果物影響: 壊れた administrative entry が rc=2 JSON ではなく、schema 出力なしの未定義終了になる。
- 提案: timestamp の Git 互換範囲を検査し、`ValueError` と `OverflowError` を `reflog-parse-error` に変換する。

### 所見 10: ledger schema が禁止された総 loose 数由来の headroom を区別も拒否もできない
- 重大度: must-fix
- 向き: 過大報告
- 根拠: tools/check_branch_rescue.py:65, tools/check_branch_rescue.py:1338
- 再現: ledger に `gc_auto_threshold=6700`、`loose_count_at_loss=6422`、`gc_headroom_at_loss=278` を置いても、型だけが検査され受理される。fanout `17` の sample、閾値、heuristic version を示す field はない。
- 成果物影響: 裁定で禁止された総数由来の偽 headroom が正常な ledger entry として残る。
- 提案: field を sample fanout、sample count、sample threshold に改名して arithmetic と version を検証するか、headroom field 自体を削除する。

### 所見 11: m16 と repository 不変テストは child subprocess を一度も覆っていない
- 重大度: must-fix
- 向き: 検出力
- 根拠: orchestrator/tests/test_check_branch_rescue.py:540, orchestrator/tests/test_check_branch_rescue.py:695
- 再現: m16 は `topic == main` で空閉包かつ ledger-check 無しなので、観測される subprocess は直接 Git だけである。不変テストも同じ空閉包である。landed/audit child に書込みを追加しても両テストはその経路へ到達しない。
- 成果物影響: s5-A の「read-only mutation killed」という対応表が subprocess 全経路の証拠にならない。
- 提案: 非空閉包と ledger-check を別々に通し、child と全子孫を含む argv および repo control bytes の不変を検査する。

### 所見 12: m03 fixture は candidate reflog を完全に無視する変異を殺さない
- 重大度: must-fix
- 向き: 検出力
- 根拠: orchestrator/tests/test_check_branch_rescue.py:303
- 再現: fixture の reflog OID は現在の candidate tip と同じであり、その tip は branch ref から既に正側へ入る。candidate reflog の parse と正側投入を丸ごと削除しても、現在の全 assert が通る。
- 成果物影響: 所見1の不可逆な過小報告が、28 test green のまま残る。
- 提案: candidate を C1 から `main` へ戻し、C1 が reflog にしか存在しない fixture で、C1 の閉包出現と parse failure の rc=2 を検査する。

### 所見 13: m10 と m11 の共用 fixture は pack mtime 変異を独立には殺さない
- 重大度: should-fix
- 向き: 検出力
- 根拠: orchestrator/tests/test_check_branch_rescue.py:427
- 再現: pack mtime は 2000 年、assessment は 2030 年である。変異が `max(now, pack_mtime + pruneExpire)` を内部値に使っても結果は同じ assessment time になり、status/basis を変えない数値変異は生存する。現在の status assert は主として m11 を殺している。
- 成果物影響: s5-A の m10 KILLED は m11 と独立した証拠にならない。
- 提案: pack mtime を assessment より未来側へ置く m10 専用 fixture と、status だけを変える m11 fixture に分離する。

### 所見 14: 期限付き root が保持する祖先 commit の additional source が欠落する
- 重大度: should-fix
- 向き: 過小報告
- 根拠: tools/check_branch_rescue.py:1195
- 再現: surviving reflog または prunable worktree HEAD が C2 を指し、candidate closure が親 C1 と C2 を含む場合、C2 は C1 も保持する。しかし `item["oid"] == oid` の完全一致しか見ないため、C1 の `additional_sources` は空になり得る。
- 成果物影響: rc=0 のまま C1 の retention source と下界が過小になり、不要に早い期限として表示される。
- 提案: 各期限付き root から loss closure 内への到達関係を一括計算し、祖先 commit にも source と expiry を伝播する。

## 総括

- blocker: 6 件
- must-fix: 6 件
- should-fix: 2 件
- この実装を land してよいか: NO-GO
- 最も見落としやすい点: candidate reflog は「負側へ入れない」だけでは足りず、削除で失われる過去 OIDを正側へ入れなければ、その commit は閉包から完全に消える。
- 検査方法: 指定された資料だけによる静的検査。テストは実走していない。