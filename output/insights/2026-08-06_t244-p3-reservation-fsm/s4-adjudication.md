# 段 4 裁定 — [T-244] P3 reservation FSM

wave: `dev-wave-t244-p3-reservation-fsm` / branch: `worktree-dev-wave-t244-p3-reservation-fsm`
起点 local main: `cfda4abe`

判断材料は 4 つの独立な情報源である — 親の段 1 前提実測 (N1〜N9 と erratum E1〜E3)、
段 2 プラン (codex read-only)、段 3 レンズ A (正しさ境界・恒真化)、段 3 レンズ B (実効性・会計・段取り)。
**両レンズが独立に NO-GO を返した。** その NO-GO を受け、下記のとおり scope と名乗りを改訂して実装する。

## 裁定 (要旨)

**実装する。ただし brief を 4 点改訂し、名乗りを「U-5 の ledger 側成分」へ縮小する。**

1. **U-5 完了を名乗らない。** 本 wave が実装するのは U-5 (c) のうち **(a) 予約 event を FSM へ追加**
   だけである。(b) caller 制御流は実装しない。理由は親の好みではなく**依存の閉塞**である —
   実 caller を作るには本番 authority へ entry が要り、それは U-10 (予算値) 未決のため
   D183 が禁じている。これは (241) の分割一覧に書かれていない依存であり、裁定パッケージへ返す。
2. **scope は 2 file でなく 3 file。** transitive consumer (E2) を含める。
3. **schema / runtime の版番号は上げない。** 段 2 プランの v3 分離案を**不採用**とする (下記 R1)。
4. **予約中 origin の復旧面 (recovery surface) を同一変更単位に含める。** 含めないと ledger 自身の
   liveness が閉じない (下記 R4)。

## 所見の裁定表

区分: `採用` = plan v2 へ入れる / `パッケージ` = ユーザー裁定へ返す / `訂正` = 親の記述を直す /
`不採用` = real だが本 wave では採らない。

| # | 出所 | 判定 | 区分 | 要旨 |
|---|---|---|---|---|
| R1 | A-1 | **real** | 採用 (代案) | authority v2 の同一 bytes が feasibility 変更で受理→拒否へ分裂する。**プランの v3 分離案では解決せず、むしろ v2/v3 の不整合を作る**。親の代案 = 版を一切上げない (下記) |
| R2 | A-2 / B-1 | **real** | 訂正 + パッケージ | 予約は「候補生成より前」を保証しない。ledger は provider 呼出しを観測しない。名乗りを縮小する |
| R3 | A-2 / B-3 | **real** | 採用 | 2-file scope では受入が閉じない。probe を scope へ入れる |
| R4 | A-6 / B-2 | **real** | 採用 | 予約中 origin の batch_id / cardinality / iteration / query 基点が公開面に出ないため、再起動した caller が commit も abandon もできず origin が永久に停止する |
| R5 | A-3 | **real** | 採用 | forfeited が certifiable floor を満たさないことを殺す負例が無い |
| R6 | A-4 | **real** | 採用 | 新 binding / counter 検査に単一理由の独立負例が不足。1 event に複数の誤りを載せると前段が後段を mask する |
| R7 | A-5 | **refuted (scope 変更により消滅)** | — | 「v3 分離に独立境界テストが無い」は R1 で v3 分離自体を不採用にしたため成立しない |
| R8 | B-4 | **real** | 採用 | 閉じる成果層は **0 / 11**。worklog と新 D に併記する |
| R9 | B-5 | **疑い → 裁定** | 採用 | `DW-G04` の artifact path は fixture 経路で満たすと裁定する。ただし「fixture 上でのみ発火し production では発火しない」を必ず併記する |
| R10 | A / B | **refuted** | — | codec feasibility の数値。両レンズが独立に再計算し、プランの literal と全数一致した |
| R11 | A / B | **refuted** | — | query / iteration partition の提案式。両レンズが到達可能な全相で成立を確認した |
| R12 | B | **real** | パッケージ | 後続分割 wave の依存順序が (241) の一覧では不足している |
| R13 | B | **nit → 採用** | 採用 | `forfeited_queries` は物理 query 数ではなく「予約した member 行数」である。field docstring と新 D に D166 の限定を継承する |

