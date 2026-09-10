## 抜けの所見

| # | 判定 (real/refuted) | 経路 | file:line | 具体的な入力 | 影響 |
|---|---|---|---|---|---|
| 1 | real | authority root の**祖先**を削除・移動する操作。計画の判定は `candidate inside authority_root` の一方向だけで、祖先との重なりを見ない。fast path に authority literal も現れない | `s2-plan.md:43-48`; `guard_bash.py:2366-2406`; `guard_bash.py:2523-2529` | `rm -rf /work/1/SFC/tanab` | authority root 全体を消せる。破壊系では `_inside(root, candidate)` 側も必要 |
| 2 | real | authority の親 directory を destination にし、archive/copy/rsync の内容から authority component を生成する経路。archive member/source basename は hook から見えない | `guard_bash.py:2475-2485`; `s2-plan.md:15-19` | `tar -xf /tmp/payload.tar -C /work/1/SFC/tanab`（archive 内に `dev-wave-authority/key`）／`cp -a /tmp/dev-wave-authority /work/1/SFC/tanab/` | fixed root を一度も argv に書かず、既存鍵を上書きできる |
| 3 | real | root component の一部を glob にした形。authority 判定に既存 `_glob_prefix()` 相当の重なり判定を使う計画がない | `guard_bash.py:2212-2214`; `guard_bash.py:2393-2395`; `s2-plan.md:43-48` | `rm -rf /work/1/SFC/tanab/dev-wave-authorit?` | shell 展開後は exact root だが、hook 時点では literal regex・`_inside()`・fast trigger のすべてを外れる |
| 4 | real | Bash の ANSI-C quote / locale quote。`shlex` は通常 quote と異なり `$'...'` の `$` を残す。raw にも完成後の root literal がない | `guard_bash.py:1290-1306`; `guard_bash.py:2413-2425`; `s2-plan.md:21-23` | `printf x > /work/1/SFC/tanab/dev-wave-$'authority'/key` | Bash は exact authority path に展開するが、計画した fast path と canonical 判定は到達・一致しない |
| 5 | real | cwd を変更する `pushd` を状態遷移として扱わない。`pushd` 自体は pure reader 扱い | `guard_bash.py:131-143`; `guard_bash.py:2552-2563`; `s2-plan.md:24-25` | `pushd /work/1/SFC/tanab/dev-wave-authority >/dev/null && rm -f acceptance-issuer-public-key.pem` | 最終 `rm` は authority 内で実行されるが、計画の `authority_cwd` は repo cwd のままで許可する |
| 6 | real | `&&`、`||`、subshell の実行・スコープを捨て、単一 cwd を全 segment に直列適用する | `guard_bash.py:119-122`; `guard_bash.py:1309-1321`; `guard_bash.py:2552-2563`; `s2-plan.md:21-24` | `cd /work/1/SFC/tanab/dev-wave-authority && (cd /tmp); rm -f acceptance-issuer-public-key.pem` | 実 shell の外側 cwd は authority のままだが、hook は `/tmp` に更新して最終削除を見逃す |
| 7 | real | cwd を変更する wrapper option を追わない。`env --chdir` は既存 wrapper metadata に存在するが path guard の状態には反映されない | `guard_bash.py:378-380`; `guard_bash.py:1324-1344`; `s2-plan.md:24` | `env --chdir=/work/1/SFC/tanab rm -rf dev-wave-authority` | fixed root literalなしで root を削除でき、fast path で許可される |
| 8 | real | hardlink alias。lexical/realpath は inode identity を変えない alias を検出できない。計画は明示的に inode index を除外 | `guard_write.py:75-130`; `guard_write.py:155-171`; `guard_bash.py:2246-2323`; `s1-brief.md:67-69`; `s2-plan.md:69` | 既存 `/tmp/key-alias` が private key の hardlink のとき、`Write(file_path=/tmp/key-alias)` または `printf x > /tmp/key-alias` | authority 内の鍵 inode を直接変更できる。0700 は同一 uid に対する根拠にならない |
| 9 | real | `perf` の密着短 option 値が仕様・テスト matrix にない。現行専用分岐は `-o FILE` と `--output=FILE` だけを認識し、`--` 後に args を差し替える | `guard_bash.py:2564-2582`; `s2-plan.md:26`; `s2-plan.md:163-165` | `perf stat -o/work/1/SFC/tanab/dev-wave-authority/perf.data -- true` | 有効な `-oFILE` 綴りを専用分岐が落とす。段6変異にもこの綴りがない |
| 10 | real | 内部例外 fallback は exact authority literal しか見ないため、canonical alias/hardlink alias は fail-open | `guard_write.py:378-400`; `guard_bash.py:2633-2649`; `s2-plan.md:12`; `s2-plan.md:29` | `/tmp/authority-alias -> authority` が存在し、`Write /tmp/authority-alias/key` の判定中に例外が発生 | 正常系では canonical 判定できても、まさに fallback が必要な状態では rc=0 になる |
| 11 | real（既知の scope 外） | script、変数展開、persistent shell、別 process、MCP/apps/plugins/子エージェント | `hooks-readme-protection-boundary.md:10-14`; `s2-plan.md:210-215` | `bash /tmp/writer.sh`（script 内で authority を更新） | 本 wave の hook 防壁だけでは「AI が書けない領域」を成立させない |
| 12 | refuted | 通常の external symlink alias 経由の直接書込み | `guard_write.py:230-240`; `guard_bash.py:2305-2323`; `s2-plan.md:45-48` | `/tmp/a -> /work/1/SFC/tanab/dev-wave-authority` として `printf x > /tmp/a/key` | 実行時に存在する alias なら canonical 側で捕捉できる |
| 13 | refuted | 単純な `cd parent && relative-path` | `s2-plan.md:21-25`; `guard_bash.py:2552-2563` | `cd /work/1/SFC/tanab && rm dev-wave-authority/key` | 分岐や別 cwd-changing primitive がなければ、計画した absolute cwd 状態で捕捉できる |
| 14 | refuted | 一般の `=` 値・短 option 密着値 | `guard_bash.py:2413-2419`; `s2-plan.md:18` | `dd of=/work/1/SFC/tanab/dev-wave-authority/key`／`sort -o/work/1/SFC/tanab/dev-wave-authority/key` | `_argument_hits_authority()` を既存全 call siteへ確実に伝播すれば捕捉できる。`perf` は専用 early branch のため #9 と別 |

