## 親の実測と一般化への攻撃

- **[real] 6.954 秒は「4 回の観測最大」であり、運用上の最大値や尾部確率の根拠にはならない。** 同一 checkout の反復は cache 状態も共有し得る。仮に独立標本でも、発生率 1% の遅延を4回とも観測しない確率は約96%。「43倍あるから十分」という plan の肯定は強すぎる。実測ログ・計測方法は今回未確認であり、値は親の報告として扱う。根拠：`brief.md:39`、`plan.md:142`。

- **[疑い] 同じ共有 FS でも、login node と計算ノードの I/O regime が同じとは限らない。** client cache、metadata 競合、通信経路、同時 shard 数、cold start により変わる。load 57〜81／147 だけではこれらを比較できず、CPU 時間が短いことも I/O 待ちと scheduler 待ちを分離しない。適用先で300秒を超える頻度は未確認。根拠：`brief.md:42`、`brief.md:44`、`tools/pegasus/paper_story_a1_paired.sh:7`。

- **[real] 現在の tracked file 数・commit 数だけでは将来の作業量を表せない。** 対象は `--all` で到達する履歴であり、別 ref の増加、過去 tree の大型化、blob のサイズ、object の配置も効く。全履歴走査は各 commit の各 blob を読み直すため、増大は単一呼出し時間と呼出し総数の両方に現れる。根拠：`orchestrator/campaign/trial_registry.py:2543`、同`:2560`、同`:2606`。

## 予算の値と形

- **[real] D265 は固定300秒を裏付ける裁定ではない。** ruleops では軽い呼出しを20秒に残し、作業量比例予算の上限を300秒とした。さらに、その根拠には観測通常値の33〜46倍の尾部事象がある。親の43倍は、既知の別経路の尾部倍率さえ大幅には超えていない。別 module の実測を今回へ直接移植もできない。根拠：`docs/decisions.md:12206`、`brief.md:43`、`plan.md:142`。

- **[疑い] 固定300秒は局所修正の暫定値としては合理的だが、十分性は未証明。** 短くすると正常な遅い呼出しを拒否する。長くすると軽い `rev-parse` の停止にも5分待ち、受入全体の5分枠を一発で消費する。無期限待ちの削減には意味がある一方、受入を期限内に完了させる保証にはならない。根拠：`orchestrator/campaign/trial_registry.py:987`、`plan.md:144`、同`:146`。

- **[real] subcommand 別の定数分岐それ自体が監視 framework とは限らない。** ただし今回の資料には分岐ごとの妥当な予算根拠がなく、作業量取得・再較正機構まで導入すると scope を拡張する。今回は固定値を維持し、「実測で安全を証明した値」ではなく「単一呼出しを打ち切る暫定運用値」と記述するのが適切。根拠：`brief.md:20`、`plan.md:140`。

## spawn-site 登録簿

- **[real] 提示された変更なら登録値1は維持される。** scanner は認識対象の process API の `ast.Call` を、相対 path と class/function scope の組で数える。`try/except`、数値の timeout 引数、`TimeoutExpired` の捕捉は scope も process call 数も変えない。テストディレクトリは走査対象外なので、追加 shim もこの件数には入らない。根拠：`orchestrator/tests/test_ccbench_spawn_sites.py:31`、同`:284`、同`:347`、同`:378`。

- **[real] 一致が崩れる条件は明確。** 別 helper・内側関数への移動や改名で scope が変わる。retry 用の第2の `subprocess.run` を書けば件数が増える。一方、同じ call を loop で反復しても静的件数は1のまま。また `run` を別の認識済み API に交換しても同じ key/count になり得るため、この登録簿は API 種別や timeout の効き方を保証しない。根拠：`orchestrator/tests/test_ccbench_spawn_sites.py:293`、同`:339`、同`:378`。

## A-1 source closure

- **[real] 「凍結 sha256 定数がない」は、既存証拠への波及がないことを意味しない。** `trial_registry.py` は non-certifying closure に入り、binding は各 file の Git blob OID・working SHA-256・測定 commit を保持する。その canonical JSON の digest も common record に入るため、変更後の新しい binding/digest は変わる。通常の `SOURCE_RELATIVE_PATHS` との区別も必要。根拠：`orchestrator/campaign/paper_story_a1_paired.py:174`、同`:4573`、同`:6049`。

- **[real] 投入中 job の有無だけでは確認不足。** land 前に、対象 job の実 checkout、expected HEAD、submission intent／receipt の source binding、完了・final view 発行の進捗を対応付ける必要がある。既存 job が読む checkout を更新すると起動時 HEAD 検査で拒否され得る。測定終了後でも completion／final view の source 再検証が残っていれば、HEAD・working bytes の変更で拒否される。別 checkout が旧版に固定されていれば main の前進だけではその checkout は変わらない。現時点の job 状態は未確認。根拠：`brief.md:35`、`tools/pegasus/paper_story_a1_paired.sh:135`、`orchestrator/campaign/paper_story_a1_paired.py:6673`、同`:6697`、同`:7519`。

