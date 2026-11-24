# Review of the eight-page expansion

Baseline: 175f9e299c3722c870b8bde120f45e31288be059. The revision expands the existing seven-page main body to eight pages while preserving the scientific result set and template.

## Scientific checks

- Reader standardization uses the paragraphs of the 2,000 composed training examples. Shared linear weights, state-specific fitting, and candidate-restricted deployment match the existing protocol.
- The paired-query discussion describes behavioral availability of constituent answers. It preserves the distinction between this observation and intervention-based evidence about attention.
- The four-arm explanation describes each local attention-row transformation and explicitly retains downstream changes in the receiver computation.
- The shared-context account preserves two bridges by two relations, 100 receivers, 25 quadruplets, token alignment, and quadruplet-level uncertainty estimates.
- The additive reference 64+47−51=60% uses the existing Llama accuracies; 76−60=16 percentage points equals the previously audited interaction. It introduces an interpretation of existing results.
- The unique-candidate result 817/822 is already present in the audited appendix and graph records.
- The ambiguity comparison uses the same adapted checkpoint and the same graph-defined population. Joint correctness remains a complete-procedure behavioral measure.

The independent review recommended two small refinements, both incorporated: random controls are described by matching layer-wise head counts, allowing overlap with ranked heads; the input-order row is described as a controlled comparison for attention-based selection. A redundant reader-state sentence was removed and its appendix reference retained at the end of the expanded explanation.

## Section allocation

The matched source-word estimate increases by 974 words: Introduction +186, framework +342, and experimental interpretation +446. Related Work and Conclusion retain their prior lengths. The counting convention and exact section totals are in eight_page_section_allocation.json. The four supplied papers support concentrating additional space on diagnostic design and interpretation; their main-page limits and camera-ready lengths are treated separately from the current eight-page submission target.

## Layout acceptance

The current PDF has an eight-page main body, two pages containing statements/references, and fifteen appendix pages. Figures and result tables remain inside the main body; the conclusion appears on page 8. The current_pdf_qa.json record is the authoritative final PDF/hash/layout check.
