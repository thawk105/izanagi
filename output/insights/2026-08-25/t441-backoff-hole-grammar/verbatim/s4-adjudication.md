# 段 4 裁定 (確定) — [T-441] backoff 軸 EVOLVE-BLOCK hole 受理文法

段 2 プラン 1 本 + 段 3 敵対 2 レンズ (A = 正しさ境界・C++ 意味論、B = consumer 閉包・既裁定整合) を
裁定する。所見は計 12 件 (A=8、B=4 must-fix + nit/backlog)。**refuted は 2 件、残りは real。**
裁定 inbox は段 4 直前に再走査し、wave 開始後の更新なし。

## 0. 結論

**段 2 と両レンズは「設計凍結 + 裁定パッケージ」を停止点として推奨した。親はこれを部分的に採らない。**
凍結ではなく**二層に割り、Tier 1 を実装し、Tier 2 を裁定パッケージで返す。**
理由は 1〜3 に書く。Tier 1 は「両方の読みが同時に禁じる集合」だけで構成するため、
どちらの契約解釈が後で採られても過剰拒否にならない。

## 1. [T-409] README の D127 引用は過一般化である (親が独立に本文を引いて確認)

段 2 プランとレンズ B はともに「consumer だけ狭めるのは D127 決定 (1) が退けた形」を根拠に
literal-only を止めた。**D127 本文はそう書いていない。** `docs/decisions.md:6235-6239` 逐語:

> (a) は role 定義が**複数行の raw comparator**を契約上許可しており、consumer だけ狭めると
> producer 契約と非互換になり、**sort 軸では**合成が事前 allowlist からの選択に化ける。

禁止の前提は「role が複数行の生コードを許すこと」であり、明示的に sort 軸へ限定されている。
backoff 軸の role が宣言する出力は `"implementation": "double now_backoff = <式>;"` で、
複数行の生コードではない。**したがって D127 決定 (1) は backoff 軸の文の形の固定を禁じていない。**
ただし `<式>` の中身を絞る部分については、前提 (role が `<式>` を限定していない) が成立するので
D127 の論理が**そのまま当たる**。これが Tier 1 / Tier 2 の境界である。

## 2. 二つの正本が食い違っている — この衝突自体を裁定へ返す

- `docs/decisions.md:1076-1079` (D39 決定 1) 逐語: 「**coder 編集面は #if 合成枝 (hole) の 1 行のみ。**」
- `patches/silo-backoff-fixed.patch` の骨格コメント逐語: 「閉じた領域制約 (D23 道Y、hook が機械執行):
  **既存 silo API を呼ぶ straight-line code のみ。**」

前者は 1 文、後者は複数文の straight-line を許す。**さらに `orchestrator/tests/test_p3_s4_loop.py:230` の
`test_effect_scanner_runs_only_after_structure_and_sees_exact_written_hole_bytes` は、
backoff marker に 4 行の複文を渡して `accepted.passed` を期待値として固定している。**
つまりテストは後者の読みを既に固定している。

**親はこの衝突を自分で解かない。** どちらを採るかは受理集合を変える設計判断であり、
`DW-S04` の「scope 外の real 所見は実装せず裁定パッケージへ返す」に当たる。
Tier 1 は**両方の読みが同時に禁じる集合**に限る。

## 3. 実装する集合と返す集合

### Tier 1 — 実装する (どちらの読みでも禁止。既決の機械化であって契約を狭めない)

| # | 規則 | 根拠 (逐語で引ける正本) |
|---|---|---|
| T1-1 | 空実装の拒否 | 骨格の stock 枝が `now_backoff` を宣言する。空は role テンプレートでも straight-line でもない |
| T1-2 | `double now_backoff` の宣言がちょうど 1 個存在すること (型が exact `double`、名前が exact、参照 `&` でない、単一宣言子) | role `.claude/agents/coder-v4-autonomous.md:60` のテンプレート |
| T1-3 | `now_backoff` を再宣言・再束縛する形の拒否 | 同上 |
| T1-4 | straight-line 違反の拒否 (`goto` / `return` / `throw` / label / `break` / `continue`) | 骨格コメント自身が「straight-line code のみ」と宣言 |
| T1-5 | `static` / `thread_local` 記憶域の拒否 | D39 決定 7 の整合規約。呼出しを跨ぐ状態は genome の `BACKOFF_FIXED` と実行値を乖離させる |
| T1-6 | `coder.value` が整数で 1..1000、`int()` 変換が無損失であることの要求 | D39 決定 7 + role `:58` の値域宣言。**現行の実欠陥を閉じる (下記 4)** |
| T1-7 | type / raw-size の preflight を帰属検査と materialization より前に置く | レンズ A 所見 5 (real) |

