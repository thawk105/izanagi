---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t1942-floor-gate-probe
seq: 2
---

## 新規

### {{F:self-invalidating-input-manifest}}. 検証が要求する入力を、その入力を記録した producer 自身が検証前に削除していた [ドリフト] [手順漏れ]

- 事象: 床値実測の主経路が binary admission receipt の発行段で
  `compiler input manifest の完全検証に失敗: external compiler input is unavailable` で落ち続けた。
  cache 再利用の副作用と読まれていたが、実測では **cache が空の初回実行でも落ちる**。
  記録された入力 588 件のうち 38 件が、1 回の実行かぎりで消える場所の絶対 path だった
  (build cache の作業用 directory `.staging-<PID>-<nonce>/_deps/…` が 31 件、
  job 専用作業領域 `/scr/0_<jobid>.nqsv/{gflags,glog}-install/include/…` が 7 件)。
- 根本原因: 記録側と検証側が別の生存期間を前提にしていた。`buildcache.py:2690-2712` は
  compiler input manifest を `completion.json` へ確定した**直後に**
  `_discard_build_dir(staging)` で作業用 directory を破棄し、その後 publish する。
  一方 `s8b_compiler_input.py:632-639` の検証は、記録された全 path を
  `resolve(strict=True)` で再解決することを要求する。**producer が消した path を
  consumer が実在要求する**構図なので、関門は原理的に一度も通らない。
  `_external_entry` を導入した `0bc33ba8f` は、この検証を追加した際に主経路を
  実機で最後まで通しておらず、次の実投入 (同日 14:02) で初めて露出した。
- 恒久対応: D1192 が是正の正本 (根の分類 + 根相対 path + 使用時の再束縛)。ただし裁定文は
  build cache 側の 1 クラスしか名指ししていないため、job 専用作業領域を含む 2 クラスへ
  射程を広げるかをユーザー裁定へ返した ([T-2027])。手順面は `DW-G01` の生死実験先行に加え、
  F731 の恒久対応「関門 X を外せば主経路が通るを実装だけで閉じない。外した後に実機で
  最後まで通すことを終端条件にする」を、**関門を足す変更にも同じく適用する**。
- 再発検知: 関門が要求する実在 path のうち、producer が同じ処理の中で削除・改名する場所に
  属するものが 1 件でもあること。cold cache の 1 回走行を positive control として、
  受領書発行段まで到達するかで判定する。

## supersede 追記

- F731 **supersede: 2026-08-29** — 「同日中に環境か main が変わった」の未特定部分を特定した。環境ではなく main で、`0bc33ba8f` (2026-08-27 06:19) が `_external_entry` を新規導入したことが原因である。あわせて、この赤は cache 再利用の条件付きではなく無条件であり、cold cache の初回実行でも落ちる ({{F:self-invalidating-input-manifest}})。
