### S1

**主張:** 受入全走で差分により赤化しうる既存 nodeid を全件検索した。静的に影響入力が変わる既存 node は次の10件だが、現差分で赤になる条件は見つからず、**期待赤集合は空**である。

- `test_s8c_preregistration_core.py::test_current_markdown_extracts_nine_fields_and_conditions_1_to_12`
- `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
- `test_s8c_preregistration_invariant.py::test_candidate_commit_observes_uncommitted_worktree_delta`
- `test_s8c_preregistration_invariant.py::test_candidate_is_not_effective_and_has_zero_satisfied_predicates`
- `test_s8c_preregistration_invariant.py::test_wave_files_do_not_contaminate_production_holdout_scan`
- `test_s8c_preregistration_invariant.py::test_s8c_living_doc_reference_negative_controls`
- `test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`
- `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries`

**根拠:** `orchestrator/tests/test_s8c_preregistration_core.py:434-441`、`orchestrator/tests/test_s8c_preregistration_invariant.py:125-159,242-306,336-358`、`orchestrator/tests/test_s8b_repo_scan_invariant.py:27-35`、`orchestrator/tests/test_real_repo_serialization.py:724-737`、`orchestrator/tests/test_plain_runner_coverage.py:60-86`。

使用した全件検索 command。いずれも `head` で切っていない。

```bash
rg -n --glob '*.py' 'SOURCE_PATH|FREEZE_DIR|generation_path|condition-freeze|holdout_conjunction_hits|search_repository|enumerate_repository_files|LIVING_DOCS|FROZEN_MANIFEST|repository_candidate_commit|s8c-preregistration-candidate|test_s8c_preregistration_invariant\.py' orchestrator/tests tools

rg -n --glob '*.py' 'collect|nodeid|test_\*\.py|xdist_group|REAL_REPO_SERIAL_NODES|PYTEST_ONLY_ALLOWLIST|FROZEN_MANIFEST|KNOWN_CONJUNCTION_HITS' orchestrator/tests tools

rg -n '^def test_|_XDIST_GROUP_NAMES_GOLDEN|_REAL_REPO_SERIAL_NODES_GOLDEN|fixture_closure|allowlist|ALLOWLIST|test_s8c_preregistration_invariant' \
  orchestrator/tests/test_real_repo_serialization.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_pytest_collection_config.py \
  orchestrator/tests/README.md
