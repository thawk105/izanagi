---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-exec-loc-and-usage-fixes
seq: 2
---

## {{D:exec-loc-classification-unknown-hold}}. `tools/claude_session_ledger.py` の分類は `unknown` に据え置き、実測は非 certifying な補助証拠として evidence に残す

**決定:** ユーザーが分類の**選択**を AI へ委任し、計算ノードでの実測が得られたが、
`class` は `unknown` のままとする。変えるのは `reason` / `primary_gate` / `evidence` の 3 field だけで、
hook の受理 bit は 1 つも動かさない。evidence には測定方式が §7.0 の canonical 手順でないこと、
測定 commit、実際に読んだ file 数と bytes、cap 到達、全走が `rc=2` だったことを書く。

**理由:**
- 実測は共有 service cgroup の `memory.current` delta sampling である。計算ノードには per-job cgroup も
  cgroup delegation も無く (`/proc/self/cgroup` が 1 行、2 ノードで確認)、非 root では専有 scope を
  作れない。同居 job の充当が混入し、実際に 1 走が負 delta になった。
- 測ったのは ledger 既定 argv (25 file) である。admission は path 粒度なので、
  許可すれば本番 helper の `--max-files=1000` も通る。cap 境界は測っていない。
- 非 `tools/pegasus/` path の `local-ok` は loader と hook が構造的に禁止し、negative test 3 本が
  張られている。この禁止は「適用 path を広げても受理集合は単調に縮む」(D175 決定 6) を
  成立させている当の機構であり、分類の反映のために撤去してよいものではない。

**却下した選択肢:**
- `class` を `local-ok` にする — 上記 3 点すべてに反する。受理集合を広げる新しい admission
  architecture であり、独立の裁定が要る。
- registry から entry を削除する — `_NON_PEGASUS_ADMISSION_FALLBACK_PATHS` が空集合になると
  `"|".join(...)` が空文字になり `re.compile("")` が全入力へ一致し、hook 内部例外時に
  無関係な command まで拒否する。保護も失う。
- evidence を `unmeasured` のまま残す — 実測が行われた事実と食い違う。

## {{D:message-id-replica-dominance}}. 同一 `message.id` の cross-file replica は usage dominance で 1 回だけ計上し、支配 candidate が無ければ従来どおり fatal にする

**決定:** 空でない canonical な `message.id` の一致を model call 同一性の公理として明示し、
複数 transcript へ複製された replica を 1 回だけ計上する。判定は 3 相で行い、
**final representative map と final invalid set は相 3 まで書かない**。
相 2 で canonical ID・全 member の終端 usage 存在・**usage dominance**・terminal model 一致・
tool identity 部分集合・**group 全 member の selector 判定一致**を検証する。
支配 candidate が 1 つも無ければ `message_id_collision` を立てて fatal に倒す。
共有 alias が無くても record UUID と正規化 content digest が完全一致する exact clone は結合する。
`FATAL_ISSUES` / `STRICT_ISSUES` からの降格はしない。

**理由:**
- 並列 subagent の transcript には同一 model call が複製される。従来の一律 fatal では
  使用量が 1 件も記録されなかった。
- 単純な「非 fatal へ降格」は複製を別 request として数え上げ、token を最大 4 重計上する。
  規律 2 の意味で、ゲートを緩めるのではなく意味を正しくするのが正しい方向である。
- 「終端 usage 全一致なら同一」という初案は実データで反証された。実入力には同一 message.id で
  終端 `output_tokens` が 10933 と 3 の群があり、これは streaming 途中の部分 snapshot である。
  dominance なら前 3 field が一致し output だけ差がある実データを正しく 1 回に畳める。
- selector 判定を代表 member だけで行うと、member 間で cwd や時刻が異なるときに対象 wave の call が
  欠落したり対象外の call が混入する。group 全体で一致を要求し、不一致は fail-closed にする。

**却下した選択肢:**
- `parentUuid` を同一性証拠に含める — 実データで replica 間の終端 `parentUuid` が一致しない。
- `message_id_collision` を `FATAL_ISSUES` から外す — 過大計上を招く。
- 支配関係の代わりに終端 usage の完全一致を要求する — 部分 snapshot を過剰拒否する
  (positive control 変異 MUT-4 が KILLED でこれを固定した)。

## {{D:usage-collector-exit-code-contract}}. `tools/collect_wave_usage.py` の rc を状態別に分け、収集は wave 完了 gate にしない

**決定:** rc は `complete`=0 / login と確証できた `blocked`=3 / 外側 argparse 拒否=2 /
それ以外 (`PEGASUS_SUSPECT` の `blocked`、`incomplete`、`missing`、`error`、未知 status)=1 とする。
artifact は従来どおり**先に**保存し rc だけを変える。呼び手は rc と artifact の
`collection.status` を併読し、**D220 のとおり収集は wave 完了 gate ではないので rc≠0 でも
完了済み wave を失敗へ戻さない**。内側 collector へ渡す argv は全て等号 1 token 形にする。
外側 CLI では先頭 `-` の slug に等号形を要求し、**外側 argv の正規化は行わない**。

**理由:**
- 従来は何が起きても rc=0 で、実 slug で内側 parser が `SystemExit(2)` になっても
  呼び手は成功と誤認した。台帳の欠測が検出されない。
- `blocked` は Pegasus login で正常に起きる既知状態なので、故障と同じ rc に倒すと標準手順が必ず失敗する。
  一方 `PEGASUS_SUSPECT` は「分類の証拠が壊れている」であり、正当な不実行と区別する必要がある。
- 外側 argv の正規化は、未知 option・argparse の省略形 (`--cwd-u`)・単独 `-` を値として飲むため
  受理集合を広げる。依頼された欠陥は内側の等号化だけで閉じる。

**却下した選択肢:**
- 全 status を非 0 にする — login での標準手順が必ず失敗する。
- rc を 0 のままにして stderr だけで知らせる — 現に見落とされてきた。
- 外側で `--project -slug` を正規化して受理する — 上記の受理集合拡大を招く。
