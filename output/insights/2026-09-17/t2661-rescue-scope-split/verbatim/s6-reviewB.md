## 前提の検算

**U2 静的レビューでは must-fix 0 件です。** 実装・docs は裁定に整合しています。計測時の子 stdout 捕捉と、検証結果の記載に注意点があります。

射影資料を読み、現物と照合しました。ファイル変更・pytest 実行はしていません。以下、ADC＝`tools/audit_dangling_commits.py`、CBR＝`tools/check_branch_rescue.py`、TD＝`orchestrator/tests/test_check_docs.py` と略します。

- `s5-implementation.diff` は現物の対象 **7 file** の差分と完全一致。
- `docs-parent.diff` は現物の親所有 **2 file** の差分と完全一致。
- status は計9 file の変更のみ。staged 差分・untracked はありません。
- brief の P4「台帳 entry 不要」は、正本である `s4-adjudication.md:24` により撤回済みとして評価しました。

## 入口固定

**refuted：掃除入口から repo 外走査が復活する穴は確認できません。**

- CBR:1797 の子 argv は `--offrepo-scan off` 固定。
- CBR:209 の allowlist に root env はなく、`IZANAGI_AUDIT_SCAN_WORKERS` も追加されていません。
- `_no_lazy_fetch_child_env` は CBR:230 で `_child_env()` を使用。Git 子（277）、landed 子（1571）、CLI 検証子（2182）にも root env は渡りません。
- command:37 は明示 off。overlay skill は dispatcher を参照するだけで、監査 argv の複製はありません。
- `git grep -n 'offrepo-root'` の現行手順には、runbook:860 と台帳:117 の明示 full 例だけが残っています。`docs/decisions.md:11501` は入力指定方式の説明で、flag 無しの実行例ではありません。

flag 省略＋env root の互換経路は残りますが、裁定で認めた範囲です。

## JSON / rc 契約

**refuted：既存契約の破壊は確認できません。**

CBR:1803・1809・1840 の summary 全3経路に `offrepo_scan: "off"` があり、CBR:1944 の初期値 `audit: None` は維持されています。通知3種、台帳 field、rc `0 / 2 / 3 / 64`、parser は変更されていません。

ADC の rc と rescue の rc は区別されています。ADC は findings に応じて `0 / 1`、実行不能は `2`。off＋CLI root は usage error、full＋root 無しは既存の実行不能経路です。

台帳の分岐小節より前と「覆わない範囲」以降は HEAD と byte 一致。schema・状態遷移・stale 通知・rc 表・被覆境界の逐語は不変です。TL 自体にも差分はありません。焦点走ログは集計のみですが、列挙された skip は TD の3関数で、TL の skip・失敗は報告されていません。

## pin 閉包と予算

**refuted：pin 不一致・予算超過はありません。**

| 検算対象 | 結果 |
|---|---|
| command 実 bytes | 6,181 |
| 最長行 | 105、上限110以内 |
| SHA-256 | `7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae` |
| `check_docs.py:789`／TD:581 | 実 hash と一致 |
| `_SYNTHETIC_CLEANUP_COMMAND` | 実 command と byte 一致 |
| 超過 fixture | 6,181＋改行1＋`"x" * 23`＝6,205 bytes |
| 上限 | 6,204 bytes／110、不変 |

`test_branch_rescue_ledger.py:166` の実行 edge は、新 §1 でも全候補・1回・rescue invocation・監査と台帳への同一 bullet 内参照を満たし、否定語もありません。

skill 自体は未変更です。`check_docs.py:6604` の skill hash と、6615 の command hash は別対象なので、skill digest 更新は不要です。

## docs と実装の一致

**refuted：A1 の撤回漏れ、full の過大保証はありません。**

台帳:111–123 は、off による通知・追記候補の増加、新規 `pending`、既存状態遷移への従属、full の抑止行を判断材料として残すことを明記しています。D970／D1031 の対象限定もあり、台帳 entry 免除や一般的破棄許可は導入されていません。

