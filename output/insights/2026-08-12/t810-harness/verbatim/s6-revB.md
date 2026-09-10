結論は **NO-GO**。中心契約である「外部承認 receipt」と「手続きの凍結」が、現在の公開 API と runtime 経路を拘束していない。

静的検査のみ実施し、pytest は走らせていない。

## 所見

### 1. blocker — receipt は外部権威ではなく、caller が自己発行できる

親裁定は「artifact 自身から expected digest を導出する経路を API に持たない」と要求しているが、実装が検査するのは、任意 caller が渡す digest・任意の非空 `approval_id`・schema version だけである。[t810_preregistration.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:121)

CLI も caller 指定の任意ファイルを `ApprovalReceipt(**approval_value)` にしているだけで、署名、issuer、承認 stage、protocol ID、trust root を検査しない。[validate_t810.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/validate_t810.py:43)

したがって公開 API だけで次が可能である。

```python
raw = path.read_bytes()
receipt = ApprovalReceipt(
    artifact_sha256=sha256(raw).hexdigest(),
    approval_id="self-issued",
    schema_version=APPROVAL_RECEIPT_SCHEMA_VERSION,
)
load_t810_preregistration(path, approval_receipt=receipt)
```

テスト自身の `_receipt_for(raw)` が、まさにこの自己発行能力を示している。[test_t810_preregistration.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_preregistration.py:60)

さらに `VerifiedT810Preregistration` は公開 dataclass なので、loader を通さず mutable な任意 projection を構築できる。validator は `isinstance` と `run_authorized == false` しか確認しない。[t810_validator.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:848)

**放置時の影響:** artifact と自己発行 receipt を同時に差し替えるだけで、N・R・τ*・区間式・終端状態・下流許可表を「承認済み」として変更でき、certified 成果物の受理集合と参照先が丸ごと変わる。

必要なのは、artifact digest、protocol ID、承認 stage、approval ID を署名した receipt と、wave から独立した trust root による署名検証である。fixture digest をテストと同じ commit に置く方式は外部権威にならない。

### 2. blocker — 終端 FSM が親裁定と逆で、同名実装が二つある

親裁定は、receipt 欠損・矛盾を最優先し、次に `measurement_start` 実在を評価して `incomplete_after_start` へ倒す。[s4-adjudication.md:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/output/insights/2026-08-12_t810-harness/s4-adjudication.md:82)

validator 側はその順序を実装している。[t810_validator.py:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_validator.py:621)

一方、参照 estimator の `classify_terminal_state()` は `pre_release_invalid` boolean を最初に評価する。[t810_estimator_v1.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_estimator_v1.py:73) テストも全 failure が同時に真なら `pre_release_invalid` と期待しており、誤った順序を固定している。[test_t810_estimator_v1.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_estimator_v1.py:280)

つまり同一 repository に、同じ名前で逆の分類を返す公開関数が二つ存在する。7 本の golden は invalid terminal evidence を一つも入力しない。

**放置時の影響:** measurement 開始後または receipt 不完全な attempt が retry 可の `pre_release_invalid` に誤分類され、次 attempt の性能値を選び直せるため、採用 attempt と受理集合が変わる。

estimator 側の重複 FSM を除去して validator の一実装へ集約し、欠損・矛盾・開始済みが同時に存在する vector を凍結対象に含めるべきである。

### 3. blocker — golden は runtime の estimator を拘束していない

loader が golden について検査するのは「list で 7 件以上」だけで、ID、入力 schema、期待 field、意味論を検査しない。[t810_preregistration.py:390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:390)

また、production code には golden を再生する conformance gate がなく、`evaluate_t810()` の production consumer もない。`version_id` は文字列一致だけで、実行 module の bytes や conformance receipt に束縛されていない。

7 本すべてを通る実装差し替えを具体的に構成できる。例えば `terminal_reduced` だけ slope 分散の分母に選択時 N=13 を再利用する、または reduced 時の slope gate を常に false にする。唯一の reduced vector は全 node の傾きが同じなので gate は false のままであり、全 golden が通る。実データで reduced 12 node の傾きが不均一なら、結論だけが変わる。

同様に、golden は以下を拘束しない。

- invalid 3 状態の FSM
- reduced 状態で発火する slope gate
- raw throughput から自然対数行列を作る経路
- §5.1 の副次量
- 下流対応表を実際の判断へ適用する consumer

**放置時の影響:** 同じ artifact digest と同じ estimator version ID のまま、実測時だけ異なる τ、gate、結論 code、下流 fan-out 許可を生成できる。

runner/preflight が実行 module の identity と golden conformance receipt を必須検査する必要がある。加えて reduced slope、invalid FSM、log 変換、副次出力を vector に含めるべきである。

### 4. blocker — F backend の選択が環境依存で、境界 vector は 1 ULP 下側

