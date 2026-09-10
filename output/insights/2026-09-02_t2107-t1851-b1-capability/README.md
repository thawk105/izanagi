# [T-2107] 分類権限の着手前実測 + [T-1851] 実装単位 B1

2026-09-02。branch `worktree-dev-wave-t2107-t1851-b1`、base `6ff06800d` (着手時 local main)。
実装 commit `cb1f56b8ee054463a0f37e4c95d0730113dfb421`。
**D1341 により単独では land しない unlanded checkpoint である。**

台帳配線 3 task 閉包 (T-1851 前半 / T-2107 / T-1946) の 6 段分割
`B1 → A → B2 → D1 → C → D2` のうち、**B1 だけ**を実装した。残り 5 段は次以降の wave が担う。

## 中身

| file | 内容 |
|---|---|
| `brief.md` | 段 1 の親 brief。**段 4 裁定の訂正表が上書きする** |
| `s4-adjudication.md` | 段 4 裁定。T-2107 の結論、scope の縮小、API の不変条件 4 件、変異事前登録、裁定パッケージ |
| `mutation-spec-probe.json` / `mutation-probe-out.json` | 変異 probe (全件 SURVIVED 期待で観測 node を集める段) |
| `mutation-spec-final.json` / `mutation-final-out.json` | 変異本走。10 変異すべて期待と完全一致 |
| `verbatim/s2-plan.md` | 段 2 plan |
| `verbatim/s3-lens-a.md` `verbatim/s3-lens-b.md` | 段 3 敵対検査 2 本 |
| `verbatim/s5-author.md` | 段 5 実装子の完了報告 |
| `verbatim/s6-review-a.md` `verbatim/s6-review-b.md` | 段 6 敵対レビュー 2 本 |
| `verbatim/s6-fix.md` | 段 6 fix 子の完了報告 |

## 1. [T-2107] の結論 — 機械導出できる。ユーザーへ返す値は無い

D1380 は着手前の実測を要求していた。**答えは (i) 機械導出できる**で、止めてユーザーへ返すべき
未決値は存在しない。

決め手は、D1380 が名指す面の同定である。逐語は「計測の**起動層**が**出力前**に成否を分類する方針を
名乗るための production 定数」であり、現物にはその面がちょうど 1 つ実在する。

- `orchestrator/campaign/s8b_floor_attempt_launcher.py:105-110` の `ClassificationAuthority` は
  docstring で自らを "Pinned identity for the launcher's **pre-output** classification policy" と
  名乗る。起動層の出力前方針であり、D1380 の語と一致する。
- 方針を実行する純関数は同 file `:378-385` の `_pre_observation_failure_reason` で、結果は
  post-probe 競合・起動失敗・理由なしの**ちょうど 3 つ**。自由選択は無い。
- したがって権威文書の値は、この 2 つの理由定数、probe の意味、優先順位、権威 id、schema version
  だけから機械導出できる。**人間が新しく決める値はゼロ。**
- 既存の同型権威 `s8b_scheduler_accounting.authority_policy_document()` (`:65-102`) と同じ形
  (module 定数を canonical 文書へ射影し bytes の digest を取る) がそのまま使える。

### 親と段 2 plan がともに面を取り違えていた

親 brief は campaign の最終 `excluded_reason` ラダー (`s8b_floor_campaign.py:6147-6162`) を対象と読み、
閾値 `session_cv_max` を権威文書へ埋めるべきかで悩んでいた。これは**出力後**の面である。
段 2 plan も 4 理由すべてを一つの権威に入れる前提で、閾値と反復数の収録を提案していた。
段 3 のレンズ A がこの混同を反証した。

**取り違えの実害:** 親は存在しない設計択一 (閾値の収録可否) をユーザー裁定候補に数えかけていた。
面を正しく取れば、その択一自体が発生しない。

### 4 理由すべてを名乗る権威を作る場合は答えが変わる

将来 campaign の 4 理由すべてを一つの権威で名乗るなら、答えは **(iii) 条件付き**になる。
レンズ A が数値で示した — 反復 5 の `[90, 95, 100, 105, 110]` は閾値 `0.10` で valid、
`0.05` で performance anomaly になる。4 理由を名乗るなら閾値の収録は必須であり、
さらに導出主体を campaign から起動層へ移す作業が要る。**本 wave はその権威を作っていない。**

### 配線側への要件

