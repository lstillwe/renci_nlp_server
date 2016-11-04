DROP TABLE IF EXISTS raw_news CASCADE;
CREATE TABLE raw_news(
  news_id bigserial primary key,
  url text,
  news_title text,
  news_text text,
  news_time timestamp with time zone,
  mentioned_org text[],
  mentioned_people text[]
);

DROP TABLE IF EXISTS sentences CASCADE;
CREATE TABLE sentences(
  document_id bigint,
  sentence text,
  words text[],
  lemma text[],
  pos_tags text[],
  dependencies text[],
  ner_tags text[],
  parse_tree text,
  sentence_offset bigint,
  sentence_id text -- unique identifier for sentences
  );

DROP TABLE IF EXISTS doc_coreference CASCADE;
CREATE TABLE doc_coreference(
  document_id bigint,
  coreferences text[],
  coref_offset bigint,
  coref_id text -- unique identifier for doc_coreference
);

DROP TABLE IF EXISTS doc_coref CASCADE;
CREATE TABLE doc_coref(
  sentence_id text,
  sen_coref text[],
  document_id bigint,
  sentence_offset bigint
);