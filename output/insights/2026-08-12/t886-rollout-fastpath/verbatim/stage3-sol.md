## 総括

**判定: 現行 plan のまま段 5 へ進むのは BLOCKER。**

主因は 2 点です。

1. plan が発見した「無関係 rollout の未捕捉例外を fast path が迂回する」拡大は、現在の信頼境界では**名前 glob fast path の必然的帰結**です。親 brief の「拡大は重複 session id だけ」は撤回が必要です。
2. fast path を「通常の filesystem failure と `ValidationError` だけ fallback」とすると、`verify_source*=False` で現行が受理する入力を新しく例外終了させる反例があります。fast path 全体を speculative な `except Exception → 現行全走査` にする必要があります。

一方、plan §3 の「旧実装と新実装がともに path を返すなら同じ resolved path」という証明には、安定した filesystem を前提とする限り反例を構成できませんでした。

---

### 1. 無関係 rollout の例外迂回は回避不能

- **深刻度:** BLOCKER（段 4 で認可範囲を明文化するまで）
- **反例または構成手順:**

  ```text
  sessions/
    rollout-0-poison.jsonl
    YYYY/MM/DD/rollout-timestamp-S.jsonl
  ```

  `S` は label `L` の session id、後者は `ROLLOUT_SHA256[L]` と一致する実 bytes とします。`rollout-0-poison.jsonl` には `"session_meta"` と 10,000 桁の JSON 整数を置きます。

  現行全走査は名前順で poison を開き、[_session_meta_rows](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:231) から `ValueError` を伝播します。fast path は pinned candidate だけを開き、内容・SHA が一致して path を返します。

- **判定:** これは回避可能な余分な拡大ではなく、**必然**です。poison の無い世界と、未読 file の bytes だけを poison に変えた世界は fast path から同一に見えます。両者を区別するには全 file を読むか、全 writer がトランザクション的に更新する信頼済み索引／Merkle manifest が必要です。後者は今回の裁定と scope の外です。
- **成果物影響:** 旧実装なら生成されなかった golden/prompt/certified 結果が生成され、レポート・台帳へ到達します。
- **提案する対処:** [brief の P1/P3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/brief.md:22) を「重複だけ」から「非候補 file の重複および未捕捉例外を観測しない一方向拡大」へ修正し、段 4 で明示認可すること。認可できなければ plan §6 どおり実装中止です。SHA は選択候補しか検査しないため、この反例を殺せません。

### 2. speculative fast path 自身が新しい拒否を作る

- **深刻度:** BLOCKER
- **反例または構成手順:**

  test 用 label の pin を、多数の短い JSONL 行からなる大きな正当 rollout の SHA にします。process の address-space 上限を「行単位走査は可能だが、rollout 全体の `read_bytes()` は確保不能」にします。

  ```python
  derive_independent_golden(..., verify_source_sha=False)
  # または
  render_prompt(..., verify_source=False)
  ```

  現行は `_session_meta_rows` の streaming scan 後、外側 SHA を省略して受理します。新 fast path は [_verify_rollout_sha](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:303) の `path.read_bytes()` で `MemoryError` を出します。plan が列挙する `ValidationError` / 通常の filesystem failure だけでは fallback しません。

  また、名前順で先行する poison `p` と、別内容の `ValueError` を出す名前候補 `c` を置くと、旧実装は `p` の例外、新実装は先に probe した `c` の例外を返します。受否は同じでも failure evidence が変わります。

- **成果物影響:** false flag 経路で従来作れた golden/prompt が新たに作れなくなります。後者では失敗理由・traceback が変わります。
- **提案する対処:** fast attempt 全体を speculative にし、**fallback 本体だけは catch の外**へ置いてください。

  ```python
  try:
      # eligibility、separator、escape、rglob、content、resolve、SHA の全て
      ...
      return resolved_candidate
  except Exception:
      pass

  return _find_rollout_full_scan_exact(sessions_root, session_id)
  ```

  `BaseException` は捕捉せず、旧全走査の例外は握り潰さない構造です。これなら `MemoryError`、`KeyError`、候補 parse の `ValueError` も、最終的には旧走査が権威になります。

### 3. 親の corpus 実測は不変条件ではなく、同一 snapshot ですらない

