# Retrieval Corpus Schema

## 1. Purpose

The retrieval corpus is a processed representation of the frozen government scholarship and education scheme corpus.

The same underlying scheme corpus will be used for BM25, all-MiniLM-L6-v2, and all-mpnet-base-v2 retrieval experiments.

## 2. Retrieval Text

The retrieval text for each scheme will be constructed from the following fields:

* Scheme name
* Category
* Study level
* Target group
* Description
* Eligibility
* Benefits
* Keywords

## 3. Retrieval Text Format

The fields will be combined into a single normalized text representation.

The structure will be:

Scheme Name: [scheme name]

Category: [category]

Study Level: [study level]

Target Group: [target group]

Description: [description]

Eligibility: [eligibility]

Benefits: [benefits]

Keywords: [keywords]

## 4. Fields Excluded From Retrieval Text

The following fields will not normally be included in the searchable text:

* scheme_id
* official_url
* source_name
* verification_date
* rule_version
* effective_from
* superseded_date

These fields are retained as metadata rather than semantic retrieval content.

## 5. Fair Comparison

BM25, all-MiniLM-L6-v2, and all-mpnet-base-v2 will use the same processed scheme corpus and the same retrieval text.

The benchmark queries and relevance judgments will also be identical across all three retrieval methods.

## 6. Metadata Preservation

The original scheme information will be preserved so that retrieved results can be traced back to the corresponding scheme and official source.

## 7. Corpus Version

The retrieval corpus is derived from Government Scholarship Corpus Version 1.0.
