---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-cicada
seq: 1
title: VHash の hot block (構成 B) を Cicada に入れて初めて実物で測り、ro 95% でも同時刻の stock 比 0.98〜1.01 (草稿 §5.5 の語で予備的に不支持・差なし)、更新中心は key ごとの排他の待ちで 0.23〜0.80 倍、判定器は 5 腕で巡回なし・壊し 2 本は検出 (コード + patch + insight、branch worktree-dev-wave-vhash-hot-block-cicada)
---

## 本文

- 依頼: 並行 VHash wave の md_23 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt`)。一次資料 `output/insights/2026-09-29/vhash-hot-block-cicada/README.md`、設計の判断は {{D:vhash-hot-block-seqlock-prefix}}。
- 段構成: 全 9 段 (md_23 が段 2・3・6 を省かないと指定)。段 2 plan 1 本、段 3 相談 2 本、段 5 実装子 4 単位 (C++ patch・driver・登録簿・interface の直し)、段 6 レビュー 2 本・fix 5 巡 (うち 2 巡は計算ノードの smoke と本走で見つけた欠陥)・焦点再レビュー 1 本。Codex は全段 gpt-6-sol / medium。
- 棄却・訂正: 段 1 の親案 P4 (ABORTED を hot から外して評価計画草稿の数え方に合わせる) は段 2 の反例 (`later_ver` の意味が崩れる) で撤回。段 6 の A1/B2 (巡回 0 で serializable を受け入れよ) は refuted (Cicada は `--protocol cicada` で上限 indeterminate、serializable が返れば呼び方の異常として拒否)。焦点再レビューの「trace 見積りが和でなく max × 2」は過大側で計画を変えないので nit へ降格。
- 素材: 書き区間の待ちは更新中心の cell で 1 update commit あたり 9.8 万〜11.8 万サイクル、保持は約 2,800〜3,800 (診断 build 1 走)。ro 95%・GC 100 ms の stock で第 1 段が 16 版以上飛ばす読みが 21%、K=8 でも cold へ出た読みが 2,335 万回。壊し B2 (PENDING を飛ばす) は結果前の予測「validation に止められて検出 0」が外れ、T1 で commit 67・巡回 9、T2 で commit 4,331・巡回 402 を検出・帰属した (機序未特定)。
- 草稿 v1 §5.5 (D2301) は本 wave の結果より前に main に置かれたが、本 wave の計測は §5.5 を知る前に設計したので A/A 腕と主 cell c23 (ro 95%・GC 100 µs) を含まない。規則を変えずに当て、ro 95% の 12 組は予備的に不支持 (差なし)、c23 は欠測、K\* = 1。T-2893 (評価計画の発効) の前提のうち構成 B の inert patch と門・壊した variant・性能用 build での ro 指定率の制御は、この wave の patch で揃った (T-2893 の本文は書き換えていない)。
- 異常と逸脱: (1) 同じ計測木から本走 6 job を並列に投げ、5 本が rc 16 (orphan hold、子は未起動) — DW-C00 の直列の規律の不適用、残りを 1 本ずつ流した。(2) smoke1 で条件 gate が COUNT の meaning を拒否 (宣言 20 / 観測 8、分岐が K の内側) — companion `CICADA_VHASH_K=1` で解消。(3) 本走の trace job 0 が壊し版の integrity 違反を例外にして止まり、driver を直して同じ binary で取り直した。(4) 実装子 (U3) が test の分岐条件を一般化して既存 macro の照合を壊し、親の焦点走で見つけて戻した。(5) Codex 子は login で `tools/run_tests.py` が qstat preflight の rc 16 で起動せず、test の実走は親の焦点走だけ。(6) 最初の submodule 初期化は `update-no-fetch` で落ち、再走で通った (子木 2 本も同じ)。
- 計算: 計算ノードの job 合計 4,034 s (計測 2,808・変異 876・焦点走と監査 350)、受入全走は別。依頼の上限 2 node 時間未満。
- 変異: 独立 clone で最終のコード tip (474552f1c) に固定し、M0 (等価) SURVIVED・M2〜M11 の 10 本 KILLED・baseline PASSED・wrapper rc 0。M1 は別の層が同じ入力を先に拒否して単一理由にならず登録しなかった。
- 受入: 受入全走はこの記録の tip で行い、受領証は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-cicada/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分

### 新規

- {{T:vhash-hot-block-writer-exclusion}} **P2・新規**: VHash の hot block の書き込み側の排他を CAS の外へ出す設計を 1 つ試す。md_23 の実装 (key ごとの seqlock の中で挿入の CAS を行い hot を物理列の先頭の写しに保つ) は、更新中心の cell で書き区間の待ちが 1 commit あたり約 10 万サイクルになり stock 比 0.23〜0.80 倍だった。hot を遅れて更新してよい条件の論証 (md_23 の安全の論証は「書き区間の中で列を変える」ことに頼るので流用できない) を先に書き、同じ 12 cell で比がどこまで戻るかを測る。ro 95% の利得は md_23 で ±1% 程度だったので、読みの速さでなく書き込み側の費用の除去が目的。一次資料 `output/insights/2026-09-29/vhash-hot-block-cicada/README.md` §6・§12。
- {{T:vhash-hot-block-followups}} **P3・新規**: md_23 の残り。(1) 壊し B2 (PENDING を飛ばす) が validation に止められなかった機序を小モデルか計器 build で調べる。(2) snapshot の遅れの計器 (ro の begin 時の wts − rts) の bucket が 2^16 ts で飽和したので、µs に換算できる単位へ直す。(3) driver `vhash_cicada_hot_block.py` の `estimate` の trace job の所要を裁定どおり 2 job の走数の和にする (現行は多い方 × 2 で過大側)。(4) 作図の fig-write の下段に書き区間の待ちサイクルを足す (現行は保持だけ)。一次資料 §8・§11・§12。
