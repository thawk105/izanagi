結論として、(P1) の方向は正しいものの、g1〜g3 が版を持たない legacy v1 であるため、対象を「新たに発行する世代 record」に限定した代案がより正確です。実装順は doc を未 commit で編集し、その状態で g4 を生成し、テストを加え、3 ファイルを一括 commit とします。

## 1. 実行順序

以下の行番号は変更前 HEAD 基準です。

1. doc を編集する

   - 前提: HEAD は g1〜g3 だけを持ち、g4 が存在しないこと。現行 SHA-256 は g1=`a8fe5246…3419`、g2=`d3c6a3de…4225`、g3=`2b28cde3…23e1`。
   - [phase3-8c-preregistration.md:244-250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:244) を、後述の差分どおり編集する。まだ commit しない。
   - doc 編集前に producer を実行すると、worktree contract と HEAD の protected hash が同じなので [s8c_preregistration.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1889) の `spurious-revision` になる。

2. 親が g4 を生成する

   ```bash
   python3 -m orchestrator.campaign.s8c_preregistration prepare-revision \
     --ruling-reference D458 \
     --revision-reason 'T-1250 (D458): 世代 record へ判定器の版を束縛する — 改訂手続きに版 bump 規範を追加し、schema v2 の第 4 世代を発行する'
   ```

   非対称性は次のとおりです。

   - `commit` の既定値は `HEAD` ([s8c_preregistration.py:1837-1846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1837))。
   - 世代数は resolved HEAD の `ls-tree` から数えるため、g1〜g3を見て次を g4 とする (`:1849-1862`)。
   - `supersedes_sha256` も HEAD の妥当な g3 bytes から作る (`:1873-1879`)。期待値は `2b28cde32feaa4509ff6c8cfe382240d7b4d2d8f919608a6199f2b282c2f23e1`。
   - 一方、新 record の contract は worktree の doc と evidence contract から作る (`:1882-1887`)。
   - `_record_document` は schema v2 と現在の `DECIDER_VERSION` を書く (`:1808-1834`)。
   - g4 は exclusive-create され、再実行は `revision-exists` になる (`:1900-1907`)。

   したがって必要な状態は「HEAD は妥当な g3、worktree の doc は次契約」です。doc だけ先に commit すると、HEAD の g3 と新 doc が不一致になり、`prepare_revision()` 内の `validate_condition_freeze_at()` (`:1875`) が `record-protected-mismatch` で止まります。逆に g4 生成後に doc を再編集すると、g4 の hash が即座に陳腐化します。

3. Codex author がテストだけを新設する

   - [test_s8c_preregistration_invariant.py:126-170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:126) の real-repo invariant 族へ、後述の 1 関数だけを追加する。
   - テスト編集は producer の入力ではありませんが、g4 を実物として確認してから author に渡す順序にします。
   - 新テストは明示的に `HEAD` を読むため、commit 前は意図的に g3 を見て失敗します。pre-commit の複合 tree は既存の candidate fixture (`:77-101`) と `test_candidate_freeze_matches_contract_and_generation_chain` で確認し、新テストを skip や xfail にしてはいけません。

4. 親が 1 commit にまとめる

   同じ commit に最低限、次の 3 ファイルを含めます。

   - `docs/phase3-8c-preregistration.md`
   - `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json`
   - `orchestrator/tests/test_s8c_preregistration_invariant.py`

   doc だけ、または g4 だけの中間 commit を作ってはいけません。[doc:244-250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/docs/phase3-8c-preregistration.md:244) 自身が同一 commit を要求し、履歴 validator も record と contract の同時一致を要求します。D458 の存在は g4 導入 commit の `docs/decisions.md` blobで検査されます ([s8c_preregistration.py:1381-1403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1381), `:1498-1506`)。

   新しい HEAD 専用テストと受入検査は、この commit 後に親が `tools/run_tests.py` 経由で実走します。

