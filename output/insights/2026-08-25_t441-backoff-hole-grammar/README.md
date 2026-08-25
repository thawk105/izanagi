# [T-441] backoff 軸 EVOLVE-BLOCK hole の受理文法 — Tier 1 実装と裁定パッケージ

2026-08-25、dev-wave `dev-wave-t441-backoff-hole-grammar`、基準 main = `c3c5ca0a`。
[T-409] 択一 4 (scope は trigger 軸で閉じ backoff は本 task が所有) による分離。

**本 wave は Tier 1 を実装して land し、Tier 2 の 4 択を裁定パッケージで返す。**

## 1. 起点 — 今日の backoff hole は敵対形をほぼ全部受理していた (実測)

pin `028f34d` の実 `include/backoff.hh` に実 `patches/silo-backoff-fixed.patch` を適用した木を
repo 外に作り、本物の `p3_s4_loop.quarantine(write=False)` へ 32 形を通した。

**実装前: 受理 25 形 / 拒否 7 形。** 拒否の内訳は既存 denylist 3 (`system` / `ofstream` / `asm`)、
無条件 loop 2 (`while(true)` / `for(;;)`)、コメントと継続行 2 だけで、
**hole の「形」を見る規則は 1 つも無かった。**

通っていた危険な形: 共有適応状態の読み書き (`Backoff_.load` / `.store`)、`static` と
`thread_local` による隠れ適応、`rdtscp` による非決定合成、NaN と inf、`goto` / `return` / `throw`、
多重宣言子、参照束縛、型変更、lambda、comma 演算子、三項、**空実装**。

**実装後: 受理 15 形 / 拒否 17 形。** 新たに拒否した 10 形はすべて `BACKOFF_GRAMMAR` に帰属し、
既存 7 形の拒否理由は subtype ごと保存されている。

## 2. 実装した Tier 1 と、その根拠

Tier 1 は **この hole の編集面を規定する 2 つの正本が同時に禁じる集合**に限ってある。

- `docs/decisions.md` D39 決定 1 逐語: 「coder 編集面は #if 合成枝 (hole) の **1 行のみ**。」
- `patches/silo-backoff-fixed.patch` の骨格コメント逐語: 「既存 silo API を呼ぶ
  **straight-line code のみ**。」

**この 2 つは「ちょうど 1 文か、straight-line な複数文か」で食い違う。** さらに既存テスト
`test_effect_scanner_runs_only_after_structure_and_sees_exact_written_hole_bytes` は
backoff marker に 4 行の複文を渡して受理を期待値に固定していた。
**親はこの衝突を自分で解かず、Tier 1 を両方の読みの共通部分に限った** — どちらが後に採られても
過剰拒否にならない。

| 規則 | 内容 |
|---|---|
| 空実装 | 拒否 |
| 宣言 | `double now_backoff` の exact な単一宣言 1 個 (型変更・参照束縛・多重宣言子・括弧付き declarator を拒否) |
| 出現 | 宣言以外の `now_backoff` 出現を一律拒否 (読み書きを区別しない) |
| 制御フロー | jump / label / 分岐 / loop / try-catch を拒否 |
| 記憶域 | `static` / `thread_local` を拒否 |
| 値 | `coder.value` の整数性と 1..1000 値域、`int()` 変換の無損失性 |
| 資源 | type と raw-size の preflight を帰属検査と materialization より前へ |

## 3. 塞いだ帰属汚染 2 型 (段 6 の敵対レビューが発見、親が現物で再現)

**(a) 数値 token の前方一致。** 文法は C++ の pp-number 全体を 1 token にするのに、
帰属検査は十進**接頭辞**しか読んでいなかった。次がいずれも全関門を通り、
台帳の genome と実行値が食い違ったまま certified され得た。

| 申告値 | hole | 実際に走る値 |
|---:|---|---:|
| 1 | `double now_backoff = 1e2;` | 100 |
| 20 | `double now_backoff = 020;` | 16 (8 進) |
| 2 | `double now_backoff = 2'0;` | 20 (桁区切り) |

**修正は表記を狭めず、token 全体を C++ の値として読む形にした。**
`double now_backoff = 20.0;` は既存の canonical な正例なので、20 として通り続ける。

