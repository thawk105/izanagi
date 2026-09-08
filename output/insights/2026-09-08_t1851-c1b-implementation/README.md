# [T-1851] 単位 C1b — 封印 terminal 証拠を実装し、台帳・profile・起動層・adapter へ結線した

base `8924c0ef3` (継承 tip `b2a3d9ce2` + 健全 local main の merge)。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**
契約の正本は `../2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`、
実装手順は同 dir の `plan-v2.md`。**本 wave はこの 2 文書を書き換えていない。**

## 1. この wave が出した結論

**2 wave 続けて実装 0 行だった C1b が、契約 v3.1 と plan v2 のまま段 5 から実装できた。**
契約の条項で実体化できなかったものは無い。

| commit | 内容 |
|---|---|
| `d03b26773` | 葉 — `s8b_terminal_evidence.py` (production 873 / test 692 行) |
| `d52b2f833` | 統合 — core / profile / 起動層 / adapter (production +1040 / test +1206 行) |
| `2cb24ead5` | fix 1 — 敵対レビュー 2 本の blocker 6 件・must-fix 2 件 |
| `ec5f31aac` | fix 2 — 焦点再レビューの blocker 1 件・must-fix 3 件 |
| `e3d00d62e` | 段 1・4・6 の裁定と全子の逐語 |
| `1c16b8d46` | 受入所要台帳へ 242 node 登録 |
| `ffbba31ba` | 健全 main の取り込みと台帳の和集合合成 |
| `0f06d3499` | fix 3 — 保護対象の三軸漏洩 (F335 再発) |

## 2. 段 1 の実測 — 契約は 38 commit 進んだ main の上でも成立していた

継承 branch は local main より 38 commit 遅れていたが、**契約が指す anchor は 1 つもずれて
いなかった** (profile の event key 組立て位置、起動層と campaign の捕捉集合、台帳 core の
時刻検査、durable claim の identity)。凍結の key 集合は語まで一致し、新識別子の pin も
触る 8 file の file 全体要約値の pin も **0 件**だった。既存 4 test file の関数数も一致した。

**plan の記述を 2 件覆した** (詳細は `s4-adjudication.md` 2 節)。

- 呼出し閉包の「4 / 7 / 3」は caller 数ではなく**出現数**で、実 caller は 2 / 6 / 2 だった。
  結論 (規約を変えるなら全 callable を同じ commit で直す) は不変なので、実装子には
  「数を写さず自分で数え直せ」と渡した。統合が 1 本足した結果、最終的に 2 / 7 / 2 になり、
  レンズ B の独立計数と実装子の報告が全項目一致した。
- 台帳 core の公開 API の consumer は s8b 系の外にも 3 module ある。keyword-only 既定で
  変更不要という見込みを、実装子が現物の file:line で確かめた。

## 3. 段 6 — 3 本のレビューが出した 12 件

正本は `s6-adjudication.md` (1 巡目) と `s6-adjudication-2.md` (2 巡目)。

**敵対レビュー 2 本はどちらも判定 `no`。重複を除いて blocker 6 件・must-fix 2 件。**
**blocker 6 件はすべて 1 つの型に集約した** — 起動層が可変で呼び手所有のオブジェクトを
未信頼の終端 builder へ渡し、その後で権威として読み直していた。

| # | 内容 | 親の裏取り |
|---|---|---|
| R-1 | test seam が real registry への委譲を塞いでいない | 契約 6.2 が名指しした箇所 |
| R-2 | builder の後に予約情報を読み直すため、**分散の閾値を緩めて分散超過を観測成功に見せられる** | **親が file:line で確定。規律 2 に抵触** |
| R-3 | 可変な probe / rep sink を builder へ渡してから権威として再読 | R-2 と同型 |
| R-4 | duck-typed な写像が gate と封印に別の値を返せる | 二重読みの TOCTOU |
| R-5 | 識別 3 欄が実 slot へ再束縛されていない | **親が確定。2 レンズが独立到達** |
| R-6 | capture 失敗と非ゼロ起動失敗数の矛盾を受理 | 契約 1.2 違反 |
| R-7 | 例外名のサブクラスが正規化されず正当な終端を拒否 | **2 レンズが独立到達** |
| R-8 | 観測前競合の正当な枝が終端化前に落ちる | 契約 4.1 枝 1 が到達不能 |

