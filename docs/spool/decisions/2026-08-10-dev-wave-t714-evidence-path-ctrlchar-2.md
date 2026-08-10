---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t714-evidence-path-ctrlchar
seq: 2
---

## {{D:evidence-path-identity-wall}}. 証拠 path の同一性防壁は 2 層に置き、検査した値そのものを下位層へ渡す

**決定:**

- 証拠 path の同一性を壊す文字は、**契約 loader (`_safe_path`) と blob 読み出し
  (`read_blob_at`) の両方**で fail-closed 拒否する。片方だけにしない。
- `read_blob_at` の guard は **git へ渡す値そのもの**に掛ける。値は一度だけ文字列化し、
  `str` サブクラスの `__str__` / `__format__` / `__radd__` 上書きで
  「検査した値」と「渡す値」がずれない exact `str` へ固定してから spec を組む。
- 拒否の理由語は層ごとに分ける (`path-control-char` / `contract-path-control-char`)。
  既存の汎用理由語へ相乗りしない。
- 例外 message に生の path を入れない。診断のために入れる場合も、行を分断しうる文字を
  そのまま出さない。
- `read_blob_at` の guard は **CR/LF の framing wall** であって汎用の path validator ではない。
  canonical 化 (`./` 等) は契約 loader 側の責務であり、primitive へ持ち込むなら別途裁定する。

**理由:**

- `git cat-file --batch-check` は 1 行 1 要求で読む。path が行終端文字を含むと要求が
  分断・切り詰められ、契約が指す path とは別の blob が返る。実測では末尾 CR 付き path が
  prefix path と同一 blob OID を返した。
- 契約 loader だけに置くと、loader を通らない直接 caller と手組み dataclass を守れない。
  blob 読み出しだけに置くと、契約自体は valid と判定され、使われない汚染値が型付き契約へ残る。
- 「検査した値」と「渡す値」が別物になりうる経路 (f-string は `__str__` ではなく
  `__format__` を呼ぶ) は、guard を恒真にする。防壁は同一 bytes の上で閉じなければならない。
- 付随的な拒否 (空白 strip の副作用で端の制御文字が落ちる等) は防壁として数えない。
  明示検査と区別できないと、退行しても気づけない。

**却下した選択肢:**

- NUL 区切り入力への移行 — `--batch-check` は NUL 区切りを直接は取らないため実現性調査が要る。
  受理集合を狭める最小の変更で同じ穴を閉じられるなら、そちらを先に取る。
- 制御文字一般 (C0 全体) の拒否 — tab は alias しないと実測しており、同一性の観点では過剰。
  承認された裁定の範囲を親が広げない。
- 非文字列 path そのものの拒否 — 受理集合の変更が CR/LF を越える。API 前提の明示で足りる。
