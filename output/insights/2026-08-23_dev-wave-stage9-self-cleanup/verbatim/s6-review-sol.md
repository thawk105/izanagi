静的レビューのみです。read-only のため `pytest` は実走しておらず、緑は主張しません。

## 裁定照合

`○` は実装済み、`△` は裁定どおりの残余または不完全、`×` は防壁が実効でないことを示します。

| 裁定 | 判定 | 実装照合 |
|---|---:|---|
| §4-1 所有条件 | △ | common-dir は `dev_wave_cleanup.py:493-500,540-541`、tip/clean/ancestry は `:422-453,517-545`。同一 invocation の所有権は証明しない。 |
| §4-2 path 差替え | △ | 裁定どおり quarantine なし。検証と削除は `:551-553` の別操作。 |
| §4-3 path 正規化 | ○ | raw spelling は `:138-179`、porcelain byte 一致は `:268-299`、削除値は `VerifiedWavePath` 経由の `:538-553`。 |
| §4-4 branch CAS | △ | tip/ancestry 再検査は `:665-670`、削除診断照合は `:601-613`。CAS はなく、事後検出だけ。 |
| §4-5 occupancy | A3 | A3 の緩和述語を `:383-413` に実装したが、下記所見 1 の false negative がある。 |
| §4-6 ignored/job | △ | tracked/untracked は `:422-428`。ignored byte と remote job はコード上未防護。 |
| §4-7 global prune | ○ | dry-run と現存 directory 拒否は `:556-576,655-663`。検査と prune 間の排他はない。 |
| §4-8 land 部分成功 | △ | fold state は `:520-526`。親の `landed` 判定は CLI 入力にも receipt にも束縛されない。 |
| §4-9 reflog | × | branch reflog だけを `:437-453` で検査し、linked-worktree の HEAD reflog を見ない。 |
| §4-10 5 状態 | × | 分類は `:463-479`。状態 c が過広で、canonical prefix 以外も受理する。 |
| §4-11 allowlist | × | wrapper は `:182-216` にあるが、`branch -d -f` が通る。 |
| §4-12 実測限定 | — | 文書・測定上の裁定であり、この 4 実装対象に runtime 述語はない。 |
| A1 | ○ | `worktree list --porcelain` は `:292-294`。制御文字・曖昧 record は `:237-289` で拒否。 |
| A2 | ○/残余 | 訂正後の命令形は `:437-453`。ただし検査対象が branch reflog に限定される。 |
| A3 | × | 緩和された受理条件は実装済みだが、「cmdline が worker を捕捉する」は成立せず、診断値も cleanup の報告から消える。 |
| A4 | ○ | zombie 判定は `check_worktree_occupancy.py:195-203,291-303`、件数出力は `:467-483`。State 読取失敗は `False` に倒れ、元の cwd issue が残るため fail-closed。非 zombie 回帰は `test_check_worktree_occupancy.py:589-612`。 |
| A5 | — | 手続裁定。テスト未実走なので acceptance の有効性は確認不能。 |
| A6 | ○ | 緩和正例は `test_dev_wave_cleanup.py:228-257`、occupants/issues 拒否は `:207-225` に残る。 |

### 所見 1

- 主張: A3 の「cwd を読めなくても cmdline で worker を捕捉する」という根拠は偽で、稼働中 worker の byte を `removed` として削除できる。
- 具体的な破れ方: same-UID worker が non-dumpable、cwd が対象 worktree、argv が `["/usr/bin/python3", "worker.py"]`、出力先が ignored の `.cache/result.bin` とする。cwd は `PermissionError`、相対 argv は process cwd 不明なので照合から落ち、`same_uid_cwd_unreachable` だけが残って status は `unoccupied` になる。`git status` に ignored file は出ず、二度目の occupancy も通り、`shutil.rmtree` が実行中の成果物を削除する。
- 根拠: `ruling.md:116-130`、`check_worktree_occupancy.py:276-317,447-452`、`dev_wave_cleanup.py:405-428,545,645`。テスト自身も `comm="worker"` を非 blocking として固定する (`test_dev_wave_cleanup.py:228-257`)。
- **成果物影響 (1 行)**: 撤去受理集合に「cwd が読めず argv に絶対 path を持たない live worker」が入り、ignored の生成途中 byte が消え、台帳は `removed` になる。
- 提案する対処: **scope 外として裁定へ返す**。scheduler/job lease と終端証明を必須化し、少なくとも same-UID 到達不能 process を無条件受理しない。

### 所見 2

