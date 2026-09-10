# 段 6 fix 2 巡目 裁定 — in-tree 一時ファイルの除去

親裁定。fix 1 巡目後の親の組み合わせ実走 (`t2.log`) で新しい赤が 1 件出た。

## 実測 (一次資料)

`python3 tools/run_tests.py orchestrator/tests/test_pytest_failure_digest.py
orchestrator/tests/test_plain_runner_coverage.py orchestrator/tests/test_real_repo_serialization.py`
→ **1 failed, 25 passed** (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/t2.log`)

落ちたのは
`test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root@real-repo`。

```
AssertionError: 実 repo tree が変化した: paths=[
  'orchestrator/tests/.failure-digest-states-ytansggt/test_collect_error.py',
  'orchestrator/tests/.failure-digest-states-ytansggt/test_green_states.py',
  'orchestrator/tests/.failure-digest-states-ytansggt/test_strict_xpass.py']
```

guard の `before` にはこの 3 件が `??` として写り、`after` では消えている。すなわち
**新規テストが repo 作業ツリー内へ一時 test file を作り、guard の観測窓と競合した**。

fix 1 巡目の前 (`t1.log`) でも E2E は `orchestrator/tests/.failure-digest-e2e-<rand>/` を
作っており、そのときは偶然通っていた。**これは潜在フレークが顕在化したものであり、
受入全走へ非決定的な赤を持ち込む。**

## F11 — 新規テストは repo 作業ツリーへ一切書かない

**裁定: 一時 test tree を repo 内に作ってはならない。すべて `tmp_path` 配下へ移す。**

対象は少なくとも次の 2 系統 (他にあれば同様に移すこと)。

- E2E の `orchestrator/tests/.failure-digest-e2e-*`
- 実終了形テスト (F6) の `orchestrator/tests/.failure-digest-states-*`

### conftest 自動 discovery の満たし方

`-p orchestrator.tests.conftest` による強制ロードは**引き続き禁止**である (段 4 の B#2 裁定)。
代わりに次で満たす。

1. 実 `orchestrator/tests/conftest.py` を `tmp_path` の rootdir へ**コピー**し、
   一時 test file をその配下に置く。pytest の通常の conftest 自動 discovery を通す
2. subprocess の `PYTHONPATH` に repo root を入れる。実 acceptance は
   `python -m pytest` を `cwd=repo root` で起動するため CWD が `sys.path[0]` に入る
   (`tools/run_tests.py:378`)。同じ条件を明示的に再現するだけであり、緩和ではない
3. **コピー元と実ファイルの内容一致を sha256 でテスト内 assert する。**
   コピーが陳腐化したら赤にする (実 conftest と乖離したものを検査して緑にしない)

### 守る不変条件

- 走行の前後で `git status --porcelain` が変化しないこと。**repo 内に一時ファイル・
  一時ディレクトリを一瞬でも作らない**
- 既存テスト (`test_real_repo_serialization.py` を含む) を 1 文字も変更しない
- F1〜F10 で閉じた内容を退行させない。特に E2E は引き続き
  「`-p` なしの自動 discovery」「実 nodeid」「末尾 sentinel」「全 account 値の独立検算」
  「digest 開始以降 < 64 KiB」「stdout が終了マーカで終わる」を検査すること
- subprocess は `start_new_session=True`、timeout 時は process group TERM→KILL、
  descendant 消滅確認を維持する

## 実走の要件

**単一ファイルだけの実走で緑を主張してはならない。** 今回の赤は組み合わせ実行でだけ出た。
最低限、次の 3 ファイルを**同時に**指定した実走で緑を確認し、その argv と結果を報告に書くこと。

```
python3 -m pytest orchestrator/tests/test_pytest_failure_digest.py \
  orchestrator/tests/test_plain_runner_coverage.py \
  orchestrator/tests/test_real_repo_serialization.py
```

加えて、実走の**直前と直後**に `git status --porcelain` を取り、差が無いことを報告に書くこと。
