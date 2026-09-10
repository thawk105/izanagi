## 所見

1. [実測] blocker — E1 の raw-fact carrier が閉じていない。plan の5入力には pre-probe と post-open `open_error` がない。sealed schema は `probe_before` / `probe_after` を持ち、現行 campaign は pre-probe competition と `measure_error` を terminal reason に使う一方、launcher が保持するのは post-probe と `OpenedFloorAttempt.open_error` である。根拠: `s2-plan.md:71-84,93-103`; `orchestrator/campaign/s8b_ratified_freeze.py:262-269`; `orchestrator/campaign/s8b_floor_campaign.py:6077-6103,6147-6153`; `orchestrator/campaign/s8b_floor_attempt_launcher.py:114-123,589-626`; `orchestrator/tests/test_s8b_floor_attempt_launcher.py:362-421`。  
成果物影響: open failure / pre-probe competition が partial・observedへ誤分類されるか正当な sealed record が拒否され、試行台帳の status/reason/primary value と将来の certified 候補集合が変わる。

2. [実測] blocker — B1 marker capability を v2 reserve へ渡す production handoff がない。plan は `reserve_attempt_slot(..., consumption_marker=None)` を追加しつつ launcher caller は「既存 v1 なので変更0」とするが、`FloorAttemptReservation` に marker field がなく `_reserve()` も渡していない。根拠: `s2-plan.md:177-180,228`; `orchestrator/campaign/s8b_floor_attempt_launcher.py:53-69,444-469`; `orchestrator/campaign/s8b_holdout_admission.py:322-368`。  
成果物影響: v2 reserve は常に marker 不在で拒否され、generation 台帳に start/terminal が生まれず、材料レポートと certified 選択の参照先も生まれない。

3. [実測] blocker — `_entry_paths()` の call site を1件数え落としている。plan は create/read/reserve/resume の4件と後続 handle path を挙げるが、全 handle 使用時に走る `_assert_state_path()` の `:522` が残る。ここは protocol を渡さず1段 v1 pathを再計算する。根拠: `s2-plan.md:186`; `orchestrator/campaign/s8b_attempt_registry.py:277-313,516-526`。  
成果物影響: v2 handle は予約後の classify/observe/terminal 入口で path 不一致となり、terminal row が書けない。

4. [実測] must-fix — A2α の「既存 test green は未裁定」という判定は誤り。E2 active 化は brief と前 wave handoff が既に明示しており、空集合 pin は A1' の未完成状態を固定した test である。根拠: `brief.md:16-17`; 前 wave `README.md:67-76,87-88`; `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2172-2216`; `s2-plan.md:38-40,265`。  
成果物影響: 不要な裁定待ちで空集合を残すと v2 retryable terminal の受理集合が開かず、再測定台帳が生成されない。

5. [実測] must-fix — M6 の「profile gate 以外は止めない」は、前 waveで固定した `v2 slot.attempt_ordinal == 0` 境界と矛盾する。根拠: `s2-plan.md:206`; 前 wave `verbatim/s2-plan.md:429,451,473`; core の次 ordinal 経路 `orchestrator/campaign/attempt_registry_core.py:1106-1144`。  
成果物影響: 正しい adapter guardを実装すれば M6片側は SURVIVED になり、実装しなければ未承認 recovery ordinal が台帳予算・試行列へ入る。

6. [実測] must-fix — M8 は二層ではなく少なくとも四層で過剰決定される。`_read_regular_bytes()` のほか、`_ensure_durable_directory()`、`_write_staging()`、admission の guarded writer が parent component を再検査する。create-only の既存 destination 拒否も残る。根拠: `s2-plan.md:209-210,216`; `orchestrator/campaign/s8b_attempt_registry.py:531-547,836-888,891-968`; `orchestrator/campaign/s8b_holdout_admission.py:1272-1295,1298-1343`。  
成果物影響: 現行 M8b は構造的に SURVIVED し得るため、symlink 防壁を誤って「KILLED」と認証し、台帳 write-path の保証を誤記する。

