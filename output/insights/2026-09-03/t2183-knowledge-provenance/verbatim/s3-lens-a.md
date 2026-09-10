## 宣言集合と投入集合の無関係化

- 所見: 計画どおり相互比較をしない場合、検証済み宣言 source と無関係な未検証 source を投入集合として受理できる。
- 根拠: [plan.md:10](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:10)、[plan.md:147](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:147)。現行 receipt が Git 実在検証を記録するのは宣言 `sources` だけである [knowledge_manifest.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:389)。具体的には、manifest/verified sources を集合 A、`injected_sources` を自己整合する別集合 B とし、lock に `digest(A)` と `digest(B)`、WAL に A/B を書けば、計画中の二つの独立 digest 検査はすべて通る。
- 成果物への影響: certified 選択・材料レポート・試行台帳が、宣言範囲外かつ producer の Git 実在検証を受けていない B を「実投入済み」として一貫して記録・受理する。
- 提案する最小の是正: normalized descriptor 全体で `injected_sources ⊆ declared_sources` を v2 receipt 作成時、receipt reader、WAL reader の既存検査内で強制する。現 producer は全 source を投影するため、現時点では equality を要求しても既存受理集合を狭めない。distinct-set テストは宣言 `{A,B}`・投入 `{B}` とし、宣言外 `{C}` は拒否する。

## 実投入確定点と identity の順序

- 所見: identity の循環参照自体は避けられているが、計画の pre/post digest 照合は現コードでは同じ dict の再読なので恒真的で、さらに receipt が実ファイル emit より先に発行される。
- 根拠: 計画は projection から先に digest を作り、同じ projection を `planner_context_payload()` に渡して再抽出する [plan.md:88](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:88)。現関数は渡された dict を変換・コピーせずそのまま格納する [p3_s4_loop.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:794)、[p3_s4_loop.py:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:810)。通常入力で照合を偽にする例は構成できない。一方、計画は receipt 作成後に emit する [plan.md:94](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:94) が、実際のファイル書込み点は [p3_s4_loop.py:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/p3_s4_loop.py:2008) である。receipt 作成直後に crash すれば「投入済み」receipt だけが残り、run は計画の step 8 によりそれを受理できる。
- 成果物への影響: identity は期待集合には束縛されるが、planner context が一度も emit されていない campaign でも receipt・WAL・材料レポートが実投入を主張できる。
- 提案する最小の是正: context の canonical bytes を一度だけ組み、書込み成功・close 後にその exact bytes から投入集合を抽出して v2 receipt を発行する。identity は事前候補 digest で決め、emit 後の独立 bytes と照合すれば循環しない。テストでは emit seam で source を差し替えて照合を実際に偽にする。

## 材料レポート v3 据え置き

- 所見: `additionalProperties:false` の v3 に optional property を追加する案は、旧 v3 validator を壊す一方で、新 validator には provenance を削除した新 knowledge report を受理させる。
- 根拠: 現 schema は top-level unknown property を拒否する [layer3_schema.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:5)。したがって旧 schema file を保持する consumer は、同じ `layer3-material-report/v3` literal の新 `knowledge_provenance` を拒否する。逆に新 schemaで top-level required に入れない計画 [plan.md:184](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:184) は、field を除去した knowledge-aware v3 も受理する。repo 内にも全 report を fresh rebuild と比較する consumer があり、legacy omission の補正対象は現在二欄だけである [autonomous_trial_completeness.py:4687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:4687)、最終比較は全体一致である [autonomous_trial_completeness.py:5015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:5015)。従って「repo 内 consumer は安全」という [plan.md:198](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:198) も成立しない。
- 成果物への影響: 旧 consumer は新材料レポートを拒否し、新 consumer は proof-chain 欄を剥がした新 knowledge report を schema-valid とみなす。
- 提案する最小の是正: 親 brief の P2 [brief.md:67](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/brief.md:67) に戻し、新 producer を v4・field required とする。v3/v2 reader を別 acceptance set として残し、exact-comparison consumer では v3 に限り当該欄の欠落を補正する。「既存テスト期待値を変えない」は意味的拒否の弱体化禁止に限定し、version literal の意図的 migration は許容すべきである。

## receipt と材料レポートの proof chain

- 所見: `_artifact_refs()` が receipt を hash するだけでは、receipt 内容と WAL/report provenance の一致を証明しない。
- 根拠: `_artifact_refs()` はファイル列挙と SHA 計算しかしない [layer3_report.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:195)。計画中の report helper は lock と WAL snapshot のみを受け取る [plan.md:176](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:176) のに、receipt digest まで proof chain と数えている [plan.md:179](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:179)。receipt は BUILD_START 書込時には検査される [wal.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:986) が、replay の topology 検査は WAL provenance のみを見る [wal.py:1875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:1875)。
- 成果物への影響: BUILD_START 後に receipt を別 canonical receipt へ置換すると、材料レポートは WAL の集合を載せながら、不一致な receipt の hash を proof-chain 参照として載せて受理する。
- 提案する最小の是正: report 生成時にも既存 `_knowledge_provenance_from_receipt()` 相当を再利用し、lock・receipt・一意な WAL provenance の三者一致を確認してから `_artifact_refs()` を確定する。

