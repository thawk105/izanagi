## 所見

### R1. 項目 4 は off-HEAD の fail-closed を rc=0 へ反転させる

- **主張:** 単独選択時に policy epoch を selected commit の祖先から解決する変更は、非権威な off-HEAD 監査を拒否する既存防壁を緩和する。
- **根拠 (file:line):**
  - プランは単独 commit なら resolver にその commit を渡すとしている (`s2-plan.md:157-166`)。
  - 現行契約は policy epoch を「current HEAD から検証」する (`tools/check_ai_provenance.py:1576-1593`)。
  - 既存 `test_known_violation_off_head_policy_guard_is_stale_rc2` は、policy epoch と target を作った後、policy の無い orphan HEAD へ切り替え、`target^!` が rc=2 になることを固定している (`orchestrator/tests/test_check_ai_provenance.py:2446-2493`)。
  - 変更後は `_implementation_policy_commit(target)` が epoch を発見し、target の `missing-codex-author` が既知違反として消費され、静的には rc=0 になる。
  - この挙動は commit `5ed3844f3` で意図的に着地した。worklog は同じ off-HEAD 緩和が一度 fail-open を作り、偽赤を受容して rc=2 へ戻した経緯を明記している (`docs/archive/worklog-phase3-0807-289.md:20-27`)。
  - 全 consumer は `_scope_policy_commit`: production `:1605`、tests `:2720,:3660`、`_implementation_policy_commit`: production `:1606`、tests `:751,:2479,:2721,:3661,:3847,:4151`。プランは `:2479` の意味契約を取り残している。
- **帰結:** 非権威な履歴からの既知違反監査の受理値が rc=2 から rc=0 へ広がり、過去に却下済みの fail-open を再導入する。
- **深刻度:** blocker

### R2. `LIVING_DOCS` singleton は実 inventory 経路を検査しなくなる

- **主張:** `LIVING_DOCS=[PREREG_DOC]` に差し替えると、`assert injected` は本番 inventory を main が辿る証明ではなく、テストが与えた singleton を読むだけの自己充足に変わる。
- **根拠 (file:line):**
  - 実 inventory は `tools/check_docs.py:47-87`、本番走査は `:5258-5324`。
  - 現在の負例は実 inventory の中から `PREREG_DOC` が読まれたことを `injected` で確認する (`test_s8c_preregistration_invariant.py:342-364`)。
  - プランはその直前に inventory 自体を singleton へ交換する (`s2-plan.md:103-111`)。
  - 具体的な reward-hack 変異は `tools/check_docs.py:5258` の loop 内へ次を入れる形である: 実 `LIVING_DOCS` が複数件のときだけ `phase3-8c-preregistration.md` を `continue` する。修正前は `injected=False` で赤、singleton 後は長さ 1 なので対象を読み、全 assert が緑になる。実際の引数なし checker は 8c 文書を黙って未検査にする。
  - 8c 文書を名指しする負例はこの node だけである。直前 node は集合所属しか検査しない (`:336-339`)。
- **帰結:** 本番 main が 8c 文書を実 inventory から選択的に落としても対象 node が受理し、不在 path・腐敗行番号の受理集合が広がる。
- **深刻度:** blocker

### R3. 項目 3 の修正は比例源も除去し切らない

- **主張:** singleton 化しても `check_docs.main()` の repository-growth-proportional な閉包は残るため、4.79 秒の node を固定入力へ変えられない。
- **根拠 (file:line):**
  - `main()` は living-doc loop より前に command/reference、spool、dispatch、Pegasus、`decisions.md` 全文を検査する (`tools/check_docs.py:5217-5255`)。
  - loop 後も placeholder、worklog/phase backlog、archive 索引と `ARCHIVE_DIR.iterdir()`、worklog、handoff を読む (`:5326-5426`)。
  - `_check_backlog_guard` は singleton により `phase3_text` が `_UNREAD` のままでも phase3 を再読する (`:1839-1872`)。
  - 正規 seam は存在しない。`main(argv)` の引数は `--expect-active-transaction` だけで、per-doc checker は inline のままである (`:5212-5324`)。
  - DW-O14 は既存 seam を確認し、monkeypatch を最後の手段とする (`docs/dev-wave/operations.md:88-91`)。
