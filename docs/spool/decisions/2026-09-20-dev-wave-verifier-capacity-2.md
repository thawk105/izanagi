---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-verifier-capacity
seq: 2
---

## {{D:verifier-packed-producer-array-workers}}. 直列性検査の producer / versions は鍵単位の packed 配列とし、edge worker は親の Python object に触れず配列だけを読む — 10 s trace の未完走 2 型 (OOM kill / pool 停滞) の除去

**決定 (2026-09-20 計算ノード実測に基づく親裁定、`dev-wave-verifier-capacity`):**

1. **原因の同定。** trace-enabled 10 s 走の未完走 2 型 (D2160 項 4) は、fork した edge worker 16 本が親の producer dict (key tuple / value int) と versions list (版 tuple) に refcount で触って copy-on-write で page を複製し、node memory 128 GiB を使い切る OOM kill である。balanced は親が殺され (rc −9、t≈308 s、`vmstat oom_kill` 0→1)、write-heavy は worker 1 本が殺され pool が壊れ、残 15 worker が計算ノードの job 配下 (SIGTERM 無視) で `Process.terminate()` に応じず `shutdown(wait=True)` の下で停滞して hard timeout に達する。`gc.freeze()` 単独では減らない (refcount 書込みが主因)。worker 数を 8 / 4 に減らせば現行でも完走するが worker 1 本の複製量は増える (親の object graph に比例) ので、既定 16 (D1553) は変えない。
2. **採る形 (1 つの変更)。** `orchestrator/verifier/dsg.py` の `_build_compact` は、全 write の epoch / tid が 32 bit 非負なら packed 経路 — writer を持つ鍵だけに初出順 id、file ごとの `token_id → key_id` 配列、版を `((epoch<<32)|tid) − 2**63` の flat `array("q")`、producer txid の並走配列、鍵ごとに版昇順・同版は出現順の安定整列で最初の writer — を作り、edge worker は配列と `bisect` だけで wr / rw / ww を生成する。範囲外の trace は従来の tuple builder をそのまま使う (partial な integrity を残さない)。`producer` / `versions` は既存消費者が使う Mapping 操作だけの薄い view。D1664 が「別 wave の候補」と残した「writer を持つ鍵だけに id を振る形」の実装である。
3. **pool 破綻の終端。** parse / edge とも worker 例外時に残 worker を SIGKILL してから shutdown し、Future / executor / 部分結果の参照を解放してから全件を親で逐次再計算する (D1552 の fallback は不変、部分結果は採らない)。
4. **判定の同一性。** `adj` の dict-of-tuple、set 再生順、root 初出順、witness 選択は変えない。fixture 全件 (22) の `result_to_dict` sha256 が base `947fd160a` の凍結一覧と一致し、完走済み校正 trace (fixed-5 / fixed-10 の 3 s / 6 s) と 10 s 2 件で旧新の `result_to_dict` と `VerifyResult` 全 field (非 wire の `expected_commits` / `observed_commits` / `proof_surfaces` を含む) が同一。
5. **実装しない案。** CSR 隣接、txid 直接 index の Tarjan、「全辺が前向きなら非巡回」の前判定は本 wave では採らない (未完走 2 件は replay / SCC に到達していない。前判定は rw 辺が commit 順・txid 順で逆向きになりうるため緑 trace で発火しない)。read-heavy 10 s 級 (1.2B edge 見込み) の将来 wave の候補として insight に設計を残す。

**理由:**
- 段 1 の profile (Pss / Private_Dirty の時系列、`oom_kill`、freeze A/B、worker 数対照) が原因を判別した。worker の Private_Dirty は自前出力の 10 倍超で、node MemAvailable の減少と一致する。
- 見積り (同 process 内): dict producer 8.96 GB / 105 s → packed 1.96 GB / 70 s (bal6、44.1M write)、5.28 → 1.55 GB (wh3)、4.15 → 1.04 GB (rh6)。実装後の compare: balanced 10 s 478 s / node peak 32.4 GiB (旧 8 worker 725 s / 78.7 GiB、旧 16 worker は OOM kill)、write-heavy 10 s 297 s / 15.2 GiB (旧 8 worker 493 s / 72.4 GiB、旧 16 worker は timeout)、balanced 6 s 275 s / 19.5 GiB (旧 364 s / 80.2 GiB)。
- 段 3 相談が「最小案から積む」「JSON 一致は非 wire integrity の代用にならない」「Private_Dirty だけで CoW を同定しない」「read-heavy 10 s は未保全」を指摘し、完了条件を bal10 / wh10 の完走 + 同一性へ改めた。

**却下した選択肢:**
- 既定 worker の削減 — 症状は消えるが根本原因 (共有 object graph の複製) は残り、所要が伸び規模で再発する。
- `gc.freeze()` の追加 — bal6 で効果なし (node peak 80.4 → 78.9 GiB)。
- CSR / 配列 Tarjan / 前判定を同時に入れる — 未完走 2 件の解消に不要 (段 3 B-1 / B-5)。
- 校正規則 (≤ 600 s) の充足を目標にする — 規則の改訂は裁定事項。結果として 10 s 2 件は 600 s 内だが、本 wave はそれを適格化とは扱わない。

**研究状態への影響:** certified 選択・レポート・台帳の値は変えない。verifier bytes の変更で既存 campaign lock は `contract-loader-drift` で再開不能 (D1552 と同じ帰結、扱いは裁定パッケージ)。B-8 の取得は主張しない (対象・種・長さは別の裁定事項)。
