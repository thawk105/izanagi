---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1025-allowlist-writers
seq: 3
---

## 新規

### {{F:adversarial-lens-classifier-refusal}}. 敵対レンズ子が上流分類器に拒否され 2 回とも出力ゼロで死んだ [セッション死・救出]

- 事象: 段 3 の敵対レンズ A が 2 回連続で rc=1・出力 0 bytes で終了した。1 回目は
  guard 自身が `python3 -c` での判定直叩きを (設計どおり) 拒否し、子が測定手段を失って停止。
  親が repo 外の判定 runner を用意して 2 回目を投入したところ、今度は上流の分類器が
  「cybersecurity risk」として `turn.failed` を返し、828 秒 / model call 16 / 出力 30,797 token が
  全損した。`evidence_status` は `complete` で、receipt からは正常終了と区別が付かない。
- 根本原因: (1) 防壁を狭める wave の敵対レンズは、本質的に「迂回コマンドを列挙して実測する」
  作業になる。prompt 冒頭に防御目的を明記しても、**作業内容そのもの**が分類器の閾値を越える。
  (2) 防壁を検査する子に、防壁自身が拒否する測定手段しか渡していなかった。
- 恒久対応: {{D:hooks-edit-route}} と同 wave の運用で、(a) 判定の実測は**親が repo 外に置いた
  runner を script file 実行で渡す** (`python3 <runner> <repo> bash "<cmd>"` は allowlist を
  通るため、防壁を迂回せずに測れる)、(b) 迂回列挙型のレンズは段 3 で単独に投げず、
  段 6 のレビューへ**中立な適合性検査**として畳み込む。memory
  `codex-adversarial-prompt-defensive-framing` に「防御目的の明記だけでは足りない」を追記する。
- 再発検知: 子の receipt で `codex_exit_code=1` かつ `output_bytes=0` かつ
  `evidence_status=complete` の組み合わせを、events の `turn.failed` まで開いて分類する
  (rc だけでは web 検索由来の全損と区別できない)。

### {{F:predicate-widening-revives-fixed-false-positives}}. 判定述語を上位集合へ差し替えて過去に潰した false positive が 2 件戻った [ドリフト]

- 事象: 防壁の受理集合を狭める実装が、末端判定の述語を上位集合 (campaign tree と ccbench tree の
  祖先を含む) へ差し替えた。結果、`echo external deps: $(nproc) cores` (防護対象の字面を
  含まない mention 語 + 不透明構文) と `tee output/campaigns/c` (official campaign root への
  旧受理) が拒否されるようになった。どちらも過去の敵対レビューで明示的に潰した
  false positive であり、回帰テストが両方を捕まえた。
- 根本原因: 述語を「より広く判定するもの」へ置き換えると、狭める方向の変更としては
  一見安全に見えるが、**過去の FP 修正が依存していた境界**が同時に消える。
  さらに token を記号で分割して候補を作ったため、散文中の裸単語 `external` / `output` まで
  「防護対象に触れた」と判定された。
- 恒久対応: 述語は元の 3 つ (末端 regex / hooks subtree / namespace marker) に戻し、
  option 値と inline program 内の path fragment 抽出だけを残した。加えて
  {{D:acceptance-set-reversal-check}} で、受理集合を変える wave に wave 前との反転検査を課す。
- 再発検知: `orchestrator/tests/test_hooks.py` の
  `test_bash_false_positive_fixes_allowed` と
  `test_bash_official_campaign_root_direct_writers_keep_legacy_acceptance` (両方ともこの
  再発を実際に赤で検出した)。加えて反転検査の `WIDENED=0` 要求。
