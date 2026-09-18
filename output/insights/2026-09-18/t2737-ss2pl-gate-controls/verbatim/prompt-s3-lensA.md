単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls

## レンズ A — 正しさ境界: 試作が gate の意味を骨抜きにしていないか (規律 2 / 規律 1 の面)

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/s1-brief.md` — 親の段 1 brief (**親自身も検査対象**。P1〜P6 は親の provisional 裁定であり攻撃対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/codex-artifacts/dev-wave-t2737-ss2pl-gate-controls/s2-plan.md` — 段 2 plan (検査対象)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-d2120-item12.md` — ユーザー裁定の逐語
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/verbatim-t2644-s5.md` — 一次資料 (不整合 7 件)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/orchestrator/campaign/condition_meaning_gate.py` — gate。読むべき範囲: 59-199、813-1000、1851-1950、2033-2118、2143-2330、2372-2471、2544-2712 (行番号は親の読みで、ずれは現物で直す)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/tools/pegasus/run_ss2pl_lock_study.py` — runner。読むべき範囲: 40-110、1061-1095、1334-1500、1657-1700、1959-2045
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls/patches/ss2pl-lock-protocol-study.patch` — 現行 patch (plan が名指しする範囲だけ)

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2737-ss2pl-gate-controls`。上記以外も repo 内を読んでよい (`docs/decisions.md` の D790 / D791 / D1272 / D2120 は `grep -n "^## D790\." …` で位置を出してその節だけ読む)。**大きい file を全文 `cat` しない。** `grep -n` → `sed -n` で 200 行以内ずつ。

## この段の仕事

plan を守らせず検査する。次を攻撃する:

1. **gate の意味の骨抜き。** gate (T-2018) は「define が owner TU に届いて効いている (非 inert) / 既定は stock と byte 同一 (inert)」を保証する inert witness の防壁である。試作 patch や shadow 登録簿が、その保証を**名目上は通しながら実質を失わせる**形になっていないか。具体的に: (a) 登録簿 `target` を `tpcc_ss2pl.exe` にすると、gate が認証する TU (tpcc target の transaction.cc) と runner が測る binary (`ycsb_ss2pl.exe`) の TU が別になる。`SS2PL_WORKLOAD_YCSB` で囲んだ差分は tpcc 側では消え、ycsb 側では残る — これは「stock 逐語」の保証が ycsb binary には届かないことを意味する。この隙間を親の brief (P3) は費用として明記すると言うが、**それで gate の目的 (D790 の「既定は stock 逐語」) は保たれているか、それとも (i) 軸ごとの絞り込みと同じ効果を裏口から作っていないか**。(b) DLR を `SS2PL_DLR` 純 define に付け替えて stock の `#ifdef DLR0/DLR1` 分岐を書き換えると、S arm (DLR=1) の前処理 bytes は stock と一致するが、**stock binary の semantics を patch 側で再実装している** — 一致は bytes で示せるか、それとも `#if` 書換えで意味が変わる箇所があるか。(c) KIND の companion を外す shadow は「KIND=1 は stock と同一」を stock 比較で通すが、KIND=0 は IMPL=0 では効かない。gate は各要求を独立に判定するので **arm 全体としての整合** (4 軸がその arm の実 build に届いていること) はどこで保証されるか — runner の `_validate_compile_definitions` / `_expected_cache` か、gate か、どちらでもないか。
2. **shadow 登録簿の監査可能性。** 「登録簿の行だけ差し替え、logic bytes は同一」を probe が `difflib` で検算する設計は、差し替え行に logic を紛れ込ませる攻撃 (例: `inert_values` に値を足す、`companion_defines` を変える、`owner_tus` を変える) を検出できるか。検算の受理集合を「`_DEFINE_SPECS` 内の SS2PL 4 entry の `target` field と `companion_defines` だけ」に限定できるか。shadow module を `orchestrator.campaign` package の下に読み込む案で、repo の実 module (`source_digest` 等) が本当に使われ、shadow が repo の gate を**置き換えない** (sys.modules を汚さない) ことをどう示すか。
3. **規律 1 との関係。** 試作 patch で `wfg.cc` を無条件 compile にすると、性能 build (WFG=0) に計器の TU が入る (中身は空)。runner の `_wfg_absence_evidence` (`validate_wfg_absence`) は binary の識別子・symbol・前処理出力を見る — 空 TU なら緑のはずだが、**T-2644 §5.4 の path 偽陽性**と、`__FILE__` 等で source path が binary に残る経路がないか。試作は性能 arm を走らせないので本 wave では観測しないが、採否材料としては「性能 build から計器が完全除去される (D14 の契約)」ことが (ii) の前提条件になる — これを材料に含めるべきか。
4. **親の実測値の一般化。** 親は login の g++ 11.4 で `-E -P` の空 header 寄与 0 byte と `#pragma once` 残渣を測った。計算ノードの `c++` が別版・別 vendor (clang) なら崩れるか。gate は requested / control を同じ compiler で前処理するので版差は両側に等しく出るが、`#pragma once` 残渣が stock 側 header にもあるとき「両側に等しく出る」は本当か (stock 木と patched 木で `#pragma once` header の include 回数・順序が同じか)。
5. **cell matrix の予測が恒真になっていないか。** 例: 「試作 × shadow(companion なし) × S = 全 green」を期待するが、その green は「試作が stock と同じ bytes を出す」という**自分で作った条件の確認**でしかない。gate が本来検出すべき負例 (試作の S arm に 1 行だけ stock と違う行を混ぜる) を cell に足して、gate が red を出すことを示すべきか。probe にその負例 cell (= gate の positive control) を 1 つ入れる案の要否。
6. **scope 逸脱。** plan が gate・検査・台帳・一般化を足していないか。runner の変更を提案していないか (本 wave は runner を触らない)。試作 patch に新しい lock 意味論を足していないか (P5)。

