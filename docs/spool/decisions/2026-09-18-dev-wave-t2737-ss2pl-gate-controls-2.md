---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2737-ss2pl-gate-controls
seq: 2
---

## {{D:ss2pl-gate-controls-materials}}. SS2PL runner の condition gate 問題の対照材料は、gate と登録簿を repo 側で 1 byte も変えず、job dir の試作 patch と shadow 登録簿で層別に取る — shadow の結果は機構診断であり、stock 側 ycsb target の比較の成立とは扱わない

**決定:** D2120 項 12 の再提示材料 (`output/insights/2026-09-18/t2737-ss2pl-gate-controls/`) は次の形で取り、次の限定を付す。

1. 試作 patch (revS) と abort 無条件除去版、shadow 登録簿 (O = repo と byte 同一 / T+ = target を `tpcc_ss2pl.exe` / T− = T+ + KIND の companion 除去) は job dir にだけ置き、repo の `patches/`・`condition_meaning_gate.py`・runner は変えない。shadow の受理条件は「repo の gate bytes に許可置換だけを施した期待 bytes との全体一致」とし、`inert_values` / `owner_tus` / 式 / 非 SS2PL entry / logic の変更は拒否する。
2. 材料の先頭に「stock の ss2pl に `ycsb_ss2pl.exe` target が無い限り、inert arm の stock 比較は gate 不変では構造的に成立しない」「shadow T± の結果は tpcc target の owner TU の機構診断であって、測定する ycsb TU の stock 逐語 (D790) の認証ではない」を置く。shadow の admission を production の認証・certified 選択に流用しない。
3. 試作 patch に新しい lock 意味論、KIND を IMPL=0 で効かせる細工、`#line` 指令を入れない。S arm の復元は stock 本文の復元に限り、固定範囲で届かなければ残差を成果物とする (実測: 残差 1 行 = login diff で `ERR` macro の `__LINE__`)。
4. `wfg.cc` は CMake の `CCBENCH_SS2PL_WFG_DIAG` 条件付きのまま (runner の `validate_wfg_absence` は source 名の `wfg` を拒否する)。WFG の閉包差は owner TU の `ss2pl_wfg.hh` include 無条件化と中身の `#if` 囲いで閉じる。
5. (iii) warm-up の測り方は既存 helper `buildcache.prepare_masstree_fetchcontent` (D2131 と同形、`FETCHCONTENT_BASE_DIR` は既存 non-symlink directory を事前に作る) とし、生の `cmake --build --target masstree_build` は使わない。
6. 採否は書かない。材料は「成立した比較 / 成立しない比較 / 必要な変更層 / 費用・隙間 / 証拠 cell」の 1 表と、択一の骨子までとする。

**理由:**
- gate (T-2018) は inert witness の防壁で、主経路外の研究のために緩めない (D2120 項 12 の (i) 不採用)。登録簿の行だけ差し替えた写しで測れば、gate logic を変えずに「どの層の変更で何まで進むか」が層別に読める。
- tpcc target の一致を採用根拠へ昇格させると、未検査の ycsb 経路を残したまま対象を変えて防壁を迂回した結論になる (段 3 / 段 6 レンズ A)。
- `#line` は gate の比較対象 (前処理 bytes) を人為的に揃える操作であり、材料の段階で入れると「成立」の意味が変わる。
- 9 driver と t316 probe が既に helper 経由で masstree を準備しており、SS2PL runner だけが欠く。同形で測るのが最小差分で、生の cmake target 呼び出しは D2131 が sink として却下した形。

**却下した選択肢:**
- 8 変更群だけの試作を別版として先に測る (段 2 plan) — S 一致まで復元した 1 版で届かなければ残差が同じ材料になる。
- `wfg.cc` を無条件 compile にする (段 2 plan) — runner の source 名検査に抵触し、owner TU の閉包にも無関係。
- gate の positive control として S に 1 行差分を混ぜる cell を足す — abort 無条件除去版 (残差 218 行) が対照になる。ただし両版 red なので「abort 単独で green → red」の反転対照は未成立と書く。
- 試作 patch・probe を repo へ入れる — 実装面は Codex author が書き、job dir に置いて insight に `.md` 逐語で残す (T-317 未裁定、`compute-probe-stays-out-of-repo`)。
