静的読解のみです。pytest・checker・run_tests は実行していません。

現案は「更新済み `dev_wave_land.py` を通り、tip 側 checker が非 0 を返す場合」には効きます。しかし「全層を覆う」「land 後 main の full audit を保証する」という主張には blocker があります。

### 1. land 経路外と可変 trust root を覆えていない

**深刻度: blocker**

**根拠:** `parent-brief-v2.md:47-63,75-78`、`rulings-inbox/...:31-37`、`tools/dev_wave_land.py:4-7,27-36`、`tools/check_ai_provenance.py:4-7,29-33`、`hooks/README.md:10-18,86-90`、`docs/dev-wave/core.md:107-112`

塞ぐのは land helper 内の子 checker rc だけである。

- 親の直接 `git commit`、直接 main 更新、`update-ref`、別の merge 経路は塞がない。
- provenance checker は hook 配線されていない。Codex hook も未配線で、cron・subprocess 内部も hook の観測外。
- supervisor / cron は、正しい helper を起動し、さらにその exit code を尊重した場合だけ効く。
- `check_ai_provenance.py` とその import 依存 (`site_policy` など) は tip 側なので、tip が checker を弱めたり known violation を追加したりできる。
- 実行する `dev_wave_land.py` 自体も `__file__` 起点の import であり、tip 側 helper を実行すれば関門呼び出しそのものを削除できる。

3 例の判定は次のとおり。

- 22 commit: 将来、更新 helper で非 0 のまま land すれば止まる。しかし既に land 済みなら遡及しない。tip 自身が登録を known 扱いすれば通る。
- 1 commit: 同じく、更新 helper 経由の非 0 なら止まるが、直接 main 更新・旧 helper・既知登録済みなら止まらない。
- grep だけで検出された例: underlying checker が非 0 または dispatch rc=16 なら止まる。checker 外の grep だけ、または既に land 済みなら止まらない。

**成果物影響:** 直接更新または自己弱化された checker では、赤い provenance 履歴が main・台帳・レポートの受理集合に残り、certified 結果の証拠参照が信頼できなくなる。

**具体的な修正案:** 独立した immutable trust root から land helper・checker・known-violation registry を実行し、tip の実行体を検査対象にしない。そこまで scope を広げないなら、保証文を「協調的な通常 land 経路上の誤読を止める」に縮小し、上記層を裁定パッケージへ返す。

### 2. full audit を lock 内で走らせる設計は実効性が悪い

**深刻度: must-fix**

**根拠:** `s2-plan.md:45-50`、`tools/dev_wave_land.py:1126-1145,1673-1682`、`tools/check_ai_provenance.py:1285-1305,1456-1508,1542-1557,1973-2020`

提示された 38.3 秒の local audit、20 秒の dispatch、8 wave 並行という条件で、1 wave が common lock を保持したまま全史監査と queue wait を行う。現行 lock は non-blocking なので、他 wave は待たず `lock-busy` になる。外部 retry が重なるだけで直列ボトルネックになる。

`check_ai_provenance.py` の dispatch failure、queue-wait-timeout、rc=16 を非 0 として拒否する方向は正しい。成功扱いにしてはならない。

lock 前監査は、次を満たせば正しく、かつ実効的である。

1. 監査開始時に `HEAD == tested_tip` を確認する。
2. full audit の結果に tip SHA と checker blob/tree SHA を束縛する。
3. lock 内で HEAD/ref、wave clean、checker SHA を再照合する。
4. 不一致なら land せず再監査する。

**成果物影響:** 誤受理そのものより、`landed` の遅延、`lock-busy` の連鎖、queue timeout による並行 wave の停止が発生し、台帳 fold と land 順序が変わる。

**具体的な修正案:** full audit を lock 前へ移し、lock 内は SHA・cleanliness・main 状態の再照合と ff/fold に限定する。現案を維持するなら、8 wave 並行時の lock 保持時間・retry・timeout の受入条件を追加する。

### 3. `already-landed` と fold 後監査の契約が変わる

**深刻度: must-fix**

**根拠:** `docs/dev-wave/operations.md:90-97,121-132`、`s2-plan.md:91-105`、`tools/dev_wave_land.py:1735-1744,1840-1892,1921-1952`、`tools/dev_waves/git_state.py:45,775-807`

P3 の「子の `returncode != 0` だけを見る」と P4 の rc=29 は妥当で、P5 の escape hatch 不在も妥当である。

しかし関門を `already-landed` 分岐より前に置くため、既に main が tip に到達済みでも、queue timeout や dispatch rc=16 で `already-landed` ではなく `rejected` になる。plan のテスト自身がこの意味変更を要求している。

また full audit は wave tip と ff 前までで、成功後に生成される fold commit は監査対象外である。固定の `AI-Agent: none` と fold shape 検査は補助証拠だが、DW-O17 の「merge 後 full audit」と同値だとはまだ示されていない。

**成果物影響:** 同じ request の結果が `rc=0/already-landed` から `rc=29/rejected` へ変わり、fold・台帳採番・レポートの status が変わる。fold 後の main SHA は full audit 未観測のまま `landed` になり得る。

**具体的な修正案:** no-op の `already-landed` は従来どおり idempotent にするか、監査失敗を含む新契約を DW-O23 へ明記する。fragment fold がある場合は fold commit 後に full audit して失敗時 rollback するか、固定 fold shape が full audit の代替であることを独立テストと文書で定義する。

