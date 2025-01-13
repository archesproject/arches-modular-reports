from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("arches_provenance", "0003_pretty_print_config"),
    ]

    forward_sql_string = """
        CREATE OR REPLACE FUNCTION __arches_get_concept_label_v2(
            concept_value UUID,
            language_id TEXT DEFAULT 'en'
        )

        RETURNS TEXT
        LANGUAGE 'plpgsql'
        COST 100
        VOLATILE PARALLEL UNSAFE

        AS $BODY$

        DECLARE
            concept_label      TEXT := '';
            normalized_lang_id TEXT;
            base_lang_id       TEXT;
        BEGIN
            IF concept_value IS NULL THEN
                RETURN concept_label;
            END IF;

            normalized_lang_id := replace(language_id, '_', '-');
            base_lang_id := split_part(normalized_lang_id, '-', 1);

            SELECT v_lang.value
            INTO concept_label
            FROM values v_orig
            JOIN concepts c ON v_orig.conceptid = c.conceptid
            JOIN values v_lang ON c.conceptid = v_lang.conceptid
            WHERE v_orig.valueid = concept_value
            AND v_lang.valuetype = 'prefLabel'
            AND (
                v_lang.languageid = normalized_lang_id
                OR v_lang.languageid = base_lang_id
                OR v_lang.languageid LIKE base_lang_id || '-%'
                OR v_lang.languageid LIKE base_lang_id || '_%'
            )
            ORDER BY
                CASE
                    WHEN v_lang.languageid = normalized_lang_id THEN 1

                    WHEN (normalized_lang_id = base_lang_id AND 
                        (v_lang.languageid LIKE base_lang_id || '-%' OR v_lang.languageid LIKE base_lang_id || '_%'))
                        OR
                        (normalized_lang_id != base_lang_id AND v_lang.languageid = base_lang_id) THEN 2

                    WHEN v_lang.languageid LIKE base_lang_id || '-%' 
                        OR v_lang.languageid LIKE base_lang_id || '_%' THEN 3

                    ELSE 4
                END
            LIMIT 1;

            IF concept_label IS NULL THEN
                concept_label := '';
            END IF;

            RETURN concept_label;
        END;

        $BODY$;

            CREATE OR REPLACE FUNCTION public.__arches_get_concept_list_label_v2(
                concept_array jsonb,
                language_id text DEFAULT 'en')
                RETURNS text
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE PARALLEL UNSAFE
            AS $BODY$
                            declare
                                concept_list     text := '';
                            begin
                                if concept_array is null or concept_array::text = 'null' then
                                    return concept_list;
                                end if;

                                select string_agg(d.label, ', ')
                                from
                                (
                                    select __arches_get_concept_label_v2(x.conceptid::uuid, language_id) as label
                                    from (select json_array_elements_text(concept_array::json) as conceptid) x
                                ) d
                                into concept_list;
                                
                                if (concept_list is null) then
                                    concept_list := '';
                                end if;
                            
                            return concept_list;
                            end;
                            
            $BODY$;

            CREATE OR REPLACE FUNCTION public.__arches_get_node_display_value_v2(
                in_tiledata jsonb,
                in_nodeid uuid,
                language_id text DEFAULT 'en')
                RETURNS text
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE PARALLEL UNSAFE
            AS $BODY$
                    declare
                        display_value   text := '';
                        in_node_type    text;
                        in_node_config  json;
                    begin
                        if in_nodeid is null or in_nodeid is null then
                            return '<invalid_nodeid>';
                        end if;

                        if in_tiledata is null then
                            return '';
                        end if;

                        select n.datatype, n.config
                        into in_node_type, in_node_config
                        from nodes n where nodeid = in_nodeid::uuid;

                        if in_node_type in ('semantic', 'geojson-feature-collection', 'annotation') then
                            return 'unsupported node type (' || in_node_type || ')';
                        end if;

                        if in_node_type is null then
                            return '';
                        end if;

                        case in_node_type
                            when 'string' then
                                display_value := ((in_tiledata -> in_nodeid::text) -> language_id) ->> 'value';
                            when 'concept' then
                                display_value := __arches_get_concept_label_v2((in_tiledata ->> in_nodeid::text)::uuid);
                            when 'concept-list' then
                                display_value := __arches_get_concept_list_label_v2(in_tiledata -> in_nodeid::text);
                            when 'edtf' then
                                display_value := (in_tiledata ->> in_nodeid::text);
                            when 'file-list' then
                                display_value := __arches_get_file_list_label(in_tiledata -> in_nodeid::text, language_id);
                            when 'domain-value' then
                                display_value := __arches_get_domain_label((in_tiledata ->> in_nodeid::text)::uuid, in_nodeid, language_id);
                            when 'domain-value-list' then
                                display_value := __arches_get_domain_list_label(in_tiledata -> in_nodeid::text, in_nodeid, language_id);
                            when 'url' then
                                display_value := ((in_tiledata -> in_nodeid::text)::jsonb ->> 'url');
                            when 'node-value' then
                                display_value := __arches_get_nodevalue_label(in_tiledata -> in_nodeid::text, in_nodeid);
                            when 'resource-instance' then
                                display_value := __arches_get_resourceinstance_label(in_tiledata -> in_nodeid::text, 'name', language_id);
                            when 'resource-instance-list' then
                                display_value := __arches_get_resourceinstance_list_label(in_tiledata -> in_nodeid::text, 'name', language_id);
                            else
                                display_value := (in_tiledata ->> in_nodeid::text)::text;

                            end case;

                        return display_value;
                    end;

                        
            $BODY$;
        """

    reverse_sql_string = """
            drop function if exists __arches_get_node_display_value_v2;
            drop function if exists __arches_get_concept_list_label_v2;
            drop function if exists __arches_get_concept_label_v2;
        """

    operations = [
        migrations.RunSQL(forward_sql_string, reverse_sql_string),
    ]
