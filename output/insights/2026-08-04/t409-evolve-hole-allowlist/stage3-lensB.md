結論から言うと、現プランは採用不可である。driver 単位の配線に留まり、D127 が禁じた materializer 迂回を再現している。以下は静的検査のみで、実装・編集・テスト実行はしていない。

### 1. consumer 閉包が成立していない

- 判定: **real — must-fix**
- 根拠:
  - プランが gate を置くのは trigger driver、autonomous driver、S8A sweep、S1 direct の各 wrapper である（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:128-155`）。
  - autonomous driver は実際には trigger driver の materialization を再利用している（`orchestrator/campaign/p3_autonomous_workload_trial.py:1224-1233`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1430-1462`）。
  - S8A sweep は独自に template を適用し build する（`orchestrator/campaign/s8a_trigger_sweep.py:410-480`）。S1 direct も同様である（`orchestrator/campaign/s1_direct_comparison.py:485-561`）。
  - しかし extime calibration には、trigger template を適用し、汎用 `p3_s4_loop.quarantine()` を経て buildcache に渡す別 materializer がある。プランに列挙されていない（`orchestrator/campaign/s1_verify_extime_calibration.py:329-357`）。
  - 汎用 materializer `p3_s4_loop.quarantine()` は任意の `implementation` を受け、DiffQuarantine 後に C++ へ書き込む（`orchestrator/campaign/p3_s4_loop.py:182-219`）。DiffQuarantine は構造・変更範囲・byte 制約であり、trigger 文法は検査しない（`orchestrator/campaign/diff_quarantine.py:437-497`）。
  - `patchharness` も任意 patch を適用でき、trigger recognizer を通らない（`orchestrator/campaign/patchharness.py:192-200`, `orchestrator/campaign/patchharness.py:234-251`）。
  - その先の `pipeline.evaluate()` は SourceEvidence/admission を検証するが、trigger 文法は検査しない（`orchestrator/campaign/pipeline.py:435-452`, `orchestrator/campaign/pipeline.py:572-610`, `orchestrator/campaign/pipeline.py:645-695`）。
  - `loop.run_campaign()` も同じく language admission を要求せず evaluate へ進む（`orchestrator/campaign/loop.py:96-113`, `orchestrator/campaign/loop.py:223-237`）。
  - `buildcache.build()` と `build_v2()` の admission は provenance と path allowlist であり、C++ 内容の trigger 文法ではない（`orchestrator/campaign/buildcache.py:562-643`, `orchestrator/campaign/buildcache.py:790-815`; `orchestrator/campaign/source_digest.py:73-82`, `orchestrator/campaign/source_digest.py:824-875`）。
  - D127 はまさに「driver の `run_one_iteration()` 内だけでは pipeline、sweep、screening、手動 patch が素通しになる」ため admission を materializer 側へ置くと裁定した（`docs/decisions.md:6247-6250`）。
  - 静的に構成できる迂回例は、trigger template に文法外の実装を手動適用し、汎用 `p3_s4_loop.quarantine()` → `loop.run_campaign()`／`pipeline.evaluate()` → buildcache と渡す経路である。正規の coder authority を持つ入力なら、現行 build admission は trigger 文法違反を識別できない。なお same-process issuer の真正性自体も未閉鎖と明記されている（`docs/decisions.md:6650-6654`）。
  - 固定値を使う characterization materializer も存在する（`orchestrator/campaign/s8a_trigger_freq.py:141-149`, `orchestrator/campaign/s8a_trigger_coverage.py:106-162`, `orchestrator/campaign/s8a_trigger_coverage.py:248-264`）。これは信頼済み固定入力として除外可能だが、閉包台帳には分類が必要である。
  - 手動・shell materialization が registry の保護外であることは現行 admission 自身も明記している（`orchestrator/campaign/materializer_admission.py:2-13`）。
- 成果物影響: 文法外 implementation が certified 選択・材料レポート・台帳へ到達できるため、「新 gate 済み」という certification が偽になる。
- scope: **scope 内**。少なくとも trigger marker を書く汎用 materializer と build 境界で再検査または封印済み admission receipt を必須化し、全 caller を閉包検査すべきである。

