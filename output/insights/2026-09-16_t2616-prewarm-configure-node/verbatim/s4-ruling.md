# 段 4 裁定 — [T-2616] receipt memo prewarm を collection 前へ

親の裁定。段 2 plan と段 3 相談 A (入れ子・発火条件) / B (正しさ防壁・受理集合) の全所見を
real / refuted / 採否 / scope で裁く。

## 0.0 wave 開始後に着地したユーザー裁定 (`DW-S04` の裁定 inbox 再走査)

段 5 dispatch 直前の `--mode midflight` gate が「local main より 2 commit 遅れ」を実測し、
再読したところ **第 19 回 /rulings の 39 項が着地していた** (main の `2313cb40d` / `ac472026c`、
docs のみで実装面 0 件)。そのうち **項 4 が本 wave を名指ししている**。

> **項 4 — 受入短縮の前倒しは赤 0 件で成立する形が示せた場合だけ採る。対象: T-2616。**
> 決定: 受領証の準備を collection 前へ移し待ち合わせを外す変更は、**赤 0 件で成立する形が
> 示せた場合に限り採用する。示せない間は D518 の待ち合わせ契約を維持する。**

**この裁定を本 wave の授権および受理条件の正本とする。** 親の R5 と同内容であり、
加えて次を確定させる — **赤 0 件の形を示せないときは、中間的な形を着地させず
D518 の現行契約 (collection 後の同期 barrier) をそのまま残す。**

関連する同回の裁定も取り込む。

- **項 20 (T-2619)**: 受入の分割数は **3 を維持**する。本 wave は K に触れない。
- **項 30 (T-1933)**: 実測として **112 走中 106 走が 300 秒超**、
  **最遅の担当が 2 番から 112 走中 103 走で 0 番へ変わった**。
  shard-0 は receipt memo の consumer がいる shard であり、28.3 秒の barrier が
  最遅化に直接寄与している。本 wave の対象選定はこの実測と整合する。

## 0. 親自身の誤りの撤回 (先に書く)

- **[撤回] 「`DSession.pytest_sessionstart` は probe plugin より先に走るので FakeMemo が
  間に合わない」**。相談 A が反証し、親が現物で追認した。`xdist/dsession.py:82` に
  `@pytest.hookimpl(trylast=True)` があり、pluggy は trylast を list 先頭へ入れて
  (`pluggy/_hooks.py:464`) `reversed()` で回す (`pluggy/_callers.py:93`) ので **trylast は最後**。
  FakeMemo は `setup_nodes()` の前に入る。この候補は (b) の機序から外す。
- **[撤回] brief (P2)「受入 shard 走なら consumer は必ず居る」**。段 2 が insight README:51-57 で
  反証。shard-1 / shard-2 は consumer 不在だった。
- **[訂正] brief (P3)「`test_memo_barrier_*` は 10 本」→ 現物は 9 本**。親が再検算して追認。
- **[撤回] brief の完了判定「300 秒未満は目標であって受理条件ではない」**。相談 B が
  「同じ brief の『全体 5 分が絶対上限』と矛盾し、301 秒を上限達成として受理する入口になる」と
  指摘した。real として採る。R5 で書き直す。
- **[撤回] 「argv を継がない入れ子では必ず spec=None」**。相談 A が `PYTEST_PLUGINS` /
  `PYTEST_ADDOPTS` 経由の plugin ロードで反証した。正規受入はこの 2 つの env を拒否する
  (`tools/run_tests.py:695-699`) ので今回の列挙は覆らないが、**一般命題としては偽**。

## R1. 発火条件 — parsed option 面で判定する

早期起動は次の連言が真のときだけ行う。

1. controller Config である (`hasattr(config, "workerinput")` が偽)。
2. `_izanagi_acceptance_shard_spec` が実在する。
3. `collectonly` でない。
4. **全 suite 選択である** — `config.args` がちょうど suite root 1 個で、
   **かつ parsed option に narrowing が一切ない**。

**(4) の判定面は `config.args` ではなく parsed option (`config.option`) を正本とする。**
これは相談 A の real 所見 2 件を 1 手で閉じる。理由は、pytest が `PYTEST_ADDOPTS` と ini の
`addopts` を **argv へ足してから parse する** (`_pytest/config/__init__.py:1523-1527`) ため、
`config.args` には現れない narrowing も **parsed option には現れる**からである。

判定に含める narrowing は少なくとも次とする: `keyword` (`-k`)、`markexpr` (`-m`)、
`deselect`、`lf` / `ff` / `last_failed`、`ignore`、`ignore_glob`、`pyargs`。
既存の `_COLLECTION_NARROWING_OPTIONS` は `--ignore` / `--ignore-glob` / `--pyargs` しか持たず、
そのままでは足りない。**この拡張は新しい gate の新設ではなく、既存述語の穴埋めである**
(`DW-O13`: 既存 exact 述語の改訂で受理形を**増やす**場合が新設に当たる。本件は受理形を
**減らす** 方向なので新設ではない)。