実装は SciPy の有無で `scipy.stats.f.ppf` と独自 beta-bisection を切り替える。[t810_estimator_v1.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_estimator_v1.py:20) artifact には backend、SciPy version、libm、許容誤差、丸め規則が無い。

`upper_equality_boundary` は等号ではない。現在環境では次の値だった。

```text
tau_U    = 0x1.89374bc6a7ef9p-8
tau_star = 0x1.89374bc6a7efap-8
```

つまり 1 ULP 小さく、結論は `material_node_difference_refuted` である。artifact 自身も「within-one-binary-ulp」と書いている。[t810_prereg_v1.json:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:453)

テストは F 分位に絶対誤差 `2e-13` を許しながら、判定は狭義比較なので、許容範囲内の backend 差でも `refuted` と `underdetermined` が反転しうる。[test_t810_estimator_v1.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_estimator_v1.py:146)

**放置時の影響:** SciPy の有無や数値 backend の差だけで `τ_U < τ*` の真偽が反転し、job 間 fan-out の許可と T-139 感度表の生成可否が環境ごとに変わる。

F 分位を二つの自由度組について固定 binary64/hex 定数にするか、単一 backend・版・丸めを凍結すべきである。等号の判定確認は行列から 1 ULP 境界を逆算せず、`conclusion_code()` への exact scalar vector として artifact に持たせるべきである。

### 5. must-fix — golden の「独立導出」が部分的に恒真

`_independent_interval()` は F 分位を SUT の `f_quantile()` から取得している。[test_t810_estimator_v1.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_estimator_v1.py:137) したがって F 実装そのものの誤りに対する独立 oracle ではない。

さらに、

- artifact の期待値
- preregistration test の fixture digest
- estimator test の fixture digest
- estimator 実装

を同じ commit で同時更新できる。repo 外の署名済み pin は存在しない。これは「実装出力を焼き直して digest を更新する」変更を拒否できない。

境界 vector にも弱点がある。

- `upper_equality_boundary` は等号でなく 1 ULP 下。
- `slope_gate_strict_boundary` も `S_beta == 2V_beta` ではなく、浮動小数点上では `S_beta < 2V_beta`。
- `upper_truncated_to_zero` は `MS_A = MS_E = 0` で、負値の切捨てを直接検査しない。M6 は別の `slope_gate_fires` vector が負分散になるため偶然 KILL される。

**放置時の影響:** estimator のバグと expected 値・fixture digest を一緒に焼き直すと全テストが緑のまま τ と結論 code が変更され、同じ名前の凍結手続きが別物になる。

F 定数と期待値を別実装・別 authority から導出し、導出式・hex 値を固定する必要がある。fixture receipt の更新は通常実装 commit から分離し、人間署名を要求すべきである。

### 6. must-fix — canonical benchmark argv 追加だけでは同型穴が残る

親の「exact benchmark argv 配列を artifact へ追加」は必要だが、次の手続きがまだ値だけ、または宣言だけである。

- build argv は `required: true` 等の条件しかなく、exact 配列／placeholder 展開規則がない。[t810_prereg_v1.json:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:95)
- qsub、Python wrapper、runner、benchmark の各 command layer のうち、qsub の exact argv がない。`submission_argv_comparison: exact` は比較対象を持たない。[t810_prereg_v1.json:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:622)
- §3.2 の seed と permutation は field 名だけ。PRNG、slot domain、順列生成法、qsub への適用順、canonical encoding がない。[t810_prereg_v1.json:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:66)
- `response: natural-log-throughput` はあるが、raw field の選択、非正値の扱い、float parse、log 実装を拘束しない。estimator は既に log 済み行列を受け取るだけである。
- §5.1 の副次量カテゴリ列挙は artifact にあるが、参照 evaluator は raw-scale fit、κ、ICC、node summary、完全な drift diagnostics を出さない。[t810_estimator_v1.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_estimator_v1.py:35)
- §7 の対応表は値として存在するが、これを下流判断へ適用する consumer がない。[t810_prereg_v1.json:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/tools/pegasus/policies/t810_prereg_v1.json:324)

**放置時の影響:** 同じ測定 literal を使いながら投入順、実行 command、log 行列、副次レポート、下流許可の適用を変えられ、採用 attempt・τ・材料レポート・proof chain の参照が変わる。

command は builder/qsub/wrapper/benchmark の層別 exact 配列または型付き template として凍結し、seed 展開、入力変換、出力 schema、下流 consumer まで閉じる必要がある。

### 7. must-fix — `_walk_no_hidden_design` は隠し候補を塞いでいない

walker が拒否するのは key 名に `candidate` または `design_option` を含む場合だけで、文字列値は見ない。[t810_preregistration.py:180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:180)

