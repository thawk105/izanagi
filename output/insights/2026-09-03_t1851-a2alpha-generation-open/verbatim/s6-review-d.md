## 所見

1. [実測] blocker — M6 は受理集合を変える kill にならない。`_publish_registry_generation_create_only()` の早期拒否を消しても、既存 path は `_publish_create_only()` が再度拒否する。名指し test は診断文の違いでだけ赤になる。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1057-1091,984-1012`; `orchestrator/tests/test_s8b_attempt_registry.py:2583-2595`。  
放置影響: 材料レポートが単層防壁を KILLED と誤認証し、既存世代の再発行に対する実効防壁の所在を誤記する。

2. [実測] blocker — M7b を kill する nodeid は存在しない。publisher test の symlink は空 directory を指すため、symlink 四層を消しても `not path.is_file()` による「不完全世代」拒否が残って緑になる。`test_unchecked_generation_symlink...` は enumerator を test 内で stub 化して二重計上を観察するだけで、登録された publisher 四層変異を赤にしない。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1057-1077`; `orchestrator/tests/test_s8b_attempt_registry.py:2104-2165,2519-2537`。  
放置影響: symlink alias による横断予算の二重計上可能性を検査せず KILLED と報告し、試行台帳の受理可能 attempt 数を誤認証する。

3. [実測] blocker — M13 も実効 kill ではない。marker 必須の早期拒否を消しても、同じ経路の `assert consumption_marker is not None` が先に落ちる。名指し test は例外型・診断の違いで赤になるだけで、marker なし予約は引き続き fail-closed である。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1697-1705,1766-1786`; `orchestrator/tests/test_s8b_attempt_registry.py:2614-2620`。  
放置影響: 材料レポートの M13 結果が KILLED と誤記され、実際には残っている下流拒否層が不可視になる。

4. [実測] blocker — v2 capability はすべての mutation を囲んでいない。reserve と observation は `marker.use()` 経路だが、classification claim/row と recovery row は通常の `_atomic_update()` を使う。さらに start-only resume は marker を lock 内で検証後、lock 外で `classify_attempt()` を呼ぶため再検証との間に窓がある。根拠: `orchestrator/campaign/s8b_attempt_registry.py:1766-1787,2065-2072,2213-2227,2456-2462,2547-2650,2858-2869`; marker の契約は `orchestrator/campaign/s8b_holdout_admission.py:339-348,5219-5227`。  
放置影響: reserve 後に失効・改変された durable authority でも classification claim・receipt・recovery row を試行台帳へ追加でき、台帳値と後続参照の受理集合が広がる。

5. [実測] must-fix — M8 の test は「measurement だけ異なる二 claim」を作っていない。helper が measurement ordinal を含む identity から `schedule_row_sha256` も作り直すため、measurement field を address から除いても二 payload は schedule-row digest で異なる。現在の変異は key 直接 assertion で赤になるが、裁定が求めた create-only path 衝突は証明していない。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:109-128,2706-2723`; codec は同じ digest を持つ別 ordinal を許す `orchestrator/campaign/s8b_attempt_profile.py:180-209`。  
放置影響: measurement axis を claim address から外す別実装形を見逃し、二試行の classification claim 参照が衝突し得る。