**採らない案**: spec 単独。plugin 自体は焦点選択を禁じないので、spec があっても焦点走でありうる。
D518 が却下した「無条件 prewarm」に実質的に近づく。

## R2. nonce 伝播は発火条件の外に置く

`pytest_configure_node` の**冒頭で早期 return してはならない**。現行の receipt / oracle の
session nonce と所要台帳の `workerinput` 伝播を**先に完了させ**、そのあとで R1 を判定する。

段 2 plan と相談 A がともに [real] とした唯一の code-proven な退行がこれである。冒頭 return は
非受入の入れ子 probe への nonce 伝播ごと飛ばし、worker 側の必須読取り
(`conftest.py:2603` / `:2660`) が `UsageError` を送出する。前 wave の (b)「probe の入れ子 xdist
走行で worker が crash」と形が一致するが、**同定ではなく有力候補**として扱う。

## R3. 待ちは既存 flock の上の最小差分にする

**新しい待ち機構を作らない。** `prewarm` の `write_once()` は `_locked(...)` の内側で
`_resolve_now()` を呼ぶ (`real_repo_receipt_memo.py:545-575`) ので、cache の `flock` は解決の
全所要 (実測 28.328 秒) のあいだ保持される。reader の `read_existing()` も同じ blocking
`flock` の中にある。**プロセス跨ぎの待ちは既に実装済みである。**

欠落は 1 点だけ — **reader が writer より先に lock を取ると本体不在で即 `cache-missing`** になる。
早期起動では実際にこの競走が起きる。したがって足すのは次だけとする。

1. controller は R1 成立時、**背景 thread を起動する前に** `.pending` marker を作る
   (lustre I/O を伴わない安い操作)。
2. controller は早期 job の identity を `workerinput` で worker へ明示する。
   **worker は「明示された早期 job がある」ときにだけ待つ。** 継承 env や spec の有無から
   待機を推測しない。
3. worker は lock 内で本体不在を見たとき、**早期 job が明示されている場合に限り** lock を解放して
   期限まで retry する。明示が無ければ**現行どおり即 `cache-missing` で赤**。
4. writer は成功時に `.pending` を消し、失敗時は `.failed` へ置き換える。
   **`.failed` と本体が共存したら `.failed` を優先して赤にする** (相談 B の [unknown] を閉じる)。
5. `.pending` / `.failed` を `_prune_stale_caches` の pattern に足す (親の指摘)。

**絶対に倒してはならない方向** (insight README の明文、規律 2):
「cache が無いので既定値」「worker が自分で resolver を呼ぶ」へ倒さない。
production resolver を呼べる唯一の経路が prewarm であるという性質を壊さない。

## R4. 待ち予算は 120 秒を硬い上限とする

段 2 plan の `B = ceil(2 × max(W))` は**上限が無く、依頼が定めた「最大 120 秒」を超えうる**
(相談 B の real 所見)。**採らない。**

**裁定: 待ち上限は 120 秒固定とする。** 根拠は 2 系統。

1. **実測からの倍率** — prewarm の実測所要は 28.328 秒 (受入 shard-0、走 F、n=1)。
   120 秒はその約 4.24 倍。母集合が n=1 なので裾は未知であり、そのことを定数のコメントに書く。
2. **上限からの逆算** — 既存の `_REAL_REPO_LOCK_TIMEOUT_S = 245.0` は
   「5 分の受入上限 − 観測最長 resource cohort 55.02 秒」で決まっている (`conftest.py:1028-1031`)。
   同じ論法で、120 秒待っても実行窓は伸びない — 早期 job は collection (約 63 秒) と重なるため、
   worker が実際に待つのは「prewarm 所要 − 既に経過した collection 時間」であり、
   120 秒は**到達しないことを期待する上限**である。到達したら赤になる。

観測 max の 2 倍が 120 秒を下回るなら小さい方を採ってよいが、**120 秒を超える値は採らない**。

## R5. 完了判定を書き直す (brief の訂正)

**受理条件は次の 2 つだけである。**

1. 受入全走で**新規赤 0 件**。既存の非帰属赤は `DW-O18` に従って判定する。
2. canonical 受入 (`tools/run_tests.py`) の**最遅 shard wall を実測して worklog に記録**する。

**「全体 5 分が絶対上限」は緩めない。** main の現状は 306.9〜321.3 秒で**既に超過している**。
本 wave はその超過を縮める作業であり、上限を動かす作業ではない。したがって:

- 最遅 shard wall が **300 秒未満**に入ったときだけ [T-2616] を完了として閉じる。
- 入らなければ**実測値とともに持ち越す**。301 秒を「上限達成」と書かない。
- **300 秒に入れるために赤を許容することは絶対にしない** (規律 2)。前 wave が H を撤去した理由。

## R6. 早期起動を実際に pin する検査を必ず入れる

相談 A の real 所見: **既存 probe は「prewarm が collection 前だったこと」を検査していない。**
「早期起動を削って collection 後の同期 barrier へ戻す」変異は既存 probe を素通りする。

