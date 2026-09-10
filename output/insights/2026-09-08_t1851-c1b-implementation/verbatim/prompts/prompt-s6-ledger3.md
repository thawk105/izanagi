単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-adjudication-2.md

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-ledger`
(branch `impl-dev-wave-t1851-c1b-ledger`、**本 wave の tip `1c16b8d46` にリセット済み・clean**) である。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/main-ledger.json` — **健全な local main (`6172ea26b`) の受入所要台帳の現物** (nodeid 19,761 件)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/ledger-junit.xml` — **親が計算ノードで実測した JUnit** (407 件、failures 0)

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/tests/acceptance_duration_ledger.json`

**他の file を 1 byte も変えるな。** docs の編集、`git commit`、`git merge`、`git add` はしない。

## 背景 — なぜこの形なのか

本 wave は自分の base の台帳へ 242 node を登録済みだが、その後 local main が**同じ台帳を
大幅に作り直した** (他 wave の登録と key 順の是正)。text merge では 4,000 行規模の競合になり、
手で解くと実測値を壊す。

**したがって競合の解決を「main の台帳を土台に、同じ tool で本 wave の node を足し直す」形で作る。**
これは main の履歴が既に採っている解法である
(`merge: main と待ち手 wave の受入所要時間台帳を実測値の和集合で合成`)。

**なぜ main の木の上で作れないか (実測済み):** `update_acceptance_duration_ledger.py` は JUnit の
classname から Python module の実在を検査する。本 wave の `test_s8b_terminal_evidence.py` は
main に存在しないため、main の木では `classname 'orchestrator.tests.test_s8b_terminal_evidence'
has no Python module` で rc=2 になる。**本 wave の木の上でだけ作れる。**

## 依頼 — 次の 2 手だけを実行する

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-ledger
cp /work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/main-ledger.json \
   orchestrator/tests/acceptance_duration_ledger.json
python3 tools/update_acceptance_duration_ledger.py --add-only \
  /work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/ledger-junit.xml
```

1 手目は台帳を **main 側の現物へ差し替える**(競合を「theirs を採る」形で解く)。
2 手目は `--add-only` で **既存 entry を byte exact に保ったまま、未登録の nodeid だけを足す。**

## 期待結果 (これと食い違ったら止めて報告しろ)

- 起点 (main 側現物) の `nodeid_count` は **19,761**。
- **削除 0 件、main 側の既存 duration value の変更 0 件。**
- `excluded_frozen_removed` / `excluded_writer_base_key` / `excluded_frozen_suite` が
  すべて 0 であること。**0 でなければ止めて報告しろ。**
- 追加される nodeid は、本 wave が新設・改修した次の 4 file のものだけであること。
  **これ以外の path が追加集合に現れたら止めて報告しろ。**

| file |
|---|
| `orchestrator/tests/test_s8b_terminal_evidence.py` |
| `orchestrator/tests/test_s8b_attempt_registry.py` |
| `orchestrator/tests/test_s8b_floor_attempt_launcher.py` |
| `orchestrator/tests/test_attempt_registry_core_s8b_profile.py` |

- **追加件数は 242 とは限らない。** main 側が同名 nodeid を既に持ちうるためである。**実測値を報告に書け。**
- `schema_version` と `unit` は不変。

## 禁止

- **台帳を手で編集するな。** 上記 2 手だけを使え。
- **main 側の既存 entry に触れるな。** 凍結 8 suite
  (`test_t1574_changed_suite_ledger_node_delta_is_exact` が exact hash で固定) も同様。
- **`git merge` / `git add` / `git commit` をするな。** 統合は親が行う。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定するな。**
- docs を編集しない。所有外 file を触らない。

## 検査・報告

- `git diff --stat` で変更が台帳 1 本だけであることを確かめろ。
- 自走 harness で台帳 consumer を走らせろ。
  `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-ledger && PYTHONPATH=. python3 orchestrator/tests/test_update_acceptance_duration_ledger.py`
  **`test_t1574_changed_suite_ledger_node_delta_is_exact` が緑であることを明示的に確認しろ。**
  この test は main 側で凍結された 8 suite の node 集合を exact hash で固定しているので、
  **main の台帳を土台にした本作業では特に重要である。**
- **緑には実走 nodeid・範囲を併記する。**

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 総括

最後に `## 総括` 節を置き、次を書く。

- tool の出力全件 (added / skipped_existing / excluded_* の各件数)
- `nodeid_count` の変化 (19,761 から幾つへ)
- **追加された nodeid の file 別内訳**
- 削除件数と、main 側既存値の変更件数 (どちらも 0 であること)
- `git diff --stat`
- 実走した nodeid と結果。特に `test_t1574_changed_suite_ledger_node_delta_is_exact` の可否
