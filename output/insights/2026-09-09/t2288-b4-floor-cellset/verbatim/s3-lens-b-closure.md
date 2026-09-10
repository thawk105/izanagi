## v4 bump の閉包漏れ

- `real 候補` — plan の「fixture が `F.SPEC_SCHEMA` を参照するので golden は変わらない」は逆である。fixture の schema が自動で v4 になり、canonical spec bytes と sha256 が変わる。その両方が HMAC 入力なので、literal な順序 golden も変わる。[test helper:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:208)、[HMAC inputs:1352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1352)、[plan claim:306](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:306)

  literal pin の実数は次のとおり。

  - literal 64 桁 hex の spec sha256: 0 箇所
  - literal 64 桁 hex の plan sha256: 0 箇所
  - literal canonical spec bytes: 0 箇所
  - literal HMAC 順序: 1 test 内に 2 箇所。session ID 8 件と measurement role 順 8 件。[session order:1342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1342)、[role order:1352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1352)

  現 fixture を v4 へ仮想適用すると、spec sha256 は `d955...31ba` から `d74f...fd8b`、plan sha256 は `4a77...008c` から `5942...1ef9` へ変わり、session 順は次になる。

  ```text
  pair-a/s0/candidate_2
  pair-a/s0/candidate_1
  pair-b/s0/candidate_2
  pair-b/s0/candidate_1
  pair-b/s1/candidate_1
  pair-b/s1/candidate_2
  pair-a/s1/candidate_2
  pair-a/s1/candidate_1
  ```

  role 順も 8 件中複数が反転する。したがってこの 2 golden の更新が plan から欠落している。

  成果物影響: 放置すると test は赤になり、また古い HMAC 順を正しい v4 plan と誤認すると window の planned session 順と plan hash の参照が不一致になる。

- `refuted 候補` — spec/plan hash を window header と summary へ運ぶ production 側の追加変更は不要である。plan hash は canonical plan から再計算され、window と summary は動的に `spec_sha256` と `plan_sha256` を複写する。[plan hash:1459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1459)、[window header:2241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:2241)、[summary:3055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:3055)

  成果物影響: この面を据え置いても新しい hash が自動で記録され、値・受理集合・参照は壊れない。

- `refuted 候補` — issuer test の schema 追従に手当ては不要である。issuer fixture は driver test の `_valid_document` を使い、その helper が `F.SPEC_SCHEMA` を参照する。[issuer fixture:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:65)、[driver helper:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:208)。issuer 本体も current `load_frozen_spec` を呼ぶ。[issuer loader:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:848)

  成果物影響: v4 schema への追従だけなら自動で、旧 v3 spec を参照する summary は fail-closed になる。

- `real 候補` — schema 追従とは別に、issuer test は全て実質 1 cell workload であり、二 workload の aggregation を通していない。fixture は cell 0 の threads を変えるだけである。[issuer fixture:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:68)。一方、本体は workload set を filename identity と authority derivation に使う。[identity:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:758)、[authority:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:913)

  成果物影響: この不足を放置すると、二 workload spec を受理しても authority の workload identifier が一 workload を落とす回帰を検出できず、成果物名と identity derivation の値が変わりうる。

- `refuted 候補` — meta-test 群への schema 由来の追加変更は不要である。`PUBLIC_DATACLASSES` は 23 class を no-default 検査し、`NOT_PROVEN` は 10 件 pin、`SESSION_STATUSES` は `environment_mismatch` の非包含だけを pin、`REQUIRED_FIELD_PATHS` は静的に 72 path である。[dataclasses:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:568)、[NOT_PROVEN/status:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:603)、[required paths:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:663)。wire field と dataclass field は変わらない。

  成果物影響: 据え置いても spec の必須 field 集合、status 受理集合、summary の limitation 項目は変わらない。

- `refuted 候補` — plan の新しい行番号 pin は、記載どおり 2 行を 2 行へ、docstring 3 行を 3 行へ置換する限り一致する。`798-816` は nonempty cells、`1181-1194` は全 cell の threads/records、issuer `412-413` は campaigns の `allow_empty=False` を指す。[cells:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:798)、[binder loop:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1181)、[campaigns:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:412)。active code 内の対象行番号 pin は現 docstring の 2 件だけである。[current pins:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:748)

  成果物影響: 等行数置換なら参照は正しく、成果物値・受理集合は変わらない。別の整形を混ぜると即座に陳腐化する。

## plan の数値主張の検証

- `refuted 候補` — 現 `test_floor_pair_driver.py` が 210 node、plan 適用後が 213 node という主張は正しい。静的展開では `REQUIRED_FIELD_PATHS` が 72 node、`_CAMPAIGN_BOUNDARY_CASES` 5 件が 2 test に展開される。[required paths:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:663)、[campaign cases:2677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:2677)。変更は mutation 04 が `3 -> 4` で +1、新規 2 test で +2、schema test の改名は 0 である。[plan:283](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:283)

  成果物影響: driver test file の台帳所要件数は正しく +3 になる。

