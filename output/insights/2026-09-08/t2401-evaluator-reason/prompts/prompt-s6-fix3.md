単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md` — **段 6 裁定 3 巡目 (この段の正本)。実測した停止理由と fix scope はここが確定版である。**
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7。**不変**)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py` — 参照のみ (変更しない)

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。現在の tip は commit `f3c6f1c9d`。

## 親が実測した事実 (推測ではない)

変異走行で `_default_registry_results` の fallback status を `ERROR` から `SATISFIED` へ変えたところ、
その変異で落ちるはずの 3 件は落ちたが、**pytest 自身が `INTERNALERROR` を出して worker が死に、
rc=3 になった。** 停止した箇所は次のとおり。

```
INTERNALERROR> E   File ".../orchestrator/tests/test_s8c_preregistration_core.py", line 529, in __getattribute__
INTERNALERROR> E     raise SystemExit("secret-detail")
INTERNALERROR> E   SystemExit: secret-detail
INTERNALERROR> AssertionError: ('orchestrator/tests/test_s8c_preregistration_core.py::test_invalid_exception_type_uses_bounded_sentinel_without_leaking[hostile-type-name]', <WorkerController gw47>)
```

pytest は失敗を整形するとき `_pytest/_io/saferepr.py` → `reprlib.repr1` → `typename = type(x).__name__`
を通る。本 wave が足した敵対 fixture の metaclass `__getattribute__` がここで `SystemExit` を送出し、
worker が落ちる。**失敗すると走行そのものを壊すテストになっている。**

## この段の仕事

段 6 裁定 3 巡目の「fix の scope」1〜3 を**そのまま**実装する。**それ以外を実装しない。**

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/tests/test_s8c_preregistration_core.py`

`orchestrator/campaign/s8c_preregistration.py` を変更しない。他の test file も変更しない。
新規 file を作らない。docs を編集しない。`git add` / `git commit` / push をしない。

### 実装

1. **敵対的な挙動を、検査対象の呼び出しの前後だけ有効にする (arm / disarm)。**
   `__getattribute__` / property / metaclass が例外を送出したり非文字列を返したりするのは、
   診断抽出を呼ぶ**その瞬間だけ**にする。それ以外の時点では通常の class・通常の属性として
   振る舞わせる。context manager でも明示的な flag でもよいが、**例外が起きても必ず disarm
   される**形にすること (`try` / `finally` か context manager)。
2. **対象は本 wave が足した敵対 fixture すべて。** `SystemExit` を送出する型、
   非文字列の `__name__` を返す型、`reason` 属性が無い / 非文字列 / 例外を出す型を含む。
   `reprlib` は `type(x).__name__` を直接読むため、**非文字列の `__name__` も pytest の
   報告経路を壊しうる**。同じ扱いにすること。
3. **armed でない状態で安全であることを機械で固定する。** 各敵対 fixture の instance と型に対し、
   armed でない状態で `repr(instance)`、`repr(type(instance))`、`type(instance).__name__` を
   評価しても例外が出ず、`__name__` が `str` であることを assertion で固定する。

### 変えてはならないもの

- **固定している命題。** 敵対的な `__name__` / `reason` が診断専用 sentinel へ倒れること、
  detail・message・path が診断のどの field にも現れないことは、これまでどおり固定する。
  arm 区間を絞るのは**危険な挙動が有効な区間**を変えるだけであり、命題は 1 つも変えない。
- 既存テストの期待値。反転・緩和・skip・削除を禁じる。
- `orchestrator/campaign/s8c_preregistration.py` の中身。
- 段 4 裁定の不変条件 1〜7。

fixture へ現行 hash を差し込んでテストを甘くしない。期待値へ揮発 payload を焼き込まない。
`_default_registry_results` / `_normalize_predicate_results` / 診断 helper / sibling API を stub しない。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- **加えて、次を必ず自分で確かめて報告に書くこと。**
  敵対 fixture を使う test を**意図的に失敗させたときに、pytest が traceback を整形できること**。
  自走 harness の中で一時的に assertion を反転させる等の方法で確認し、**確認後は必ず元に戻す**
  (最終差分に反転を残さない)。反転を残していないことを `git diff` で確かめて報告すること。
  この確認ができない場合は「未確認」と正直に書く。

## 禁止

- 上記 1 file 以外の変更、新規 file の作成、docs 編集、`git add` / `git commit` / push。
- production コードの変更。
- 既存テストの期待値の変更・反転・緩和・skip・削除 (上記の一時確認は最終差分に残さない)。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 直した内容` — file:line で何をどう変えたか
- `## 固定している命題が変わっていないこと` — 各敵対 fixture について 1 行ずつ
- `## 失敗時に pytest が整形できることの確認` — どう確かめたか、結果、反転を戻したことの確認
- `## 実走した nodeid と結果`
- `## production 無変更の確認`
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