## 2. doc 追記の正確な差分

挿入位置は現行 `docs/phase3-8c-preregistration.md:246` の直後、`:247` の「無記録の変更」の直前です。空行を入れず、同じ「改訂手続き」段落へ次を挿入します。

```diff
 世代 record は
 直前世代の bytes hash・変更理由・**裁定の参照** (`docs/decisions.md` の決定見出し) を持つ。
+新たに発行する世代 record は schema v2 とし、判定器の版 (`DECIDER_VERSION`) を持つ。既存の
+schema v1 record は版を持たない legacy として改変せずに残す。判定器・評価器・射影のいずれかで
+受理集合・拒否理由・射影された判定入力の意味を変える変更は、`DECIDER_VERSION` を bump し、
+その版を持つ新世代の record を発行しなければならない。整形など意味不変の変更では bump しない。
 無記録の変更、記録のない差し戻し、
```

(P1) からの改善点は、最初の文を legacy-aware にしたことです。現行 loader は schema v1 を `decider_version=None` として読む ([s8c_preregistration.py:1053-1063](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1053)) うえ、既存 real-repo test も g1〜g3についてそれを固定しています ([test_s8c_preregistration_invariant.py:164-169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:164))。したがって (P1) の無限定な「世代 record は版を持つ」は履歴に対して偽になります。

保護 hash への包含は次の経路で保証されます。

- `NORMALIZATION_VERSION` は `s8c-prereg-markdown/v2` ([s8c_preregistration.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:53))。
- `_section_bounds()` は H2 の §6 から次の H2 §7 までを取るため、配下の H3 と改訂手続き本文も範囲内です (`:681-715`)。
- `parse_preregistration_markdown()` は §1・2・3・4・6・7 を `normative_sections` に入れます (`:896-904`)。
- plain paragraph の文字列は `_normalize_fragment()` の paragraph node に残ります (`:585-678`)。code span の装飾は落ちても `DECIDER_VERSION` という内容自体は残ります (`:538-564`)。
- 追記は §0、§5 の値、HTML comment、fence 内ではありません。HTML comment を含む raw HTML はそもそも拒否されます (`:497-535`)。

この正確な代案をメモリ上で parser に通した静的確認では、次の差になりました。

- `normative_body_sha256`: `1d143e24…1746` → `19ab798d…276e9`
- `protected_sha256`: `5c7e32c9…ae14` → `fea3a889…fcc3`
- §5 欄名 hash: 不変
- §6 条件 1〜12 hash: 不変

したがって `spurious-revision` 例外は不要で、既存規則をそのまま通せます。

## 3. 新設テストの署名と内容

挿入位置は現行 `test_candidate_freeze_matches_contract_and_generation_chain` の後、legacy parameter test の前、現在の `test_s8c_preregistration_invariant.py:163` 付近です。

```python
def test_repository_tip_binds_current_decider_version_without_activation() -> None:
    report = prereg.activation_report_at(ROOT, "HEAD")
    assert report.condition_freeze_valid is True
    assert report.freeze_generation is not None

    tip_raw = prereg.read_blob_at(
        ROOT,
        report.commit,
        prereg.generation_path(report.freeze_generation),
    )
    assert tip_raw is not None
    tip = json.loads(tip_raw)

    assert tip["schema_version"] == prereg.SCHEMA_VERSION
    assert tip["decider_version"] == prereg.DECIDER_VERSION
    assert report.decider_version == prereg.DECIDER_VERSION
    assert report.decider_version_matches is True
    assert report.decider_version_reason_code == "decider-version-match"
    assert report.effective is False
```

`effective is False` は入れることを推奨します。

