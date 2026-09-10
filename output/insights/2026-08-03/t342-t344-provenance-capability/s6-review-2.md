静的読解のみ。対象は `HEAD=f087a91` と現行 `git diff HEAD` 25 files（+517/-145）。書き込み・pytest・build は実施していない。

## 所見

### 1. [High] guided の start/evaluate は新 identity API に追随していない

**claim:** `guided.py` は admission policy を持たない `CampaignConfig` を作り、必須 keyword なしで新 API を呼ぶ。`start` と `evaluate` はいずれも identity 確立前に停止する。

**evidence:**

- `canonical_preimage()` は `search_config.build_admission` を必須化している。[ident.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:132)
- `ensure_campaign_identity()` / `ensure_resumable_wal()` は keyword-only `admission_policy` が必須。[ident.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:185)
- guided config には policy がない。[guided.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:88)
- 両 command と既存試験は旧呼出しのまま。[guided.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:162) [guided.py:185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/guided.py:185) [test_guided.py:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_guided.py:228)

**impact:** 空の trial directory は作り得るが、lock/meta/WAL の正規 trial は開始・再開できない。

**成果物への波及:** P2.5 guided の試行台帳へ新規評価行が追加されず、そこからの certified 選択・材料参照は空集合になる。

**suggested_fix:** 新規 trial は明示的な安定 no-build policy で config を bind し、両 API へ同一 policy を渡す。既存 pre-policy trial は lock を書き換えず、別の read-only legacy resume 契約として扱う。

---

### 2. [High] diff-reject 試験は production payload と矛盾し、pre-policy lock で実 topology を回避する

**claim:** writer は START/ABORT に同一 `build_attempt_id` を追加したが、exact payload 試験はその key を禁止している。さらに critic fixture は lock を pre-policy に上書きし、post-policy attempt validator を踏まない。

**evidence:**

- writer は同一 attempt ID を両 record に記録する。[p3_s4_loop.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop.py:240)
- abort payload の exact key 集合には `build_attempt_id` がない。[test_p3_s4_loop.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop.py:263)
- `_critic_view()` は lock を `{"search_config": {}}` に置換する。[test_p3_s4_loop.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop.py:70) 同じ迂回が sort/trigger にもある。[test_p3_s4_loop_sort.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop_sort.py:81) [test_p3_s4_loop_trigger_gating.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:89)
- pre-policy artifact は topology 検査なしで view を取得できる。[artifact_admission.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:367) post-policy だけが validator を踏む。[artifact_admission.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:384)

**impact:** 現行 exact assertion は後段 critic 検査へ到達できず、attempt ID の欠落・START/ABORT 不一致を検出しない。

**成果物への波及:** writer 変更により WAL bytes と WAL SHA は既に変わる。ID topology が退行すれば post-policy campaign は材料レポート・critic の受理集合から外れ、その campaign の source reference が消える。

**suggested_fix:** §1-E にこの payload 変更を明示裁定したうえで、旧 payload を歴史定数として残す。現行試験では key 集合に ID を含め、START/ABORT の値一致を確認し、実 policy-bound lock と `require_admitted_campaign()` を使う。

---

### 3. [High] machine sweep の exact class 検査が、context/callable の存在検査へ緩和された

**claim:** S6/S8a の既存 exact admission 検査が §1-E 列挙外で除去された。新試験は resolver を呼ばないため、machine resolver が常に `None` を返しても成立する。

**evidence:**

- 旧試験は stock と machine の class を exact に区別していた（`ea6ca43:orchestrator/tests/test_s6_sort_sweep.py:314`、`test_s8a_trigger_sweep.py:307`）。
- 現在は同じ context object だけを確認する。[test_s6_sort_sweep.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s6_sort_sweep.py:314) [test_s8a_trigger_sweep.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8a_trigger_sweep.py:308)
- `_eval_one` 試験も resolver が callable であることしか確認しない。[test_s6_sort_sweep.py:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s6_sort_sweep.py:347) [test_s8a_trigger_sweep.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8a_trigger_sweep.py:349)
- §5 正例は helper を直接呼ぶだけで、stock pin も production policy から導出する自己照合。[test_p3_build_authority_cli.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_build_authority_cli.py:100)
- 実 resolver は別経路にある。[s6_sort_sweep.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s6_sort_sweep.py:203) [s8a_trigger_sweep.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_sweep.py:247)

