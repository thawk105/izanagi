U-E2 をコード・テストの2ファイルに実装しました。commit および docs 編集はしていません。pytest は実行基盤障害により未実走のため、完了を `closed` とは申告しません。

### 実装内容

- [erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:24)
  - registered / approved / draft ID を型で分離。
  - `DRAFT_ERRATA = {"t139-core-s7-stresscheck-v1"}` を追加。
  - approved/draft が非重複かつ registry を完全被覆する検査を追加。
  - `t139-core-s7-stresscheck-v1` 固有 validator を登録。
  - operation 数1、対象語句1件とlocator一致、行SHA/old_text一致、新旧とも1行を検査。
  - 第1 erratum 固有の2 operations・a12→a13差分検査は流用していません。
  - 未知IDの拒否点を一意化し、M6を単一理由で検出可能にしました。

- [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:388)
  - M1〜M6の指定nodeを追加・改名。
  - 行数不変、対象語句とlocatorの束縛、実core 221行SHAを追加検査。
  - locator `{404, 424}` と `{221}` の非重複を固定。
  - 実際に計算した2件合成digestを固定：
    `dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c`
  - 第1 erratum単独digest
    `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82`
    とは異なることを検査。

gate API 4名は実装・exportしていません。`test_module_exports_no_admission_api` は変更せず維持しています。

### 検査結果

成功した静的・標準検査：

- AST parse、module import、`git diff --check`: rc=0
- 実core＋両erratumを通したproduction合成smoke: rc=0、上記digestを再現
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

pytestはすべて標準runner経由で試行しましたが、`qstat -Q preflight rc=1` により runner `rc=16` で停止しました。pytest collection自体は開始していません。

- M1〜M6、行数、実合成、非exportの計10 node
- 対象ファイル全体
- meta-test:
  - `orchestrator/tests/test_plain_runner_coverage.py`
  - `orchestrator/tests/test_pytest_collection_config.py`

したがって、これらはすべて「実装済み・未実走」です。親の受入全走も未実施です。

### M1〜M6の単一理由性

静的確認では欠落nodeはありません。

| 変異 | 対応node | 単一理由 |
|---|---|---|
| M1 | `test_s7_erratum_rejects_operation_count_not_one` | 他条件を満たす2 operations |
| M2 | `test_s7_erratum_rejects_old_sha256_mismatch` | SHAだけ不一致 |
| M3 | `test_s7_erratum_rejects_occurrence_count_not_one` | operation行を含む対象語句2件 |
| M4 | `test_draft_erratum_is_not_in_approved_set` | registered draftの承認混入だけを検査 |
| M5 | `test_overlapping_locators_rejected` | 両固有validatorと合成digestは成立し、locatorだけ重複 |
| M6 | `test_unknown_erratum_id_fails_closed` | 構造・第1validator・合成digestは成立し、IDだけ未知 |

ただしmutation harnessの実走は、同じrunner障害のため未実施です。

### 所有外への波及可能性

- `orchestrator.preregistration.__init__` が既にexportする `parse_erratum` / `compose_core` は、第2 erratumをregistered文書として検証・機械合成できるようになります。
- 承認問い合わせはdraftを返しません。`compose_core` 自体は引き続き非admissionの純粋な合成部品です。
- repo内のproduction callerは `__init__.py` の再export以外に見つかりませんでした。
- 共有fixture・consumer testは同じT-139テストファイルのみです。
- 所有外の未追跡 `docs/spool/...` と `output/insights/...` には触れていません。

## 総括

U-E2の実装、期待digestの実計算、M1〜M6対応testの配置、非export維持は完了しました。標準checkerは緑ですが、pytestとmutationはPegasus dispatch障害で未実走のため、状態は「実装済み・未実走」です。