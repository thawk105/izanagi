# 段 6 敵対レビュー A (正しさ回帰・受理集合) — Claude 子 opus / read-only の逐語

親注記: pytest 未実走 (DW-O05)。判定は NO-GO、blocking 2 件 (RA-1/RA-2 と RA-7)。

読了完了 (patch / s4-adjudication-r5.md / s1-brief-r5.md)。以下、静的検査のみ。テストは一切走らせていない。

以下では
`TD` = `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch.py`
`TT` = `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/orchestrator/tests/test_pegasus_test_dispatch.py`

---

# 所見一覧

## [RA-1] blocking — E1 の `clean_return` gate は `completion_unknown` 分岐で丸ごと迂回でき、裁定 3 が閉じるはずだった系列が残っている

根拠:
- `TD:6613-6616` `clean_return = qsub_result.get("returncode") == 0 and not unknown_completion`
- `TD:6617` gate は `if not clean_return and not unknown_completion:` → SUBMIT_FAILED (`TD:6626-6644`)。**`unknown_completion=True` なら `clean_return=False` のまま `TD:6650` の submit-receipt 分岐へ到達する**
- `TD:6662` `if clean_return:` → False なので `_bind_resumed_submit_identity` は**呼ばれない**
- 到達する製品状態: `TD:5857-5897`。qsub の timeout / signal / output-limit / rc126 は `completion_unknown` を立て、`_recover_submission_identity` (`TD:5883`) が submit-receipt を封印し `submit-identified` を WAL へ書く (`TD:5727-5744`)。その後 final publish 前に crash すれば、`qsub-result.json` は rc124/`completion_unknown=true` のまま残る
- 攻撃者能力は裁定 3 が仮定したものと同一 (`submit-receipt.json` の差替のみ)。`auth_sha`/`request_sha`/`result_sha` は不変なので `_validate_submit_object` (`TD:2601-2623`) は内部整合しか見ず通す
- 偽 id は cancel-intent と一致しない (`TD:6787-6791` が `job_id_normalized == normalized` で filter) ので、そのまま `monitor_job` へ渡る → 他人 job への `qstat -f` は権限で rc≠0 → not-visible → visibility timeout → **qdel**。これは裁定 4 の A-3 が「wrong-group が落ちる主経路」と名指しした経路そのもの

成果物影響 (書ける): 段 1 brief の事前登録成果物影響「未実装なら wrong-group の既知 job が resume で受理集合へ入り monitor/qdel の対象になる」が**未達のまま残る**。受理集合は「clean return かつ qsub.stdout が parse 可能」な部分集合でしか縮小していない。台帳・レポートに「R5 resume consumer closed」「裁定 3 の系列を閉じた」と書けば虚偽になる。certified 選択には影響しない (実装は入っている) が、closure の主張範囲を「clean-return 部分集合」へ書き換える必要がある。

blocking。

## [RA-2] blocking (RA-1 と同根) — 同じ関数内に全分岐で使える強い束縛 (`submit-identified` WAL 行) があるのに比較していない

根拠:
- `TD:6685-6705` — `submit_matches` は **event 名だけ**で数え、`len != 1` でしか raise しない。行が持つ `qsub_request_id_raw` / `job_id_normalized` を receipt と一度も比較しない
- 一方 `TD:3966-3976` (`_validate_scheduler_lookup_chain`) は publish 時に `submit_event["qsub_request_id_raw"] != submit["qsub_request_id_raw"]` を**既に**照合している

つまり「publish では拒否するが、qdel を出す前には拒否しない」非対称が残る。E1 が選んだ束縛 (`qsub.stdout`) は 3 分岐中 1 分岐にしか存在しないのに対し、`submit-identified` 行は recovery 経路でこそ存在する (`TD:5735-5744`)。RA-1 の全分岐 (clean_return 有無・parse 可否) を 1 条件で閉じられる。新 I/O ゼロ、新 WAL event ゼロ、裁定 5 が落とした C-1/C-2 とは別物。