### Tier 2 — 実装せず裁定パッケージへ返す

- **(i) `<式>` の中身をどこまで絞るか** (定数式のみ / literal のみ / 現状維持)。
  閉じられるのは `Backoff_.load` / `(Backoff_.store(0), 50)` の comma 形 / `rdtscp()` /
  `0.0/0.0` / `1.0/0.0` / lambda 即時呼出し / `std::max(...)` / 三項 / 算術。
  **狭化に当たるため role・review ledger・adapter・manifest を同一変更単位で改訂する必要があり、
  ユーザーの明示承認が要る。**
- **(ii) hole は「ちょうど 1 文」か「straight-line な複数文」か** (上記 2 の衝突)。
- **(iii) grammar version を identity / WAL / cache へ束縛するか** (レンズ B 所見 2、
  [T-409] must-fix B-2 の backoff 版)。束縛すると backoff campaign の ID と cache namespace が動く。
  **実測 6 のとおり自律 backoff campaign の凍結コーパスは `output/` に不在なので影響半径は小さいが、
  `DW-G04` の発火条件を満たす artifact path を親は書けない。** 先行実装しない。

## 4. real / refuted 表

| # | 出所 | 所見 | 裁定 | scope |
|---|---|---|---|---|
| A-1 | レンズ A | 小数 literal を受理すると genome `int(value)` と実行値が乖離 | **real・採用** | Tier 1 (T1-6) |
| A-2 | レンズ A | P2 単独では lambda・comma を閉じない | **real・採用** | Tier 2 (i) へ明示 |
| A-3 | レンズ A | 親の NaN/inf/負値の機序説明が誤り。実コードは積を `uint64_t` へ変換してから比較するので UB | **real・採用。追補を訂正する** | 記録 |
| A-4 | レンズ A | BNF と lexer と semantic の境界が矛盾 (`1e2` / `001` / suffix をどの段で落とすか未凍結) | **real・採用** | Tier 1 の判定順凍結 |
| A-5 | レンズ A | 新 type/raw-size gate が帰属 regex と materialization より後で遅すぎる | **real・採用** | Tier 1 (T1-7) |
| A-6 | レンズ A | 変異登録が各規則の独立検出力を証明しない (exact parser が前段を mask する) | **real・採用** | 変異登録を 2 分割 |
| A-7 | レンズ A | P1 は偽、P2/P4 は条件付き | **部分 real** | 上記 1〜3 |
| A-8 | レンズ A | 32 形実測は quarantine 単体で、純増検出力の射程が過大 | **real・採用** | 記録の限定 |
| A-9 | レンズ A | macro parity gate なし | real・**backlog** | scope 外 |
| B-1 | レンズ B | `quarantine()` 1 点は consumer 閉包でない (D127 決定 (3)) | **構造は real / 即時の抜け道は refuted** | 下記 5 |
| B-2 | レンズ B | grammar version が identity/WAL/cache に非束縛 | **real・不採用 (scope 外)** | Tier 2 (iii) |
| B-3 | レンズ B | 小数と `int(value)` の乖離 | **real・採用 (A-1 と同一)** | Tier 1 (T1-6) |
| B-4 | レンズ B | 正準化がない (`20` / `20.0` / `20.00` が別 variant) | **real・採用** | Tier 1 (T1-6 が同時に閉じる) |
| B-5 | レンズ B | freeze 対象は 7 file でなく 9 file (外部 2 件を親が数え落とした) | **real・採用。親の実測 3 を訂正** | 記録 |
| B-6 | レンズ B | 親の実測 1/4/6 の射程が過大 | **real・採用** | 記録の限定 |

## 5. B-1 の裁定 — 構造は real、即時の抜け道は実測で refuted

レンズ B は「`quarantine()` の呼び手閉包を build consumer 閉包と取り違えている」と指摘し、
D127 決定 (3) 「gate は driver でなく materializer に置く」を引いた。**構造の指摘は正しい。**

**しかし「今日すでに文法外の bytes が別経路で build へ進む」という強い読みは、親が現物で反証した。**
レンズ B が挙げた別経路はいずれも **coder 由来テキストを穴へ入れない**。

- `p3_kickoff.py:62-63` — 穴へ入るのは commit 済みの人手 patch (`patches/variant-backoff-static50.patch`)。
  同 file の逐語コメントが「coder が書いた合成枝の実体は patch 側の literal」と書いている。
