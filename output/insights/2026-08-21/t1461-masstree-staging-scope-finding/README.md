# [T-1461] floor campaign の Masstree staging transport — command 前提の誤りと実効化に要る設計の再スコープ

## 要約

[T-1461] は D399 (decisions.md:16805) の設計 (`IZANAGI_SORT_SWO_MASSTREE_ROOT` という
env var transport) に従い、`tools/pegasus/floor_campaign.sh`/`submit_floor.sh` の 2 file だけを
編集して masstree source のログインノード pinned staging → compute node 受け渡しを配線する
「最小実装」を目的として起票された。**本 wave は実装に着手する前の brief 段階で、この 2 file
だけの配線は floor campaign の実行経路に一切到達せず、実効性がゼロであることを file:line で
確認した。** さらに、段2 (codex プラン起草) と段3 (敵対相談 3 レンズ) による独立検証で、
「2 file の scope を超えて `s8b_floor_campaign.py` を最小限修正する」という代替案についても、
(a) command が明示的に禁じた measurement logic 領域への変更を要すること、(b) それでもなお
T-1431 の実障害 (計算ノードでの network 不可による FetchContent 失敗) を解消する保証がないこと、
(c) 独立に正しさ・信頼境界上の懸念 (config.h/archive の期待 hash 不在、pin 検査が CMake 実行後)
があることが判明した。**本 wave はコードを一切変更せず、設計択一と所見を裁定パッケージとして
記録する。**

## 背景

- [T-971] (2026-08-14、`docs/archive/worklog-phase3-0814-549.md`、D399) が
  floor campaign の masstree FetchContent staging を「scope 外の real 所見」として初めて特定した。
- [T-1431] (2026-08-20/21、`output/insights/2026-08-21_t1431-floor-pilot-resubmit/README.md`) が
  実際の床値 pilot 投入で同じ gap に再遭遇し、`rr20::sort_best` セルで
  `SortSwoOracleUnavailable: sort-swo-oracle-infrastructure-unavailable` により fail-closed
  停止した。この insight は「`tools/pegasus/floor_campaign.sh` に
  `IZANAGI_SORT_SWO_MASSTREE_ROOT` の配線を追加する」ことを次の一手として推奨し、これが [T-1461]
  起票の直接の根拠になった。
- [T-1128] (2026-08-21、entry 794) は本 wave 開始前日、同じ floor/build root 領域
  (`buildcache.prepare_masstree_fetchcontent`/`_v2_commands`) で owner 衝突を検出し、
  実装せず停止する裁定を下していた。本 wave の開始時重複チェックでは、この owner
  (`t-1431 floor pilot recompute` peer) は既に完了・land 済みであることを確認し、
  新たな衝突は検出しなかった。

## 発見: `IZANAGI_SORT_SWO_MASSTREE_ROOT` は floor 実行経路から参照されない

file:line 裏取り (基準 commit `b1c54220`、`orchestrator/campaign/s8b_floor_campaign.py`):

- 行129-138: `sort_swo_oracle` から `OracleEnvironmentCandidate`/
  `OracleEnvironmentResolutionFailure`/`OracleInfrastructureFailure`/`OracleStatus`/
  `SortSwoOracleResult`/`SortSwoOracleUnavailable`/`INFRASTRUCTURE_REASON_CODE`/
  `private_attempt_record` の**型・定数だけ**を import する。`resolve_oracle_environment()`
  (`IZANAGI_SORT_SWO_MASSTREE_ROOT` を読む関数本体、`sort_swo_oracle.py:1102-1133`) は
  import も呼出しもされていない (grep 実測 0 件)。
- floor 独自の masstree 依存解決は別経路として存在する:
  `_canonical_floor_fetchcontent_base()` (2301行) → `_prepare_floor_oracle_dependency()`
  (2414行) → `buildcache.prepare_masstree_fetchcontent()` (呼出しは2433行)。
- この経路への注入点は `build_cells()` の `fetchcontent_base_dir` 引数
  (2933-2938行、段2 codex が `_run_campaign_core` という親の当初認定を訂正) である。
- production wrapper `run_campaign()` (5628-5688行) と `_run_campaign_core()`
  (5691-5700行、fresh/resume 双方の `build_cells()` 呼出し 6085-6090/6150-6155行) は
  この引数を一切公開・転送していない。CLI `_parser()` (6832-6845行) にも対応 flag が無い
  (`--mode`/`--protocol`/`--resume`/`--confirm-irreversible-pilot-holdout` の 4 つのみ)。
  `run_campaign(` の他の呼出し元 (grep 全件確認、`p2_2.py`/`sanity_silo.py` 等は同名の別関数) にも
  `fetchcontent_base_dir=` を渡すものは無い。