成果物影響 (書ける): RA-1 と同一。加えて、実装子が「E1 が裁定 3 の系列を閉じた」と主張した根拠が、実際には publish 時にしか成立していないことを台帳へ明記しないと、後続 wave が同じ closure を二重に主張する。

blocking。

## [RA-3] blocking-adjacent (実質は表現の限定) — 想定攻撃者能力の下では E1 の gate 自身が攻撃者データ

根拠:
- `clean_return` の入力 (`returncode` / `completion_unknown`) は `qsub-result.json` の field = 攻撃者が書ける。整合を要求するのは `qsub.rc` (`TD:2581-2590`)、`qsub-return` WAL 行 (`TD:6591-6612`)、receipt の `qsub_result_sha256` だけ
- WAL は genesis anchor を持たない: `TD:454-477` `_validate_journal_raw` は先頭行の `prev_sha256 is None` しか要求せず、chain を頭から再構築されると検出できない。final-receipt 封印前は journal head の外部固定点が存在しない (`TD:6509`)

したがって「dispatch dir へ書ける攻撃者」に対して E1 は何も閉じない。E1 が実際に閉じるのは **「submit-receipt.json 1 file だけが壊れた」故障モデル (部分書込・bit rot・実装 bug) かつ clean return** の場合のみ。

成果物影響 (書ける): レポートで「closure」「fail-closed」と書くなら故障モデルを明記しないと過大主張。「adversarial closure ではなく single-artifact corruption に対する fail-fast」へ限定表記すべき。

blocking (文言限定を要求する意味で)。

## [RA-4] nit — E1 の parse 失敗 silent return は、まさに identity が lookup 由来の場合を無検査で通す

根拠: `TD:6454-6457`。docstring (`TD:6448-6451`) はこれを正当化しているが、その分岐でこそ WAL に真の identity がある (RA-2)。成果物影響: RA-1 と同一のため単独では nit。

## [RA-5] nit — E1 は検証済みバイト列でなく disk を再読する

根拠: `TD:6453` `read_text`。hash 検証は `TD:6562-6568` (`verify_files=True`) → `TD:3701-3723` `_receipt_matches_file` で確かに**この時点より前に済んでいる** (質問 1 の確認事項は充足)。ただし検証と読取が別 I/O なので TOCTOU 窓がある。加えて `read_text` の `OSError` / `UnicodeDecodeError` は `DispatchError` へ変換されない (既存 `TD:6712` と同型だが、submit-receipt 有りの経路では新規曝露)。成果物影響: 書けない (到達には chain 再構築が要る)。nit。

## [RA-6] 所見なし (質問 2 の検証結果) — E1 は resume の他経路を塞いでいない

`TD:6706-6710` (receipt 無し + submit-identified 有り → raise)、`TD:6711-6738` (`qsub_raw is None and clean_return` の再 parse + receipt 新規作成)、`TD:6739-6757` (`_recover_submission_identity`)、`TD:6626` (SUBMIT_FAILED)、`TD:6768` (SUBMIT_UNKNOWN)、`TD:6489-6507` (published / pending final 短絡) はいずれも変更前と同値。liveness 回帰なし。

## [RA-7] blocking — E2 は monitor 側 `policy.account` と再検証側 `bound_policy.account` の一致を強制しておらず、**封印不能 dispatch** を新規に作り得る

