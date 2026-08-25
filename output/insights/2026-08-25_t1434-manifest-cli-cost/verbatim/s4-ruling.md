# 段 4 裁定 — [T-1434] task manifest の CLI 入力口と費用の正規化計算

- 段 2 プラン: `s2-plan-2.md` (22446 bytes、check_codex_output rc=0)
- 段 3 レンズ A (正しさ境界): `s3-lensA.md` (19485 bytes、rc=0)、所見 A-1〜A-9
- 段 3 レンズ B (変更閉包・実効性): `s3-lensB.md` (21982 bytes、rc=0)、所見 B-1〜B-9
- 裁定 inbox 再走査 (段 4 直前): 本件に関する新しいユーザー裁定は無い。
- main は wave 開始後 `c83b5b2c` → `a068b7f5` へ前進。取り込みは受入の post-claim merge で行う。

## 0. 親自身の誤りの訂正 (先に確定させる)

段 1 brief の「実測した前提」のうち 3 項目が誤り・一般化過剰だった。両レンズが独立に指摘し、
親が現物で裏取りした。

| brief の記述 | 実際 | 裏取り |
|---|---|---|
| `supervise_pair` は既に `task_manifest` 引数を持つ | **持たない** | `tools/codex_reasoning_ab.py:7181-7196` の署名に無い |
| resource 行を作るのは `_replay_manifest` | **`_aggregate_verified`** | 同 `:9752-9790` |
| receipt に cache_write 対応 field が存在しない | 正規 receipt には無いが、**raw usage には `cache_write_input_tokens` が実在**する | 同 `:7789` |

3 件目は重要である。「価格不明」の実体は**単価が不明なのではなく、正規 receipt が数量を保存していない**
ことである (単価は sol `5` / luna `0.25` と snapshot に実値がある)。完全な費用を出すには
receipt schema と price snapshot の新しい登録世代が要る。本 wave の scope 外とし、裁定パッケージへ回す。

## 1. real / refuted と採否

### 採用する (real、scope 内、実装必須)

| # | 所見 | 裁定 | 成果物影響 (DW-G05) |
|---|---|---|---|
| R1 | A-1 / B-5 (CRITICAL) token 0 が「測定不能」と区別されず 0 USD になる | **real・採用** | 測定できなかった試行が 0 円として arm 集計に入り、費用比較を過小方向へ歪める。証拠の数値が直接誤る |
| R2 | A-2 (CRITICAL) 検証した bytes と cost 計算に使う bytes が同一でない | **real・採用** | 検証後に差し替えられた単価で計算した費用が、凍結 version の名前を掲げたまま出る |
| R3 | A-3 / B-2 (CRITICAL) task manifest の同一性が CLI 呼び出し間で束縛されない | **real・採用 (scope 拡大を親が認める)** | 下記 §2 で単独に論じる |
| R4 | A-6 (HIGH) loader が宣言した UTF-8 / 一意 JSON 契約を実装しない | **real・採用** | 重複 key の後勝ちで、同じ表示のまま別の oracle 種別・別の finding 集合が採用される |
| R5 | A-4 / A-5 (HIGH) partial な費用が完全な費用・certified 証拠に見える | **一部採用** | 下記 §3 |
| R6 | A-7 (MEDIUM) cost 層の拒否条件のうち 3 つが恒偽 | **real・採用** | 恒偽の条件を「防壁」として登録すると、実際には何も守らない gate が台帳に残る |
| R7 | B-6 実装子 A / B は並列投入できない | **real・採用** | 段 5 は A → B の順次投入。docs は親が最後に一度だけ扱う |

### real だが scope 外 (裁定パッケージへ回す)

