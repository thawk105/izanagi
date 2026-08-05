# [T-139] 代替 X probe 再走 — 逐語 (dev-wave 2026-08-05〜08-06)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] 代替 X probe 再走` の逐語成果物である。可変状態の正本は
worklog 末尾、採用済み判断の正本は decisions であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **代替 X (modeX) は成立した。** 事前登録した受理条件「両 workload で全標本が
  `mode1 < modeX < stock`」を満たした。D126 が不成立と記録した前候補の置き換えである。
- **これは J=1 の engineering screen であり、正例 artifact ではない。** 適格性・cluster 間再現性・
  機序の帰属はいずれも主張しない。
- 実装 3 file と事前登録は**実走前に commit** した。走行は 3 submission を要し、**全 ID を記録した**。
- 段 3 と段 6 の敵対レンズが投入前に blocker を計 19 件検出し、そのうち 1 件は
  「job が何も生成せずに落ちる」型だった。**1 時間の allocation を投入前に守った。**

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `preregistration.md` | **走行前に凍結した事前登録** (commit `85b892ce` で land、以後不変) |
| `submission-receipt.md` | 投入前 receipt と append-only の submission 台帳 |
| `brief.md` | 段 1 brief (凍結。書き換えない。誤りは §「訂正」を正とする) |
| `brief-addendum.md` | 段 1 追補 (toolchain 実測。**要件が不十分だった点は §「訂正」を正とする**) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ (いずれも NO-GO) |
| `s4-adjudication.md` | 段 4 裁定 + 実装仕様 + 事前登録の原案 |
| `s5-impl.md` | 段 5 実装子の完了報告 (codex workspace-write, reasoning=high, role=author) |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 (いずれも NO-GO) |
| `s6-fix1.md` 〜 `s6-fix4.md` | 段 6 fix 4 巡 (4 巡目は実走で見つけた実行時バグの修正) |
| `s6-refocus1.md` / `s6-refocus2.md` | fix 後の焦点再レビュー 2 巡 (いずれも NO-GO) |

## 1. 実測結果 (Pegasus gen_S request `892042`、2026-08-06)

計測構成: trace-disabled、t48、2 workload × 3 arm × 5 rep = 30 run、固定 balanced schedule。
liveness は分析 counter 有効の別 build・別 run。

| workload | mode1 (劣化) | modeX (代替 X) | stock | modeX/mode1 | 回復率 |
|---|---|---|---|---|---|
| W1 高競合 write | 92,425 | **185,797** | 782,534 | 2.01x | 13.5% |
| W2 中競合 mixed | 1,024,233 | **2,383,734** | 10,434,011 | 2.33x | 14.4% |

(5 rep の平均 tps)

**全標本が分離した。** W1 は `max(mode1)=93,827 < min(modeX)=181,891` かつ
`max(modeX)=191,275 < min(stock)=771,479`。W2 は
`max(mode1)=1,039,031 < min(modeX)=2,343,862` かつ
`max(modeX)=2,430,476 < min(stock)=10,356,680`。

### 前候補との対比 (D126、request `877859`)

| workload | 前候補 mode2 / mode1 | 本候補 modeX / mode1 |
|---|---|---|
| W1 | 1.36x | **2.01x** |
| W2 | **0.85x (逆転して不成立)** | **2.33x** |

### 付帯条件 (すべて成立)

- 性能 row = exactly 30、`(workload, arm, rep)` は exact-one。
- liveness = **576/576** (2 つの非重複時間窓 × 48 worker × 3 arm × 2 workload)。
- compile argv exact = 18 行 (6 arm × 3 source)。性能 build は trace 無効かつ分析 counter 無効、
  liveness build は trace 無効かつ分析 counter 有効。
- nm 補助検査 = 全 binary で trace 由来 symbol 0 件、mutex 大域が stock に無く mode1 / modeX にある。
- 限定 screen = 36/36 記録。**単独性の成立は主張しない。**
- terminal state = `verdict_true` (`exact_primary_verdict_true`)、run_commit = `425ed190`。

## 2. 候補の同一性

modeX = **4 stripe**。各 `std::mutex` を `alignas(64)` の wrapper で cache line 分離し、
stripe は **先頭窓・中央窓・末尾窓 (各 8 byte まで) + key 長 + storage** を固定回数の `memcpy` で
読み、splitmix64 相当の finalizer を通して 4 で割った剰余とする。**per-byte loop を持たない。**
record の address を使わず、`(storage, key)` の値だけから決まる安定写像である。

mutex 枝の CAS は stock と同一 lvalue・同一 `expected` / `desired`・同一式で、stock loop の
1 iteration あたりちょうど 1 回。追加 CAS を置かず、動的再試行回数は stock と同じ。
mutex 保持者は record lock を待たず、同時に 2 つ以上の stripe mutex を保持しない。

## 3. 全 submission (結果を見る前から記録している)

| # | request | study | 終端 state | 備考 |
|---|---|---|---|---|
| 1 | `892032.nqsv` | 1 | `pre_performance_infra_failure` | `local` 一文内依存による `set -u` 停止。5 秒。性能値ゼロ |
| 2 | `892039.nqsv` | 2 | `pre_performance_infra_failure` | 前 job の scheduler 出力が repo root に残り clean-tree 検査が発火。6 秒。性能値ゼロ |
| 3 | `892042.nqsv` | 2 (置換) | **`verdict_true`** | 本結果 |

