## 検査条件

[実測] HEAD は `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3`、worktree は clean。指定 4 文書と現物コードを静的に検査した。sandbox が read-only のため pytest は実走していない。

## A-1 — 再利用可能 capability は発行後の durable evidence 改竄を見逃す

**主張:** validator と adapter 利用の間に TOCTOU があり、「変更後も malformed marker を拒否する」という受理表は成立しない。

**[実測]** 現行 adapter は admission root lock 内で marker を読み、その直後に同じ lock 内で observation row を作る。[s8b_attempt_registry.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:1003)、[s8b_attempt_registry.py:1529](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:1529)。一方プランは capability を再利用可能にし、adapter 側では seal と identity equality だけを検査して path・marker・claim・主台帳を再読しない。[s2-plan.md:88](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2107-t1851-b1/artifacts/t2107-t1851-b1/s2-plan.md:88)、[s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2107-t1851-b1/artifacts/t2107-t1851-b1/s2-plan.md:108)。

**具体的な破れ方:** 正しい marker から capability を得た後、marker を削除する、extra key を足す、または claim・主台帳を改竄してから `begin_attempt_observation()` へ渡す。identity は変わらないため observation-start が追記される。プランの負例はすべて capability 発行前の改竄であり、この順序を検査しない。

**深刻度:** `blocker`

## A-2 — capability は registry slot 全体へ束縛されていない

**主張:** プランがいう「別 slot への移植拒否」は、予定された identity 集合では実装できない。

**[実測]** registry slot identity は holdout、configuration、`repetition`、`attempt_ordinal` の四軸だが、capability assertion 案には後二軸も `schedule_row_sha256` もない。[s8b_attempt_profile.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_profile.py:272)、[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2107-t1851-b1/artifacts/t2107-t1851-b1/s2-plan.md:92)。現行 `_consumption_identity()` も slot に対して cell equality と attempt ID の prefix しか検査しない。[s8b_attempt_registry.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:139)。

**具体的な破れ方:** 同一 cell の slot B を予約しながら、caller が slot A の `attempt_id` を reservation に入れ、A の marker capability を渡す。capability と `_AttemptState.attempt_id` は一致し prefix 検査も通るため、A の consumption marker で B の observation-start を開ける。プランの「別 attempt capability」負例は、state 側の attempt ID も A にそろえるこの入力を殺さない。

**深刻度:** `blocker`

## A-3 — legacy の正当な受理形は維持されない

**主張:** 「正しい legacy claim・主台帳があれば legacy capability を再構築できる」という受理表の入口は存在しない。

**[実測]** 通常の `finalize_floor_holdout_admissions()` は current measurement-generation state だけを発行する。[s8b_holdout_admission.py:1715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:1715)、[s8b_holdout_admission.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:1795)。inspector の legacy token は局所的な `inspection_states` に置かれるだけで `_cell_states` へ登録されず、戻り値も token ではなく inspection receipt である。[s8b_holdout_admission.py:6227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:6227)、[s8b_holdout_admission.py:6422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:6422)。新 validator が使う `_cell_state()` は登録されていない token を拒否する。[s8b_holdout_admission.py:4151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:4151)。

**具体的な破れ方:** exact legacy marker、legacy claim、主台帳がすべて正しくても capability を発行できず、必須 keyword 化された adapter は拒否する。これは brief の「legacy v1 validator を残し、受理形を減らさない」に反する。[brief.md:36](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2107-t1851-b1/brief.md:36)

**深刻度:** `blocker`

裁定パッケージ候補は、legacy adapter 受理を保存する admission-owned再検証入口を設けるか、既存 legacy 受理を前向きに廃止するかの二択である。後者は現 brief の不変条件を覆すため親だけでは選べない。

## A-4 — P1-c は B1 の境界を越え、それでも production caller を作らない

**主張:** adapter 差し替えを B1 に移しても capability validator の production caller は生えず、前 wave の六段境界だけを壊す。