6. [実測] nit — `test_v2_profile_is_rejected_by_public_mutation_but_slot_lookup_is_five_axis` は有効な v2 ではなく validator を除いた forged v2 の拒否を検査しており、名前と実態が一致しない。有効 v2 の正例は次の別 test にある。公開 create/read の型 annotation もなお v1 slot/profile 限定である。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:2410-2465`; `orchestrator/campaign/s8b_attempt_registry.py:1582-1589,1628-1634`。  
放置影響: runtime の台帳値は変わらないが、静的 consumer と材料レポートが v2 の公開受理面を誤読する。

7. [実測] nit — 規模は 1,329 changed LOC で、裁定上限 1,030 を299行超えた。production は710行、test は619行なので、上限超過299行は算術上 test 側の320行超過で説明できる。新設は9 test nodeだけで、direct replay、実 admission fixture、publisher、v2 lifecycle を巨大な複合 node にまとめている。根拠: `orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2219-2427`; `orchestrator/tests/test_s8b_attempt_registry.py:243-313,2449-2758`。  
放置影響: 成果物の受理集合を直接変えないが、材料レポート上の変異帰属が mask されやすくなる。

## 16 変異の静的判定

| ID | 判定 | kill / survivor の根拠 |
|---|---|---|
| M1 | KILLED 可 | `orchestrator/tests/test_s8b_attempt_registry.py::test_v2_profile_opens_generation_create_and_read` (`:2449`)。v1 factory 固定なら create の `_assert_profile` で赤。 |
| M2 | KILLED 可 | `...::test_v2_profile_exact_gate_rejects_both_new_field_mutations` (`:2468`)。validator identity 比較以外の拒否層なし。 |
| M3 | KILLED 可 | 同 node (`:2478-2490`)。policy field 比較以外の拒否層なし。 |
| M4a | SURVIVED、登録どおり | adapter 拒否を消しても core validator `attempt_registry_core.py:1326-1327` が同じ入力を拒否する。 |
| M4b | KILLED 可 | `test_attempt_registry_core_s8b_profile.py::test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` (`:2251-2297`)。core replay が terminal を受理して `pytest.raises` が失敗する。 |
| M5 | KILLED 可 | `test_s8b_attempt_registry.py::test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` (`:2598`)。classify 時の handle path 再照合が1段 pathになり赤。 |
| M6 | kill 不可 | 名指し publisher node (`:2508`) は下層拒否の診断差でのみ赤。実効上は SURVIVED。 |
| M7a | SURVIVED、登録どおり | parent symlink 検査単層を消しても複数拒否が残る。 |
| M7b | kill 不可 | 有効な nodeidなし。publisher node は不完全世代拒否で mask、unchecked node は別の enumerator 変異。 |
| M8 | KILLED 可、ただし弱い | `...::test_v3_claim_address_separates_measurement_ordinals` (`:2706`) は field 欠落で赤。ただし path 衝突の単一理由性は未証明。 |
| M9 | KILLED 可 | v2 lifecycle node (`:2659-2670`)。protocol tamper を受理するようになり期待拒否が消える。 |
| M10a | SURVIVED、登録どおり | `marker.use` と durable identity 再導出の lock 検査が残る (`s8b_holdout_admission.py:5009,5172`)。 |
| M10b | KILLED 可、条件付き | v2 lifecycle node (`:2622-2639`) と `test_s8b_holdout_admission.py::test_floor_marker_capability_requires_live_caller_held_lock` (`:2491`)。M10b が admission 側の両 call site も消す定義なら赤。 |
| M11 | KILLED 可 | v2 lifecycle nodeの正常 resume (`:2673-2681`)。legacy marker reader へ戻すと正例が拒否される。 |
| M12 | KILLED 可 | `...::test_locked_update_seam_does_not_reacquire_lock_or_run_prelock_hook` (`:2372`)。hook を locked 関数へ移すと `snapshots == []` が破れる。rendezvous node (`:1666`) も赤になる。 |
| M13 | kill 不可 | marker 必須検査削除後も `assert` で拒否される。名指し node の赤は診断・例外型だけ。 |

## 過剰拒否の正例

| 正例 | 判定 | 実在 node |
|---|---|---|
| P1 | 実在 | `test_s8b_attempt_registry.py::test_resume_start_and_seal_without_old_handle_reaches_terminal` (`:1309`)。1段 v1 rootで start/resume/classify/observe/terminal を通す。 |
| P2 | 実在 | `...::test_resume_classification_and_incomplete_reader_add_no_rows` (`:1260`) および既存 v1 lifecycle。reserve/resume は default `consumption_marker=None`、observation は legacy marker を読む。 |
| P3 | 実在 | `...::test_v2_marker_claim_v3_resume_and_legacy_terminal_fail_closed` (`:2598`)。実 admission capability による create/reserve/claim v3/resume 正例。 |
| P4 | 実在 | `...::test_canonical_v1_lifecycle_ignores_non_generation_sibling` (`:1970`)。非64 hex siblingを無視して列挙・mutationを通す。 |
| P5 | 実在 | `test_attempt_registry_core_s8b_profile.py::test_terminal_validator_direct_replay_and_producer_mapping_keep_v1_positive` (`:2251`) と adapter 正例 `test_s8b_attempt_registry.py:2726`。 |

## テスト弱体化

[実測] `git show 69497db66 -- orchestrator/tests/` の削除は、`typing.Any` import の置換と、旧「正規 v2 を拒否」入力を forged v2 へ変えた2箇所だけである。skip・xfail・test 削除・期待緩和はない。後者は E3 の受理集合変更に必要で、別の正規 v2 正例も追加されている。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:20,2410-2465`。

[実測] working-tree hash、現在時刻、絶対 workspace path、行番号を期待 payload に焼き込んだ追加はない。固定時刻・固定 digest と `tmp_path` のみである。現行 hash を fixture へ差し込んだ箇所もない。根拠: `orchestrator/tests/test_s8b_attempt_registry.py:243-313,2598-2723`。