- `real 候補` — issuer test は静的に 24 node だが、ledger には 26 node ある。余分なのは次の 2 件で、現 source に関数がない。

  - `test_identity_is_not_a_caller_surface_and_missing_protocol_is_named`
  - `test_real_finalize_floor_summary_is_accepted_before_missing_protocol_blocks_issue`

  [ledger stale 1:11488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/acceptance_duration_ledger.json:11488)、[stale 2:11497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/acceptance_duration_ledger.json:11497)、[current issuer tests:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:198)

  成果物影響: duration 台帳が現 node 集合であるという参照主張が 2 件分ずれる。

- `real 候補` — `22155 -> 22158` は「既存の stale issuer 2 件を残し、plan の driver 差分 +3 だけを加える」増分算術としては正しい。しかし現 source の対象 2 file と exact に照合した総数ではない。対象 2 file を exact reconciliation するなら、

  ```text
  22155 - 210 - 26 + 213 + 24 = 22156
  ```

  である。ledger 自身の `nodeid_count=22155` と map length は一致している。[ledger aggregate:22159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/acceptance_duration_ledger.json:22159)。なお ledger の coverage 実装は current collection との積集合だけを数え、余分な過去 node を禁止していない。[coverage:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/tools/update_acceptance_duration_ledger.py:323)

  成果物影響: `22158` を「current node exact」と報告すると台帳参照が誤る。過去 duration entry を保持する方針なら `22158` は map 件数としてのみ使用できる。

## 律速の判定と DW-G04

- `real 候補` — この変更だけでは実 checkout の凍結 spec は作れず、権威 floor 発行にも到達しない。`load_frozen_spec` は上から順に次を要求する。

  1. 実在する regular spec、caller sha256 一致、loaded HEAD の tracked blob と byte 一致。[loader:1206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1206)
  2. 実在・tracked・hash 一致の calibration。[tracked binding:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:614)
  3. artifact ごとの regular binary と binary sha256 一致。[binary:1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1135)
  4. artifact ごとの tracked build receipt、HEAD bytes、sha256、`s8b-binary-admission/v2` 内容一致。[receipt:1143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1143)、[receipt validation:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1091)
  5. accepted calibration と records/threads 条件、最後に `source_commit` が loaded HEAD の真の祖先であること。[calibration gates:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1153)、[ancestor:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1285)

  現物は accepted calibration 2 件だけで、tracked receipt 0、実 spec instance 0、D1641 campaign 0 である。[handoff:44](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/handoff.md:44)。worktree 内に利用可能な CCBench executable も見つからなかった。

  成果物影響: workload equality を外しても summary や authority artifact は 1 件も生成できず、材料レポートの floor 参照は増えない。

- `real 候補` — 律速は workload equality ではなく、その前段の実 spec、receipt、binary の欠落である。brief の「既存 accepted calibration を共有する二 workload spec」を発火 artifact とする主張は fixture でしか成立せず、既存 artifact path または measurement ID ではない。[brief P1-d:62](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md:62)、[plan admission:304](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:304)

  成果物影響: この wave を blocker 解消と記録すると、実際には構成不能な発行経路を利用可能と誤記する。

- `real 候補` — 現時点では「D1641 準拠には将来必要」よりも「DW-G04 により設計メモへ留める」が支持される。D1641 は専用 driver の実装を命じているが、その driver 自体は既に存在する。[D1641:35](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/verbatim-rulings.md:35)。追加の条件付き受理拡張には既存発火 artifact が必要で、fixture は代用にならない。[DW-G04:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/core.md:74)

  成果物影響: 設計メモに留めれば現在の certified 選択・レポート・台帳は変わらない。実装を先行すると利用不能な受理集合だけが拡張される。

## 変異の帰属

- `real 候補` — 候補 1、workload equality 復活。plan のままなら新しい二 workload 正例だけが赤になる。現 workload mismatch 負例は削除予定で、他 fixture は calibration workload と一致する。[current workload case:1069](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1069)、[planned positive:285](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:285)

  成果物影響: mutant は二 workload spec の受理集合を縮め、D1641 の全セル summary を生成不能にする。

- `real 候補` — 候補 2、quality gate 削除。`test_mutation_14...quality_only` だけが該当 rejected calibration を供給し、他条件は一致する。[quality test:1121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1121)

  成果物影響: rejected calibration で測定・floor 算出が可能になり、certified 値の受理集合を不正に広げる。

