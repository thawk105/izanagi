## 攻撃面 1〜10 の所見

静的検査の結論は、**入力・closure・批准 topology の計画は概ね成立するが、D2077 step 4 を未確定のまま restore へ進める根拠にはならない**。plan 自身の条件付き停止は妥当である。file 作成・編集、Git 状態変更、pytest、producer 実行はしていない。

以下、`plan` は指定された `s2-plan.md`、`brief` は `s1-brief.md`、`裁定` は `rulings-verbatim.md`。コードの略称は以下を指す。

- HF: `orchestrator/campaign/s8b_holdout_freeze.py`
- EV: `orchestrator/campaign/s8b_floor_evacuation.py`
- RF: `orchestrator/campaign/s8b_ratified_freeze.py`
- HA: `orchestrator/campaign/s8b_holdout_admission.py`
- FS: `orchestrator/campaign/s8b_floor_stats.py`
- AR: `orchestrator/campaign/s8b_attempt_registry.py`

**A-1 — 攻撃面1：固定 bundle は共有されるが、未退避の別 worktree まで収集しない。重大度：should。**

- **対象・主張：** brief P2、plan:27、104–152。「T-2698 木を evacuate すれば当該 env の namespace 全体になる」は、その木が未退避成果物の全所在である場合に成立する。
- **根拠：** EV:154–166 が列挙するのは指定 root の namespace だけ。EV:173–187 は既存 bundle と累積する。EV:40–62 の導出は同じ common dir なら同じ bundle になり、EV:225–245 はその全体を同じ repo 相対位置へ戻す。
- **反例：** earlier eligible run A が別 worktree に未退避で残る → T-2698 の B だけ evacuate → chain に restore → HF:1833–1849 は chain 内だけを列挙するため A を見ない。これは bundle の部分 restore ではなく、退避対象の取りこぼしである。
- **是正案：** 新 checker は不要。既存の所在記録で「未退避の official namespace は T-2698 の当該集合だけ」を確認し、適用範囲を記録する。別木への restore 自体は「元の repo 相対位置」に適合し、worktree を変えるだけでは bundle の部分選択口は生じない。

手動 bundle の並存だけでは API の受理集合は広がらない。producer／restore は job dir を読まない。ただし、それを正規 bundle の差替え元に使えば裁定:59–60 の既知残余に入る。plan:135 の「正規位置へそのまま置かない」は維持すべきである。

**攻撃面2：破れず。** plan:36–98 は、run siblings、launch certificate、共有 admission、v5 registry／receipt／evidence、環境 activation と calibration、現行 build policy を挙げている。確認した経路で追加の必須入力の取りこぼしは見つからない。

入力不足時の具体的な帰結は以下のとおり。

| 欠落・不整合 | 停止理由と根拠 |
|---|---|
| sibling manifest／journal | `floor-admission-unverifiable: sibling-manifest-unavailable`／`sibling-journal-unavailable`。HF:1544–1550、1584–1595 |
| 共有 root／claims／consumed／lock | `root-missing`／`claims-missing`／`consumed-missing`／`lock-missing`。HA:6180–6193、HF:1643–1649 が接頭辞を付ける |
| cell claim／main ledger／attempt ledger | `claim-file-missing`／`main-ledger-missing`／`attempt-ledger-missing`。HA:6225、6364、6732 |
| v5 registry | `floor-admission-unverifiable: attempt-registry-read-unavailable`。FS:1155–1186、AR:937–957 |
| registry replay 不整合 | `floor-admission-mismatch: attempt-registry-replay-invalid`。AR:1069–1076 |
| launch certificate | `floor-launch-certificate-invalid`。HF:1679–1695 |

`store_path` の binary 実体はこの portable validation では開かない。`s8b_binary_admission.py:324–442` は record 内の receipt／proof／hash を照合する。run-directory claim もこの inspector の入力ではない。環境 calibration は `env_contract.py:643–654` で active 各行を検証し、build policy は `build_admission.py:500–518` のコード内 authority から導出する。plan の区別は正しい。

**攻撃面3：破れず。** plan:172–182、263–265 の「closure が空」は追加 hit がない場合の期待値として書かれている。HF:1981–2009 は全 hit から専用6 path を引く。`result.md` は専用集合にないため、hit すれば X1 blob と worktree の一致を要求して closure に入る。plan は X1 に同 file を含めるため、この場合も対応できる。生成前は candidate がまだなく、生成後の scan では candidate 自身も hit するが、専用 path なのでこの差だけでは closure は増えない。

