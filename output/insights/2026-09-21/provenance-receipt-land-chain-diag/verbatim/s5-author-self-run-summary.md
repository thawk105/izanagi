## 総括

4本を作成。P-1/P-3実走済み、P-2の候補分類は実走済み。P-2のprefix/raw-correction replayは実装済み・未実走（registry loaderのコマンド制約）。P-4は未実走、bash -nのみ成功。Python 3本のcompileも成功。テストの作成・既存テスト実行・docs編集・commitはしていない。

### 所在とCLI

基点: /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe

- `receipt_ledger.py`: `python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_ledger.py --store <store> --out <jsonl> [--diff <before.jsonl>]`。--store省略時はcwdのgit common-dirとcheckerの_RECEIPT_DIRECTORYから解決。
- `receipt_reuse_replay.py`: `python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_reuse_replay.py --ledger <jsonl> --repo <worktree> --landed-at 2026-09-21T00:12:00+09:00 --out <jsonl>`（--since既定は2026-09-20T21:00:00+09:00）。
- `audit_attempt_ledger.py`: `python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/audit_attempt_ledger.py --jobs /work/1/SFC/tanab/dev-wave-jobs --ledger <jsonl> --since 2026-09-20T21:00:00+09:00 --out <jsonl>`（--landed-at既定は2026-09-21T00:12:00+09:00）。
- `launch-force-dispatch.sh`: `bash /work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/launch-force-dispatch.sh <wave-worktree> <out-dir> <n>`。親が1 requestずつ実行。dispatch receipt dirは `<wave-worktree>/output/pegasus-dispatch`、通常 `<nonce>/receipt.json`、schema `pegasus-dispatch-receipt/v2`。

### 親scriptの採用・修正

- A1: inventoryのpartition走査、chain_classifyの前時刻・祖先・bindings比較を採用。bytes全文の凍結、実装の選択集合・ancestry・bitset距離/filename順、実関数prefix検査、実regexによるdelta検査を追加。warm実績という呼称を不採用。prefixが失敗したら次候補へ進む実装本体の挙動も保持。
- A2: land_accept_wallのlog読取という枠組みを採用。初回の決め打ちを不採用。65966f4d8a92は00:07:22→00:08:30で68秒、c383bac070f7は00:15:49→00:17:10で81秒、前者は候補なし、後者はbindings一致候補あり（replay未判定）。いずれも監査単独wallではない。
- A3: chain_classifyの差分比較を採用。mtimeでM/Rを分け、旧checkerも除外しない。新形/旧形attributes、root .gitattributes変更commitの有無、全binding差分・比較相手・複合差を保存。旧形参考区分を .gitattributes変更と同一視しない。
- A4: land_accept_wallのHH:MM:SS読取を採用。受入はstarted/finished/tip-beforeから再構築、merged行は不採用。landのISO形式を追加。終了±2秒までに制限して全partition候補を列挙、区間外と欠測を保存。log statusと上書きされ得る同名JSONのstatusは別に保持。
- A5: inventoryのenvironment参照を採用しbindings全文を保存。partitionの用途決め打ち・dispatch件数の断定を不採用。inherited各keyの有無を行に表示、差分値はJSONLへ保存。

### 非同値の近似・制限（全列挙）

1. 当時のlookup集合に代えて、凍結時に残存しmtime_nsがBより小さい受領証を使う。並走・prune・同tip上書き・当時の読取/実行時失敗は復元しない。mtimeはos.replaceより前でありpublish完了時刻ではない。
2. P-1の指定に従いmodeを検査しないため、実際の_read_audit_receiptによる受入可否を再現しない。保存した元bytesからreplayする。
3. 旧checkerの実行コードは復元せず、現行checkerの_receipt_prefix/regexで事後検証する。registryは現行loaderとmanifestが一致した場合だけ使用する設計だが、この自己実走では下記コマンド制約により未実走。
4. 他partitionの比較相手は距離/filename→新しいmtime→partition名順の代表候補。この差分は因果の単独同定ではない。
5. P-3の時刻のみのland logはmtimeのJST日付を基に、開始がmtimeより後なら前日、終了時刻が開始時刻より前なら翌日へ補正する。複数日に跨る長いlogは復元不能。
6. P-3のpostmergeは、preclaimで対応したpartition内・同区間・別tipという指定条件による推定。並走する別waveの監査も含み得る。件数・間隔を実際のpostmerge監査件数・時間と読まない。preclaim未対応ならpartitionを推定せずpostmerge行は出さない。
7. P-3の同名land JSONはloop再実行で上書きされ得るため、log statusを優先し、JSON由来値と帰属制限を別記。

候補の選択集合 `_commit_range(None, head=B.tip)`、`_build_ancestry([B.tip], authoritative=True, head=B.tip)`、bitset距離は実装と同値。祖先判定も同じ閉包のbitsetを使用（同じ履歴ではmerge-base --is-ancestorと同値）。rev-list --countによる距離の近似は採用していない。moduleのREPOは__file__から決まるため--repo内のcheckerファイルを直接importし、その一致を検査する。

### 自己実走

P-1: receipts=499 partitions=19 errors=0。`receipt-ledger-self.jsonl`に元bytes(base64)、sha256、mtime_ns、bindings全文を保存。全体を同時に凍結したatomic snapshotではない。
P-2: 85件（M=48、R=37）。Mはbindings一致候補あり47件、旧形attributes差1件。M/R合計51件のprefix replayは未判定。成功を観測したとは報告しない。
P-3: stdout末尾の集計はattempt開始がlanded-at以降の行。unsupportedは監査attemptと確定していないファイルを別枠で数える。推定postmergeの20行は実監査件数ではない。load1はgate観測値。
P-4: bash -n成功、実走なし。checker本体は一度も起動していない。

