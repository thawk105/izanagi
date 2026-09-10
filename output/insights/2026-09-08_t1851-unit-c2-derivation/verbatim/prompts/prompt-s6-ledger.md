単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-ledger2`
- **受入全走の JUnit (正本の入力)**: `/work/1/SFC/tanab/.izanagi-acceptance-shards/e04319292c80256eba45349c4a6a061c/junit.xml`
- 台帳の生成器 (正本): `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-ledger2/tools/update_acceptance_duration_ledger.py`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-ledger2/CLAUDE.md`

# 受入所要時間台帳へ、本 wave が新設した node を add-only で登録する

## 所有する file (これ 1 つだけ。他の追跡下 file を 1 つも変更しない)

```
orchestrator/tests/acceptance_duration_ledger.json
```

**`git` を一切実行しない。commit しない。** `docs/` と `output/` を触らない。
**production file も test file も変更しない。**

## 事象 (親が実測)

受入全走 attempt 2 は **22,390 passed / 1 failed** で、唯一の赤が

```
orchestrator/tests/test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection
```

である。本 wave が新設した test node が台帳に未登録なので、被覆率が閾値を割った。

## やること

**正本の生成器を `--add-only` で当てる。手編集はしない。**

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-ledger2
python3 tools/update_acceptance_duration_ledger.py --add-only \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/e04319292c80256eba45349c4a6a061c/junit.xml
```

`--help` を先に読んで argv を確かめること。`--repo` や `--output` の既定が
作業 root を指しているかを確認し、指していなければ明示的に渡すこと。

## 守ること

- **既存 entry を 1 件も削除しない。既存の duration 値を 1 件も変更しない。**
  `--add-only` はそれを保証する契約だが、**実行後に自分で検算して件数を報告すること。**
- `nodeid_count` が `duration_seconds_by_nodeid` の実体数と一致すること
  (`conftest.py` の loader が不一致を拒否する)。
- `schema_version` は 1、`unit` は `"seconds"` のまま。
- **台帳を手で開いて編集しない。** 生成器の出力をそのまま使う。
- 被覆率の閾値を下げる方向の変更をしない (所有外でもある)。

## 実走

登録後、被覆率検査が緑になることを確かめること。

```
PYTHONPATH=. python3 orchestrator/tests/test_acceptance_schedule_order.py
```

自走 harness が無くて収集 0 件になる場合は、**harness を新設せず**、
対象関数を import して直接呼ぶ最小の一時 script を作業 root 直下に作り、
確認後に削除すること。一時 file を残さないこと。

**緑には実走した nodeid を必ず併記する。** 走らせていないものを緑と書かない。

## 禁止

- `git` を実行しない。commit しない。
- 台帳以外の追跡下 file を 1 つも変更しない。
- 台帳を手編集しない。生成器を通す。
- duration の値を丸めない・書き換えない。entry を消さない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 出力形式 (この見出しをこの順で使う)

## 実行した argv
## 生成器の報告 (added / skipped / excluded)
## 登録前後の nodeid_count と実体数
## 削除 0 件・既存値変更 0 件の検算
## 追加された nodeid の内訳 (file 別の件数)
## 実走した nodeid と結果
## 総括
