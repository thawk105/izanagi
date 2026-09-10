# 逐語射影 — [T-2028] 段 2 / 段 3 の子へ渡す既裁定と契約文

親が `docs/decisions.md` と凍結物から逐語で写した。省略記号で切っていない。

## D95 (実装面の著者境界) の適用

実装面 (コード・テスト・実行可能な probe / harness / script・機械設定) は Codex `role=author` の
実装子が書く。親は実装面を直接編集しない。

## D1206. 索引が版番号を返さない場合は代替の来歴で固定してよい (2026-08-28)

**決定:** 文献索引が API や export の版番号を返さない場合、**接続先・応答の field 名・
応答 header・生データの digest** を組にして版の代わりに固定してよい。
ただし**「版番号」と呼ばず「版が取得不能な場合の代替来歴」と明記**し、改訂手続きの中で固定する。

**理由:**

- 対象の 3 索引はいずれも版番号を返さない。代用を認めないと、当該軸は最上位の証拠水準に
  到達できない。
- 代用を「版番号」と呼ぶと、他所の版番号と同じ強度の主張に読める。呼び名を分けることで、
  主張の強度の違いが読み手に伝わる。
- 固定する 4 つ組は、いずれも取得時点に観測できて事後に改変できない。

**却下した選択肢:**

- **代用を認めない** — 当該軸が構造的に到達不能になる。
- **代用を版番号と同じ名前で記録する** — 主張の強度を実際より強く見せる。

## 旧登録 §8.3 の pacing 条項 (逐語)

**OpenAlex の pacing。** 測定記録によれば、本 wave の約 13 request の後に HTTP 429 が返り、
`Retry-After` は 79725 秒 (約 22.1 時間) を示した。軸 1 の凍結記録が示す
「1 窓 100 request」には達していない。

> **「無償枠が IP 単位で複数の実行主体に共有されている」は、この観測と
> 同日に別 wave が同一ノードから OpenAlex を測っていた事実からの推論であって、
> 直接の観測ではない。** 直接観測したのは request 数・status・`Retry-After`・時刻・
> 送信元ノードだけである。**共有の単位は実行段の preflight で観測して確定する。**

- **実行前の availability preflight で `Retry-After` を読み、値が残っている間は本走を開始しない。**
- **最小 request 間隔と cooldown を実行段の preflight で測り、記録する** (§13.2 の N3)。
- API キー、email、前払い残高は加えない。

## 旧登録 §8.4 失敗の扱い (逐語)

- **429・503・空ボディ・通信失敗・再試行上限到達は、その query を `未完走` にする。**
  完走した query だけを取り出して軸の成熟度を名乗ってはならない (§7.3 の論理積)。
  部分結果から書いてよいのは、**完全に完走した単一 query ID についての内部的な取得報告だけ**で、
  そこに不在の表現を置いてはならない。
- **索引スナップショットの不一致:** §7.4 に従う。補えない範囲は限界として記録する。

## 旧登録 §13.2 の N3 (逐語)

| N3 | OpenAlex の最小 request 間隔と cooldown | `Retry-After` と rate-limit header を記録し、pacing を確定して実行記録へ書く (scheduling のみ) |

## amendment §6 の U11 条項 (逐語)

- **arXiv が同一 work ID を頁境界で 2 回返し、宣言総数では 1 回だけ数える事象**が軸 1 の実行で
  観測されている。本実行器は再出現を完走拒否として扱う (厳格側)。この扱いを維持するかは
  人間裁定に属し、裁定が付くまで軸 3 の live 本走は開始できない。

## amendment §3 の release gate (逐語)

**外部 request 前の全test・docs・provenance緑はmanagerのrelease gateであり、実行器自身が
acceptance receiptを検証する機械関門ではない。** managerはこの順序を守り、未受入codeからlive CLIを
起動しない。production成果物はcanonical CLIの`--live` sessionだけが発行する。bundle validatorが
保証するのは、seal済みphase argv・live session marker・requestごとのone-shot send receipt・WALの
構造的一貫性までであり、CLIを起動した主体の人間性や因果性を証明しない。

## amendment §3 の seal closure (逐語)

**registration seal が束縛するのは、封印対象として列挙した closure の bytes だけである。** その
closure は exact に次の 8 file と、catalog・OQL fixture・argv/phase contract である — 実行器 source
2 本 (`orchestrator/related_work_search.py`、`tools/run_axis3_search.py`)、schema 4 本
(`axis3_search_{catalog,checkpoint,page_evidence,registration_seal}.schema.json`)、frozen input 2 本
(旧登録と本 amendment)。**header が列挙する他の input path (索引実測、軸 1 実行記録、7.7 の規則、
decisions) は本文書の来歴であって seal の受理 closure ではない。** seal がそれらの blob を
束縛するかのように読んではならない。

**repository 全体の HEAD 一致を受理条件にしない。** 記録を commit すれば HEAD は必ず動くため、
HEAD 全体を条件にすると seal が発行と同時に再利用不能になる。**受理条件は上記 closure の各 file に
ついて、作業ツリーの bytes と `HEAD:<path>` の blob が一致することである。** Python interpreter の版と
依存 package の版は**来歴として記録するが受理 gate に入れない** — 無関係な環境更新で seal が腐るためである。

## 軸 1 amendment が固定した最小間隔 (逐語)

- **最小間隔:** arXiv 3 秒、DBLP 45 秒、OpenAlex 1 秒。**host 単位の limiter を control・枝・
  再試行で共有する。**

## 軸 1 実行記録の DBLP 実測 (逐語)

### 4.5 `transport` — DBLP の切断

DBLP は連続取得で接続を切る。2 秒間隔では 24 リクエスト目付近から、15 秒間隔でも 7 リクエスト
程度で `RemoteDisconnected` が 3 回の再試行 (契約 §8 の 3→6→12 秒) を通り抜けた。
**45 分の冷却の後、30 秒間隔で再走したところ回復した。**
`AX1-T12@dblp` はさらに `f=100` で HTTP 500 に当たり、7 分の冷却後に完走した。
`C-OP-1@dblp` の 1 回目も `f=300` で HTTP 500 に当たり、10 分の冷却と 45 秒間隔で完走した。
