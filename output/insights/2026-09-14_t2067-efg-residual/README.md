# [T-2067] 残件 (e)(f)(g) — 塞ぎの再実測と母集合の再検算

- 日付: 2026-09-14
- branch: `worktree-dev-wave-t2067-efg-residual`
- 基準 commit: `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a` (着手時は `f5423e2ff`、差分は
  `docs/spool/` の断片 1 file のみで対象コードに差分なし)
- 実装面の差分: ゼロ

## 結論

1. **(e)(f)(g) を塞いでいる 3 つの前提は、今日の main でも現物で成立する。** したがって本 wave では
   3 件とも実装しない。D1371 の不実装裁定はそのまま維持される。
2. **(b) の母集合は 2026-09-08 の値と一致する。** 静的 loader `load_ratified_freeze` の production
   callsite は 9 箇所 / 9 関数 / 7 module、選択規則へ静的に配線済み 7 / 未配線 2。親と段 2 の子が
   独立に数え、段 3 のレンズ A が第三の経路で検算して一致した。
3. **caller 閉包を固定するテストの新設は不採用とした。** 過去に実際に起きた 2 件の誤りを、この
   テストは 1 件も検出しない。防ぐのは「将来 10 件目の未配線 callsite が増える」ことだけで、
   その発生実績は無い。依頼の scope 制約 (仮想リスク向けの gate・検査の追加は scope 外) の
   却下側にある。

## 1. 母集合の再導出

導出は 3 者が独立に行った。親は識別子検索とコード読解、段 2 の子は import 束縛を解決する AST 走査、
段 3 のレンズ A は `git ls-files --cached --others --exclude-standard` による列挙 + AST parse
(production Python 448 file = orchestrator 288 / tools 120 / output 36 / hooks 4) で数えた。

| callsite | 所属関数 | 選択規則への配線 |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_manifest.py:1205` | `build_approved_manifest` | `:1206` 直接 API |
| `orchestrator/campaign/s8b_oracle_report.py:2547` | `main` | `:2548` 直接 API |
| `orchestrator/campaign/s8b_oracle_judge.py:749` | `main` | `:750` 直接 API |
| `orchestrator/campaign/s8b_verdict.py:828` | `main` | `:829` 直接 API |
| `orchestrator/campaign/s8c_result_judge.py:2076` | `_load_selection_checked_ratified_floor` | `:2078` 直接 API |
| `orchestrator/campaign/s8b_oracle_driver.py:644` | `gate_check` | `:664` の `launch_validate` |
| `orchestrator/campaign/s8b_oracle_driver.py:1335` | `run_block` | `:1351` の `launch_validate` |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:4957` | `run_trial` | **未配線** (D1371 決定 1) |
| `orchestrator/campaign/s8b_oracle_driver.py:496` | `_gate_check_core` | **未配線** (D1831 決定 4 の裁定待ち) |

直接 API は `assert_g1_floor_selection_identity`。`launch_validate` 経由が配線として成立する根拠は、
`orchestrator/campaign/s8b_ratified_freeze.py:3579` が `_launch_validate` へ
`result_type=LaunchValidatedFreeze` を渡し、`:3332` の exact 型分岐の中でだけ `:3334` の
`_hf._assert_floor_selection_identity` を呼ぶことである。

### 導出条件と限界

- 列挙は tracked + untracked (ignore 対象外) から test を除いた Python に限る。ignored untracked、
  非 `.py`、gitlink 内部 (`external/ccbench`) は入らない。
- 動的解決 (文字列を組み立てる呼び出し、名前を含まない汎用 deserializer) は証明していない。
  別名代入・`getattr` 文字列呼び出し・`functools.partial`・decorator 経由は**探して見つからなかった**
  が、不存在を証明したわけではない。
- **この件数を「権威ある閉包に由来する」と書かない。** loader の caller を exact 一致で固定する
  メタテストは今日も repo に実在しない (D1831 決定 3 の状態が続いている)。

### 「配線済み 7」の意味を過大に読まない

- `assert_g1_floor_selection_identity` は `s8b_ratified_freeze.py:3601` で `generation_number != 1`
  のとき**何もせず返る**。直接 API 5 件は非 g1 では空検査になる。
- 一方 full launch core は `:3136` で非 g1 を**拒否**する。したがって「非 g1 なら 7 件すべてが
  空検査」は誤りで、直接 API 5 は対象外・launch 2 は拒否、と向きが分かれる。
- `reverify_published_freeze` は `result_type=ReverifiedFreeze` (`:3691`) を渡すため `:3332` の
  分岐に入らない。**「launch という名の呼び出し = 配線済み」は一般には偽**であり、公開
  `launch_validate` の exact wrapper に限って成立する。
- 配線の実在は「公開成果物までに必ずその検査を通る」ことを証明しない。再代入・到達しない分岐・
  例外の握り潰しは静的な隣接からは区別できない。

### 現行 HEAD では loader 自体が発火しない

本 wave で production 入口を直接叩いて確かめた。

```
resolve_active_generation() -> RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)
load_ratified_freeze()      -> RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)
```

9 callsite はいずれも現行 HEAD では loader 段階で止まる。選択規則の配線は v2 発効後に効く前向きの
ものであり、現時点の実行確認ではない。

## 2. (e)(f)(g) の塞ぎ — 今日の現物

