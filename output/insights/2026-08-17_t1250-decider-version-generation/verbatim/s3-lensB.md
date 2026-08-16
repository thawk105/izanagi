静的レビュー結論です。clean な状態で「doc を未 commit で編集 → producer を一度だけ実行 → test を追加 → 3 ファイルを一 commit」なら成立します。ただし、事前確認や文言修正で簡単に停止します。

pytest、`tools/check_docs.py`、`tools/check_ai_provenance.py` は実走していません。以下は実コードに基づく静的判定です。

### B1 — `prepare_revision` は HEAD と worktree を非対称に読むため、再実行手順が詰まる

**主張**  
producer の一回目は条件付きで成功するが、doc 編集前、二回目、doc の修正ではそれぞれ別の理由で停止する。

**根拠**

- 世代数と既存 record の検証は resolved `HEAD` の tree を読む。[s8c_preregistration.py:1849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1849)、[s8c_preregistration.py:1875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1875)
- 新 record の contract は worktree の doc/evidence から作る。[s8c_preregistration.py:1882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1882)
- doc 編集前は protected hash が同じため `spurious-revision`。[s8c_preregistration.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1889)
- doc だけを commit すると、HEAD の新 doc と g3 record が不一致になり `record-protected-mismatch`。[s8c_preregistration.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1285)
- g4 生成後、未 commit のまま再実行すると destination は同じ g4 で `O_EXCL` が `revision-exists` を返す。[s8c_preregistration.py:1905](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1905)
- g4 を commit した後に doc を修正して再実行すると、g4 を置換せず g5 を作る。[s8c_preregistration.py:1876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1876)

さらに `validate_condition_freeze_at` と `activation_report_at` は worktree ではなく commit の blob だけを読む。[s8c_preregistration.py:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1411)、[s8c_preregistration.py:1678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1678)

**成果物への影響** — 失敗すると g4 が存在せず tip は g3/schema v1 のままなので、`decider-version-unbound` が残り、certified 選択や発効可能な admission は増えない。

**推奨対応**  
doc の最終文言を確定してから producer を一度だけ実行する。producer 後の doc 修正は行わず、`revision-exists` が出た場合は対象ファイルの commit/index 状態を確認して停止する。pre-commit 検証には HEAD 専用テストでなく、既存の candidate commit 検証を使う。

### B2 — 意図した変更で赤になる既存 nodeid は静的には 0 件

**主張**  
計画どおりの doc 文言、canonical g4、同じ test file の追加を一 commit した場合、既存 nodeid が g4 の追加だけで赤になる根拠はない。計画の表は「失敗条件」であり、実際の赤一覧ではない。

**根拠**

全件検索に使った command:

```bash
git grep -n -I -e 'decider_version' -e 'decider-version' -- orchestrator/campaign orchestrator/tests tools docs/phase3-8c-preregistration.md docs/phase3-8c-wiring-design.md output/README.md
rg -n 'test_.*s8c_preregistration|WAVE_REQUIRED_PATHS|REAL_REPO_SERIAL_NODES' orchestrator/tests
```

条件付きで赤になる既存 nodeid は次のとおり。

- `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
- `test_s8c_preregistration_invariant.py::test_repository_legacy_v1_generations_remain_readable[1]`
- 同 `[2]`、`[3]`
- `test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
- `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
- `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
- `test_s8c_preregistration_core.py::test_current_markdown_extracts_nine_fields_and_conditions_1_to_12`
- `test_s8c_preregistration_core.py::test_generation_added_without_protected_change_is_spurious`
- `test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract`
- `test_check_docs.py::test_normative_exact_section_pins_accept_real_repo`
- `test_check_docs.py::test_real_repo_clean`

g1〜g3 の legacy test は `(1, 2, 3)` だけを読む。[test_s8c_preregistration_invariant.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:164)

test file は新設されず既存 allowlist 済みなので、file 集合 meta-test は赤にならない。[orchestrator/tests/README.md:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/README.md:174)、[test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_plain_runner_coverage.py:60)

