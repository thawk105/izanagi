---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t940-ledger-count
seq: 1
title: 既知違反台帳の件数 literal 固定を外す (test-only、変異 9/9 一致、branch worktree-dev-wave-t940-ledger-count)
---

## 本文

ユーザー裁定 (2026-08-12 第 6 束、authority: user)「T-940 = 件数 literal 固定のみ外す (内容完全
一致は保つ、敵対検証を受入条件)」を執行した。編集面は
`orchestrator/tests/test_check_ai_provenance.py` のみで、production
(`tools/check_ai_provenance.py`) と docs は 1 bit も変えていない。設計判断は {{D:ledger-count-dynamic}}。

**起票時に見えていなかった第 2 の件数 literal を実測で見つけた。** 段 1 で台帳へ 39 件目を実編集で
足して計算ノードで全走したところ (request 908040.nqsv)、赤は 2 node だった — 起票が名指す
`test_known_violation_ledger_is_exactly_thirty_eight_literal_entries` (`len(...) == 38`) と、
`test_production_registry_notes_satisfy_descriptive_contract` (`len(registry) == 38`)。後者を外さなければ
裁定の目的 (承認のたびに受入が止まる) は解消しない。裁定文言は機構を指し行を指さないと読み、
scope に含めた。tree は実測後に復元済み (blob = HEAD と一致)。

**段 4 の裁定を段 6 で自ら覆した。** 段 2 プランと段 3 レンズ A は「`observed == expected` の
tuple 比較が長さを厳密に含意するので `assert len(KNOWN_PROVENANCE_VIOLATIONS) == 38` は削除して
よい」と結論し、親も段 4 でそれを採った。段 6 の敵対レビュー A がこれを反証した — 台帳を `tuple`
派生型にし、`len()` は正直に 39 を返しつつ `__iter__` が literal test に対してだけ未承認の 1 件を
隠すと、削除後は内容完全一致・SHA 一意性・registry の件数と値 tuple・実在 35 件検査が**すべて緑**に
なる。含意は `observed` が台帳の反復から作られることに依存しており、反復が呼び手で件数を変える容器
では成立しない。**これは既存の穴ではなく本 wave の削除が開けた穴**で、受理集合を裁定の許す範囲
(承認済み entry の件数変化) を超えて広げるため fix した。fix は件数 literal を戻さずに済み、
`== len(expected)` という動的な形で検出力を wave 前と入力ごとに同一へ戻した。

レビュー A が併せて提案した exact-type 固定 (`type(...) is tuple` と全 field の型検査) は
**不採用**。fix が同じ攻撃を型検査なしで捕まえるため本 wave には不要であり、型検査でしか
捕まらない形 (件数が同じまま `str` 派生型で SHA をすり替える) は wave 前の `== 38` でも捕まって
いない既存の穴である。**T-940 の検出力主張からこの形を明示的に除外する** — 本 wave が保証するのは
exact built-in 型の台帳に対する内容完全一致であり、多相型に対する保証ではない。
起票は {{T:ledger-exact-type-pin}}。新 entry の「実在違反であること」を検査する positive coverage が
無い点 (実在検査は固定 35 件のまま) は {{T:ledger-entry-liveness-coverage}} として残す。

段 6 レビュー B は「2 node が赤になる変異は単一理由性違反」と判定したが**不採用**とした。
`output/insights/2026-08-07_t618-known-violation-ledger/s4-adjudication.md` に先行判断があり、
赤理由が 1 つで node が 4 本になった事例を「検出層が 4 つあるためで理由の分散ではない」として
全 node を登録している。DW-M01 の要求は赤理由が 1 つであることで、検出層の数ではない。

