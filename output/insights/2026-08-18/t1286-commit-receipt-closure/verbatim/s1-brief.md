# 段 1 brief — wave t1286-commit-receipt

作成 2026-08-18 12:52 JST / 親 (Claude) / base main a160f4aa

## scope (裁定 3 + 乗り合い 1)

1. **[T-1286] 要求させる** — 全 `STAGE_COMMIT` producer に、verifier の判定と lock identity へ
   結び付いた**一回限りの** receipt を要求させる。実装しないと: verifier を通っていない variant の
   COMMIT record が WAL へ入り、certified 選択・fitness・材料レポートの母集合が
   「正しさ未確認の試行」を含む (受理集合の拡大)。
2. **[T-1287] 比較する** — 新 certified lock 生成時に、捕捉した enforcement source closure digest を
   **批准済み known-good digest** と比較する。実装しないと: verifier を弱めて commit → その bytes で
   新 lock を作る経路が新しい E1 として受理され、以後の全 certified 成果物の proof chain が
   弱化後の verifier を「正規」として参照する。
3. **[T-762] 塞ぐ** — `ident.py` の第 3 経路 (`env_contract` wrapper を経ない直接呼び) を塞ぐ。
   実装しないと: 承認外 transition へ束縛された activation tuple を持つ `campaign.lock` が
   `admission_status="admitted"` の受理集合へ入る。
4. **[T-1252] 含める (索引 31 が「索引 13 の設計時に対象へ入れること」と明記)** — 認証閉包の対象に
   判定器 module 群を含める。実装しないと: 8c 事前登録の `decider_version` 主張が bytes で
   裏打ちされず、Layer 3 が認証を開いた瞬間に版だけ一致した別 bytes の判定器が通る。

## 確定済みユーザー裁定 (覆さない)

- 3 件とも正しさの門の支配点であり、**防御的堅牢化の見送り方針は適用しない**。実害の観測を待たない。
- **恒真な保証 (謳うだけで発火しない assert) を作らない。負の対照を同じ land で足す。**
- 実装面は Codex author (D95)。親は実装面を直接編集しない。

## 親が実測した事実 (裁定・引数の前提検査、DW-S01)

- **live `campaign.lock` 30 件はすべて v1 (`authority` 無し・legacy key 無し)。** v2 は 0 件。
  → (a) 閉包を広げても既存 lock の bytes を 1 件も無効化しない (`DW-O09` の pin 閉包は
  test 側 `_EXPECTED_ENFORCEMENT_SOURCE_PATHS` とコード側 `CONTRACT_LOADER_RELATIVE_PATHS` の 2 本
  + consumer test 6 file に限る)。(b) **`wal.py` の既存 per-COMMIT contract 検査
  (`_validate_*`, wal.py:1070 近傍) は、v2 でも legacy key でもない lock では手前で `return` し、
  live 30 campaign のどれでも 1 度も発火していない。** 新要求を v2 枝の内側だけに置くと
  恒真になる — これが本 wave 最大の罠である。
- **既存 AST gate (`test_campaign.py:7024`) は `pipeline.evaluate` 内の `wal.log(..., STAGE_COMMIT, ...)`
  ちょうど 2 箇所しか数えない。** 同じ関数内の `qualification_policy.event_sink.emit(..., STAGE_COMMIT, ...)`
  2 箇所 (pipeline.py:1252, 1310) と `guided.py:141` の COMMIT は構文 gate の外にある。
  「支配点が無い」は実在する (機構名でなく性質で検索した結果)。
- **`env_contract` wrapper が足しているもの** (`_load_authority_snapshot`, env_contract.py:631):
  active row ごとの `_verify_entry_calibration`、`entry.contract.contract_sha256 == row.contract_sha256`
  の registry 交差検査、`_VERIFIED_CONTRACT_SHA256S` の更新、fork 安全な lock 下 cache。
  `ident.py:211 / :292` はこの 4 つをすべて素通りする。

## 不変条件 (破ってはいけない)