`check_docs.py` は当該 doc を `LIVING_DOCS` として読むが、phase doc 用の byte budget、見出し規約、一般行長制限は持たない。[check_docs.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_docs.py:64)、[check_docs.py:4557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_docs.py:4557) 主な実効規則は行番号参照、D 参照、path 実在性である。[check_docs.py:5285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_docs.py:5285)、[check_docs.py:5308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_docs.py:5308)

提案文の `D458` と `docs/decisions.md` は実在し、`output/README.md:24` の namespace 記述とも矛盾しない。

**成果物への影響** — 正しい三ファイル commit なら certified 状態や受理集合は変わらず、誤った path/hash/世代連鎖だけが land を止める。

**推奨対応**  
「commit 後に既存検査が赤になる」とは記録せず、「静的予測では既存赤 0、条件付き failure は上記」と記録する。pytest 未実走を明記する。

なお、既存の `legacy_prefix` は実際の path の `/condition-freeze/` を含まないため、負の assert が実質無効である。[test_s8c_preregistration_invariant.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:134) これは本 wave の直接赤ではないが、別途修正候補である。

### B3 — 新しい HEAD 実 repo test が serial node 集合から漏れている

**主張**  
計画は新 test を `REAL_REPO_SERIAL_NODES` に登録不要としているが、新 test は実 repo の HEAD と live source を読むため、共有 worktree writer と競合し得る。

**根拠**

計画は登録不要と明記している。[s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:119)

全件検索:

```bash
rg -n 'test_s8c_preregistration|REAL_REPO_SERIAL_NODES' orchestrator/tests/conftest.py orchestrator/tests/README.md orchestrator/tests/test_s8c_preregistration_invariant.py
```

`conftest.py` の `REAL_REPO_SERIAL_NODES` に s8c invariant node は無い。[conftest.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/conftest.py:170) 一方、activation report は commit blob と live `__file__` の bytes を比較する。[s8c_preregistration.py:1698](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1698)、[s8c_preregistration.py:1705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1705)

**成果物への影響** — certified 値自体は変わらないが、並行 writer との競合で `core-blob-mismatch` 等の偽赤が発生し、受入検査の通過集合が不安定になる。

**推奨対応**  
新 node を `REAL_REPO_SERIAL_NODES` または同等の real-repo xdist group に登録する。少なくとも「immutable blob だけを読むため安全」という説明は、live module bytes を読む実装と整合させる。

### B4 — digest 消費者は全件検索で見つかったが、new HEAD 用の再生成境界を明記すべき

**主張**  
`decider_version` と `decider_version_reason_code` の直接消費者は実質 preregistration 本体と synthetic test である。activation digest は複数 consumer が読むが、動的に capability から導出しており、g4 のためにコード修正が必要な箇所は見つからない。

**根拠**

全件検索:

```bash
git grep -l -I -e 'decider_version' -- . | sort
git grep -l -I -e 'decider_version_reason_code' -- . | sort
git grep -l -I -e 'activation_report_digest_sha256' -e 'report_digest_sha256' -e '_activation_report_digest' -- . | sort
rg -l -I --hidden --glob '!.git/**' --glob '!*.pyc' -e 'decider_version' -e 'decider_version_reason_code' -e 'activation_report_digest_sha256' -e 'report_digest_sha256' -e '_activation_report_digest' . | sort
```

production consumer は次のとおり。

- `orchestrator/campaign/autonomous_trial_completeness.py:80`、`:986`
- `orchestrator/campaign/reflux_origin_binding.py:155`、`:236`、`:259`
- `orchestrator/campaign/s8c_acceptance_receipt.py:38`、`:252`
- `orchestrator/campaign/trial_registry.py:1364`、`:2246`、`:2543`、`:2631`
- `orchestrator/campaign/s8c_preregistration.py:1932`、`:1962`

digest は dataclass 全体から導出される。[s8c_preregistration.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1932) g3 から g4 では少なくとも generation、protected hash、`decider_version`、match flag、reason code が変わる。

