### 新 tool は現行の必須取り込み経路を通らない

severity: blocker  
判定: real  
根拠: plan の配線は `DW-O17` の一行置換だけだが、正規の main 取り込みは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-merge-audit-necessity/docs/dev-wave/operations.md:153-155` により `dev_wave_wait.py acceptance` 内で行われる。同 waiter は merge 完了直後から provenance を連続実行し、外部の親が `--index` tool を挟む停止点がない (`tools/dev_wave_wait.py:3635-3675`)。`DW-O17` を読むのは commit 直前だけである (`.claude/commands/dev-wave.md:105`)。必ず通すには waiter の merge 完了後、`merge-history-provenance` より前へ生成処理を置き、repo 外 artifact と監査済み再開契約まで実装する必要がある。  
成果物影響: 現案では監査 prompt と台帳に projection 参照が残らず、certified 受理集合は変わらない一方で高速化は実効ゼロになる。

### D770 の authority 起動不能という前提は現行コードでは成立しない

severity: blocker  
判定: real  
根拠: D770 は staged merge では子を起動不能としている (`docs/decisions.md:29752-29760`) が、後発の D785 は `stage=author` かつ `sandbox=workspace-write` に限り mid-merge を許可した (`docs/decisions.md:30156-30182`)。実装も `allow_mid_merge=True` を渡す (`tools/codex_worker_launch.py:2632-2637`)。D770 の 2 commit 実例はこの変更前である (`docs/archive/worklog-phase3-0824-904.md:78-104`)。D770 と現行手順の優先関係を裁定し直す必要がある。  
成果物影響: 古い前提を維持すると同じ tree に不要な 2 commit と provenance 記録が増え、監査対象 commit と台帳参照が現行経路と食い違う。

### 「有用なアンカーが監査を速める」という因果は未確定

severity: major  
判定: unclear  
根拠: 支持材料は、4 file・約1.04 MB・repo 遮断の stage6 が 468 秒、1 path・疑い3点の t1726 が 320 秒であることと、射影なし・交差0でも全差分を探索した t1636 が394秒だったこと (`evidence.md:60-66`)。一方、最も厚い射影が最遅であり、最速の106秒・162秒には射影量と file 数がない。同一モデルだった比較2件も stage が consult/author で異なる (`s2-plan.md:5-11`)。file 数、1 MB入力、repo 遮断、wave難度の方が同程度以上に説明力を持ち、日次モデル挙動は未観測である。plan は具体的な短縮秒数を書いていないため、数字として検査可能な速度主張もない。  
成果物影響: certified 選択は変わらないが、改善レポートへ短縮秒数や因果を記載すると未統制データからの過大主張になる。

### 監査子は全体時間の少数派とは見積もれない

severity: minor  
判定: refuted  
根拠: 現行受入の別 regime による推定値は `56.4 + 149.4 = 205.8` 秒 (`docs/worklog.md:2692-2710`)。AST の親実測10.9秒を足すと、全体概算は `106+205.8+10.9=322.7` 秒から `468+205.8+10.9=684.7` 秒で、監査子占有率は約33%から68%。異なる母集合を合わせた推測だが「少数派」とはならない。D770 の人手時間と exact な merge-message rc=70 所要は未計測なので、これ以上の精度は出せない。  
成果物影響: 律速占有率を理由に wave 全体を撤回する根拠はなく、変更すべき scope は高速化対象ではなく必須経路への配線である。

### 52分損失と lease 待ちを現行の利得へ数えてはならない

severity: major  
判定: real  
根拠: 52分は旧待ち行列で順位を失った事例 (`docs/decisions.md:22600-22603`)。現行は単発 claim で、他 holder がいても即投入し、待ち行列自体が到達不能である (`docs/decisions.md:27296-27309`, `docs/dev-wave/operations.md:187-194`)。lease TTL は2400秒、receipt余裕は300秒 (`tools/dev_wave_wait.py:231-232`) なので、監査106から468秒は窓の4.4%から19.5%。受入205.8秒とAST10.9秒を含めても最大約28.5%で、lease窓は律速ではない。既知の25秒 rc=70 は preclaim-history-provenance の事例で、merge-message-provenance の実測ではない (`docs/failures.md:10633-10643`)。  
成果物影響: 放置するとレポートの節約時間だけが52分単位で水増しされ、receipt の lease 値やcertified受理集合は変わらない。

### Pegasus 実行分類が未解決のままでは正式手順で tool を実行できない

severity: blocker  
判定: real  
根拠: 新規 script は Pegasus login で事前分類が必須で、実測はユーザー端末の cgroup charged-memory、未測定は `unknown` として dispatch-required 扱いである (`tools/README.md:11-23`)。親の60 MBは最大RSSなのでこの証拠要件を満たさない (`evidence.md:101-115`)。44 script が未登録なのは machine gate の被覆漏れであり、同 README 自身が「3層の外は緑」と明記する (`tools/README.md:31-34`)。現ホストも `pegasus02` である。  
成果物影響: 分類または sanctioned dispatch が無ければ projection は生成されず、監査 prompt・レポート・台帳の参照はいずれも従来の手作業のままになる。

### AST走査は現規模では致命的でないが、上限と rc=1 の消費契約がない

severity: major  
判定: real  
根拠: 現物計数は `orchestrator/` 533 file・582,868行、`tools/` 93 file・119,394行、計626 file・702,262行。既存 streaming scanner の実測は8.232秒 (`docs/archive/worklog-phase3-0821-778.md:8-16`)、台帳値16.0秒 (`orchestrator/tests/acceptance_duration_ledger.json:2606-2611`)、親実測10.9秒 (`evidence.md:95-102`) で、106から468秒の監査を単独で相殺する大きさではない。parse不能を個別列挙して手動監査・rc=1とする判断は plan にある (`s2-plan.md:108-131`) が、blob上限値・出力上限値は未決定で、非Python pathが一つでも通常のrc=1になる。そのrc=1を誰が成功扱いで監査子へ渡すかも `DW-O17` 一行にはない。  
成果物影響: 正常な非Python mergeでも親が停止するか不完全出力を採用するかが分岐し、監査の受理集合と台帳結果が呼び手依存になる。

### 同一機能の既存 tool はない

severity: nit  
判定: refuted  
根拠: `check_subprocess_bytecode_guard.py` は全Pythonをstreaming parseするが、目的は subprocess bytecode guardだけである (`tools/check_subprocess_bytecode_guard.py:1-22,339-390`)。merge path集合は `check_ai_provenance.py:1529-1700` にあるが、変更識別子と全call-site閉包は実装していない。`tools/` の45 top-level scriptと `hooks/` に直接の重複は見つからなかった。新設自体は妥当だが、既存scannerの列挙・parse失敗処理とprovenanceのpath authorityは共有すべきである。  
成果物影響: 新設によるcertified選択結果の重複権威化は、既存関数と走査部品を再利用する限り発生しない。

## 総括

blocker は3件あります。最大の懸念は、toolが正規の postclaim merge と provenance の間に入らず、実装しても使われないことです。

scope は「新script＋test＋DW-O17一行」から、`dev_wave_wait.py` の必須経路、projection artifact、監査後の再開契約、consumer pinまでへ変更すべきです。速度効果は同じ merge・同じstageで projection 有無を比較する対実験まで数値化しないでください。