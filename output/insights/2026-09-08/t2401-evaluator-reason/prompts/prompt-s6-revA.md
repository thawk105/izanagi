単独段 dispatch: stage=review; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件・変異事前登録の正本)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md` — 段 1 brief
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s5-author2.md` — 実装子の完了報告 (自己申告。裏を取る対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/trial_registry.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_gate_report.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。差分は commit `134e5926d` として着地済みなので、`git show 134e5926d` や `git diff 134e5926d^ 134e5926d` で読んでよい。

## この段の仕事 — 段 6 敵対レビュー・レンズ A: 実装が裁定の不変条件を本当に守っているか

**実装を守るのではなく壊しに行く。** 実装子の自己申告 (`s5-author2.md` の「不変条件の自己検査」) は主張であって証拠ではない。**コードの現物で裏を取る。** 実装・編集・commit はしない。出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest 実走は要求しない。静的検査でよい。**実走は親が行う。実走していない結果を「緑」と書かない。

裁定「不変条件」1〜7 を 1 項ずつ、コードの現物で検査せよ。

1. **受理集合を 1 bit も広げていないか。** 変更前後で、例外時の 12 件の `status` / `reason_code` / `evidence` / `effective` が完全に同じか。`_uniform_predicates(PredicateStatus.ERROR, "evaluator-exception")` が、変更前の直接構築した tuple と**要素ごとに等価**か。test-registry 経路の `registry-exception` も同様か。
2. **`ActivationReport` / `PredicateResult` / `EvidenceRef` の field が増減していないか。** `_jsonable` と `_activation_report_digest` の preimage が同一 report で不変か。新 dataclass が digest preimage に混入する経路が 1 つも無いか。
3. **CLI stdout の形と bytes が不変か。** `--json` と非 `--json` の両方で、print の順序・内容・改行が変更前と同一か。診断の出力が stdout へ漏れる経路が無いか。終了値が変わっていないか。
4. **stderr に危険な payload が出ないか。** `callsite` / `exception_type` / `preregistration_reason` の 3 値それぞれについて、**外部から制御できる文字列が生のまま出る経路**を探せ。charset・長さ検査を迂回できる入力はあるか。`str(exc)`・detail・traceback・repo path・環境値が混ざる経路は本当に無いか。
5. **新規 file が無いか。** commit の変更 file 集合を確認せよ。
6. **`ReasonCode` / `REASON_CODES` が拡張されていないか。** 診断 sentinel が predicate の `reason_code` として使われる経路が無いか。
7. **fail-closed の終端が壊れていないか (最重要)。** 診断生成 helper が **total** か。次を具体的に攻撃せよ。
   - `type(exc).__name__` の取得が例外を出す型 (hostile metaclass、`__getattribute__` を上書きした型)。
   - `isinstance(exc, PreregistrationError)` 自体が例外を出す型 (`__class__` property、`__instancecheck__`)。
   - `exc.reason` が property で例外を出す / 非 str / 巨大文字列 / 再帰的 object。
   - `len()` や正規表現 `fullmatch` が例外を出す入力。
   - helper の外側 (2 つの `except Exception as exc:` block の中、`EvaluatorExceptionReason` の構築、
     tuple 化、返り値の unpack) で例外が出る経路。
   - CLI の `json.dumps(_jsonable(diagnostic))` が失敗しうる入力。
   - **`except Exception` では捕まらない `BaseException` 直系が診断生成中に出た場合。**

さらに次も検査せよ。

- **try 分割の副作用。** `raw = evaluator(...)` を第 1 try に、`_normalize_predicate_results(raw)` を第 2 try に置いた結果、**変更前に捕捉されていた例外が捕捉されなくなる、または変更前に捕捉されていなかった例外が捕捉されるようになる**経路があるか。遅延 generator、`__iter__`、`__next__`、`__len__` の評価タイミングを具体的に追え。
- **診断の完全性。** 「診断が空 ⟺ 例外を握り潰していない」が全経路で成立するか。例外を握り潰しているのに診断が空になる分岐、逆に例外が無いのに診断が非空になる分岐を探せ。
- **既存 consumer への波及。** `activation_report_at` / `_activation_report_at` / `_activation_report_at_for_test` / `effective_at` / `require_effective_preregistration` の signature と返り値が変わっていないか。`s8c_gate_report.py` と `trial_registry.py` から見た挙動が変わる経路が無いか。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案 (裁定の scope 外)。`## scope 外の所見` へ分けて書く。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

所見は 1 件ずつ `- 所見 N (深刻度: blocker | must-fix | nit):` の形で番号を振り、**それぞれに「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で書く。書けない所見は nit にする。** 所見ゼロなら「所見ゼロ」と明記し、そう判断した根拠を各不変条件について 1 行ずつ書く。

次の H2 見出しをこの順で使う。

- `## 不変条件 1〜7 の逐条検査`
- `## try 分割の副作用`
- `## 診断の完全性`
- `## 既存 consumer への波及`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