### 2. cache と replay は新しい language policy を認識しない

- 判定: **real — must-fix**
- 根拠:
  - D127 当時は admission が cache preimage に入らない穴が明記されていた（`docs/decisions.md:6258-6261`）。
  - ただし、その前提は現行全体には古い。D136 が provenance-class admission を legacy/v2 cache、campaign、replay に組み込んでいる（`docs/decisions.md:6590-6596`, `docs/decisions.md:6610-6630`, `docs/decisions.md:6656-6659`）。
  - 現行 legacy cache key は admission receipt を含み、v2 preimage も admission を含む（`orchestrator/campaign/buildcache.py:130-148`, `orchestrator/campaign/buildcache.py:246-266`）。cache hit 時にも sidecar/manifest admission を検査する（`orchestrator/campaign/buildcache.py:377-417`, `orchestrator/campaign/buildcache.py:667-686`, `orchestrator/campaign/buildcache.py:838-844`）。
  - しかし BuildAdmissionPolicy の識別対象は schema、repo pin、coder authority、generator/review registry 等で、trigger 文法または文法 version は含まれない（`orchestrator/campaign/build_admission.py:281-289`）。
  - SourceEvidence は source bytes を hash するが、「どの trigger 文法で合格したか」は記録しない（`orchestrator/campaign/source_digest.py:99-120`, `orchestrator/campaign/source_digest.py:149-160`）。
  - campaign identity も BuildAdmissionPolicy だけを束縛し、新 gate policy を含まない（`orchestrator/campaign/ident.py:28-44`, `orchestrator/campaign/ident.py:125-144`）。
  - WAL replay の検査対象も admission の canonicality/policy で、trigger 文法 version はない（`orchestrator/campaign/wal.py:606-644`, `orchestrator/campaign/wal.py:716-747`）。
  - `loop.run_campaign()` は terminal 状態なら evaluate 前に skip する（`orchestrator/campaign/loop.py:152-220`）。screening resume も同様である（`orchestrator/campaign/screening_driver.py:134-178`）。
  - プランは reject の `reason_code` は規定するが、合格側の grammar version/hash、cache migration、WAL migration を規定していない（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:181-194`）。
  - したがって、pre-D136 artifact は既に D136 により cold/deny の対象だが、D136 導入後かつ新 gate 導入前の同一 source/cache/WAL は、新 gate policy が identity に入らないため別問題として残る。
  - S8B floor resume も保存済み manifest/binary を source-language 再検査なしで読む（`orchestrator/campaign/s8b_floor_campaign.py:3004-3072`）。その resume が admission receipt に束縛されない点はファイル冒頭にも明記されている（`orchestrator/campaign/s8b_floor_campaign.py:41-48`）。
- 成果物影響: gate 導入前に受理された文法外 source の binary/result が cache hit または terminal replay で再利用され、材料レポートと台帳に新 gate 合格相当として混入しうる。
- scope: cache/WAL identity と合格 receipt は **scope 内**。既存 cache・WAL・S8B resume を cold invalidate、再検査、overlay のどれで移行するかは **裁定パッケージ行き**。

### 3. D96 との手続き的衝突

- 判定: **refuted**
- 根拠:
  - D96 は受理集合を変える変更に新 D と境界テストを同一変更単位で要求している（`docs/decisions.md:4269-4279`）。
  - プランには新 D の骨子と、positive/negative/boundary テスト行列がある（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:157-194`, `/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:214-230`）。
  - D96 の「機械検査は新設しない」は consumer 閉包を一般 AST 検査で強制する案についての判断で、個別 domain recognizer の恒久禁止ではない（`docs/decisions.md:4281-4292`）。
- 成果物影響: D96 だけを理由に変更を拒否する必要はない。ただし新 D の内容不足は別所見のとおり残る。
- scope: **scope 内・手続きは満たせる**。

### 4. 「既存契約を狭めない」は偽

