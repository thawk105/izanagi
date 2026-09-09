## 実装への所見

- **refuted — 新しい拒否は恒真ではない。** manifest は registry 全体ではなく、適格行の先頭 201 件だけから生成されるため、正規発行された publication でも registry-only 行が存在し得る。[p3_b4_analysis_ledgers.py:1071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1071)、[p3_b4_analysis_ledgers.py:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1083)、[p3_b4_prerun_issuer.py:796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:796)  
  影響: 受理集合は従来集合と「loaded manifest に一意に属する」の積へ狭まり、manifest 外の registry 行による campaign を除外する。

- **refuted — 実装に受理集合を広げる変更はない。** publication の厳格 load 後に membership を追加し、従来の registry 一意性・driver・hash 照合はすべて残っている。[p3_s4_loop.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:493)、[p3_s4_loop.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:499)、[p3_s4_loop.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:508)  
  影響: certified 選択・report・台帳値・参照 publication の決定には変更がなく、bootstrap admission だけが縮小する。

- **real — 検査順は受理集合ではなく拒否理由を変える。** membership が registry/driver/hash より先なので、manifest 外かつ driver/hash 不一致の行、または完全に未知の attempt は、従来理由ではなく membership 理由で停止する。[p3_s4_loop.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:499)、[p3_s4_loop.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:508)、[p3_s4_loop.py:513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:513)  
  影響: 受理集合と成果物値は同じだが、重複して不正な入力の観測エラー分類が membership 優先へ変わる。これは段4で事前登録された等価順序変異と整合し、must-fix ではない。

## テストへの所見

- **real — 現在の負例は membership 分岐自体には到達するが、正規 publication の受理境界を迂回している。** テストは attempt_id だけを変えた行を registry に追加し、loader を monkeypatch している。[test_p3_b4_proposal_binding.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:107)、[test_p3_b4_proposal_binding.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:113)、[test_p3_b4_proposal_binding.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:126) この合成 registry は block_id が重複し、schedule receipt、canonical bytes、sealed hash も更新されないため、正規 loader が受理できる publication ではない。[p3_b4_analysis_ledgers.py:470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:470)、[p3_b4_analysis_ledgers.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:686)、[p3_b4_prerun_issuer.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:1140)  
  影響: 放置すると、membership コードの単体分岐は証明できても、「実 loader が受理した publication に対して D1880 が受理集合を狭めた」という検査証拠にならない。

- **real — 差し替えなしの実体的負例は構成可能であり、monkeypatch は最後の手段ではない。** issuer は 201 件以上の適格 scheduled input を許し、manifest はその先頭 201 件だけを選ぶ。[p3_b4_prerun_issuer.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:709)、[p3_b4_prerun_issuer.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:801)、[p3_b4_analysis_ledgers.py:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_analysis_ledgers.py:1083) したがって、driver/hash が一致し、attempt_id・block_id・ordinal が一意な 202 番目の適格行を実 issuer で発行し、その attempt を指定すればよい。  
  影響: この形なら loader・receipt・完全性再生成をすべて通過した上で membership だけが拒否し、D1880 の実在する受理集合差を証明できる。

- **refuted — monkeypatch 後の現在の負例は DW-M03 の単一理由性自体は満たす。** コピー元から driver/hash を保持し、document hash の一致と manifest 不在を明示しているため、合成オブジェクト上では membership だけが赤になる。[test_p3_b4_proposal_binding.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:108)、[test_p3_b4_proposal_binding.py:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:120)、[test_p3_b4_proposal_binding.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:134)  
  影響: hash/driver 層による偽陽性ではないが、上記の publication 実体性不足は残る。

- **refuted — 既存期待値の緩和・反転はない。** 既存 behavioral test は変更されず、変更された既存期待値は NON_GUARANTEES の exact tuple pin だけで、実装文字列と一致する。[test_p3_b4_proposal_binding.py:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:569)、[p3_s4_loop.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:172)  
  影響: 既存の受理・拒否期待を広げず、D1880 により陳腐化した文字列だけを更新している。

## 非保証文言への所見

- **refuted — 新しい項目3は過剰でも過少でもない。** 文言は「読み込んだ publication」の manifest 外 bootstrap attempt の拒否だけを主張し、その manifest の権威性を明示的に否定する。[p3_s4_loop.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_s4_loop.py:173) D1881 と別 root 再発行は項目2および issuer の非保証、continuation は項目1、耐久証拠は項目4として残っている。[p3_b4_prerun_issuer.py:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:8)、[p3_b4_prerun_issuer.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/campaign/p3_b4_prerun_issuer.py:53)  
  影響: D1880 が閉じた loaded-manifest membership だけを表し、publication 権威、別 root、continuation、耐久証拠、report/certified 接続を閉じたとは読めない。

## must-fix 一覧

1. [test_p3_b4_proposal_binding.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:94) の負例を、loader monkeypatch と不整合な `dataclasses.replace` publication から、実 issuer が発行して実 loader が受理する registry-only attempt に置き換える。推奨形は 202 件の適格行を発行し、先頭 201 件の manifest から外れる 202 番目を、同一 driver・一致 proposal hash で指定すること。

## 総括

実装本体は D1880 どおり受理集合を狭めており、恒真化・既存ゲートの撤去・規律2違反・非保証の過剰主張はありません。must-fix は負例の実体性 1 件です。現在のテストは membership 分岐の単体検査としては有効ですが、実発行・実 loader 経路で構成可能な負例がある以上、その経路を迂回する根拠はありません。

pytest は実走しておらず、実装子報告の `26 passed` を独立確認済みとは扱っていません。