## 変更の要約

指定の 2 ファイルのみ更新しました。

- `tools/check_docs.py`：command SHA を更新（+1/−1 行）。
- `orchestrator/tests/test_check_docs.py`：独立 literal 2 行、期待 SHA、bytes assert 2 箇所、padding を更新（+6/−6 行）。

予算上限・SKILL SHA・helper・拒否期待値は不変です。

## byte 一致の確認

一時 script で両対象の `HEAD == 現物 == fixture`、`現物 SHA == production 定数 == fixture 期待定数` を確認しました。script は削除済みです。

| 対象 | bytes | 一致 |
|---|---:|---|
| command | 6,201 | 全一致 |
| SKILL | 3,060 | 全一致 |

```text
command: c8db749bd90fdf3b663eadbb516682472bd489bd57589f2036b972398f7da9c8
SKILL:   3cf0344df609115811d30a30ffe875cca1756e5a5a9aaa2c26e3c9f278269930
```

`discard_changes: true` は本文・fixture とも 1 回です。

## 既存 test 追随の有無

旧断片への依存は更新した fixture 2 行以外にはありません。SKILL の同種 bytes assert はありません。

## 実走結果

指定の `pytest.main` 経路で実行しました。

| 対象 | 結果 | rc |
|---|---|---:|
| 変更前 `check_docs.py` | command SHA 不一致 1 件のみ | 1 |
| 指定 `-k` 焦点走 | 33 passed、550 deselected | 0 |
| `orchestrator/tests/test_check_docs.py` 全件 | 580 passed、3 skipped | 0 |
| `test_plain_runner_coverage.py`・`test_check_subprocess_bytecode_guard.py` | 合計 9 passed | 0 |
| 変更後 `check_docs.py` | `check_docs: 違反なし` | 0 |
| `git diff --check` | 指摘なし | 0 |

前巡で失敗した `orchestrator/tests/test_check_docs.py::test_cleanup_command_leading_space_h2_is_rejected` は緑に戻りました。

全件走の skip は既存 growth hold の次の 3 nodeid です（共通 prefix：`orchestrator/tests/test_check_docs.py::`）。

- `test_dev_wave_model_pins_accept_current_docs_contract`
- `test_normative_exact_section_pins_accept_real_repo`
- `test_real_repo_clean`

## 波及

指定ディレクトリ内の 4 識別子の参照元は、編集対象 2 ファイルだけでした。command 本文・SKILL・`docs/failures.md` 等の歴史記録は未変更です。

## 未了・懸念

既存 hold 3 件は未実走です。子の実走は親の全走を代替しません。commit は作成していません。

## 総括

fix 3 の pin 追随と指定検証を完了しました。差分は working tree に残しています。