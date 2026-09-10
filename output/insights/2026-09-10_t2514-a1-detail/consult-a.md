## 総括

**最小差分は成立します。P1に反証はなく、実装を止める欠陥は静的検査では見つかりませんでした。** production 1ファイルと既存testへの局所追加で進められます。編集・pytest・変異実行はしていません。

- **P1：支持。** [`_v3_job_roots`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/paper_story_a1_paired.py:2485) がworkload別の `raw_root` を生成し、3482行以降の受領証検証、6840行以降のCLI roots照合を経て採用されています。保存先の新規gateは不要です。
- **元拒否の保持：planの境界で成立。** [6773行の拒否分岐](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2514-a1-detail/orchestrator/campaign/paper_story_a1_paired.py:6773) は既存の `could not run` 用tryの外です。この位置で本文を先に確定し、各recordのdigest取得から保存までを `except Exception` に収めれば、保存例外による拒否の置換を防げます。失敗対象の識別には固定ラベルと添字を使い、except節でdigestを再取得しないことが必要です。
- **受理集合・成功経路：変更不要。** admission判定、reason codeの順序・重複、全greenでもadmission拒否の場合の本文を維持できます。admitted時は保存用canonical化も呼ばない配置にしてください。admissionはarm本文を内包しないため、greenを含む全armの保存が必要です。
- **原子保存：既存方式の局所適用で足ります。** directory fsync失敗時は、replace済みの完全な最終fileが残り得ます。「保存失敗なら最終file不在」という期待値は誤りです。不完全な最終fileの不在を要求するのはreplace前の失敗です。
- **親brief・所有：参照訂正のみ。** [handoff:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2514-a1-detail/handoff.md:21) の `_v3_workload_paths` は存在せず、正しくは `_v3_job_roots:2485` です。31行には訂正済みですが、brief本体にも反映してください。T-2581所有の `p3_s4_loop.py` とpin依存testを編集する必要はありません。

変異の帰属では、**拒否が続いていてもdetail保存を欠けば本件の回帰**です。一方、`BaseException` の伝播はD1912どおりであり、拒否保持の破れには数えません。保存分岐へ到達しなかった変異は保存境界の検証不成立で、成功扱いにはできません。

今回支持できるのはコード上の成立性までです。過去のLustre上の `os.link` probeは、本案の `os.replace` とdirectory fsyncの実機保証には使えません。F855のdetail消失は本件対象ですが、F580の依存供給不備とsource問題は残り、本変更から次回A-1の成功は導けません。