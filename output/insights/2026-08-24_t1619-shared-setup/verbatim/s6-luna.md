## 総括

実装を止める must-fix はありません。5 件の直接 consumer と group/shard 契約は提示済み実走で覆われています。
ただし 46 秒残・129 秒削減は、48-worker 全走の保証値ではなく条件付き推定です。
また shard 検査は閉包だけを証明し、割当や最大 weight の不変性までは証明していません。

[severity: should-fix] [攻撃シナリオ] 147.28 → 38.9 秒の比率 0.26412 をそのまま台帳 175 秒へ掛けると、残り 46.22 秒、削減 128.78 秒、work 下界改善は 128.78 / 48 = 2.68 秒となる。ただし変更前 setup 回数は distinct worker 数 k で 1 から 5。焦点走の setup 5 x 15.44 秒と call 合計 70.08 秒を使うと、変更前 work は 70.08 + 15.44k であり、同じ 38.9 秒に対する比率は k=1 で 0.455、k=5 で 0.264。175 秒への外挿は残り約 79.6 から 46.2 秒、削減約 95.4 から128.8 秒まで動く。さらに worker 再起動、group を跨ぐ複数 invocation、非 loadgroup 実行、I/O・cache・CPU contention、台帳採取時と今回の評価コスト比の相違で壊れる。[根拠 implementation.diff:46-56,64-134; s4-adjudication.md:13-15,24-31] [提案] 約46秒・約129秒は「k=5かつ焦点走と同じ費用比」の推定と明記し、受入全走では worker id、setup 回数、group の setup+call 合計を記録する。

[severity: nit] [攻撃シナリオ] 現実測の新鎖は 38.9 秒で、103.0 秒 floor より64.1秒短い。scheduler は同じ suffix を一つの work unit とし、全 item の duration を加算するため、この比較方法は正しい。新鎖が律速になる境界は setup+call 合計が 103.0 秒を超えた時であり、確定仕様の「103.0秒未満」では等値も不受理となる。現実測比では 2.648 倍以上、46秒予測比では2.239倍以上の膨張が境界である。[根拠 conftest.py:904-908,947-979; chain-measurement.md:8-23; s4-adjudication.md:30-31] [提案] 受入全走の group 合計が103.0秒以上なら不採用とし、台帳推定175秒と実鎖を混同しない。

[severity: should-fix] [攻撃シナリオ] stale 台帳では変更前の5 unit 47,32,32,32,32秒が、変更後は一つの175秒 unitになる。duration reorder は unit 内を合算して降順投入するため、新 group は既知の103.0秒、102.6秒 group より前へ移り、既知 group 中の最大推定 weight も175秒になる。これは投入順の変化であって実 work の増加ではない。一方 shard 検査は live marker を `ItemRecord` に渡して閉包を確認するだけで、前後の shard 番号、weight、最大 weightを比較していない。したがって「shard割当と最大 weightは不変」はこの検査結果からは導けない。[根拠 conftest.py:952-995; test_real_repo_serialization.py:1177-1200] [提案] 同じ shard test に、group 追加前後の合成 records を与え、選択 shardと最大 weightの差を明示的に検査する。少なくとも現状の報告は「group非分割を確認」に限定する。

[severity: nit] [攻撃シナリオ] 参照関係では、共有 fixture の直接 consumer は差分中の5件、二つの新 golden の直接 consumer は `test_real_repo_group_collection_exactly_matches_canonical_nodes` だけ、live marker の shard consumer は `test_shard_assignment_preserves_live_xdist_group_components_and_split_control` である。loadgroup test は合成 `"probe"` group、負の対照は合成 report と明示 expected setを使うため、新 group の直接 consumerではない。従って、提示された194件全走、group契約、shard検査で直接 consumerは覆われており、不足する既存 nodeid はない。残る定量的 shard gapは追加 nodeidではなく既存 shard testのassert不足である。[根拠 implementation.diff:13-38,46-136; test_real_repo_serialization.py:1045-1059,1172-1200,1204-1327,3757-3833] [提案] 実走記録では直接 coverage と汎用 detector controlを分けて記載する。

[severity: nit] [攻撃シナリオ] 将来5関数の一つを改名すると、collection側だけが変わり独立 literal が missing/extra で赤くなる。これは過剰結合ではなく、鎖構成変更を無審査で通さない意図した fail-closed である。ただし `canonical_node` を set 化しているため、将来の parametrizationによる instance増加は同じ canonical名へ潰れ、鎖増大を検出できない。[根拠 test_real_repo_serialization.py:559-565,1050-1059; implementation.diff:13-19] [提案] 改名時の同時更新は維持する。exactly-five instanceまで契約にするなら、canonical setに加えてgroup item数または canonical Counterをassertする。

[severity: nit] [攻撃シナリオ] 5件すべてで unpack後の `root` と `head` が未使用になっており、Pyflakes/RuffのF841を有効にした経路なら赤になる。ただし射影されたpytest consumer、conftest、実行環境には Ruff・Flake8・Pyflakesを呼ぶ経路または実行可能ファイルを確認できず、提示された受入経路がこれを赤にする証拠はない。[根拠 implementation.diff:71,85,101,117,133] [提案] 将来のlint導入に備え、`_root, _head, results` または `_, _, results` とする。動作上のland blockerではない。

[severity: nit] [攻撃シナリオ] 古い鎖測定資料には削減160秒・wall改善3.3秒という記述が残り、確定資料の約129から130秒・下界改善2.7秒と矛盾する。また work 下界が鎖より大きいだけでは、削減分が実 wallへそのまま効くとは証明できない。[根拠 chain-measurement.md:24-25; s4-adjudication.md:24-31] [提案] chain-measurementを superseded と明記するか、130秒・2.7秒へ訂正し、wall短縮保証の文を削除する。