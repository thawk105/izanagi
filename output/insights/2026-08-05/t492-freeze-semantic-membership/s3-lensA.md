結論は **NO-GO** です。`s1_known_axes_freeze` 内の二つの検査位置は妥当ですが、freeze 族全体の受理経路、proof-chain 帰属、次回 refreeze の閉包が未処理です。以下は静的レビューであり、pytest は実走していません。

## 成立している点

- main/remeasure provenance から known freeze を作る公式経路は、`generate()` → `build_document()` → `_trigger_entries()` です。[build_document:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:621)、[generate:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:774)。この経路では提案位置を迂回できません。
- `"izanagi_gate_pass = true;"` は既存権威でも明示的な非 member です。[is_canonical_predicate:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/trigger_gate_binding.py:113)、[既存負例:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_trigger_gate_binding.py:234)。両 provenance をこの値に揃えれば、生成側・doc 側の新検査はいずれも発火します。恒真な検査ではありません。
- `_validate_schema()` への配置は、通常 verify、measurement、T-080 の双方へ届きます。[verify_document:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:720)、[measurement:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_measurement_freeze.py:160)、[T-080 delegate:1812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1812)、[static adapter:2084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:2084)。
- `source_resolver` は schema 検査より後なので、別 root を指定しても非正準 doc は resolver 到達前に拒否されます。ただし generator は module-global `ROOT` を見るため、verify 全体が任意 root に対して hermetic という意味ではありません。[generator check:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:724)、[resolver:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:729)。
- `validated_target(..., verify_fn=noop)` は `_validate_schema()` も迂回します。現在使用する read-heavy/system_gate 一値は consumer-local gate が拒否するため実値は守られますが、「差し替え verifier でも doc 全体を検査する」という P2 の帰属にはできません。[verified target:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_verify_extime_calibration.py:202)、[sink gate:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_verify_extime_calibration.py:216)。

## 所見

### F1 — real / blocker: holdout freeze の生成・受理経路が検査を通らない

根拠となるコールグラフは次です。

```text
非正準な known_axes JSON
  → s8b_holdout_freeze.build_document()
  → _load_json(root / KNOWN_AXES_REL)
  → build_variant_binding()
  → _strip_measurements() で gate_predicate をそのまま複製
  → holdouts.*.variant_binding.entries.*
  → generate() が holdout freeze を書く
```

`build_document()` は known doc を読みますが s1 validator を呼びません。[load:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:524)、[binding copy:472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:472)、[write:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:585)。`verify_document()` も known bytes の hash と同じ無検査の binding 再構成だけです。[known load:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:749)、[binding verify:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_holdout_freeze.py:809)。manifest と ratified 層も意味ではなく参照 hash を検査します。[manifest:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_manifest.py:848)、[ratified:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_ratified_freeze.py:948)。

放置すると、`holdouts.{rr20,rr80}.variant_binding.entries.{system_gate,ident_all}.gate_predicate` と、それを指す `known_axes_freeze.sha256` を整合したまま非正準にできます。現行の公開 oracle driver は最後に legacy/T-080 known gate で拒否するため誤 certification は防ぎますが、holdout 凍結台帳・manifest・ratified 参照は先に成立し、材料レポートと campaign は判定不能になります。

この層まで同 wave で閉じるか、generator hash/T-080 cascade を伴う別裁定パッケージにする必要があります。現プランのまま「freeze 族では生成も受理も不能」とは言えません。

### F2 — real / blocker: membership 権威が凍結 proof chain に帰属していない

新しい受理集合は `trigger_gate_binding.py` と、その入力を生成する `reflux_ir.py` に依存します。[index:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/trigger_gate_binding.py:97)。しかし known freeze の generator hash は `s1_known_axes_freeze.py` 一ファイルだけです。[generator record:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:634)。trigger entry の source closure も `axis_trigger_gating` と `s8a_trigger_sweep` だけで、新しい二依存を含みません。[common sources:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:499)。

さらに、将来生成される台帳の `selection_rules.system_gate` は main/remeasure 完全一致しか記述せず、membership gate を記録しません。[selection rule:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:657)。

放置すると、helper/emitter の連動 drift で受理集合が変わっても、凍結台帳には「どの semantic authority で受理したか」の source hash が残りません。T-490 の sink も同じ権威を使うため、権威側の common-mode drift では certified 選択・材料 source・試行台帳が一緒に変わり得ます。

現行 artifact を再発行せずとも、将来の生成結果には少なくとも権威二ファイルの source record または同等の immutable digest と、membership を明記した selection rule が必要です。これに伴う独立 golden の source layout 更新もプランへ入れるべきです。

### F3 — real: 親の「1 failed / 222 passed」からの一般化は成立しない

brief は変異した一行、baseline、実行した7ファイル、runner command、skip node/reason、復元確認を記録していません。[brief:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/brief.md:23)。したがって再現可能な実測手続きになっていません。

また、一行編集で見えた赤は、legacy verifier が source resolver より先に live generator SHA を比較するための診断順位です。[generator check:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:724)。T-080 active は historical blob を照合し、reconstruction から generator cell を除くため live 編集を許しますが、never-issued は legacy verify を呼びます。[metadata closure:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1072)、[generator exclusion:1100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1100)、[legacy branch:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:406)。これは「現行 active receipt が live generator drift を許す」という限定的事実であり、generator 編集一般の安全性ではありません。