- `s1_direct_comparison.py:651-659` — `backoff_fixed_best` は CMake flag が枝を選ぶだけで
  EVOLVE-BLOCK を置換しない (同 file の逐語コメント「EVOLVE-BLOCK は置換しない」)。
- `backoff_sweep.py` — `implementation` / `render_hole` / `hole` の出現が **0 件** (完全検索)。genome flag 駆動。

したがって **coder 由来テキストの ingress は `quarantine()` の 1 点で正しい。**
採るのは「その事実をテストで固定する」ことである — 将来 coder テキストを通す経路が増えたときに
黙って穴が開かないよう、閉包を機械検査へ移す。materializer 側への gate 複製は Tier 2 (iii) と束ねて返す。

## 6. 変異事前登録 (DW-M01 / B-057。実装前に凍結)

B-057 は述語 `validator_or_rejection_gate_changed` で発火する (新 reject gate の新設)。
既裁定は**追認のみ**なので追加裁定はせず、実装前登録の義務だけ履行する。

**レンズ A 所見 6 を採り、変異を 2 種へ分ける。** exact parser が前段を mask するため、
「層を消す変異」は受理集合を変えないことがある。単一理由性 (`DW-M01`) を守るため、
**受理集合を広げる変異**と**拒否 stage/rule ID を変える変異**を別カテゴリで登録し、
後者の kill は「診断文字列だけの赤」ではなく **rule ID の観測値が期待と変わること**で数える
(`DW-M03` の「受理集合か fail-closed 挙動が期待方向へ変わったとき」に該当させる)。

| ID | 変異 | 種別 | 期待 |
|---|---|---|---|
| t441.m01 | validator を無条件 `accepted=True` | 受理集合 | KILLED (負例全件 + 正例は緑のまま) |
| t441.m02 | validator を無条件 `accepted=False` | 受理集合 | KILLED (**正例が落ちる = 過剰拒否の検出。`DW-M01` の正例登録**) |
| t441.m03 | 空実装検査を外す | 受理集合 | KILLED |
| t441.m04 | 単一宣言子検査を外す | 受理集合 | KILLED |
| t441.m05 | 型 exact 検査 (`double`) を外す | 受理集合 | KILLED |
| t441.m06 | 参照束縛検査を外す | 受理集合 | KILLED |
| t441.m07 | straight-line 検査を外す | 受理集合 | KILLED |
| t441.m08 | `static` / `thread_local` 検査を外す | 受理集合 | KILLED |
| t441.m09 | `value` 整数性検査を外す | 受理集合 | KILLED |
| t441.m10 | `value` 値域 1..1000 を外す | 受理集合 | KILLED |
| t441.m11 | preflight を帰属検査の後ろへ戻す | 拒否 stage | KILLED (rule ID / 例外の観測が変わる) |
| t441.m12 | marker 条件を全 marker へ拡張 | 受理集合 | KILLED (trigger / sort 非影響テストが落ちる) |
| t441.m13 | marker 条件を削除 (backoff でも走らせない) | 受理集合 | KILLED |
| t441.m14 | 閉包テストの対象集合を空にする | 受理集合 | KILLED (positive control) |

`DW-M04` に従い置換対象の一意性を実装後に確認し、一意でなければ登録から外して理由を記録する。
`DW-M05` に従い `tools/mutation_harness.py` を使う。baseline 緑を先に取る。

## 7. 記録に必ず書く限定 (書かないと過大主張になる)

- **Tier 1 を land しても backoff 軸で規律 2 が成立したとは書けない。** 式段の逸脱
  (`Backoff_` / `rdtscp` / NaN / inf / lambda / comma / 三項) は Tier 2 の裁定まで開いたまま。
- **32 形の実測は `quarantine()` 単体の字句的増分であって、certified 受理集合を測っていない。**
  build / verify / bench / COMMIT / cache / WAL replay は測っていない (レンズ A 所見 8)。
- **production では帰属検査が quarantine より前にある** (`p3_s4_loop.py:971`)。
  数値 literal を含まない敵対形は今日でもそこで落ちる。ただし `value` も coder が出すので、
  一致する literal を入れれば通る。**敵対的な受理集合は依然として広い。**
- **freeze の live source pin は 9 file** (Python 7 + `external/ccbench` の 2)。主編集面はその外。
- 親の NaN/inf 機序説明は誤りだった (A-3)。実コードは積を `uint64_t` へ変換してから比較する。
