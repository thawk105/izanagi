# 段 4 裁定 — [T-2266] 静的 backoff の tail 実測

2026-09-03 21:00 JST。入力は `brief.md`、`s2-plan.md`、`s3-sol.md`、`s3-luna.md`。

## 裁定 1 — 測定する。段 2 の「0 job」推奨を却下する

**luna の命題 1 (real: 親は scope を縮めている) を採用する。** 親の段 1 (P1-e) の傾きは誤りだった。
依頼は「同一ビルド・同一 job 割付けで測る」という測定行為を要求しており、
既存値の再掲はその要求を満たさない。

**加えて sol が独立に、測ることの科学的実体を示した。** 歩行 model の完全再計算は
「有効な 901〜1000 µs の点」と「rep 単位の abort 率」が無いため判定不能である。
歩行 model の格子は 1000 µs まで到達しうるのに、その領域に有効点が 1 つも無い。
**2 レーンが別々の理由で「測ることに実体がある」へ到達した。**

sol の real 所見「谷に届く静的 tail は既存 28 点で外挿なしに閉じる」は採用し、
これは訂正文書側の結論として残す。測らない理由にはしない。

## 裁定 2 — 格子は `none` + `adaptive` + 固定 6 点の計 8 点

luna の「baseline の identity が判定不能」に対する裁定である。
段 2 の「固定 0 を baseline とする」は採らない。`backoff_extended_sweep.py:285-293` が
`none` (`BACK_OFF=0, BACKOFF_FIXED=-1`)、`adaptive` (`BACK_OFF=1, BACKOFF_FIXED=-1`)、
固定点を別の点として扱っており、固定 0 は no-backoff ではないからである。

採用する格子:

| label | flags | 役割 |
| --- | --- | --- |
| `none` | `BACK_OFF=0, BACKOFF_FIXED=-1` | backoff 無しの基準線 |
| `adaptive` | `BACK_OFF=1, BACKOFF_FIXED=-1` | 適応側 (谷) の基準線 |
| `fixed-150us` 〜 `fixed-999us` | `BACK_OFF=1, BACKOFF_FIXED={150,200,300,500,750,999}` | 依頼の静的点 |

**`adaptive` を同じ job に入れる理由:** sol の real 所見が使った適応側の谷 1,241,671 tps は
別 job (`0:966801.nqsv`) 由来であり、静的 tail との比較が job を跨いだ継ぎ合わせになっている。
同一 job へ入れれば、依頼の「同一 job 割付け」が静的点だけでなく比較相手にも及ぶ。
build 1 本の増分で継ぎ合わせが 1 つ消えるので採用する。

固定 0 は入れない。既存格子に 0 があり、本 wave の対象は tail である。

## 裁定 3 — 要求集合と実現集合を分離する。「6 点完了」と書かない

luna の real 所見を採用する。段 2 の `T2266_REQUESTED_US` に 999 を含める命名は不正確である。

- `requested_us = (150, 200, 300, 500, 750, 1000)` — 依頼の座標。
- `realized_us = (150, 200, 300, 500, 750, 999)` — 実際に測る座標。
- `unrealized = {1000: "F718 — 現符号化では商 1・振幅 0 となり固定 0 へ復号される"}`

**999 を「1000 の測定値」と書かない。** 成果物・worklog・insight のいずれにも
「6 点完了」と書かず、「5 点実測 + 1 点は現符号化で測定不能、最近傍の表現可能点 999 を併せて実測」
と書く。この区別は F718 が既に台帳へ残した事実であり、本 wave で緩めない。

## 裁定 4 — 経路は B-10 既存 path の opt-in mode。登録簿は無変更

段 2 の (ii) を採用し、(i)(iii)(iv) を却下する。2 レーンとも同じ結論に達した。

- (iii) 新規 path: `hooks/guard_bash.py:609-623` が未登録実行体を実行時に拒否し、
  `orchestrator/tests/test_hooks.py:2572-3044,3445-3456` が登録簿の path と 4 field を
  literal golden で固定し、`tools/check_docs.py:4404-4438` が `docs/pegasus-runbook.md:484-487` の
  投影表との集合完全一致を要求する。**新規 path の同期は最低 3 file。**
- (i) A-5 流用: job が write-heavy / balanced しか受けず (`a5_second_boot_backoff_sweep.sh:188-206`)、
  driver は `backoff_sweep.py` に固定 (`:589-592`)、契約テストが exact 2 workload を pin する
  (`test_a5_second_boot_job_contract.py:177-187`)。A-5 正式測定の意味を壊す。
- (iv) generic dispatch: 子環境が clean 集合で PBS / reservation 変数を落とすが
  (`dispatch_compute.py:335-345`)、`orchestrator/campaign/loop.py:198-207` が reservation 束縛を必須にする。

**`tools/pegasus/admission_registry.json` は無変更である。** 登録簿は path を key にし
(`tools/pegasus_admission_registry.py:69-77`)、既登録 path の内容変更では更新不要である
(`test_hooks.py:3445-3456` が比較するのは path と 4 field であって script の bytes ではない)。
既存 entry の `class` / `primary_gate` / `evidence` / `reason` を変えない。
**したがって稼働 wave t2189 との編集面重複は発生しない。依頼が求めた着手前報告の条件は成立しない。**

