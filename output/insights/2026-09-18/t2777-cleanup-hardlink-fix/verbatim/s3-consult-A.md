## 検査範囲と結論

指定資料はすべて読めた。静的検査のみで、pytest・撤去・Git clone は未実測。race・recovery・変異の帰属判定はレンズ B に委ねる。

**must-fix は1件。plan の述語は「object store 配下」と「パスの途中に `objects` がある」を混同し、registry file の hardlink を受理する。** 親 brief P1 の誤りを plan が継承している。

以下、`brief` は `s1-brief.md`、`plan` は `codex/s2-plan.md`、`tool` は `tools/dev_wave_cleanup.py`、`test` は `orchestrator/tests/test_dev_wave_cleanup.py` を指す。rc は他の前提条件が成立した場合の静的予測である。

## A1 — object store の境界を識別できない述語

**自己判定: real／must-fix。**

`plan:18–20` の述語は、次のすべてを True にする。

| admin 相対パス | 評価 |
|---|---|
| `modules/objects/config` | submodule 名が `objects` なら registry file。誤受理 |
| `modules/group/objects/HEAD` | submodule 名が `group/objects` なら registry file。誤受理 |
| `modules/sub/refs/objects/topic` | `objects/topic` という ref の file。object store 外なのに誤受理 |
| `modules/sub/logs/refs/objects/topic` | 同様に reflog。誤受理 |
| `modules/sub/objects/info/alternates` | 実際の object store 配下なら今回の path 境界内 |
| `modules/sub/objects/pack/p.keep` | 実際の object store 配下なら今回の path 境界内 |

前半4件は、`brief:9` の非 object `config`／`HEAD`／`refs`／`logs` に対する nlink==1 要求と衝突する。特に refs の例は、submodule 名の解釈に依存しない。

現行 snapshot はディレクトリ名の意味を検証せず再帰し、regular file を読むため、この形を fixture に置けば変更対象の読取へ到達する（`tool:789–800`）。plan の削除側も同じ誤分類を使う（`plan:74–78`）。`modules/sub/config` だけの負例ではこの穴を検出できない（`plan:165–193`）。

`parts[2:-1]` への変更だけでは解消しない。複数 component の submodule 名や `refs/objects/topic` が残る。必要なのは、実際の submodule gitdir の直下にある `objects` と、その子孫を分類することであり、任意の中間 component の一致ではない。

**段9への影響:** 該当 registry file が nlink>1 の対象では、現行の preflight rc=20 が撤去継続・条件成立時 rc=0 に変わる。自 wave 内の registry entry が消える。他 worktree の alias の bytes は残るが、規律2の拒否境界には違反する。

## A2 — unlink の効果とその他の拒否境界

**自己判定: refuted — object hardlink の unlink が外部 alias の bytes まで消す、という懸念。**

`tool:973` は `os.unlink(name, dir_fd=fd)` で、当該ディレクトリエントリを除去する。別名の hardlink が残れば inode と bytes は残る。外部 alias の nlink と ctime は変化するため、「他 worktree に一切影響しない」ではなく「外部 alias と bytes を削除しない」が正確。plan の bytes と nlink=1 の確認はこの主張に対応している（`plan:108,163`）。

FD は束縛した admin から子ディレクトリへ辿り、最後も `admin.name` を registry FD から除去する構造である（`tool:814–821,963–973,1027–1030`）。提示 diff は対象選択を変更しておらず、D2119 項8の他 admin を削除しない境界は維持する。

**段9への影響:** 正当な共有 object による rc=20 を解消しても、admin 撤去範囲は自 wave のまま。外部 alias の bytes は保持される。未実測。

**自己判定: refuted — semantic、symlink、特殊 file、marker 拒否の迂回。**

- semantic 集合は root 相対の4つの完全一致であり、`modules/` 始まりの分類とは交差しない（`tool:798–800`、`plan:58–59`）。
- marker 判定は読取より前にあり、述語追加では迂回しない（`tool:782–788`）。
- snapshot の特殊 file 拒否と読取の `O_NOFOLLOW`／regular 判定は残る（`tool:753,797–803`、`plan:32–38`）。
- `.keep` は既存 marker ではない。真の object store 配下の `.keep` や `info/*` を拡張子で除外する要件は、今回の「配下の regular file」という境界にはない。

**段9への影響:** これらの拒否による停止は維持され、撤去範囲や他 worktree の bytes への影響は増えない。DW-O28 の禁止コマンドを追加する差分もない。未実測。

## A3 — 負例の到達性と nlink==0

**自己判定: refuted — 負例 A の直接 assertion が marker で先に落ちる懸念。**

`_make_repo` は `locked=False` が既定で、True の場合だけ lock を作る（`test:57–61,85–86`）。plan の既定 fixture なら `locked` による先行拒否はない。

CLI の A は resolver の `_read_admin_file(fd, "gitdir")` で拒否され、変更述語へ到達しないという plan の指摘は正しい（`tool:631,1183–1185`）。追加する直接 assertion は resolver を経由せず、snapshot の regular file 読取で述語を通る（`plan:184–190`、`tool:797–800`）。

**段9への影響:** root `gitdir` の hardlink は変更後も CLI rc=20 で止まり、撤去されない。直接 assertion はその CLI 結果だけでは見えない snapshot の拒否境界を検証する。未実測。

**自己判定: refuted — 負例 B が変更述語へ届かない懸念。**

B は root `gitdir` を変更しないため、この hardlink を理由に resolver が拒否することはない。`_bind_admin` の snapshot は `modules/sub/config` まで再帰する（`tool:830,795,798`）。ただし、B が守るのはこの単純な名前の場合だけで、A1 の反例は守れない。

