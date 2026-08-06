静的判定は **NO-GO**。以下はすべて静的読解で構成した壊れ筋であり、pytest・障害実験は実施していない。

### 1. [must-fix] 抽出先が proof receipt の code-identity 閉包外になる

**所見**: 「`wal.py` が pin 対象でない」は安全根拠ではなく、抽出後は受理判定を担う `durable/jsonl.py` を同一 validator identity のまま変更できる。

**根拠**: `brief.md:58-61`、`s2-plan.md:503-514`、`orchestrator/campaign/artifact_admission.py:99-115,541-542,577-600`、`orchestrator/campaign/s8b_oracle_manifest.py:44-52,411-450`、`orchestrator/campaign/s8b_oracle_report.py:1264-1293`。

**壊れ方**: 抽出後、`durable/jsonl.py` だけを変更して duplicate key を last-wins にする。`artifact_admission.py` 自身の bytes は不変なので receipt の `validator.sha256` も不変である。同一 WAL に同値の duplicate `env_tag` を入れると、旧版は parse error、変更版は正常 record として進める。oracle manifest の exact 5 source に `wal.py` も新層も含まれないため、同じ generator identity で oracle row も変わる。

**成果物影響**: `CampaignAdmissionDecision.classification/admission_status`、Layer 3 admission、oracle row の `status/outcome`、最終 judge の UNKNOWN・disqualified・eligible 集合が、同じ validator/generator identity の下で変わる。

**提案**: read-side framing/parser の抽出を保留するか、`wal.py` と `durable/jsonl.py` を含む versioned transitive source closure を新設し、既存 manifest とは世代分離する。既存 exact key-set を無断で拡張できないため、これは段 4 の裁定事項にする。

### 2. [must-fix] WAL byte 不変が prose-only で、全 writer 経路に固定されていない

**所見**: `canonical_json_bytes(sort_keys=True)` と現行 WAL encoder は別方言であり、単一の byte-identical test 名だけでは recovery suffix を含む全 writer の誤用を防げない。

**根拠**: `s2-plan.md:29-39,55-57,416-425`、`orchestrator/campaign/wal.py:309-313,487-491,1185-1193`、`orchestrator/campaign/artifact_admission.py:565-576`。

**壊れ方**: payload を挿入順 `{"z":1,"a":"é"}` とする。現行 `_record_to_line` は top-level と payload の挿入順を保ち、`ensure_ascii=False` で書く。共通 canonical encoder を `append` または `_append_records_locked` に一度でも流用すると、top-level と nested payload が sort され、意味が同じでも WAL は別 bytes になる。特に recovery-abort suffix だけが新 encoder を通る実装も、計画上の generic 共通化と両立してしまう。

**成果物影響**: raw `wal_sha256`、Layer 3 の artifact ref、admission receipt が変わる。既知 overlay は path/id が一致しても `hashes_are_exact=False` となり、`OverlayMutationError` へ変わるため受理集合も縮む。

**提案**: `append/log`、`recover_interrupted_attempts` の複数-frame append、tail-repair receipt の各経路に、現行 bytes を固定した golden vector を置く。Unicode、nested dict の逆順、共有 DAG、int/float を含め、campaign writer から `canonical_json_bytes` への到達を禁止する meta-testも追加する。

### 3. [must-fix] facade の例外順序と write 前 gate が完全には仕様化されていない

**所見**: 同じ module object を import するだけでは、例外 identity・複合違反の診断順序・materialization gate の位置は保存されない。

**根拠**: `s2-plan.md:47-50,74-89,152-161`、`orchestrator/campaign/wal.py:254-285,367-371,532-535,648-651`、`orchestrator/campaign/layout.py:467-475`、`orchestrator/campaign/loop.py:272-279`、`orchestrator/campaign/layer3_report.py:96-119,413-421`。

**壊れ方**:

