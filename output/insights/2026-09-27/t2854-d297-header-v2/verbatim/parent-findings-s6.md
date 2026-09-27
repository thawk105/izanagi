# 親の事前所見 (段 5 統合 commit 9ceb5519 に対して、段 6 レビュー前)

レビュー子は以下を「親の主張」として検証対象にすること (real / refuted を独立に判定)。

- P-1 予定集合と実行済み集合の照合が恒真: `_h_check` で `done` は予定 `planned` の走査ループ内で同時に積まれ、比較の実行 (`pool.map(_h_compare, ...)`) の結果から作られていない。`done != set(planned)` は常に偽。test `test_v3_v4_v9_...` の `planned_count == executed_count` も同じ値を 2 回数えるだけで、V9 (予定の 1 件を実行しない) を殺せない。
- P-2 未選定 protocol の genome 調査 (discovery) が configure の全 entry を依存列挙しており、裁定 S4 (b) の「p の production target の entry だけ」より重い。実 CCBench では tictoc・cicada の 48 genome × 旧新 × 135 entry × TRACE 2 で、1 起動あたり十数分の増 (生死確認の単価: 135 entry × 2 の依存列挙 ≈ 11 秒 / 側)。
- P-3 既存 `_assert_proven_repo_absent_macros` の呼び出し位置を ancestry 検査の前から `_validate_diff` の後へ動かし、header だけの差分では呼ばなくした。既存の拒否順序・既存 caller の挙動を変える (裁定は .cc 経路の不変を求める)。
- P-4 `_h_compare` の volatile builtin 検出は `-U__DATE__ -D__DATE__="..."` を argv に足すが、実 CCBench の consumer argv は `-Werror` を持ち (設計審査 job dir の compile_commands で確認)、GCC 11.4 は `<command-line>: error: undefining "__DATE__" [-Werror=builtin-macro-redefined]` で rc=1 になる (親が login で実測。`-Wno-builtin-macro-redefined` を足すと通る)。このままでは実 CCBench の header 判定が常に拒否になる。合成 fixture は `-Werror` を持たないので test は緑 ([テスト代表性])。
- P-5 V2 (依存列挙に `-MG` を足し生成 build を飛ばす 2 層変異) は、実装が `-E -dM -MD -MF` の 1 回実行で依存を取るため、未生成 header で必ず rc≠0 になり偽緑に到達しない (実装子の実測 0.65 秒)。事前登録の V2 は構造的に不成立で、登録から外し理由を記録する案。