### 所有外への波及

なし (tracked file 変更 0)。4 sourceはgit check-ignoreでignored確認。参照したchecker/wait/land/dispatchの4ファイルはgit show HEAD:<path>とのbytes一致も確認。共有store・dev-wave-jobsへの書込みなし。

### 未完了・不確実

P-2の現行registry loaderは内部でgit ls-files、manifest取得はgit ls-treeを使う。依頼の許可一覧（rev-parse / merge-base / rev-list / cat-file / log / show / check-ignore）には含まれない。既存関数内部に限る許可を質問済みだが回答未着。probeのsubprocess audit hookで一覧外commandを実行前に止め、代替registryで検査を弱めず「未判定」を保存した。追加許可が得られれば既存関数内部のこの2 commandをguardに追加してP-2を再実走する必要がある。親の正式実走値としてreplay成功数を確定する段階には至っていない。

実際の未判定理由:
未判定: registry loader: task git allowlist excludes: ['git', 'ls-files']

以下は自己実走の生stdout全文（各行も含む）。正式値は親の再実走から取る。

### P-2 stdout全文

```text
REUSE SUMMARY rows=85 excluded_ledger_errors=0
再利用可能性の事後推定であり実績ではない。mtime順・残存集合・現行checker条件に限定。
population	verdict	cause	n
M	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	候補あり (未判定)	registry loader	47
R	候補あり (bindings 不一致)	attributes 差 (新形、原因未特定)	3
R	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	22
R	候補あり (未判定)	registry loader	4
R	候補なし	checker sha 変更	6
R	候補なし	partition 跨ぎ	2
PARTITION SUMMARY: population	partition	verdict	cause	n
M	4608b761416c	候補あり (未判定)	registry loader	10
M	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	c508d1de93e1	候補あり (未判定)	registry loader	37
R	18d19753b740	候補なし	checker sha 変更	1
R	2a6c7dae048c	候補あり (bindings 不一致)	attributes 差 (新形、原因未特定)	3
R	2a6c7dae048c	候補あり (未判定)	registry loader	2
R	2a6c7dae048c	候補なし	checker sha 変更	1
R	4608b761416c	候補なし	partition 跨ぎ	1
R	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	8
R	53e9a718e601	候補あり (未判定)	registry loader	1
R	5f183033771c	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	13
R	7669d7b2ef9a	候補なし	partition 跨ぎ	1
R	8c683754078a	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
R	ae7ec43852ce	候補なし	checker sha 変更	1
R	c508d1de93e1	候補なし	checker sha 変更	1
R	cceb9da4d834	候補なし	checker sha 変更	1
R	cfdf571bda61	候補あり (未判定)	registry loader	1
R	cfdf571bda61	候補なし	checker sha 変更	1
COLD/UNDETERMINED ROWS: mtime partition tip checker population verdict cause comparison diff_fields compound
2026-09-20T21:05:52.000000000+09:00 5f183033771c da0e7127cdb1 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/a79e72553ec6 | attributes | compound=False
2026-09-20T21:14:47.000000000+09:00 5f183033771c ddd3fb344537 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/da0e7127cdb1 | attributes | compound=False
2026-09-20T21:31:54.000000000+09:00 8c683754078a 8b58dce4a070 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 8c683754078a/716004faa224 | attributes | compound=False
2026-09-20T21:32:02.000000000+09:00 5f183033771c 25334c9b7bf5 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/ddd3fb344537 | attributes | compound=False
2026-09-20T21:44:12.000000000+09:00 5f183033771c 26b7a35e46ce 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/25334c9b7bf5 | attributes | compound=False
2026-09-20T21:46:19.000000000+09:00 cceb9da4d834 4c532aa0b400 1acbb4961ca6 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | attributes,environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL,environment.schema | compound=True
2026-09-20T21:51:57.000000000+09:00 5f183033771c b3082348cc7c 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/26b7a35e46ce | attributes | compound=False
2026-09-20T21:52:06.000000000+09:00 ae7ec43852ce aa81e3c64445 89a60a884088 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T21:53:50.000000000+09:00 53e9a718e601 47719ab411fa 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T21:59:35.000000000+09:00 5f183033771c a49941b437e7 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/b3082348cc7c | attributes | compound=False
2026-09-20T22:06:39.000000000+09:00 53e9a718e601 0ee3e5075ea6 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:07:27.000000000+09:00 2a6c7dae048c 62ed683aba12 65476dafe9c0 R 候補なし | checker sha 変更 | ae7ec43852ce/aa81e3c64445 | environment.checker | compound=False
2026-09-20T22:07:55.000000000+09:00 53e9a718e601 f82b1e30f4e5 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/0ee3e5075ea6 | attributes | compound=False
2026-09-20T22:09:45.000000000+09:00 5f183033771c e2d6b88005b0 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/a49941b437e7 | attributes | compound=False
2026-09-20T22:12:25.000000000+09:00 18d19753b740 4c9c8d480e9f 65476dafe9c0 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | environment.checker,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LANG,environment.inherited.LC_ALL,environment.inherited.LC_CTYPE | compound=True
2026-09-20T22:14:35.000000000+09:00 53e9a718e601 b7dc82bbff75 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:14:47.000000000+09:00 5f183033771c 82705b75480a 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/e2d6b88005b0 | attributes | compound=False
2026-09-20T22:15:47.000000000+09:00 53e9a718e601 4242a6ebaa00 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/47719ab411fa | attributes | compound=False
2026-09-20T22:32:57.000000000+09:00 53e9a718e601 74163cf5952f 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/47719ab411fa | attributes | compound=False
2026-09-20T22:38:37.000000000+09:00 5f183033771c e4dca4255d2f 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/82705b75480a | attributes | compound=False
2026-09-20T22:39:54.000000000+09:00 5f183033771c bc66f8b4c6e1 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/82705b75480a | attributes | compound=False
2026-09-20T22:45:21.000000000+09:00 5f183033771c 56e00b2f379c 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/bc66f8b4c6e1 | attributes | compound=False
2026-09-20T22:51:30.000000000+09:00 5f183033771c e55255ac90de 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/56e00b2f379c | attributes | compound=False
2026-09-20T22:54:10.000000000+09:00 53e9a718e601 cf1f1370ad2d 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:58:04.000000000+09:00 53e9a718e601 a5fc308b9dde 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/74163cf5952f | attributes | compound=False
2026-09-20T22:58:25.000000000+09:00 53e9a718e601 0fef5ed1f2be 7c02fb2d5fec R 候補あり (未判定) | registry loader | 53e9a718e601/a5fc308b9dde | - | compound=False
2026-09-20T23:03:17.000000000+09:00 cfdf571bda61 47fbfd58cf6a 2b72e1d543cd R 候補なし | checker sha 変更 | 5f183033771c/e55255ac90de | attributes,environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T23:09:33.000000000+09:00 5f183033771c 0fef5ed1f2be 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/e55255ac90de | attributes | compound=False
2026-09-20T23:12:12.000000000+09:00 2a6c7dae048c 7cac2d8c7d07 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/62ed683aba12 | attributes | compound=False
2026-09-20T23:17:15.000000000+09:00 2a6c7dae048c b8fa2c57629e 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/7cac2d8c7d07 | attributes | compound=False
2026-09-20T23:17:21.000000000+09:00 cfdf571bda61 ddae70ed1296 2b72e1d543cd R 候補あり (未判定) | registry loader | cfdf571bda61/47fbfd58cf6a | - | compound=False
2026-09-20T23:17:45.000000000+09:00 2a6c7dae048c 1e5fb5705d18 65476dafe9c0 R 候補あり (未判定) | registry loader | 2a6c7dae048c/b8fa2c57629e | - | compound=False
2026-09-20T23:27:48.000000000+09:00 7669d7b2ef9a 1e5fb5705d18 65476dafe9c0 R 候補なし | partition 跨ぎ | 2a6c7dae048c/1e5fb5705d18 | environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T23:36:39.000000000+09:00 2a6c7dae048c 43c32588b3e6 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/1e5fb5705d18 | attributes | compound=False
2026-09-20T23:45:43.000000000+09:00 c508d1de93e1 65966f4d8a92 e69764c1d885 R 候補なし | checker sha 変更 | cfdf571bda61/ddae70ed1296 | environment.checker | compound=False
2026-09-21T00:02:58.000000000+09:00 2a6c7dae048c bf30a3650e7e 65476dafe9c0 R 候補あり (未判定) | registry loader | 2a6c7dae048c/43c32588b3e6 | - | compound=False
2026-09-21T00:08:30.000000000+09:00 4608b761416c 65966f4d8a92 e69764c1d885 R 候補なし | partition 跨ぎ | c508d1de93e1/65966f4d8a92 | environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-21T00:17:10.000000000+09:00 4608b761416c c383bac070f7 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/65966f4d8a92 | - | compound=False
2026-09-21T01:01:26.000000000+09:00 c508d1de93e1 f6a530523931 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/65966f4d8a92 | - | compound=False
2026-09-21T01:07:31.000000000+09:00 c508d1de93e1 3016f22eec17 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/65966f4d8a92 | - | compound=False
2026-09-21T01:16:36.000000000+09:00 c508d1de93e1 92263e53e1a5 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/f6a530523931 | - | compound=False
2026-09-21T01:17:57.000000000+09:00 4608b761416c 3016f22eec17 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/c383bac070f7 | - | compound=False
2026-09-21T01:41:03.000000000+09:00 c508d1de93e1 993d2fc5f3c6 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/65966f4d8a92 | - | compound=False
2026-09-21T01:43:58.000000000+09:00 c508d1de93e1 b5c85a8d9ffe e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/3016f22eec17 | - | compound=False
2026-09-21T01:52:48.000000000+09:00 c508d1de93e1 82b36fb6446c e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/3016f22eec17 | - | compound=False
2026-09-21T01:58:53.000000000+09:00 c508d1de93e1 6d600f0a63b3 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/993d2fc5f3c6 | - | compound=False
2026-09-21T02:00:09.000000000+09:00 4608b761416c b5c85a8d9ffe e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/3016f22eec17 | - | compound=False
2026-09-21T02:08:27.000000000+09:00 c508d1de93e1 3934e2921bba e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/82b36fb6446c | - | compound=False
2026-09-21T02:10:06.000000000+09:00 c508d1de93e1 6dae18be1210 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/92263e53e1a5 | - | compound=False
2026-09-21T02:12:28.000000000+09:00 c508d1de93e1 2afb3976822d e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/3016f22eec17 | - | compound=False
2026-09-21T02:12:52.000000000+09:00 c508d1de93e1 9ad14946ee00 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/b5c85a8d9ffe | - | compound=False
2026-09-21T02:19:14.000000000+09:00 c508d1de93e1 618fb85014d6 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/6d600f0a63b3 | - | compound=False
2026-09-21T02:24:41.000000000+09:00 c508d1de93e1 6e0cafe08828 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/b5c85a8d9ffe | - | compound=False
2026-09-21T02:28:31.000000000+09:00 c508d1de93e1 8845b133be2d e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/b5c85a8d9ffe | - | compound=False
2026-09-21T02:31:47.000000000+09:00 c508d1de93e1 c82f42da712b e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/3934e2921bba | - | compound=False
2026-09-21T02:36:27.000000000+09:00 c508d1de93e1 e6d09d887d44 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/b5c85a8d9ffe | - | compound=False
2026-09-21T02:44:53.000000000+09:00 4608b761416c e6d09d887d44 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/b5c85a8d9ffe | - | compound=False
2026-09-21T02:47:02.000000000+09:00 c508d1de93e1 aa23bb0f184f e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/6e0cafe08828 | - | compound=False
2026-09-21T02:50:51.000000000+09:00 c508d1de93e1 6ba49a471c73 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/aa23bb0f184f | - | compound=False
2026-09-21T02:51:14.000000000+09:00 c508d1de93e1 972ba4fbf928 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/6ba49a471c73 | - | compound=False
2026-09-21T02:52:52.000000000+09:00 4608b761416c 4566c64b4354 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/e6d09d887d44 | - | compound=False
2026-09-21T03:00:08.000000000+09:00 c508d1de93e1 79c32e0b41b2 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/9ad14946ee00 | - | compound=False
2026-09-21T03:00:30.000000000+09:00 c508d1de93e1 0d132aa000e3 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/79c32e0b41b2 | - | compound=False
2026-09-21T03:12:33.000000000+09:00 c508d1de93e1 9e6f2b08d15b e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/8845b133be2d | - | compound=False
2026-09-21T03:16:43.000000000+09:00 4608b761416c 8621eb641280 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/4566c64b4354 | - | compound=False
2026-09-21T03:18:52.000000000+09:00 c508d1de93e1 49cb3412fd02 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/0d132aa000e3 | - | compound=False
2026-09-21T03:19:14.000000000+09:00 c508d1de93e1 6dcd0490889c e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/49cb3412fd02 | - | compound=False
2026-09-21T03:21:20.000000000+09:00 c508d1de93e1 5ae40acbc649 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/972ba4fbf928 | - | compound=False
2026-09-21T03:29:32.000000000+09:00 c508d1de93e1 131bbc9e22e0 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/9e6f2b08d15b | - | compound=False
2026-09-21T03:29:54.000000000+09:00 c508d1de93e1 ab0374ccbf97 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/131bbc9e22e0 | - | compound=False
2026-09-21T03:36:20.000000000+09:00 c508d1de93e1 e33b7febdaa6 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/6dcd0490889c | - | compound=False
2026-09-21T03:36:41.000000000+09:00 c508d1de93e1 e8c097dfd24c e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/e33b7febdaa6 | - | compound=False
2026-09-21T03:41:59.000000000+09:00 4608b761416c ab0374ccbf97 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/8621eb641280 | - | compound=False
2026-09-21T04:02:51.000000000+09:00 4608b761416c 4cb00a8510c6 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/ab0374ccbf97 | - | compound=False
2026-09-21T04:11:50.000000000+09:00 53e9a718e601 a6ac2c54c2c2 7c02fb2d5fec M 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-21T04:19:31.000000000+09:00 c508d1de93e1 98e946f9d8cb e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/e8c097dfd24c | - | compound=False
2026-09-21T04:21:51.000000000+09:00 c508d1de93e1 e4f4c900c2a5 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/e8c097dfd24c | - | compound=False
2026-09-21T04:29:42.000000000+09:00 4608b761416c 98e946f9d8cb e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/4cb00a8510c6 | - | compound=False
2026-09-21T04:40:50.000000000+09:00 c508d1de93e1 088bbdec71e4 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/98e946f9d8cb | - | compound=False
2026-09-21T04:58:08.000000000+09:00 c508d1de93e1 cf1c90e1faf9 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/088bbdec71e4 | - | compound=False
2026-09-21T05:22:10.000000000+09:00 4608b761416c cf1c90e1faf9 e69764c1d885 M 候補あり (未判定) | registry loader | 4608b761416c/98e946f9d8cb | - | compound=False
2026-09-21T07:45:34.000000000+09:00 c508d1de93e1 002f926f452e e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/cf1c90e1faf9 | - | compound=False
2026-09-21T07:57:04.000000000+09:00 c508d1de93e1 956cce1c9111 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/002f926f452e | - | compound=False
2026-09-21T08:13:30.000000000+09:00 c508d1de93e1 98b81b5df7e7 e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/956cce1c9111 | - | compound=False
2026-09-21T08:17:22.000000000+09:00 c508d1de93e1 71f7c5fbb27a e69764c1d885 M 候補あり (未判定) | registry loader | c508d1de93e1/cf1c90e1faf9 | - | compound=False
```

