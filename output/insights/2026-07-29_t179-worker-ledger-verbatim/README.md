# [T-179] worker 資源台帳 dev-wave 逐語・変異台帳 (凍結、2026-07-29)

親の裁定要約は `docs/worklog.md` 2026-07-29 (62)。実装 commit は
`72f8858f0634f123530e23a4ebe4039e86f5bc2a`。

| ファイル | 役 | sha256 (凍結時) |
|---|---|---|
| `brief.md` | 段1 brief (親) | `6acb1bd50022ec1039a2c556da882d4d75219645c8c1392d8ff892dfee33998b` |
| `adjudication.md` | 段4 裁定・変異事前登録 (親) | `83f93f9ff024b566e8a88a3abbe54ee2a2648206ecb9542eb3866554774c82b6` |
| `author.md` | 段5 実装報告 | `676c7c1109db036059f2db602b6627bd723049d769e39471e13eb3b100d24749` |
| `review-a.md` | 段6 敵対レビュー A (数値の帰属レンズ) | `0717426190014b64a1fe354cc7c579e31e1ea6798c42090851851b6158e0b266` |
| `review-b.md` | 段6 敵対レビュー B (gate 実効性レンズ) | `31e2ab06378311f4469b90cb4267292773d579a11cb3c3369ec99d4a9f8917f5` |
| `adjudication-s6.md` | 段6 裁定・変異再照準 (親) | `b8bf7c9c392ef9125dcebe130da353296926ae2c0c862bf38800601373648947` |
| `fix1.md` | 段6 fix 1 報告 (F-1〜F-12) | `a16c09a72330f985219f58fb7fc0b4dd108dc50860e04c6da511c9833795a5d6` |
| `fix2.md` | 段6 fix 2 報告 (stage 意味論の回帰是正) | `24d6cbdc520ed975759f4993980a35cbc21e6e875295aea548a9a48c737594df` |
| `focus.md` | 段6 焦点再レビュー (NO-GO) | `a1fc28cc882c8e4acf7d4581410661d6f3529f1f769441dad27da365f097c39c` |
| `fix3.md` | 段6 fix 3 報告 (焦点レビュー 5 件) | `f3157649651befec870ee92718f6f8a7890d9fa458c073bee2da69885147c805` |
| `mutation-ledger-raw.json` | 統合 commit 後の変異 11 本の生結果 | `15df5afb74f7ebcb84253ffee9a1f19e4db8a1a3a5440766f438e4f4a88aa263` |

相談・レビュー 3 本は `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`、
実装・fix 4 本は同 `reasoning="high"`・`-s workspace-write`。全成果物は
`tools/check_codex_output.py` で機械検収済み (rc=0)。
read-only review は静的判定であり、テスト実測の正本は親の worklog と本台帳である。

段 2 (codex plan 起草) と段 3 (敵対相談) は省いた。理由は `brief.md`「wave path」に記す
(設計択一を実ログの直接実測で閉じたため)。段 6 の敵対レビュー 2 本は省いていない。

## 本 wave が再構成した凍結値

対象 = `session_meta.cwd` に `dev-wave-t153e-t15423` を含む rollout (T-153(e)/T-154 の worker)。

```
sessions=10  model_calls=434  cli_reported=2,757,982
per_turn_sum=2,765,553  cumulative_minus_per_turn=-7,571 (focus2 の 1 件のみ)
```

| stage | sessions | model_calls | cli_reported |
|---|---|---|---|
| plan | 1 | 39 | 224,150 |
| consult | 2 | 62 | 392,185 |
| author | 1 | 47 | 171,736 |
| review | 2 | 87 | 544,553 |
| fix | 2 | 100 | 605,734 |
| focus | 2 | 99 | 819,624 |

**session_id → stage の独立 oracle** (親が rollout の raw `user_message` 先頭から導出。
台帳の規則表とは独立に作り、逐件で照合した。aggregate 一致は循環論法なので根拠にしない):

| session_id | prompt 先頭の役割 | stage |
|---|---|---|
| `019fac45-a834-7161-9528-c717f2995940` | 段2 read-only Codex planner | plan |
| `019fac54-85a7-7d43-8431-e2e6a3c5037b` | 段3 adversarial consultant A | consult |
| `019fac54-85dc-7582-9973-fe0e7388798b` | 段3 adversarial consultant B | consult |
| `019fac6b-4f74-7a03-aa4d-8a9de22b352c` | 段5 Codex implementation worker (role=author) | author |
| `019fac79-f65b-7c20-b6b5-6be058e4a7d5` | 段6 adversarial reviewer A | review |
| `019fac79-f6b3-70b0-bf59-05b8fda911d1` | 段6 adversarial reviewer B | review |
| `019fac91-8cde-7f73-bce1-77a9d63b4269` | 段6 Codex fix worker | fix |
| `019faca2-6e1f-7601-bfc7-be27edcfb4ba` | 段6 fix後 focused reviewer | focus |
| `019facb2-7ddb-7102-814d-eeddcb1102ed` | 段6 fix2 implementation author | fix |
| `019facbe-9584-7642-aa30-37f1c77e6c5f` | 段6 fix2後 focused adversarial reviewer | focus |