関連テスト面も7ファイルより広く、holdout、materialization、manifest、ratified、report、T-080、frozen manifest 等があります。既存 exact pin も `test_reflux_ir` だけではなく、独立 literal golden が既にあります。[known test:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s1_known_axes_freeze.py:52)、[independent predicate golden:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/s1_expected_goldens.py:624)。

放置時は、多くの場合 fail-closed で certified 値そのものは出ませんが、measurement/holdout/manifest のどこで赤くなるか未確定のまま、材料レポートと凍結台帳が使用不能になります。結論は「限定 probe」へ格下げし、実装後の対象集合＋全受入で再測定すべきです。

### F4 — real / blocker: 次回 refreeze は T-080 receipt を必ず無効化する

次回 refreeze では少なくとも `/generator/sha256` が変わり、known freeze raw SHA も変わります。[build_document:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:636)。一方、T-080 は旧 known/holdout raw SHA を定数で固定しています。[T-080 pins:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:44)。`verify_receipt()` はこの定数で artifact をロードするため、新 raw bytes では receipt refusal になります。[artifact load:1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/t080_freeze_migration.py:1936)。その refusal は legacy verify が通っても最終 decision に残ります。[decision merge:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_oracle_driver.py:121)。

したがって「T-492 を入れれば次回 refreeze が可能」ではありません。T-080 receipt の supersede/retire、known→measurement→holdout→manifest/ratified の再発行順、旧参照の扱いが別途必要です。放置すると新しい凍結台帳は作れても公開 gate は常に拒否し、certified 選択・材料レポートは生成できません。これは実装したふりにせず、次回 refreeze の必須裁定パッケージとして分けるべきです。

### F5 — real: テスト計画の public wiring 帰属が弱い

`test_verify_document_rejects_noncanonical_predicate_before_rebuild` が現行 artifactを使い、単に `FreezeError` だけを期待すると、membership を削除しても stale generator SHA で先に `FreezeError` となり偽緑です。plan 自身も generator/reconstruction による別拒否を認めています。[plan:143](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-out.md:143)、[plan:177](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t492-freeze-semantic-membership/plan-out.md:177)。

また、新規テストは s1 内の直接検査に集中し、T-080 active/public gate で非正準値が `known_axes.schema` refusal になる配線テストを計画していません。static-adapter 系既存テストは `_verify_known_schema` を pass stub にしています。[test helper:1128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/tests/test_s8b_oracle_driver.py:1128)。

放置すると `_validate_schema` の単体 gate は存在しても、公開 consumer からの call-site 脱落を mutation が検出しません。将来 T-080 移行時に凍結台帳が受理され、後段 sink で初めて拒否されるため材料レポートが作れません。

public wiring テストは診断を `正準集合外` に完全固定し、generator/hash/resolver が呼ばれないことも spy で検査してください。T-080 active 経路についても、schema call-site 削除を一意に殺す node を追加すべきです。

### F6 — real / scope 外裁定候補: canonical だが名前と違う mask は通る

具体例として、main/remeasure の `entries.g_rl.implementation` を両方とも mask 4 の emitter 文、つまり `g_rt` 相当へ変えるとします。これは32集合の memberなので新検査を通り、完全一致も通ります。[equality:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:493)。pairing は system/ident の述語が異なることしか見ません。[pairing:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:594)。

放置すると `name="g_rl"` のまま mask 4 の source が materialize され、T-490 sink も canonical member として受理します。これは certified 選択、材料レポート、試行台帳の configuration 名と実 CC を食い違わせ、誤 certification まで到達し得ます。

これは今回の「集合外だけを拒否する」という狭い裁定を否定しませんが、brief の「name→mask 表に依存しない」は保証ではなく、未保護面の宣言です。別 P1 裁定候補として起票すべきです。

## `.strip()` 受理集合の判定

この変更による受理集合の拡大はありません。変更前は main/remeasure が同じ `str` なら外周空白付きも既に生成可能で、変更後はその集合と strip-membership の積集合になるためです。

T-490 U-1 により、外周空白は materialize 前に emitter bytes へ畳まれます。[canonicalization:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/p3_s4_loop.py:202)。したがって materialized source・`src_token`・variant ID は統合されます。一方、raw freeze bytes と S8b の `entry_sha256` / `binding_sha256` は空白に敏感なままです。[binding hash:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s8b_materialization.py:117)。これは T-490 で意図的に残した境界であり、T-492 が新たに作る変更ではありません。

P3 の test-local `ROOT` patch は、期待する source mismatch までで停止する限り目的を保ちます。ただし再構成まで進むと、import 済み module の `__file__` が patched root 外となり `_module_source()` が別理由で落ちます。[module source:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t492-freeze-semantic-membership/orchestrator/campaign/s1_known_axes_freeze.py:109)。成果物影響はないため、これは nit です。長期的には plan が挙げた隔離 subprocess の方が hermetic です。

## 総括

**NO-GO**

- blocker 1: `s8b_holdout_freeze` の生成・verify が非正準 known doc を無検査で variant binding へ凍結できる。
- blocker 2: `trigger_gate_binding` / `reflux_ir` と membership selection rule が将来の known freeze proof chain に帰属しない。
- blocker 3: 次回 refreeze は T-080 receipt を必ず無効化するのに、supersede 手順と active/public 配線の検出テストが未計画。