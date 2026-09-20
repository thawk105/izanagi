# 段 4 裁定 (親、2026-09-20 21:2x JST) — 軽量版、段 2・3 省略

裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査 (21:1x JST): 本 wave 開始後の更新は第 26 回 verdicts (19:50) だけで、
K2 4 巡目の入力元に触れる裁定は無い (T-2795 §7 の pin 比較 = 据え置き、DW-O26 収載 = 採用、いずれも本件と独立)。承認済み裁定を覆す新事実なし。

## 段 1 の provisional 裁定 (P1〜P3) の確定

- (P1) real・採用: 3 巡稿 §5.1 を原本 sha256 の記録として採る。記録 wave の README の 2 文は insight の記載範囲について正しく、矛盾しない。
  本 wave は記録 wave の file を書き換えない (所有外)。差は insight §0・§1 に「埋まる」として書く。
- (P2) real・採用: `submit-tree-pair` の lock は裁定パッケージの付随項にし、本 wave は打たない (隔離 session の guard)。gate・台帳を足さない。
- (P3) real・採用: 「round 3 の `loop_state.json` からの再開」= 親の射影の入力元の問題。択 A / B / C を並べ、推奨 = A + 付随 1 項。

## scope 内 / 外

- scope 内 (実施済み): 対応表 (README §2)、裁定パッケージ (README §4)、phase3 項 4 の 1 行、worklog fragment ([T-2795] 更新)。
- scope 外 (実装せず insight に記録): digest の再描画 (未実測)、round 2 root の写しからの復元 + fresh rebuild、README stale 注記 (peer の編集面)、
  cleanup command の改訂 (記録 wave の別 T)、submit-tree-pair の lock (次の非隔離 session)。

## 変異 matrix

実装面 (D95 決定 2) の差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は免除しない (`dev_wave_wait.py acceptance`)。
実 repo を読むテスト = docs 系 (`check_docs`) と受入の全走。

## 段 6

一次資料から事実を再抽出する docs-only → read-only codex レビュー 1 本 (DW-C00)。レンズ 2 つを 1 本に: (a) §1・§2 の不在断定・sha 照合・
「bytes 一致 / 内容同一 / 値のみ」の区別が実測 log と一致するか、(b) §4 の推奨 (択 A) を通してはいけない最も強い理由 (成立しなければそう書く)。