1. 物理 JSON に unknown top-level key と payload 内の `\uD800` を同居させる。現行は `wal.py:264-270` の exact-key 違反が先で `WalLineError` になる。generic validator が campaign schema より先に全 tree を検査すると `WalPayloadTypeError` が先になる。
2. generic append が完全な newline frame を書いた後、directory fsync で `JsonlAppendError` を上げ、それが facade から漏れる。`loop.py:275` の `isinstance(..., WalAppendError)` が偽になり、variant 固有例外として replay と abort 追記へ進む。現行なら直ちに再送出され、不確かな WAL へ追記しない。
3. `wal.py:358-453` を移す際、`_admit_materialization()` より先に parent fd を開く。禁止された worktree container に runs/WAL が作られ、後段 gate の拒否が write 後になる。

**成果物影響**: 1 は oracle/layer3 の理由文字列と report SHA を変える。2 は variant を abort terminal にし、再評価・選択集合を変える。3 は本来存在しない campaign WAL と trial ledger を残し、resume の skip 判定を変える。

**提案**: 両 import mode で `type`、`__module__`、`args`、`.path`、nested `.cause`、複合違反の優先順位を exact 固定する。generator wrapper の `try/except` は iterator 生成時ではなく iteration 中の例外も写す。`_admit_materialization()` は mkdir/open/fd 取得より前という facade 契約にし、既存 materialization-gate nodes も焦点回帰へ入れる。

### 4. [must-fix / activation-blocking] S2 の compare-then-act は lease なしでは CAS にならない

**所見**: plan 自身が TOCTOU を認めながら、lease capability を持たない `commit` / `discard` signature を固定している。

**根拠**: `brief.md:33-35`、`s2-plan.md:181-183,237-257,339-355`、`docs/mutation-restore-durability-design.md:184-202,377-380`。

**壊れ方**: commit が live inode/hash/metadata を再検査した直後、非協調 writer が同じ target を人間編集版へ置換する。その後 S2 が `os.replace` すると、その編集を上書きする。復元後は記録済み HEAD bytes に戻るため Git cleanliness は緑になり、失われた編集を検出できない。discard も、登録 inode の検査後から `unlink(name)` までに同名を差し替えられると別 process の file を削除できる。

**成果物影響**: 人間編集や別 attempt の結果を失った木が `clean` になり、その木で得た測定値・trial ledger・certified 選択が正当化されうる。

**提案**: `commit`、`discard`、全 target preflight から最後の replace/unlink までを覆う opaque exclusive-lease capability を API に必須化する。lease 実装を scope 外に保つなら API を private/非活性として固定し、「単体で安全な public primitive」とは扱わない。

### 5. [must-fix / activation-blocking] `clean` の真偽を任意 callback が自己申告できる

**所見**: evidence の意味検証を後続 scope に送りながら、同じ wave で `CleanVerifier` の返値だけから `clean` と `CleanAttempt` を発行する構造になっている。

**根拠**: `s2-plan.md:322-327,352-370,493`、`docs/mutation-restore-durability-design.md:145-148,223-225`、`brief.md:41-45,53-54`。

**壊れ方**: target が mutated のままの状態で、`RestoreExecutor` を no-op、`CleanVerifier` を「file/dir fsync、HEAD、bytes、mode、cleanliness、quiescence は全て確認済み」という fixture object を返す callback にする。plan は evidence の意味を検証しないため、その返値を schema/hash 化して `clean` を appendし、`last-clean` 更新、`active` unlink、`CleanAttempt` 発行まで進められる。

**成果物影響**: mutated/OTHER bytes の木が clean terminal になり、結果 ledger capability、trial 完了、certified 選択への入場条件を満たしてしまう。

**提案**: S3 自身が fd から target bytes・inode・metadata を再読し、HEAD/cleanliness と quiescence の issuer を検証する。`RecoveryAuthorization` と `CleanVerification` は production verifier だけが発行できる sealed capability にする。それが scope 外なら、この wave は codec/FSM reader までに縮め、`recover()` と `clean` 発行を実装しない。変異 kill は診断文字列ではなく、実 target bytes、callback 非呼出し、journal/locator 非変更で判定する。

### 6. [must-fix] process-local poison は fsync の UNKNOWN を再起動後に忘れる

**所見**: 同じ state object の poison だけでは、完全な `clean\n` が見えているが fsync 成否が不明な状態を durable に記録できない。

