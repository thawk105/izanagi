# 裁定パッケージ — [T-595] reasoning A/B (2026-08-07)

wave = `dev-wave-t595-reasoning-ab` / branch = `worktree-dev-wave-t595-reasoning-ab`
逐語 = `output/insights/2026-08-07_t595-reasoning-ab-latch/`

## 何が起きたか (1 段落)

依頼は「段 2/3 の `reasoning=max` を `high` へ落とせるかを paired・blind・非劣性で評価する」
だった。**評価は実施していない。** D207 が必須とした endpoint (後段の must-fix 件数と fix 巡回数)
は段 2/3 の下流にあり、1 replicate = 1 本の完全な dev-wave になる。単一 wave の射程を桁で超える。
代わりに、A/B が済むまで既定が黙って下がらないようにする機械 pin を実装した。
**引き下げ可否の evidence は 0 件のままである。**

---

## 裁定 1 — A/B campaign に着手するか

**論点:** D207 の endpoint をそのまま満たす実験は、完全な dev-wave を多数走らせる資源決定である。
親は決めない。

**必要規模の見積もり (下限であって上限ではない):**

- endpoint を fix 巡回数、margin を 1 巡に取ると、片側 5% / 検出力 80% の正規近似だけで
  10 pair 台後半。有限標本の t、co-primary の joint power、欠測を入れればさらに増える。
- 1 pair = 同一 task を 2 arm で走らせる = **完全な dev-wave 2 本**。
- 分散の見積もり自体が弱い。歴史成果物から取った分布は、fix worker 出力でない裁定文書を
  巡回に混入させており、実装を伴う wave の同定も命名揺れに依存する。
  **paired 差の分散も、引き下げ側 arm の分散も相関も未観測である。**
- codex 実走はログインノード限定 (計算ノードは外向き DNS 不通)。

**選択肢:**

- **(a) 着手する。** 予算と wall-clock を確保し、campaign 設計 wave を起こす。
- **(b) 着手しない。** 機械 pin を恒久扱いにして T-595 を閉じる。
  「max のまま」が既定として固定される。
- **(c) 保留。** T-595 を裁定待ちのまま残し、pin だけ効かせる。

**親の推奨:** (c)。理由は裁定 3 の前提が未整備で、いま (a) を選んでも campaign を
正しく設計できないため。ただし (b) も筋が通る — 節約施策として見合わない可能性が高い。

---

## 裁定 2 — 着手するなら joint か段別帰属か

**論点:** 段 2 と段 3 を同時に `high` にする joint 設計は「両方下げてよいか」には答えるが、
**片方だけの可否と交互作用には答えない。**

**選択肢:**

- **(a) joint (`MM` 対 `HH`)。** 必要本数は裁定 1 の見積もりどおり。
  T-595 の文面は満たすが、段別の裁定はできない。
- **(b) 段別帰属 (`MM` / `HM` / `MH`)。** 同じ case 数で **1.5 倍**の本数。
- **(c) 交互作用まで (`MM` / `HM` / `MH` / `HH`)。** **2 倍**の本数。

**親の推奨:** (a)。段 2 プランと段 3 の敵対相談も joint を推奨。
ただし段 3 レビューは「joint で通っても段別には使えない」と明記しており、
将来「段 2 だけ下げたい」が出たとき再実験になる点を承知のうえで選ぶこと。

---

## 裁定 3 — campaign の前に閉じる必要がある前提 (装置外)

段 3 / 段 6 が real と裁定し、本 wave が**実装しなかった**もの。
いずれも `tools/codex_reasoning_ab.py` の中では閉じられない。

1. **trusted supervisor がない。** endpoint を偽装不能にするには wave の全 worker を実際に
   起動する単一の supervisor が要る。現行 dev-wave の正本は `DW-O01` の直接 `codex exec` +
   `.done` であり、`tools/codex_worker_launch.py` の production caller は repo 内に存在しない
   (実測)。caller 登録 API では手書き JSON でも台帳が成立する。
2. **外部 custodian の独立 trust root がない。** 現行の masking は same-owner advisory であり
   盲検ではない。ユーザーが承認した公開鍵 fingerprint と append-only な campaign registry を
   repo 外に置かない限り、`blind=true` を名乗れない。
   **これはユーザーが用意しない限り実走を開始できない項目である。**
3. **producer 契約の追記先に予算がない。** 上記を `docs/dev-wave/*.md` へ書く必要があるが、
   aggregate 予算は **25,187 / 25,200 bytes = 残り 13 bytes** (実測)。
   [T-597] と束ねて捻出先を決める裁定が要る。
4. **母集団・層化・margin・power が未確定。** 対象 task の包含・除外規則、
   margin の導出根拠 (許容できる最大損失から決める)、欠測の扱いが未定。

**未発火のまま持ち越した所見 10 件:** A-4, A-5, A-6, A-10, A-11, B-3, B-4, B-6, B-7, B-9。
**refuted ではない。** 全文は `s3-lensA.md` / `s3-lensB.md`、対応表は `s6-focus.md`。

---

## 裁定 4 — 段 8 で予算に阻まれた dev-wave 改善候補 2 件

段 8 の自己改善契約は「予算に収まらなければ reference へ統合し、それでも意味等価にできなければ
変更を止めてユーザー裁定へ返す」と規定する。`docs/dev-wave/*.md` の余地は **13 bytes** であり、
次の 2 件は書けなかった。[T-597] (予算の捻出先) と束ねて裁定してほしい。

1. **`DW-O01` の起動形が、背景 job + worktree 隔離下では実行できない。** 入口が書く
   `codex exec ... を bash -c で包んで nohup setsid` の一行形は、Bash guard に複合コマンドとして
   拒否される。実際には wave ごとに `run_sN.sh` を Write して起動する形が事実上の標準に
   なっているが、`DW-O01` にその形が書かれていない。本 wave も全子でこの形を使った。
2. **変異 harness の `--runner-mode dispatch` は runner argv と整合しない。** harness 側で
   `dispatch` を宣言しても、runner (`tools/run_tests.py`) に `--force-dispatch` を渡さなければ
   ログインノードでは local 実行になり、baseline が dispatch receipt を得られず
   `PARSE_ERROR` で harness ごと中止する。本 wave で 1 走を空費した。
   `DW-M05` が挙げる「tool が検証できない自己申告」が実は 3 つある。
   機械化するなら harness 側の入力検査 (dispatch 宣言時に runner argv を検証) が候補だが、
   コード変更を伴うため段 8 の自動是正の枠を超える。

**親の推奨:** 2 を harness の入力検査として実装する小さい T を起票する。1 は [T-597] の
捻出結果に従う。どちらも本 wave では実装していない。

## 参考: 本 wave が land する変更 (裁定不要、報告のみ)

`tools/check_docs.py` が `docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` の
`reasoning=max` を節ごとに exact pin する。可視本文から effort 表記
(`reasoning=` / `reasoning_effort=` / `model_reasoning_effort=`、引用符付きを含む) を
すべて抽出し、値の列が厳密に `["max"]` のときだけ受理する。

- 受入 7113 passed / 20 skipped、変異 7/7 KILLED。
- **解除は自動化していない。** A/B の後継裁定 → 契約と pin の同時更新 → 再走 の 3 段だけが経路。
- **この pin は実効 effort を attest しない。** 守るのは docs の記述だけである。
- 引用内に effort 値の例示を書いた DW-S02 / DW-S03 節は新たに拒否される (意図した fail-closed)。
  comment / code fence 内の例示は引き続き受理する。
