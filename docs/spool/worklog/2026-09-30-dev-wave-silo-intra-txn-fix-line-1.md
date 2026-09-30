---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-silo-intra-txn-fix-line
seq: 1
title: [T-2905] Silo の取引内の値の修正に #line +3 の 1 commit を足し、push を依頼できる状態にした — 新 tip dbac49b6、D297 (b) は GCC 11・12 とも一致 (CCBench commit + insight、branch worktree-dev-wave-silo-intra-txn-fix-line)
---

## 本文

- 依頼は gen-opt 第 4 陣の md_12 (repo 外の `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_12.txt`)。D2305 項 5 (択 B) の実施で、新しいユーザー裁定は無い。
- 段 3 相談の所見 6 件はすべて採用 (計装 patch が `#line 658` を文脈に含み新 tip に当たらない、前回 script の親 OID 固定 3 か所、(b) に `--expect-paths` 4 path、(a) を省く、前回 message の「#line untouched」が偽になる)。段 6 レビューの must-fix R1 (判定 script が検査器の拒否でも rc=0) は refuted とした — 段 4 で「script は走り終われば rc=0、合否は親が `b-gccN.rc` で読む」と決めており、読み違いは R2 (表示行の引数ずれ) の修正で塞いだ。R2・R3 (trace 起動器の親 OID 照合) は fix 1 本で閉じ、焦点再レビュー GO。
- 予測 (login の probe) と結果が一致した: pin + 修正と新 tip は `ERR` が 106・693 で TRACE=0 前処理も一致、D297 (b) は GCC 11 971 秒・GCC 12 982 秒で両方 pass。
- 異常: 隔離 guard が変数入りの sed・python・`bash <script>; ...` の連結を拒否し、launcher を Write で書き直した。`dev_wave_submodule_init.py` は wave 木・子木とも 1 回目が `update-no-fetch` で落ち、再走で rc=0 (既知の型)。子木の checkout 中に `.gitattributes` 読取の割り込み警告 31 件 (作業ツリーは clean)。
- 工数: Codex 子 5 本 (consult・author・review・fix・focus、すべて gpt-6-sol / medium)。計算 3 job 2,186 秒 ≈ 0.61 node 時間 (37765・37764・37772.nqsv)。
- peer 通知: land 調整役と gen-opt manager から land 手順の追補 (LAND-READY → PREP/GO → land 1 回 → LANDED/FAIL 返信) を受けた。
- 根拠: `output/insights/2026-09-30/silo-intra-txn-fix-line/README.md`。

## 次の一手差分

### 更新

- [T-2905] **P2・新 tip commit 済み、push は人間**: CCBench の branch `izanagi-silo-intra-txn-fix` = `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43` (親 `7e5fa528`、D2305 項 5 の `#line` 4 本 +3 だけ)。上流 CI 相当は緑 (format は新 tip の 213 file を clang-format 14.0.0 と CI image の 14.0.6 で rc=0、build は CI image :ci で rc=0・本体の警告 0)。D297 (b) pin + 修正 → 新 tip は GCC 11・12 とも pass (前回は拒否)。trace (U0 の照合器・2 workload) で新 tip は取引内の値の照合 (D2b)・手順列の照合 (D1) とも 0 件、判定器 certified、対照 F は D2b 赤。主 checkout の submodule の branch ref は、本 wave が land の後 (段 9) に `7e5fa528` → `dbac49b6` へ非 force で fast-forward する (land の時点では未実施。`git -C external/ccbench rev-parse refs/heads/izanagi-silo-intra-txn-fix` で確かめられる)。残り (ユーザー) = 主 checkout で `cd external/ccbench && git push origin izanagi-silo-intra-txn-fix`、GitHub の CI (build・format) の緑の確認。上流へ送る説明文の下書きは insight §5。その後の gitlink 前進は [T-2917]。根拠: `output/insights/2026-09-30/silo-intra-txn-fix-line/README.md` §0・§5。
  base: e872cbfa08567517c3d319b53be538e5e2748afdff2eda9a896e818515c43878
- [T-2885] **P2・修正を CCBench の branch に commit 済み、push は人間**: stock Silo の `TxExecutor::read` を書き込み集合から先に探し、`TxExecutor::update` の 2 度目の書きで値を置き換える修正 (D16 の本物のバグ修正、ユーザー裁定 2026-09-29「Siloに不具合があったなら直すよ」)。branch `izanagi-silo-intra-txn-fix` の tip は `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43` (修正 `7e5fa528` + `#line` +3、[T-2905])。gen-opt の評価開始の前提 (取引内の値の照合が全 key で 0 件) は新 tip の trace build でも満たした (200 record・4 thread・1 秒、RMW あり / なしの 2 workload、各 1 回)。完了は gitlink が新 tip へ進んだ後 ([T-2917])。INSERT・DELETE の要素への 2 度目の update と `scan` の読み集合優先は未修正。修正後の stock は別 build、修正前の測定は当時の事実として残す。根拠: `output/insights/2026-09-29/silo-intra-txn-fix/README.md` §1・§2、`output/insights/2026-09-30/silo-intra-txn-fix-line/README.md` §3。
  base: 10c625521137a1d05cafccb43f1611f1704f9eb90e9968e110150772a1c94705
- [T-2917] **P2・前提待ち**: CCBench の gitlink を Silo の修正 tip へ進める wave。前提: F `25898d00` への pin 前進 ([T-2854]) の main 着地、ユーザーによる branch `izanagi-silo-intra-txn-fix` (tip `dbac49b6dc2d2ab9211b1ec0a41e44fa21245f43`) の push と GitHub の CI (build・format) の緑。やること: gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` の同時更新、D297 の扱いの定義 (本物の修正では旧新一致が成り立たない。材料は前回 insight §3 の (a) F → 旧 tip の期待拒否と、本 wave の (b) pin + 修正 → 新 tip の GCC 11・12 pass)、patches/ の V26 `broken-silo-stale-read-own-write`・V27 `broken-silo-repeat-update-buffer` を修正後の挙動を壊す形に作り直す (修正 tip に当たらない。他の Silo 系 39 本は当たり inert 一致、3 本は F でも当たらず [T-2854] の範囲。棚卸しは旧 tip `7e5fa528` で取ったもので、`#line` の数値だけが変わった新 tip では取り直していない)、修正後の stock を対照にする計測の取り直し (規律 7)。変異を外して緑にしない (規律 2)。根拠: `output/insights/2026-09-29/silo-intra-txn-fix/README.md` §4・§6、`output/insights/2026-09-30/silo-intra-txn-fix-line/README.md` §2。
  base: 54431c4a2c179cb24242b07a039ed3ee47f60caffa3133249c078c2a841d92a6
