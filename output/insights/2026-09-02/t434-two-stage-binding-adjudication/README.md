# 2026-09-02 [T-434] D1407 の二段束縛は実装できるか — 実装差分は小さいが順序が塞がっている

```
status: ADJUDICATED
machine_effect: NONE        # 実装面の差分ゼロ。機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変
```

D1407 (二段束縛の topology 確定) を受けて実装を試みた wave の記録。**実装しないと裁定した。**
ただし先行 wave (`2026-09-01_t434-cap-lift-receipt-v3`) と同じ結論の繰り返しではない。
本 wave が新しく確定したのは「**実装差分は当初の見積りよりはるかに小さいが、順序が塞がっている**」
ことと、その順序の持ち主である。

## 結論

`A` の topology を検査する cap-lift 固有の部品を**単体で land しない**。理由は独立に 4 本。

1. **D1407 §1・§3 に正面から反する** — §1 は「内容 commit `G` が実装一式を導入する」、
   §3 は「`G` と `A` は同一 land transaction」。部品を先に land すると、後の `G` は
   「実装一式を導入する commit」ではなくなる。
2. **D1407 の却下選択肢と同じ欠陥型** — 「到達不能と承知で受領証の入口だけを land する」。
   提案部品は受領証を parse しないので字義上の該当ではないが、**呼び手が無く一度も評価されない**
   点で同型である。
3. **DW-G04 を満たせない** — 発火条件を満たす既存 artifact path も計測 ID も 1 件も書けない。
   識別子検索ではなく性質で全件確認した。
4. **D841 (ユーザー裁定) の positive control 要求を満たさない** — 受領証と consumer 結線を
   伴わない部品を T-434 の実装成果として数えられない。

## 本 wave が新しく確定したこと

### 1. 実装差分は小さい — D1407 が `A` に要求する述語はすべて既存機構にある

| D1407 が `A` に要求すること | 既存実装 |
|---|---|
| 非 merge かつ親集合が exact `{G}` | `orchestrator/campaign/trial_registry.py:1243` `assert_effective_commit_exact_parent` |
| 追加 path が exact で他 status ゼロ | `orchestrator/campaign/s8b_ratified_freeze.py:607` `_added_paths` + `:1273` `_verify_pairing` |
| `AI-Agent: none` を逐語ちょうど 1 本 | 同 `:546` `_is_none_commit` (raw 行 byte 一致 + parse 値 exact の二重判定) |
| `G != A` | 同 `:1284` |

さらに **exact-parent 側の負例は既に実 git で網羅済み**である
(`orchestrator/tests/test_trial_registry.py` の同関数を呼ぶ 9 箇所が root・別親・merge・
非 canonical 引数・parent query 失敗・graft file・replace ref・measurement HEAD 祖先要求を覆う)。
正例も stub 無しで書ける (`orchestrator/tests/test_s8b_ratified_freeze.py` の
`_commit` / `_commit_raw` / `_commit_verbatim` / `_commit_exact`)。

**独立述語は 4 つでなく 3 群である。** 親集合 exact `{G}` は非 merge を論理的に含む。

### 2. 塞いでいるのは順序であり、その持ち主は [T-941] P6 実装 wave である

`docs/phase3.md:1118` が「機械実装は [T-941] P6 実装 wave の所有」と明記し、T-941 は起票以来
未実施 (`docs/archive/worklog-phase3-0812-489.md:649`)。T-434 は T-941 に順序依存する。
あわせて T-942 の V-11「**P6 の実装と認定をどの wave が所有するか**」が同 `:654` で
ユーザー裁定待ちのまま残っている — D156 と phase3.md は既に T-941 の所有と書いているので、
これは済んでいる可能性が高い停止項である。

### 3. 素朴な実装が踏む欠陥を 5 件、実装前に確定した

- **R1** 追加 path 集合を `{認定記録, 受領証}` と集合比較すると、2 引数が同一のとき 1 path へ縮退して通る。
- **R2** `_added_paths` は status `A` しか見ないため、追加された 2 件が symlink や gitlink でも通る。
  literal regular blob の確認が無い (先例は `orchestrator/campaign/s8c_acceptance_receipt.py:658`)。