**安全確認 (親の実測):** 停止中の B-10 正式走は `b10_backoff_shape_campaign.sh` /
`submit_b10_backoff_shape.sh` を使う (`docs/b10-multinode-formal-run-design.md:102,161,164`)。
本 wave が編集するのは `b10_backoff_grid.sh` / `submit_b10_backoff_grid.sh` であり別物である。
`qstat` 時点 (21:00 JST) で B-10 grid の job は queue に無い。
grid job body は実行時に committed blob と executing bytes の SHA を照合するので、
既定 branch の挙動を 1 bit も変えない実装にする。

## 裁定 5 — 段 2 プランから削るもの

- **不採用:** `s2-plan.md:83` の実行本体の全面 private-helper 化。
  mode ごとの point / config 選択を最小分岐で注入する形に限定する (luna real)。
- **不採用:** `s2-plan.md:91` の「既存格子と既存 identity 不変」の重複検査追加。
  `test_backoff_extended_sweep.py:152-172,371-396` が既に検査している (luna real)。
- **維持:** `_require_backoff_condition_gate` と既存 pipeline の correctness 経路。
  これは規律 2 の維持であって scope 外の追加 gate ではない (luna refuted を採用)。

## 裁定 6 — 段 2 プランへ足すもの (must-fix)

`DW-G05` に従い、放置したときに成果物の値・受理集合・参照がどう変わるかを 1 行で書く。

1. **run kind を全 receipt へ束縛する** (luna real)。
   放置すると、どの mode で得た成果物か成果物自身から判定できず、
   B-10 拡張格子の成果物と T-2266 の成果物を取り違えて集約しうる。
   束縛先は submit event、reservation、failure receipt、completion。
2. **report の実装先を確定する** (luna real)。
   既存 `backoff_extended_sweep_report.py:83-96` は exact 31 点を要求するので流用不可。
   放置すると job が数値を出さずに完走し、測定が成果物にならない。
   driver 側で最小の `.dat` + JSON を create-only で書く。新しい判定規則は足さない。
3. **rep 単位の throughput と abort 率を保存する** (sol real + luna real)。
   既存 `.dat` は throughput = 5 rep 中央値、abort 率 = 中央値 rep 1 本の代表値である。
   放置すると、歩行 model の再計算が要求する rep 単位 abort が再び得られず、
   sol が「判定不能」とした点が閉じない。**これが本 wave の測定の主目的の一つである。**
4. **完了条件を定義する** (luna real)。期待 genome 数の完走、全点の commit、report 生成を
   completion 前に検査する。放置すると部分完走が「完走」として記録される。
   新しい科学 gate ではなく、依頼した測定が完走したことの確認である。

## 裁定 7 — 文書訂正は測定の有無に関わらず行う

`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` §5 の
「b > 100 µs の静的 `T(b)` は 1 点も測っていない」は実測が否定する。追記で訂正する。
併せて `output/insights/2026-09-03_t2266-backoff-static-tail/` に次を置く。

- 既存 28 点の逐語表 (3 workload) と出所 SHA。
- `.dat` の集約規則 (throughput = 5 rep 中央値、abort = 代表 1 rep、cv = throughput の標本 CV)。
- F718 による b = 1000 の測定不能と、符号化の 4 分岐の逐語。
- 旧 model の指数外挿と実測の乖離 (500 µs で 3.04 倍、900 µs で 13.21 倍の過小評価)、
  および滞在重み固定の単純混合での寄与上限 (+0.037 M tps)。
- 新規測定の結果 (得られ次第)。

**すべて非認証である。** trace-disabled の性能測定であり直列性の検査を通していない。
variant 採用の根拠には使えない (規律 2)。

## 変異事前登録 (DW-M01)

実装前に登録する。実装面があるので変異 matrix は免除されない。
各変異は実装後に単一理由性 (同じ入力を拒否する層が前後にも内側にも無いこと) を確認する。

| # | 変異 | 期待する赤 |
| --- | --- | --- |
| 1 | `realized_us` から 750 を落とす | T-2266 格子の点数・literal 検査 |
| 2 | `realized_us` の 999 を 1000 へ変える | 要求集合と実現集合の分離検査 |
| 3 | `B10_RUN_KIND` の既定を `t2266-tail` にする | 既存 extended branch の routing 検査 |
| 4 | completion receipt へ run kind を書かない | receipt 束縛検査 |
| 5 | rep 単位 abort を捨て代表 1 rep だけ残す | 成果物 schema 検査 |
| 6 | `EXTENDED_SWEEP_US` を T-2266 格子で上書きする | 既存 identity 検査 (既存 gate の生存確認) |
| 7 | `_require_backoff_condition_gate` の呼び出しを外す | 既存 condition gate |

## 段 5 の分割

実装子 1 本 (Codex `role=author`、workspace-write)。所有面は次のとおり。

- `orchestrator/campaign/backoff_extended_sweep.py`
- T-2266 report の実装先 (driver 内 or 新規 module。実装子が file:function で確定する)
- `tools/pegasus/b10_backoff_grid.sh`
- `tools/pegasus/submit_b10_backoff_grid.sh`
- `orchestrator/tests/test_backoff_extended_sweep.py` および必要な新規テスト

**分割しない理由:** run kind の束縛が driver・job body・submitter・receipt を跨ぐ
producer / consumer 契約であり、並行 fix は契約を壊す。1 子に持たせる。
