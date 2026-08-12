# [T-816] 手順 4 — trace v2 専用化と ccbench pin 前進 (実装 wave)

```text
wave: dev-wave-t816-step4-impl / branch worktree-dev-wave-t816-step4-impl
起点 main: a70a5acd
上位裁定: 2026-08-12 /rulings 一括裁定 (粗い provenance 基準。decisions への採番は rulings wave 所有)
前 wave (段 4 で停止): output/insights/2026-08-12_t816-step4-blockers/
```

## 何をしたか

1. **trace を v2 専用にした。** `C` は exact 7-field (read/write 件数つき)、txn 終端の `E` を必須。
   5-field の v1 は専用 `ParseError`。**互換分岐も hash 束縛の legacy 例外も作っていない** (裁定どおり)。
2. **framing integrity を足した。** `count-mismatch` / `missing-end` / `duplicate-end` の 3 種を
   構造化して数え、`Integrity.framing_violations` を `clean()` と report の JSON/text、
   silo-ladder の acceptance と exact key-set、t152 の counter mirror まで通した。
3. **既存の穴を 2 つ塞いだ。**
   - 負の txid が `expected = max(txid)+1` の欠番計算を相殺して `certified` になりうる穴
     (v2 化とは独立に v1 parser でも成立していた)。
   - record 種別を**先頭 1 文字**で判定していたため `End 0` が正規の `E 0` として、
     `Commit …` が `C …` として受理されていた fail-open (段 6 レビュー A が発見)。
4. **gitlink を `d706650` → `511c9538` へ前進**し、現用 pin 23 箇所と `patches/ledger.json` の
   base commit を追随させた。歴史 preimage・固定 fixture・凍結 golden は据置。
5. **凍結 v1 証拠の再検証を退役した。** bytes は 1 bit も変えていない。

## 実測 (すべて本 wave、Pegasus login + 計算ノード dispatch)

| 事実 | 値 |
|---|---|
| TRACE=0 正規化 preprocess 同一性 (g++-12) | **pass** / 16 context すべて identical (`identity-g++-12.log`) |
| submodule 差分 | `cc/silo/transaction.cc` 1 file / +14 -1 |
| gitlink + 承認定数だけの赤 (着手前) | `10 failed, 78 passed, 1 error` — 全 10 件 `test_s8a_trigger_sweep.py` |
| 統合直後 (gitlink 未 commit) | `26 failed, 801 passed, 10 skipped, 1 error` |
| gitlink commit 後 | `13 failed, 814 passed, 10 skipped, 1 error` |
| fix 第 1 巡後 | `2 failed, 826 passed, 10 skipped, 1 error` |
| **fix 第 2 巡後 (最終)** | **`828 passed, 10 skipped, 1 error`** (焦点 16 file) |
| 変異 (spec-a、8 件) | **KILLED 6 / MISMATCH 2 / SURVIVED 0** |
| 変異 (spec-b、再登録 2 件) | **KILLED 2 / MISMATCH 0 / SURVIVED 0** |

**1 error は偽赤である。** `test_s8b_approved.py` の収集失敗 (`No module named 'tests'`) で、
単一ファイル選択走で import path が確立しないために起きる (DW-O18、前 wave も同じものを観測)。
`sys.path` に `orchestrator/` を入れれば `tests.skiputil` は正常に import できることを確認した。
権威はディレクトリ全体を走る受入全走である。

## 親の裁定を 1 件撤回した (段 6 レビュー B)

段 4 で親は「校正・凍結 artifact のうち**生きた driver が verify するもの**は現用だから機械再 pin」と
裁定した (`verbatim/s4-ruling-plan-v2.md` の R1、provisional と明記)。**これは逆だった。**

- `s8b_oracle_driver.py:208` は `sha256(known_axes_freeze.json の実 bytes)` が
  `t080_migration.KNOWN_AXES_RAW_SHA256` (**旧 bytes**) と一致することを要求する。
  再 pin すると 8b oracle が即座に拒否する。同じ bytes は `output/s8b-freeze/holdout_freeze.json` と
  `measurement_freeze.json` の `implementation_hashes` にも byte SHA で束縛されており、
  閉包を追うと凍結 holdout / seal の書き換えに波及する (触ってはいけない側)。