**(b) 間接的な再束縛。** 次が文法・効果検査・帰属検査をすべて通り、
`BACKOFF_FIXED=20` の候補が実値 30 で走っていた。

```cpp
double now_backoff = 20;
[](double& x) { x = 30; }(now_backoff);
```

`(&now_backoff)[0] = 30;` と `*(&now_backoff + 0) = 30;` も同様。
字句検査で読みと書きを区別できず参照引数経由で読みが書きに化けるため、
**宣言以外の出現を一律拒否**する fail-closed を採った。

## 4. D127 決定 (1) の引用は過一般化だった

段 2 プランと段 3・段 6 のレンズ B は揃って「consumer だけ狭めるのは D127 決定 (1) が
名指しで退けた形」を根拠に literal-only を止め、**設計凍結**を推奨した。
本文を引くと禁止の前提は「role 定義が**複数行の raw comparator** を契約上許可しており
(中略) **sort 軸では**合成が事前 allowlist からの選択に化ける」であり、軸固有の推論である。
backoff 軸の role が宣言する出力は単一の代入文なのでこの前提が成立しない。

**一次資料の要約 ([T-409] README) が限定を落として一般則として引用しており、
2 つの子が独立にそれを継承した。** 決定本文を引く規律が別経路で 2 回必要になった事例である。

## 5. 変異事前登録は実測でやり直した — 13 規則のうち独立検出力があるのは 8 件

実装子が「空実装の拒否は宣言必須に包含される」と申告したため、13 規則すべてについて
**その規則だけを除いた版**を repo 外に作り、40 入力の受理集合を除去前後で比較した
(guard が `return _reject(...)` 形なので `return` を外すと制御が続く = 規則の除去)。

- **受理集合が広がる 8 件** (raw-size / storage / control-flow / reference /
  declaration-count / rebinding / value-integer / value-range) → accepted-set kill として登録。
- **受理集合は不変だが除去すると拒否が未捕捉例外へ倒れる 2 件** (input-type / tokenize)。
  `TypeError` / `AttributeError` / `AssertionError` / `UnboundLocalError` になり、
  campaign が異常終了して reject が台帳に残らない → fail-closed kill として登録。
- **拒否 rule ID が変わるだけの 3 件** (empty / declaration-type / single-declarator)。
  実効 gate は `declaration-count` で、この 3 件はその診断上の細分化である。
  「診断文字列だけの赤を kill にしない」規律に従い**登録から外した**。

**実装は誤っていないが、「13 層の独立した関門」とは書けない。**

## 6. 変異 matrix

**baseline PASSED (失敗 node 0) / 12 KILLED / SURVIVED 0 / MISMATCH 1。**
MISMATCH は表記由来で実質 13/13。詳細は `mutation-matrix.md`、spec は `mutation-spec-final.json`。

過剰拒否を捕まえる正例側も対で登録し、実際に発火した。

- 「文法を無条件に全部拒否する」変異は **69 node** を落とし、その中に
  `test_quarantine_passes_clean_backoff_value` (既存の `20.0` 正例) が含まれた。
- 「文法を全 marker へ拡張する」変異は **trigger 軸と sort 軸のテスト**を落とし、
  「1 bit も変えない」不変条件が実在して発火することの裏が取れた。

## 7. 閉じていないもの (過大主張を避けるための明示)

- **backoff 軸で規律 2 が成立したとは書けない。** 式段の逸脱 — `Backoff_` の読み書き、
  `rdtscp`、NaN、inf、comma 演算子、関数呼出し、三項 — は Tier 2 の裁定まで開いたまま。
- **表記の正準化は閉じていない。** `20` / `20.0` / `20.00` は同じ実効値なのに別 `src_token`・
  別 variant・別 cache entry になる。
- **grammar version は identity / WAL / cache に束縛していない。** 文法を後で変えても、
  旧文法で受理した成果物が再検査されずに再利用され得る ([T-409] must-fix B-2 の backoff 版)。
- **32 形の実測は `quarantine()` 単体の字句的増分**であって certified 受理集合を測っていない。
  build / verify / bench / COMMIT / cache / WAL replay は測っていない。
