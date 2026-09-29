# Held-out comparison

Headline numbers are the test split. Development items were not used to change the judge.
Level 2 retrieves with the benchmark rewrite. Level 3 uses that rewrite only if the judge accepts it.
Hit@1 is against the document for the original request. Recall@3 uses the top 3 chunks.

## Test judge

### Test

- Harmful Rewrite Detection Rate (HRDR): 1.000 (31 harmful)
- Harmful false acceptance rate: 0.000
- Safe rewrite rejection rate: 0.480 (25 safe)
- Ambiguous accuracy: 0.769 (13 ambiguous)
- Ambiguous macro F1: 0.435

## Test retrieval

| Level | Hit@1 | Recall@3 | Fact coverage | Faithfulness | Harmful rewrites reaching retriever |
| --- | ---: | ---: | ---: | ---: | ---: |
| Level 1 baseline | 0.855 | 0.947 | 0.870 | 1.000 | 0.000 |
| Level 2 rewrite | 0.870 | 0.971 | 0.870 | 1.000 | 1.000 |
| Level 3 judge | 0.899 | 0.976 | 0.913 | 1.000 | 0.000 |

### Test retrieval by rewrite label

| Label | n | L1 Hit@1 | L2 Hit@1 | L3 Hit@1 |
| --- | ---: | ---: | ---: | ---: |
| safe | 25 | 0.800 | 0.960 | 0.920 |
| harmful | 31 | 1.000 | 0.871 | 1.000 |
| ambiguous | 13 | 0.615 | 0.692 | 0.615 |

## Test by category

| Category | n | HRDR | False acceptance | Safe rejection | Ambiguous accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| abbreviation | 5 | — | — | 0.000 | — |
| ambiguity | 3 | — | — | — | 0.667 |
| constraint | 6 | 1.000 | 0.000 | 0.500 | 1.000 |
| entity | 7 | 1.000 | 0.000 | — | 1.000 |
| intent | 1 | 1.000 | 0.000 | — | — |
| multi_constraint | 2 | 1.000 | 0.000 | — | — |
| negation | 6 | 1.000 | 0.000 | — | — |
| number | 9 | 1.000 | 0.000 | 0.000 | 1.000 |
| scope | 7 | 1.000 | 0.000 | 1.000 | 1.000 |
| semantic_equivalent | 12 | — | — | 1.000 | 0.000 |
| synonym | 4 | — | — | 0.000 | — |
| temporal | 7 | 1.000 | 0.000 | — | 1.000 |

## Development split (not used to tune)

### Development

- Harmful Rewrite Detection Rate (HRDR): 0.909 (11 harmful)
- Harmful false acceptance rate: 0.091
- Safe rewrite rejection rate: 0.556 (9 safe)
- Ambiguous accuracy: 0.714 (7 ambiguous)
- Ambiguous macro F1: 0.417

| Level | Hit@1 | Recall@3 | Fact coverage | Faithfulness | Harmful rewrites reaching retriever |
| --- | ---: | ---: | ---: | ---: | ---: |
| Level 1 baseline | 0.926 | 1.000 | 0.926 | 1.000 | 0.000 |
| Level 2 rewrite | 0.852 | 1.000 | 0.852 | 1.000 | 1.000 |
| Level 3 judge | 0.926 | 1.000 | 0.926 | 1.000 | 0.091 |

## Test queries

