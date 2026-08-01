# 裁定パッケージ — 並行セッション開発 (parallel-dev wave、2026-08-01)

本 wave の scope 外だが real と裁定した所見。実装せずユーザー裁定へ返す。

---

## R1 — main 進行に伴う再検査ループそのもの (B 軸)

### 事実 (実測)

- land (`tools/dev_wave_land.py`) は **ff-only のみ**。merge commit も rebase も force も作らない。
  tested main が現在の local main と乖離すると `RC_STALE_MAIN` を返して終わり、**自動救済経路は無い**
- 協調 lock は `fcntl.flock(..., LOCK_EX | LOCK_NB)` = **非ブロッキング・待機なし・timeout なし**。
  取れなければ即 `RC_LOCK_BUSY`
- lock の保持範囲は land 本体だけで、**受入全走 (約 200 秒) の間は保持しない** (D102 決定 2 の設計どおり)
- stale / busy のたびに呼び出し側は `DW-O23` / `DW-S09` / D102 決定 (1) により
  **fresh context で (i) 新 main の監査、(ii) 固定 SHA の wave-side merge、(iii) 受入全走の再実行、
  (iv) 新しい `A..T` 閉包の再構成** を行ってから再試行する義務を負う
- D104 が受入全走の約 200 秒の床は in-scope のテスト側施策では動かないと実測確定済み
  (律速は本番 `_history_touches_path` の履歴走査、約 80 秒)。フォローアップ [T-201] は裁定待ち
- **main の前進間隔 (基準 `5948a6f` で再測、直近 60・10h 未満の 58 件)**:
  - **ref 更新ベース (reflog) = stale 判定の正しい指標: 中央値 22.08 分 / 平均 68.72 /
    p25 11.13 / 15 分以内 36.2%**
  - commit ベース: 中央値 8.22 分 / 平均 27.79 / p25 4.20 / 15 分以内 60.3%
  - **ff-only land は N commit を 1 回の ref 更新で運ぶため、commit ベースは約 2.7 倍の過大である。
    R1 の評価には ref 更新ベースを使うこと。**
  - **訂正記録**: 本パッケージの初版は中央値 11.6 分 / 15 分以内 57% と書いたが、
    それは invalidate 済みの旧基準 `5544794` を commit ベースで測った値だった (`DW-O18` に従い測定基準を併記する)
- 実績: (72) は段 9 中に main が 2 回前進し、そのたび受入全走をやり直した (4012 → 4089 → 4098 passed)
- **訂正**: 初版は「land 阻害に直接起因する受入再走は計 4 回」と書いたが、**帰属が誤りだった**。
  `docs/worklog.md:940-948` は (78) について **「主因は main の diverge」「実行順では control-plane
  preflight が先に当たり rc 21 を返した」**と自ら記録している。つまり handoff 拒否は先に当たっただけで、
  本 wave の S1 を入れても同じ land は `RC_STALE_MAIN` で落ちる。(72) の 2 回も stale 起点である。
  **S1 が実際に消す受入再走は 0〜1 回**であり、R1 の主因は依然として stale そのものである

### 構造的な問題

受入 (約 200 秒 + queue 待ち) → 監査 → land という直列の窓が、main の **ref 更新間隔
(中央値 22.08 分、p25 11.13 分、15 分以内 36.2%)** と同オーダーである。
窓の間に main が進むと全部やり直しになり、やり直しの間にまた進む。
**lock を受入中に持たない設計** (正しい判断: 200 秒の critical section を共有しない) が、
同時に **この窓を構造的に開けている**。

### なぜ本 wave で実装しないか

D102 却下案 (c) が「stale 検出後に**同一 context で自動 merge / 再試行**」を、
「新 upstream の監査と受入を省略し得る」という理由で**明示的に却下している**。
この却下を覆す案はすべて既存の設計判断の変更であり、`DW-S04` の
「scope 外の real 所見は実装せず裁定パッケージでユーザーへ返す」に該当する。

### 追記 (2026-08-01、基準を `5948a6f` へ更新して判明)