- 結論: production では `fetchcontent_base_dir` は常に `None` となり、
  `_canonical_floor_fetchcontent_base` は毎回 `$TMPDIR` 配下に新規 mkdtemp
  (2305-2353行) → 毎回ネットワーク越し `buildcache.prepare_masstree_fetchcontent` を試みる
  (2433-2439行) → 計算ノードで network 不可のため fail。これは T-1431 が実際に踏んだ経路と
  一致する。

**したがって、`floor_campaign.sh`/`submit_floor.sh` だけで
`IZANAGI_SORT_SWO_MASSTREE_ROOT` を login staging から export しても、floor driver は
この値を一切読まないため実効性はゼロである。** D399 (env var transport の設計自体) と
`sort_swo_oracle.resolve_oracle_environment()` (その実装) はいずれも正しく、
T-971/T-1431 当時に想定された consumer だったと思われるが、floor 実行の実際の call graph は
これとは別の経路に分岐している。

## 段2 (codex plan、read-only、reasoning=max) の検証結果

上記認定を独立検証し、3 案を file:line 粒度で提示した
(`stage2-plan-output.md`、check_codex_output.py rc=0)。

- **案A (command 文字通り、shell 2 file のみ):** 上記の理由により効果ゼロの dead wiring。
- **案B (実効化に要る最小差分):** `run_campaign()`/`_run_campaign_core()`/`build_cells()`
  呼出し/CLI `_parser()`/`main()` へ `fetchcontent_base_dir` の pass-through を追加
  (振る舞い変更なし、未指定時は現行 `None` デフォルトを維持)。これは
  `orchestrator/campaign/s8b_floor_campaign.py` という command が明示的に禁じた
  「measurement logic」領域への変更を伴う。
- **案C (shell 内 inline Python monkeypatch):** `s8b_floor_campaign.py` を1バイトも
  変更しない代替。ただし段2案が提示した具体形 (`run_campaign` を差し替える) は
  現行 signature と不一致で `TypeError` になり動作しない (段3 scope レンズが検出)。
  動作させるには内部 symbol `build_cells` の runtime patch が必要で、CLI contract の
  二重化・provenance/テスト契約からの逸脱を伴う。

新規 test file は不要 (既存 `test_s8b_floor_campaign.py`/`test_pegasus_floor_tools.py`/
`test_buildcache_v2.py` の tmp-path/fake-subprocess harness を流用可能、との見込み)。

## 段3 (敵対相談、3 レンズ並列、read-only、reasoning=max、--lane luna) の検証結果

3 レンズとも独立に「本 wave では実装しない」方向へ収束した。

### レンズ1: scope・権限 (`stage3-lens-scope-output.md`)
推奨は **(iv) docs-only で裁定パッケージを返す**。案Bは「既存 seam への pass-through」と
弁護できるが、実際には production の依存物・実行可否・測定対象 binary を変える
(`s8b_floor_campaign.py:2301-2353`, `6085-6090`, `6150-6155`)。案Cは提示形のままでは
`TypeError` で動かず、動作版も `build_cells` という内部 symbol への runtime patch になり
案Bと同程度に production semantics を変える。command の shell-2-file scope 照合は
「編集の前提条件」であって Python production driver への許可を意味しないと判定した。
また親 brief 自身の飛躍 (seam の所在を `_run_campaign_core` とした誤り、「計算ノードは
常に fail」という過度な一般化、「command 起草者が誤りに気づいていなかった」という断定) を
訂正した。

### レンズ2: 正しさ・信頼境界 (`stage3-lens-correctness-output.md`)
CONFIRMED/P1 が 2 件:
1. `config.h`/`libkohler_masstree_json.a` の**期待 hash が独立に束縛されていない**。
   HEAD は共有 policy pin と照合される (`s8b_floor_campaign.py:2027-2057`, `2268-2275`) が、
   config/archive の hash は compute 側の現在値を計算するだけで (`2276-2298`)、
   login 側 payload や改変後の値と照合する「期待値」が存在しない。D399 自身が
   「残余」として認めていた未解決事項 (`decisions.md:16823-16840`) と一致する。
2. **pin 検証が CMake 実行の後に行われる**。`_prepare_floor_oracle_dependency()` は
   先に `prepare_masstree_fetchcontent()` (2414-2458行) を実行し、その後で
   `_verify_floor_oracle_dependency_source()` (2469-2472行) を呼ぶ。HEAD 不一致・改変済み
   生成物は拒否される前に CMake/FetchContent へ入力される。規律6 (信頼境界: 外部データは
   先に検査してから使う) の観点で不十分。
   
CONFIRMED/High が 1 件 (login node の network 到達性が未検証・未束縛。
`docs/pegasus-runbook.md:748-771` の「proxy 経由の CMake/Git 可否は一般化しない」との
整合が取れていない) と、CONFIRMED/PLAUSIBLE が 1 件 (`buildcache.py:2169-2179` に
既記録の絶対 path relocation 実障害と同種のリスクが、login→compute 間のコピーでも
再発しうる) だった。