**impact:** 「registered machine sweep が受理される」という §5 正例の統合証拠になっていない。

**成果物への波及:** 直接波及は nit（現行 resolver 本体は静的に存在）。ただし resolver→`None` の退行時、machine 候補は全て pre-build abort となり、certified 選択集合が stock のみに縮み、sweep provenance の outcome が置き換わる。

**suggested_fix:** public `run_sweep` から pipeline の admission 境界まで進む試験を置く。実 resolver を独立 `SourceEvidence` で呼び、sealed generator receipt と `MACHINE_GENERATED` を確認する。stock pin は policy から逆算せず独立 literal で固定する。

---

### 4. [High] campaign ID の歴史値保存が不統一で、一部 sentinel は内部矛盾している

**claim:** §1-E は旧 ID を歴史定数として残すよう要求するが、現在値への単純上書きと、旧値を current config に適用する試験が混在している。

**evidence:**

- 旧値保存は明示義務。[s4-ruling.md:85](/work/1/SFC/tanab/dev-wave-jobs/70fa1240/wave-t342-344/s4-ruling.md:85)
- `test_campaign.py` は「歴史的」と記述しながら `_bound()` した現在 config を使い、backoff/S6 の旧 literal を新値へ置換している。[test_campaign.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:371)
- S8a sweep の `config_for()` は policy-bound になったが、試験は旧 ID を current config の期待値としている。[s8a_trigger_sweep.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_sweep.py:208) [test_s8a_trigger_sweep.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8a_trigger_sweep.py:232)
- trigger loop sentinel は新値へ上書きされ、隣接する `_PRE_T343_*` がない。[test_p3_s4_loop_trigger_gating.py:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:516)
- autonomous fixture は build campaign `623e929a` を選ぶ一方、独立 pin 試験は no-build の `948f4c43` を要求する。[test_autonomous_trial_completeness.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:94) [test_autonomous_trial_completeness.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:1295)

**impact:** current ID、pre-T343 ID、no-build ID の意味が混線し、後方互換 sentinel と current producer pin の双方が弱い。

**成果物への波及:** 新 campaign は新 directory を選び、試行台帳の `campaign_id` / `campaign_root` / Layer3 source refs が変わる。一方、旧値消失により歴史成果物への参照 drift を検出できない。

**suggested_fix:** 全対象で `_PRE_T343_*` と `_T343_*` を対にする。歴史導出は旧 preimage を明示構築し、current config から導出しない。autonomous は build/no-build の ID 定数を別名で固定する。

---

### 5. [Medium] T126 と compute sink の admission negative が「引数欠落」試験へ置換された

**claim:** coder admission の意味検査が `build_context=None` による `TypeError` へ変わり、対象 admission gate へ到達しない。これは §1-E の許可列挙外。

**evidence:**

- T126 は production source の文字列検査になった。[test_t126_qualification_driver.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_t126_qualification_driver.py:43)
- 「unadmitted coder」試験は `build_context=None` しか与えない。[test_t126_qualification_driver.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_t126_qualification_driver.py:52)
- trigger compute も同じ TypeError 検査へ置換された。[test_p3_s4_loop_trigger_gating.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:630)
- T126 production は authority なし context を作るため、正しく検査すべき境界自体は存在する。[t126_driver.py:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_driver.py:512)

**impact:** required-argument 回帰は検出するが、dirty/coder source が authority なし context で拒否される契約は検査しない。

**成果物への波及:** 直接波及は nit。gate が退行した場合は coder-authored member が T126 の評価 event/attempt ledger に入り、formal 材料の受理集合と member reference が増える。

**suggested_fix:** missing-context 試験は別に残し、authority なしの正規 context＋dirty coder `SourceEvidence` を与え、build spy 手前の `BuildAdmissionError` を単一理由で固定する。T126 stock class の独立 positive も戻す。

---

### 6. [Medium] autonomous Layer3 chain fixture が production producer から期待値を生成する

**claim:** persisted report と cell admission decision を `layer3_report.build_report()` から生成し、consumer も同じ関数で fresh report を作る。共有 projection の誤りを検出できない。

**evidence:**

- fixture が production report を生成し、その admission decision を cell へコピーする。[test_autonomous_trial_completeness.py:1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:1253)
- consumer も同じ producer を再実行して比較する。[autonomous_trial_completeness.py:917](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/autonomous_trial_completeness.py:917)
- cell/persisted の比較も同じ値同士である。[autonomous_trial_completeness.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/autonomous_trial_completeness.py:1018)

