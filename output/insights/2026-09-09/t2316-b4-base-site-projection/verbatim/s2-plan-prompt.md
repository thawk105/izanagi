単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/brief.md` — 親の段 1 brief (逐語)。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop_trigger_gating.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py`

repo の path は上記 worktree のものだけを使う。`/work/1/SFC/tanab/izanagi/orchestrator/...`
のような親 checkout の path を使ってはならない。

## 段の宣言

これは段 2 (プラン起草) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。**
実測は親が段 6 で行う。実走していない検査を「通した」と書いてはならない。
コードを編集してはならない。commit してはならない。

予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

出力に結合文字 U+0300〜U+036F を使うな。

## 依頼

[T-2316] の実装プランを file:line 粒度で起草せよ。

欠陥: `p3_b4_launcher.py` の `_driver_configs` は `driver_kind == "trigger"` のときだけ
site 射影する。base の driver (`p3_s4_loop.main`) は自身の側で必ず site 射影するため、
`PEGASUS_COMPUTE` では launcher が束縛する campaign ID と driver が要求する
`expected_campaign_id` が食い違い、`require_b4_production_context` が拒否して build へ到達しない。

親 brief の「機序」節に、親が実測で確定した行番号つきの因果がある。プランはこれを**独立に検証**し、
誤りがあれば指摘せよ。同意する場合も、同意した根拠の file:line を自分で挙げよ。

## プランに必ず含めるもの

1. **変更する file:line と、変更後の関数の完全な形。** 対象は
   `orchestrator/campaign/p3_b4_launcher.py` の `_driver_configs`。
   base のとき `p3_s4_loop._current_site()` / `_admit_env_contract()` / `_campaign_cfg_for_site()`
   をどう呼ぶかを、trigger 分岐の現行コードと対比して書け。
2. **親の (P1) 3 件への判定。** 各々 real / refuted と、その根拠の file:line。
   - (P1-a) `_driver_configs` 内の分岐追加だけで足り、`prepare_launch` /
     `launch_bootstrap_impl` / `launch_continuation_impl` は変えなくてよい。
   - (P1-b) launcher 側で `ident.bind_admission_policy` は不要 (trigger が現にそうしている)。
   - (P1-c) `_campaign_cfg_for_site` は冪等で、driver 側の二重射影は campaign ID を変えない。
     冪等性は `ident.bind_environment_contract` の実装まで辿って判定せよ。
3. **base の授権境界 3 箇所** (`p3_s4_loop.py` の `require_b4_production_context` 呼び出し) の
   それぞれについて、修正後に `expected_campaign_id` が launcher の `context.campaign_id` と
   一致するかを、cfg がその地点で射影済みか未射影かまで辿って判定せよ。
   一致しない箇所が残るならそれを名指しし、scope 内で閉じられるか scope 外かを述べよ。
4. **`sort` を巻き込まない設計であること。** `p3_s4_loop_sort.py` には
   `_current_site` / `_admit_env_contract` / `_campaign_cfg_for_site` が存在しない。
   driver 種の一般 dispatch 表へ畳む案は sort を壊すので採らない。base の分岐追加に留める形を書け。
5. **test の設計。** `orchestrator/tests/test_p3_b4_launcher.py` には現在
   `site` / `PEGASUS` / `measurement_env` の出現が 0 件である。追加する test の
   - node 名、
   - 何を pin するか (受理側: 修正後に base の launcher ID が driver の要求と一致する)、
   - 対になる拒否側 (射影が無いと授権境界が現に拒否する) をどう書くか、
   - `site_policy.current_site` を PEGASUS_COMPUTE へ解決させる正規の注入 seam
     (monkeypatch は最後の手段。resolver / 環境変数 / 引数のどれが正規かを実装まで読んで決めよ)、
   - OTHER でも既存の緑を壊さないことをどう示すか、
   を書け。既存 test の書き方 (fixture、helper) に合わせること。
6. **触ってはいけない面。** 変更してはならない file と、その理由。

## 禁止

- 授権境界 `require_b4_production_context` の比較を緩める案を出してはならない。
  campaign ID の一致要求はそのまま。射影を足して「一致するようになる」のであって、
  比較を弱めるのではない。
- 未知 site の fail-closed (`_site_admits_measurement` の exact set) を広げてはならない。
- OTHER の campaign_id を変える案を出してはならない。
- `sort` の挙動を変える案を出してはならない ([T-2318] の scope)。
- [T-2317] の `_assert_layout_matches_campaign` / `_with_campaign_location` 移植を含めてはならない。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を足してはならない (依頼の明示指示)。
- 本題と無関係な refactor、命名変更、型注釈の整理を含めてはならない。

## 出力形式

以下の H2 見出しをこの順で使え。

## 機序の独立検証
## 変更プラン (file:line)
## (P1) 判定
## 授権境界 3 箇所の照合
## test 設計
## 触らない面
## 総括