**fix は個別修復でなく 1 つの構造変更へ集約した** — 副作用前に私有の正準 snapshot を作り、
builder には復元した別の木を渡し、封印はその snapshot だけを読む。
設計判断は本 wave の decisions fragment (`docs/spool/decisions/2026-09-08-dev-wave-t1851-unit-a-28.md`) の
「未信頼の値を返す呼び手へ、権威の出所そのものを渡さない」に置いた。

**焦点再レビューが、その fix 自身が入れた穴を 4 件見つけた。**

- 外部証拠の要約値が正準証拠の外にある私有属性で、**発行時にしか照合されない**。証拠 file の
  部品要約値だけを差し替えれば、契約 7 の 11 項目も identity も保ったまま crash 後の再生で
  受理される経路が残っていた。
- 検査より先に JSON 往復させたため厳密型の検査が発火せず、**v2 の受理集合が意図せず広がっていた**。
- **残る 2 件は変異の帰属の問題で、これが最も重要だった。** 変異テストが無条件に送出する偽
  recorder を使っており、対象 gate を外しても後段が必ず拒否する。冗長 gate による見かけの kill で、
  **この状態で変異 matrix を走らせても意味がなかった。**
  設計判断は同 fragment の「変異の帰属を示す fixture は、対象 gate を外したとき
  最後まで通るものにする」に置いた。

## 4. 変異 matrix — probe → 本走 → 最終 commit での再走

台帳は `mutation-probe-out.json` / `mutation-final-out.json` / `mutation-final2-out.json`、
spec は `mutation-probe-spec.json` / `mutation-final-spec.json` (spec 要約値
`b24d2186f44e131e1b1c72a939dc3e031c75eb833b80e8d39150f9efc594b016`)。

**probe は全件 SURVIVED で登録して観測 node を集め、その実測値を期待集合として本走に exact 固定した**
(期待 node を推測で書かないため)。最終 commit `0f06d3499` で anchor を再検証してから再走した。

| 変異 | 狙い | 赤くなった node |
|---|---|---|
| F4a / F4b / F4c | 識別 3 欄の実 slot 束縛を 1 つずつ外す | 各 2 件 (発行側・再生側) |
| F5 | capture 失敗時の起動失敗数 0 検査を無効化 | 2 件 |
| F6 | 例外名正規化からサブクラスの枝を落とす | 4 件 |
| F8 | 再生側の外部証拠再照合を外す | **1 件** |
| F9 | 型検査を正準往復の後ろへ戻す | 2 件 |

**3 回とも baseline PASSED・全件 KILLED・期待 node 完全一致。** 巻き添えの赤も他機構への漏れも無い。
**識別 3 欄の変異がそれぞれ自分の parametrize case だけを落としたことは、3 つの検査が独立していて
1 つの過剰決定 gate になっていないことの証拠である。**

## 5. 受入全走 — 一度止め、main の是正後に 3 attempt で緑にした

**受入待ち手は投入前に local main の先端を merge するが、その先端が壊れていた。**
`.codex/worktrees/` 配下の Codex 子 worktree **110 個が mode 160000 の gitlink として commit**
されており、`.gitmodules` の mapping は 0 件。checkout した木では submodule 操作が必ず失敗する。

**試験 merge を 1 回だけ回して実測したところ、競合も警告も出さずに rc=0 で成功し、110 件が
staged された** (直後に abort、汚染 0 件)。静かに伝播する。

混入は先端 1 commit だけで、1 つ前の `6172ea26b` は 0 件で健全。**汚染を飲んで gate を満たすのは
規律 6 と停止条件の迂回にあたるため、いったん受入全走を止め、健全側を固定 SHA で取り込んだ。**
その間は受入の儀式抜きの全走で回帰を見た (**権威ある受入 receipt ではない**)。

