# 段 4 裁定 — [T-2232 後続] 初回投入

軽量版のため段 2・3 は省いた (設計択一が割れず、正しさ防壁に触れず、受理集合を変えない)。

## C1 — 依頼本文は stale carry (real、採用)

[T-2232] の実装は 2026-09-07 03:19 に main へ着地済み。land 受領証・ancestry・worklog (1286)・
insight README・変異 16/16 KILLED をすべて一次資料で照合した。**再実装しない。**

## C2 — scope を依存項目へ繰り上げる (real、採用)

`DW-S01` / F35 に従い、台帳が名指しする残件「初回投入と reservation / attestation の実効確認は
後続 wave」を本 wave の scope にする。F660 (新規 Pegasus 実行体は登録した wave で投入できない) は
登録が main へ着地した時点で解けている。

## C3 — 実装面の差分ゼロを既定とする (採用)

`DW-S04` により実装面の差分ゼロなら変異 matrix を免除する。**受入全走は免除しない。**
実測で欠陥が出た場合、修正の要否は実測結果を見てから再裁定する。修正すると裁定した場合だけ
Codex `role=author` の実装子を起こし、変異事前登録 (`DW-M01`) をその時点で行う。

## C4 — 割れたら記録して止める (採用)

依頼本文の最後の制約をそのまま採る。attestation の exact 照合、reservation 束縛、claim root の
provisioning が割れた場合、**推測で迂回する変更を実装しない。**再現条件 (投入 argv、job ID、
環境、停止した行) と停止点を insight へ記録し、修正の設計は裁定パッケージへ送る。

## C5 — 投入は 1 本に限る (採用)

fixture 経路 (`--value 20`) の 1 本だけ投入する。gen_S は RUN 24 / QUE 9 で混雑しており、
複数本の同時投入は queue を塞ぐだけで得られる情報が増えない。割れた層が判明したら、
その層より前を通過することは既に示されている。

## plan v2 (親が実行する手順)

1. 固定 SHA の専用 checkout を job dir 配下に detached worktree として作り submodule を初期化する
2. `fetch_third_party.py hydrate` で `.source_root` を得る
3. evidence root を job dir 配下 (= 全 repository の外) に作る
4. README §7 の tagged qsub command の形で 1 本投入する
5. 完了を待ち、evidence root の全成果物と `job.stdout` / `job.stderr` を読む
6. 通った層と止まった層を記録する

## 変異事前登録

実装面の差分ゼロのため免除 (`DW-S04`)。差分が生じた時点で `DW-M01` に従い登録する。