**変異 matrix は 9/9 事前登録どおり (MISMATCH 0、KILLED 5 / SURVIVED 4)。** spec は実ファイルから
生成し、9 変異すべての置換位置の一意性を機械検査した。作成中に M3 の設計ミス (削除のつもりが
既存 SHA と重複する形) を自分で見つけて修正した。ユーザーが受入条件に挙げた 2 論点への実測の答えは
M1 (未承認 39 件目の混入 → KILLED、赤は literal node 1 件) と M2 (既存 note を 1 文字変更 →
KILLED) であり、「件数を外したら未知 entry が緑で通る」も「内容一致検査が恒真」も**起きない**。
M9 (容器が `len()`=39 と申告し反復は 38 件) がレビュー A の攻撃を実測で殺しており、fix の有効性の
裏取りになっている。M5 が wave 前の実コードの形 (件数 literal) の登録である。

受入全走: **1 failed / 10239 passed / 65 skipped (125 秒)**。赤は
`orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
**1 件だけ**で、**main 由来の既知赤**である。親自身の実測で切り分けた — `validate_condition_freeze_at`
を直接呼ぶと `7c9ac465` (octopus 直前の main) は GREEN、`d1de13ad` (親 4 つの octopus merge) は
`PreregistrationError [octopus-merge]` で RED。本 wave の差分はテスト 1 file の 4 行で s8c の履歴検査に
到達しない。既知赤として land してよいというユーザー裁定 (authority: user、発話逐語「既知赤として
登録して land して.このことは並行セッションに知らせてください」、2026-08-13 01:05 JST) は
**本セッションで直接受け取ったものではなく**、別 wave (dev-wave-t930-hold-no-bypass) が
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-known-red-octopus-merge.md` に残した一次控えを
根拠にした。控えの適用条件 (この 1 node だけの赤に限る・結果に明記・自差分に帰属させない・
フレークは既知赤にしない) はすべて満たしている。

工数の異常: 段 3 のレンズ B に codex 子を 4 回投入し 3 回失った。1・2 回目は
`evidence_status=invalid` で全損 — 原因は Web 検索ではなく、**子が repo 全体の内容付き `git grep` を
流し、約 1 MB の `aggregated_output` を 1 行の event に載せたため events.jsonl の 3 行が JSON として
閉じなかった**こと (`tools/codex_worker_launch.py:934` が `stdout_invalid` を立てる)。
`codex_exit_code=0` / `validator_rc=0` / 成果物 12 KB でも丸ごと破棄される。3 回目は出力量の制約が
効いて証拠経路は正常になったが、親が書いた「超えると全損する」という警告を子が停止条件と解釈し、
229 bytes の中止宣言だけ出して降りた。4 回目に「推奨であって停止条件ではない、絞り直して必ず
成果物を出せ」と書き直して成功した。失敗は {{F:codex-large-output-breaks-evidence}}。

`tools/dev_wave_wait.py producer` の待ち手が 3 回、producer 生存かつ `.done` 不在のまま rc=0 で
早期終了した (段 6 fix、変異走 2 回)。いずれも成果物実在 + `.done` + producer 死の 3 点照合で
不成立を検出し、張り直して正しく待った。

## 次の一手差分

### 完了

- [T-940] 件数 literal 固定を外し、敵対検証と変異 9/9 で裏取りして land した。
  remaining: none
  base: 179634a0fa32d4fbe74f609c26c9718df0bed6a4d4d75dba6568f27e0c596146

### 新規

- {{T:ledger-exact-type-pin}} **P2・新規**: 既知違反台帳の容器・spec・全 5 field の exact type を
  literal oracle の直前で固定する (test-only)。現行は `isinstance` のため `str` 派生型で SHA を
  すり替えると件数が同じまま内容 oracle を欺ける。段 3・段 6 の敵対レンズが独立に指摘し、
  段 4 で「wave 前から存在する穴」として scope 外に裁定した項。逐語案はレビュー A が提示済み。
- {{T:ledger-entry-liveness-coverage}} **P2・新規**: 既知違反台帳の各 entry が「実在する commit で
  実際にその違反を持つ」ことを検査する positive coverage を足す。現行の実在検査は固定 35 件で、
  承認のたびに更新されないため新 entry の実在性は無検査。production 台帳の各 SHA を個別に
  `_audit_history([sha])` へ通す独立 test が候補。
