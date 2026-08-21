---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: worktree-t1434-wave-d
seq: 1
---

## {{D:t1434-4-wave-d-apparatus}}. T-1434(4) Wave D は装置4面を完成させるが、T-189 の routing_evidence_status は inconclusive のまま確定させる

**決定:** `tools/codex_reasoning_ab.py` の Wave D 所有面 (`_validate_schedule` の
task/cache/requested_model/price_version schema、`_validate_verdict_row`/`append_verdicts`
の finding ID 盲検 union 化、`_aggregate_verified`/`_replay_manifest`/
`_aggregate_token_usage_observations` の task・stage・model・cache 軸拡張、`make_packets` の
動的 task count) を実装する。T-189 (`docs/phase3-t189-model-routing-preregistration.md`)
が要求する独立 custodian・oracle 凍結・cache 分離・price version・ITT 実質化・非劣性 margin の
6条件のうち、実データ・独立第三者・実測を要する部分 (§5.3 列挙の6項目) はいずれも本 wave の
scope 外のまま成立せず、実装完了後も `routing_evidence_status` (§12.1) は `inconclusive`、
same-owner custodian の結果は `apparatus_diagnostic` のまま確定する。cache 未制御時の
resource `not-applicable` 抑止ロジックは、gate 評価器自体 (§12 全体) が未実装のため本 wave では
実装しない。block 内で arm・model が両方同時に異なる pair を schema レベルで拒否すべきかは
未裁定のまま残す (現状は許容)。

**理由:**
- preregistration §5.2 の変更点表自体が、装置完成 (schema/集計/packet 化の model 軸拡張) を
  実装対象として明記しており、§5.3 の6項目 (証拠成立の条件) とは別の bar である。装置未完成の
  まま止める根拠にはならない。
- Wave A/B/C が同型パターン (機構は一般化、実データは POS/NEG のみ・cache/price は null 専用
  fail-closed) で3回実証済みであり、Wave A が用意した `normalize_schedule` 等の汎用層が
  未配線のまま放置される DW-G05 の成果物影響 (将来また同じ調査を要する) を避けられる。
- 段3敵対相談2レンズが「6条件不成立ゆえ絶対に実装しない」を独立に refuted と判定した。
  ITT の解析規約 (§4.1) や oracle の freeze/hash/bijection 整合性は既に装置内に存在し、
  未成立なのは実データ・独立第三者・実測部分に限られる。

**却下した選択肢:**
- 実装しない、設計メモに留める — DW-G04 (発火条件を満たす既存 artifact path) を満たしており
  (§5.2表 + Wave A 実装済みコード)、放置する理由が乏しい。
- cache 未制御時の resource `not-applicable` 抑止を先取り実装する — gate 評価器
  (`routing_evidence_status`/`confirmatory-go`/`confirmatory-no-go` の計算ロジック) 自体が
  無いままこの抑止だけを作ると「使われない飾り」になり規律5に反する。
- block 内 arm・model 両方同時変化を schema レベルで拒否する — preregistration は
  「主解析にしない」とのみ述べ拒否を要求していない。未裁定のまま許容側に倒すのが安全側の
  最小変更である。

段2 codex plan・段3 敵対相談2レンズ・段6 敵対レビュー2レンズが、当初 plan の block 検査
(「2つの arm」への一般化) が同一 arm・異なる model の pair を誤って拒否する blocker、
および `_validate_verdict_row` の finding ID 検査がモジュール固定集合に依存し task 汎用化が
閉じない blocker を独立に発見し、段4裁定で是正した。変異事前登録6件、baseline PASSED、
5/6 KILLED (1件は既知の node ID 登録制約で MISMATCH 確定、erratum は worklog 参照)。
受入 verdict=child-green。