### 4. 既存 64 テストは関門削除を検出しない

**深刻度: must-fix**

**根拠:** `orchestrator/tests/test_dev_wave_land.py:119-123,185-187,1427-1433,1545-1547,1670-1672,1797-1799,1852-1854,1887-1889,2066-2068,2651-2653,2667-2695,2866-2885`、`s2-plan.md:67-77`

fixture に `SystemExit(0)` の checker を追加すると、既存 64 test は本物の全史監査をせず、常に緑の子を呼ぶだけになる。関門呼び出しを削除しても、既存テストの期待値は変わらない。CLI/E2E も同じ成功 stub を使う。

既存テストの範囲は、追加テストを除けば概ね `:414-1212` と `:1557-2863`。7 箇所の `_preflight_fold_message` stub も、全史関門の発火証拠ではない。

plan の新規4本は負例を含むため方向はよいが、checker 削除・symlink を未コミットで試すと、関門より前の `:1708` で `RC_DIRT` になり、`RC_PROVENANCE` の検査にならない。

**成果物影響:** 関門を削除・移動・main 側実行体へ変更した実装が緑になり、テスト結果が受理集合の偽の保証になる。

**具体的な修正案:** 関門呼び出し削除 mutation を新規負例で必ず kill する。checker 欠落/symlink は clean な commit tip として試す。さらに dispatch rc=16、起動例外、fold 後監査、trusted helper と tip helper の取り違えを別テストにする。

### 5. 23 件の順序制約は実質的な停止依存である

**深刻度: must-fix**

**根拠:** `parent-brief-v2.md:29-30,100-102`、`rulings-inbox/...:49-54`、`s2-plan.md:117-120`

並行 wave が known-violation 登録を先に land できなければ、本 wave の tip full audit は 23 件の新規違反で非 0 となり、関門は ff 前に rc=29 を返す。これは正しい fail-closed だが、両 wave を進める機構ではない。

P1 の tip checker を採る限り、将来の known-violation 登録 wave は、登録と違反 commit を同じ tip に含めれば land できる。逆に main 側 checkerを使う案は恒久的 deadlock になる。この非対称性は、同時に自己免除の穴でもある。

**成果物影響:** 並行 wave failure 時は main HEAD、台帳 fold、次の certified/report 更新が停止し、登録 wave が自分の違反を登録できる場合は provenance の受理集合が拡大する。

**具体的な修正案:** 段4で「登録 wave の先行 land」を明示的な前提・停止条件にする。known registry はユーザー裁定 SHA と独立 trust root に束縛し、tip が任意の違反を自己承認できない設計にする。

### 6. 既存2検査との「同型」一般化は成立しない

**深刻度: must-fix**

**根拠:** `parent-brief-v2.md:33-38`、`tools/dev_wave_land.py:1363-1404`、`tools/check_ai_provenance.py:838-857,1939-2020`

既存の `_validate_generated_docs` と `_preflight_fold_message` と共通なのは、`subprocess.run` を直接呼び `returncode` を見る構文だけである。

既存2本は、短時間・login node 完結・main の手元入力を検査する。一方、新関門は policy commit から tip までの全史を対象にし、tip 側コードを import し、login admission・bounded scope・Pegasus dispatch・queue wait を通る。

**成果物影響:** 既存2本を根拠に lock 保持時間・dispatch failure・全史権威性まで「既に同型で実証済み」と扱うと、land 遅延や誤受理が報告・台帳へ反映される。

**具体的な修正案:** 「構文上の subprocess 型が同じ」に主張を限定し、full-history/dispatch/infra rc/lock の独立した実効性証拠を追加する。P6 の38秒受容は既存2本から一般化しない。

### 7. W2 は文書上の注意書きであり、F37 の機械防壁ではない

**深刻度: nit**

**根拠:** `docs/dev-wave/core.md:27-39`、`s2-plan.md:107-115`、`docs/decisions.md:4261-4264`、`docs/skill-self-improvement.md:18-20,83-84`

DW-S01 には既に「性質で既存被覆を先に検索する」とあるため、追加文は probe 全般への明確化である。ただし、これ自体は親が無視でき、`check_docs.py` も意味実行を保証しない。

D95 が却下した「注意書きだけ」と同じになるのは、W2 を F37 の防壁として数える場合である。裁定4がW2を選んだ理由は、F37の受理阻止ではなく、不要で弱い証拠 probe を作る手順浪費を減らすためであり、この限定なら整合する。

**成果物影響:** certified 選択や land 受理集合は変わらないが、不要 probe が裁定パッケージの根拠として残り、レポートの参照証拠が弱くなる。

**具体的な修正案:** W2を非阻害の手順改善と明記し、brief に検索語・既存 path・純増性質を記録させる。W1の機械強制化とは別の効能として扱う。

## 総括

(a) **blocker はある。** tip 側 checker と実行 helper が可変で、direct main 更新・hook 外・supervisor の rc 無視を塞げない。

(b) 最も危険なのは、P1 が known-violation registry と checker import 閉包を tip 側へ置き、関門自身の受理集合を incoming wave が変更できる点。

(c) 段4の択一は次の二つ。

- A: 保証範囲を「更新済み helper を通る協調 land の accidental non-zero 停止」に縮小して進む。
- B: 本当に全層を保証する immutable trust-root checker/helper を別 scope・別裁定で設計する。

**推奨は B。**