[実測] D1522 の直接検査と正例対照は terminal、publisher、lock に存在する。ただし M6・M7b・M13 は残存層による mask、M8 は相関 fixture という弱体点がある。根拠: `test_attempt_registry_core_s8b_profile.py:2251-2380`; `test_s8b_attempt_registry.py:2508-2758`。

## consumer 波及

[実測] production constructor は v1 factory、v2 factory、S8C の3組だけである。S8C は新 field を省略しており、`terminal_row_validator=None`、`retryable_terminal_opens_next_attempt=True` になる。core の追加分岐はそれぞれ no-op と従来許可なので、S8C の terminal・retry 挙動は静的に不変である。根拠: `orchestrator/campaign/trial_registry.py:2113-2164`; `orchestrator/campaign/attempt_registry_core.py:1136-1140,1326-1327`。

[実測] private `_load_registry_bytes` の直接 consumer は `trial_registry.py:2342-2352` に残る。S8C profile が上記 default を使うため replay の受理集合は不変である。

[実測] holdout admission の full replay は v1 factoryを作って core loaderへ渡すため、新 validatorは発火しない。marker/lock consumer は adapter の marker-owned reserve/observe から参照されるが、classification/recovery の未接続が所見4の blockerである。根拠: `orchestrator/campaign/s8b_holdout_admission.py:5602-5622,5004-5227`; `orchestrator/campaign/s8b_attempt_registry.py:1770,2065,2213,2456`。

[実測] scheduler accounting は渡された profileで core replayする。v1は不変、v2 terminal拒否は新しい意図どおりである。根拠: `orchestrator/campaign/s8b_scheduler_accounting.py:319-341`。

[実測] launcher の reservation は4軸 slotで markerを渡さず、現行 v1 callerとして default `None` を使う。したがって text変更なしの経路は静的に不変だが、v2 production handoffは引き続き存在しない。根拠: `orchestrator/campaign/s8b_floor_attempt_launcher.py:53-69,444-469`。

[実測] `_assert_consumed_marker` の旧名は production/test 全体に残存0件。新名の call site は observation と resume の2件である。根拠: `orchestrator/campaign/s8b_attempt_registry.py:2089,2176,2845`。

## 新規 test file と規模

[実測] 変更は既存5 fileだけで、新規 test fileはない。したがって `test_plain_runner_coverage.py` の file集合 meta-test更新は不要である。根拠: `orchestrator/tests/test_plain_runner_coverage.py:44-93`。

[実測] commit stat は5 files、`+1,239 / -90`、changed LOC 1,329。裁定見積り740〜1,030に対して299行超過した。内訳は production 710 changed、test 619 changedであり、超過は主として9個の大型複合 test、実 admission fixture転用、direct lower-layer対照から来ている。

## 総括

- blocker:

  - M6 は診断差だけで赤になり、実効 kill ではない。
  - M7b を kill する nodeid がない。
  - M13 は下流 `assert` に mask され、実効 kill ではない。
  - v2 classification/recovery が marker capability の再検証を迂回する。

- 16変異:

  - kill nodeを名指しできた: M1、M2、M3、M4b、M5、M8、M9、M10b、M11、M12。
  - 意図どおり SURVIVED: M4a、M7a、M10a。
  - 有効な kill nodeなし: M6、M7b、M13。

- 事前登録の修正提案:

  - M6: 単層を `SURVIVED` に変更し、generation早期拒否・`_publish_create_only` の事前拒否・link race拒否を同時に消す M6b を `KILLED` として追加する。
  - M7b: 現定義は `SURVIVED` へ変更する。`KILLED` を維持するなら、空 target ではなく完全 targetまたは mkdir 後の symlink swap を作り、不完全世代・existing destination・enumerator の maskも変異定義へ明記する。
  - M13: 早期 guard単層を `SURVIVED` に変更する。markerなしを通常 `_atomic_update` へ流して start rowが実際に追加される combined mutationを別途 `KILLED` とする。
  - M8: 期待は `KILLED` のままでよいが、二 slot の `schedule_row_sha256` を同値に固定する。

- 過剰拒否正例: P1〜P5はいずれも実在する。

- テスト弱体化: skip・xfail・削除・揮発 hash挿入はない。ただし M6/M7b/M13 の mask、M8 の相関 fixture、大型複合 nodeへの集中がある。

- consumer 波及: S8C、v1 holdout replay、scheduler v1、launcher v1 は defaultにより静的不変。v2 marker-owned mutation closureだけが未完。

- 読めなかった資料: なし。指定4資料を順番どおり全文読了した。

- 確かめられなかった事実: pytest実結果、mutation matrix実走結果、487-node consumer全走、受入全走。いずれも緑として数えていない。