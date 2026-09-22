静的検査と保存済みデータの再集計を行った。編集・テスト実行・計算 job 投入はしていない。**主な must-fix は、モデルの事前固定と生成設定の採取不足の2点。** registered 経路や N1 について、plan の説明を覆す新たな破綻は確認できなかった。

以下の略記を使う。

- `PLAN` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-effect-bundle/codex/s2-plan.md`
- `BRIEF` = 同ディレクトリの `brief.md`
- `PR` = `docs/b5-generator-contrast-preregistration.md`
- `D` / `R` = `orchestrator/campaign/b5_generator_contrast.py` / `b5_generator_contrast_report.py`
- `C` / `P` = `orchestrator/campaign/p3_s4_loop.py` / `pipeline.py`
- `J` = `tools/pegasus/p3_s4_loop_pegasus.sh`
- `PILOT` = `output/insights/2026-09-20/t2797-b5-contrast/`
- `OLD` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/llm_round.py`

### 1. must-fix — exact ID の事後記録では、可変 alias による発効の問題が解決していない

**根拠:** `PR:190`、`BRIEF:43`、`PLAN:243`、`PLAN:286`、`R:467`。

PLAN は予定 ID と観測 ID を区別しており、この限定自体は正しい。しかし「予定 `claude-opus-5`、起動 `opus`、実走後に観測」という構成のままでは、PR の「可変 alias や『既定モデル』のまま発効させない」を満たしたとは言えない。

別 ID・複数 ID・欠落が出た場合の扱いも決まっていない。report の共通構成比較はモデル記録を読まないため、モデルが変わっても registered の数値判定は進む。

`message.model` は保存された assistant メッセージのモデル表記を示す。`.meta.json` の `agentType` / `toolUseId` はローカルな対応付けの材料であり、将来の alias 解決、推論設定、当該巡への実送達を証明しない。親が引数で付けた巡番号の正しさも、それだけでは確定しない。

**必要な修正:** exact ID を指定できる起動方法とその保存箇所を具体化する。できなければ「固定済み」とせず、発効前の未解決事項として再提示する。

**成果物への影響:** 放置すると、束に記載したモデルと異なる生成器の結果が registered 判定へ入る。

**裁定パッケージ候補:** alias 起動を残す場合の許容条件と、観測 ID 不一致・欠落時の規約不適合の扱い。新しい自動 gate や report 変更は本検査では提案しない。

### 2. must-fix — §12 対応表から「生成設定」の実値・出所が落ちている

**根拠:** `PR:190`、`PR:542`、`PLAN:245`、`PLAN:280`–`289`。

対応表の「exact model・設定」は、role file、親設定の hash、client 版、応答 ID 採取器に依存している。これで `model` / `effort` の宣言は残せるが、生成設定を何として固定するかが書かれていない。

少なくとも、使用する client が公開・指定する生成パラメータ、未指定項目、指定不能・観測不能項目を分ける必要がある。設定ファイルの hash は、そのファイルに存在しない設定の実値を補わない。親についても、設定 hash と観測したモデル ID は別の証拠である。

correctness 側は、PLAN が API 引数・既定 mode・実装版の採取を明記しているので、同じ取りこぼしとは判定しない。ただし `PLAN:308` の `…` は最終束では残せない。

**必要な修正:** 役割別の推論・生成設定について、値、未指定時の扱い、出所、固定可能性を採取項目にする。観測不能を「既定値で固定済み」に置き換えない。

**成果物への影響:** 放置すると、異なる生成条件を同じ hash 束の実験構成として扱える。

### 3. should — P2 は件数条件を満たすが、workload 内の block と LLM 位置が完全に交絡する

**根拠:** `BRIEF:37`–`40`、`PLAN:322`–`338`、`PR:354`–`367`。

P2 では、ある workload・block の4系列すべてで LLM が同じ stage に走る。例えば write-heavy の block 1 は全対で LLM が先、block 3 は全対で後になる。

したがって、stage 間の共通ドリフトは、その block の4対へ同方向に入りうる。全12系列で6順序を均等にしても、workload 別・block 別の対差の相関は相殺されない。ドリフトが実在したとは未確認だが、**配置がこの感受性を作ることは確定**している。PR 自身も独立性を保証していないので、直ちに規約違反・検定無効とは断定しない。

同じ stage 運用と p=4 のまま、より均衡した配置を作れる。逆順の組を次の3組とする。

- A = `{LRS, SRL}`
- B = `{LSR, RSL}`
- C = `{RLS, SLR}`

各 `(workload, block)` に2組、計4順序を割り当て、除外する組を workload・block 間で循環させる。すると、

- 各 workload で6順序が各2回。
- 各 block・stage の LLM は全 workload 合計で4本。
- 各 workload・block で LLM 対各 baseline の先後が2対ずつ。