台帳:108 は mode を起動方針とし、完走を `complete` と区別しています。131–132 も確認不能と否定結果を分けており、「full は全件確認済み」とする断定はありません。

runbook:865–867 の説明は、off の明示開示、full＋root 無しの rc 2、省略時の従来開示と整合します。

所要受理は `s4-adjudication.md:25` と93–95で掃除入口 off に限定され、full の1走はデモです。親 docs にこれと矛盾する受理主張はありません。ただし、同裁定が要求する decisions fragment と実測結果は今回の差分にはなく、完了確認の対象外です。

## 報告と実体

差分規模は author 報告どおりです。

| 対象 | 実測差分 | 上限 |
|---|---:|---:|
| ADC | 追加39＋削除7＝46行 | 120 |
| CBR | 追加5＋削除5＝10行 | 30 |
| TA／TR追加 | 150＋102＝252行 | 450 |

author の新規8＋4関数、p04 の assert 2個追加、TD の限定変更も実体と一致します。自己申告の成功件数は `166＋88＋38＋22＝314` と算術上整合しますが、直接実走の個別証跡は今回の資料では独立確認できません。

[focus-1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/focus-1.log:1) は、login local で上限到達後、計算ノードへ dispatch して **872 passed、3 skipped** です。「login node で完走」とは記録できません。また、ログ自身が受入全走ではないと明記しています。

TD の3 skip は real-repo 検査で、cleanup 22関数ではありません。`opted_in:false` なので、author の解除 token 使用を親の解除権限として扱う必要もありません。

## scope 逸脱

**refuted：指定された scope 外変更はありません。**

T-2662 の境界 helper、T-2664 の alias 配布、T-2749 の予算定数、workers env allowlist、cleanup §2〜§5、通知 kind・台帳 field はすべて差分外です。親 docs の変更も指定小節内です。

計測 (d) は、CBR:58 の tool 隣接パスと `--repo` の独立性により、fixture repo に変更後 ADC を適用できます。ただし CBR:1799 は子 stdout を捕捉し、1843では hash のみ保存、2202では JSON のみ出力します。**通常の CLI stdout 保存だけでは子の開示行を取得できません。** TR:1718 のように実子の `subprocess.run` 結果を観測する方法なら、実装変更なしで取得可能です。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定・重要度 | 根拠・放置時の影響・最小是正 |
|---|---|---|
| U2-1 | **real / nit** | `s4-adjudication.md:96`、CBR:1799・1843・2202：CLI 出力保存だけでは子の開示行が欠け、計測 (d) の証拠が不足する；TR:1718 同様の観測方法を計測手順へ明記する。 |
| U2-2 | **real / nit** | `focus-1.log:5–14,36,42`：「login 完走」「TD 全緑」「受入全走」と要約すると検証範囲を誤読させる；計算ノード完走・872 pass／3 skip・焦点走と記録する。 |
| U2-3 | **unknown / nit** | `s5-author.md:89`：解除 token を使った22関数の直接実走は自己申告で、個別ログ未提示；親の権限や全受入の根拠に転用せず、親焦点走と区別する。 |
| U2-4 | **refuted / 修正不要** | CBR:209・1797、command:37：argv／env／規範入口の固定は成立し、掃除で全走査が復活する差分はない。 |
| U2-5 | **refuted / 修正不要** | 台帳:47・114・120・122：追記免除は撤回済みで、新規 object の記帳漏れや一般的破棄許可を導入していない。 |
| U2-6 | **refuted / 修正不要** | `check_docs.py:789,6604,6615`、TD:9948：pin・synthetic・予算は閉じており、この変更による受入赤の原因は確認できない。 |

## 総括

**実装・親 docs は U2 観点で GO、must-fix 0 件です。** 計測 (d) の子 stdout 捕捉方法と焦点走の正確な記録を補足してください。実測・変異・受入全走の完了や wave 全体の受理は、本レビューでは認定していません。