**段9への影響:** 通常の `modules/sub/config` hardlink は引き続き preflight rc=20、無撤去となる設計。未実測。

**自己判定: refuted — 初回 nlink==0 を追加受理する懸念。**

`plan:35–38` は初回 `fstat` が nlink==0 なら `allow_shared_object=True` でも拒否する。現行 `tool:755–757` と同じである。名前から open した後、初回 `fstat` 前に最後の link が外されれば、この状態は到達可能である。未実測。

ただし「読取中の全時点で nlink==0 を明示的に拒否する」とまでは言えない。後続 stat は `stable()` と名前の照合で扱われる（`tool:764–765`）。そこはレンズ B の対象。

**段9への影響:** 初回 nlink==0 に関して受理集合は変わらず、preflight なら拒否、mutation 中なら partial failure の経路となる。撤去範囲は広がらない。

## A4 — 狭すぎる可能性、fixture、親 brief の一般化

**自己判定: real／nit — 全実環境の hardlink 分布を確定できない。**

F1026:16–19 は local clone による object 共有を根本原因としているが、射影資料には Git の実装・仕様の逐語がない。「Git local clone が hardlink するのは objects 配下だけ」と全条件について断定することは不確実であり、未実測。

`packed-refs`、`index`、`logs/**`、`info/exclude`、`description`、sample script に hardlink があれば、object store 外として拒否を維持すべきである。今回の資料から、通常の初期化だけでそれらが共有される到達性は確認できない。この不確実性を理由に許容範囲を広げてはならない。

**段9への影響:** 実際に object store 外の hardlink があれば rc=20 は残るが、規律2が要求する拒否である。本 wave にその条件があるとは示せないため、must-fix にはしない。

**自己判定: refuted — synthetic fixture では要求正例が成立しない、という懸念。**

対象処理は object の Git 形式を解釈せず、regular file、inode、bytes と階層を扱う（`tool:752–805,956–974`）。実 hardlink と外部 alias を使う正例は、限定した「hardlink 入り admin dir の撤去成功と alias 保持」を検証できる（`plan:123–163`）。

ただし `.idx`／`.rev`、入れ子 submodule、名前に `objects` を含む非 object 境界は現 fixture の被覆外である。拡張子差は現述語に分岐を作らないため、それだけで must-fix ではない。A1 の修正時には、**同じ fixture 内に真の入れ子 object 正例と紛らわしい非 object 負例を含める**ことが有効である。

段9の1回の live 成功が埋めるのは、その時点の本 wave の実際の構成と共有状態の差である。将来の全構成や、nlink==1 だった入れ子 object の共有時の挙動、誤受理しない境界までは証明しない（`brief:10,17`、`plan:357`）。

**段9への影響:** synthetic 正例が緑でも live rc=0 は未確定。A1 の誤受理も live 成功だけでは検出できない。

**自己判定: real／nit — brief の観測と一般化の混在。ただし plan は大部分を訂正済み。**

`brief:10` の115 regular／31 shared、入れ子 nlink==1、registry 全件 nlink==1 は、本 wave の観測として読む限り矛盾しない。全 admin の性質へ一般化する根拠にはならない。F1026:5–8 の複数 admin の走査も各 admin の最初の hardlink で打ち切っており、他の file 分布を証明しない。

「全数 rc=20」「直近11 wave 連続」（`brief:5`）は、過去 rc 未確認という F1026:20–21 と整合する形へ限定する必要がある。plan:375–376 は既にこれを指摘しており、継承していない。入れ子の nlink==1 も一般的保証にしない旨を補えばよい。

**段9への影響:** 表現訂正そのものでは rc・撤去範囲・他 worktree への影響は変わらない。実装に影響する継承誤りは A1 の分類である。

## 総括

**(a) must-fix（real）**

- **A1:** `brief:11` → `plan:18–20,381` の「任意の中間 `objects`」判定は、非 object registry file を追加受理する。`modules/sub/refs/objects/topic` 等で規律2を破る。

**(b) refuted と理由**

- 外部 alias の bytes まで消える：`tool:973` は当該名前の unlink。
- semantic／symlink／特殊 file／marker が迂回される：完全一致集合と既存の先行拒否を維持。
- 負例 A の直接 assertion が locked で先に落ちる：fixture は既定 unlocked。
- 負例 B が述語へ届かない：binding snapshot が modules を再帰する。
- 初回 nlink==0 を許容する：提示 diff は引き続き拒否。
- synthetic 正例が無意味：実 hardlink と unlink の要求挙動は検証できる。ただし被覆範囲は限定される。

**(c) 裁定パッケージ候補**

現時点ではなし。object store 外の hardlink を将来許容する要望が出れば別裁定が必要だが、今回その必要性は示されていない。T-2778 は対象外。

**(d) plan v2 への具体的修正指示**

1. `brief:9–11`、`plan:18–25,381`：object store と任意の `objects` component を区別する分類へ改める。`parts[2:-1]` だけの修正では不十分。新しい一般検査を追加せず、今回の分類に限定する。
2. `plan:123–193`：既存 fixture に、真の入れ子 object の共有正例と `modules/sub/refs/objects/topic`、`modules/objects/config` の共有拒否例を組み込む。後者は snapshot 層でも拒否を確認する。
3. `plan:52–83`：修正した分類を snapshot と削除側で一致させる。部分撤去後の分類維持はレンズ B と整合を取る。
4. `plan:94,375–376`：入れ子 nlink==1 と registry 全件 nlink==1 も本 wave の観測に限定する。段9の1回の成功から一般的成功を主張しない。
5. `plan:184–193` の負例 A の直接 assertion は維持する。これは到達性のある検証であり、削除する理由はない。