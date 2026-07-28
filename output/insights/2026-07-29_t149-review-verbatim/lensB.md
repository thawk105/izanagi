# 判定

現行 brief / plan v1 は段 5 へ進めない。特に S4 は「値不変」でも凍結 proof chain を即座に壊す。以下はすべて静的検査結果で、pytest は実走していない。

## 所見

### [B-1] must-fix — S4 は自己ハッシュ generator を変更し、既存 freeze を即時無効化する

file: `brief.md:20,32-45,51`、`plan-out.md:111-131,220,230`、`orchestrator/campaign/s1_known_axes_freeze.py:31,634-636,724-727`、`output/s1-freeze/known_axes_freeze.json:5-7`

`known_axes_freeze.json` は generator の SHA-256 `1d4d45…` を記録し、現行スクリプトの実 SHA も同値だった。S4 の import・定数変更は、評価結果が同じ文字列でもスクリプト bytes を変える。

具体経路:

1. `s1_known_axes_freeze.py` を変更する。
2. `verify_document()` が記録 hash と現行ファイル hash を `:724-727` で比較する。
3. `sources` や `SILO_CMAKE_REL` の値を調べる前に `generator sha256 不一致` で拒否する。
4. `s8b_oracle_driver.py:409-413` の legacy gate では `known-axes-freeze-verify` refusal になる。

freeze を更新する案も小差分ではない。`test_frozen_artifacts.py:38-46` の manifest、`s1_measurement_freeze.py:249-257`、`s8b_holdout_freeze.py:553,710`、さらに `s8b_ratified_freeze.py:61-62` の V1 束縛まで再裁定候補になる。

P2 は棄却すべきである。推奨は S4 を本 wave から外し、独立 hard-code を歴史的凍結レシピとして残すこと。ドリフトを可視化したいなら、自己ハッシュ generator を編集せず外部テストで一致を検査する。live import を維持するなら、別の freeze migration / ratification 裁定パッケージが必要。

### [B-2] must-fix — S5 の「被覆ゼロ」「単一帰属」は成立せず、S3 欠陥は無検出

file: `brief.md:35-37`、`plan-out.md:162-212`、`orchestrator/tests/test_campaign.py:2977-3000`、`orchestrator/tests/test_hooks.py:262-264`、`orchestrator/tests/test_s6_proposal_rounds.py:211-220`

静的な帰属表は次のとおり。

| 単一欠陥 | 新規で赤 | 既存で赤 | 帰属 |
|---|---|---|---|
| EBS だけを追加・並べ替え | S5a | `test_constants_match_source_digest` | 2 本以上。単一でない |
| ALLOWLIST から Options 等を欠落 | S5a | `test_source_digest_allowlist` | 2 本以上 |
| opened が旧 literal のまま | S5b | 該当なし | S5b だけ。純増 |
| regen が `+ ["include/backoff.hh"]` のまま | なし | freshness は `:219` で無効化 | 欠陥が生存 |
| `p3_s4_loop.SOURCE_REL` が EBS 外 | S5c |既存 p3 動作テストも経路次第で赤 | 単一帰属は未実証 |

S5b は `cc/silo/future.cc` を使うため、S3 の stale literal を殺さない。`cc/silo/future.cc` は既存の `git ls-tree cc/silo/` 走査だけで regen に入る一方、cc/silo 外の追加分は現行値でも提案値でも `include/backoff.hh` のままだからである。

S3 用に、例えば `include/future.hh` を live EBS と frozen map に追加し、正しい導出なら `[]`、旧 literal なら「領域集合不一致」になる別 focused test が必要。S5a は検出力ゼロではないが、「同期更新 mask を止める diagnostic pin」であり、単一変異の一意な kill として数えてはならない。

### [B-3] must-fix — 新規テストファイルが repo の runner 契約と import 前提を落としている

file: `plan-out.md:133-138,164-178,203-208`、`orchestrator/tests/README.md:53-74`、`orchestrator/tests/test_plain_runner_coverage.py:60-86`、`orchestrator/tests/conftest.py:19-22`

予定の `test_edit_surface_contract.py` には `_run()` / `__main__` がなく、README allowlist への追加もない。したがって全走では `test_every_test_file_is_self_runnable_or_allowlisted` が必ず赤になる。

また `conftest.py` は `sys.path` を設定しない。`test_s6_proposal_rounds.py:19-23` が自前で `orchestrator/` を挿入しているだけである。新規ファイルにも同等の bootstrap、または一貫した package import が必要。

この二テストは fixture 非依存なので、自走 harness を持たせるのが自然。pytest 専用にするなら `orchestrator/tests/README.md` を scope に追加する。

### [B-4] must-fix — brief の G05 放置影響は三箇所で不正確

file: `brief.md:25-34,43-47`、`source_digest.py:662-698,701-713`、`s6_proposal_rounds.py:148,231-236,361-362,467-475`

