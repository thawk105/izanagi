# T-1411 段1 brief — loop.py sink-local single_process 強制 (D553)

wave: `dev-wave-t1411-single-process-claim` / 2026-08-19 / branch
`worktree-dev-wave-t1411-single-process-claim` / 基準 commit `752773cdab05b1f316138d903a0b4fa1f5aabc84`

## scope

`orchestrator/campaign/loop.py` の `_authorize_measurement` (現状 loop.py:92-120) に、
`contract.isolation_policy.single_process is True` のときだけ発火する **claim 取得**
(`orchestrator/campaign/campaign_claim.py` の `acquire_claim`/`ClaimRecord`) + **reservation 検査**
(`orchestrator/campaign/reservation.py` の `read_binding`/`check_reservation`) を sink-local に追加する。
両 leaf は [T-1167]/[T-330] で 2026-08-16 に landed 済み (commit `6eb77ef9`) — 新規 leaf は作らない。

**scope 外:** tracked wrapper 新設 (D125 決定6・D108 決定2〜5 の campaign task 凍結境界)。
`allow_resume=False` の拒否 (D553 決定文が明記するのは「claim 取得・reservation 検査」の 2 つのみ —
D419 決定(3) が列挙した 3 項目のうち残り 1 つは対象外。段3 で D553 決定文の文言を再確認させる)。
`campaign_claim.py`/`reservation.py` 自体の既知の限定 (claim 排他が protocol 単位でなく
run-identity 単位、reservation が caller 自己申告で host/script/nonce 未照合) の是正 — D464/D465 が
生きたまま受理した設計であり、本 wave が新たに広げる欠陥ではない。

## 確定済みユーザー裁定

D553 (`docs/decisions.md:22565-22588`、2026-08-19)。caller は当面 repo 外 untracked
`dev-wave-jobs/2026-08-15_t1097-s8c-live-abc/live/live.pbs` のまま。2026-08-03 裁定の
「発火 caller を持たない部分実装は採らない」禁止は本件に限り明示解除済み — 再度問い直さない。
一次資料: `docs/failures.md:8415-8434` (F322)、`output/insights/2026-08-16_t330-scr-single-process/`
(s4-adjudication.md が「(c)→(a)」の順で (a) を再裁定へ返し、D553 が (a) を採用した)。

## 不変条件

- `contract.isolation_policy.single_process is False` (OTHER/linux-baremetal、
  `env_contract.py:292-310`) の挙動を 1 bit も変えない。
- `_authorize_measurement` の既存原則「明示 contract と required attestation を最初の書込みより
  前に検査する」(loop.py:98 docstring) を保つ — claim 取得もその「最初の書込み」に含める。
- `campaign_claim`/`reservation` の semantics は変更せず呼ぶだけ。
- 失敗は fail-closed (例外伝播)。握りつぶし・fallback 実装をしない。

## (P1) 未決の設計選択 — 段2プランが file:line で確定する

`_authorize_measurement` の現呼出し (`loop.py:170`) は `cid`/`layout` の計算 (`loop.py:181-182`) より
**前**にあり、floor 実装の `claim_root = out_root / "claims"` パターン (`s8b_floor_campaign.py:5891`
周辺) をそのまま持ち込めない。候補: (a) `layout.env_scope_dir(env_tag, output_root)`
(`layout.py:490-493`、campaign 非依存で `env_tag`/`output_root` は `run_campaign` の生パラメータ
= 呼出し前から入手可) を claim_root の base にする。(b) `_authorize_measurement` の呼出し自体を
`cid` 確定後へ後ろ倒しする (attestation の「最初の書込み前」原則との整合を要検証)。
`protocol_digest` (64桁小文字hex 必須、`campaign_claim.py:54-59`) の元ネタも同様に未決 —
`ident.campaign_id` 相当の安定識別子から導出するか、bind 前の `cfg` から導出するか。
claim_root の事前 provisioning 要否 (floor は provisioning 済み前提、is_symlink/is_dir で拒否) も
loop.py 側でどちらの設計にするか要判断。

## (P2) 実測事実 — blocker ではないが worklog に記録する

未追跡 `live.pbs` を直接読了 (6999 bytes、2026-08-19)。`IZANAGI_RESERVATION_*` 8 変数・
`PBS_JOBID` を使った claim/reservation 供給を一切行わず、claims/ の事前 provisioning もしていない
(`IZANAGI_EXPLORATION_OUTPUT_ROOT` のみ export)。したがって実装後、[T-1097] の transport 欠陥が
直っても本 caller は新 gate で fail-closed になる見込み — D553 の意図どおりであり本 wave の
blocker ではない ([T-1097]/[T-276] の所有範囲)。

## 成果物影響 (DW-G05)

実装しない場合: [T-1097] 解消後、single_process 未検査の exploratory WAL・report・binary SHA が
受理され続ける (F322、恒真ゲート)。certified 選択・材料レポート・proof chain・凍結 bytes には
現時点でも将来的にも影響しない (Pegasus tagged exploratory 経路限定)。
実装する場合: 同じく certified 側は不変。既存の real-path Pegasus contract テスト
(`_authorize_measurement` を monkeypatch しないもの) は新しい claim/reservation 前提を満たす
fixture 拡張が必要になる (`orchestrator/tests/test_campaign.py` に env_tag="pegasus" で
`_authorize_measurement` 非 monkeypatch の呼出しがあれば要修正 — 段2プランで洗い出す)。

## 分割方針

単一実装単位 (`loop.py` 本体 + 関連テスト、所有ファイルが競合しないため分割不要)。
Codex author = D95。段6 レビュー2本必須 (受理集合が変わるため軽量版の省略対象外、DW-C00)。
変異 matrix 必須 (DW-M01)。