## 出力形式

所見ごとに: 番号、**分類 (正しさ境界 / 骨抜き / 監査可能性 / 一般化 / 恒真 / scope)**、**real か refuted かの自己判定と根拠 (file:line)**、**放置時に成果物 (insight の採否材料・certified 選択・台帳) がどう変わるか 1 行**、是正案 (plan の変更として)。所見ゼロの分類はそう書く。最後に `## 総括` (必須、無いと不採用) を 10 行以内: real 所見の件数、最重要 1 件、plan を止めるべきか続けてよいか、予算が尽きた場合の途中結論。

## 禁止

file を作成・編集しない。git の状態を変えない。pytest を走らせない (静的検査でよい)。走らせていない結果を緑と書かない。gate の判定 logic を変える提案、gate の適用範囲を絞る提案 ((i)、D2120 項 12 で不採用確定) をしない。予算が尽きそうなら途中結論を出力形式どおり書いて終わること (無出力が最悪)。

## 親の段 4 方向 (provisional、これも攻撃対象)

plan の総括を受けて親は次を考えている。(1) 試作 patch は plan の 8 変更群に加えて **S arm (IMPL=0,KIND=1,DLR=1,WFG=0) の transaction.cc 前処理 bytes を stock と一致させるまで stock 経路を復元する 1 版 (revS)** に絞る。plan が「主版は S が red のまま」と予測する 8 群だけの版は別 patch として作らない (revS が一致に届かなければ、その残差 diff が同じ材料になる)。abort 増分を無条件除去した対照版は plan どおり作る (4 cell)。(2) cell は plan の 60 から 44 へ絞る: revS×{O,T+,T−}×S、revS×{O,T−}×phase1、現行×O×{S,phase1}、現行×T−×S、pristine 対 (現行×O×phase1、revS×T−×S)、abort 無条件版×T−×S。(3) author は login で `g++ -E -P` + `cmp` により S 一致を自分で検算してから納品する。この方向が gate の意味を骨抜きにする (例: stock 経路の「復元」が実は再実装で、bytes 一致を人為的に作っている) かどうかも検査せよ。