| # | 所見 | 理由 |
|---|---|---|
| S1 | B-3 の中核: 費用を §11.2 の resource 指標・§12 の gate 表・overall へ接続する | 部分被覆を pass / fail / inconclusive のどれにするかは**事前登録の protocol の意味規則**であり、本 wave が決めてよい事柄ではない。command が protocol 改訂を禁じている |
| S2 | 正規 receipt へ `cache_write_input_tokens` を保存し、完全な費用を出す | receipt schema と price snapshot の新しい登録世代が要る。凍結 artifact の bytes を変える |
| S3 | (b) `_load_adjudication` の task-specific oracle 対応 | command が明示的に scope 外とした。§8 の独立 oracle ledger 待ち |
| S4 | `_certification_scope` を改訂して費用を certified field にする | certification 契約の改訂であり protocol に属する |
| S5 | served model attest の不在 (レンズ A・B が独立に指摘) | 既知の未解決点。本 wave は requested SKU による正規化値しか作らない |

### 撤回する (親の provisional 裁定 P1)

**P1 を撤回する。本 wave は `docs/phase3-t189-model-routing-preregistration.md` を一切編集しない。**

- レンズ A は「文書本文を変更する以上、例外が明示されない限り事前登録の改訂として扱うべき」と述べ、
  レンズ B は「§5.2 の 4 行 + §10 の 81-83 に限れば耐える」と述べた。両者は割れている。
- 親は §13 と D674 の**原文を読んでいる**。§13 の凍結対象は「run 開始後の oracle・margin・
  task 除外規則・判定表」であり、run は開始していない。したがってレンズ A の
  「立証不能」という理由付けは、A への射影が §13 原文を含まなかったことの影響であって、
  それ自体は決定的でない。
- **しかし結論はレンズ A を採る。** 理由は原典解釈ではなく、ユーザーの明示指示である。
  command は「事前登録文書そのものを改訂する必要が出たら、凍結・再事前登録の手続きに従い、
  勝手に in-place 改訂しないこと」と書いている。判断が割れる場面でこの指示を狭く読む根拠は無い。
- 代わりに、**到達度の食い違いを worklog へ正直に記録し、差し替える文面案を裁定パッケージとして
  ユーザーへ返す。** 文面案はレンズ B が特定した 5 箇所 (§5.2 の 4 行、§10 の 81-83) を対象とする。

### 不採用 / refuted

- A-9 の項目 5 (「事前登録文書に whole-file pin が無い」は未立証)。親が `tools/check_docs.py` を
  実測しており、pin は cleanup-branches skill の 1 件だけである。ただし本 wave は同文書を
  編集しないので、この点は結論に影響しない。
- B-1 の「invocation-local な入力口は入力口と言えない」という言い方は採らない。
  R3 を実装すれば実験工程を通じた入力口になる。実装しない場合の扱いは §2 に書く。

## 2. R3 — なぜ scope を広げるのか (最重要の裁定)

`--task-manifest` を足すだけの実装は、**現状より正しさを弱める。**

- 現在、task manifest は module 定数であり、実験工程の途中で差し替える経路が存在しない。
- `--task-manifest` を足すと、`make-packets` → `append-verdicts` → `freeze-verdicts` →
  `reveal-mapping` → `verify` を**別々の manifest で順に実行できる**。
- packet state (`:10727-10731`)、private mapping (`:10736-10743`)、verdict freeze (`:10932-10938`)
  のどれにも task manifest の digest が無いため、この交換は検出されない。
- 交換対象には `known_finding_ids` (verdict の `equivalent_to` 受理集合) と `oracle_kind`
  (positive / negative の分類) が含まれる。**これは正しさゲートそのものの受理集合である。**

絶対規律 2 は「正しさゲートを緩める変異を許さない」と定める。性能や利便性のために緩めてはならず、
これは本 wave の scope 定義にも優先する。したがって:

**裁定: R3 を実装するか、さもなくば (a) を実装しない。両方を満たさない中間案は採らない。**

実装の要求は次のとおり。

1. 外部 manifest を受け取った時点で、**その canonical bytes の SHA-256** を計算する。
2. その digest を、既に連鎖している成果物へ記録する。
3. `--task-manifest` を受け取る各 consumer は、先行成果物が記録した digest との
   **exact 一致**を要求し、不一致・欠落なら fail-closed で拒否する。
