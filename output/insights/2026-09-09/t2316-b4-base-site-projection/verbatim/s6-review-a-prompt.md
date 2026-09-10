単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md` — **段 4 裁定。実装の正本。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s5-author.md` — 実装子の完了報告。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py`

レビュー対象の差分は commit `db95ffb3bd0b585a702ecbd9523a5aba790652f4` である。
`git show db95ffb3b` で読め。repo の path は上記 worktree のものだけを使う。

## 段の宣言

これは段 6 (敵対レビュー) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。**
実走していない検査を「通した」と書いてはならない。コードを編集してはならない。commit してはならない。

**実装を守るな。壊せ。** 所見が出ないこと自体が失敗である。
予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ: 変異で死ぬか (test の検出力)

親は段 4 で次の変異を事前登録した。**実装された 5 node がこれらを本当に殺すかを、
コードを読んで判定せよ。** 殺せない変異が 1 つでもあれば real 所見である。

| ID | 変異 | 期待 |
|---|---|---|
| M1 | `_driver_configs` の base 射影ブロックを削除する | N1 と N3 が RED |
| M2 | base 分岐で `_campaign_cfg_for_site` を使わず marker だけ足す | N2 が RED、N1 は GREEN |
| M3 | 分岐条件を `driver_kind in {"base", "sort"}` へ広げる | N5 が RED |
| M4 | `p3_s4_loop._current_site()` を literal `site_policy.OTHER` に置き換える | N1 が RED |

対応する node は次のとおり。

- N1 `test_base_driver_configs_project_both_arms_for_pegasus_compute`
- N2 `test_base_driver_configs_bind_resolved_contract_for_both_admitted_sites`
- N3 `test_base_launcher_pegasus_context_passes_real_authorization_and_g4`
- N4 `test_base_driver_configs_preserve_other_campaign_ids`
- N5 `test_sort_driver_configs_remain_unprojected_on_pegasus_compute`

次を順に攻撃せよ。所見ごとに **real / refuted** を判定し、根拠を file:line で示せ。

1. **各変異に対して、期待どおりの node が、期待どおりの理由で赤くなるか。**
   期待より多くの node が赤くなる場合、その追加の赤は同じ原因か別の原因か。
2. **単一理由性 (`DW-M01`)。** 各変異について、同じ入力を拒否する層が前後にも内側にも無いか。
   前段の admission 検査や `require_any_context` が先に拒否して、狙った比較まで到達しない
   変異があれば名指しせよ。
3. **過剰決定 (`DW-M03`)。** ある node が複数の独立な理由で赤くなるなら、それは単一理由の
   fixture ではない。差し替えるべきか、冗長 gate として単独変異の証拠から外すべきかを述べよ。
4. **等価変異。** 親は「base 分岐の helper を `p3_s4_loop_trigger_gating` の同名 helper へ
   差し替える変異は両実装が同一なので SURVIVED が期待値」と裁定した。この判定は正しいか。
   両 helper を逐語比較して確かめよ。差があれば real 所見である。
5. **殺せない変異を自分で探せ。** 上の 4 つ以外に、実装を壊すのに 5 node すべてを通過する
   変異が作れるか。作れるなら具体的な変異内容を書け。**これが最重要の攻撃点である。**
6. **N3 の主張の射程。** N3 は registry spy を使う。実装子は報告で
   「launcher 分岐の証明であり base `main` 全体の実走証明ではない」と自己申告している。
   この自己申告は正確か。過大でも過小でもないか。

## 禁止

- 授権境界の比較を緩める案を出してはならない。
- 既存 test の期待値を変える案を出してはならない。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を提案してはならない。
  scope 外だが real な所見は「実装せず裁定へ返す候補」として明記せよ。

## 出力形式

以下の H2 見出しをこの順で使え。所見には通し番号 RA1、RA2、… を振れ。

## 変異ごとの判定
## 所見 (real)
## 所見 (refuted)
## scope 外だが real (裁定へ返す候補)
## 総括
