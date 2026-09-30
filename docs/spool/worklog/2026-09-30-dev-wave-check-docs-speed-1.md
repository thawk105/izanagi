---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-check-docs-speed
seq: 1
title: check_docs.py を判定を変えずに約 2.4 倍速くした — 計算ノードの同時刻対照で wall 中央値 37.49 秒 → 15.52 秒、旧版との出力一致を main の現物・故障 6 種・全 fixture で確かめた (コード + test + insight、branch worktree-dev-wave-check-docs-speed)
---

## 本文

- 依頼: md_5 (`/work/1/SFC/tanab/tmp/speedup-2026-09-29/md_5.txt`、共通指示 common.txt)。2026-09-29 のユーザー依頼「日常の営みを高速化」の 1 本。一次資料 `output/insights/2026-09-30/check-docs-speed/README.md`。
- 律速 (計算ノードで取り直した profile): `_check_backlog_guard` が 91% で、行番号の先頭からの数え直し・同じ entry 本文の再解析・archive 全ペアの正規表現解析という CPU 処理だった。依頼文にあった「stat で約 25 秒」は login での観測で、計算ノードでは stat 2.9 万回で 1.4 秒。login の wall は半分以上が I/O 待ちで、今回は縮めていない。
- 結果: 同じ node で旧/新を交互に 5 回ずつ (bnode007) — wall 中央値 旧 37.49 秒 (37.29〜37.60) → 新 15.52 秒 (15.51〜15.91)、比 0.414。最大常駐メモリ +3.0% (309,044 → 318,288 KiB)。
- 判定不変: main の現物と故障 6 種の木で rc・stdout・stderr が bytes 一致 (故障はすべて検査に届いたことを確認)、test_check_docs.py の全 583 node の結果と checker 呼出し 727 回の rc・出力が一致 (差分 3 件はテストが渡す transaction id の値だけで、旧同士でも走ごとに変わる値)、旧実装との網羅対照 test、変異 8 件が事前登録どおり (KILLED 7 + 等価 1)。
- 途中で見つけて直したもの: (1) 追加 test を hold 呼出しの後ろに置いて hold 契約 test が赤 → fix 第 1 巡で移動。(2) probe の故障 3 種が検査に届いておらず判定不変の証拠にならなかった → 故障の入れ方を直して取り直した。(3) 最初の版が最大常駐メモリを +61 MiB 増やしていた (archive 先頭 entry の ID 約 84 万件が別実体の文字列) → `sys.intern` で共有する fix 第 2 巡で +3.0% に戻した。
- 棄却した所見: 段 3 相談 B の「O3 (raw slice) と O4 (順序検査) を初回から外す」は、純関数で網羅対照 test により等価を示せ、cache の寿命問題もない局所計算にできるので採用した (反例の提示は無かった)。段 6 レビュー A の「T4 の断片 assert を全文比較に」は、全文比較を repo 外 probe で行ったので不採用。
- 計算資源: 計算ノードの job Elapse 合計 5,782 秒 (約 1.61 node 時間、受入を除く)。Codex 子: 相談 2・実装 2 (本体 1、probe 1)・レビュー 2・fix 3 (本体 2、probe 1)・焦点再レビュー 1。

## 次の一手差分

### 新規

- {{T:check-docs-carry-scan}} **P3・新規**: check_docs.py に残る成長比例の項を縮める。最終版でも `_check_backlog_guard` が cProfile 下 30.9 / 34.7 秒を占め、carry 参照 958,894 件の走査 (15.3 秒) が entry 数 × active な T の数に比例して伸びる。候補は (1) 同じ「次の一手」節の 3 重解析を 1 回に (`_iter_carry_references` の逐次性を観測する既存 test を保つ設計)、(2) carry ごとの raw slice と sha256 を既知不一致の照合が要る場合だけ求める、(3) 凍結済み archive の走査結果を内容 hash で再利用する (実行をまたぐ cache なので無効化条件の設計から)。根拠: `output/insights/2026-09-30/check-docs-speed/README.md` の「残る成長比例の項と次の一手」。
