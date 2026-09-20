## 所見

**実装しない判断は維持可能ですが、P1〜P5 の根拠は修正が必要です。特に mtime の区間定義、標本の「単独」扱い、`--reference` の効果説明に誤りがあります。**

以下、`V/` は [指定の verbatim ディレクトリ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/verbatim)、`brief` は [親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-wave-startup-cost/brief.md) を指します。must-fix は今回成果物である実測レポートの数値・裁定根拠を訂正するものです。

1. **real / must-fix — checkout 中央値 70 秒は記載した算式では再現しない。**
   `brief:26`、`V/wt_timeline.out:102–111`。diag-login-check-wall は `commondir` 07:32:45 → `index` 07:34:06 = **81 秒**。33 秒は `logs/HEAD` または `locked` までの差である。全10本を宣言どおり計算すると **18 / 39 / 51 / 65 / 75 / 75 / 81 / 82 / 90 / 96、中央値75秒**。ただし75秒も checkout 実測中央値ではない。
   **放置時の影響:** レポートに再現不能な中央値が残り、固定費比率の分母を誤る。

2. **real / must-fix — mtime は処理境界そのものではない。**
   `V/wt_timeline.sh:3–4`、`V/wt_timeline.out:125–147,173–195`。Git 2.34.1 の `commondir` 書込みは add 内部の準備後、`reset --hard` 前であり、コマンド開始ではない。最初の index 書込みは checkout 終盤の代理になるが、後続 status の refresh、checkout、merge で更新されうる。submit-tree の index 21:54:45 は最深 module の21:54:32より13秒遅く、t2786-author は起動から約12時間後に更新されている。後続更新は checkout 区間を**過大**にする一方、commondir 起点は add 全体の前半を**除外**する。純粋な checkout 時間への総バイアスは断定不能。根拠：[Git v2.34.1 worktree.c、315行付近](https://github.com/git/git/blob/v2.34.1/builtin/worktree.c#L315)。
   **放置時の影響:** 後続操作の時間を初回 checkout に誤配賦する。

3. **real / must-fix — ccbench/config→最深 index は再帰初期化全体を過小評価する。**
   `V/self-startup-timeline.txt:3–4`、`V/submodule-init.log:2`、`V/wt_timeline.out:21–24`。submodule helper は `clone --no-checkout` を実行し、その後 checkout、さらに再帰先の init が親 module の config に nested URL 等を書き込む。したがって原因は「clone 最後の config 書込み」だけではなく、**ccbench checkout 後の nested 登録**にもある。自 wave は before 07:39:31、ccbench index/config 07:39:32、最深 index 07:39:38で、代理区間 **6秒に対して直接計測7.46秒**。欠落はこの標本では約1.46秒であり、数十秒の隠れた ccbench 初期化とは整合しない。他標本への一律補正はできず、後続 index 更新があれば逆に過大にもなる。根拠：[helper、1667行付近](https://github.com/git/git/blob/v2.34.1/builtin/submodule--helper.c#L1667)、[再帰順序、402行付近](https://github.com/git/git/blob/v2.34.1/git-submodule.sh#L402)。
   **放置時の影響:** 中央値8秒を「3段すべての所要」と誤表示し、submodule 比率を小さく見せる。

4. **real / must-fix — 昨日の標本は「単独・混雑なし」と確認できない。**
   `brief:27`、`V/t2797-tree-build-mtimes.txt:1–4`。submit-tree は21:53:38〜21:54:59、mutation-source は21:54:11〜21:55:19で、**48秒重なる**。submit-tree の commondir→config は48秒だが、その中には初期化の前半も入り、checkout ≈45秒は直接計測ではない。最深 index は21:54:32で configとの差は**6秒**。21:54:33の ccbench index は後続 PIN checkout の影響を排除できない（`V/t2797-setup-submit-tree.log.filtered:13–20`）。
   **放置時の影響:** 混雑なしの対照標本が存在するように見え、P1を過剰一般化する。

5. **real / should — 「大半ではない」は観測条件に限定すべき。**
   `V/submodule-init.log:2`、`V/gate-time.txt:1`、`V/F26.md:78–82`。自 wave の直接計測では **7.46 / (85 + 7.46 + 6.70) = 7.5%**であり、条件成立を支持しない。F26の7分は checkout 側の長時間化を示すだけで、submodule 比率の観測ではない。温かい superproject、module 側だけの混雑なら比率上昇は本運用でも起こりうる。別 filesystem への配置による copy 化も一般には可能だが、今回の同一 store・同 inode の標本を説明する条件ではない。`V/inspect_links.out:2–5` の実数は **nlink157**で、155ではない。また16本は startup時刻順ではなく job directory のmtime順で選んでいる（`V/scan_startup.sh:6–10`）。
   **放置時の影響:** 今回の非実装判断を、未観測条件まで保証する結論として残す。

6. **real / must-fix — P2の「hardlink約36件をalternates一行で省く」は、単なる `--reference` 追加では成立しない。**
   `brief:36`、`V/git_state.py.excerpt:64,118–124`、`V/inspect_modules.out:29–32`。絶対パスの local clone は `--reference` を指定しても `clone_local()` に進み、`--shared` でなければ `copy_or_link_directory()` を実行する。**reference設定とlocal object複製は別分岐**である。hardlink作成を省く説明は `--shared` 等との混同。3段のclone／checkout、`.gitmodules`解決は残るため、現行argvへの追加だけで正の短縮を見込む根拠はない。**「≤1〜2秒」という実測上限も資料から導けない。** 根拠：[Git v2.34.1 clone.c、347行付近](https://github.com/git/git/blob/v2.34.1/builtin/clone.c#L347)。
   **放置時の影響:** 効果のない変更を有効な最適化候補としてレポートに残す。

   補足として、36件はccbench storeのobject file数で、再帰全体の件数ではない。1,438＋1,036＝2,474もgoogletestの独立した件数が未提示であり、「3段合計約2,500」とは確定できない（`V/inspect_links.out:9–17`）。また抜粋のURL検査は最上位に限られ、`--no-fetch`だけでは初回nested cloneの通信まで禁止しない（`V/git_state.py.excerpt:78–124`、`V/inspect_modules.out:34–37`）。

7. **real / should — alternatesの不採用理由は、依存が生じる条件を正確に記す。**
   `V/F26.md:4–6`、[cleanup実装:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/dev_wave_cleanup.py:831)、[F1026追記:28007](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/docs/failures.md:28007)。残すべき説明は次のとおり。

   - **gc/prune:** 借り手にしか必要性が見えないobjectが貸し手で削除され、借り手にも実体がなければcheckout等が壊れる。
   - **deinit:** 通常のdeinitはmodule storeを保持するため、それだけでalternate消失とはいえない。F26が実証するのは共有configの登録消失。
   - **主checkout/store撤去:** alternate先のobjectsが実際に消え、借り手がそこに依存していれば壊れる。
   - **cleanup:** 現行は所定object名のnlink>1を許可済み。通常のnlink1のalternatesファイルを一律拒否する実装ではない。`objects/info/*`をhardlink共有すればrc20となり、参照先の寿命はnlink検査では保証されない。

   単なるreference追加で既存objectのhardlinkも残る場合、参照先消失が直ちにobject欠落になるとは限らない。[Git cloneの依存条件](https://github.com/git/git/blob/v2.34.1/Documentation/git-clone.txt#L64)とも区別すべき。
   **放置時の影響:** 既修正のF1026やdeinitの別機序を、不採用の誤った根拠にする。

8. **real / must-fix — P3の残り20秒と、起動→段1の帰属が断定過剰。**
   `brief:5,37`、`V/self-startup-timeline.txt:1–6`。85−65＝20秒は代理区間外の残差であり、branch作成・lock・session切替への分解も「gitでは縮まない」も未実証。EnterWorktree前→gate後は **331秒**、直接計測3処理の合計は **99.16秒**で、残り約232秒は別区間である。さらにwall-decompのS1は原則 **startup-gate後から**であり、11.7分の「うち」にgate以前の固定費を入れられない（`V/wall-decomp-README-s1-3.md:15–16,37`）。
   **放置時の影響:** 異なる時間窓を包含関係として扱い、短縮可能量を誤る。

9. **real / should — checkoutが最大の観測成分でも、metadata律速・3〜9分は未確定。**
   `brief:29,38`、`V/ls-files-count.txt:1–22`。31,699 entry、872.4 MB、insights比率 **77.0%は件数比**として支持される。metadata操作と書込みbytesの寄与は分離していない。木の列挙は **1＋(1〜3)＋1＋1＝4〜6本**であり、3本にはsubmit-treeなし等の条件が必要。t2797はwave・unit・mutation-source・submit-treeの4本を支持するが、全impl共通ではない。70秒×3〜6本なら3.5〜7分、75秒なら3.75〜7.5分で、3〜9分は別途仮定が必要。並走分の合計をwaveのwall短縮量にもできない。
   **放置時の影響:** 未分離の律速仮説と概算を実測結果として扱う。

10. **判定不能 — 「+60秒」＝T-2817のpreは有力候補だが同定できない。**
    `brief:12,31,39`、`V/t2817-README-s1.md:12–19`。pre61.9秒は実測されているが、fresh対warmの差60秒ではない。比較で見えている増分はshard plugin等を載せた **約45.9秒**。外側の木作成がないことから、ユーザーの指す時間をpreと一意に決めることもできない。post-claim merge、readiness、fingerprintは別区間で、[dev_wave_wait.py:2256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/dev_wave_wait.py:2256)、同`:2587,3925`に処理はあるが、提示資料に各60秒級の計時はない。T-2817にはテスト内部のbase copy配置 **64.2秒**という別の60秒級成分もある。
    **放置時の影響:** ユーザーの測定対象を別の既知区間へ置き換え、未解決部分を閉じた扱いにする。

11. **real / should — 次候補は機構の局所性と今回のscopeを分ける。**

    | 候補 | 判定・根拠 |
    |---|---|
    | **(a) checkout.workers** | 既存Git機構の局所設定。2.34.1で利用可能でreset等にも効く。ただし主checkoutのlocal configは共有worktreeにも及び、独立cloneには自動継承されない。今回の「submoduleが大半なら」の代替実装にはしない。[Git設定仕様](https://github.com/git/git/blob/v2.34.1/Documentation/config/checkout.txt#L22)、`brief:10–11`。 |
    | **(b) insightsを省くsparse** | Git既存機構だが、必要ファイルの実在を変える設計変更で今回scope外。77%件数削減を77%時間削減とはできない。 |
    | **(c) unit木再利用** | **同一unitのfixで同じ木を使うのは既存手順**。`docs/dev-wave/workers.md:19`、`V/wall-decomp-README-s1-3.md:53`が支持。異なるunitやwave間の流用、D1009の独立mutation-source廃止は別設計でscope外。 |

    sparse／alternates拒否の[README:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/pegasus/README.md:327)はthird-party取得節の規則である。[verifier:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/tools/pegasus/fetch_third_party.py:334)と同`:541–551`も検査対象は各source repository。**superproject全体の禁止根拠へ拡張するのはrefuted**。対象source自体をsparse／alternates化すれば拒否される。
    **放置時の影響:** 局所候補を誤って禁じるか、既存隔離条件を変える案を単なる設定変更として扱う。

12. **real / should — workers既定→8→既定のABAは追加実験である。**
    `brief:9–11`、`V/DW-S04.md:4–5`。既存資料によるsubmodule効果見積りとは別対象・別資料のprobeなので、今回の必須作業には含めない。次候補の予備診断としては合理的だが、各条件1回・混雑下ではcache温まりと負荷変動を分離できず、採用効果は確定しない。独立clone作成全体を測ればworktree addとの差も混ざる。
    **放置時の影響:** 条件不成立で閉じる依頼が、未承認の別最適化実験へ広がる。

13. **refuted — scope・不変条件・docs-onlyの受入全走は過剰ではない。**
    `brief:10–21`は依頼の境界を保存し、`V/DW-S04.md:8–9`は実装差分ゼロでも受入全走を明示要求する。静的検査だけでよいのは今回consultであり、親wave全体の免除ではない。一方、`brief:43`の「影響は壁時計のみ」は不十分で、**誤った内訳・見積りがinsightと裁定根拠に残る**というレポート影響を書くべき〔real / should〕。条件不成立でも見積りは残す。ただし根拠のない秒数ではなく、所見6の機構上の評価を書く。
    **放置時の影響:** レポート訂正の必要性を矮小化するか、親が受入全走まで省略する。

## 親 brief への指摘

- **P1:** 「今回の直接計測ではsubmoduleは7.5%、他標本の代理指標も大半を支持しない。実装条件は満たされたと判断しない」に限定する。
- **P2:** 「≤1〜2秒」を撤回。絶対パスlocal cloneへのreference追加はhardlink処理を省かず、正の短縮量は未実証とする。
- **P3:** 65秒を「commondir→最終観測indexの代理区間」、20秒を「未分解残差」に変更する。
- **P4:** metadata／bytesの律速未分離、木の本数は条件付き概算、合計処理時間とwave wallは別とする。7分の参照は **F30ではなくF26**。
- **P5:** pre61.9秒は候補として記載し、「fresh木に由来する追加60秒」の同定は未了とする。

## 段 4 裁定に入れるべき変更

1. **条件付き実装は行わず、docs-onlyで完了する方針を維持する。**
2. 直接wall、mtime代理区間、仮説を分け、中央値の算式と標本の重複を訂正する。
3. `--reference`の不採用理由を「現行local cloneでは省ける処理が示せない」に修正し、依存寿命の説明は条件付きで短く残す。
4. workers・sparse・木再利用は候補の分類だけ記録し、このwaveで設定変更やprobeを追加しない。
5. 変異免除・受入全走必須は維持し、親が実走結果を記録する。

## 裁定パッケージへ返すべき択一

必要なら **checkout.workersの別診断を行うか**だけを返す。

- **推奨:** 今回は訂正したinsightで閉じ、workersの効果は未測定候補として残す。
- **代案:** 別scopeで独立環境の予備ABAを認める。ただし1回ずつの結果を採用判断や一般的短縮率にしない。

既存手順どおりの同一unit fix木再利用には、新しい裁定は不要です。

## 総括

**「実装しない」は妥当ですが、「中央値70秒対8秒で混雑を問わず約1割」「reference効果≤1〜2秒」は、そのまま成果物に残せません。** 自waveの直接計測を判断の中心に置き、mtime・代表性・効果機構・「+60秒」の不確実性を訂正してください。

必読資料はすべて読み取り済み。静的検査のみで、書込み・probe・テスト実行は行っていません。