- **深刻度:** MUST-FIX
- **反例または構成手順:** [premise.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/premise.json:1) は 2,941 files、[divergence.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t886-rollout-fastpath/artifacts/divergence.json:1) は 2,945 files です。二つの主張は既に異なる時点の corpus を測っています。また divergence probe の `name_id()` は末尾 5 hyphen segment を UUID とみなすため、非 UUID の将来 label を一般化できません。

  将来 writer ごとの結果は次です。

  | 将来の配置 | fast path |
  |---|---|
  | matching filename、内容は別 id | 内容述語で落ちて全走査 |
  | 内容 id は一致、bytes は pin 不一致 | SHA で落ちて全走査 |
  | exact pinned bytes の rename/copy | SHA は通る。別の非定型名 copy が残れば旧 duplicate 拒否を迂回 |
  | 無関係 file に巨大整数・深すぎる JSON | 候補 SHA では検出不能。所見 1 の拡大 |
  | matching-name copy が 2 本 | `len != 1` で全走査 |

- **成果物影響:** 三段述語が維持される限り、form A の増加だけでは成果物は変わりません。しかし「0/2,945」を仕様として扱うと、将来の述語削除を誤って正当化できます。
- **提案する対処:** 「glob は偽陽性を出さない」を削除し、「当該時点の 5 pin で観測 0」と限定すること。form A は内容述語、内容一致・別 bytes は SHA が殺しますが、exact copy、非候補 duplicate、非候補例外は殺せないと記録してください。

### 4. `thread_id` は UUID 保証されていない

- **深刻度:** MUST-FIX
- **反例または構成手順:** [_thread_id_from_events](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:2482) は `thread_id` が `str` であることしか検査しません。

  ```json
  {"type":"thread.started","thread_id":"../x*?[ ]/e\u0301 "}
  ```

  という event と、その文字列を `session_meta.payload.id` に持つ `rollout-arbitrary.jsonl` を置けば、現行 [_find_rollout 呼出](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/tools/codex_reasoning_ab.py:2879) は内容一致で返せます。共通 helper が separator 拒否や glob 作成を eligibility より先に行う実装なら、新規拒否になります。

- **成果物影響:** replay の rollout、session report、台帳上の `rollout_path` が欠落または別 failure になります。
- **提案する対処:** pin eligibility 不成立なら glob・escape・separator 判定へ一切入らず旧全走査へ直行させること。pin 無しで `* ? [ ] / ..`、大文字、NFC/NFD、末尾空白を使う回帰を追加してください。

  なお、plan を厳密に実装すれば path traversal 反例は構成できません。`/` は fallback、`..` 単独は basename 内の literal であり、path join されません。symlink による root 外 resolve は現行にも存在します。

### 5. 複数 glob 候補テストは M05 を殺せない

- **深刻度:** MUST-FIX
- **反例または構成手順:** plan の `...[multiple]` は「2 候補のうち一方だけ内容一致、返り path を確認」です。

  - mutant が内容一致候補を先頭に取れば、その候補を返して期待値と一致します。
  - 不一致候補を先頭に取れば fallback して同じ期待値を返します。

  したがって `len(candidates) == 1` を `>= 1` にしても、どちらの順序でも通り得ます。

- **成果物影響:** 複数の matching-name file があるのに先頭を受理する実装を、変異 matrix が誤って保護済みと認定します。
- **提案する対処:** matching-name file を 2 本とも**同一の pinned bytes**にしてください。正実装は full scan で `RC_SESSION=21`、M05 はどちらを選んでも SHA が通って受理するため、結果だけで確実に殺せます。

### 6. SHA 内部照合テストが呼出回数に依存している

- **深刻度:** MUST-FIX
- **反例または構成手順:** `test_find_rollout_pinned_sha_mismatch_falls_back_to_full_scan` は、SHA 不一致候補が内容検査を 2 回受けることを spy します。SHA を削除した実装でも返り path 自体は同じで、kill は `_session_meta_rows` の呼出回数という副作用に依存します。false flag の wiring tests は `_find_rollout` 自体を sentinel 化するため、実 SHA を通しません。
- **成果物影響:** 内部 SHA が無い実装で、wrong bytes が `verify_source*=False` から golden/prompt に入る余地を残します。
- **提案する対処:** 結果で区別できる fixture にしてください。

  ```text
  c = matching-name、内容一致、SHA 不一致
  d = nonmatching-name、内容一致
  ```

  正実装は SHA mismatch 後の全走査で duplicate `RC_SESSION=21`。M08 は `c` を直接受理、M09 は SHA mismatch を直接伝播します。これで同じテストが両変異を意味的に殺します。sentinel wiring tests は「false でも label を渡す」証明として残して構いませんが、P2 の唯一の証拠にはしないでください。

### 7. F90 型の階層 coverage が skip 可能な実 corpus test に依存する

