# 段 6 裁定 — レビュー A / B の所見と親の実測

両レビューとも NO-GO。親が全所見を real/refuted に裁定し、1 回の fix にまとめる。
fix 単位を分けない理由: 所見 A10 / B4 は `LEDGER_FIELDS` (tool) と台帳文書の**両方**を同時に
変える必要があり、所見 B3 の配線検査は tool の CLI 契約に依存する。所有を素集合にできない。

## 親が現物で確認した所見 (子の申告をそのまま採らない)

- **B1**: `tools/check_branch_rescue.py:1247` と `:1309` が `branch_delete_authorized: False` を
  新 schema へ書いている。`:1296` は旧 checker の出力に対する境界検査で、これは正当。
- **B2**: `:1444-1456` の audit 完全性判定は summary・commit 行数・rc だけを見ており、
  `docs/unreachable-object-ledger.md:88` が課した `elapsed_seconds=` 終端を検査していない。
- **親の dogfood (D2)**: `locked` field で実 repo が常に rc=2。53 worktree 中 37 本が locked。
- **親の実走**: `test_check_docs.py` が **309 failed**。原因は
  `orchestrator/tests/test_check_docs.py:627` の `_SYNTHETIC_CLEANUP_COMMAND` が旧本文のまま。
  pin 閉包は 3 箇所 (親の指示漏れ)。

## 裁定表

| # | 所見 | 裁定 | 是正の方針 |
|---|---|---|---|
| A1 | 候補 branch の reflog だけが保持する commit が正側 root から落ち、閉包から消える | **real / blocker / 採用** | 下記 §1。この wave の主題そのもの |
| A2 | landed checker / audit tool の path を CLI から注入でき read-only を破れる | **real / blocker / 採用** | production CLI から path 注入を除去。子は固定 |
| A3 | partial clone で `cat-file` が lazy fetch し object DB を変える | **real / blocker / 採用** | 全 git 子孫へ `GIT_NO_LAZY_FETCH=1`。promisor 欠落は issue + rc=2 |
| A4 | global / system の実効 gc 設定を捨て既定へ倒すため期限が未来へずれる | **real / blocker / 採用** | 実効 config を全 scope で読む。読めない scope は既定へ倒さず rc=2 |
| A5 | prunable worktree の期限を admin directory の mtime から計算している | **real / blocker / 採用 (方式変更)** | 下記 §2 |
| A6 | `--now` が任意の未来時刻を受理し全 floor を偽装できる | **real / blocker / 採用** | production CLI から `--now` を除去。時刻注入は import 時の seam に限定 |
| A7 | `bare` record と C-quoted path を受理できない | **real / must-fix / 採用** | 親の `locked` 欠陥と同じ根。§3 で一括 |
| A8 | branch 名と refname の受理集合が git より狭い | **real / must-fix / 採用 (縮約)** | §4 |
| A9 | 範囲外 reflog timestamp が未定義終了になる | **real / must-fix / 採用** | `ValueError` / `OverflowError` を `reflog-parse-error` + rc=2 へ |
| A10 / B4 | 台帳の headroom が総数由来か標本由来か固定されていない | **real / must-fix / 採用** | §5 |
| A11 | m16 と不変テストが child subprocess を覆っていない | **real / must-fix / 採用** | 非空閉包 + ledger-check を通す経路で argv と repo bytes 不変を検査 |
| A12 | m03 fixture が candidate reflog を無視する変異を殺さない | **real / must-fix / 採用** | A1 の負例と同じ fixture で作る |
| A13 | m10 / m11 の共用 fixture が pack mtime 変異を独立に殺さない | **real / should-fix / 採用** | fixture を 2 つに分ける |
| A14 | 期限付き root が保持する**祖先** commit へ additional source が伝播しない | **real / 採用しない (次の一手へ)** | 下記 §6 |
| B1 | 新 schema に無条件 `false` の削除許可 field を再生成している | **real / must-fix / 採用** | `:1247` と `:1309` を削除。`:1296` の境界検査は残す |
| B2 | audit の必須終端が欠けても `--ledger-check` が rc=0 を返せる | **real / must-fix / 採用** | 終端を厳密検査し `audit-contract-invalid` + rc=2 |
| B3 | 配線テストが frontmatter と単なる言及を実行配線として受理する | **real / must-fix / 採用** | §7 |
| 親 D2 | `locked` field で実 repo が常に rc=2 | **real / blocker / 採用** | §3 |
| 親 D4 | `_SYNTHETIC_CLEANUP_COMMAND` が旧本文のまま 309 failed | **real / blocker / 採用** | §8 |

## §1. A1 — 候補 reflog は「負側に入れない」だけでは足りない

裁定 §2.3 の分類は**負側**についてだけ正しかった。`git branch -d` は
`logs/refs/heads/<branch>` も消すので、**候補 reflog だけが保持していた過去 OID は、
削除によって失われる側である**。したがって正側 (`<oid>`) へ入れなければならない。

- 候補 branch の reflog の old/new OID を parse し、commit 型のものを閉包の**正側**へ加える。
- 撤去対象 worktree の HEAD reflog も同じ扱いにする。
- reflog が読めない・parse できない場合は `rc=2`。**空として扱わない。**

## §2. A5 — prunable worktree の期限は git を再現せず fail-closed にする

git 2.34.1 の `should_prune_worktree` を忠実に再現するのは保守負債が大きい。
**prunable worktree が保持する commit の下界は assessment time とし、
`deadline_status: "indeterminate"` にする。**理由を `retention.reason` に書く。
これは過小報告 (= 早すぎる期限) 側であり安全である。
admin directory の mtime から未来の確定期限を出す現行は採らない。

