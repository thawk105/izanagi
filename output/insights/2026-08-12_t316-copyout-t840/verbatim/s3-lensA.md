静的レビューの判定は **NO-GO** です。A の方向性は維持できますが、B は「既知 CLI の起動前拒否」に留まり、「非認証成果物としての機械隔離」にはなっていません。

pytest・build・実測は行っていません。read-only の静的検索と SHA-256 比較のみで、worktree は clean です。

## F1 — B の分類は認証済み選択へ接続されない

- 重大度: blocker
- 主張: registry に `NON_ADMISSIBLE` / `QUARANTINE_GATED` を追加しても、下流の campaign admission・Layer3 report はその分類を読みません。したがって「非認証成果物として機械隔離」は成立せず、既知 2 CLI の起動前拒否だけが実効差分です。
- 根拠: `orchestrator/campaign/materializer_admission.py:69-99` は registry の射影と診断 dict を返すだけです。coder receipt は `orchestrator/campaign/build_admission.py:462-482` の `class="coder-authored"` / `authority_kind` までで quarantine/site を持たず、`orchestrator/campaign/artifact_admission.py:720-785` は trigger binding の特例後、全 post-policy artifact を `admission_status="admitted"` にします。Layer3 は `orchestrator/campaign/layer3_report.py:424-438,586-600` でその `"admitted"` だけを certifying input 条件にしています。
- 成果物影響: registry 外または quarantine 非通過経路の structurally valid coder campaign も、静的帰結として `admission_status=admitted` のまま report/proof chain に参照され得ます。
- 提案: 本 wave の B を「red/kickoff の bounded pre-build deny」と改称・縮小するか、成果物単位の隔離を T-841 と一緒に裁定パッケージへ戻してください。後者を本 wave へ密輸してはいけません。

## F2 — `QUARANTINE_GATED` は quarantine 通過を観測しない恒真ラベルになる

- 重大度: blocker
- 主張: 計画された registered helper が観測するのは entry-point site の静的 status だけで、当該 iteration の `DiffQuarantineResult.passed` ではありません。登録済み site では status 判定が常に通るため、名前に反して quarantine の実発火証拠になりません。
- 根拠: 実際の gate result は process-local な `orchestrator/campaign/p3_s4_loop.py:193-276` で、build との順序は個別 driver の `:941-955` にしかありません。一方、authority action は `orchestrator/campaign/build_admission.py:253-278` で token を発行するだけです。予定正例の母体である `orchestrator/tests/test_p3_exploration_namespace.py:99-137` は quarantine を `passed=True` に差し替えて build 到達だけを検査するため、driver から quarantine 呼出しを外してもこの正例単体は緑のままです。既存の別 driver test が偶然捕捉するかは未実走・未確認です。
- 成果物影響: registry row と token 発行を残したまま gate 呼出しが脱落・後置されると、通常の coder admission/WAL/COMMIT 系列へ進めます。
- 提案: `QUARANTINE_GATED` 各 site について、gate の失敗結果を注入して build・WAL が 0 である負制御と、gate 呼出し削除変異を事前登録してください。registry equality は補助証拠に格下げすべきです。

## F3 — AST 閉包の走査 root 外に実在する issuer がある

- 重大度: must-fix
- 主張: `orchestrator/campaign/**/*.py` 固定走査は repository-wide な coder entry-point 閉包ではありません。走査外へ新しい issuer を置いても黙って通り、現に実行可能な走査外 issuer が存在します。
- 根拠: 現行の build-launch closure 自体も `orchestrator/tests/test_s8b_floor_campaign.py:1628-1668` で `orchestrator/campaign` だけを root にしています。`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:2-10,65-99` は低位 `add_coder_build_authority_argument` を直接使い、`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_job.sh:422-428` から実行されます。この smoke 自体は `smoke_driver.py:48-52` で trigger driver を通るため、現在の quarantine bypass 実例だとは主張しませんが、走査母集合が閉じていない証拠です。
- 成果物影響: runnable producer が registry/site 台帳から欠落し、その成果物に登録 site の分類参照を与えられません。
- 提案: tracked Python 全体を走査し、test・歴史 fixture の除外は exact registry にしてください。走査外 executable を許すなら、その出力を非認証とする別の機械境界が必要です。

## F4 — red/kickoff の起動前拒否は具体的な過剰拒否