**根拠**: `s2-plan.md:372-374,496`、`orchestrator/campaign/wal.py:390-408,433-451`、`brief.md:43`。

**壊れ方**: `clean` frame の全 bytes と newline を `write` した後、file fsync または close が EIO を返す。現 process の object は poison されるが、frame は page cache から読める。再起動後の reader は canonical hash-chain と terminal `clean` を受理する。`s2-plan.md:374` の cleanup-resume が、その clean inodeから `last-clean` 更新と `active` unlinkを行う。失敗した fsync が UNKNOWN だった事実はどこにも残らない。

**成果物影響**: UNKNOWN が clean へ丸められ、active 不在・CleanAttempt・結果 ledger の発行へ進む。物理障害後に clean record が失われれば、ledger と journal の参照も食い違う。

**提案**: append 前に別 inode/locatorへ durable な `pending` を立て、record fsync 成功後にだけ durable に解除する。pending の残存は常に quarantine とする。少なくとも full-write→fsync failure、dir-fsync failure、close failureの各ケースで新しい `MutationJournal` を開き直し、cleanを受理せず active を残す test/mutation を事前登録する。

### 7. [must-fix] clean cleanup の再試行が次 attempt の `active` を消せる

**所見**: `active` の no-overwrite publish は安全でも、unlink 再試行に attempt identity と相互排他が束縛されていない。

**根拠**: `s2-plan.md:362,369,374,489,494-495`、`docs/mutation-restore-durability-design.md:193-200`。

**壊れ方**: attempt A が clean と `last-clean` を durable にした後、`unlink(active)` は成功するが親 fsync が失敗する。見えている namespace では active が無いため、attempt B が自分の journal を active として publishし、変異を開始する。その後 A の cleanup-resume が名前だけで `unlink("active")` すると、B の locator を削除する。

**成果物影響**: B が target を変更中なのに active が不在となる。consumer は inactive/clean epoch と誤認し、汚染された測定値やレポートを採用できる。

**提案**: arm・cleanup・次 arm を直列化する state-root lock/lease を導入し、unlink直前に active の `st_dev/st_ino` が A の journal と一致することを検査する。inode再検査だけでは check→unlink race が残るので、lock が必須。A/B の interleavingを固定した testを追加する。

### 8. [must-fix] hash-chain が record 間の意味的一貫性も suffix 完全性も証明しない

**所見**: schema・seq・previous hash・FSM だけでは、「同じ attempt/target/原像について進んだ chain」を保証できず、計画の破損検出主張は広すぎる。

**根拠**: `s2-plan.md:263-285,309-327,333-344,374,477-484`。

**壊れ方**:

1. `armed` の target set を A、後続 `clean` の target set/hash/metadata を B として、それぞれ exact schema で再hashする。計画には全 record の `attempt_id`、repo/incarnation、target path/order、original/mutated hash、metadata が genesis と exact 一致する reader 条件がない。形式上正しい chainを terminal cleanとして読める。
2. `[armed, mutated, restoring]` の最後の完全な newline frame を丸ごと削除する。残った prefix は newline終端・seq連続・hash正当なので、unterminated-tail testでは検出できず `mutated` として自動 recovery に入る。
3. 書込権限を持つ者が chain 全体を作り直せることを認めながら、外部 anchorなしで journal payloadを復元命令として使う。これは「真正性ではない」という限定と `recover()` の権限が一致していない。

**成果物影響**: target を検証していない clean recordから locator cleanupが再開され、active不在・last-clean・ledger参照が誤って確定する。suffix破損も quarantine ではなく自動書込へ変わる。

**提案**: genesis の `plan_sha256` を固定し、全 record の attempt/repo/target集合・hash・metadataを逐次 cross-checkする。さらに active/activation receipt側へ genesis digest、expected terminal headまたはrecord countを外部 commitmentとして置く。真正性anchorが無い状態では auto-recoverせず inspect-only/quarantineにする。

### 9. [must-fix / activation-blocking] `TrustedRoot` は canonical/provision済みであることを証明しない

**所見**: fd/dev/inoだけの constructible capabilityでは、rootより上の耐久性・site canonical性・repoとの失敗ドメイン一致を担保できず、P2は成立しない。

