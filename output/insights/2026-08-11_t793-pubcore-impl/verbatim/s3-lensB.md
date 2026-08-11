# レンズ B 所見

テスト実走・編集・commit は行っていない。

## 総括

**NO-GO**。段 2 プランの `plan_fold()` への結線は通常経路では有効だが、`apply_fold()`、active transaction の resume、land recovery が同じ gate を通らない。さらに source main gate・台帳予約・P exact-key は実 caller がなく、ライブラリ単体の検査に留まる。

§10.4 の 11 変異は、実成果物経路では **0/11**、直接 parser の負例としても **#7 と #9 の 2/11 に限定**される。

### 結線監査

| gate | 実 caller | 本 wave の結線 | 判定 |
|---|---|---|---|
| marker | `check_docs.py:797-830`、`plan_fold():1944` | `_discover()` に置く案 | 通常計画経路のみ。`apply_fold()` は bypass |
| publication ledger | 現在なし。既存の実 caller は source trial ledger のみ (`p3_autonomous_workload_trial.py:610-620`) | `reserve_next_publication()` はテストからのみ | 実運用では未結線 |
| P exact-key | `addendum_envelope.py:152-186` は汎用/A 専用 | 新 wrapper と単体テストのみ | P freeze/resolver への caller なし |
| D291 reader/report | 現在なし | 新 CLI の内部 caller のみ | material report/consumer へ未結線 |
| source main gate | `submit_main` の実 callerなし | 新 D fold 後の将来 land | 本 wave では未結線 |

## B1

- **severity:** blocker
- **根拠:** `tools/spool_fold.py:1932-1946`, `tools/spool_fold.py:2277-2292`, `tools/spool_fold.py:2497-2515`, `tools/spool_fold.py:1048-1088`, `tools/dev_wave_land.py:2214-2224`, `tools/dev_wave_land.py:1869-1873`
- **落ちる具体経路:** `addendum-p-draft.md:35-44` の marker を含む blob を指す approval fragment は、通常の `plan_fold()` では検査できる。しかし active state があると CLI は `:2505-2506` で `_state_plan()` を直接読み、`apply_fold()` も `_discover()` を呼ばない。直接 `apply_fold(repo, plan)` と land recovery の `validate_spool_layout()` 経路も同様に marker 検査を通らない。
- **成果物影響:** marker 入り blob を pin した承認 fragment が canonical `docs/decisions.md` へ fold され、後続 resolver が解決不能な承認・参照を受理する経路が残る。

段 2 の「`_discover()` に置けば direct `plan_fold()` も共有する」は、`plan_fold()` に限れば正しい。**全 fold 経路を共有するという主張は誤り**である。gate は `apply_fold()` の state/resume 前、または land recovery 前にも再検査する必要がある。

なお、親 brief の P5 (`spool_fold.py` を変更しない) と、段 2 の解決策 (`spool_fold.py:936-1038` を変更する) は所有境界も衝突している。変更を許可する裁定か、direct apply の保証を捨てる裁定が必要である。

## B2

- **severity:** blocker
- **根拠:** `docs/decisions.md:13470-13482`, `docs/decisions.md:13583-13588`, `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:644-653`, `orchestrator/campaign/s8c_preregistration.py:1809-1838`
- **落ちる具体経路:** 空の `output/registry/t139-publication-reservations.jsonl` に対して source main を投入する caller は現在存在せず、既存の source launcher (`orchestrator/campaign/p3_autonomous_workload_trial.py:610-620`) は publication gate ではなく trial registry だけを呼ぶ。D291 自身も `source_main_run_gate = not_implemented` と明記している。
- **成果物影響:** source main が publication reservation を確認せず走れるため、将来の公表 study の事前登録性・予約済み判定が失われる。現時点では D292 により pilot/main は forbidden のままで、即時の certified 値は動かない。

