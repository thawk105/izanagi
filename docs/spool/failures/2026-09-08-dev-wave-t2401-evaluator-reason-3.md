---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2401-evaluator-reason
seq: 3
---

## 新規

### {{F:hostile-fixture-breaks-failure-reporting}}. 敵対 fixture が pytest の失敗報告経路を壊し、変異走行が失敗 node を抽出できなくなる [テスト代表性] [恒真ゲート]

- 事象: 診断抽出の totality を検査するために、`__name__` の取得で例外を出す metaclass と、
  `KeyboardInterrupt` を送出する property を fixture に置いた。正常時は全件緑だったが、
  変異走行で近傍のテストが落ちた瞬間に走行系が壊れた。2 形を実測した。
  (a) metaclass が `SystemExit` を出す形では pytest が `INTERNALERROR` を出して xdist worker が死に、
  rc=3 になった。失敗は failure digest に出るが `FAILED` の要約行が出ないため node を抽出できない。
  (b) `KeyboardInterrupt` を出す形では pytest が session 中断と解釈して rc=2 を返した。
  変異 harness はどちらも rc が 0/1 でないため結果を分類できず停止した。
- 根本原因: pytest は失敗を整形するとき `_pytest/_io/saferepr.py` -> `reprlib.repr1` ->
  `typename = type(x).__name__` を通る。敵対的な属性取得はこの経路で発火する。
  **正常時に緑であることは、失敗時に正しく報告できることを含意しない。**
  `KeyboardInterrupt` と `SystemExit` は runner が特別扱いする型でもある。
- なぜ静的レビューで捕まらなかったか: 段 3 の敵対相談 2 本と段 6 の焦点再レビュー 1 本は、
  いずれもこの型を挙げなかった。**テストが緑になる経路しか読んでおらず、
  テストが落ちたときに走行系がどうなるかを誰も見ていなかった。**
- 恒久対応: 危険な挙動は検査対象の呼び出しの瞬間だけ有効にする (arm / disarm)。
  armed でない状態で `repr(instance)` / `repr(type(instance))` / `type(instance).__name__` を
  評価しても例外が出ず `__name__` が `str` であることを assertion で固定する。
  `BaseException` の負例には、runner が特別扱いしない専用 subclass を使う
  (`Exception` を継承すると「`except Exception` では捕まらない例外」という命題が検査できない)。
  実体は `orchestrator/tests/test_s8c_preregistration_core.py` の arm 機構と
  `_DiagnosticGuardBaseException`。
- 再発検知: 敵対 fixture を足した wave では、**その fixture を使うテストを意図的に失敗させて
  harness の rc が 1 であることを実測する**。rc が 2 や 3 なら本件である。

### {{F:guard-test-cannot-observe-the-guard}}. 例外 guard の検査が guard の有無を区別できていなかった [恒真ゲート] [テスト代表性]

- 事象: CLI の診断出力を囲む `except Exception` を `except ZeroDivisionError` /
  `except OSError` へ狭める変異が、事前登録した 26 変異のうち 2 件として生存した。
  対応する 2 つのテストは緑のままだった。
- 根本原因: テストは子 process で `sys.stderr` を「write すると例外を出す object」へ差し替え、
  `raise SystemExit(main([...]))` を実行し、stdout の完全一致・`returncode == 1`・
  `stderr == b""` を検査していた。**guard が捕まえなくてもこの 3 つはすべて成立する。**
  例外が `main()` の外へ出ると未処理例外になるが**その終了コードも 1** であり、
  traceback は差し替えた object へ書かれるので**実 fd 2 は空**、stdout は診断より前に出力済みで
  **不変**である。「guard が効いて `main()` が値を返した」ことを 1 つも観測していなかった。
- 恒久対応: `main()` の返り値を受け取れたこと自体を、壊れていない出力先へ記録し、
  その実在と値を assertion で固定する。実体は
  `orchestrator/tests/test_s8c_cli_entrypoints.py` の
  `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror` と
  同 `_value_error` の返り値記録 assertion。
- 再発検知: 「例外が握り潰されること」を検査するテストを書いたら、**握り潰しを外す変異を
  事前登録して実際に走らせる**。生存したら、そのテストは guard を観測していない。
  終了コードだけを見る検査は、未処理例外の終了コードと衝突しうる。

## supersede 追記

- F631 **supersede: 2026-09-08** — 「なぜ通らなかったかが消える」部分のコード側修正が着地した。評価器呼び出しを囲む広い例外捕捉は、fail-closed の終端 (12 件の `ERROR / evaluator-exception`、`effective=False`、CLI stdout の bytes、report digest) を 1 bit も変えないまま、捕捉した理由を `callsite` / `exception_type` / `preregistration_reason` の 3 field へ構造化して残すようになった。判定器 CLI の `check` はこれを stderr へ 1 行の JSON で出す。設計と却下案は {{D:evaluator-diagnostic-outside-report-digest}}。**gate report CLI と、判定器 CLI の外側 catch が出す `str(exc)` は本 wave の対象外である。**