となる。系列番号と report の block 制約も維持できる。順序算術は独立に確認した。これは新しい gate や解析変更を必要としない。

block-stock の stage 1 集中は PR の明文違反ではない。ただし5 session が早期に固まり、後続 stage の score に対応する時間変動を捉える保証はない。既存の5連続 session job を維持するなら、stage 2 配置も候補になるが、それでも全 block の時間変動を測れるとは言えない。

**成果物への影響:** 放置すると、block 別対差・floor の時間的代表性に配置由来の限界が残る。P2 への無条件賛成にはこの限定が必要。

### 4. should — P5 が支持するのは感度分析の結果であり、warm-up 不要の一般判定ではない

**根拠:** `BRIEF:46`–`48`、`PLAN:355`–`388`、`PILOT/README.md:185`、同 `:197`、逐語 `d28.md:3`・`:13`。

保存済み台帳から再集計し、次を確認した。

- 53 session、全件1 round。
- rep 1 除外による median 相対差の最大は **0.6960199%**。
- 1%以上は0件、CV 5% の境界変更は0件。

数値への攻撃は成立しなかった。

ただし5 repから1件を除く操作は、「warm-up 後に5 rep測る」操作の反実仮想ではない。また1%未満でも近接候補の順位は変わりうるため、「fitness・endpoint に影響しない」とは言えない。

共有 lock 待ちは最初の performance trace と bench 開始前に現れる。bench の rep 1 高値と同じ計時対象ではないが、測定前の状態との交絡は残る。待ちがほぼない7件は単純な lock 原因説を弱めるものの、特定の LLM 系列後半という選ばれた部分集合である。

D28 は主に各 run 内の冒頭区間の破棄を扱う。PLAN の区別は正しく、BRIEF の「D28 と同じ理由」は縮めるべきである。

**必要な修正:** 結論を「保存済みデータでは、登録した感度基準から構成変更を要求する差は見つからなかった」に限定する。追加測定を本 wave へ持ち込む必要はない。

**成果物への影響:** 放置すると、write-heavy 試走の限定的な感度分析が、全 workload の warm-up 不要という実験根拠へ拡張される。

### 5. should — prompt の一般化では、既存の狭い指示と誤った但し書きも変更一覧に含めるべき

**根拠:** `PLAN:162`–`191`、`PLAN:265`–`270`、`OLD:154`–`175`、`OLD:204`、`PILOT/llm/round-1/coder-prompt.md:1`、`PR:82`–`87`。

試走 coder prompt は `<整数リテラル>` と指示する一方、PR の受理文法は「接尾辞なし数値 literal、value と数値的一致」である。この狭い生成指示は試走の構成事実なので、一般化時に黙って広げるべきではない。保持する場合も、共通受理文法そのものとは区別して束に残す必要がある。

また OLD の planner への但し書きには、系列開始 stock を「同時刻対照」と呼ぶ文がある。実際には逐次測定であり、試走 critic 自身も32分差を記載している。workload 名だけ置換すると、この過剰な説明まで本走へ持ち越す。

PLAN の「試走 fixture と本走 template を分ける」は妥当。変更一覧にはラベル・path・動作点だけでなく、こうした意味を持つ文の保持／訂正も含めるべきである。

**成果物への影響:** 放置すると、生成器の指示範囲が意図せず変わるか、不正確な測定説明を含む prompt が固定される。

知識漏洩については、PLAN の「固定 K2 知識は共通、workload 別差分は動作点説明だけ」という方針に破綻は見つからなかった。試走 critic の「3%」という記述だけでは、本 cohort の floor 結果が入力へ戻った証拠にならない。

### 6. should — proposal 公開順の変異は、consumer の検出力を示す変異ではない

**根拠:** `PLAN:546`、`D:683`–`697`、`OLD:249`–`254`。

driver は `proposal.exists() and inputs.exists()` が成立してから入力を読み、継承を検査する。単一 writer が両方を正常に公開する条件では、inputs と proposal の公開順だけを逆転しても、この consumer の受理条件は変わらない。

公開順を spy で検査すれば変異を殺せるが、証明するのは採用した公開手順の遵守であって、誤入力の検出や受理集合の縮小ではない。正常完了時の consumer 挙動に対しては等価な変異になりうる。

ほかの候補は次を満たせば内容へ帰属できる。

- model 集約は、同一 ID が2件だけの fixture ではなく、異なる ID が混在する fixture で検出する。
- ceil→floor は非整数積の k を用いる。
- registered→pilot は「例外が出ない」ではなく、consumer の `invalid` と purpose 分岐を確認する。
- prompt の期待値は、被検査 renderer と同じ処理で再生成しない。

