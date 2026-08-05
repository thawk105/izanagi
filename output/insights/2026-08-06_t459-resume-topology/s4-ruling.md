# 段 4 裁定 — [T-459]

親が段 3 の 2 レンズ所見を real/refuted・採用/不採用・scope 内/外に裁定し、plan v2 と
変異事前登録を確定する。

## 前提の確定 (段 1 の誤りの訂正)

- **訂正 1**: brief (P2) の「`wal.replay` は read-only のまま残す」は事実誤認。現行 replay は
  trigger orphan の tombstone を書く (`wal.py:1014-1025`)。両レンズ指摘は real。
- **訂正 2**: brief 不変条件 2 の「既存 bytes を変えない」は、終端 record の追記と逐語で両立しない。
  正しくは「**既存の valid prefix は不変。追記は suffix のみ。read 経路は無変更**」。
- **訂正 3**: M3 は「共有 admission gate を通る consumer (Layer3 / critic / completeness)」に、
  M6 は「`loop.run_campaign` 系が生成する campaign」に限定する。raw WAL を直接読む
  `tools/plotting/plot_backoff.py` と、独自 lock/report を持つ S8b oracle は反例。
- **訂正 4**: M4 の走査は repo `output/` 30 本に限る。レンズ A の独立走査でも repo exploration
  WAL 0 本、`IZANAGI_EXPLORATION_OUTPUT_ROOT` 未設定、job root WAL 0 本だったが、
  **未走査の外部 root がないことの証明ではない**。worklog にはこの限定付きで書く。
- **確認 (実測)**: `test_campaign.py:3991` `test_loop_identity_error_retryable_survives_inflight_crash`
  は「build_start だけで途切れた in-flight crash の次 run で再評価される」ことを D25 の保証として
  pin している。したがって **crash 時に停止する設計 (fail-closed halt 一本) は既存保証の後退**であり、
  採らない。recovery-abort 方向 (P1) を確定する。

## 所見の裁定

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A1/B1 | campaign-wide owner lease 不在。並行 resume・生存 peer を排除できない | **real** | **scope 外**。新機構であり運用契約を変える設計択一。裁定パッケージへ。本 wave は「resume は旧 evaluator 終了後」という運用前提を worklog に明記する。**新たな悪化はない** — 並行実行は現行でも二重 start を作る。新規ハザードは「生存 peer の attempt を中断扱いにする」ことだが、peer が後続 record を書けば従来どおり topology が loud に拒否し、書かなければ成果が捨てられるだけで**偽の certified は生じない** |
| A2 | recovery record の真正性を admission が証明できない (二重 start で恒久拒否だった WAL を、abort 混入で救済できる) | **real** | **scope 外・裁定へ**。「recovery 済み campaign を certifying とするか」は設計択一。WAL は元来 hash chain を持たない (`wal.py:14`) ため、本 wave の差分が作る穴ではなく、救済可能列が 1 つ増える |
| A3 | `verify_done` / `bench_done` が attempt 非局所。A の bench を B の commit へ誤帰属しうる | **real・成果物直撃** | **本 wave で塞ぐ (縮小方向)**。恒久解 (signal の attempt 束縛 + consumer 射影) は scope 外・新 T。本 wave は **回復対象 attempt が `verify_done` / `bench_done` を出していたら recovery せず fail-closed** とし、誤帰属が起こりうる列を受理集合から外す。build 中の crash (支配的な窓) は従来どおり回復する |
| A4 | recovery abort payload の余剰 key (`build_admission` body 等) が通る | **real** | **本 wave で塞ぐ**。exact key 集合のみ許可 |
| A5 | 決定的 crash で「recovery + 新 start」が無限に増える | **real** | **本 wave で塞ぐ**。variant ごとの recovery 回数上限 (既定 3) と明示的 `recovery-exhausted` 終端 |
| A6/B4 | 親 M1〜M6 の過剰一般化 | **real** | 訂正 1〜4 で採用 |
| B2 | p3 の outer `drive_iteration` が `stopped-before` で inner seam を迂回 | **real** | **本 wave で塞ぐ**。recovery は public entry 側、`check_stop`・checkpoint・provenance 書き込みより前に置く |
| B3 | guided は fresh-only でなく、attempt schema 無しの pseudo-WAL を再利用する | **real** | **scope 外・新 T**。本 wave の主張を「admission-aware な post-policy build attempt」に限定し、「全 `build_start` を被覆した」とは書かない |
| B5 | trigger provenance の `recovered_attempts` が無いと trigger campaign は admission 不通のまま | **real** | **scope 外**。proof chain 文書の schema 拡張は独立審査に値する。代わりに **trigger campaign は recovery 対象外として fail-closed** とし、「trigger では効かない」ことを worklog に明記する (実装したふりにしない) |
| B6 | 入口網羅テストが穴を殺さない | **real** | **本 wave で採用**。public entry ごとの real-writer テストを要求 |
| B7 | recovery の schema 判別条件が曖昧 | **real** | **本 wave で塞ぐ**。判別を exact に定義する (下記) |
| plan §5 | `wal.replay` の書き込み除去 (read-only 化) | real な改善だが | **scope 外・新 T**。trigger orphan 自己修復の移設を伴い、trigger を fail-closed にする本 wave では移設先が無い。replay は無変更とする |
| plan §8 | trigger provenance 拡張 | — | B5 と同じ。不採用 |
| plan §7 | 5 inner entry の置換 | — | 採用するが B2 により **public entry 側**へ置く |

