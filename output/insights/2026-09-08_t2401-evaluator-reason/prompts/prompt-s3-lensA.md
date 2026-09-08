単独段 dispatch: stage=consult; sandbox=read-only; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/brief.md` — 親の段 1 brief
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s2-plan.md` — 段 2 のプラン (攻撃対象)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration_evidence.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/trial_registry.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_gate_report.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/campaign_lock.py`

上記以外の repository 内 file は、上の file から辿って必要と判明した場合だけ読んでよい。
repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない。

## この段の仕事 — レンズ A: 正しさ境界と受理集合

段 3 の敵対相談である。**プランを守らせるのではなく壊しに行く。** 親の brief 自身も攻撃対象である。実装・編集・commit はしない。出力は最終メッセージ本文にすべて書く (file へ書けない sandbox である。省略記号で途中を切らない)。

sandbox は read-only で書込み可能な tmp が無いため、**pytest 実走は要求しない。静的検査でよい。**実走していない結果を「緑」と書かない。

このレンズの攻撃面は次のとおり。すべて `file:line` を添えて具体的に述べること。

1. **受理集合が 1 bit でも広がる経路。** プランの差分を当てた後に、現在 `ERROR` に倒れているどれかが `ERROR` でなくなる、`reason_code` が変わる、`effective` が真になりうる、`_activation_report_digest` が変わる経路があるか。無いなら「無い」ではなく、なぜ無いかを構造で述べる。
2. **try の分割が捕捉集合を変える可能性。** プランは現行の 1 つの `try` を「evaluator 呼出し」と「normalize 呼出し」の 2 節に分割する。この分割で、現在捕捉されている例外が捕捉されなくなる (外へ漏れる)、あるいは現在捕捉されていない例外が新たに捕捉される (受理側へ倒れる) ケースを探せ。generator を返す evaluator、`__iter__` の遅延評価、`tuple()` 化の時点など、評価タイミングが移動する経路を特に見よ。
3. **診断 channel が正しさ防壁を弱める経路。** 新しい sibling API が、`require_effective_preregistration` / `effective_at` / `trial_registry` の capability 検証を迂回する入口になりうるか。診断つき API から得た report を、検証を通さずに consumer が使える形になっていないか。
4. **親 brief の不変条件 2 の裏取り。** 「`ActivationReport` に field を足すと `trial_registry` の台帳が全件不一致になる」という親の主張を、実際のコードで検算せよ。**正しければ正しいと書き、誤りまたは過大なら訂正せよ。** 逆に、親が挙げていない digest / pin 束縛が他にもあれば列挙せよ (`campaign_lock.py` の enforcement source closure、`_canonical_bytes` を通る他の preimage、`REASON_CODES` の閉じた語彙を検査する test を含む)。
5. **fail-closed の終端が壊れる経路。** 診断生成そのものが例外を送出したら何が起きるか。`type(exc).__name__` や `exc.reason` の取得が失敗する例外 object (`reason` 属性が無い `PreregistrationError` subclass、`__name__` が異常な型) を渡されたときに、fail-closed の返却が例外送出に変わらないか。
6. **規律 2 / 規律 3 の観点。** この差分が「検証を甘くして通す」方向へ寄与しうる面があるか。逆に、診断を残すことが「なぜ壊れたか」の構造化として実際に十分か (F631 の真因 `PreregistrationError("predicate-result-type")` が、この設計で本当に人間に届くか)。

## 禁止

- 実装・編集・commit・push。
- 新しい gate・検査・台帳・一般化の追加提案 (親 brief の scope 外)。思いついたら `## scope 外の所見` へ分けて書く。
- 既存テストの期待値の変更・反転・緩和・skip・削除の提案。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。所見は 1 件ずつ `- 所見 N (深刻度: blocker | must-fix | nit):` の形で番号を振り、**それぞれに「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で書く。書けない所見は nit にする。**

- `## 受理集合`
- `## 捕捉集合の変化`
- `## 診断 channel と正しさ防壁`
- `## digest / pin 束縛の検算`
- `## fail-closed 終端`
- `## 規律 2 / 3`
- `## scope 外の所見`
- `## 総括`

予算が尽きそうなら、その時点の途中結論をこの出力形式どおりに書いて終われ。無出力が最悪である。
