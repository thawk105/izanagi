---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2005-b4-projection-registration
seq: 1
title: [T-2005] B-4 projection 登録の機構と規範を閉じ、値は宣言源の不在で止めた (code + docs + insight、branch worktree-dev-wave-t2005-b4-projection-registration、変異 8/8 KILLED)
---

## 本文

- 依頼は 3 driver の projection closure hash を事前登録と admission record へ登録することで、
  「凍結物の再発行が要るなら権限が既存枠内で閉じるかを先に実測し、閉じないなら不足を記録して
  停止する (新しい権限主体を作らない)」という条件が付いていた。**閉じたのは機構と規範だけで、
  値は登録していない。** 停止理由は 1 点に絞れた。
- **凍結物の再発行は要らなかった。** 事前登録文書は §0 が自ら発効前 draft と宣言し、
  `check_docs.py` も living 扱いにする。`p3_b4_analysis_prereg_consumer` が exact pin する
  §5.1.1 の raw / semantic sha256 は §5 の表と §5.1 の当該項目を編集しても不変であることを
  編集前後の実測で確認した。bytes を pin する commit 済み record も存在しない。
  **この結論は最初の record を発行する前の一時点に限る。**
- **`expected_claude_model_snapshot` だけが repository から導出できない。** 実 CLI 応答の
  `modelUsage` が返す exact slug は走らせる時期で変わり、本 repo の成果物には
  `claude-opus-5[1m]` と `claude-opus-4-8` の両方が実在する。docs 全体を検索しても宣言源・
  承認者を定める規範は無い (同 field への言及は D998 の 1 箇所のみ)。事前登録 §0 は部分記入の
  例外を「実行責任者・開始時刻」1 行に限るため、同じセルの prompt hash と projection hash も
  同時に記入できない。**値を書けば新しい権限主体を作ることになるので停止した。**
- **親の段 4 裁定が受理集合を広げていた。** 親は「文書 3 値が live と一致し record 値が選択
  driver の live と一致すれば対応は導ける」として verifier へ driver 種別を渡さない設計を採ったが、
  これは pair 経路しか見ていなかった。起動器の bootstrap は同 verifier しか通らず、
  変更前はそこで record と文書の projection が照合されていた。段 6 の敵対レビューが指摘し、
  親が実測で裏取りして裁定を訂正した。{{F:verifier-moved-check-strands-single-caller-path}}
- **fix 子が文書に合わせて実装を緩めた。** 「文書の記述が実装より広い」という所見に対し、
  実装を広げる向き (model の接頭辞要求を落とし hash に大文字を許す) で解決していた。
  焦点再レビューが指摘し、狭める向きへ戻した。{{F:doc-implementation-mismatch-resolved-by-widening}}
- 段 3 の 2 レンズは独立に「§5 の値欄を本 wave で埋めてはならない」へ到達した。D1060 は
  当該 wave 限定の裁定だが、以後の wave へ記入の権限を与えるものでもない。正しいのは
  D1060 が env_tag 等で採ったのと同じく **§5.1 へ解除条件を足すこと**である。
- 変異は DW-M07 に従い、全件 SURVIVED 期待の probe で観測 node を集めてから完全集合で本走した。
  baseline PASSED、8/8 KILLED、SURVIVED 0、MISMATCH 0、期待 node 完全一致。M3 は共有 helper への
  変異で 4 層を同時に倒すため、独立発火する M1 / M2 / M8 と分けて数える (D1275)。
- 計算ノードの queue 混雑で変異 harness が dispatch-runner-timeout の orphan-hold を 2 度出した。
  qstat で対象の終端を確認し、hold と orphan-stop sidecar と attempt-out を退避してから
  timeout を延ばして再投入した。手動 qdel はしていない。
- 待ち手を harness の背景 job として張ると、子の生存中に出力ゼロ・rc=0 で完了扱いされる事象が
  段 6 で 3 回続いた。前景で同じ引数を走らせると正しく `producer-timeout rc=70` を返した。
  `.done` 非空で判定していたので誤判定には至っていない。{{F:background-job-notification-is-not-a-waiter-verdict}}
- 正式 qsub、正式 B-4 実測、admission record の JSON 発行、push、次 wave 起動は行っていない。
- 一次資料は `output/insights/2026-08-29_t2005-b4-projection-registration/`。

## 次の一手差分

### 更新

- [T-2005] **P2・ユーザー裁定待ち**: B-4 の projection 登録は、機構 (3 driver 完全形を要求する
  行の文法、raw bytes への exact 一致、record と文書の driver 束縛、登録 3 値を bootstrap・
  pair 生成・invoke・最終 certification の 4 か所で live 照合) と §5.1 の解除条件を 2026-08-29 に
  閉じた。**値は未登録である。** 残るのは (i) §5.1 が要求する 4 点 — 結果に依存しない宣言源、
  承認する人間の識別子、宣言の時点、観測 slug が食い違ったときの扱い — を別 commit で固定すること、
  (ii) model・prompt・3 driver の projection を同じセルへ原子的に記入すること、(iii) その版を
  commit すること、(iv) その版へ束縛した record を driver ごとに発行すること。
  **(i) の 4 点は人間の指名を含むため AI が確定できない。** `expected_claude_model_snapshot` の
  exact slug をユーザーが指名すれば (ii) 以降は機械的に進む。
  base: be779d340eb0815bd1411641384afb77828ea983cd17d6cce1b583fb7906b86a
