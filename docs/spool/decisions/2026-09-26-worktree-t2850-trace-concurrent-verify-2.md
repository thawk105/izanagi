---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-t2850-trace-concurrent-verify
seq: 2
---

## {{D:trial-v2-effect}}. 探索の独立反復の試走を、同時検査の実装に固定した cohort t2850-trial-v2 の 3 block・18 job として発効させる

**決定:** 事前登録 v1 (`docs/search-repetition-trial-preregistration.md`、raw SHA-256 `7501bd1f7f893801010dba2f93ceb45966badd11ed3e9e4a0aafa39f99d88206`) の試走を、
追補 1 (`5badbac61f62bf48d6448b6c473601a47dca15964cfa91d43a71d5cb99da7759`) と追補 2 (`docs/search-repetition-trial-preregistration-addendum-2.md`、
`62d3eade18feb6e8fd896b832cad77b02213f25696003311d48e98f6d37e43ab`) のとおり、次の値で発効させる (本登録 §10)。D2245 の発効 (cohort `t2850-trial-v1`) の
block 1 は追補 2 §5 のとおり予備走とし、以後その cohort に投入しない。

1. **計算確認 (D2212 項 4):** 2026-09-26、本決定の wave の最終報告で「試走 3 block (18 job) を見積り 22.2〜40.5 node 時間 (LLM の待ち 1.9〜19.5 時間) で投入してよいか」を
   問い、ユーザーは「いいよ」と答えた。費用上限は本登録 §9.2 の 200 node 時間のまま、job Elapse の総和が見積りの上側を超えそうなら新しい投入を止めて再確認する。
2. **実装の commit:** `299aa022ef08fca35ee4625e847cc25b49397ee6` (同時検査の実装 {{D:concurrent-local-verify-fork-receipt}} を取り込んだ main の fold commit。
   受入の tested tip `5fd096999` からの差は docs だけ)。job ごとに 1 本の repo 外の detached checkout で走らせ、以後の main の変更で動かさない。CCBench は campaign の pin `511c9538…`。
3. **配置:** cohort `t2850-trial-v2`、S1-wh × 5 手法 (random・sweep・bo・evolution・llm) × 系列 b = 1, 2, 3 + block job 3 = 18 job。系列番号 R = b (追補 1 §3)。
   A = 30、B = 10、N_eval = 5、block stock 5 session。walltime は系列 24:00:00、block job 08:53:30 (本登録 §4)。block 内の投入順は block 1 と同じ規則の順序
   (block 1 の spec の順序番号をそのまま使う)。時間帯の区切りを置かず (追補 2 §4、D2249)、18 job を block の順にまとめて投入する。
4. **LLM (K0) の親:** exact ID `claude-opus-5`、D2222 の起動契約と D2245 項 5 の再開型の起動器 (repo 外の `parent_driver.py`、sha256 `b1eba1bf…`) のまま。
   指示文 template は D2245 の写しの固定 commit を 2. に差し替えただけのもの (sha256 `ada47925…`)。1 系列 1 親、同時の親は 3 本 (D2216 の上限 4 以下)。
5. **投入の glue:** repo 外の v3 (期待 commit を引数で受ける、`submit.py` sha256 `0f1de5ee…`)。spec は `specs-trial-v2.json` (sha256 `ea83ce7b…`)。
6. **変えない値:** 手法の定数・BO の失敗集合・生成器・評価の exact 引数 (correctness は同時検査に変わった以外同じ)・較正 record は D2245 の発効束
   (`output/insights/2026-09-23/t2850-trial-effect-bundle/bundle/t2850-trial-effect-bundle.json`) のまま。
7. 記録と repo 外の成果物の所在は `output/insights/2026-09-26/t2850-trace-concurrent-verify/README.md` §6。

**理由:**
- 同時検査の実装の smoke で 5 session すべて certified・settled・品質正常を確かめ、見積りが 40.8〜58.2 → 22.2〜40.5 node 時間に下がった。ユーザーはこれで投入を認めた。
- job ごとに checkout を分けるのは、同じ checkout の build 領域を同時に使う job が build の claim で衝突しうるため (block 1 は 6 job で 1 本を共有した)。
- 固定 commit を受入済みの実装を含む最小の main の commit にし、後から main に入った別 wave の変更 (条件の意味検査など) を試走に混ぜない。

**却下した選択肢:**
- 旧 cohort `t2850-trial-v1` の block 2・3 として続ける — block 1 と実行方法 (所要) が違い、同じ cohort の系列を混ぜることになる (本登録 §3.1)。
- block の間に 1 時間を置く — D2249 の追加項で外した。
