単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- **作業 root (書込み可。編集は所有 path だけ)**: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix2`
- **親の段 4 裁定**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/s4-adjudication.md`
- **配線子 B の報告 (この赤の実測がここにある)**: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-b.md`
- 子 A2 の報告 (ordinal 訂正): `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/out-s5-a2.md`
- 契約の追記訂正 2 の草稿: `/home/SFC/tanab/.claude/jobs/460f7d58/tmp/t1851unitsel/contract-v3.1-erratum-2.md`
- 契約の正本: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 共通規律: `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix2/CLAUDE.md`

# 段 6 fix 2 — adapter が 2 件目以降の clean attempt を予約できない欠陥を閉じる

## 所有 path (編集はこの 2 つだけ)

- `orchestrator/campaign/s8b_attempt_registry.py`
- `orchestrator/tests/test_s8b_attempt_registry.py`

`orchestrator/tests/test_s8b_floor_campaign.py` は**読んで走らせてよいが 1 行も編集しない**。
**docs は編集しない。commit しない。`git add` もしない。**
`orchestrator/campaign/attempt_registry_core.py` は**変更しない** (`aborted=False` keyword と
`OriginSealed(False, ...)` を書くことも禁止。`test_reflux_formal_consumer.py` の AST 走査が拒否する)。

## 実測された赤 (配線子 B が報告)

```
test_s8b_floor_campaign.py::test_v5_prefix_covers_every_consumed_non_competing_session
[s8b-v2-terminal] v2 terminal requires the sealed evidence API
```

1 件目の sealed terminal が記録された後、**2 件目の clean attempt を予約する時点で発火する**。
production campaign は通常複数の clean session を持つので、この状態は完了扱いにできない。

B が静的に示した原因:

- `s8b_attempt_registry.py:2557-2588` — `_evidence_by_digest` を受け取るが**使っていない**。
  `core.reserve_attempt_slot(..., profile=profile)` へ plain v2 profile を渡すため、
  既存の sealed terminal を再度拒否する。
- 同じ形が classification (`:2779-2847`) と observation-start (`:3028-3056`) にもある。
  **reserve だけ直すと次の遷移で再発火する可能性がある** (B の指摘)。

## 直す内容

3 つの遷移 (reserve / classify / observation-start) すべてに、**検証済み evidence profile を伝播する**。

- **`_evidence_by_digest` を実際に使う。** 既存の sealed terminal 証拠を検証済みとして core へ渡す。
- **検証を飛ばす形にしない。** 「sealed evidence API の要求を外す」「型検査を落とす」
  「例外を握って続行する」形は禁止。**受理集合を広げてはならない。**
  改竄・別世代・未検証の evidence が通る形にしたら、それは欠陥である。
- 3 遷移のうち直したものと直していないものを**明示的に区別して報告**する。

## 強度の対照 (新設する)

- **正例**: clean attempt を 2 件以上連続して予約・分類・観測開始できること。
  1 件だけの fixture では今回の欠陥を検出できないので、**必ず 2 件以上**にする。
- **負例 (少なくとも 2 つ)**:
  - 検証されていない evidence (digest 不一致・改竄・別世代) を渡すと拒否されること
  - sealed evidence API を要求する経路で plain profile を渡すと拒否されること
    (= 今回の欠陥そのものを再現する変異を殺す negative control)

負例は**実体を名指しし、依存先を stub しない**。

## 禁止

- 赤を skip・xfail・deselect・assert 緩和・期待値反転で消さない。
  実装が誤りだと判断したら**直さず報告して止まる**。
- 所有外 file を編集しない (`test_s8b_floor_campaign.py` を含む)。
- 既存 test の期待値を変えない。**ただし** 親が段 4 §2 で名指しした ordinal 関連の 3 箇所は
  既に訂正済みである。それ以外は不可。
- `FORMULA_ID`、凍結成果物、`attempt_registry_core.py` に触れない。
- 期待値へ揮発 payload を焼き込まない。
- 出力へ結合文字 U+0300〜U+036F を使わない。

## 検査 (自分で実走する)

**`tools/run_tests.py` は sandbox では rc=16 になるので使わない。** 自走 harness を使う。

```
cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c3-fix2
PYTHONPATH=. python3 orchestrator/tests/test_s8b_attempt_registry.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_terminal_evidence.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py
PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_campaign.py
```

4 file すべての passed/failed の実数を報告する。とくに
`test_v5_prefix_covers_every_consumed_non_competing_session` が緑になったかを明記する。
走らせていないものを緑と書かない。

## 出力形式

```
## 総括
(3-5 行)

## 原因の確定 (file:line、B の静的指摘の検算)

## 直した 3 遷移 (reserve / classify / observation-start それぞれの file:line と、直したか否か)

## 受理集合を広げていないことの論証

## 新設した test (nodeid / 正例は 2 件以上の連続 attempt / 負例 2 種)

## 実走結果 (command と passed/failed の実数)

## 残った懸念
```
