# 段 4 裁定 — land の fold 署名検査

**裁定: 実装する。ただし scope を land CLI 経路の最小修正へ絞る。**
段 2 案 (三 tree 免除) と親案 (累積差分) はどちらも不採用。

## 所見の real / refuted

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| plan | 親案 (累積差分) は `landed_main_sha` が post-fold HEAD で範囲端が誤り、正しい端に直しても hidden fold 後の tree 復元を見逃す | **real** | 親案を撤回 |
| B-1 | 三 tree 免除は **path 単位**なので、protected 2 path を main 親から、canonical 台帳を wave 親から採る merge を免除する | **real / blocker** | 三 tree 案を不採用 |
| A2-1 | 署名 2 条件は lock 外 fold の十分条件でない (canonical-only、`T` gitlink、同一 commit 内 A→D 復元を受理) | **real** | **scope 外 → ユーザー裁定へ** |
| A2-3 | checker / daemon は receipt の**初期** `base_main_sha` に束縛され、tested main cutoff ではない。schema 変更なしでは正規 merge を通せない | **real** | **scope 外 → ユーザー裁定へ** (本 wave は land CLI 経路のみ) |
| A2-7 | 三 tree は commit × parent × key × 候補で git subprocess が増え、共有 30 秒 deadline で正規履歴を timeout 拒否しうる | **real** | 三 tree 案を不採用する追加根拠 |
| B-2 | consumer (checker/daemon) の受理変更を識別するテストがない | **real** | 採用 — 実装子に現況の実測報告を義務づける |
| B-3 | `merge-base --all` の rc=1 契約が欠落 | **real** | 採用 (新経路を使うなら) |
| B/A2 | bootstrap 循環 (旧 helper でしか land できない) は存在しない。helper は自分の checkout の `git_state` を import する | **refuted** | — |
| B | main を取り込むたびに tip と audited closure が変わるので受入・監査を再確認する必要がある | **real** | 採用 — 手順として明記 |

## 採用する設計 (plan v2)

**規則**: 署名判定の差分相手を「その commit が **trusted main cutoff の外側で加えた変更**」に限定する。

1. `commit-diff` から `-m` を外す (merge commit は既定で差分を出さない)。
2. 各 landed commit `C` について:
   - parent が 0 or 1 → 現行どおり `C` の差分全体を署名判定にかける (`--root` 維持)。
   - parent が 2 以上 → parent のうち **tested main cutoff の祖先であるもの**を数える。
     - ちょうど 1 つ (`P`) なら、`diff-tree P C` **だけ**を署名判定にかける。
     - 0 個または 2 個以上なら、**全 parent との差分**を署名判定にかける (fail-closed、現行と同じ強さ)。
3. tested main cutoff は land CLI が持つ `tested_main_sha`。`verify_declared_fold_commit` へ
   新しい keyword で明示的に渡す。**渡されない呼び出し経路は現行挙動 (全 parent 走査) を保つ。**

**根拠**: ff-only で main に載るのは「wave が trusted main の上に加えたもの」だけである。
`diff(P, C)` はまさにそれを表す。main 自身の既 land 履歴が wave 側 parent との差分として
再び現れる現象 (本欠陥) は、この定義では原理的に起きない。

**この規則が現行より弱くなる点 (明示)**: merge で「wave が自分で追加した fragment を落とす」
操作が検出されなくなる。これは wave 自身の記録が失われるだけで採番の偽造ではなく、
かつ A2-1 が示した既存の canonical-only 穴の内側にある。**穴を広げない**が塞ぎもしない。

## 不変条件 (実装子への拘束)
1. 署名 2 条件の意味を変えない。path 集合を狭めない。
2. `test_n31_landed_interval_cannot_hide_an_earlier_fold` は**置換せず現行のまま残す**
   (A2 の指摘。net-zero の新例を純増させる)。
3. 既存の拒否テストを 1 本も緩めない。期待値の反転・skip・削除を禁じる。
4. cutoff を渡さない呼び出し経路の受理集合を変えない。
5. octopus (parent 3 以上) は trusted parent が 1 つに定まらない限り fail-closed。
6. `merge-base` / `rev-list --parents` を新設するなら rc≠0 と複数解を fail-closed で扱う。

## 変異事前登録 (`DW-M01`)
実装後に old 逐語を固定する。各変異は「手前に同じ入力を拒否する検査がない」ことを確認してから登録する。

1. trusted parent の判定 (`ancestor` 検査) を恒真化 → 任意の parent が trusted になり、
   merge で fragment を落とす負例が緑になる。
2. trusted parent が 0 個のときの fail-closed 分岐を「素通り」へ変異 → 非 main merge の負例が緑。
3. trusted parent が 2 個以上のときの fail-closed 分岐を「先頭を採用」へ変異 → octopus 負例が緑。
4. cutoff 未指定時に「全 parent 走査」へ落とす既定を「素通り」へ変異 → 既存 consumer の負例が緑。
5. `-m` 削除後、非 merge commit の走査を落とす変異 → 既存の fragment 削除・FOLDED 変更負例が緑。
6. `diff-tree P C` の引数順を入れ替える変異 → D と A が反転し、fragment 削除負例が緑。
7. `merge-base` の複数解 fail-closed を「先頭採用」へ変異 → 該当負例が緑。
8. 正例 (main 取り込み merge を含む landed 区間) を拒否する側へ倒す変異 → 正例が赤 (過剰拒否の検出)。

## 新設する正例 (F82 の再発検知が要求)
- **正例**: main が fold を含めて進み、wave がそれを 2-parent merge で取り込んだ landed 区間が受理される。
  **この正例は現行実装で赤になることを実装子が確認する** (純増検出力の証明)。
- **負例**: 同じ形の merge で、wave が merge resolution により (i) main に存在する fragment を削除する、
  (ii) `FOLDED.md` を main と異なる内容にする → いずれも拒否される。
- **負例**: trusted parent が存在しない merge (wave 内 branch 同士) に署名がある → 拒否される。

## scope 外 → ユーザー裁定パッケージ
1. **署名 2 条件の不完全性** (A2-1)。canonical-only・`T` gitlink・同一 commit 内復元を受理する。
   閉じるには fold transaction の意味検証 (FoldPlan の delta 保存または決定的 replay) が要り、
   「legacy wave が canonical を直接編集する」現行契約 (F82 が記録) と衝突する。
2. **checker / daemon の cutoff** (A2-3)。receipt へ tested main cutoff を別 field で永続化・
   binding する schema 変更が要る。本 wave では land CLI 経路のみ直し、
   supervised runner 経路は**現状のまま (正規 merge を拒否する)** で残る。

## 手順 (B の指摘への対応)
- main を都度取り込む。取り込むたびに tip と audited closure が変わるため、
  **land 直前に受入を再走**し、監査 commit 列を取り直す。
- 前 wave branch の land 可能性は**実 main 上で確認する** (それが目的そのものであるため)。
  本 wave が land すると main が動くので、前 wave 側は再 merge → 再受入 → land の順になる。

## 分割
段 5 は単一 Codex 実装単位。編集面 = `tools/dev_waves/git_state.py`、
`orchestrator/tests/test_dev_waves_git_state.py`、および cutoff を渡す
`tools/dev_wave_land.py` の呼び出し 2 箇所。
