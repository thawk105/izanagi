---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2637-offrepo-parallel-scan
seq: 1
title: [T-2637][T-2660] 到達不能監査の repo 外走査を directory 単位の work queue で並列化した — 実根 warm の列挙 936〜1298 → 110〜336 秒 (同時刻対照で 3.2〜9.4 倍)、走査強制 fixture の D958 判定は 6 走 max 335.8 秒で不合格、実 repo は上限内、本 wave 限定の追補 D で受理 (コード + テスト + docs、branch worktree-dev-wave-t2637-offrepo-parallel-scan、変異 matrix = baseline PASSED・負例 9/9 KILLED 期待 node 完全一致・等価 2 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「到達不能監査 `tools/audit_dangling_commits.py` の repo 外走査を並列化する第 1 段 (D2104 項 20)。
  範囲・規則・出力は変えない (findings の同一性を正例で固定)。並列禁止 test は削除でなく『並列化しても範囲・規則・
  出力が不変』を検査する形へ置換。第 2 段 (用途分離) は第 1 段の実測で 300 秒に入らないことを示してから (D2034)。
  Codex author (D95) + 変異事前登録。本題の並列化だけ」。
- **閉じた (受理は事後変更を明記した追補による)。** 一次資料は `output/insights/2026-09-17/t2637-offrepo-parallel-scan/README.md`。
  設計判断は {{D:offrepo-scan-directory-queue}}、{{D:audit-d958-fixture-forced-scan}}、{{D:d958-improving-wave-acceptance-t2637}}。
  実装 commit `78f8af060` (Codex author)。
- **D958 項 1 の判定と受理の決定。** 走査強制 fixture × 実根 (login、warm) の new16 有効 6 走 = 240.2 / 118.9 / 110.4 / 164.2 /
  194.9 / 335.8 秒 (max/min 3.0 > 1.5 で 3 走追加済み) → **max 335.8 秒 > 300 秒で D958 の文言どおりの判定は不合格**。
  同時刻対照の old は 936.2 / 1297.9 / 1114.4 / 1068.4 秒 (上限の 3.1〜4.3 倍)、実 repo (findings 0 件、走査省略) は
  18.1 (warm-up) / 14.1 / 15.5 / 9.1 秒で上限内。段 4 §3 に結果を見る前に固定した「fixture で超過なら land せず、裁定パッケージへ
  返す」は、「裁定へ返す」が 2026-09-14 のユーザー指示と整合しないため、codex 2 本 (決定側 = land、点検側 = 見送り) に相談して
  親が決めた: **改善 (対照系列すべての最小 936.2 秒を変更後の max 335.8 秒が下回る) と実 repo の上限内を代替受理条件とする
  本 wave 限定の追補 D を置いて land する。** 上限達成とは記録しない。点検側の最も強い反対理由 (結果後に凍結条件を解除する
  手続き上の不利益、第 1 段を保存して第 2 段と合算で land する道は閉じていない) は追補 D に逐語で残した。new16-7 (327.0 秒) は
  親の onerror probe との同時走査 (待ち手の鍵の取り違え) で無効とし、値と理由を記録した (戻しても判定は変わらない)。
- **段 5 の第 1 案 (探索根直下の subdirectory 単位に `os.walk` を worker へ配る) は実根で tail に頭打ちになった。**
  最初の 60 秒は約 14,500 file/秒 (変更前の約 10 倍) で進むが、`dev-wave-suite-floor-recheck/…/pytest-of-tanab/…`
  (pytest tmp repo の森) を 1 worker が 15 分以上逐次に歩き、列挙 1042 秒で変更前 warm 935 秒より遅かった。
  段 6 で directory 1 個 = 1 task の work queue + walk key (逐次版 first-seen の再現) へ替え、列挙 110〜335 秒。
  段 4 §3 の「prototype 判定 (列挙倍率 < 1.2 なら停止)」は、並列段の速度が「Python thread では出ない」という前提を
  反証したため停止でなく分割単位の是正へ進めた (erratum は一次資料)。
- **現行 main は findings 0 件で走査が省略される (41 秒)。** 探索根の外に fixture repo (到達不能 commit 1 本・
  候補 4 file) を置いて走査を強制し、変更前 tool (main `abc7085ae` の bytes を job dir へ写し `--repo` 指定) を
  同時刻対照に挟んだ。実根 (直下 1,252 entry、約 185 万 file) は昨日 (176 万 file、warm 455 秒) から増えており、
  本日の変更前 warm は 935 / 1297 / 1113 秒 (load 20〜90 の共有 login node)。
- **段 3 の両レンズが親 brief の数値と裁定の読みを 5 件倒した。** warm 455 + 113 は cold 残余の混算 (warm は
  478.1 = 455.4 + 22.7)、P1「D958 の受理条件は上限超過でも land を拒まない」は逐語から導けず撤回、I4「代表を path 昇順
  最小にしてよい」は非等価 (同 inode の alias でも `os.open` の失敗有無が path で変わる)、I6 の例外契約が広い、
  「最大 job dir 59,723 file」は被覆表の値。login 計測が runbook §7 と不整合という指摘は一部 refuted (同節の列挙は
  CC 計測、D958 自身の受理値が login)。計算ノードは補助系列にした。
- **段 6 レビュー 2 本は GO (must-fix 0)。** nit 4 件 (同値 key の OID 挿入順の tie-break、読めない dir を worker 数超に、
  M5 の局所 witness、例外 test の join 検証) を fix 子で反映 (反実仮想 4 件すべて赤化)。
- **並列走だけに「repo 外候補の確認不能」(scan_failures) が高負荷の窓で出た** (2 / 11 / 149 / 220 件、他の並列走と
  逐次走は 0)。探索根では同時刻に他 wave の mutation worktree (1 本 26,000 file) が生成・削除されていた。churn の無い
  静的な複製 (59,927 file) では old / new16 / new1 の 6 走が逐語一致・失敗 0。Codex author の onerror 記録 probe (path・errno・
  走査後の存在) の正例実験 — 16 worker の走査中に 5,120 dir を rm -rf — で ENOENT 123 件 (全件その木の下・走査後に不在) を再現し、
  1 worker では 0 件。機序 = 親が列挙してから子 task が走査するまでの遅れが queue で長く、その間に消えた directory を
  `onerror` が数える (規則は同じ、観測の機会が違う、抑止は増えない)。個々の件数の path は取れておらず、同時刻の他 wave の
  削除への帰属は状況証拠。
- 実走: 焦点走 `test_audit_dangling_commits.py` は段 5 後 153 passed (login)、fix 後 155 passed (計算ノード)。
  provenance full 10,923 件・新規違反なし。受入全走は本 fragment の commit 時点では未投入 (docs commit 後に wave worktree から
  投入し、結果は land receipt と job dir の `acceptance-*.log` に残す)。
- **変異 matrix (container worktree、`run_tests.py` 1 file、probe と本走で各 12 request = baseline + 11 変異)。**
  probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走。本走は baseline PASSED、負例 9 件 (M1〜M9) すべて KILLED で
  期待 node と観測 node が完全一致、等価変異 M0 (docstring) と M4b (`followlinks=True`、1 yield しか使わないため等価) は
  SURVIVED、MISMATCH 0。専属 killer: M6 (worker 例外の握りつぶし) → `test_parallel_offrepo_scan_propagates_worker_exception`
  1 node、M7 (worker からの heartbeat) → `test_parallel_offrepo_scan_heartbeat_runs_on_caller` 1 node、M9 (空候補で queue
  生成) → `test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool` 1 node。M2 (sorted 末尾の子 task を落とす) は
  既存 37 node、M8 (既定 workers 0) は 41 node。M4 は `followlinks=True` では等価変異になるため `islink` 判定の除去へ
  再照準した (fix 子の指摘)。
- 残存 (scope 外、記録のみ): `check_branch_rescue.py` の env allowlist に計測用 env が無く掃除経路は常に既定 16
  (T-2663 の射程)。thread 生成に失敗する環境では逐次版なら完走した監査が rc=2 になりうる。例外後の終了待ちは
  実行中 task の I/O 完了まで上限なし。cold の倍率は login では測れず、計算ノードの 1 走目 (77 秒) は補助観測。
- 工数: codex 子 9 本 (plan 1、consult 2、author 1、fix 2、review 2、probe author 1、全段 `gpt-6-astra` / `medium`)。
  親の実測は login 計測 20 走超 (fixture 14、実 repo 5、静的 6)、計算ノード 4 走 (generic dispatch)、変異 2 走
  (probe 12 request + 本走 12 request)、焦点走 3 本、provenance full 2 本。

## 次の一手差分

### 完了

- [T-2637] 第 1 段 (並列化) を実装し、実根 warm の同時刻対照で 3.2〜9.4 倍 (走査強制 fixture の 6 走 max 335.8 秒は D958 の
  文言では不合格、実 repo は上限内、本 wave 限定の追補 D で受理)、findings / suppressions / unreferenced_copies の同一性を
  静的な複製で固定した。第 2 段の有効化条件 (第 1 段の実測で 300 秒に入らないことを示す) は warm の fixture で満たした。
  remaining: none
  base: 096f8e67308689fc81855ff5751f3052eff39dc4fedb0a28f2d7af67028587c5

- [T-2660] Python thread の実測倍率 (login warm の同時刻対照で列挙 4.95 / 5.4 / 9.4 / 5.5 倍) を取り、並列禁止 test を等価性検査へ
  置換して着地した。(b) の cold は計算ノード bnode044 の 1 走目 (77 秒) を補助観測として記録したが、4 走が同じ node に割り当てられ
  「別 node の 1 走目」の形では取れなかった。第 2 段の判断は warm の実測で足りる (相談 A) ため cold を追わない。
  remaining: none
  base: 61022f1b50206108859b11421600fd0fb14feb1473a64295569597eac554ba17

### 更新

- [T-2661] **P2・着手可能**: 第 2 段 (掃除では走査 off・救出 triage では full の用途分離)。第 1 段の実測 (走査強制 fixture、
  login warm) で有効 6 走の監査全体 max 335.8 秒が所要上限を超え、D2038 / D2104 項 20 の有効化条件 (第 1 段で 300 秒に入らない
  ことを示す) を満たした。計算ノードでは全条件 300 秒以内 (bnode044)、cold は未測定なので「全環境で超過」とは言わない。
  付ける条件 5 件 (未実施と否定結果の分離、台帳通知の増加の開示、D970 / D1031 を一般許可にしない、off / full の入口と実行主体の
  固定、`check_branch_rescue.py` の子 process 環境 allowlist の同時修正) は 2026-09-16 の一次資料 README §5。用途分離は未実装・未受理。
  base: 227ab8a9871c6fb4c6d28ee05853f5104e1c19edf0764f200d55584c1459638e
