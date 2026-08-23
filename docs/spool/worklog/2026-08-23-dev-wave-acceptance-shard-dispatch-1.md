---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-shard-dispatch
seq: 1
title: 受入全走を K shard へ分けて計算ノードへ同時投入する経路を入れた。テスト実行は縮むが総所要は queue 次第で、混雑時は分割が不利だと実測した (コード+テスト、branch worktree-dev-wave-acceptance-shard-dispatch、変異 matrix = 8/8 KILLED)
---

## 本文

- 依頼は「受入全走の高速化。Pegasus で開発中、テストを計算ノードに投げることがある。
  それをいい感じに分割して計算ノードに投げることで受入全走の高速化を試みる」。
  設計判断は {{D:acceptance-shard-dispatch-optin}}、{{D:acceptance-shard-exact-preservation}}、
  {{D:artifact-root-outside-control-container}}、{{D:acceptance-cost-four-layers}}。
  cost 構造の一次資料は `output/insights/2026-08-23_acceptance-shard-cost-structure/`。

- **結論から言うと「機構は正しく、テスト実行は縮むが、総所要は queue の空き次第」である。**
  既定 K=1 (opt-in) のまま着地させ、有効化の推奨は運用者の判断に委ねる。
  D312 に従い、5 分に届くかどうかを合否にしていない。

- **親は着手前に cost 構造を 1 走で実測した。** 14467 件 / 直列総和 5364.9 s /
  排他鎖 `s8c-preregistration-candidate` 103.0 s と `real-repo` 103.0 s と
  `dev-waves-runtime` 14.9 s / 最長単体 85.46 s / 実効並列度 48.7%。
  固定費は差分推定でなく「48 worker を起動し全 collection を行いテストを 1 件も走らせない走行」で
  直接測り 12.86 s を得た (D531 の 26 s は wall と鎖長の差分からの推定値)。

- **親の一般化を段 3 の敵対相談が 3 つ崩した。** (1)「律速が排他鎖から総 work へ移った」は
  1 走からは言えないので撤回。(2) `直列総和 / (48K)` は下界でなく仮想 capacity 指標。
  (3) 生死実験の「1.87 倍」は完全集合の走行でないので暫定値。いずれも親が受け入れて格下げした。
  親の当初仮説「file 単位に割れば collection も K 分の 1」も親自身の実測で反証した
  (全 238 file 8.15 s に対し半分ずつが 4.48 s と 5.93 s、合計 10.41 s > 8.15 s)。

- **生死実験で本物の設計欠陥を 2 件見つけた。** 使い捨て driver で実物の 2 分割を同時投入したところ、
  (a) file を positional target へ渡すと `sys.path` の確立が変わり
  `test_s8b_approved.py` と `test_profiler_directive.py` が `ModuleNotFoundError` になる、
  (b) もう一方の shard の dispatch が repo の `output/pegasus-dispatch/` を書き、
  実 output tree を snapshot するテストが落ちる。
  (b) は段 3 レンズ A が同型を全数列挙し **9 関数 / parametrize 込み 11 node** と確定した。
  いずれも実装前に設計へ反映した。

- **段 3 レンズ B が「速くならない条件」を先に立証していた。** 空き時の利得は 117 s なので
  最遅 shard の queue skew が 117 s を超えれば負ける、という指摘である。
  **これが実地で成立した** — 外側 wall は K=1 が 218 / 326 / 391 s、K=2 が 476 / 495 s、
  K=3 が 291 s である。
  一方 pytest wall は K=1 が 157.43 / 187.35 / 347.45 s、K=2 の最遅 shard が
  127.40 / 138.57 / 144.99 s で、**テスト実行そのものは縮み、しかもばらつきが小さくなる。**
  **K=2 の一方の shard は 3 session とも 324 / 330 / 324 s の queue 待ちを引いた。**
  幅が 6 s しかなく、混雑の揺らぎというよりスケジューラの周期に近い。3 標本なので断定しないが、
  もしそうなら K>=2 は約 325 s の準決定的な追加費用を払い、現在の queue 設定で総所要が勝つことはない。
  なお同一集合でも pytest wall が 157.43〜347.45 s とばらつき、
  **この noise floor が分割で得られる差 (最遅 shard で 20〜40 s) より大きい。**

- **K=3 は K=2 より速くならない。** K=3 の最遅 shard は 143.92 s で K=2 の 138.57 s を下回らない。
  排他鎖 103.0 s + 固定費 12.86 s の床に当たっている。K の閉集合は `{2,3}` のままとしたが、
  これは「K が排他 group 数以上なら各 group を別 shard へ置ける」ことを担保するためであり、
  速度のためではない。件数 LPT は所要を代表しない
  (`s8c` は 5 件で 103 s、`dev-waves-runtime` は 22 件で 14.9 s)。

- **自分の実装が他 wave の land を止めた。** shard の artifact 置き場を `repo.parent` にしたところ、
  repo が worktree のとき `.claude/worktrees/` になり、
  land がそこの子を全部 git worktree と見なして `.git` を要求するため
  **同じ checkout の全 wave が rc=21 で着地不能**になった。並行 wave からの報告で判明。
  進行中の 1 本だけ自然終了させ (途中で殺すと PBS job を孤児化させるため)、
  104 file / 48,734,025 bytes を byte 一致で退避してから削除し、相手へ解消を連絡した。
  恒久対処は {{D:artifact-root-outside-control-container}}。
  **「repo の外」という条件は満たしていたのに、別機構の縄張りを見ていなかった。**

