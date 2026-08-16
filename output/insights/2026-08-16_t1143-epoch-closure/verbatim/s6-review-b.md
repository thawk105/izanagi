### 所見

blocker・major・minor に該当する取り残しは検出しなかった。

### 固定依存の再集計

件数は一致した行数。裸の `8` は全件を closure 語彙で再分類した。

| 対象 | `8` | `eight` | `exact 8` | `8-path` | `len(...) == 8` |
|---|---:|---:|---:|---:|---:|
| `orchestrator/campaign` | 2298 | 3 | 0 | 0 | 0 |
| `orchestrator/tests` | 9241 | 14 | 1 | 0 | 15 |
| `orchestrator/verifier` | 18 | 0 | 0 | 0 | 0 |

closure 関連の旧 8 件依存は 0 件だった。`exact 8` の唯一の残存は [test_t139_stress_check_simulation.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_t139_stress_check_simulation.py:481) の「8 raw bytes」で別契約。`len(...) == 8` の15件も WAL stage、round 数、hash suffix 等で closure と無関係だった。`eight` は `weight` や別テスト名への一致だった。

### 整合確認

- exact 12 の内容と順序は [campaign_lock.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/campaign_lock.py:29) で、既存8件を保持し `core → dsg → model → parse` を末尾追加している。独立 literal は [test_t671_source_binding.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_t671_source_binding.py:22)。
- closure 定数の consumer 11ファイルは、動的反復または独立 tuple との完全一致。共有 helper も [campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/campaign_lock_test_support.py:10) で動的追随する。
- 診断文字列は [artifact_admission.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/artifact_admission.py:65) から JSON へそのまま転送される。[s8b_oracle_report.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/s8b_oracle_report.py:357) と [test_s8b_oracle_report.py:767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_s8b_oracle_report.py:767) は新しい定数と整合する。
- 新規4 node は [test_artifact_admission.py:1113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_artifact_admission.py:1113) の literal parametrize から生成される。旧・新テスト名および新 node 名の外部固定参照は0件で、新規 test file もない。
- wire key と schema は [campaign_lock.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/campaign_lock.py:15) から不変。epoch は tuple 順に反復し [artifact_admission.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/artifact_admission.py:742) で同じ `/v1` preimage、[artifact_admission.py:746](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/campaign/artifact_admission.py:746) で同じ `E1:` prefix を使う。hash 順序の sort 化はない。
- `b20c5459` 自体の変更は7個のコード・テストファイルのみで、`docs/**` と `output/**` は0件。指定 range に見える docs 2件は介在 commit `0829f565` と `35a006c2` の変更であり、実装 commit の変更ではない。`git status --short` は0件だった。

pytest は実走しておらず、緑とは数えていない。

## 総括

GO  
指定された固定依存、consumer、診断転送、メタテスト、wire 契約に取り残しは見つからなかった。  
exact 12 の要素と順序は裁定どおりで、epoch preimage の算出方法も保存されている。  
新規4 nodeによる既存の固定 node 集合・test file 集合への破壊も検出しなかった。  
実装 commit は docs・output を変更せず、作業木も clean である。  
最終的な実走受入は親が行う必要がある。