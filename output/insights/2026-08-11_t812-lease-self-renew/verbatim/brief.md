# 段 1 brief — [T-812] 受入 lease の自己保持 deadlock の恒久対応

## scope (裁定 = worklog 424 / inbox §96、推奨 3 点セット)

1. `tools/wave_land_window.py` の `claim`: 自己保持 (lease が有効 かつ holder == self) を検出したら
   **TTL を更新 (lease の mtime を現在時刻へ) して `held-self` を返す**。
2. `tools/dev_wave_wait.py` (待ち手正本): claim 受理集合を `{acquired, held-self}` へ広げ、
   `held-self` でも受入 command を投入する。
3. **自己保持なのに進めない場合は黙って polling せず fail-closed で理由を出す** (TTL 更新に
   失敗した / 自己保持だが有効性を確認できない)。

- 却下済み代替 = release して取り直す (飽和時に最後尾へ戻る + 解放窓で並行受入の穴)。段 4 で
  非同値な択一へ戻さない (`DW-S04`)。
- 併せて **deadlock 再現テスト**で固定し、変異で検出力を実測する (共有調整機構のため必須)。
- docs 整合: `docs/pegasus-runbook.md` §7.3 (待ち手の受理集合・TTL・release 権限の記述)。
- **scope 外 (裁定で明示的に除外)**: docs-only fold が lease 外で main を進める隣接 race
  (rc=23 / rc=10 stale-main)。受理集合に触れるため実装せず、**機構案を裁定パッケージで返す**
  (inbox §96 追記・§98 付帯 2)。

## 実測した前提 (段 1、私有 lease dir・repo 外 probe)

- **F-1** `claim` #1 = `acquired`。**F-3** 同一 wave の `claim` #2 = `state=held` /
  `holder_self=true` → 待ち手の exact `acquired` 判定に永久に一致しない。
- **F-4** 自己 claim の前後で lease の mtime は **1786441353 のまま不変** = **TTL は延びない**。
  自己保持のまま長時間走ると 2400 秒で自分の lease が stale になり、他 wave に奪われうる。
- **F-6** 正本待ち手 (poll 30 / max-wait 60) は自己保持で空転し `stage=claim-timeout rc=70`
  (32 秒後)。**本番既定は max-wait 7200 秒**であり、実害 3 例 (land 1 で約 18 分、t756 で約 20 分)
  は人手中断による。**F-5** 待ち札の残骸は 0 枚 (自己保持で ticket は残らない)。
- 既存テストは **deadlock 側を固定している**: `test_acceptance_non_acquired_state_never_runs_command`
  は `held` で command を投入しないことを assert し、`wave_land_window` 側にも自己 claim が
  `held` を返す前提の assert がある。→ 本 wave は両方を書き換える。

## 純増検出力 (性質で検索した結果)

現状 `orchestrator/tests/` には「**自己保持が他 wave の保持と区別され、進行可能である**」性質の
テストが 1 件も無い (`holder_self` の assert はあるが、いずれも *進行できる* ことを要求しない)。
純増は次の 4 性質:
- (N1) 自己 claim が TTL を延ばす (mtime が前進する)。
- (N2) 自己 claim の返り状態が他 wave 保持と**別の値**であり、待ち手がそれで投入する。
- (N3) 自己保持だが更新できないとき、待ち手が polling せず **理由付きで** fail-closed する。
- (N4) 他 wave 保持 (`held` / `queued` / `stale-held` / `unavailable`) は従来どおり投入しない。

## 不変条件 (緩めない)

- 直列化の意味論 (1 tip を 1 main に対して検査する) を弱めない — 裁定 425 (d) と整合。
  `held-self` は **既に自分が持っている lease で進む**だけで、並行受入の窓を新設しない。
- 他 wave の lease を触らない (holder digest 不一致では何もしない)。
- 待ち行列 (待ち札) の公平性を退行させない。自己保持時に他 wave の待ち札を消さない。
- fail-closed を loop・警告・default-allow へ緩めない。
- `tools/run_tests.py` と受入形状判定には触れない ([T-813] の評価対象、干渉禁止)。

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1)** 新状態名は `held-self` (裁定文の逐語)。`stale-held` の自己保持 (TTL 超過) は
  `held-self` に**含めない** — TTL 超過は排他が失われた可能性を意味し、黙って更新すると
  正しさの機構が弱まるため。既存の stale 経路 (unlink → 再取得 → `acquired`) を変えない。
- **(P2)** `held-self` は待ち手に **release 権限を与えない**。runbook §7.3 の
  「この呼出しが作った lease 以外は release しない」不変条件を保ち、失敗時も保持したまま返して
  親の終端 release に委ねる (同一 slug の別 invocation を巻き添えにしないため)。
  → 受入赤のとき lease が残る点が `acquired` 経路と非対称になる。攻撃対象。
- **(P3)** TTL 更新は `claim` の自己保持分岐だけで行う (専用 `renew` subcommand を新設しない)。
  裁定文が `claim` へ寄せているため。
- **(P4)** 版混在の互換層は作らない。待ち手は自分の worktree の `wave_land_window.py` を呼ぶので、
  旧待ち手が新 `held-self` を見る経路が無い (見た場合も未知 state で fail-closed = 安全側)。
- **(P5)** 更新失敗の表現は既存 `unavailable` + 新 reason (例 `self-renew-failed`) とし、
  claim の state 語彙をこれ以上増やさない。待ち手は reason を **stderr へ出して** fail-closed する。

## 成果物の形

- `tools/wave_land_window.py` / `tools/dev_wave_wait.py` の差分 (Codex `role=author`)。
- `orchestrator/tests/test_wave_land_window.py` / `test_dev_wave_wait.py` の追加・改訂。
- 変異 matrix (**wave 前の実コードの形 1 件を必ず含む** = 自己保持で `held` を返す形 /
  待ち手受理集合が `{acquired}` だけの形)。
- `docs/pegasus-runbook.md` §7.3 の整合 (親が docs-only で編集)。
- 裁定パッケージ: scope 外の docs-fold race 機構案。

## 成果物影響 (`DW-G05`)

実装しない場合、受入 lease を保持したまま 2 走目へ入る wave は待ち手が最大 7200 秒空転して
**受入全走が投入されない**。その間 lease は他 wave も取れないため、**certified 選択・レポート・
台帳へ入るべき成果が land されずに滞留する** (実害 3 例で計約 38 分の空転を実測済み)。
また TTL が延びないため 2 走目で lease が stale になり、**他 wave が同時に受入を始める窓**が開く
= 直列化の意味論そのものが壊れる。

## 分割方針

小さい面 (2 file + 2 test file) なので実装子は 1 本。段 3 の敵対レンズは 2 本
(正しさ/排他の面、fail-closed と権限境界の面)。段 6 レビューは 2 本 + 焦点再レビュー。

## 環境

login node で pytest 実測 (計算資源は不要)。受入全走は共有 lease を取ってから (稼働中の
[T-813] が段 9 で待機中のため、待ち行列に並ぶ)。