固定 digest は `test_reflux_originless_compatibility.py:234` と過去の `output/insights/2026-08-16_t1186-decider-version/` に存在するが、前者は synthetic repo の pre-wave baseline、後者は履歴 audit であり、現 HEAD の期待値ではない。現行の production receipt/golden が新 HEAD digest を固定しているものは全件検索で見つからなかった。

**成果物への影響** — 旧 commit に束縛された旧 report は維持できるが、新 commit を指す admission、lifecycle、acceptance receipt に旧 digest を入れると registry の exact 比較で拒否される。[trial_registry.py:2246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/trial_registry.py:2246)

**推奨対応**  
旧 historical golden は書き換えない。新 HEAD を参照して生成する report/admission だけを新 digest で再生成し、commit を明示的に束縛する。

### B5 — doc の規範は D458 と一致するが、bump 忘れを機械検出するようにも読める

**主張**  
提案文は D458 の要件を弱めてはいない。しかし実装は semantic change と version bump の対応を検査しないため、機械保証として読める余地がある。

**根拠**

提案文は `schema v2`、v1 legacy、判定器・評価器・射影の意味変更、format-only の非 bump を明記している。[s2-plan.md:57](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s2-plan.md:57)

実装が強制するのは、新規 record の v2/current version 書込み。[s8c_preregistration.py:1817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1817)、v2 の形式検査。[s8c_preregistration.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1072)、tip version の一致判定。[s8c_preregistration.py:1741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1741)

D458 は「bump 忘れは検出しない」と明記している。[docs/decisions.md:19139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/decisions.md:19139)

また brief の「変わるのは reason code の 1 点だけ」は dataclass 差分としては誤りである。[s1-brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/t1250-decider-version-generation/s1-brief.md:21) `ActivationReport` の複数 field と digest が変わる。[s8c_preregistration.py:1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1759)

**成果物への影響** — 「reason code だけが変わる」と記録すると、実際には変わる report digest、generation、protected hash を台帳や受入報告から落とす。

**推奨対応**  
doc に「bump 忘れは機械検出しない。版一致検査は、明示的 bump 後の旧 record 再利用だけを止める」と一文追加する。brief の不変条件は「effective は false のまま、版判定が unbound から match へ変わる」と書き換える。

### B6 — P4 の「g4 生成は実装面でない」は D95 と整合する

**主張**  
生成 JSON は D95 の実装面分類に入らず、test file の編集だけが Codex author 必須である。

**根拠**

D95 は `orchestrator/` 等の非 Markdown、Python、test、generator を実装面とする。[docs/decisions.md:4249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/decisions.md:4249)

provenance checker も implementation prefix/suffix を同じように定義している。[check_ai_provenance.py:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_ai_provenance.py:59)、[check_ai_provenance.py:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/check_ai_provenance.py:1215)

`output/...g4.json` は対象外だが、編集対象の `orchestrator/tests/test_s8c_preregistration_invariant.py` は対象である。

**成果物への影響** — nit。g4 bytes、certified 選択、受理集合、台帳値は P4 の分類だけでは変わらない。

**推奨対応**  
P4 は維持する。ただし test を含む commit には `AI-Agent: product=codex; ...; role=author` を付け、commit 後に `python3 tools/check_ai_provenance.py` を実行する。generator code に触れた場合は P4 を再判定する。

### B7 — P5 は「land 対象がない」という意味では正しいが、ledger の carry は残っている

**主張**  
T-324 の未着地 patch は見つからず、land target は stale である。一方、current worklog と archive には T-324 の carry と古い「同一 wave で land」記述が残る。

**根拠**

実行した全件 command:

```bash
for branch in worktree-dev-wave-t1132-t1134-prereg-contract \
  worktree-dev-wave-t1184-prereg-contract-revision \
  worktree-dev-wave-t324-8c-prereg; do
  git cherry main "$branch"
done

git log --all --oneline --decorate -- \
  output/s8c-preregistration/condition-freeze/condition-freeze.v1.g2.json \
  output/s8c-preregistration/condition-freeze/condition-freeze.v1.g3.json \
  docs/phase3-8c-preregistration.md
```

