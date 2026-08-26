---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1774-jsonl-line-split
seq: 1
title: JSONL の行分割を改行だけに限り、codex 子の成果物が U+2028 / U+2029 で全損する経路を断った (コード + テスト、branch worktree-dev-wave-t1774-jsonl-line-split、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **裁定 D971 の実装である。** 着手時点では追認の決定が未 land の branch
  `worktree-rulings-20260826-adopt` にしか無かったため、本 wave は段 1 でその blob を
  直接読んで前提を確認した。段 7 の main 取り込み時点で D971 として着地済みを確認している。
  担い手 2 件 ([T-1774] と [T-1731]) は同じ裁定に含まれるので一括で扱った。
- **裁定文の「6 箇所」の数え方が 2 通りあり、片方は tool を壊す。** [T-1731] は
  「`tools/codex_worker_launch.py` の JSONL 分割 6 箇所」と書くが、同 file の
  `splitlines()` 6 出現のうち 1 つは `git rev-parse --show-toplevel` の stdout であって
  JSONL ではない。ここを `split("\n")` にすると正常な live git 出力の末尾 LF で要素数が 2 になり、
  `len(top_level_lines) != 1` が常に真になって launcher が起動前に必ず失敗する。
  正しい閉包は `orchestrator/codex_roles/events.py` の 1 式 +
  `tools/codex_worker_launch.py` の 5 式で、[T-1774] の「`parse_jsonl` を含む 6 箇所」と一致する。
  段 3 の相談 2 本のうち 1 本が独立に同じ結論へ到達した。
- **親 brief の一般化が 2 箇所で誤っており、段 3 が両方を突いた。** (a) 親は
  「bytes を分割する 5 箇所は現状でも全損経路ではない」と書いたが、`_drain_stdout` と
  `_recompute_attempt_metering` の stdout 側は分割後に `parse_jsonl` を呼び、同関数が
  bytes を str へ decode してから `str.splitlines()` を通る。site 自体は bytes でも
  **経路としては全損に到達する**。局所原因は `events.py` の 1 箇所だけ、経路上の影響は
  上記 2 箇所にも及ぶ、残る 3 箇所は非影響、と 3 分するのが正しい。(b)「行分割は 6 箇所で
  閉じる」は repo 全体では偽で、live reader は LF `rpartition` でも行を切っている。
  以後は「指定 2 file の置換対象 `splitlines()` 6 式」と表記する。
- **親の provisional 裁定 1 件が恒真だった。** 「bytes 側 5 箇所も U+2028 / U+2029 の
  受理だけを検査する」案は、`bytes.splitlines()` がその 2 文字で分割しないため、
  5 変異すべてを SURVIVED にする。段 2 の plan と段 3 の 2 本が独立に同じ指摘を返した。
  撤回し、bytes 5 箇所の killer は CRLF 終端の ASCII JSON event とした。
- **段 6 の must-fix 2 件を実測で却下した。** (a)「受理拡大が 8 種ある」は実測では 3 文字だけで、
  制御文字 5 種は変更前後とも拒否で差が無い。提案された「JSON 文字列の quote 状態を追う
  splitter の新設」は、直す対象が実在しないうえ `strict_json_loads` と二重の JSON 解釈を作るため
  却下した。代わりに U+0085 を負例テストの parametrize へ加えて挙動を固定した。
  (b)「CR だけの空行が blank skip で捨てられる」は、変更前後で挙動が完全に同一であることを
  実測した。本 wave の回帰ではないので裁定パッケージへ送った。
- **段 6 の must-fix 1 件は本物だった。** 新規テスト file が repo 由来の import より前に
  `sys.path` の bootstrap を持たず、`python3 orchestrator/tests/test_codex_jsonl_line_split.py`
  が `ModuleNotFoundError` で rc=1 になった。親が実機で再現し、fix 子が直した後に
  rc=0 / 12 passed を実機で確認した。F42 の再発に至る手前で止めた形になる。
- **実測 1: 封印済み codex event artifact 3,678 件を走査し、CR を含む file は 0 件。**
  「旧版で封印された CRLF artifact が resume 監査で壊れる」という懸念は、その artifact が
  実在しないため発火しない。CR / CRLF の拒否強化を採る根拠にした。
- **実測 2: 受理差は新規受理 3 文字・新規拒否は非 LF 区切り入力だけ。** 詳細と却下した代案は
  {{D:jsonl-line-boundary-is-lf-only}} が正本。
- **scope 外の real 所見を 2 件、裁定パッケージへ返した。** `tools/check_codex_hooks.py` の
  `_parse_events` に同型欠陥が残る件と、bytes 側 5 箇所で CR だけの空行が
  blank skip される件である。どちらも D971 が明示列挙した 6 箇所を広げる話なので実装しなかった。
- **子の工数:** codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 1) と
  焦点再レビュー 1 本。すべて `gpt-5.6-sol` / `xhigh` / rc=0。
  親の焦点走は 8 file で 444 items、440 passed / 4 skipped。
  変異は `DW-M07` に従い全件 SURVIVED 期待の probe で観測 node を集めてから本走した。
  正例 1 本 (空行 skip の除去) は 92 node を落として過剰拒否の検出力を示した。

## 次の一手差分

### 完了

- [T-1774] `parse_jsonl` を含む 6 式を LF 専用分割へ変え、U+0085 / U+2028 / U+2029 を含む
  event 行を受理する負例テストを置いた。実装面は Codex `role=author` が書いた。
  remaining: none
  base: 3cabf739b1f0e150481d3c53ceb78d2e25246cb20e4142e40fbf76dbda086a81
- [T-1731] `tools/codex_worker_launch.py` の JSONL 分割を同じ裁定で [T-1774] と一括で扱った。
  対象は 5 式で、`git rev-parse` の出力を扱う 1 式は JSONL でないため除外した。
  remaining: none
  base: c197f39aa375db61645c6b16a10aeeeca88e2b267bb28b6021ac94bbcf1c65c5

### 新規

- {{T:check-codex-hooks-line-split}} **P2・新規**: `tools/check_codex_hooks.py` の
  `_parse_events` が Codex JSON event の str stdout を `splitlines()` で切っており、
  U+0085 / U+2028 / U+2029 で同型に割れる。D971 が 6 箇所を明示列挙していたため
  本 wave の scope 外とした。同じ修理と負例テストを当てるか、意図的に残す理由を裁定する。
- {{T:dev-wave-s01-anchor-recount}} **P3・新規**: 段 8 の自己改善で `DW-S01` へ
  「裁定の N 箇所は実アンカーで数え直し、同名の非対象は対象外行に残す」「受理集合を変えるなら
  広がる側と縮む側の両方を書く」を足そうとしたが、**L1 層の予算を 150 bytes 超過**して
  入らなかった (10,775 > 10,625)。安全義務を削る圧縮はしないので入口へは入れず、
  dev-wave 文書予算の収容表へ載せる案件とする。本 wave はこの 2 点を実際に踏んでおり、
  片方は tool を常時失敗させる誤りだった。
- {{T:crlf-blank-line-skip}} **P3・新規**: `tools/codex_worker_launch.py` の bytes 側 5 箇所は、
  行に分けた直後の空行 skip が CR だけの行を捨てるため、CRLF の空行を混ぜた stdout / rollout が
  `evidence_status=complete` になりうる。変更前後で挙動は同一 (実測) であり本 wave の回帰ではないが、
  この系が CR を不正と宣言していることとは整合しない。拒否分岐を足すかどうかを裁定する。
