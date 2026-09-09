---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2188-nonmonotonic-mechanism
seq: 1
title: [T-2188] 刻み応答の非単調性の機序は滞在分布だった — 滞在を実測すると混合が閉じ、歩行 model の否定的結論は model 側の誤りと分かった (コード + 実測 + insight、branch worktree-dev-wave-t2188-nonmonotonic-mechanism、変異 10/10 KILLED・期待 node 完全一致)
---

## 本文

- **依頼が引く一次資料の「次に必要なこと」は、後続 wave が実現しても更新されない。**
  `2026-09-02_t2216-...` §7-1 は `Backoff_` 時系列の直接記録を「新しい計算ノード用実行体を要するため
  範囲外」と書いていたが、**その実行体は 3〜5 日後に別 wave (2026-09-05 / 09-07) が着地させていた。**
  段 0 の棚卸しで気づくまで誰も更新していなかった。段 8 の改善候補へ回した。
- **親が段 1〜2 の待機中に自分で出した実測値を、逐語 file にして段 3 の両レンズへ渡した。
  その結果、親の解釈 2 件が倒れた。** `DW-S03` は「親自身の実測値とその一般化」を攻撃対象と
  書いているが、渡し方 (逐語 file を作って射影する) は書かれていない。段 8 の改善候補へ回した。
- **レビュー B が「合計の一致は同一性ではない」を指摘し、実測で裏付いた。** 468 走行の合計は
  101,857 = 101,857 で完全一致するのに、event 対では 260 件 (0.072%) 食い違う。
  相殺で合計が一致していた。親は当初この合計一致を根拠に報告しており、訂正した。
- **段 5 実装子 2 本が 1 往復まるごと空振りした。** 親が裁定文書を worktree 側にだけ置き、
  prompt では job dir の path を指していた。両方とも「読めなければ即停止」に従って正しく
  fail-closed し、作業ツリーへの変更はゼロ。file を配置し job-id を変えて再投入した。
- **計測が 1 度失敗した。** 投入用の detached submit-tree を `git worktree add --detach` で作った後、
  **submodule を初期化していなかった。** probe が外側 repo の HEAD を ccbench の HEAD と読み、
  pin 不一致で 17 秒で fail-closed した (job `986864.nqsv`、成果物 0 件)。
  初期化して `989505.nqsv` として再投入し成功。
- **変異 M3 が過剰決定だった。** `or retained != min(updates, 65_536)` の行ごと削除は、
  狙った関門に加えて行番号 pin も同時に壊す。`DW-M03` に従い行数を保つ形へ差し替えた。
- **行番号 pin の破れは静的レビュー 2 本とも見つけられず、親の焦点走が捕まえた。**
  `test_ccbench_spawn_sites.py` の deferred gate 台帳が probe の build 地点を行番号で固定しており、
  本 wave の追加で 57 行ずれて 15 件の define が未分類になった。
- 工数: codex 子 9 本 (plan 1 / consult 2 / author 2 / review 2 / fix 3)。
  うち author 2 本は上記の path 誤りで即停止したため実質 2 本を再投入した。

## 次の一手差分

### 完了

- [T-2188] 機序を確定した。更新窓が狭いと `Backoff_` が高域へ暴走し、その滞在先の静的性能が
  そのまま throughput になる。実測した滞在分布を既測の静的 `T(b)` へ時間加重で混ぜると、
  6 セルすべてで実測を −9.1% 〜 +4.7% で再現する。刻み 1 µs 固定で更新間隔だけ 10 → 2560 µs に
  すると `Backoff_` 中央値 88 → 6 µs、throughput 1.83 倍。材料は
  `output/insights/2026-09-09_t2188-nonmonotonic-mechanism/README.md`。
  remaining: none
  base: 7e426711773ace54f1539aca2b59c9bf56ef14cdd9fec9a924d8d1ff85ff556b

### 更新

- [T-2190] **P3・ユーザー裁定待ち**: 上流 CCBench への還元候補について、機序が確定した。
  非単調性は「更新窓が狭いと歩行が高い `Backoff_` へ暴走する」ことによる。
  したがって還元候補は刻みではなく**更新間隔**であり、材料は
  `output/insights/2026-09-09_t2188-nonmonotonic-mechanism/README.md` に更新。
  単一環境・単一 workload・正しさ未検査という限界は同文書 §5 に明記済み。
  base: a15b7a766986ce17238bcd26aa2773d03009140d1652daab6b6c873ef361b9f2

### 新規

- {{T:backoff-high-region-sign-behavior}} **P2・新規**: 高域 (`Backoff_` > 50 µs) での勾配符号の
  振る舞いを測る。本 wave の J1 は両条件が重なる低域 (12 辺、`Backoff_` <= 12 µs) しか見ておらず、
  そこでは差が +0.040 で不支持だった。高域は広窓側が 1 度も訪れないので比較対象が無い。
  比較を成立させる設計 (例えば広窓側の初期値を高域へ置く) から要る。
- {{T:static-tb-above-900us}} **P2・新規**: 静的 `T(b)` の b > 900 µs を測れるようにする。
  現符号化では b = 1000 が固定 0 へ復号される (F718)。本 wave の混合検算では
  `nm-step25` の 3.1%、`nm-step100` の 9.6% の時間がこの未測定領域に落ちており、
  そこを 900 µs の値で平坦に置いた。`2026-09-08_backoff-static-ceiling` が
  表現上限を 9999 µs へ広げているので、測る側の裁定だけが残っている。
- {{T:t2188-mixture-other-workloads}} **P3・新規**: 混合の検算を balanced / read-heavy でも行う。
  本 wave は write-heavy 48 スレッド 1 rep だけである。静的 `T(b)` は 3 workload とも既測なので、
  trace を 2 workload 分足せば閉じる。
