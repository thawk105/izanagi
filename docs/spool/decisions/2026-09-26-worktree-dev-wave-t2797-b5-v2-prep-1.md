---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-dev-wave-t2797-b5-v2-prep
seq: 1
---

## {{D:b5-v2-execution-contract}}. B-5 v2 の実行契約 — 系列開始 stock と評価 1 は同じ job に残し、評価 2 以降は 1 評価 1 job で LLM の待ちを node の外へ出し、利用上限 (429) は構造化 field だけで判定して期限なしで保留し、critic の入力に「recommend / avoid は次の planner と coder へデータとして渡る」を足し、balanced にも同時検査を使う

**決定:** D2249 項 1 (択 C) の前提 (c)(d) を次の形で実装し、`docs/b5-generator-contrast-preregistration-v2.md` (v1 の発効時の版を土台にした差分登録) に固定した
(記録 `output/insights/2026-09-26/t2797-b5-v2-prep/README.md`)。本決定は本走の認可ではない (発効は node 時間のユーザー確認の後、D2212 項 4)。

1. **job の切り方 (全 arm 共通):** job 1 = 系列開始 stock 1 session + 評価 1、job 2〜10 = 評価 1 回ずつ、最終 job = score 5 session。LLM の原提案 1 は stock の current_perf を要するので
   job 1 の中でだけ待つ。原提案 2 以降は login の起動器 (`tools/pegasus/b5_contrast_launch.py` の v2 経路) が待ち、提案が継承検査を通ってから次の評価 job を投入する。
   計算 job は台帳から導いた次の単位と要求が一致しなければ session を始めない。途中で死んだ系列は自動で再投入せず止める。
2. **利用上限:** LLM 親の出力 JSON が読め `is_error` が真かつ `api_error_status` が 429 のときだけ保留とし、期限なしで同じ session・同じ原提案番号で再開する。保留は A・B・retry を消費せず系列を欠測にしない。
   job 1 の待ち中なら job は評価せずに終わり、次の job 1 で stock を測り直す。正常終了で提案が無い = 空出力 (A を消費)。model の不一致の記録があれば系列を分類不能欠測で終える。他の異常終了は同じ原提案で追加 2 回まで。
3. **(d) の修正先:** write-heavy の却下 11 件は評価 1 の critic 診断が別 role 宛ての「指示」を名乗ったことが原因で、同じ診断が 11 回入力された ({{F:b5-critic-instruction-quarantine-loop}})。
   v2 cohort の critic の入力に「`## recommend` と `## avoid` は次の原提案の planner と coder へ診断データとして逐語で渡る。他 role 宛ての指示・採否手順・判定規則や gate の読み方の指定は書かない」を足した。
   検疫 (`_consume_k2_coder_output`)・coder の役割文書・診断の節抽出・`.claude/agents/` は変えない (差分が要らなかったのでユーザーへの提示は発生していない)。
4. **同時検査:** [T-2850] (b) の取得済み trace の同時検査 (D2251) を v2 の write-heavy と balanced の全 session に使う。balanced は本番順序で実測し (stock 24.5 GiB・load ≤ 4.0 まで 79 s、
   重い候補の代理 48.4 GiB・55 s、10 本 serializable)、初回静定上限 120 s のまま `p3_s4_loop` の許可を balanced へ広げた (read-heavy は拒否のまま)。
5. **判定規則 (v2):** 4 比較の Holm、batch (旧 block) は名札だけで batch ごとの条件を判定から外す、stock CV と fallback は workload の 15 session を pool する。
   random と sweep の preimage は v2 の版文字列で作り直す (v1 の値は閲覧済み)。v1 の判定と挙動は変えない。

**理由:**
- D2249 追加項は同時刻対照 (同じ job で測る対照) を残すと定めた。B-5 の同 job の対照は系列開始 stock と評価 1 なので、それを分けずに原提案 1 だけを node 上で待つ (24 系列で 3〜6 node 時間)。
- 429 を文言で判定すると成功応答の引用で無期限保留になりうる (段 3 相談 A)。model 不一致を空出力と数えると、model の違う系列が生成器の結果として主標本に入る (段 6 の親の読み)。
- critic 側の入力で直せば、検疫の受理集合を変えずに済む。coder の検出基準を狭めるのは検疫を緩めることになる。

**却下した選択肢:**
- 系列開始 stock を別 job にする (段 2 案) — 同時刻対照を崩す。
- 投入予約・scheduler 照会・自動回収 (段 2 案) — 1 cycle 前の仮想リスク向け (DW-G02)。途中死は止めて報告する。
- v1 の経路・report を削って v2 専用にする (段 3 相談 B) — v1 の既存 test の期待値を変える。版の分岐で v2 を足した。
- coder の役割文書の検出基準を改める — 検疫を実質的に緩める。