- 利点: 「版を束縛したが本 wave では発効させない」という wave 固有の不変条件を、実 HEAD に対して同じ関数内で固定できます。
- 重複: candidate tree の false と全 12 predicate 非充足は既存 `test_candidate_is_not_effective_and_has_zero_satisfied_predicates` (`:199-212`) が既に検査します。合成 repo でも一致・不一致・legacy・全 conjunction が [core test:1998-2139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_core.py:1998) にあります。
- それでも必要な理由: 既存被覆には「着地済み HEAD の tip が v2 かつ現行版と一致し、それでも未発効」という 1 点の結合検査がありません。将来の正規の発効 wave は既存 candidate false assert も既に改訂対象になるため、新たな将来負債もほぼ増えません。

登録面は次の扱いです。

- 新しい test file ではないため、file 集合 meta-testへの追加は不要です。既に `orchestrator/tests/README.md:176` の pytest-only allowlist にあり、`test_plain_runner_coverage.py:44-86` がそれを検査しています。
- `WAVE_REQUIRED_PATHS` にも同 file は既登録です (`test_s8c_preregistration_invariant.py:30-40`)。
- `REAL_REPO_SERIAL_NODES` と独立 golden への登録は不要です。新テストは HEAD の immutable blob を読むだけで、親 worktree や共有 CCBench の writer ではありません。既存 legacy real-repo test も unmarked です。
- `s8c-preregistration-candidate` group も不要です。candidate fixture を消費せず、HEAD を明示的に検査するためです。

なお「`ActivationReport` で変わってよい field は reason code だけ」を字義どおりの dataclass 差分としては固定できません。g3→g4 では必然的に `freeze_generation`、`protected_sha256`、`decider_version`、`decider_version_matches` も変わります ([s8c_preregistration.py:1759-1767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:1759))。制約は「発効の結論は false のまま、版判定の理由が match へ移る」という意味で解釈する必要があります。全 field のうち reason だけ、という意味なら wave の成果物と両立しません。

## 4. 回帰の危険

静的に直接波及する既存 nodeid は次です。

| nodeid | 赤になる条件 |
|---|---|
| `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain` | doc/g4 の hash 不一致、世代 gap、bad supersedes、D458 不在、別 commit 化 |
| `test_s8c_preregistration_invariant.py::test_repository_legacy_v1_generations_remain_readable[1]`〜`[3]` | g1〜g3 の bytes/schema を改変した場合 |
| `test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates` | 本 wave が誤って発効側へ倒した場合 |
| `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan` | doc または g4 の理由文が holdout 三軸 conjunction を作った場合 |
| `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control` | 同じく repository 全体の既知 hit 集合を増やした場合 |
| `test_s8c_preregistration_core.py::test_current_markdown_extracts_nine_fields_and_conditions_1_to_12` | Markdown 構造を壊した場合 |
| `test_s8c_preregistration_core.py::test_generation_added_without_protected_change_is_spurious` | 禁止された `spurious-revision` 例外を入れた場合 |
| `test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract` | living-doc lint 違反 |
| `test_check_docs.py::test_normative_exact_section_pins_accept_real_repo` | 同上 |
| `test_check_docs.py::test_real_repo_clean` | 同上 |

最後の check_docs 3 node は既定では growth hold 対象ですが、親の直接 `python3 tools/check_docs.py` は省略できません。今回の追記には docs 間行番号参照、実在しない path、placeholder、command 予算面の変更はありません。

個別判断は次のとおりです。

