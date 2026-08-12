---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t-codex-hook-trust
seq: 2
---

## {{D:codex-hook-trust-bypass}}. codex の hook 信頼は probe と本番の双方で明示 bypass し、その手前に fail-closed の配線検証を置く

**決定:** `tools/check_codex_hooks.py` の probe argv と `tools/codex_worker_launch.py` の worker argv の
**双方**へ `--dangerously-bypass-hook-trust` を option 領域に exact 1 件置く。その直前に配線の exact
検証を通し、赤なら起動しない。**flag 無し起動への fallback は作らない。**
sandbox bypass の禁止は不変で、argv 検査は prompt 内の substring も拒否する。
flag の検査は **prompt を除いた option 領域だけ**を見る — argv 全体を数えると、prompt に flag の
文字列を置くだけで検査を通せる。

これは D294 の却下選択肢「trust bypass を gate に使う」を supersede する。
**supersede が成立する条件は、checker と launcher を同時に land することである。** 片方だけでは
D294 の却下理由がそのまま実現する — checker だけなら本番の worker は未防護のまま gate が緑になり、
launcher だけなら受入が閉じない。D294 の他の内容 (判定核の共有、`codex_guard.sh` 経由の
fail-closed 化、閉じた面と開いた面の区別) は変更しない。

worker 側の検証は **retry ごとに `Popen` の直前**で行い、次をすべて満たさなければ `LaunchError` とする。

- `git -C <cwd> rev-parse --show-toplevel` が単一行・非空・絶対 path で、`--repo-root` に一致する。
  codex は `.codex/hooks.json` を cwd の project root 基準で解決するため、ここが食い違うと
  検証した file と実行される file が別物になる。`git` 不在・非 0・timeout は fail-closed。
- `.codex/hooks.json` が regular non-symlink で、PreToolUse の配線が exact 一致する。
- `hooks/codex_guard.sh` / `hooks/guard_write.py` / `hooks/guard_bash.py` が regular non-symlink で実在する。

検証後にも累積 wall-clock を再確認し、期限超過なら起動しない。

**保証の範囲を過大に書かない。** checker の rc=0 が言えるのは「bypass 下で、その clone の配線について、
一致する拒否証拠が stderr にあり、保護対象の side effect が無い」までである。**protected を exact 1 回
試したことの証明ではない。** worker 側は static preflight だけで live attestation を持たない。
guard 本体の bytes / hash、検証から `Popen` までの TOCTOU、user / global config、CLI semantics は
検証範囲外である。`tools/codex_reasoning_ab.py` と `orchestrator/codex_roles/launcher.py` の
直接起動経路も本決定の外にある。

**理由:**
- 信頼は hooks.json の絶対パス単位で永続化され、main checkout の承認は worktree にも使い捨て clone にも
  継承されない。信頼の無いパスの hook を codex は無警告で外す。この機序により dev-wave の codex 子は
  hook 無しで走っており、checker は構造的に rc=0 になれなかった (実測)。
- flag の但し書きは「hook source を自前で検証済みの自動化向け」であり、検証を先に置けば条件に沿う。
  ただし現在の検証は配線までで guard bytes は見ていないため、docs では「bytes 検証済み」と書かない。
- 両経路へ同時に入れることで probe と本番が同じ前提で走り、gate が本番を代表する。

**却下した選択肢:**
- checker だけに flag を入れる — 本番が未防護のまま gate が緑になる。D294 の却下理由そのもの。
- worktree のパスの信頼を `~/.codex/config.toml` へ機械追記する — ユーザーの個人 config を機械が
  書き換えることになり、wave ごとに肥大する。
- 検証が赤のとき flag 無しで起動する fallback を持つ — 黙って hook が外れる現状の再生産になる。
- probe を実 repo で行う — 保護対象への書込み試行を実 tree で繰り返すことになる。

## {{D:codex-hook-refusal-evidence}}. hook 拒否の証拠は event 列でなく stderr の nonce 一致で取る

**決定:** `check_codex_hooks.py` の protected control の判定を、event 列の
「`item.started` が exact 1 件あり、その start から `turn.completed` までの間に拒否文がある」から、
**stderr の逐語一致**へ移す。受理条件は、拒否 marker と handler marker と probe ごとの nonce と
相対 path が stderr に揃い、拒否 marker の出現が exact 1 で、保護対象の side effect が無いこと。
protected 側の `item.started` は 0 件を正とし、存在する場合は成功完了していないことを要求する。

codex が Bash command を報告する形は、**素の形と、実測された `/bin/bash -lc "<inner>"` の
exact 2 形だけ**を受理する。共通形へは畳まない — 畳むと outer executable・option・arity の区別が
失われ、受理集合が意図せず広がる。

**理由:**
- hook に拒否された tool 呼び出しは JSON event を一切生成しない (router の段で弾かれる)。拒否文は
  stderr にのみ出る。従来のモデルは、**hook が正しく効くほど赤になる**構造だった (実測)。
- nonce と相対 path は probe ごとに生成されるため、protected を試していなければ stderr に現れない。
  「未試行なのに緑」は排除される。
- ただし stderr は process-wide で、event ID・時系列との結合が無い。試行回数の完全な束縛はできない。
  拒否 marker の出現回数を exact 1 に縛って可能な範囲まで戻し、保証文はそこまでに下げる。

**却下した選択肢:**
- event 列の要求を残したまま flag だけ足す — 拒否された呼び出しは event を作らないので緑にならない。
- 拒否証拠を marker の存在だけで判定する — nonce と path が無いと、別 probe の拒否文や無関係な
  出力で緑になりうる。
- wrapper と素の command を共通形へ正規化する — outer の差を検査できなくなる。
