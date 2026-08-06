判定は **段 5 進行 NO-GO**。以下は静的読解結果であり、pytest・実機検証は行っておらず、緑は主張しない。

なお、role 名 key の review ledger は `orchestrator/codex_roles/review_ledger.py:15-50` を確認したが、対象は 13 個の agent role source であり、今回の `wal.py` / `durable/` は pin 対象ではなかった。また設計文書の exact path に対する SHA pin も見つからなかった。この二経路は real 所見に数えない。

### 1. P1 は leaf hash を「実効 parser の identity」と誤認している

- **所見**: **must-fix** — `wal.py` の path pin がなくても、論理 identity を key にした admission/report pin が存在し、その transitive closure に `wal.py` と新 `durable/` が入っていない。
- **根拠**: `brief.md:58-61`、`s2-plan.md:503-515`、`orchestrator/campaign/artifact_admission.py:542,577,600,711`、`orchestrator/campaign/layer3_report.py:91-117,490,499`、`orchestrator/campaign/s8b_oracle_manifest.py:44-52,411-450`、`orchestrator/campaign/s8b_oracle_report.py:1264-1291`
- **壊れ方**: `artifact_admission.py` は自分自身だけを `validator_sha256` として記録しながら、判定は `wal.read_records_checked` に依存する。Layer3 と oracle も leaf generator source だけを hash する。抽出後に framing・例外変換・parse 順序が drift しても、validator/generator の hash は不変のまま受理集合だけが変わる。`wal.py` の path 検索ではこの pin を発見できない。
- **成果物影響**: `admission_decision.validator.sha256`、Layer3 `meta.generator.sha256`、oracle `generator_versions.report.sha256` が同じなのに、campaign の admitted 集合、report の `protocol_violation`、certifying input 集合、`source_refs` が変わりうる。既存 overlay の `wal_sha256` は WAL bytes を pin するが parser 意味論は pin しない。
- **提案**: P1 を「列挙した regression に対する現行 worktree の挙動不変」まで縮め、「proof identity が transitive semantics を閉じる」とは書かない。transitive closure digest の追加は schema・凍結 receipt を変えるため、**裁定パッケージ候補**として別 wave に送る。

### 2. 新規 file 集合は path 検索で見えない `clean_scan_digest` を確実に変える

- **所見**: **must-fix（主張修正）** — 「凍結成果物を動かさない」は、歴史的 frozen bytes と今後の proof lineage を分けていない。
- **根拠**: `brief.md:58-61,69-70`、`s2-plan.md:9-11`、`orchestrator/campaign/s8b_holdout_freeze.py:197-212`、`orchestrator/campaign/s8b_floor_campaign.py:1642-1661,1673-1688`
- **壊れ方**: `orchestrator/durable/*.py` と新 test file は repository file 列挙へ加わる。`clean_scan_digest` の preimage は file 名集合を含むため、各 file の個別 path pin がなくても digest は変わる。
- **成果物影響**: 次回 official run の `launch_certificate.clean_scan_digest`、certificate bytes SHA、journal の `launch_certificate_sha256`、そこから辿る proof reference が変わる。既存の凍結ファイル bytes 自体は変わらないので、両者を同一視してはならない。
- **提案**: brief に「歴史的 frozen bytes は不変。ただし新 commit の repository-files digest と今後の launch lineage は変わる」と明記する。既発行 expected digest の再利用が必要なら **裁定パッケージ候補**として invalidate/reissue の要否を確認する。

### 3. S1〜S3 の成果物影響は、いずれも本 wave の差分では発生しない