- **深刻度:** MUST-FIX
- **反例または構成手順:** 実装を `rglob` から非再帰 `glob`、または `YYYY/MM/DD` 固定 pattern に変えます。tmp の pinned candidate が root 直下なら fast tests は通り、実 corpus test は `_HISTORICAL_SESSIONS` 不在時に skip できます。これは [F90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/docs/failures.md:2669) と同型です。
- **成果物影響:** 現 layout では緑でも、archive 階層変更後に全走査へ退行し、fixture 構築費が再び履歴比例になります。
- **提案する対処:** tmp candidate を現在と異なる任意深度、例えば `root/a/b/c/d/e/` に置き、別階層に同内容の非定型名 duplicate を置いてください。正しい `rglob` は pinned candidate を短絡し、固定深度／非再帰 mutant は fallback して duplicate 拒否になります。skip 不能な outcome test になります。

  production と fast path はともに `Path.rglob` なので、directory symlink を再帰しない点は本 wave の差ではありません。現状の `YYYY/MM/DD` への暗黙依存も実装案自体にはありません。

### 8. 変異の帰属が成立しないもの

- **深刻度:** MUST-FIX
- **反例または構成手順:**

  - **M07:** 既存 `test_find_rollout_session_meta_encoding_and_payload_field_equivalence` が先に殺します。新 fast-path test の検出力の証拠ではありません。
  - **M12:** 既存 `test_find_rollout_session_meta_scanner_propagates_value_error` が先に殺します。同様です。
  - **M04:** 「pin 存在」と「label/id 対応」を一変異に束ねています。label/id equality だけを削除しても、普通の mismatched label fixture では後段 SHA mismatch が fallback を起こし、変異が観測不能です。
  - 所見 2 の `except Exception → fallback` を採ると、「SHA key membership 削除」は `KeyError` が fallback されるだけなので意味的に冗長になり得ます。

- **成果物影響:** mutation matrix が、fast path 固有の境界を検査していない変異を `KILLED` として計上します。
- **提案する対処:** M04 を分割してください。label/id equality 変異には、label A の SHA を session B の named candidate bytes に意図的に cross-wire し、B に内容 duplicate を置く fixture が必要です。正実装は equality gate で full-scan reject、mutant は SHA を通して受理します。M07/M12 は「既存 gate による kill」と明記し、新規テストの効力に数えないでください。

### 9. fallback は構成次第でほぼ 2 倍の directory walk になる

- **深刻度:** NIT
- **反例または構成手順:** 大量の空 directory と、非定型名の target rollout 1 本を置きます。eligible label の narrow glob は 0 件なので、全 directory を narrow `rglob`、続いて broad `rglob` で再走査します。既存は broad walk 1 回です。
- **成果物影響:** 結果・RC は変わりませんが、fallback-heavy な synthetic corpus では lookup 時間がほぼ 2 倍になります。実 corpus の 0.02 秒対 4.4 秒では影響は小さいです。
- **提案する対処:** これは index 無し fast path の自然な費用として記録し、fallback 性能を成功時 speedup と混同しないこと。正しさのために fallback を候補集合だけへ狭めてはいけません。

## 構成できなかった攻撃

### 異なる path を双方が正常返却する反例

- **深刻度:** NIT（反例なし）
- **攻撃結果:** narrow 集合 `G` は broad 集合 `U` の部分集合です。fast return した候補 `c` は旧内容述語を満たすため、旧 matches に必ず `c.resolve()` が入ります。旧実装も正常返却するなら matches は 1 要素なので、返却 path は同じです。
- **`resolve()` / sort / 複数 row:** `resolve()` の位置は内容一致直後で旧実装と同じです。narrow 候補は 1 件を要求するため narrow sort の有無は結果に影響しません。fallback の broad sort は例外順のため維持が必要です。同一 file 内で複数 row が真でも、旧実装は `break` により path を 1 回だけ追加し、boolean helper と一致します。
- **成果物影響:** stable filesystem では golden/prompt bytes の返り path 差は構成不能です。
- **提案する対処:** plan §3 のこの限定証明は維持してよいです。ただし受理集合・例外全体の等価性証明へ一般化しないでください。

### F141 型の非決定選択

- **深刻度:** NIT（正しさ反例なし）
- **攻撃結果:** [F141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t886-rollout-fastpath/docs/failures.md:3835) の `next(glob(...))` と異なり、今回は runtime で候補数 1 を要求し、2 本なら deterministic な全走査へ戻ります。非定型名の duplicate があっても選択の錨は列挙順でなく SHA bytes です。
- **成果物影響:** 2 本目の matching-name file は性能退行を起こしますが、非決定な certified bytes は作りません。
- **提案する対処:** 「全 2,945 file で名前重複 0」は性能前提にだけ使い、正しさ根拠には数えないこと。

静的検証のみで、書込み・pytest 実走・緑の主張は行っていません。