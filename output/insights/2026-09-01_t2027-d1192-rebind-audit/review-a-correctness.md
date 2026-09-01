## Must-fix

### 1. `filesystem` tag により stale masstree 根を current 根として再検証せず受理できる

一文要約: v2 の `filesystem` entry が旧 FetchContent 根 A を指す場合、current 根 B を渡しても A の bytes だけを検査して receipt を発行でき、root tag canonicality が不完全です。

失敗シナリオ:

1. build の depfile が `A/masstree-src/include/x.hh` を参照する。
2. `allow_external_inputs=True`、origin/current root はともに `None` で collector を呼ぶ。この組み合わせは拒否されず、入力は `filesystem` として保存される。
3. A を残し、current canonical root B の `include/x.hh` を異なる bytes にする。
4. manifest と current root B を validator または receipt issuer に渡す。
5. validator は B を `_strict_root()` で確認するものの、`filesystem` 分岐では A を hash する。A は B または B の親配下ではないため canonicality 検査も通り、B の差異を見ずに受理する。

根拠:

- current だけ指定した場合しか拒否せず、origin/current の両方省略は許容: [s8b_compiler_input.py:998](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:998)
- origin が無ければ全 snapshot 外入力を `filesystem` 化: [s8b_compiler_input.py:1059](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:1059)
- `filesystem` canonicality は snapshot、current root、current root の親だけを除外: [s8b_compiler_input.py:925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:925)
- receipt issuer はこの validator の結果をそのまま proof に採用: [s8b_binary_admission.py:230](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_binary_admission.py:230)
- 負例テストは B 自身を `filesystem` に retag する場合だけで、stale A を指す場合を覆わない: [test_s8b_compiler_input.py:524](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_s8b_compiler_input.py:524)

成果物への影響: binary admission receipt が current canonical masstree B の異なる bytes を検査せず、旧 A を `filesystem` proof として参照した binary を certified 集合へ入れられます。

scope: scope 内です。`s4-adjudication.md` が scope 外とした「completion と digest の同時改竄」は不要で、公開 collector の許容引数だけで生成できます。また M2/M7 が防ぐとした分類・tag 詐称そのものです。

### 2. production floor の cache identity は run-local source root を含み、D1192 が要求する run 間 hit が成立しない

一文要約: source snapshot が同一 bytes でも使い捨て worktree の絶対 path が admission 経由で cache preimage に入るため、別 run は常に別 cache digestを選びます。

失敗シナリオ:

1. run 1 は `/tmp/izanagi_wt_X/wt`、run 2 は `/tmp/izanagi_wt_Y/wt` に同一 snapshot を生成する。
2. `SourceEvidence.source_root` が異なるため admission body とその SHA が変わる。
3. admission 全体が `_v2_identity()` の preimage に入るため full build digest も変わる。
4. run 2 は run 1 の v2 completion を選ばず fresh build へ進み、今回追加した current-root hit validator は発火しない。

根拠:

- production materializer は呼出しごとに `mkdtemp` で一意 worktree を作る: [patchharness.py:362](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/patchharness.py:362)
- floor preparation はその checkout を source root に使う: [s1_direct_comparison.py:625](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s1_direct_comparison.py:625)
- `SourceEvidence.as_receipt()` は絶対 `source_root` を保存: [source_digest.py:164](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/source_digest.py:164)
- admission は source body を含む: [build_admission.py:662](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/build_admission.py:662)
- cache preimage は admission 全体を含む: [buildcache.py:1305](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:1305)
- 実装コメント自身も正式 S8b では hit が起きないと記す: [buildcache.py:2225](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/buildcache.py:2225)
- 新しい hit 正例は二回とも同じ `tmp_path/ccbench` と同じ evidence を再利用しており、run-local root の変化を再現しない: [test_buildcache_v2.py:3274](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_buildcache_v2.py:3274)

成果物への影響: 別 run の既存 completion は選択候補にならず、D1192 が修復対象とした run 間 cache-hit 受理集合が production floor では空のままです。

scope: scope 内です。D1192 は run 間再利用を明記し、brief の P3 も v2 内で再利用が保たれると仮定しています。差分が新設した欠陥ではありませんが、親の前提を反証します。