**D102/`DW-S09` の fresh-context 要求は、運用上すでにユーザー裁量で上書きされている。**
`docs/worklog.md` (78) は、ユーザー指示 **「やってください。並行セッション開発してますんで、
そういうことはおきます」** を受けて **同一 context で main を 3 度取り込んだ**
(`3ca5cfe` → `3926405` → `5544794`)。2 度目は [T-205] wave と同一ファイル 168 行の衝突が起きたが
**コードは 3-way merge が自動解決**し、手で解いたのは docs 2 件だけだった。

したがって下記 (b)(d) は「新しい提案」ではなく **既に実地で行われている運用の追認・明文化**にあたる。
D102 却下案 (c) が禁じたのは「新 upstream の**監査と受入を省略**する自動 merge」であって、
監査と受入を行う同一 context 取り込みそのものではない。**この区別を明文化するのが本 R1 の核心。**

### 選択肢 (親の評価つき、いずれも要裁定)

- **(a) 現状維持 + S1 の効果を待つ。** 追加コストゼロ。ただし上記の訂正により、
  **S1 が消す再走は 0〜1 回に留まり、stale という主因は残る**。したがって (a) は
  「まず実測してから判断する」以上の効果を期待できない。**親の推奨は (a) + (d) の併用**へ改める
- **(b) 受入と land の窓を短くする。** 受入完了から land までの間に docs 記録・段 8 を挟まず、
  land を先に行う (段順の入れ替え)。受理集合は変えないが `DW-S07`/`DW-S08`/`DW-S09` の段順の変更になる
- **(c) 影響範囲による再走免除。** 新 main の差分が wave の触れた path と素集合なら受入再走を省く。
  **受理集合が広がる方向であり、D102 却下案 (c) の懸念に正面から当たる** (path が素集合でも
  意味的相互作用はありうる)。親としては単独では推さない
- **(d) lock を待機可能にする (`LOCK_EX` + timeout)。** busy のときに fresh context を作り直す代わりに
  短時間待つ。stale は解決しないが busy は解決する。critical section は現状のまま短い

### 成果物影響

放置すると wave の成果が main へ着地せず branch に留まる ((73) に実績)。
worklog 台帳と main の実状態が乖離し、後続 wave の基準 commit 選択を誤らせる。

---

## R2 — (72) の 12 回連続 rc=20 は land の正しい判定だった

### 事実

(72) では land が `rc=20` (`RC_DIRT`) で **12 回連続拒否**し、原因は最後まで未追跡 1 path
= 並行セッションの成果物 `output/insights/2026-07-30_dev-wave-gate-cost-and-suite-floor.md` だった。
最終的に「一回限りの land adapter」で宣言 1 path だけを非接触扱いに拡張して着地した。

### 裁定

**これは land の誤検出ではない。** `_verify_main_clean` (760-795) は untracked path を
land 対象と衝突する場合だけ拒否する。つまり 2 つのセッションが**同じ `output/insights/` 配下を
真に奪い合っていた**。land の判定は正しく、S1 の対象ではない。

### 返す課題

`output/insights/` の命名規約が衝突を許している。現行は `<日付>_<wave 名>/` だが、
(72) の衝突例は `<日付>_<主題>.md` という**ディレクトリを作らない平置き**形式だった。
平置きを禁じて必ず wave 専用ディレクトリを切れば、異なる wave の成果物は構造的に衝突しない。
`DW-O02` は job artifact について同趣旨を既に定めているが、`output/insights/` の
成果物側には同じ規約が無い。**規約の新設は受理集合を変えるためユーザー裁定へ返す。**

### 成果物影響

放置すると、同日に 2 wave が走るたび land が正しく拒否し、一回限り adapter という
**監査経路の外の迂回**が繰り返される。(72) では実際にそれが使われた。

---

## R3 — worktree 置き場の `.gitignore` 追記 (元 S4) は実装しない

### 親の裁定: 実装せず裁定へ返す

段 1 では実装候補 (S4) だったが、段 2 の consumer 監査と親の実測で**費用対効果が成立しない**と判断した。

### 事実 (実測)

- `.claude/worktrees/` の除外は**マシンローカル・未追跡の `.git/info/exclude:11`** にしかなく、
  repo に入っていない。`.codex/worktrees/` はどこにも無い
