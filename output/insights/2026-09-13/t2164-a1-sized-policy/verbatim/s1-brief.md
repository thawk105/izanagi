# 段 1 brief — A-1 sizing 証明書の生成と本走 policy の凍結

**研究前進.** 論文の但し書き A-1 (均衡 5-rep 配置での variant−baseline 差) の本走は、反復数を決める
証明書が無く、本走 policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` が不在のため
起動できない。pilot attempt-0004 は 2026-09-11 に全 3 workload valid で完走し、材料は揃っている。
完了判定 = (a) 証明書が `status=selected`、(b) 独立実装の replay receipt が通る、
(c) sized policy が `_validate_policy_v3_semantics` / `load_policy` を通る、
(d) 本走が未投入で [T-1505] の人間認可待ちであることが成果物本文に明記される。

**確定済みユーザー裁定.** D1296 (本番機構の pilot から反復数を取り直す)、D1452 (反復数を決める道具の
受理範囲は証明書側で照合する)、[T-1505] (正式測定の認可は人間手番のまま)、D95 (実装面は Codex author)。
本 wave の引数で確定: 凍結済みの式・確率・候補・種の定義域・停止規則に触らない。pilot からは scale だけを
取る。性能の優劣も headline も主張しない。本走の投入をしない。

**scope (純増分のみ).**
1. 証明書生成 — `tools/size_paper_story_a1_balanced.py` に登録値だけを渡す。root seed
   `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3`、探索 20,000、認証 100,000、
   候補 `28..4096` (事前登録 §5.5 の逐語)。
2. 検証 — `tools/verify_paper_story_a1_balanced_sizing.py` の replay receipt。
3. sized 事前登録 README (人間可読の正本) を新規 insight dir へ置く。
4. `paper_story_a1_paired.v3-sized.json` (機械可読の正本) を Codex author が書く。
5. driver の `V3_SIZED_PREREGISTRATION_RELATIVE_PATH` / `V3_SIZED_PREREGISTRATION_SHA256` を None から実値へ。
6. (P1-1) D1452 の consumer 側照合 — 証明書の `policy.search.trials` / `policy.certification.trials` /
   `policy.candidate_grid.{registered_minimum,maximum}` / `policy.root_seed.digest` を登録値と exact 比較する。

**不変条件.** 規律 2 を緩めない (anomaly を出す variant の即 reject は不変)。pilot 観測値を最終推定へ混ぜない。
pilot 成果物 dir (create-only で publish 済み) の下へ書かない。`tools/size_*` `tools/verify_*` の式・確率・
候補・seed・停止規則を変えない。既存 golden `test_legacy_frozen_bytes_have_independent_literal_goldens` は
headline dir の file 集合を exact 固定しているので、新規 dir を使い触れない。

**割れうる前提 (親の provisional 裁定、段 3 の攻撃対象).**
- **(P1-1)** D1452 を本 wave で閉じる。理由: 本走 policy の凍結が実効を持つかを直接決める裁定済み項目で、
  仮想リスクではない。攻撃点: 引数の「本題だけ」を超えるか。道具側ではなく consumer 側だけで閉じられるか。
- **(P1-2)** 成果物の置き場は新規 dir `output/insights/2026-09-13_paper-story-a1-balanced5-sized-preregistration/`
  とし、README / 証明書 / replay receipt を同居させる。先例は headline の 2026-08-27 dir。
- **(P1-3)** sized policy の `authority` は `formal=true` / `promotion_prohibited=false` /
  `result_authority` を本走用に置く。攻撃点: 認可前に formal を宣言することが昇格に当たるか。
  代案は pilot と同じ `formal=false` のまま凍結し、認可時に別版へ差し替える。
- **(P1-4)** `schedule_root_seed` は workload ごとに pilot と別の値を新規に凍結する。攻撃点: pilot と
  同じ seed を使い回すと本走の物理順が pilot と相関する。導出規則を本文へ書けるか。
- **(P1-5)** `durable_measurement_base` / `materialization_relative_path` は本走専用の新しい path を凍結する。

**成果物の形.** (i) 新規 insight dir の README.md (sized 事前登録、`authority: preregistration`)、
sizing-certificate.json、sizing-replay-receipt.json。(ii) `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`。
(iii) driver の 2 pin (+ P1-1 採用時は照合 1 箇所とその正例・負例テスト)。(iv) worklog / phase3 / decisions。

**受入・実測環境.** 計測は無い。証明書生成は login node の純 numpy 計算で、実測 1.1 秒 (探索 200 / 認証 1000)
から本番値でも数分。受入全走は既存 acceptance 経路 (`tools/dev_wave_wait.py acceptance --lease-optional`)。

**変更面の実アンカー.**
- `orchestrator/campaign/paper_story_a1_paired.py:212-213` (sized 事前登録 pin、現在 None)
- `orchestrator/campaign/paper_story_a1_paired.py:1292-1387` (`_validate_v3_sized_certificate`、P1-1 の差し込み先)
- `orchestrator/campaign/paper_story_a1_paired.v3-sized.json` (新規)
- `orchestrator/tests/test_paper_story_a1_paired.py:1012-1095` (sized 形の既存テスト)
- `output/insights/2026-09-13_paper-story-a1-balanced5-sized-preregistration/` (新規)

**並列分割方針.** 段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A = 凍結・事前登録の拘束と規律 2、
レンズ B = consumer 契約と受理集合)。段 5 は実装子 1 本 (所有 = orchestrator 配下の実装面)。
親は証明書生成・検証・docs・commit・受入・land を担う。