- **[real] この変更だけを理由に過去の測定をやり直す必要はない。** D111 は測定の帰属を revision 束縛で管理し、main の freeze を廃止している。旧測定の raw・凍結受領証・source binding は旧版の証拠として保持し、新しい digest へ書き換えない。現行 checkout で再検証できない場合は、まず元の revision と束縛された bytes を使う。実行途中の混在や旧 source の復元不能が判明した場合に、当該走行を個別判断すべきである。根拠：`docs/decisions.md:5186`、`orchestrator/campaign/paper_story_a1_paired.py:7527`。

## テスト所要

- **[real] 台帳の249件・合計715.117秒は読取り集計と一致した。** ただしこれは node 所要の合計であり、並列受入の壁時計時間ではない。group suffix がなければ node ごとに scheduling unit となり、未知所要には代替 cost が与えられる。追加3件を台帳未登録のまま扱えるという plan の説明は整合するが、5分以内の維持は静的には証明できない。根拠：`orchestrator/tests/acceptance_duration_ledger.json:3019`、`orchestrator/tests/conftest.py:1633`、同`:1726`、同`:1739`。

- **[real] 正例は毎回2秒待つ設計ではない。** 正常実装では約0.25秒で遮断し、timeout 削除変異では2秒後に終了して assertion failure になる。shell を `exec` で置換する点も適切。ただし process 作成・回収・fixture の時間は別なので、合計1.5秒は実所要上限ではない。根拠：`plan.md:96`、同`:105`、同`:107`。

- **[疑い] 正常系の0.25秒／実 repo の1秒は間欠赤を追加し得る。** とくに実 repo 負例へ1秒を課す根拠がなく、短い Git timeout が受入を壊したという問題設定と逆行する。実 repo 負例は production の既定値を使い、正常 shim も余裕のある値にするべき。timeout 値を大きくしても、正常終了時にその秒数を待つわけではない。根拠：`plan.md:97`、同`:98`。

## plan の実効性

- **[real] 減るのは、16 call site が共有する `_git` の単一 subprocess 待ちである。** OS が子を終了・回収できれば、超過は戻り値分岐に進まず `TrialRegistryError` になる。genesis 判定の握り潰しは JSON decode のみを囲み、Git timeout を成功へ変換する経路ではない。根拠：`orchestrator/campaign/trial_registry.py:967`、同`:2576`、同`:2606`、`plan.md:24`。

- **[real] 「node が終わらない」の主要な残余がある。** 全履歴・全 blob の反復、blocking `flock`、通常の file I/O・`fsync` は今回の timeout で縛られない。また失敗処理が terminal 記録へ進むため、最初の timeout 後も処理時間が加わる。brief の loop に関する限界は正しいが、これらの具体例まで補うべき。根拠：`orchestrator/campaign/trial_registry.py:2611`、同`:2881`、同`:2953`、同`:3027`、`orchestrator/campaign/p3_autonomous_workload_trial.py:5096`。

- **[real] subprocess timeout は厳密な壁時計上限でも子孫全体の停止保証でもない。** 参照した標準ライブラリでは `Popen` の後で timeout 付き `communicate` を開始し、超過後は直接の子を kill して timeout なしで wait する。plan は OS 作成・終了処理の限界を既に明記しており、この点は brief より正確。補助探索の Python 3.9／3.11 の path は不在で未確認、3.10 の実装を参照した。根拠：`/usr/lib/python3.10/subprocess.py:503`、同`:518`、`plan.md:146`。

- **[real] 追加テストは production 既定値の退行を直接検出しない。** 3例とも `timeout_s` を明示するので、既定値だけが `None` になり production が無期限待ちへ戻っても、この3例は通り得る。既定値が300.0であることを同じテストファイル内で検査するのは、修正の核心に対応する。根拠：`plan.md:13`、同`:96`、同`:98`。

## scope 逸脱

- **[real] 提示 plan に他 module の変更、汎用 watchdog、新規 gate・台帳の導入はない。** private helper の予算注入引数は局所的なテスト seam であり、既存16 caller の変更も不要。A-1 binding の確認は既存契約の影響確認として収まる。根拠：`plan.md:3`、同`:34`、同`:116`、同`:128`。

## 総括

**[real] 局所修正の方向は妥当だが、plan をそのまま採用するには修正が必要。** 正常系テストの過小 timeout を外し、production 既定値の検査を補うこと。300秒の根拠は暫定判断へ弱め、A-1 は job の checkout と完了後の再検証まで確認すること。過去測定の一律やり直しは不要。根拠：`plan.md:96`、同`:142`、`brief.md:35`、`docs/decisions.md:5186`。

**[real] 本回答は静的検査と既存台帳の集計のみ。** pytest・性能測定・編集・commit・push は実施しておらず、受入の緑と追加所要5秒以内は未確認。根拠：`plan.md:107`。