## 巻き込みの所見

| # | 判定 (real/refuted) | 巻き込まれる path | file:line | 影響 |
|---|---|---|---|---|
| 1 | real | authority を**入力元として読むだけ**の `cp`、`rsync`、archive backup | `guard_bash.py:2152-2202`; `guard_bash.py:2597-2620`; `s2-plan.md:28` | `cp authority/public-key /tmp/public.pem` は authority hit + unknown writer で拒否される。`cat authority/public-key > /tmp/public.pem` は通るため、読取り防護にもならない不整合な偽陽性 |
| 2 | real | authority を指す external symlink entry 自身の削除・移動 | `guard_write.py:310-325`; `guard_bash.py:2305-2323`; `s2-plan.md:58` | `rm /tmp/authority-alias` は authority を変更せず外側の symlink だけを unlink するが、final component の realpath 解決により拒否される |
| 3 | real | 実行されない `cd` の後続 relative path | `guard_bash.py:1309-1321`; `guard_bash.py:2552-2563`; `s2-plan.md:21-24` | `false && cd <authority>; rm -f docs/safe.md` は実際には repo の `docs/safe.md` を消すが、直列 tracker は authority 配下と誤認して拒否する |
| 4 | real | authority path をデータとして表示するだけの opaque command | `guard_bash.py:2531-2542`; `s2-plan.md:109` | `printf '%s\n' '<authority>' \"$(date)\" > /tmp/note` が拒否される。authority への書込みはない |
| 5 | refuted | `/work/1/SFC/tanab/dev-wave-authority-copy/*`、`dev-wave-authority2/*` | `guard_write.py:71-72`; `guard_bash.py:2242-2243`; `s2-plan.md:50-56` | `_inside()` の component boundary と exact literal regex を計画どおり実装すれば巻き込まれない |
| 6 | refuted | `/work/1/SFC/tanab/other/*` | `s2-plan.md:43-56` | 同じ親 directory というだけでは固定 root の内側にならない |
| 7 | refuted | job dir・worktree の `...authority-guard` | `s2-plan.md:50-67` | fixed absolute root component と一致せず、canonical path も authority 外なので通常判定では拒否されない |

## 親 brief への所見

- **(P1-a) は支持。** 固定 absolute module constant は、repo root・argv・環境変数から authority を差し替えさせない点で妥当である（`s1-brief.md:65-66`; `s2-plan.md:9,97`）。

- **(P1-b) は反証。** lexical/canonical の二面は妥当だが、inode index を張らない根拠は弱い。hooks subtree が inode index を持つのは、path alias ではなく「同じ regular-file inode への別名書込み」を塞ぐためである（`guard_write.py:75-130`; `guard_bash.py:2246-2303`）。0700 は同一 uid を隔離せず、D1478 は配置を防護追加より先に要求するため、activation 前 alias の存在可能性も構造上ゼロにできない（`d1478-key-ceremony-order.md:3-13`）。

