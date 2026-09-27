---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: dev-wave-t2726-t2727-pin-closure-recollect
seq: 1
title: [T-2726] [T-2727] dev-wave 手順 2 点 — DW-O09 の pin 閉包を module/file 名でも逆引きし、DW-S05-A で midflight gate の直後に段 1 の consumer 検索を local main で採り直す。L1.5 の予算は既存記述の空白削減で収め、上限は上げていない (docs のみ、branch dev-wave/t2726-t2727-pin-closure-recollect)
---

## 本文

- **依頼 2 点のうち (1) の半分は着地済みだった。** `DW-O09` には T-548 の段 8 (`b35d08435`) で「変更 file の変更前 sha256 で output/ も検索」
  「hit した test は中身を読む — 行番号・本数・live 比較の pin は一覧に出ない」が既に入っていた。純増は「path・module/file 名で `git grep -n`」だけ
  (full path の検索は、import 名や path 部品の連結で編集 file を指す test を拾わない。F370 の 2026-09-16 再発)。
- **(2) は既存の「gate実測NOTE≠0ならanchor再読」(D1180 項 3) と同じ行へ統合した。** 採り直しは NOTE の値によらず無条件で、検索対象は wave の木でなく local main
  (F1014 は main に着地した新 consumer を落とした事例)。
- **予算。** 着手時 (main `ad114fba0`) の実測は `DW-O09` 981/1000、L1.5 9690/9696。追記後は L1.5 が 70 bytes 超過した。
  D730 / D782 の第 1 段 (既存記述の削減) として、L1.5 の 13 節で「code span の外で日本語に隣接する半角空白」を除去し (意味不変、T-2778 の先例)、
  自分が足した文を縮めて 9695/9696・`DW-O09` 998/1000 に収めた。上限引き上げ・例外収容はしていない。
- **空白削減で踏んだもの 2 つ。** (a) 削減 script が箇条書きの `- ` の空白まで消した (`DW-S05-C` の 6 行)。差分目視で見つけて復元した。
  (b) check_docs が文言 pin 2 件を赤にした (`DW-O02` の「prompt 先頭は AGENTS.md の単独段例外と同形式。」、`DW-S06-A` の「実装面に Codex `role=author` のないハンク」)。
  2 行とも元に戻し、足りない 1 byte は pin の無い行 (`DW-S06-A` の「1本は`DW-S03`の過剰」) から取った。reasoning 文・`DW-O01` の待機行と経路行は最初から除外した。
- **pin 閉包 (`DW-O09` を自分に適用)。** 編集した 3 file (operations.md・workers.md・mutation.md) を path・名前・変更前 sha256 で逆引きした。sha の hit 0。
  名前の hit は check_docs 系・入口 command・launch authority (reasoning 値を実行時に導出、値は不変) だけ。合成 fixture は該当節の本文を `body` で置くので
  exact 節 pin の対象外で、Codex author と fixture placeholder の作法は発火しなかった。実装面の差分 0。
- **検査。** `python3 tools/check_docs.py` 違反なし (rc=0)。焦点走 3 file (`test_dev_wave_launch_authority.py`・`test_codex_worker_launch.py`・`test_check_docs.py`) 860 passed / 3 skipped (rc=0)。
  skip 3 件の個別名は `-q` で出ていない。実 repo を読む check_docs 正例は直叩きで代えた。provenance 全史監査 12970 件 違反なし。受入は本記録の commit 後に投げる。
- **段 6 read-only レビュー 1 本 (gpt-6-sol、medium、model call 4 回、48 秒): GO、must-fix 0。** 忠実性・非弱化・予算手順・scope の 4 レンズとも不成立。
  prompt・逐語資料・出力は `/work/1/SFC/tanab/dev-wave-jobs/t2726-t2727-pin-closure-recollect/review1/`。
- 軽量版: 段 2・3 は省いた (設計択一が割れず、正しさ防壁・受理集合に触れない docs のみ)。変異 matrix は実装面の差分 0 のため免除 (DW-S04)。
- 工数: codex 子 1 本 (review)。計算ノード job は焦点走 1 本と受入。

## 次の一手差分

### 完了

- [T-2726] `DW-O09` の着手前 `git grep -n` を「path・module/file 名で」に広げた。hit した test の中身で行番号・本数・live 比較の pin を読む義務と、
  変更前 sha256 の逆引きは T-548 で既に入っていたので、合わせて F370 の追加検索形が閉じた。
  remaining: none
  base: 2cd6f6db7e06a2f993e8f458330665bb7cfbfff9b18f21617107beb534b9493f
- [T-2727] `DW-S05-A` に「(midflight gate の) 直後に段1のconsumer検索をlocal mainで再走し差を裁定へ(F1014)」を足した。NOTE≠0 の anchor 再読と同じ行に置いた。
  remaining: none
  base: 75a16804551fe354885ddceb03b6af8916a2c878d4f2dcc1a92d3d3a2454c0f3
