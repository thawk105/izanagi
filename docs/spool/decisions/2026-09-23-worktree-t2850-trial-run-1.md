---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: worktree-t2850-trial-run
seq: 1
---

## {{D:t2850-trial-effect}}. 探索の独立反復の試走を write-heavy だけで発効させる — 実装は T-2849 の着地 commit に固定し、seed preimage を実装どおりに追補で登録し、LLM 親は機会ごとに同じ session を再開する

**決定:** 事前登録 v1 (`docs/search-repetition-trial-preregistration.md`、raw SHA-256 `7501bd1f7f893801010dba2f93ceb45966badd11ed3e9e4a0aafa39f99d88206`、D2231) の測定を、
追補 1 (`docs/search-repetition-trial-preregistration-addendum-1.md`) と発効束 (`output/insights/2026-09-23/t2850-trial-effect-bundle/bundle/t2850-trial-effect-bundle.json`) のとおり発効させる。

1. **計算確認 (D2212 項 4):** 2026-09-23 にユーザーが「write-heavy だけで試走」を選んだ。試走は S1-wh × 5 手法 × 3 系列 + block job 3 の 18 job、
   見積りは実測単価で 42.4〜60.6 node 時間 (中心 47.6)、LLM の直列時間 1.9〜19.5 時間。費用上限は事前登録 §9.2 の 200 node 時間のまま、job Elapse の総和が見積りの上側を超えそうなら新しい投入を止めて再確認する。
   先立つ smoke 3 回と glue の自走テストで約 2.44 node 時間を使った (試走の標本に数えない)。
2. **実装の commit:** `7ea9aa09dad0012aebd5464c70a9e468c409dd92` (比較基盤の着地、D2233)。repo 外の固定 checkout で走らせ、以後の main の変更で動かさない。CCBench は campaign の pin `511c9538…` を使う。
3. **seed preimage:** 実装は系列 id を整数 R として preimage に入れ、事前登録 §4 の文字列 `t2850-trial-s<b>` を受ける口を持たない。固定 commit を守るため実装は変えず、生成の前に追補 1 で preimage を実装どおりに登録した。
   試走は R = b、smoke は R = 9、本比較は重ならない整数を本比較の生成前の追補で決める。
4. **未指定の定数:** BO の失敗集合は {rejected-tier0, build-failed, anomaly} と anomalies を持つ結果で、rejected-preprocess・bench-aborted・aborted は含めない。BO の格子・雑音・jitter・進化の丸めなどは発効束に列挙した実装の値のまま。
5. **LLM:** exact ID `claude-opus-5`、D2222 の起動契約 (起動構成で alias を固定、role に model 引数を渡さない、巡ごとに記録、不一致なら何も公開しない)。親は repo 外の起動器が request の公開ごとに同じ session を起こし
   (最初は `--session-id`、以後は `--resume`)、1 機会分だけ処理して応答を終える。期限を過ぎた request では起こさない。
6. **課題の縮小:** 試走の課題は S1-wh だけ (追補 1 §4)。本比較に read-heavy・balanced を入れるときの分散は S1-wh からの未検証の外挿で、read-heavy の費用は本比較の計算確認の前の追補で別に示す。

**理由:**
- smoke の実測で、評価 1 回の所要の大半が正しさの検証 (legacy 1 回と 3 秒の trace 5 本の直列性検査) で、bench は 16〜17 s だった。read-heavy の候補は 1 評価 741〜約 2,210 s で、2 課題の試走は
  110.9〜252.2 node 時間 (上側は上限 200 を超える) になった。ユーザーはこの見積りを「絶対におかしい」と問い、内訳を見て write-heavy だけを選んだ。検証の回数と規模は正しさゲート (規律 2) と
  評価の定義なので、AI の判断では減らさない。
- 依頼は束を T-2849 の着地 commit に固定することを求めた。preimage をコードで直すと commit が変わる。まだ 1 系列も生成していないので、追補での登録は事前登録 §0 の手続きの内にある。
- 背景の待ち手を使った親は `claude -p` の応答の終わりで session が終了し、前景の `sleep` は Bash の防壁が拒否した (並走の B-5 本走 wave の実測)。A = 30 の系列で次の request に親がいないと期限切れで score が欠測になる。
  再開型の起動器で LLM 経路の再 smoke (t2850-smoke-v2) が 2 機会・critic 1 回を通して完走した。
- BO の失敗集合は基盤設計 §3.2 の列挙と「品質欠測は外さない」に一致する。bench-aborted の一部は品質欠測に当たるので、候補起因の失敗を一括で足すとこれに反する。

**却下した選択肢:**
- 2 課題の試走を登録どおり走らせる — ユーザーが費用を見て選ばなかった。
- 検証の回数を減らす・測り直しの検証を省く — 正しさゲートに触れるので AI は決めない (ユーザーは選ばなかった)。
- preimage を事前登録どおりにするコード変更 — 束の commit が T-2849 の着地物から動く。
- 親に request を待たせる — 背景の待ち手では session が終わり、前景の sleep は防壁が拒否する。
- 投入 script を repo の `tools/pegasus/` に置き admission registry へ登録する — 本題に要らない登録簿の追加になる。repo 外の glue (Codex author) で足りた。
