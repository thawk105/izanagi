# 段 4 裁定 — [T-2298][T-2273] (2026-09-04 22:5x JST、親)

## 前提の再裁定 (P1〜P5)

- (P1) 引数「`real_repo_fixture_lock` を使う」→ **refuted、不採用**。段 2 単位 E と lens A が独立に同結論:
  同 fixture は `parent` / `ccbench` の git common-dir に束縛された別資源。流用は資源の取り違え。
  **採用: fixture 自前の `fixture.lock` を残し mode を変える。**
- (P2) 「258.1 秒の直列」→ **refuted (台帳値)**。当日 junit の 17 consumer 合計は 84.5 秒 (lens A が 82 → 84.5 へ訂正、採用)。
  M-A timeline では consumer の setup 合計 ≈ 90 秒。lens A の指摘どおり合計は critical path の wall ではない
  (待ちが重なる)。T-2298 の効果は D1620 の測定面 (最遅 shard wall) では小さく、worker-time の削減が主。
  **scope は変えない (依頼が命じた本体)。効果の主張は「鎖の解消」に留め、wall の短縮量は受入で実測する。**
- (P3) D1593 鎖 1 (real-repo group 303.7 秒) → **現物と食い違う (suffix strip、2026-08-26)**。lens B の点検待ち。
  scope 外。裁定パッケージへ (D1618 / T-2297 の実装対象が現物と食い違う)。
- (P4) shard-0 の wall − 占有 (95〜207 秒) の正体 → M-A (全 suite 非 shard) では隠れ待ち 0。M-C (shard-0 file 集合) で再測。
  受入形固有なら、report.json に session timeline を足す提案を裁定パッケージへ (新規 field なので scope 外)。
- (P5) t080 e2e の中身は filesystem + git → M-B の phase 内訳で確定する。

## 段 3 所見の裁定

### lens A (正しさ境界)
- must-fix 1 (実 fixture の lock 保持配線が未検査) → **real、採用**。実 fixture scope を enter した状態で別 fd の
  `LOCK_EX|LOCK_NB` が EWOULDBLOCK になる検査 + AST で「共通 scope の yield が lock context の内側」を固定。
  変異 (f) 「lock 解放後に yield」を事前登録に追加。
- must-fix 2 (seed 完了印が非 transactional) → **real、採用 (最小形)**。metadata は同 dir の temp へ書き fsync 後
  `os.replace`。EX 取得後に metadata 不在かつ `shared/"evidence"` が残っていれば残骸として消してから seed。
  変異 (g) 「temp+replace を直接 write_bytes に戻す」は殺す検査を用意できれば登録、できなければ登録しない (DW-M01)。
- nit SIGKILL 境界 → real、既知限界、明記のみ (現行から不変)。
- nit producer writer → refuted (親も現物確認済み、`campaign_lock` は terminal record 不在時のみ)。
- nit AST 閉包の恒真/恒偽条件 → 採用 (期待 map 明示列挙、両 fixture 名を起点、`_publish` 返値は非 taint、代入先名へ fixed-point 伝播)。
- nit AST は直接 mutation 限定 → 検査名とコメントに明記 (採用)。
- nit node id 不変・新規 6 node の波及 → 採用: 実装後に collect-only nodeid 集合の差 (新規 node だけ) と 17 node 焦点走を照合。
- 親 brief 「marker」表記 → B2 (別 fixture) に統一 (採用)。

### lens B (整合・実効性)
- must-fix 1 (鎖 1 の反証は現行 run について成立、「裁定時点で既に不在」は commit 束縛が要る) → **real、採用**。
  親が追加で裏取り: strip commit `5ac638955` (2026-08-26 13:19 JST) は D1593 を起草した wave の tested_tip
  `62531b9a` の祖先 (`git merge-base --is-ancestor` rc=0)。D1593 の 303.7 秒は台帳 (ledger) の合計値であり
  group 直列の実走測定ではない (D1593 本文「実測で鎖 1 が 303.7 秒」は台帳集計)。裁定パッケージでは
  「D1593 の起草時点のコードに strip は既に在り、303.7 秒は台帳合計」と書き、「過去の実測が虚偽」とは書かない。
- must-fix 2 (junit testsuite wall は lock 待ちを含む、testcase / occupancy は含まない) → **real、採用**。表現を直す。
  残差 179 秒は「collection + worker 起動終了 + protocol 外 lock 待ち + session cleanup の混合」と書く。
- must-fix 3 (T-2298 単独で 21:16 走を 5 分へ入れることは数値上不可、consumer 集合は plan の表が正) → **real、採用**。
  17 consumer = 段 2 の表 (M09 は含まず、driver 不一致と non-guarantees を含む)。junit 合計 84.9 秒。
  効果の主張は worker-time と鎖の解消に限定し、wall への寄与は受入で実測して書く。
- must-fix 4 (T-2297 は runtime 効果あり、D1618 の明示契約 (ItemRecord affinity 属性、payload/parser、component /
  closure gate、g6 の期待値) は未了) → **real、採用**。裁定パッケージにこの区別を書く。「実装済み」とは書かない。
- must-fix 5 (shard-0 固有の因果は未証明、関連のみ) → **real、採用**。host / 時刻の交絡を切っていない。M-C を
  1 点追加するが、それでも受入形の残差 (collection・起動・cleanup) の内訳は timeline field が無い限り確定しない。
  裁定パッケージへ「report.json に session timeline (collection 終了・各 worker の最初/最後の test 時刻・
  lock 取得/解放時刻) を足す」を提案として送る (新規 field、scope 外)。