新 D が fold されるまで `admission.py` を land 対象外とする判断自体は正しい。ただし、その状態で Q1 の必須要件を「実装済み」と報告してはならない。裁定パッケージ候補として返すべきである。

## B3

- **severity:** must-fix
- **根拠:** `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:578-585`, `docs/decisions.md:13503-13510`, `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:681-691`, `orchestrator/preregistration/addendum_envelope.py:152-186`
- **落ちる具体経路:** `reserve_next_publication()`、P wrapper、D291 report は新 package 内の単体 API とテストからしか呼ばれない。P draft は `addendum-p-draft.md:15-18` により resolver/producer/consumer が発効前に読んではならず、reservation entry も発行しないため、実成果物を拒否する caller がない。
- **成果物影響:** 台帳が空でも source/publication の受理集合は変わらず、P の `p04` 余剰や未承認 blob が実際の freeze/resolver で拒否されない。material report の承認欄も自己申告のまま残る。

最低限、各 API に「production caller なし・単体検査のみ」と明記すべきである。特に `reserve_next_publication()` の正例は、実運用の予約発行を意味しないことをテスト名・report・handoff で固定する必要がある。

## B4

- **severity:** must-fix
- **根拠:** `tools/run_tests.py:505-563`, `tools/run_tests.py:629-666`, `tools/ruleops.py:71-72`, `tools/ruleops.py:771-789`, `tools/check_docs.py:112`, `tools/check_docs.py:1263-1327`, `orchestrator/tests/test_frozen_artifacts.py:38-85`, `orchestrator/tests/test_frozen_artifacts.py:125-153`
- **落ちる具体経路:** 0-byte の tracked file は、受入形検査では pytest 引数の形しか検査されず、RuleOps の対象 (`orchestrator/tests` と `output/insights`) にも入らない。`check_docs.py` は worklog/archive/insights と spool を走査し、`output/registry/` を走査しない。`test_frozen_artifacts.py` も manifest の 23 path だけを走査する。
- **成果物影響:** tracked である限り 0-byte 台帳は既存検査をすべて通るため、削除・再作成・別台帳への差し替えを別の ledger gate が検出しなければ、予約履歴と公表 entry の一意性が変わる。

land の扱いは次のとおり。

- wave worktree に untracked で残れば `tools/dev_wave_land.py:887-889` で赤。
- main に untracked で存在すれば `tools/dev_wave_land.py:845-871` で赤。
- wave commit に tracked file として入れば `tools/dev_wave_land.py:923-942` の target には含まれるが、それ自体は赤にならない。
- 既存の ignored path と衝突すれば `tools/dev_wave_land.py:990-1019` で赤。

`FROZEN_MANIFEST` を変更しない判断は、追記型台帳を whole-file digest で凍結しないという意味では整合する。ただし、D282 の primary ledger が `docs/decisions.md:12941-12957` で導入 commit・履歴規則を別途固定しているのと同じく、新 ledger も初回導入・regular mode・削除再作成拒否を独立 gate として持たなければならない。

## B5

- **severity:** should-fix
- **根拠:** `orchestrator/preregistration/__init__.py:8-28`, `docs/decisions.md:13323`, `docs/decisions.md:13347-13377`, `git show worktree-dev-wave-t139-manifest-w2:orchestrator/preregistration/approval_payload.py:16-50`, `git show worktree-dev-wave-t139-manifest-w2:orchestrator/tests/test_t139_approval_payload.py:135-152`
- **落ちる具体経路:** land 2 の parser は D282 専用で、decision kind は `t139-preregistration-approval-supersession/v1`、固定 decision ref と 6 role、10 top-level key を要求する。D291 は別 kind、2 approved role、3 relation subtree、14 top-level key である。D282 の `alpha_reservation` も `t139-alpha-reservations.jsonl`、`alpha_reservation`、root `dce4...` を固定しており、publication ledger の `individual_publication` / root `88d68...` とは別 bytes である。
- **成果物影響:** D282 parser を流用すると source approval または primary alpha ledger を publication approval と誤認し、誤った role・root・ledger entry が材料 report に入る。誤 import なら T-793 が先に main に入った時点で import failure になる。

