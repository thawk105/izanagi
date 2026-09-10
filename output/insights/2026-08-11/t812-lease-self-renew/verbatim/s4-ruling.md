# 段 4 裁定 — [T-812] 受入 lease の自己保持 deadlock

所見は sol 9 件 (A-01〜A-09) + luna 8 件 (F-01〜F-08)。**refuted は 0 件**、うち scope 内採用 7 束、
scope 外 (裁定パッケージ行き) 6 束、nit 1 件。プラン v2 は下記のとおり。

## 1. 採用 (scope 内・実装する)

- **R-1 = 裁定 3 点セットそのもの** (worklog 424 / inbox §96)。段 2 プラン §1〜§2 の形で実装する。
  `claim` の自己保持分岐で TTL (lease mtime) を更新し `held-self` を返す / 待ち手の受理集合を
  `{acquired, held-self}` へ / 自己保持なのに進めないときは polling せず理由付き fail-closed。
- **R-2 (A-03、real)**: `_open_lease` は **flock 取得後に再 `fstat` し、その metadata から
  age/stale を再計算する**。現状は flock 前の snapshot を使うため、TTL 境界で「更新直後の lease を
  先に snapshot した claimant が stale と判定して unlink する」経路がある。**これを塞がないと
  R-1 の TTL 更新が実効を持たない** (更新した端から回収されうる)。`_open_ticket` は既に
  flock 後 `fstat` しており (`:355-357`)、非対称の解消でもある。
- **R-3 (A-04、real)**: `held-self` の `age_seconds` を synthetic な `0` にせず、**更新後の実
  `fstat` から `_mtime_state` で再計算**する。再計算結果が stale なら成功にせず fail-closed。
  「更新したと報告したが実際は延びていない」を構造的に不可能にする。
- **R-4 (F-02、real・最重要)**: **renewal 経路の失敗をすべて構造化 `unavailable` +
  `reason=self-renew-failed` へ畳む**。`utime` / `fstat` / owner・regular 検査 / `_same_entry` の
  どれが失敗しても例外を外へ出さない。例外が出ると helper は rc=2 `internal-error` になり、
  待ち手の ownership が `UNKNOWN` のまま cleanup へ入って **lease を release する** (= 稼働中の
  受入から lease を奪う)。各注入点にテストを 1 件ずつ置く。
- **R-5 (F-01、real)**: 待ち手は `held-self` を **top-level `state` の exact 一致に加え、
  `holder_self is True` / `holder` が 12 桁 hex / `age_seconds` が int / `source =
  {"status":"ok","reason":null}`** を満たすときだけ受理する。**`state="held"` は
  `holder_self=true` でも決して受理しない** (wave 前の形 = deadlock の逐語) → stage
  `claim-self-unverified` で fail-closed。
- **R-6 (F-05、real)**: `status` は **mtime も payload も変えない**ことをテストで固定する
  (監視の定期 `status` が死んだ wave の lease を延命し続ける変異を殺す)。
- **R-7 (F-03/F-08、real)**: `held-self` 経路の **受入赤・postclaim 失敗・signal** で
  **release しない**ことを各 1 件のテストで固定する。event 列だけでなく **sleep 回数・release
  回数・実 lease の mtime/payload** を分離して検査し、`_FakeEffects` の期待 event 列を書き換える
  だけで緑にできる形を避ける。

**P1 / P2 / P3 / P5 は維持**する。P2 (「`held-self` は待ち手に release 権限を与えない」) は
両レンズとも「release 権限を与える方が正しさ影響が重い」と評価しており、専用
`_LeaseOwnership.HELD_SELF` (merge abort 権限あり・release 権限なし) で実装する。
**P4 (版混在の互換層を作らない) は維持するが、下記 (S-5) の但し書きを裁定パッケージへ書く。**

## 2. scope 外 = 裁定パッケージで返す (実装しない)

いずれも **real** だが、受入の受理集合・排他の意味論を変えるため、ユーザー裁定なしに実装しない
(`DW-S04`)。却下済み代替 (release して取り直す) へ戻すものではない。

- **S-1 (A-01 / A-02 / F-04、最重要)**: `holder` は **wave slug の SHA-256 先頭 12 桁**であり、
  **invocation の識別子ではない**。したがって `held-self` は「同一 slug の別 invocation」も通す。
  実測: **`tools/run_tests.py` に flock は無く、並行受入を後段で直列化する層は存在しない。**
  さらに待ち手の identity preflight は「branch 名が wave slug で終わる」ことしか要求しないので、
  **別 worktree でも同一 slug を持てる**。恒久解は invocation capability / fencing token であり、
  受入結果の受理条件そのものに触れる。**当面は「1 slug につき active invocation は 1 本」を
  運用前提として明示する** (機械保証ではない)。
