## 所見対応表

必須 pytest が dispatch 前に停止したため、dev-wave 実装子契約に従って全件 `partial` とします。

| 所見 | 状態 | 根拠 |
|---|---|---|
| FIX-1 | partial | Git 環境を既存 helper で scrub: [s8b_floor_campaign.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:619)、負例 `test_reseal_protocol_scrubs_ambient_git_dir_authority`: [test_s8b_protocol_builder.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:752) |
| FIX-2 | partial | index の contract 一意性: [s8b_floor_campaign.py:695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:695)、単体負例 `test_floor_protocol_index_rejects_same_contract_with_different_pin`: [test_s8b_protocol_builder.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:812) |
| FIX-3 | partial | `output`／`output/s8b-freeze` の symlink 拒否: [s8b_floor_campaign.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:724)、負例: [test_s8b_protocol_builder.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:826) |
| FIX-4 | partial | commit OID と blob OID への固定、publish 後 HEAD 検査: [s8b_floor_campaign.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:619)、[s8b_floor_campaign.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:860)。HEAD race 負例: [test_s8b_protocol_builder.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:838)、publish 後移動: [test_s8b_protocol_builder.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:614) |
| FIX-5 | partial | 件数固定を legacy 一致・全 entry 検証・contract 一意性へ変更: [test_s8b_protocol_builder.py:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:1110) |
| FIX-6 | partial | 継承呼出しを post-condition と明記。closed namespace、duplicate-key、read-back 3 分岐の理由を固定: [test_s8b_protocol_builder.py:647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:647)、[test_s8b_protocol_builder.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:674)、[test_s8b_protocol_builder.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:701)、[test_s8b_protocol_builder.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:914) |

## 実装

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py)
  - ambient Git repository/object override を除去。
  - anchor mode、blob bytes、gitlink を同一 commit OID に固定。
  - 同一 contract の複数 index entry と祖先 symlink を拒否。
  - publish 直前の恒真 gitlink gate を除き、publish 直後の HEAD commit 移動を拒否。
  - flock は不使用。常設 index 不変条件と post-write scan により、並行発行が両方成功を返すことを防止。
- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py)
  - FIX-1〜FIX-6 の負例と拒否理由検査を追加。
  - 唯一許可された実 repo 件数期待を不変条件検査へ変更。
- `s8b_floor_contract.py` は変更なし。

## 実走結果

| nodeid | rc | passed | failed | 結果 |
|---|---:|---:|---:|---|
| `orchestrator/tests/test_s8b_protocol_builder.py` | 16 | 0 | 0 | `qstat -Q preflight rc=1`、収集前停止のため未実走 |
| `orchestrator/tests/test_s8b_floor_contract.py` | 16 | 0 | 0 | `qstat -Q preflight rc=1`、収集前停止のため未実走 |

補助検査:

- AST parse: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

## 受理集合の差分

狭まったもの:

- ambient Git 環境で別 repository を authority にする経路。
- 同一 `contract_sha256` の複数 protocol。
- `output` または `output/s8b-freeze` が symlink の index。
- 単一 snapshot に存在しない anchor bytes／gitlink の組。
- publish 中に HEAD commit が移動する発行。

変わらないもの:

- `freeze_protocol()` と `_freeze_protocol_parser()` の受理集合。
- sanctioned filename 文法、16/2 field 分割、create-only 規則。
- `_CHAIN_RECORD_PATTERNS` と既存 consumer の参照先。
- read-back 検査の受理集合。拒否理由の検出力のみ強化。

## 未閉鎖

- Pegasus の `qstat -Q` preflight 障害により、必須 pytest 2 ファイルは未実走。
- このため FIX-1〜FIX-6 は実装済みですが、`closed` 判定にはしていません。
- docs、protocol artifact、`output/`、commit は変更していません。

## 総括

FIX-1〜FIX-6 のコード・テスト修正を許可された 2 ファイルへ実装しました。  
Git authority は衛生化環境と単一 commit OID へ束縛しました。  
index は同一 contract の複数件と祖先 symlink を fail-closed で拒否します。  
publish 後に HEAD が移動した場合も実際に発火する拒否へ置換しました。  
負例は対象 branch の拒否理由まで照合します。  
実 repo の揮発する件数期待は裁定された不変条件へ置換しました。  
必須 pytest は dispatch infrastructure の rc=16 により未実走です。  
commit、docs 編集、artifact 発行は行っていません。