### P-3 stdout全文

```text
ATTEMPT ROWS: log 点 → 受領証 mtime の間隔 (監査単独の wall ではない)
wave | stage | start / end | duration_s | head | rc/status | load1 | partition:inherited-presence | receipt_mtime | start_to_mtime_s | unmatched_reason
dev-wave-t2766-pairing-adopt | land | 2026-09-20T21:04:03+09:00 / 2026-09-20T21:12:28+09:00 | 505.0 | da0e7127cdb1 | 0/landed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T21:05:52.000000000+09:00 | 109.0 | None
dev-wave-paper-story-20260920b | accept-preclaim | 2026-09-20T21:05:57+09:00 / 2026-09-20T21:07:57+09:00 | 120.0 | c634768f273d | 70/None | 22.95 | None: | None | None | tip の受領証自体が無い
dev-wave-paper-intro-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go-1.nohup.log]
dev-wave-paper-intro-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go-2.nohup.log]
dev-wave-t2153-witness-requested-us | accept-preclaim | 2026-09-20T21:15:50+09:00 / 2026-09-20T21:18:17+09:00 | 147.0 | 227674a6ed43 | 70/None | 26.49 | None: | None | None | tip の受領証自体が無い
dev-wave-cleanup-backup-loss-record | accept-preclaim | 2026-09-20T21:17:10+09:00 / 2026-09-20T21:29:14+09:00 | 724.0 | 57d2a57fa896 | 0/None | 17.11 | None: | None | None | tip の受領証自体が無い
dev-wave-paper-intro-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go.log]
dev-wave-t2153-witness-requested-us | accept-preclaim | 2026-09-20T21:20:37+09:00 / 2026-09-20T21:29:53+09:00 | 556.0 | 25334c9b7bf5 | 0/None | 11.22 | None: | None | None | 区間内に無い; nearest=2026-09-20T21:32:02.000000000+09:00 boundary_delta_s=129.000000000
dev-wave-cleanup-backup-loss-record | land | 2026-09-20T21:30:27+09:00 / 2026-09-20T21:39:37+09:00 | 550.0 | 94b39e8eaa4f | 10/stale-main | None | None: | None | None | tip の受領証自体が無い
dev-wave-paper-story-20260920b | accept-preclaim | 2026-09-20T21:32:02+09:00 / 2026-09-20T21:44:12+09:00 | 730.0 | 6250a8e1804b | 0/None | 13.49 | None: | None | None | tip の受領証自体が無い
dev-wave-fig13-b10-waiting-grid | accept-preclaim | 2026-09-20T21:35:46+09:00 / 2026-09-20T22:08:59+09:00 | 1993.0 | 8b58dce4a070 | None/None | None | None: | None | None | 区間内に無い; nearest=2026-09-20T21:31:54.000000000+09:00 boundary_delta_s=-232.000000000
dev-wave-t2153-witness-requested-us | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-loop.log]
dev-wave-t2153-witness-requested-us | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-stderr-1.log]
dev-wave-cleanup-backup-loss-record | land | 2026-09-20T21:40:17+09:00 / 2026-09-20T21:49:33+09:00 | 556.0 | 26b7a35e46ce | 0/landed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T21:44:12.000000000+09:00 | 235.0 | None
dev-wave-paper-related-work-ja | accept-preclaim | 2026-09-20T21:51:46+09:00 / 2026-09-20T22:01:56+09:00 | 610.0 | c5f12d70ff6e | 0/None | 12.78 | None: | None | None | tip の受領証自体が無い
dev-wave-paper-story-20260920b | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1.nohup.log]
dev-wave-paper-related-work-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go-1.nohup.log]
dev-wave-k2-loop-originals-lost-downstream | accept-postmerge (推定) | 2026-09-20T22:04:49+09:00 / 2026-09-20T22:32:01+09:00 | 1632.0 | 4242a6ebaa00 | 0/None | 7.49 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:15:47.000000000+09:00 | 658.0 | None
dev-wave-k2-loop-originals-lost-downstream | accept-postmerge (推定) | 2026-09-20T22:04:49+09:00 / 2026-09-20T22:32:01+09:00 | 1632.0 | b7dc82bbff75 | 0/None | 7.49 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:14:35.000000000+09:00 | 586.0 | None
dev-wave-k2-loop-originals-lost-downstream | accept-postmerge (推定) | 2026-09-20T22:04:49+09:00 / 2026-09-20T22:32:01+09:00 | 1632.0 | f82b1e30f4e5 | 0/None | 7.49 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:07:55.000000000+09:00 | 186.0 | None
dev-wave-k2-loop-originals-lost-downstream | accept-preclaim | 2026-09-20T22:04:49+09:00 / 2026-09-20T22:32:01+09:00 | 1632.0 | 0ee3e5075ea6 | 0/None | 7.49 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:06:39.000000000+09:00 | 110.0 | None
dev-wave-paper-story-20260920b | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go.log]
dev-wave-paper-related-work-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go-2.nohup.log]
dev-wave-paper-related-work-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go.log]
dev-wave-fig13-b10-waiting-grid | land | 2026-09-20T22:13:16+09:00 / 2026-09-20T22:18:53+09:00 | 337.0 | 82705b75480a | 0/landed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T22:14:47.000000000+09:00 | 91.0 | None
dev-wave-t2813-o26-inventory | accept-postmerge (推定) | 2026-09-20T22:13:30+09:00 / 2026-09-20T22:27:19+09:00 | 829.0 | 4242a6ebaa00 | None/None | None | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:15:47.000000000+09:00 | 137.0 | None
dev-wave-t2813-o26-inventory | accept-preclaim | 2026-09-20T22:13:30+09:00 / 2026-09-20T22:27:19+09:00 | 829.0 | b7dc82bbff75 | None/None | None | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:14:35.000000000+09:00 | 65.0 | None
dev-wave-t2807-b8-prerun | accept-preclaim | 2026-09-20T22:32:31+09:00 / 2026-09-20T22:40:47+09:00 | 496.0 | 74163cf5952f | 0/None | 8.05 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:32:57.000000000+09:00 | 26.0 | None
dev-wave-k2-loop-originals-lost-downstream | land | 2026-09-20T22:33:41+09:00 / 2026-09-20T22:36:34+09:00 | 173.0 | bc66f8b4c6e1 | 31/fold-gate-failed | None | None: | None | None | 区間内に無い; nearest=2026-09-20T22:39:54.000000000+09:00 boundary_delta_s=200.000000000
dev-wave-t2813-o26-inventory | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1.log]
dev-wave-t2813-o26-inventory | land | 2026-09-20T22:36:58+09:00 / 2026-09-20T22:39:11+09:00 | 133.0 | e4dca4255d2f | 31/fold-gate-failed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T22:38:37.000000000+09:00 | 99.0 | None
dev-wave-k2-loop-originals-lost-downstream | land | 2026-09-20T22:37:05+09:00 / 2026-09-20T22:42:57+09:00 | 352.0 | bc66f8b4c6e1 | 0/landed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T22:39:54.000000000+09:00 | 169.0 | None
dev-wave-t2807-b8-prerun | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-final.log]
dev-wave-t2813-o26-inventory | land | 2026-09-20T22:43:48+09:00 / 2026-09-20T22:49:08+09:00 | 320.0 | 56e00b2f379c | 0/landed | None | 5f183033771c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T22:45:21.000000000+09:00 | 93.0 | None
dev-wave-t2807-b8-prerun | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-final-2.log]
dev-wave-t2243-collection-diag | accept-preclaim | 2026-09-20T22:53:53+09:00 / 2026-09-20T22:55:12+09:00 | 79.0 | cf1f1370ad2d | 70/None | 6.67 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:54:10.000000000+09:00 | 17.0 | None
dev-wave-t2807-b8-prerun | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-final-3.log]
dev-wave-t2243-collection-diag | accept-postmerge (推定) | 2026-09-20T22:57:43+09:00 / 2026-09-20T23:07:30+09:00 | 587.0 | 0fef5ed1f2be | 0/None | 4.82 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:58:25.000000000+09:00 | 42.0 | None
dev-wave-t2243-collection-diag | accept-preclaim | 2026-09-20T22:57:43+09:00 / 2026-09-20T23:07:30+09:00 | 587.0 | a5fc308b9dde | 0/None | 4.82 | 53e9a718e601:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T22:58:04.000000000+09:00 | 21.0 | None
dev-wave-t2804-provenance-timeout-contract | accept-preclaim | 2026-09-20T23:11:55+09:00 / 2026-09-20T23:13:06+09:00 | 71.0 | 7cac2d8c7d07 | None/None | None | 2a6c7dae048c:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:12:12.000000000+09:00 | 17.0 | None
dev-wave-t2804-provenance-timeout-contract | accept-postmerge (推定) | 2026-09-20T23:16:38+09:00 / 2026-09-20T23:26:31+09:00 | 593.0 | 1e5fb5705d18 | None/None | None | 2a6c7dae048c:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:17:45.000000000+09:00 | 67.0 | None
dev-wave-t2804-provenance-timeout-contract | accept-preclaim | 2026-09-20T23:16:38+09:00 / 2026-09-20T23:26:31+09:00 | 593.0 | b8fa2c57629e | None/None | None | 2a6c7dae048c:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:17:15.000000000+09:00 | 37.0 | None
dev-wave-t2803-provenance-receipt | accept-preclaim | 2026-09-20T23:16:40+09:00 / 2026-09-20T23:28:02+09:00 | 682.0 | ddae70ed1296 | 0/None | 4.48 | cfdf571bda61:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:17:21.000000000+09:00 | 41.0 | None
dev-wave-t2804-provenance-timeout-contract | land | 2026-09-20T23:26:46+09:00 / 2026-09-20T23:30:57+09:00 | 251.0 | 1e5fb5705d18 | 0/None | None | 7669d7b2ef9a:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-20T23:27:48.000000000+09:00 | 62.0 | None
dev-wave-t2803-provenance-receipt | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1.log]
dev-wave-t2803-provenance-receipt | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-2.log]
dev-wave-t2803-provenance-receipt | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-wait-2.log]
dev-wave-t2344-closure-stage | accept-preclaim | 2026-09-20T23:35:44+09:00 / 2026-09-20T23:48:04+09:00 | 740.0 | 43c32588b3e6 | 70/None | 3.92 | 2a6c7dae048c:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:36:39.000000000+09:00 | 55.0 | None
dev-wave-t2803-provenance-receipt | accept-preclaim | 2026-09-20T23:45:07+09:00 / 2026-09-21T00:06:54+09:00 | 1307.0 | 65966f4d8a92 | 0/None | 3.53 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-20T23:45:43.000000000+09:00 | 36.0 | None
dev-wave-t2344-closure-stage | accept-preclaim | 2026-09-21T00:02:39+09:00 / 2026-09-21T00:14:58+09:00 | 739.0 | bf30a3650e7e | 0/None | 4.73 | 2a6c7dae048c:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T00:02:58.000000000+09:00 | 19.0 | None
dev-wave-t2803-provenance-receipt | land | 2026-09-21T00:07:22+09:00 / 2026-09-21T00:12:00+09:00 | 278.0 | 65966f4d8a92 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T00:08:30.000000000+09:00 | 68.0 | None
dev-wave-t2803-provenance-receipt | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-wait-3.log]
dev-wave-t2344-closure-stage | land | 2026-09-21T00:15:49+09:00 / 2026-09-21T00:21:24+09:00 | 335.0 | c383bac070f7 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T00:17:10.000000000+09:00 | 81.0 | None
rulings-all-20260921 | accept-preclaim | 2026-09-21T01:07:14+09:00 / 2026-09-21T01:16:22+09:00 | 548.0 | 3016f22eec17 | 0/None | 4.18 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T01:07:31.000000000+09:00 | 17.0 | None
rulings-all-20260921 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1.log]
dev-wave-paper-abstract-conclusion-ja | accept-postmerge (推定) | 2026-09-21T01:43:40+09:00 / 2026-09-21T01:58:51+09:00 | 911.0 | 82b36fb6446c | 0/None | 3.33 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T01:52:48.000000000+09:00 | 548.0 | None
dev-wave-paper-abstract-conclusion-ja | accept-preclaim | 2026-09-21T01:43:40+09:00 / 2026-09-21T01:58:51+09:00 | 911.0 | b5c85a8d9ffe | 0/None | 3.33 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T01:43:58.000000000+09:00 | 18.0 | None
dev-wave-paper-abstract-conclusion-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go-1.nohup.log]
dev-wave-paper-abstract-conclusion-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go.log]
dev-wave-paper-abstract-conclusion-ja | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1-wait.log]
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T02:12:09+09:00 / 2026-09-21T02:23:47+09:00 | 698.0 | 618fb85014d6 | 0/None | 4.24 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:19:14.000000000+09:00 | 425.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T02:12:09+09:00 / 2026-09-21T02:23:47+09:00 | 698.0 | 9ad14946ee00 | 0/None | 4.24 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:12:52.000000000+09:00 | 43.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-preclaim | 2026-09-21T02:12:09+09:00 / 2026-09-21T02:23:47+09:00 | 698.0 | 2afb3976822d | 0/None | 4.24 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:12:28.000000000+09:00 | 19.0 | None
dev-wave-wall-decomp | accept-postmerge (推定) | 2026-09-21T02:28:14+09:00 / 2026-09-21T02:50:28+09:00 | 1334.0 | aa23bb0f184f | 0/None | 2.38 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:47:02.000000000+09:00 | 1128.0 | None
dev-wave-wall-decomp | accept-postmerge (推定) | 2026-09-21T02:28:14+09:00 / 2026-09-21T02:50:28+09:00 | 1334.0 | c82f42da712b | 0/None | 2.38 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:31:47.000000000+09:00 | 213.0 | None
dev-wave-wall-decomp | accept-postmerge (推定) | 2026-09-21T02:28:14+09:00 / 2026-09-21T02:50:28+09:00 | 1334.0 | e6d09d887d44 | 0/None | 2.38 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:36:27.000000000+09:00 | 493.0 | None
dev-wave-wall-decomp | accept-preclaim | 2026-09-21T02:28:14+09:00 / 2026-09-21T02:50:28+09:00 | 1334.0 | 8845b133be2d | 0/None | 2.38 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:28:31.000000000+09:00 | 17.0 | None
dev-wave-paper-story-20260921 | accept-preclaim | 2026-09-21T02:36:10+09:00 / 2026-09-21T02:43:38+09:00 | 448.0 | e6d09d887d44 | 0/None | 2.56 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:36:27.000000000+09:00 | 17.0 | None
dev-wave-paper-story-20260921 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1.nohup.log]
dev-wave-t2814-cleanup-command | accept-preclaim | 2026-09-21T02:46:42+09:00 / 2026-09-21T02:47:28+09:00 | 46.0 | aa23bb0f184f | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:47:02.000000000+09:00 | 20.0 | None
dev-wave-paper-story-20260921 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-go.log]
dev-wave-paper-story-20260921 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-1-wait.log]
dev-wave-t2814-cleanup-command | accept-postmerge (推定) | 2026-09-21T02:50:30+09:00 / 2026-09-21T03:15:00+09:00 | 1470.0 | 0d132aa000e3 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:00:30.000000000+09:00 | 600.0 | None
dev-wave-t2814-cleanup-command | accept-postmerge (推定) | 2026-09-21T02:50:30+09:00 / 2026-09-21T03:15:00+09:00 | 1470.0 | 79c32e0b41b2 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:00:08.000000000+09:00 | 578.0 | None
dev-wave-t2814-cleanup-command | accept-postmerge (推定) | 2026-09-21T02:50:30+09:00 / 2026-09-21T03:15:00+09:00 | 1470.0 | 972ba4fbf928 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:51:14.000000000+09:00 | 44.0 | None
dev-wave-t2814-cleanup-command | accept-postmerge (推定) | 2026-09-21T02:50:30+09:00 / 2026-09-21T03:15:00+09:00 | 1470.0 | 9e6f2b08d15b | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:12:33.000000000+09:00 | 1323.0 | None
dev-wave-t2814-cleanup-command | accept-preclaim | 2026-09-21T02:50:30+09:00 / 2026-09-21T03:15:00+09:00 | 1470.0 | 6ba49a471c73 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T02:50:51.000000000+09:00 | 21.0 | None
dev-wave-wall-decomp | land | 2026-09-21T02:52:01+09:00 / 2026-09-21T02:55:30+09:00 | 209.0 | 4566c64b4354 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T02:52:52.000000000+09:00 | 51.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T02:59:51+09:00 / 2026-09-21T03:09:31+09:00 | 580.0 | 0d132aa000e3 | 70/None | 2.42 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:00:30.000000000+09:00 | 39.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-preclaim | 2026-09-21T02:59:51+09:00 / 2026-09-21T03:09:31+09:00 | 580.0 | 79c32e0b41b2 | 70/None | 2.42 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:00:08.000000000+09:00 | 17.0 | None
dev-wave-t2810-g1-launch-validation | accept-preclaim | 2026-09-21T03:12:15+09:00 / 2026-09-21T03:17:06+09:00 | 291.0 | 9e6f2b08d15b | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:12:33.000000000+09:00 | 18.0 | None
dev-wave-t2814-cleanup-command | land | 2026-09-21T03:16:12+09:00 / 2026-09-21T03:19:32+09:00 | 200.0 | 8621eb641280 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T03:16:43.000000000+09:00 | 31.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T03:18:33+09:00 / 2026-09-21T03:30:36+09:00 | 723.0 | 131bbc9e22e0 | 70/None | 4.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:29:32.000000000+09:00 | 659.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T03:18:33+09:00 / 2026-09-21T03:30:36+09:00 | 723.0 | 5ae40acbc649 | 70/None | 4.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:21:20.000000000+09:00 | 167.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T03:18:33+09:00 / 2026-09-21T03:30:36+09:00 | 723.0 | 6dcd0490889c | 70/None | 4.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:19:14.000000000+09:00 | 41.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T03:18:33+09:00 / 2026-09-21T03:30:36+09:00 | 723.0 | ab0374ccbf97 | 70/None | 4.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:29:54.000000000+09:00 | 681.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-preclaim | 2026-09-21T03:18:33+09:00 / 2026-09-21T03:30:36+09:00 | 723.0 | 49cb3412fd02 | 70/None | 4.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:18:52.000000000+09:00 | 19.0 | None
dev-wave-t2810-g1-launch-validation | accept-postmerge (推定) | 2026-09-21T03:29:14+09:00 / 2026-09-21T03:41:01+09:00 | 707.0 | ab0374ccbf97 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:29:54.000000000+09:00 | 40.0 | None
dev-wave-t2810-g1-launch-validation | accept-postmerge (推定) | 2026-09-21T03:29:14+09:00 / 2026-09-21T03:41:01+09:00 | 707.0 | e33b7febdaa6 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:36:20.000000000+09:00 | 426.0 | None
dev-wave-t2810-g1-launch-validation | accept-postmerge (推定) | 2026-09-21T03:29:14+09:00 / 2026-09-21T03:41:01+09:00 | 707.0 | e8c097dfd24c | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:36:41.000000000+09:00 | 447.0 | None
dev-wave-t2810-g1-launch-validation | accept-preclaim | 2026-09-21T03:29:14+09:00 / 2026-09-21T03:41:01+09:00 | 707.0 | 131bbc9e22e0 | None/None | None | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:29:32.000000000+09:00 | 18.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-postmerge (推定) | 2026-09-21T03:36:03+09:00 / 2026-09-21T03:58:52+09:00 | 1369.0 | e8c097dfd24c | 0/None | 3.37 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:36:41.000000000+09:00 | 38.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | accept-preclaim | 2026-09-21T03:36:03+09:00 / 2026-09-21T03:58:52+09:00 | 1369.0 | e33b7febdaa6 | 0/None | 3.37 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T03:36:20.000000000+09:00 | 17.0 | None
dev-wave-t2810-g1-launch-validation | land | 2026-09-21T03:41:32+09:00 / 2026-09-21T03:44:27+09:00 | 175.0 | ab0374ccbf97 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T03:41:59.000000000+09:00 | 27.0 | None
dev-wave-t2817-acceptance-bottleneck-3 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-loop.attempt1.log]
dev-wave-t2817-acceptance-bottleneck-3 | unsupported | None / None | None | None | None/None | None | None: | None | None | unsupported: no recognized land start [land-loop.log]
dev-wave-branch-residue-cleanup | accept-postmerge (推定) | 2026-09-21T04:19:14+09:00 / 2026-09-21T04:28:37+09:00 | 563.0 | e4f4c900c2a5 | 0/None | 2.99 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T04:21:51.000000000+09:00 | 157.0 | None
dev-wave-branch-residue-cleanup | accept-preclaim | 2026-09-21T04:19:14+09:00 / 2026-09-21T04:28:37+09:00 | 563.0 | 98e946f9d8cb | 0/None | 2.99 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T04:19:31.000000000+09:00 | 17.0 | None
dev-wave-t2797-b5-contrast | accept-preclaim | 2026-09-21T04:21:32+09:00 / 2026-09-21T04:29:06+09:00 | 454.0 | e4f4c900c2a5 | 70/None | 2.93 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T04:21:51.000000000+09:00 | 19.0 | None
dev-wave-branch-residue-cleanup | land | 2026-09-21T04:29:15+09:00 / 2026-09-21T04:32:25+09:00 | 190.0 | 98e946f9d8cb | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T04:29:42.000000000+09:00 | 27.0 | None
dev-wave-t2797-b5-contrast | accept-preclaim | 2026-09-21T04:40:32+09:00 / 2026-09-21T04:52:36+09:00 | 724.0 | 088bbdec71e4 | 0/None | 2.39 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T04:40:50.000000000+09:00 | 18.0 | None
dev-wave-t2797-b5-contrast | land | 2026-09-21T04:54:42+09:00 / 2026-09-21T04:54:43+09:00 | 1.0 | cf1c90e1faf9 | 23/rejected | None | None: | None | None | 区間内に無い; nearest=2026-09-21T04:58:08.000000000+09:00 boundary_delta_s=205.000000000
dev-wave-t2797-b5-contrast | accept-preclaim | 2026-09-21T04:57:50+09:00 / 2026-09-21T05:20:47+09:00 | 1377.0 | cf1c90e1faf9 | 0/None | 1.44 | c508d1de93e1:GIT_EDITOR=1,LANG=1,LC_ALL=0,GIT_CONFIG_GLOBAL=0 | 2026-09-21T04:58:08.000000000+09:00 | 18.0 | None
dev-wave-t2797-b5-contrast | land | 2026-09-21T05:21:30+09:00 / 2026-09-21T05:26:06+09:00 | 276.0 | cf1c90e1faf9 | 0/landed | None | 4608b761416c:GIT_EDITOR=0,LANG=1,LC_ALL=1,GIT_CONFIG_GLOBAL=1 | 2026-09-21T05:22:10.000000000+09:00 | 40.0 | None
dev-wave-dwm08-selfrun-probe | accept-preclaim | 2026-09-21T08:13:04+09:00 / None | None | 98b81b5df7e7 | None/None | 4.37 | None: | None | None | 終了点なし/開始終了逆転: 区間を確定できない
ATTEMPT SUMMARY since=2026-09-21T00:12:00+09:00; n=attempt rows; intervals=all candidate matches (ambiguity retained)
stage	n	intervals_n	min_s	median_s	max_s	unmatched	ambiguous
accept-postmerge (推定)	20	20	38.0	425.5	1323.0	0	0
accept-preclaim	17	16	17.0	18.0	21.0	1	0
land	7	6	27.0	35.5	81.0	1	0
unsupported	10	0	None	None	None	10	0
```