根拠:
- monitor: `TD:5303-5307` は caller 由来 `policy.account`。`monitor_job` 内に snapshot 束縛検査は無い。`verify_snapshot_tree` (`TD:6424-6430`) は tree summary の比較だけで policy field を照合しない
- 再検証: `TD:4412-4416` は `bound_policy` (`TD:4313-4316` → `TD:2402-2409` で snapshot tree からロードし `policy_sha256` を照合)
- `_stage_and_publish_final` (`TD:4466-4485`) は **final-intent を WAL へ書いてから** `stage_final` → `validate_final_receipt_object(verify_files=True)` (`TD:4544-4551`)。ここで group 不一致が出ると raise し `final-receipt.json` は出ない
- 次回 resume は `_publish_pending_final_if_present` (`TD:4489-4525`) が同じ document を再検証して同じ raise → **永久に封印不能**。`_completed_dispatch` (`TD:1149-1157`) False → `_prune_retention` (`TD:1188-1193`) の victim にならない
- これは裁定 4 が変更 D を落とした理由 (「正しさを買わずに liveness を売る」) と**同型**であり、変異事前登録 (R4/R5) にも受入にも無い
- 到達性: `tools/pegasus/submit_tests.py:359` は `load_policy()` (repo 側) を使い snapshot は同 file を写すので実運用では一致する。到達には repo/snapshot の policy 乖離が要り、現実到達性は低い。ただし修正は 1 行 (`:5306` を `bound_policy.account` にするか、`monitor_job` 冒頭で `policy == snapshot_policy` を assert)

成果物影響 (書ける): 未修正なら「E2 は fail-closed で受理集合を縮小する」という主張に「ただし封印不能 dispatch を新規に作り得る」という留保が要る。裁定 2 が `:5255` を「冗長な整合 assert (恒真に近い)」と呼んだ前提は、この乖離下では恒真でない。R5 変異の「冗長 gate の診断 pin」という位置づけも成立しなくなる。

blocking。

## [RA-8] nit — E2 の retention 影響 (質問 3 の回答): 経路は実在するが本 wave で新規到達可能にはならない

根拠:
- 経路は実在: `TD:1149-1157` → `load_final_receipt` → `validate_final_receipt_object(verify_files=True 既定)` → `TD:4400-4416` の group 照合。False になると `TD:1188-1193` が `DispatchError("dispatch retention limit has no completed victim")` を上げ、`max_retained_dispatches=8` (`/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/tools/pegasus/test_dispatch_policy.json`) 到達時に**新規 dispatch が起動不能**になる
- ただし E2 後の monitor は group 不一致 footer を封印しない (`TD:5303-5315` → 120 s の accounting grace を消費して `accounting=None` / `ACCOUNTING_INCOMPLETE`)。`accounting is None` なので `TD:4400` の分岐に入らず、その final は prunable のまま。**poison を作れるのは E2 以前に封印された final だけ**であり、本 branch は未 release (裁定 11)
- `bound_policy` が各 dispatch 自身の snapshot から来る (`TD:4313-4316`) ため、policy file の `account` を後日変えても既存 dispatch を遡って毒さない。**これは実装の正しい選択であり、明示的に評価する**
- 実データ整合: `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve/output/env/pegasus/calibration/attempts/0_867876.nqsv/final-receipt.json:51` が `"Group Name:             SFC"`、policy の `"account":"SFC"` と一致。E2 の前提 (footer の Group Name == policy.account) は実 probe で成立している

成果物影響: 書けない (現実到達系列を構成できない)。裁定 6 の nit 分類は妥当。現実的な脅威は RA-7 の方。nit。

## [RA-9] 所見なし (質問 4 の回答) — `:4412` の `expected_group` 出所は snapshot 束縛済み、弱化経路なし

`bound_policy` は `_validate_qsub_request_object` (`TD:2402-2409`) が snapshot tree の policy を読み `snapshot.policy_sha256` と照合したもの。`_validate_scheduler_lookup_chain` (`TD:4349`) が既に使っている同一 object。呼出側が group を弱められる経路は無い。弱化経路があるのは `:5303` の方 = RA-7。

## [RA-10] nit — E3 の逐語 move は 10 条件とも保存。ただし**診断文言の回帰**があり、それは resume だけでなく既存 `lookup_scheduler_job` site にも波及する

