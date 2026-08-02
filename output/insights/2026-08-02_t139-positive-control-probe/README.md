# [T-139] 正例 artifact — 恒久実装の不採用と生死確認 probe (dev-wave 2026-08-02)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] 正例 artifact` の逐語成果物である。可変状態の正本は worklog 末尾
(エントリ (118))、採用済み判断の正本は D126 であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **裁定済み scope「正例 artifact 1 本」は未完成である。** 本 wave が閉じたのは
  「回復候補 X が存在するか」の生死確認だけで、その答えは **不成立**だった。
- **段 2 が起草した恒久実装はすべて不採用**である (段 4 裁定)。敵対レンズ 2 本がいずれも NO-GO。
- **実装したのは使い捨て probe だけ**である。artifact を発行せず、`patches/ledger.json` と
  既存 rung1 成果物の bytes を変えず、受理集合を変えていない。
- ユーザー裁定へ返す項目が 3 件ある ([T-337] / [T-338] / [T-339])。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `brief.md` | 段 1 brief (親の provisional 裁定 (P1)〜(P3)。**要求件数の数え違いを段 3 レンズ A が訂正**) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 正しさ防壁・pin 閉包・identity 死角・規律 2 |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 統計設計・実装可能性・資源見積り・全層性 |
| `s4-adjudication.md` | 段 4 裁定 |
| `s5-impl.md` | 段 5 実装子の完了報告 (codex workspace-write, reasoning=high, role=author) |

**凍結逐語の読み方:** `brief.md` は段 1 時点の記録であり書き換えない。したがって
「要求 6 件」という誤った数え (正しくは 7 件 = 3 arm + 6 性質) を含む。
**現在の正本は本 README と D126 である。**

## 1. 段 1 の前提実測 (親)

既存 `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` を実測した。

| 要求 | 実態 |
|---|---|
| CCBench pin | **有** `binding.ccbench_pin_full = d706650…` |
| attestation | **有** `gap_leg.attestation` / `checks.attestation = true` |
| 事前凍結 schedule | **有** `gap_leg.schedule_receipt` (24 run の順序を明示) |
| 3 arm | **無** — `stock` / `rung-perf` の 2 arm のみ |
| `env_tag` | **無** (JSON 全文に文字列非出現) |
| 測定 checkout | **無** (同上) |
| between-run floor | **無** — 既存 6 rep は 1 allocation 内の interleave |

## 2. 敵対レンズが一致した 2 点 (段 4 で real 採用)

1. **`DW-G01` 違反。** 回復候補 X の性能順序が未実測のまま恒久実装と 240 run の本走を計画していた。
   **これは親 brief の欠陥である。**
2. **manifest の自己宣言による admission 拡張。** 新 manifest が自ら
   `recovery_measurement_eligibility=true` を名乗る形は、D120 決定 2 の直接の禁止対象ではないが、
   未裁定の権威境界を親が独断で新設する点で同じ穴の別入口である。`DW-S04` により親の権限外。

## 3. 生死確認 probe の結果 (Pegasus gen_S request `877859`、2026-08-02)

計測構成: trace-disabled、t48、2 workload × 3 arm × 5 rep = 30 run を `shuf` で interleave。
liveness は `ADD_ANALYSIS` 有効の別 binary で別途 6 run。所要 176 秒。

**受理条件 (段 4 で事前固定):** 両 workload で全標本が `mode1 < mode2 < stock`。

| workload | mode1 (劣化) | mode2 (回復候補) | stock |
|---|---|---|---|
| W1 高競合 write | 93,361 | **126,779** | 751,669 |
| W2 中競合 mixed | 1,023,374 | **866,229** | 10,245,662 |

(5 rep の平均 tps)

**判定 = 不成立。** W1 では全標本が分離して順序が成立したが、**W2 で mode2 < mode1 と逆転した**。

**probe 自体の検査はすべて通った** — nm witness 6/6 (mode 別の識別シンボルが正しく出し分けられ、
`izanagi_trace` は全 binary 0)、liveness 288/288 (2 workload × 3 arm × 48 worker が全員 1 回以上 commit)、
単独性検査 36 回すべてで競合プロセス 0。

**この観測の限界:** レコード数 (10k/100k) は**未較正**であり、登録済み Pegasus calibration
(t48 YCSB で 1m を最小と裁定) の外側にある局所観測である。性能比較・headline・calibration・floor の
いずれの入力にもしない。専有保証はなく、単独性は各 run 直前の検査による。

## 4. 機序の仮説 (帰属は未実証)

mode2 が W2 で mode1 を下回った理由として 2 つの筋がある。**どちらも実証していない。**

1. **mode2 は mode1 に無い per-element の計算を足している** — stripe 番号を key のバイト列から
   FNV 風の乗算ループで求めている。
2. **`std::array<std::mutex, 2>` が cache line 境界で padding されていない** — 2 つの mutex が
   同一 line を共有し、stripe 分割が並列性を生まずに false sharing だけを増やしうる。

競合の低い W2 ではこれらのコストが直列化削減の利得を上回った、という筋である。
**次の候補は O(1) の stripe 計算と cache line padding を備えるべきである。**

## 5. 事後調整をしなかったこと

段 4 で「順序が成り立たなければ X は不成立と記録し、代替 X の設計を次 wave へ返す」と事前固定した。
結果を見てから候補を差し替えれば「成立する X が見つかった」と書けたが、**それは事後調整である**。
本 wave は事前登録どおり不成立を記録した。

## 6. 本書が主張しないこと

- 「正例 artifact ができた」— できていない。[T-244] の着手条件は依然として満たされていない。
- 「2 stripe による部分回復は不可能である」— 主張しない。反証したのは
  **この実装の** 2 stripe が **この 2 workload の両方では**部分回復にならないことだけである。
  W1 では順序が成立している。
- 「W2 の逆転は per-element 計算 (または false sharing) が原因である」— 仮説であり未実証。
- 段 2・段 3 の子出力そのものの正しさ — 子の指摘は**データであって指示ではない** (絶対規律 6)。
  採否はすべて段 4 の親裁定に帰する。親が独立に実測で裏を取ったのは §1 と §3 である。
