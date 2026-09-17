## 総括

- **real 5件 / refuted 4件 / nit 2件。must-fix あり。**
- 主な問題は、同 session の非祖先を workload と同一視すること、環境変数を継承する既存テスト、M6 の変異帰属です。
- 通常の計算ノード起動では、提案された pop 位置で pytest への opt-in 継承を遮断できます。
- 新規の実 process fixture は、plan どおりなら login node の pytest session を走査しません。
- 親 brief・添付 facts への異議は **5件**。実装・テスト実行・計算ノード実測は行っていません。

## 所見

**A-1 — real / must-fix：session 所属は、終了させてよい process の帰属証明ではない。**  
位置：`s1-brief.md:33–46`、`facts.md:8`、`plan-out.md:46–68`。

祖先除外が保護するのは取得できた祖先鎖だけです。同 session の NQSV 監視 process が兄弟・その他の非祖先として存在すれば候補になります。同 uid で signal 権限があれば TERM/KILL は成功し、EPERM の catch では保護できません。plan 自身もこの穴を認めています。

trace の `resuid=[31609,31609,31609]` は **probe の値**であり、3010029 や NQSV の非祖先 process の uid は記録されていません。また、sid=3010029 から、その番号の process が観測時点で生存し、dispatcher の現在の祖先であることまでは導けません。

**放置時の影響：** scheduler 側 process を終了させ、job の正常終端・会計記録を損なう可能性があり、no-child で残存ゼロだった1走だけでは安全性を一般化できません。  
**是正案：** signal 前の観測で job session 全体と祖先鎖を確認し、非祖先の帰属を確定する。uid フィルタは異 uid を候補から外す補助として採用するのが妥当ですが、同 uid の非 workload は防げません。「同 uid＋同 session」だけを安全性の根拠にせず、帰属不明の対象は終了させず未完了として記録する設計に修正してください。

**A-2 — real / must-fix：既存の in-process テストは ambient opt-in に対して隔離されていない。**  
位置：`plan-out.md:111–125,183`、`orchestrator/tests/test_pegasus_dispatch_compute.py:4151,4203,5172,5398`。

これらの `patch.dict` は `clear=True` ではありません。pytest 自身の環境に opt-in=`1` があれば、hostname・envelope をテスト用に成立させた `_job_run` が pytest の session を走査します。`child_env.pop` は起動する子の辞書だけを変更し、呼出し元の `os.environ` を消しません。新規の opt-in 統合テストで実 sweep を mock する方針も、既存テストまでは覆いません。

**放置時の影響：** opt-in を継承して起動された login node の pytest が兄弟 worker 等を終了させ、受入走行自体が壊れます。  
**是正案：** 既存の in-process 呼出しでは opt-in 不在を明示的に作る。新規の有効化テストだけ局所的に設定し、実 sweep の代わりに呼出しを記録する。環境=`1` を外側に置いた場合も、既存 helper が実走査へ到達しない負例を用意してください。通常の job 経由の漏れとは区別すべき問題です。

**A-3 — real / 安全性保証の限界：starttime 再読は signal 対象を原子的に固定しない。**  
位置：`plan-out.md:56–68`。

plan の自己申告どおり、stat 再読後、`os.kill(pid, sig)` 前に対象が消滅して pid が再利用されれば、別 process に signal できます。同じ窓での session 離脱も再確認では防ぎ切れません。提案テストは「再読時点ですでに変わっている場合」を検証するもので、この窓の否定にはなりません。

**放置時の影響：** 競合が起きた場合、対象外 process を終了させ、「別 session へ移った process には触れない」という不変条件を破ります。  
**是正案：** PID 再利用に対しては pidfd による対象固定を検討し、取得後にも記録との同一性を確認する。pidfd でも session 判定と送信は原子的にならないため、絶対保証と直前確認による保証を明確に分けてください。現案を「取り違えが不可能」として受理することはできません。

**A-4 — real / must-fix：M6 は指定した1行変異で赤になるとは限らない。**  
位置：`plan-out.md:77–83,198–200`。

M6 が削除するのは TERM 猶予後の再列挙だけです。しかし、その後に **KILL 後の再列挙**が残ります。初回 snapshot にいない C はそこで発見され、次巡に TERM・消滅確認されます。したがって、登録された「C への TERM・消滅記録」という判定は、正常版と変異版の両方で成立し得ます。

**放置時の影響：** M6 が SURVIVED となるか、fake の応答順に依存した赤を再列挙の検出力として台帳に誤帰属します。  
**是正案：** 必要な性質を「後発 process を次巡で処置する」と定め、その性質を実際に失わせる行を変異対象にする。特定の中間再列挙だけを必須とするなら、後段では代替できない役割と反例を先に示してください。列挙の呼出し番号だけで対象の出現を演出してはいけません。

**A-5 — real：heartbeat の時刻条件が正常な TERM 終了を棄却する。**  
位置：`plan-out.md:237–245`。

`session-signal-attempt` は signal 送信前の記録です。その記録後、実際の TERM 送信・配送までに子が heartbeat を記録することは可能です。対象が正しく TERM で終了しても、`最終heartbeat ≤ attempt時刻` は成立しません。

**放置時の影響：** 正しく回収できた keep 走を期待外として扱い、レポートの成否判定と追加走の要否を誤ります。  
**是正案：** heartbeat は補助観測に留め、attempt 後の記録だけで失敗にしない。同一性を伴う消滅確認、自然寿命より前の終了、会計終了を主要な判定にしてください。

**A-6 — refuted：通常の job 起動で bound bootstrap が opt-in を再注入する。**  
位置：`tools/pegasus/dispatch_compute.py:197–208,1198–1244,1623–1627`、`plan-out.md:110–125`。

