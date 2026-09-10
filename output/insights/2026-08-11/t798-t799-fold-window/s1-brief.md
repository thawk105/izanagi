# 段 1 brief — [T-798] / [T-799] 窓の実測と裁定パッケージ

wave: `dev-wave-t798-t799-fold-window` / branch: `worktree-dev-wave-t798-t799-fold-window`
checkout: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window` (HEAD `9abd23da`)

## scope

1. [T-798] の窓 (apply_fold の state 削除 → land の docs 検査・commit・postcondition) を
   **実際に crash させて**再現し、残骸と復旧経路の実挙動を測る。
2. [T-799] の窓 (fold state が land 起源・base・tested tip を束縛しない) を再現し、
   standalone resume と land recovery の双方で検出力を測る。
3. 各選択肢 (a)/(b)/(c) に、実測に基づく実装コストと検出力を添えて裁定パッケージを返す。

**scope 外 (ユーザー明示):** 本番コードの編集。したがって本 wave の裁定は「実装しない」であり、
段 5・6 を飛ばして `4→7→8→9` とする。変異 matrix は `DW-S04` により免除、受入全走は免除しない。

## 確定済みユーザー裁定

- 「本番コードは編集しないでください」— 実装面の差分は 0 とする。
- probe は repo 外に置く ([T-317] 裁定 = 境界は repo へ入るか)。本 wave の probe は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-fold-window/probe/` にある。

## 不変条件

- 実 repo (`docs/`, `tools/`, `orchestrator/`) を probe が変更しない。測定は tempfile 配下の
  合成 repository と、実 repo に対する**読み取り専用**の実行だけで行う。
- 実 repo の Git admin dir へ transaction state を置かない (置くと実 land を wedge する)。
- 本番 module (`tools/dev_wave_land.py`, `tools/spool_fold.py`) へ monkeypatch を当てない。
  crash 注入は本番が subprocess 起動する `tools/check_docs.py` (fixture 側) に閉じる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** fixture (合成 repo + stub `check_docs.py`) で測った制御フローは、実 repo の
  land / fold の制御フローと同一である。**模擬なのは台帳の中身と check_docs の実装であって、
  測っている経路そのものではない** — `tools/dev_wave_land.py` と `tools/spool_fold.py` は実体を
  import している。窓の**幅**だけは合成では測れないので、実 repo の実物で別途測る。
- **(P2)** `_validate_generated_docs` が `tools/check_docs.py` を subprocess 起動する時点は、
  [T-798] が主張する窓の内側である (apply_fold から返った直後・commit 前)。
- **(P3)** [T-798] の窓の露出は「crash した land の 1 回」に閉じ、正常系の land は影響を受けない。
- **(P4)** [T-799] の standalone resume は、成功しても commit を作らないので、
  必ず [T-798] と同じ残骸に着地する。

## 成果物の形

- 裁定パッケージ (`rulings-package.md`) — 選択肢ごとに「実測した検出力」「実装コスト」
  「成果物影響」を持つ。番号付きの問として返し、親の推奨を明記する。
- worklog fragment 1 本 (`docs/spool/worklog/`) — 実測値と裁定パッケージへのポインタ。
- probe 一式 (repo 外、逐語は insights へ)。

## 並列分割方針

実装面が無いので段 5 は無い。段 3 相当の敵対相談を 2 レンズ (sol / luna) で並列に回し、
**親の実測値とその一般化そのもの**を攻撃対象にする。
