```text
検査条件: HEAD 330f67d09eade8d556ab672e08b33d5694228887。pytest は非実走。
コード静的検査、artifact の jq 読取、directory 実査、git check-ignore、Python 3.10 pathlib 実装確認のみ。
現時点では pin=None、公式 2 directory はともに不存在、active ratified freeze も不存在。

1. [refuted] / 主張:
   brief P6・親案・段 2 案の「現行 X0 ⊊ 新 X」という単純な受理集合拡大。

   根拠:
   現行テストは pin や authority を一切見ず、directory.rglob("*") のうち
   path.is_file() が真になる path が 0 件なら通す
   (orchestrator/tests/test_s8b_oracle_manifest_contract.py:130-146)。
   提案 U は pin=None、authority=None、全 entry なしを要求するため、状態空間を同じに取ると
   現行で通る状態を削り、approved regular file 状態を追加する。両集合は包含関係でなく交差する。

   状態別の静的結果:
   - root directory 不在: 現行は受理。提案 U も受理。
   - 空の実 directory: 現行は受理。提案 U も受理。
   - 空の下位 directory、空の hidden directory、空の __pycache__: 現行は受理。
     提案 NS を文字どおり実装すれば拒否。未確認。
   - hidden regular file: Python 3.10 の "*" は dotfile に一致するため現行も拒否。提案も拒否予定。
   - __pycache__/x.pyc: 現行も拒否。git ignored でも物理的に存在すれば列挙される
     (.gitignore:2-3)。
   - regular file を指す symlink: is_file() が追従するため現行は拒否。
     directory symlink、broken symlink、FIFO、socket は現行で file と数えず受理しうる。
     提案 no-follow NS なら拒否予定。未確認。
   - pin が 64hex だが両 directory に regular file がない状態: 現行は受理するが提案は拒否する。
   - D 自体が regular file、broken symlink、directory symlink の場合は提案 NS の定義域が未指定。
     root 自身を lstat 対象に含めない実装なら fail-open しうる。未確認。

   成果物への影響:
   現在の certified 選択、レポート、台帳は変わらない。ただし裁定資料が受理集合変更を
   「拡大だけ」と誤記しており、namespace 厳格化という縮小を未裁定で混入させる。

   推奨:
   裁定へ返せ。旧集合と新集合を pin、authority、root type、全 entry type を含む同一状態空間で
   再定義し、「拡大」と「安全側の縮小」を別々に明示すること。

2. [refuted] / 主張:
   「pin=None の間は 1 byte も広がらないことを、提案されたテスト本文が保証する」。

   根拠:
   段 2 成果物にあるのは述語と設計表だけで、NS、authority loader、pin 分岐の実行可能な
   テスト本文はない。現行テストには s8b_oracle_spec の import すらなく、pin を観測しない
   (test_s8b_oracle_manifest_contract.py:13,130-146)。
   また root 自身の no-follow type 検査、走査時 PermissionError の fail-closed 化、
   symlink root の拒否が設計されていない。
   regular leaf 1 byte は意図した U なら拒否されるが、その実装挙動は未確認。

   Git 状態について:
   - tracked、untracked、ignored の区別は filesystem テストには見えない。
   - untracked reviewed_spec.json でも、物理 bytes、pin、receipt が一致すれば提案 A は緑になりうる。
     staged blob に入ったことは証明しない。
   - reviewed_spec.json 自体は現 .gitignore に該当しないが、未 stage の可能性は残る。
   - entry 511 が要求した staged blob 検査
     (output/insights/2026-08-12_t499-spec-producer-design/producer-design.md:237-240)
     は本提案の contract test に配線されていない。

   成果物への影響:
   working tree だけの緑を durable commit の成立と誤認できる。承認後の clone では file がなく、
   pin だけ残って no-approved-spec 系で停止し、承認 receipt と pin の再発行が必要になる。

   推奨:
   却下。具体的なテスト本文、root 自身を含む lstat、走査例外の fail-closed、index/staged blob 検査が
   揃うまで「1 byte も広がらない」と承認資料へ書かないこと。

3. [refuted] / 主張:
   PIN_GATE_SPEC_RAW が「承認済み exact 1 件」branch の通る正例になる。

   根拠:
   この golden は configuration_ids が
   backoff_fixed_best と stock_common の 2 件だけで、run_contract も
   env_tag="test-env"、clocks=1800、ccbench_pin="pin"
   (orchestrator/tests/test_s8b_oracle_manifest.py:61-100)。
   現 freeze は rr20、rr80 とも 6 configuration を持つ
   (holdout_freeze.json の holdouts.*.variant_binding.entries)。
   validate_reviewed_spec は freeze product を検査しないため golden を通すが、
   build_approved_manifest は全 configuration 集合との一致を要求して落とす
   (s8b_oracle_manifest.py:1192-1213)。
   計画自身も「形だけ」と認めている。外部 R も存在しないため、実際に通る承認正例ではない。

   成果物への影響:
   contract test が緑でも manifest candidate は生成できず、台帳、report、certified 選択には
   到達しない。代わりに無効な spec bytes、pin、receipt が durable 化され、承認手番を消費する。

   推奨:
   却下。active freeze、実 run contract、全 12 cell binding に束縛された production 相当の
   witness 以外を lifecycle gate の正例に数えないこと。

4. [real] / 主張:
   pin、file、receipt を同じ手が書ける限り検査は恒真化し、人間承認を証明しない。
   提案の外部 authority 保証は現状発火しない。

   根拠:
   D356 は同じ担当が bytes、hash、receipt、pin を作れば一致検査が全て通ると明記する
   (docs/decisions.md:15565-15592)。
   AuthenticatedApproval と verify_external_authority は orchestrator/campaign/ と
   orchestrator/tests/ の scoped 検索で実装 0 件。
   production loader が見るのは pin と disk bytes の SHA 一致だけである
   (s8b_oracle_spec.py:182-200)。
   test fixture も file を書いた直後に同じ hash を monkeypatch する
   (orchestrator/tests/s8b_oracle_spec_fixture.py:102-112)。

   謳うだけで発火しない保証:
   - verify_external_authority(R)
   - pin=None 時の authority 不在検査
   - bytes、authority、pin が同一 staged change にあること
   - spec fixed parent と leaf の no-follow 検査
   - runtime loader による外部 authority の再検証
   - spec 層での A3-3 発火

   成果物への影響:
   自己整合した未承認 spec が freeze その他の下流条件まで満たす場合、manifest の spec_sha256、
   schedule、n、campaign ID、binding がその値へ固定される。以後の trial 台帳、oracle report、
   median、winner、combined verdict、certified 選択まで「人間未承認」の値で進みうる。

   推奨:
   裁定へ返せ。外部 trust root と変更不能な trust anchor の所有者を決めるまで positive branch を
   有効化せず、pin=None と zero-artifact 状態を維持すること。

5. [real] / 主張:
   親の独立見解 §1、すなわち a12 判定式と配線済み judge 規則は別物である。

   根拠:
   judge は各 trial の bench_values の中央値を取り、さらにその中央値を取る
   (s8b_oracle_judge.py:131-155)。configuration 間は最大値への float 完全一致で
   unique-best または tie を決める (同:313-321)。docstring も規則が未再凍結と明記する
   (同:164-169)。
   a12 artifact の false_pass_rule.formula は
   mean - q*sqrt(s/J) > 0 であり、標本平均、標本分散、q を使う。
   s8b_verdict は judge をそのまま再導出する (s8b_verdict.py:279-286)。
   下流条件 3 は median(on)-median(off)>floor という点推定値の閾値判定で、
   q、分散、J による信頼限界ではない (同:629-651)。
   よって a12 相当規則は下流にも別途配線されていない。

   補足:
   downstream floor gate は小差を certified 結論から除くが、型 I 誤りを制御する a12 の代替ではない。
   親の主張は誇張でなく real であり、むしろ「effect threshold はあるが統計的不確実性 gate はない」
   という区別を追記すべきである。

   成果物への影響:
   a12 の q(J)、cell_pass、false-pass U は現 judge の winner、report、台帳、certified 選択を
   支配しない。これを n 根拠として書けば proof chain の参照が誤る。

   推奨:
   却下。a12 を oracle n の根拠から完全に外すこと。a12 規則へ変更する案は C1-C6 変更として
   別途裁定へ返すこと。

6. [refuted] / 主張:
   親の独立見解 §2 の n=8 は、限界を注記すれば承認値候補として提示できる。

   根拠:
   - 正規標本中央値の 1.253*sigma/sqrt(n) は、iid な単一標本中央値の漸近式である。
     現実装は reps=5 の内側 median と n 個の外側 median であり、n=8 は偶数なので中央 2 値を
     平均する。内側 median の分布密度、時系列相関、block 効果を無視した単一 median の式ではない。
   - certified 条件が使うのは on と off の中央値差である。必要なのは 2 推定量の共分散を含む差の
     誤差であり、単一中央値の SE ではない。6 configuration の argmax 安定性も評価していない。
   - Pegasus の 2 calibration は両方 rr50、skew=0.9、120 秒 noise run、within-run CV
     1.1706% と 1.2479%。対象は rr20、rr80、extime=5 秒である
     (registered/*.json の workload、noise_floor、acquisition_receipt.walltime.formula)。
     対象環境・対象 workload の between-run 分布の代用にはならない。
   - between-run 実値は linux-baremetal の rr5、rr50、rr95、extime=3 秒だけであり、
     Pegasus rr20、rr80 への移送可能性は未確認。
   - holdout_freeze.json の floor と budget は null。3% は floor_protocol の
     wired_min_rel_floor であって、現 per-pair floor 実値ではない。
   - 親の仮定をそのまま使った算術でも、sigma=1.2479%、floor/5=0.6% なら n=7 で
     SE=0.591% となり、n=8 は「最小」ではない。
     独立な 2 median の差と仮定すれば n=8 の SE は約0.782%、3% の26%で、20%以下には
     約14が要る。一方、内側5 medianをiid正規として二段近似すれば約0.310%になる。
     これらモデルはいずれも未確認であり、結論が倍以上変わること自体が現導出の不識別性を示す。
   - floor n_sessions=8 は別 estimator の数値先例にすぎず、oracle n の根拠ではない。
   - brief M4 の「U は J とともに単調増加」も artifact に反する。
     W1/H は J=9 の0.00166916からJ=10の0.00162912へ、
     W2/G はJ=12の0.00390044からJ=13の0.00381252へ低下する。

   成果物への影響:
   n は schedule 行数、予約時間、各 cell の trial_medians、median_of_medians、
   unique-best/tie、report、combined floor 判定を直接変える。誤った n は将来の
   certified 選択と trial 台帳を実質的に変えうる。

   結論:
   n=8 は承認材料として提示不可。提示できるのは「40分という費用点の一例」であり、
   統計的に導出された推奨値ではない。

   推奨:
   却下。Pegasus、rr20/rr80、extime=5、対象 configuration で outer trial median の
   between-run・paired 差分布を pilot 取得し、誤選択率または検出力目標を事前固定してから再導出すること。

7. [real] / 主張:
   N2、すなわち spec 層は A3-3 の exact 1 block を検査しない。

   根拠:
   validate_reviewed_spec と validate_approved_spec_snapshot は build_schedule だけを呼ぶ
   (s8b_oracle_spec.py:123-137,236-254)。build_schedule は複数 block を許す
   (s8b_oracle_manifest.py:221-270)。
   exact 1 block は _validate_schedule にだけある (同:278-305)。
   manifest builder は書込前にこれを発火する (同:712-725,1215-1231)。
   verify_manifest も使用前に再検査する (同:1038-1040)。

   成果物への影響:
   複数 block spec は loader、pin、契約上の「approved spec」までは通るが、
   candidate 作成時に落ちる。承認手番と durable pin/receipt を無駄にし、oracle を停止状態にする。
   一方、manifest candidate の書込、trial 台帳、report、certified 選択へは到達しないため、
   現状の帰結は誤選択ではなく承認整合性と可用性の欠陥に限定される。

   推奨:
   実装せよ。別 wave で schedule validator を共有公開関数化して spec validation から必ず呼び、
   2 block canonical spec が approval 前に落ちる負例を追加すること。
```

## 総括

倒した主張は「`X0 ⊊ X` は拡大だけ」「提案正例が実効的」「`n=8` は承認可能」の3件。  
親の N1 と N2 は real。ただし N2 は下流 fail-closed により誤選択ではなく承認・可用性の欠陥。  
最も危険な残存欠陥は、外部 trust root がなく、自己作成した bytes・pin・receipt が「承認済み」を装えること。