- 主張: reflog 検査は branch reflog しか走査せず、linked-worktree の HEAD reflog にだけ残る commit を失う。
- 具体的な破れ方: worktree を detach し、commit U を作り、detached のまま landed tip T へ reset してから branch を再 checkout する。U は worktree HEAD reflog にだけ残り、branch reflog 検査は T だけを見て通る。directory と administrative record の削除で HEAD reflog が消え、branch 削除後に U は後続 GC の回収対象になる。
- 根拠: 検査対象は `git rev-list --walk-reflogs refs/heads/<branch>` だけ (`dev_wave_cleanup.py:437-453`)。既存テストは branch に接続したまま U を commit しており、同じ欠落を共有する (`test_dev_wave_cleanup.py:357-366`)。
- **成果物影響 (1 行)**: worktree HEAD reflog 専有 commit が撤去受理集合から漏れ、回収可能だった commit object とその tree/blob が失われる。
- 提案する対処: **実装で閉じる**。対象 administrative gitdir の `logs/HEAD` が参照する全 commit も main ancestry 検査へ入れ、detached-commit fixture を追加する。

### 所見 3

- 主張: 状態 c は「directory 不在・record 存在・branch 存在」だけで成立し、record と削除 branch の束縛を要求しない。
- 具体的な破れ方: 不在 path P の stale record が `branch=refs/heads/other, HEAD=T`、別の未 checkout branch `wave` も T を指し、T は main に landed 済みとする。`--wave-worktree=P --wave-branch=wave --tested-wave-tip-sha=T` は c に分類され、P の registry record を prune し、無関係な `wave` branch を削除して `removed` を返す。
- 根拠: c の条件は record の `detached/branch` を見ない (`dev_wave_cleanup.py:463-479`)。後続も record HEAD と「他 record が target ref を保持していないこと」しか検査しない (`:529-545`)。prune と branch 削除は `:654-680`。
- **成果物影響 (1 行)**: 一つの cleanup で P の administrative record と別 ref `wave` が混成対象として消え、台帳は正常な単一対象撤去として `removed` になる。
- 提案する対処: **実装で閉じる**。c は `record.detached is True && record.branch is None && record.head == tip` を必須にし、全状態を完全な積 predicate として列挙する。

### 所見 4

- 主張: runtime allowlist は先頭 2 要素しか検査せず、禁止された force branch deletion の等価形を許可する。
- 具体的な破れ方: `_git(main, "branch", "-d", "-f", "--", branch)` は `args[1] == "-d"` なので allowlist を通るが、実行される `git branch -d -f` は `branch -D` と同じ force deletion になり、未 merge branch を削除する。
- 根拠: `dev_wave_cleanup.py:182-198`。テストは literal 3 組をそのまま渡すだけで、追加 option を検査しない (`test_dev_wave_cleanup.py:417-437`)。argv spy も現行 happy-path だけである (`:440-459`)。
- **成果物影響 (1 行)**: runtime guard の受理集合に強制 branch 削除が入り、将来の動的 argv 組立てで未 land commit の ref/reflog を消せる。
- 提案する対処: **実装で閉じる**。verb 単位でなく完全 argv schema を照合し、branch は正確に `("branch","-d","--",branch)` だけを許可する。

### 所見 5

- 主張: 削除へ渡る `Path` は検証済みオブジェクトそのものだが、identity 検査と pathname lookup が非原子的なので inode の取り違えは残る。
- 具体的な破れ方: `_assert_identity(P)` の復帰直後に P と sibling Q を `RENAME_EXCHANGE` し、続く `shutil.rmtree(P)` に新しい P、すなわち Q を開かせる。削除後の path 不在検査は成功し、元 P が Q の名前へ残ったことも検出しない。
- 根拠: `Args.wave_worktree` がそのまま `VerifiedWavePath` に入り (`dev_wave_cleanup.py:538-539`)、削除にも `verified.path` が渡る (`:551-553`)。したがって値のすり替え経路はないが、OS lookup の間隙はある。これは裁定済み残余 (`ruling.md:54-55`)。
- **成果物影響 (1 行)**: 検証した P ではなく Q 配下の全 byte が再帰削除されても、exact path の postcondition は成立し得る。
- 提案する対処: **scope 外として裁定へ返す**。既裁定を変更し、repository-wide lease と dirfd/rename による原子的隔離を採る必要がある。

### 所見 6

- 主張: branch の事後 SHA 照合は CAS ではなく、競合 branch を削除した後でしか取り違えを検出しない。
- 具体的な破れ方: tip T の再検査後、別 session が branch を別の landed commit V へ更新する。`branch -d` は V も merged なので削除に成功し、診断の V と T の不一致から `partial` になるが、V の ref は既に消えている。
- 根拠: 再検査と削除は別操作 (`dev_wave_cleanup.py:665-673`)。診断照合は削除後 (`:601-613`)。裁定もこの残余を部分採用として明記する (`ruling.md:56`)。
- **成果物影響 (1 行)**: tested tip ではない V の branch ref/reflog が削除され、台帳だけが事後的に `partial` になる。
- 提案する対処: **scope 外として裁定へ返す**。最終照合から削除まで repository-wide cooperative lock を保持する。

### 所見 7