- nit: 38 worker (26+ ではない)、gw27 の 2 item = t080 は未証明 (node→worker 対応は記録されない)、
  real-repo 100 node の phase 合計 604.5 秒は worker-time → すべて採用して表現を直す。

## 段 3 の総合
段 2 plan は 2 つの must-fix (lens A) を足せば author-ready。lens B の 5 件は記録・裁定パッケージの表現に効き、
実装面には効かない。scope は依頼どおり (1) T-2298 の実装 + (2) 測定 (M-A/M-B/M-C) に確定。

## plan v2 (author へ渡す確定事項)

1. `test_p3_b4_raw_record_producer.py`: `certified_evidence` (:1178-1243) を 3 層 (lock scope / evidence scope / 2 fixture) に分ける。
   lock 順序: fd open → metadata 不在なら EX → 再確認 → (残骸掃除) → seed → metadata を temp+fsync+replace → UN →
   reader SH / writer EX → metadata 読み → patch → yield → finally unlock → close。
2. M17 / M18 の引数を `certified_evidence_writer` へ。assertion は不変。
3. 検査 (同 file、17 consumer を増やさない): 二 reader 正例、seeded reader no-EX、reader 保持中 writer NB 負例、
   writer 保持中 reader NB 負例、seed double-check 競合、**実 fixture scope 保持中の別 fd NB 負例**、
   **AST: yield が lock context 内**、writer 閉包 AST (期待 map 明示、両 fixture 名起点、直接 mutation 限定を明記)。
4. `pytest.ini` / `conftest.py` は変更しない。

## 段 6 レビューの裁定 (2026-09-04 23:2x)

- MF-1 (lens C・D 独立に同一、real、採用): 実 fixture scope の検査が両 mode に `LOCK_EX|LOCK_NB` を当てるため、
  共通 scope が `access_mode` を定数化する退行 (全 reader 再直列化 / writer 非排他) が緑で通る。
  fix: read mode では競合 `LOCK_SH|LOCK_NB` 成功かつ `LOCK_EX|LOCK_NB` 失敗、write mode では `LOCK_SH|LOCK_NB` 失敗を
  実 scope で検査。AST で共通 scope が `_certified_evidence_lock_scope(..., access_mode=access_mode)` と転送すること、
  両 wrapper fixture の yield が `with _certified_evidence_fixture_scope(...)` の内側にあることを固定。
- MF-2 (lens C、real、採用): atomic metadata 検査は helper 直呼びだけで、production seed (共通 scope 内 `seed()`) が
  helper を経由する call edge と、`os.replace` の source != target・temp 名を固定していない。
  fix: AST で `seed` 内の metadata 公開が `_write_certified_evidence_metadata` 経由だけであり `write_bytes` 直書きが
  無いことを固定。既存 atomic 検査に「replace の source が metadata_path と異なり temp 名 prefix を持つ」assertion を足す。
- nit (lens C): `os.fdopen` 例外時の temp fd leak → 記録のみ (通常条件で起きない、防御的堅牢化は既定見送り)。
- nit (lens C): M18 の最初の共有変異が `try` の外 → 既存 consumer 本文、本 wave の scope 外。次の一手に記録。
- nit (lens C): taint が `joinpath` / `/` / `resolve` を追わない → 現 15 consumer に該当なし。docstring の限定に含まれる。記録のみ。
- lens D nit 4 件 (閉包 AST・F649・揮発・メタテスト) はすべて refuted (現物確認済み)。台帳・焦点走の波及は real・修正不要。
- 変異事前登録へ追加: h = 共通 scope の `access_mode=access_mode` を `"write"` 定数化 → MF-1 の実 scope 検査 (read mode) が殺す。
  g2 = production seed の公開を `write_bytes` 直書きへ → MF-2 の call-edge AST が殺す。
  lens C の kill 表 (b / e / f は帰属非一意、c / c2 は alias 形なら closure 単一) を probe で実測する。

## 焦点再レビュー (lens E) の裁定 (2026-09-04 23:5x)

- MF-1 closed (現物判定)。MF-2 partial: MF-2A (seed 内の直接公開禁止が receiver の path 構文に依存し、helper を残して
  `joinpath(...).write_bytes` を足す形が通る)、MF-2B (fsync が write 後である順序を観測していない) → **両方 real、採用。**
  fix 2 巡目 (最終) を 1 本投入。以後は fix を重ねず、親が変異 i (helper を残した直接公開) / j (fsync を write 前へ) で
  裏取りして閉じる (DW-O16 の上限)。
- nit: h の帰属は「実 scope 検査 (主) + mode 転送 AST (冗長)」と明記する。

## 変異事前登録 (DW-M01)

| # | 変異 | 殺す検査 |
|---|---|---|
| a | writer mode を LOCK_SH | writer 保持中 reader NB 負例 |
| a2 | writer wrapper が "read" を渡す | wrapper-mode AST |
| b | reader が本体 lock を取らない | reader 保持中 writer NB 負例 (+ seeded no-EX 検査。帰属非一意は明記) |
| c | M17 の writer 宣言を外す | writer 閉包 AST |
| c2 | M18 の writer 宣言を外す | writer 閉包 AST |
| d | EX 後の double-check を外す | seed double-check 競合検査 |
| e | reader を LOCK_EX のまま (旧挙動) | 二 reader 正例 (+ no-EX 検査) |
| f | lock を解放してから yield | 実 fixture scope 保持中の NB 負例 + yield 位置 AST |
| g | metadata を temp+replace でなく直接 write | (殺す検査が単一理由で作れる場合のみ登録) |

baseline: 変異前に対象 file の焦点走が緑であること。実走は計算ノード (dispatch)。
