# [T-2141] raw 試行記録 producer の rejection 耐久化 — 一次資料

wave `dev-wave-t2141-rejection-durability`、branch `worktree-dev-wave-t2141-rejection-durability`。
base commit `4ec3eba04`。2026-09-03。

`verbatim/` に段 1〜6 の全成果物 (brief、その訂正追記、plan、敵対相談 2 本、裁定、実装子報告、
敵対レビュー 2 本、fix 2 巡の報告) を逐語で置く。

## 何を閉じたか

`orchestrator/campaign/p3_b4_material_report.py` が自ら宣言していた非保証

```
past_producer_rejections_are_not_fully_reconstructible_from_publication_root
```

を、機構を足して**部分的に**閉じた。閉じた範囲と閉じていない範囲を成果物へ明記した。

`publish_b4_attempt_result` / `publish_b4_attempt_results` は棄却時に
`B4RawRecordRejection` を**戻り値としてだけ**返していた。成功時だけ `_publish_exact` が
issuer の計画した path へ書くので、publication root だけを入力とする consumer は
「どの候補がなぜ棄却されたか」を後から復元できなかった。

## 成果物

- `orchestrator/campaign/p3_b4_raw_record_producer.py` (rejection 台帳の writer と loader)
- `orchestrator/campaign/p3_b4_prerun_issuer.py` (固定名の予約と衝突拒否、3 行)
- `orchestrator/campaign/p3_b4_material_report.py` (復元経路、母数 3 種、但し書き)
- 上記 3 つの test file

## 相乗り可否を先に測った (段 2)

ユーザー指示は「既存の記録経路に相乗りできるかをまず測り、足りない分だけ足す」だった。
段 2 の read-only codex が 5 経路を file:line で測り、**全経路が不可**と判定した。

| 経路 | 判定 | 根拠 |
|---|---|---|
| issuer publication の固定 3 artifact | 不可 | receipt が bytes を pin する。後追記で publication が失効する (`p3_b4_prerun_issuer.py:1056-1067`) |
| `p3_b4_admission_record.py` | 不可 | 事前 admission の read-only verifier。writer も path も schema も持たない |
| `p3_b4_analysis_ledgers.py` の violation 事象 | 不可 | reason 語彙が 5 値に閉じ producer の 12 issue code を保持できない。`append_registry_violation` は file へ書かず in-memory 値を返すだけ |
| campaign WAL | 不可 | 書き先が campaign root 配下で publication root から常に導出できない。request 検証前の棄却では campaign root 自体が未確定 |
| 成功 attempt leaf への union | 不可 | `PLANNED_PATH_CONFLICT` と leaf 自身の IO error という**最も重要な棄却理由ほど記録できない** |

足したのは publication root 直下の固定名 leaf `raw-record-rejections.jsonl` **1 種だけ**。
実験母数と attempt mapping は既存の issuer receipt を再利用した。

## hash chain を入れなかった (D1533)

段 2 プランは event に `previous_event_sha256` / `event_sha256` / chain 再生成検査を置いていた。
段 3 の両レンズが独立に「chain head を pin しないので末尾の完全切断と file 削除を検出できない」と
指摘した。

段 4 直前の裁定再走査で、wave 開始後に入った **D1533 (ユーザー裁定)** を取り込んだ。同裁定は
「成果物の不変性は同じ path が残っている間の再作成防止までとし、**防いでいない範囲を成果物へ
明記する**」「改竄が正式な受理まで届く実経路が示されていない段階では bytes 級 provenance は
見送り側」と定めている。**したがって chain は不採用とし、範囲の明記で閉じた。**

**D1529 (同じくユーザー裁定)** に従い、件数と率の数値主張には母集団の但し書きを、文書単位でなく
**その主張に**付けた。

## 非保証は「落とす」のではなく 2 つに割って狭めた

段 3 の両レンズが最重所見として挙げたのは次の反例である。

1. valid な attempt を棄却して durable rejection を作る
2. 同じ候補を campaign lock 保持中に再試行し deferred を返す
3. planned leaf は absent のままだが matching rejection は存在する

この状態で「absent + matching rejection = 説明済み」と判定すると、非保証を**誤って**落とす。
そこで非保証を割った。

- **落とした:** 記録された棄却は publication root から復元できない、という主張。
- **残した (文言を狭めた):** absent な planned leaf の**現在の**理由は決定できない。
  未試行・deferred・記録前の棄却・記録失敗を区別できないためである。
- **新たに明記した:** 台帳の削除と末尾の完全切断は検出しない (D1533)。

## 保証範囲を正直に狭めた

「全 rejection の耐久化」は**達成不能**だった。publication の検証そのものが失敗したときは、
書き込む信頼できる root が確定しない。保証を
**「publication の検証に成功した後に producer が返す rejection」**へ明示的に狭めた。

batch の collection 型不正 (`publish_b4_attempt_results` の入口) は検証前に返るため記録対象外で、
返却順序も変えていない。

## 段 6 の敵対レビューが見つけたもの

レンズ D の反実仮想が、**実装のいくつかは抜いても全テストが緑**であることを暴いた。
`flock`、台帳の `O_NOFOLLOW`、`fsync`、batch の記録行 2 本、event の schema 値、
Markdown の一部表示がそれである。

さらに重い所見が 2 件あった。どちらも D1533 の「防いでいない範囲を明記する」の実装漏れである。

