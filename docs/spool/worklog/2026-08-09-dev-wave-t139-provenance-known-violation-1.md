---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t139-provenance-known-violation
seq: 1
title: F37 を機械強制へ移した — land の ff-only だけに全史 provenance 監査を課す (コード + docs、敵対検証 4 本が全部 NO-GO で設計を 2 度組み直した、変異 12 件 SURVIVED 0、branch worktree-dev-wave-t139-provenance-known-violation)
---

## 本文

- **ユーザー裁定 2 件を実装した。**逐語は
  `dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md` (項目 2、
  発話「推奨通りで」) と `2026-08-09-t139-r4-probe-provenance-format-violation.md`。
  設計判断は {{D:land-ff-only-provenance-gate}}、事故側は F37 の再発記録へ書いた。
- **scope が段 1 の途中で変わった。**当初は「22 件の known-violation 登録 + F37 機械強制化」
  だったが、(i) inbox 確認 (08:32) の 6 分後 (08:38) に新しい裁定が着信し、
  (ii) ユーザーが 08:43 に並行 wave (`worktree-dev-wave-t682-provenance-known-violations`) を
  起動した。`DW-STOP` の「承認済み裁定の前提を覆す未見の新事実」に該当したため brief を
  invalidate して段 1 を再実行した。**発見の契機は並行 session からの通知**で、
  親は独立に裁定ファイルを読んで確認した。
- **並行 wave と file 所有を素集合に割った。** `tools/check_ai_provenance.py` への
  23 件登録は t682 が、`tools/dev_wave_land.py` の関門は本 wave が持つ。相互に SendMessage で
  確認済み。**land の順序は「t682 の登録 → 本 wave の関門」**で合意した — 現状 23 件の赤が
  あるため、順序を守らないと関門が自分自身の land を fail-closed で拒否する。
- **敵対検証 4 本 (段 3 の 2 レンズ、段 6 の 2 レビュー) がすべて NO-GO / blocker を返し、
  親案を 2 度組み直した。**親の当初案は 3 点で誤っていた。
  (i) 監査を lock 内に置き `lock-busy` の即時性と D102 の順序を壊す。
  (ii) 38.3 秒という単発観測を lock 予算の根拠にした (実際は dispatch 経路で
  queue 900s + walltime 2400s + grace 300s を含みうる)。
  (iii) **「active fold recovery は新規 commit を 1 つも admit しない」という偽の署名**を書いた
  — `_fold_main_locked()` は実際に commit する。線引きを「新規 commit を作るか」から
  「wave の commit を main へ新たに入れるか (ff-only を行うか)」へ引き直して解いた。
- **段 3 の両レンズが推した「B: 止めて immutable trust root を別 scope で設計」は採らなかった。**
  両者は「関門が tip 側コード実行という新しい信頼面を作る」を前提にしていたが、
  runbook の land 手順は worktree の cwd から相対 path で helper を起動するので
  **親は既に tip 側 helper を実行している**。関門は信頼面を増やさない。
  ただし残余課題としては real なので裁定パッケージへ回した。
- **親自身の実測の誤り 2 件を撤回した** (段 3 の両レンズが独立に指摘)。
  「`pipefail` の hit ゼロ」は `tools/**/*.sh` を検索から落としていた誤り。
  「既存 2 本の子検査と同型」は構文が同じだけで、latency・例外・transaction 境界が別物だった。
- **変異は 12 件で SURVIVED 0** (`mutation-ledger.json` 11 件 + `mutation-ledger-m10b.json` 1 件)。
  期待 node がちょうど発火したのは 7 件、期待 node は発火したが他 node も落ちた過剰決定が 4 件
  (M3 は 56 node)。**M10 だけは期待 node が発火せず erratum とした** — fingerprint 照合が
  2 箇所あり片方の変異はもう一方に mask される。`DW-M02` に従い両層同時変異 M10b を追加登録して
  本走し、collision テストの発火を確認した。初回結果は消していない。
- **変異走行では対象から 1 テストを除外した (silent cap にしない)。**
  `-k "not test_exploration_external_root_keeps_wave_clean"`。harness は緑の baseline を要求するが、
  同テストは本 wave の差分と無関係の環境要因で赤になる。除外対象は変異対象 file から到達不能で、
  どの変異の期待 node にも含まれない。
- **本 wave の差分と無関係な赤 1 件を実測した。** 同テストはログインノードでは `/tmp/.git`
  (空ディレクトリ、2026-07-28 作成) により、計算ノードでは
  `CertifiedWriterAuthorizationError` により、**別々の理由で**落ちる。帰属の根拠は
  (i) 差分が当該テスト本体に触れていない、(ii) `dev_wave_land.py` は campaign を import しない、
  (iii) 同テストは base に存在し直近の受入全走 (7570 passed) で緑だった、の 3 点。
  `/tmp/.git` は並行 8 wave の最中に共有状態を変えないため削除していない。
  計算ノード側は [T-657]/[T-660] の領域なので調査も手当もしていない。
- **docs 予算が満杯で reference を更新できなかった。**
  `DEV_WAVE_AGGREGATE_BYTES = 25_200` に対し現在 25,199 bytes = 余白 1 byte。
  `DW-O23` / `DW-O17` / `DW-S09` への関門契約の追記も、裁定項目 4 の `DW-S01` 追記
  (「書く前に既存被覆を検索する」) も入らない。既存本文の削除はユーザー裁定に限ると
  `docs/skill-self-improvement.md` が定めており、予算のために安全義務を削るのは禁じられている。
  **予算値は上げず、変更を止めて裁定へ返した** ({{T:dev-wave-docs-budget-blocks-gate-sync}})。