**攻撃面4：破れず。** plan:274–286 の topology は成立しうる。RF:450–459 は first-parent ではなく H の全 ancestry を使い、RF:1006–1014 は G の唯一の親が X1 であることを要求する。したがって **X1 が main の first-parent 鎖上にある必要はない**。

ただし、保存 branch の存在だけで批准可能になるわけではない。通常 merge で G の ancestry を H に含め、floor source／protocol／closure を H tree に保持し、worktree を H blob と一致させる必要がある。欠落は `closure-not-at-head`、dirty は `closure-dirty`、別 bytes を含む祖先履歴は `history-mutated` になる（RF:490–505、1036–1052）。X2 の子として G を作ると `frozen-at-head-mismatch`。plan はこれらを既に明記している。

**A-2 — 攻撃面5：N7 の branch 全称と、その逆命題は成立しない。重大度：should。**

- **対象・主張：** brief:30 の「main の全 branch」、P1 の main 保全の説明。plan:22、288 は前者を正しく限定している。
- **根拠：** `s8b_floor_campaign.py:5532–5540` は現在の root の列挙・scan を検査する。HF:370–384 は tracked と ignore されない untracked、ccbench の tracked file を列挙する。
- **反例：** X1 を main に merge しても、X1 を継承しない既存 worktree はそれだけでは赤にならない。逆に X1 を main に載せなくても、main worktree に untracked の result 複製を置けば赤になる。
- **是正案：** 「成果物を保持する checkout では clean scan が拒否される」「docs-only land は今回の成果物による hit を main に持ち込まない」と書く。「main は official を起動し続けられる」は、clean scan と他の起動条件を毎回満たす場合に限定する。

起動時の scan 本体は `s8b_launch_cert.py` ではなく floor campaign 側である。certificate leaf は構造・identity を検証し、strict 版だけが渡された期待 digest と比較する（`s8b_launch_cert.py:50、129–143`）。

**A-3 — 攻撃面6：実 repo scan の test がもう1本ある。「受入は赤にならない」は広すぎる。重大度：should。**

- **対象・主張：** brief N3、plan:18、423。
- **根拠：** `test_s8b_repo_scan_invariant.py:21–35` も実 checkout の hit が空の既知集合と一致することを要求する。こちらも `growth_test_holds.py:201–202` に登録済み。指定された S8c test は同:241–246。既定 skip は `conftest.py:2173–2187`。
- **反例：** chain 木で hold を明示解除すると、S8c test に加えて repo-scan invariant も成果物の hit により失敗する。docs-only 木なら、chain の存在だけを理由に赤にはならない。
- **是正案：** 2本を併記し、「この2本は既定 hold により実行されない。受入全体の成功は未確認」とする。

`correctness_gate=True` は正しさに関係する検査であるという記録であり、skip を合格に変える意味ではない。解除条件は `explicit-user-command-only`（`growth_test_holds.py:16–18、54–59`）。検索で見つかった他の直接 scan 呼出しには、一時 repo・明示 file 集合・mock を使うものがある。今回の静的検索だけで受入全体の成功は保証できない。

**A-4 — 攻撃面7：guard の許可と session 切替の成立を分ける必要がある。重大度：should。**

- **対象・主張：** brief P5、plan:109–121、140、430。
- **根拠：** `guard_bash.py:81–108` の防護集合に `output/env/pegasus/calibration/` はなく、提示された evacuation／restore module 呼出しには同:2746–2748 の拒否トリガがない。`guard_write.py:290–331` にも calibration namespace 全体の拒否はない。`git add`／`git commit` は `guard_bash.py:154–157` の許可集合にある。
- **反例・限界：** module 内部の `shutil` や `git -C` は別の Bash tool 呼出しではなく、この hook が再帰的に検査する対象ではない。また `.claude/settings.json:9–44` の hook 配線は `EnterWorktree` の可用性・session 権限を証明しない。
- **是正案：** 「提示 argv は当該 guard の静的判定上拒否されない。親 session での切替と実行は未確認」と記録する。切替後は cwd と module 所在を確認する。plan の「拒否時に迂回しない」は維持する。

この read-only consult の権限から、親 session の書込み可否を推定することはできない。

**攻撃面8：破れず。** plan 全体に走査除外・allowlist・test・producer・批准側を緩める操作は見つからない。生成先は candidate namespace、X2 は candidate 1 file のみ。将来 G/A/X の説明は実施対象から明確に分離されている（plan:207–237、267–286）。D95 の実装面を新設する手順もない。

