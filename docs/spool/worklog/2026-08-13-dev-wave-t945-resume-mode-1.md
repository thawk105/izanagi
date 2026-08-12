---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t945-resume-mode
seq: 1
title: 起動 gate の再開モードは「新設」ではなく「無条件 bypass の条件付け」だった — 包含偽装 3 経路も封鎖した (コード + docs、変異 16/16 KILLED、branch worktree-dev-wave-t945-resume-mode)
---

## 本文

- **裁定の前提が実測で覆った。** 2026-08-12 第 6 束の裁定は「checker へ再開モードを足す」だったが、
  `--mode resume` は checker 初版 (commit `aaafa772`) から**既に存在**していた。ただし裁定文が
  求める条件 (main 包含・0 遅れ) を持たず、点 1 だけでなく作業 branch と clean tree も無条件に
  素通ししていた。実体は「モードの新設」ではなく「fail-closed gate の中にあった bypass mode を
  条件付けし、点 2 以降を締め戻す」作業だった。設計は {{D:startup-resume-mode-is-conditioned-fresh}}。
- **敵対検証をユーザーが受入条件に指定したため、段 2・3 と段 6 review を省かない全経路で回した。**
  段 3 の 2 レンズが 34 所見 (real 22 / refuted 12)、段 6 の 2 レンズが 19 所見 (real 8 / refuted 11)。
  最大の収穫は「`refs/heads/main` を symbolic ref にすれば replace / graft を使わずに包含を偽造
  できる」で、しかもこれは **fresh の等式検査も同じ OID で通す**。片方の mode だけ塞ぐと新設した
  保証が成立しないため、symbolic ref 拒否だけは mode 共通へ広げた ({{D:startup-gate-containment-is-raw-graph}})。
- **棄却した所見 (主なもの):** 「既定 mode・環境変数・設定ファイルから resume が暗黙有効になる」
  (parser は literal default と 2 値 choices のみ)、「INFO 文字列が gate の根拠へ流入する」
  (`main()` は表示後に破棄し gate は独立に git を再実行)、「`--mode` の表記揺れで resume 枝へ
  入れる」(未知値はすべて unsupported failure)、「`_commit_all` が status を空にできない」
  (`external/ccbench/.git` を同一 bytes で退避・復元し、削除と symlink は index へ commit する)。
- **`git rev-parse --git-path info/grafts` は終端 symlink を解決した path を返す**という実測を得た
  (最小再現で確認)。`--git-path` の結果だけを `lstat` すると dangling symlink の graft を検出
  できない。git common directory へ自分で連結する形に変えた。
- **scope 外として裁定へ返す残件を 7 件立てた** (下記の新規項目)。いずれも `--mode resume` 固有では
  なく wave 前から fresh 経路にも存在する穴・非保証であり、修正はいずれも別の受理集合を動かす。
- **変異は 2 走した。** 1 走目 (probe、spec sha `5cedcdb0…`) は 13 KILLED / 3 MISMATCH / SURVIVED 0。
  MISMATCH 3 件はすべて「予測より広く検出された」方向で、期待集合が観測集合の真部分集合だった
  (`_commit_all` が HEAD を 1 commit 進めることを親が見落とし、resume 正例が 1 件増えていた)。
  完全集合で再登録した 2 走目 (spec sha `b9d13203…`) は **16/16 KILLED、MISMATCH 0、SURVIVED 0**。
  probe の spec と結果は `mutation-spec-probe1.json` / `mutation-out-probe1.json` に保全した。
- **main 由来の既知赤 1 件を確認した。** 2026-08-13 00:45 に main へ入った 4 親の octopus merge
  `d1de13ad` により `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が決定的に赤。本 wave で一次確認 (`validate_condition_freeze_at`: `7c9ac465` GREEN /
  `d1de13ad` RED / `adf7997f` RED)。本 wave の差分から到達しない。
- **効くのは `DW-O20` 経由の手動実行だけである。** repo 内に checker の自動 caller は 0 件で、
  supervisor の `resume RUN_ID` は checker を呼ばない別契約。今回の変更で supervisor 側の受理集合は
  変わらない。
- **工数 (receipt.json 実測):** codex 子 8 本、accepted 7 / not_accepted 1、
  wall clock 合計 5915 秒、output token 合計 259,241。1 本目の敵対レンズ (luna) は
  `max_cli_reported_tokens` の観測上限 1,000,000 に当たって SIGTERM (`output_bytes=0`)。
  上限を 3,000,000 へ上げて再走し受理した。
- **セッション異常:** 背景待ち手の完了通知が 3 回誤発火した (producer 生存・`.done` 不在・成果物
  不在なのに completed)。成果物実在・`.done`・producer 死の 3 点照合で毎回検出し、待ちを張り直した。
  通知だけで次段へ進むと成果物ゼロのまま先へ行く。

## 次の一手差分

### 完了

- [T-945] 起動 gate の再開モードを裁定 (i) の形へ是正した。`--mode resume` は「点 1 だけを
  『local main を包含し 0 commit 遅れ』へ置換した fresh」となり、branch・進行状態・clean tree・
  submodule・handoff は mode 非依存で必ず走る。未知 mode は CLI と Python API の双方で fail-closed。
  包含の偽装 3 経路 (replace ref / legacy graft / symbolic main) を封鎖し、`DW-O20` に
  `--mode resume` の指定を明記した。
  remaining: none
  base: e892d051b694bd176a19f6d5eda62fbf06eab81b8c3d75c9e9027abe7447099a

### 新規

- {{T:startup-gate-residual-hardening}} **P2・ユーザー裁定待ち**: 起動 gate の残る穴・非保証 7 件を
  裁定へ返す。いずれも `--mode resume` 固有ではなく wave 前から fresh 経路にも存在し、修正は
  別の受理集合を動かすため T-945 の scope 外とした。(R-1) `_check_no_operation_in_progress` は
  `Path.exists()` なので dangling symlink の `MERGE_HEAD` / `rebase-*` を素通しする。
  (R-2) `_check_fresh_branch` は short 名しか見ず `refs/remotes/...` を指す symbolic HEAD を通す。
  (R-3) handoff 検査は opt-in のままで `DW-O20` の foreground 経路は `--forbid-worktree-handoff` を
  付けない。(R-4) clean-tree は `--ignore-submodules=none` を固定せず submodule dirt を設定で
  隠せる。(R-5) `--repo` と期待 worktree の束縛・wave identity の認証・自 wave checkpoint OID の
  照合がない (本 wave では `--help` と `OK:` 行へ「認証しない」と明記するに留めた)。
  (R-6) supervisor の `resume RUN_ID` は checker を呼ばない別契約で、全再開 gate の一体化は未着手。
  (R-7) graft 検査・symbolic 検査・`rev-list` の間に TOCTOU があり、検査後に main が進むと
  「古い main を包含」で緑になりうる。R-5 と R-7 は同じ層 (caller 側で対象 main OID を束縛する)
  の設計で、まとめて裁定するのが自然である。
