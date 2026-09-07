---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2411-a6-readheavy
seq: 2
---

## {{D:a2-noreplace-link-publish}}. `renameat2(RENAME_NOREPLACE)` の無い filesystem では `os.link` へ落とし、link 成功時点で publish 完了とする

**決定:** `_atomic_write_bytes_noreplace` は、`_rename_noreplace` が
`EINVAL` / `ENOSYS` / `ENOTSUP` を返したときだけ
`os.link(staging, path, follow_symlinks=False)` へ落ちる。**link が成功した時点で publish は
完了**とみなし、以後 destination を削除も上書きもしない。staging の後始末は best-effort とし、
その失敗を関数の失敗にしない。それ以外の errno はそのまま伝播する。

**理由:**

- Lustre には `renameat2(RENAME_NOREPLACE)` が無い (実測: /work と /home で errno 22 EINVAL、
  ノード内蔵の /tmp では成功)。認証の受理証跡はこの経路でしか書けず、A-6 read-heavy の
  実走が 36 秒で止まっていた。
- `os.link` は既存名に対して `EEXIST` を返すので、regular file なら**上書き禁止の意味論を
  弱めずに**原子的な create-only publish になる。directory を publish する materialize 側が
  弱い代替 (排他 claim + 存在検査) を使っているのは link が directory に使えないためであり、
  regular file に同じ弱い形を持ち込む理由は無い。同じ選択を `orchestrator/calibrator/cli.py` の
  `_rename_noreplace` が既に採っている。
- **後始末の失敗で publish を失敗にすると、受理集合を不当に狭める。** destination は正しい
  bytes を持って durable なのに関数が失敗を返すと、再実行が `EEXIST` で永久に拒否され、
  成立するはずの走行が indeterminate になる。

**却下した選択肢:**

- materialize 側の `_publish_staging_after_einval` を流用する — 非協調 writer に対して
  原子的でないと docstring が明記しており、regular file には不要な弱体化になる。
- `EINVAL` だけを代替へ落とす — `ENOSYS` / `ENOTSUP` を返す filesystem で同じ欠陥が残る。
- `published` を後始末の後ろで立てる — 上記の再実行不能を招く。

**残る限界 (主張せず明記する):** link と unlink の間で process が死ぬと staging の別名が残る。
1 関数の局所修復では消せず、単一 syscall で無名 inode を publish する別 primitive が要る。
consumer は destination の正確な名前しか見ないので、成果物の値も参照も変わらない。

## {{D:a6-verification-fanout-axis}}. 認証の分割可否は「ノード間の性能差」でなく「比べる量かどうか」で決める

**決定:** 認証 campaign をノードへ分割してよいかは、**その工程が出すものがノード間で比較される
量かどうか**で判定する。真偽値を返す正しさ検査は分割してよい。stock と採用版の性能比較は
1 job・1 ノードに閉じたまま残す。

**理由:**

- `docs/pegasus-runbook.md`「ノード間の性能差は未測定である — これを禁止の根拠にしない」節が、
  ノード間差の大きさを fan-out 禁止の根拠にすることを明示的に禁じている。CC ベンチの
  ノード間比較は本 repo に存在しない。
- 同節が残す禁止は**処置とノードの一対一割付け (完全交絡)** であり、これは差の大小に依らず
  成立する。ただし成立するのは**量を比べる**場合だけである。直列性検査が返すのは
  serializable か否かであって、ノード間で引き算も割り算もしない。
- A-6 の実測では 73 分中約 70 分が正しさ検査 (48 スレッド × 約 7 分 × 10 回) で、性能計測は
  17 秒だった。各検査が全コアを使うので 1 ノード内では並べられず、**ノードへ割るのが唯一の
  短縮手段**である。

**却下した選択肢:**

- 検査の回数・強さを減らして短縮する — 正しさゲートの弱体化であり絶対規律 2 に反する。
- stock と採用版を別ノードへ割る — 一処置一ノードの完全交絡。

**未解決として残すもの:** 実行ファイルの同一性。認証は `perf_bin_sha256` を実ファイルと
照合するので、検査を別ノードで走らせるには同一 bytes の実行ファイルが要る。ノードを跨いで
建て直すと bytes が変わることは実測済みである。これは「技術的に不可能」ではなく
「現行 protocol では禁止」に当たり、配布か再現可能ビルドかを決める別の裁定で解ける。