**[実測]** 前 wave の終端裁定は `B1 (claim/marker capability) → A (core/profile/adapter)` と明記する。[s4-adjudication-r2.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md:29)。現 launcher は adapter を一引数で呼ぶだけで validator を呼ばず、プランも launcher を変更しない。[s8b_floor_attempt_launcher.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_attempt_launcher.py:533)、[s2-plan.md:152](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t2107-t1851-b1/artifacts/t2107-t1851-b1/s2-plan.md:152)。現 campaign は adapter/launcher ではなく admission-aware wrapper から直接 ticket を consume する。[s8b_floor_campaign.py:5795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:5795)。

**具体的な破れ方:** B1 checkpoint の API で現 launcher を動かすと必須 `consumption_marker` が無く停止する一方、現 campaign は新 validator を通らない。したがって「adapter を含めれば恒真 API ではない」という P1-c の理由は偽である。

**深刻度:** `blocker`

裁定パッケージ候補として、推奨は前 wave どおり adapter を単位 A に戻し、slot codec 確定後に A-1/A-2 を閉じること。launcher/campaign まで B1 に引き込む案は単位 C を先取りするため非推奨。

## A-5 — T-2107 は二つの異なる分類面を一つの authority に混ぜている

**主張:** プランの三択結論 `(i)` は、literal な launcher pre-output classifier と campaign の最終 excluded reason を混同した形では成立しない。

**[実測]** `ClassificationAuthority` が名乗るのは launcher の pre-output policy であり、実際の純関数は post-probe、launch failure、None の三結果だけである。[s8b_floor_attempt_launcher.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_attempt_launcher.py:105)、[s8b_floor_attempt_launcher.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_attempt_launcher.py:378)。pre-probe、`reps`、`session_cv_max`、rep integrity、performance は campaign 側の別ラダーである。[s8b_floor_campaign.py:6077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:6077)、[s8b_floor_campaign.py:6132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:6132)。しかも最終 terminal は caller-provided `terminal_builder` が作る。[s8b_floor_attempt_launcher.py:628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_attempt_launcher.py:628)。

full campaign policy と読む場合、プランは `use_perf` も落としている。`use_perf` は perf receipt から決まり、同じ ScalePoint の counter status を valid にも partial にも変える。[s8b_floor_campaign.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:446)、[s8b_floor_campaign.py:1891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:1891)。launcher の external evidence digest は post-probe と launch failures しか含まない。[s8b_floor_attempt_launcher.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_attempt_launcher.py:362)。

**具体的な破れ方:** full policy digest を固定しても caller が terminal builder の excluded reason を書き換えられる。また同じ rep observation を `use_perf=False` と `True` で評価すると valid と partial が分かれるが、現 classification evidence はその差を束縛しない。

**深刻度:** `blocker`

修正結論は条件付きである。D1380 を字義どおり launcher pre-output policy と読むなら `(i) 機械導出可能` だが、policy は二理由の precedence と probe semantics に限定され、CV 閾値は含まない。四理由すべての権威を意図するなら `(iii) unit C で導出主体と perf/reps/CV 束縛を launcher 側へ移した後に可能` である。

## A-6 — 「read 側だけなので書き出す bytes は不変」は広すぎる

**主張:** admission document の encoding は不変でも、B1 は adapter の書込み到達集合を変えるため DW-O10 不成立とは断言できない。

**[実測]** adapter は marker 検証後に `observation-start` を構築し、candidate registry bytes を staging、replace、fsync する。[s8b_attempt_registry.py:1539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:1539)、[s8b_attempt_registry.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:1028)。

**具体的な破れ方:** 正しい current marker は変更前には legacy path lookup で拒否され registry bytes を書かないが、変更後には capability が通り observation-start を追記する。逆に raw legacy 入力は変更前には追記し、変更後には capability 不在で追記しない。marker・claim・admission ledger の個々の bytes は同じでも、producer が実際に書く byte 列の集合は変わる。

**深刻度:** `real`

## A-7 — adapter 不一致から現 campaign の成果物影響へ一般化している

**主張:** path 不一致は実在するが、現 campaign が adapter を利用しているという DW-G05 の一般化は反証される。