- 重大度: must-fix
- 主張: T-840 は成果物を非認証として隔離する裁定ですが、計画は現在正当に起動できる red/kickoff の明示 opt-in 実行自体を消します。これは「分類」ではなく既存の診断・配線 build の削除です。
- 根拠: kickoff は `orchestrator/campaign/p3_kickoff.py:89-118` で opt-in token 後に exploration namespace の二つの campaign を実行します。red も `orchestrator/campaign/p3_s4_red.py:142-175` で liveness-red / verify-red を実行します。現在の契約テストも `orchestrator/tests/test_p3_exploration_namespace.py:313-356` で両 CLI を明示的な正例として扱っています。
- 成果物影響: kickoff の配線 WAL/cache と red-path の負制御 WAL が生成されなくなり、探索・診断台帳の受理集合が縮みます。
- 提案: 「pre-build denyで廃止」か「実行可能だが certified consumer が拒否する非認証 lane」かをユーザー裁定へ返してください。後者の receipt/consumer 束縛は本 wave 内で暗黙実装しないこと。

## F5 — A の TOCTOU 制御は差し替える pathname が違う

- 重大度: must-fix
- 主張: 計画の「copy 後に元 staging path を差し替える」試験では、clean destination を pathname で再 open する実装や、destination entry の差し替えを検出できません。同一 destination fd の主張に対する帰属試験になっていません。
- 根拠: 現行 `full_sha256` は `orchestrator/campaign/buildcache.py:87-117`、fsync は `:318-333` で pathname を再 open します。また build runner は `:1121-1137` の直接 `subprocess.run` だけで、process-tree の終了・残存子孫を確認しません。未実装案への静的指摘であり、実際の差し替え発生は未確認です。
- 成果物影響: held fd の nm/SHA と、最終 directory entry が指す binary が分裂すると、manifest の SHA と fresh build 直後に実行される bytes が異なり得ます。
- 提案: source ではなく clean destination entry を copy後・hash後に置換する負制御を追加し、rename 直前まで `fstat(fd)` と no-follow `stat(name, dir_fd=...)` の dev/inode/type/size/time を照合してください。ただし同一 UID 競合を完全に防ぐ主張はしないこと。

## F6 — A の保証は downstream 実行時の binary identity まで届かない