- 判定: **real — must-fix**
- 根拠:
  - 親 brief は新 gate が既存 producer contract を狭めないと主張する（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/s1-brief.md:19-20`）。
  - D48 は enum と compile-time constants を許している（`docs/decisions.md:1749-1753`）。
  - 現行 role も compile-time literals を明示的に許し、要求は一行・副作用なしである（`.claude/agents/coder-v4-autonomous-trigger-gating.md:82-109`）。
  - 現行 machine gate は五つの identifier blacklist のみである（`orchestrator/campaign/p3_s4_loop_trigger_gating.py:112-139`）。parser も物理一行性しか見ない（`orchestrator/campaign/p3_autonomous_workload_trial.py:324-347`）。
  - 新文法は `true`、`false`、enum、論理・比較演算子だけを許し、数字を lexical rejection する（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:55-91`, `/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:105-124`）。
  - したがって `izanagi_gate_pass = 1;` や `izanagi_gate_pass = (1 == 1);` は、現行 role の literal 契約、一行、副作用なし、五識別子非使用を満たす一方、新 gate では拒否される。意味関数の表現能力が残っても、producer が許される表現集合は狭まる。
- 成果物影響: 新 D が「単なる機械化」と記録すると、実際には producer 契約を変更して得た certified 集合を旧契約と同一と誤記する。
- scope: **scope 内かつ裁定パッケージ行き**。数字等も文法に入れるか、D48/D51 を明示的に改訂して表現契約を狭めるかの択一が必要である。

### 5. D48 は機械執行を永久に auditor 目視へ限定したか

- 判定: **refuted**
- 根拠:
  - D48 当初は auditor 目視を執行に割り当てていた（`docs/decisions.md:1770-1772`）。
  - しかし D51 は五識別子 blacklist を machine hard gate とし、auditor をその上位集合とする構成を明示的に採用している（`docs/decisions.md:1947-1955`）。
  - D49 も安全側の穴を狭める変更について Stage B への全面差し戻しを不要としている（`docs/decisions.md:1815-1819`）。D48 が Stage B 返却を明示しているのは member-read の拡張時である（`docs/decisions.md:1751-1753`）。
- 成果物影響: 新 recognizer 自体を「D48 違反」として廃棄する必要はない。ただし literal 契約変更と enforcement allocation の上書きは新 D に明記する必要がある。
- scope: **scope 内**。新 D で足り、Stage B 全面差し戻しは不要。

### 6. 「LLM synthesisability を維持」は過大主張

- 判定: **real — must-fix**
- 根拠:
  - trigger axis の実験 domain は五つの gateable reasons、すなわち高々 `2^5` の有限選択である（`orchestrator/campaign/axis_trigger_gating.py:45-51`）。
  - D50 の実測では有効自由度は三 bit で、`2^3` と controls を列挙している（`docs/decisions.md:1863-1872`）。
  - D48 は意図的に「偵察空間＝coder 変異空間」とした（`docs/decisions.md:1749-1753`）。
  - 新文法が全 enum 値を含むため構文上は `2^7` の真理値関数を表現できる、という記述は数学的には成立する（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:93-103`）。しかし測定上同値な policy が多数あり、探索は有限 allowlist 上の選択・論理合成である。
  - プランの「arbitrary Boolean synthesis autonomy は維持される」という回答は、この有限選択化と測定上の同値類を扱っていない（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:196-212`）。
  - なお Phase 3 正本は trigger axis を headline から外し、LLM が機械列挙を上回れない点を既に認めている（`docs/phase3-main-experiment.md:163-173`）。また selector と generation/synthesis を区別している（`docs/phase3.md:411-419`）。したがって Phase 3 全体の主張が直ちに崩れるわけではない。
- 成果物影響: 材料レポートが finite policy selection を LLM synthesisability の実証として再包装すると、研究主張が証拠より強くなる。
- scope: **scope 内**。新 D・レポート境界に「有限 policy 選択であり headline synthesis evidence ではない」と固定すべきである。

### 7. 受理集合が広がる入力はあるか

