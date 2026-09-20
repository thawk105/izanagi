## 変更の要約

指定 2 ファイルだけ更新しました。

- `tools/check_docs.py`：command SHA 1 行（+1/−1）。
- `orchestrator/tests/test_check_docs.py`：独立 literal、期待 SHA、bytes assert 2 箇所、padding（+5/−5）。

予算上限・SKILL SHA・helper・拒否期待値は不変です。

## byte 一致の確認

一時 script で両対象の `HEAD == 現物 == fixture`、`現物 SHA == production 定数 == fixture 期待定数` を確認しました。script は削除済みです。

| 対象 | bytes | 一致 |
|---|---:|---|
| command | 6,204 | 全一致 |
| SKILL | 3,060 | 全一致 |

```text
command: 1d37a04b559e34e9e80e3e9f937f1abe11345c9e406a80dc95aa3c1309170317
SKILL:   3cf0344df609115811d30a30ffe875cca1756e5a5a9aaa2c26e3c9f278269930
```

## 既存 test 追随の有無

旧断片「§1 の status 空を再確認」への依存は、更新した fixture 1 行以外にはありません。`discard_changes: true` は本文・fixture とも 1 回です。

## 実走結果

- 変更前 `check_docs.py`：rc=1、command SHA 不一致 1 件のみ。
- 指定経路・指定 `-k` の焦点走：**1 failed、32 passed、550 deselected、rc=1**（16.63 秒）。

失敗 nodeid：

```text
orchestrator/tests/test_check_docs.py::test_cleanup_command_leading_space_h2_is_rejected
```

[失敗箇所](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2814-unit-impl/orchestrator/tests/test_check_docs.py:10024)：

```text
assert _violation_count(res) == 1
E assert 2 == 1
```

実際の違反は次の 2 件でした。

```text
6205 bytes > 予算 6204 bytes
whole-file SHA-256 が契約と不一致
```

## 余白 0 の影響

上記テストは helper を使わず H2 の先頭に空白 1 byte を追加するため、6,205 bytes になります。SHA 違反に予算超過が加わり、期待違反件数 1 件が成立しなくなりました。本差分に起因する失敗です。

## 波及

指定ディレクトリを検索し、4 識別子の参照元は編集対象 2 ファイル内だけでした。command 本文・SKILL・歴史記録は未変更です。

## 未了・懸念

**「赤があれば nodeid と理由を報告して止める」の指示に従い停止しました。** 期待値や mutation は変更していません。

全件走、meta-test、変更後の `check_docs.py`、`git diff --check` は未実走です。

## 総括

pin 追随と byte 一致確認は完了しましたが、余白 0 による既存テストの失敗で検証未完了です。差分は未コミットの working tree に残しています。