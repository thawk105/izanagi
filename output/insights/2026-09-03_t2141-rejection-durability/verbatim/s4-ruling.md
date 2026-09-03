# [T-2141] 段 4 裁定とプラン v2

親が段 2 プランと段 3 の 2 レンズを real/refuted に裁定し、実装する形を確定する。
段 5 実装子はこの文書を契約として実装する。

## 0. wave 開始後に入った裁定 (段 4 直前の再走査で取り込み)

local main が `4ec3eba04` → `b20543ba4` へ進み、決定が 29 件増えた。本 wave の設計を直接決めるのは 2 件。

- **D1533 (ユーザー裁定, 2026-09-03):** 成果物の不変性は「同じ path が残っている間の再作成」を
  防ぐところまでとする。削除・改名・別 path での選別再走は防がない。**防いでいない範囲を成果物へ
  明記する。** 改竄が正式な受理まで届く実経路が示されていない段階では、bytes 級 provenance は
  見送り側に入る。
- **D1529 (ユーザー裁定, 2026-09-03):** 欠測 attempt を含む母集団から出た数値主張には但し書きを
  付ける。**但し書きの単位は「文書」でなく「数値主張とその母集団」とする。**

この 2 件は、段 3 の両レンズが独立に指摘した「chain head を pin しないので完全性を主張できない」を
**機構の追加ではなく範囲の明記で閉じよ**と裁定している。以下の裁定 R2 と R4 はこれに従う。

## 1. real / refuted

### real — 採用して直す

| # | 出所 | 所見 | 成果物影響 |
|---|---|---|---|
| R1 | sol 3 / luna 1 | deferred を記録しないまま「absent + matching rejection = 説明済み」と判定すると、棄却の後に deferred が起きた候補で非保証を誤って落とす | 材料レポートが偽の完全性を主張する |
| R2 | sol 4 / luna 5 | chain head が pin されないので末尾の完全切断と file 削除を検出できない。件数と棄却率が過少化する | レポートの参照値が実際より小さくなる |
| R3 | sol 2 / luna 2 | 未終端 tail の直後に `O_APPEND` すると次行が連結し、以後 loader が恒久的に拒否する | 記録の失敗が consumer の利用可否へ漏れる |
| R4 | luna 3 / sol 5 | batch の collection 型不正と publication 検証自体の失敗は、検証済み root が無いので記録できない | 「全 rejection を耐久化」は達成不能。保証範囲を狭めて明記する要 |
| R5 | luna 4 / sol 5 | planned mapping は全 scheduled、manifest は先頭 201 eligible。母数が 2 つある | manifest 非選択の候補が永久に「理由不明」になる |
| R6 | sol「受理集合が動く可能性」 | ledger の検証失敗を assembly の失敗へ昇格すると、正常な success leaf まで利用不能になる | 記録の失敗が成果物の利用可否へ漏れる。規律に反する |
| R7 | sol 1 | plan の open flag に `O_WRONLY`/`O_RDWR` と作成 mode が無く、逐語実装では書けない | 台帳が残らない |
| R8 | luna「受入時間」 | 201 件の棄却 fixture を証拠生成経路で作ると過去の 451 秒を再現する | 受入全走 5 分上限を壊す |

### real だが scope 外 — 実装せず記録する

| # | 所見 | 裁定 |
|---|---|---|
| R9 | ledger の完全性を外部 head で保証する仕組み | **D1533 により見送り側。** 実経路が示されていない。範囲の明記で閉じる |
| R10 | 親 brief の DW-O10「producer の書き出し面は 1 種類」は誤り | **訂正する (下記 §5)。** 実装への影響は無いが、記録として残す |

### refuted — 採用しない

- **「registry violation 行へ足せばよい」** — `p3_b4_analysis_contract.py:59-67` の reason 語彙は 5 値に
  閉じており producer の 12 issue code を保持できない。`append_registry_violation` は file writer で
  なく in-memory の新しい registry 値を返すだけである。さらに更新後 registry は issuer receipt の
  descriptor 検査 (`p3_b4_prerun_issuer.py:1056-1061`) に拒否される。
- **「成功 attempt leaf を union にすれば新 file は不要」** — `PLANNED_PATH_CONFLICT` と leaf 自身の
  IO error という**最も重要な棄却理由ほど記録できない**。
- **「campaign WAL は既に durable」** — 書き先が campaign root 配下で publication root から常に
  導出できない。request 検証前の棄却では campaign root 自体が未確定である。
