---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1520-receipt-survives-main-merge
seq: 3
---

## 新規

### {{F:truncated-ruling-projection}}. 裁定本文を行範囲で切り出して子へ渡し、実装条件の後半が欠けたまま段 3 を走らせた [手順漏れ]

- 事象: 親が `docs/decisions.md` の裁定を `sed -n '<開始>,<終了>p'` で job dir へ切り出し、
  段 2・段 3 の子へ「必読事項の射影」として渡した。行範囲の終端を実際の次見出しで
  確かめていなかったため、**実装条件 4 項のうち後半 2 項が欠けた本文**が子へ渡り、
  段 3 の 2 レンズはその状態で攻撃を行った。
- 根本原因: 切り出しの終端を「だいたいこのくらい」で決め、切り出した後に
  末尾が節の終わりであることを確認しなかった。射影した資料の完全性を検査する経路が無い。
- 恒久対応: 節単位の切り出しは行範囲でなく次見出しまでを取る
  (`awk '/^## <見出し>/{f=1} f&&/^## /&&!/^## <見出し>/{exit} f'`)。
  切り出した直後に末尾を目視し、節の最後の項が含まれることを確かめる。
  memory `truncated-diagnostics-are-not-a-closure` の適用先を「診断出力」から
  「子へ射影する一次資料」へ広げる。
- 再発検知: 敵対レンズが「brief が裁定に帰属させた条件が射影本文に無い」と指摘したことで
  発覚した。射影資料の完全性は子のレビュー観点に含める。
- 実害: この回は brief 側に 4 条件とも書いてあったため裁定の実質は失われなかった。
  ただし brief が正しくなければ、欠けた条件を無視した設計が段 4 まで通っていた。

## 再発

### F24

- **再発: 2026-08-24** — 同一 wave 内で `tools/dev_wave_wait.py producer` の偽完了が **3 回**。
  段 6 の敵対レビュー A の待ち手、変異 probe の待ち手、変異本走の待ち手のいずれもが
  rc=0・出力ゼロ・`.done` 不在で戻り、実際には子が生存して走行を続けていた。
  恒久対応 (`.done` の実在と成果物の実在を併せて確認し、待ち手の rc を信じない) が
  3 回とも効き、実害はゼロ。追加事実は **偽完了が特定の段に偏らず、
  read-only の codex 子にも計算ノードへ dispatch する変異 harness にも等しく起きる**点である。

### F106

- **再発: 2026-08-24** — 変異 matrix の走行中に、親が段 7 の設計判断 fragment を worktree へ書き、
  `tools/mutation_harness.py` が runner 実行前の preflight で untracked file を検出して
  rc=2 で停止した。**親は同じ turn の中で「変異走行中は tree へ書かない」と自ら明示した直後に
  違反している。** 追加事実は、**規律を言語化することは順序の設計の代わりにならない**点である。
  恒久対応の向きは「走行中に書かない」ではなく「走行前に、変異結果を待たない記録
  (設計判断 fragment) を書き終えて commit しておく」という順序の固定にある。
  実害は 1 往復ぶんの再走。

### F57

- **再発: 2026-08-24** — 変異 harness の baseline が、親の焦点走では緑だった node で赤になった。
  焦点走は 10 file (1676 item)、変異 baseline は 2 file (327 item) で、どちらも同じ
  計算ノードへ dispatch している。落ちたのは
  `test_exploration_external_root_keeps_wave_clean` で、赤の本文は
  `orchestrator/campaign/execution_guard.py` の
  `CertifiedWriterAuthorizationError`「Pegasus compute では receipt state 内で一意な
  required authorization_contract だけを受理する」。当 wave の差分は campaign 層にも
  当該テストにも触れていない。`REAL_REPO_SERIAL_NODES` 未登録。
  追加事実は、**フレークの引き金が worker 数ではなく file 集合 (xdist の同居関係) でも成立する**
  点である。D690 に従い `--deselect` で外して先へ進めた。
  **申し送り**: この node の file 集合依存を根治する作業は別 wave が要る。

### F225

- **再発: 2026-08-24** — 親が `docs/dev-wave/operations.md` を編集した未 commit 状態で
  段 6 の fix 子を投げ、`NG: docs/dev-wave/operations.md: working tree が authority commit と異なる`
  で rc=2 拒否された。追加事実は、**merge 由来だけでなく親自身の docs 編集でも同じ拒否が起きる**
  点である。段 6 は「親が docs を直す」と「子に実装を直させる」が同じ段に同居するため、
  この順序衝突は構造的に起きる。回避は docs 編集を統合 commit にしてから子を投げること。