```

`test_repository_legacy_v1_generations_remain_readable[1]`、`[2]`、`[3]` は parametrize が `(1, 2, 3)` のままで、g4を読まないため除外した。`FROZEN_MANIFEST` 族も明示23件だけを読むので除外した。

**成果物への影響:** 静的に既存 node の期待値変更は不要だが、未実走なので受入結果の代替にはならない。

**推奨対応:** 上記10件、新設2件、指定meta-testを焦点走に含め、既存期待値は変更しない。

---

### S2

**主張:** 新設2関数による collection、xdist group、fixture scope の不整合は見つからない。`repository_candidate_commit` の consumer は3件から4件へ増えるが、全consumerが同じ既存groupに入り、worker内でsession fixtureは1回だけ生成される。

**根拠:** fixtureは `orchestrator/tests/test_s8c_preregistration_invariant.py:119-122`。consumerとmarkerは同ファイル `125-127,164-167,269-272,285-288`。group名は既存goldenに登録済みである `orchestrator/tests/test_real_repo_serialization.py:113-118`。meta-testはgroup名集合とmarker形を検査するだけで、candidate node名のgoldenは持たない `同:523-552,724-737`。新設第2関数はfixtureを消費せず、AST走査ではテスト関数11件、重複0件だった。

`REAL_REPO_SERIAL_NODES` は別のcanonical集合であり、candidate fixtureはそのclosure seedではない `test_real_repo_serialization.py:586-620`。既存ファイルはpytest-only allowlist登録済み `orchestrator/tests/README.md:174-177`。

**成果物への影響:** candidate commitの生成回数は増えず、同groupの実行時間だけが1 node分増える。

**推奨対応:** `REAL_REPO_SERIAL_NODES`、group golden、allowlistへ追加しない。collection meta-testを実走して最終確認する。

---

### S3

**主張:** doc追記は現行`check_docs`規則を通る。D参照、code span、行番号、path、行長、byte予算、exact section pinのいずれにも違反はない。

**根拠:**

- phase docはliving docに列挙済み: `tools/check_docs.py:47-64`
- D参照は `\bD(\d{1,3})\b`: `tools/check_docs.py:838`
- D458実体: `docs/decisions.md:19099`
- living doc検査: `tools/check_docs.py:5258-5324`
- strict行番号規則: `tools/check_docs.py:89-97`
- phase docにはbyte・行長予算登録がなく、予算対象はcommand/self/tools/provenance族: `tools/check_docs.py:173-207`
- 追記は729 bytes、全体は36,786から37,515 bytes。追記最長は65文字、127 UTF-8 bytes。
- `` `DECIDER_VERSION` `` を検査する一般的なcode-span規則はなく、追加文にpath参照や行番号参照もない。
- `rg -n 'phase3-8c' tools/check_docs.py` ではliving doc登録以外のexact section pinはなかった。
- 実行済み: `python3 -B tools/check_docs.py` はrc=0、`check_docs: 違反なし`。

**成果物への影響:** normative/protected hashだけが意図どおり更新され、§5・§6条件hashは維持される。

**推奨対応:** doc修正不要。commit後にも正規手順で`tools/check_docs.py`を再実行する。

---

### S4

**主張:** g4 JSONはnamespace、gitignore、canonical record、連鎖、holdout scan、placeholder検出の各面で適合している。`FROZEN_MANIFEST`へは追加してはならない。

**根拠:**

- namespace正規表現: `orchestrator/campaign/s8c_preregistration.py:41-59`
- history全pathのclosed namespace検査: `同:1181-1191`
- output正本の命名規則: `output/README.md:23-24`
- canonical key・schema・版・reason・ruling検査: `s8c_preregistration.py:1060-1112`
- `revision_reason` は非空かつ前後空白なしだけを検査する。`_PLACEHOLDER_RE` はfreeze reasonへ適用されない。
- `git check-ignore -v -- <g4>` はrc=1で非ignore、`git ls-files --others --exclude-standard`はg4を列挙した。
- 発行済み外部g4とworktree g4は`cmp -s`で一致。
- g3 SHA-256はg4の`supersedes_sha256`と同じ`2b28cde3...c2f23e1`。
- 読み取り専用比較でcanonical v2、decider、全hash、D458、g3連鎖の12項目がすべて一致した。
- 変更3ファイル限定scanとrepo全scanはいずれも`rr80=[]`, `rr20=[]`。g4も列挙対象だった。
- `FROZEN_MANIFEST`は独立した23件の明示集合で、新規output全体を列挙しない `orchestrator/tests/test_frozen_artifacts.py:41-150,234-247`。

**成果物への影響:** 新しいimmutable g4が1件増えるだけで、既存s8b frozen artifactや既知hit台帳は変わらない。

**推奨対応:** g4をそのままtrackedにし、`FROZEN_MANIFEST`、既知hit台帳、`.gitignore`は変更しない。

---

### S5

**主張:** 段7 fragmentでは既存`[T-1250]`を`完了`しなければならない。新しい`{{T:...}}`を作るとT-1250が残り、二重タスク化する。指定されたbase digestは正しい。

**根拠:**

- T-1250の既存allocation: `docs/spool/FOLDED.md:1400`
- 実体item: `docs/archive/worklog-phase3-0816-600-601.md:508-512`
- carry解決はstubを遡り、最初の実体blockをdigest化する: `tools/spool_fold.py:1536-1596`
- digestは末尾LFを1個へ正規化したitem全体のSHA-256: `同:535-538`
- base照合と停止: `同:1774-1777`
- 実行したcommand:

```bash
sed -n '508,512p' docs/archive/worklog-phase3-0816-600-601.md | sha256sum
```

結果は親計算と一致する。

```text
63604b218710c8df0f56cc0bd88da98ec3fd365d7ae5fe6f60a4fabb60e15583
```

fragmentでは少なくとも次の形が必要である。

```markdown
### 完了

