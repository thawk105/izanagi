## レンズ A

**must-fix は 1 件。merge 一括化 (c) は、現状の argv のままでは等価ではありません。** (a)(b)(d) に具体的な判定差は見つかりませんでしたが、成立条件と変異の帰属には補足が必要です。

以下、行番号は指定 worktree の checker／tests、および親 brief／plan を指します。

### must-fix

**M1 — (c) `diff.ignoreSubmodules` による親別 path 集合の差を保持していない。**

- **根拠:** checker:1640 の現行取得は porcelain `git diff`。plan「(c) merge の親別集合」は plumbing `git diff-tree` に置換する。Git 2.34.1 では前者が `git_diff_ui_config`、後者が `git_diff_basic_config` を読み、`diff.ignoreSubmodules` は UI 側で処理される。`--no-renames` はこの差を消さない。[builtin/diff.c](https://github.com/git/git/blob/v2.34.1/builtin/diff.c#L428)、[builtin/diff-tree.c](https://github.com/git/git/blob/v2.34.1/builtin/diff-tree.c#L109)、[diff.c](https://github.com/git/git/blob/v2.34.1/diff.c#L323)
- **成果物への影響:** `diff.ignoreSubmodules=all` の下で、両親と異なる gitlink を持つ merge が、旧版の受理から新版の `missing-codex-author` に変わり得る。
- **具体例:** 実装面に分類される `tools/vendor` を gitlink とし、merge の参照先を両親のいずれとも異ならせる。個別 submodule ignore の上書きがなければ、旧親別集合では除外され、新 batch では含まれる。後段の `--cc` も plumbing なので、global 設定による除外を復元しない。
- **是正案:** まず (c) を見送るか、設定依存の等価性を満たさない場合は旧経路に戻す。設定を明示 argv に移すなら、`submodule.<name>.ignore`／`.gitmodules` の優先関係も維持すること。単純な `--ignore-submodules=none` 追加は旧判定を変える。実 Git fixture で親別集合から最終 finding・rc まで比較する。

`submodule.<name>.ignore` は両コマンドが使う共通 diff 処理でも参照されるため、「plumbing は submodule 設定を全部無視する」も誤りです。[submodule.c](https://github.com/git/git/blob/v2.34.1/submodule.c#L193)

一方、`diff.noprefix` は今回の name-only 出力に prefix を追加・除去せず、`core.quotePath` の引用は `-z` で回避されます。`diff.orderFile` の順序差は merge の集合化で消えます。`diff.relative` は REPO が repository root である今回の前提を明記すべきです。これらを M1 と同じ判定差として数える根拠はありません。

### should

該当なし。以下は、現計画のままでは成果物が変わるとまでは断定できないため、指定基準に従い nit とします。

### nit

**N1 — (a) 結論は妥当だが、「pathspec 無し」だけを等価性の根拠にしない。**

- **根拠:** plan:36–45、checker:1883–1927。`--parents` は親書換えを有効にするが、今回の固定 argv では tree pruning が有効にならない。`--topo-order` は commit の出力順を制御し、親列を並べ替えない。したがって guards 成立下の固定 HEAD 完全閉包では `%P` と順序込みで一致する。[Git 2.34.1 revision.c](https://github.com/git/git/blob/v2.34.1/revision.c#L2101)
- **成果物への影響:** 今回の固定 argv では差なし。説明を「pathspec 無しなら常に安全」と一般化すると、将来の取得条件変更を誤って許容する。
- **是正案:** 次の境界を論証に明記する。
  - pathspec による TREESAME 簡約。
  - **pathspec がなくても** `--simplify-by-decoration` による簡約・親書換え。
  - pruning と組み合わされた `--simplify-merges`、`--full-history --parents` 等の親書換え。`--full-history` 自体は「生の親列」を保証する指定ではない。
  - range・除外 revision・日時制限・first-parent 等による閉包欠落は、親書換えと区別する。これらすべてが単独で親列を書き換えるわけではない。[履歴簡約の文書](https://git-scm.com/docs/git-rev-list#_history_simplification)

閉包外親は root と解釈せず、計画どおり親キャッシュ全体を破棄する。現行 ancestry が未知親を無視することは、親表注入の正当化にはならない。

また、**selected 外と index 外は別物**です。policy 導入前や再利用 prefix の commit にも親はあり、HEAD 閉包の index には含まれます。親表を selected だけに縮めないこと。HEAD 到達外の要求は通常 authoritative 入力ではなく、cache miss なら `%P` に戻す必要があります。

**N2 — (b) 見出し契約は成立する。最終 hex path の抜けは計画本文にはない。**

- **根拠:** plan:62–70。Git 2.34.1 の commit 入力は `show_log` で `line_termination` を出し、`-z` なら `<oid>\0`。空差分は `--always` が同じ見出しを出す。対して **tree OID pair** の見出しは専用処理の `<tree1> <tree2>\n` であり、混同できない。[log-tree.c](https://github.com/git/git/blob/v2.34.1/log-tree.c#L573)、[stdin の commit/tree 分岐](https://github.com/git/git/blob/v2.34.1/builtin/diff-tree.c#L19)
- **成果物への影響:** 記載された全 token 検査なら差なし。最後の要求見出しを読んだ時点で検査を打ち切る実装は、衝突を見逃す。
- **是正案:** 最後の commit の path に「既知 OID」「未知 OID」「64 桁 hex」を置く fixture を明示する。未知 hex も見出し候補なので、要求列との完全一致に失敗して全体 fallback する。これは既存設計の確認であり、新方式は不要。

同じ環境・設定と正常 object を前提に、通常 non-merge、root、空 tree root、空 commit、type change、gitlink は、見出しを除いた path 列を現行と一致させられます。双方とも plumbing であり、root／再帰／rename 無効化の指定が一致しています。

改行・tab・CR・非 ASCII は NUL 分割を壊しません。ただし既存 `_git` の text-mode 改行変換も維持する必要があります。不正な文字コードは batch を破棄して旧取得で処理する境界です。hex path は高速経路を断念するケースであり、監査対象から除外するケースではありません。

**N3 — (c) 仮親と親番号 batch の設計自体は正しい。**

- **根拠:** plan:85–100。Git 2.34.1 の `stdin_diff_commit` は後続 commit OID で先頭 commit の親リストを置換する。従って `<merge> <parent>` は parent→merge の比較になる。初出順で selected を重複除去し、親番号ごとに各 merge を一度だけ列挙すれば、同一 batch 内の見出しも一意になる。[stdin_diff_commit](https://github.com/git/git/blob/v2.34.1/builtin/diff-tree.c#L20)
- **成果物への影響:** この構成による差は認めない。ただし M1 の設定差は独立して残る。
- **是正案:** 重複除去が**取得要求だけ**に適用され、worker の selected 重複監査を保存することを pin する。同一親を複数 slot に持つ場合も slot を勝手に統合しない。

方向反転は現在の全 status filter・rename 無効・name set では等価変異になり得ます。この注記は正しい。ただし stdin の行反転は見出し OID も変えるので、実装上は検証不成立から fallback する可能性があります。向きの契約違反と provenance 判定差は別に記録すべきです。

**N4 — (d) 値共有は固定設定下で等価。「二回目も絶対同じ」ではない。**

- **根拠:** checker:1323、1481、1611、1976–2012、plan:121、165。両 validator は values を変更しない。現行の parse 条件も同一。
- **成果物への影響:** 固定環境では差なし。監査途中に repo/global config、include 先、Git 実行系等が変われば、旧版の二回目だけ異なる結果になる可能性はある。
- **是正案:** 計画にある「監査中の設定不変」という等価性の前提を維持する。通常の固定入力に対する Git parser の非決定性を、別の阻害要因として扱う根拠はない。

`None` と `[]` の区別は必要です。ただし falsy 判定への変異は、固定設定なら主に再 parse 回数を変えるため、判定差の kill と呼ばないこと。message-file・waiver・oracle の従来呼出しを残す設計に矛盾は見つかりません。oracle にも無条件で事前 parse を追加する実装は計画外です。

**N5 — 変異表は「判定差の kill」と「呼出し契約の kill」を混同している。**

- **根拠:** plan:230–250、checker:1650–1710、tests:1577–1889。
- **成果物への影響:** テスト計画の説明だけでは成果物は変わらないが、誤った kill 理由では判定不変の証拠にならない。
- **是正案:** 各変異を単独適用し、到達した変更行、最初に破れた assertion、公開結果差の有無を記録する。特に以下を修正する。

| 変異 | 静的評価 |
|---|---|
| intersection→union | side-only path は後段の実 `--cc` でも除外される。指定 fixture の「偽陽性」は成立しない。候補列・余分な subprocess の pin で検出する。 |
| root の `None`→falsy、空 values の `None`→falsy | 主に取得回数の契約違反。判定差とは分ける。 |
| path の sort／set 化 | fixture の列が実際に変わることが必要。validator は実装 path を再 sort するので、helper の列差が finding 差になるとは限らない。 |
| 終端・件数・順序検査の個別削除 | 他の検査が同じ破損を拒否すれば survivor になる。各検査だけで拒否される入力を用意するか、冗長検査として分類する。 |
| 部分結果返却・親集合複製・別 message 値の注入 | 判定差を作れる候補。ただし実 Git／実 validator を残した反例が必要。 |

既存 tests:7295 付近は `HistoryAudit` の authoritative 比較を持つ一方、公開出力比較は `_run_range` 経由です。(a)(b)(c) は range で無効なので、その公開比較を流用するだけでは高速経路を通りません。authoritative CLI で高速経路の発火を確認してから、独立した旧取得との結果を比較してください。計画にある全史旧新版比較は、この不足を補うものです。

また、旧新版の両方で `_combined_diff_paths` や validator を同じ stub に替えると、両層が緑でも判定等価の証明になりません。

**N6 — 親 brief の数値は、測定区間と一般化の強さを修正すべき。**

- **根拠:** brief:9、17–31、指定 profile 表・micro 表。
- **成果物への影響:** 現判定は変わらない。速度改善量や dispatch 方針の確実性を過大評価する。
- **是正案:**

| 主張 | 評価・修正 |
|---|---|
| `_commit_paths` 66% | `838.9 / 1272.8 ≈ 65.9%`。worker の `_normal_commit_audit` 累積時間に対する比率。wall の66%ではない。 |
| 計算ノード41.7秒／CPU288秒 | profile の A 区間で支持される。prelude が別掲されており、CLI 全区間との同一視は避ける。 |
| login88.1秒／混雑時428–574秒 | 指定された一次ログには当該走の全記録がなく、今回は brief の報告値としてのみ確認。41.7秒との同条件比較ではない。 |
| sys が83秒増えたため wall が CPU 総量に近づく | CPU競合は説明候補だが、I/O待ち等との分離は未測定。因果の確定とはしない。 |
| tempdir 等74秒 | `136.2−62.4=73.8秒` は関数内の subprocess 外を含む累積差。tempdir 単独の費用でも wall 短縮上限でもない。 |
| 480秒に確実に収まる | 混雑上限を固定していない以上、保証にはならない。指定条件での改善実測を完了基準にする。 |
| dispatch失敗率3.5%、待ち時間分布 | 残存受領証の標本値。将来の失敗確率・尾部保証へ一般化しない。 |
| trailer重複2,224回 | `13,993−11,769` と整合する。micro の単一 message 一致は ambient 設定全体の等価性を証明しない。 |

**N7 — attributes の実装読解は正しいが、「tip を跨ぐと全 partition 失効」は条件付き。**

- **根拠:** checker:2156–2229、brief:25–27、D2045。全 index entry の path から祖先 directory の `.gitattributes` 候補を列挙し、存在しない候補も名前と `absent` を digest に含める。
- **成果物への影響:** 判定は変わらず、受領証再利用の可否と費用が変わる。
- **是正案:** 「新しい祖先 directory を持つ tracked path が現在の index に加わると、属性 file が増えなくても fingerprint が変わる」と記す。

`head` 引数はこの関数では使われず、tip tree 自体には依存しません。空の未 tracked directory、既存 directory 内への通常 file 追加、index を変えない tip 移動では、この理由だけの失効は起きません。「全 partition」は旧 directory 集合に束縛された受領証についての主張に限定すべきです。「land がほぼ毎回 cold」は wave ごとの index 変化を確認して初めて頻度として言えます。

## 総括

**(c) は設定差を修正するまで採用不可。** `diff.ignoreSubmodules=all` と gitlink merge が具体的な判定差の反例です。

(a) の親順、(b) の NUL 見出しと末尾 hex path 検出、(d) の値共有は、計画の限定条件下で妥当です。変異表では特に intersection→union の kill 理由を修正し、判定差と取得回数の差を分けてください。

指定資料を読んだ静的検査です。書込み・pytest・変異実走・性能測定は行っていません。