- `s8a_trigger_freq_t48.json` は **TRACE=1 で採った値**なので、TRACE=0 同一性証拠は適用できない。
  さらに現物は `build_admissions` field を持たないため、`load_effective_reasons()` は
  **本 wave 以前から静的に fail-closed** である (= 実 artifact は既に未使用)。

→ **3 件とも旧 pin のまま据置 (退役)。** 前進を維持するのは `patches/ledger.json` の base commit と
コード・テスト側の現用 pin だけである。

**誤りの機序**: 「生きた consumer が居る」ことだけで現用と判定し、**その consumer が何を要求して
いるか**を読まなかった。consumer は新しい pin ではなく旧 bytes を要求していた。

## 受入全走で出た構造的 blocker (本 wave は land していない)

焦点走が緑になった後の**受入全走は `44 failed, 9357 passed, 31 skipped`** だった。

| 系統 | 件数 | 内容 | 処置 |
|---|---:|---|---|
| A | 12 | pin 由来の campaign identity golden 11 件 + 段 2 の A/B 分類を 1 件誤って据置にした fixture pin 1 件 | 本 wave で修正済み (`44 failed` → `32 failed` を実測) |
| B | **32** | `s1_known_axes_freeze.verify()` が `ccbench_pin` を**submodule の現 HEAD**と比較するため、gitlink を進める限り通らない。T-080 移行受領証 → holdout freeze → 8b oracle → 床値 protocol の連鎖が fail-closed になる | **ユーザー裁定待ち** |

**焦点走の範囲が狭すぎたことが、この発見を最後まで遅らせた。** 前 wave は 5 file、本 wave の
焦点走も 16 file しか測っておらず、`test_s8b_oracle_driver.py` / `test_s8b_holdout_freeze.py` /
`test_autonomous_trial_completeness.py` が入っていなかった。前 wave の記録にある
「S1 freeze の破れは受入では検出されない」は**誤り**である。

裁定パッケージ =
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t816-step4-freeze-chain-blocks-pin-advance.md`
(択一 4 つ、親推奨 = 凍結チェーンの機械的再発行。根拠 = TRACE=0 同一性の機械証明)。

## 退役の帰結 (上記 B に吸収された)

pin を前進させた結果、S1 freeze 族 (`known_axes_freeze.json` / `measurement_freeze.json`) は
記録された pin と現行 pin が食い違う状態になった。`s1_measurement_freeze.verify()` と
`s1_known_axes_freeze.verify()` は実行時に pin 不一致で拒否する。
**受入全走では検出されない** (検査は実 artifact を読まない) が、`s1_report` と 8b oracle を
新 pin で走らせると refusal が出る。再発行 (再測定) するか、旧 pin で走らせるかは裁定が要る。

## 変異が示したこと

- v1 の C 行を再び受理させる / 宣言件数の照合を殺す / `E` 欠落・重複の記録を落とす /
  負 txid 検査を外す / framing を clean 判定から外す / record 種別を再び先頭 1 文字で判定させる —
  **6 種すべてが赤で捕まった。**
- 受理集合を縮小する wave の必須正例 (`0 0` frame を過剰拒否させる変異) も捕まった。
- 段 4 で登録した M1 (v1 受理) と M8 (校正 pin gate) は、レビュー A が「単一理由が成立しない」と
  指摘した。M1 は 1 箇所の置換で受理集合が実際に広がる形へ作り直し、M8 は**登録を取り下げた**
  (成功 fixture が常に現行 pin を持つため、gate を fail-open にしても挙動が変わらない)。
- MISMATCH 2 件は「検出はされたが落ちるテストが予想より広い」型だった。初回結果は
  `mutation-ledger-a.json` に残し、実測の完全集合で再登録した確認走を
  `mutation-ledger-b.json` に置いた。

## 逐語

`verbatim/` に段 4 裁定 + plan v2、段 5 実装子 2 本、段 6 敵対レビュー 2 本、fix 2 巡を凍結した。
