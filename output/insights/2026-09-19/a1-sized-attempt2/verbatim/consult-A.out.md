## 所見

以下、`brief` は指定の `brief.md`、`materials/*` は同 job dir の射影資料、`事前登録` は sized-preregistration の README、`attempt1稿` は指定の results 稿を指す。静的検査のみ実施し、投入・変更・pytest は行っていない。

1. **real — 「import 閉包で変わった file は 2 本だけ」は誤り。**

   `git diff d2ebef7a4 a99425b66` で、直接 import される `condition_meaning_gate.py` と `trial_registry.py` にも変更を確認した。前者は MOCC define 登録の追加、後者は attempt registry 履歴検査の変更を含む。さらに `layout.py` は新規の `agent_outputs.py` を import し、`trial_registry.py` の import 先である `autonomous_trial_completeness.py` と `s8c_acceptance_receipt.py` にも差分がある。
   
   根拠: `brief:34–36`、`orchestrator/campaign/paper_story_a1_paired.py:47–68`、`orchestrator/campaign/layout.py:33`、`orchestrator/campaign/trial_registry.py:32–46,2699`、`orchestrator/campaign/condition_meaning_gate.py:205`。
   
   **放置時の影響:** results 稿・台帳が、未確認の閉包同一性を比較可能条件の実測済み事実として記録する。

2. **根拠不足 — 束縛 9 file と CCBench pin の一致だけでは、測定・判定の等価性を証明できない。**

   束縛外 module は実際に A-1 から呼ばれる。たとえば条件関門は `condition_meaning_gate`、非認証 projection 発行は `trial_registry` に依存する。ただし、確認した条件関門の変更は MOCC 用で、A-1 の要求は `BACKOFF_FIXED`。registry の変更箇所も、確認した A-1 projection 発行経路とは別である。**親の閉包調査は誤りだが、A-1 の数値・verifier 判定が変わる具体的反例までは得ていない。**
   
   「同じ測定条件・解析規則」と「同じ測定値が出る」は別であり、環境契約が同じでも後者は保証されない。
   
   根拠: `paper_story_a1_paired.py:6891–6934,7084–7095`、`trial_registry.py:4167–4195`、`brief:55`。
   
   **放置時の影響:** commit 差・実行環境差を未評価のまま「測定は等価」と記し、観察以上の比較可能性を主張する。

3. **refuted — §6.1 から「study 全体で公開は一度だけ」「対案 (a) は必ず迂回」とは導けない。**

   実装は `repo_root / policy の相対 path` と宛先の一致、およびその宛先の不存在を検査する。study 全体・全 worktree を横断した公開回数の検査ではない。§6.1 も宛先の一度限りの作成を述べており、第二 attempt 自体の禁止は述べていない。D2096 は sized の attempt pin を明示的に採らない。
   
   したがって、旧 commit の clean tree 内にある正規の固定 path へ公開し、その**実際の絶対 destination を保存する**案は、直ちに事前登録違反とはいえない。repo 内の別 path に保存する場合は「公開原本の byte 同一の記録複製」と明記する必要がある。なお、実装の実効原子性まで保証する読みも強すぎる。attempt1稿は fallback の非協力的書き手に対する限界を記録している。
   
   根拠: `事前登録:328–332`、`materials/code-exact-destination.py:5–23`、`materials/d2096.md:9–16,26–28`、`attempt1稿:324`。
   
   **放置時の影響:** 有効な submit-tree 選択肢を根拠なく排除し、公開不能を study 固有の必然として台帳へ固定する。

4. **refuted — `_materialized_result` が統計値も変更するという疑い。ただし P2 は条件付きに直す必要がある。**

   v3 分岐は `**result` に `materialization_evidence` を追加するだけで、`workloads[].statistics` を変更しない。したがって raw を統計値の転記元にする技術的根拠はある。ただし公開 receipt には別途 `materialization` が追加されるため、「束全体が 1 key だけ違う」とは書けない。
   
   また materialize は、宛先検査より前に raw 文書、submission、completion、非認証 observation、source、WAL を検証する。**宛先既存による拒否**なら、測定値の無効化を意味しない。一方、これらの検証での拒否まで「公開 leaf が無いだけ」と扱うのは誤りである。
   
   根拠: `paper_story_a1_paired.py:8195–8225,8694–8734,8735–8755`、`brief:60–61`。
   
   **放置時の影響:** 証拠不整合による拒否まで公開上の限定に縮約し、受理されていない raw を受理済み結果として掲載しうる。

5. **real — attempt-0002 の転記元を results 系列の規則へ接続する変更が不足している。**

   現行規則は図の provenance JSON を転記元とし、公開 leaf の `result.json` を使う例外は **attempt-0001 を名指し**している。P3 の「図なし」と P2 の「raw から転記」を採るなら、表への行追加・stale 注記だけでは説明が閉じない。
   
   materialize 拒否は、裁定の「どこかの層で落ちた」に数える。その後の再投入・宛先変更・別 tree での再試行はしない。ただし、停止した事実を報告し、既に検証された測定を限定付きで記述することは、今回明示された results 稿作成と両立する。全層完走とは書かない。
   
   根拠: `docs/paper-story/README.md:253–265`、`brief:13–17,28,52–61`。
   
   **放置時の影響:** attempt-0002 稿の転記元が系列規則と食い違い、公開済み成果物と未公開 raw の参照上の区別が失われる。