- 主張: 状態 e は成功 postcondition を再検査せず、実際には cleanup 済みでないのに `already-clean` を返せる。
- 具体的な破れ方: worktree list と branch 解決時には path/record/ref が全不在で e になり、その直後に別 session が同 path/ref を作成する。cached state のまま早期 return し、新しい directory・record・branch が存在していても rc=0 と `already-clean` を出す。
- 根拠: 状態用 snapshot は `dev_wave_cleanup.py:506-518`、e の早期 return は `:527-528,693-694`。通常の postcondition `:675-680` は通らない。
- **成果物影響 (1 行)**: 撤去されていない worktree byte/ref が残る一方、台帳値は cleanup 完了を示す `already-clean` になる。
- 提案する対処: **実装で閉じる**。e でも path・record・ref の全不在を直前に再取得し、競合検出時は拒否する。

### 所見 8

- 主張: `partial/rc=30` 契約は通常の `Exception` だけに効き、Ctrl-C などの中断では発火しない。
- 具体的な破れ方: detach 完了後または `shutil.rmtree` 中に Ctrl-C が入ると `KeyboardInterrupt` は `except Exception` を通過し、rc=30 の一行報告なしで終了する。directory は半削除または消失済みになり得る。
- 根拠: mutation と top-level の捕捉はいずれも `Exception` 限定 (`dev_wave_cleanup.py:681-682,699-715`)。失敗テストは `RuntimeError` しか注入しない (`test_dev_wave_cleanup.py:477-554`)。
- **成果物影響 (1 行)**: byte/registry が部分撤去されたのに `partial` 台帳行が存在せず、半壊 directory は 5 状態にも戻れない。
- 提案する対処: **実装で閉じる / scope 裁定**。`KeyboardInterrupt` を partial 化し、catch 不能な kill には外部 journal が必要である。

### 所見 9

- 主張: A3 が要求した非 blocking 診断値は作られるだけで捨てられ、cleanup の報告へ出ない。
- 具体的な破れ方: `cwd_permission=2030` と `same_uid_cwd_unreachable=[worker]` を伴って削除が成功しても、返値は単なる `removed` であり、呼び手は盲点の規模も PID/comm も記録できない。
- 根拠: 診断 object は `dev_wave_cleanup.py:66-68,414-419` で作られるが、両 call site は返値を捨てる (`:545,645`)。CLI 出力は `:695-717`。これは `ruling.md:127-130` の「値を報告へ出す」と乖離する。
- **成果物影響 (1 行)**: 撤去受理集合は変わらないが、台帳から `cwd_permission` と same-UID 到達不能 process の値が欠落する。
- 提案する対処: **実装で閉じる**。診断を structured success result へ伝播し、preflight/recheck の双方を記録する。

### 所見 10

- 主張: テストは複数の拒否理由を同時に立てるケースがあり、個別防壁の破壊を検出しない。
- 具体的な破れ方: occupancy の occupied case は `rc=1`、`status=occupied`、nonempty occupants を同時に与えるため、どれか一つの検査を削除しても残りで赤になりテストは通る。reflog fixture は branch-attached commit なので HEAD-only 欠落を共有し、allowlist は `-d -f` を試さず、状態 fixture c は detached record だけを生成する。
- 根拠: `test_dev_wave_cleanup.py:207-225,357-366,417-437,139-178`。
- **成果物影響 (1 行)**: acceptance gate が単一防壁を失った実装や HEAD reflog を漏らす実装を受理し、上記の過広な撤去集合を固定できない。
- 提案する対処: **検査で閉じる**。各信号を一つだけ不正にした payload、HEAD-only commit、`-d` と force option の順列、record/branch 混成状態を追加する。

### 所見 11

- 主張: 同一 invocation の所有権は未証明なので、同一 repository 内の別 session の整合済み worktree 一式を削除できる。
- 具体的な破れ方: 別 session の clean・landed・現在非占有な `<main,P,branch,T>` をそのまま渡すと、common-dir、tip、clean、ancestry はすべて通り、lock reason も検査せず unlock して P と branch を削除する。
- 根拠: CLI authority は 4 個の自己申告値だけ (`dev_wave_cleanup.py:31-36,108-135`)。common-dir は repository の同一性しか証明しない (`:493-500`)。任意 lock の解除は `:626-628`。裁定済み残余は `ruling.md:53-54`、元所見は `consult-sol.md:3-8`。
- **成果物影響 (1 行)**: 撤去受理集合に別 session 所有の worktree が残り、その全 byte・local branch・reflog が削除対象になる。
- 提案する対処: **scope 外として裁定へ返す**。capability/lease を D205 外として拒否した判断を再裁定しない限り閉じない。

## 総括

(a) must-fix は、A3 の live-worker false negative、状態 c の record/ref 混成受理、worktree HEAD reflog の未検査です。

(b) この実装は land してはいけません。現行コードの通常入力だけで、稼働中成果物・別状態の registry/ref・HEAD-only commit を不可逆に失う経路があります。