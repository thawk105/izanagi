# [T-316] R-1 (b)+(c) と [T-840] — 何を実装し、何を主張せず、何を裁定へ返すか

- 生成 wave: `worktree-dev-wave-t316-copyout-t840` (2026-08-12)
- 種別: **実装**。commit `c9ebbca3` (copy-out + issuer 閉包 + docstring)、
  `a469863d` (変異検査が摘出したテストの非決定性と等価変異の修正)
- 上流: ユーザー裁定 `rulings-inbox/2026-08-12-coarse-provenance-45rulings.md` 34–35 行、
  裁定パッケージ `2026-08-09_t316-semantic-gate/package.md` (R3-6)、
  実装段 `2026-08-11_t316-semantic-gate-impl/package.md` (R-1 / R-2)

---

## 0. この文書が答える問い

ユーザーは [T-316] R-1 を **(b) build 出力 copy-out の厳格化 + (c) 本 wave の lexical 効果 gate を
defense-in-depth として併置**、(a) source の DSL/IR 化は不採用と裁定し、[T-840] (機械隔離) を
同 wave 同梱とした。本 wave は (b) と (c) を実装した。**[T-840] は裁定どおりには実装できず、
実装できる部分だけに縮めて、残りを新事実つきで再裁定へ返す。** その線引きが本文書の主目的である。

---

## 1. 実装したもの

### 1.1 (b) build 出力 copy-out の厳格化

`orchestrator/campaign/buildcache.py` の v2 / legacy の publish 経路 2 本を書き換えた。

**wave 前:** staging binary を `os.path.isfile` / `os.path.exists` (どちらも symlink を追う) で
検査し、`os.rename(staging, bdir)` で **staging directory を丸ごと** publish していた。
symlink 拒否も許可ファイルの絞り込みも無い。

**wave 後:**

- 中間 component を保持した dir-fd から `O_NOFOLLOW|O_DIRECTORY` で辿り、
  pre-stat と fstat の dev / inode / type 一致を要求する。
- leaf は `O_NONBLOCK|O_NOFOLLOW` で開き、`S_ISREG` / `st_nlink == 1` /
  setuid・setgid・sticky 不在を要求する。
- **nm / sha256 / fsync / publish をすべて同一 destination fd に対して行う。**
  検査したものと publish したものが分かれる窓を作らない。
- metadata (`completion.json` / `admission.json`) は untrusted staging からコピーせず host が生成する。
- 環境の POSIX capability を起動時に fail-closed で検査する。
- cache hit 側の manifest / sidecar / binary 読みも no-follow 化する。
- publish する binary の mode は `0o500`。
- gate failure では staging と clean candidate の双方を破棄し、v2 は claim だけ残す。

### 1.2 (c) lexical 効果 gate の併置

既 land の `coder_effect_gate` は実装を変えず、docstring に build **前**の source 側防壁と
build **後**の output 側防壁の関係、およびどちらも host-security boundary ではないことを書いた。

### 1.3 [T-840] のうち実装した部分 — issuer 集合の機械閉包

- 単一 registry を site kind (`DIRECT_MATERIALIZER` / `CODER_ENTRYPOINT`) で型付き拡張した。
  **第 2 registry を作っていない。** 既存 projection と診断 dict の schema は不変。
- **未登録 site からの coder authority 発行を、token 生成前に fail-closed で拒否する。**
  現存する 6 entry point はすべて登録済みなので、**受理集合は 1 件も縮まない**。
- 補助の AST 閉包は tracked Python 全体 (474 file / 約 16 MB / 実測 10.4 秒) を母集合とし、
  除外を `(path, function, helper, count)` の exact allowlist (11 件) にした。
  low-level helper binding の非 `Call.func` load を taint として拒否する。

---

## 2. 意図的に主張しないこと

- **これは host-security boundary ではない。** 任意の C++ が起こす効果に対して閉じていない。
- **certified の安全性を主張しない。**
- **実行時の binary identity を保証しない。** publish 後に pathname で開き直して実行する経路は残る
  (R3-4 / [T-841] の領分)。本 wave の主張は **cache publish 時点の inode 厳格化に限定**する。
- **staging tree 全体が fd で anchor されているとは主張しない。** build subprocess には
  cmake `-B` で pathname を渡さざるを得ない。
- **directory publish の create-only 原子性を主張しない。** Python 3.10 stdlib に
  `renameat2(RENAME_NOREPLACE)` が無い。
- **成果物の隔離が完成したとは主張しない。** §3 のとおり。
- **Python issuer を完全に閉じたとは主張しない。** 閉じたのは静的に追跡できる範囲だけである。

### 残余 (docstring に逐語列挙済み)

完全動的な文字列、`eval` / `exec`、外部注入、monkeypatch された import / builtins、
同一 process からの private / low-level factory 直接呼び出し、shell materializer、
任意 binary path、`output/**` の runnable script、旧実装が作った extra member を含む既存 cache entry、
下流 artifact admission。

---

## 3. [T-840] を分割した理由 — 裁定の前提を覆す新事実

裁定は [T-840] (機械隔離) と [T-841] (receipt 束縛、R3-3 / R3-9 後) を**別項に分離**した。
しかし段 3 の敵対レンズ 2 本が独立に指摘し、親が実コードで裏取りしたところ、
**この 2 つは成果物のレベルでは分離できない。**

