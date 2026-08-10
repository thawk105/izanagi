pytest は実行していません。静的解析と親の実測事実だけで判定します。

### fix 2 の焦点監査

- controller は collection を行わず、`session.items` も並べ替えません。worker の `pytest_collection_finish` が `tryfirst=True` で先に並べ替え、その後 xdist が並べ替え後の id 列を controller へ送ります。controller はその列を index として scheduler に渡します。したがって、A3 の「production では無意味」という Critical は成立しません。
- sidecar hook は二重化せず、`pytest_collection_finish` 1 個へ同居しています。[conftest.py:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:281) sidecar は node ID を set 化し、digest もソート済み set から作るため、並べ替えによる観測値の変化はありません。[pytest_stats.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/tools/task_runs/pytest_stats.py:24)
- `-p no:cacheprovider`、`--collect-only`、`-k`、`--lf` でも、選択後の `session.items` を対象にするため範囲外アクセスはありません。`--ff/--nf` の順序は意図的に priority が上書きします。`--lf` の直接対照は未実走です。
- 残る問題は、canonical group 外の payer と他 scope の開始順・cache owner・wall 実測です。

### 所見対応表

| 所見 | 判定 | 根拠と残件 |
|---|---|---|
| A1 kwargs 負例の二重決定 | **closed** | positional 1個＋kwargs非空の fixture になった。[test_real_repo_serialization.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:450)、[同:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:573) |
| A2 group 集合の片側負例 | **closed** | missing-only と extra-only が分離され、exact equality も維持。[同:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:459)、[同:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:586) |
| A3 最終 hook / xdist 順序 | **closed** | finish hook で priority を適用。[conftest.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:262)、[同:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:285)。worker→controller の送信はこの後。 |
| A4 parameter instance 誤拒否 | **closed** | 全 CLI の最大 index と全 barrier の最小 index を比較。[test_real_repo_serialization.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:492)、[同:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:671) |
| B1 payer の閉包漏れ | **out-of-scope (裁定済み)** | 元所見は残るが、本 wave では直さない。[s6-revB.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s6-revB.md:3) |
| B2 collection 順と実行開始順・性能予測 | **partial** | 同一 `real-repo` group 内の FIFO は補強された。[test_real_repo_serialization.py:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:846)。ただし payer など別 scope との開始順、cache owner、wall の実測は未解消。[s6-revB.md:10](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s6-revB.md:10) |
| B3 snapshot の Git env | **out-of-scope (裁定済み)** | [s6-revB.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s6-revB.md:18) |
| B4 RuleOps 固定 timeout | **out-of-scope (裁定済み)** | [s6-revB.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t692-r3-xdist-walltime/s6-revB.md:25) |
| B5 手書き `real-repo` marker | **regressed** | 既存 marker を skip し、形だけを検査するため、正しい positional marker は通過する。[conftest.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:257)、[test_real_repo_serialization.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/test_real_repo_serialization.py:539)。provenance 検査がない。 |

### MT1〜MT7 の単一理由性

| 変異 | 判定 | 最初に落ちる assertion |
|---|---|---|
| MT1 | **closed** | `test_real_repo_serialization.py:519` の canonical set と golden の不一致 |
| MT2 | **closed** | `test_real_repo_serialization.py:450` の positional/kwargs 契約 |
| MT3 | **partial** | **落ちない**。現行 canonical node に既存 marker がないため、skip 分岐を消しても marker は二重化しない。[conftest.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t692-r3-xdist-walltime/orchestrator/tests/conftest.py:187)。想定の `:441` は MT2 と同時に入れた場合だけ発火する。 |
| MT4 | **closed** | `test_real_repo_serialization.py:643` の明示的 `AssertionError`（kwargs 負例が通過） |
| MT5 | **partial** | group 集合変異より先に kwargs 負例が `test_real_repo_serialization.py:450` で落ちる。集合 assertion `:459` の単一理由検証が mask されている。 |
| MT6 | **closed** | `test_real_repo_serialization.py:473` の独立 priority literal 比較 |
| MT7 | **closed** | 同じく `test_real_repo_serialization.py:473`。fix2 報告の `:468` は tuple 開始行で assertion 行ではない。 |

MT6/MT7 の実 mutation 本走は未確認です。

## 総括

- **NO-GO**
- 対応表の集計: **closed 4 / partial 1 / regressed 1 / out-of-scope 3**
- 残る must-fix:
  - B2 の cross-scope 開始順・cache owner・wall 根拠。
  - B5 の手書き marker provenance 検査。
  - MT3 の単独生存と MT5 の kwargs mask を解消する mutation fixture 分離。