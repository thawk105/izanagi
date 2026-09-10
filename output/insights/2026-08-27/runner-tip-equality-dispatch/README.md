# 受入の実行器 tip 等値要求を外せるか — dispatch 経路の実測と裁定パッケージ

- 依頼 (ユーザー): 受入 launcher の runner byte 一致要求を外す。実行元を tested main の blob に
  固定する保護は維持し、tip との等値要求だけを落とす。D838 の代償 (当該 file を直す wave が
  受入を通せない) を解消する。
- wave branch: `worktree-dev-wave-runner-tip-equality-20260827`、base local main `c0b8fb7f`。
- 関連: D838 (等値の導入)、D440 / D583 (待ち手・launcher の束縛境界)、D387 (防御対象は事故)、
  D524 / D690 / D987 / D1103。
- 逐語は `verbatim/`。
- **実装面の差分はゼロ。** 依頼の 2 条件が同時に成立しないことを実測したため、
  ユーザー再裁定へ返した。

## 結論

依頼は次の 2 つを同時に求めている。

1. tip との byte 等値要求を落とす。
2. 「実行元を tested main の blob に固定する保護」は維持する。

**この計算機では 1 と 2 は同時に成立しない。** 受入全走の pytest を実際に駆動するのは
tested tip 側の作業ツリー file であって、tested main の blob ではない。両者が今日一致しているのは、
まさに落とそうとしている等値要求のためである。しかも成立しなくなるのは、
**本変更が通そうとしている当の wave (実行器を編集する wave) についてだけ**である。

## 実測した連鎖

すべて本 wave 中に親が実行した。

| # | 事実 | 測り方 |
|---|---|---|
| 1 | この host は `PEGASUS_LOGIN`、queue `gen_S` は `ENA=ENA` / `STS=ACT` (待ち 33・実行 41) | `site_policy.current_site()` と `queue_state.dispatch_possible()` を実行 |
| 2 | その条件下で待ち手は受入 launcher へ `IZANAGI_ACCEPTANCE_SHARDS=3` を渡す | `tools/dev_wave_wait.py` の `_acceptance_launcher_environment` |
| 3 | launcher は tested main の blob を `exec` するが、`__file__` に作業ツリーの canonical path を入れる | `tools/acceptance_launcher.py` の `_RUNNER_BOOTSTRAP` (`'__file__': sys.argv[1]`) |
| 4 | 実行器は `__file__` から `_REPO` を導く → **wave worktree** | `tools/run_tests.py:55` |
| 5 | shard mode の LOGIN 実行は必ず dispatch する | `tools/run_tests.py` の LOGIN 分岐 |
| 6 | dispatch は `repo_root=Path(_REPO)` を渡す | `tools/run_tests.py` の `_default_dispatch` |
| 7 | 計算ノード側の子は `[python, <repo_root>/tools/run_tests.py, *argv]` を **pathname で**起動する | `tools/pegasus/dispatch_compute.py:1013` (`bnode*` hostname 検査の内側) |

launcher の main blob 実行が覆うのは、dispatch を決める外側の 1 プロセスだけである。

## なぜこれが「未見の事実」なのか

- D838 の裁定文にも、その実装 wave の記録 (archive worklog 960) にも、dispatch 側の再入は無い。
- `docs/pegasus-runbook.md` は「bounded / dispatch の内側の子は pathname を読み直すため
  実行 bytes の束縛外にある」と**残余としては記録している**。
- **記録が無いのは両者の相互作用である。** 等値要求こそが、その残余の実害を消していた唯一の
  仕掛けだった。等値がある限り pathname 側の bytes は main と同一なので残余は無害である。
  等値を外すと残余が実害に変わる。

## 再開する脅威

D838 の裁定文が名指しした脅威そのものである — 「wave が実行器を書き換えるだけで実際は赤の走行を
『子は緑』として着地させられる」。等値を外した後、実行器を編集した wave は
**自分が編集した実行器に自分を判定させる**。受領証の `runner_executed_sha256` は main の値のままなので、
受領証・land 結果・worklog のどこを見てもこの差は現れない。

