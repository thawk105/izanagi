---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-15
wave: dev-wave-t1116-known-red-registry
seq: 2
---

## {{D:known-red-registry-has-no-trust-root}}. 批准済み既知赤 registry は、AI が動かせない trust root が無い限り成立しない

**決定:** 「批准済み既知赤 nodeid の registry」を実装するときは、批准の権威を
**AI が変更できない場所**へ置くことを必須条件とする。repo 内の artifact
(JSON、decisions の D 番号、worklog エントリ番号、`authority:` 相当の field、
remote-tracking ref) はいずれも権威にならない。条件を満たせないなら registry を実装しない。

**理由:**

- 実測時点 (commit `330f67d0`) の repo に、人間だけが動かせる trust root は **0 件**である。
  `verify-commit` / `verify-tag` / allowed-signers は存在せず、git 呼出しに現れる gpg 関連は
  すべて署名を無効化する向きである。
- 書込みを禁止している機構は `hooks/` subtree だけである。`tools/check_codex_hooks.py` の
  pinned path 群は working bytes と HEAD blob の drift を検査するものであって、
  書込み禁止機構ではない。**pinned であることを「人間だけが書ける」の根拠にしてはならない。**
- `refs/remotes/origin/main` はローカル ref であり、`git update-ref` による移動と実際の push を
  暗号学的に区別できない。加えて実測時点で main は origin より 92 commit 先行しており、
  1 回の push が全 entry の一括承認になる。
- 権威を repo 内に置くと、**2 wave かけた事前登録**で任意の nodeid を救済できる。
  wave A が将来壊す nodeid を登録して緑で land し、wave B がその node を壊す。
  「registry を tested main 側から読む」拘束は同一 wave の後付けしか防がない。
- これは D316 が waiver を却下した 3 番目の理由 (批准 field を書くのは AI 自身であり、
  人間裁定を要求する機械的拘束にならない) が、registry 形でもそのまま生きていることを意味する。

**却下した選択肢:**

- **`expires_on` + 件数上限 + 台帳参照の必須化だけで批准とみなす** — 任意追加を難しくするが、
  すべて AI が書ける field なので批准の証明にならない。件数上限も snapshot 上限にすぎず、
  期限切れ entry の交換や同一 nodeid の再登録を禁じていない。
- **`refs/remotes/origin/main` への到達可能性を批准とみなす** — 上記のとおり ref が
  ローカルで移動でき、一括承認にもなる。ユーザーが明示的に「公開された registry snapshot 全体を
  批准と定義する」と裁定した場合にだけ成立する弱い定義である。
- **entry 署名だけを足す** — 公開鍵と verifier を同じ wave が交換できるなら無効化できる。
  署名を採るなら鍵の外部 pin、verifier 実行体の権威、rotation と revocation、
  署名 payload の domain separation まで同時に決める必要がある。

## {{D:acceptance-red-check-interpreter-is-tip-bound}}. 非帰属判定の実行体は wave tip 側にあり、実行体の権威は tested main へ束縛されていない

**決定:** 受入の赤を非帰属と判定する経路について、**判定の実行体 (checker script) が
wave tip の bytes である**という現行構造を事実として記録する。この構造を前提にしない
防壁設計 (registry、waiver、批准機構) を作らない。

**理由:**

- `tools/dev_wave_wait.py` は wave working tree の `tools/check_acceptance_reds.py` を起動し、
  受入受領証へ束縛する blob sha を `tested_tip` から採る。
- `tools/dev_wave_land.py` の受入受領証検証も `tested_tip:tools/check_acceptance_reds.py` と
  照合するだけで、**`tested_main` 側の checker blob と比較する検査は 1 件も無い。**
- land の protected path は handoff と control container だけであり、`tools/` 配下の
  内容を gate しない。監査は commit 列の provenance を見るもので、差分の意味を見ない。
- 帰結として、wave は自分の tip の checker を書き換えることで自分の赤を非帰属に分類させ、
  land を通せる。**この経路は registry の有無と無関係に現行で開いている。**
  probe worktree が tested main に作られることは、probe 対象の tree を固定するだけで、
  判定を下す実行体を固定しない。

**却下した選択肢:**

- **probe worktree が tested main であることを「判定が main 側で行われる」の根拠にする** —
  実測と食い違う。固定されるのは被験体であって判定者ではない。
- **本 wave で実行体束縛を実装する** — ユーザー裁定の scope は registry であり、
  実行体束縛は別の受理集合変更である。`DW-S04` に従い所見として裁定へ返す。
