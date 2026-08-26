# 裁定パッケージ — [T-1629] 署名批准 broker の wave

本 wave は実装・レビュー・変異・記録まで完了し、**受入全走で残った赤 1 件だけが land を塞いでいる。**
その赤は本 wave 由来ではなく、**現時点で受入を通す全 wave を塞ぐ repo 全体の条件**である。

## R-a. 受入 gate が main 単独で割れている (これが本体)

### 事実 (2 セッション独立で再現)

計測した main = **`b9d21206382c6a80d59e5a6bb2fe9e4521869455`**
(peer の指摘どおり coverage は動く値なので SHA を固定する)

| 観測者 | wave の性質 | 分母 (collected) | 結果 |
|---|---|---:|---|
| 本 wave | テスト node を **126 足す** | 17826 | `1 failed, 17764 passed, 61 skipped` |
| 本 wave (main worktree で単独実測) | wave 無し | 17700 | `15912/17700 = 89.898305%` で赤 |
| peer (`runner-tip-equality` wave) | テスト node を **1 つも足さない** | 17700 | `1 failed, 17638 passed, 61 skipped` |

赤はどの観測でも**同一の 1 node** だけである。

```
orchestrator/tests/test_acceptance_schedule_order.py::
  test_g5_real_ledger_covers_at_least_90_percent_of_real_collection

AssertionError: acceptance duration ledger coverage too low: 89.898305%
```

**node を 0 個足す wave でも踏む。** したがって「node を足した wave が悪い」ではなく、
**閾値 90% を main 自身が割っている。**

### 本 wave の寄与と限界

本 wave は 126 node を足すので 89.263% まで下げる。
しかし**自分の 126 node に所要をすべて与えても `16038/17826 = 89.97%`** で、
0.03 ポイント届かない。**超過分は main 側にあり、本 wave では閉じられない。**

### 直せなかった理由 (すべて実測で確定)

**本 wave は「台帳を再生成すれば直るのではないか」を実際に測った。答えは「直せない」だった。**

診断走 (受入形ではない別走) で全走 JUnit XML を採り、
`tools/update_acceptance_duration_ledger.py` で台帳を一時領域へ再生成して pin を照合した。

- **この tool は join ではなく全面置換である。** `main()` は
  `_ledger_bytes(args.JUNIT, repo)` の結果をそのまま書き出し、既存台帳を読む経路が無い。
  したがって「不足分だけ追記する」ことが tool ではできない。
- 再生成すると台帳は **15944 node から 17825 node** になる。
  現行台帳が 15944 しか持たないのは過去の再生成時点の collection を写しているためで、
  再生成は全 suite の node 集合を一斉に更新する。
- その結果 `test_t1574_changed_suite_ledger_node_delta_is_exact` の pin が壊れる。

  | pin | 内容 | 結果 |
  |---|---|---|
  | 所要値 exact (12 node) | `5.89` 等 | **12/12 不一致** (5.89→8.2、5.88→8.3、0.12→0.17 等) |
  | suite の node 集合 identity (8 接頭辞) | 件数 + sorted node の sha256 | **6/8 不一致** (例: `test_critic` 121→138) |
  | removed node の不在 (5 node) | | **1 件が復活** |

  **所要値は機体負荷で動くので量子化では吸収されない。**

- **閾値を下げるのは関門の弱体化**なので採らない (絶対規律 2)。
- 受入の argv は exact pin されており `--junit-xml` を足せない (D713)。
  台帳更新に要る JUnit XML は受入走からは得られず、別走が要る (本 wave はその別走を実施した)。
- 対応する F が `docs/failures.md` に無く、`orchestrator/tests/flaky_test_holds.py` にも登録が無い。
  **DW-O18 は「F 不在なら登録せず裁定へ送り停止」**と定めている。本 wave はこれに従って停止した。

### 択一

1. **(α) 台帳を全面再生成し、T-1574 の pin 18 件を同じ変更で更新する。**
   - 利点: 全 wave が即座に解ける。coverage は約 100% になる。値はすべて実測。
   - 代償: **別 wave が固定した pin を 18 件書き換える** (所要値 12・node 集合 6)。
     T-1574 の pin は「その wave の node delta が exact である」という主張を守るもので、
     書き換えると**その主張の証拠が現在の collection で上書きされる**。
   - 要る作業: 台帳生成 (本 wave が JUnit まで実施済み) + pin 更新 (Codex `role=author`)。
2. **(β) 不足分だけを追記し、pin は触らない。**
   - 利点: 他 wave の pin を 1 つも壊さない。8 接頭辞の外の node だけを足せば pin は不変である。
     不足は本 wave の分母で **6 件**、main の分母で **18 件**しかない。
   - 代償: **現行 tool では実行できない。** 全面置換しかできないため、
     台帳を手で編集するか、tool へ join mode を足す必要がある。どちらも別 wave の作業になる。