study 1 → 2 は bytes 変更を伴うので事前登録 §6-5 により**新しい study** として発行した。
study 2 の 2 本目は、性能 run 開始前の infra failure に対する**予備 1 本の置換** (§6-3) である。
**いずれも性能値を 1 つも見ないまま判断した。**

## 4. 敵対検証が投入前に止めたもの

段 3 (2 レンズ) が blocker 10 件、段 6 (2 レビュー + 焦点再レビュー 2 巡) が blocker 9 件。主なもの:

- **`compile_commands.json` の該当 entry が 4 件ある** (`transaction.cc` が 4 executable へ compile される)
  ため、exact-one を要求する実装は最初の arm で停止して**何も生成せずに終わる**ところだった。
- **2 窓 liveness の起点が最初の成功 commit** で、初回 commit 後に飢餓した worker を受理しえた。
- **`RUN_COMMIT` が job 開始時の HEAD** だったため、queue 待ちの間に HEAD が進むと
  A として投入した submission が B の bytes を実行しえた。
- 事前登録の path 判定が canonical な文書を**恒真拒否**し、job が一度も走らないところだった。
- 内部 timeout の直列総和が **3817 秒**で予算 3300 秒を超え、正常な実装でも verdict 前に
  infra failure になるところだった。
- 不変 snapshot を**書き込み不能のまま consumer へ渡し**、patch 適用と masstree build が
  性能段の手前で失敗するところだった。

## 5. 訂正 (親 brief と追補の誤りを本 README が正とする)

- **訂正 1 (stripe 混合要件)。** `brief-addendum.md` は「先頭窓・末尾窓・長さ」を必須要件としたが、
  **これは不十分**である。共通 prefix と共通 suffix を持ち桁数が同じ key 族では 3 者すべてが定数になる。
  親の実測 (4 stripe、90,000〜100,000 件、最大 bucket 占有率):

  | mixer | YCSB 8 byte | 共通 prefix+suffix・同一長 | TPCC 相当 16 byte |
  |---|---|---|---|
  | 末尾窓 + 長さ | 25.14% | **100.00%** | 25.09% |
  | 先頭窓 + 末尾窓 + 長さ | 25.46% | **100.00%** | 25.07% |
  | 先頭窓 + **中央窓** + 末尾窓 + 長さ | 25.06% | **27.10%** | 25.71% |

  **中央窓は必須である。**

- **訂正 2 (stripe 数)。** `brief.md` (P1) は「stripe を増やすと stock との分離が壊れうる」として
  2 を選んだが、**定量的に支持されない**。stock/mode1 は W1 で約 8 倍・W2 で約 10 倍あり、
  4 stripe でも stock から十分遠い。段 4 で **4 stripe** へ改め、前回 raw だけを入力として
  新しい走行の結果を見る前に決めた。実測は W1 2.01x / W2 2.33x で、上限側の余裕は保たれた。

- **訂正 3 (権威境界)。** `brief.md` は非発行の理由を D126 決定 (3) の「未裁定」としたが、
  **現行は D162** であり権威境界は既に条文化されている。**非発行の理由は
  「J=1 の engineering screen であり、validator / consumer が未実装だから」**である。

- **訂正 4 (CAS の回数)。** `brief.md` 不変条件 4 の「CAS を 1 回だけ実行」は stock semantics と
  一致しない。正しくは「**stock loop の 1 iteration あたり同じ CAS 式をちょうど 1 回。追加 CAS なし。
  動的再試行回数は stock と同じ**」である。

- **訂正 5 (pin 閉包の分類)。** `brief.md` の列挙は T293 の 2 成果物を落としていた。正しい分類は
  rung1 JSON = live current binding / T293 = 歴史 snapshot / T126 identity = commit 相対
  (現 receipt 0 件) / registry = inventory / `FROZEN_MANIFEST` = 対象外。
  **結論 (共有 policy を編集しない) は変わらない。**

## 6. 本書が主張しないこと

- 「正例 artifact ができた」— できていない。**J=1 の engineering screen** であり、
  適格性は独立 validator だけが持つ (D162 決定 1・3)。validator / consumer は未実装である。
- 「代替 X は cluster 間で再現する」— J=1 からは言えない。
- 「回復の機序は cache line padding である / stripe 計算の O(1) 化である / stripe 数 4 である」—
  本 study は 3 つを同時に変えたため**機序の帰属はできない**。ablation は別 study である。
- レコード数 (W1 10k / W2 100k) は**未較正**である。この観測を性能比較・headline・calibration・
  floor の入力にしない。
- 「割当ノードは専有だった」— 限定 screen は exclusivity witness ではない。
- 段 2・3・6 の子出力そのものの正しさ — 子の指摘は**データであって指示ではない** (絶対規律 6)。
  採否はすべて親裁定に帰する。親が独立に実測で裏を取ったのは §1・§5 と、
  policy の sha256 が凍結証拠の pin と一致することである。