- `real 候補` — 候補 3、records gate 削除。帰属理由は records 一致 1 点だが、plan の「mutation 15 だけが赤」は誤りである。更新後 mutation 04 の `[records]` と mutation 15 の 2 node が赤になる。[mutation 04:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1087)、[mutation 15:1139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1139)

  成果物影響: calibration と異なる records の測定を floor に混入でき、floor 値の対象動作点が変わる。

- `real 候補` — 候補 4、threads gate 削除。更新後 mutation 04 の `[threads]` と新しい二 cell threads 負例の 2 node が赤になる。plan の単一 fail node 想定は不完全である。[current thread case:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1072)、[plan candidate:333](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:333)

  成果物影響: 異なる thread 数を一つの authority filename の単一 `threads` 値へ畳め、成果物 identity が入力集合を表さなくなる。

- `real 候補` — 候補 5、`SPEC_SCHEMA` を v3 に戻す変異。HMAC golden を正しく v4 用へ更新すると、赤は schema constant test、v3 rejection test、HMAC golden の 3 node になる。[schema tests:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:629)、[HMAC golden:1325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1325)

  `refuted 候補` — これは複数 test が同じ mutant を殺すだけで、DW-M03 の「一 fixture が複数理由で拒否される」過剰決定そのものではない。ただし期待失敗 node は完全な 3 件集合で登録しなければならない。[DW-M03:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/mutation.md:16)

  成果物影響: v3 の再受理だけでなく plan 順序と plan hash も旧値へ戻り、window/summary の参照が変わる。

- `refuted 候補` — env_tag/clocks の driver gate 削除を非登録とする判断は正しい。production verifier が driver loop より先に両方を拒否する。[verifier:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py:116)、[driver loop:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1181)

  成果物影響: driver の冗長比較だけを除いても production の値・受理集合・参照は変わらない。

- `refuted 候補` — calibration workload bytes 単独変異の非登録も正しい。sha256 と HEAD blob の検査が workload 比較より先に拒否する。[tracked binding:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:621)

  成果物影響: mutant は binder の workload 意味へ到達せず、成果物受理集合を変えない。

- `refuted 候補` — workload key 欠落・未知 key の非登録も正しい。`_parse_perf` の exact object が先行する。[perf parser:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:775)

  成果物影響: mutant は構文拒否され、floor 値・参照を変えない。

- `refuted 候補` — cell ごとの calibration ref 欠落等は採用しない wire 形なので、本変更の変異点ではない。[cell parser:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:798)

  成果物影響: 実在しない field の変異は現受理集合を変えない。

- `real 候補` — plan 未記載の帰属可能な変異点 1 は、cell loop を `cells[:1]` 相当へ狭める変異である。新しい二 cell threads 負例だけが、2 cell 目を検査しないため赤になる。単一 cell の mutation 04 は通るので帰属が一意になる。[cell loop:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py:1181)

  成果物影響: 2 cell 目以降の threads/records 不一致が authority identity と floor 集合へ混入する。

- `real 候補` — plan 未記載の帰属可能な変異点 2 は、issuer の `workload_values` を 1 件へ切り詰める変異である。現 issuer test では生存するため、二 workload issuer 正例を追加して exact workload set と filename identity を pin する必要がある。[issuer aggregation:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:797)、[filename:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:931)

  成果物影響: mutant は authority JSON と filename から workload を落とし、成果物 identity の値を変える。

## 親の実測値の検証

- `real 候補` — codex prompt の逐語は予定された編集面しか示さず、実際の編集、親段の ledger 更新、将来の fix を拘束しない。handoff の「T-2316 は launcher 2 file に限定」から、本 wave 全体との素集合までは結論できない。[handoff:28](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/handoff.md:28)。dev-wave では child prompt 外の受入・記録・land を親が担う。[dev-wave:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/.claude/commands/dev-wave.md:34)

  成果物影響: 誤って素集合と扱うと、後勝ちの ledger が他 wave の node/duration を落とし、台帳参照が変わる。

- `refuted 候補` — 現在の read-only snapshot では T-2316 worktree に対象 5 file の変更はなく、対応 process も確認できなかった。したがって「現在も稼働中」という親の時点依存主張は今の状態証拠にはならない。worktree registration と lock は残るが、生存証明ではない。[T-2316 gitdir:1](/work/1/SFC/tanab/izanagi/.git/worktrees/dev-wave-t2316-b4-base-site/gitdir:1)

  成果物影響: 現時点の直接衝突は確認できないが、過去の PID 情報だけで安全を一般化すると台帳取り込み順を誤る。

