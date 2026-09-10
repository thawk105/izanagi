# [T-936] `_find_rollout` の rollout 自己同一性 — wave 記録

2026-08-16 JST / branch `worktree-dev-wave-t936-rollout-identity` / base = main `ab3feb04`

ユーザー一括裁定 #41「全走査を維持したまま判定式を直す ([T-886] と矛盾しない形で)」の実装。

## 成果物

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。scope、不変条件、前提実測、provisional 裁定 (P1)-(P4)。 |
| `s4-adjudication.md` | 段 4 裁定と erratum E1 / E2。判定式の確定形と変異事前登録。 |
| `verbatim/s2-plan-v1.md` | 段 2 プラン (codex plan, reasoning=max)。 |
| `verbatim/s3-consult-a-sol2.md` | 段 3 敵対レンズ A (正しさ境界)。**NO-GO**。 |
| `verbatim/s3-consult-b-luna.md` | 段 3 敵対レンズ B (整合と実効性)。**NO-GO**。 |
| `verbatim/s5-unit1b.md` | 段 5 実装子の完了報告。 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー A (実装の正しさ)。**NO-GO**。 |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー B (実害と契約整合)。**NO-GO**。 |
| `verbatim/s6-fix-u1.md` | 段 6 fix 1 巡目。 |
| `verbatim/s6-fix2-u1.md` | 段 6 fix 2 巡目。 |
| `mutation/mutation-spec-round1-probe.json` | 変異 spec (probe)。 |
| `mutation/mutation-result-round1-probe.json` | probe 結果。KILLED 3 / MISMATCH 5 / SURVIVED 0。 |
| `mutation/mutation-spec-round2.json` | 本走 spec。期待 node は probe 観測から再導出した完全集合。 |
| `mutation/mutation-result-round2.json` | **本走結果。8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。** |
| `mutation/a4-corpus-measurement.json` | A4 実測 第 1 版。**erratum。land 根拠にしない** (下記)。 |
| `mutation/a4-corpus-measurement-v2.json` | A4 実測 第 2 版。**これが確定根拠。** |

## 判定式 (確定形)

```
own(r) = payload["id"]         ("id" が非空 str)
       = payload["session_id"] ("id" key が存在しない、かつ値が非空 str)
       = 未確定                 (それ以外: null / 数値 / bool / 空文字 / payload が dict でない)

determinable(F) = own(r) が未確定でない meta 行の列 (元の行順を保つ)

owns_X       = ∃r ∈ determinable(F): own(r) == X
first_owns_X = determinable(F) が空でなく own(determinable(F)[0]) == X
declares_X   = ∃r ∈ determinable(F): own(r) != X かつ r.payload["session_id"] == X

F が X を名乗る ⇔ owns_X ∧ (first_owns_X ∨ ¬declares_X)
```

意味は「**先頭の確定できた session_meta 行が file の自己同一性を決める。
自分を X の子孫だと宣言する file は X ではない。ただし先頭行が X を名乗るなら剥奪しない**」。
`first_owns_X` は意図的に**行順に感受性がある**。codex は自分の行を先に書くため実データはこれを満たす。
規約が破れた file は解決されず fail-closed になる。

## A4 実測 (確定版 `a4-corpus-measurement-v2.json`)

実 corpus `~/.codex/sessions` を直接走査し、**実装後の production module を import して呼んだ**。

| 項目 | 値 |
|---|---|
| file 数 | 3,649 |
| distinct id 数 | 3,649 |
| 新述語の解決件数ヒストグラム | すべて 1 (件数 1 以外の id = **0 件**) |
| 旧述語の解決件数ヒストグラム | 1 が 3,647、2 が 1、4 が 1 |
| 新旧で解決集合が異なる id | **2 件** (`019f690c…`、`019fd52d…`) |
| **旧で一意だった id で返り path が変わったもの** | **0 件** |
| raw bytes 走査での session_meta 候補行 | 4,741 |
| raw の parse 失敗 / open 失敗 | **0 / 0** |
| symlink / 重複 inode | 0 / 0 |
| corpus 安定性 (測定対象の内容 digest 前後一致) | **true** (変化 0、削除 0、走行中の追加 1 は測定対象外) |
| 絞り込み検証 (無作為 30 id を全 file 評価と突合) | 不一致 **0** |
| pin 付き 5 label | すべて解決 (fast path、SHA 照合とも従来どおり) |
| fork / subagent file | 4 件、親 2 系統、producer 2 系統 (codex_vscode 0.144.2 / codex_exec 0.146.0) |