3. **(γ) F を起票し、この gate を `flaky_test_holds.py` へ hold 登録する。**
   - 利点: 全 wave が即座に解ける。関門の実装は残る。
   - 代償: **90% を割ったまま「割っていてよい」と宣言することになる。**
     gate の意味が失われる方向であり、規律 2 の面で慎重な判断が要る。
   - **さらに、これは一度きりの回避にならない (下記 §構造的帰結)。**
4. **(δ) 所要値 pin を exact 値から値の性質を見る述語へ置き換える** (有限・非負・上限、
   あるいは相対誤差)。そのうえで (α) を行う。
   - 利点: **生成器が再び使えるようになる。** (α) の代償が node 集合 pin 6 件だけに縮み、
     その 6 件は「集合が増えた」という正常な前進なので更新の正当性を書きやすい。
   - 代償: 別 wave が固定した pin の**性質**を変える。exact 値で守っていた
     「count-preserving swap も検出する」という検出力のうち、値側の分は失う
     (node 集合 identity は残るので、集合の入替えは引き続き検出できる)。

### 構造的帰結 (これが選択の分かれ目)

**所要値は機体負荷で動く。したがって exact 値 pin が在る限り、生成器は今回だけでなく
永久に使えない。** 本 wave の実測 (5.89→8.2、5.88→8.3、0.11→0.079) は 1 回の観測ではなく、
この pin の構造的な帰結である。量子化は「小さい jitter」を吸収する設計だが、
観測された差は 39% に達し吸収範囲の外である。

この帰結は (γ) の読み方を変える。**被覆率は node を足す wave が land するたび下がり、
唯一の是正手段 (再生成) が構造的に封じられているので、hold は恒久的に更新し続けることになる。**
「(γ) は安い」という読みは成立しない。

**親の推奨: (δ) → (α)。** 生成器を使える状態へ戻すことが、この gate を将来にわたって
機能させる唯一の道である。次点は (β) を可能にする最小の tool 改修 (不足は 6〜18 件しかない)。
ただし**別 wave が固定した pin の性質を変えるか、tool の契約を変えるかの判断はユーザーの領分**
なので、ここで止めている。

(δ) は peer session (`runner-tip-equality` wave) が指摘した形である。
構造的帰結の主張は本 wave が実測 (12/12 不一致) で裏付けた。

## R-b. 本 wave が閉じた範囲 (参考。裁定は不要)

- D905 の執行機構を署名 receipt として実装し、閉包を 27 path へ広げ、gate を v1 から v2 へ切り替えた。
- 回収した 3 worktree の内容を独立監査し、real 37 件・refuted 0 件を裁定した。
- 変異 18 件は **baseline PASSED / 18 KILLED / SURVIVED 0 / MISMATCH 0**、期待 node 56 件が全件一致。
- 受入は**赤 1 件 (上記) を除いて 17,764 件通過 / 61 skip**。

## R-c. 本 wave が返す設計上の裁定事項 (別途)

段 4 と段 6 で scope 外と裁定した項目。詳細は
`output/insights/2026-08-27_t1629-ratification-broker/verbatim/s4-ruling.md` と `s6-adjudication.md`。

1. **判定器が判定対象の内側にある** — 外側の固定実行器が無く、repo を編集できる主体は
   鍵を持たなくても gate を消せる。D906 の「実行器と検査器の bytes を署名対象に含める」の実装方法。
2. **既存 lock の resume と certified artifact consumer が署名 gate を素通りする** —
   閉じるには campaign lock の authority へ signed receipt identity を記録する schema 変更が要り、
   D956 の領域に当たる。本 wave では素通りを固定する負例テストだけを入れた。
3. **鍵の紛失・交代・信頼根 rotation を schema が表現できない。**
4. **批准から official 起動までの非介在条件**を機構で強制する lease の是非。
5. **全史検査と履歴取得の間の TOCTOU** (v1 も同一構造)。
6. **qualification lane へ署名 gate を付けるか** (evidence-only lane の意味が変わる)。

## R-d. ユーザーが行う一度きりの bootstrap (裁定ではなく手順)

land が済んだ後、AI が到達できない host で 1 回だけ行う。逐語は
`output/insights/2026-08-27_t1629-ratification-broker/README.md` と
同 `verbatim/s5-broker-bootstrap-procedure.md`。

**この手順を踏むまで批准の受理集合は空**であり、certified な選択結果は生成されない
(land 前と同じ状態で、後退ではない)。
