## 段 1 brief (親)

- **研究前進:** 土台。F1022 は受入全走を決定的に赤にする穴で、暫定防壁 (wave 名に `release` を含めない) は memory 依存。
  完了判定 = 同 test が repo path の語に依らず緑で、handshake 行の注入で赤 (変異で実証)。止めている研究は無い (P2)。
- **scope:** `orchestrator/tests/test_pegasus_dispatch_compute.py` の同 test 1 本の検査置換だけ。production
  (`tools/pegasus/dispatch_compute.py::_job_script`) は変えない。追加 gate・他 test の同型是正・docs の一般化は scope 外。
- **確定済みユーザー裁定 (引数):** 着手直前の local main から fresh worktree / Codex author (D95) / 変異事前登録 (a)(b) /
  着地後に暫定防壁が不要になる旨を worklog へ / 規律 2 を緩めない / 本題の検査置換だけ。
- **由来 (一次資料):** T-188 の裁定 FA-4 (`output/insights/2026-07-30/pegasus-compute-node-dispatch/fix-adjudication.md`):
  「計算ノード側が submission dir へ marker を書き、親はその実在を永続性の証拠とする (cross-namespace 証拠)。
  親→job の release handshake は作らない (親死亡で job が待つ形にしない)」。commit a34266d2d で語不在の assert が入った。
- **script に埋まる環境依存文字列 (実測 `_job_script`):** `RESULT` `PROBE` `REQUEST` `MARKER` (submission_dir 配下)、
  `REPO` (repo_root)、`DISPATCHER` (repo_root/tools/pegasus/dispatch_compute.py)、job_name (`izdw-` + submission_dir.name[:10])。
  template 由来の残りは定数 (SFC / gen_S / candidates / env 名 / INFRA_RC) と shell 本文。
- **不変条件:** (i) 既存 3 assert (marker 名の存在・`mv` が `selected=""` より前・`while` 不在) は変えない。
  (ii) 検出力は現行以上: 現行が赤にする「template 由来の release 行」は新検査でも赤。(iii) 環境依存文字列 (path) だけで反転しない。
  (iv) 規律 2: 検査を甘くして通す方向の変更は不採用。
- **成果物:** test 1 本の差分 (Codex author)、変異 matrix (baseline + 負例 + 正例対照 + 等価)、受入全走緑、worklog fragment
  (暫定防壁の memory `wave-slug-must-not-contain-release.md` が不要になる旨)、failures fragment (F1022 へ恒久対応の追記)、insight。
- **分割方針:** 実装子 1 本 (test file 単独所有)。段 2 plan 1 本、段 3 consult 2 本 (レンズ: 規律 2 / 検出力、F1022 型の再発面)、
  段 6 review 2 本。軽量版を採らない理由 = 受理集合が変わる (path に release を含む script を受理する) + 正しさ防壁 (設計不変条件の test)。
- **割れうる前提 (親の provisional 裁定・攻撃対象):**
  - (P1) 検査の形: path を除いた本文を行に割り、`release` (大小無視) を含む行を handshake 候補として全件列挙し、空を要求する。
    ユーザーの括弧書き「marker を操作する release 行」を「release と marker 参照の同一行共起」に狭めると現行より検出力が落ちる
    (`RELEASE=...` 単独行を見逃す) ので、親は「release 行 = handshake 行」の広い定義を provisional とする。
  - (P2) 除く文字列: repo_root だけでなく submission_dir 配下の全 path (RESULT/PROBE/REQUEST/MARKER) と job_name も環境依存なので
    `str(_REPO)` と `str(tmp_path)` の両方 (と shlex.quote 形) を除く。「repo path を除いた本文」の字義 (repo_root だけ) より広い。
  - (P3) 正例対照を test 自身に持たせるか: `repo_root` を `[_REPO, <release を含む合成 path>]` で parametrize し、F1022 の再発を
    test 自身が守る。scope「本題の検査置換だけ」の内側と親は読む (追加 gate ではなく同 test の入力)。
  - (P4) `"while" not in script` は触らない (scope 外)。path 除去後の本文に掛け直すのは同型是正だが、依頼が名指すのは release 行だけ。
- **変異事前登録 (段 4 で確定):** (a) repo path に release を含む fixture で緑 = P3 の parametrize node が baseline で緑
  (+ 変異「path 除去を外す = 旧検査へ戻す」で同 node が赤 = KILLED)。(b) `_job_script` template へ handshake 行
  (例: `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` を `mv` の前に注入) で赤 = KILLED。等価 M0 = comment 行のみ = SURVIVED。
- **受入・実測環境:** login node で焦点走 (test file 単独 + `_job_script` の consumer)、変異 matrix は計算ノード dispatch
  (`tools/mutation_harness.py`、container worktree)、受入全走は `tools/dev_wave_wait.py acceptance` (`IZANAGI_ACCEPTANCE_SHARDS=3`)。
- **条件 dispatch の判定:** DW-O08/O09/O10 (freeze / 凍結 bytes) 非成立 (test file のみ、凍結成果物に触れない)。
  DW-O13 (gate 新設) 非成立 (既存 assert の置換)。DW-O11 (削除) 非成立。DW-O19 (tracked file 一時変異) は変異 matrix で成立 → 段 6 前に読む。