- **所見**: **scope must-fix** — `DW-G05` を厳密適用すると、brief の三つの成果物影響はすべて将来の activation を仮定した反実仮想であり、現 scope の blocker にはできない。
- **根拠**: `brief.md:9-29,31-37,47-50`、`s2-plan.md:537-555,559`、`docs/dev-wave/core.md:62-67`
- **壊れ方**: S1 は既存 WAL の bytes・API・受理集合を変えないことが成功条件。S2/S3 は harness、repair、root、consumer、ledger のどこからも呼ばれない。実装を完了しても現行 harness は引き続き in-place write で、journal も quarantine も存在しない。
- **成果物影響**: 本 wave 内では certified 選択、report、試行台帳の値・受理集合・参照はいずれも変わらない。したがって S1〜S3 の安全効果は `DW-G05` 上は **nit/backlog** である。実在する差分は所見 1・2 の source/proof lineage だけで、brief の安全効果ではない。
- **提案**: 段 4 で、(a) inert foundation を `DW-G05` の明示例外として実装するユーザー裁定を得る、または (b) S1〜S3 を activation program まで deferred にする、の択一にする。repair/consumer/harness を無断で scope へ足してはならず、これは **裁定パッケージ候補**。

### 4. `TrustedRoot` は capability になっておらず、P2 は成立しない

- **所見**: **S3 を残すなら must-fix** — issuer のない `TrustedRoot(fd, st_dev, st_ino, display_path)` は任意 caller が作れる値で、canonical root の権威を表さない。
- **根拠**: `brief.md:62-63`、`s2-plan.md:352,380-388,398,408,548,552`、`docs/mutation-restore-durability-design.md:162-169`
- **壊れ方**: canonical resolver が scope 外なのに public `TrustedRoot` を受け入れると、caller は任意 directory fd と自己申告 metadata を渡せる。nonce も immutable provisioner receipt ではなく文字列であり、現 worktreeには実在しない。missing を拒否すれば誰も `arm` できず、caller 値を受ければ split-brain を許す。
- **成果物影響**: 現 wave では caller がないため直接影響を書けず、S3 は backlog 相当。将来そのまま配線すると同じ repo に二つの `active` / `last-clean` が成立し、試行台帳の重複・欠落や、片側だけ clean とした結果の certified 採用が起こりうる。
- **提案**: 現 wave では stable な `arm` / `TrustedRoot` / nonce API を作らない。canonical resolver と provisioner が発行する root+incarnation receipt の exact schema を先に裁定する。scope 外なので **裁定パッケージ候補**。

### 5. `armed.writer` 一個では、実際に木を読む runner を束縛できない

- **所見**: **S3 を残すなら must-fix** — exact v1 schema は arm 後に生まれる child/PBS job を表現できず、後続 wave で schema を作り直す。
- **根拠**: `s2-plan.md:299-307,320-327,401-408`、`tools/mutation_harness.py:1277-1290,1132-1141`、`docs/mutation-restore-durability-design.md:212-225`
- **壊れ方**: 現 harness は target を変異した後で新 process session の runner を起動する。dispatch mode では、その先に別 PBS job も生まれる。`armed` 時点ではこれらの PID/PGID/start token/cgroup/job ID は存在しない。現在 process 一個だけを記録すると、owner 死後も runner が生存しているのに recovery が quiescent と誤認できる。
- **成果物影響**: `clean` と `active` 除去後に runner が `.pyc`、target、出力を再汚染し、その結果が試行台帳や report に載る。現 wave には consumer がないため即時影響はなく、stable v1 schema の実装自体を backlog にすべき所見。
- **提案**: attempt owner と動的な execution 集合、または全 child を包含する exclusive lease/scheduler receipt を設計してから schema version を固定する。U-5 / [T-360] に跨るため **裁定パッケージ候補**。

### 6. typestate API は S2 と verifier を任意 callback に逃がし、順序を強制しない

- **所見**: **must-fix if retained** — `MutationExecutor` / `RestoreExecutor` / `CleanVerifier` を caller callback にすると、S3 は「正しい最終 bytes」を見るだけで atomic replace・fsync・quiescence を検証できない。
- **根拠**: `s2-plan.md:327,352-370`、`docs/mutation-restore-durability-design.md:117-148,265-271`、`tools/mutation_harness.py:611-635`
- **壊れ方**: executor が従来どおり in-place write して正しい最終 hash を返せば `mutated` へ進める。verifier が syntactically valid な evidence hash を返せば、その意味検証は scope 外なのに `clean`、locator cleanup、`CleanAttempt` 発行まで進む。さらに original bytes が記録 HEAD blob に由来することを、`--no-replace-objects --no-lazy-fetch` で検証する issuer もない。
- **成果物影響**: crash 時に部分 bytes が残るか、HEAD と無関係な「原文」へ復元した状態で結果 ledger capability が発行される。結果として trial ledger と report の受理集合、certified selection の根拠が誤って広がる。
- **提案**: S3 自身が armed に束縛した S2 `PreparedReplacement` を commit し、S2 だけが発行できる receipt を消費する構造にする。`clean` は hardened HEAD、cleanliness、quiescence issuer の capability が揃うまで公開しない。issuer 群が scope 外なら `recover` / `clean` / `CleanAttempt` も今 wave から削る。