- **`.gitignore` を広げる案は D102 却下案 (a) が名指しで却下している** —
  「他の strict cleanliness consumer まで受理集合を変える」。段 2 の監査はこの懸念が実在すると確認した
  (`tools/dev_waves/git_state.py:47` 経由の `main_dirty`、
  `tools/check_wave_startup.py:127-133 _check_clean_tree` の 2 つで受理集合が広がる。
  `orchestrator/campaign/s8b_ratified_freeze.py:352` は pathspec 限定で無影響)
- **land の受理集合は変わらない** ことは確認済み。`_verify_target_collisions` の `protected` に
  `_CONTROL_CONTAINERS` が無条件で入るため、`.claude/**` `.codex/**` 形の target は
  `_ignored_paths_for_target` へ到達する前に `RC_CONTROL_PLANE` で落ちる

### 実装しない決め手 (親の実測)

共有 main checkout に対する `_parse_status` の実測は **`main_dirty = True` / 16 エントリ**。
内訳は `.codex/worktrees/*` が 10 件、`.claude/settings.local.json` が 1 件、残りが untracked handoff。
**`.gitignore` に worktree 2 種を足しても `.claude/settings.local.json` と handoff が残るため
`main_dirty` は True のまま**であり、S4 単独では何も解決しない。
D102 の却下を覆すのに、それを正当化する**実測された被害が 1 件も無い** (`DW-G04` の趣旨)。
`.git/info/exclude` が失われても land は衝突検査へ落ちて耐えるため、堅牢性の穴も致命ではない。

### 返す選択肢

- **(a) 現状維持 (親の推奨)**。`.git/info/exclude` 依存は残るが、失っても land は耐える
- **(b) `.gitignore` へ追記し、D102 却下案 (a) の取り消しとして新 D に受理集合の変化 2 件を明記する**
- **(c) `.gitignore` は変えず、除外が効いていることを `check_wave_startup.py` が検査する。**
  受理集合をどこも広げずに「マシンローカル依存で気づかず壊れる」だけを閉じる。
  ただし現状 `.codex/worktrees/` は除外されていないので、この検査は新規に赤を作る

### 成果物影響

放置しても main の値・監査済み集合・台帳は変わらない。変わるのは clone / 別マシン /
exclude 消失時に `git status` 系 gate が他セッションの worktree を dirt として拾う点だけ。

---

## R6 — mid-flight 検査が非対称でないため、他セッションの「正常終了」が land を落とす (段 6 の残余)

### 事実 (段 6 Fix-A が実装・実測)

D109 実装後も、`_control_snapshot` の**名前集合比較**は残る (`:566` の relist と `:709` / `:1298` の
2 スナップ間比較)。ここは handoff が **現れても消えても** `RC_CONTROL_PLANE` を返す。
負例 `test_foreign_handoff_appearing_mid_flight_is_still_rejected` と
`test_foreign_handoff_disappearing_mid_flight_is_still_rejected` が両方向を固定している。

**しかし 2 方向の危険度は同じでない。**

- **現れる方向は危険**: 新しい path が生まれるので、`protected` を計算した時点では存在せず、
  merge 時に自分の target が上書きしうる。再検査が要る
- **消える方向は安全**: 保護対象が減るだけである。仮に自分の target がその path と一致していても、
  ファイルが消えた後に書くことは他セッションの成果物を壊さない

つまり**消える方向の拒否は、T-220 (a) の「incoming と衝突する未知 untracked だけ拒否」に反する**。

### なぜ本 wave で直さなかったか

- **`docs/handoff/README.md` の運用ルールでは、handoff の削除は「正常終了時に worklog へ吸収して
  ファイルを削除する」という規定手順**である。つまり**最も正常な操作が land を落としうる**
- ただし (i) main は不変で**再試行可能** (fix した post-land の非再試行窓とは異なる)、
  (ii) 発生はセッションあたり 1 回で窓も短い (内容更新の 10 分周期とは頻度が 2 桁違う)、
  (iii) mid-flight 検査の意味論を変えるのは正しさ防壁の変更であり、
  段 6 の時点で敵対レビューを経ずに scope を広げるべきでないと裁定した

### 返す選択肢

- **(a) 非対称化する (親の推奨)**: 名前集合の比較を「**追加された名前があれば拒否、消えただけなら通す**」
  へ変える。`protected` は保守的に**和集合** (両スナップに現れた名前の合併) を使えば、
  消えた path への書き込みも引き続き拒否できる。受理集合は狭まる方向にしか動かない
