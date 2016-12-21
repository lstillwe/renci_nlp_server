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
GRANT ALL PRIVILEGES ON TABLE raw_news TO nlp_user; 

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
GRANT ALL PRIVILEGES ON TABLE sentences TO nlp_user; 

DROP TABLE IF EXISTS doc_coreference CASCADE;
CREATE TABLE doc_coreference(
  document_id bigint,
  coreferences text[],
  coref_offset bigint,
  coref_id text -- unique identifier for doc_coreference
);
GRANT ALL PRIVILEGES ON TABLE doc_coreference TO nlp_user; 

DROP TABLE IF EXISTS doc_coref CASCADE;
CREATE TABLE doc_coref(
  sentence_id text,
  sen_coref text[],
  document_id bigint,
  sentence_offset bigint
);
GRANT ALL PRIVILEGES ON TABLE doc_coref TO nlp_user; 
GRANT USAGE, SELECT ON SEQUENCE raw_news_news_id_seq to nlp_user;
