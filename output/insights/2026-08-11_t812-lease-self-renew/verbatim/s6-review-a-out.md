## A-01 / must-fix

**一行要約:** real helper が返すすべての `acquired` を `claim-self-unverified` と誤判定し、取得直後の lease を cleanup で release する。

**根拠:** helper の `acquired` は必ず `holder_self=true` を返す（[tools/wave_land_window.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:435)）。待ち手は先に ownership を `ACQUIRED` にする一方（[tools/dev_wave_wait.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:610)）、その後の `elif holder_self` が `acquired` にも発火する（[tools/dev_wave_wait.py:630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:630)）。cleanup は `ACQUIRED` を release 対象にする（[tools/dev_wave_wait.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:812)）。

**具体的な失敗系列:**

1. lease 不在、または stale lease 回収後、または待ち列先頭から `_create_lease` に成功する。
2. helper は `state=acquired, holder_self=true` を返す。
3. `_claim_once` は ownership を `ACQUIRED` にした後、`claim-self-unverified` を送出する。
4. acceptance command は一度も走らず、finally が取得した lease を release する。
5. rc=70 で終了する。

したがって親の一次診断は正しい。既知の 3 赤はすべてこの根で説明できる。さらに同根なのは、初回取得だけでなく、stale 自己/他者 lease の再取得と、待ち列からの取得を含む real `acquired` 全経路である。

テストの多くが `{"state":"acquired"}` だけを返す fixture（[orchestrator/tests/test_dev_wave_wait.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:197)、[orchestrator/tests/test_dev_wave_wait.py:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/orchestrator/tests/test_dev_wave_wait.py:302)）を使い、`holder_self=false` 相当になっているため、real helper の形だけが赤になる。

**成果物影響:** 裁定上の受理集合 `{acquired, valid held-self}` が、実環境では事実上 `{valid held-self}` に縮む。新規 wave は受入へ進めず、land と対応する台帳記録が生成されない。

**修正案（scope 内）:** `state == "acquired"` を自己保持拒否 guard から除外し、`held-self` の厳格検証後にのみ「それ以外の `holder_self=true`」を拒否する。real 形の acquired payload を使う正例を追加し、後段失敗時には従来どおり release することも固定する。

## 状態機械

`OK*` は `source == {"status":"ok","reason":null}` に加え、12 桁 holder と `type(age_seconds) is int` を満たす場合。`RF` は `reason=self-renew-failed` であり、実装は `source.status` を検査していない。

| state | holder_self | source | 実際の遷移 | ownership / cleanup |
|---|---:|---|---|---|
| acquired | false | 任意 | 進行 | `ACQUIRED`、後段赤なら release |
| acquired | true | 任意 | **誤って fail: self-unverified** | `ACQUIRED`、**release** |
| held-self | true | OK* | 進行 | `HELD_SELF`、release なし |
| held-self | true | その他 | fail: self-unverified | `HELD_SELF`、release なし |
| held-self | false | 任意 | fail: self-unverified | `HELD_SELF`、release なし |
| held | false | 任意 | polling | `NONE` |
| held | true | 任意 | fail: self-unverified | `HELD_SELF`、release なし |
| queued | false | 任意 | polling | `NONE` |
| queued | true | 任意 | fail: self-unverified | `HELD_SELF`、release なし |
| stale-held | false | 任意 | fail: claim-state | `NONE` |
| stale-held | true | 任意 | fail: self-unverified | `HELD_SELF`、release なし |
| unavailable | false | 任意 | fail: claim-state | `NONE` |
| unavailable | true | RF | fail: self-renew-failed | `HELD_SELF`、release なし |
| unavailable | true | その他 | fail: self-unverified | `HELD_SELF`、release なし |

新規の穴は A-01 の意図しない停止・release。`held` / `queued` の `source.status` 不整合は無視されるが待機は `max_wait_seconds` で有界であり、差分前からの state-only 契約である。`acquired/holder_self=false` も source に関係なく進むが、これも既存契約であり本差分による拡大ではない。

## その他の攻撃面

- `HELD_SELF` は merge abort 権限だけを持ち、release されない。[tools/dev_wave_wait.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:795)
- cleanup は実処理前に ownership を `NONE` へ消費するため再入は no-op。[tools/dev_wave_wait.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/dev_wave_wait.py:801)
- `UNKNOWN` の release 権限は維持されているが拡大していない。未知 state や helper 応答前の失敗が同一 slug の lease を消しうる点は裁定済み S-5/S-1 境界であり、本差分の新設ではない。
- flock 後の再 `fstat` は claim・release・status の全呼び出しへ適用される。[tools/wave_land_window.py:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:314) claim は更新後 lease の誤回収を防ぎ、release/status は判断・age を lock 取得時点へ新しくする。排他や出力 shape を緩める経路はない。
- renewal の `except Exception` は対象の `OSError` / `ValueError` をすべて構造化失敗へ畳み、`KeyboardInterrupt` / `SystemExit` 等の `BaseException` は飲まない。[tools/wave_land_window.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t812-lease-self-renew/tools/wave_land_window.py:749) R-4 に反する別の例外漏れは見つからない。
- 外国 wave の ticket、queue 順序、`message` / `release` / `status` の出力構造に変更はない。自己 renew の owner 優先は裁定済み S-4、同一 slug 並行進行は S-1 であり、新しい直列化破れは見つからない。

テストは再実行しておらず、緑は主張しない。

## 総括

must-fix は **1 件**。  
1. A-01: real `acquired` 全経路が拒否され、取得 lease まで release される。  
2. 独立した追加 must-fix はなし。`HELD_SELF` の非 release と cleanup 再入は保たれている。  
3. flock 後 snapshot・ticket 公平性・出力契約に新しい排他破れは見つからない。