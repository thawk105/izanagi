---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2483-exact62-historical-grammar
seq: 1
title: [T-2483] exact-62 の旧閉包 grammar を歴史閲覧 decoder へ収載し、実在 3 本が読めることを実測した (コード + テスト + docs、branch worktree-dev-wave-t2483-exact62-historical-grammar、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「exact-62 の campaign lock を読む経路を用意する。対象は既知の 3 本に限定。
  [T-2125] と [T-2117] が同じ読取り層に触るので段 1 で編集面の重複を実測し、重なるなら順番を決める。
  本題の読取り経路だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **依頼が求めた編集面の重複は実測で 0 だった。** [T-2117] の実体は `tools/codex_reasoning_ab.py` の
  session pin で、lock の読取り層への参照は 0 件。[T-2125] は同じ `artifact_admission.py` だが別関数
  (`require_admitted_campaign` 内の現行 policy 照合) で、対象 3 本の `build_admission` は測定時の
  `_current_policy().as_preimage()` と正規化 sha256 `949ddcc295…` で一致しており現に発火しない。
  他 wave も 114 branch・116 worktree すべてで対象 2 file に差分ゼロ。順番の制約は無かった。
- **段 1 で活動ごと止める裁定を探し、逆に活動を許す裁定を見つけた。** D1653 が
  「収載する grammar は実在 corpus が確認できたものだけ」と定めており、`docs/phase3.md` の見送り項
  [T-2345] はその条件が成立しない 5 grammar を止めている。exact-62 はその 5 件に含まれず、
  実在 corpus 3 本を観測済みで条件が成立する側だった。D1653 は別入口・別返却型・exact ordered tuple
  識別・独立 literal・全 path digest 照合・grammar 固有 scope という必須条件まで確定していたので、
  本 wave はその条件を exact-62 へ実体化しただけで新しい方針は作っていない。
- **親の brief が段 3・段 6 で 2 度縮んだ。**
  (a) 不変条件に書いた「現行 63 から 1 path 落とした 62 を未知 grammar として使う既存テストの
  差し替え」は空振りだった。既存の unknown-grammar 変異はすべて pre-T733 24 を土台にしており、
  62 path を未知として使うテストは 0 件。実在した接点は同じ形の parameter を持つ**通常 decoder の**
  拒否テストで、これは維持すべきものだった (段 6 レンズ A が確認)。
  (b) 「読めるようになる」の範囲は中央の歴史閲覧 API までで、材料レポート経路は含まない。
  段 3 レンズ B が `layer3_report._read_campaign_lock` の無条件な通常 decoder 呼び出しを指摘し、
  親が現物で確認した。scope 外として新規項目へ送った。
- **段 6 レンズ B の must-fix が実測で裏づけられた。** 「期待 epoch を期待 path 列から再計算すると
  本体と期待値を同時に並べ替えても緑になる」という指摘に従い、固定文字列で置くことを段 4 で必須にした。
  変異本走で「62 literal の宣言順を 2 要素入れ替える」変異がちょうど 4 node を落としており、
  この固定値が実際に検出している。
- **変異 1 件が生存し、再照準した。** 当初の M08 (歴史 epoch の scope 組が既知 2 種以外のときに
  raise する else 枝の除去) は SURVIVED だった。`HistoricalCampaignVerifierEpoch.__post_init__` の
  scope 白名単が先に塞ぐため到達不能な冗長 gate である。DW-M02 に従い実効 gate
  (exact-62 の scope に対する expected_paths の割り当て) へ再照準した M08R は 2 node を落とした。
  初回の SURVIVED は erratum として insight に残した。
- **段 5 の実装子はテストを 1 件も実走できなかった。** sandbox から計算ノードへの投入が
  `NQSconnect: [API EACCTAUTH] Unknown user-id (uid: 31609)` で 3 回とも停止し、
  `child_started=false` の rc=16 になった。実装は静的検査だけで報告され、テスト実測は親が行った。
- 実在 3 本の検証 script は Codex `role=author` に書かせ、親が repo 外へ退避して実行した。
  実行形は repo へ入れず、逐語を insight の `verbatim/real-corpus-probe-script.md` に残した。

## 次の一手差分

### 完了

- [T-2483] exact-62 の歴史 grammar を収載し、実在 3 本 (t2364-20260907b の rr5 / rr50、
  a6-20260908b の rr95) が歴史 decode・歴史 epoch・歴史 admission の 3 段すべてを通ることを実測した。
  同じ 3 本は認証経路では `ArtifactAdmissionError` で拒否され、exact-24 の既存 lock も従来どおり読める。
  lock と WAL の bytes は実行前後で不変。逐語は
  `output/insights/2026-09-16_t2483-exact62-historical-grammar/`。
  remaining: none
  base: e9602eb666d35892322c96a1fd2c4b1e6268d7235e5ad253ec1416a17df3044f

### 新規

- {{T:layer3-report-ignores-read-purpose}} **P2・新規**: `layer3_report._read_campaign_lock`
  (`orchestrator/campaign/layer3_report.py`) が `purpose` を見ず `decode_campaign_lock` を
  無条件に呼ぶため、中央の歴史閲覧 admission を通った lock でも材料レポート生成段で再拒否される。
  [T-2483] で exact-62 が中央 API から読めるようになった後も、この経路からは読めないままである。
  段 3 のレンズ B が指摘し親が現物で確認したが、読取り経路の本題を超えるので scope 外とした。
  成果物影響 = 歴史閲覧用途の材料レポートが、中央 admission が受理した記録に対して生成できない。
