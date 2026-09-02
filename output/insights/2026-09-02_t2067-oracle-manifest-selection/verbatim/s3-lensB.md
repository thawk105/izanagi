## 所見 1 — historical reverify は選択 identity を実行せず、3 consumer は未被覆

**所見:** 親 brief の「`reverify_published_freeze` が `_launch_validate` を通るので report / verdict / oracle_judge は被覆済み」は反証できる。選択検査は `_launch_validate` 内でも `result_type is LaunchValidatedFreeze` の場合だけ実行され、`ReverifiedFreeze` を指定する historical reverify では明示的に飛ばされる。したがって `s8b_oracle_report`、`s8b_verdict`、`s8b_oracle_judge` も本 wave の裁定対象に戻す必要がある。

D1370 に沿う補正は、`reverify_published_freeze` 自体を変更するのではなく、各 consumer の `load_ratified_freeze` 直後に狭い公開 API を呼ぶ形である。report と judge を編集すると `generator_versions` の実 byte hash も変わるため、対応 test golden まで scope に含める必要がある。

**根拠 (file:line):** 選択検査の条件は [s8b_ratified_freeze.py:3303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3303)、historical 側の型指定は [s8b_ratified_freeze.py:3658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3658)。既存 test も earlier result を追加したまま reverify が成功することを明示している [test_s8b_ratified_verify.py:975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:975)。未被覆 consumer は [s8b_oracle_report.py:2547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_report.py:2547)、[s8b_verdict.py:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_verdict.py:828)、[s8b_oracle_judge.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_judge.py:749)。report と judge の source pin は [s8b_oracle_manifest.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:65)。

**成果物影響:** approved-spec 経路が有効な状態では、より早い適格 run を持つ g1 でも observations、oracle verdict、combined verdict が受理され、床値由来の値と freeze 参照が選択規則不適合のまま公開され得る。現状の production pin は `None` なので今この瞬間の official 出力集合は空だが、計画が主張する被覆は成立しない。

**must-fix か nit か:** **must-fix**

## 所見 2 — CLI は一意だが、module API と test helper には別の manifest 構築経路がある

**所見:** CLI の生成入口は `build-approved` だけであり、CLI bypass は見つからない。一方、production module は公開 `build_manifest(freeze_path=...)` と `write_manifest` を持ち、批准 loader や選択 gate を通さず `OfficialManifest` を構築、保存できる。repository 内の caller は test helper に限られるが、API 自体は private ではない。

これは lower builder に I/O gate を密輸せよという意味ではない。「supported production 生成面は `build_approved_manifest` だけで、`build_manifest` / `write_manifest` は fixture primitive」と境界を固定するか、別の選択済み構築 API を設けるかを裁定パッケージにする必要がある。

**根拠 (file:line):** raw freeze builder は [s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:818)、保存 API は [s8b_oracle_manifest.py:902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:902)。`OfficialManifest` は provenance 証明ではない marker と明記される [s8b_oracle_artifacts.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_artifacts.py:61)。代表的な test helper は [test_s8b_oracle_manifest.py:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:159) と [test_s8b_oracle_driver.py:2288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_driver.py:2288)。CLI parser は [s8b_oracle_manifest.py:1263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1263)。`build_manifest_from_ratified` の repository 内 production caller が `build_approved_manifest` だけという親の個別主張は支持される [s8b_oracle_manifest.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:842)、[同:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1244)。

**成果物影響:** in-process caller は選択 gate を通らない official marker と freeze path/hash 参照を生成できる。現状の launch driver は後段で選択検査するが、所見 1 の report / verdict 系はその manifest を選択未検査のまま消費し得る。

**must-fix か nit か:** **must-fix**

## 所見 3 — 4 test の g2 化は新しい g2 選択規則ではないが、実在不能 fixture と g1 成功被覆を残す

**所見:** D1325 との文言上の判定は「新しい g2 挙動の定義ではなく、D1370 が既に決めた非 g1 no-op をなぞる」でよい。ただし test 証拠としては不十分である。

合成 document は実際には v2 世代文書ではなく、legacy v1 文書へ `floor` と `budget` だけを追加したものだ。dataclass の `generation_number` だけを 2 にすると、選択 helper は document を読む前に return し、builder はその数字から `holdout_freeze.v2.g2.json` を組み立てる。実 loader が要求する v2 exact schema、本文の generation number、世代連鎖、approval/pointer pairing は一切通らない。

さらに成功する既存 2 test を g2 に移し、追加する genuine g1 2 test は両方 output 作成前に終了するため、g1 が選択 gate 通過後に manifest を最後まで構築し、`holdout_freeze.v2.g1.json` を参照し、再検証される成功被覆がゼロになる。

