静的レビューは修正要求です。production 実装の中心経路は裁定を満たしていますが、回帰を見逃す must-fix のテスト穴が 3 件あります。

## 所見

**所見 1**: M4 のテストは `build_v2()` から identity への配線欠落を殺せない

- **具体的失敗**: [buildcache.py:2333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2333) の policy ID と manifest hash の `_v2_identity()` 引数を両方削除する。直接 `_v2_identity()` を呼ぶテストは手動で policy を渡すため通る。統合正例も post-oracle 側だけ archive hash を identity に持ち、generic 側は archive hash を省略しているため、policy 配線がなくても `build_dir` は異なり、全 assert が通る。
- **成果物影響**: 同一 receipt、archive の禁止前 entry を post-oracle build が hitし、flag 無しで作った binary が flag 付き `configure_argv` として floor manifest、レポート、台帳へ入る。
- **区分**: must-fix。generic build を同じ base、receipt、archive で先に seedし、同じ材料の capability build が必ず missする統合テストが必要。

**所見 2**: oracle receipt の manifest hash 照合だけを外す回帰が偽緑になる

- **具体的失敗**: [buildcache.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1073) の raw `SHA256SUMS` hash 比較だけを削除する。追加テストは `tracked.hh` だけを書き換え、ローカル manifest は変更しないため、後続の per-file hash 検査で従来どおり赤になる。一方、`tracked.hh` とその `SHA256SUMS` 行を同時に書き換え、HEAD、config、archive を維持すると、receipt 権威を見ない実装は通る。
- **成果物影響**: oracle が判定した manifest と異なる自己整合的な材料から binary が生成され、certified 床値の材料参照だけが旧 receipt のまま残る。
- **区分**: must-fix。binding を凍結後、tracked file と manifest の digest 行を同時更新し、configure 呼び出し 0 回で拒否する負例を追加すべき。

**所見 3**: floor から capability を渡す production 配線を削除しても追加テストが通る

- **具体的失敗**: [s8b_floor_campaign.py:4022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4022) の capability 追加ブロックを削除する。新規 5 テストは `build_v2()` を直接呼ぶ。既存 floor consumer test は注入 `build_fn` を使い、このブロックを意図的に通らないため、production floor が base、receipt、archive だけを渡す旧状態へ戻っても検出しない。
- **成果物影響**: `sort_best` configure に flag、manifest 検査、policy identity が一括して入らなくなる。既存 postflight は HEAD、config、archive だけなので、再 populate や別 header 使用を許した binary が certified 選択へ到達しうる。
- **区分**: must-fix。default の `build_fn` 経路で、PASS attempt 由来の exact capability が渡ることを consumer test で固定する必要がある。

## 過剰拒否

現行条件式から、裁定外の既存入力を拒否する回帰は摘発しませんでした。

具体的な正当入力として、canonical base `/abs/B`、正常な 2-key receipt、`post_oracle_dependency_binding=None` の generic base-only 呼び出しは、manifest schema 検査を通らず、flag 0 本、従来 identity のままです。`mimalloc-src` と `googletest-src` が未 populateでも disconnected flag は付かず、従来の populate 経路を維持します。

条件ごとの確認結果は次のとおりです。

- exact 5-key schema は capability が非 `None` の場合だけ発火する。
- 5 field はすべて裁定が必須とした base、manifest、HEAD、config、archive である。
- 旧 base、receipt、archive の同時指定は必須化されておらず、capability から導出できる。
- 旧引数を併記した場合だけ同値を要求する。片方向含意を同値化して generic caller を拒否する条件ではない。
- capability 無しの non-base、base-only、source-dir の argv と identity には新 field が入らない。

## 対応表

| 裁定 | 段 3 所見 | 判定 | 理由 |
|---|---|---|---|
| R1 | correctness 所見 1 | closed | configure 後、build 前に `CMakeCache.txt` の exact `BOOL=ON` を検査する |
| R2 | correctness 所見 7 | closed | flag と材料検査は専用 capability の存在だけで発火し、base-only generic は維持される |
| R3 | scope 所見 1 + correctness 所見 2 | closed | oracle attempt の manifest/config authority を渡し、raw manifest、全宣言 file、集合、HEAD、config、archive を configure 前後で検査する |
| R4 | scope 所見 3 + correctness 所見 5 前半 | closed | 現行コードは bound identity に policy ID と manifest hash を入れる。ただし所見 1 の回帰検出穴がある |
| R5 | scope 所見 4 | closed | staging と publish の argv 完全一致を要求せず、policy token の exact 本数だけを固定している |
| R6 | scope 所見 7 | partial | 純増 vector を選んでいるが、M4 の production 配線と raw manifest authority 単独削除を検出できない |
| R7 | correctness 所見 8 | closed | flag と policy ID は test 側の literalであり、production 定数から期待値を生成していない |