- 判定: **refuted**
- 根拠:
  - 現行 gate は五識別子を含む文字列を拒否する（`orchestrator/campaign/p3_s4_loop_trigger_gating.py:112-124`）。
  - 新文法の許可 token は Boolean literal、指定 enum、論理・比較演算子等で、五識別子のいずれも含まない（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:55-91`）。
  - コメント記号 `/` も lexical prefilter で拒否される（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:105-124`）。
  - よって新 gate を実際に通過する入力はすべて旧 blacklist も通過する。例示された「コメント内の `write_set_`」は旧 gate では識別子により拒否され、新 gate ではコメント記号により拒否される。
  - ただし所見4のとおり、狭まり方はプランが認めるより大きい。
- 成果物影響: active gate を正しく置換できた経路に限れば、blacklist 撤去による新規受理は発生しない。
- scope: **scope 内・この攻撃は棄却**。

### 8. positive-controls の「trigger 9件」分類

- 判定: **refuted**
- 根拠:
  - trigger 代入式は 1、3、5、41、43、45、47、49、51 行の九件である（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:1-5`, `/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/positive-controls.txt:41-51`）。
  - trigger stock prose が一件（同 `:7`）、sort stock/control と comparator が十六件（同 `:9-39`）、合計二十六件である（同 `:53`）。
  - 九式はいずれも plan の比較式・論理和・括弧・enum 文法で表現でき、`kUnset` 条件を含む（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:55-103`）。
  - 凍結 JSON にも同じ trigger predicates と source pins が記録されている（`output/s1-freeze/known_axes_freeze.json:46-47`, `output/s1-freeze/known_axes_freeze.json:79-80`, `output/s1-freeze/known_axes_freeze.json:272-273`, `output/s1-freeze/known_axes_freeze.json:498-499`）。
  - S1 direct は predicate を materialize できなければ停止する（`orchestrator/campaign/s1_direct_comparison.py:516-553`）。
- 成果物影響: 九式については回帰しない。仮に一式でも拒否すれば既存 bytes 自体ではなく、proof chain の能動的な再現・継続が停止する。
- scope: **scope 内・プランの件数と分類は正しい**。

### 9. 許可文法を role に書くと勝ち筋が漏れるか

- 判定: **refuted**
- 根拠:
  - 現行 role は既に全 enum 名と許可 input を提示している（`.claude/agents/coder-v4-autonomous-trigger-gating.md:82-100`）。
  - runtime の `GATING_SPEC` と designated context も enum members と許可カテゴリを列挙する（`orchestrator/campaign/p3_autonomous_workload_trial.py:221-240`）。
  - D51 は naked member names の提示を許し、member ごとの説明・順位・推奨 subset を禁じている（`docs/decisions.md:1957-1962`）。
  - プランも subset、ranking、winning hints を追加しないとしている（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:198-212`）。
  - D48 の firewall は frozen axis の observation を coder に渡さないことが中心である（`orchestrator/campaign/axis_trigger_gating.py:11-16`, `docs/decisions.md:1776-1778`）。
- 成果物影響: 演算子と閉文法だけなら、certified 選択の勝者を coder へ漏らす新しい side channel にはならない。
- scope: **scope 内・リーク攻撃は棄却**。member ごとの意味説明や推奨形は引き続き禁止。

### 10. role 更新は Codex adapter/review ledger と不整合

- 判定: **real — must-fix**
- 根拠:
  - role source の変更は review ledger の明示的 review 対象であり、adapter 再生成だけで source drift を承認できない（`orchestrator/codex_roles/review_ledger.py:1-6`, `orchestrator/codex_roles/review_ledger.py:15-47`）。
  - spec は role source hash drift を拒否する（`orchestrator/codex_roles/spec.py:583-593`）。
  - checker は adapter の embedded body、source body、rendered bytes の一致を検査する（`tools/check_codex_agents.py:216-245`, `tools/check_codex_agents.py:257-263`）。
  - 現行 adapter には旧 role body と hash が埋め込まれている（`.codex/role-adapters/coder-v4-autonomous-trigger-gating.json:145-185`）。
  - プランは role、runtime spec、runbook の更新と checker 実行だけを挙げ、review ledger、manifest、adapter 更新・承認導線を scope に入れていない（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:196-212`, `/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:249-261`）。
  - role 変更には明示的 user approval が必要という既裁定もある（`docs/decisions.md:1366-1370`, `docs/decisions.md:1964-1969`）。今回の敵対レビュー依頼は、その変更承認ではない。
