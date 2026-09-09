単独段 dispatch: stage=author; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — **段 4 裁定 (最優先の正本)。設計 v2・変異事前登録・不変条件はここが確定版である。**
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md` — 段 1 brief
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md` — 段 2 プラン (裁定で上書きされた箇所がある)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s3-lensA.md` — 段 3 レンズ A
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s3-lensB.md` — 段 3 レンズ B
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。上記以外の repository 内 file は、必要と判明した場合だけ読んでよい。

## この段の仕事

段 4 裁定の「設計 v2 (確定)」を実装する。**裁定が段 2 プランと食い違う箇所は裁定が勝つ。**

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/campaign/s8c_preregistration.py`
- `orchestrator/tests/test_s8c_cli_entrypoints.py`
- `orchestrator/tests/test_s8c_preregistration_core.py`

**新規 file を作らない。docs を編集しない。commit しない。push しない。** `git add` も `git commit` もしない。統合と commit は親が行う。

### 実装の要点 (裁定「設計 v2」の 1〜7 を全部満たすこと)

1. `EvaluatorExceptionReason` を独立した frozen dataclass として足す。`ActivationReport` /
   `PredicateResult` / `EvidenceRef` の field は 1 つも増減しない。
2. 診断抽出 helper は **total** にする。例外 object から値を取り出す全処理を自身の `try` で囲み、
   何が起きても診断 object を返す。**診断生成が原因で例外が外へ漏れてはならない。**
3. 3 field はすべて安全な文字列へ正規化する。`callsite` は実装が与える固定 literal のみ。
   `exception_type` と `preregistration_reason` は型・charset・長さを検査し、外れたら固定 sentinel。
   **`str(exc)`・detail・message・traceback・repo path・環境値は 1 つも入れない。**
4. sentinel は診断専用の固定文字列で、`reason_code` として使わない。
   `ReasonCode` / `REASON_CODES` を拡張しない。
5. `_default_registry_results` の現行 1 つの `try` を「evaluator 呼出し」と
   「`_normalize_predicate_results` 呼出し」の 2 節に分ける。**`_normalize_predicate_results(raw)` の
   呼び出し全体を第 2 try の内側に置く。`tuple(raw)` 等の materialize を 2 つの try の間へ出さない**
   (遅延 generator の例外が漏れる)。両 catch の型は `except Exception as exc` のままにし、
   捕捉集合を変えない。`get_registry()` など現在 try 外にある処理を try 内へ移さない。
6. test-registry 経路 (`allow_test_registry` の分岐) も同じ形で診断を返す。**この分岐だけ診断を
   空にしてはならない。**「診断が空 ⟺ 例外を握り潰していない」を成立させる。
7. `activation_report_at` と `_activation_report_at_for_test` の既存 signature と返り値の型を変えない。
   診断つきの新 sibling API を足し、production sibling に `registry` 引数を露出しない。
8. CLI `check` だけが sibling API を呼び、診断を **stderr** へ 1 件 1 行の compact JSON object で出す。
   **stdout の形と bytes を 1 bit も変えない。** 終了値も変えない。`--json` 指定時・非指定時の両方で
   同じ stderr 挙動にする。診断が無ければ stderr は完全に空。
9. `callsite` は「例外の意味上の発生源」ではなく**捕捉した評価地点**であることを docstring に明記する
   (遅延 generator の例外は normalize 側 callsite になる)。

### テスト (裁定「設計 v2」の 5・6・7)

裁定の「必須 assertion」を**すべて**実装する。到達方法は裁定の 5 に従う。

- **実 process 方式 (CLI e2e):** temporary repo に変更後の core・projection・**11 件しか返さない
  evaluator** を同じ bytes で配置して commit し、`cwd=<temporary repo>` の `-m` 形式と、
  temporary repo 側 core file の path 直接起動の両方で CLI を走らせる。
- **直接呼び出し (単体):** `_default_registry_results(root, commit, module)` の `module` 引数は
  設計上の正規注入 seam である。ここへ module 様 object を渡してよい。
- **monkeypatch は使わない。** 正規注入 seam が実在するので最後の手段に当たらない。
- `_default_registry_results` / `_normalize_predicate_results` / 診断 helper / sibling API を
  **stub しない。** stub すると機構を通らない緑になる。

既存テストの期待値を変更・反転・緩和・skip・削除してはならない。唯一の例外は
`orchestrator/tests/test_s8c_preregistration_core.py` の `test_non_json_cli_reports_decider_reason` で、
monkeypatch 対象を新 sibling API へ合わせ返り値を `(report, ())` にする追随だけを許す。
**exit code と stdout の期待値は 1 文字も変えない。**

fixture へ現行 hash を差し込んでテストを甘くしない。期待値へ揮発 payload (working tree hash、
temporary path、時刻) を焼き込まない。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- 実走した nodeid と結果を報告に書く。**子の実走は親の全走を代替しない。**
  実走できなかったものは「緑」と書かず「実装済み・未実走」と書く。

## 禁止

- 上記 3 file 以外の変更、新規 file の作成、docs 編集、`git add` / `git commit` / push。
- 受理集合を広げる変更 (現行 `ERROR` が `ERROR` でなくなる、`reason_code` 文字列が変わる、
  `effective` が真になりうる、`_activation_report_digest` が同一 report で変わる)。
- `ActivationReport` / `PredicateResult` / `EvidenceRef` の field 増減。
- 新しい gate・検査・台帳・一般化の追加 (裁定の scope 外)。
- 既存テストの期待値の変更 (上記の唯一の例外を除く)。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 現行の受理・拒否挙動` — 変更前に、対象経路が現在どう受理・拒否しているかを明記する
- `## 実装した差分` — file:line で何をどう変えたか
- `## 追加したテスト` — 各テストが固定する命題と、裁定の「必須 assertion」との対応表
- `## 実走した nodeid と結果` — 自走 harness の実走範囲と結果。未実走はそう書く
- `## 波及の静的列挙` — 所有外 caller・共有 fixture・consumer test への波及可能性
- `## 不変条件の自己検査` — 裁定「不変条件」1〜7 の各項について、満たした根拠を 1 行ずつ
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