**段 9 に入った時点で別 wave (`dev-wave-research-gate`) が同じ欠陥を独立に検出し `48837186c` で
是正していた**ため、是正後の main を取り込んで受入を投入し直した。

| attempt | 結果 | 判定 |
|---|---|---|
| 1 | rc=70 `child-verdict`、赤 49 件 | 赤は `test_t1259_qsub_env_delivery_probe.py` 1 file に集中。同 file は本 wave の変更 file を 1 つも import しない。**単独走は 51 passed で緑**なので非再現と判定し、規定どおり同一 tip で 1 度だけ再走 |
| 2 | rc=70 `merge-message-provenance` | main がさらに前進し、両親が同じ実装面 (`tools/check_docs.py` と対応 test) を触った。Codex `role=author` の merge message が必要 |
| 3 | **`child-green`** | **22,034 passed / 68 skipped / 0 failed。** receipt は `acceptance-receipt.json`、tested main `efba99a88` / tested tip `1cdafc4c0` |

**競合 0 件は合成の正しさを含意しない**ので、attempt 3 の前に親が staged 合成で
`check_docs` rc=0 / `test_check_docs.py` 572 passed を実測し、**その裏取りを Codex 子に独立検証
させてから** merge message を書かせた。子は `COMMAND_LIMITS` / `COMMAND_INTERFACES` /
`DEV_WAVE_DW_O26_SECTION_LITERAL` / `_SYNTHETIC_DW_O26_SECTION` を名指しして、同じ定数・辞書 key・
登録簿要素の奪い合いが無く両側の変更が残ることを確認した。

## 6. その全走が本 wave 帰属の欠陥を掘り当てた (F335 再発)

葉の新規テストの fixture が保護対象の三軸を同一 file へ揃え、未知性検査に 1 件 hit していた。

| 走行 | 木 | 結果 |
|---|---|---|
| 焦点走 (2 file) | 健全 main | **617 passed / 0 failed** |
| 同じ焦点走 | 本 wave | **41 failed / 576 passed** |

**焦点走はすべて緑で、pin 閉包にも掛からず、敵対レビュー 3 本も検出していない。全走でだけ出た。**
F335 が「焦点走の緑を根拠に汚染なしと判断してはならない」と書いていたとおりだった。
**F335 の恒久対応は存在したが、親の手順に組み込まれておらず発火していなかった。**

是正後、親が repo 全域で走査し `scan-repo-precommit.txt` のとおり
**両保護対象の conjunction hit 0 件・陽性対照 152 hit** を実測した (149.6 秒)。
陽性対照の hit 数を併記するのは、**変更 file だけに絞ると陽性対照が 0 hit になり走査式の発火を
保証できない**ためである。

## 7. 最終状態の実測

- **受入全走 `child-green`: 22,034 passed / 68 skipped / 0 failed** (attempt 3、receipt 発行済み)。
- 受入形でない全走 (attempt 前) は 22,016 passed / 0 failed。
- setup 段の error 17 件は `git ls-files --others` の 30 秒 timeout。単独実測でも同コマンドは
  **13.1 秒** (user 0.023s / sys 0.531s = ほぼ I/O 待ち) かかり、48 worker 下で超過した。
  該当は投入系 fixture のみで、**本 wave の変更 file とは無関係。非帰属**と判定した。
- 親が独立に実走した緑: 所有 5 file **407 件**、consumer 7 file **809 件**、
  漏洩修正後の再検査 **689 件**。
- 受入所要台帳: main 側 19,761 件を byte 一致で保ったまま本 wave の **242 件**を追加
  (削除 0・既存値変更 0 を親が独立に検算)。凍結 8 suite の exact hash 検査も緑。

## 8. 収録物