**根拠 (file:line):** plan の g2 化は [plan.md:91](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:91) と [plan.md:98](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:98)。fixture は v1 を読み [test_s8b_oracle_manifest.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:272)、`fill` は 2 field しか変更しない [s8b_v2_freeze_fixture.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/s8b_v2_freeze_fixture.py:61)。real loader の exact schemaと本文番号検査は [s8b_ratified_freeze.py:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:897)。早期 return は [s8b_ratified_freeze.py:3567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3567)。`freeze_rel` の組立ては [s8b_oracle_manifest.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:849)。`verify_manifest` は freeze path を再読込せず supplied document/hash だけを使う [s8b_oracle_manifest.py:1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1024)。追加 g1 正例も `no-approved-spec` で output 無しとする計画である [plan.md:110](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:110)。

**成果物影響:** g1 の選択検査だけが成功しても、manifest の生成失敗や誤った g1 freeze 参照を検出できず、candidate bytes とその参照を壊す回帰が test green のまま残り得る。また合成 g2 成功は、real loader では成立しない受理集合を test 上だけ作る。

**must-fix か nit か:** **must-fix**

## 所見 4 — 提案された個別 gate 自体は D1370、D1325、D1313 の境界内

**所見:** `build_approved_manifest` の load 直後に狭い API を呼ぶ部分自体は、`launch_validate`、activation HEAD、current build admission、closure、binding graph、live scan、certificate、起動秒を持ち込まない。失敗理由も既存 3 reason の passthrough で、新造されない。test 名も「actual selection gate」「rule mismatch」であり、certifying や実時間順の証明とは表現していない。

`VerifiedManifest` の既存 docstring も provenance 証明ではないことを明記しており、plan はこれを解除していない。所見 1 の補正でも、historical reverify に gate を埋め込まず各 consumer で狭い API を呼ぶ限り同じ境界を維持できる。

**根拠 (file:line):** 提案コードは [plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/plan.md:17)、D1370 は [rulings-verbatim.md:40](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:40)、D1325 は [同:22](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:22)、D1313 は [同:3](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:3)。非証明 token の説明は [s8b_oracle_manifest.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:98)。

**成果物影響:** この境界に関する追加の値、受理集合、参照変更はない。advisory / non-certifying 上限も文言上は維持される。

**must-fix か nit か:** **nit**

## 所見 5 — driver:496 は production 到達する load-only 入口ではなく、C06 は既裁定で除外済み

**所見:** repository 全体の production 参照では、driver:496 は private `_gate_check_core` を直接呼ぶ test 以外から選択未検査の v2 成功経路にならない。public `gate_check` の v2 は line 644 で load 後、必ず line 664 の `launch_validate` へ進む。`run_block` も同じ順序である。

別の実 load-only 入口として `p3_autonomous_workload_trial` の C06 予算経路は存在するが、これは D1371 が明示的に現時点の実装対象外としたものなので、本 wave へ戻すべきではない。

**根拠 (file:line):** private core の load は [s8b_oracle_driver.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:493)。public v2 経路は [同:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:641) と [同:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:663)、run-block は [同:1332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:1332)。C06 load は [p3_autonomous_workload_trial.py:4710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/p3_autonomous_workload_trial.py:4710)、除外裁定は [rulings-verbatim.md:85](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:85)。

**成果物影響:** driver:496 を本 wave で変更しなくても production の manifest、report、ledger の受理集合は変わらない。C06 も既裁定どおり現状では成果物集合が空である。

**must-fix か nit か:** **nit**

## 所見 6 — 編集予定 file は全て W-d 所有だが、これは将来計画であって現行 lock ではない

**所見:** plan の production/test 2 file は双方とも W-d に割り当てられている。所見 1で必要になる report、verdict、judge と各 test も同じ W-d 所有であるため、将来の W-d wave とは衝突し得る。

ただし文書は「第2設計段パッケージ、未了」と明記し、W-c にも未充足の開始条件があり、W-d の predicate 順は「W-d 開始時」に決めるとしている。したがってこれは将来の exact ownership plan であり、現行 T-2067 を止める active file lock とは読めない。

**根拠 (file:line):** 文書状態は [freeze-permanent-design-s2.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:1)。manifest と test の割当は [同:2522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2522) と [同:2541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2541)。追加候補群は [同:2525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2525) から [同:2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2548)。W-d 開始時の確定事項は [同:2620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2620)、W-c 開始条件は [同:2942](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/docs/freeze-permanent-design-s2.md:2942)。

**成果物影響:** 現時点の成果物値、受理集合、参照には影響しない。将来 W-d と並行編集すれば、gate または対応 test の上書き衝突が起こり得る。

**must-fix か nit か:** **nit**

## 総括

must-fix は **3件**。反証できた親実測は、`reverify_published_freeze` による report / verdict / oracle_judge の選択被覆と、それを前提にした「未被覆 load-only 入口は build_approved_manifest 1箇所」の2点である。`build_manifest_from_ratified` の production caller が1件であることと、manifest module 自身が generator pin に含まれないことは支持される。書き込み、pytest 実走は行っていない。