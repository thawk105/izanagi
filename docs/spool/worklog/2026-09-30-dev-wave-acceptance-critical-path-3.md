---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-acceptance-critical-path
seq: 3
title: 受入全走の最長経路を実測で分解し、9/26 以降の shard あたり約 1 分増の原因 (受入門番の共有雛形の PYTHONDONTWRITEBYTECODE=1 で bytecode cache が冷えたまま) を特定して雛形から外した。台帳・割付の見直しは効果 0 秒、fixture 共有は次の一手 (insight + repo 外の雛形、branch worktree-dev-wave-acceptance-critical-path)
---

## 本文

- 依頼: 並行 wave の md_2 (`/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_2.txt`、共通指示 `common.txt`)。受入全走の wall を受理集合を縮めずに縮める。一次資料 `output/insights/2026-09-29/acceptance-critical-path/README.md`、判断は {{D:acceptance-template-no-dontwritebytecode}}、失敗は {{F:measurement-env-leaked-into-shared-template}}。
- 段構成: 軽量版 (依頼が段 3 相談 1 本・段 6 review 1 本を残すと指定)。段 2 は brief が plan を兼ねた。codex 5 本 (consult・author・review・fix・focus)、Claude sonnet の調査子 3 本 (区間分解と pyc 照合、コード地図、割付の机上試算)。repo 内の実装面差分ゼロなので変異 matrix は免除 (DW-S04)。
- 素材: 9/29 の緑 58 走の外側 (投入意図 → 統合 junit) 中央値 509.5 秒、各指標の中央値は待ち行列 177.6・W_max 337.9・後処理 15.7 秒。依頼の「約 14 分」級は待ち行列が 458〜514 秒の走で、W は通常範囲。
- 素材: pre (計算ノード collection) は 9/26 午後以降、冷 (125〜140 秒) が多数派。dispatch の request env の `PYTHONDONTWRITEBYTECODE=1` と走単位で強く対応 (あり 73 走 = 冷 67、なし 51 走 = 冷 2)。共有雛形 (9/26、[T-2838]) の export 行が原因。雛形を差し替えた (repo 外、旧版は job dir `meas/run-acceptance-gated.sh.old`)。
- 同時刻対照 2 対 (事前登録、同 commit `4604b9fe4` の fresh 木 4 本): 判定は「判定不能」(待ち行列が 22〜29 秒と短く、H の全 shard が login collection 完了前に開始)。観測値は H の pre が 6/6 shard で 24.7〜28.6 秒短い、ΔW_max は +23.8 / −148.3 秒。全効果 (約 65 秒) の同時刻対照は、追加の対で最終受入込み 2 node 時間を超える見込みのため取っていない。対照の計算は 12 job の Elapse 合計 4,058 秒 (1.13 node 時間)。
- 棄却・訂正: 段 1 brief の明示の温め (login で pytest を直接起動) は段 3 相談 高 1 (AGENTS.md の直接起動禁止) で撤回。依頼文の「T-080 群 約 3,566 秒」は遅い走の値で、中央値は 2,112 秒。台帳の再生成・割付の見直しは机上試算で効果 0 秒 (現行 allocate の再計算は実走と完全一致)。
- 段 6: review 1 本 NO-GO (must 3・should 4、全部 real) → fix 1 回 → 焦点再レビュー 1 巡 NO-GO。親の裁定で閉じた: 新規 must 1 (runner が K と H に同じ木を受け付ける) は運用で閉じる (木 4 本の一意性・fresh・submodule・commit を木作成 log と record.json の path で親が照合)、partial 3 件は木作成 log・終了後 pyc・request env・同時起動直前の ps 全行で足りる、should 1 件 (JSON 要素の一致) は要素の完全一致なので refuted。fix を重ねなかった (DW-O16)。
- 異常: `git worktree add` の checkout 中に `.gitattributes` 読取りの EINTR 警告が多数出たが、5 本とも checkout は完了し submodule 初期化 rc=0 (最初の wave 木の submodule 初期化は 1 回目 update-no-fetch rc=1、同引数の再実行で rc=0)。隔離 session の guard が変数入り複合 command と `git -C` を拒否したので、他の木の git 操作は親の script 経由にした。段 3 相談の起動時刻を handoff に推定で書いて誤った (実際は 23:41、date で訂正)。
- 受入全走は記録 commit を含む最終 tip で行い、受領証は job dir に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分

### 新規

- {{T:acceptance-first-run-prewarm}} **P2・新規**: 初回受入でも shard の collection 開始前に投入元 worktree の bytecode cache をそろえる。待ち行列が login collection より短い初回受入では雛形の変更の効果が pre 約 −27 秒に留まる (一次資料 §4)。正規経路 (`tools/run_tests.py`) の中で login collection の完了を shard の collection 開始の前に置くか、計算ノード worker に cache を書かせるかの設計択一。run_tests.py の blob 変更は D987 で in-flight 全 wave の再受入を招くので時間帯を選ぶ。見込みは短い待ち行列の初回受入で pre −約 38 秒。
- {{T:acceptance-shard0-busiest-worker}} **P2・新規**: 受入 shard-0 の最忙 worker (実測中央値 207 秒、shard-1 / 2 は約 157 秒) を作る成分を削る。候補は T-080 共有 base の構築待ち、test_s8b_floor_campaign の `_real_output_snapshot()` 前後 2 回 (重い 10 関数 12 nodeid、各約 87 秒)、T-080 active-v2 系 9 node の emitter memo 迂回。fixture の scope 引き上げは test 間の状態共有を生むので、実装前に最忙 worker の item 列を実測し、段 3 相談・段 6 review を残す。md_2 の fixture 項の未実施分。