- 成果物影響: 計画されたファイルだけを変更すると repo の role parity 検査を満たせず、成果物を受理可能な変更単位にできない。
- scope: **scope 内かつ承認待ち**。role を変更するなら review ledger／adapter／manifest を同一変更単位へ入れる必要がある。

### 11. `axis_trigger_gating.py` を触らない制約は不要か

- 判定: **refuted**
- 根拠:
  - frozen JSON は live module の path/hash を複数箇所で pin している（`output/s1-freeze/known_axes_freeze.json:46-47`, `output/s1-freeze/known_axes_freeze.json:272-273`, `output/s1-freeze/known_axes_freeze.json:498-499`）。
  - production verifier は文書に記録された各 source の hash を検証する（`orchestrator/campaign/s1_known_axes_freeze.py:718-742`）。
  - S1 direct は measurement freeze を load・verify する（`orchestrator/campaign/s1_direct_comparison.py:119-131`）。
  - measurement verifier は known-axes freeze を再帰的に検証する（`orchestrator/campaign/s1_measurement_freeze.py:156-163`, `orchestrator/campaign/s1_measurement_freeze.py:387-408`）。
  - したがって一つのテストで pin が発火しないことは、production proof chain に pin が存在しないことを意味しない。
- 成果物影響: axis module を編集すれば frozen proof chain の再検証が失敗し、再 freeze なしには既存 certified 選択を継続利用できない。
- scope: **scope 内・no-touch を維持すべき**。

### 12. frozen pin を直接発火させないテスト穴

- 判定: **real**
- 根拠:
  - frozen artifact test の manifest は JSON artifact 自体の hash を検査する構造である（`orchestrator/tests/test_frozen_artifacts.py:38-42`, `orchestrator/tests/test_frozen_artifacts.py:125-136`）。
  - known-axes freeze の単体テストは current docs を生成して検査する形で、凍結済み JSON と live source の組を一貫して検査する保証にはなっていない（`orchestrator/tests/test_s1_known_axes_freeze.py:103-115`）。
  - extime calibration test も injected verifier を使う経路がある（`orchestrator/tests/test_s1_verify_extime_calibration.py:109-113`）。
  - 親が記録した発火件数そのものは本レビューでは再実行しておらず、現行実測値は未確認。ただし静的には直接 pin 回帰テストの穴がある。
- 成果物影響: production verifier は守られていても、将来 source pin を外す回帰が通常の凍結 artifact 検査で早期検出されない。
- scope: **scope 外・裁定パッケージ行き**。本 wave に直接 pin 回帰を追加するか、別 task として owner を付けるべきである。

### 13. trigger 軸だけでは EVOLVE-BLOCK hole は閉じない