### レンズ3: 技術的実効性 (`stage3-lens-effectiveness-output.md`)
**最も重大な追加発見。** `_prepare_floor_oracle_dependency()` は `fetchcontent_base_dir`
に既に有効な hydrate 済み payload があるかどうかに関わらず、**毎回無条件で**
`buildcache.prepare_masstree_fetchcontent()` (ネットワーク越し configure/build) を
呼び出す (`s8b_floor_campaign.py:2419-2439`、helper 自体にも skip 分岐なし
`buildcache.py:1351-1412`)。**つまり案B/Cの「pass-through 追加」だけでは、
production wrapper/CLI へ配線が通ったとしても、compute node は依然として
毎回ネットワーク越しビルドを試み、T-1431 と同じ理由で fail する。** 実効化には
`_prepare_floor_oracle_dependency` 自体 (または呼出し判断) へ「有効な pre-verified
payload があれば network build を skip する」分岐を新設する必要があり、これは
段2で既に scope 外と識別された measurement logic への変更よりもさらに一段深い。

また、silo_ladder_rung1 の先例 (`silo_ladder_rung1.sh:17-31`, `343-383`) は
「ビルド済み archive の transport」ではなく「未ビルド pinned source の transport
(`IZANAGI_THIRDPARTY_SOURCE_ROOT`、`cp -a`) + compute 側での `-DFETCHCONTENT_SOURCE_DIR_*`
によるビルド」であることを確認した。floor の `FETCHCONTENT_BASE_DIR` 方式より
FetchContent の populate stamp に依存しない分、実効性の不確実性は低いと考えられるが、
`buildcache.py`/receipt/postflight/dependency identity の変更を要し「最小差分」では
なくなる。

結論: **案B/Cは実装前に、実際の計算ノード上で (network 不可条件下)
login-side payload の transport → 再取得なし → configure/build 成功 → postflight 成功、
を確認する DW-G01 生死実験が必須。**

## 裁定 (段4、親)

3 レンズすべての独立な収束を踏まえ、次のとおり裁定する。

1. **本 wave ではコードを一切実装しない。** 案A (command 文字通り) は効果ゼロと判明した
   ものを実装するだけであり、無意味である。案B/Cは command が明示的に禁じた
   measurement logic 領域への変更を要し、かつそれだけでは目的 (T-1431 の解消) を
   達成できないことが判明した。DW-S04 に従い、scope 外の real 所見として設計択一と
   所見を裁定パッケージにまとめ、実装しない。
2. **[T-1461] の次の一手を本 insight を指す形に更新する** (worklog 次の一手差分)。
   元の「2 file の最小配線」という記述は前提の誤りに基づくため置き換える。
3. **[T-1431] の床値 pilot 再投入は引き続き blocked のまま**、command 指示どおり本 wave の
   scope 外とする。
4. **将来この問題に再着手する場合の推奨スコープ**(ユーザーが明示的に scope を
   拡大した場合の出発点):
   - `_prepare_floor_oracle_dependency()`/`buildcache.prepare_masstree_fetchcontent()` に
     「有効な pre-verified payload があれば network build を skip する」設計を新設する
     (measurement logic 変更、Codex `role=author` 必須、D95)。
   - config.h/archive の期待 hash を独立に束縛する設計 (D399 の「残余」を閉じる) と、
     pin 検証を CMake 実行前に前倒しする順序修正を同時に行う。
   - 実装前に DW-G01 の生死実験 (計算ノード 1 回、network 遮断条件で
     transport→no-refetch→build 成功を確認) を先行させる。
   - silo_ladder_rung1 の `FETCHCONTENT_SOURCE_DIR_*` 方式への統一 (第4の設計、
     populate stamp 依存を回避できるが `buildcache.py`/receipt/postflight の変更を伴う)
     を代替案として比較検討する。
   - これは「最小実装」ではなく独立した設計・実装プロジェクトであり、専用の
     dev-wave (段1 brief から) として起票するのが適切。

## 証拠・成果物の所在

- 段2 codex plan: `/work/SFC/tanab/dev-wave-jobs/2026-08-21_t1461-masstree-staging/stage2-plan-output.md`
- 段3 敵対相談 3 レンズ:
  `/work/SFC/tanab/dev-wave-jobs/2026-08-21_t1461-masstree-staging/stage3-lens-{scope,correctness,effectiveness}-output.md`
- 各 receipt (`schema_version=3`) は同ディレクトリ配下の `<job-id>/receipt.json`、
  いずれも `check_codex_output.py` rc=0、`codex_exit_code=0`。
- 親 handoff (作業中の生きた進捗): `docs/handoff/2026-08-21-t1461-masstree-staging.md`
  (worklog 吸収後に削除予定)。

## エージェント工数

Codex 子 4 本 (段2 plan 1 本、段3 consult 3 本)、いずれも `gpt-5.6-luna`・`reasoning=max`・
`sandbox=read-only`。実装子 (author/review/fix) は 0 本 (「実装しない」裁定のため段5/6省略)。
