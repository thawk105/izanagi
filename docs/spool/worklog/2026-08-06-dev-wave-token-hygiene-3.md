---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-token-hygiene
seq: 3
title: 開発ループの消費は claude 側が未計装だったので台帳を新設した — 削減施策は 1 つも land せず、自分の計測の誤りを台帳ごと残した (コード + docs、受入 6837 passed / 20 skipped、変異 12/12 KILLED、branch worktree-dev-wave-token-hygiene)
---

## 本文

- **依頼は「品質を落とさずトークンを減らす施策があればやる」だったが、削減施策は 1 つも
  land しなかった。** 親の観察値では削減判断を支えられないと段 3・段 6 が独立に判定し、
  親も real と裁定したためである。land したのは計測の空白を埋める台帳 1 本だけである。
- **親が段 0 で測った値のうち複数が誤っており、訂正前にユーザーへ報告してしまった。**
  文脈の内訳 (33.5/26.8/17.9/2.0%) は同一 block の二重計上、
  「子 1 tool あたり 105,774 tok」は観測 model call を tool 呼び出しと取り違えた比、
  「6 日で 11,860 M」は単一 encoded cwd の subtotal で sidechain と旧 checkout が欠落していた。
  段 3 の敵対レンズが実データで否定した。詳細と訂正表は
  `output/insights/2026-08-06_token-hygiene/README.md`。誤りを含む段 0 スクリプトも
  訂正の証拠として同 dir へ凍結した ({{F:measurement-double-count-reported-to-user}})。
- **親は着手前の既存被覆検索 (DW-S01) を怠り、codex 側の二重実装を brief に書いていた。**
  `tools/codex_worker_ledger.py` と `tools/codex_reasoning_ab.py` が既に存在し、D100 が
  「token は observable proxy」と裁定済みだった。段 3 が指摘し、親も独立に確認して scope から外した。
  一方 **claude 側は完全に未計装**で (`grep -rln "claude/projects"` の hit は archive 1 件のみ)、
  消費の大きい方が見えていなかった。ここだけを埋めた ({{D:claude-session-ledger}})。
- **effort 引き下げは実装せず、既存の A/B 装置へ送った。** 観察では `reasoning=max` の子が
  入力の 63% を占め、中央値で high の 2.02 倍だったが、現契約が段 2・段 3 を max、
  段 5 を high と固定しているため stage・難易度・turn 数と交絡している。max 群は
  model call 数自体が 1.44 倍あった。検出力を下げる変更を交絡した観察値で入れるのは
  規律 2 の対象だと裁定した ({{D:effort-downshift-needs-controlled-experiment}})。
- **入口文書へ換算率を書く案も却下した。** stale 化するうえ、依存のある呼び出しまで
  無理に束ねさせる。しかも「独立 tool は 1 応答に束ねられる」「ファイル読取に汎用シェルを
  使わない」は既に実行面の system prompt にあり、書き足しても無効である
  ({{D:no-fixed-token-rates-in-entry-docs}})。
- **`docs/dev-wave/workers.md` には 1 行も足せなかった。** 4 文書の aggregate 予算は
  25,200 bytes に対し現状 25,187 bytes で**余地 13 bytes**。削除先を特定しないまま
  追記しない方針を守った。予算引き上げは提案していない。
- **段 3 と段 6 の 3 レンズはすべて独立に NO-GO を返した。** 段 3 が must-fix 6 件、
  段 6 の 2 本が計 8 件。親は全 14 件を real と裁定した。両レンズ間の衝突はなく、
  いずれも「値が間違っていても緑になる経路」を指していた。
- **段 6 レビュー B は変異の生存を事前に予告し、実測がそのとおりになった。**
  M8 / M10 / M12 が「JSON は検査されるが利用者が読む既定テキストは無検査」という理由で
  生存すると指摘し、1 走目で実際に生存した。fix 後は 3 件とも KILLED。
- **1 走目の M7 SURVIVED が最も重い所見だった。** sidechain の取得枠を 0 にする変異が
  検出されなかった。親は等価変異か否かを実測で判定し、root 0..7 × sidechain 0..7 ×
  max_files 1..8 の**全 512 通り中 185 通りで配分が食い違う**ことを確認した
  (最悪例は root 2 / sidechain 1 / 予算 2 で、正 1/1 に対し変異後 2/0 = sidechain 枯渇)。
  等価ではないと裁定してテストを 1 本新設した。**実装は変更していない** —
  配分ロジックは元から正しく、欠けていたのは検査だけだった。
