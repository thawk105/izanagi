---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: wave-t340-thirdparty-fetch
seq: 2
---

## {{D:thirdparty-fetch-path}}. third-party source の取得は任意 preflight helper とし、cache は repo 外・publish は mkdir 予約 + rename にする

**決定 (1): 取得経路は `tools/pegasus/` の新規 CLI 1 本に閉じ、凍結ファイルを変更しない。**
凍結 evidence が policy・submitter・job script・driver の 4 本を sha256 で束縛しているため、
既存 shell の取得ロジックには触れない。consumer 接続は submitter の
「destination が既に在れば clone 分岐を通らない」性質を使い、staging を先に埋める形で行う。
submitter 自身の pin/clean 検査と receipt 生成はそのまま走る。

**決定 (2): この helper は取得の権威ではない。** 取得経路は submit receipt にも evidence にも
値として現れないため、「取得の由来が台帳から追える」とは主張しない。helper は任意であり、
最終判定は凍結 shell の pin/clean 検査のままである。helper を必須工程と解釈すると、helper が
追加要求する検査 (origin URL、repo root、Git metadata) の分だけ end-to-end の受理集合が変わる。
任意と定めることで「受理集合を変えない」が成立する。

**決定 (3): cache root は明示必須とし、policy から導出しない。**
`--cache-root` か環境変数のどちらかを必須にし、repo 配下は拒否する。機体固有の値は環境専用
runbook に置く。policy の `gflags_source_path` の親から導く案は却下した — 実測で gflags と glog は
**shallow clone** であり、新規に作る 3 本の self-contained clone とは管理形態が異なる。
無関係な policy field に保存場所の意味を後付けすることにもなる。

**決定 (4): worktree 内 staging への供給は copytree でなく fresh clone にする。**
`git status --untracked-files=all` は **ignored file を列挙しない**。上流の `.gitignore` が
ビルド生成物 (`*.a`、`config.h`) を無視し、CCBench の FetchContent はそれらを再生成せず
リンクするため、cache を丸ごと複製すると pin 一致・clean のまま改竄済み成果物を build 入力へ
運べる。cache からの `clone --no-hardlinks --no-checkout` + detached checkout なら
ignored file は構造的に入らない。既存 destination を再利用する経路では
`ls-files --others --ignored --exclude-standard` が空であることも要求する。

**決定 (5): directory の create-only publish は `mkdir` 排他予約 + `rename` にする。**
実測で、共有 FS では `renameat2(RENAME_NOREPLACE)` が directory に対して `EINVAL` を返す。
`/home` だけでなく **`/work` でも同じ**である。`os.link` は directory に `EPERM` なので
既存の link+unlink fallback も使えない。`os.mkdir` は `EEXIST` で排他が効き、空 directory への
`rename` は成功するので、この 2 段で race-free な create-only が成立する。予約後に失敗したときは
**自分が作った空の予約 inode である場合に限り**片付ける。

**決定 (6): Git 子プロセスは hardened 環境で起動し、cache の `.git/config` は起動前に text で検査する。**
`core.fsmonitor` / `core.sshCommand` / filter / `include` は git 実行時に任意 command を起こす。
system/global config を無効化し protocol を操作ごとに固定したうえで、危険 key を含む config は
git を起動する前に拒否する。継続行と旧式 dotted subsection は自作解釈せず全面拒否する
(Git の解釈と食い違うと拒否をすり抜けるため)。

**却下した選択肢:**
- cache root の既定を policy から導出する — 上記のとおり管理形態が違い、別 host では成立しない。
- 検証ロジックを新規実装する — 凍結 driver の `third_party_policy` /
  `third_party_source_contract` が同じ検査を持つ。二重化は drift を生む。
- consumer へ cache root を渡す — cache は ignored ビルド生成物を持ちうるため、
  `cp -a` する consumer に渡すと決定 (4) の防壁を迂回する。渡してよいのは hydrate の出力だけ。
- 取得を強制する経路を作る — 凍結 submitter の書き換えが要り、本裁定の射程外である。