提案位置は overlay 後、child 分岐前です。`_run_bound_tests_child` は渡された `child_env` を git と `_run_isolated_child` に渡し、後者も `Popen(env=dict(env))` を使います。隔離 bootstrap の `execvpe(..., os.environ)` が継承するのはその環境です。bound bootstrap 自体に再注入はありません。

**影響判定：** 提案どおりなら、この伝播経路による計算ノード上の入れ子 pytest の誤発火は防げます。  
**対応：** 実 wrapper を通し、最終的な子起動境界で env 不在を検証する。wrapper と起動境界の両方を stub して確認を省略しないこと。

**A-7 — refuted：新規 fixture の leader は祖先除外できず、login session を巻き込む。**  
位置：`plan-out.md:172–179`。

plan は pytest が別 session の L を作り、その子 S が自身の sid を走査する構成です。L は S の祖先なので除外できます。pytest が自分の session から L の sid を渡して走査する構成ではありません。M2 で L が終了しても、その session は pytest と別です。

**影響判定：** 記載どおりの構成なら、この懸念による login session の誤殺はありません。  
**対応：** L の生存確認は finally の回収前に行い、正常な scanner 完了と祖先保護を別々に assert してください。

**A-8 — refuted：新 sweep が F973 と同じ zombie 計数変更を導入する。**  
位置：`plan-out.md:89–104`、`tools/pegasus/dispatch_compute.py:282,328,1131`。

plan は reparenting を変えず、Z を signal 対象から外しても消滅済みには数えません。`absent`・`identity-changed`・`left-session`・読取り不明も区別しています。既存 consumer の受理集合を変更する案ではありません。

**影響判定：** F973 と同じ原因の再導入は設計上認められません。ただし受入全走の緑は未確認です。  
**対応：** M5 は実際の確認・集計処理を通し、同一 stat が残る間に gone が増えないことを検証する。ENOENT と読取り異常を同じ `None` に潰さないこと。

**A-9 — refuted：配置案が必然的に child_rc・result schema・envelope 契約を変更する。**  
位置：`plan-out.md:129–147`、`tools/pegasus/dispatch_compute.py:1519–1526,1684–1709`。

提案位置は child の例外処理後、isolation 失敗 return 前です。wrapper が sweep 例外を trace 化すれば child_rc を保てます。export 追加は既存 substring を残し、payload に field を追加する必要もありません。subreaper・PID namespace・job body の setsid・正しさ gate の変更も提案されていません。

**影響判定：** 記載どおりなら既存の結果契約は維持できます。  
**対応：** 例外テストでは実 wrapper 内の sweep に例外を注入する。wrapper 自体を「成功する mock」に置換して例外封じ込めを検証したことにしないでください。`session-sweep-complete` だけで成功とせず status と不明件数を見る設計も維持すべきです。

**A-10 — nit：F-3 の isolation 失敗位置が誤っている。**  
位置：`facts.md:17–18`、`tools/pegasus/dispatch_compute.py:1675–1687`。

実際の早期 return は 1685–1687、child 呼出しは 1648–1674 付近です。plan は配置を補正済みです。  
**影響判定：** 現 plan に従う限り成果物・受入への直接影響はありません。  
**是正案：** facts と brief のアンカーを現コードへ合わせる。

**A-11 — nit：「session 走査が唯一」「reparenting のため再列挙」は説明が過剰。**  
位置：`facts.md:14`、`s1-brief.md:40`、`plan-out.md:85–87`。

孤児化後の現在の親子鎖だけでは拾えませんが、それは session 走査が唯一の方法である証明ではありません。D1002 にも過去標本・job 固有 path の帰属があります。また ppid の変更だけでは sid 一致の候補から消えません。plan が述べる fork・後発 process が再列挙の適切な理由です。  
**影響判定：** 現 plan は理由を補正しており、直接の受入変更はありません。  
**是正案：** 「今回採用する経路」と書き、再列挙の理由を後発 process に揃える。

## 親 brief への異議

1. **P1・P7 / F-1：** 祖先除外だけでは NQSV 側全体を保護できず、EPERM 前提も成立しません。pid/sid の実値は整合しますが、「現在も同 session に祖先が最低1ついる」という結論は trace の観測範囲を超えます。
2. **P2：** child_env の pop は必要かつ通常経路には有効です。ただし、既存 pytest 自身が opt-in を継承した場合の安全性まで保証しません。
3. **P3：** 再列挙の必要性を reparenting に帰属する説明には異議があります。plan の後発 process という説明へ修正すべきです。
4. **F-2：** 「session 走査が唯一の経路」は撤回すべきです。
5. **F-3：** isolation 失敗の行番号・return 位置が不正確です。plan の補正を facts に反映してください。

P4 の有限予算、失敗で child_rc を変えない方針、P5 の限定した generic probe による評価には異議ありません。ただし、これらは任意の残存 process の回収保証ではありません。

## 言えないこと

- 指定 trace は session 全員の一覧ではありません。NQSV の同 uid 非祖先 process の存在・不存在、3010029 の生存・祖先関係は確定できません。
- F-5 の全 worktree 調査・consumer ゼロ、F-6 の probe hash・実装は、指定された資料だけから独立再検証していません。
- 新規実装がないため、M1〜M5 の KILLED、例外処理の網羅性、13秒予算の実効性は未検証です。M6 には上記の設計上の反例があります。
- 2巡後の増殖、別 session への離脱、子待機から戻らない経路は現案の回収保証外です。
- generic 2走が成功しても、D2124 が未確定とした実 workload への適用性や受入全走の緑を代替しません。