- **R3** 末尾空白付き `AI-Agent: none ` の負例は通常の commit helper では作れない。
  git の既定 cleanup が末尾空白を落とすため `--cleanup=verbatim` が要る。
- **R4** `trial_registry` 系と `s8b` 系の git 呼出しは同じ repository・graph を見ていない
  (環境 allowlist と config 無効化の有無が違う)。素朴に合成すると別 graph を混ぜうる。
- **R5** commit の形だけでは発効を証明できない。`A` の発見、`A` が pinned HEAD の祖先であること、
  `A` の 2 blob と HEAD blob の一致が要る。exact `G` の直子だが main から到達しない
  dangling `A` が通ってしまう (先例は `orchestrator/campaign/trial_registry.py:1499`)。

### 4. 冗長 gate を 2 件、実測で除外した

段 2 プランは負例表に「rename 検出時: `R`」を挙げたが、**既存 `_added_paths` は `-M` を渡さないため
`R` は出ない。** 親が repo 外の使い捨て repo で、段 3 のレンズが repo 内の実 rename commit で
独立に実測し、どちらも `A` + `D` になった。`diff.renames=true` を `-c` でも repo config でも
与えても変わらない (plumbing の `diff-tree` は config で rename 検出に切り替わらない)。

- **rename 負例は削除負例と同じ理由に退化する。** 別枠で登録すると独立 gate 数を過大表示する。
- **mode 変更のみの負例も内容変更と同じ `M`** で、独立 gate ではない。
- `_added_paths` へ `--no-renames` を足す必要も無い。

### 5. 訂正した 2 つの言明

- **`AI-Agent: none` は人間性の機械的証明ではなく自己申告である。** 親 brief は
  「`A` は人間の commit であり AI は作れない」と書いたが機械的には偽で、
  `_is_none_commit` は message の raw 行と trailer parse しか見ない。
  正確には「AI が書いてはならない (provenance 規律)。機械的に防いではいない」。
  結論は変わらない — 本 wave が `A` を作ることはできない。
- **`reflux_formal_consumer` は「無条件停止」ではない。** 前段の条件が失敗すれば
  `FormalContractRejected` になり、**全前段を通過したときだけ** `P6Unavailable` になる。
  親 brief が先行設計の表現を引き写した誤りである。

## ユーザーへ返す裁定パッケージ

親は代行しない。詳細は `s4-adjudication.md` の裁定 5。

- **U1** [T-941] P6 実装 wave を起動するか。あわせて T-942 の V-11 (P6 の実装と認定の所有) は
  済んでいるか — 済なら閉じ、未済なら所有を確定してほしい。
- **U2** D1407 の `G` は単一の導入 commit か、累積 tree の tip か。§1 は単数で「導入する」と
  書くが、実装一式は 1 回の差分に収まらない規模である。段 2 と両レンズが独立にこの曖昧さを指摘した。
  **現裁定からは前者しか導けない。**
- **U3** レンズ A が指摘した s8b の Git trust boundary 共通化 (R4) を別タスクとして起票するか。
  今日の production 経路から発火する実在の差分だが、本題ではなく防御的堅牢化なので
  本 wave では scope 外とした。

## file

| file | 中身 |
|---|---|
| `brief.md` | 段 1 brief (親の scope・不変条件・実アンカー表) |
| `parent-measurements.md` | 親が独立に取った実測 6 件 (既存機構の棚卸し、diff-tree の実測、行番号検算、既存被覆、T-941 特定、自己訂正) |
| `s4-adjudication.md` | 段 4 裁定の全文 |
| `verbatim/s2-plan.md` | 段 2 プランの逐語 |
| `verbatim/s3-lensA.md` | 段 3 レンズ A (正しさ境界と既裁定整合) の逐語 |
| `verbatim/s3-lensB.md` | 段 3 レンズ B (実効性・正例と負例の本物性) の逐語 |

先行する設計と裁定は `output/insights/2026-09-01_t434-cap-lift-receipt-v3/` と
`output/insights/2026-09-01_t434-topology-ruling/` を参照する。
