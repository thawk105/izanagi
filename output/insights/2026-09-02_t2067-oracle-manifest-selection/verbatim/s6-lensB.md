## 所見 1 — 受理集合の縮小は g1 の選択検査に限定される

- 所見: 新たに拒否されるのは、loader が返した g1 が床値選択検査で `floor-selection-unverifiable`、`floor-selection-eligibility-underivable`、`floor-selection-rule-mismatch` になる場合である。後段でもともと拒否される入力は受理集合自体は変わらず、先に選択理由が返るようになる。g2 は D1370 の狭い API の no-op 契約に委ねられ、loader 自身が例外を出す経路は gate に到達しない。
- 根拠 (file:line): [s8b_oracle_manifest.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1205) で load 直後に exact `(ratified, root)` を渡し、[s8b_oracle_manifest.py:1214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1214) より前に検査する。g1 限定の契約は [rulings-verbatim.md:40](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:40)。patch と現物に食い違いはない。
- 成果物影響: 選択違反 g1 からの manifest 生成だけが止まり、選択適合 g1 と g2 の manifest 値と参照は変わらない。後段拒否入力では成果物は前後とも生成されず、観測 reason だけが変わり得る。
- must-fix か nit か: nit なし。意図どおりで must-fix ではない。ただし狭い API 本体は射影対象外のため、g2 no-op の実装本体までは本レビューで再監査していない。

## 所見 2 — consumer の reason 集合は既存の選択系 3 理由だけ増える

- 所見: 差分前の loader、spec、manifest 構築、writer の理由集合に、上記の選択系 3 理由が manifest consumer から新たに観測可能になる。新しい理由名は発明していない。`no-active` だけを `no-active-ratified-freeze` に写す既存規則と、それ以外の素通しは維持される。
- 根拠 (file:line): [s8b_oracle_manifest.py:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1207) の同一 except と [s8b_oracle_manifest.py:1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1209) の exact mapping。理由素通し方針は [ruling.md:75](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/ruling.md:75)。負例は [test_s8b_oracle_manifest.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1521) で外側と cause の理由を固定している。
- 成果物影響: 新たな選択理由では writer 前に停止して manifest と参照を作らない。loader 由来の既存拒否では成果物、受理集合、reason のいずれも変わらない。
- must-fix か nit か: nit なし。must-fix ではない。

## 所見 3 — test 間 import に静的な collection 障害は見当たらない

- 所見: 単独 file 走では test directory を明示的に `sys.path` へ入れてから import するため解決できる。全走では同名 module が `sys.modules` で共有され、xdist では worker ごとに独立して同じ処理を行う。import された module の top-level に repository や tmp への書き込みはなく、collection 順序を変える副作用も見当たらない。既存にも test module から別 test module の private helper を import する先例がある。
- 根拠 (file:line): path 設定は [test_s8b_oracle_manifest.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:16) と import は [test_s8b_oracle_manifest.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:29)。被 import 側も [test_s8b_ratified_freeze.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:28) で同じ設定を行い、既存先例は [test_s8b_ratified_freeze.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:51)。conftest は射影対象外なので固有 hook は未確認だが、名前解決自体は conftest に依存しない。
- 成果物影響: production 成果物、受理集合、参照への影響はない。残るリスクは test basename や pytest import mode を将来変更した際の collection 保守性だけである。
- must-fix か nit か: nit。test module への直接依存は共有 fixture module より脆いが、現状の単独、全走、xdist に collection error を生む具体的要因はない。

## 所見 4 — 共有 helper の前提や状態は変更されていない

- 所見: `build_production_emitter_g1` と `_commit_exact` の定義は変更されず、新規 test が既存 helper を呼ぶだけである。各 builder は test 固有 `tmp_path/repo` を作り、`_commit_exact` は staged path と commit path の完全一致を検査する。`_derive_floor_selection_eligibility` の差し替えは `monkeypatch` により test 終了時に復元される。
- 根拠 (file:line): helper 定義は [test_s8b_ratified_freeze.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:286) と [test_s8b_ratified_freeze.py:966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:966)。新規使用は [test_s8b_oracle_manifest.py:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1475)、[test_s8b_oracle_manifest.py:1499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1499)、[test_s8b_oracle_manifest.py:1511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1511)。
- 成果物影響: production manifest の値、受理集合、参照には影響しない。test 間でも repository 状態は共有されない。
- must-fix か nit か: nit。`_commit_exact` と `_derive_floor_selection_eligibility` という private 名への cross-module 依存は rename に弱いが、正しさの問題ではない。

## 所見 5 — D1370 と non-certifying 上限を越えていない

- 所見: 差分は narrow API を 1 回呼ぶだけで、`launch_validate`、activation HEAD、current admission、closure、binding graph、live scan、selected certificate、path 起動秒の検証を追加していない。production docstring に認証主張を加えておらず、新規 test 名も gate の実行と理由伝播だけを主張している。
- 根拠 (file:line): production 差分は [s8b_oracle_manifest.py:1206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1206) の 1 行だけ。禁止境界は [rulings-verbatim.md:42](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:42) と [rulings-verbatim.md:53](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:53)。fixture 自身も [test_s8b_ratified_freeze.py:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:972) で固定 seam かつ実測代表 bytes ではないと明記する。
- 成果物影響: 選択 identity 以外の理由で manifest の受理集合を狭めず、certificate や起動秒を新しい参照として成果物へ焼き込まない。D1241/D1313 の advisory、non-certifying 上限は維持される。
- must-fix か nit か: nit なし。must-fix ではない。

## 所見 6 — 同 module の公開迂回口は残るが既裁定どおり scope 外

- 所見: 強制点は production CLI の `build_approved_manifest` だけである。`build_manifest` は任意 freeze path から、`build_manifest_from_ratified` は loader token から、選択 gate なしで `OfficialManifest` を返し、`write_manifest` がそれを書ける。したがって「module 内の全生成入口」という意味では強制は網羅的でない。一方、これは ruling が real だが scope 外とし、実装対象を 1 箇所へ固定した既知境界である。parser/main に別の approved production 入口はない。
- 根拠 (file:line): [s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:818)、[s8b_oracle_manifest.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:842)、[s8b_oracle_manifest.py:902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:902)。scope 裁定は [ruling.md:24](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/ruling.md:24)、[ruling.md:46](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/ruling.md:46)、[ruling.md:100](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/ruling.md:100)。
- 成果物影響: generic 入口の直接 caller は、選択違反 g1 を参照する manifest bytes を従来どおり構築、保存できる。本差分による値や受理集合の変化はなく、production approved CLI だけが新たに拒否する。
- must-fix か nit か: nit。本 wave では既裁定により scope 外なので must-fix ではない。

## 総括

must-fix 0件。受理集合は production approved CLI における選択違反 g1 だけ縮小し、g2、loader 例外経路、generic builder の受理集合は不変である。pytest は本レビューでは実行していない。