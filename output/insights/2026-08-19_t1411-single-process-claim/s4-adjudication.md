# 段4 裁定 — T-1411 (D553)

親は両レンズの所見を独立に裏取りした。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:637-649`
を直接確認し、実 8c trigger 経路が `run_campaign` を `output_root` 省略・
`declared_use_class="exploration"` で呼ぶことを確認済み (両レンズの中核所見と一致)。

## 採否 (file:line 根拠は敵対相談2レンズの出力を参照、重複引用しない)

### real・in-scope・plan v2 で修正必須

1. **claim_root と実際の campaign output root の不一致** (レンズA/B が独立発見)。
   `env_scope_dir(env_tag, output_root)` は `output_root` 空文字なら常に repo `output/` に
   フォールバックし、`IZANAGI_EXPLORATION_OUTPUT_ROOT` を一切見ない。一方 exploration 経路の
   layout はその環境変数由来の外部 root を使う。claim が保護対象と無関係な場所に置かれるのは
   F322 を形を変えて再生産する (「宣言はあるが実効 consumer がない」→「実効 consumer はあるが
   保護対象と無関係」)。**採用: sink 側で `declared_use_class` に応じて layout と同じ
   root 解決を行い、claim_root をその root 配下に置く。caller 側 (`p3_s4_loop_trigger_gating.py`
   等) の変更は要求しない (sink-local を維持)。**
2. **durable-root policy が既定では外部 exploration root を承認しない** (レンズA/B)。
   `default_durable_root_policy()` は repo `output/` だけを approved root とし、exploration
   root は `_has_git_ancestor` 検査で repo 外を要求されるため構造的に非承認になる。
   **採用: floor 既存の `durable_root_policy` 引数注入パターン (`s8b_floor_campaign.py:5508`
   等) を `run_campaign`/`_authorize_measurement` にも持ち込み、既定 `None` (repo 既定
   policy) を維持しつつテスト・将来 caller が override できる seam を用意する。** 本 wave では
   実 caller への override 配線までは行わない (caller 側ファイルは触らない)。
3. **identity の二重算出による drift リスク** (レンズA)。**採用: `_authorize_measurement` が
   計算した `campaign_identity`/bound cfg を呼出し元へ返し、`run_campaign` 側 (`loop.py:181`)
   はその値を再利用する (再計算しない)。** 二重の source of truth を作らない。

### real・in-scope・実装はミニマムのまま明記で足りる

4. **`required_s=1, safety_margin_s=0` は実効 budget を検査しない** (レンズA/B)。
   D553 の scope は「reservation 検査」であり budget 式の新設は要求していない。loop.py は
   自身の想定実行時間を知らない (floor と異なり duration 入力がない)。**採用: 値は変えず
   「reservation の存在・時刻整合性のみを検査する presence gate であり、campaign 実行時間の
   保護を意味しない」ことを実装コメント 1 行 + worklog に明記する。budget 式の新設は
   scope 外としてユーザーへ裁定パッケージに残す (下記)。**
5. **claim 後の失敗で同一プロセス retry が詰まる** (レンズA/B)。D464 が release/
   stale 回収を持たないことを既に確定済みの leaf 仕様として受理しているため、これは
   T-1411 が新たに導入する欠陥ではない。**採用: claim 取得を `_authorize_measurement` 内で
   実際に必要な直前 (reservation 検査の直後、他の書込みより前) に置くことで window を
   最小化する以上の対応はしない。** retry/recovery policy の新設は scope 外。

### real だが scope外 (裁定パッケージとしてユーザーへ返す、実装しない)

6. **想定 caller (`live.pbs`) が新 gate を positive に一度も通らない** (レンズA/B)。
   [T-1097]/[T-276] の所有範囲。brief 記載どおり fail-closed 停止は D553 の許容結末。
7. **実 Pegasus caller 以外の非 loop sink (`screening_driver.py` 等) は未保護のまま**
   (レンズA)。D553 の scope は明示的に `loop.py` の `_authorize_measurement` に限定される。
8. **`1/0` を超える budget/recheck の導入、exploration root への `durable_root_policy` override
   の実配線** (レンズB総括の「scope外の裁定パッケージ候補」)。

### refuted (対応不要)

- `canonical_preimage` の安定性・private API 境界 — 両レンズとも public かつ
  安定であることを確認、親も `ident.py` 該当箇所を追加確認済み。
- OTHER/linux-baremetal の不変性懸念 — 分岐が `single_process is True` に限定される
  限り無関係。
- `_authorize_measurement` 直接 caller 漏れ — repo 全体で production call 1 箇所
  (loop.py:170) のみ、既存 monkeypatch も `*args/**kwargs` なので影響なし。
- D465 receipt を使わないことの scope 違反 — D553 決定文が明示するのは claim+
  reservation のみ。
- claim 前の fail-closed 順序自体 — 設計は正しい。
- 変異候補の一部 (`protocol_digest`→contract SHA、`acquire_claim`削除) は refuted (健全) —
  ただし `is_symlink()/is_dir()` の `or`→`and` 変異は現行 fixture 案では
  kill できないため、plan v2 で symlink-points-to-directory の fixture に差し替える。

## 次の一手 (段4時点)

plan v2 を codex `--stage plan` (read-only, reasoning=max) で再度起草させ、上記「real・in-scope」
3 点 (root 解決一致・durable_root_policy 引数注入・identity 再計算排除) を file:line で確定させる。
影響ファイルは `loop.py` + `test_campaign.py` を維持できる見込みだが、layout.py 側に小さな
公開 helper を足すかは plan v2 の判断に委ねる (既存 `campaign_layout`/`exploration_campaign_layout`
の挙動を変えない範囲に限定する)。

## plan v2 確定 (2026-08-19)

親が検収し **採用**。A は `layout.py` に `resolve_campaign_output_root(declared_use_class,
output_root)` を新設し `campaign_layout`/`exploration_campaign_layout` 双方がこれを使う
(既存挙動不変の内部委譲)、claim_root もこれを経由して同じ base を使う。B は floor 既存パターン
(`s8b_floor_campaign.py:5599` 等) と同型の `durable_root_policy=None` kwarg を
`run_campaign`/`_authorize_measurement` に追加 (実 caller への配線はしない)。C は
`_authorize_measurement` の返り値を `_AuthorizationResult` (bound_cfg・campaign_identity を含む)
に変え、`run_campaign` 側の二重算出 (`loop.py:180-181`) を削除する。既存 monkeypatch
(`test_campaign.py:8182-8202`) は 2-tuple → 4-field に更新 (shim なし)。統合テスト
(official/exploration 各1本、real leaf 使用、`durable_root_policy` override、
`ident.campaign_id` 呼出し回数 spy) と変異候補7件も plan v2 で file:line 確定済み。
影響ファイル: `layout.py`, `loop.py`, `test_campaign.py` (3 file、当初想定の2 fileから1増、
理由は A の root解決一致に必須)。

## 段6 敵対レビューの追加所見と fix (段4後の追記)

段6 レンズ1 (正確性・退行) が real 2件を発見。1件 (claim 取得前の `campaign_identity` 検証が
layout 側より緩く、孤児 claim が残りうる) は安価に修正可能な実欠陥と判断し fix した
(`layout.validate_campaign_id` を claim 取得前に呼ぶ、commit `e2013e73`)。もう1件
(non-required attestation 経路での `perf_preflight` と identity 計算の実行順変化) は
有効入力での最終値に差がなく certified 成果物への影響を1行で書けないため、DW-G05 に従い
nit として worklog に記録するに留めた。段6 レンズ2 (契約整合性・波及) は real 0件。

段3で二度目の敵対相談は行わない — 段6の敵対レビュー2本 (実装差分そのものを対象、reasoning=max
必須) が安全網として残っているため、これ以上のplan段反復は不釣り合いと判断した。