- **(P1-c) は反証。** `_hooks_tree_violation()` の実 call site は三つだが、それだけでは `perf`、fast path、例外 fallback、builder 例外を通らない。段2の反証はコードと一致する（`guard_bash.py:2396`; `guard_bash.py:2423`; `guard_bash.py:2501`; `s2-plan.md:37-39`）。さらに本レビューの ancestor、glob、cwd primitive/control-flow が残る。

- **(P1-d) は反証。** 四変異では不足し、段2が増やした変異集合にも ancestor overlap、archive-to-parent、partial glob、ANSI-C quote、`pushd`、conditional/subshell、`env --chdir`、hardlink、`perf -oFILE`、directional read の各独立 detector がない（`s1-brief.md:72`; `s2-plan.md:122,155-165`）。

- **N1/D374 の適用可能性も親 brief のままでは成立しない。** 現行 `guard_write` は既に `hooks/` を拒否し、apply_patch の全 directive を `classify_path()` へ通す（`guard_write.py:239-243`; `guard_write.py:301-325`）。したがって D374 の「guard_bash を先に apply_patch」「guard_write を最後に apply_patch」は現在の worktree では通らない（`d374-guard-edit-procedure.md:5-11`; `s2-plan.md:191-199`）。

- **「純増」は限定的に支持。** 射影された現行 guard には authority 固定 root がなく、読取り専用の `decide()` 直呼びでも authority への `Write` と `printf >` は現在 `allow` だった（`guard_write.py:239-288`; `guard_bash.py:2523-2529`）。計画上も既存条件への OR なので、既存の拒否から許可へ反転する入力は確認できない。ただし追加拒否集合は、親がいう「authority への writer」より広く、上記の copy-out 等を巻き込む。

- **受理を増やす計画上の入力は見つからない。** builder 例外も legacy leaf に限定するため、設計どおりなら `A1 ⊆ A0` である（`s2-plan.md:114-120`）。問題は受理増加ではなく、拒否不足と過剰拒否の同居である。

- **「編集面の衝突なし」は再現不能。** `s1-brief.md:21-22` の 104 branch・95 worktree 測定に使った inventory と時点状態は射影されていない。仮に当時正しくても snapshot であり、実装開始時まで衝突がないことへ一般化する lock にはならない。

- production の参照二件と authority root の 0700・四件配置も、参照先の tools と authority directory 自体が今回の射影外なので独立再確認はしていない（`s1-brief.md:13-20`; `s2-plan.md:124-137`）。

## 裁定パッケージ候補

1. **inode alias を scope に入れるか。** 推奨は authority regular files の inode index を両 guard に加えること。外部 hardlink の unlink まで拒否するかは、書込みと directory-entry 操作を分離して裁定する。

2. **ancestor/destination semantics。** `rm`/`mv` では authority の祖先も拒否し、tar/rsync/copy の directory destination では authority を生成・上書きし得る祖先を扱う必要がある。ただし親 `/work/1/SFC/tanab` への無関係な copy まで全面拒否すると偽陽性になるため、command別解析か保守的拒否かを裁定する。

3. **shell 状態モデル。** `pushd`、`env/sudo --chdir`、subshell、`&&`/`||`、partial glob、ANSI-C quote を scope に足すか、これらを明示 residual として「直接 Bash 面を閉じた」という主張を狭める必要がある。現状の単一 cwd 変数では両立しない。

4. **D906 を満たす実効層。** 同一 uid の 0700 + PreToolUse hook は「AI が書けない領域」ではない。推奨は秘密鍵と issuer を別 OS principal/service に置き、AI 側には検証用公開鍵または限定署名 API だけを渡すこと。`guard_read` 追加だけでは Bash、script、別 process、MCP 等を閉じない（`d906-receipt-authenticity.md:3-10`; `hooks-readme-protection-boundary.md:10-14`）。

5. **D374 の一度きりの適用経路。** 現行 self-guard 下で author の apply_patch は実行不能である。path を隠す Git 操作や一時無効化ではなく、ユーザー承認済みの外部一回適用手順を先に裁定する必要がある。

## 総括

段2は P1-c/P1-d と現行 D374 手順の問題を正しく見抜いているが、提案された実装範囲でも authority の直接 Bash 面は閉じない。特に ancestor 操作、parent destination、partial glob、ANSI-C quote、cwd 状態、hardlink が実経路として残る。一方、copy-out、symlink alias の unlink、実行されない `cd` は過剰拒否になる。

既存拒否を許可へ反転する計画上の経路は確認できない。ただし D906 の「AI が書けない領域」は hook wave 単独では成立せず、OS 権限境界を別裁定にする必要がある。ファイル変更と pytest 実行は行っていない。実行したのは書込みを伴わない現行 `decide()` の分類 probe のみである。