- **帰結:** 成果物の `docs_bytes` 比例分類と受入 work の成長率が残り、項目 3 を「修正済み」とする値が虚偽になる。
- **深刻度:** must-fix

正しい方向は private な per-doc 検査関数の切り出しである。ただし直接 helper を呼ぶだけでは main との結線が抜けるため、default `main()` が無改変の `LIVING_DOCS` を helper へ渡すことと、渡された複数 doc を全走査することを別の固定入力 control で守る必要がある。部分走査用 CLI・環境変数は恒久保留の裏口になるので作らない。

### R4. 項目 2 の mutation anchor は launcher の退行を観測しない

- **主張:** 新 helper を単独 import する検査では、実 launcher を旧 self-import に戻す変異を捕捉できない。
- **根拠 (file:line):**
  - プランの新 node は独立 subprocess で helper を importして `sys.modules` を見る (`s2-plan.md:74-85`)。
  - 変異対象は別箇所である実 launcher (`test_dev_waves_integration.py:2050-2058`)。
  - `_serve_child_main` を旧 module から削除する実装なら、変異時に赤になるのは既存 socket node (`:2165-2167`) で、新規 node は緑のまま。この既存 node は `xdist_group` 所属なので期待 node に登録できない。
  - 互換 alias を残す実装なら、旧巨大 module を importしてから helper を呼べるため、socket nodeと新規 nodeの双方が緑になりうる。
- **帰結:** 旧 self-import を復活させた入力が mutation matrix で MISMATCH または SURVIVED となり、比例源除去の受理集合が守られない。
- **深刻度:** must-fix

実 launcher と同一の child command を probe mode で起動し、その child 自身が禁止 module の不在を報告する形へ照準する必要がある。

### R5. 項目 4 の wrapper は revision の「受領」しか検査しない

- **主張:** wrapper の `assert revision == commit` は、resolver が revision を実際の `git log` に使用することを保証しない。
- **根拠 (file:line):**
  - プランの唯一の anchor は resolver wrapper である (`s2-plan.md:173-179`)。
  - 修正後の resolver から `revision` の `_git()` 引数だけを再び落とす変異では、wrapper は正しい引数を受け取るため通る。
  - 二つの固定 target は現 HEAD と同じ epoch を返すとプラン自身が確認している (`s2-plan.md:166`)。
  - さらに現行 off-HEAD test は HEAD を無視しない変異を期待するため、この「revision を無視する」変異側が既存期待値とも整合する。
- **帰結:** 全史 HEAD scan を残したまま対象 2 node と新規 wrapper が緑になり、比例源除去の成果値が恒真化する。
- **深刻度:** must-fix

### R6. 項目 1 の「7 node」は特定できるが、プランの列挙が別集合である

- **主張:** 7 件という歴史上の集合は再現できるが、プランはそのうち 2 件を別 node と取り違えている。
- **根拠 (file:line):**
  - 元の敵対所見が列挙した 7 件は `test_codex_agents.py:121-124,127-150,164-213,216-230,233-249,511-519,1300-1307` (`output/.../verbatim/s3-lensA.md:44-51`)。
  - 関数名では、先頭 5 件に加え `test_shared_developer_instruction_template_has_independent_pin` (`test_codex_agents.py:511-519`) と `test_direct_role_coverage_drift_raises_clean_profile_error` (`:1300-1307`) である。
  - プランは後二者を落とし、既に旧 A06 集合にあった `test_current_sources_render...` と、実 repo でなく `_fixture()` を使う `test_any_native_discovery_toml_is_rejected` (`:252-263`) を入れている (`s2-plan.md:30-38`)。
- **帰結:** 「対象 11 node」の実測・mutation 記録が別集合になり、既知漏れ node 数と対象名の成果物値が誤る。
- **深刻度:** must-fix

## 親 brief への反論

P1 の「13 pin だから比例ではない」は誤りである。`EXPECTED_ROLE_COUNT` は最大値でなく、増減時に明示更新する review checkpoint である (`review_ledger.py:10-13`, `spec.py:542-548`)。実際、commit `2f8eda595b34...` で 12 から 13 へ更新されている。read-only の `git ls-tree -r -l` でも `.claude/agents` は 11 file / 72,697 bytes、12 / 79,521、13 / 84,264 と増え、現 HEAD は同じ 13 fileでも 83,157 bytesである。各 body は全読込・再 hash される (`spec.py:320-330,582-585`)。したがって count も byte 量も永久固定ではない。D463 が role 定義を第三区分の例にしているため no-hold/no-edit 結論は維持可能だが、根拠は「13 が上限」ではなく、review-controlled な固定用途集合と D451 である。