例えば次は通る。

```json
"assurance": {
  "minimum": "0.80",
  "alternatives": [{"N": 12, "R": 12}]
}
```

`design` 直下の key 集合は閉じているが、`assurance`、`dropout_assurance`、`repetition_precision` 等の nested schema は閉じていない。文字列内へ `12/12` 表を埋めても通る。

現テストは `design.hidden_candidate` を追加するため、walker に到達する前の `_exact_keys(design, ...)` で落ちる。walker 自身の検出力を検査していない。[test_t810_preregistration.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/tests/test_t810_preregistration.py:146)

**放置時の影響:** 12/12 等の代替設計を承認 artifact 内に温存し、結果や費用を見た後に N・R・自由度・測定集合を再選択できる。

blacklist walker ではなく、`design` 以下の全 object を exact schema と exact literal で再帰的に閉じるべきである。

### 8. nit — canonical bytes と loader 由来 projection の深い不変性は成立

この部分は確認できた。

- digest は再直列化後ではなく raw bytes を hash している。[t810_preregistration.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:151)
- `object_pairs_hook` は nested object にも適用され、Unicode escape 後に同じ key になる duplicate も拒否する。
- exponent 表記、float、NaN/Infinity、`-0` は拒否する。
- `ensure_ascii=True`、`sort_keys=True`、`separators`、`indent=2`、末尾 LF が明示されている。[t810_preregistration.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:107)
- loader から得た projection は dict→`MappingProxyType`、list→tuple を再帰適用しており、nested mutable は残らない。[t810_preregistration.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-harness/orchestrator/campaign/t810_preregistration.py:395)

ただし整数範囲、Unicode scalar validity／正規化は明示されていない。現在の ASCII artifact では直ちに値を変えないため nit とする。公開 dataclass を直接構築した場合の mutable projection は所見 1 の authority bypass に含めた。

## golden／手続き被覆

| 対象 | 静的判定 | 根拠 |
|---|---|---|
| `F_0.05` / `F_0.95` 入替 | 殺せる | normal vector、固定期待値、直接式 test |
| `max(0,·)` 削除 | 殺せるが間接的 | zero vector 自身は無力。負分散になる slope-fire vector が例外化 |
| `R` の除算位置 | 殺せる | interval の直接式 test と非ゼロ vector |
| reduced の自由度 | 殺せる | N=12 と誤った N=13 の差を直接比較 |
| slope `>` / `>=` | unit test は殺す | golden の「等号」は厳密等号でない |
| 判定行の順序 | 部分的に殺す | slope-before-interval と invalid-before-slope の直接 test |
| `τ_U` / `τ_L` 等号 | unit test は殺す | upper golden は 1 ULP 下で等号を拘束しない |
| invalid 終端 FSM | golden は無被覆 | unit test はむしろ親裁定と矛盾 |
| reduced slope gate | 無被覆 | reduced vector は傾き不均一性なし |
| log 変換・副次量・下流対応 | 無被覆 | estimator の入力外／出力外、consumer 不在 |

## 事前登録変異の静的予測

| 変異 | 予測 | 殺す検査／注意 |
|---|---|---|
| M3: 再直列化後を hash | **KILLED** | `_verify_approval_digest()` へ noncanonical raw と canonical を別々に渡す test が赤になる |
| M4: receipt 無視・自己 digest | **KILLED** | digest が全 0 の receipt を拒否する test が赤になる |
| M5: F 分位入替 | **KILLED** | normal golden、独立 interval 配置、`tau_U > tau_L` が赤になる |
| M6: 切捨て削除 | **KILLED** | `slope_gate_fires` vector で分散が負になり `sqrt` が失敗。ただし名指しの zero vector は kill 理由にならない |
| M7: `>` → `>=` | **KILLED** | `slope_gate_fires(2.0, 1.0) is False` が赤になる |
| M8: reduced で N=13 自由度 | **KILLED** | reduced 専用 test が `(12,11,99)` と誤差 `>1e-4` を固定 |
| M13: seal 迂回 | **KILLED** | `request_t810_launch()` が成功する形、または validation result に launch を追加する名指し変異は赤になる |
| M13 同型: `VerifiedT810Preregistration` の直接構築 | **SURVIVED** | 公開 constructor と `isinstance` 検査を使う loader/receipt 迂回には負例がない |

## 総括

**NO-GO。**

最も危険な穴は、**承認 receipt が外部権威ではなく caller 自身で発行できること**である。これが残る限り、raw-byte hash、canonical JSON、golden、immutable projection を個別に強化しても、artifact と receipt を一緒に更新するだけで凍結全体が恒真化する。

その次に、親裁定と逆の終端 FSM が参照 estimator とテストに固定されている点、および golden を runtime 実装へ強制する conformance 経路がない点が blocker である。