- `test_candidate_freeze_matches_contract_and_generation_chain`: 最重要の pre-commit candidate 検査。新 HEAD test の代替ではなく、commit 前に複合 tree を検査する役割です。
- `test_repository_legacy_v1_generations_remain_readable`: param は `(1, 2, 3)` のままです。g4 を加えると「legacy v1 族」という意味が壊れます。
- g1〜g3 bytes: テストだけでなく、親が上記 3 SHA-256 を生成前後・commit 後に比較すべきです。
- `output/README.md:24`: 変更不要です。`g<N>` の namespace 説明と前世代 hash・理由・裁定参照は v2 でも真で、field の完全列挙とは書いていません。「全 record が版を持つ」と追記すると g1〜g3 に対して偽になります。必要なら将来「新規 schema v2 は版も持つ」と限定する別 docs 改訂にします。
- `GIT_TIMEOUT_CAP_SECONDS`: [s8c_preregistration.py:107-116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/campaign/s8c_preregistration.py:107) の再較正条件は、実は base の g3 ですでに成立しています。元の計測正本も「g2 以上」を再較正条件としています。g4 が初めて発火させる条件ではなく、既存の未処理債務です。
  - 本 wave では no-touch module 内のコメント・定数・テスト期待値を変更しません。
  - `test_git_timeout_budget_constants_match_preregistered_measurement` (`core.py:2642-2649`) の期待値も変えません。
  - 親はこの wave が再較正を済ませたとは記録せず、計算ノードで行う別の再較正 follow-up として残すべきです。candidate invariant が `git-timeout` になった場合は再試行や timeout 緩和で隠してはいけません。

pytest は実走していません。read-only sandbox に writable temp がなく、`activation_report_at()` の直接実行も完了できませんでした。上記 hash 差だけはファイルを書かず Markdown parser をメモリ上で適用して確認しています。

## 5. 変異事前登録の候補

重要な実行上の注意があります。新テストは `HEAD` を読むため、通常の `mutation_harness.py` が行う「HEAD を固定したまま worktree だけを変異」では artifact 変異が新テストから見えません (`tools/mutation_harness.py:943-980`, `:1747-1815`)。以下は、統合 commit の親を親に持つ「兄弟 mutant commit」を隔離 worktree に作り、その mutant を HEAD として実行する必要があります。統合 commit の子で g4 を改変すると `generation-mutated` が先に発火し、狙った単一理由性が失われます。

| 変異内容 | 静的に期待する KILL node |
|---|---|
| wave 前の実装面へ戻す: doc 追記を戻し、g4 を除去して tip=g3/schema v1/unbound とする。新テストは残す | 新設 `test_repository_tip_binds_current_decider_version_without_activation` のみ |
| doc は新しいまま、g4 を canonical schema v1 にし `decider_version` key を除く | 新設 node のみ。freeze chain 自体は妥当だが schema assert が殺す |
| g4 の `decider_version` だけを `s8c-decider/v2` にする。`DECIDER_VERSION` は変更しない | 新設 node のみ。record は構造上妥当だが version/assert と mismatch reason が殺す |
| doc の追記中の意味語を 1 語変更し、g4 を再生成しない | 新設 node、および `test_candidate_freeze_matches_contract_and_generation_chain` |
| g4 の `supersedes_sha256` を g3 hash から g2 hash へ変える | 新設 node、および `test_candidate_freeze_matches_contract_and_generation_chain` |

段 6 の実測で追加 failure node が出た場合は、上表を完全集合として扱わず probe 結果で再登録してください。未 commit worktree 変異のまま新 HEAD test が通っても、それは SURVIVED ではなく変異が観測面へ届いていない無効試験です。

## 総括

- 骨子は「doc を未 commit で編集 → 親が g4 を exclusive-create → author が real-HEAD test を追加 → 3 ファイルを単一 commit」です。
- g1〜g3、判定器 3 module、`DECIDER_VERSION`、`spurious-revision` は変更しません。
- 親が裁定すべき択一:
  - doc 文言は、legacy v1 と矛盾する (P1) 原文ではなく、本稿の schema v1/v2 を区別した代案を推奨します。
  - 新テストの `effective is False` assert は入れることを推奨します。
  - 「reason code だけが変わる」は全 dataclass field の差分ではなく、発効結論に関する制約として明示的に解釈する必要があります。
- g2 以上での git timeout 再較正は既に発火済みの別債務です。本 wave でコメントや定数を触らず、親が別 follow-up へ送るのが適切です。