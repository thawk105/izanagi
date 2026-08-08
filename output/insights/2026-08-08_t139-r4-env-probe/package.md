# [T-139] R4 環境 probe 後 — 凍結承認パッケージ (再提出)

```text
authority: none
default_effect: no-state-change
```

本書は**裁定前**の問い・選択肢・推奨理由である。裁定の結果の正本は `docs/worklog.md` の該当エントリ。

---

## 0. 何を承認してもらうのか

2026-08-08 の裁定 §47 で **R1〜R7 は全問推奨どおり**に確定し、
**R4 = (a)「gen_S 環境 probe 先行・導出写像を先に凍結」** に従って本 wave が probe を実走した。
同裁定の既定は **「凍結は段階 1 のまま probe 後一括再提出」** である。本書はその再提出にあたる。

| 成果物 | 状態 |
|---|---|
| `addendum-a-reissue.md` — 追補 A (再発行版) | 承認待ち |
| `derivation-map.md` — 判定写像 (probe より前に凍結済み) | 承認待ち |
| `../2026-08-08_t139-addendum-a/erratum-core-s15.md` — §15 の erratum | 承認待ち (bytes 不変) |
| `../2026-08-08_t139-addendum-a/record-items.md` — 受領証 schema の要件 | 承認待ち (bytes 不変) |

**凍結 core の bytes は 1 byte も変えていない** (`ac939af4…` を投入前後で照合済み)。

---

## 1. probe の実測結果 (3 測定すべて取得)

request `0:896504.nqsv`、node `bnode028`、gen_S、633 秒、
run commit `1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7`。
成果物は `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/`。

| 測定 | 結果 |
|---|---|
| (i) 待機後の `/proc/stat` | **13 窓すべて `valid`、すべて `[0, 1.0]` に収まった。最大 `0.0791` core-equivalents** (上限の 7.9%)。窓長は全 13 窓が `10.000 ± 0.100` 秒以内 |
| (ii) `CCBENCH_TRACE=1` build | **通った** (`stock`、`TRACE=1 / ADD_ANALYSIS=1`、configure 1.5 秒 / build 4.6 秒)。witness ゼロの状態が解消 |
| (iii) compiler digest | **取得** (`gcc`/`g++` とも `11.4.0`、realpath は `x86_64-linux-gnu-*-11`、bytes SHA-256 を記録) |

判定は **`feasible`**。

**閾値は観測から作っていない。**判定写像は probe より前に commit してあり、
probe が返すのは 3 値だけである。`a03` の `[0, 1.0]` は初版から**変えていない**。

**副産物の実証: `load1` を判定に使わない選択は正しかった。**
`post-03` は `load1 = 3.33` だが実測 busy は `0.0150` core-equivalents で、2 桁以上乖離する。
`load1` に `[0, 1.0]` を当てていれば正常な割当てが軒並み不成立になっていた。

---

## 2. 実測が既存の追補 A の誤りを 2 件確定させた

いずれも**初版が事実に反することを書いていた**もので、再発行版で訂正済みである。

### 2.1 `a04` の「予備 2 本が吸収する」は偽

初版は `a03` 不成立のコストを「`J_max` の余裕と**予備 2 本**が吸収する」と書いた。
core §9 の逐語は「性能測定の**開始前**の infra failure だけ…予備から置換可」
「**開始後**の失敗は reject または判定不能。予備で置き換えない」である。
`a04` は `a03` 不成立を**開始後**へ写しているので、**予備は使えない。**

→ 当該文を削除し、`J_max` の余裕でのみ吸収されること、届かなければ
`design_not_feasible` で終端することを明記した。あわせて写像先を
**`判定不能` 一意**に絞った (core が残す二択の裁量を消すため。`a04` の権限内)。

### 2.2 `a08` の「唯一の差は `-DCCBENCH_TRACE`」は偽

初版は configure argv の共通部分が既存 probe の `COMMON` と同一で、
差は `-DCCBENCH_TRACE` だけだと書いた。**実測では compiler の渡し方も異なる。**
既存 probe は `$(command -v gcc)` を渡し、`a08` は realpath 済み絶対 path を要求する。
計算ノードでも `command -v` = `/bin/gcc`、realpath = `/usr/bin/x86_64-linux-gnu-gcc-11` で
**両者は異なる文字列**である。exact argv validator はこれを別 token として扱う。

→ 差が 2 点あることを明記し、realpath 側を採る理由 (alternatives 切替の検出) を書いた。

---

## 3. 裁定を求める問い

### Q1. 再発行版の追補 A を凍結してよいか

**推奨: 承認して段階 2 (文書発効済み / 機械 gate 未実装 / pilot 投入不可) へ進める。**

13 field のうち probe で変わったのは `a03` の**支持測定の追記**と `a08` の**期待値追記**だけで、
`a03` の許容範囲そのものは初版から不変である。R4 (a) が要求した 3 測定はすべて取得した。