`git cherry` は全 branch で空。main には g2 の `d0fc008c`、g3 の `00e1ebdf` が既に存在する。branch tree でも main と t1184 は g1〜g3、t1132/t324 は g1〜g2 である。

archive には古い pending 文言がある。[worklog-phase3-0816-574.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/archive/worklog-phase3-0816-574.md:87) current worklog には T-324 carry が残る。[docs/worklog.md:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/worklog.md:144) また insight も「文書は既に main、land 対象外」と記録している。[brief.md:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/output/insights/2026-08-16_t1132-t1134-prereg-contract/brief.md:25)

**成果物への影響** — T-324 をこの wave で誤って完了扱いすると、worklog の active task 集合と履歴説明だけが変わり、certified 選択は変わらない。

**推奨対応**  
T-324 の land や新規 close を T-1250 に混ぜない。archive の記述は履歴として保持し、current carry の整理が必要なら別の worklog transition として扱う。

### B8 — stage 7 fragment は既存 T/D allocation と carry digest を踏みやすい

**主張**  
今回の fragment で新しい T/D を発行すると二重在籍になり、T-1250 を完了にする場合は carry stub ではなく実体 item の digest が必要である。

**根拠**

既に `FOLDED.md` に次が割り当て済み。

- `T:s8c-decider-version-generation -> [T-1250]`。[docs/spool/FOLDED.md:1400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/spool/FOLDED.md:1400)
- `D:s8c-decider-version-binding -> D458`。[docs/spool/FOLDED.md:1401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/spool/FOLDED.md:1401)

T-1250 の実体は archive entry にあり。[worklog-phase3-0816-600-601.md:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/archive/worklog-phase3-0816-600-601.md:508) current worklog の最新表示は carry stub である。[docs/worklog.md:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/worklog.md:2883)

spool 規則は carry 鎖の実体 digest を要求する。[docs/spool/worklog/README.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/spool/worklog/README.md:81)、[spool_fold.py:1775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/spool_fold.py:1775)

同じ symbol の再定義は `symbol-duplicate`、未定義 placeholder は `symbol-undefined` になる。[spool_fold.py:1241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/spool_fold.py:1241)、[spool_fold.py:1255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/tools/spool_fold.py:1255)

**成果物への影響** — base mismatch、二重 T/D、stale `tested_tip` があると fold が land lock 内で停止し、canonical ledger、受入記録、landed 状態は更新されない。

**推奨対応**  

- worklog fragment は既存の `[T-1250]` を操作し、base は archive の実体 item から作る。
- D458 は既存 D の参照として `D458` と書き、新しい decision fragment や `{{D:...}}` を作らない。
- fragment で canonical 3 台帳を直接編集しない。
- `check_docs` と `python3 tools/spool_fold.py --dry-run --show-diff` を、最終 tested tip で確認する。
- land は `dev_wave_land.py` の lock 内で行い、wave 側で fold しない。[operations.md:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/dev-wave/operations.md:146)

提案済み三ファイルの内容には、現時点で nonexistent D や fake path は見つからない。`D458` は実在し、`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json` も実装が使う実在 namespace である。

## 総括

### must-fix 候補

- B1: producer は一度だけ実行する必要があり、HEAD trap と `revision-exists` を手順へ明記する。
- B3: 新しい実 repo HEAD test の serial/group 登録漏れ。
- B4/B5: digest、generation、protected hash も変わることと、bump 忘れを検出しない限界を明記する。
- B8: 既存 T-1250/D458 allocation と carry 実体 digest を使う。

### scope 外の real 所見

- B6 の P4 判定は D95 と整合する。
- B7 の P5 は未着地 patch が無いという意味で正しいが、current ledger の T-324 carry は残っている。
- `output/README.md` は g4 と矛盾しない。
- historical digest golden と mutation ledger は書き換え対象ではない。
- pytest、check_docs、AI provenance は未実走であり、緑とは報告していない。