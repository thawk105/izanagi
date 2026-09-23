## 所見

- **A01 — must-fix — [V18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-no-write-tid-max.patch:19)、[V35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-no-read-tid-max.patch:19)**  
  `fired_version_le(const Tidword&, …)` が `transaction.hh` の include より前に定義されています。`Tidword` は同 header が取り込む `tuple.hh` で宣言されるため、macro 有効時はコンパイルできません。helper を include 群の後へ移してください。  
  **成果物影響:** V18・V35 の build が失敗し、検出表の該当行を測定できません。

- **A02 — must-fix — [V20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-published-version-mismatch.patch:50)**  
  親の指摘は **real** です。公開値の `tid` は 29 bit の最大値です。次にその key を更新すると、[版生成](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/transaction.cc:567) が `max_wset_` 由来の `tid_a.tid++` を行い、0 に巻き戻ります。[Tidword](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/external/ccbench/cc/silo/include/tuple.hh:19) の epoch はそのままなので、通常の小さい epoch の `tid_b`・`tid_c` が選ばれれば、次の公開版は先の公開版より小さくなります。公開版だけを C/W と食い違わせる R2・F03 の狙いに版逆転が混ざります。`epoch=UINT32_MAX, tid=2^28` など、1 秒の走行中に到達しない余裕を持つ値へ変更し、後続の C/W がその値へ到達しないという実走上の境界を明記してください。  
  **成果物影響:** V20 の I/N や追加の版異常を orphan 単独の検出として帰属できません。

- **A03 — must-fix — [起動器](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:245)**  
  V21 の `no_witness_verify` は証人あり `_verifier_run` が例外を投げると、証人なし検査へ進みません。[呼出元](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:316) は `no_witness_verifier: null` を残します。[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/campaign/s2_verify_calibration.py:295) もこの例外経路では trace を削除しないため、通常経路の順序は正しくても「証人なしを必ず実行・記録する」契約を満たしません。元検査の例外を記録したうえで、trace が存在する間に証人なし検査を独立して試し、両方の argv・rc・結果または例外を保存してください。  
  **成果物影響:** V21 の証人あり／なしの対になる値が欠け、末尾欠落の分類が不能になります。

- **A04 — should — [台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/orchestrator/tests/acceptance_duration_ledger.json:7468)**  
  test を `...exact_57...` に改名しましたが、受入 duration 台帳には旧 `...exact_38...` nodeid が残っています。台帳の更新規約に沿って新 nodeid の所要時間を記録してください。  
  **成果物影響:** 検出表の値は変わりませんが、受入 shard の所要時間見積りがこの test に追随しません。

[V19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-mutation-run/patches/broken-silo-fixed-commit-version.patch:49) の `(1,1)` は genesis `(1,0)` より大きく、この固定値自体の `+1` は行われません。V20 と同型の最大値巻き戻りはありません。後続の同 key 更新を再び `(1,1)` にする版重複は、V19 が意図する機構です。

## patch ごとの判定

| Patch | 静的判定 |
|---|---|
| V17 read-lock-check | 条件 3 の abort のみ省略。版一致検査は残り、reached／changed／committed は相談表と整合。 |
| V18 no-write-tid-max | 機構と診断条件は整合。**A01 により有効ビルド不可。** |
| V19 fixed-commit-version | 固定版による重複という単一機構。genesis・巻き戻りの追加問題なし。 |
| V20 published-version-mismatch | UPDATE 公開版だけを変更。**A02 により版逆転が混入。** |
| V21 tail-commit-omission | `quit_` 後に成功を返し、write 有無も記録。1 thread の W5 は worker が現取引後に終了するため、lock 解放漏れから後続取引の hang は見込まれません。入力への影響は、裁定どおり write／trace の末尾欠落として扱う必要があります。 |
| V22 stale-read-payload | 二度目の TID 取得後に relaxed atomic を加算。版差と成功取引を分けて記録。 |
| V23 corrupt-write-payload | 元の payload 複写後に先頭 byte だけを変更。単一機構。 |
| V24 skip-node-validation | node 版不一致を通した場合だけ changed。W4 での未到達という期待と整合。 |
| V26 stale-read-own-write | write set の旧 tuple bytes と buffer の相違で changed。相談表と整合。 |
| V27 repeat-update-buffer | 二度目の入力とも旧 buffer とも異なる byte を入れ、入力と最終 buffer の相違を満たす。 |
| V35 no-read-tid-max | 機構と extra counter は整合。**A01 により有効ビルド不可。** |
| V31 double-abort-backoff | backoff を追加し、abort 取引の changed と committed=0 を分離。 |
| V32 reverse-write-order | 共通の逆順比較へ変更し、2 key 以上で並びの変化を診断。 |
| V33 conservative-abort | 非空・偶数 write set の事前 abort に限定。成功取引は別に必要。 |

14 本はそれぞれ単一 macro の条件枝で元の処理を残しており、未定義時の pin 一致を崩す差分は見つかりませんでした。race 区間への I/O 追加も見つかりませんでした。condition gate の追加は 14 macro・申告 site 数と一致し、既存の判定処理は変更していません。許可ドメインが 43 から 57 へ広がる点は裁定 F08 どおりです。

起動器の W1〜W8、J1〜J4 の割当て、job ごとの stock build 1 回と workload ごとの stock run 1 回は R3・R5 と一致します。`stock_precondition` が参照する `certified`、`verdict`、`integrity.clean` は verifier の実出力 key と一致します。`_run_once` は stderr を capture しており、起動器の保存経路から `T2847_FIRED` を抽出できます。

## 未確認点

build・test・実走は依頼どおり行っていません。特に各 patch の実際の発火数、V20 の orphan、V21 の先行 prefix と証人なし S、対照の非空 commit は実走結果で確認が必要です。

## 総括

**NO-GO。** V18/V35 の有効ビルド、V20 の単一機構への帰属、V21 の証人なし検査の例外経路を修正してから本走へ進むべきです。