7. [推測] must-fix — M3 も片側 KILLED には固定できない。core validator が sealed record bytes と `raw_output_sha256` を再照合するなら producer equality 除去は SURVIVED、照合しないなら historical replay の binding が欠ける。さらに KILLED 予定の M1b〜M12 に具体的 test nodeid が割り当てられていない。根拠: `s2-plan.md:71-74,125-127,198-214`; 現行 digest-only state `orchestrator/campaign/s8b_attempt_registry.py:1798-1804`。  
成果物影響: mutation 緑が terminal bytes・claim・marker の実効受理集合を証明せず、誤った試行台帳を正当化し得る。

8. [推測] must-fix — changed LOC / 新設 node は引き続き上振れ方向。plan は parametrize 展開を正しく直したが、raw carrier の pre-probe/open-error、marker handoff、未列挙 handle pathを含まない。また「3 symbol の hard-coded 参照29行」は実コード上26 occurrenceで、literal countだけでは11件の `_entry_paths()` consumerを表せない。根拠: `s2-plan.md:13-21`; `orchestrator/campaign/s8b_attempt_registry.py:122,167,171,319,459,975-976,1020-1114,1335-1499,1753,1886,2057-2060` および `_entry_paths()` calls `:508,522,1346,1378,1428,1583,1808,1922,1973,2027,2115`。  
成果物影響: stage 5 実装中に境界追加が発生し、carrierまたはv2 consumerが欠けた不完全 checkpointになりやすい。

9. [実測] must-fix — 親 brief のアンカー表と規模表は現 tree と一致しない。主な誤りは次のとおり。

   - production 成果物3 fileの列挙から、必須変更先 `s8b_floor_attempt_launcher.py` が欠落している。`brief.md:49-53` 対 `s8b_floor_attempt_launcher.py:114-142,429-469,589-644`。
   - core terminal producer の実体は `attempt_registry_core.py:1877-1960` で、brief の `:1814-1897` は途中までしか覆わない。`brief.md:88`。
   - adapter terminal は `s8b_attempt_registry.py:1908-2010` で、brief の `:1512-1713` は classification/claim blockである。`brief.md:89`。
   - launcher anchor は terminal carrier/call `:114-142,614-644` を落とし、現物にない `_terminal_*` を挙げる。`brief.md:90`。
   - E4 anchor は claim 前半 `:1017-1108` と resume 本体 `:2072-2367` を落とす。`brief.md:96`。
   - test 数 `50/78 + 35/59 + 9/16 = 153` と consumer 172 は A1' 前の値で、現 tree は三file 176、launcher込み188、consumer union 487。`brief.md:97`; 各 test の parametrize は `test_attempt_registry_core_s8b_profile.py:400-432,603-621,1792-1849,2066-2160`, `test_s8b_attempt_registry.py:423-424,677-934,1329-1330,1902-1906`, `test_attempt_registry_core_equivalence.py:497-569`, `test_s8b_floor_attempt_launcher.py:234-268,600-609`。

成果物影響: 誤アンカーに従うと sealed terminal と launcher consumer が変更漏れになり、v2 台帳の値・参照が最終成果物へ到達しない。

10. [実測] nit — plan は新規 test fileを作るか既存2 fileへ追記するかを固定していない。新規 fileなら全 `test_*.py` を列挙する meta-test が存在し、焦点走に3 nodeを追加する必要がある。根拠: `orchestrator/tests/test_plain_runner_coverage.py:44-93`; `s2-plan.md:253`。  
成果物影響: certified 値は直接変わらないが、新規 test が実行されない偽緑または allowlist 赤を招く。

## 総括

- blocker の一覧

  - E1 evidence carrier に pre-probe / open-error がない。
  - B1 marker capability を launcher→adapterへ渡す境界がない。
  - `_assert_state_path()` 内の `_entry_paths()` call site `s8b_attempt_registry.py:522` が未計画。

- [実測] 静的に数え直した既存 node

  | 群 | 既存回帰 node |
  |---|---:|
  | E1 | 430 |
  | E2 | 176 |
  | E3 | 419 |
  | E4 | 143 |
  | union | 487 |

  4重点 file は `86 + 74 + 16 + 12 = 188 node`。trial 225、holdout関連72、scheduler 1、campaign helper 1を含む union が487である。`s2-plan.md:3-9`; launcher parametrize `test_s8b_floor_attempt_launcher.py:234-268,600-609`。