D387 が定める事故モデルでも成立する。実行器の編集がうっかり選択集合を狭めれば、
その wave の受入は自分の回帰を見逃したまま緑になる。

## 順序のデッドロック

dispatch 側の穴を塞ぐには、計算ノードの子も tested main の blob から実行させる必要がある。
その実装は `tools/run_tests.py` と `tools/pegasus/dispatch_compute.py` を編集する。
**`tools/run_tests.py` の編集は、いま外そうとしている等値要求そのものによって塞がれている。**
「穴を塞いでから等値を外す」は現行契約では実行できない。どちらを先にするかはユーザー裁定が要る。

## 選択肢 (親の推奨は B)

- **A. 依頼どおり等値だけ外し、dispatch 側の穴は残余として受容する。**
  目的は即座に達成される。代償は自己判定の窓が開いたままになること。窓が閉じるのは
  dispatch 束縛 wave の land 後である。D838 以降その file は 1 度も変更されていないので
  母集合は小さく、各 wave は意図的である。
- **B (推奨). 等値の撤去と dispatch 束縛の実装を 1 つの wave に載せ、その wave についてだけ
  「実行器を編集した wave の land」を明示的に一度だけ認める。**
  受入の権威が一度も薄くならない。代償は、その land の認可の形をユーザーが決める必要があること。
- **C. 等値を維持し、[T-1932] は別経路で解く。** 現状維持。

**B を推す理由:** A は正しさの関門を一時的に緩めて後で戻す形であり、その窓の間に実行器を触る
wave が 1 本でも通れば、その wave の受入は証拠として無効になる。B は同じ結果を、
権威を一度も薄くせずに得る。追加費用は認可の 1 手だけである。

## 副次的に実測したこと

- **既存テストの検出力が 3 か所で足りない (等値の可否と独立)。**
  - `_read_runner_blob` の revision 指定 (`f"{revision}:{_RUNNER_PATH}"`) を殺すテストが無い。
    unit test は `blob_reader` を差し替えるので通らず、実 Git を通す E2E は main と tip の
    実行器が同一なので `HEAD` へ変えても通る。
  - land の tip 側述語 (実在・`blob` type) が片側だけの fixture で殺されていない。
    現行の path absence test は main から消して tip で足す形、non-blob test は main を tree にして
    tip へ継承する形で、どちらも main 側の述語が先に落とす。
  - `_assert_v5_binding_baseline` は `runner_executed_sha256` を **tested tip** の blob と
    照合している。main==tip の木でしか意味を持たない書き方である。
- **land の caller 側 SHA 形式述語 2 行は恒真である。** `_runner_tree_entry` が返す値の集合が
  既に 40/64 桁 hex に限られているため。防御的重複として残す分には害が無いが、
  発火する保証として数えてはならない。
- **等値を外すと拒否の分類も変わる。** 現行は runner 不等値が先に short-circuit して
  非 retryable の拒否になる。外すと後続の外部処理失敗 (main blob 読取、checker lookup) まで進み、
  `retryable_same_request` と `release_safe` が反転しうる。
  「受理集合が 1 点だけ広がる」という言い方は、外部処理失敗を含む観測可能結果については成立しない。
- **本 wave の brief の過大主張を 1 件訂正した。** 「既存の受領証・過去の判定結果は 1 件も
  変わらない」は証明されていない。正しくは「以前受理された受領証を新たに拒否することはない。
  tracked な v5 受領証 1 件は main/tip の実行器が同一で不変。divergent な受領証の受理集合だけが
  広がる」。権威ある受領証は通常 repo 外に置かれるため、全数は確認できない。
- **launcher を先例として引く類推は完全ではない。** launcher には
  `tested-tip-bootstrap` mode があり、tip 側の実在も要求しない。実行器には bootstrap mode が無く、
  提案後も tip 実在は要求する。類推は「main が存在する通常 mode の source 選択」に限られる。
- **D987 (取り込んだ main が実行器を変えた場合だけ受領証の再利用を拒否する) は未実装である。**
  forward-main 経路は landing tip の topology を検査するが実行器を引かない。
  段 2 のプランはこの経路を positive test に固定する案を含んでいたので、そのまま実装すると
  D987 が拒否を求める入力を「成功」として凍結するところだった。
