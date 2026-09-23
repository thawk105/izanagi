---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-23
wave: dev-wave-t2863-silo-policy-stage-d
seq: 2
---

## {{D:silo-policy-stage-d-recon}}. silo-function-policy 軸の段階 D を、型付き有限 IR の固定 16 点の偵察で閉じる — 基準は骨格内の退化点 abort0、二値は同 job 比 3% 超の別 job 再現、後段へは二値だけを渡す

**決定:** D2214・D2226 に続き、軸 `silo-function-policy` の段階 D (手順書 §3-D の機械偵察) を実装・実測した。記録の正本は `output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md`、段 4・段 6 の裁定の逐語は同 dir の `verbatim/`。

1. **IR:** 設計 §5 の契約値を、frozen dataclass の型付き式木 (定数・abort 要因・lock 試行番号・状態参照・比較・条件式・min / max・飽和加減算・有界 shift) と hook ごとの同時代入で表す。深さは葉を 1 として ≤ 4、node は全 hook の式木の出現数の合計で ≤ 64、状態 ≤ 4 field、数値二項演算は同型同士、乱数は入れない。描画は hook の入口で参照する状態を局所へ写してから計算し最後に代入する。出力は policy-C++ v1 の部分集合で、受理契約と 4 段検査は変えない。
2. **列挙:** 4 因子 (lock 応答・状態依存・要因依存・待機の単位) × 2 水準の完全要因 16 点。定数は段階 C の手書き方策の値から結果を見る前に固定する。「全 IR の列挙」ではなく固定テンプレートの部分空間の全列挙と記す。
3. **基準と二値:** 比較の基準は骨格内の退化点 abort0 (待機 0・lock 競合で即 abort) を各 job に置く。二値 = 「両 verify certified・非 high-abort (abort 率が同 job の abort0 の 2 倍以下) の点が、同 job の abort0 に対して 5 rep 中央値で 3% 超を示し、それが別 job の再測でも再現したか」。欠測・照合不成立・再測未完了は null で、false にしない。軸 OFF の stock と `B0-L-W0` は同 job の参考値として別掲し、二値に使わない。
4. **計算の分割:** 初走は 8 job (各 job = {ID, bit 反転} の 2 点 + abort0、stock と `B0-L-W0` は 1 job ずつ) を同時投入、再測は候補ごとに 1 job (abort0 を先頭に順序を反転) を ID 順に 4 本ずつ投げ、1 点でも再現したら次の組は投げない。投入は既存の許可済み経路 `dispatch_compute.py --task generic` を計測用 worktree ごとに使う。
5. **firewall:** 後段 (段階 E / F の coder・planner の入力) へ渡すのは二値と射程文だけの投影 JSON (`projection.json`) で、点 ID・因子・比・順位を含めない。偵察 insight を読んだ事実は段階 E / F の campaign provenance に情報源として記録する。機械的な firewall は段階 E の scope。
6. **結果:** 二値 = true。16 点すべてが両 verify certified、abort0 比 1.34〜1.78、ID 順の先頭 4 点が別 job で 1.53〜1.62 を再現。計算は約 1.6 node 時間 (ユーザー承認の上限 4.0 の内側)。

**理由:**
- 1・2: 構成で停止性と算術安全を保証でき (loop・再帰・任意 call なし、除数と shift 量は literal、飽和は条件式で危険側を評価しない)、login の正式検査 (17 方策の構文検査・単独 TU compile、UBSan harness 20/20) で裏取りできた。
- 3: 軸 OFF の stock を基準にすると骨格の常駐コストが混ざる (trigger 偵察の ident_all と同じ理由)。abort0 は `B0-L-W0` と同じ意味論を骨格内で表す点で、同 job の値もほぼ一致した (2,407 と 2,423 千 txn/s)。
- 4: ユーザー指示「一瞬で終わらせてね。計算ジョブを分割して投げることで」。dispatch は checkout ごとに同時 1 本なので worktree を分けた。子が書いた新しい投入 script は投入許可台帳に未登録で実行できなかった。
- 5: 手順書 §3-D の firewall。

**却下した選択肢:**
- 2 job 分割 (段 4 の当初案) — ユーザー指示で 8 job に替えた。偶奇分割は因子 M と job を完全に交絡させる (段 3 相談 A1 / B5)。
- 新しい job body と投入 script を投入許可台帳へ登録する — 台帳・hook test・runbook の改訂と admission の証拠が要り、既存の generic dispatch で足りる。
- high-abort 除外の基準を別の値に変える — 結果を見る前の裁定事項であり、abort0 比 2 倍 (D46・trigger 偵察の規則の流用) のまま限定を記す (基準率 ≥ 0.5 では構造的に不発)。

**限定:** 基準 abort0 は write-heavy で abort 率 0.78 の thrashing 点で、待機を入れる方策ならほぼ何でも 3% 線を越える。本決定の二値は「IR 空間に既知最良 (調整済みの静的・適応 backoff) を超える地形があるか」には答えていない。床 3% は Pegasus・新骨格で較正していない暫定値である。
