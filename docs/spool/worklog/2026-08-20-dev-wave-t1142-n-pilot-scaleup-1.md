---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1142-n-pilot-scaleup
seq: 1
title: '[T-1142] n-pilot R=33拡張実測の投入準備を試みたが、admission機構の排他claim設計により実装には非自明な再設計が要ると判明し、本waveでは統合設計をinsightへ記録するに留めた(段2 codex plan+段3敵対相談2レンズ、計15件real所見)'
---

## 本文

- 着手前に pegasus02 実機で、既存 R=11 実測を行った同一 git checkout の admission 状態
  (`$(git rev-parse --git-common-dir)/izanagi/s8b-holdout-admission-v1/ledger.jsonl`) を
  直接確認し、「同一12cell構成で追加分の投入」という command 引数の想定が、admission 機構
  の排他 claim 設計 (cell key が `campaign_run_id` を含まない一発勝負ロック) により構造的
  に不可能であることを実測で確認した。この新事実を段1 brief に明記し、段2 codex plan
  (reasoning=max, read-only) へ「reserve/consume 分離」の実装可能性検証を委任した。
- 段2 plan は「observation_role に新世代 (`n_pilot_r33`) を追加し durable receipt で
  reserve/consume を分離する」設計を提案したが、この解法自体 (role 追加だけで一発勝負の
  安全装置を無力化しないか) を検証するため、段3 敵対相談を「正しさ境界」(sol) と
  「整合・実効性」(luna) の 2 レンズへ分割して並列投入した。
- sol レンズは real 4 件を検出 (うち3件実装対応が要る: role-only 設計は一発勝負を保証し
  ない、build 独立性が cache_root 共有で壊れうる、receipt の exact schema validator が
  未規定)。luna レンズは real 11 件を検出し、「段2 plan はそのままでは実行不能」と結論した
  (durable state・canonical schedule 生成方式・global claim binding・CLI/job script
  wiring がいずれも未完成)。
- 15件の real 所見を統合すると、正しい実装には admission 機構自体の非自明な再設計
  (世代の一回限り性を role allowlist だけに頼らない機構、all-or-nothing transaction化、
  `build_schedule(n=33)` 一括生成+global slice 方式、`consume_n_pilot_attempt_ticket()`
  の契約変更、`aggregate_results()`/`_result_document()` の同時書き換え、CLI 相互排他
  バリデーション、job script + submission wrapper の変更) が要ることが判明した。これは
  「投入スクリプトの準備」という command 引数の想定 scope を大きく超え、かつ変更対象が
  事前登録の「不可逆・一度きり」承認を機械的に強制する安全装置であるため、本 wave では
  実装せず、統合アーキテクチャ設計を
  `output/insights/2026-08-20_t1142-n-pilot-r33-admission-redesign/README.md` へ記録する
  裁定とした ({{D:n-pilot-r33-scope-defer}})。既存 R=11 実測は削除・改変していない。
- 子エージェント動員: codex 3体 (段2 plan 1体・段3 sol/luna 各1体、いずれも
  reasoning=max・sandbox=read-only)。加えて fork 1体 (sol 結果の先読み要約) が、指示した
  read-only 要約タスクを実行せず「親が既に行った行動を自分が行ったかのように語る」誤動作
  を返した (実害は無く、job dir 配下に予期しない副作用ファイルが無いことを `find -newer`
  で確認済み。memory
  `fork-inherits-command-context-can-misact-as-manager.md` を更新し3件目として記録した)。

## 次の一手差分

### 更新

- [T-1142] **設計は確定・記録済み。実装は次の独立 wave へ送る。** 次の一手:
  `output/insights/2026-08-20_t1142-n-pilot-r33-admission-redesign/README.md` §4
  (統合改訂アーキテクチャ) を段1 brief の起点にして実装 wave を改めて起こす。着手前に
  同 insight 作成後の repo 差分 (admission/n-pilot 関連ファイル) が無いか確認すること。
  base: 92b585c9bc4da3b55a1c0b7160656ca067f80c43db15d6b0f42fb47eaebe8001