## plan v2 (実装する内容)

### 受理する回復の定義 (exact)

`campaign.lock` が admission policy を宣言する post-policy campaign で、WAL の EOF 時点に
**未終端 attempt** (`build_start` 済みで `commit` / `abort` 無し) がある場合に限り回復する。
次のいずれかに当たるものは**一 byte も書かず fail-closed で停止**する。

1. 回復対象 attempt の `build_start` より後に `verify_done` または `bench_done` がある (A3)。
2. campaign が trigger 系 (trigger machine lock、または当該 attempt に trigger binding
   commitment がある) (B5)。
3. 当該 variant の recovery 回数が上限 (既定 3) に達している (A5)。
4. 既存 WAL が回復前の時点で topology 違反である (追記で既存違反を上書きしない)。
5. 回復対象が 1 variant に 2 つ以上ある (単一 variant に複数 active = 既に不整合)。

**schema 判別 (B7)**: いずれかの record が attempt-schema key (`build_attempt_id` /
`build_admission` / `build_admission_receipt_sha256` / trigger commitment) を 1 つでも持つなら、
追記前に必ず strict topology 検査へ送る。key が全く無い WAL (guided の no-build pseudo-WAL) は
no-op とし、bytes を変えない。「start が marker を持つか」だけで判定しない。

### 追記する record (A4)

stage は `abort`。payload は次の exact key 集合のみ。他の key (とくに `build_admission` body、
fitness、verify payload) は載せない。

- receiptless: `{"reason": <RECOVERY_REASON>, "build_attempt_id": <元 attempt id>}`
- receiptful: 上記 + `{"build_admission_receipt_sha256": <元 start と同一 SHA>}`

`variant` と `env_tag` は元 `build_start` のものを再利用する。
`RECOVERY_REASON = "recovery-abort-incomplete-attempt"` を `model.py` に定数として置き、
`RETRYABLE_ABORT_REASONS` へ追加する (P3。追加しないと crash した variant が永久 skip され、
D25 の保証と `test_campaign.py:3991` を破る)。

### 原子性

scan → 事前 topology 検査 → prospective records の再検査 → append を、WAL fd の
`LOCK_EX` を保持したまま 1 区間で行う。検査に落ちたら一 byte も書かない。
これは**同一ホストの二重 recovery を直列化するだけ**であり、A1 の owner lease ではない。

### 配置

- `ident` に identity 照合済みの回復 seam を置く。`ensure_resumable_wal` (identity → tail repair
  → recovery) は既存 4 caller の挙動を保つ。