**裁定: 新しい検査は、この変異を落とさなければならない。** 検査すべき命題は
「早期 job の prewarm 開始が、worker の collection 完了通知より前である」である。
既存 assertion の複製では足りない。**この 1 本は変異事前登録の必須項目にする** (下記 M-3)。

## R7. 触ってはならないもの

- **既存 test の削除は 0 本。** 期待値の反転・緩和・skip・削除を禁じる。
- `test_run_tests_task_run.py:902` の `result.stderr == ""` を**緩めない**。
  相談 A の real 所見どおり、対処点は marker の抑制ではなく**発火条件**である
  (`IZANAGI_MEMO_PREWARM_V1` 自身も stderr へ出るので、marker だけ抑えても守れない)。
- 二重 guard の逐語 pin (`test_receipt_memo_both_worker_guards_are_required_as_redundant_defense`)
  を維持する。相談 B が [refuted] とした — 待機を guard block の**外**へ置けば両立する。
- 診断 payload の 4 key 完全一致 pin を維持する。`hook="configure_node"` は**値**を増やすだけで
  key を増やさない (相談 B [refuted])。
- production resolver、resolution の内容、closed-schema JSON、opt-out、D573 の nonce 生成は変えない。
- 新規 test file を作らない (自走 harness と所要台帳で赤になる)。既存 file へ足す。

## R8. consumer 不在 shard の追加費用は scope 内・実測で判定する

相談 B の [real]。現行は consumer 不在なら解決しない (`conftest.py:921` / `:979`)。
R1 の条件では**全 shard の controller が早期起動する**ので、consumer 不在 shard にも
解決 1 回分が乗る。

**ただしこれは H の 279.8 秒に既に含まれている。** insight README は H の実装を
「consumer の有無は collection 前に確定できないので**全 controller で起動する**を選ばざるを
得なかった」と明記している。R1 は H より発火範囲を**狭める**方向なので、lustre 競合は H 以下になる。
**受入実測で shard 別 wall を記録し、最遅 shard が入れ替わっていないか確認する。**

## R9. 採るが今回は実装しない所見 (scope 外・記録のみ)

- 相談 B [unknown]「JSON 公開後の writer unlock 失敗」「ready 後の本体消失」
  「非 blocking lock の再試行対象 (`EIO` を競合と混同しない)」— いずれも実装時に閉じる
  **設計上の必須事項**として段 5 の prompt へ入れる。新しい gate の新設ではない。
- 相談 B [unknown]「controller の背景 job 回収が長引けば 5 分を超えうる」— 非 daemon thread の
  回収は既存構造を維持する。**受入実測の wall がこれを含むので、実測で判定する。**
- 相談 A [unknown]「合成 runner 経由の間接呼出しの完全列挙は未完」— 正規受入下の判定は
  覆らないので scope 外。受入全走が実質的な全数検査になる。

## R10. 変異事前登録 (`DW-M01`)

実装前に位置と赤理由を登録する。**期待 node は段 5 完了後に確定し、`DW-M07` に従って
最終 commit で anchor と期待 node を再検証してから本走する。**

| # | 変異位置 | 変異内容 | 期待 | 単一理由性 |
|---|---|---|---|---|
| M-1 | `pytest_configure_node` | 冒頭で R1 不成立なら即 return (nonce 伝播ごと飛ばす) | KILLED | worker の `UsageError` はここでしか出ない |
| M-2 | 早期 reader の待ち | timeout 捕捉を `return self.prewarm(...)` に変える | KILLED | worker が resolver を呼ぶのはこの 1 箇所 |
| M-3 | 早期起動の起動点 | 早期起動を削り collection 後の同期 barrier だけへ戻す | KILLED | **R6 の検査だけが落とす。既存 probe は通る** |
| M-4 | R1 の narrowing 判定 | parsed `keyword` の除外だけを削る | KILLED | 焦点走で解決 0 回を要求する検査だけが落とす |
| M-5 | `.failed` の優先 | `.failed` と本体が共存したとき本体を優先する | KILLED | 失敗情報の迂回はここだけ |
| M-6 | 待ち予算 | 上限 120 秒を無制限にする | KILLED | 5 分上限の証明可能性を壊す |
| M-7 | 未 announce 時の挙動 | 早期 job 未明示でも待つ | KILLED | 現行の即赤を緩める唯一の経路 |

`DW-M04` に従い、置換対象が一箇所でなければ停止する。`DW-M03` に従い、診断文字列だけの赤は
kill に数えない。

## R11. 分割方針

**実装子 1 本。** 編集面が `orchestrator/tests/conftest.py` を中心に一枚岩で、所有を割ると
同一 file の競合になる (`DW-S06-B` の「一枚岩なら理由 1 行」に該当)。
`reasoning` は段 5 / 6 とも docs 権威 (caller 指定不可)。sandbox は `workspace-write`。

段 6 は敵対レビュー 2 本 (`DW-S06-A` 必須) + fix + 変異 matrix + 受入全走。
