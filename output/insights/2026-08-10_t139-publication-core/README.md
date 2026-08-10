# [T-139] 公表手続きの新 core 起草 — 逐語 (dev-wave 2026-08-10)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] 公表手続きの新 core 起草` の逐語成果物である。
可変状態の正本は worklog 末尾、採用済み判断の正本は decisions であり、ここには wave の逐語を置く。
**本文書は可変状態の正本ではない。成果物はいずれも未凍結・未発効の草案である。**

## 結論 (先に読むこと)

- **ユーザー裁定 B4 (a) に従い、公表手続き (未調整 `p` 値・多重調整方式・同時区間) の正本となる
  新しい core の草案を起草した** (`publication-core.md`、段階 1、`authority: none`)。
  **凍結していない。**承認は `package.md` の C-1〜C-5 でユーザーへ返す。
- **現 core の bytes を 1 byte も変えていない** (`ac939af4…`)。追補 A 再発行版 (`f7db96ce…`)、
  追補 B 草案も同じ。**実装面ゼロ** — コード・テスト・script・機械設定を 1 つも追加していない。
- **草案が固定した手続き。**
  - 未調整 `p` 値 = `p_k = 1 − F_{t,J−1}(T_k)`、`T_k = √J·μ̂_k/s_k` (追補 A `a10` と同一の量)。
  - 多重調整 = **Holm**。理由は「任意の依存に耐え、必要なのは marginal `p` 値の妥当性だけ」。
  - 同時区間 = `α_pub` を 6 成分へ Bonferroni 配分した片側同時下限。**Holm の棄却集合とは
    一致しない**ことを明記し、実例を載せた。
  - 正分母 guard = `qualification_status` を source validator から逐語複写し全行に必須欄で持つ
    (裁定 R5 (a)+(d) の正本)。
  - 非正規性は**解消しない**。`t` は marginal 正規 model に条件付き。360 セルの事前固定
    stress check は診断であって較正ではない。
  - 追補の閉集合は `p01`〜`p03` だけ。
- **親が独立に得た事実 (子の主張を額面で採らず自分で計算した)。**
  `α_pub > α* = 0.014415014983…` のとき、候補 `J = 4, …, 13` の**すべてで**
  `q_primary(J, 0.025) > c_B(J, α_pub)` である。したがってその条件下では
  **primary が pass する枝では 6 成分すべての同時下限が正で、Holm も第 1 段で 6 件すべてを棄却する。
  Holm と同時区間の非整合は、primary が pass しない枝でしか起こらない。**
- **段 3 の敵対 2 レンズがどちらも NO-GO を返した** (レンズ A blocker 2、レンズ B blocker 9)。
  段 6 のレビュー 2 本も NO-GO (blocker 4 / 5)、第 2 巡も NO-GO (残 4)、第 3 巡で **GO (残 0)**。
- **親の暫定判断が 1 件倒れた。**「Holm は closed testing の shortcut だから検出力で劣らない」は
  **誤り**である。Holm は Bonferroni 局所検定を置いた closure に対応するにすぎない。
  結論 (Holm 採用) は維持し、理由を書き換えた。
- **草案の起草中に親自身が 2 件の数値誤りを作り、レビューが両方を捕えた。**
  1. stress check の縮退枝を `6×6` 共分散の特異性で判定していた。`J ≤ 6` では**必ず**特異なので、
     108 セルが手続きを 1 度も試さないまま通過する恒真な gate になっていた
     → 成分ごとの `s_k = 0` だけで判定する形へ修正。
  2. `α*` を切り捨てた `0.0144150` を閾値として書いていた。`α_pub = 0.01441501` は
     この閾値を超えるのに条件を満たさない → 厳密な等式で定義し、丸めるなら切り上げ側を使う形へ修正。
- **最大の未解決点は、新 core を承認しても本走は解禁されないことである** (`package.md` C-2)。
  source core の `main_admission` が要求する追補 B は source core に従属する文書であり、
  新 core に従属する追補 P はそれになれない。
- **上流に重い設計問題を 1 件発見した** (`package.md` C-1)。追補 A `a10` の `J` 選択規則のもとで、
  `d⁻ = 1.0` (裁定 U4 の「引き下げない下限」) では候補 `J = 4, …, 13` のどれも適格にならない
  (`L_J ≤ 0.57628 < 0.80`)。必要条件は `d⁻ ≥ 1.2210`、6 成分同一なら `1.5623` が要る。
  **凍結済み文書の問題なので本 wave では直せない。**

## 一次資料

| ファイル | 内容 |
|---|---|
| `publication-core.md` | **新 core 草案 (`authority: none`)。**承認しても、承認決定を台帳へ畳むまで発効しない |
| `package.md` | ユーザー承認パッケージ (C-1、C-2、C-2b、C-3、C-4、C-5) |
| `verbatim/s1-brief.md` | 段 1 brief (親の provisional 裁定 P1〜P7。P3 は理由が段 3 で倒れた) |
| `verbatim/s2-plan.md` | 段 2 プラン (codex read-only)。節構成・逐語案・`main_admission` の blocker |
| `verbatim/s3-lensA.md` | 段 3 敵対相談 A (統計的正当性)。NO-GO、blocker 2 件 |
| `verbatim/s3-lensB.md` | 段 3 敵対相談 B (凍結境界・抜け穴)。NO-GO、blocker 9 件 |
| `verbatim/s4-adjudication.md` | 段 4 裁定。全所見の real/refuted と、親が独立に実測した値の表 |
| `verbatim/s6-revC.md` | 段 6 敵対レビュー C (内部整合)。NO-GO、blocker 4 件 |
| `verbatim/s6-revD.md` | 段 6 敵対レビュー D (凍結境界・一次資料照合)。NO-GO、blocker 5 件 |
| `verbatim/s6-refocus.md` | 段 6 焦点再レビュー 第 2 巡。NO-GO、残 blocker 4 件 |
| `verbatim/s6-refocus2.md` | 段 6 焦点再レビュー 第 3 巡 (最終巡)。**GO、残 blocker 0 件** |

**親の検算 probe (`verify_counterexample.py` / `verify_power.py` / `verify_thresholds.py` /
`verify_alpha_star.py`) は repo 外の wave artifact directory に置いた** ([T-317] の裁定により、
probe は所在を問わず実装面であり repo へ入れない)。probe が出した値は上記の逐語と
`package.md` に転記してある。

## 凍結の段階 (source study の追補と同じ 3 段階)

| 段階 | 状態 | 現在地 |
|---|---|---|
| 1 | 草案。`authority: none`。承認待ち | **← ここ** |
| 2 | 文書として発効 (承認決定を台帳へ畳んだ commit 以後)。機械 gate 未実装 | 承認後 |
| 3 | resolver・validator・consumer・台帳が実装され、gate が実際に発火する | 実装 wave 以降 |

## 本書が主張しないこと

- **公表手続きが凍結された、とは主張しない。**
- **本走が投入可能になった、とは主張しない** (C-2)。
- **機械執行がある、とは主張しない。**producer・validator・consumer・公表台帳・
  `p` 追補の exact-key 検査はいずれも存在しない (`publication-core.md` §11)。