- 判定: **real**
- 根拠:
  - 親 brief は trigger のみを対象とし、sort を T-410 に分離する（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/s1-brief.md:6-11`, 同 `:60-70`）。
  - backoff の proposal は任意 `implementation` を保持する（`orchestrator/campaign/p3_s4_loop.py:110-117`）。
  - backoff consistency check は対応する数値 literal を regex で見つけるだけで、その後続 C++ を文法として閉じない（`orchestrator/campaign/p3_s4_loop.py:554-582`）。その implementation はそのまま materialize・build される（`orchestrator/campaign/p3_s4_loop.py:619-690`）。
  - D127 は DiffQuarantine を通る例として `std::system`、`execl`、`ofstream`、無限 loop を既に記録している（`docs/decisions.md:6228-6233`）。
  - sort も任意 comparator implementation を受け、DiffQuarantine と auditor の後に build する（`orchestrator/campaign/p3_s4_loop_sort.py:110-119`, `orchestrator/campaign/p3_s4_loop_sort.py:137-164`, `orchestrator/campaign/p3_s4_loop_sort.py:242-252`）。
  - D127 が sort を別 wave にした理由も、有限集合化で合成が選択へ変わる問題である（`docs/decisions.md:6235-6239`）。
- 成果物影響: T-409 完了後も backoff と sort から同型の文法外 C++ が certified materialization へ入れるため、台帳に「trigger instance を閉じた」としか書けない。
- scope: trigger の実装自体は **scope 外**。ただし backoff の owner が brief にないため、trigger-only 完了とするか wave を拡張するかは **裁定パッケージ行き**。

### 14. 親の既存 ruleops 失敗を「無関係」とした判断

- 判定: **refuted**
- 根拠:
  - 過去の測定と T407 由来の切り分けは worklog に記録されている（`docs/worklog.md:366-371`, `docs/worklog.md:596-598`, `docs/worklog.md:833-845`, `docs/worklog.md:1086-1088`）。
  - 当該 test は実 repository に対して `ruleops inventory` を実行する（`orchestrator/tests/test_ruleops.py:1710-1749`）。
  - inventory は対象 blob を strict UTF-8 decode し、invalid byte で失敗する（`tools/ruleops.py:642-668`）。
  - T-409 の planned files は ruleops、inventory test、問題 blob を変更しない（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:128-212`）。
  - 本レビューではテストを実行していないため、現時点で同じ事象が存在するかは未確認。ただし静的な責務分離として「T-409 gate 変更とは無関係」は支持できる。
- 成果物影響: この既知事象を T-409 の gate certification に混ぜる必要はないが、T407 側の未解決状態を消してはならない。
- scope: **scope 外・既存 owner 維持**。

### 15. gate 新設 wave の全層 scope が不足している

- 判定: **real**
- 根拠:

| 層 | プランの扱い | 静的に残る穴 |
|---|---|---|
| proposal 受理 | driver parser と final gate（`stage2-plan.md:128-148`） | 汎用・手動 proposal は未拘束 |
| materialize | 四系統を列挙（同 `:150-155`） | extime、汎用 quarantine、patchharness、固定 materializer の分類漏れ |
| build | 明示なし | pipeline/buildcache は language policy を要求しない |
| cache | 明示なし | grammar version/hash が preimage にない |
| replay/resume | 明示なし | loop/screening terminal skip、S8B resume |
| 記録・台帳 | reject reason のみ（同 `:181-194`） | pass receipt、policy version、migration record がない |
| 監査 | role/runbook 更新（同 `:196-212`） | auditor 目視と machine-pass 証明を結ぶ記録がない |

  - プラン自身も「将来 materialization path が増えれば bypass」と認めるが、閉包機構ではなく既知 risk として残している（`/work/1/SFC/tanab/dev-wave-jobs/t409-evolve-hole-allowlist/stage2-plan.md:266`）。
- 成果物影響: proposal wrapper だけを gate 済みとしても、build/cache/replay/recording が同じ policy を証明しないため、certified 選択・材料レポート・台帳の端から端までの主張にならない。
- scope: proposal・materialize・build・cache・replay・pass 記録は **scope 内**。既存 artifact migration と他 axis への展開は **裁定パッケージ行き**。

## 裁定パッケージ候補

1. materializer 中央再検査と封印済み gate receipt のどちらを権威境界にするか。
2. 既存 cache・WAL・resume artifact を cold invalidate、再検査、overlay のどれで移行するか。
3. D48 の literal 契約を維持して文法を広げるか、契約を狭めて role 変更を明示承認するか。
4. trigger-only 完了とし backoff/sort に owner を付けるか、本 wave を全 axis へ拡張するか。
5. frozen live-source pin の直接回帰テストを本 wave に含めるか、別 task に切るか。

## 総括

- プランは採用可能か: **不可**
- must-fix の件数と最重要1件: **5件。最重要は driver 配線では consumer/materializer 閉包にならず、実行可能な迂回経路が残ること**
- 裁定パッケージへ返すべき設計択一の件数: **5件**
- 親 brief で誤っていた点: **D136 後の cache/replay 基線を落としていること、「既存契約を狭めない」が numeric literal 反例で偽であること、extime・汎用 materializer・resume を含む consumer 閉包が不完全であること、gate policy を記録せず proof chain 不変と言い切ったこと**