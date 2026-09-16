## 変更点 (file:line と要旨)

- [s8b_holdout_freeze.py:1375](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/campaign/s8b_holdout_freeze.py:1375)：index authority で protocol を解決し、captured HEAD・worktree・record bytes を照合。解決 path を返し、candidate と measurement closure に反映しました。
- [s8b_v2_freeze_fixture.py:737](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/s8b_v2_freeze_fixture.py:737)：`versioned_protocol=False` を追加。True の場合だけ fixture ccbench HEAD に対応する版付き文書を作成します。既存の `git add -A` と commit で gitlink も記録されます。
- [test_s8b_holdout_freeze.py:1838](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1838)：版付き生成の正例、固定 hash への改変拒否、版付き worktree 改変拒否の3テストを追加しました。既存期待値は変更していません。

版付き worktree 不一致は解決器内で先に拒否されるため、その例外を包む際にも既存の不一致文言を残しています。

## 受理集合の前後

- 前：固定 protocol と一致する result だけ受理。
- 後：index authority が解決した現行 protocol と一致する result だけ受理。

後段の canonical・freeze・result hash・proto8・header 検査は維持しました。固定 anchor、走査除外、allowlist、admission、批准側は変更していません。

## 実走した検査と結果 (nodeid・件数・rc)

| 検査 | 結果 |
|---|---|
| 指定の焦点走を `tools/run_tests.py` 経由で起動 | rc=16。`qstat -Q preflight rc=1` により dispatch 失敗 |
| pytest 実走 nodeid・件数 | **なし・0件**。`child_started=false` |
| 変更3ファイルの AST parse | 3件成功、rc=0 |
| 静的制約確認 | subprocess 起動点不変、anchor 代入 exact 1件、必須3呼出し維持。rc=0 |
| `git diff --check` | rc=0 |

全体走と変異走は未実走です。子の実走による緑は報告しません。

## 変異 M0〜M5 の単一理由性

以下は**静的評価であり、KILLED／SURVIVED の実測ではありません**。node 名の接頭辞は `orchestrator/tests/test_s8b_holdout_freeze.py::` です。

| ID | 最初に赤になる箇所の予測・重複検査 |
|---|---|
| M0 | コメント追加なら挙動不変。SURVIVED 予測。 |
| M1 | `test_v2_candidate_build_and_generate_versioned_protocol` の build 呼出しが result hash 不一致で例外。後段にも pin/header・admission の検査があり、単一理由ではありません。 |
| M2 | 同正例の `document["floor_protocol"] == {...}` assert。build 内に出力 path の同等照合はなく、この assert が直接検出します。 |
| M3 | 固定版の既存 seed 改変テストは record bytes 検査で拒否され、`pytest.raises` の文言 match が赤になる予測。新版の負例は解決器の前段検査で引き続き成功します。**拒否能力の単一理由性なし**。各照合層を独立させる resolver stub 等を用いた再登録が必要です。 |
| M4 | `test_v2_candidate_rejects_legacy_hash_for_versioned_protocol` の `pytest.raises` が `DID NOT RAISE` になる予測。既定 v4 fixture では変更した result hash 自体への別の一致検査は確認できませんでした。v5 には registry hash 照合があるため、この評価は v4 に限定します。 |
| M5 | 登録が指す既存 `protocol.freeze` 不一致テストは見つかりませんでした。さらに後段 `_authority` に freeze path/hash 検査があります。**現登録では殺せる根拠なし**。producer の早期拒否を分離して検証するテストへの再照準を提案します。 |

## 波及の静的列挙

- `candidate_repository` の呼び手は `test_s8b_holdout_freeze.py` 内のみ。既定 False の分岐では既存処理を維持しています。
- `_validate_floor_inputs` と `_measurement_closure` の呼び手は、それぞれ `build_v2_g1_candidate` の1箇所で更新済みです。
- `FLOOR_PROTOCOL_REL` 参照を持つテスト：`test_s8b_protocol_builder.py`、`test_s8b_floor_campaign.py`、`test_campaign.py`、`test_s8b_holdout_freeze.py`、`test_s8b_ratified_freeze.py`。共有 fixture にも参照があります。
- consumer、起動点台帳、perf closure の pytest 回帰確認は未実走です。

## 未実装・未実走・懸念

- 実装済みですが、焦点走・全体走・変異走の成功確認はできていません。テスト回帰の有無は未判定です。
- 不一致文言の変換は campaign 側の既存エラー文字列に依存します。
- runner が禁止領域の `output/pegasus-dispatch/1c7f792fe00d2a29db2b02a8a0027de7/receipt.json` へ receipt を保存したと報告しました。意図しない副作用として報告します。所有外のため削除していません。
- tracked 差分は所有3ファイルのみです。docs 編集・commit はしていません。

## 総括

C-1 の局所修正と3テストの追加は完了しました。実走検証は dispatch 障害で未完了です。M3・M5 は単一理由性を満たすよう親側で再登録が必要です。