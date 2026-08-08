# 段 1 brief — 到達不能監査に repo 外正本の探索を足す (dangling-audit-offrepo-authority)

## scope

`tools/audit_dangling_commits.py` の判定に **4 番目の抑止条件**を足す。到達不能 commit が変更した
path のうち、**repo 外の dev-wave 作業領域に同じ basename・同じ bytes の実体があるもの**は
「失われていない」として報告から外す。既存 3 条件 (到達不能 / main の tree に不在 / 他 local branch
tip の tree に不在) は 1 文字も変えない。編集面は同 tool と
`orchestrator/tests/test_audit_dangling_commits.py` の 2 ファイル、加えて repo 外 path の所在を書く
`docs/pegasus-runbook.md` §7.2 (親が書く docs)。

## 確定済みユーザー裁定 (2026-08-08 /rulings、発話「推奨通りで」)

一次控え = repo 外 `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-07-dangling-audit-alarm-fatigue.md`。

- **(b) 採用** — repo 外の正本を探しに行く。本 wave が実装するのはこれだけである。
- **(c) 採用** — 裁定済み残骸 ([T-409] / [T-213]) は git gc の自然回収に任せる。実装なし。
- **(a) 不採用** — ack 台帳は作らない。sha を記録して黙らせる機構を足してはならない。
- **(d) 不採用** — `git gc --prune=now` 相当の即時 prune は実行しない。**不可逆操作は本 wave で行わない。**

## 段 1 実測 (前提の再検証、DW-G01 の生死実験を含む)

1. 現状 = `--repo /work/1/SFC/tanab/izanagi` で **rc=1・8 commit・28 (commit,path) 対**、wall 9.7 秒。
   群は [T-409] 4 / [T-213] 2 / [T-574] 2 で、2026-08-07 の起票時と同一。
   (訂正: 初版は「24 対」と書いたが、24 は失われた **basename の異なり数**であり対の数ではない。
   段 3 lensA-4 が検出し、段 4 で 28 対と再実測した。)
2. 生死実験 = 到達不能側 blob と `dev-wave-jobs/` 配下の **basename 一致 + bytes 一致**を照合すると、
   [T-574] `probe_g2_consumers.py` (裁定が指した偽陽性) に加え [T-409] の wave 成果物 11 本が一致
   (計 13 対)。`README.md` は同名 121 件あるが bytes 一致 0 件で残る。
   **この述語は段 4 で採らなかった** — 段 4 実測 B により landed 参照の連言を足し、抑止は 2 対に絞った
   (`s4-adjudication.md`)。どちらの述語でも commit 数は 8 → 6 で同じ。
3. 対応関係 = repo 内 `output/insights/2026-08-06_t574-historical-resolver/` ↔ repo 外
   `dev-wave-jobs/t574-historical-resolver/`、repo 内 `2026-08-04_t409-impl-superseded/` ↔ repo 外
   `t409-impl-trigger-grammar/`。**ディレクトリ名が一致しないので相対 path 照合では検出できない。**
4. コスト = `dev-wave-jobs` 全走査 1946 dir / 20544 file / wall 2.0 秒。
5. 環境変数の先例 = `IZANAGI_WAVE_LEASE_DIR` (runbook §7.3)。`IZANAGI_DEV_WAVE_JOBS_DIR` は
   repo 全体で未使用 (`grep IZANAGI_` で 10 個の既存変数と衝突しないことを確認済み)。

## 既存被覆と純増検出力 (機構名でなく性質で検索した)

現行 tool は **path 名の有無しか見ない** (`audit()` の 3 条件、`tree_paths()` は名前集合)。blob・
patch・内容を比較する経路は tool にも既存テスト 8 本にも存在しない。repo 外を参照する経路も無い。
**純増は「到達不能 blob の bytes と、repo 外実体の bytes が一致することを確認して初めて抑止する」
判定 1 つだけ**であり、既存 3 条件のいずれの言い換えでもない。

## 不変条件 (破ったら停止)

- tool は read-only を維持する。repo にも repo 外にも書かない。`git` は読み取り command のみ。
- **抑止を silent にしない。**抑止した (commit, path) と、根拠になった repo 外正本の絶対 path を
  必ず出力する。rc=0 のときも出す。抑止件数が分からない出力は masking であり不可。
- 抑止条件は **bytes 完全一致**に限る。basename 一致だけ、size 一致だけ、mtime、path 断片一致では
  抑止しない。到達不能側が blob でない (削除・gitlink・symlink) 場合は抑止しない。
- 探索根が未指定なら**探索を行わず、行わなかったことを出力に書く**。既定で無音の縮小をしない。
- repo 外 path を repo 内ファイルへ焼かない (機種依存の絶対 path は runbook にだけ書く)。
- [T-593] (事項 1(c) 第 2 警告カテゴリ、事項 4 refs snapshot 再試行、事項 6(a) fixture 隔離) と
  [T-516] は scope 外。実装しない。

## 成果物影響 (DW-G05)

実装しない場合、監査は裁定済み残骸で rc=1 に貼り付いたまま `/cleanup-branches` のたびに同じ 8 件を
再判定させ、**次に本物の未 land 作業 (worklog / failures fragment、insights、campaign 成果物) が
到達不能になったとき、その 1 件が 6〜8 件の既知ノイズに埋もれて台帳から永久に欠落する。**
F118 の恒久対応が「鳴りっぱなしで無視される gate」に退化するのを止めるのが本 wave の値である。

## 親の provisional 裁定 (P1〜P5 — 攻撃対象。段 3 で潰してよい)

- **(P1) 探索根の与え方**: 環境変数 `IZANAGI_DEV_WAVE_JOBS_DIR` を既定とし、`--offrepo-root`
  (複数指定可) で上書きする。tool にも `.claude/commands/cleanup-branches.md` にも絶対 path を
  焼かない。所在の正本は runbook §7.2。
- **(P2) 照合述語**: basename 一致 + bytes 一致。実測 3 が示すとおり相対 path 照合では効かない。
  size で prefilter してから hash する。
- **(P3) 出力**: 抑止分は findings から外し、独立の節「repo 外正本で抑止」に
  (commit, path, 正本 path) を列挙する。rc は残った findings だけで決める。
- **(P4) 走査の安全**: symlink を辿らない (`followlinks=False`)。読めないファイルは候補から外し、
  抑止根拠にしない。走査エラーは rc=2 でなく「抑止しない」側へ倒す (fail-closed = 報告する側)。
- **(P5) 探索根の正当性**: 探索根が repo work tree の内側なら拒否する。repo 内の untracked な写しは
  「repo 外正本」ではなく、抑止根拠にすると自作自演の masking になるため。

## 成果物の形と分割方針

- 実装単位は 1 つ (`tools/audit_dangling_commits.py` + `orchestrator/tests/test_audit_dangling_commits.py`)。
  ファイル所有が素集合にならないので分割せず、段 5 は Codex 実装子 1 本。
- docs (runbook §7.2 への環境変数 1 段落、spool fragment) は親が書く。
- 本 wave は安全監査の報告集合を縮める = DW-C00 の「受理集合が変わる」に該当するため**軽量版に
  しない**。段 2 プラン、段 3 敵対 2 レンズ、段 6 レビュー 2 本を省かない。
- 受入・実測環境 = Pegasus。受入全走は runbook の dispatch 経路、受入 lease を claim してから投入する。
