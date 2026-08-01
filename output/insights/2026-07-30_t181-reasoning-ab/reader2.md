```jsonl
{"packet_id":"0da6b8754c70e542dcf8869da40888ed","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"1d614167c134a0b63af3198cf501cc19","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"37b2f0861a5ac331981144f0d9e150da","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"40015ddbf07d2940070d2a2c7a1a7faa","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"7537d2ff41aad4a0967785f8b4ca7267","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"ba6f9bfa9b99752250177b99fc9b64f7","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"c17e5b2cca38ce2e050c6988606fd4f6","r1_detected":false,"decision":"GO","findings":[]}
{"packet_id":"c864cd954654b4f73ba05d7dd1d1ba3d","r1_detected":false,"decision":"NO-GO","findings":[{"root_cause":"author_patch_evidence_missing"}]}
{"packet_id":"f315c385974b9bf72b98057fe09ca093","r1_detected":true,"decision":"NO-GO","findings":[]}
{"packet_id":"f795a2d743b06cd52a4a2ada05f44d0b","r1_detected":true,"decision":"NO-GO","findings":[]}
```

## 総括

`r1_detected=true` は6件、falseは4件でした。decisionの分布はGO 3件、NO-GO 7件、unclear 0件です。新規findingは1件・root cause 1種類で、一覧は `author_patch_evidence_missing` です。これはauthor限定patch等の一次証拠がなく、最終実装差分の作業帰属を独立照合できないため、provenance成果物が誤記され得るという明示的な成果物影響を伴う指摘として数えました。

迷った点は、bare CRが読取入口でLFへ正規化される指摘の扱いです。発生箇所はparser内部より手前ですが、非LF境界による誤分割という根因と受理集合への影響はA-1と意味同値と判断し、新規には数えませんでした。M2 fixtureやmutation controlの単一理由性に関する指摘もB-3と同根です。また、二次的な履歴走査コストや再追加専用fixtureの欠落は、本文が具体的な現成果物影響を認定せずbacklogまたはrelease findingとしてrefutedとしていたため、保守的に除外しました。

codebookで明示されていない境界は、機能欠陥ではなく一次証拠の欠落そのものを新規findingに含めるか、および「コスト構造はrealだがrelease blockerではない」という指摘を数えるかです。前者は本文内に根拠と具体的なprovenance成果物影響が揃っていたため採用し、後者は成果物影響が示されていないため不採用としました。R-1とdecisionについては各本文の肯定・否定および最終結論が明示されており、codebook上で判定不能となるpacketはありませんでした。