**impact:** producer と consumer が同じ誤った receipt projection を採用すると、比較は恒真化する。

**成果物への波及:** 直接波及は nit。共有誤りが入ると、不正な validator SHA、overlay record reference、attempt receipt list を持つ材料レポートが試行台帳から参照され続ける。

**suggested_fix:** 最小 Layer3 report と admission decision を独立 literal で作る試験を追加する。fresh rebuild 等価性試験とは分離し、receipt 各 field の単独変異を consumer に与える。

---

### 7. [Medium] silo ladder の downstream-visible refusal が統合差分で削除された

**claim:** registry 契約は non-admissible producer が成果物へ refusal を載せるとしているが、silo ladder の production schema と fixture から `classification.build_admission` が削除された。

**evidence:**

- registry 正本は producer が `admission_status=non-admissible` を公開すると明記する。[materializer_admission.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/materializer_admission.py:2)
- silo materializer は registry に残る。[materializer_admission.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/materializer_admission.py:29)
- 現行 producer/schema には refusal がない。[silo_ladder_rung1.py:1236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/silo_ladder_rung1.py:1236) [silo_ladder_rung1.py:4673](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/silo_ladder_rung1.py:4673)
- fixture も同じ field を削除して自己整合させている。[test_silo_ladder_rung1_driver.py:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_silo_ladder_rung1_driver.py:219)

**impact:** registry と emitted evidence の対応が切れ、artifact 単体から拒否理由・materializer identity を復元できない。

**成果物への波及:** silo ladder 成果物の classification bytes から `admission_status/materializer/reason` が消える。`research_goal_eligible=False` は残るため現行 certified 選択の直接変更は nit だが、材料レポートの拒否参照は1件失われる。

**suggested_fix:** `build_admission=non_admissible_materializer(...)` を production schema と独立 fixture の双方へ戻し、registry test から実 producer document まで検査する。

---

### 8. [High] §5 の変異事前登録は 5 件が単一理由 attribution を満たさない

**claim:** M3/M7/M9/M10/M11 は、別例外・別検査・広すぎる mutation surface によって expected node の意味へ帰属しない。

**evidence:** M3 の guard 後には `_nonce` dereference がある。[build_admission.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/build_admission.py:299) M7 の key 検査後に必須 field の直接参照がある。[buildcache.py:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:377) M9 は topology 全体を一括呼出しする。[wal.py:716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:716) M10 の sink は wrapper を使わず再度 `_inspect_campaign()` を呼ぶ。[artifact_admission.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/artifact_admission.py:439) M11 の validator 戻り値は後段で必須参照される。[layer3_report.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:359)

**impact:** mutation の kill 自体を gate の検出力と誤認できる。

**成果物への波及:** 直接波及は nit。ただし誤った mutation 証拠を採用すると、実効 gate の退行時に旧3 campaignが certified/material 受理集合へ戻る、または receiptless WAL が試行台帳の terminal として再利用される。

**suggested_fix:** 下表の再照準先へ mutation を狭め、正常な隣接検査を保持したまま対象入力だけが受理される変異にする。

## 変異 11 件の静的判定

| ID | 判定 | 根拠／再照準 |
|---|---|---|
| M1 | 単一理由で kill される | `tracked_clean` を外すと dirty no-op が stock 分岐へ入る。対象 node と追加 coder-namespace node は同一理由。 |
| M2 | 単一理由で kill される | repo pin 条件だけを外すと pin 不一致 source が stock になる。 |
| M3 | 帰属不成立 | exact-type guard だけ緩めても `True._nonce` で別例外。parser token と同等に扱う coherent seam へ再照準する。 |
| M4 | 単一理由で kill される | admission digest を legacy key から外すと4 classの key集合が1つへ潰れる。 |
| M5 | 単一理由で kill される | 旧 binary を新 key 配下へ置いており、sidecar validator が実際の最初の拒否点。 |
| M6 | 単一理由で kill される | admission map を v2 preimage から外すと4 class digestが同一になる。 |
| M7 | mask されている | expected key から `admission` を外しても後段 `manifest["admission"]` が別経路で停止させる。field を optional 化した coherent validator mutation へ再照準する。 |
| M8 | 単一理由で kill される | policy key を hash preimage から外すと独立 pre/current ID pair が差を検出する。 |
| M9 | 帰属不成立 | topology 全体の skip は receiptless terminal のほか cross-attempt splice、duplicate START、receipt reuse を同時に無効化する。receiptless terminal 分岐だけへ再照準する。 |
| M10 | 帰属不成立 | `classify_campaign()` を偽装しても実 sink の `require_admitted_campaign()` は独立に `_inspect_campaign()` を呼び、受理集合は変わらない。共通 `_inspect_campaign` overlay branch へ再照準する。 |
| M11 | 帰属不成立 | validator assignment を消すと `admitted_campaign` の未束縛参照で停止し、旧 campaign の render 受理を証明しない。raw view を coherent に代入する変異へ再照準する。 |