## §3. A7 + 親 D2 — porcelain parser を実データの語彙へ合わせる

- 既知 field を `worktree` / `HEAD` / `branch` / `detached` / `bare` / `locked` / `prunable` とする。
- `locked` と `prunable` は理由文字列つきの行と単独の行の**両方**が実在する (親の実測)。
- `bare` record は HEAD を持たない。HEAD/index root として扱わない。
- **未知 field 1 個で repo 全体の絵を捨てない。** 当該 record を `inspection_complete=false` にし、
  `issues` へ出し、その record の root は**恒久 root 側に残す** (安全側)。
  ただし撤去対象 worktree の record が不完全なら rc=2 にする (撤去の影響を測れないため)。
- path が C-quoted の場合は git の quote 規則で復号する。復号できなければ rc=2。

## §4. A8 — 受理集合を git に合わせる

- branch 名の妥当性判定に独自 ASCII allowlist を使わない。`git check-ref-format --branch` を
  allowlist に加えて使うか、git の refname 規則をそのまま実装する。
- refname / path の非 UTF-8 byte は `surrogateescape` などの可逆表現で保持し、
  JSON へは可逆な形で出す。strict decode 失敗で rc=2 に倒す現行は、
  git が扱える repo を受理集合から落とすので採らない。

## §5. A10 / B4 — headroom の出所を schema で固定する

台帳にはまだ 1 件も entry が無いので schema 変更は自由である。

- `gc_headroom_at_loss` を**削除**し、次へ置き換える。
  `gc_auto_sample_fanout` (string、実測では `"17"`)、`gc_auto_sample_count` (integer)、
  `gc_auto_sample_threshold` (integer)、`gc_auto_heuristic_version` (string)。
- `loose_count_at_loss` は**観測値としてだけ**残し、余裕の計算に使わない。
- 検査で `sample_threshold == (gc_auto + 255) // 256` の算術を検証する。
- 台帳文書の field 表と `LEDGER_FIELDS` を同時に更新し、一致検査を通す。

## §6. A14 — 採用しない (次の一手へ送る)

期限付き root が保持する祖先 commit へ source が伝播しない件は real である。
ただし向きは「**実際より早い期限を表示する**」であり、`DW-G05` の意味で成果物の値を
危険側へ動かさない (早い期限 = より急いで見える)。閉包からの脱落は起こさない。
本 wave では実装せず、次の一手へ 1 件起票する。理由を worklog に書く。

## §7. B3 — 配線検査を本文だけに絞る

`orchestrator/tests/test_branch_rescue_ledger.py` の配線検査を次にする。

- frontmatter、code fence、HTML コメントを**除外した**可視本文だけを対象にする。
- `§1` の同一 bullet に `python3 tools/check_branch_rescue.py` と `--ledger-check` と
  「全候補を 1 回で渡す」旨が揃っていることを検査する。
- 負例を 2 つ足す。(a) frontmatter にだけ path を置いた本文 → 赤。
  (b) 本文で言及するが実行命令でない形 → 赤。
- 同じ検査を `docs/unreachable-object-ledger.md` への到達 edge にも適用する。

## §8. 親 D4 — pin 閉包は 3 箇所

`.claude/commands/cleanup-branches.md` を変えたら次の**3 つ**を同時に更新する。

1. `tools/check_docs.py` の `CLEANUP_COMMAND_SHA256`
2. `orchestrator/tests/test_check_docs.py` の `_EXPECTED_CLEANUP_COMMAND_SHA256`
3. `orchestrator/tests/test_check_docs.py:627` の `_SYNTHETIC_CLEANUP_COMMAND`
   (**command 本文の逐語コピー**。これが旧のままだと合成 fixture が全滅し 309 failed になる)

## 変異事前登録の追加 (DW-M01)

段 4 の m01〜m17 に次を足す。

| ID | 位置 | 変異 | 期待 | 単一理由性 |
|---|---|---|---|---|
| m18 | 閉包の正側 | 候補 reflog の old/new OID を正側へ入れない | KILLED | A1 の fixture (C1 が reflog にしか無い) でだけ落ちる |
| m19 | porcelain parser | 未知 field で repo 全体を rc=2 にする (現行の挙動へ戻す) | KILLED | `locked` を含む fixture でだけ落ちる |
| m20 | gc config | global / system scope を無効化して既定へ倒す | KILLED | global に `gc.pruneExpire=now` を置いた fixture |
| m21 | prunable 期限 | admin directory の mtime から確定期限を出す | KILLED | prunable worktree fixture の `deadline_status` |
| m22 | audit 完全性 | `elapsed_seconds=` 終端の検査を外す | KILLED | 終端を欠いた audit 出力の fixture |
| m23 | 配線検査 | frontmatter を除外せずに path を探す | KILLED | frontmatter にだけ path を置いた負例 |
| m24 | schema | `branch_delete_authorized` を新 schema へ再出力する | KILLED | JSON 全階層に authorization field が無いことの assert |
| m25 | lazy fetch | `GIT_NO_LAZY_FETCH=1` を外す | KILLED | promisor fixture での object DB 不変検査 |

**正例の追加:**

| ID | 内容 | 期待 |
|---|---|---|
| p05 | `locked` (理由つき・単独の両形) と `detached` を含む実形の porcelain | rc=0 |
| p06 | 候補 reflog に過去 OID があり、それが閉包に現れる | rc=0、closure に当該 commit |