- **変異は 3 走した。** 1 走目 KILLED 5 / MISMATCH 6 / SURVIVED 1、2 走目 KILLED 11 /
  MISMATCH 1 / SURVIVED 0、3 走目 **12/12 KILLED・MISMATCH 0・SURVIVED 0・baseline PASSED・rc=0**。
  MISMATCH はすべて親の登録ミスで変異自体は初回から検出されていた (F87 再発)。
  今回の新しさは、**SURVIVED を閉じるためにテストを 1 本足したことが、
  既存の期待 node 登録を陳腐化させて 2 走目に新たな MISMATCH を生んだ**点である。
  v1 / v2 の spec と台帳は消さず erratum として残した。
- **背景 job が子の完了待ちを張らずに 6 時間 24 分停止した。** fix 子は 14:19 に rc=0 で
  終わっていたが、親が投入と報告だけで turn を終えたため通知が発火せず、ユーザーの
  「動いていますか？」まで進まなかった。恒久対応は memory
  `never-end-turn-with-unawaited-child`、およびユーザー指示による
  「5 時間無変化なら止めて状態と再開コマンドを報告する」運用 ({{F:bg-job-idled-without-a-wait}})。
- **`tools/check_ai_provenance.py` は local main の時点で既に赤である。** 他 session
  `worktree-rulings-20260806-a` の merge commit 5 本に `AI-Agent` trailer がなく、
  それが local main の祖先に入っている (`git merge-base --is-ancestor` で確認)。
  本 wave の 3 commit はいずれも clean。他 session 所有物なので触らず裁定へ返す。
- 受入全走は Pegasus 計算ノードで tip `b14e37ee` に対し 1 回、
  **6837 passed / 20 skipped** (request 893648.nqsv、933.91s、rc=0)。
  焦点走行は段 5 直後 13 passed → 段 6 fix 後 33 passed → fix 2 巡目後 34 passed。
- **名乗りの上限。** 名乗ってよいのは claude セッション側の消費が read-only 台帳で
  観測可能になったことまで。**トークン消費が減ったこと・effort の最適値・往復削減の効果・
  codex 側の計測改善・成果物 (certified 選択、材料レポート、試行台帳、proof chain) への
  影響は一切名乗らない** — 成果物の値と参照は不変である。
- 逐語と変異台帳は `output/insights/2026-08-06_token-hygiene/`。

## 次の一手差分

### 新規

- {{T:codex-effort-ab-evaluation}} **P2・新規**: dev-wave の段 2 / 段 3 の `reasoning=max` を
  `high` へ落としてよいかを `tools/codex_reasoning_ab.py` の paired・blind・非劣性で評価する。
  観察では max が codex 入力の 63% を占め中央値で 2.02 倍だが、stage と交絡しており
  観察値では決められない ({{D:effort-downshift-needs-controlled-experiment}})。
  評価では消費だけでなく**後段の must-fix 件数と fix 巡回数**を endpoint に含める —
  弱い起草が巡回を増やして総消費が上がる経路を排除するため。
- {{T:main-provenance-trailer-red}} **P1・新規**: local main の `check_ai_provenance.py` が
  他 session `worktree-rulings-20260806-a` の merge commit 5 本
  (`88f0f9f0` `85dacc27` `6e69ca5c` `16affe16` `905c867a`) の trailer 欠落で赤である。
  **所有 session が不明なまま history を書き換えられないため、ユーザー裁定が要る。**
  merge commit へ trailer を要求する運用そのものの是非を含めて決める。
- {{T:dev-wave-reference-budget-exhausted}} **P2・新規**: dev-wave 4 文書の aggregate 予算は
  余地 13 bytes で、本 wave は `workers.md` に 1 行も足せなかった。**予算引き上げは提案しない**
  方針 (T-127 裁定) のもとで、陳腐化した記述の特定とテスト化による捻出先を決める。
- {{T:claude-session-ledger-consumers}} **P3・新規**: `tools/claude_session_ledger.py` に
  production consumer が無い。台帳を実際に読む経路 (定期観測・wave 記録への添付・
  A/B の endpoint) のどれを結線するかを決める。**結線先が決まるまで削減施策は起票しない** —
  before/after を測れない施策は評価できないため。