- `s1-brief.md` — 段 1 brief (anchor の実測表と pin 閉包)
- `s4-adjudication.md` — 段 4 裁定と変異事前登録
- `s6-adjudication.md` / `s6-adjudication-2.md` — 段 6 の 2 巡の裁定
- `mutation-*-spec.json` / `mutation-*-out.json` — 変異 spec と台帳 3 回分
- `scan-repo-precommit.txt` — repo 全域の三軸走査 (陽性対照込み)
- `verbatim/` — 実装子 2 本、敵対レビュー 2 本、fix 3 本、焦点再レビュー、台帳登録の逐語
- `verbatim/prompts/` — 全子へ渡した prompt の逐語

## 9. 次 wave の出発点

- **次は C2。** runner の構造化実行失敗と campaign の算出変更、rep observation の 6 key → 7 key 化と
  それに伴う凍結 gate の pin 閉包を持つ。C1b は実行失敗数を**等値でのみ縛り、各回の実行成否は
  証明しない**と射程を切ってあるので、その射程を広げるのが C2 の仕事である。
- **land は 6 単位が揃うまで行わない (D1341)。**
- **main 先端の gitlink 混入はユーザー裁定へ返す。** 是正は共有状態への操作であり、
  本 wave の範囲外である。

## 10. 段 8 — 自己改善の候補 2 件はどちらも機械 gate が止めた

実測した候補を該当 reference 節へ統合しようとしたが、`tools/check_docs.py` が両方を拒否した。
**入口 (command 本文) は触っていない。**

1. **`DW-S05-A` の `reasoning=xhigh` は argv flag と読める** — 実際に渡すと
   `dev_wave_codex.py` が `--reasoning は --stage review/focus/author/fix では指定できない` で
   rc=2 即死し、本 wave は 1 投入を無駄にした。正しい規定は `DW-C01` にある。
   `effort=xhigh (DW-C01 に従い導出)` へ言い換えようとしたところ、
   **同語は段 5 実装子の adoption pin で固定**されており「変更には採用裁定と pin の同時更新が必要」
   と拒否された。自己改善契約の「裁定境界の変更は実装せず裁定パッケージへ送る」に該当するので、
   **ユーザー裁定へ返す。**
2. **prompt が参照する絶対 path の投入前実在検査** — 本 wave では親が裁定文書を job dir へ
   複製し忘れ、fix 子が 21 秒で fail-closed 停止した (子の挙動は正しく、1 byte も書いていない)。
   `--dry-run` は argv しか見ないのでこの型を検出しない。
   最初 `DW-O02` へ新しい文として足したところ **L1.5 の byte 予算超過 (9875 > 9696)** で拒否され、
   **一度は「実装せず候補に留める」と処理した。これは契約違反だった** — D782 は「予算に阻まれた
   収容は案件ごとに裁定へ返さず、D730 の手順を AI が適用して閉じてよい」と委任している。
   **手順を最後まで適用してやり直し、収容した。**
   - 収容先を `DW-O01` の既存の投入前検査の列挙へ変えた (意味の置き場所として正しく byte も安い)
   - 空いた分は `DW-O02` の意味等価な短縮で作った
   - **上限は引き上げていない** (D730 の第 1 手で収まったため、D782 の報告義務には該当しない)
   - 実測: `check_docs.py` rc=0、`test_check_docs.py` 572 passed / 3 skipped

1 は revert 済み。2 は `5c3358fab` で着地している。

**なお `db2c9a415` と `5c3358fab` は受入の tested tip `1cdafc4c0` より後の commit であり、
受入 receipt の被覆外である。** docs 変更の被覆は `check_docs.py` と `test_check_docs.py` で取った。
land する wave が改めて受入を取り直す。

## 11. 記録 commit 後の再走

`scan-repo-postcommit.txt` — 記録 commit `9d93fbd3a` の後に repo 全域の三軸走査を再走し、
**両保護対象 0 件・陽性対照 152 hit** を確認した (120.5 秒)。F335 の恒久対応が求める
「記録そのものが汚染源になるため記録 commit の後にも走らせる」に従ったものである。