- **`tools/check_acceptance_reds.py` の受理経路 (ii) は D690 以降到達不能である。**
  待ち手は completion の `red_check` を常に `None` にし、child rc が 1 でも receipt を publish しない。
  それでも runbook は 2 つの受理経路を現役として説明している。本変更が原因ではない既存の陳腐化。

## 段 2 プランの扱い

プランは削除 2 か所・残す述語・テストの 3 分類・runbook 文案まで実装可能な水準で正確である。
`verbatim/s2-plan.md` に保存した。ユーザー裁定が A または B なら、
変更面の骨格が同一なので次 context は段 2・3 成果物を流用して段 4 から再開できる。

## ユーザー裁定と codex 相談の結果 (2026-08-27 追記)

ユーザーは「推奨 B で進めて。ただ、codex に相談し、賛成をもらったらね」と裁定した。
codex 相談 2 本 (択一の是非 / 設計の実現可能性) を投入した結果、**賛成は得られなかった**。
逐語は `verbatim/s4b-consultA.md` と `verbatim/s4b-consultB.md`、親の再裁定は
`verbatim/s4c-consult-result.md`。

- **codex は B に反対した。** 理由は「B を着地させる一度きりの land 認可が現行機構に存在しない」。
  受領証は必須で検証は merge より前に無条件で走り、D388 が受領証欠落時の bypass を明示的に
  禁じている。認可を表す consumer を B の wave 自身へ足すと、**その機構を着地させるために
  同じ例外が要る**。
- **codex の対案は三段ブリッジ P → Q → R。** P は実行器を byte 不変のまま、計算ノード側の子が
  tested main の blob を読み hash 照合して実行する機構を入れる (等値は残す)。
  Q は等値だけ外す。R で初めて実行器を編集する。**等値を外したのに束縛が無い時点が存在せず、
  一度きりの受領証 bypass も要らない。**
- **親は codex の出力を見る前に同じ形へ独立到達していた。** 根拠は環境変数の伝播経路で、
  launcher が実行器を起動する `subprocess.run` は `env=` を渡さないため launcher の環境が
  そのまま継承され、`_dispatch_environment` が `os.environ` を複製して dispatch へ渡す。
  したがって実行器を 1 行も編集せずに束縛の材料を計算ノードまで運べる。二経路の独立一致。

### codex が親の実測を補正した 2 点 (いずれも real)

1. **dispatch しない経路にも同じ欠陥がある。** queue 不可用で local budget が得られると
   bounded local 実行になるが、これも作業ツリーの実行器を pathname で再実行する。
   親の「必ず dispatch する」は言い過ぎで、正しくは「dispatch でも bounded local でも
   tip 側 file が二段目を駆動する」。是正は実行器の編集を伴うので R の担当。
2. **dispatcher 自身も束縛対象である。** 外側の実行器は dispatcher を worktree から import し、
   計算ノードの job script も worktree の dispatcher path を使う。
   runner だけ束縛しても dispatcher は tip 側のままである。

### 親が新たに見つけた未解決点 — P の束縛は tip 側コードが執行する

外側の実行器が dispatcher を worktree から import する以上、その import 先を main へ束縛するには
実行器の編集が要る (= R)。したがって P で入れた束縛は **tip 側の dispatcher が実行するコードに
よって執行される**。実行器だけを編集した wave は捕まるが、**実行器と dispatcher の両方を
編集した wave は捕まらない**。

D387 の事故モデルの下では前者が現実的な母集団なので P には価値がある。しかし
「実行元を tested main の blob に固定する保護を維持する」というユーザーの条件を、
**Q の時点では完全には満たさない**。満たすのは R の後である。よって Q の時期は二択になる。

- **Q-early:** P 直後に等値を外す。実行器を編集する wave が解禁され [T-1932] が進む。
  ただし「実行器 + dispatcher を両方触る wave」に対して無防備な期間が R まで続く。
