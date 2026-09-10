# [T-1143] enforcement source closure を exact 12 path へ — 材料と実測

2026-08-16、branch `worktree-dev-wave-t1143-epoch-closure`。
裁定は 2026-08-16 /rulings 全件 #11「closure を広げ、verifier 4 ファイルを束縛対象へ」
(authority = ユーザー「推奨通りで」)。

`campaign_verifier_epoch` が束縛する enforcement source closure へ
`orchestrator/verifier/{core,dsg,model,parse}.py` を加え、exact 8 path から exact 12 path にした。

## 閉じたもの / 閉じていないもの

**閉じたのは 1 つだけである。** 「E1 lock を記録した後に verifier の実装 bytes だけを
書き換えても epoch が変わらず、anomaly を含む run が同じ epoch の certified 集合へ入る」経路。

**閉じていない。** 次を「閉じた」と読める記述をしてはならない。

| 経路 | 状態 | 根拠 |
|---|---|---|
| `orchestrator/verifier/__init__.py` の再 export 差し替え | 開いている | `pipeline.py:30` が `from ..verifier import verify_trace_dir`。shim は閉包外 |
| `report.py` / `cli.py` / `__main__.py` / `orchestrator/verify.py` | 開いている | いずれも閉包外 |
| 弱化して commit してから作る fresh lock | 拒否しない | 閉包が見るのは記録後の drift だけ。新しい `E1` として受理される |
| `__pycache__` / monkeypatch / `sys.modules` / `PYTHONPATH` | 開いている | disk の `.py` bytes しか読まない |
| 未束縛 bootstrap (`campaign_lock.py` 等) | 開いている | D268 が root of trust と明記済み |
| pipeline の推移依存 (calibrator / buildcache / build_admission / source_digest 等) | 開いている | D268 が閉包外と明記済み |
| epoch の cross-version 認証 | 無い | oracle validator は scope を非空文字列としか検査しない |
| T126 qualification の code identity | 追随しない | verifier では `core.py` しか含まない |

## 親の実測 (裁定の前提検査と pin 閉包)

| 項目 | 実測値 |
|---|---|
| `output/**/campaign.lock` の総数 | 32 |
| うち v2 (`contract_loader_blob_sha256s` を持つ) | **0** |
| 凍結成果物中の文字列 `exact 8 path` (insights の歴史逐語を除く) | 0 件 |
| `campaign_verifier_epoch` を含む campaign 成果物 | 0 件 |
| `campaign_lock.py` の bytes を pin する live な台帳・manifest | 0 件 |
| `FROZEN_MANIFEST` の key 23 件のうちソース path | 0 件 (全て `output/**`) |
| レポートの `generator.sha256` の対象 | 各 report module 自身の `__file__` |
| `REQUIRED_CODE_IDENTITY_PATHS` に `campaign_lock.py` | 含まれない |
| `silo_ladder_rung1` の runtime binding | verifier 8 file を `rglob` で既に束縛 (本 wave は verifier bytes を変えないので digest 不変) |

**「pin 0 件」は path 検索だけでは確定しない。** 段 3 レンズ A の指摘を受け、key 側 (authority key)・
role 側 (generator identity、runtime module 集合) でも数え直して確定した。

## テスト実測

| 走 | 対象 | 結果 |
|---|---|---|
| 焦点走 1 (login node, bounded local) | 7 file | **rc=16、テスト 0 件** (cgroup の `memory.max` / `memory.oom.group` を走行中に attest 不能) |
| 焦点走 2 (計算ノード, `--force-dispatch`) | 7 file | **347 passed / 0 failed** (6.58s、Pegasus request 913229) |
| 焦点走 3 (fix 第 1 巡の後) | 7 file | **347 passed / 0 failed** (6.08s) |

段 5 実装子と段 6 fix 子はいずれも同じ理由で pytest を 1 件も実走できず、
「実装済み・未実走」と正しく申告した。**実測はすべて親が行った。偽の緑は無い。**

## 変異 matrix

runner 範囲 = `test_t671_source_binding.py`, `test_artifact_admission.py`,
`test_campaign_lock_codec.py`。runner は `tools/run_tests.py --force-dispatch -rf`。
harness は `tools/mutation_worktree.py` (固定 commit の使い捨て worktree)。

### 走 1 = probe (固定 commit `999357c5`)

baseline PASSED。**SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**、KILLED 2 / MISMATCH 5。
MISMATCH はすべて期待 node の不足であって検出力の欠如ではない (`DW-M08` の probe + erratum)。

**この走が fix 第 2 巡の根拠になった。** M1〜M4 のいずれでも drift test の 4 node すべてが
落ちており、「外した path の node だけが落ちる」判別が成立していなかった。原因は fix 第 1 巡で
期待 epoch を独立 literal から導くようにしたことで、変異後 (11 path) の記録 epoch と
期待値 (12 path) がずれ、対象外の node まで epoch 不一致で落ちていたことである。
ledger = `mutation-ledger-probe.json`。

### 走 2 = 権威走 (固定 commit `ae19c506`)

baseline PASSED。**KILLED 7 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0。
7 変異すべてで登録した期待 node が 1 件も欠けず過不足なく落ちた。**
spec = `mutation-spec-final.json`、ledger = `mutation-ledger-final.json`。

| ID | 変異 | 分類 | 失敗 node 数 | drift test で落ちた node |
|---|---|---|---:|---|
| M1 | closure から `orchestrator/verifier/core.py` を削除 | negative | 44 | `[core.py]` のみ |
| M2 | 同 `dsg.py` | negative | 44 | `[dsg.py]` のみ |
| M3 | 同 `model.py` | negative | 44 | `[model.py]` のみ |
| M4 | 同 `parse.py` | negative | 44 | `[parse.py]` のみ |
| M5 | identity scope を旧 exact 8 文字列へ戻す | **diagnostic sensitivity pin** | 1 | — |
| M6 | excluded scope を旧文字列へ戻す | **diagnostic sensitivity pin** | 1 | — |
| M7 | 記録 map と現在 map の比較を常に不一致にする (過剰拒否) | positive | 2 | — |

**path 単位の判別が成立している。** 閉包から `core.py` を外すと落ちる drift node は
`[core.py]` ただ 1 本で、`[dsg.py]` `[model.py]` `[parse.py]` は緑のまま。4 変異とも同じ形。
これが本 wave の純増検出力 (「verifier の 4 file の bytes が drift すると certified 実行が
fail-closed する」) の直接証拠である。

**M5 / M6 は `DW-M08` に従い diagnostic sensitivity pin として別枠に記録する。**
受理集合も fail-closed 挙動も変えないので、「受理集合を守った kill」ではない。

## レビューの帰結

| 段 | 子 | 判定 |
|---|---|---|
| 3 | consult sol (レンズ A = 正しさ境界) | NO-GO、13 所見 (blocker 6) |
| 3 | consult luna (レンズ B = 整合・実効性) | NO-GO、8 所見 (blocker 4) |
| 6 | review A (弱化と偽緑) | NO-GO、1 所見 (major) |
| 6 | review B (取り残しと契約破壊) | **GO、所見ゼロ** |
| 6 | focus (fix 後の全体) | NO-GO、変異の帰属で 2 点 |

**段 3 の 2 レンズは独立に同じ blocker (再 export shim) へ収束した。**
段 2 プランと段 3・段 6 の全レビューが `__init__.py` の追加 (exact 13) を推したが、
親は批准された裁定文が名指しした 4 file だけを実装し、shim は裁定パッケージへ返した。

逐語は `verbatim/` に置く。段 4 の裁定は `verbatim/s4-adjudication.md`。