6. **refuted — D2120 の再認可条件に抵触するという疑い。**

   D2120 は次の投入に改めて認可を要求し、今回の裁定は attempt-0002 を独立再現として **1 attempt 明示的に認可**している。この条件は満たす。§6.4 の失敗後の再走許容理由から今回の認可を捻出する必要はない。逆に、今回失敗した後は §6.4 の理由に該当しても自動で再投入できない。
   
   根拠: `materials/d2120-item3.md:5–7`、`brief:13–19`、`事前登録:371–381`。
   
   **放置時の影響:** 認可根拠を D2120 や §6.4 に取り違えると、今回の独立反復と失敗後の再投入の境界が台帳上曖昧になる。

7. **根拠不足 — 第二 attempt の実施だけでは「独立性」「反復間の安定性」は成立しない。並記は可能。**

   D1993 項 6 の逐語は A-2・A-6・balanced 対の横断集計を禁じるものであり、それ自体が全 attempt 一般の禁止を定義した文ではない。本件の非プール義務は、今回の裁定にも明示されている。
   
   表は **workload × attempt の 6 行**とし、各行に n、平均、h、B、分類、valid、出所を置けばよい。n=60、統合平均・区間・分類、成功率、「再現成功」「安定性確認」への集約はしない。同じ policy の別実行という事実は、測定値の統計的独立性の証明ではない。
   
   根拠: `materials/d1993-item6.md:1–3`、`brief:5–8,17`、`事前登録:128–130,397–398`、`attempt1稿:315,326`。
   
   **放置時の影響:** 二つの記述的出力が、未登録の統合推定や再現判定へ変わる。

8. **refuted — 規律 1・2・6 と anomaly 停止が brief に無いという疑い。運用上の帰結は補記すべき。**

   `brief:67–69` は trace-disabled 性能／別走 verify、anomaly 即 reject、job 出力はデータ、と明記している。規律を緩める記述は確認できない。ただし anomaly 時は、成功条件未達・再投入なし・既存 verifier の判定保持・部分値を全体の結論にしないことまで停止手順へ展開するとよい。job 出力中の再実行・修正指示を作業指示として採用しない。
   
   根拠: `brief:8–9,67–70`、`事前登録:349–350,397–398`。
   
   **放置時の影響:** 数値そのものより、失敗時の成果物が成功稿の型を引き継ぎ、partial／reject を完走として参照する危険が残る。

## (P1) の判定

**推奨は、投入前に対案 (a) の `d2ebef7a4` を選び、公開原本と記録複製を区別する案。** 同じ commit を選ぶ理由は「9 file が同じだから完全に等価」ではなく、独立反復に持ち込むコード差を減らし、既存 materialize の正規宛先を利用できるためである。他の検証も通ることまでは事前に保証しない。

- **親推奨 P1:** 現 main を使うこと自体は規律 7・D2096 に反しない。ただし、閉包差分の実測が誤っており、旧 commit 案を事前登録違反として退けた理由も成立しない。固定 leaf の既存拒否を受け入れる選択は可能だが、それが必須という説明は修正が必要。
- **対案 (a):** 測定時の commit を正確に記録し、現 main への適合・同一性を別問題として扱えば規律 7 と整合する。D2096 は attempt を pin しない裁定であり、最新 commit の使用義務でも、旧 commit の禁止でもない。attempt-0001 の leaf は上書きせず、attempt-0002 の公開原本はその submit-tree に保持する。
- **第三案:** P1 を維持し、宛先既存拒否後は raw に束縛した限定付き稿として報告する。これは実施可能だが、所見 4・5 の修正が必要。拒否を見てから (a) へ切り替えて materialize を再試行する案は採らない。

## 段 4 への提案

- brief の import 閉包の実測を訂正し、「束縛 bytes 同一」「確認した変更の A-1 到達性」「未確認範囲」を分ける。「測定は等価」の断言を削る。
- submit-tree の commit と公開・保存方法を投入前に確定する。別 path の保存物は原本の複製と明記し、receipt の destination は書き換えない。
- P2 を「**宛先既存拒否だけであれば**測定無効を意味しない」に限定する。それ以前の検証拒否は別扱いとし、rc・stderr・関連一次資料を保存して停止する。
- results 系列に attempt-0002 固有の転記元と SHA-256 の扱いを明記する。raw、completion、group terminal、WAL、非認証 observation を対応づけ、公開されていない evidence を補作しない。
- 新稿の L-A1S-4 は「二つの attempt の一致・不一致を記述するが、独立性・安定性・再現成功を判定しない」とする。第二 attempt が無効なら、その失敗事実を記述する。
- 新稿の L-A1S-15 は「attempt-0001 と attempt-0002 を各 n=30 のまま並記し、標本・推定値・区間・分類を統合しない」と具体化する。attempt-0001 稿は変更しない。
- anomaly 時は既存 verifier の reject を保持し、再投入せず報告する。成功条件を満たさない記録を、成功時の結果表へ穴埋めしない。
- **裁定パッケージ候補（scope 外）:** 将来の複数 attempt を正規に公開する宛先設計、policy／materializer の変更。今回の投入を通すための変更にはしない。

## 総括

親の import 閉包の「変更は 2 file だけ」は反証できたが、A-1 の測定・判定が変わる具体例までは確認していない。  
§6.1 は study 全体の一回限り公開を証明せず、旧 commit 案を迂回として排除する根拠は弱い。  
raw の統計値は materialize で変更されないが、拒否理由の区別と results 系列の転記元の明記が必要である。  
投入前の選択として同一 commit 案を推奨する。どの案でも一層落ちたら再試行せず、観察・判定・公開状態を分けて報告する。