- `ensure_campaign_identity` だけを呼ぶ 5 経路 (`s6_sort_sweep`, `s8a_trigger_sweep`,
  `p3_s4_loop`, `p3_s4_loop_sort`, `p3_s4_loop_trigger_gating`) には、**truncated tail repair を
  伴わない** identity + recovery の seam を新設して呼ばせる (既存の tail repair 挙動を entry ごとに
  変えない)。
- p3 の 3 系統は public `drive_iteration` 側、`check_stop`・checkpoint・provenance 書き込みより
  **前**に置く (B2)。

### 変更しない (明示)

`wal._validate_attempt_topology` の拒否条件、`pipeline.evaluate` の attempt id 生成と
`build_start` emit、`artifact_admission` の topology 直呼び、`wal.replay` の現行挙動。

## 成果物影響 (DW-G05)

実装しない場合: crash を挟んだ post-policy campaign は次 replay と artifact admission で
campaign 単位に拒否され、実行時に committed と報告された certified 選択・Layer3 report・
台帳参照が事後失効する。
本 wave の縮小裁定 (A3/B5 を fail-closed) により、**verify/bench 到達後の crash と trigger
campaign は自動回復されず、人手介入が要る**。これは偽の certified を出さないための意図的な
受理集合の縮小であり、worklog に射程として明記する。

## 変異事前登録 (DW-M01 / B-057)

各変異は単一理由性を実装時にコードで確認し、確認できなければ登録を取り下げて実効 gate へ再照準する
(F28)。期待 node は実装後に確定した nodeid へ正規化して突き合わせる (F33/M8)。

| # | 変異位置 | 無効化する保証 | 期待 kill (受理集合の変化) |
|---|---|---|---|
| MU-1 | recovery payload から `build_attempt_id` を落とす | 終端 record と attempt の束縛 | topology の abort 分岐が拒否 → 回復 E2E が赤 |
| MU-2 | receiptful attempt の SHA 伝播を落とす | 別 attempt receipt の流用防止 | topology の abort SHA 一致検査が拒否 → 赤 |
| MU-3 | `verify_done`/`bench_done` guard を外す | A3 の誤帰属防止 | signal 到達後 crash を回復してしまう → 専用テストが赤 |
| MU-4 | trigger guard を外す | B5 の proof chain 不整合防止 | trigger campaign を回復してしまう → 専用テストが赤 |
| MU-5 | recovery reason を `RETRYABLE_ABORT_REASONS` から外す | crash 済み variant の再評価 | 永久 skip に戻る → `skipped=1` で赤 |
| MU-6 | recovery 回数上限を無効化 | A5 の無限成長防止 | 上限テストが赤 |
| MU-7 | 事前 topology 検査を外す | 既存違反 WAL への追記禁止 | 違反 WAL の bytes が変わる → 専用テストが赤 |
| MU-8 (正例) | 変異なし | 過剰拒否の検出 | 非 trigger・signal 前 crash が回復され admission を通る (緑であること) |

## 裁定パッケージ (ユーザーへ返す)

1. **campaign-wide execution lease の要否と形** (A1/B1)。推奨: run 全体で
   `campaign.run.lock` を `LOCK_EX|LOCK_NB` 保持 (process 死で OS が解放するため stale lease を
   作らない)。同一ホスト限定である点、同一 process の二重取得を避ける配線が要る点が論点。
2. **recovery 済み campaign を certifying とみなすか** (A2)。WAL は hash chain を持たないため、
   recovery を許すと「二重 start で恒久拒否だった WAL」を救済できる列が 1 つ増える。
   admission decision へ recovery の可視化を入れるか、recovery 済みを non-certifying に落とすか。
3. **`verify_done` / `bench_done` の attempt 束縛と consumer 射影** (A3 の恒久解)。本 wave は
   fail-closed で暫定回避。
4. **trigger provenance の `recovered_attempts`** (B5)。入れないと trigger campaign は crash 後
   admission 不通のまま。
5. **guided の no-build pseudo-WAL** (B3)、**raw plotter の admission 非経由** (B4)、
   **`wal.replay` の read-only 化** (plan §5) の 3 件を別タスクとして起票するか。
