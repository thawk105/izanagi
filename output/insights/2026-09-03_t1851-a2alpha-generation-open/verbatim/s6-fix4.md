## 修正内容

対象 test の共有 helper 呼び出しを、同ファイルの既存作法どおり `tmp_path` の直接渡しへ変更しました。共有 helper、production コード、他 test は未変更です。

changed LOC は 4（追加 1、削除 3）です。`git diff --check` は成功しました。

## Assertion の確認

assertion は一切変更・弱化していません。exact 署名検査と ordinal 0 の正例対照はそのままです。

## 実走結果

実行を試みた nodeid:

`orchestrator/tests/test_s8b_attempt_registry.py::test_v2_resume_rejects_recovery_ordinal_and_accepts_zero`

runner rc=16、`qstat -Q preflight rc=1` で pytest child は起動しませんでした。`queue-wait-timeout` ではないため再投入条件外です。実装済み・未実走です。

## 総括

- 直した内容: helper に存在しない中間 directory ではなく、test 固有の既存 `tmp_path` を直接渡すよう修正
- 実走した nodeid と結果: 上記 nodeid を投入したが、infra rc=16 で child 未起動（実装済み・未実走）
- 追加した changed LOC: 4（追加 1、削除 3）
- あなたが読めなかった資料、確かめられなかった事実: 読めなかった資料なし。pytest node の成否は infra 障害のため未確認