| 残件 | 塞ぎ | 現物での確認 |
|---|---|---|
| (e) s8c C06 予算群 | D1371 決定 1。再評価の発火条件は C05 の着地 | `p3_autonomous_workload_trial.py:2074` の `_load_s8c_schedule_authority` は引数を捨てて無条件に raise する。`:2112` 経由で `:4964` の予約前に止まり、予算台帳を作れる入力集合は空のまま |
| (f) 起動証明書の実時間性 | D1371 決定 2。閉じるには署名・外部 nonce・一回性台帳のいずれかが要り、D1241 / D1243 がそれを禁じている | `s8b_floor_campaign.py:5521-5538` は clean scan の preimage を局所変数として組み立て、sha256 だけを返す。certificate が持つのは digest だけで、launch 時点の独立した commitment は保存されない |
| (g) s8c production final claim 配線 | D1371 決定 3 | (e) と同じ C05 不在により、judge が要求する exact 6 cell schedule の正本が production に無い |

**限界:** (f) について、発行時点の整合性検査自体は既に在る (`s8b_floor_campaign.py:5588-5613` が
独立 2 回 scan と strict expected 比較を行う)。不能なのは「後日の独立した実時間証明」であって
「関連コードが何も書けない」ことではない。(g) についても、3 表 publish API と transaction 処理は
`s8c_result_judge.py:2413` に在る。本 wave が確認したのは C05 の不在までで、attestation authority と
receipt schema の結合まで全数監査したわけではない。**「既存裁定の下で要求保証を閉じられない」を
「実装可能性が無い」と読み替えない。**

## 3. 閉包テストを新設しない理由

段 2 は隣接する `test_build_observations_production_caller_is_main_only`
(`orchestrator/tests/test_s8b_oracle_report.py:5706`) と同型の caller inventory test を起案した。
段 3 の 2 レンズが独立に攻撃し、親は**不採用**と裁定した。

1. **反実仮想が成立しない。** 実際に起きた誤りは (i) 2026-09-08 の carry が訂正前の文面を写した
   転記誤り、(ii) 2026-09-03 の wave が `s8b_oracle_driver.py:496` を到達不能と判断して母集合から
   外した判断誤り、の 2 件である。**提案されたテストはどちらも検出しない。** 前者は文書運用、
   後者は到達可能性の判断であって、caller の静的件数ではない。
2. **防ぐ対象に発生実績が無い。** テストが検出するのは「10 件目の未配線 callsite が増える」ことで、
   これは今日まで一度も起きていない。D1831 は同じ理由で二読 fallback の縮小と library 経路への
   token 追加を却下している。
3. **証拠力が既存テストと重複する。** 事前登録候補 10 件のうち 8 件は、既存テストが同じ変更で
   既に赤になる。下表はレンズ A が既存 source の assertion から予測したもので、変異の実走ではない。

   | 変異候補 | 既に殺している既存テスト |
   |---|---|
   | manifest `:1206` の選択検査除去 | `test_s8b_oracle_manifest.py:1438`, `:1499` |
   | report `:2548` の除去 | `test_s8b_oracle_report.py:1807`, `:1836` |
   | judge `:750` の除去 | `test_s8b_oracle_judge.py:763`, `:833` |
   | verdict `:829` の除去 | `test_s8b_verdict.py:1027` |
   | s8c judge `:2078` の除去 | `test_s8c_result_judge.py:1776` |
   | driver `:664` の launch 除去 | `test_s8b_oracle_driver.py:5407` |
   | driver `:1351` の launch 除去 | `test_s8b_oracle_driver.py:4752` |
   | core `:3334` の除去 | `test_s8b_ratified_verify.py:997`, `:1032` |

4. **受入の所要を押し上げる。** 同型の既存テストは台帳で 7.8 秒
   (`test_build_observations_production_caller_is_main_only`) と 6.9 秒
   (`test_stage6_candidate_gate_caller_inventory_matches_repository_and_docs`) を要する。
   提案は全 production Python を対象にし、正例 1 回に加えて負例側で走査を反復するため、粗い試算で
   数十秒の追加になる。これは台帳値からの予測であり本 wave の実測ではない。
5. **上限解除に寄与しない。** D1313 は削除済み earlier run、後続世代、起動証明書の実時間性も
   残余として挙げ、「選択規則の実装だけでは non-certifying 上限を解除しない」と明記する。
   inventory の固定は未配線 2 件も公開物の受理集合も変えない。

## 4. 分離して返す裁定待ち (実装しない)

D1831 決定 4 の択一がそのまま開いている。本 wave は**どちらも既成事実にしていない**。

- 対象: `orchestrator/campaign/s8b_oracle_driver.py` の `_gate_check_core` 内 self-load (`:496`)。
- 択一: (i) 現状維持のまま到達条件つきで台帳へ記録する / (ii) exact `LaunchValidatedFreeze` 必須へ
  縮めて D65 決定 (5) の不変条件を全分岐で成立させる。
- 到達条件: 「初回 read が失敗し、直後の再 read が成功する」外部要因の状態変化が要る。`:503` の
  sha256 完全一致により、受理されうる freeze は active 世代そのものに限られる。
- (ii) は実装面のため D95 の Codex role=author と変異事前登録が要る。

## 5. 親 brief の誤り (段 3 が指摘し、訂正した)

- 「隣接テストと同じ母集合」は誤り。`test_build_observations_production_caller_is_main_only` は
  `ORCH.rglob("*.py")` で orchestrator 配下だけを走査する。本 wave が数えた 448 file には
  `tools/`・`hooks/`・`output/` が含まれる。
- 「裁定パッケージ 2 件」は過大。D1371 の不実装判断を覆す新事実は出ていないので、返すのは
  D1831 決定 4 の 1 件だけである。
- 「母集合の誤導出が 2 度起きた」という表現は強すぎる。2 件は別原因だが、どちらも新設テストの
  検出対象ではないため、新設の根拠にならない点が本質である。

## 資料

- 段 2 プラン / 段 3 レンズ A / 段 3 レンズ B の逐語は job 側の wave 専用 dir に置いた
  (repo へは複製しない)。本書は結論と根拠 file:line だけを持つ。
