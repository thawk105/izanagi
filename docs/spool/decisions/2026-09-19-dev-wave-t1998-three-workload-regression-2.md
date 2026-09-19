---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-19
wave: dev-wave-t1998-three-workload-regression
seq: 2
---

## {{D:b7-fixed5-three-workload-regression-authorization}}. 採用候補 fixed 5 µs を 3 workload で同時期に測り、D1639 の床値で退行を判定する — B-7 充足の判定はしない

**決定 (ユーザー裁定、2026-09-19):** 採用候補 1 本を 3 workload で同一 build・同時期に走らせ、床値超の退行を判定する。
「候補 = `docs/t1998-balanced-stock-inline-preregistration.md` の採用 arm、床値 = D1639 の between-run noise floor (3 workload)、
判定 = 各 workload で候補 vs stock の対差が −floor を下回れば退行、結果は退行込みで 3 workload 全件を報告する。B-7 要件充足の判定は
本 wave でしない (D2044 項 3 維持)」。機構は A-2 (write-heavy / balanced) と A-6 (read-heavy) の certification 経路
(`orchestrator/campaign/paper_story_a2_certification.py` 系) を descriptive に使い、3 workload を条件で割って複数ノードへ同時投入し、
同時刻の stock 対照を各 workload に置く。既存材料 (`results/2026-09-16-b7-three-run-materials.md`) と併記し、プールしない。
成果は results 系列稿 1 本と図の材料。規律 2 (anomaly が出た候補は即 reject) は緩めない。
scope 外は certification の昇格・新 protocol・追加 gate。

**実装の形 (AI の段 4 裁定、本決定の範囲内):**
- A-6 追加 (60605bec3) と同形で、新 study `paper-story-b7-fixed5-regression` (rr5 / rr50 / rr95 × stock / fixed5 の 6 cell、
  全 workload の `adopted_backoff_us` = 5、nodes 5 / walltime 12:00:00) を shipped policy の closed set へ 1 path 足す。
  既存 A-2 / A-6 policy・job body・partial 完了の exact two-workload 境界・正しさ gate は変えない。
  protocol SHA-256 は study・workloads・cells を preimage に含むので新 study の値は新しくなるが、これは「既存 protocol schema の
  別 study instance」であって新しい判定手順ではない。
- 「同一 build」は「同一候補・同一ソース条件 (genome・controlled define・toolchain・patch 適用下の source bytes digest) から
  workload ごとに別 build」と読む。binary の同一性は主張しない。
- 判定規則は結果を見る前に固定する: `effect_w` = 機構の `effects[w]` (5 標本 median の比 − 1、未丸め)、
  `floor_w` = 床値 JSON の `between_run.cv` の全桁、`regression_w ⇔ effect_w < −floor_w` (strict)。effect が無い workload は理由付きで
  判定不能、anomaly は別欄。「退行なし」は優越でも差が無いことの証明でもない。outer status と `a4_noise_floor_status` は機構の
  出力として写すだけで書き換えない。床値判定はコードに入れず稿で計算する (追加 gate を作らない)。
- 再投入は基盤要因の失敗に限り同じ commit・同じ policy で attempt id を変えて 1 回だけ。科学的要因 (anomaly・reject・unstable・
  source unbound) では再投入しない。1〜2 workload が欠けたら partial 対応を足さず、予定成果は未達と明記する。

**理由:**
- 論文の失敗条件 (e) は「target workload では勝つが他の workload で floor 超の退行がある → 退行込みで全 workload を報告する」と
  定めるが、既存材料 (2026-09-14 / 09-16 稿、A-1 sized attempt-0001) は workload ごとに別の採用値を別 attempt で測ったもので、
  D2044 項 3 が「同一 variant の横断比較と床値超の判定を供給していない」と確定していた。同一候補の同時期測定 + 床値判定が純増である。
- 既存の certification 経路は正しさ検査 (trace-enabled 別 build、legacy 1 + performance 5) と trace-disabled 性能測定の分離、
  source binding、条件関門を備えており、descriptive に使うだけで新しい protocol や gate を要しない。
- 床値と対差の直接比較は D1639 が定める量 (「差が信用できるかの下限、compare の丸め閾値」) の記述的な用法であり、
  √2 補正や有意差判定へ広げない。

**却下した選択肢:**
- 既存 2 policy (A-2 の 10 / 5 µs、A-6 の 2 µs) をそのまま使う — 同一候補の横断にならない。
- A-1 paired (30 対の交互配置) で測る — ユーザーが機構を A-2 / A-6 経路に指定しており、成果物の形 (certification 経路の
  権威 bytes) も異なる。
- login で 1 度 build して 3 node へ配る「同一 binary」 — 既存機構に無く新 protocol になる。
- 3-workload の partial 完了対応・plotter の拡張・A-2 / A-6 policy の変更・bench.lock の変更 — scope 外 (要求外の一般化)。
