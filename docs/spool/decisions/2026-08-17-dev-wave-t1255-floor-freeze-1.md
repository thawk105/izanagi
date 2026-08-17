---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1255-floor-freeze
seq: 1
---

## {{D:floor-protocol-committed-authority}}. 床値 protocol index の versioned record を committed-only にする

**決定:** 床値 protocol の versioned record は、**固定 commit の exact 100644 blob として存在し、
その bytes が作業ツリーと完全一致する**ときだけ index に入る。未 commit、dirty、
commit 済み entry の削除、mode 違いはすべて fail-closed で拒否する。
issuer の post-write 自己検査だけを full index scan から分離し、
read-back・strict parse・導出 path・継承・canonical bytes・repository 内 destination の検査は維持する。

**理由:**

- D444 決定 4 は lineage anchor を「固定 HEAD commit の exact 100644 blob から読む」と定めたが、
  実装はその要求を **legacy anchor にしか適用していなかった**。versioned entry は
  `iterdir()` と `read_bytes()` だけで index に入っていた。
- 解決先を versioned record へ移した瞬間、凍結成果物の権威が **Git の commit から作業ツリーへ後退する**。
  同一 UID が canonical な名前で file を 1 件置けば、それが current protocol として選ばれる状態になる。
  これは受理集合の拡大であり、規律 2 に触れる。
- したがって、解決規則の改訂 ({{D:floor-protocol-head-pin-disambiguation}}) と**同じ wave で**
  塞がなければならない。片方だけを入れることはできない。

**却下した選択肢:**

- **versioned entry も working tree から読み、consumer 側で bytes を再照合する** — 走査と再読の間の
  差し替えを束縛しない。証拠の由来は Git に置くべきで、consumer の照合で代替しない。
- **issuer の post-write 検査にも committed-only を課す** — issuer は書いた直後の未 commit artifact を
  検査する。同じ経路を使うと発行そのものが構造的に不可能になる。
- **untracked entry を無視して走査を続ける** — 失敗した発行の残骸が黙って見過ごされる。
  D444 決定 7 の「取り除くまで発行できない」と整合しない。

## {{D:floor-protocol-head-pin-disambiguation}}. 現行契約候補の中でだけ HEAD の ccbench pin で曖昧性を解く

**決定:** `resolve_current_floor_protocol` は固定 HEAD commit OID を厳密に 1 回だけ解決し、
その OID を index 走査と gitlink 読取の双方へ渡す。現行 env 契約に一致する候補集合 `C` を作り、

- `len(C) == 0` なら fail-closed、
- `len(C) == 1` なら **gitlink を読まずに**その record を返し、
- `len(C) >= 2` のときだけ HEAD の `external/ccbench` gitlink を読んで
  `C` の部分集合 `E = {r ∈ C | r.ccbench_pin == head_gitlink}` を構成し、
  `len(E) == 1` ならその record、それ以外は `current_count` と `head_exact_count` を添えて fail-closed。

辞書順・mtime・最大 pin・namespace 優先といった別の曖昧性解消規則は入れない。
公開 API の引数は repository root だけのまま据え置く。
解決した record は index 化に使った固定 commit OID を保持し、consumer はその OID の blob を読む。

**D460 の「選択条件に ccbench pin を入れてはならない」を、この範囲で撤回する。**
D460 が残した caller 非選択・現行契約一致の必須性・zero match と曖昧な複数 match の fail-closed・
再読 bytes の sha 照合は維持する。

**理由:**

- D460 の禁止は理由節で「pin を条件に入れると今日 0 件になり、床値の受理経路が壊れる」という実測を
  根拠にしていた。`len(C) == 1` で gitlink を読まない節がその状態を保つため、**禁止が守ろうとした害は
  発生しない**。理由が指す害が消えた以上、禁止だけを狭く撤回する。
- D471 は resolver 不変更を記したが、却下理由として (ii) 実 driver が固定 legacy path を渡すための
  authority 分裂、(iii) 配線と実発行が別タスクの所有であることを挙げていた。
  **同じ wave が配線と実発行の両方を持てば (ii) と (iii) は消える。** D471 は禁止ではなく先送りだった。
- 発行後は現行契約に一致する record が 2 件になる。曖昧性を解かなければ床値 admission が止まり、
  pilot result・材料レポート・試行台帳が新規生成されなくなる。
- `E` を index 全体からでなく `C` の部分集合として作るのは、stale な契約の record が
  pin 一致だけで選ばれる順序逆転を構造的に排除するためである。
- gitlink 読取を `len(C) >= 2` まで遅延させるのは、submodule を持たない repository で
  候補が一意でも解決が落ちる回帰を避けるためである。候補が 1 件なら pin を見ても結果は同じ record に
  なるので、読む必要がない。**変更前の挙動と厳密に同値である。**

**却下した選択肢:**

- **legacy anchor を解決候補から常に外す** — pin を選択条件に入れずに済むが、発行前は候補 0 件になり、
  部分着地・rollback・別 worktree・legacy 専用 fixture で受理集合が空になる。
  次回 pin 前進時に同一契約の versioned が 2 件並ぶ問題も先送りされるだけである。
- **explicit current pointer artifact を新設する** — 第二 artifact、更新手順、chain record、
  障害復旧、履歴検査が必要になる。粗い provenance で足りるという既定方針と衝突する。
- **resolver を変えずに発行だけ行う** — 発行した瞬間に床値 admission が fail-closed する。

## {{D:floor-protocol-supplied-authority-precheck}}. 供給 protocol の権威不一致を最初の副作用より前に拒否する

**決定:** `run_campaign` は、供給された protocol が resolver の返す record と一致することを、
**いかなる副作用よりも前**に検査する。不一致は供給 path と resolver が選んだ path の両方を添えて拒否する。
holdout reservation 側の既存検査は最後の防壁として残す。

**理由:**

- versioned protocol を発行すると、退いた legacy protocol を直接 CLI へ渡した場合の受理は
  正しく拒否へ変わる。しかし変更前の拒否点は holdout reservation であり、
  **build・run directory 作成・binary store・manifest 発行がすべて済んだ後**だった。
  部分成果物だけが残り、pilot result と試行台帳は生成されない。
- 拒否を早めることは受理集合を変えない。同じ入力が同じ判定で拒否され、副作用が減るだけである。

**却下した選択肢:**

- **holdout reservation の拒否だけに任せる** — 上記の部分成果物が残る。
- **driver CLI から `--protocol` 引数を削る** — 公開 CLI 契約の変更であり、本 wave の scope を超える。
  早期拒否はその判断を待たずに実害を消せる。