**[実測]** current marker は `measurement-generation-consumed/`、adapter は `consumed/` を見るため静的不一致自体は real。[s8b_holdout_admission.py:4519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:4519)、[s8b_attempt_registry.py:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_attempt_registry.py:1458)。しかし current campaign は `finalize_floor_holdout_admissions()` と `_wrap_admission_aware_measure()` を使い、attempt registry launcher は呼ばない。[s8b_floor_campaign.py:7722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_campaign.py:7722)。

**具体的な破れ方:** 「放置すると現 campaign の certified proof が誤束縛される」という現在形は再現しない。これは単位 C で launcher を接続した後に発火する将来 blocker であり、現物への即時影響ではない。

**深刻度:** `real`

## A-8 — 親の token hit 数と field 参照の説明は再現しない

**主張:** 「repo 全体 22 hit」と「唯一の field 参照は `token.protocol_sha256`」は、どちらも実測値として誤っている。

**[実測]** `rg -n 'CellHoldoutAdmission' .` は 31 line hit、うち production file が 26、既存 insight が 5 だった。exact class 名だけでも production file に 10 line hit ある。[s8b_holdout_admission.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:48)、[s8b_holdout_admission.py:6229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:6229)。また 1727 行の `state.token` は `_ReservationState.token: FloorHoldoutReservation` で、`CellHoldoutAdmission` ではない。[s8b_holdout_admission.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:369)、[s8b_holdout_admission.py:1727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:1727)。

**具体的な破れ方:** 直ちに誤受理は生じないが、親 brief の「唯一の consumer を数え切った」という監査証跡には使えない。

**深刻度:** `nit`

## A-9 — field 追加そのものから serialized bytes への流出は反証材料なし

**主張:** `CellHoldoutAdmission.measurement_generation_claim_digest` の追加だけが marker・claim・台帳・result の field を増やす経路は見つからなかった。

**[実測]** cell token は `_cell_states[id(token)]` の process-local state に結び付けられ、production で直接読む公開 field は mapping key 作成時の `token.cell_id` だけである。[s8b_holdout_admission.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:434)、[s8b_holdout_admission.py:1819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:1819)。`asdict`、`astuple`、pickle、位置引数による外部構築への流れは見つからなかった。

**具体的な破れ方:** 反証材料なし。変わるのは dataclass の equality、hash、repr shape であり、A-6 の adapter 書込み到達集合とは別問題である。

**深刻度:** `nit`

## A-10 — 深い marker 再導出と threshold pin には反証材料なし

**主張:** capability 発行時の canonical read、current generation ID 再導出、`session_cv_max="0.10"` の policy bytes への収録方針は正しい。

**[実測]** canonical reader は symlink、non-regular、複数行、非canonical JSON を拒否する。[s8b_holdout_admission.py:1228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:1228)。`_measurement_generation_claim_identity()` は role と campaign run ID から generation ID/digest を再導出するため、プランの追加呼出しは現在の弱い手検査を狭める。[s8b_holdout_admission.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_holdout_admission.py:835)。CV 閾値を省けば、例えば reps 5 の `[90,95,100,105,110]` は閾値 `0.10` では valid、`0.05` では performance anomaly となり、同じ authority digest で結果が変わる。したがって full classifier を名乗る場合の P1-b は refuted で、プランの threshold 収録が必要である。[s8b_floor_stats.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2107-t1851-b1/orchestrator/campaign/s8b_floor_stats.py:126)

DW-O09 についても、指定 schema/path を pin する凍結 manifest・golden・review ledger の反例は見つからなかった。

**具体的な破れ方:** 反証材料なし。ただし A-1 の発行後改竄と A-5 の authority surface 混同は、この発行時検査の正しさだけでは閉じない。

**深刻度:** `nit`

## 総括

blocker は **5 件**。

プランはこのまま実装子へ渡せない。最低限、次が必要である。

- capability 使用時に durable marker・claim・主台帳を同一 lock 内で再検証する。
- attempt ID と registry の四軸 slot identity を全単射で束縛する。
- legacy 受理維持について裁定を取り直す。
- adapter を単位 A に戻す。
- T-2107 を launcher-only と full campaign classifier に分離し、三択結論と policy document を書き直す。

pytest は実走しておらず、緑の主張はない。