---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-b4-prereg-enactment
seq: 2
---

## 新規

### {{F:shared-tmp-git-marker-reds}}. 共有 /tmp に断続的に現れる空の .git が、/tmp を出力先にする 44 テストを確率的に落とす [環境] [偽陽性]

- 事象: 段 6 の焦点走で `test_campaign.py` が 44 件赤になった。追跡すると
  `orchestrator/campaign/layout.py` の出力先検証が
  「official output_root は repository 外でなければならない」で止めていた。
  原因は `/tmp/.git` という**空の directory** が存在し、`_has_git_ancestor` が祖先を遡って
  `<ancestor>/.git` を lstat するため、**`/tmp` 配下すべてが repository の内側と判定される**こと。
  初回観測は 2026-08-25 23:57 作成のもので、本 wave の開始 (2026-08-26 09:38) より前だった。
  撤去後の再走で 44 件は消えたが、**同ディレクトリは断続的に再出現する** — 監視を並走させた走行で
  13:05:49 / 13:06:46 / 13:07:37-52 に存在を記録し、16:46 にも再作成されていた。
  現れている窓に当たったテストだけが落ちるため、同じ木で緑にも赤にもなる。
- 根本原因: `orchestrator/tests/conftest.py` は TMPDIR を既定 (`/tmp`) のままにする方針を明記し、
  一部テストは `output_root="/tmp/izanagi_x"` を**直書き**する。したがって TMPDIR を差し替えても
  回避できない (専用 TMPDIR で 44 件中 43 件は消えたが、直書きの 1 件は残った)。
  作成元は特定できていない。repo 内に `/tmp/.git` を作るコードは無いことを確認した
  (直接生成と `<tempdir>.parent / ".git"` の両方を全文検索。`.git` を**ファイル**として書く
  テストは 3 件あるが、観測されたのは**ディレクトリ**で別物)。
- 恒久対応: 本 wave では検知の作法を確立するに留める。焦点走・受入で `/tmp` 由来の
  「repository 外でなければならない」が出たら、**まず `/tmp/.git` の実在を確かめ、
  空ならこれに帰属させる**。撤去は `rmdir /tmp/.git` で足り、`mkdir` で戻せる。
  走行中の再出現を捉えるには、走行と並走する監視 (数秒間隔で実在を記録、または実在時に撤去) を
  張る。**作成元の特定と恒久遮断は未了であり、裁定パッケージへ送る。**
- 再発検知: 焦点走・受入の赤を非帰属と判定する前に `/tmp/.git` を見る。
  本 wave では監視を掃除役に変えた走行で「一度も出現せず、それでも赤が残る」ことを確かめ、
  残った赤が環境でなく構造 (下記の別 F) に由来すると特定できた。

### {{F:merge-validation-before-commit}}. 取り込みを commit する前にテストで検証しようとして、契約検査の偽の赤 109 件を踏んだ [手順漏れ] [偽陽性]

- 事象: 並行 wave の着地を取り込み、競合解消の直後に**merge を commit せずに**焦点走を回したところ
  109 件が赤になった。表示は
  `contract-loader-drift: disk bytes が HEAD blob と不一致: enforcement_source_ratification.py` で、
  一見すると取り込みの合成が壊れたように読める。実際に親は一度そう疑った。
  merge を commit した直後に同じ範囲を走らせると **516 passed / rc=0** で、赤は全消えした。
- 根本原因: 契約 loader の束縛検査は**作業ツリーの bytes を HEAD の blob と照合**する。
  merge 未確定の間は HEAD が取り込み前の commit を指す一方、作業ツリーには相手側のファイルが
  載っているため、必ずずれる。**取り込みは commit してからでないとテストで検証できない**という
  構造であり、検証の順序を知らずに回すと必ずこの赤を踏む。
- 恒久対応: 取り込みの検証順序を「競合解消 → `git add` → commit → テスト」に固定する。
  commit 前の実走は、契約 loader を通らない静的検査 (AST parse・関数集合の突き合わせ・
  `git diff --check`) に限る。実体は本 F と、取り込み子への prompt に置く
  「commit は親が行う。あなたは競合解消と編集だけ」という権限境界である。
- 再発検知: 取り込み後の赤で `contract-loader-drift` が出たら、**まず `git rev-parse HEAD` と
  `MERGE_HEAD` の有無を見る**。merge 未確定なら合成の破壊ではない。