権威文書を手で組み立てるだけでは、分類規則だけを変えたときに権威 digest が旧値のまま残り、
「旧方針を名乗って新規則で分類する」状態を作れる。分類の実行と canonical bytes を
**同一の宣言 object から生成する**こと。これは配線側の設計要件であり、上記の分岐の答えを変えない。

## 2. [T-1851] B1 の中身

`orchestrator/campaign/s8b_holdout_admission.py` と `orchestrator/tests/test_s8b_holdout_admission.py`
の 2 file だけ、`+998 / -13` 行。

- cell token へ現行世代の claim digest を read-only で射影する (`str | None`。旧世代の
  inspector 再構築は `None` を渡すため型を固定できない)。
- 消費 marker を admission 側で完全再導出して検証し、opaque な capability を返す。
- capability は使用時に marker・claim・主台帳行を同じ lock 区間で再導出し、発行時 identity との
  完全一致を要求する。identity には 3 文書の canonical bytes digest を含む。
- 試行枠 identity の 4 軸すべてへ束縛する。
- 現行世代専用である。旧世代 token は発行者の process-local state へ登録されないため発行できない。
- 呼び手が保持する lock handle を必須とし、非 live な handle を機械的に拒否する。

設計判断の正本は decisions の該当エントリ。

### 受理集合は変えていない

既存の消費経路、既存 marker validator、旧世代 cut-6 の回復経路はいずれも不変である。
adapter の差し替えは単位 A の所有なので含めない。

### 閉じていない窓を明記した

試行枠 4 軸のうち反復と序数の権威は journal だが、journal の書き手は admission root lock に
参加しない。この TOCTOU 窓は既存の性質であり、本変更は閉じていない。docstring にそう書いた。

## 3. 前 wave の分割裁定を親が越えかけ、撤回して安くなった

親 brief は `(P1-c)` で adapter の差し替えを B1 に含めると裁定した。しかし前 wave の終端裁定は
逐語で `B1 (claim/marker capability) → A (core/profile/adapter)` と書いており、**adapter は単位 A の
所有**である。段 3 のレンズ A がこれを指摘し、親は段 4 で撤回した。

撤回によって次が同時に消えた。

- 意図的な赤 21 node (adapter の署名変更に由来)。受入で緑を要求できるようになった。
- 共有 fixture への新 helper 追加と、その 10 consumer file への波及。
  既存の admission テストが消費経路の完全な流れを 39 箇所で既に持っており、新 fixture が不要だった。
- 規模超過。段 3 のレンズ B が見積もった 550-850 行 / 45-65 node のうち、adapter と fixture の分が落ちた。

**承認済みの分割裁定を守る方が、越えるより安かった。**

## 4. 段 3 の 2 レンズは非対称だった

一方 (レンズ A) は現物のコードを読み、全所見に file:line を付けた。
他方 (レンズ B) は射影した 4 資料だけを読み、**全所見を自ら推測と申告した**。

親が全件検算した結果、レンズ B の blocker 2 件は現物で反証された。

- 「pre-probe 失敗と必須 marker が両立しない」→ 2 つの開始 API は**どちらも**同じ内部関数へ合流し、
  そこが消費 marker の検査を無条件に呼んでいる。marker 必須は既存の制約であり、B1 の新設ではない。
- 「launcher 分の赤が数え落とされている」→ launcher テストの 6 呼出しは全て偽 registry を注入し
  (1 つは呼ばれたら失敗する哨戒)、実 adapter を通さない。

**コードを読まないレンズの blocker は、そのままでは差し戻し理由にならない。**
一方で同レンズは、規模の過小評価、変異の単一理由性、検索語からの一般化といった
**手続きの穴**を正確に突いており、価値は別のところにあった。

## 5. 変異 matrix — 7 KILLED / 3 SURVIVED (全件事前登録どおり)

`mutation-final-out.json`。baseline PASSED、`repo_head` は実装 commit、10 変異すべて
`matches_expectation=True`。