- **Q-late:** R まで等値を維持し R の中で同時に外す。ただし R は実行器を編集するので、
  結局 B と同じ一度きり認可が要る。

この二択はユーザー裁定に返す。前者は規律 2 に対する残余を一定期間受け入れる判断、
後者は D388 の land 権威に例外を作る判断であり、どちらも親が単独で決める種類ではない。
**P はどの経路でも必要で、実行器を触らないので通常の受入・land で着地でき、後戻りしない。**

## 決定 (2026-08-27) — P に着手する / Q-early

ユーザーの再指示「codex に相談してどちらも判断してください」を受け、相談 2 本
(判断役 `verbatim/s4d-consultC.md`、反対役 `verbatim/s4d-consultD.md`) を投入し、親が決定した。
判断役は `P: 着手すべき` / `Q: early`。反対役は「三段ブリッジに致命的欠陥あり」で戻ったが、
中身は実装前に潰すべき 4 件であって放棄勧告ではなく、判断役の条件と一致した。

### 決定の土台 — 同時編集の母集団 (親が独立実測)

dispatcher 導入日 2026-07-30 以降、main 上で

| 対象 | commit 数 |
|---|---|
| 実行器を触った | 24 |
| dispatcher を触った | 22 |
| **両方を触った** | **6 (実行器を触った commit の 25.0%)** |

該当 6 件は `16df3e4e` `532635b4` `9e81501f` `a34266d2` `d26b345c` `fee55899` で、
codex の列挙と SHA が完全一致した。したがって「実行器と dispatcher を同時に編集する wave は
稀だから tip 側執行で足りる」は**成立しない**。申告 (attestation) を main 束縛コードが要求する
形 (仮説 H) は任意ではなく**必須**である。

### 段階 P の確定設計 (6 点)

1. **執行は launcher、機構は dispatcher。** main 束縛の launcher が全 shard の申告を無条件に
   要求し、dispatcher は launcher 所有の manifest がある走行にだけ束縛を適用する。
   これで P 自身の受入 (旧 launcher が動く) は落ちず、恒久的な暗黙 fallback も作らない。
   反対役が挙げた「初回だけ binding 不在」「非受入 caller が壊れる」の 2 件は、この配置で同時に解ける。
2. **同一 buffer 束縛。** hash する bytes と子の stdin へ渡す bytes を不可分にする。
   期待 digest の転記では pathname 起動へ戻す変異を殺せず恒真になる。
3. **launcher が session nonce と exact K を所有し、`0..K-1` の完全一致を要求する。**
   K を決められない走行は受け付けない。
4. **dispatch しない authoritative 受入は R まで fail-closed。** bounded local 経路も
   作業ツリーの実行器を pathname 再実行するため、ここを開けたままでは束縛が意味を失う。
5. **申告は既存の repo 外 shard artifact 経路に載せる。** 作業ツリーへ file を作らないので、
   走行前後の無変更要求に触れない。
6. **negative control 4 種** (申告欠落、digest 不一致、転記変異、非 dispatch 走) を
   launcher のテストへ置く。P 自身の受入では新機構が発火しないので、
   これらと Q の実受入が activation control になる。

**反対役の「launcher に dispatcher の main/tip 等値検査を足す」案は不採用**とした。
D838 の代償を別 file へ移すだけであり、上表のとおり dispatcher も同程度に触られている。
仮説 H が成立すれば等値検査なしで同じ保護が得られる。

### Q-early を採る理由

Q-late は選好ではなく**実行不能**である。land は受領証を必須引数とし、その検証は
`already-landed` と merge の双方より前に走る。D388 は flag・環境変数・互換 bypass を
逐語で禁じている。手動 ff-only は受領証だけでなく provenance・fold・postcondition も
まとめて迂回するので、Q-early の限定残余より侵害面が広い。

Q は P の直後に置く。**Q 自身の受入が新機構の production activation control になる** —
Q の受入は P の main launcher が動くので、申告検査が実際に発火した証拠が受領証として残る。
その緑を見てから等値を外す。仮説 H を上記の形で実装できなければ P を land せず、Q へも進まない。