根拠 (`TD:4651-4692` と patch の `-` 行を 1 条件ずつ照合):
- `job_id_normalized` → `request_name` → `user_name` → **(group をここから先頭へ移動)** → `queue` の `split("@",1)[0]` → `account` → `created_epoch_s` 型 → `created_epoch_s` 下限 → `state` 値域 → `hosts` 型 → 要素型。group 以外は順序・短絡・型検査とも不変
- `request_id_raw = str(...)` + `normalize_job_id` は旧同様 group 検査より前 (`TD:4668-4669`)。raw が壊れた候補は従来どおり `normalize_job_id` (`TD:648-654`) の文言で落ちる
- 戻り値: 旧 `str(candidate["state"])` / `tuple(hosts)` と等価。resume 側の旧 `tuple(str(host) for host in hosts)` も全要素 str 必須なので等価
- **変化**: group と他条件が同時に壊れた候補は、従来 `"scheduler lookup WAL candidate is malformed"` だったのが `"...candidate group is not the policy account"` になる。これは **`lookup_scheduler_job` の既存 site (`TD:4788-4799`) にも波及**する。resume 専用の変更ではない

成果物影響: 書けない (該当文言を assert する既存 test は repo 全体に無い。grep 済み、hit は plan 文書のみ)。nit。

## [RA-11] nit — E3 を resume へ適用しても正規 WAL は 10 条件を通る (質問 6 の回答)。false rejection は見つからない

根拠 (書き手から遡って照合):
- 書き手 `TD:4900-4914`: `execution_hosts=list(...)` は `_BNODE_RE.findall` 由来の str list (`TD:3117`)、`created_epoch_s` は `_nqsv_created_epoch` (`TD:1512-1531`) の **`int`**、`state` は `_QSTAT_STATES.get()` の値 (`TD:3110`)、`queue` は `@` 込みの生文字列 (`TD:3116`) で `split("@",1)[0]` 比較に合う (`TD:3122` と同式)、`group_name` / `account` は identity gate (`TD:3118-3125`) を通った `policy.account`
- 引数も同値: resume は `exact_job_name=scheduler_job_name(snapshot)` / `expected_user=str(request["submit_user"])` (`TD:6680-6682`)、lookup は `TD:4733-4734` で同式。`qsub_started_epoch_s` は request 由来で `TD:4726` が同一性を照合済み
- ただし resume の `matched_results` 選択 (`TD:6668-6676`) が既に `candidates[0]["job_id_normalized"] == normalized` を要求するので、E3 が resume で**新たに**落とせるのは「id は一致するが他 9 項が壊れた候補」= 製品が書けない WAL のみ。裁定 1 の「closure は主張しない」と整合し、純増検出力は forged WAL に対してのみ
- 逆向きの liveness: 落ちたときは resume が DispatchError で abort し final を封印しない → RA-7 と同じ「封印不能 + prune 不能」。従来の resume は同入力を素通しできた。入力集合が非製品 WAL に限られるので nit

成果物影響: 書けない。nit。

## [RA-12] nit — 新 test の証拠力: R6 正例の WAL 行は製品が publish できない形

根拠: `TT:1545-1580` `_append_matched_lookup_result` が作る行は `raw` / `returncode` / `signal` / `timed_out` / `output_limited` を欠く。`_validate_scheduler_lookup_chain` (`TD:3828-3849`) はこれらを必須にするので、この行を含む dispatch は実 FS で publish 不能。R6 正例は「製品が publish できない WAL を resume が受理する」ことしか示さない。docstring (`TT:1546-1553`) はこれを自認している。成果物影響: 書ける (変異表 R6 の「過剰拒否を検出する正例」欄は、実 publish 可能な入力での過剰拒否を検出しない)。nit。

## [RA-13] 情報 (質問 7 の回答) — 静的には**新たに赤くなる既存 test は見つからない**。ただし実測ではない