- `artifact_admission` は trigger-machine campaign の binding 特例を除き、構造的に妥当な
  post-policy campaign を一律 `admission_status="admitted"` で返す。coder 由来かどうかも、
  quarantine を通ったかどうかも読まない。
- layer3 はその `admitted` だけを certifying input の条件にしている。

したがって「生成物を非認証として隔離する」を成立させるには分類を下流が消費する必要があり、
それが [T-841] の receipt 束縛そのものである。**registry に分類を書くだけでは恒真ラベルになる。**

この依存関係は 2026-08-11 の裁定パッケージ R-2 に書かれていない (R-2 は「機械隔離するか、
残余のまま台帳に明示するか」の二択として提示している)。よって親は不採用にせず、再裁定へ返す。

---

## 4. ユーザーへ返す裁定

| # | 問い | 親の推奨 |
|---|---|---|
| **Q1** | red / kickoff を**廃止**するか、**実行可能だが認証されない lane** として残すか | **後者。** 起動前 deny は既存の診断 WAL / campaign を消し、既存の正例テストを壊す。本 wave では実装していない |
| **Q2** | 分類を `artifact_admission` / layer3 / WAL / COMMIT へ束縛して**真の成果物隔離**にするか | **[T-841] と同時に裁定する。** 本 wave へ密輸しない |
| **Q3** | calibrator の任意 binary path と shell materializer の扱い | **本 wave 対象外と明記済み。** 別系列の認証済み成果物 intake であり Python inventory の外 |
| **Q4** | 旧実装が作った既存 cache entry (extra member を含む) を拒否・再発行するか | **しない。** 正しさの穴ではなく費用の問題で、強制すると全件無効化になる (規律 4) |
| **Q5** | fd-to-exec 束縛、build 子孫の終了保証、floor / oracle の store / resume 束縛 | **R3-4 / host-security 系の別裁定へ** |

---

## 5. 検査の信頼性

### 5.1 敵対検証 5 本がすべて NO-GO

段 3 の敵対レンズ 2 本、段 6 の敵対レビュー 2 本、焦点再レビュー 1 本。
blocker 2 件 (close 失敗時の fd ownership transfer 漏れ、registry が下流へ接続されない) と
must-fix 11 件を **2 巡の fix** で閉じた。

**焦点再レビューは指摘を書くだけでなく、audit helper へ synthetic source を実投入した。**
tuple / dict 格納、関数引数渡し、`globals()` 経由、変数へ束ねた動的解決の 4 経路が
`calls=[] / dynamic=[]` で素通りすることを実データで示した。これが無ければ
「別名は追跡済み」で終わっていた。fix 2 巡目で 6 パターンすべてを閉じ、閉じきれない範囲は
docstring で主張を縮めた。

### 5.2 親の 2 つの推定が外れた

- **`DW-O09` 判定の根拠が不十分だった。** 親は `FROZEN_MANIFEST` だけを見て「source pin なし」と
  結論したが、レンズ A が `t080_freeze_migration` による `p3_s4_loop_sort.py` の source SHA pin を
  発見した。照合は固定 commit の blob に対して行われ working tree を読まないため**結論は維持**したが、
  論証が閉包検査になっていなかった。
- **フレークの真因推定が外れた。** 親は `next(rglob(...))` の非決定性と推定したが、実際は
  rename が held inode の `ctime` を更新し `_stable_file_identity()` の `ctime_ns` 比較で
  拒否理由が 2 分岐していた。fix worker が変異ログに両方の結果が残っていることから特定した。

### 5.3 変異検査が、静的レビュー 5 本が見つけられなかった 2 件を摘出した

- **フレークによる帰属汚染** (`{{F:flaky-anchor-contaminates-mutation-attribution}}`)。
  無関係な変異の失敗集合へ紛れ込み、「その変異が防壁を殺した」と誤記させかけた。
  並列走行でしか出ないため静的レビューでは原理的に見えない。
- **等価変異を「殺せない変異」と読み違えていた**
  (`{{F:equivalent-mutation-recorded-as-unkillable}}`)。注入は実在したが意味が変わっていなかった。

### 5.4 単独で殺せない検査は冗長 gate として証拠から外した

通常ファイル検査 (`stat.S_ISREG`) を単独無効化しても 1 件も赤にならなかった。
FIFO はコピー処理の `os.lseek` が ESPIPE を、directory は `os.read` が EISDIR を先に出して拒否する。
**M2 を `SURVIVED` 期待で登録して単独変異の証拠から外し、実効層を含む両層同時変異 (M2b) で
防壁の存在を裏付けた。** 「変異を殺せたから防壁が効いている」と書かないための処置である。

### 5.5 実測 (すべて Pegasus 計算ノード、`--force-dispatch`)

- 焦点走 (最終 tip `a469863d`): **323 passed / 0 failed**。
- 変異本走: **KILLED 8 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0**、
  **9 件すべて期待と一致** (`matching: 9`)。baseline は `PASSED` (失敗 node ゼロ)。
- フレーク切り分け: 該当 node の単独走行 3 回連続で `2 passed` / rc=0。

**codex 子は全段で pytest を実走できなかった** (`qstat -Q preflight rc=1` / runner `rc=16`)。
5 本の子はいずれも「実装済み・**未実走**」と申告し、緑を騙らなかった。実測はすべて親が行った。

---

**実装段の残り blocker ([T-184] canonical stage matrix 未発行、R3-3〜R3-9、R2-b 独立 oracle 本体)
は変わらず。** 本 wave はそれらを閉じていないし、閉じたとも主張しない。