## R1 の裁定 — 版番号を上げない (プランの v3 分離案を不採用)

段 2 は event / head / state / runtime directory を v3 へ分離する案を出した。レンズ A は
**その案が authority を v2 に残したまま v2 authority の受理集合を黙って狭める**点を real 所見として
突いた (feasibility は authority parse 中に呼ばれる)。親はこれを real と認めるが、
**プランの案ではなく v3 分離そのものを取り下げる**ことで閉じる。

親が実測した根拠 (段 4 で追加実測):

- runtime root は `git-common-dir/izanagi/reflux-origin-ledger/v2` (`reflux_origin_ledger.py:1440`) で、
  **git に追跡された runtime store は 1 件も無い** (`git ls-files | grep reflux-origin-ledger` が 0 件)。
- production 初期化は明示禁止であり、本番 store は作られたことがない。
- fixture store はテストごとに tmp へ新規作成される。

したがって **v2 の event stream は世界のどこにも存在しない。** プランが v3 分離の理由とした
「同じ v2 stream を以前は受理し変更後は拒否する破壊的意味変更」は、**再解釈される stream が
存在しないため成立しない。** 版を上げない方が、v2/v3 の版境界不整合 (R1 の原因) を根元から消せる。

**ただし feasibility 包絡線が狭まる事実は消えない。** これは受理集合の変更なので D96 に従い、
新 D に明記し、境界テストで固定する。加えて `DW-S04` の「gate の禁止は署名で書き、通る正例を
1 つ添える」に従い、**本番 authority JSON が変更後も parse できること**を正例として固定する
(entry 0 件なので予算 feasibility 自体が走らない — この事実をテストで pin する)。

**帰結:** plan.md の「wire/runtime version」節 (`:187-198`)、および V01 / V15 / V21 の
schema literal 更新行は**すべて無効**とする。

## R4 の裁定 — recovery surface を同一変更単位に含める

`OriginSnapshot` (`reflux_origin_ledger.py:540`) に予約の binding field を公開する。

- 追加: `reserved_batch_id`, `reserved_iteration_index`, `reserved_cardinality`,
  `reserved_query_ordinal_start` (予約中でなければ全て `None`)。
- **漏洩は増えない。** これら 4 値は既に公開 event stream (`batch-reserved` payload) に平文で
  載っており、P5 の裁定どおり pre-seal 射影にも残る。候補 bytes も outcome も含まない。
- これを入れないと、予約直後に process が落ちた caller は再起動後に matching commit も
  abandon も構成できず、origin は `BATCH_RESERVED` のまま永久に seal 不能になる。
  **ledger 自身の liveness であって caller の都合ではない**ため、本 wave の scope 内とする。

レンズ B の指摘どおり、プランの V29 案は同一 process が予約変数を保持したまま store だけ
再生成するため kill/restart の検査になっていない。**別 process で durable 状態だけから
abandon できることを実測する node を必須**とする (既存の `_crash_script` 機構を使う)。

## 親の記述の訂正 (段 1 brief に対して)

- **(P4) を訂正する。** 「caller は書く対象が無い」は**偽**である (E2 の probe、および
  レンズ B が挙げた 8c driver `p3_autonomous_workload_trial.py`)。正しい理由は
  **「実 caller の結線には本番 authority entry が要り、U-10 未決のため D183 が禁じている」**である。
  結論 (本 wave では caller 制御流を実装しない) は変わらないが、根拠を差し替える。
- **(P2) の射程を狭める。** 「放棄 event を入れれば kill 後の seal 不能が解ける」とは名乗らない。
  event は必要条件にすぎず、R4 の recovery surface と caller の再開規則が揃って初めて解ける。
- **brief の「予算消費点を候補生成より前へ移す」を撤回する。** 正しくは
  **「`BatchCommitted` より前へ移す」**である。ledger は provider 呼出しを観測しないため、
  候補生成順は束縛できない (R2)。
