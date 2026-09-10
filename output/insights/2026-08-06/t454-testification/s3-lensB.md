## 総括

- **NO。今 wave が実際に解放する量は 0 bytes**で、合計は 25,187 / 25,200 のまま。予算問題を解かない。
- S1/S2 後に裁定可能な意味保持 pointer 案は **−207 bytes**（O01 −159、M05 −48）だが、本 plan は適用しない。
- 最重所見は、既存 2,591 行 launcher と T-184 所有面を比較せず、利用強制のない第二 launcher を作るため、義務強制にも予算回収にも接続されないこと。
- 採録待ち4件が本文へ入らないことを親は物理的には認めるが、P2 の「機械強制済み」評価とは矛盾する。
- `refuted`: N2, N3, P1, P2, P3, P4, P7。`real`: N1, N4, P5, P6, P8（ただしP6はplan未履行）。

### 所見 B-01 — この wave の回収量は 0 bytes

**主張**

S1/S2が完成しただけでは `docs/dev-wave/**` は1 byteも減らない。親が禁止した本文変更と、planの「0 bytes」がそのまま wave の結果である。以下の pointer 差分を後日裁定・適用した場合に限り、意味を残した回収見込みは207 bytesになる。

**根拠**

親 brief は本文不編集と総量不変を明記する（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t454-testification/brief.md:49-59`）。段2も削除候補ゼロ・回収0・全Markdown不変を結論している（`s2/plan.md:290-296`）。

UTF-8 raw bytes、末尾LF込みで測った提案本文は次のとおり。

`DW-O01` の `docs/dev-wave/operations.md:8-12` を置換:

```text
起動は `python3 tools/dev_wave_codex.py launch --job-dir <ABS> --prompt-file <ABS> --output-file <ABS> --log-file <ABS> --cwd <ABS> --sandbox <値> --reasoning <値> [--model gpt-5.6-sol]`、待機は `python3 tools/dev_wave_codex.py wait --job-dir <ABS>` を使い、model / reasoning / sandbox は該当 worker 節に従う。
prompt に `## 総括` を要求する。`wait` rc≠0 は停止し、採用条件は `tools/check_codex_output.py <出力>.md` rc=0（F23/F24/F43）。
```

`DW-M05` の `docs/dev-wave/mutation.md:35-37` を置換:

```text
検証できない自己申告なので親の義務に残る。生死は `python3 tools/mutation_harness.py probe-running --repo <repo>` の rc（0=生存、1=不在、2=不明）で判定し、2 は停止する。
```

| 対象 | 現行 | 提案 | 差 |
|---|---:|---:|---:|
| `DW-O01:8-12` | 644 | 485 | −159 |
| `DW-M05:35-37` | 263 | 215 | −48 |
| 合計 | 907 | 700 | **−207** |

適用後なら合計24,980、余白220 bytes。しかし今 wave は適用しないので実績は0 bytesである。

**成果物への影響**

採録待ち4件は今 wave 後も本文には入らない。親は不変条件ではこれを認めている一方、P2では(a)を機械強制済みと扱う（`brief.md:78-81`）。さらにS4未実施時は(a)が機械検査にも入らないと書いており（同`:71-73`）、会計作業S4と機械強制S1を混同している。

**推奨**

段4で成果を「予算問題の解決」ではなく「将来の−207 bytes差分を裁定可能にした」と限定する。裁定パッケージへ上記の逐語差分と、適用前0／適用後−207の二値を載せる。

### 所見 B-02 — tool完成からdocs削減へ至る接続がない

**主張**

「機械化したのにproseが減らない」経路が成立する。S1を実装してテストが緑でも、旧 `DW-O01` が正規手順として残り、新toolを使わせるcaller gateもないためである。

**根拠**

planは旧artifactだけでなく旧手順自体を維持する（`s2/plan.md:102-111`）。採用検査もtool内部ではなく、`wait` 後の別段階に残す（同`:104-109`）。親 brief も旧手順を壊さないことを不変条件にする（`brief.md:61-62`）。

成立する系列は次である。

1. 新toolと単体テストを追加する。
2. 既存raw `DW-O01` も利用可能なまま残す。
3. callerが新toolを通ることを検査しない。
4. output checkerの実行も親の外部操作に残す。
5. したがって現行proseを削除できず、実回収は0 bytes。

`check_docs.py` はbyteと構造しか検査せず、意味やtool利用を固定しない（`tools/check_docs.py:2-10`、`docs/skill-self-improvement.md:79-84`）。

**成果物への影響**

新toolを迂回した子について、残留 `.done`、二重waiter、producer死亡の事故型がすべて残る。tool単体の安全性をwave全体の安全性へ一般化できない。

**推奨**

caller側で「新規dev-wave子は必ず新経路」という負例付きgateを作るか、旧経路を明示的にlegacy-onlyへ降格する裁定を取る。それがない限りO01削減を予算へ計上しない。

### 所見 B-03 — 先行機械化は対象proseを70 bytes増やしていた

**主張**

N2の「先行waveが、機械化だけが恒久的に空ける手段だと実測済み」は反証される。機械化は削減の必要条件になり得るが、削減の十分条件でも、恒久性の実測でもない。

**根拠**

先行README自身が、#8〜#11を機械化した一方で「義務の完全削除はゼロ」と記録する（`output/insights/2026-08-01_t291-devwave-mechanization/README.md:21-31`）。

commit `1ecf6a015c687d7e7a8c4ae56dd24280a5816e20` と親blobを実測した結果:

| 面 | before | after | 差 |
|---|---:|---:|---:|
| `DW-M05` | 635 | 786 | +151 |
| `DW-M06` | 339 | 258 | −81 |
| #8〜#11 合計 | 974 | 1,044 | **+70** |
| dev-wave 4冊全体 | 23,990 | 23,956 | **−34** |

全体−34は別節の理由文・注記の縮約によるもので、機械化対象節そのものは+70だった。READMEの「458 bytesは33時間で再消費」も単発縮約の寿命を示すだけで、機械化後の余白が恒久だとは示さない（同`:54-64`）。

**成果物への影響**

N2を一般則として使うと、tool追加時点で未適用の削減を先取り計上する。本waveも同じ誤算を再現する。

**推奨**

各機械化について「対象節before／pointer after／caller強制／適用commit」の四点を同時に計測する。「恒久」は後続消費を観測するまで名乗らない。

### 所見 B-04 — S1は過大で、既存launcherへの二重投資である

**主張**

S1は待ち手規約の強制に対して過大であり、既存launcherの起動・検証面を再実装する。P4の「所有分離と回帰面の最小化」は比較抜きの標語で、根拠になっていない。

**根拠**

S1はlaunch/waitの2 command、`.done`・`launch.json`・`started.json` の3 state、producer/waitの2 lock、複数rcを新設する（`s2/plan.md:13-47,58-83`）。さらにCodex argvとdetach処理を直接再実装する（同`:64-76`）。

一方、2,591行の `tools/codex_worker_launch.py` は既に次を持つ。

- Codex argv、model/reasoning/sandbox/cwd/output: `:1078-1113`
- `DEVNULL`、`shell=False`、別session: `:1161-1169`
- prompt非空・absolute path・既存output拒否: `:1519-1558`
- bounded監督とreap: `:1180-1258`
- create-only receiptとoutput公開: `:1620-1628,1727-1762`
- output validatorとの実接続: `:985-991,2406-2413`

D100はこのlauncherをCodex job envelopeのwrapperと定め、`DW-O01` 結線とstage別上限値をT-184の所有にしている（`docs/decisions.md:4422-4457`、`docs/phase3.md:683-695`）。planにはD100/T-184との比較がない。

**成果物への影響**

新S1は既存のbounded receipt経路を迂回し、同じprompt・argv・spawn・output検査に第二の退行面を作る。将来T-184が結線すると二つのlauncher policyが衝突する。

**推奨**

既存launcherを実行本体にし、dev-wave側は薄いdetach/wait adapterだけに縮める。既存create-only receiptを唯一の耐久stateとし、1 lock fileのbyte-rangeをproducer/waiterに分け、開始handshakeはpipeで行えば、3 stateの新設とCodex argv再実装は不要になる。stage上限値が未裁定ならT-184へ返す。

### 所見 B-05 — scopeは採録待ちにも既承認T-454にも足りない

**主張**

S1/S2/S3後も、4件のうち(a)〜(c)は正規経路への結線規範が残る。(d)だけは追加テストで完全に機械化できる。さらに、既にT-454へ割り当てられた複数の起草物がbriefから消えている。

**根拠**

4件の残余は次のとおり。

| 件 | S1/S2/S3後の状態 |
|---|---|
| (a) 待ち手3条 | S1利用時だけ。旧経路と異なるjob-dirで迂回できるため、利用義務またはcaller gateが必要 |
| (b) stale `.done` | 新toolは拒否するが旧 `DW-O01` は有効。旧経路への禁止規範が残る |
| (c) pgrep自己一致 | S2利用を義務化するpointerが必要。tool追加だけでは親がpgrepを使える |
| (d) exact node set | planのstrict-superset testで固定可能（`s2/plan.md:215-227`） |

またT-454には過去に以下が明示的に割り当てられている。

- T-505の削除リストと恒久3機構の規範文・新D起草: `docs/archive/worklog-phase3-0805-224-225.md:247-251,293-304`
- F112/F124の `DW-S06-B` 追記: `docs/archive/worklog-phase3-0805-235-236.md:307-310`
- `DW-S01` / `DW-S02` の撤回2候補、計142 bytes: `docs/archive/worklog-phase3-0805-237.md:37-43`
- 追記274 bytes、必要枠270の持越し: `docs/archive/worklog-phase3-0806-242-244.md:969-973`
- 最新scopeにも待ち手束・3候補・F112/F124が残る: 同`:1010-1013`

本提案で207 bytesを削っても余白は220 bytesで、既知の274-byte追記単独すら入らない。さらに142 bytesとT-521/T-505が続く。

**成果物への影響**

「入らない分だけ見送り」の対象が列挙されず、単にbriefから脱落する。これは見送り裁定ではなくscope lossである。

**推奨**

段4で全候補を、`機械化済み / pointer待ち / bytes不足で見送り / 新D発効待ち` に分類し、各bytesを出す。T-505は発効を止めても、規範文案と裁定材料の作成まで消してはならない。

### 所見 B-06 — `condition_id` は「同一条件」を識別していない

**主張**

S1は「1条件1待ち手」を機械強制しない。random nonceをidentityへ混ぜたため、同じ論理条件でも再投入ごとに別条件になる。

**根拠**

`condition_id` はjob-dir、done path、random nonceのhashである（`s2/plan.md:58-61`）。wait lockはこのidentity内だけで競合し（同`:78-89`）、異なるjob-dirは競合しないことを仕様・テストで肯定している（同`:99,192-193`）。

一次裁定が要求したのは通知や再実行を跨ぐ「1条件1待ち手」である（`rulings-inbox/2026-08-05-background-waiter-duplication.md:23-28`）。nonceで毎回変わるgeneration IDとは異なる。

**成果物への影響**

同じレビュー条件を別job-dirで再投入すれば、二本目のwaiterを合法的に起動できる。73本常駐事故の主要経路をテストがむしろ仕様として固定する。

**推奨**

論理 `condition_key` を親が安定値として渡し、generation nonceとは別fieldにする。排他identityはcondition key、artifact freshnessはgenerationで判定するテストを追加する。

### 所見 B-07 — P1は場所で「新D」を判定しており、広すぎかつ狭すぎる

**主張**

P1の「削除実施と新D発効を返す」＝「本文を1 byteも変えない」は同値でなく、`その他のMarkdownも変更しない` への拡張は段7と衝突する。一方、永続CLIをcommit・dogfoodしてもD fragmentを書かなければ発効でない、という読みは狭すぎる。

**根拠**

planは全Markdown不変を宣言する（`s2/plan.md:296`）が、段7はworklog・insights・設計判断の記録を必須とする（`.claude/commands/dev-wave.md:45-54`、`docs/dev-wave/core.md:84-95`）。

worklog fragmentはcanonical decisionではない。waveはspool fragmentを書き、land時にfoldする（`docs/spool/README.md:3-5,65-84`）。routingも、採用済みの長期設計・権限・interfaceだけをdecisionsへ送り、未裁定の大変更は裁定パッケージへ返す（`docs/skill-self-improvement.md:22-29`）。

**成果物への影響**

記録を止めればwaveの完了条件を破る。逆にS1を標準経路として記録・利用すれば、D100/T-184に触れる長期interfaceをdecisionなしに既成事実化する。

**推奨**

境界を意味で切る。

- 許可: 事実だけを書くworklog fragment、insights、非規範の提案diff・byte会計
- 保留: `docs/dev-wave` pointer置換、利用義務、decisions fragment
- S1 code: 裁定前はexperimental・非権威と明記し、標準callerへ結線しない

### 所見 B-08 — dogfoodは遅く、G01を満たさず、失敗分岐を踏まない

**主張**

U1→U2直列化はdogfoodのためだけに並列性を捨てる。しかも実装後の通常利用は、実装前実験を要求するG01を遡及的に満たさず、G04の判定とも無関係である。

**根拠**

planは段3・U1ではdogfood不能と認め、U1統合後にU2を起動する（`s2/plan.md:113-124`）。U1/U2はもともと所有が素集合だった（`brief.md:88-91`）。

所要時間をU1=`t1`、U2=`t2`、統合=`i`とすれば、並列の概算 `max(t1,t2)` が直列 `t1+i+t2` になり、少なくとも `min(t1,t2)+i` 増える。

G01は大型機構の本格実装前に既存driverか100行以内の使い捨てdriverで生死確認する規則である（`docs/dev-wave/core.md:42-45`）。G04は既存artifact pathまたは計測IDをbriefに書けるかという実装許可gateで（同`:57-60`）、briefには既存 `.done` 実例が既にある（`brief.md:31-35`）。

**成果物への影響**

U1欠陥がU2起動を塞ぐ新しいself-hosting choke pointになる。旧経路へfallbackすればdogfood証拠が消え、停止すれば独立なS2まで失う。通常成功runを一回または複数回使っても、stale `.done`、二重waiter、producer死亡の分岐は発火しない。

**推奨**

U1/U2実装は旧経路で並列維持し、統合後に小さい専用jobでdogfoodする。G01用には本実装前に薄い既存launcher adapterで、正常・stale・二重waiter・producer killの4実験を行う。G04は既存artifactにより成立済みとだけ記録する。

### 所見 B-09 — 「既存テストがある」誤読が別面で再発している

**主張**

親の(d)誤判定と同型の誤りが、S1のoutput採用とS2のlock probeにある。componentのテストをcallerとの接続テストへ読み替えている。

**根拠**

(d)の既存testは `expected={one}`, `failed={two}` の互いに素な場合だけで、`expected={one}`, `failed={one,two}` を固定しない。plan自身がこれを正しく反証している（`s2/plan.md:215-227`）。

同じ型が二箇所ある。

- planはoutput checkerの既存testを理由に追加不要とする（同`:229-235`）が、S1はcheckerを呼ばず外部採用手順へ残す（同`:104-109`）。checkerの性質は固定されても、callerが呼ぶ性質は固定されない。
- 既存flock testは二本のexclusive harnessの競合だけを固定する（同`:205-213,229-234`）。shared probe、owner死亡後の遷移、probeとrunのraceまでは固定しない。こちらはplanの追加testが修復する。

既存launcherは実際にvalidatorを呼び、receipt再検査でも再実行する（`tools/codex_worker_launch.py:985-991,2406-2413`）。新S1はこの接続を失う。

**成果物への影響**

`wait` rc=0の無効出力を、親がcheckerを呼び忘れて採用できる。P7の「採用条件まで丸ごと吸収」は成立せず、O01の採用proseも削れない。

**推奨**

S1のconsumer E2E testで「wait成功→validator成功までが採用」を固定し、validator call削除変異を登録する。外部操作のままならP7を撤回し、残置proseとしてbyte会計する。

### 所見 B-10 — 親前提 N1〜N4・P1〜P8 の裁定

**主張**

判定は次のとおり。

| 前提 | 判定 | 理由 |
|---|---|---|
| N1 | `real` | 独立棚卸しと実発火反証は存在する。ただし「節全削除ゼロ」であり、部分pointer縮約ゼロまでは導かない（`brief-addendum.md:5-22`） |
| N2 | `refuted` | 先行#8〜#11は対象節+70 bytes、完全義務削除ゼロ。恒久性・唯一性を実測していない（同`:24-32`、T291 README`:21-31`） |
| N3 | `refuted` | R3の名指しはM08/O11/O20/O23で、O01やM05 pgrepではない。R2も所要見積り・外側supervisorの話である（`brief-addendum.md:34-39`、T291 README`:90-97`） |
| N4 | `real` | #10はpgrepを明示的にtool射程外としており、S2はその判断を反転する（`brief-addendum.md:41-49`） |
| P1 | `refuted` | 削除・D発効の保留から全Markdown凍結は導けず、段7記録とも衝突する |
| P2 | `refuted` | tool利用は強制されず、condition identityも論理条件でない。意味保持pointerも「1行」ではなく最低限の起動・採用条件を要する |
| P3 | `refuted` | production追加は不要だがstrict-superset testは純増検出力を持つ（`s2/plan.md:215-227`） |
| P4 | `refuted` | 既存launcherとD100/T-184を比較せず、同一機能を再実装する |
| P5 | `real` | Pegasus login nodeでpytest・変異を直接走らせずdispatchする規律と一致する（`AGENTS.md:31-38`） |
| P6 | `real` | byte会計＋提案diffへの組替えは必要。ただし現planは0-byte節棚卸しで終わり、履行していない（`s2/plan.md:244-296`） |
| P7 | `refuted` | checker採用・stage別model/reasoning/sandbox・利用義務がtool外に残る |
| P8 | `real` | O10/O04はいずれも発火実績または機械代替不足があり、削除条件を満たさない（`brief-addendum.md:11-19`、`s2/plan.md:274-294`） |

**根拠**

特に親の(d)誤測定は `DW-S01` の「機構名でなく性質を検索する」義務への直接違反である（`docs/dev-wave/core.md:24-30`）。S1のchecker接続でも同型を繰り返している。

**成果物への影響**

このまま段4で親前提を維持すると、0-byte waveを予算解決と誤記し、optionalな二重launcherを標準化し、既承認scopeを無言で落とす。

**推奨**

段4では少なくともP2/P3/P4/P7を撤回し、P6を実施する。S1は既存launcher adapter案との比較とT-184裁定まで実装保留、S2とstrict-superset testは独立scopeとして切り出す。byte値は静的 `wc -c` とgit blobで実測し、read-only段3のためpytestは実行していない。