4. 既定 (option 未指定) の経路では、既定 `TASK_MANIFEST` の canonical digest を同じ規則で扱う。
   既定同士の実行は現行と同じ挙動になること。

**連鎖を閉じられない verb があった場合の裁定 (fallback):**
凍結成果物の schema を変えないと digest を運べない verb には、**`--task-manifest` を足さない。**
option を持たない verb はその option を未知引数として拒否する。
受理集合を広げないことを優先し、「足したが守れない」状態を作らない。
実装子は連鎖を実コードから列挙して報告し、閉じられない箇所は**自分で機構を発明せず停止して報告する**。

## 3. R5 — 費用を何と呼ぶか

レンズ A・B が独立に「計算した費用に読み手がいない」と指摘した。事実である
(`resource_ledger` の参照は生成箇所のみ、gate 評価器は存在せず、`decision` は resources を読まない)。

親 brief の成果物影響「resource-overall gate が値を持てる」は**誤りだった。** 訂正する。

裁定:

- 費用の値は生成する。§10 が「費用の正規化計算は未実装」と名指しした穴は、計算機構の不在である。
- **ただし成果物上、これを完全な費用・実請求額・resource gate の値と呼ばない。**
  `cache_write` が常に未計上であるため、被覆は構造的に常に partial である。
- 出力には次を必ず併記する: 通貨、単価の per-million 表記、凍結 price version、
  未計上 category の一覧、被覆状態が partial であること、
  そして**この値が certified field ではないこと**。
- `_certification_scope` は**変更しない** (S4)。したがって費用は explanatory な記述統計として出る。
- gate への接続は S1 として裁定パッケージへ回す。

## 4. プラン v2 (段 5 の実装指示)

段 2 プランを基礎とし、次の差分を当てる。

**実装子 A = (a) task manifest の CLI 入力口 + R3 digest 連鎖**

- A-1. `--task-manifest PATH` を、digest 連鎖を閉じられる verb にだけ足す。
  段 2 プランの 11 verb は**上限**であって下限ではない。閉じられない verb からは外す。
- A-2. loader は R4 を満たす。UTF-8 strict decode、重複 key 拒否、`NaN` / `Infinity` 拒否、
  `type(schema_version) is int` の exact 検査、top-level が object であること。
  **既存 `_validate_task_manifest` の `!=` 比較は `3.0` を受理する**ため、exact 型検査を足す。
  これは §10 が price schema へ課した規則 1 と同じ形であり、新しい発明ではない。
- A-3. `SESSION_IDS` (`:287`) / `ROLLOUT_SHA256` (`:299`) の実行時 consumer
  (`:501,502,545,829`) を外部 manifest 経路から切り離す。`EXPECTED_SCHEDULE` /
  `KNOWN_FINDINGS` には consumer が無いことを両レンズと親が確認済みで、追加対応は不要。
- A-4. `main()` 冒頭 (`:11262-11272`) の alias 解決を、外部 manifest 確定の**後**へ動かす。
- A-5. digest 連鎖 (§2 の 1〜4)。閉じられない箇所は停止して報告する。

**実装子 B = (c) 費用の正規化計算**

- B-1. token の可用性を**三値**にする: `observed` / `unavailable` / `not-incurred`。
  起動前失敗 (`prelaunch_failure is not None`) と replay 失敗は費用を計算しない。
  **exact int の 0 を「観測されたゼロ」と扱ってはならない。**
  費用を計算しなかった試行を、費用の分母 (`attempt_count`) に数えない。
- B-2. price snapshot は**一度だけ読む**。読んだ bytes に固定 SHA-256 を当て、
  **その同じ bytes から作った検証済み tree を返す**。検証後の再読を禁じる。
- B-3. 単価の写像は snapshot の `receipt_token_mapping` から読み、hard-code しない。
  実装する operation は `identity` と `input_tokens-minus-cached_input_tokens` と
  空 field list の 3 つに閉じる。
