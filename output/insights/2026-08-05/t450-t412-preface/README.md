# [T-450] + [T-412] 前置 — DW-O15 削除と deletion preflight の fail-closed 化、および剪定再裁定パッケージ

- 日付: 2026-08-05
- branch: `worktree-dev-wave-t450-t412-preface`
- 種別: コード + docs
- 裁定の出所: worklog archive (184) [T-454]「前置 2 件をまず実行し、その後テスト化 pass を 1 wave」
- 素材 (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t450-t412-preface/`
  (brief、plan、敵対レンズ 4 本、実装子 2 本、fix、焦点再レビュー、変異 spec と結果)

---

## 0. 結論 (先に読む)

1. **[T-450] は完了した。** `DW-O15` (55 bytes の残骸) を `docs/dev-wave/operations.md` から削除し、
   入口の条件 15 は `DW-M07` 単独で残した。`tools/check_docs.py` の `_OPERATION_NUMBERS` と
   literal pin も追随させた。復活には新規裁定が要る旨を `DW-O07` と同じ形でコメントに残した
2. **[T-412] 前置は「runner-local な fail-closed 化」まで完了した。** bypass 環境変数を全廃し、
   git 検査不能も受入形では停止するようにした
3. **しかし [T-412] の剪定は 0 bytes である。** `DW-O11` は削除できない。
   残余義務は機械化しきれないと、段 3 の敵対レンズ 2 本が独立に示した (§2)
4. したがって **[T-287] §5 (a) の必要枠 270 bytes は、[T-450] が空けた 55 bytes だけでは
   依然として満たされない。** 残りの筋は [T-454] のテスト化 pass に移る

## 1. 何を実装したか

| 面 | 変更 |
|---|---|
| `tools/run_tests.py` | `IZANAGI_TEST_ALLOW_UNSTAGED_DELETIONS` の定数と全 bypass 分岐を削除。`_deletion_git_failure` を trigger 非依存の rc=13 に。診断は stage と復元の両方を案内 |
| `tools/pegasus/dispatch_compute.py` | tests task の env allowlist から同 key を削除 |
| `tools/check_docs.py` | `_OPERATION_NUMBERS` から 15 を除外。条件 15 は `DW-M07` 単独の明示代入 |
| `docs/dev-wave/operations.md` | `DW-O15` 節を削除。`DW-O11` を実挙動へ是正 (223 bytes) |
| `.claude/commands/dev-wave.md` | 条件 15 行と段 5 / 段 6 の範囲表記 |
| テスト | 既存 4 本を fail-closed 期待へ追随。非参照 pin を 4 経路へ。過剰拒否の正例 2 本。transport 1 本 |

`_is_acceptance_run` は変更していない。targeted run は従来どおり gate の外にある。

## 2. なぜ `DW-O11` を剪定できないか (段 3 の敵対レンズ 2 本が独立に到達)

1. **受入形の判定は argv の構文的な代理でしかない。** `PYTEST_ADDOPTS` が非空だと
   `_is_acceptance_run` は偽になるが、pytest は既定 target 全体を走る。すなわち
   「gate を通らない全走」を作れる。`IZANAGI_TEST_TRIGGER=final` を足してもこの判定は変わらない
2. **受入結果と landed tip を結ぶ receipt が無い。** `tools/dev_wave_land.py` は冒頭で
   「tested SHA / audited commit 列を受入証明とはみなさない」と自ら明記している。
   規律違反の caller を land が拒否できない
3. **「stage が緑への唯一経路」は偽。** 意図しない削除を**復元**しても次回 preflight は rc=0 になる。
   これは正当な経路でもあるので、親の当初の前提 (P1) は反証された
4. **`git rm --cached` は gate をすり抜ける。** index から消えて worktree に残るため
   `git ls-files --deleted` は空になり、測った tree と commit する tree が食い違う
5. **preflight 後 pytest 起動前の TOCTOU** が残る

## 3. 剪定再裁定パッケージ (ユーザー裁定へ)

### R1 — 明示 acceptance mode + 受入 receipt + land 消費

`DW-O11` 第 2 文を機械化するには、(a) argv 形状の代理をやめた明示的な acceptance mode、
(b) 受入コマンド・rc・tip SHA・index/worktree fingerprint を束ねた機械可読 receipt、
(c) それを land / 記録側が消費する配線、の 3 つが要る。

| 択 | 内容 | 備考 |
|---|---|---|
| (i) | 3 点を 1 wave で一体導入する | 受理集合を大きく変える。段 2/3 の攻撃を新規に要する |
| (ii) | (a)(b) を先に入れ、(c) の land 結線は次段へ | receipt が孤児になる期間が生じる |
| (iii) | 見送り、`DW-O11` 第 2 文を prose のまま維持する | **親の推奨。** 現状の実害は観測されておらず、費用が大きい |

### R2 — `git rm --cached` の乖離と post-preflight TOCTOU

| 択 | 内容 | 備考 |
|---|---|---|
| (i) | cached-delete path が worktree に実在しないことを検査し、テスト前後で index/worktree fingerprint を照合する | 実装は中規模 |
| (ii) | 固定 index/tree から隔離 checkout を作って受入を走らせる | 最も強いが遅い |
| (iii) | 未機械化残余として記録し、剪定判定から除外する | **親の推奨** |

### R3 — 計算ノード子の environment から legacy key を排除する

`tools/pegasus/dispatch_compute.py` の `_job_run` は、request の `environment` を allowlist で
再検査せずに `child_env.update()` する。親側 allowlist から key を外しても、既存 request と
ambient environment の経路は残る。**現行 `run_tests.py` に reader が無いため成果物影響はゼロ**だが、
dead capability の transport は残る。

| 択 | 内容 | 備考 |
|---|---|---|
| (a) | 未知 key を含む request を **reject** する | fail-closed だが、submit 後に repo_root の code が更新された窓で稼働中 job を落としうる |
| (b) | 未知 key を **drop (scrub)** して起動する | **親の推奨。** 移行安全で transport は止まる。ただし「拒否でなく黙って落とす」の是非は要裁定 |
| (c) | 現状維持 | reader 復活時に静かに効いてしまう |

### R4 — bypass 全廃に伴う探索用途の非互換 (記録のみ、裁定不要)

stage 前に全走で collection/import 破断を見る用途は、`git add -A` を挟む形に変わる。
`git reset` で戻せるため運用上の損失は小さいと裁定した。ただし段 3 のレンズ A が指摘したとおり、
これは利用者を `PYTEST_ADDOPTS` 経路 (§2-1) へ誘導する誘因になる。R1 を要求する根拠の 1 つ。

## 4. 変異 matrix

`tools/mutation_harness.py` / `DW-M05` / `DW-M07` に従い、統合 commit 後に本走した。
**12 変異すべて KILLED、SURVIVED 0。**

| ID | 何を壊すか | 結果 |
|---|---|---|
| A-M1 | 入口の条件 15 から `DW-M07` の指名を削る | KILLED |
| A-M2 | 入口の条件 15 へ `DW-O15` を再追加 | KILLED |
| A-M3 | 入口 段 5 の範囲表記を旧形へ戻す | KILLED |
| A-M4 | 入口 段 6 の範囲表記を旧形へ戻す | KILLED |
| A-M5 | `_OPERATION_NUMBERS` へ 15 を戻す | KILLED |
| B-M1 | bypass の `return 0` を preflight へ再注入 (`"1"`) | KILLED |
| B-M6 | 同上を**未列挙の綴り** `"yes"` で再注入 | KILLED |
| B-M7 | `_deletion_git_failure` 冒頭へ legacy env の読み取りを再注入 | KILLED |
| B-M2 | `_deletion_git_failure` の rc=13 を 0 に (冗長層 pin) | KILLED |
| B-M3 | targeted early return を無効化 (過剰拒否の正例) | KILLED |
| B-M4 | `if not deleted: return 0` を無効化 (正例) | KILLED |
| B-M5 | dispatch の env allowlist へ legacy key を戻す | KILLED |

**B-M6 と B-M7 が本 wave の要点である。** 有限 spelling を列挙するだけのテストでは
両方とも生存する。「preflight が当該 key を一度も参照しない」ことを行動レベルで固定した
検査だけがこれらを殺す。B-M7 は段 6 レビュー C2 が指摘した穴そのもので、fix 前なら生存した。

**erratum (`DW-M02`): 初回走行の結果を消さない。** 初回 (`mutation-ledger.json`) は
12/12 検出・SURVIVED 0 だったが、4 件 (A-M5 / B-M1 / B-M2 / B-M4) が `MISMATCH` になった。
いずれも**事前登録した期待 node が実 node の真部分集合**で、取りこぼしではなく
「予想より多くの node が赤くなった」ケースである。特に A-M5 は `_OPERATION_NUMBERS` から
fixture が導出される自己整合面のため 162 node が赤くなる。実測に合わせて期待 node を更新した
spec v2 で再走し、12/12 KILLED・MISMATCH 0 を得た (`mutation-ledger-v2.json`)。
更新は観測結果の焼き込みであり、実質的な保証は「両走とも SURVIVED 0」である。

## 5. erratum

- commit `0ccf85ba` の題名は「must-fix 2 件を閉じ」と書いたが、焦点再レビューの判定では
  **C1 は `partial`** である (テスト名の是正であって根本修正ではない)。本文と実装は一致するが、
  題名は過大である。履歴は書き換えず、ここに erratum として残す
- 親の段 4 裁定 §3 は「child env に legacy key が現れないことを固定する transport テスト」と
  書いたが、実 child env の排除 (R3) は本 wave の scope 外である。裁定文の誤りであり、
  段 6 裁定で射程を「親 dispatcher が新規生成する request の `environment` field」へ訂正した
- 段 1 brief の「task-run 台帳 14 件」は **top-level entry 数**であり、task-run directory は 10 件。
  「2026-07-21 以降に新規 task-run が無い」という結論は変わらないが、そこから言えるのは
  利用頻度を評価できないことまでである
- 段 1 brief は `DW-G04` の発火 path を「台帳が空だから書けない」としたが、これは誤り。
  既存の deletion fixture (`orchestrator/tests/test_run_tests_preflight.py` の未 stage 削除 fixture)
  が発火条件を満たす既存 artifact である。台帳を使わない理由は所有 ([T-166]) と設計択一の未整理である

## 6. 段 8 自己改善 — 候補 1 件。実装せず裁定へ (予算の先約)

`docs/skill-self-improvement.md` の発火 gate と routing を適用した。

### 候補 — `DW-S04` に「scope 内外は対で列挙する」を足す

- **実測**: 本 wave の段 4 裁定 §3 は in-scope 側に「child env に legacy key が現れないことを
  固定する transport テスト」と書きながら、scope 外一覧には `_job_run` 側を入れなかった。
  結果、fix 子は名前の是正だけを行い、焦点再レビューが NO-GO を出した。**レビュー 1 巡分の
  往復が実際に無駄になった**
- **行き先**: routing 3 (dev-wave 固有の手順 → 発火段の既存 leaf 節)。`docs/dev-wave/core.md` の
  `DW-S04` へ 1 文 (実測 37 bytes) を足せば統合できる。裁定境界そのものの変更ではなく、
  裁定文の**網羅性**を求める明確化である
- **実装しない理由 (予算の先約)**: 適用後の `docs/dev-wave/**` は 25,181 / 25,200 bytes となり
  機械 gate は通る。しかし本 wave が空けた 55 bytes は、archive (184) の裁定が
  **待ちの 2 件 ((169) の V5 と (181) の `DW-O18` 追記) に充てると明言している**。
  自己改善で先に 37 bytes を消費すると、その裁定を親が黙って上書きすることになる。
  実際に編集して測ってから revert し、`docs/dev-wave/**` は 25,144 bytes に戻した
- **択一**: (a) [T-454] のテスト化 pass が空けた分から入れる (**親の推奨**)、
  (b) 待ちの 2 件より先に入れる、(c) 見送る

**これは (164) の wave と同型の再発である。** そこでも「本 wave の主題 (枠不足) が、同じ wave の
自己改善候補を実際に 1 件塞いだ」と記録されている。今回は枠を空けた側の wave でも同じことが
起きた — 空いた枠に先約があるためである。

**候補にしなかったもの:** 変異 spec の `category` 閉集合 (`negative` / `positive` / `both-layers`) を
docs に書く案は採らない。harness が `category が未知: ...` で fail-fast し、正しい値を
示さないまでも誤りを即座に止める。prose を足すのは機械検査の重複になる。