## 既存事後検知

指定された既存経路はすべて残っています。

| 旧位置 | 現位置 | 結論 |
|---|---|---|
| `buildcache.py:1932-1939` | [buildcache.py:2259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2259) | build 前 archive 照合を維持 |
| `buildcache.py:2042-2053` | [buildcache.py:2377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2377) | cache-hit 中 archive 再照合を維持 |
| `buildcache.py:2122-2151` | [buildcache.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2471) | build 後 root、HEAD/config、archive 検査を維持 |
| `s8b_floor_campaign.py:3379-3608` | [s8b_floor_campaign.py:3409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3409) | floor postflight の全条件を維持 |
| `s8b_floor_campaign.py:4048-4066` | [s8b_floor_campaign.py:4084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:4084) | binary admission 前の postflight 呼び出しを維持 |

新しい `BuildCacheError` は cleanup 後に再送出され、floor では failure recordへ変換したうえで再送出されます。握りつぶしや既存 postflight の迂回はありません。

## 変異検出力

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1: capability 時に flag 無し | 殺せる | bound 正例の flag exact 1 本、commands 自己検査、実効値検査のいずれかで赤になる |
| M2: manifest 検査を全廃し HEAD/config のみにする | 殺せる | `tracked.hh` 改変が受理され、期待した例外が出ない。ただし raw manifest hash 比較だけの削除は所見 2 のとおり殺せない |
| M3: configure 後の実効値検査を外す | 殺せる | OFF のまま build が呼ばれ、例外期待と `calls == ["configure"]` が崩れる |
| M4: post-oracle identity に policy IDを入れない | 殺せない | production 配線を policy、manifest とも外す変異が、direct helper testと archive の差による `build_dir` 分離をすり抜ける |
| M5: flag を無条件追加 | 殺せる | generic caller の 0 本 assert、または commands 自己検査が赤になる |
| M6: configure 前の raise を warning 化 | 殺せる | configure が呼ばれて `calls == []` が崩れる。後段検査が例外を出しても偽緑にならない |

## テストの偽緑

所見 1から3以外に、恒真 assertや重複 parametrize caseは見つかりませんでした。

- fixture の digest は fixture bytesから独立に `hashlib` で作られ、production helperの戻り値を期待値にはしていない。
- flag と policy ID は test 内 literal。
- 新規テストに parametrize はなく、実質同一 caseの重複はない。
- identity test自体の assertは恒真ではないが、production 配線を通らないため検査層が不足している。
- production floor が使う「capabilityと旧 3 引数の同時指定」正例は未登録。

## 所有外への波及

静的に必ず赤になる既存 consumer test は特定しませんでした。

- `test_paper_story_a1_paired.py`、`test_paper_story_a2_certification.py`、`test_build_site_gate.py` は capability 無しで `_v2_commands()` を呼び、argvは不変。
- [test_real_repo_serialization.py:2115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_real_repo_serialization.py:2115) は共有 fixture helperを参照するが、追加 `SHA256SUMS` を capability 無し buildへ渡さないため静的な赤要因はない。
- `test_s8b_floor_campaign.py` の注入 build seamは従来 kwargsのままなので赤にはならない。ただし、これが所見 3 の検出欠落でもある。
- `test_s8b_materialization.py` の対象経路は production dependency bindingを作らず、新 capabilityの影響を受けない。
- `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact` に影響する authority callの増減はない。

したがって、実装子が挙げた既存 consumer への非波及は静的には閉じています。一方、formal floor配線の追加 assertionが所有外として未実装なのは must-fixです。

静的検査として 3 ファイルの AST parse、`git diff --check`、U+0300からU+036Fの不在だけを確認しました。pytest、CMake、buildは実走しておらず、緑と認定したテストは 0 件です。

## 総括

現行 production コードは R1からR5、R7を静的に満たし、既存事後検知も維持しています。過剰拒否も確認しませんでした。

ただし、M4 の identity 配線、oracle manifest raw authority、floor capability 配線の 3 回帰が偽緑になるため、このままのテスト防壁では採用不可です。R6を partialとし、上記 3 must-fixを閉じた後に未実走 nodeidと関連 consumerを実走する必要があります。