- **brief の「差分は 2 file のみ」を撤回する。** 3 file とする (R3)。
- **brief の「[T-244] の残り分割 wave が乗る土台が成立する」を限定する。** 閉じる成果層は 0/11 で、
  成立するのは fixture ledger の局所受理面だけである (R8)。
- N3 / N5 / N7 の erratum は `parent-measured.md` の E1〜E3 が正本。

## plan v2 (段 2 プランからの差分。これ以外は plan.md をそのまま採る)

`plan.md` は本裁定と併せて読む。**衝突したら本節が優先する。**

| # | plan.md の該当 | plan v2 の裁定 |
|---|---|---|
| V-1 | `:187-198` wire/runtime version を v3 へ | **削除。** 版は一切上げない (R1)。`_EVENT_SCHEMA_ID` / `_HEAD_SCHEMA_ID` / `_DOMAIN_STATE` / runtime directory `v2` は不変 |
| V-2 | `:240-250` V23 / V24 の新 literal | **採用。** ただし schema 変更由来ではなく frame 数変更由来として更新する。両レンズが独立再計算で一致させた値をそのまま使う |
| V-3 | `:335-353` V01 literal golden の変更範囲 | **v3 由来の変更行を全削除。** V01 は event SHA / head SHA / state domain とも**不変**でよい。追加するのは `batch-reserved` / `batch-reservation-abandoned` の独立 literal frame だけ |
| V-4 | `:279-301` 既存 test 追随表の schema 更新列 | **v3 / `v3-real` の記述を削除。** それ以外の lifecycle 追随はすべて採用 |
| V-5 | `:390-398` public API | **`OriginSnapshot` へ予約 binding 4 field を追加** (R4)。それ以外は採用 |
| V-6 | `:355-388` 新設 test node | 採用。ただし **V29 を別 process 版へ差し替え**、下記 4 node を追加する |
| V-7 | `:411-423` 2-file blocker | **scope を 3 file へ拡張して解消。** `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` を予約対応させる。`receipt` と `preview-wire-11111.json` は**歴史記録として不変** |
| V-8 | `:100-103` counter | 採用。`forfeited_queries` の docstring に「物理 query 数ではなく予約した member 行数」を書く (R13) |

### plan v2 が追加要求する test node

1. **`forfeited` は certifiable floor を満たさない** (R5)。
   `genesis → Reserve(card=2) → Abandon → OriginSealed(certifiable, sealed=0, forfeited_q=2)` を
   floor 不足で拒否する。
2. **abandon の batch binding** (R6)。`Reserve(b0) → Abandon(b1)` を拒否し、
   続く `Abandon(b0)` が受理されることまで同じ node で示す。
3. **seal の forfeited counter 照合** (R6)。既存 counter を全て正しくし、
   **新 counter だけ**誤らせて拒否させる。
4. **別 process からの復旧** (R4)。予約 event だけを durable commit した後、
   **新しい subprocess** が `OriginSnapshot` の予約 binding だけを読んで
   matching commit / abandon を構成できることを示す。同一 process の変数持ち回しは不可。

R6 の趣旨により、**1 つの event に複数の誤りを載せない**。batch ID・iteration・cardinality・
query 基点の各不一致は、他を正しくした独立 event で 1 件ずつ拒否させる。

## 変異事前登録 (`DW-M01`。実装前に登録する)

harness は `tools/mutation_harness.py` を使う (`DW-M05`)。runner は pytest。
各変異は**赤理由が 1 つに絞れること**を親が実装後・本走前にコードで確認する。

| ID | 変異位置 | 変異内容 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | reserve 枝の Imax 検査 | 検査行を削除 | KILLED | 変更後 `BatchCommitted` 枝から Imax 検査は消えるので、前後に同じ入力を拒否する層は無い |
| M2 | reserve 枝の Qmax 検査 | 検査行を削除 | KILLED | 同上 |
| M3 | abandon 枝 | forfeit を **refund** に変える (`queries_used -= cardinality`、forfeited は加算しない) | KILLED | この変異は query partition 等式を**保つ**ため partition assert では落ちない。no-refund を直接見る node だけが殺せる |
| M4 | commit 枝の予約 binding | `iteration_index` の一致検査を削除 | KILLED | 変更後 commit 枝で iteration を見る層はここだけ |
| M5 | `OriginSealed` の forfeited counter 照合 | 新 counter 2 個の照合を削除 | KILLED | 既存 counter の照合とは独立した条件 |
| M6 | certifiable floor 判定 | `sealed_queries` を `sealed_queries + forfeited_queries` に変える | KILLED | floor 判定はここ 1 箇所 |
| M7 (正例) | reserve 枝の cardinality 上限 | 上限を `batch_cardinality_min` に固定し**過剰拒否**させる | KILLED | 受理集合を縮小する wave の承認外過剰拒否を検出する正例 (`DW-M01`) |

