CREATE OR REPLACE FUNCTION execute_sql(query TEXT)
RETURNS SETOF JSONB
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY EXECUTE format('SELECT row_to_json(t)::jsonb FROM (%s) AS t', query);
END;
$$;