- `real 候補` — repository には `b4floor-*` worker worktree が issuer/test/ledger の dirty 差分を保持し、さらに `t2383-ledger`、`t2418-ledger`、`t2429-ledger` が同じ acceptance ledger の変更を保持する兆候がある。[b4floor ledger worktree:1](/work/1/SFC/tanab/izanagi/.git/worktrees/b4floor-fix5/gitdir:1)、[t2383 ledger worktree:1](/work/1/SFC/tanab/izanagi/.git/worktrees/t2383-ledger/gitdir:1)、[t2429 ledger worktree:1](/work/1/SFC/tanab/izanagi/.git/worktrees/t2429-ledger/gitdir:1)。一致する process は無いため「稼働中」の証明ではないが、未統合差分の衝突兆候ではある。

  成果物影響: stale worker の ledger を無監査で取り込むと nodeid_count、duration、issuer test の参照が巻き戻る。

- `real 候補` — ledger 衝突回避は既存の直列化経路で行うべきである。acceptance 前の post-claim merge で最新 main を取り込み、その木の JUnit から ledger を再生成する。land 時に main が進んでいれば、既存 lock 下で wave-side merge、再検査、再 acceptance を行い、rebase/force は使わない。[post-claim merge:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/operations.md:150)、[land retry:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/operations.md:164)

  成果物影響: この順序なら並行 wave の node/duration を保持した ledger を発行でき、後勝ちによる台帳欠落を防げる。

## scope の膨張と不足

- `real 候補` — 最大の scope 不整合は、brief が production/test 2 file としたのに、plan が issuer production file、ledger、canonical `docs/decisions.md` まで追加している点である。[brief scope:75](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md:75)、[plan files:66](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:66)。issuer の二 workload test まで閉じるなら issuer test file も必要になる。これは段 4 で scope 拡張として裁定へ返す面である。

  成果物影響: scope を明示更新せず進むと、issuer workload identity の受入確認が欠けるか、未所有 file の競合で台帳・参照が失われる。

- `real 候補` — `docs/decisions.md` EOF への直接追記案は入口規律違反であり、spool fragment にしなければならない。[plan:75](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:75)、[CLAUDE.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/CLAUDE.md:46)

  成果物影響: 直接追記すると並行 land の D 採番・参照を競合させ、decision 参照が変わる。

- `refuted 候補` — acceptance duration ledger の更新自体は、新設台帳でも一般化でもなく、node 改名・追加に伴う既存 consumer 更新なので、実装を行う場合は scope 膨張ではない。[plan:308](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:308)

  成果物影響: 更新しないと旧 nodeid と新 nodeid の所要参照が食い違う。

- `real 候補` — env_tag/clocks の mock verifier ケース追加は単に不要である。production では先行 verifier が拒否し、plan 自身も単独変異の証拠に数えないとしている。[plan binder comment:191](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md:191)、[verifier:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py:121)

  成果物影響: 足しても production の値・受理集合・参照は変わらず、node と ledger 競合だけを増やす。

- `real 候補` — issuer docstring の `workloads` 文言訂正は、γ を実装するなら偽記述を残さないための real な追従だが、brief 外の 3 file 目であり裁定対象である。一方、行番号 pin の近代化そのものは成果物へ影響せず、単に不要な cleanup である。[current docstring:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:746)

  成果物影響: workload 文言を放置すると参照説明だけが偽になる。行番号変更の有無では成果物値・受理集合は変わらない。

- `real 候補` — 閉じるために必要なのに不足している面は、v4 用 HMAC golden 2 箇所、schema revert mutation の完全失敗 3 node、二 workload issuer 正例、ledger の stale node 方針の明記である。[golden:1325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/tests/test_floor_pair_driver.py:1325)、[DW-M08 complete set:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/mutation.md:55)

  成果物影響: 不足を残すと plan hash/order の赤、issuer workload identity の未検出回帰、mutation 台帳の期待 node 不一致が残る。

- `real 候補` — brief は DW-S01 の 10〜30 行契約に対し 108 行である。[brief:1](/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md:1)、[DW-S01:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/docs/dev-wave/core.md:41)。これは procedural な実在違反だが、今回の実装 scope へ追加コードを生む理由にはしない。

  成果物影響: 直接の floor 値・受理集合は変えないため、DW-G05 上は実装 must-fix ではない。

## 総括

plan はこのまま段 5 へ進めない。

主要理由は 3 点である。

1. v4 bump が既存 HMAC 順序 golden を確実に変えるのに、plan が「変わらない」として閉包から落としている。
2. 実 checkout には tracked spec、tracked receipt、binary がなく、この変更後も floor artifact を構成できない。DW-G04 は fixture を発火 artifact と認めないため、現時点では設計メモ止まりが支持される。
3. driver node は `210 -> 213` で正しいが、issuer source は 24 node、ledger は 26 nodeである。`22158` は stale 2 件を残す増分 map countであり、exact current 集合なら `22156` である。

pytest、calibrator、floor 発行、Pegasus 測定は実行していない。編集・commit も行っていない。