**A-5 — 攻撃面9：N4 の観測範囲と N5 の最初の拒否理由を訂正する。重大度：should。**

- **対象・主張：** brief:27–29。
- **根拠：** plan:19、107 は無人状態を再確認していないと限定する。`s8b_oracle_manifest.py:1122–1135` は active freeze 検証を spec 検証より先に行う。
- **反例：** cwd 走査が0件でも、別 cwd の process が絶対 path で書く可能性や、観測後の再開は排除できない。また active freeze がない現状では、spec pin の検査前に `no-active-ratified-freeze` で止まる。
- **是正案：** N4 は「観測時点の cwd 走査0件」とし、実行直前の writer／job 終端確認を残す。108 file と hash 一致は、対象集合・観測時刻・一次資料への参照を付ける。N5 は plan:20 の拒否順序を brief に反映する。

N1／N2 はコードと整合する。N6 の実装済み・stale の対比も `docs/archive/worklog-phase3-0811-416-417.md:599` と `docs/archive/worklog-phase3-0825-944.md:194` に裏付けられる。N7 の過大一般化は A-2 のとおり。

**A-6 — 攻撃面10：隔離 restore は step 7 の影響を限定するが、step 4 の決定を代替しない。重大度：must-fix（restore 実行前の条件）。**

- **対象・主張：** brief scope 1／P1、plan:26–32、137–152、420、429。
- **根拠：** 裁定:10–14 は「その holdout 集合の official 走行を打ち切ると決めてから restore」と「その commit を持つ branch の帰結」を別に定めている。EV:225–245 は打ち切り決定を検証しない。
- **破れる操作列：** 打ち切りを未決のまま T-2698 から退避 → chain に restore → X1/X2 作成 → main では同じ集合の official 継続を予定 → 「D2077 を満たした」と記録。機構上は進めても、既裁定の順序を満たしたとはいえない。
- **是正案：** plan:32 の条件を実際の実行条件として維持する。依頼の「この result から候補を作れ」は候補生成と必要な配置の明確な指示ではあるが、**同じ集合の official 走行全体の打ち切りまで決定したか**は、引用された文言だけでは一意に決まらない。親はこの区別を裁定事項にする。

隔離は main への影響を抑える保守的措置である。しかし、そのことだけで順序適合にはならない。例外として隔離生成を認める扱いが確定した場合は、その根拠と限定を記録する。未確定のまま実施済みなら「step 4 は未裁定のまま隔離して実施した」と事実を書くべきで、「D2077 を満たした」とは書けない。

restore 後も bundle が残ることは**データ再取得可能性**の根拠になる。打ち切り判断や公開した履歴を取り消してよい根拠にはならない。

## plan を採用してよいか (GO / NO-GO と条件)

**条件付き GO。未裁定のまま restore 以降を実行することは NO-GO。**

採用条件は以下。

1. D2077 step 4 の打ち切り決定、または隔離候補生成の明示的な扱いを restore 前に確定する。
2. T-2698 が未退避 namespace の全所在であるという前提を確認する。
3. brief の N3／N4／N5／N7 を上記の範囲へ限定する。
4. guard 静的判定、親 session の実行結果、producer 成功、批准成功を別々に記録する。

binary 実体の追加コピー、除外拡張、producer／批准側の変更は、この検査結果からは不要である。

## 裁定パッケージへ送るべき項目

- **restore 前の判断：** 当該 holdout 集合の official を打ち切るのか、隔離候補生成を限定的に認めるのか。main への導入判断とは分ける。
- **main への導入：** 成果物を保持する checkout では official clean scan が赤になることを明示する。
- **批准の履歴条件：** G は X1 の直子。通常 merge で ancestry と入力 bytes を保持し、G の cherry-pick／squash を代替にしない。
- **hold 解除時の帰結：** 実 repo scan の2本が成果物を持つ木で赤になる。既定 skip を正しさの合格として扱わない。
- **保証の限界：** 手動 bundle は参照用、固定 bundle の直接差替えは既知残余、共有台帳は live authority。candidate 成功だけでは批准・oracle 起動成功を意味しない。

## 総括

plan は、入力要件、空 closure の条件、将来の G topology を概ね正しく捉えている。主要な未解決点はコード不足ではなく、**restore 前の打ち切り判断と隔離生成の関係**である。

この条件を確定し、brief の過大な一般化と test の記載漏れを直せば採用可能。今回の所見は静的検査であり、実行・テスト成功の報告ではない。