指定 2 ファイルだけを修正しました。docs 編集・commit・gate API 追加はありません。

| 所見 | 状態 | 対応 |
|---|---|---|
| F-A1 | `partial`（実装済み・pytest未実走） | 起草文書の `new_text` 117 bytes（末尾 LF 含む）を SHA-256 `92fd71754c81b45b6cc01fb14600bfdc140af8e464c50484b45e1bb8caaa01a4` として固定。2反例の拒否テストを追加 |
| F-B2 | `partial`（実装済み・pytest未実走） | s7 validator 内で SHA-256 と `old_text` bytes を自前照合。共有 helper は s15 のみ使用 |
| F-B4 | `partial`（静的確認済み・mutation未実走） | コード変更不要。M4を「s7 IDをDRAFTから除きAPPROVEDへ移す」とした場合、既存の指定nodeだけが承認集合の誤りを検出 |
| F-B6 | `partial`（具体変異確認済み・mutation未実走） | M6の具体置換を固定。既存テストの補強は不要 |

変更箇所は [erratum.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/preregistration/erratum.py:23) と [test_t139_preregistration_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w1/orchestrator/tests/test_t139_preregistration_binding.py:417) です。

M4/M6 の確認内容：

- M4:
  - `APPROVED_ERRATA = {s15, s7}`
  - `DRAFT_ERRATA = {}`
  - この変異では `test_draft_erratum_is_not_in_approved_set` の exact-set assertion が偽になります。
  - registry の直和・非重複条件は保たれるため、production の別経路では先に落ちません。
- M6:
  - 具体置換は、未知ID時の
    `raise UnknownErratumError(...)`
    を
    `return cast(RegisteredErratumId, "t139-core-s15-exactkey-v1")`
    に置換するものです。
  - production probe で未知IDがs15 validator経由で受理されることを確認しました。
  - 未知IDを扱うテストは `test_unknown_erratum_id_fails_closed` のみです。

検査結果：

- production validator probe: rc=0
  - 承認予定 `new_text`: 受理
  - 強い較正主張: 拒否
  - 無限定な安心表現: 拒否
  - s7 SHA不一致・`old_text` bytes不一致: 拒否
  - s7は共有helperを通らず、s15は共有helperを維持
- static compile: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- admission API 4名の非export: 確認済み

pytestは次の対象を標準runnerで投入しましたが、`qstat -Q preflight rc=1`、runner `rc=16` でcollection前に停止しました。このため緑とは主張しません。

- 新規2反例node
- s7/s15 SHA束縛node
- M4/M6指定node
- 2 errata合成node
- 非export node
- `test_plain_runner_coverage.py`
- `test_pytest_collection_config.py`

所有外への波及可能性：

- s7 erratumを任意の一行へ置換していた外部consumerは、新しいexact digest検査で拒否されます。これは意図した受理集合縮小です。
- s15 validatorの共有helper経路と既存挙動は維持しています。
- `compose_core` のrepo内production callerは見つかりませんでした。
- 新例外はpackageからexportしていません。
- resolver、manifest、受領証schema、予約台帳、admission APIは未実装のままです。
- 作業木に存在する対象外のdocs/output差分には触れていません。

## 総括

4所見への必要な実装・テスト追加・具体変異の固定は完了しました。ただしpytestとmutation harnessはdispatch障害で未実走なので、全件 `partial（実装済み・未実走）` です。commitは作成していません。