---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1607-mid-merge-codex-author
seq: 2
---

## {{D:mid-merge-author-capability}}. mid-merge の作業木は author capability を渡した live 起動だけが authority docs の bytes 比較を省ける

**決定:** `snapshot_authority` へ keyword-only の `allow_mid_merge` を足す。既定 `False` では
現行と 1 bit も変わらない。`True` かつ「健全な 2 親 merge が進行中」のときだけ、authority docs
2 file の working bytes と HEAD blob の比較を省く。capability を渡すのは
`tools/codex_worker_launch.py` の `_preflight_run` 1 箇所だけで、`stage=author` かつ
`sandbox=workspace-write` のときに限る。`commit` を指定する historical 経路は capability を無視する。

「健全な 2 親 merge」は、`git rev-parse --absolute-git-dir` が返す worktree 固有 git-dir 直下の
`MERGE_HEAD` を `O_NOFOLLOW` で開き、同じ fd を `fstat` して regular file を確認し、同じ fd から
サイズ上限内で読み、内容が lowercase hex40 のちょうど 1 行で、その OID が replacement を無効化した
状態で commit object であること、と定義する。file 不在だけが正常な `False` で、file はあるのに
内容が不正なら fail-closed で拒否する。octopus (2 行以上) は拒否する。

導出値 (model / effort) は従来どおり常に commit 由来 blob から parse する。
`AuthoritySnapshot.as_dict()` の shape、digest 定義、receipt schema V4、historical 再構成の
一致検査は変更しない。merge 進行中であった事実は receipt へ記録しない。

**理由:**
- 受入投入前の local main 取り込み merge の最中は HEAD が wave tip のままなので、main 側が
  authority docs を触っていれば競合の有無に関わらず live 起動が拒否されていた。実測では
  authority docs を誰も触っていない mid-merge は元から通っており、拒否の原因は mid-merge でも
  conflict マーカーでもなく **working bytes と HEAD blob の不一致だけ**だった。
- 親が競合を直接解決するしかない結果、その merge commit は Codex 著者を持てず
  known-violation 台帳へ登録され続けていた。D721 は手で競合解決した merge を実装面から
  除外する免除を却下しており、本決定はその逆方向 — 免除を作らず、Codex が実際に解決できる
  経路を作る — なので D721 と整合する。
- 緩和を全 stage へ開く案は受理集合を不必要に広げる。`snapshot_authority` は stage を受け取らない
  ため、capability を呼び手から明示的に渡す形にしないと plan / consult / review / fix / focus まで
  同時に開いてしまう。受理集合を実際に狭めるのは path 方向の条件ではなく stage 方向の限定である。
- `git rev-parse --verify MERGE_HEAD` の成否だけを sentinel にすると、`MERGE_HEAD` という名前の
  branch へ DWIM 解決するため、merge していない作業木を merge 中と誤認する (実測)。
  物理 file の存在と内容を検査する複合 sentinel が要る。
- 緩和は `git merge` に限局する。rebase / cherry-pick / revert / `rebase --rebase-merges` /
  `git am` / `stash apply` はいずれも競合しても `MERGE_HEAD` を作らない (実測)。

**却下した選択肢:**
- **merge の変更集合に入っている path だけ差異を許す** — `HEAD:path != MERGE_HEAD:path` は
  「incoming がこの merge で変更した」ことを意味しない。wave 側だけが変更した file でも真になり、
  incoming が無変更でも手編集を素通しする (実測)。merge base 相対へ直しても、正当に競合した path
  では任意 bytes を許すため穴は閉じない。stage 限定の方が受理集合を実際に狭める。
- **既存の historical 経路 (`commit` 指定) へ live 起動を流す** — working tree 比較と live の
  v2 必須を同時に外すため、迂回であって正規経路ではない。
- **merge 進行中であった事実を receipt へ記録する** — closed な receipt schema と
  `AuthoritySnapshot.as_dict()` の digest pin を同時に破る。受理集合の可視化は
  negative control 側で担う。
- **大文字 hex40 も受理する** — 受理集合を広げる方向であり、Git は `MERGE_HEAD` へ lowercase しか
  書かない。lowercase 限定は fail-closed 側の狭さであり、承認外の受理を生まない。