- **「deferred も ledger へ記録すべき」(luna が plan の否定理由を誤りとした件)** — luna の指摘
  「別 leaf への状態 event は planned success leaf の no-publish 契約と両立する」は**技術的には正しい**。
  しかし deferred は再試行で解消する一時状態であり、記録しても「現在 absent の理由」を決定できない
  (記録後にさらに状態が変わる)。**R1 は deferred を記録することではなく、非保証の落とし方を
  狭めることで閉じる。**追加の器を作らない方が最小である。

## 2. プラン v2 — 実装する形

### R-A: 記録先は publication root 直下の固定名 leaf 1 種だけ

`raw-record-rejections.jsonl`。issuer は発行時に作らない (発行直後の root が固定 3 artifact である
既存期待を変えない)。最初の棄却時に producer が作る。

### R-B: event の中身 — hash chain を入れない

1 event = canonical JSON 1 オブジェクト + 改行。持つのは次だけとする。

- `schema_version`
- `issuer_commitment_sha256` — どの publication の棄却かの束縛
- `attempt_id` (string または null)
- `issues` — 既存 `B4RawRecordIssue` の `artifact` / `field` / `code` / `detail` を全項目

**`previous_event_sha256` / `event_sha256` / `event_index` を入れない。chain 再生成検査も作らない。**
理由は D1533。chain head を pin しない chain は末尾の完全切断と file 削除を検出できず、
守れない範囲を守れるかのように見せる。**代わりに R-E で範囲を明記する。**

### R-C: 書き込み手順 (R3 / R7 を閉じる)

1. `_ensure_real_parent` で publication root まで実 directory を確認する。
2. root directory fd を `O_RDONLY|O_DIRECTORY|O_NOFOLLOW` で開く。
3. ledger を `O_RDWR|O_APPEND|O_CREAT|O_NOFOLLOW`、mode `0o600` で開く。
4. `flock(LOCK_EX)` を取る。
5. **file が改行で終わっていなければ、最後の改行までを `ftruncate` する。**
   捨てた fragment の有無を loader が読める形にするため、この事実は戻り値で親関数へ返す。
   fragment を捨てずに追記してはならない (R3)。
6. 完成した 1 行を単一の `write` で追記する。
7. file を `fsync` し、新規作成時は root directory も `fsync` する。

`_publish_exact` は 1 行も変更しない。成功 leaf の no-replacement、同一 bytes の idempotence、
symlink 拒否をそのまま残す。

### R-D: 呼び出し位置と保証範囲 (R4 を閉じる)

**耐久化するのは「publication の検証に成功した後に producer が返す rejection」だけとする。**

- `publish_b4_attempt_result` — `_validated_publication` 成功後に発生した `_Reject` と
  予期しない例外から作る rejection を、return の直前に追記する。
- `publish_b4_attempt_results` — validated publication を得た後の各 rejection を追記する。
  batch 前走査で publication 検証前に返る rejection (`:1781-1804` の collection 型不正) は
  **追記しない。呼び出し順序も変えない。**
- `B4RawRecordDeferred` は追記しない (`:1665-1672`, `:1748-1749`, `:1849-1851` は writer を通さない)。
- 追記に失敗したら、元の rejection へ `IO_ERROR` issue を 1 件足して **rejection のまま返す。**
  成功公開へ倒れる枝を作ってはならない。

`B4_RAW_RECORD_NON_GUARANTEES` (producer 側) は**変更しない**。公開 artifact の bytes を変えず、
既存テストの期待値も変えないためである。保証範囲の明記は R-E の材料レポート側で行う。

### R-E: consumer 側 — 非保証を「落とす」のではなく「2 つに割って狭める」(R1 / R2 / R5 を閉じる)

`assemble_b4_raw_analysis` は ledger を snapshot して結果へ付ける。
**ledger の読み取り失敗を assembly の失敗へ昇格しない (R6)。** ledger の状態は独立した値として運ぶ。

材料レポートは次を出す。

- `producer_rejections.events` — 記録された棄却 event の全項目。
- 母数を 3 つ別々に出す (R5)。`scheduled_attempt_count`、`planned_result_artifact_count`、
  manifest が選んだ block 数。manifest 非選択の scheduled attempt は `not_selected` として説明する。
- `unresolved_absent_attempts` — absent かつ event で説明できない候補。理由不明と明示する。
- `rejection_history_status` — ledger が読めたか、fragment を捨てたか。

非保証の扱いは次のとおり。

