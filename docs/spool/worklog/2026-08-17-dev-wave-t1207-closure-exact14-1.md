---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1207-closure-exact14
seq: 1
title: enforcement source closure を exact 14 へ広げ、path 単位の判別で発火を実証した — 親は自分の受理集合主張を撤回した (コード + テスト + docs、branch worktree-dev-wave-t1207-closure-exact14、変異 matrix = 9/9 KILLED)
---

## 本文

2026-08-16 /rulings 全件 第 3 回の [T-1207] 択 (c) =「`__init__.py` と `report.py` を加えた 14 と
する」の実装。設計判断は {{D:enforcement-closure-exact14}}。一次資料は
`output/insights/2026-08-17_t1207-closure-exact14/`。

- **親が段 1 前に実測した前提 3 件** (実編集 → 測定 → `git checkout --` 復元、復元後 clean 確認)。
  (1) physical な campaign lock は 32 本すべて v1 で v2 は 0 本 = 費用の時計の前提は成立。
  (2) `__init__.py` の 1 行差し替えで `pipeline` が呼ぶ dispatch の解決先が変わるのに exact 12 の
  閉包検査は緑のまま。(3) `report.py` の 1 行差し替えで rejection payload の `certified` が
  実結果から離れるのに、やはり緑のまま。

- **親は自分の主張を 1 件撤回した。** 段 1 brief に書いた「1 行差し替えで certified 選択の
  受理集合が epoch 診断に現れずに変わる」は実測から導けない。段 3 レンズ A が指摘したとおり、
  差し替え先の関数は `expected_commits` keyword を受けないので呼出しは例外になって abort へ落ち、
  棄却判定そのものは閉包内の `core.py` 由来である。以後の全文書は「閉包が見ない」「dispatch と
  payload を制御できる」までの狭い形だけを名乗る。撤回は新 D の「名乗ってよい範囲」へ固定した。

- **段 3 の 2 レンズは所見を 1 件も却下せずに済んだ (real 判定 100%)。** 独立に
  「閉包は固定 exact list なので将来 module を束縛しない」へ収束したため、親は test-only の
  package census を採用した。verifier package 直下の `.py` が exact 8 件であることを実 directory
  走査で検査し、新 module の追加を赤で止めてユーザー裁定へ返す。

- **段 6 の敵対レビュー 2 本はコード側の must-fix ゼロ。** 恒真な test node ゼロ、削除・緩和・
  skip された既存 assert ゼロを静的に確認した。残った should-fix 3 件はいずれも親の担当
  (費用分類の訂正、偽赤候補集合の過大、本 fragment 群の未 land) だった。

- **実装子の費用申告が誤りで、レビューが訂正した。** 実装子は「新規検査は O(1)」と報告したが、
  対照 node と clean node は閉包サイズ N に対し O(N)、既存の path 単位系列は O(N^2) である。
  N は repo の成長ではなく裁定でしか動かない設計量なので O(履歴) の処理は 1 件も無い。
  同一経路 (計算ノード) の実測は **51 node 2.65s → 63 node 2.70s = 1.02 倍**で閾値 1.1 倍未満。

- **login ノードの bounded local 経路が 4 回連続で rc=16 (テスト 0 件) になった。** 理由は
  cgroup の `memory.max` / `memory.oom.group` を走行中に attest できないことで、F57 既載の
  形と同じ。以後の実測はすべて `--force-dispatch` で計算ノードへ回した。

- **[T-819] の再訪条件が発火したので本 wave で消化した。** 変異 runner を drift 非感受 node へ
  絞る作法は、本 runner 範囲では**既に成立していた** — 閉包 member (`artifact_admission.py`) を
  変異させた M7 でも F358 の共通核は出ず 4 node しか落ちなかった。E1 node が `_REPO_ROOT` を
  一時 repo へ差し替えるためである。

- **変異は probe → 権威走の 2 巡で、権威走は 9/9 KILLED、MISMATCH 0 / SURVIVED 0。**
  段 2 プランが提示した期待 node 表は構造的に誤っており (同一構造の 2 parameter で片方だけが
  落ちる登録)、かつ wave 前の実コードの形 (exact 12 へ戻す変異) を欠いていたため、親が破棄して
  作り直した。**path 単位の判別が成立している** — `__init__.py` だけを外すと `report.py` 側では
  落ちない 3 node がちょうど落ち、逆も対称 (共通核 49 node)。新設した対照 node は対応する path が
  閉包に入っているときだけ発火しており、恒真ではない。scope 文字列だけを旧文言へ戻す変異は
  1 node しか落とさないので `DW-M03` に従い diagnostic sensitivity pin として別枠に置いた。

- **F357 の偽赤範囲が実測で確定した。** 段 6 レビュー B は静的解析だけで偽赤 node を 1 件と予測し、
  統合 commit 前の実走がその 1 件ちょうどを返し、commit 後の同範囲再走は 465 passed / 0 failed
  だった。実装子が挙げた広い候補集合は過大だった。詳細は F357 の supersede 追記。

## 次の一手差分

### 完了

- [T-1207] enforcement source closure を exact 14 path へ広げ、`__init__.py` の dispatch 面と
  `report.py` の report 面を束縛した。設計判断は {{D:enforcement-closure-exact14}}。
  変異 9/9 KILLED で path 単位の判別を実証し、受入全走まで通した。
  remaining: none
  base: eaeeb1f5608f020e999f351ae9db5586db357b80547ac53c5dd06e7747843d96

### 更新

- [T-1208] **P2・ユーザー裁定待ち**: 旧定義の `E1` を新閉包の certified 選択から排除する機構が
  無い。本 wave の段 3 で穴が**実到達**であることを確認した — oracle の artifact validator は
  scope を非空文字列としか検査せず、judge は `state=E1` と `certified_eligible=true` だけで
  採用し、既存テストが任意の `E1:` digest と任意 scope を unique-best まで通す。
  閉包が exact 12 から exact 14 になったことで、同じ `campaign-verifier-epoch/v1` domain が
  2 つの grammar を歴史上指す曖昧さも生じた。択一は (a) hash domain を `/v2` へ上げる /
  (b) oracle 側で現行 scope の exact 一致を要求する / (c) 現状維持。
  本 wave は (c) を採り domain を据え置いた。
  base: 002edfa6a7256e71a2da4d968b631727195a121fcecf52c7930fc1e3537a2ccb

### 新規

- {{T:certified-sink-dominance}} **P2・新規**: certified sink の支配点が無い。
  `pipeline.evaluate` の COMMIT と低層 WAL writer は verifier receipt を要求せず、
  `ident` の停止点を通らずに commit record を書ける。閉包を広げてもこの面は 1 つも減らない。
  全 `STAGE_COMMIT` producer に、verifier の判定と lock identity へ結び付いた一回限りの
  receipt を要求させるかを決める。
- {{T:fresh-weak-lock-and-module-census}} **P2・新規**: 弱化してから作る fresh lock を
  拒否する機構が無い。閉包が検出するのは lock 記録後の drift だけなので、verifier を弱めて
  commit し、その bytes で新しい lock を作れば新しい `E1` として受理される。
  fixed-list 外の新 module も同じ経路で入る (本 wave の census は追加を赤で止めるが
  runtime の束縛ではない)。新 lock を批准済み known-good digest と比較する設計にするかを決める。

### 見送り追記

- [T-819] 2026-08-17 に発火し消化 ({{D:enforcement-closure-exact14}} が同一ファイルを編集)。runner を drift 非感受 node へ絞る作法は本 runner 範囲で既に成立しており、閉包 member を変異させても F358 の共通核は出ず 4 node しか落ちなかった。