- **provenance trailer の綴りをピア調整で決めた。** `/model` 切替時の規則
  (切替を見たら `model=unknown`) はユーザー裁定済みだが、本セッションは切替しておらず射程外。
  モデル ID `claude-opus-5[1m]` は角括弧が `[a-z0-9][a-z0-9._-]*` に反しそのままでは書けない。
  main に land 済みの前例 `claude-opus-5-1m` が 4 commit あり checker を通るため、
  **既存慣行に揃えた**。`unknown` も `not-exposed` も厳密には該当しないという並行 session の
  精読と整合する。規約の穴自体は同 session が起票済み。
- **受入全走は tip `05f99b6f` で 1 走した** (request 896778.nqsv、1330.92 秒、
  **7582 passed / 1 failed / 20 skipped、rc=1**)。lease は 30 秒間隔の待ち手が約 5 分で取得し、
  受入の終端で解放した。取得時に main が `bcda1c02` → `c9d14c23` へ進んでいたため、
  投入前に取り込んで merge commit を作った。
  **赤 1 件はフレークである。** `test_s8c_preregistration_invariant.py::`
  `test_candidate_freeze_matches_contract_and_generation_chain` が
  `git cat-file --batch-check` の 15 秒 timeout で SIGKILL (`returncode: -9`) された。
  論理的な失敗ではなく xdist 並列下の負荷由来である。**単独再走で 8 passed / rc=0** を実測し、
  再現しないことを確認した (`DW-O18`)。本 wave の差分は `s8c_preregistration` 経路に到達しない。
  なお心配していた `test_exploration_external_root_keeps_wave_clean` は**この走行では通った** —
  同テストの赤はノードと大域状態に依存する。
- 段 5 と段 6 の実装子・fix 子はいずれも **pytest を実走できなかった**
  (`qstat -Q preflight rc=1`、runner rc=16)。テスト実測はすべて親が行った。
  ログインノードでは bounded scope の attest が 4 回連続 rc=16 (並行 8 wave でメモリ逼迫、
  実効天井 15GB に対し 10.7GB 使用) だったため `--force-dispatch` で計算ノードへ回した。

## 次の一手差分

### 新規

- {{T:dev-wave-docs-budget-blocks-gate-sync}} **P1・ユーザー裁定待ち**:
  `docs/dev-wave/**` の合計予算が満杯 (25,199 / 25,200 bytes) で、本 wave が land へ入れた
  関門の契約を `DW-O23` / `DW-O17` / `DW-S09` へ書けない。ユーザー裁定の項目 4
  (「書く前に既存被覆を検索する」を `DW-S01` へ) も同じ理由で入らない。
  必要量は `DW-O23` への最小追記だけで約 110 bytes、`DW-S01` 追記が約 150 bytes。
  **段 8 の自己改善候補も同じ壁で入らない** — 「段 4 の裁定確定の直前にも rulings-inbox を
  読み直す」という 1 文。本 wave は段 1 の inbox 確認の 6 分後に着信した裁定を取りこぼしかけ、
  並行 session の通知で救われた。`DW-S01` は「brief 前に承認済み裁定の前提を実測する」とは
  言うが inbox の再走査は求めていない。行き先は `DW-S01` か `DW-S04`。
  選択肢は (a) 既存 reference から陳腐化した節・冗長な説明を削って空ける (削除の実施は
  ユーザー裁定に限る)、(b) 予算値を上げる (通常の自己改善に含めず独立審査が要る)、
  (c) 外出し先を新設する (dev-wave 系は leaf 節単位の読み込みで削減 0 という既測があり不適)、
  (d) reference への記載を諦めコードとテストだけを正本とする。**推奨は (a)。**
  実装と台帳の記録は済んでおり、欠けているのは reference の同期だけである。
- {{T:land-gate-immutable-trust-root}} **P2・新規**:
  land 対象の wave が、自分を裁く checker と land helper 自身を変更できる。
  段 3・段 6 の敵対検証 4 本すべてが最優先課題として挙げた。本 wave の関門はこの境界を
  悪化させないが解消もしない (親は既に tip 側 helper を実行しているため信頼面は増えていない)。
  選択肢は immutable trust root からの実行体固定と宣言的 registry の分離、または
  「協調境界として受容する」の明文化。checker を更新する wave のための bootstrap 手順も要る。
- {{T:exploration-external-root-test-red-both-nodes}} **P2・新規**:
  `test_exploration_external_root_keeps_wave_clean` が両ノードで別々の理由により赤。
  ログインノードは `/tmp/.git` (空ディレクトリ、2026-07-28 作成) が
  `_has_git_ancestor` に拾われるため。計算ノードは
  `CertifiedWriterAuthorizationError` (「receipt state 内で一意な required
  authorization_contract だけを受理する」) のため。直近の受入全走では緑だったので、
  いずれも本 wave 期間より後に生じた大域状態の変化である。受入全走を赤にしうる。
  計算ノード側は [T-657]/[T-660] の活性化と未実行のユーザー手番に関係する可能性がある。
