md_1: MOCC の validation の隙間 (版の読みと lock 状態の読みの間) を CCBench で直す

■ ユーザー裁定
- D2277 項 2 (逐語)「普通に使います。そして修理もします」。修理は AI の手番、CCBench の変更は Codex author、CCBench の CI (build・format) を通す。上流 (thawk105/ccbench) への push は人間 (ユーザー) が行い、AI は push しない。
- D2277 項 1: pin の前進は CCBench の CI が緑の tip に限る。

■ 台帳の項目
本文に「切り分け済み (本体の欠陥) → 修理」を含む item (MOCC read-heavy の G2 の item) を対象にする。pin 前進の item は本文に「整形 commit F」を含む item (TPC-C 段 1)。

■ 一次資料 (main に着地済み、見出しで引く)
- 欠陥の切り分け: output/insights/2026-09-29/t2872-mocc-g2-split/README.md (§0 結論、§2 機序の導出、§3 計器、§5 結果、§6 上限、§7 修理方針)。
  pin C の MOCC は validation の read set 走査で版の比較 (1035-1037) と lock 状態の読み (1049) を別の load で行い、その間に他の取引が公開と解錠を終えると古い版を読んだ取引が commit する。`max_rset_` の再読 (1063) で相手の版を取り込み相手より後ろの tid を取る。trace 無しの build で 112 走すべてに観測、trace 有りの G2 5/112 走の witness は 2 件直接一致・3 件推論で帰着。
- 計器と runner (repo の外): /work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/ (t2872_probe.py 50c16ab0…、mocc-g2-probe.patch ff243794…、arms-t2872.json 807c5848…)。保全の写しと MANIFEST.sha256: /work/1/SFC/tanab/izanagi-repro-archive/t2872-mocc-g2-split-20260929/。
- 既往の診断 patch (validation の版再読 + cold 側 abort を束ねたもの、5/120 → 0/120): output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md §2 の `mocc-close-version-counter-gap.patch` の所在。

■ 親が確かめた前提 (2026-09-29 夜、読み取りだけ)
- main の gitlink はまだ pin C = 68106660。pin 前進 (整形 commit F の item、稼働中の「ccbench ci integration」) は、整形 commit F = 25898d00 (branch `izanagi-tpcc-v3-silo-mocc-fmt`、GitHub にはまだ無い) への前進を人間の push と GitHub の CI 緑の後に行う段取り。
- F の cc/mocc/transaction.cc でも validation は同じ構造 (lock 読み 1047、`max_rset_` 1061、publish 1306、unlockCLL 1320)。
- 本 wave の計器 patch (mocc-g2-probe.patch) は F には `patch --dry-run` で fuzz・offset 付きでしか当たらない (厳密適用では当たらない見込み)。F 用に作り直しが要る。
- 並走の「silo-intra-txn-fix execution」wave が F の上に branch `izanagi-silo-intra-txn-fix` を作っている (cc/silo だけを触る。cc/mocc と file は重ならない)。

■ やること
1. submodule で F (25898d00) の上に branch `izanagi-mocc-validation-fix` を切り、修理を 1 commit にする (Codex author、commit message は上流の流儀に合わせた英語。D16 の本物のバグ修正)。
   最小案: read set の各 item で lock 状態を読んだ後に版を読み直し、最初の版 (epoch, tid) と違えば abort する。`max_rset_` は再読でなく検査した版から取る。lock を先に読んでから版を比べる順序の入れ替えも同値の候補で、どちらを採るかは段 2・3 で上流 Silo の検査と照らして決める。受理集合を縮める方向の変更だけにし、検査を甘くする変更は取らない (規律 2)。
   F がまだ無い・変わった場合は、その時点の pin 前進の item の前進先の tip の上に作り、根拠を書く。
2. 上流 CI 2 本を CI と同じ手順で通す (記憶 ccbench-changes-must-pass-upstream-ci): 全体 build と、`git ls-files -- cc include common` の .cc/.hh/.cpp 全 file への clang-format 14 `--dry-run --Werror`。
3. D297 (header 受理規則) の検査を F → 修正後の tip で取る (pin 前進の item と同じ手順)。
4. trace build の実測 (計算ノード、切り分け insight と同じ cell: 48 thread・1,000,000 record・rr95・rmw 0・max_ope 10・zipf 0.9・3 秒、stock genome、Release・gcc-11): 計器 patch と runner を F 用に作り直し (repo 外の使い捨て、Codex author)、修正前 F と修正後を同じ job で交互に走らせる。
   - 修正後で commit 側の class A が 0 件 (構造上そうなるはずのものの実測)、trace 有りの G2 が 0 件であること。反復数は切り分けと同じ 112 を結果の前に固定し、延長しない。修正前 F でも同じ形の G2 と class A が出ることを同時刻の対照として取る。
   - trace 無し build の commit 数を修正前後で並べ、修理の性能への影響を観測として記録する (headline・性能主張には使わない、規律 1)。
   - 計算は smoke の Elapse 単価で見積もり、合計 2 node 時間以上ならユーザー確認後に投入 (切り分けの本走は 2 job で 1.86 node 時間。修正前後の 2 系統で倍程度の見込み)。
5. patches/ の MOCC 系 patch (cc/mocc/transaction.cc を触るもの) が修正後の tip に厳密適用で当たるかを棚卸しする。当たらない・意味が変わる patch の扱いは段 4 で裁定し、検査を甘くする方向は取らない。
6. ここで止めて、ユーザーに push を依頼する: 修正の branch 名・commit SHA・CI 相当の結果を最終報告に書く。gitlink は進めない。上流へ送る説明文の下書き (英語、短く) を添える。

■ gitlink を進める時期
F への pin 前進が main に着地し、ユーザーが修正の branch を push して GitHub の CI が緑になった後に、別の wave で前進する。Silo 修理 (`izanagi-silo-intra-txn-fix`) と同じ時期になるなら、両方を積んだ tip への前進を 1 wave にまとめてよい (force push はしない)。その wave の起票を spool fragment に含める。

■ 成果物
- 一次資料: output/insights/<着手日>/mocc-validation-fix/README.md (commit の中身、CI 2 本・D297・trace build の結果と生出力の所在、修正前後の対照、patch 棚卸しの表と裁定、push の依頼内容、上流への説明文の下書き)。
- spool worklog fragment: MOCC read-heavy の G2 の item を更新 (完了は gitlink 前進の後)。gitlink 前進の wave を新規起票。

■ 所有
external/ccbench の新 branch `izanagi-mocc-validation-fix` とその commit、上の一次資料、自分の spool fragment、repo 外の使い捨て patch・script・job 一時 file (/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/ 配下)。cc/silo と Silo 修理 wave の branch、稼働中の VHash wave の orchestrator/campaign/condition_meaning_gate.py・screening_driver.py には触らない。gate・検査・台帳・一般化の追加は scope 外。
