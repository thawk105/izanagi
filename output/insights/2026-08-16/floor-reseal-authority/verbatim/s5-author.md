## 実装

- [s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_contract.py:43)
  - 43–48: 可変 2 field／継承 16 field の exact 分割。
  - 252–285: field ごとの canonical bytes 比較。`1` と `1.0`、nested object、list 順序を区別。

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:164)
  - 164–166、257–268: 決定的 namespace/path と exact chain-record pattern。
  - 572–784: `IndexedFloorProtocol`、HEAD 100644 blob loader、path 導出、strict index scan。
  - 805–900: 零引数 `reseal_protocol()`。D3 拒否、create-only、read-back、post-write index、HEAD gitlink 再実測。
  - 5992–6003、6115–6149: `reseal-protocol`／`check-protocol-index` CLI。
  - `freeze_protocol()` と `_freeze_protocol_parser()` は旧版との関数 source 完全一致を確認済み。

- [test_s8b_protocol_builder.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_protocol_builder.py:311)
  - 311–364: committed-anchor tmp repository fixture。
  - 485–836: M1–M8、公開 scan/issuer 変異、D2/D3 正例、strict scan、read-back、CLI read-only。
  - 883–901: 既存 real-repo serial node 内へ index 常設検査を追加。

## 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_s8b_protocol_builder.py -x -q`
  - rc=16、0 passed / 0 failed、**未実走**。
  - 予約台帳を更新できず compute dispatch を選択後、`qstat -Q` preflight rc=1。

- 診断用 plain runner `python3 -B orchestrator/tests/test_s8b_protocol_builder.py`
  - rc=1、39 passed / 1 fixture error。
  - error は既存 `test_repo_status_scrubs_git_environment_and_disables_optional_locks` に plain runner が `monkeypatch` を注入できないため。個別に fixture を注入した診断は rc=0。
  - 既存 confirm／TTY／T-080／writer 凍結領域拒否は診断上 PASS。
  - pytest の緑とは申告しない。

- `check-protocol-index` dogfood: rc=0、count=1、legacy SHA-256 は `261cec1c…74aac`。
- `test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root` 診断: rc=0。
- `check_codex_agents.py`: rc=0。
- `check_docs.py`: rc=0。
- AST parse、`git diff --check`、NFC／結合文字検査: rc=0。

## 受理集合の差分

現行は versioned protocol の発行入口がなく、その path は launch clean scan で未知 file として拒否されていました。

新規受理:

- 未使用 `contract_sha256` と HEAD gitlink の組から導出した exact pathへの一回限りの発行。
- exact `64hex--40hex.json` chain record。
- strict index の read-only CLI。

依然拒否:

- 既出 contract の別 pinを含む二件目。
- 同一組重複、別名、入れ子、短い hash、大文字 hex、symlink、未知 entry。
- 16 field の変異、非 canonical bytes、duplicate key、caller 指定 path／contract／pin。
- HEAD anchor の欠落、非 blob、mode 非 100644。
- generic writer による freeze namespace 書込み。

変化なし:

- `validate_protocol()`、既存 builder、通常 campaign CLI。
- `freeze_protocol` の confirm／TTY／T-080／固定 destination。
- 固定 consumer、hold、承認定数、23-key manifest。

## 波及

- 新 API の所有外 caller は現時点で CLI dispatch のみ。
- production consumer 6 件は固定 legacy pathのまま:
  `certified_writer_admission.py`、`s8b_holdout_admission.py`、`s8b_holdout_freeze.py`、`s8b_ratified_freeze.py`、`s8b_prediction_runner.py`、`tools/pegasus/floor_campaign.sh`。
- shared fixture／serial meta-testへの新 node追加は不要。既存 serialized node内で real-repo indexを検査。
- `test_s8b_floor_campaign.py` の clean-scan群、consumer test群、`test_frozen_artifacts.py` は正式 pytest 未実走。

## 未閉鎖

- pytest は実行基盤障害により未実走。段 6 以降で再実走が必要。
- consumer 結線と実 protocol 発行は後続 wave。
- 削除後の同一組再発行、ratified pointer の namespace 束縛は scope 外。
- 実 repo に `floor-protocols/` や artifact は作成していない。
- docs 編集・commit は指示どおり実施していない。

## 総括

可変 2 field／継承 16 field の境界を実装した。  
legacy authority は committed HEAD の 100644 blobへ固定した。  
組 indexは legacyを必ず含み、閉じた namespaceを strict scanする。  
D3として contract既出時の発行を機械拒否する。  
新 pathは組からのみ導出し、create-onlyで公開する。  
read-backとpost-write full indexを実装した。  
D2の受理拡大はexact pattern一件だけに限定した。  
正式 pytestだけは基盤障害により未閉鎖である。