- 既存の設計テストを反転させない (相手側の専用テスト名は pin)。既存診断の優先順位を奪わない。
- 受理集合を**狭める**方向のみ。v1 lock を持つ live 30 campaign の replay/recovery を壊さない
  — ただし「壊さない」を口実に新要求を v2 枝へ閉じ込めない (上記の恒真の罠)。
- `CONTRACT_LOADER_RELATIVE_PATHS` を伸ばす場合、exact-list pin を同じ land で更新し、
  12→14 を足した先例 (`test_pre_wave_exact_twelve_misses_but_exact_fourteen_rejects_new_enforcement_face`)
  と同型の**負の対照**を新 path について足す。
- receipt は「一回限り」— 同じ receipt を 2 つの COMMIT record が消費できないことを機械で示す。

## 成果物の形

- production: `wal.py` の低層 writer 側 chokepoint、`pipeline.py` / `guided.py` の producer 側 receipt 発行、
  `ident.py` の wrapper 経由化、新 known-good digest 台帳 (append-only) と生成時比較。
- test: 各項の**負の対照** (receipt 無し COMMIT が拒否される / 未批准 digest の新 lock が拒否される /
  wrapper を経ない直接呼びが拒否される / 判定器 bytes 差替が閉包で赤になる)、AST gate の
  producer 全数化 (emit・guided.py を含む)。
- 変異事前登録: 各 gate を無効化する形 + **wave 前の実コードの形** (v2 枝限定 return・
  `wal.log` だけを数える AST gate・直接 `load_activation_state` 呼び) を必ず含める。

## provisional 裁定 (P: 攻撃対象。段 3 で潰してよい)

- **(P1)** T-1286 の chokepoint は `wal.append` (低層 writer) に置き、`log()` 糖衣ではなく
  record 検証側で要求する。producer 側だけの要求は「支配点が無い」を解かない。
- **(P2)** receipt の「一回限り」は WAL 内の消費済み receipt id 集合 (同 attempt 内 replay を含む)
  で表し、新しい外部 state file を作らない。
- **(P3)** T-1287 の known-good digest 台帳は `CONTRACT_LOADER_RELATIVE_PATHS` の
  closure digest 1 本 (path→blob map 全体の canonical hash) を append-only で批准し、
  人間の批准 commit を要件にする。AI が自動で追記できる形にしない。
- **(P4)** T-1252 の「判定器 module 群」の権威ある集合は段 2 で導出する。親の初期候補は
  `s8c_preregistration.py` / `s8c_generation_projection.py` / `s8b_oracle_judge.py`。
  **この 3 本は親の推測であり、段 2 が repo から独立に導出して置き換えること。**
- **(P5)** 4 項は 1 land で閉じる (裁定が同一作業を明記)。ただし T-1252 の閉包拡張だけは
  T-1287 の批准台帳が先に在ることを前提とするため、実装順序は 762 → 1286 → 1287 → 1252。

## 並列分割方針

- 段 5 は 3 単位: A=`ident.py` 経由化 (T-762)、B=COMMIT receipt chokepoint (T-1286)、
  C=批准台帳 + 閉包拡張 (T-1287 + T-1252)。A と B は編集面が重ならない
  (`ident.py` / `env_contract.py` 対 `wal.py` / `pipeline.py` / `guided.py`)。
  C は `campaign_lock.py` / `contract_loader_binding.py` / 新 module で、A・B と衝突しない。
- 段 3 は 2 レンズ (sol / luna)。段 6 は敵対レビュー 2 本 + fix。

## 環境

- 実測・受入とも Pegasus login ノードの worktree 内。焦点走・受入とも
  `python3 tools/run_tests.py` (相対・素の名前ちょうど、余計な flag を足さない)。
- 変異 runner は dispatch recipe (`--force-dispatch` を argv に必ず入れる)。

## 並行 wave との編集面重複 ([T-396])

- `worktree-dev-wave-t396-contract-alignment` は 12:30 JST 時点で working tree に差分ゼロ・
  branch は main と同 tip。**現時点で重複なし。** 段 6 受入直前に再検査する。