- [T-1250] ...
  remaining: none
  base: 63604b218710c8df0f56cc0bd88da98ec3fd365d7ae5fe6f60a4fabb60e15583
```

`remaining`と`base`の要件は `docs/spool/worklog/README.md:64-85`。repo内参照として使える実在pathは、phase doc、テストファイル、g4の3件で、D458も実在する。

**成果物への影響:** placeholderまたはbaseを誤るとfoldが停止し、段9は`landed`を返さない。

**推奨対応:** `[T-1250]`の`完了`だけを書き、fragment commit前に`check_docs`と`spool_fold.py --dry-run --show-diff`を実行する。wave側でfoldしない。

---

### S6

**主張:** このcommitはdocs-onlyではない。テスト`.py`が実装面と判定されるため、Codex `role=author` trailerが必須である。

**根拠:** 実装面suffixに`.py`が含まれる `tools/check_ai_provenance.py:59-69`。path判定本体は `同:1215-1229`、Codex author要求は `同:1231-1261`。実コードでの分類結果は次のとおり。

```text
docs/phase3-8c-preregistration.md                                      False
output/s8c-preregistration/condition-freeze/condition-freeze.v1.g4.json False
orchestrator/tests/test_s8c_preregistration_invariant.py               True
```

最低限必要な物理行の形は次である。値は実際のauthor session表示から記録し、推測しない。

```text
AI-Agent: product=codex; model=<actual-slug>; reasoning=<actual-value>; role=author
```

最終trailer blockに置き、本文との間に空行が必要 `docs/ai-provenance.md:11-35`。同じroleの行を複数置く場合は各行に`scope=`が必要。docs/g4へ実質寄与した別AIがいる場合も、その実際のroleを別行で記録する。

**成果物への影響:** Codex author行がなければfull-history provenance監査が赤になり、landは`RC_PROVENANCE=29`でmainを変更せず拒否する。

**推奨対応:** message-fileで事前検査し、そのmessageでcommit後、`python3 tools/check_ai_provenance.py`の全史監査を実行する。

---

### S7

**主張:** 現時点の確定したland blockerは、pytest・変異・受入全走が未実走で、有効なacceptance receiptがないこと。

**根拠:** 実装報告は投入がdispatch `rc=16`で止まり、1 nodeも実行されていないと明記している `s5-author.md:45-60`。dev-wave契約は段6で変異matrixと受入再走を要求する `.claude/commands/dev-wave.md:50-54`。landはacceptance receiptを必須引数とし `tools/dev_wave_land.py:70-96,130-138,3369-3389`、tip・runner・verdictを検証して不適合なら`acceptance-receipt-rejected`、`RC_AUDIT=23`となる `同:529-756,3023-3029`。

本レビューで実行したのは`check_docs`、静的AST、hash/JSON比較、holdout scanだけであり、pytestを緑とは判定していない。

**成果物への影響:** 正規acceptance receiptなしでは段9 landを機械的に通せない。

**推奨対応:** commit後の固定tipで新設2 node、上記既存影響node、collection meta、M01からM05、受入全走、`check_codex_agents.py`、`check_docs.py`、provenance監査を正規runner経由で完了する。

## 総括

**must-fix**

- S5: 段7は新規Tを作らず、`[T-1250]`を正しいbase digestで完了する。
- S6: commitに実値を使ったCodex `role=author` trailerを付ける。
- S7: pytest・変異・受入全走を実行し、固定tipへ有効なacceptance receiptを発行する。

**nit**

- なし。collection、doc、g4、holdout、namespace、`FROZEN_MANIFEST`について静的な修正要求はない。