`orchestrator/publication/` 自体は land 2 branch の tree に存在せず、package path・現在の `__init__.py`・`test_t139_approval_payload.py` の nodeid は衝突しない。一方、land 2 branch は共有の `preregistration/blobref.py`、`erratum.py`、`test_t139_preregistration_binding.py` を変更している。したがって「file 非重複」は「統合面ゼロ」ではない。T-793 は D291 parser から `BlobRef/read_pinned_blob` だけを利用し、`preregistration.approval_payload` や共有 test file を import/変更しない契約を明記すべきである。

## B6

- **severity:** should-fix
- **根拠:** `orchestrator/campaign/trial_registry.py:418-473`, `orchestrator/campaign/trial_registry.py:814-968`, `orchestrator/campaign/trial_registry.py:1415-1457`, `orchestrator/tests/test_trial_registry.py:1566-1613`, `orchestrator/tests/test_trial_registry.py:1970-2004`, `orchestrator/preregistration/addendum_envelope.py:114-186`, `orchestrator/tests/test_t139_preregistration_binding.py:289-329`
- **落ちる具体経路:** JSONL の canonical 化、blank line/duplicate key/unique identity、inode・lock・fsync、Git prefix history、delete/recreate 拒否は trial registry に既に存在する。Markdown exact-key envelope も A 用の汎用 parser と負例 test が存在する。land 2 branch には decision body を pinned bytes から読む D282 parser (`approval_payload.py:166-188`) も存在する。
- **成果物影響:** T-793 がこれらを独立実装すると、同じ duplicate/非 canonical/delete-recreate 変異の検出力は純増せず、publication ledger と trial ledger の挙動が将来分岐する。

P wrapper は既存 `parse_addendum_fields()` に固定集合 `{p01,p02,p03}` を渡す薄い wrapper に限定すべきである。ledger の公開 API は trial registry を丸ごと流用できないが、低層の履歴・append primitive を共有するか、意図的な重複であることを明記し、publication 固有の差分（root/kind/dataset identity）だけを新規検査にすべきである。

## B7

- **severity:** must-fix
- **根拠:** `orchestrator/preregistration/blobref.py:89-135`, `docs/decisions.md:13445-13468`, `tools/check_docs.py:4647-4649`, `tools/dev_wave_land.py:1872-1873`, 段 2 job artifact `s2-plan.md:556-569`
- **落ちる具体経路:**

  1. D291 relation の `note` を 1 文字変更すると、実際の `F_p:docs/decisions.md` では先に全体 digest gate が落ち、relation exact gate の kill と帰属できない。
  2. approved triple の digest を変更すると、approved-set exact gate と `read_pinned_blob()` の blob digest gate のどちらでも落ち得る。
  3. marker 入り P blob の bytes と宣言 digest を同時に変えると、blobref gate と marker gate が競合する。marker だけを変える場合は既存 digest を更新し、blobref を通過させる必要がある。
  4. duplicate ledger row は JSONL uniqueness、row の削除再作成は Git history gate が先に発火し得る。
  5. `p04` と D292 の forbidden state を同じ fixture に入れると、P exact-key または deny-only report のどちらが kill したか不明になる。
  6. marker gate は `check_docs.py:4648` の spool guard の後段検査を実行させない。land では `apply_fold()` 後の `check_docs.py` (`dev_wave_land.py:1872-1873`) が late failure となり、期待していた後段 node の失敗理由を置き換える。

- **成果物影響:** mutation receipt の kill gate/nodeid が不定になり、どの不変条件を実証したかを証明できず、受入時の certified・material report・試行台帳の検査対象が置き換わる。

D291 の bytes mutation は `load_d291_payload()` の実 blob path ではなく、固定 digest gate を一旦外せる bytes parser seam で relation gate を単独検査する必要がある。marker、digest、relation、ledger history は一 fixture 一変異に分離すべきである。