単独走の 4.23 秒と 4.79 秒を受入 wall の約 9 秒へ足すことはできない。受入は既定で xdist `loadgroup` (`tools/run_tests.py:4-8`)。項目 2 は `dev-waves-runtime` group (`test_dev_waves_integration.py:2165`) に直列化される一方、項目 3 は ungrouped で並行しうる。collection/import、OS cache、worker 配置、group の critical path が異なる。`repository_candidate_commit` は session fixture (`test_s8c_preregistration_invariant.py:119-122`) だが項目 3 自身は consumer ではなく、全 file 走と単独 node 走で構築費の帰属も変わる。親 measurements の「一般化に注意」は正しいが、brief の「4件はいずれも wall に載る」は additive な寄与としては未証明である。

項目 2について、self-import が不要な成長入力であることは real だが、「主要な支配項」とする根拠はない。child call は同時に実 `tools/task_runs` を copytree (`test_dev_waves_integration.py:160-185`)、複数の `git init/commit/submodule add/clone/fetch` (`:176-239`)、実 Supervisor、socket exchange、terminal wait (`:1685-1752`) を実行する。新 helper も production import 閉包とこの workload は必要とする。4.23 秒だけでは parse/compile、Git、copytree、daemon のどれが支配的か分離できない。

また「child 側だけの依存閉包」は小さくない。harness は `_isolated_process_environment`、`_temporary_repo`、`_supervisor`、`_request`、`_wait_terminal` 等へ到達し、同 file 内の出現数はそれぞれ 43、42、43、48、31 である。逆 import を禁じるなら、これらを一つの共有 source として移して全 consumer を更新する必要があり、複製は T-145 の liveness fixture を二系統へ分岐させる。プランの「payload/main と child-only closure」だけでは所有・consumer 計画が不足している。

項目 4 の current HEAD 依存は偶然の無駄ではなく、既知違反台帳の権威境界でもある。0.034 秒の tip scan を除くためにこの意味を selected commit へ移すことは、費用最適化ではなく受理集合変更である。

## refuted

- 新規 `growth_test_holds`、`skip`、`xfail`、環境変数による保留はプランにない。既存 socket node の `xdist_group` は実行除外ではない。
- `LIVING_DOCS` 差し替え後に `_ENUMERATED_DOCS` が import 時集合のままでも、それ自体は偽 finding を作らない。main は両集合の equality を検査せず、対象 `PREREG_DOC` は元から `_ENUMERATED_DOCS` に含まれる (`check_docs.py:64,82,5261-5268`)。phase3 未走査も `_check_backlog_guard` が再読する (`:1862-1872`)。
- singleton で縮む検査は、列挙 doc 不在、読取不能、腐敗行番号、現況主張再掲、次アクション再掲、CURRENT_PIN literal、未知 D、実在しない path の全件である (`check_docs.py:5261-5324`)。ただし「無関係な別 doc の finding が消える」だけではこの負例の赤緑は変わらない。現行 node は既に注入 finding により rc=1 を期待し、余分な finding を exact 拒否していない。real な穴は R2 の実 inventory 結線喪失である。
- 項目 1 は実装差分なしなので、現存拒否経路そのものは減らない。問題は分類根拠と対象 node inventory の誤りである。
- pytest は実行していない。以上は静的検査と Git 履歴確認であり、緑は主張しない。

## 総括

段 5 へは NO-GO である。blocker は、項目 4が既に一度却下された off-HEAD fail-open を再導入することと、項目 3の singleton が本番 `LIVING_DOCS` 結線をテスト用入力へ置換して reward-hack 可能にすることの 2 件である。加えて、項目 3は比例閉包を除去し切らず、項目 2・4の mutation anchor は提案変異を観測せず、7 node の対象集合も誤っている。項目 3は per-doc seamと独立した main wiring 防壁へ、項目 4は current-HEAD 権威を保った別の費用除去策へ設計し直す必要がある。