### 7. S1 の固定 signature は journal locator の安全な reader を提供していない

- **所見**: **must-fix if S3 retained** — `iter_binary_frames(path)` は path を reopen するため、dirfd・inode に束縛した `active` hard link 検証と整合しない。
- **根拠**: `s2-plan.md:34-39,362-386`、`docs/mutation-restore-durability-design.md:193-198`
- **壊れ方**: `active` の inode を検査した後、path-based iterator が同名の差替え・symlink・別 inode を読む TOCTOU ができる。S3 が独自 fd reader を実装すれば、S1 の「第二方言を作らない」を自ら破る。
- **成果物影響**: 検証した attempt と実際に clean/repair 対象にした attempt がずれ、誤った `clean` と台帳 capability が発行されうる。現状は未配線なので即時 product 影響はない。
- **提案**: S1 の固定 API に `iter_binary_frames_fd(fd)` または `iter_binary_frames_at(parent_fd, name, expected_dev, expected_ino)` を加え、`O_NOFOLLOW`・`fstat`・lock 済み descriptor のまま読む。signature 固定前に直す。

### 8. file 所有は素集合だが、三本同時投入は worker 契約違反

- **所見**: **must-fix** — file intersection と `conftest.py` 衝突は見つからなかったが、実行依存は S1→S2→S3 であり、signature を文書に書いただけでは並列実装可能にならない。
- **根拠**: `brief.md:78-81`、`s2-plan.md:9-13,17-39,175,315,364`、`docs/dev-wave/workers.md:19-23`
- **壊れ方**: S2 は S1 の `write_all` / `fsync_directory_fd` / `replace_name_at` を import する。S3 も S1 を import し、所見 6 を閉じるなら S2 capability に依存する。隔離 worktree で同時投入すると module がなく test import が赤になる。共有 worktreeなら未完成 API を読む race になる。
- **成果物影響**: integration test が赤になり report/ledger を発行できないか、S3 が S2 schema を複製して temp registration の受理集合を分裂させる。
- **提案**: worker 契約どおり S1 を完了・patch 展開後に S2、S2 完了後に S3 とする。少なくとも S1→(S2,S3) の二段では足りず、callback bypass を閉じるなら S1→S2→S3 が必要。

### 9. S2 の metadata policy は未裁定・未計測で、全 target 拒否になる可能性がある

- **所見**: **stage 4 ruling 必須** — plan 冒頭は「実装可能」と断定する一方、末尾で xattr/ACL/inode-flags policy の親裁定が必要と認めている。
- **根拠**: `s2-plan.md:1,223-233,540`、`docs/mutation-restore-durability-design.md:261-266`、liveness `README.md:41-59`
- **壊れ方**: 実 target/Lustre で `O_NOATIME`、xattr/ACL 列挙、inode flags ioctl のいずれかが利用不能なら、fail-closed 実装は全 target を arm 前に拒否する。逆に検査を省けば metadata を失う。生死確認は完全 bytes を測っただけで、この gate の通る正例を測っていない。
- **成果物影響**: activation 後に全 mutation trial が欠落して ledger が不完全になるか、metadata drift がテスト結果を変えて report/certified 選択を汚す。現 wave では caller がなく、`DW-G05` 上は backlog。
- **提案**: metadata の accepted set を段 4 で明示裁定し、activation 前に実際の mutation target で正例 probe を要求する。現 scope で安定 API を固定するなら **裁定パッケージ候補**。

### 10. L-B UNKNOWN は prose だけで、test 名と完了記録の過大主張を止められない