- [推測] changed LOC / 新設 node の再見積り

  | 群 | changed LOC | 新設 node |
  |---|---:|---:|
  | E1 | 540–780 | 48–64 |
  | E2 | 25–45 | 10–14 |
  | E3 | 170–260 | 20–28 |
  | E4 | 720–1,020 | 42–58 |
  | 重複除去後 union | 1,380–1,900 | 110–145 |

  上振れ要因は parametrize ではなく、pre-probe/open-error carrier、marker capability handoff、v1/v2 handle path、複数 symlink barrierである。

- [推測] 1 wave には収まらない。親の800–1,000 LOC見積りが前 wave同様約2倍へ外れると1,600–2,000 LOCとなり、stage 5の実装子で破綻する。分割は逐次 A2α=`E1+E2+完全な evidence carrier`、A2β=`E3+E4` が妥当だが、A2α→A2β の境界 signature は pre-probe/open-error と marker handoffを固定するまで未完成。並列分割は不可。

- [実測] 数え落とされていた call site

  - `orchestrator/campaign/s8b_attempt_registry.py:522` — `_assert_state_path()` の v1 path再計算。
  - `orchestrator/campaign/s8b_floor_attempt_launcher.py:454-469` は件数には入っているが、「変更0」は誤り。v2では marker capabilityを渡す変更が必要。
  - markerを `FloorAttemptReservation` に保持する設計なら test constructor `test_s8b_floor_attempt_launcher.py:193,546` も consumerになる。

- [推測] 変異事前登録の修正提案

  - M3を M3a=`producer equalityのみ` SURVIVED、M3b=`producer + core digest/record binding` KILLED の対にする。
  - M6を M6a=`profile exact比較のみ` SURVIVED、M6b=`profile比較 + v2 attempt_ordinal=0 adapter guard` KILLED の対にする。
  - M8を `_read_regular_bytes`、`_ensure_durable_directory`、guarded writer、create-only既存先の全拒否層を列挙した多層変異へ組み直す。
  - KILLED nodeを少なくとも `test_replay_rejects_rechained_sealed_terminal_projection_tamper`、`test_sealed_terminal_binds_exact_session_line_to_raw_output_digest`、`test_v2_reserve_rejects_unproved_recovery_ordinal`、`test_generation_publish_rejects_complete_parent_symlink`、`test_v3_claim_rejects_protocol_identity_tamper`、`test_v3_claim_address_separates_measurement_ordinals`、`test_v2_resume_requires_current_generation_marker` として名指しする。
  - M1a/M1b、M2、M4、M5、M7a/M7b、M9–M12も mutation specへ exact nodeidを登録する。

- [実測] 親 brief の誤り一覧

  - production file列挙から launcherが欠落。
  - 800–1,000 LOC と1実装子判定が過小。
  - E1 core / adapter / launcher anchorが不完全または別block。
  - E4 claim / resume anchorが不完全。
  - test 153 node / consumer 172 nodeが古い。
  - P1-c の raw/sealed 両立形が固定8 signatureでは運べない。
  - P1-d の5入力は repetition evidenceが未到達で、pre-probe/open-errorも閉じていない。
  - `FROZEN_MANIFEST` 23件、E2 null matrix、E3の5 direct call siteについては誤りを見つけなかった。根拠: `test_frozen_artifacts.py:41-117`; `attempt_registry_core.py:934-984`; `s8b_attempt_registry.py:519,1343,1376,1410,2082`。

- [推測] provisional 裁定

  - (P1-a) refuted。
  - (P1-b) real。ただし4 semantic causeとの厳密な1対1対応をtestで固定すること。
  - (P1-c) refuted as written。二重導出自体は可能だが、現8 signatureでは raw factsを運べない。
  - (P1-d) refuted。
  - (P1-e) real as post-implementation acceptance。新規性能測定は不要。

- 読めなかった資料・確かめられなかった事実

  - 指定された4資料はすべて全文読了し、別 worktree・親 repoは読んでいない。
  - pytest、collection、mutation harnessは実行していない。
  - 親が repo外 probeで得たというE3の実行結果、live Pegasus上の具体的入力値は独立確認していない。
  - 実装後の確定 changed LOC / node数は未確定で、上記は静的見積りである。