- **切り捨てた事実が consumer へ届かない。** 未終端 tail の切り捨ては正しく行われるが、
  その事実は追記成功時の戻り値にしか残らず、後から台帳を読む loader は
  `fragment_discarded=False` を返していた。fix で、切り捨て時は `attempt_id=null` の
  修復 event を既存 schema で台帳へ残すようにした。
- **`fsync` 失敗の event が耐久済みと同じ顔で数えられる。** 戻り値には `IO_ERROR` が付くが、
  可視になった event を後続の loader が通常 event として数えていた。fix で、同じ lock 内で
  追記開始 offset へ切り戻すようにした。これで「数えられた event は fsync が成功している」が真になる。

**機構の正例が実体を名指していなかった。** 「台帳が invalid でも正常な assembly は成功し続ける」
という保証の正例が、**両側とも `INCOMPLETE_SET` で落ちる入力**を使っており、一度も機構を
通っていなかった。fix で既存の certified 201-block 正例を再利用して作り直した。
本走で N08 がこの node を落としたことが、機構を通った証拠である。

## 実測 (親が実走した値)

| 走 | 内容 | 結果 |
|---|---|---|
| baseline | 実装前の producer test | 29 passed / 30.84s |
| 焦点走 run1 | 段 5 実装子の成果物 | 4 failed / 162 passed / 1 skipped、105.78s |
| 焦点走 run2 | fix1 適用後 | 1 failed / 171 passed / 1 skipped、105.64s |
| 焦点走 run3 | fix2 適用後 | **172 passed / 1 skipped、107.51s** |

焦点走の対象 4 file は参照関係で引いた
(`test_p3_b4_raw_record_producer` / `test_p3_b4_prerun_issuer` / `test_p3_b4_material_report` /
`test_real_repo_serialization`)。

## 変異 matrix — 10/10 KILLED、生存 0

`mutation-spec.json` と `mutation-ledger.json` が本登録の spec と結果、
`mutation-probe-spec.json` と `mutation-probe-ledger.json` が probe 巡である。
anchor は 10 件とも対象 file 内で厳密に 1 回だけ出現し `old != new` であることを、
親が投入前に機械検査した (bad=0)。

| 変異 | 壊した箇所 | 落ちた node 数 |
|---|---|---|
| N01 | 単発 publish の耐久記録呼び出し | 6 |
| N02 | 未終端 tail の切り捨て | 1 |
| N03 | 追記失敗時の `IO_ERROR` 付与 | 3 |
| N04 | deferred を台帳へ書かせる | 1 |
| N05 | issuer の固定名予約 | 4 |
| N06 | unresolved の判定条件 | 1 |
| N07 | 現在理由の非保証の保持 | 1 |
| N08 | 台帳失敗を assembly 失敗へ昇格 | 3 |
| N09 | 切り捨ての修復 event | 1 |
| N10 | `fsync` 失敗時の切り戻し | 1 |

**N01〜N09 は probe の観測 node をそのまま本登録した。N10 だけは probe を取れなかったため
親の予測 node で登録し、本走で一致した。** 外れた場合は DW-M08 の erratum + 再登録の経路を
使う予定だった。予測を後から書き換えて辻褄を合わせてはいない。

### 帰属が一意でない組

- **N02 と N09 は同じ 1 node に落ちる。** 別の欠陥だが、同じテストが両方を検出する。
  node 集合では区別できない。追加テストは作らず、限界として記録する。

### 検査していない面

- **`flock` による並行追記は検査していない。** 単一 process のテストでは殺せないため、
  kill に数えず diagnostic として別枠に置いた。

## 計算資源の観測 (この wave の外にも効く事実)

- **変異 harness は login node での `--runner-mode local` を禁止している**
  (`--runner-mode local は PEGASUS_LOGIN で実行できない`)。混雑時でも dispatch しか選べない。
- **queue 待ちの実測:** request 970788 は 12:43:48 投入で `Planned Start Time = 13:49:29`。
  約 66 分待ち。別の走では 04:13 投入の job が 08:53 開始 (約 4 時間半)。
- **D612 の queue-wait 上書きは、単独で `run_tests.py` を叩けば効く。**
  正例対照: `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=60` で
  13:03:45 → 13:04:48 (63 秒) に `queue-wait-timeout` rc=16。
  **しかし mutation harness 経由の走行は 3600 秒設定でも 904 秒で切れた。**
  harness は `IZANAGI_DISPATCH_*` を設定も除去もしておらず、collection の timeout は
  `spec.timeout_seconds` を使う。**食い違いの原因は特定していない。**
  5400 秒設定の本走は完走したので、実用上は上書きを大きく取れば通る。

## 走行の中断と復元

変異 probe の 2 回目は session の終了に巻き込まれて harness が途中で死に、
**作業ツリーに N10 の変異が残った。** 待ち手の通知ではなく `git status` と `pgrep` で
生死を判定したため検出でき、`git checkout --` で復元した (DW-O19)。

orphan hold を 2 回外した。いずれも qstat で対象の不在または終端を確認し、dirty なしを確認し、
clean / HEAD を確認してから hold と sidecar を手動削除した。`git ls-files` で tracked 0 件も確認した。

## 閉じられなかったこと

- **台帳の削除と末尾の完全切断は検出しない。** 検出するには成果物とは別の権威へ attempt を
  予約する仕組みが要る。D1533 により見送り側に入れ、範囲を成果物へ明記した。
- **absent な planned leaf の現在の理由は決定できない。** 未試行・deferred・記録前の棄却・
  記録失敗を区別できない。
- **publication 検証そのものの失敗は記録できない。** 信頼できる root が確定しないため。
- **並行追記は検査していない。**