- **(b) 現状維持**: 再試行可能なので実害は限定的
- **(c) 窓自体を縮める**: `:1282`〜`:1343` の窓には `git status --ignored` と `check-ignore` が
  target ごとに走る。ここを短縮すれば両方向の発火確率が下がる

### 成果物影響

放置すると、隣のセッションが規定どおり handoff を回収した瞬間に land が落ち、
**再走 (受入全走を含む) が 1 巡増える**。R1 の再検査ループの一因として残る。

---

## R5 — 共有 `.git` 面にも同型の「無関係な全 land 停止」経路が実在する (段 3 M7)

### 事実 (段 3 レンズが file:line で実証)

本 wave の S1 は `docs/handoff/` 表面の untracked/dirt 軸だけを緩める。しかし
**incoming と無関係に他セッション起因で全 land を止める経路は他にも実在する**。
`tools/dev_wave_land.py` の raise サイトは 88 あり、プランが分析したのは 20 だけだった。

- **`_verify_effective_config:515-535`**: `git config --includes` を読む。**`.git/config` は
  全 worktree 共有**なので、他セッションが `filter.*` を書けば incoming と無関係に
  全 land が `RC_AUDIT` で**恒久停止**する
- **`_verify_history_modifiers:495-512`**: 共有 `.git/shallow` / `info/grafts` / `refs/replace/`
- **`_verify_repository:400-407`**: 他セッションの `git worktree prune` で自分の admin 束縛が消える
- **`_open_lock:1148/1157`**: 共有 git-dir の永続 lock file の mode / uid / nlink
- **`_worktree_snapshot:689` / `_validate_admin_binding`**: 未登録 alias・不正 child 名

### 本 wave の scope 境界 (親が明記した原則)

> 本 wave が緩めるのは **main worktree の `docs/handoff/` 表面における untracked/dirt 軸だけ**である。
> 共有 `.git` の config / history modifier / lock、および worktree admin 束縛は**変更しない**。

**[T-220] の裁定文「incoming と衝突する未知 untracked だけ拒否」を字面どおり読めば
上記も射程内である。** 親は brief v2 の不変条件で除外したが、その判断自体が裁定事項である。

### 返す選択肢

- **(a) 現状維持 (親の推奨)**。これらは「他セッションが異常な状態を作った」ときにだけ発火し、
  handoff のような**正常運用で日常的に触られる面ではない**。実測された被害も無い
- **(b) 同じ原則を共有 `.git` 面へも広げる**。受理集合が大きく動くため独立の wave が要る
- **(c) 少なくとも診断を改善する**。現状これらは「自分の land の失敗」として報告されるが、
  原因は他セッターにある。規律 3 の「なぜ壊れたか」を正しい所有者へ返す形にする

### 成果物影響

放置すると、他セッションが共有 `.git` を触った瞬間に全 wave の land が止まり、
原因が自分の差分にあると誤帰属される。頻度は低いが停止は恒久的になりうる。

---

## R4 — `dev_waves` の `main-dirty` gate は共有 checkout で恒常的に発火している (観測)

### 事実 (実測)

`tools/dev_waves/git_state.py:_parse_status` は porcelain-v2 の `?` レコードを
`main_entries` へ入れ (240-243)、`main_dirty = bool(main_entries)` を返す (287)。
共有 main checkout での実測は **`main_dirty = True` / 16 エントリ**で、
すべて他セッションの worktree・handoff と `.claude/settings.local.json` である。
consumer は `checker.py:454-455` (`ReasonCode.MAIN_DIRTY`)、`daemon.py:847-850`、`daemon.py:1510`。

### 未確定

対話型 dev-wave の常用経路は `dev_wave_land.py` であり `dev_waves` daemon ではないため、
**この恒常発火が実際に誰かを止めた実績は確認できていない**。実害の有無を確かめずに
gate を緩めるのは規律 2 の方向に反するので、観測として起票するに留める。

### 成果物影響

現時点では不明。daemon 経路を使う運用が始まった時点で「常に main-dirty」により
fail-closed し続ける可能性がある。
