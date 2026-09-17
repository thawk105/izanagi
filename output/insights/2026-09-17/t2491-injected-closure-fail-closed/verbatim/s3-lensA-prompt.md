単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s1-brief.md (親の段 1 brief。末尾の「v1.1 訂正」が最新の P1/P2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s2-plan.md (段 2 plan。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1869.md (裁定 D1869 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/F918.md (失敗の型 F918 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (対象 test。1168〜1222、1367〜1454、1499〜1600、1700〜1760、1766〜1900、2002〜2025、2147〜2190、2582〜2700、2864〜3210 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。50〜56、95、996〜1030 行。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。113〜126、358〜404、1151〜1153、1204〜1345、1380〜1390 行。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。62〜69、104、1655〜1665、1726〜1734、1774〜1825、1836〜1862 行。変更禁止、読むだけ。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2491] の段 3 敵対相談役 **レンズ A (規律 2 / fail-closed の穴)**。plan を守らず、**brief v1.1 の P1/P2 (「握り潰されていない」の定義) を通り抜ける
握り潰し・無効化の形**を探せ。親 brief 自身も検査対象である (親の実測値とその一般化、file:line、前提を疑え)。pytest は走らせられない (書込可能 tmp が無い)。
静的検査だけでよく、緑を主張するな。

**文脈:** F918 は、n_pilot の `except S1DriverError as exc: raise PilotError(...) from exc` を `except S1DriverError: pass` に変えても閉包検査が緑のままだと実測した。
D1882 は「弱い一致だけでは被覆済みに数えない、fail-closed 側へ寄せる、名指しした判定だけ変える (D1869)」と裁定し、「import 真正性・shadow・支配関係まで静的に検査する」
案は族全体の新機構として却下した。親は P1/P2 (v1.1) を provisional 裁定としている。

## 答えるべきこと

1. **P1/P2 (v1.1) を通り抜ける形の列挙:** 次の各形について、新判定が「被覆に数える (穴)」か「数えない (fail-closed)」かを v1.1 の規則の逐語に沿って判定し、穴なら real/refuted・
   scope 内/外 (D1882 の名指し = 「弱い一致だけで被覆済みに数える」判定) を分けて返せ。
   (a) DEFINITE handler の末尾が `raise` だが、その直前に無条件 `return` がある (到達不能 raise)。
   (b) DEFINITE handler 内で `raise` が `try/finally` の finally 側にあり、finally が `return` で終わる (例外を消す)。
   (c) enclosing try の `finalbody` が `return` / `break` / `continue` で終わる (Python は finally の return で例外を消す)。
   (d) `with contextlib.suppress(Exception):` の中の check。
   (e) 関数内の局所 alias `E2 = S1DriverError` を handler 型に使い `pass`。
   (f) module scope で `E2 = S1DriverError` の alias chain (plan は `module_assignments` で引くと言う) と、`E2 = getattr(mod, "DriverError")` のような式。
   (g) `except (S1DriverError, PilotError): pass` (tuple の DEFINITE)。
   (h) `except* S1DriverError: pass` (TryStar)。
   (i) check call を lambda / 内包表記 / 別の入れ子関数 (`def _check(): require_returned_condition_evidence(built)`) に包み、その呼出しを握り潰す。
   (j) check を `if False:` / `if enabled:` の中に置く (条件 guard)。既存の injected 経路がこれを何も検査しないのは v1 と同じで、D1882 の名指し外か。
   (k) `result_name` の再束縛 (`built = other` を check の前に置く) と、check の第 1 引数が `built` のまま別物を検査する形。
   (l) DEFINITE handler が `raise` で終わるが、それは `raise SystemExit(0)` / `raise StopIteration` など「例外でない終了」。
   (m) MAYBE handler (`except wal.WalAppendError:`) が変換再送出 → v1.1 は「被覆に数えない」とする。これは過剰拒否か、fail-closed として正当か。
   (n) 変換再送出 (`raise PilotError(...) from exc`) で追跡を止める規則: 外側 try が `except PilotError: pass` なら握り潰されるのに被覆に数える。これを「名指し外の保証限界」とする親の読みは妥当か、
       それとも D1882 の「fail-closed 側へ寄せる」に反するか。
2. **親の実測値の一般化:** 「helper は base の `DriverError` を直接 raise する」「`DriverError(RuntimeError)`」「production 4 箇所の handler 順」を s1 358〜404 行と production で確認し、
   規則が依存する前提に漏れがないか (例: helper が内部で呼ぶ関数が別の例外を送出する経路、`observed_requests` 内の raise、`DriverError` の子 class を helper が送出する経路)。
3. **NONE 分類の健全性:** 「本 file の module scope ClassDef (E 以外) に束縛された名前は E を捕まえない」は、`class Foo(DriverError)` (子) なら正しい。`class Foo(RuntimeError)` を
   `DriverError = Foo` のように**再束縛**する形、`class DriverError(...)` を s1 以外の module で定義して helper を自 module で定義しない形、などで破れるか。
4. **規律 2 との整合:** v1.1 は v1 (全 enclosing try に P1/P2) より受理形が広い (変換再送出で追跡を止める)。これは「受理形を増やす向きの変更」(brief 不変条件 i) に当たるか。
   現行 main (弱い一致だけ) と比べれば狭いことは確認せよ。
5. **推奨:** 穴のうち、本 wave の scope 内 (名指しの判定の中で閉じる、族全体の新機構にならない、production 4 sink を誤拒否しない) で塞ぐべきものを最大 3 件、file:line と
   規則の追加文で示せ。残りは裁定パッケージ候補 (scope 外) として列挙せよ。

## 制約

- 出力は file に書かず、最終メッセージの本文に全文を書け。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 通り抜ける形の判定表 ((a)〜(n)、穴/fail-closed、real/refuted、scope 内/外)
## 親の実測値・前提の検証
## NONE 分類と規律 2 の整合
## 推奨 (scope 内で塞ぐ最大 3 件、裁定パッケージ候補)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
