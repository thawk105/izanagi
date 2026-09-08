## 直した内容

- fixture の `diagnostic_genome_arm`、`diagnostic_arm`、`trace_enabled_arm`、`unstable_arm` を `arm is not None` で保護し、`None == None` の誤発火を除去しました。
- consumer に固定対専用の arm 判定を追加しました。診断 marker が 1 個だけ加わった genome も元の固定対へ正しく帰属させます。
- 対外 genome に診断 knob があっても固定対を受理する回帰テストを追加しました。
- テストの既存 assertion、閾値、pin は変更していません。

変更箇所は [consumer](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-a/orchestrator/campaign/t1998_stock_inline_pair.py:96) と [fixture/test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-unit-a/orchestrator/tests/test_t1998_stock_inline_pair.py:119) です。

## 走査範囲の判断とその理由

内容検査を事前登録された固定 2 点だけへ狭めました。

D1244 と段 4 裁定 §3 は、固定対では build、verify、bench、commit の内容を読み、他 6 点では stage の形と abort の有無だけを見る契約です。したがって、対外 genome の診断 knob は headline に使う 2 点を汚さず、全点の stage 完備と abort 不在が維持される限り受理してよいと判断しました。

arm は文字列部分一致では判定しません。完全な固定 genome、またはそこへ `BACKOFF_NOINLINE=1` が 1 個だけ追加された genome を定数と照合します。このため target の診断 build は target、baseline は baseline に帰属し、対外 genome を baseline と誤表示しません。

## 実走した検査

- `PYTHONPATH=. python3 orchestrator/tests/test_t1998_stock_inline_pair.py`
  - 最終結果: **16 passed / 0 failed**
  - 実行時間: 99.87 秒
  - 赤 node: なし
  - 元の赤 9 node はすべて通過
- 同 harness の先行実走も 16 passed / 0 failed。
- 所有 3 file の AST parse: 通過
- `git diff --check`: 通過
- U+0300〜U+036F 検査: 該当なし
- `git status --short`: 変更は所有 3 path のみ

build、benchmark、性能測定、qsub は実行していません。

## 所見ごとの対応表

| 依頼 | 状態 | 対応 |
|---|---|---|
| 1. fixture 欠陥と同型比較の修正 | closed | optional arm 比較 4 箇所を保護 |
| 2. consumer 走査範囲と arm 帰属 | closed | 内容検査を固定対へ限定し、定数照合で帰属 |
| 3. 元の赤 9 件を緑化 | closed | 期待値を弱めず全件通過 |
| 4. 自走 harness の実走 | closed | 16 passed / 0 failed を確認 |

partial、regressed はありません。

## 残した赤とその理由

残した赤はありません。

## 総括

fixture の `None == None` 誤発火を解消し、consumer を「固定 2 点だけ内容を読む」という裁定へ整合させました。自走 harness は最終的に 16 passed / 0 failed です。commit、`git add`、docs 更新、所有外の変更は行っていません。