- **落としてよい:** 「記録された棄却は publication root から復元できない」。記録された分は復元できる。
- **残す (文言を狭める):** 「absent な planned leaf の**現在の**理由は決定できない」。
  未試行・deferred・記録前の棄却・記録失敗を区別できないためである。これが R1 の閉じ方である。
- **新たに明記する (D1533):** ledger の削除と末尾の完全切断は検出しない。
- **数値主張に但し書きを付ける (D1529):** 棄却件数と棄却率は「記録された event の母集団」から出た
  値であり、上の未検出範囲を含む。但し書きは文書単位でなく**この数値主張に**付ける。

### R-F: テストの作り方 (R8 を閉じる)

- 棄却 fixture は **証拠導出より手前で落ちる入力**で作る (unknown field、ill-typed request 等)。
  実証拠を伴う棄却は既存の 1 件 (`test_p3_b4_raw_record_producer.py:1101-1115` 相当) だけを使う。
- 201 件規模の fixture を新設しない。`_evidence_scope` を繰り返し呼ぶ構造を作らない。
- 既存 fixture を複製して使い、各 case で 201-block の証拠を再生成しない。

## 3. 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由であることを probe 走で確認してから本登録する
(DW-M08 の probe → 本登録 → 再走)。probe は全件 SURVIVED 期待で登録して観測 node を集める。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| N01 | producer の単発 rejection return 直前 | ledger 追記の呼び出しを削除する | KILLED |
| N02 | ledger writer の tail 修復 | 改行までの `ftruncate` を削除して素の追記にする | KILLED |
| N03 | ledger 追記失敗時 | `IO_ERROR` を足さず元の rejection をそのまま返す | KILLED |
| N04 | deferred 返却路 | deferred でも ledger writer を呼ぶ | KILLED |
| N05 | issuer の固定 artifact 名リスト | 新しい固定名を除く | KILLED |
| N06 | 材料レポートの unresolved 判定 | 「absent かつ event 無し」を「absent すべて」へ緩める | KILLED |
| N07 | 材料レポートの非保証 | 未解決が残っていても非保証を落とす | KILLED |
| N08 | ledger 読み取り失敗の扱い | assembly の失敗へ昇格させる | KILLED |

**受理集合を縮小する側の正例も登録する (DW-M01):** N05 と N08 は拒否を増やす向きなので、
「正常な入力が通り続ける」正例を対にして登録する。

`flock` は単一 process のテストでは殺せない。**並行追記は検査していないと明記し、
kill には数えず diagnostic として別枠に置く (DW-M08)。**

## 4. gate の署名と通る正例 (DW-S04)

新設する拒否は 1 つだけである。

- **署名:** issuer の発行時と reload 時に、planned result artifact path が
  `<publication-root>/raw-record-rejections.jsonl` と完全一致するか、その配下にあるか、
  publication root 自身であるとき `PLANNED_RESULT_PATH_INVALID` で拒否する。
- **通る正例:** publication root 配下の別名 leaf
  (例: `<publication-root>/results/attempt-0001.json`) を planned path とする publication は、
  従来どおり発行も reload も成功する。

## 5. 親 brief の訂正 (追記でのみ訂正する)

- **DW-O10 の「producer が書くファイル種は 1 種類だけ」は誤り。** 恒久的に残る種類は 1 種
  (issuer が計画した attempt result leaf) だが、検証の過程で `p3_b4_raw_record_producer.py:867-870`
  が receipt bundle の snapshot 群を一時 directory へ書き、`_publish_exact` も staging file を作る。
  本 wave で恒久的な種類が 1 つ増える、という結論自体は変わらない。
- **「0o700 real-parent 検査」は不正確。** `_ensure_real_parent` は新規 `mkdir` の mode が 0o700
  であって、既存 directory の mode を検査しない。検査するのは symlink でない実 directory であること。
- brief の anchor 2 件を訂正する。batch の戻り口は `:1836-1885` でなく `:1836-1891`。
  publication reload の実復元は `:1007-1046` でなく `:1081-1119`。
- **DW-O09 の「pin 0 件」は両レンズが独立に支持した。** `test_frozen_artifacts.py` の 23 path に
  producer は無く、producer 自身の projection closure にも自分は含まれない。

## 6. 分割方針

実装面は Codex `role=author` **1 本**に持たせる。producer の writer、consumer の復元、issuer の
固定名、材料レポートの非保証の狭め方が 1 つの契約を跨ぐため、並行 fix で契約を割らない。
親は brief・裁定・commit・変異・受入・記録・land を担い、実装面を直接編集しない。