M7 は「受理集合を縮小する wave では、承認外の過剰拒否を検出する正例も登録する」への対応である。
実装後に anchor (old 逐語) を再検証してから本走する (`DW-M07`)。

## `DW-G05` 成果物影響

- **本 wave の実装後も、certified 選択・材料レポート・試行台帳・proof chain の現在値と参照は
  すべて不変である。** 変わるのは ledger の受理集合だけである (N5: production caller 不在)。
- **実装しない場合の影響**: 予算消費点が `BatchCommitted` のままなので、将来 caller を結線した
  ときに commit 直前の kill で候補を無料に引き直せる経路が残る。[T-244] の残り分割 wave が
  この受理集合の上に乗るため、後から入れると全 wave の境界テストを再度書き直すことになる。
- **閉じる成果層は 0 / 11** (R8)。埋まるのは機構面の一部 (event codec / FSM reducer / 無返却会計 /
  fixture 上の予約・放棄・復旧テスト) だけである。

## 名乗りの上限 (本 wave)

名乗ってよいのは
**「origin ledger の event FSM に pre-query reservation と予約放棄を入れ、予算消費点を
`BatchCommitted` より前へ移し、無返却会計と予約中 origin の復旧面を fixture store 上で実測した」**
までである。

名乗ってはならない — **U-5 の充足** (caller 制御流は未実装) / P3 充足 / 部分 P3・P4 /
production provisioning の解禁 / kill-before-commit の実運用防止 / 「候補生成より前」の保証 /
候補 batch / cap 引上げ / certified 選択の前進。
**D114 の cap=1、D166 の P4 FAIL、本番 authority の `origins: []` は不変。**

特に次を明記する。**予約は候補生成回数を束縛しない。** 束縛するのは commit できる member 行数と、
消費される予算 counter だけである。1 件の予約の下で provider を何回呼んだかを ledger は観測しない。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

- **(1) U-5 の (b) 成分は U-10 の裁定なしには実装できない。** 実 caller を結線するには本番
  authority へ entry が要り、それは U-10 (予算値) 未決のため D183 が禁じている。
  (241) の分割一覧はこの依存を書いていない。**U-5 は本 wave 後も未完のまま残る。**
- **(2) 後続分割 wave の依存順序** (R12)。レンズ B の推奨順 = ①予約 FSM + 復旧契約 + 既存 fixture
  consumer → ②ever-issued cell 台帳・authority reader/epoch/provisioning・U-10 の実予算値 →
  ③8c caller 制御・予約済み replicate・物理 evidence・critic 後置・sidecar・report v3・completeness →
  ④trial registry origin binding・P7 formal consumer・正式材料レポート。
  sidecar は seal receipt の後・report 構築の前に必要で、completeness は両者を同時に読む。
- **(3) 1 予約で provider を複数回呼べる** (R2 / scope 外)。ledger は provider 呼出しを観測しない。
  ever-issued cell 台帳と caller WAL の側で閉じる問題である。
- **(4) runtime 世代を跨ぐ累積予算** (レンズ A、scope 外)。将来 runtime を世代分離すると、
  同じ origin の予算を世代ごとに二重消費できる。epoch router / provisioning の scope で閉じる。
- **(5) 予算 feasibility 包絡線が狭まる。** frame 数が 3→4 になるため、64MiB 上限の下で
  受理できる `(Imax, Qmax)` の組が狭まる。**U-10 で予算値を決めるときはこの新しい包絡線を
  前提にする必要がある。** 本 wave が固定する新境界は境界テストに literal で入る。