- S1 は逆である。EBS を増やして ALLOWLIST が古い場合、新ファイルは digest 対象には入るが、先行する `assert_worktree_within_allowlist()` が拒否する。「編集可能だが digest 対象外」の受理ではなく、正しい変更が fail-closed で止まる可用性問題である。
- S2/S3 が止めるのは freeze / verify / run 開始時の stale packet である。`cmd_score()` は scoring prompt の hash しか再検査せず freshness を呼ばない。したがって「採点が stale 面で継続」を一般に防ぐ変更ではない。
- S4 の放置影響は将来の protocol path drift だけではない。S4を実装すること自体が現在の generator hash を即時無効化する。

DW-G05 の成果物影響を、この実経路に合わせて書き直さない限り、must-fix 優先度と scope 判定が誤る。

### [B-5] should — S1 後の運用文書が追随 scope から漏れている

file: `docs/axis-onboarding.md:70-73,114-122`、`plan-out.md:27-35`

現行 onboarding は新しい SOURCE_REL について `EVOLVE_BLOCK_SOURCES/ALLOWLIST` の双方を拡張する手順を規定する。導出後は次の区別が必要になる。

- EBS ソース追加は ALLOWLIST へ自動伝播する。
- protocol CMakeLists 等の非 EBS build-input は Options と同じ「明示的な型付き例外」であり、別途 ALLOWLIST 式を拡張する。

これは active な軸導入手順なので、scope 外なら裁定パッケージ候補として返すべきである。`hooks/README.md` は既に EBS を正本として値を再掲しておらず、`phase3.md` と `check_docs.py` には今回の値不変変更に伴う必須追随は見つからなかった。

### [B-6] should — S5c は全編集 driver の膜ではない

file: `plan-out.md:201-212`、`p3_s4_loop.py:70`、`axis_trigger_gating.py:24`、`p3_s4_loop_sort.py:88`

実効 SOURCE_REL は少なくとも三つある。S5c は backoff driver 一つだけを検査するため、trigger-gating または sort driver が EBS 外へ移っても、名前が generic な `test_edit_surface_contract.py` は緑のままになる。

裁定候補は二択:

1. 三つを parameterize して全 writer target を膜内に置く。
2. scope を歴史的 backoff driver のみに狭め、テスト名・主張も限定する。

なお EBS 外への移動は通常 `assert_worktree_within_allowlist()` が拒否するため、直ちに未 digest の certified 結果になるのではなく、主な成果物影響は campaign abort である。

### [B-7] should — P3 の「親作」は可能だが、「小さく機械的」という根拠は破れた

file: `brief.md:52-56`、`plan-out.md:227-231`、`docs/dev-wave/workers.md:37,45-49`

親が直接実装すること自体は規約違反ではなく、段 6 の両レビュー対象にもなる。しかし現行 scope は自己ハッシュ freeze、テスト meta-contract、active onboarding 文書、変異帰属を含み、機械的差分ではない。

S4を外し、S1〜S3とテスト契約を修正した後なら親作は妥当。S4を維持するなら別 migration 単位として扱うべきで、現行 P3 のまま一枚岩にする根拠はない。

### [B-8] nit — import は現行三経路で循環しないが、二重 module identity を作れる

file: `plan-out.md:140-158`、`source_digest.py:70`、`pipeline.py:35-41`、`test_s6_proposal_rounds.py:19-23`

静的 import graph は以下で、循環はない。

```text
campaign.s6_proposal_rounds
└─ campaign.source_digest
   └─ campaign.model

campaign.s1_known_axes_freeze
└─ campaign.pipeline
   └─ campaign.source_digest
      └─ campaign.model
```

直接実行、現在の pytest import、既存 consumer `s6_amendment_20260713_fence.py:23-25` の `campaign.*` import は静的には解決する。

ただし他モジュールが `orchestrator.campaign.s6_proposal_rounds` として import すると、内部の絶対 import は別名の `campaign.source_digest` を生成しうる。呼び手が `orchestrator.campaign.source_digest` を monkeypatch しても S6 には届かない。完全に三経路を支えるなら、package import 時は相対 import、直接実行時だけ path 挿入へ fallback する方が module identity を保てる。

## 攻撃したが破れなかった点

- P1 の「freshness は live EBS と凍結 packet の一致検査」という意味自体は、`s6-round-execution-design.md:82-90` と整合している。
- S1 の `frozenset(EVOLVE_BLOCK_SOURCES) | {OPTIONS_CMAKE}` は現行値・型を変えない。
- S3 の union 算式自体は、closed を含む `cc/silo/` 母集団を維持しており正しい。破れたのはテスト被覆である。
- import 循環は実グラフ上存在しない。
- S5b は opened 述語に純増の検出力がある。S5c も backoff driver 一つに限れば純増である。

ファイル変更・pytest 実走はいずれも行っていない。