## B8

- **severity:** must-fix
- **根拠:** `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:662-677`, `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:681-691`, `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:657-660`
- **落ちる具体経路:** T-793 の ledger parser と P envelope parser は、§10.4 の一部を直接拒否できるだけで、publication producer/validator/consumer へ結線されていない。特に ledger に dataset identity がないため、同一 dataset の別 core を機械的には識別できない。
- **成果物影響:** 実公表表が生成される経路では、§10.4 変異を通過した結果が certified selection や material report に混入し得る。

| # | 変異 | T-793 の判定 | 責務 |
|---:|---|---|---|
| 1 | 適格 cluster の一部だけ受理 | 実装しない | source validator / publication consumer wave |
| 2 | 6 行・partial recovery 以外を落とす | 実装しない | source validator / publication renderer wave |
| 3 | qualification を公表側で再計算・producer申告を使用 | 実装しない | source validator wave |
| 4 | 判定不能 workload で対角共分散を使用 | 実装しない | publication validator wave |
| 5 | Holm の `<` を `≤`、丸め値で判定 | 実装しない | publication validator wave |
| 6 | BH/Simes/maxT を runtime 切替 | 実装しない | publication validator / execution-config gate |
| 7 | 閉集合外 `ledger_kind` で `k=1` | **実装するが ledger parser 限定** | T-793 ledger。実予約・consumer には未結線 |
| 8 | 同一 dataset の第2 core | 実装しない | dataset-bound producer/validator wave |
| 9 | P の閉集合外 field | **実装するが P parser 限定** | T-793 wrapper。P freeze/resolver には未結線 |
| 10 | stress check の除外・再抽出 | 実装しない | publication validator wave |
| 11 | 公表結果を certified selection へ渡す | 実装しない | consumer / certified-selection wave |

したがって「機械的に拒否できる」と宣言できるのは、厳密には **直接 parser test で #7/#9 のみ**である。実際の受理・公表経路での証明は **0/11** であり、#8 を ledger tuple uniqueness でカバーしたとする主張は成立しない。

## B9

- **severity:** blocker
- **根拠:** `docs/decisions.md:13476-13482`, `docs/decisions.md:13583-13588`, `output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md:686-691`, 段 2 job artifact `s2-plan.md:599-607`
- **落ちる具体経路:** 4 必須要件を一つの wave で閉じるには、新 D の fold、source main の実 caller、publication reservation の実利用、P freeze/resolver、§10.4 validator/consumer が必要になる。現 plan は新 D と `admission.py` を条件付きで後段へ送り、producer・semantic validator・publication validator・renderer は scope 外としている。
- **成果物影響:** 一 wave 完了扱いにすると、空台帳・未承認 P・`pilot/main_submission=forbidden` のままなのに source admission と publication enforcement が完成したように見え、将来の certified/publication acceptance の境界が曖昧になる。

分割案は次のとおり。

1. **T-793 に残す:**  
   固定 path/root/kind の ledger parser、empty tracked file、独立した Git history gate、marker gate（`plan_fold`・`apply_fold`・active recovery 全経路）、D291 deny-only reader/report、既存 parser を使う P exact-key wrapper。
2. **T-793 から落とす:**  
   source `admission.py` の成功系、source main 接続テスト、reservation entry 発行、P freeze、§10.4 の validator/consumer。
3. **新 D 後の次 wave:**  
   実際の source main boundary に deny-only gate を結線し、空台帳・偽 root/kind・重複予約を本当に拒否する。
4. **さらに後段の publication validator/consumer wave:**  
   #1–#6、#8、#10、#11 と dataset identity、renderer、certified selection 境界を閉じる。

この分割なら T-793 の成果物は「台帳は空、P は未承認、pilot/main は forbidden、certified selection と material report は不変」と正直に報告できる。