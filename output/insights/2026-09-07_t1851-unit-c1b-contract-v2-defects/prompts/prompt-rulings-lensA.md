単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; task=[T-1851] C1b 未裁定 4 件の裁定

# レンズ A: 開ける道を 1 本決める

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a`、
HEAD は `68573078e` である。コードも文書もすべてこの worktree の中を読む。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/s4-adjudication.md`
   — **本件の正本。** 1 節が実測で確定した契約 v2 の欠陥 7 件 + 偽造 2 件、2 節が親が確定させた
   訂正、**3 節が本相談の対象である未裁定 4 件**、5 節が段 3 所見の裁定表
2. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s3-lensA.md`
   — 正しさ境界レンズの所見 (A-01〜A-12)。**A-06 / A-07 / A-08 / A-09 / A-10 が本相談に直結**
3. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s3-lensB.md`
   — 整合と実効性レンズの所見 (B01〜B13、S01〜S04、M1〜M18)
4. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/parent-verification.md`
   — 親の独立検算 V1〜V6 と、誤りだった V3 の撤回
5. `output/insights/2026-09-07_t1851-unit-c-launcher-raw-facts/s4-adjudication.md`
   — **前 wave が固定した契約 v2 の原文。** 3 節が exact な field 表・cross-field 不変条件・
   再導出 6 枝・E2 の 4 語・crash 後の権威、5 節が C1b / C2 / D2 の境界
6. `output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s2-plan.md`
   — 段 2 の実装プラン (判定は「実装不可」)

主要な現物 (自分で開いて確かめる。行番号は引用でなく現物から取る):

- `orchestrator/campaign/attempt_registry_core.py` — 台帳 core。terminal の検査順序、
  `terminal_row_validator`、`record_attempt_terminal`、genesis の `retryable_failure_reasons`
- `orchestrator/campaign/s8b_attempt_profile.py` — v1 / v2 の profile、`S8B_V2_RETRYABLE_FAILURE_REASONS`、
  `_reject_unsealed_s8b_v2_terminal`、`make_s8b_v2_domain_profile`
- `orchestrator/campaign/s8b_floor_attempt_launcher.py` — 起動層。分類語彙の定数、
  `_pre_observation_failure_reason`、`_CLASSIFICATION_POLICY` と authority digest
- `orchestrator/campaign/s8b_floor_campaign.py` — `_finish_session` と、その手前の理由 precedence
- `orchestrator/calibrator/runner.py` — 計測 runner。`notes` と rep 記録の生成元
- `orchestrator/campaign/s8b_floor_stats.py` — `assess_session`、`_derive_rep_integrity`
- `orchestrator/campaign/s8b_attempt_registry.py` — adapter。handle、claim、create-only publish

## 絶対に守る制約 (この repo の憲法。緩める提案は却下される)

- **規律 2: 正しさゲートを緩める変異を許さない。** anomaly を検出した対象は即 reject。
  性能や利便のためにゲートを緩めない。
- **規律 3: 正しさシグナルを後付けにしない。** 検査は pass/fail でなく「なぜ壊れたか」を構造化して返す。
- **D1113: 呼び手は証拠の値を選べない。**
- **規律 7: 過去の判定は追記でのみ訂正する。** 遡って無効化しない。

## 共通の制約

- 読取専用である。実装しない。書込可能な tmp が無いので pytest を走らせない (走らせられない)。
  テストの実測は親が行う。子の非実走を緑と数えない。
- **選択肢を並べるのではなく決めろ。** 各項目に**ちょうど 1 つの推奨**を出し、
  採らなかった案を却下理由付きで書く。「どちらもありうる」は回答として不受理である。
- 主張には **[実測] / [推測]** を付ける。行番号・件数・key 集合・値域は必ず [実測] にする。
  文書に書かれた行番号を転記せず自分で現物に当たる。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 三軸語 (`ycsb_rratio` / `ycsb_zipf_skew` / `ycsb_rmw`) の**値**を出力に書かない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、4 項目の推奨を各 1 行 + 全体の実装可否を 8 行以内で書け。

## このレンズの依頼 — 開ける道を 1 本決める

未裁定 4 件に対し、**v2 台帳の terminal 行が実際に書けるようになる最小の設計**を 1 本決めよ。
「決められない」「ユーザー次第」は不受理である。決めたうえで、その決定が規律 2 を緩めていないことを
自分で反証しにいけ。

### (1) core の等値検査と E2 語彙の衝突 — 最重

[実測済みの事実] `attempt_registry_core.py` は terminal 行に対し
(a) `failure_reason` が観測前分類の理由と等しいこと、(b) 同じ値が genesis の retryable 集合
(v2 では E2 の 4 語) に入ること、を**この順で**要求し、封印証拠の検査 hook はその**後**にある。
launcher の分類語彙は 2 語で E2 の 4 語と互いに素。E2 の 4 語を直接投入すると全件が (a) で落ち、
検査 hook は 1 度も呼ばれない。

親の当初案「v2 では分類語彙を E2 の 4 語にする」は否定済みである。E2 の 4 語のうち 2 語は
計測を開いた後にしか判明せず、分類は開く前に起きるため 4 語全部には適用できない。

**決めること:** どう直せば v2 の retryable terminal が書けるようになるか。
次を必ず含めること。

- **変更する関数と、変更後の signature を書く。** `attempt_registry_core.py` のどの行の条件を
  どう変えるか、`s8b_attempt_profile.py` の `TransitionPolicy` にどの field を足すか (足すなら)、
  launcher が何を渡すか。
- **v1 の受理集合が 1 bit も変わらないこと**を、v1 profile の値と現行 test から示せ。
- **「観測前に分類された理由」と「観測後に導出された理由」を分ける**案を採る場合、
  台帳行の key 集合がどう増えるか (v2 の event key 表への追加) と、
  crash 後に行だけを見て両者を再検査できるかを示せ。
- **規律 2 の反証:** この変更で新しく受理されるようになる terminal を全列挙し、
  そのうち 1 つでも「本来拒否されるべきもの」が混ざらないことを論じよ。
  特に、**capability を持たない呼び手が同じ道を通れないこと**を示せ。

### (2) `exec_failures` の出所

[実測済みの事実] 契約は「私有 sink の非 zero rc / 起動失敗の rep 数」と書き、campaign は
`notes` の regex からしか算出しない。レンズ A の実測では rc=1 が 2 本・notes 空のとき
campaign は `exec_failures=0` / `rep_integrity_failures=2` を返す。契約の「全件等値」は
実データで破れる。

**決めること:** (2-a) C2 で campaign の算出を sink 由来へ変える (計測の意味論の変更) か、
(2-b) 契約側を campaign の現行算出に合わせるか。

判断の軸は「**証拠は何を証明するためにあるのか**」である。
- この値が下流の何を決めるか (`excluded_reason` の precedence、`valid`、再測の可否) を現物で追え。
- (2-a) を採ると、過去に記録された測定の意味が変わるか。変わるなら規律 7 との関係を書け。
- (2-b) を採ると、証拠が主張できることがどう弱まるか。弱まった証拠でも
  「呼び手が値を選べない」(D1113) は保てるかを示せ。

### (3) 封印の信頼境界

[実測済みの事実] レンズ A は、現行の同型実装に対し発行台帳への直接 insert、private 発行子の
直接呼出し、`__reduce_ex__` 経由の発行がいずれも accepted になることを直接評価で示した。
また test 用 launcher が production 本体と同じ関数を呼び、probe・registry・capture・分類権威・
terminal builder を全部注入できる。

**決めること:** 同一 process 内の任意 module 改変を脅威に含めるか否か。
- 含めないなら、**その除外を明文でどう書くか**を逐語で起草せよ。曖昧に「現実的な脅威に限る」と
  書くのは不可。何を守り何を守らないかを、攻撃者の能力で定義せよ。
- 含めるなら、Python module の中で封印できないので何をするか (別 process 隔離など) を、
  この repo の規模で現実的な形で 1 つ決めよ。
- どちらでも、**test 用 launcher が production の封印を発行できない構造**を必ず設計に含めよ。

### (4) C1b の単位

[実測済みの事実] レンズ B は「production 効果のある分割は存在しない」と判定した。
`leaf + launcher` は呼び手 0 件の module と早期 gate で止まる launcher を積むだけで、
v2 terminal を 1 行も増やさない。全部を縦に積むと plan 見積りで production +1,228〜1,717 /
test +1,775〜2,465 で、前 wave 実績の約 3.6〜5.1 倍になる。

**決めること:** 次の wave で何を作るか。上の (1)(2)(3) の決定を反映した後の**再見積り**を出し、
1 wave で収まるか、収まらないならどこで切るかを決めよ。
レンズ B が「契約が要求していない自発的拡張」と判定した 3 件 (durable claim の新 schema、
handle state への mode 追加、core の全 load 面への引数伝播) を落とした後の規模で見積もれ。

## 出力形式

`## (1)` 〜 `## (4)` の 4 節をこの順で置き、各節に次を書く。

- `**決定:**` 1 段落。何をどうするか。
- `**根拠:**` file:line と実行結果。[実測] / [推測] を付ける。
- `**却下した案:**` 各 1 行で理由付き。
- `**規律 2 の反証:**` (1) と (3) では必須。他は該当すれば書く。