- **所見**: **must-fix（受入文言）** — brief の四項目は方向として正しいが、予定 test 名・root 契約・記録チェックリストまで落ちていない。
- **根拠**: `brief.md:39-45,67-70`、`s2-plan.md:381,461,497,557`、liveness `README.md:52-59,66-70`、`docs/mutation-restore-durability-design.md:397-408`
- **壊れ方**: `test_prepare_returns_durable_registered...` は fsync syscall 順序しか検査しないのに「durable」を成功事実として読ませる。S3 は provision 済み root より上を保証しないのに brief は「祖先耐久化」と省略する。将来の worklog が T-503 を単に「restore durability 完了」と書けば、L-B UNKNOWN と §9.1 の 1/4/5/6 未着手が消える。
- **成果物影響**: worklog/phase の activation gate が誤って開けば、物理 node death・consumer quiescence 未受入の run が trial ledger と certified 根拠へ入る。
- **提案**: test 名を `fsyncs_temp_and_directory_before_return` のような観測事実へ変える。全 module/receipt docstring に「成功した fsync の永続性を前件とする」「L-B UNKNOWN」を置く。worklog/design 状態は「部品のみ、unactivated、[T-486] deferred、§9.1 1/4/5/6 未完」を exact checklist にする。

### 11. docs index の状態同期が scope から漏れている

- **所見**: **nit** — design 本文だけ更新すると、`docs/README.md` の「実装ゼロ・実測ゼロ」が残る。
- **根拠**: `brief.md:69-70`、`docs/mutation-restore-durability-design.md:1-8`、`docs/README.md:50`
- **壊れ方**: design 冒頭と docs index が異なる状態を示し、後続が古い index だけを読んで実装・実測状態を誤認する。
- **成果物影響**: certified 選択・report・台帳の値への直接影響は書けないため、`DW-G05` 上は nit。
- **提案**: design 状態タグと同じ commit で `docs/README.md:50` も「生死確認のみ実測、S1〜S3 部品、未活性化」へ同期する。

### 12. `DW-G03` 上、repo-wide durable framework への一般化はまだ許されない

- **所見**: **nit** — U-4 は campaign WAL と mutation journal の共有を裁定したが、全 journal/checker 向け generic framework を正当化する独立二例はない。
- **根拠**: `docs/mutation-restore-durability-design.md:291-305`、`s2-plan.md:9-13`
- **壊れ方**: package 名と公開 export を根拠に第三の producer が採用すると、未検証の schema・repair・receipt 契約まで族一般化される。
- **成果物影響**: 現 wave の certified/report/ledger 変化は書けないため nit。
- **提案**: plan の「package root から S2/S3 を re-export しない」を維持し、docstring で T-503 の二 consumer に限定する。第二の独立 pair またはユーザー例外が出るまで一般 utility と呼ばない。

## 総括

**must-fix**

- P1 を source pin 不在から proof-chain 不変へ一般化しない。論理 validator/generator pin と repository file-set digest を明記する。
- `DW-G05` 裁定を先に行う。現 scope の S1〜S3 はいずれも product safety を変えず、原則 backlog である。
- S3 を残すなら `TrustedRoot`、incarnation、runner 集合、S2 capability、HEAD/clean/quiescence issuer、fd-based readerを設計し直す。現 plan の stable v1 / `CleanAttempt` は作らない方がよい。
- 実装順は S1→S2→S3。三本同時投入は不可。
- L-B UNKNOWN と未活性化を test 名・docstring・worklog acceptance checklist まで固定する。

**nit / backlog**

- metadata policy と実 target 正例 probe。
- `docs/README.md` の状態同期。
- `orchestrator/durable` を repo-wide framework として一般化しない。

削るべき中心は S3 の public `arm/recover/clean`・identity/root API。S2 単独にも caller がなく、S1 単独は active WAL を危険に晒すだけで成果物効果がない。一方、S2 を削って S3 だけ残すと atomicity を callback で迂回でき、成果は無意味になる。従って現三単位には有効な部分集合がなく、推奨は段 4 で foundation 例外を裁定するか、activation 全層が揃う wave まで延期することである。