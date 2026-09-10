単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/brief.md` — 親の段 1 brief (逐語)。**検査対象である。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s2-plan.md` — 段 2 プラン (逐語)。**検査対象である。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値 (逐語)。**検査対象である。**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/ident.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/env_contract.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py`

repo の path は上記 worktree のものだけを使う。親 checkout の path を使ってはならない。

## 段の宣言

これは段 3 (敵対相談) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。**
実走していない検査を「通した」と書いてはならない。コードを編集してはならない。commit してはならない。

**プランを守るな。壊せ。** 同意を求められていない。所見が出ないこと自体が失敗である。
予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ: 正しさ境界と授権の実効性

[T-2316] は B-4 の授権境界 (`require_b4_production_context`) に関わる変更である。
このレンズは「正しさ防壁が本当に効いたままか」「修正が防壁をすり抜けさせないか」だけを見る。

次を順に攻撃せよ。所見ごとに **real / refuted** を自分で判定し、根拠を file:line で示せ。

1. **修正は不一致を直すのか、移すだけなのか。**
   `_driver_configs` に base 射影を足したあと、正式経路
   (`launch_bootstrap` / `launch_continuation` → `p3_s4_loop.main` → `drive_iteration`
   → resolved iteration) の**すべての** ID 比較地点で、launcher 側 ID と driver 側
   `expected_campaign_id` が本当に一致するか。プランの「授権境界 3 箇所の照合」表を信用せず、
   自分で辿れ。sidecar (`write_sidecar`) と `exploration_campaign_layout` の
   campaign dir 名の一致も見よ。WAL commit 側の sidecar 照合
   (`p3_b4_launcher.py` の 412-435 行付近、`Path(layout.root).name != expected["campaign_id"]`)
   も対象に含めよ。

2. **防壁が弱まらないか。**
   射影を足すことで、これまで拒否されていた入力が受理されるようになる面はないか。
   特に `validate_production_context` / `require_b4_production_context` /
   `require_any_context` の受理集合が、driver_kind ごとにどう変わるか。
   「一致するようになる」のは正しい修正だが、「別の何かも一緒に通るようになる」なら real 所見である。

3. **新しい fail-close の向き。**
   親の実測 (parent-measurements.md 実測 1・2) は、修正後 base の `_driver_configs` が
   `PEGASUS_LOGIN` 上で `ExecutionGuardError` を投げるようになることを示す。現状は投げない。
   - これは安全側か危険側か。trigger は現に同じ挙動なので base を揃えるのは整合的か。
   - この例外が **握りつぶされる経路**が無いか。呼び出し元 (`prepare_launch` の caller、
     CLI `main`、test helper) を辿り、`except Exception` や `contextlib.suppress` で
     飲み込まれて「静かに未射影のまま進む」経路が残らないか確かめよ。
     もしあれば、それは規律 2 に触れる real 所見である。
   - `PEGASUS_SUSPECT` に解決される条件 (`site_policy.classify_site` の
     `has_nqsv` 分岐) でも同じ議論が成り立つか。

4. **test の正例・負例が機構を本当に通るか。**
   プランの test 設計 (3 node) を攻撃せよ。
   - 負例 `test_base_unprojected_pegasus_context_is_rejected_by_driver_authorization` は、
     **今回入れる機構 (`_driver_configs` の base 射影)** が無いときに赤くなるか。
     それとも `_driver_configs` を一切通らずに手で作った config だけで赤くなり、
     機構の有無と無関係に恒真な赤になっていないか。**これが最重要の攻撃点である。**
   - 正例は「実体を名指し」しているか。driver の `main` / `drive_iteration` を stub して
     しまい、両層 stub で機構を通らない緑になっていないか。
   - 赤理由が一つに絞れるか。同じ入力を拒否する層が前後にも内側にも無いか
     (前段の admission 検査、`require_any_context`、`validate_production_context` の
     どれかが先に拒否して、campaign ID 比較まで到達しない可能性)。
   - `site_policy.socket` の差し替えは `current_site` を通る seam として正しいか。
     `conftest.py` の中立化と衝突しないか。conftest が先に `socket` を差し替えている場合、
     test 内の再差し替えが効く順序になっているか。

5. **親の実測とその一般化を攻撃せよ。**
   - probe は `create_b4_launch_context_for_test` で作った **test-only** context を使っている。
     production context と search_config が同じとは限らない。
     campaign ID の変化幅 (`4e54b9ea` → `c510996c`) を production 経路の値として
     一般化してよいか。よくないなら、何を測り直すべきか名指しせよ。
   - probe は `site_policy.socket` を module 属性ごと置き換えている。
     `current_site` が `socket` 以外の入力 (`_has_nqsv`、`os.environ`) も読むなら、
     probe が作った site は production の site と同じ導出過程を通っていない可能性がある。
   - 親 brief が当初 `classify_site` を 2 値と読み違えていた事実を踏まえ、
     brief と plan に**他にも同種の読み違い**が無いか探せ。

## 禁止

- 授権境界の比較を緩める案を出してはならない。
- 未知 site の fail-closed を広げる案を出してはならない。
- OTHER の campaign_id を変える案を出してはならない。
- `sort` の挙動を変える案を出してはならない ([T-2318] の scope)。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を提案してはならない (依頼の明示 scope 外)。
  scope 外だが real な所見は「実装せず裁定へ返す候補」として明記せよ。

## 出力形式

以下の H2 見出しをこの順で使え。所見には通し番号 A1、A2、… を振れ。

## 所見 (real)
## 所見 (refuted)
## scope 外だが real (裁定へ返す候補)
## 総括
