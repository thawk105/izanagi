単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1`
- **親の段 4 裁定 (これが正本)**: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s4-adjudication.md`
- 親の段 1 brief: `/home/SFC/tanab/.claude/jobs/4ddc6923/tmp/t1851c2/s1-brief.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1/CLAUDE.md`

# 段 5 実装子 1 — runner に構造化 `execution_failure` を載せる

裁定の **S1** だけを実装する。**S2 / S3 / B1〜B7 は子 2・子 3 の所有なので触らない。**

## 所有する file (これ以外の追跡下 file を 1 つも変更しない)

```
orchestrator/calibrator/runner.py
orchestrator/tests/test_calibrator.py
orchestrator/tests/test_calibrator_deferred_output.py
```

**`git` を一切実行しない。commit しない。** merge も add も親が行う。
`docs/` と `output/` を触らない。**新しい production file を作らない。**

## 実装内容

rep observation に **7 番目の key `execution_failure`** を足す。

- 型は exact `bool`。値域は `{False, True}` のみ。`None`・key 欠落・`0`/`1` を採らない。
- **例外の型名も message も新 key に載せない。** 外部実行に由来する文字列を信頼経路へ運ばない
  (絶対規律 6)。既存の診断用 notes はそのまま残してよい。

変更する箇所は **4 つの literal と 4 つの例外捕捉**である。親が現物で実測した位置は次のとおりだが、
**自分で開いて照合すること** (ずれていたら報告する)。

| 面 | 公開関数 | observation の初期化 | observation の最終代入 | 例外捕捉 |
|---|---|---|---|---|
| deferred / capture | `capture_measure_point()` (def `:803`) | `:940` | `:990` | `:965`、`:978` |
| direct | `measure_point()` (def `:1057`) | `:1106` | `:1203` | `:1170`、`:1184` |

- 初期化 literal には `execution_failure: False` を置く。
- 例外を捕捉した rep は、その rep の observation の `execution_failure` を `True` にする。
- **両面を同じ形にする。** 片方だけ直さない。

### 触ってはいけないもの

- 集約 note `f"{n_exec_fail}/{reps} reps failed to execute"` (`:1029`、`:1247`) は**残す**。
  除去は子 2 の所有である。
- `n_exec_fail` の既存の意味を変えない。
- **受理集合を指示外に変えない。** 例外捕捉の対象例外型を増減させない。

## 期待される赤 (これは本 wave の設計どおりで、直してはならない)

runner が 7 key を出すと、**子 2 が所有する下流の exact 6-key gate が赤になる。**

- `orchestrator/campaign/s8b_floor_campaign.py:1947` 付近の `complete` 述語
- `orchestrator/campaign/s8b_floor_stats.py:487` の `set(observation) != _REP_OBSERVATION_KEYS`

**これらを xfail 化してはならない。既存テストの期待値も変えてはならない** (どちらも所有外)。
**赤の内訳 (nodeid と理由) を完了報告に列挙すること。**
所有 file 内のテストが赤になる場合は、それが上記の下流由来か自分の実装由来かを切り分けて書くこと。

## テスト

所有する 2 つの test file に、**両面それぞれの正例と負例**を足す。

- 正常 rep: `execution_failure is False`
- `RuntimeError` を捕捉した rep: `execution_failure is True`
- `subprocess.TimeoutExpired` を捕捉した rep: `execution_failure is True`
- 汎用 `Exception` を捕捉した rep: `execution_failure is True`
- 非 zero 戻り値だけの rep (例外なし): `execution_failure is False`
- **`capture_measure_point()` 用と `measure_point()` 用を別々に書く。**
  片方の test がもう片方の面へ届かないことを自分で確かめること。
- 値が exact `bool` であることを `type(...) is bool` で固定する。

**テストを甘くして緑にしない。** fixture へ現行 hash を差し込む形の緑は採らない (F27)。
**機構の正例・負例は実体を名指しし、依存先を stub で置き換えない** (F649)。
**期待値へ揮発 payload (working tree の hash、時刻、絶対 path) を焼き込まない。**

新しい test file は作らない (既存 2 file に足す)。**もし作る必要があると判断したら、
作らずに理由を報告すること** (登録簿の追随が所有外になるため)。

## 実走

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s1
PYTHONPATH=. python3 orchestrator/tests/test_calibrator.py
PYTHONPATH=. python3 orchestrator/tests/test_calibrator_deferred_output.py
```

**`run_tests` は使わない (rc=16 になる)。`python3 -m pytest` は guard に拒否される。**
自走 harness が無い file があれば、**既存 file と同形式で末尾に付ける**
(`if __name__ == "__main__": raise SystemExit(pytest.main(["-q", str(Path(__file__).resolve())]))`)。

**緑には実走 nodeid・範囲を必ず併記する。** 実走できなかったものは `closed` と申告せず
「実装済み・未実走」と書き、理由を書くこと。**走らせていないものを緑と書かない。**

制約 meta-test を自分で洗い出して走らせること。少なくとも
`orchestrator/tests/test_pytest_collection_config.py`、
`orchestrator/tests/test_official_perf_closure.py`、
`orchestrator/tests/test_campaign_import_invariant.py` を確認する。

## 禁止

- `git` を実行しない。commit しない。
- 所有 3 file 以外の追跡下 file を 1 つも変更しない。
- `docs/` と `output/` を触らない。新しい production file を作らない。
- 下流の exact 6-key gate を自分で直さない (子 2 の所有)。
- 既存テストの期待値を変えない。xfail を足さない。
- 出力に結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら、**途中結論を出力形式どおりに書いて終わること** (無出力が最悪)。

## 出力形式 (この見出しをこの順で使う)

## 変更前の受理・拒否挙動
## 実装した箇所 (file:line)
## 足したテスト
## 実走した nodeid と結果
## 期待どおりの赤 (下流由来)
## 所有外への波及可能性 (静的列挙)
## 親の実測とのずれ
## 総括