PLAN は混在 ID・境界値・保存済み prompt fixture を予定しているため、これらについて既に検査が恒真だという攻撃は成立していない。

**成果物への影響:** 放置すると、手順上の差を殺した件数が、意味上の不整合を検出した件数として報告される。

### 7. should — 既知結果差分の採取項目に閲覧者・閲覧時点が明示されていない

**根拠:** `PR` §8 の「exact な artifact と閲覧者・閲覧時点」要求、`PLAN:297`、`BRIEF:15`–`31`。

PLAN は試走・Tier0・今回の確認結果を差分台帳へ載せるが、誰がいつ何を閲覧したかを採取欄として明示していない。今回の費用見積りや schedule 選択も、追加資料を見た後の設計判断である。

これは campaign ledger の新 field 追加ではなく、既存の §8／§12 文書採取の内容で対応できる。

**成果物への影響:** 放置すると、既知結果と設計選択の時間関係を束から追跡できない。

## 総括

- **must-fix:** 所見1「exact model の事前固定と不一致時の扱い」、所見2「役割別の推論・生成設定の実値・出所」。
- **P1:** 賛成。registered producer・launcher・LLM tool は具体的な投入経路に必要。新規 gate・report 変更を当然の追加にしない。
- **P2:** 条件付き賛成。件数条件は成立するが、現配置への無条件賛成には反対。所見3の逆順組配置を推奨する。
- **P3:** 賛成。pilot 既定値維持、registered の block 関係、stock の `series=block` は consumer と整合する。
- **P4:** 現状では不十分。採取器は有用だが、所見1・2を閉じる必要がある。
- **P5:** 現行5 rep維持に賛成。warm-up 不要の一般証明とはしない。
- **P6:** PLAN の訂正後の説明に賛成。コード変更なしで記録する方針を支持する。
- **P7:** 賛成。B-8 は extime 10秒。引用した約220／496秒を B-5 の3秒 traceへ直接代入しない。系列と block-stock の両方から k を評価する。
- **P8:** 賛成。親 template に系列ごとの fresh context、許可する入力範囲、固定知識の所在を具体化する。
- **P9:** 賛成。D2202 は厳密には構成値を維持し、status 変更に加えて承認情報の `effective` 節を追加する先例。PLAN の訂正が正しい。

**攻撃が成立しなかった項目・確認できた事項:**

- **§12:** random 重み・preimage、sweep 全順序、session ID、correctness／Tier0／bench の採取方針、seed の区別、raw hash と自己参照回避は概ね網羅されている。初回 stock の未取得値を捏造せず、生成規則・schema と実走入力を区別する扱いも妥当。
- **schedule:** P2 の6順序×2、対応系列、各 stage の LLM 4本、前 stage 完了待ち、block 間1時間は整合する。report の block 制約とも衝突しない。
- **registered 経路:** purpose/cohort の分離、job ごとの submit-tree、K2 を LLM のみに渡す設計に具体的な破綻は見つからなかった。report の受理は発効束との全項目照合を意味しない点は残る。
- **walltime:** k=2／4.06 の時刻表記は正しい。J の deadline は scheduler 開始時刻＋要求秒数。`SESSION_BUDGET_S=1800` は slot 開始判定であり、session timeout ではない。
- **規律2:** `D:514`、`D:417`、`C:3702` と既存 pipeline の接続から、今回の変更案が legacy＋動作点 trace 5回や anomaly reject を弱める経路は確認できなかった。
- **whiteboard／critic:** 保存済み10巡では whiteboard が0〜9件、planner/coder間で一致。初回診断なし、以後同じ6 field の診断という構成も一致した。
- **N1:** `loop.py:755`–`791` の WAL 再生から `done` が作られる。fresh・単一 writer・1 genomeという前提なら通常到達しない。初回投入後 skip が発生すると `D:367` で submitted が落ち、B と評価件数が共に減るため `R:297` の照合は通りうる。`R:313` は終端済みとして sidecar 回収も行わず、score 欠測から判定不能になる。PLAN の読みが正しい。
- **N-a／N-b／N-c:** コード所在と試走専用構成は一致。OLD の318行・full SHA-256、context の SHA-256も一致した。
- **N-d:** 応答 ID と alias の区別は妥当。ただし提示資料には試走 subagent の具体的な raw transcript／meta の組がなく、その観測自体を独立再確認したとは報告しない。
- **N-e／N-f:** B-8 の引用値と10秒条件、較正 rep 1 の方向、試走53件の集計は資料と一致。費用と warm-up への一般化には上記の限定が必要。
- **採取物:** 保存された重みを使う独立計算で random 36系列×30機会と sweep 36全順序が一致。重み配列1000件、M、正準配列 hash も整合した。