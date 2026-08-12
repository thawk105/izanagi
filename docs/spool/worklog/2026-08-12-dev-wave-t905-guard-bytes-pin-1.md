---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t905-guard-bytes-pin
seq: 1
title: codex 起動前検証へ防壁本体 5 本の bytes pin を入れた — 期待値の権威は local HEAD で、独立 trust root は作らない (コード + docs、変異 6/6 KILLED、branch worktree-dev-wave-t905-guard-bytes-pin)
---

## 本文

- 第 4 束裁定「[T-905] = bytes pin を入れる (防壁の自己完全性は測定束縛でなく信頼境界であり、
  凍結チェーン保留 D328 の対象外)」の実装。起票は worklog (476) の hook-trust wave。
- **穴を模擬でなく実編集で測った。** `hooks/codex_guard.sh` へ 1 行入れて
  `validate_installation()` を実走すると findings は 0 件だった (素通し)。直後に復元し
  `git status --porcelain` 空を確認した。
- **段 3 の敵対 2 レンズはいずれも NO-GO。両方が独立に「local HEAD は co-mutable なので
  独立 trust root ではない」を指摘した。** 親はこれを real と認めたうえで、両レンズの代案を
  実測に基づいて不採用にした。
  - レンズ B の「親管理・worktree 外 manifest」は、期待値が版管理とレビューの外へ出る /
    guard の正当編集ごとに手更新が要り忘れると全 wave の codex 起動が止まる /
    fresh clone・別マシンで manifest 不在なら全停止、という 3 つの**新しい大域故障**を導入する。
  - レンズ A の「wave で凍結した authority commit を渡す」は実測で成立しない。
    `tools/dev_wave_codex.py` の `_resolve_base_commit` が渡す `--base-commit` は
    起動時の `HEAD^{commit}` そのもので、HEAD 比較と同じ権威にしかならない。
  - repo 内のどの trust root (manifest / 定数 / HEAD) も repo へ書ける主体には同様に可変である。
    **本 wave が作るのは改変検出器であって封じ込め境界ではない**と位置づけ、docs へ明記した。
    独立 trust root の新設は粗い provenance 基準に照らして scope 外とし、裁定へ返す。
  - HEAD 案は 3 案で唯一 commit により自己修復し、故障が当該 worktree に局所化する。
- **レンズ A の F2 (transitive trust set) を親が実測で裏取りし、pin 対象を 3 本から 5 本へ広げた。**
  `hooks/guard_bash.py` は import 時に `tools/pegasus_admission_registry.py` の source を
  compile/exec し、その loader が `tools/pegasus/admission_registry.json` から sanctioned path 集合を
  作る。読み込み失敗時は静的 fallback 集合へ落ちるため、guard 3 本だけの pin では**実効ポリシーが
  pin の外に残る**。5 本とも既に checker の `_COPY_PATHS` に live input として入っていた。
- **レンズ A の F4 は部分採用。** 全 path component の非 symlink と canonical containment は採ったが、
  `st_nlink == 1` の hardlink 検査は不採用にした。hardlink は検査後の改変の話であり scope 外とした
  TOCTOU に吸収され、偽陽性源にもなるため。
- **段 6 の敵対レビュー 2 本はいずれも GO・must-fix 0 件**で、fix 段は発生しなかった。
  レビュー B が「docs に書いてはいけない表現」を 9 個列挙したので、`hooks/README.md` の更新へ
  そのまま反映した (「同一 snapshot」「live attestation」「worker が検証済み bytes を使用することを
  保証」「独立 trust root」「全 Codex 起動経路を被覆」など)。
- **変異は 6/6 KILLED。** 初回は probe と明記して走らせ、期待 node の完全集合を実測してから再登録した
  (M1=29, M2=6, M3=1, M4=9, M5=1, M6=75 node)。**M3 は単層では実装の多層防御に mask されうるため
  `both-layers` として事前登録した** (git 不在の finding を空にする変異と、
  `HEAD blob と比較できない` fallback を外す変異の同時適用)。M2 は pin 集合から 5 本目
  (`admission_registry.json`) だけを外す変異で、その path を扱う 6 node を正確に倒した —
  pin 対象拡張が実際に検査されている証拠である。M6 は受理集合を縮小する wave の正例
  (過剰拒否の検出) として登録した。
- **erratum: 本走で M2 に無関係な node が 1 件混ざり MISMATCH になった。**
  `test_all_v3_stages_reject_prior_invalid_attempt[author-None]` が
  `receipt["attempts"][-1]["accepted"] is True` で落ちた。M2 は検査を緩める変異であり因果経路が無い。
  M2 単独で再走すると期待 6 node と完全一致で KILLED になり、混入 node は再現しなかったため
  帰属から外した。**launcher の receipt 系 node が変異走へ 1 件混ざる事象はこれで独立 2 例目**
  (1 例目は worklog (476) の M3)。初回結果は消さず本 erratum に残す。
- **実装子は pytest を実走できなかった** (`qstat -Q` preflight が rc=1、runner rc=16)。
  子は「実装済み・未実走」と正直に申告し、実測はすべて親が行った。
- 追加コストの実測: 起動 1 回あたり git 問い合わせ 5 回で 40.5 ms (3 本時)、5 本で約 57 ms。
  **履歴件数にも tracked file 数にも比例しない。**
- 設計判断は {{D:guard-bytes-pin-authority}} に記録した。

## 次の一手差分

### 完了

- [T-905] codex 起動前検証へ防壁本体 5 本の bytes pin を入れ、承認文言との差を閉じた。
  remaining: none
  base: 34ca3744edcd6185292c8ff3acaaeb48be33d067b340a846d90aa1cdbf9df577

### 新規

- {{T:guard-pin-independent-trust-root}} **P2・新規 (裁定パッケージ)**: guard bytes の期待値は
  local commit graph に束縛された detector であり、独立 trust root ではない。repo 外・署名済み
  authority へ移すか、launch receipt へ guard digest を記録して事後監査可能にするか、
  現状のまま detector として据え置くかを決める。粗い provenance 基準では既定で見送り側。
- {{T:guard-pin-toctou}} **P3・新規 (裁定パッケージ)**: 起動前検証から `Popen` までと、
  worker 存続中の再検証は被覆外。`hooks/` を guard 自身の保護対象へ加える案を含むが、
  受理集合の縮小になるため裁定が要る。
- {{T:guard-pin-other-launch-paths}} **P3・新規 (裁定パッケージ)**: `.claude/settings.json` 経由の
  Claude 側 hook 起動、`tools/codex_reasoning_ab.py`、`tools/run_codex_role.py` は本 pin の被覆外。
  [T-906] (scope 外裁定済み) と同じ面であり、まとめて再訪条件を決める。
