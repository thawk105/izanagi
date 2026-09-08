---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-acceptance-gitbatch-20260908
seq: 2
---

## {{D:contract-loader-blob-batch}}. enforcement source closure の blob 取得は ls-tree + OID 指定 cat-file --batch の 2 process で行い、受理集合を変えずに拒否の優先順位だけを契約外にする

**決定:** `contract_loader_binding` の 62 path の blob 取得を、path ごとの `git cat-file blob <commit>:<path>` (62 process) から、
`git ls-tree -r -z <commit> -- :(literal)<path>...` で path→OID を取り、OID を stdin に並べた `git cat-file --batch` で bytes を取る
2 process へ改める。各応答 header の OID を ls-tree の期待 OID と exact 照合し、entry の不在・期待外・重複・非 blob、header の型・size・
record LF の framing、余剰 bytes、NUL を含む path はすべて `contract-loader-git-error` で fail-closed にする。
**受理集合と拒否集合は不変とし、拒否の優先順位 (どの path・どの理由が先に raise されるか) は契約外とする。**
drift 検査 (disk bytes == blob) と 4 公開関数の非対称 (capture: disk → digest、live: digest → disk、committed: digest のみ) は維持する。
batch 形の 2 呼び出しの timeout は `GIT_TIMEOUT_SECONDS * n` (n = 問い合わせ数) とし、旧形の 62 process × 10 秒の総許容量と揃える。
process 内 cache・memo は導入しない。

**理由:**
- 受入全走で admission 経路を通る test が 1 本あたり +30〜50 秒重くなっていた。login の profile で 1 test 47.5 秒のうち 36.4 秒が
  `_run_git` の git subprocess 704 回で、closure 62 path × (capture 5 + committed 4 + live 1) の逐次起動だった。
- login 実測 (62 path 1 回分): 逐次 62 process 5.4〜6.8 秒、`<commit>:<path>` 62 行を 1 process の `--batch` へ送る形 0.65〜1.5 秒
  (spec ごとに tree を辿り直す)、ls-tree + OID batch 0.07〜0.09 秒。3 形の digest 62 件は完全一致。
- `<commit>:<path>` 形の batch は success 応答が path に束縛されず、逆順応答と逆対応 digest が相殺して誤受理し得る (段 3 の指摘)。
  ls-tree で得た期待 OID を各応答 header と照合する形だけがこの経路を断つ。
- 全 path を subprocess 起動前に検査するため、先頭 path の digest 不一致より後方 path の path escape が先に raise されうる。閉包は定数 tuple
  なので production では観測不能だが、契約として明示するほうが正直である。
- 同 test の login A/B (交互 3 標本): 旧 30.9 / 11.3 / 17.9 秒 → 新 9.6 / 6.4 / 4.6 秒、git 起動 802 → 142 回。
  計算ノード (48 worker 同時) での効果は本決定では主張せず、受入全走の junit で別途読む。

**却下した選択肢:**
- `<commit>:<path>` を stdin に並べる 1 process 形 — 10 倍遅く、応答が path に束縛されない。
- process 内 memo `(root, commit, path) → bytes` — content addressing は object store の不変性と可用性を保証せず、root の差し替え・prune 後に
  古い bytes を返して fail-closed を壊しうる。導入しない。
- `ident.py` の capture 直後の live verify を省く — repository と disk が不変という前提下でだけ冗長であり、前提外では拒否側の分岐が消える。触らない。
- timeout を 10 秒のまま 1 process に適用する — 旧形が受理していた入力を計算ノードの遅延で過剰拒否しうる。
- 旧形の allowlist を `p3_b4_wiring_probe` に残す — production はもう発行しないので、許可形は今 production が発行する exact argv に最小化する。
