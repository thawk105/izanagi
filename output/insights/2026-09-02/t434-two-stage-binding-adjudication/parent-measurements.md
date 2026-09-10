# [T-434] 親の独立実測 (段 2 待機中)

基準 main `28ebff456b9f57a927854950b5030fa77aec6529`。すべて現物を読んで確認した。

## 既存の commit 検査機構 — D1407 が `A` に要求する 4 述語の充足状況

| D1407 が `A` に要求すること | 既存実装 | 所在 |
|---|---|---|
| 非 merge | **あり** | `s8b_ratified_freeze.py:558` `_assert_user_commit` (`len(parents) > 1` を拒否) |
| `AI-Agent: none` を逐語ちょうど 1 本 | **あり** | 同 `:546` `_is_none_commit` — raw 行ちょうど 1 本かつ byte 一致、加えて `interpret-trailers --parse` 値が exact `["none"]` の二重判定 |
| 追加 path がちょうど 2 件で、他の status を 1 件も含まない | **あり** | `s8b_ratified_freeze.py:1273` `_verify_pairing` — `_added_paths` (`:607`, `diff-tree --no-commit-id --name-status -r`) の結果に対し `added != frozenset({approval.path, pointer.path}) or other` で拒否 |
| 親集合が exact `{G}` | **あり (別 module)** | `trial_registry.py:1243` `assert_effective_commit_exact_parent` — root commit・merge・別親・graft・replace ref・shallow を拒否 |
| `G != A` | **あり** | `s8b_ratified_freeze.py:1284` `generation-approval-same-commit` |

**結論 (親の provisional):** D1407 の topology 4 述語は、既存の 2 module に**すべて実装済みの相当物がある**。
`s8b` 側は親一致を見ず (H ancestry だけ)、`trial_registry` 側は追加 path 集合を見ない。
不足しているのは「この 2 つを同じ対象へ同時に適用する呼び手」だけである。

これは引数の「D438 決定 (4) の適用であり新機構ではないので、既存の commit 検査機構を再利用する」と
一致する。新規に書く量は当初の見積りよりかなり小さい。

## 検算した親 brief のアンカー

- `p3_autonomous_workload_trial.py:144` `MAX_APPROVED_GENERATIONS = 2` — 一致。`:506` で `>` 比較。
- `trial_registry.py:771` `generations must be the integer 2` — 一致 (`type(generations) is int and generations == 2`)。
- `reflux_formal_consumer.py:108,248,934,1034` `P6_UNAVAILABLE` / `P6Unavailable` — 一致。
- `s8c_acceptance_receipt.py:421-423` — `certifying is not False` を構造的に拒否。一致。
- `s8b_ratified_freeze.py:518,528,546,558,573` — 一致。

## 未解決 (段 3 のレンズへ投げる)

- narrow scope が D841 の「受領証だけを先に作る形は採らない」に抵触するか。
- DW-G04 の発火条件 (実在の artifact path か計測 ID) を書けるか。
- `G` の内容を複数 commit へ分けてよいか (認定記録は revision 束縛なので tree が揃えば足りるのか)。

## 親の実測 2 — diff-tree の status (repo 外の使い捨て git repo で測定)

`git diff-tree --no-commit-id --name-status -r <commit>` (既存 `_added_paths` と同じ argv) の実測。

| 操作 | 出た status |
|---|---|
| rename (`git mv`) | `A new.txt` と `D old.txt` の 2 行 |
| rename + `-M` を明示 | `R100 old.txt<TAB>new.txt` の 1 行 |
| mode 変更のみ (`chmod +x`) | `M new.txt` |

`diff.renames=true` を `-c` でも repo config でも与えたが、`diff-tree` の出力は変わらなかった
(`-M` を明示しない限り rename 検出は起きない)。`core.useReplaceRefs=false` を併用しても同じ。

**含意 (2 点、いずれも段 4 の裁定材料):**