## v1/v2 分岐の受理集合

- 所見: lock を唯一の版 discriminator とする限り、計画された v1/v2 分岐そのものには downgrade 経路は見当たらない。
- 根拠: 現在の partial-lock 拒否は [wal.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:627)、legacy WAL exact keys は [wal.py:734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:734)、v1 receipt exact schema は [wal.py:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:810)、BUILD_START 限定・欠落拒否は [wal.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:901) にある。計画も legacy lock→v1/3-key、v2 lock→v2/4-key、その他の部分集合拒否を明記している [plan.md:141](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:141)、[plan.md:151](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:151)。
- 成果物への影響: この条件を守れば、v2 identity が v1 receipt/旧 WAL shape を受理する経路、および legacy identity が v2 shape を部分的に無視する経路は生じない。
- 提案する最小の是正: 分岐を receipt の自己申告版ではなく lock binding だけで選び、三つの lock key の全8部分集合と v1/v2 receipt・WAL shape の直積を mutation matrix に固定する。

## 一意性述語とテストの帰属

- 所見: 「全 BUILD_START の投入集合が一意」は lock digest 照合後には SHA-256 collision なしで偽にできず、独立の保護や通常の mutation-red テストにはならない。
- 根拠: 計画は各 `injected_sources` から digest を再導出して一つの lock digest に一致させた後 [plan.md:147](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:147)、さらに一意性を検査する [plan.md:157](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:157)。異なる二集合を前段で両方通す具体入力は SHA-256 collision なしには構成できない。また report は helper より前に admission を呼び [layer3_report.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:689)、admission 自身が WAL topology を検査する [artifact_admission.py:1204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/artifact_admission.py:1204)。従って [plan.md:256](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:256) と [plan.md:257](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:257) の report テストは通常、前段で赤くなる。
- 成果物への影響: 受理集合は直接は変わらないが、材料レポート層の検査が発火したという誤ったテスト証拠が残る。
- 提案する最小の是正: 一意性を防御的 assertion として残しても保護として数えず、テストするなら digest 関数を collision fixture に差し替えて helper を直接呼ぶ。report-level digest mutation は admission を固定した単体テストと、前段 admission 拒否テストに分離する。

## Web source と P4

- 所見: P4 の「digest 欄が必須」という限定判断は正しいが、Web source を v2 provenance の受理対象へ広げる根拠にはならない。
- 根拠: manifest schema は Web にも SHA 欄を要求する [knowledge_manifest.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:198) 一方、producer は live Web 解決を明示的に拒否する [knowledge_manifest.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:301)。現 WAL consumer も `repo_artifact` 以外を拒否する [wal.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:674)。共有 descriptor parser と Web report schema を追加する計画 [plan.md:101](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:101)、[plan.md:188](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:188) は、この拒否境界を明記していない。
- 成果物への影響: consumer 側まで Web を許すと、URL・時刻・自己申告 digest だけの未解決 source が receipt/WAL/report に入り、現在の拒否入力が新たに受理される。
- 提案する最小の是正: live resolution が入るまでは v2 receipt/WAL/report producer の受理 kind を `repo_artifact` に固定し、direct Web payload が必ず赤になるテストを置く。

## 既発行 v1 受領証

- 所見: 計画どおり v1 producer bytesとlegacy lock branchを保持すれば静的には可読性を維持できるが、テスト計画は既発行 bytes そのものへの回帰束縛が不足している。
- 根拠: 現 v1 receipt の exact top-level、canonical manifest、verified source 検査は [wal.py:813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:813)〜[wal.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:898)、v1 producer bytes は [knowledge_manifest.py:420](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/knowledge_manifest.py:420) にある。計画はこれらの維持を明記する [plan.md:106](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:106) が、互換テストは一般名の一件だけである [plan.md:251](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/artifacts/t2183-knowledge-provenance/plan.md:251)。既発行実物は必読射影外だったため、今回は bytes 自体を開かず、brief の記録 [brief.md:35](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/brief.md:35) に基づく判定である。
- 成果物への影響: producer と parser を同時に変えた synthesized fixture だけなら、両者が同じ誤りへ移動して既発行 receipt が読めなくなっても緑になり得る。
- 提案する最小の是正: 既発行 receipt の exact bytes を repo 内の固定 fixture として保存し、legacy lock 下で再エンコードせず読めること、既存 path を上書きしないことを検査する。既存実物は WAL が空なので、新材料レポート生成を停止する判断自体は妥当である。

## 総括

1. 最も重い穴は、宣言集合と投入集合を無関係にできる点であり、既存の normalized source 検査内に subset/equality を一つ追加すべきである。
2. 「実投入」の確定点が dict 組立て時かつ receipt が emit より先なので、照合は恒真的で crash 時に虚偽の投入証拠が残る。
3. v3 据え置きは旧 validatorとrepo内 exact-comparison consumerを壊し、同時に provenance 欠落を受理するため、親 brief の v4 案へ戻すべきである。

pytest は実行しておらず、以上は静的検査結果である。