- 既存の `diffq-<hash>` と `byte_length` / 短縮 SHA-256 による候補長・同一性の漏れは
  本 wave 以前から存在し、WAL の key なので触っていない。

## 8. 裁定パッケージ (ユーザー裁定待ち 4 件)

| # | 択一 | 影響 |
|---|---|---|
| (i) | 式の中身を定数式 / literal のみへ絞るか | 上記 7 の式段が閉じる。**role・review ledger・adapter・manifest の同時改訂とユーザー明示承認が要る** |
| (ii) | hole は「ちょうど 1 文」か「straight-line な複数文」か | D39 決定 1 と骨格コメントの衝突。既存テストは後者を固定していた |
| (iii) | grammar version を identity / WAL / cache へ束縛するか | 束縛すると backoff campaign の ID と cache namespace が動く。自律 backoff campaign の凍結コーパスは `output/` に不在なので影響半径は小さい |
| (iv) | hole の数値表記を正準化するか | 閉じると重複 variant が消える。**正準十進整数の強制は既存正例 `20.0` を壊すので、正準化の定義そのものが設計判断になる** |

## 9. §8 B-1 との関係

依頼は本 wave を「合成軸そのものを広げる作業」と位置づけたが、**受理文法は軸を狭める関門で
広げない。** `docs/paper-story/2026-08-23.md` §8 の B-1 (合成軸が既知軸最良を超える証拠) は
S-1a で不成立が確定しており、本 wave はその証拠を 1 件も増やさない。
関係は前提条件の側にある — S-1a で合成軸は静的 backoff 最良に −36.0%〜−51.9% で負けたので、
backoff 軸は「既知軸を組み合わせた構成」の部品として残る道がある。その道を使うとき、
hole が実測のとおり素通しのままだと、出た利得が合成の手柄か hole 逸脱の副産物かを
機械で切り分けられない。加えて [T-409] must-fix B-6 が「有限 policy 選択は headline synthesis
evidence ではない」と釘を刺しており、受理集合を有限化するほど backoff 軸も同じ限定を負う。

## 逐語 (凍結)

| ファイル | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief |
| `verbatim/s1-brief-addendum.md` | 32 形の実測 (実測 1 の正本) と brief 本体の訂正 2 点 |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (read-only、`gpt-5.6-sol`、reasoning=xhigh) |
| `verbatim/s3-lensA.md` | 段 3 レンズ A = 正しさ境界・C++ 意味論 |
| `verbatim/s3-lensB.md` | 段 3 レンズ B = consumer 閉包・既裁定整合 |
| `verbatim/s4-adjudication.md` | 段 4 親裁定 (real/refuted 表、Tier 1 / Tier 2 の境界) |
| `verbatim/s5-author.md` | 段 5 実装子の報告 |
| `verbatim/s6-reviewA.md` | 段 6 敵対レビュー A (must-fix 10) |
| `verbatim/s6-reviewB.md` | 段 6 敵対レビュー B (must-fix 6) |
| `verbatim/s6-fix.md` | 段 6 fix 子の**停止報告** (親の指示矛盾を検出して 1 行も書かずに止めた) |
| `verbatim/s6-fix2.md` | 段 6 fix 子の実施報告 (13 件 closed) |
| `verbatim/mutation-registration.md` | 変異事前登録 (単一理由性の実測表) |
| `mutation-spec-final.json` | 最終 spec |
| `mutation-matrix.md` | 変異 matrix の結果 |

## 環境

計測は行っていない (性能値なし)。テスト実測 = Pegasus login node から `tools/run_tests.py` が
gen_S へ同期 dispatch した走行。焦点走 = 621 passed / 6 skipped
(`test_p3_s4_loop` / `test_critic` / `test_diff_quarantine` / `test_p3_s4_loop_sort` /
`test_p3_s4_loop_trigger_gating` / `test_auditor_gate` / `test_layer3_report` /
`test_campaign_import_invariant`)。変異本走は `tools/mutation_worktree.py` の使い捨て worktree で
`--runner-mode dispatch` により実行した。
