/dev-wave [T-2867] 関数単位の軸 (silo-function-policy、D2214) で「LLM 対 非 LLM 生成器」の対照を設計し、事前登録を起草する (D2259: B-5 v2
  は見送り、「なぜ LLM か」はこの軸で取り直す)。同じ評価数の予算で LLM と random 等を比べる。まず D2258 の実行契約 (1 評価 1 job、429
  の保留、LLM 親の起動器、report の v2 判定) を流用できるかを読んで確かめる。流用元は docs/b5-generator-contrast-preregistration-v2.md と
  output/insights/2026-09-26/t2797-b5-v2-prep/。そのうえで、事前登録の草稿と node 時間・LLM
  直列時間の見積りを作る。計算の投入はしない。発効はユーザー確認の後 (D2212 項 4)。driver・job body の実装は並走の [T-2865]
  の担当なので、orchestrator/campaign/p3_s4_loop_policy.py と tools/pegasus/ は編集しない。規律 2 を緩めない。本題だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree を作る。
  内訳: T-2867 は、codex の 2 巡目を投げた後に main へ着地した (D2259・entry 1880)。3 巡目の相談は手順で禁じられているため、codex
  の審査は受けていない。追加した根拠は 3 点ある。ユーザー裁定が直接指した後継であること、前提の段階 E が D2256
  で実装済みであること、計算なしの起草なので T-2865 と編集対象が重ならないこと。