## v1 と v2 の拒否条件対応

| v1 の条件 | v2 の対応 | 判定 |
|---|---|---|
| snapshot 外を拒否 | collector が snapshot tag を先に分類し、相対 path は `..` と絶対形を拒否 | 維持 |
| snapshot directory 自体を拒否 | 空 `PurePosixPath.parts` を拒否 | 維持 |
| snapshot 配下の全 symlink component を拒否 | held root fd から各 component を `O_NOFOLLOW` で開き、stat/fstat inode を照合 | 強化 |
| leaf が通常ファイルでない場合を拒否 | open 前後の inode と `S_ISREG` を照合 | 維持 |
| missing、inspection failure を構造化拒否 | stat/open/read の `OSError` を `CompilerInputError` へ変換 | 維持 |
| external entry は絶対 path 必須 | v2 では root tag と根相対 path の組で表現し、path 自体の絶対形を拒否 | 表現変更 |
| 非正規 absolute path を拒否 | 空、`.`, `..`, 絶対形、末尾 slash、重複 slash、`./` を `_normalized_relative_posix()` が拒否 | 維持 |
| external の実在を要求 | selected root fd から leaf を開けなければ拒否 | 維持 |
| external の snapshot 内着地を snapshot entry へ再分類 | collector は snapshot を先に分類し、validator は `filesystem` の snapshot 内着地を拒否 | 維持。ただし stale masstree A は所見 1 |
| external の non-symlink regular file を要求 | v2 は leaf に加えて ancestor symlink も拒否 | 強化 |
| hash 中の size、mtime、ctime、inode 安定を要求 | 同じ属性を held leaf fd 上で前後照合 | 維持 |
| path の sorted unique を要求 | `(root, path)` の厳密昇順を要求 | 維持 |
| v1 bytes を現在 path で再検証 | schema 分岐後も旧 `_compiler_input_entry()` と `_file_sha256()` を使用 | 不変 |

根拠の中心は [s8b_compiler_input.py:406](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:406)、[s8b_compiler_input.py:435](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:435)、[s8b_compiler_input.py:574](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:574)、[s8b_compiler_input.py:584](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/campaign/s8b_compiler_input.py:584) です。backslash は POSIX では区切りでなく通常の filename character として扱われ、v1 と同じです。

## Nit / backlog

- v1 の live bytes 回帰テストが薄くなっています。`test_external_input_bytes_drift_is_rejected_by_validator` は collector が v2 を返すため現在は v2 filesystem の検査であり、追加された v1 テストは missing file だけです。[test_s8b_compiler_input.py:564](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_s8b_compiler_input.py:564)、[test_s8b_compiler_input.py:583](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2027-d1192-rebind/orchestrator/tests/test_s8b_compiler_input.py:583)。成果物への直接影響はコードから確認できないため nit です。
- v2 path の空文字、絶対形、`..`、末尾 slash、重複 slash、duplicate/out-of-order と、snapshot/current root overlap の直接テストがありません。静的には拒否を確認できましたが、境界テストとして backlog です。
- pytest は実行していません。上記は射影、差分、必要な repo コードだけによる静的検査です。

## 総括

- must-fix: stale masstree 根を `filesystem` tag に落として current 根の bytes 検査を回避できる問題と、run-local `source_root` が cache identity に残り production の run 間 hit が成立しない問題の 2 件です。
- nit / backlog: v1 live bytes 回帰と v2 path/root-overlap 境界の直接テスト不足です。
- 検査したが問題を見つけられなかった観点: path 正規化、tuple 順序と重複、snapshot containment、held-fd component 走査、leaf inode/regular-file/hash 安定性、必要な fetch tag context が `None` の場合の拒否、schema-preimage 完全一致、v1 schema 分岐と旧 bytes validator の保持を確認しました。既知 4 件は所見へ再掲していません。
- 親の brief・裁定への反証: P1 は所見 1 により反証されます。P3 と D1192 の「run 間再利用」は所見 2 により反証されます。P4 は静的比較の範囲では反証できませんでした。