**第 1 版を erratum とした理由** (段 6 レビュー B 所見 1、real):
(i) `_session_meta_rows` を memo 化し候補を絞ったため production の全走査経路を通っていない、
(ii) 同 helper が読取・parse 失敗を内部で捨てるので「例外 0」が異常の不在を意味しない、
(iii) 旧述語との返り path 完全一致を測っていない、
(iv) 2 走の間で corpus digest が変わっており live corpus の安定性が未確認だった。
第 2 版はこの 4 点をすべて塞いでいる。

**実行不能性の明記:** 全 id への `_find_rollout` 直接呼出しは O(id 数 × file 数) の file I/O で
単走 225 秒 × 3,649 id = 約 9.5 日となり実行不能である。第 2 版は
「差分 id + pin + T-936 の 2 id は絞り込みも memo もせず `_find_rollout` を直接呼ぶ」
「無作為 30 id で絞り込みの正しさを全 file 評価と突き合わせる」で代替した。

## 変異 matrix

runner scope = `orchestrator/tests/test_codex_reasoning_ab.py -q --tb=no -rf --force-dispatch`。
runner-mode = dispatch。baseline PASSED (rc=0)。anchor commit = `f8f8a107`。

| ID | 種別 | 変異 | 失敗 node 数 | 結果 |
|---|---|---|---|---|
| M01 | negative | wave 前の形へ復帰 (`id == X or session_id == X` で即 return) | 12 | KILLED |
| M02 | negative | veto (`declares`) を落とす | 4 | KILLED |
| M03 | negative | `first_owns` の disjunct を落とす (= プラン v1 の形) | 6 | KILLED |
| M04 | negative | own 一致で即 `return True` (行順依存) | 4 | KILLED |
| M05 | negative | 非空 str 検査を外し全非 str を `session_id` へ fallback | 6 | KILLED |
| M06 | negative | `id` key 欠落時の fallback を削除 | 1 | KILLED |
| M07 | negative | 件数検査を `!= 1` から `< 1` へ緩める | 14 | KILLED |
| M08 | **positive** | 述語を常に偽にする (過剰拒否の検出) | 68 | KILLED |

**8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0。**

probe 走 (round 1) は KILLED 3 / MISMATCH 5 で、期待 node が親の推測と 5 件ずれた。
ずれは検出力の欠落ではなく推測の誤りである。観測から完全集合を再導出して本走を登録した。
**probe の台帳も削除せず残す** (`mutation-result-round1-probe.json`)。

M06 / M07 は既存テストが先に殺す **shared** 変異であり、新規テストの純増検出力には数えない。
段 6 レビュー A 所見 3 の指摘どおり、型 B 逆順 / 片側 veto / 真の重複の 3 本は
wave 前実装でも通るため、保存回帰および M03 の killer として記録し、
「wave 前実装を倒す新規テスト」には数えない。

## 実害の範囲 (限定して記録する)

**「実害が完全に消えた」とは書かない。** 消えたのは次の型である。

- **thread_spawn / subagent 型** (`019fd52d…`、子 3 file): 親 file の `session_meta` は 1 行なので、
  `_find_rollout` が親を返し、消費側 `:3090` の件数検査と直後の identity 検査も通る。
  T-936 が述べた実害 (「codex 子が subagent を産むと正当な作業を拒否しうる」) はこの型である。
- **compaction / resume 型** (`019f690c…`、meta 4 行): `_find_rollout` は成功するが、
  消費側が `session_meta count is 4, expected 1` で拒否し続ける。**R1 として scope 外。**

## 標本の薄さ (明記)

実 corpus の fork / subagent file は 4 件しかない。親は 2 系統、producer は
`codex_vscode 0.144.2` と `codex_exec 0.146.0` の 2 系統である。
親行コピーを持つ 3 file は同一親由来の兄弟であり、実質 1 episode である。
**この 4 件は回帰 fixture の由来として記録し、「fork は必ず親行コピーを持つ」という
普遍規則としては記録しない。** 別 producer が親行を先に書けば、
正当な run が再び拒否側へ落ちる (fail-closed)。

## [T-886] との関係

[T-886] は「現行 pin で実測一致した SHA 認可付きの限定 fast path」であり、
**全走査と普遍的に同値ではない**。既存テスト
`test_find_rollout_pinned_rglob_reaches_arbitrary_depth` が両者の差を固定している。
本 wave は pin 無し経路の全走査を 1 行も変えていない。