- 重大度: must-fix
- 主張: copy-out が固定できるのは cache publish 時点までです。公式 floor も hash 後に pathname を `measure_fn` へ渡すため、brief の「proof chain の binary 同一性を直す」という読み方は過大です。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:2290-2313` は path を hash して `binary_sha256_at_measure` を決め、その後 `:2315-2321` で同じ文字列 path を measurement へ渡します。`orchestrator/campaign/s8b_materialization.py:15-17` も content-store resume loader 等を未閉鎖と明記しています。
- 成果物影響: 同一 UID の path 差し替えがあれば、floor/oracle report が記録する `binary_sha256_at_measure` と実行 bytes が分裂し得ます。発生実績は未確認です。
- 提案: 本 wave の主張を「cache publish inode の厳格化」に限定してください。fd-to-exec、process-tree containment、store/resume の実行束縛は host-security 系の別裁定へ返すべきです。

## F7 — calibrator は別の認証済み成果物 intake で、B の外に残る

- 重大度: must-fix
- 主張: shared build cache の publish 点が二つでも、calibrator は任意 binary path を受けて accepted calibration を registered namespace へ publishする別系列です。B が「全 coder-derived 成果物」を意味するなら scope 漏れです。
- 根拠: `orchestrator/calibrator/cli.py:124-154` は `--binary` と自己申告 SHA を受け、`:645-687` で trace/hash を検査し、`:774-855` で accepted artifact を registered namespace に publishします。build-admission/quarantine classification はありません。公式 shell も `tools/pegasus/certify_calibration.sh:486-512,720-745` で別 scratch build の binary を渡します。登録 calibration は `orchestrator/campaign/env_contract.py:245-273` に参照され、`orchestrator/campaign/loop.py:68-84` で campaign 実行前に消費されます。
- 成果物影響: accepted calibration は環境契約と以後の campaign 実行 receipt に影響しますが、その binary の quarantine/site 分類は台帳にありません。
- 提案: 現 waveでは対象外と明記し、calibrator・shell materializer・任意 executable path の分類方針を裁定パッケージへ戻してください。公式 shell が現在不正だとは未確認です。

## F8 — v2 の失敗時残置方針が既存 helper と両立しない

- 重大度: nit
- 主張: 計画は v2 失敗時に staging と clean candidate を残すとしますが、現行 source/trace gate は fresh failure 時に渡された build directory を自動削除します。どちらを cleanup target として渡すか未定義です。
- 根拠: `_recheck_source_evidence` は `orchestrator/campaign/buildcache.py:1008-1038`、`_assert_trace_diff` は `:1041-1057` で `built_fresh=True` の directory を `_discard_build_dir` します。削除後検査は `:1075-1087` にあります。
- 成果物影響: completed bdir は作られないため自動の認証集合は変わりませんが、失敗した `.publish-*` を残すと手動回収時の昇格対象が曖昧になります。
- 提案: gate failure では staging/clean の双方を破棄し claim だけ残す、など exact failure matrix を決めてテストしてください。clean candidate を手動 publish 可能な回復物として扱わないこと。

## F9 — `DW-O09` の結論は支持できるが、親の根拠は閉包検査になっていない

- 重大度: nit
- 主張: `FROZEN_MANIFEST` だけを見て「source pin なし」とする論証は不十分です。ただし独立照合では、今回見つかった `p3_s4_loop_sort.py` の pin は歴史記録であり、現 wave の編集で凍結 bytes を repinする必要はないという結論自体は支持します。
- 根拠: `orchestrator/tests/test_frozen_artifacts.py:38-123` の 23 path は確かにすべて `output/` です。一方、`orchestrator/campaign/t080_freeze_migration.py:89-103` は `p3_s4_loop_sort.py` の source SHA を3箇所 pinし、`:1259-1275` は current source でなく固定 migration basis blob と照合します。read-only の独立 SHA 比較では current=`602e44fd…`、freeze record=`9b64f34b…`、migration blob=`0e716a6c…` で、既に三者が異なります。
- 成果物影響: 現 wave の凍結成果物 bytes・認証済み選択は変わりませんが、監査記録を「pin なし」のままにすると将来 live pin を見落とす手順が残ります。
- 提案: brief に「source pin は存在するが historical snapshot」と分類結果を追記し、repin不要と記録してください。

## 総括

blocker:

- F1: registry 分類が artifact admission / Layer3 に接続されず、非認証成果物隔離にならない。
- F2: `QUARANTINE_GATED` が実際の quarantine result を観測しない。

判定は **NO-GO** です。A の clean copy-out は修正後に進められますが、現計画の B を実装しても wave の表題どおりの成果物隔離は得られません。

| 暫定裁定 | 判定 | 理由 |
|---|---|---|
| P1 | 支持（限定） | shared build-cache namespace への production publish は `orchestrator/campaign/buildcache.py:851,992` の v2/legacy 二本。calibrator等は別 namespace。 |
| P2 | 支持 | final cache consumer は binary と host-generated metadata で足り、production の CMake tree 再利用は見つからない。 |
| P3 | 反証 | fixed-root AST は閉じず、registry status は runtime gate/resultにも下流 admission にも束縛されない。 |
| P4 | 未確認 | fake seam での検査可能性はあるが、既存 cache の `st_nlink`、`/proc/self/fd`、compute-node FS/syscall、正常 CMake output は未実走。 |

規律2について、A に明示的な warning 化・例外握り潰しは見つかりません。過剰拒否の具体例は F4 の red/kickoff です。hardlink 拒否によって現在正常な cache が落ちるかは未確認であり、親の実測が必要です。

T-841 への直接越境は現計画にはありません。しかし、F1を本当に「成果物の非認証分類」として直す変更は cache/WAL/COMMIT/consumer への束縛を必要とし、T-841 境界を越えます。したがって黙って実装せず裁定へ返すべきです。

scope 外として裁定パッケージへ返す項目:

- quarantine/site receipt を cache・WAL・COMMIT・freeze・`artifact_admission` に束縛する完全な成果物隔離。
- red/kickoff を廃止するか、実行可能な noncertifying diagnostic lane として残すか。
- repository-wide Python issuer、`output/**` executable、programmatic entry point、dynamic alias/token reuse の母集合。
- shell/direct-CMake materializer、calibrator の任意 executable path、S2/S3/S5/T152/silo-ladder 系成果物の扱い。
- build 子孫の終了保証、同一 UID 競合、cache path から実行までの fd/path identity、floor/oracle store/resume の束縛。

host-security boundary や certified safety を得たという明示的主張は段2にはありません。ただし、brief の「機械隔離」と「proof chain の binary 同一性」は F1/F6 の範囲まで狭めない限り過大です。