| ID | 対象 | 結果 |
|---|---|---|
| M1 | claim 文書の canonical bytes digest | KILLED (2 node) |
| M2 | 主台帳行の canonical bytes digest | KILLED (1 node) |
| M3 | marker 文書の canonical bytes digest | KILLED (1 node) |
| M4 | 現行世代 guard | **SURVIVED (到達不能)** |
| M5 | disk marker と canonical marker の等値 | KILLED (12 node) |
| M6 | claim digest と発行者 state の照合 | **SURVIVED (冗長)** |
| M7 | 使用時の durable 再導出比較 | KILLED (1 node) |
| M8 | 渡された identity と保存 identity の比較 | KILLED (8 node) |
| M9 | live lock 検査 (片側だけ) | **SURVIVED (二重呼び出しに覆われる)** |
| M10 | live lock 検査 (両層同時) | KILLED (1 node) |

### 生存 3 件の切り分け

`DW-M02` に従い、生存をそのまま「検査が効いていない」と数えず、他層の mask と等価変異を疑った。

- **M4 は到達不能な防御 guard。** 旧世代 token は発行者 state へ登録されないため、
  この分岐へ入る入力を構成できない。段 3 レンズ A が構造的に指摘した性質が、実測で裏付いた。
  **不到達を到達可能に見せる test を作らない。** 冗長として記録する。
- **M6 は canonical helper 自身の claim 検証に覆われた冗長検査。** `DW-M03` に従い
  単独変異の証拠から外す。
- **M9 は二重呼び出しによる mask。** live lock 検査は再導出側と使用側の両方から呼ばれており、
  片側だけの変異では他方が拒否する。`DW-M04` に従い**両層同時変異 M10 を kill 期待付きで
  事前登録**し、KILLED を実測した。**これにより M9 の生存が「効いていない」ではなく
  「もう一方が拒否していた」ためだと実証できた。**

### erratum — probe の結果を消さない

`mutation-spec-probe.json` / `mutation-probe-out.json` は、全件 SURVIVED 期待で登録して
観測 node を集めた第 1 段の記録である。rc=1 はその設計上の不一致であり異常ではない。
本走の期待 node 集合はこの実測から作った。

## 6. 検査

- 着手前 baseline: `test_s8b_holdout_admission.py` + `test_s8b_attempt_registry.py` で
  **190 passed / 0 failed**。着手前の赤はゼロ。
- 段 6 fix 前の焦点走: 165 passed / **1 failed** (実装子の新規テスト自身の一時 directory 欠陥)。
- 段 6 fix 後の焦点走: `test_s8b_holdout_admission.py` **175 passed / 0 failed**。
- consumer 焦点走 (変更 module を参照する 8 file を参照関係で引いた): **1181 passed / 5 skipped /
  0 failed**。lock handle の戻り値変更が既存呼び手を壊していないことの実測。
- 変異本走: 10/10 一致 (KILLED 7 / 事前登録 SURVIVED 3)。
- provenance: 実装 commit の全史監査 rc=0。

**codex 子は本環境で pytest を実走できない。** 実装子と fix 子の 2 本とも
`qstat -Q preflight rc=1` で rc=16 となり dispatch child が起動しなかった。
両者とも緑を主張せず「実装済み・未実走」と報告した。**上記の実測はすべて親が行った。**

## 7. ユーザーへ返す裁定パッケージ

いずれも scope 外の real な所見で、親は実装せず設計択一として返す。

1. **配線側: 分類権限を宣言 object 駆動にするか。** 手で組み立てる権威文書は、規則だけ変えたときに
   digest が追随しない。分類の実行と canonical bytes を同一 source から生成する案を採るか、
   追随を別の機構で保証するか。
2. **単位 A: 旧世代 token の capability 発行入口を作るか。** 現状、旧世代 token は発行者 state へ
   登録されないため capability を発行できない。旧世代の受理を保存する再検証入口を設けるか、
   旧世代の受理を前向きに廃止するか。後者は受理面の縮小なので親だけでは選べない。
3. **配線側: 計測前 probe による除外の権限層。** marker 無しで正当に終端化する経路が要る。
4. **配線側: crash 回復が token と capability を再取得する層。**
5. **journal の TOCTOU 窓を閉じるか。** 試行枠の反復と序数の権威は journal だが、
   その書き手は admission root lock に参加しない。既存の性質であり本 wave は閉じていない。

## 8. 次 wave の出発点

- 実装単位 A (core/profile/adapter) から続ける。adapter は本 wave の capability を消費する側であり、
  同じ lock を再取得しない内部更新 seam を新設する必要がある。
- 6 段すべてを積んだ後に、D1341 に従って 1 commit だけ land する。
- 本 wave の worklog / decisions fragment は `docs/spool/` に置いてあり、その land 時に fold される。
