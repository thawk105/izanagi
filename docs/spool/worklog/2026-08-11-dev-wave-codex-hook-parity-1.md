---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-codex-hook-parity
seq: 1
title: codex へ PreToolUse を配線し apply_patch 経由の proof chain 直接書き込みを塞いだ (コード + docs、branch worktree-dev-wave-codex-hook-parity)
---

## 本文

- **発端はユーザーの依頼**「codex のレート枠が戻ったので、claude の枠を先に使い切ったら codex 単独で
  dev-wave を回すことになる。同等に振る舞うか今のうちに検査して、まずければ詰めたい」。
  検査の結果と裁定パッケージを提示し、ユーザー裁定は**全問で推奨案採用**
  (問 1 = 配線する、問 2 = 実装は Codex author、問 3 = 受入は sandbox 外実行 + 配線までは手投入)。
- **文書化されていた前提が現行 Codex では成り立たなかった。** `hooks/README.md` は「Codex には
  hook を配線できない」としていたが、codex-cli 0.146.0 では hook は stable feature で既定有効、
  イベント名も payload も Claude と同型で、PreToolUse は shell も apply_patch も実際に阻止した。
  塞ぐ手段が実在するのに塞いでいない状態だった。{{D:codex-hook-wiring}}
- **本 wave で実測して初めて分かった 4 点** (いずれも設計を変えた):
  (1) Codex は hook が exit 2 のときだけ止まり、**hook command 自体の失敗は素通し**になる。
  (2) hook は Codex セッションの cwd (repo の subdirectory になりうる) で実行され `CODEX_*` は渡らない。
  そのため相対 path を repo root 基準で解決すると `../output/campaigns/.../wal.jsonl` が通った。
  (3) **信頼登録の無い hook は無警告で無視される。** 配線しただけでは何も守られない。
  (4) Codex は `.codex/` 配下へ構造的に書けない (「writing outside of the project」)。
  このため配線ファイルだけは Codex author 子が書けず、親が書いて trailer に明記した。
- **敵対相談・敵対レビューはいずれも NO-GO を返し、実装前後で合計 5 件の実 bypass を潰した。**
  相対 path の基準ずれ、Delete/Move 元の symlink entry、bootstrap の PATH 欠損 fail-open、
  祖先 symlink alias、Bash event の偽装。段 3 の指摘 1 は親が独立に再現して裏取りした。
- **scope 外として裁定へ回した real 所見**: guard_bash の既知限界 (script 経由・変数展開・
  persistent shell) と `output/s8b-freeze` の非防護、MCP/apps/plugins/子の書込み面、CLI version の pin。
  レビュー B の「発火検査を受入全走へ自動登録せよ」は、計算ノードが直接外部通信できず Codex CLI の
  到達性も未実測であるため**前提未確立として部分 refuted**にし、ログインノードの手動 gate とした。
- **本 wave が主張できる範囲を docs に明記した。** 閉じたのは apply_patch 経由と Bash 経由 (Claude と
  同じ既知限界つき) だけで、「Codex の proof chain 防護が Claude と同等になった」とは言わない。
- **現時点で発火検査は rc=1 である。** hook の信頼が未登録で発火しないためで、gate がそれを正しく
  検出している。緑にするにはユーザーが対話 Codex で hook を承認する必要がある。恒真な緑を作らないため、
  gate を緩めていない。
- **段 3 で子を 2 本空費した。** 原因は 2 つで、片方は `Selected model is at capacity`、もう片方は
  **Codex 子が web 検索を使うと成果物が必ず不採用になる**という harness の未知の相互作用だった。
  後者は {{F:codex-web-search-evidence}} として起票する。回避のため prompt に web 検索禁止を明記した。
- 検査: `test_hooks.py` + `test_codex_hooks.py` を計算ノードで実走し 257 passed / 1 skipped / rc=0。
  変異 5 件 (wave 前の形への revert を含む) はすべて期待どおり KILLED、harness rc=0。
  provenance 全史監査は新規違反なし。

## 次の一手差分

### 新規

- {{T:codex-hook-trust-and-surfaces}} **P1・ユーザー手番**: 対話 Codex で hook の信頼を承認し、
  `python3 tools/check_codex_hooks.py` が rc=0 になることを確認する。あわせて scope 外とした
  3 面 (guard_bash の既知限界と freeze、MCP/apps/plugins/子、CLI version pin) の扱いを裁定する。