**根拠**: `brief.md:62-64`、`s2-plan.md:380-388,548-552`、`docs/mutation-restore-durability-design.md:158-169,384-393`。

**壊れ方**: 呼出側が新規 `/tmp/state-root` を作るが、その親directoryをfsyncせず、fdとfstat値から `TrustedRoot` を構築する。S3はleafからrootまではfsyncするが、rootの親entryは耐久化しない。変異後の障害でroot名だけが消え、target変異は残る。別 processが異なるrootを渡せば、それぞれ独立したactiveを作り、同じcheckoutを二重に変異できる。

**成果物影響**: journalへ到達できない汚染木、split-brain attempt、欠落trialが発生し、その木での受入・campaign値が台帳またはcertified選択へ混入しうる。

**提案**: `TrustedRoot` を自由構築できるdataclassにせず、canonical resolverがroot値、親entryのprovision receipt、repo/incarnationとの束縛を検証して発行するopaque capabilityにする。issuer不在の現waveでは`arm`がmutation callbackへ到達しないよう固定し、P2を「codecはroot非依存」に狭める。

### 10. [nit / activation blocker] pre-arm crashでは部分bytesのtempが残る

**所見**: S2が消すのはlive targetの部分bytesであり、prepare途中の未登録tempには部分bytesが残りうる。

**根拠**: `s2-plan.md:241-255`、`brief.md:31-37,53`。

**壊れ方**: deterministic tempをcreateし、replacementの一部を書いたところでprocessが死ぬ。`PreparedReplacement` は返らず、armedにもname/inode/hashが無い。targetは不変だが、部分tempは同じtarget directoryに残る。後続repairは所有権を証明できず、自動削除してはならない。

**成果物影響**: 本waveは未配線なので現時点のcertified集合への直接影響はなく、nitとする。先行活性化するとconsumer quarantineやcleanlinessを止め、trial欠落を生む。

**提案**: 「部分bytesを作らない」を「live targetに部分bytesを作らない」と限定する。pre-arm残骸をquarantineするconsumer gateが入るまでactivationを禁止し、将来はpreparing intentまたは実測済み`O_TMPFILE` protocolで閉じる。

### 11. [nit] 単体test名がL-Bの物理耐久性まで証明したように読める

**所見**: plan本文はL-B UNKNOWNを維持しているが、`durable`というtest名・状態タグがfsync syscall順序と物理永続性を混同しうる。

**根拠**: `brief.md:39-45`、`s2-plan.md:461,468-471,557-559`、`docs/mutation-restore-durability-design.md:397-403`。

**壊れ方**: mock/単体testで「temp fileとdirectoryにfsyncが呼ばれた」ことを確認し、`test_prepare_returns_durable...` が緑になる。その後、成功済みfsync bytesを失うnode-deathが起きても、そのtestは検出できない。test名やdoc状態だけを根拠にactivation gateを開くと、UNKNOWNをPASSへ丸める。

**成果物影響**: 現計画の`L-B UNKNOWN`記述を維持する限り直接影響はなくnit。状態タグからD130条件3やactivationをclosedにすると、耐久性根拠の無いtrialが受理される。

**提案**: test名を `issues_and_orders_fsync` / `returns_after_successful_fsync_syscalls` に変更し、doc状態を「syscall順序実装済み・node-death永続性未計測」と固定する。

## 総括

**must-fix**: 1〜9。特に、transitive code identity、任意callbackによるclean、process-local poison、active cleanup raceは実装入り前に閉じる必要がある。S2/S3のlease・canonical root・真正性anchorをscope外のままにするなら、今waveはcodec/FSM/低レベルprimitiveまでに縮め、`recover`・`clean`・結果capabilityを発行しないのが最小修正である。段4の変異事前登録は、診断文字列だけの変化をKILLに数えず、target bytes、journal state、callback非呼出し、active/last-clean、再open後の判定を検査対象にする。

**nit**: 10〜11。pre-arm temp残骸とL-B UNKNOWNはplan自身も概ね認識しているが、activation blockerと主張範囲を明文化すべきである。