- B-4. `decimal.Decimal`。8 小数桁、`ROUND_HALF_EVEN`。JSON へ float を出さない。
  軸集計でも float へ戻さない。
- B-5. `reasoning_output_tokens` は output component に加えず、`0 <= reasoning <= output` を要求する。
- B-6. `cache_write` は component を作らず、未計上 category として出力に残す。0 を足さない。
- B-7. `price_version` が null の slot、v2 互換経路、schedule descriptor 無しの経路では
  費用 key を一切出さない。uncertified 性を変えない。
- B-8. **恒偽の拒否条件を実装しない** (A-7)。上流の `validate_price_snapshot` が先に落とす
  3 条件 (未対応 operation / mapping への reasoning 混入 / 非 decimal・非正の単価) は、
  cost 層の独立 gate として登録せず、「上流で担保」と明記する。
- B-9. R5 の併記項目を出力に入れる。

**親が担う**

- docs (事前登録文書は編集しない)、worklog / decisions の spool fragment、
  統合 commit、変異 matrix、受入全走、local main 取り込み。

## 5. 変異事前登録 (DW-M01 / B-057)

実装前に登録する。各変異は「無効化したとき赤の理由が一つに絞れる」ことを実装子が確認する。
確認できない変異は登録せず、実効 gate へ再照準する。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| M01 | cost token 可用性 | `unavailable` を 0 として計上する | KILLED |
| M02 | cost token 可用性 | `prelaunch_failure` の 0 を `observed` として扱う | KILLED |
| M03 | cost 計算 | `Decimal` を `float` へ置換 | KILLED |
| M04 | cost 計算 | `ROUND_HALF_EVEN` を `ROUND_HALF_UP` へ置換 | KILLED |
| M05 | cost 計算 | `reasoning_output_tokens` を output component へ加算 | KILLED |
| M06 | cost 検査 | `cached_input_tokens > input_tokens` の拒否を外す | KILLED |
| M07 | cost 出力 | `cache_write` を金額 0 の component として出す | KILLED |
| M08 | cost 発火条件 | `price_version` が null でも費用を出す | KILLED |
| M09 | cost 発火条件 | `sku_mapping` に無い model を受理する | KILLED |
| M10 | price snapshot 読取 | 検証後にもう一度 path を読み直す (A-2 の再現) | KILLED |
| M11 | manifest loader | UTF-8 strict decode を外す | KILLED |
| M12 | manifest loader | 重複 key の拒否を外す | KILLED |
| M13 | manifest loader | `schema_version` の exact 型検査を外し `3.0` を受理する | KILLED |
| M14 | manifest loader | top-level 配列を受理する | KILLED |
| M15 | digest 連鎖 | consumer 側の exact 一致検査を 1 箇所外す | KILLED |
| M16 | CLI 配線 | `--task-manifest` を無視して既定 `TASK_MANIFEST` を使う | KILLED |

**過剰拒否の正例 (DW-M01 が要求する登録)**

| ID | 入力 | 期待 |
|---|---|---|
| P01 | 現行の凍結 price snapshot + 全 slot `price_version` = 凍結 version | 費用が生成され受理される |
| P02 | 全 slot `price_version` = null の v3 schedule | 費用 key を出さずに受理される (拒否しない) |
| P03 | `--task-manifest` 未指定 (既定 `TASK_MANIFEST`) | 現行と同じ結果で受理される |
| P04 | v2 legacy schedule | 現行と同じ受理・同じ出力 (費用 key 無し) |

**単一理由性の確認義務:** M10 と M15 は、上流に同じ入力を拒否する層が無いことを実装子が
コードで確認する。確認できなければ登録を取り下げ、その旨を報告する。

## 6. 段 5・6 の運用

- 段 5 は **A → B の順次投入**。A の成果を親が worktree へ取り込んでから B を投入する。
- 段 6 は敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
- 実装子は docs を編集せず commit もしない。