- **S-2 (A-05)**: TTL (2400 秒) を跨いで受入 command が走ると排他は失われるのに、待ち手は
  `ttl_remaining=0` を印字して rc=0 を返す。fencing が無い以上、事後に取り消せない。
  heartbeat renewal (受入中の定期更新) か「排他喪失時は結果を受理しない」機構が要る。
- **S-3 (A-07)**: stale な自己保持を unlink → 再取得 (`acquired`) しても、**旧 invocation の
  受入が止まった証拠にはならない**。`lost-exclusivity` で止める案は既存の受理集合を変える。
- **S-4 (A-06)**: self-renew は外国待ち札を追い越す。**機構は「owner 優先」で確定** (lease を
  既に持つ wave が自分の仕事を続けるのは追い越しではなく、runbook も 2 走目を想定している) が、
  **累積保持時間 / 連続 renew 回数の上限**を設けるか (FIFO 保証を維持するか) は政策裁定。
- **S-5 (F-06)**: 旧待ち手が新 `held-self` を未知 state として拒否したとき、ownership が
  `UNKNOWN` のままなので cleanup が **同一 slug の lease を release しうる**。P4 の「未知 state は
  安全側」は `UNKNOWN` cleanup と両立していない。恒久解は atomic 配備か `UNKNOWN` の release
  権限の再裁定。**本 wave では触らない** (触ると lease leak 側へ問題が移る)。
- **S-6 (裁定 425 付帯 2、既定)**: docs-only fold が lease 外で main を進める race (rc=23 /
  rc=10 stale-main) の恒久対応。裁定文が最初から「機構案を裁定パッケージで返す」と定めている。

## 3. nit / 不採用

- **A-08 (self ticket の drop 失敗を握り潰す)**: real だが **wave 前から同一挙動**で、影響は
  自分の待ち札が最大 300 秒残ることのみ。`DW-G03` (族一般化には独立 2 例) にも達しない。変更しない。
- **A-09**: 「テスト・変異が排他破れを検出しない」は正しいが、検出すべき排他破れの大半 (S-1〜S-3)
  は scope 外である。scope 内の R-2〜R-7 に対応する試験だけ採用する。

## 4. docs 整合 (親が docs-only で行う)

- `docs/pegasus-runbook.md` §7.3: 受理集合、`held-self` の意味、P2 の release 境界、rc=70 の説明
  (「lease 未取得」→「fail-closed / 進行不可」)、2 走目の手順、owner 優先の既知限界。
- `.claude/commands/dev-wave.md`: 「`acquired` のときだけ投入」→ `{acquired, held-self}`。
  **byte 上限に注意** (追記型テストが余白を要求する)。
- `docs/decisions.md` D270 の acquired-only 記述は歴史であり書き換えず、本裁定による supersede を
  記録段で明示する。

## 5. 変異事前登録 (`DW-M01`)

実装後に anchor 逐語を確定し (`DW-M07`)、下表を spec 化する。すべて `expected_status=KILLED`。
単一理由性は「その変異を入れると当該 nodeid だけが赤くなる」ことを実装後に確認する。

| ID | 変異 (最小) | 期待 KILL |
|---|---|---|
| M01 | **wave 前の実コードの形**: 自己保持分岐を `return _lease_result("held", lease, self_holder)` へ戻す | lease 側 held-self テスト + 待ち手 deadlock 再現 |
| M02 | **wave 前の実コードの形**: 待ち手の受理集合を `{acquired}` だけに戻す | 待ち手 held-self 進行テスト |
| M03 | `os.utime` だけ削り `held-self` は返す | mtime 前進テスト |
| M04 | 更新後の `_same_entry` 再確認を削る / False を成功扱い | post-renew 照合テスト |
| M05 | renewal 失敗を `held-self` 成功 or `held` polling に変える | self-renew-failed テスト群 |
| M06 | `HELD_SELF` を `ACQUIRED` へ写す (release 権限を与える) | held-self 赤で release しないテスト |
| M07 | `HELD_SELF` を `NONE` へ写す (merge abort も省く) | 同上 + merge abort テスト |
| M08 | `held` + `holder_self=true` の即時 fail-closed guard を削る | legacy self-held テスト |
| M09 | `_open_lease` の flock 後 re-`fstat` を flock 前 snapshot へ戻す (R-2 の逆) | TTL 境界テスト |
| M10 | `age_seconds` を実 mtime 由来から synthetic `0` へ戻す (R-3 の逆) | age 由来テスト |
| M11 | `status` の self 分岐でも `utime` する (R-6 の逆) | status 不変テスト |
| M12 | renewal 失敗を例外のまま外へ出す (R-4 の逆) | 失敗注入テスト群 (rc=2 化を検出) |

## 6. 実装単位

1 単位 (Codex `role=author` 1 本)。編集面 = `tools/wave_land_window.py`、`tools/dev_wave_wait.py`、
`orchestrator/tests/test_wave_land_window.py`、`orchestrator/tests/test_dev_wave_wait.py`。
docs は親が別 commit で行う。