**worklog (59) との不一致**: 「Codex 9 job (planner 1 / consult 2 / author・fix 3 / review 3)」
に対し実測は 10 session (planner 1 / consult 2 / author+fix 3 / review+focus 4)。
不一致の実体は **review bucket の 3 対 4** (focus2 の 1 件が落ちていた) と総数 9 対 10。
台帳はこの 2 件を名指しして `--strict` で rc=2 を返す。

短縮 session_id は使えない — 先頭 8 hex が実データで 2 組衝突する (`019fac54` / `019fac79`)。

## 用語の訂正 (本 wave で確定)

- worklog (61) の「434 model turns」は、正確には **`token_count` event (`info` 非 null) の件数**
  である。台帳ではこれを `model_calls` と呼ぶ。同 session の `turn_context` は 1〜2 個しかなく、
  turn 数の別定義とは一致しない。以後 `model_calls` を使う。
- 「CLI reported tokens」= 各 session の**最後の** `total_token_usage` に対する
  `input_tokens - cached_input_tokens + output_tokens` の総和。
  per-turn `last_token_usage` の和 (2,765,553) は**正本ではない**。
- 親が段 5 の入力資料 (`rollout-schema.md`) に「`info` が `null` の `token_count` 行がありうる」と
  書いたのは実測前の推測だった。実測 (626 rollout / 56,336 usage object) では
  `info: null` は **0 件**、`reasoning_output_tokens` 欠落も **0 件**、負値も **0 件**である。
  台帳は将来形への保険としてこれらを受理するが、現コーパスに存在するとは主張しない。

## 変異台帳 (統合 commit `72f8858` 後に本走、DW-O19)

手順: 一意 anchor assert → 一時変異 → `pytest -rf` → `git checkout --` 復元 →
commit 済み内容との一致 assert。単一プロセス逐次、`flock` 単一走行 guard (DW-M05)。
harness は repo 外 (job tmp) に置き、repo を汚さない。

**kill 判定は rc の赤ではなく、事前登録した失敗 node が出たかで行う (DW-M03)。**

| ID | 攻撃対象 | 判定 |
|---|---|---|
| M1 | token 正本を per-turn 和へすり替え | KILLED |
| M2' | 重複 session_id 検出の無効化 | KILLED |
| M3 | `unclassified` を fail-open へ | KILLED |
| M4 | 成果物 validator を常に合格へ | KILLED |
| M5' | `task_complete` 欠落を completed へ | KILLED |
| M6 | worklog 突合の不一致を握りつぶす | KILLED |
| M8 | **正例**: 健全 wave にも strict 非 0 (過剰拒否) | KILLED |
| M9 | usage の型異常・欠損・負値 gate の無効化 | KILLED |
| M10 | 選択 0 件でも strict 緑 (fail-open) | KILLED |
| M11 | stage 規則を prompt 全文照合へ戻す | KILLED |

**kill 計上 = 10/10 KILLED。SURVIVED・mask・erratum なし。**

`M7` (retry の prompt 正規化を外す) は赤にはなるが受理集合も rc も変えないため、
`DW-M08` に従い **diagnostic sensitivity pin** として kill 計上から**外した**。

### 段 4 登録からの改訂 (事実として記録する)

段 4 では `M2 = session_id を先頭 8 文字へ短縮` を登録したが、段 6 レビュー B の指摘どおり
record が list のため登録した「session 融合」は起きず、healthy fixture の ID 群と連鎖して
赤理由が一意にならなかった。実効 gate は**重複検出**なので `M2'` へ再照準した (`DW-M02`)。
`M7` の再分類、`M9`〜`M11` の新規登録も段 6 の裁定で行った。改訂の理由は `adjudication-s6.md`。

## scope 外と裁定した real 所見 (次タスクへ)

- cwd 部分一致では wave の受理集合を固定できない (path 再利用・接尾辞衝突)。
  恒久解は launcher が wave manifest / session allowlist を発行すること = **[T-180]**。
  本 wave は対象 10 件の session_id を上表に凍結して監査可能にした。
- prompt hash は retry lineage ではない (同文 = retry とは限らない)。因果的な retry 同定は
  launcher receipt が要る = **[T-183]**。台帳は「同一 wave 内の同文 group」とだけ名乗る。
- library import 時の自己 pycache、worklog 工数行 grammar の一般化 = backlog。