- (a) 4 本まとめて承認し、段階 2 へ進める **(推奨)**
- (b) `a04` / `a08` の訂正だけ先に承認し、`a03` は追加 probe の後にする
- (c) 承認しない (追加の実測を求める)

### Q2. 3 arm × `TRACE=1` の witness を追加で取るか

**事実。** 今回の witness は **`stock` 1 arm だけ**である。`mode1` / `modeX` は patch を当てた枝で、
mode macro と trace 実装の相互作用でそれらだけが compile failure になる可能性は排除していない。
検証割当ては 3 arm すべての trace-enabled build を要求する。

- **(a) 現状のまま進め、3 arm の成立は検証割当ての本番で確かめる (推奨)。**
  probe は `DW-G01` の最安の生死確認であり、base witness が取れた時点で目的を果たした。
  失敗した場合の損失は検証割当て 1 本である。
- (b) probe をもう 1 本走らせて 3 arm × `TRACE=1` を確かめる。
  → 割当て 1 本を先払いして、検証割当ての失敗リスクを消す。

### Q3. 単一割当ての記述的結果で `a03` の feasibility を締めてよいか

**事実。** `feasible` は単一ノード・単一割当て・単一時刻の**相関した 13 窓**の記述的結果である。
割当て間変動の観測は 0 点で、本走の 3 arm・36 run (30 秒 gap 24 個 / 60 秒 gap 11 個) の
履歴も再現していない。これは `a12` が抱える欠陥と同型である。

ただし**実測の余裕は大きい** — 最大 `0.0791` に対し上限 `1.0` で、12 倍以上の margin がある。

- **(a) 現状の限定つき記述で締める (推奨)。**
  追補 A に「主張しないこと」を逐語で書いてある。margin が大きいので、
  複数割当てを取っても結論が変わる見込みが薄い。
- (b) 独立な複数割当てで上側許容限界を構成する。
  → 統計的に正しいが、割当てを追加消費し pilot が遠のく。

### Q4. probe の再走規律の限界を受け入れるか

**事実。** 「窓を 1 つでも観測した attempt は terminal、再走 0 回」を凍結し、
job body が namespace の既存 attempt を走査して拒否する形で機械強制した。
**限界**: scheduler 証拠つきの pre-submit ledger ではないので、namespace ごと破棄する経路と、
まだ観測行を publish していない同時 submit は防げない。

本 wave の実績: attempt 1 は**窓 0 件**で終わった (自作 validator の bug) ため再投入し、
attempt 2 で 13 窓を観測した。**不都合な観測を捨てて選び直した事実はない。**

- **(a) 現状の限界を受け入れる (推奨)。** 完全な機械強制には submit surface の追加が要る。
- (b) pre-submit ledger と submit wrapper を producer 実装 wave の scope に加える。

### Q5. group-TERM の signal identity が受領証に残らない限界を受け入れるか

**事実。** driver が group-TERM を受けたとき、受領証が段失敗コードとして記録することがある。
bash が複合文中の pending trap を遅延させ、子の死が `wait` を正常復帰させるためで、
**fix を 6 巡費やしても閉じなかった。**測定と中断検出には影響しない
(`COMPLETED` marker の規律で中断は確実に検出でき、その経路はテストで固定済み)。

- **(a) 限界として記録したまま進める (推奨)。** 受領証に
  `signal_identity_best_effort: true` と限界文を残してある。
- (b) driver を Python の単一 process へ書き直す (shell の trap 意味論から降りる)。

---

## 4. 本 wave が実装しなかったこと (scope 外の real 所見)

裁定パッケージ候補として返す。いずれも敵対検証が real と認めたが、本 wave の scope 外である。

- 複数割当てによる `a03` の上側許容限界の構成 (Q3 (b) と同じ)。
- pilot consumer が probe raw を hard reject する consumer 契約
  (現状は namespace 分離と `study_eligible=false` の付与まで。事故防止であって拒否ではない)。
- producer の `attempts[].environment_observations[]` と probe 受領証の byte 契約の統一。
- 受領証 → 再発行追補の値一致を機械照合する checker
  (現状は親が手で転記。`a03` の観測値と compiler digest が対象)。

---

## 5. 凍結の段階 (再掲)

| 段階 | 状態名 | 現在地 |
|---|---|---|
| 1 | 追補 A 案・erratum 案・schema 案 = **承認待ち** | **← 本 wave の終端** |
| 2 | 文書発効済み / 機械 gate 未実装 / **pilot 投入不可** | 承認 + fold の後 |
| 3 | producer・resolver・validator・consumer の実装と受入の後だけ **投入 gate 有効** | producer 実装 wave の後 |

**本 wave も段階 1 で終わる。**
