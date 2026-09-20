## 所見 RA-1: 赤 3 件は timeout の派生期待値 5 か所の追随漏れ

**主張:** 親の分類は正しい。本変更に帰属するテスト期待値の追随漏れであり、production の拒否機構の欠陥でも非帰属の失敗でもない。修正対象は **3 node・5 か所**。

**根拠 (file:line):** `contract_loader_binding.py:391,453` は従来どおり「10 秒 × 対象数」。現行 85 本では 850 秒になる。一方、[test_t671_source_binding.py:1638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_t671_source_binding.py:1638)、同 `1717,1723,1801,1807` は 630 のまま。焦点走では、欠落 path・digest mismatch の拒否や全 disk path 読取の確認を通過した後、呼出し引数の比較で失敗している。worktree 内のテストを検索し、同型の 630 pin はこの 5 か所以外に見つからなかった。

**real / refuted:** real。
**must-fix か nit か:** 成果物への直接影響を認めないため、本レビューの指定基準では **nit**。ただし焦点走の完了には追随修正と再走が必要。
**成果物影響:** certified 選択・材料レポート・台帳の値や受理集合は変わらず、検証結果が偽陰性になる。

## 所見 RA-2: exact-63／62／24 が certified に流入する経路は確認できない

**主張:** 歴史 grammar の追加による certified 受理集合の拡大という疑いは棄却する。

**根拠 (file:line):** [campaign_lock.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/campaign/campaign_lock.py:485) の通常 validator は現行 85 本の exact key 集合だけを受理する。`366` の歴史 authority 白名単は exact tuple と map の宣言順を検査する。`798,841` の現行→歴史変換は通常 decoder の検査後に進み、逆向きの昇格はない。

`artifact_admission.py:1037` は exact enum の purpose を確定して decoder を選ぶ。`294` の `_RecordedCampaignVerifierEpoch` は exact diagnostic 型と scope に対応する ordered map を検査し、`1186` の gate は歴史型を certified で拒否する。v1 は通常 decode 可能だが E0 gate で拒否される。

**real / refuted:** refuted。
**must-fix か nit か:** 修正不要。分類上 nit。
**成果物影響:** 旧 63／62／24 は certified 選択へ昇格せず、旧 63 の材料閲覧だけが追加される。

## 所見 RA-3: 歴史 literal・宣言順・wire 順・固定値は一致している

**主張:** literal の転記誤り、順序混同、先行分岐による誤受理は確認できない。

**根拠 (file:line):** 指定した `git show f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad:orchestrator/campaign/campaign_lock.py` を自分で取得し AST で照合した。`campaign_lock.py:234` の独立 literal は旧 63 要素と順序まで一致し、現行 tuple の先頭 63 も一致する。末尾 22 本は sorted 順で、現行全体は重複なしの 85 本だった。

`campaign_lock.py:640` は sorted wire 列を比較し、`645` は宣言順で map を再構成する。`841,850,854,859` の 85→63→62→24 は exact 比較なので重ならない。通常・24・62 validator の本文は変更前と文字列一致した。

[test_artifact_admission.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-closure-stage/orchestrator/tests/test_artifact_admission.py:370)、同 `373,683,684` の固定値 4 件も独立計算と一致。期待値は固定文字列であり、実行時に production から再生成していない。旧 scope 2 件も指定 commit と byte 一致した。

**real / refuted:** refuted。
**must-fix か nit か:** 修正不要。分類上 nit。
**成果物影響:** 歴史 63 の E1・旧 scope・順序を維持し、現行材料レポートは裁定された 85 本の scope を表示する。

## 所見 RA-4: 新設テストは対象機構を通り、未知 grammar の否定側も既知集合と衝突しない

**主張:** dataclass の構築だけ、両層 stub、既知 grammar に化けた負例による検出力の空洞化は確認できない。

**根拠 (file:line):** `test_campaign_lock_codec.py:755,776,790,830` は歴史／通常 decoder と兄弟 validator を呼ぶ。`813` では各負例の wire 列が既知 85／63／62／24 のいずれとも一致しないことを assert する。subset は `env_contract.py` を落として worker を残し、既知 62 にならない。84 本の負例も含む。順序違いは validator を直接呼ぶため、外側 canonical JSON の拒否だけで緑になる構造ではない。

`test_artifact_admission.py:3465,3511,3529,3570,3667` は実際の admission／epoch API を呼ぶ。合成 Git repo への `_REPO_ROOT` 差替えであり、検査関数自体は stub 化していない。63 本の blob mismatch は path 名と拒否理由を検査し、新 22 本の drift は未 commit 時の拒否と commit 後の受理を対にしている。

`3591` は dataclass を直接構築するが、対象が scope と map の組合せ不変条件なので適切。API 正例の代替にはされていない。

**real / refuted:** refuted。
**must-fix か nit か:** 修正不要。分類上 nit。
**成果物影響:** 記録 blob の改変や新収載 source の未 commit drift を受理する回帰を検出する構造がある。

## 所見 RA-5: 既存 node の期待値変更は裁定の追随範囲内

**主張:** 既存拒否条件の反転・緩和・skip・削除に当たる差分は確認できない。

**根拠 (file:line):** `impl-diff.txt` は自分で取得した `git diff HEAD~1 HEAD` と全文一致した。既存期待値の変更は `test_artifact_admission.py:370,1537,1664,1674` の固定値・scope・件数、`test_t671_source_binding.py:105,291` の独立 literal・件数、`test_layer3_report.py:581,1917,1997` 周辺の歴史 param・現行ラベル、`test_s1_9pair_figure_provenance.py:76` の現行 scope に限られる。凍結 E0 は変更していない。

**real / refuted:** refuted。
**must-fix か nit か:** 修正不要。分類上 nit。
**成果物影響:** 凍結成果物の期待値を変えず、新しい現行 grammar と追加した歴史 grammar の表示・検査に追随する。

## 所見 RA-6: 実 lock probe の記録は必達 A／B／C を満たすが、probe 実装までは証明しない

**主張:** 提供結果は必達を満たす。単なる例外発生を C 成功として読んだものではない。ただし JSON だけから probe 自身の assert や API 呼出しを完全監査することはできない。

**根拠 (file:line):** [real-locks-probe.json:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/real-locks-probe.json:4) の A は 20 件すべて歴史型・exact-63・記録 sha256 一致。`146` の B は指定 3 本に rr50 を加えた 4 本で、歴史型・E1・旧 scope 両方・`unknown` を記録する。`192` の C は同 4 本について、通常 decoder と certified epoch の双方が **blob map の exact key 集合**を理由に拒否している。`226` は bytes 不変を記録する。probe ソースは射影されていないため、この結果記録以上の検査強度は断定しない。

**real / refuted:** 必達未達の疑いは refuted。probe 実装を未監査という証拠上の限界は real。
**must-fix か nit か:** nit。
**成果物影響:** 記録上、実 lock bytes を変更せず歴史閲覧を回復し、指定成果物の certified 再解析は拒否を維持する。

## 総括

最も注意を要する実在所見は RA-1：3 node・5 か所の timeout pin 追随漏れ。
certified 境界の拡大、固定値の誤り、対象機構を迂回する新設テストは確認しなかった。
**採否判定: NO-GO（現 HEAD を完了扱いにすることに対して）。** 赤 3 件の追随修正・再走が残る。
本レビューは静的検査のみ。pytest・変異検査は実走していない。