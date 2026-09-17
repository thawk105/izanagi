# 段 1 brief — [T-2661] 到達不能監査の用途分離 (掃除 = repo 外走査 off、救出 triage = full)

作成: 2026-09-17 JST、基準 main `38353207f` (= origin/main)、branch `worktree-dev-wave-t2661-rescue-scope-split`、
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2661-rescue-scope-split`。

## 研究前進 (土台)

`/cleanup-branches` の到達不能監査 `tools/audit_dangling_commits.py` は、findings があると repo 外走査
(探索根 `/work/1/SFC/tanab/dev-wave-jobs`、約 185 万 file) を走らせ、第 1 段 (並列化、T-2637、D2115〜D2117) 後も
走査強制 fixture で warm 6 走 max 335.8 秒 > 所要上限 300 秒 (D958、tool 内定数) だった。掃除が止まると worktree
(現在 145 本) と branch が溜まり、共有 checkout の untracked 走査・land・受入が遅くなる (entry 1521、F945 型)。
最小差分 = 掃除経路では走査を**明示 off** (findings は core の集合そのもの = full の上位集合)、救出 triage だけ full。
完了判定: (a) off / full の入口 test 緑 + 掃除 2 入口 (command §1、rescue gate の子 process) が off に固定、
(b) 実 repo と走査強制 fixture で off の独立 3 走 (warm-up 1 走捨て) max ≤ 300 秒 (D958 項 1 の形、掃除入口のみ)、
(c) 現行 tool で取った rc 0→3 の具体例 (job dir `probe_env_inherit.json`) が変更後は「off で rc 3 + 開示行」になる。

## scope

- 実装面 (Codex `role=author`、D95): `tools/audit_dangling_commits.py` (明示 mode、off の開示行、full の fail-closed、
  `AuditReport` の mode field)、`tools/check_branch_rescue.py` (`_audit` の argv に off、`_child_env` allowlist から
  `IZANAGI_DEV_WAVE_JOBS_DIR` を除く、JSON `ledger.audit.offrepo_scan`)、`.claude/commands/cleanup-branches.md` §1 の
  監査 bullet (exact 文案は段 4 で固定)、`tools/check_docs.py` `CLEANUP_COMMAND_SHA256`、
  `orchestrator/tests/test_check_docs.py` (`_SYNTHETIC_CLEANUP_COMMAND` / `_EXPECTED_CLEANUP_COMMAND_SHA256` / 予算 fixture)、
  `orchestrator/tests/test_audit_dangling_commits.py`、`orchestrator/tests/test_check_branch_rescue.py` (p04 の期待更新を含む)。
- docs (親): `docs/unreachable-object-ledger.md` (「dangling audit の分岐」に off / full の入口・実行主体・rc 0→3 の開示・
  引き渡し契約・D970 / D1031 の射程)、`docs/pegasus-runbook.md` §7.2 (off / full の使い方 1〜3 行)、insight README、
  spool fragment (worklog / decisions)、変異台帳。
- scope 外: 追加の gate・台帳、T-2662 (境界 helper)、T-2664 (hardlink alias)、`IZANAGI_AUDIT_SCAN_WORKERS` の allowlist 追加
  (off の子には無意味、T-2663 の残部は本 wave で消える)、full 経路の所要改善、cold 計測、cleanup command §2〜§5 の変更。

## 確定済みユーザー裁定

- D2104 項 20 (第 1 段を採り、第 2 段は第 1 段の実測で 300 秒に入らないことを示してから)。有効化条件は T-2637 の warm
  fixture 6 走 max 335.8 秒で充足 (worklog 1614、D2117)。
- 一次資料 §5 の条件 5 件: (1) D2034 の順序 [充足]、(2) 未実施と否定結果の分離、(3) 台帳通知増加の開示、
  (4) D970 / D1031 を一般許可にしない、(5) off / full の入口と実行主体の固定 + 子 process 環境 allowlist の同時修正。
- 依頼文: 着手直前の local main から fresh worktree、/cleanup-branches 稼働中は変更後経路を掃除に使わない (peer
  `cleanup git branches [41ffa9]` 稼働中 = main の現行 tool を使う)、Codex author、変異事前登録、規律 2 を緩めない、本題のみ。
- D958 (所要上限は wave 受理を拘束、掃除の削除可否は拘束しない)、D2034 / D2038 / D2039、D247 (抑止の連言条件)。

## 不変条件

- I1. 規律 2: 抑止 (finding を消す側) を増やす変更を 1 bit も含めない。off の findings == core の findings
  (`audit_with_offrepo` の走査なし分岐と同一集合)、suppressions / unreferenced_copies は空。full は現行と同一出力。
- I2. off は repo 外の filesystem に触れない (walk なし、blob metadata の候補読出しもしない)。
- I3. off と「探索根未指定の未実施」は stdout で区別できる別の行を出す。off は「全走査して一致無し」と読める表示をしない。
- I4. `full` は探索根 (CLI か env) 無しでは実行しない (rc 2、「実行できません」経路)。未実施を否定結果にしない。
- I5. `check_branch_rescue.py --ledger-check` の子 process は常に off で起動し、`IZANAGI_DEV_WAVE_JOBS_DIR` を渡さない
  (2 重防壁: argv と env)。JSON に mode を開示する。既存の rc 契約 (0 / 2 / 3 / 64) と通知 kind は増やさない。
- I6. cleanup command は byte 予算 6,204・最長行 110 内、§1 の監査 bullet に `python3 tools/audit_dangling_commits.py` と
  `docs/unreachable-object-ledger.md` を共起させる (test_branch_rescue_ledger の edge 検査)。digest 定数 2 箇所を同時更新。
- I7. 既存 test の pin (「探索を未実施」「照合可能な候補 basename 0 件のため走査省略」「repo 外の同一実体で抑止 N」) は維持。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 入口は `--offrepo-scan {off,full}` の 1 flag。省略時は現行どおり (root があれば走査、無ければ未実施を開示)。
  off + `--offrepo-root` は usage error (rc 2)、off + env root は env を無視し「明示 off」と開示。
  代案「flag 必須化 (省略を拒否)」は 127 test・runbook・docs の全 CLI 例を変えるため採らない。
- (P2) 掃除の 2 入口 = command §1 の単独実行 (off) と rescue gate の子 process (off)。救出 triage の full は
  `docs/unreachable-object-ledger.md` の「dangling audit の分岐」が単独実行として固定する (command には書かない、予算 3 bytes)。
- (P3) `_child_env` の allowlist から `IZANAGI_DEV_WAVE_JOBS_DIR` を外す。git 子・landed checker 子はこの env を使わない
  (grep 0 件)。argv の off と二重にするのは、片方が退行しても走査が復活しないため (変異で各々を殺す)。
- (P4) rc 0→3 の開示は (a) JSON `ledger.audit.offrepo_scan: "off"`、(b) 台帳 doc の引き渡し契約 (off の
  `unledgered-audit-finding` は「repo 外の同一実体が未確認」の状態で出る → full を単独実行 → 抑止された対は D247 で
  要確認から外れ台帳 entry 不要、抑止されない commit は従来どおり追記候補で破棄は commit ごとの裁定)。
  通知 kind の追加・台帳 field の追加はしない (追加の gate・台帳は scope 外)。
- (P5) D958 項 1 の判定対象は掃除入口 (off) の所要。full (triage) の所要は本 wave で変えず、T-2637 の実測を引用し再判定
  しない。off の実測は実 repo (`/work/1/SFC/tanab/izanagi`、現行 main) と走査強制 fixture (`/work/1/SFC/tanab/t2637-audit-fixture/repo`
  × 実根) の両方 (D2116 の形)。full の同時刻対照 1 走は超過集合の実根デモ (fixture A が off で再表示) のためだけに取る。
- (P6) 変異事前登録 (段 4 で確定): M0 comment 対照 (SURVIVED)、M1 off で走査を続ける、M2 off が env root を読む、
  M3 full が root 無しで未実施 (rc 2 でない)、M4 rescue 子 argv から off を落とす、M5 `_child_env` に root env が残る、
  M6 off の開示行が未実施行と同じ、M7 off + `--offrepo-root` を黙って受理、M8 JSON の mode field 欠落、
  M9 cleanup command digest 定数を旧値に戻す (check_docs が赤)、M10 off で blob metadata / walk に触れる。

## 模擬 / 実の差

- unit test は `tmp_path` の小 repo (模擬)。所要は login node (共有、外乱あり) で実 repo と fixture × 実根 (実)。
  単独性: `ps -eo pid,args | grep "[a]udit_dangling_commits"` で他の監査走行 0 を確認してから。
- 生死確認 (段 1、現行 tool、fixture): env root あり → 子が走査し抑止 (rc 0)、env なし → rc 3 通知 1 件
  (`probe_env_inherit.json`)。変更後は env の有無に依らず rc 3 + mode 開示 になるのが正例。

## 成果物の形と分割

- 実装 commit 1 本 (author、7 file: 2 tool + command + check_docs + 3 test)、fix commit (必要時)、docs commit (親)。
  insight `output/insights/2026-09-17/t2661-rescue-scope-split/` (README + verbatim + 変異台帳)。
- 段 2 plan 1 本 (read-only)。段 3 consult 2 本 (レンズ A: 受理集合・規律 2・未実施/否定の分離・D247 との整合・
  D970/D1031 の射程; レンズ B: 入口固定の穴 (env・argv・第 3 の入口)・rescue JSON/rc 契約・cleanup command の pin 閉包と
  byte 予算・test の殺傷力)。段 5 author 1 本。段 6 review 2 本 + fix。

## 既存被覆 (純増だけ書く)

- D2038 / D2039 / D2034 (順序)、D2115〜D2117 (第 1 段)、D958 / D2116 (判定の形)、D247 (抑止条件)、D970 / D1031
  (28 + 19 件の裁定)、F152 (パイプ禁止)。本 wave の純増は「off / full の明示入口と掃除 2 入口の固定」「rescue gate の
  子 process の env 遮断」「off の rc 0→3 の開示と引き渡し契約」。