- **実装子が pytest を実走できないことに起因する赤が 2 巡出た。** 1 巡目は
  `TypeError: _call_with_runner_exclusions() got multiple values for argument 'exclusions'` で
  **あらゆる走行が即死**する状態だった (K=1 の既定経路を含む)。静的には正しく見える呼び出し不整合である。
  親が原因を 1 行レベルまで特定してから投げた fix が 2 巡あり、fix は通算 5 巡になった。

- **段 6 レビューが恒真な保証を 1 件見つけた。** shard report の診断 payload を空
  (`{}` / `[]`) にしても 6 gate を通り rc=0 になった。空集合に対する `all(...)` が恒真だったためで、
  gate の前に実データから再計算して照合する検査を足した。

- **変異 matrix: 8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0** (repo_head `d78977ff`、baseline rc=0)。
  各 gate の恒真化 6 件、両層同時 1 件、過剰拒否の正例 1 件。
  **M1 単独 1 node / M5 単独 1 node / M1+M5 同時 3 node** と分離しており、
  combined killer が片方だけでは落ちない。段 6 レビューが指摘した過剰決定を修正した結果である。
  probe 走 (全件 SURVIVED 期待で観測 node を集める) を先に回し、観測 node を expected へ焼いてから本走した。

- **変異 spec の落とし穴を 3 つ実測した。** runner argv に `-rf` が必須 (DW-M08)。
  `category` の閉集合は `{negative, positive, both-layers}` で `positive-control` は未知。
  untracked file があると preflight で止まる。

- **計算ノードの混雑を実地で踏んだ。** 焦点走が一度 `queue-wait-timeout` (900 s) で rc=16 になった。
  テスト失敗ではない。`--force-dispatch` を外して §7.0.0 の自動判定へ戻すと
  ローカル実行 -> cap OOM -> dispatch と設計どおり fallback して完走した。

- **並行セッションとの分担を 3 件確認した。** launcher 系の負荷依存フレークは
  「1 ノードあたり 48 worker のままで同時実行密度が下がらない」ため本 wave の分割では解けない、
  と伝えて別 session が引き取った。`tools/run_tests.py` の所有も相互に確認した。
  `conftest.py` を +254 行変更する別 wave があるので、着地後に collection hook が増えうる。

- **scope 外と裁定した所見が 2 件ある。** (1) `pytest.ini` に `addopts = -k ...` を置くと
  login と全 shard が同じ縮小集合を観測して 6 gate が全部通る。
  **既存の既知穴で本 wave の新規ではない** — `pytest.ini` 自身のコメントが
  「4 ゲートは ini の addopts を構造的に見ない」と明記し、専用テスト 2 件がその盲目性を pin している。
  同じ攻撃は K=1 でも成立する。(2) RUN 状態の job を qdel できるようにする方針変更。
  既存 gate が RUN を拒むのは意図的で、別の裁定が要る。記録漏れ (orphan-hold が単一 create-only path で
  2 本目の ID を落とす) だけ本 wave で直した。

- **段 8 の自己改善は 1 件も入れられなかった。** 候補は 5 件あった。
  (a) 「`hooks/guard_bash.py` の interpreter 検出に前置 command の穴がある」は
  **親が再検査して反証した** — 素の `python3 -m pytest ... --collect-only` も許可されており、
  `/usr/bin/time` 形の拒否は解析不能な形に対する正しい fail-closed だった。防壁の穴ではない。
  (b) 残る 4 件 (変異 spec の `category` 閉集合、untracked で preflight 停止、
  `dev_wave_wait.py producer` の `--artifact-file` 必須、隔離 worktree の detach は `.sh` 2 段) は
  **`docs/dev-wave/` の L1.5 byte 予算が満杯**で入らなかった
  (上限 9566 bytes に対し、約 184 bytes の追記で 9750 bytes へ超過)。
  自己改善契約の「予算に収まらなければ止めてユーザー裁定へ返す」に従い、
  reference は変更せず本 entry に残す。**予算値を上げる変更は独立審査対象**なので本 wave では触れない。

- **子の工数 (receipt 実測):** codex 子 10 本。内訳は plan 1 / consult 2 / author 1 / review 2 / fix 4。
  全て `gpt-5.6-sol`、`reasoning=xhigh`、`outcome=accepted`。

## 次の一手差分

### 新規

- {{T:acceptance-shard-receipt-binding}} **P2・新規**: 受入 receipt へ `shard_count` /
  `report_indexes` / `executed_nodeids_sha256` を足し、waiter・launcher・land で exact 検査する。
  現状 gate は runner の内側にあり、**receipt は shard の完全性を証明しない**。
  3 tool の受理条件を変える変更なので独立の裁定が要る。

- {{T:acceptance-exclusive-chain-shortening}} **P2・新規**: 排他鎖 103.0 s x 2 を短縮する。
  **両方を同時に短縮しないと床は下がらない** (片方だけでは他方が 103.0 s で残る)。
  第一候補は `s8c-preregistration-candidate` の
  `test_candidate_freeze_matches_contract_and_generation_chain` (30.2 s) と
  `real-repo` の `test_real_seal_protocol_to_floor_official_core_e2e` (28.2 s)。
  分割では消せない床なので、ここが最終的な下限を決める。

- {{T:real-output-snapshot-family}} **P2・新規**: 実 tree を snapshot して不変を要求するテスト
  9 関数 / 11 node と、基盤が repo 内へ書く path を突き合わせ、族として閉じる。
  「テストが観測対象にしている実 tree へ、テスト基盤自身が書き込む」型で、
  並行度が上がって初めて発火する。静的に列挙できる。

- {{T:shard-session-cleanup}} **P3・新規**: shard session directory が走行後に残る。
  1 走あたり約 15 MB。land への影響は無くなったが、共有 filesystem に溜まり続ける。