| ID | Label | Category | Judge | Correct | L1 | L2 | L3 | Fallback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| t_abbrev_pro | safe | abbreviation | PASS | yes | warranty_claims | novabook_pro | novabook_pro | no |
| t_abbrev_air | safe | abbreviation | PASS | yes | novabook_air | novabook_air | novabook_air | no |
| t_abbrev_pt | safe | abbreviation | PASS | yes | returns_refurbished | pixeltab | pixeltab | no |
| t_syn_gift | safe | synonym | PASS | yes | gift_cards | gift_cards | gift_cards | no |
| t_syn_below | safe | constraint | PASS | yes | pixeltab | pixeltab | pixeltab | no |
| t_syn_percent | safe | number | PASS | yes | student_discount | student_discount | student_discount | no |
| t_syn_guarantee | safe | synonym | PASS | yes | returns_standard | novabook_pro | novabook_pro | no |
| t_syn_sendback | safe | synonym | PASS | yes | pixelbuds | pixelbuds | pixelbuds | no |
| t_filler_express | safe | abbreviation | PASS | yes | shipping_express | shipping_express | shipping_express | no |
| t_syn_atleast | safe | constraint | REJECT | no | business_lease | business_lease | business_lease | yes |
| t_fmt_50k | safe | number | PASS | yes | novabook_air | novabook_air | novabook_air | no |
| t_fmt_two_years | safe | number | PASS | yes | novabook_pro | novabook_pro | novabook_pro | no |
| t_sem_two_weeks | safe | semantic_equivalent | REJECT | no | novabook_air | novabook_air | novabook_air | yes |
| t_sem_one_week | safe | semantic_equivalent | REJECT | no | warranty_claims | warranty_claims | warranty_claims | yes |
| t_sem_twelve_months | safe | semantic_equivalent | REJECT | no | novabook_air | novabook_air | novabook_air | yes |
| t_sem_a_year | safe | semantic_equivalent | REJECT | no | gift_cards | gift_cards | gift_cards | yes |
| t_sem_repair_words | safe | semantic_equivalent | REJECT | no | repair_bangalore | repair_bangalore | repair_bangalore | yes |
| t_sem_two_thousand | safe | semantic_equivalent | REJECT | no | shipping_remote | shipping_metro | shipping_remote | yes |
| t_sem_24h | safe | semantic_equivalent | REJECT | no | shipping_express | shipping_express | shipping_express | yes |
| t_sem_two_days | safe | semantic_equivalent | REJECT | no | returns_refurbished | returns_refurbished | returns_refurbished | yes |
| t_sem_nobody_except | safe | scope | REJECT | no | warranty_claims | warranty_claims | warranty_claims | yes |
| t_sem_fifteen | safe | semantic_equivalent | REJECT | no | employee_discount | employee_discount | employee_discount | yes |
| t_h_air_pro | harmful | entity | REJECT | yes | novabook_air | novabook_pro | novabook_air | yes |
| t_h_city | harmful | entity | REJECT | yes | repair_bangalore | repair_delhi | repair_bangalore | yes |
| t_h_program | harmful | entity | REJECT | yes | student_discount | festival_sale | student_discount | yes |
| t_h_14_30 | harmful | number | REJECT | yes | novabook_air | novabook_air | novabook_air | yes |
| t_h_express_fee | harmful | number | REJECT | yes | shipping_express | shipping_express | shipping_express | yes |
| t_h_tradein | harmful | number | REJECT | yes | trade_in | trade_in | trade_in | yes |
| t_h_ladakh_flip | harmful | temporal | REJECT | yes | shipping_remote | shipping_remote | shipping_remote | yes |
| t_h_invoice_direction | harmful | temporal | REJECT | yes | warranty_claims | warranty_claims | warranty_claims | yes |
| t_h_recall | harmful | temporal | REJECT | yes | battery_recall | battery_recall | battery_recall | yes |
| t_h_software | harmful | negation | REJECT | yes | returns_standard | returns_standard | returns_standard | yes |
| t_h_water | harmful | negation | REJECT | yes | pixelbuds | pixelbuds | pixelbuds | yes |
| t_h_swollen | harmful | negation | REJECT | yes | repair_mailin | repair_mailin | repair_mailin | yes |
| t_h_liability | harmful | negation | REJECT | yes | data_transfer | data_transfer | data_transfer | yes |
| t_h_online_only | harmful | scope | REJECT | yes | festival_sale | festival_sale | festival_sale | yes |
| t_h_cities | harmful | scope | REJECT | yes | installation | installation | installation | yes |
| t_h_sku | harmful | scope | REJECT | yes | price_match | price_match | price_match | yes |
| t_h_cutoff | harmful | constraint | REJECT | yes | shipping_metro | shipping_metro | shipping_metro | yes |
| t_h_drop_tablet | harmful | multi_constraint | REJECT | yes | student_discount | student_discount | student_discount | yes |
| t_h_drop_pro | harmful | constraint | REJECT | yes | festival_sale | festival_sale | festival_sale | yes |
| t_h_express_drop | harmful | multi_constraint | REJECT | yes | shipping_express | shipping_express | shipping_express | yes |
| t_h_add_refurb | harmful | entity | REJECT | yes | novabook_air | novabook_air | novabook_air | yes |
| t_h_add_years | harmful | number | REJECT | yes | novabook_air | novabook_air | novabook_air | yes |
| t_h_window_elig | harmful | intent | REJECT | yes | pixeltab | pixeltab | pixeltab | yes |
| t_h_claim_vs_length | harmful | temporal | REJECT | yes | warranty_claims | warranty_base | warranty_claims | yes |
| t_h_worldwide | harmful | scope | REJECT | yes | intl_warranty | intl_warranty | intl_warranty | yes |
| t_h_sunday | harmful | constraint | REJECT | yes | installation | installation | installation | yes |
| t_a_latest | ambiguous | ambiguity | REJECT | no | pixeltab | pixeltab_mini | pixeltab | yes |
| t_a_cheap | ambiguous | ambiguity | REJECT | yes | novabook_lite | novabook_lite | novabook_lite | yes |
| t_a_month | ambiguous | semantic_equivalent | REJECT | no | returns_premium | novabook_air | returns_premium | yes |
| t_a_screen | ambiguous | entity | REJECT | yes | repair_bangalore | repair_bangalore | repair_bangalore | yes |
| t_a_free | ambiguous | constraint | REJECT | yes | shipping_metro | shipping_metro | shipping_metro | yes |
| t_a_couple | ambiguous | semantic_equivalent | REJECT | no | novabook_air | novabook_air | novabook_air | yes |
| t_a_lakh | ambiguous | number | REJECT | yes | student_discount | installation | student_discount | yes |
| t_a_cancel | ambiguous | temporal | REJECT | yes | northcloud | northcloud | northcloud | yes |
| t_a_newer | ambiguous | scope | REJECT | yes | business_lease | business_lease | business_lease | yes |
| t_a_mountains | ambiguous | entity | REJECT | yes | shipping_remote | shipping_remote | shipping_remote | yes |
| t_a_extended | ambiguous | scope | REJECT | yes | novabook_air | warranty_extended | novabook_air | yes |
| t_a_sameday | ambiguous | temporal | REJECT | yes | shipping_metro | shipping_express | shipping_metro | yes |
| t_syn_bundle | safe | synonym | PASS | yes | education_bundle | education_bundle | education_bundle | no |
| t_h_openbox | harmful | number | REJECT | yes | open_box | open_box | open_box | yes |
| t_h_transfer | harmful | negation | REJECT | yes | warranty_extended | warranty_extended | warranty_extended | yes |
| t_sem_points | safe | semantic_equivalent | REJECT | no | loyalty | loyalty | loyalty | yes |
| t_h_dock | harmful | entity | REJECT | yes | northdock | northdock | northdock | yes |
| t_a_monitor | ambiguous | ambiguity | REJECT | yes | homescreen_monitor | installation | homescreen_monitor | yes |
| t_filler_mumbai | safe | abbreviation | PASS | yes | hours_mumbai | hours_mumbai | hours_mumbai | no |
| t_h_deletion | harmful | temporal | REJECT | yes | account_deletion | account_deletion | account_deletion | yes |
| t_h_holiday | harmful | negation | REJECT | yes | hours_bangalore | hours_bangalore | hours_bangalore | yes |

## Findings

- On the held-out test queries, Hit@1 is 0.855 for Level 1, 0.870 for Level 2, and 0.899 for Level 3.
- Harmful rewrites reach the retriever on 100% of harmful test queries at Level 2 and 0% at Level 3.
- Test HRDR is 1.000, harmful false acceptance is 0.000, and safe rewrite rejection is 0.480.
- On ambiguous test rewrites, accuracy against the preferred label is 0.769 and macro F1 is 0.435.
- Semantic equivalents such as '14 days' and 'two weeks' are labeled safe. A slot judge that requires the same digits will reject them, and that rejection is counted in the safe rewrite rejection rate.