M8 を含む identity 系は、所見4の baseline sentinel 矛盾を先に解消しないと mutation attribution の実測前提が成立しない。

## §5 正例の静的到達性

- clean stock: `STOCK + tracked_clean + CURRENT_PIN` の分岐は存在する。[build_admission.py:441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/build_admission.py:441)
- registered machine: generator receipt 分岐と S6/S8a resolver の配線は静的に到達可能。[build_admission.py:449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/build_admission.py:449)
- opted-in coder: parser token を持つ context の coder 分岐は存在し、5 driver の CLI 配線も確認できる。[build_admission.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/build_admission.py:462)

指定3分岐そのものに静的な過剰拒否は見つからない。ただし現行正例は public producer 経路の証拠ではない。別経路では所見1の guided が実際に過剰拒否される。

## 凍結・pin 面

- `FROZEN_MANIFEST` は exact 23 entries。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_frozen_artifacts.py:38)
- 現行23ファイルを manifest SHA と直接比較した結果は `count=23, mismatch_count=0`。
- `ea6ca43` から現作業木まで、`output/`、`s1_known_axes_freeze.py`、`t080_freeze_migration.py`、`test_frozen_artifacts.py`、`s1_expected_goldens.py` に差分なし。
- overlay 台帳は `FROZEN_MANIFEST`、S1 freeze bundle、T080、oracle manifest のいずれにも混入していない。独立 raw SHA と exact membership は固定されている。[test_artifact_admission.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_artifact_admission.py:21)

## producer 出力 bytes の変化面

| artifact 種 | 変化する bytes / path | 残る pin・問題 |
|---|---|---|
| legacy cache | admission SHA を含む key/directory、新規 `admission.json`。binary bytes 自体は必ずしも変わらない。[buildcache.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:145) | `_PRE_T343_GOLDEN_CK0` と現行値は双方保存済み。[test_campaign.py:3614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:3614) |
| v2 cache | full digest/directory、preimage、`completion.json.admission`。[buildcache.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:246) | exact fixture は更新済みだが M7 は mask。 |
| campaign | campaign ID/path、`campaign.lock`、START/DONE/COMMIT/ABORT、以後の WAL record hashes。[pipeline.py:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/pipeline.py:620) | campaign ID pin は所見4の不整合あり。 |
| Layer3 / autonomous | schema v3、`admission_decision`、artifact/source refs、trial cell の campaign refs。[layer3_report.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:442) | v2 readability は残るが、autonomous fixture は自己照合。 |
| S8a characterization | coverage/frequency JSON の `build_admissions`。[s8a_trigger_coverage.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8a_trigger_coverage.py:245) | 既存 committed output は未変更。将来再生成 bytes は変わる。 |
| S8b floor/oracle | cache digestを含む binary path/configure argv/build argv、manifest、campaign WAL/event refs。stored binary bytesは必ずしも変わらない。[s8b_floor_campaign.py:1169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s8b_floor_campaign.py:1169) | frozen 23件は未変更。新 run は旧 exact bytes と共有しない。 |
| T126 qualification | live member の build event receipt・cache reference。series identity/control pin は据え置き。[t126_driver.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_driver.py:524) | semantic coder negative が失われている。 |
| silo ladder | 本来追加された non-admissible refusal が現統合差分で再び消える。 | producer output の明示拒否値が欠落。 |

## 総括

最も危険な回帰は、global identity API の変更に guided が追随せず、start/evaluate の双方が正規 trial を作れないこと。これは検出力の問題ではなく production 経路そのものの断線である。

最も検出力が低いのは §5 の正例。production policy から期待 pin を逆算して core helper を直接呼ぶため、実 machine sweep resolver が無効でも成立し、承認外の受理集合縮小を検出しない。