根拠:
- `validate_nqsv_accounting` の呼出は in-file 2 箇所のみ (`TD:4412`, `TD:5303`)。`orchestrator/campaign/silo_ladder_rung1.py:3662` の `validate_nqsv_accounting_epilogue` は同名接頭辞の別関数で無関係 (repo 全体 grep 済み)。keyword-only 必須引数の追加で壊れる外部 caller は無い
- `_accounting()` の既定 group は `"SFC"` = `policy.account` (`TT:400`)。`group="OTHER"` を渡すのは新規 2 test (`TT:974`, `TT:2658`) だけ。既存の `TT:933` (trailing garbage) と `TT:1022` は既定のまま
- 削除された `"resume lookup host receipt is invalid"` と移送された `"scheduler lookup WAL candidate is malformed"` を assert する既存 test は無い
- 既存 resume test は全件 `_qsub_artifacts` (`TT:1447-1459`) の一致 identity (`qsub.stdout = f"{JOB_ID_RAW}\n"`、receipt `(JOB_ID_RAW, JOB_ID)`) を使うので E1 を通る。`TT:2725` は receipt を unlink するので E1 分岐に入らない
- `orchestrator/tests/test_pegasus_tools.py` / `test_run_tests_nproc.py` は本 3 点の semantics に触れない
- `TT:961` の R3 test が期待する `failure_reason` は `TD:5308-5315` → `TD:5352-5360` で `accounting_error` になり、`"terminal NQSV accounting Group Name mismatch: ..."` を含む。accounting loop は scheduler を呼ばない (`TD:5270-5315`) ので `assert_drained()` と両立する

**実測していないので緑とは記録できない。** 実装子の「新たに赤くなる既存 test は無い」という主張は、静的には反証が見つからなかった、までが言える限界。

## [RA-14] nit (本 wave 由来でない) — resume の合成 result 生成が `O_EXCL` と衝突する

根拠: `TD:6569-6585` は `create_qsub_result` を呼ぶが、`create_file` (`TD:439-441`) は `O_WRONLY|O_CREAT|O_EXCL`。`create_qsub_result` は stdout/stderr/rc を先に書いてから json を書く (`TD:2312-2344`) ため、**qsub.stdout だけ書けて qsub-result.json 前に crash した dispatch** を resume すると `FileExistsError` (DispatchError でない) で落ちる。成果物影響: 書ける (resume liveness の既知欠落として裁定パッケージへ返せる)。本 wave の scope 外。nit。

---

# 判定

**NO-GO。**

1. RA-1 / RA-2 により、段 1 brief が事前登録した成果物影響 (wrong-group / 他人 job が resume で受理集合へ入り monitor/qdel の対象になる) が `completion_unknown` 分岐と `qsub.stdout` parse 不能分岐で**未達**。closure を主張できない。修正は `TD:6685-6705` に 1 条件を足すだけ (`_validate_scheduler_lookup_chain:3973-3976` と同じ比較)。
2. RA-7 により E2 は封印不能 dispatch を新規に作り得る (裁定 4 が変更 D を落とした理由と同型) のに、変異登録にも受入にも無い。修正は `TD:5306` の 1 行。
3. E2 の group 束縛そのもの、E3 の逐語 move、既存 test への静的波及は健全 (RA-9 / RA-10 / RA-11 / RA-13)。落とすべきは実装全体ではなく E1 の gate 選択のみ。

---

# 総括

E2 と E3 は裁定どおりに実装され、既存 test を静的に壊さず、`bound_policy` 選択も正しい。
問題は E1 の**束縛先の選択**にある。`qsub.stdout` は 3 つの identity 供給経路のうち 1 つでしか存在せず、残る 2 つ (unknown-completion recovery / parse 不能 recovery) がそのまま素通しになる。
そしてその 2 経路でこそ hash-chained WAL の `submit-identified` 行が真の identity を持ち、publish 側は既にそれを照合している。
E1 は「publish では拒否するが qdel の前には拒否しない」非対称を残したまま、closure を主張しかけている。
1 条件 (RA-2) と 1 行 (RA-7) で GO に転じる。それまで台帳に「R5 resume consumer closed」と書いてはならない。