1. rename を使った「2 件に見せる」攻撃は、既存 `_added_paths` が `D old.txt` を `other` に
   入れるので既に拒否される。**rename 専用の負例を別枠で登録すると冗長 gate になる。**
   `--no-renames` を足す必要も無い — plumbing は config で rename 検出に切り替わらない。
   仮想リスク向けの検査追加はしない。
2. mode 変更のみの負例は、内容変更の負例と同じ `M` で同じ理由で赤くなる。
   これも単独理由性を持たないので別枠にしない。

## 親の実測 3 — 段 2 プランの file:line 検算

| 段 2 の記述 | 現物 | 判定 |
|---|---|---|
| `p3_autonomous_workload_trial.py:139` = `MAX_APPROVED_GENERATIONS` | **144** | 段 2 が誤り |
| `trial_registry.py:743` = `must be the integer 2` | **772** (`if` は 771) | 段 2 が誤り |
| `p3_autonomous_workload_trial.py:501` = 予算比較 | **506** | 段 2 が誤り |
| `test_trial_registry.py:6073-6249` に実 git 負例 | 6079〜6247 に 9 箇所の呼出し | 段 2 が正しい |

**段 2 の file:line 主張は一様に信頼できない。** 個別に検算してから採用する。

## 親の実測 4 — exact-parent 述語の既存被覆

`assert_effective_commit_exact_parent` の負例は既に実 git で網羅されている
(`orchestrator/tests/test_trial_registry.py` の同関数を呼ぶ 9 箇所)。

- root commit 拒否 / 別親拒否 / merge 拒否 / 非 canonical 引数拒否 /
  parent query 失敗 / graft file 拒否 / replace ref 拒否 / measurement HEAD 祖先要求。

**含意:** 仮に T-434 の topology を実装するとしても、親集合 exact `{G}` の側は
新しい負例を 1 件も足す必要がない。新規に要るのは「追加 path が exact 2 件・create-only」と
「`AI-Agent: none` 逐語 1 本」を cap-lift の主体へ当てる分だけである。
差分は段 2 の見立てよりさらに小さい。

## 親の実測 5 — blocker の持ち主 (T-941) を特定した

- `docs/phase3.md:1118` — 「機械実装は **[T-941] P6 実装 wave** の所有」と明記。
- `docs/phase3.md:1161` — T-942 (材料レポート renderer の結線) も「P6 実装 wave へ同梱」と確定済みで、
  再訪条件は「なし ([T-941] が所有)」。
- `docs/archive/worklog-phase3-0812-489.md:649` — T-941 の起票本文。
  「D156 が『境界テストを含む機械実装は P6 実装 wave と cap-lift receipt 設計の所有』と定めたまま
  **未実施**であり、本 wave はそのため条件 8 を `P6Unavailable` で fail-closed にした。
  認定 4 要件を満たすまで `OriginSealed(aborted=False)` は発行できない。」
- 同 `:654` — T-942 の V-11 は「**P6 の実装と認定をどの wave が所有するか**」で
  **ユーザー裁定待ち**のまま残っている。

**含意:** T-434 の実装は T-941 に順序依存する。T-941 が未実施である限り、
D1407 が定める `G` は完成せず、`A` の認定記録も作れない。
これは本 wave の裁量で解ける順序ではない。

## 親の実測 6 — 自分の brief の訂正 (レンズ B の N3 を現物で追認)

親 brief は `reflux_formal_consumer.py` を「`P6Unavailable` で**無条件**停止」と書いたが、
これは design-v3 の表現を引き写したもので不正確だった。現物では前段の条件が失敗すれば
`FormalContractRejected` になり、**全前段を通過したときだけ** `P6Unavailable` になる。
正確な一般化は「非 aborted の成功終端は存在せず、前段通過後は必ず `P6Unavailable`」である。

含意: 「P6 だけを壊した負例」のつもりで前段の contract も壊すと、拒否理由が別物になる。
将来の実装 wave が負例を書くときの注意点として残す。
